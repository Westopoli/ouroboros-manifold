# Ouroboros Manifold — Web App Architecture Document

> **This document defines the technical architecture for the authenticated web application layer.** It covers authentication, session management, database schema, API surface, Stripe integration, and the relationship between the static marketing site and the Next.js application. This document implements Phase 2 (Backend and Commerce) and Phase 3 (Content Delivery) of the website design doc's build sequence.
>
> **MODIFICATION RULE:** Same as all project documents — append-only unless Westley explicitly approves a deletion.
>
> **RELATIONSHIP TO OTHER DOCUMENTS:**
> - **Website design doc** (`website_design_doc_X_XX.md`) — authoritative on visual design, page layout, and content strategy. This document implements the commerce architecture and infrastructure sections.
> - **Game bible** (`game_bible.md`) — authoritative on monetization model, entitlement logic, and distribution infrastructure.
> - **Monetization reference** (`bible_monetization.md`) — authoritative on subscription flow, era pack purchases, access keys, and the hybrid Steam + direct model.
>
> **Last updated:** April 8, 2026 (v1.00) — Initial document. Auth providers, database schema, API routes, Stripe integration, session management, and deployment architecture established.

---

## Table of Contents

1. [Architecture Overview](#architecture-overview) — System topology, what lives where, how pieces connect
2. [Technology Stack](#technology-stack) — Framework, ORM, database, auth, payments
3. [Authentication](#authentication) — Providers, flows, session management, security model
4. [Database Schema](#database-schema) — Tables, relationships, entitlement resolution
5. [API Surface](#api-surface) — Route inventory, request/response contracts, middleware
6. [Stripe Integration](#stripe-integration) — Subscription flow, era pack purchases, webhook handling
7. [Access Key System](#access-key-system) — Key redemption API, validation, entitlement recording
8. [Content Delivery](#content-delivery) — R2 signed URLs, download flow, Godot client integration
9. [Static Site Integration](#static-site-integration) — How marketing pages and the app coexist
10. [Deployment Architecture](#deployment-architecture) — Hosting, environments, infrastructure
11. [Security Model](#security-model) — Threat surface, mitigations, checklist
12. [Open Architecture Questions](#open-architecture-questions) — Unresolved decisions
13. [Document Maintenance](#document-maintenance) — Rules, versioning, governance

---

## Architecture Overview

The system has three distinct layers that serve different purposes and can be deployed independently:

**Layer 1 — Static marketing site.** The existing HTML/CSS/JS pages (index, the-game, era-library marketing view, articles, article detail pages). These are pure static files served from a CDN. They contain no server-side logic, no authentication, and no database access. They are the top of the conversion funnel.

**Layer 2 — Next.js application.** The authenticated web app that handles: user sign-in/sign-out, account dashboard, subscription management, era library management (the authenticated view showing owned content), purchase flows, access key redemption, and all API endpoints. This is a server-rendered application with both page routes and API routes.

**Layer 3 — External services.** Stripe (payment processing), Cloudflare R2 (era pack file storage), Steam Web API (DLC ownership verification), and OAuth providers (Google, Discord, Steam, Apple). The Next.js app orchestrates communication with all of these.

**The Godot game client** is a consumer of Layer 2's API. It calls authentication and entitlement endpoints on launch and content delivery endpoints when downloading era packs. The client never communicates directly with Stripe, R2, or OAuth providers — the Next.js API mediates all external service access.

### System Topology

```
┌─────────────────────────────────────────────────────────────┐
│                        CDN (Cloudflare)                     │
│   Static marketing pages: /, /the-game, /articles, etc.    │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                     Next.js Application                     │
│                                                             │
│  Page Routes (SSR)          API Routes (serverless/node)    │
│  ├── /account               ├── /api/auth/*                 │
│  ├── /account/purchases     ├── /api/entitlements           │
│  ├── /account/subscription  ├── /api/keys/redeem            │
│  ├── /library (auth'd)      ├── /api/checkout               │
│  └── /redeem                ├── /api/webhooks/stripe        │
│                             ├── /api/content/download       │
│                             └── /api/steam/verify           │
└──────────────────────┬──────────────────────────────────────┘
                       │
         ┌─────────────┼──────────────┬──────────────┐
         │             │              │              │
    ┌────▼────┐  ┌─────▼─────┐ ┌─────▼─────┐ ┌─────▼─────┐
    │ Postgres │  │  Stripe   │ │ Cloudflare│ │  OAuth    │
    │ Database │  │ Payments  │ │    R2     │ │ Providers │
    └─────────┘  └───────────┘ └───────────┘ └───────────┘

┌─────────────────────────────────────────────────────────────┐
│                    Godot Game Client                         │
│  Calls /api/auth/*, /api/entitlements, /api/content/*       │
└─────────────────────────────────────────────────────────────┘
```

---

## Technology Stack

### Resolved Decisions

| Component | Choice | Rationale |
|-----------|--------|-----------|
| **Framework** | Next.js 14+ (App Router) | Server-side rendering for authenticated pages, API routes for the game client, React for interactive account UI. Resolves Open Question #3 from the website design doc — Node/TypeScript chosen over Python/FastAPI. |
| **Language** | TypeScript | Type safety across API contracts, database queries, and Stripe webhook payloads. Catches entitlement logic bugs at compile time. |
| **ORM** | Prisma | Type-safe database access, automatic migration management, parameterized queries (eliminates SQL injection by design). |
| **Database** | PostgreSQL (managed) | The entitlement system requires relational integrity — a user's access state is the join of subscriptions, purchases, keys, and Steam DLC. Postgres handles this cleanly. Hosting options: Supabase (free tier, managed), Neon (free tier, serverless), or Railway ($5/month). Resolves Open Question #4 from the website design doc — Supabase or equivalent managed Postgres, not custom JWT. |
| **Auth** | NextAuth.js (Auth.js v5) | Handles OAuth flows, session management, CSRF protection, and secure cookie configuration. Supports all five target providers. Resolves the auth provider question with a dedicated library rather than rolling custom. |
| **Payments** | Stripe | Per the website design doc's commerce architecture. Stripe Checkout for payment pages, Stripe Customer Portal for subscription management, Stripe Webhooks for event processing. |
| **Object Storage** | Cloudflare R2 | Per the website design doc's content delivery plan. Zero egress fees, S3-compatible API, signed URL support. |
| **Deployment** | Vercel (Next.js) + Cloudflare (static + R2) | Vercel for the Next.js app (free tier covers early traffic, scales with demand). Cloudflare Pages for the static marketing site. Cloudflare R2 for era pack storage. |

---

## Authentication

### Design Philosophy

No passwords. The authentication system uses exclusively **delegated identity** — OAuth providers and magic link email. This eliminates the credential storage attack surface entirely. The application never sees, hashes, stores, or compares a password. User identity is established by a trusted third party and recorded as a provider-account link in the database.

### Providers

Five authentication providers, chosen based on the target audience (PC strategy gamers) and platform coverage:

| Provider | Why | OAuth Type | Notes |
|----------|-----|------------|-------|
| **Steam** | Primary gaming identity. Most players already have a Steam account and the game ships on Steam. | OpenID 2.0 (Steam uses its own OpenID implementation, not standard OAuth2) | Steam does not provide email addresses via its API. Players signing in via Steam may need to provide an email separately for transactional communications (receipts, subscription notices). NextAuth has a community Steam provider. |
| **Discord** | Secondary gaming identity. The game will have a Discord community server. Players who engage with the community likely sign in here. | OAuth 2.0 | Provides email (if verified on Discord). |
| **Google** | Broadest reach. Covers players who don't use Discord or want a non-gaming identity. | OAuth 2.0 | Provides verified email. |
| **Apple** | Required for macOS players. Apple's sign-in guidelines require offering Apple auth if the app offers any third-party sign-in on Apple platforms. | OAuth 2.0 (Sign in with Apple) | Apple provides a private relay email by default — the user can choose to share their real email or use Apple's relay. Both work for transactional email. |
| **Email (Magic Link)** | Fallback for users who don't want to use any OAuth provider. No password involved — a one-time login link is sent to the user's email. | N/A (email verification) | Requires an email sending service (Resend, SendGrid, or AWS SES). The magic link token is cryptographically random, single-use, and expires after 10 minutes. |

### Authentication Flow

**OAuth flow (Steam, Discord, Google, Apple):**

1. User clicks "Sign in with [Provider]" on the account page or in-game Era Library.
2. NextAuth redirects to the provider's authorization page.
3. User authenticates with the provider (may already be signed in).
4. Provider redirects back to `/api/auth/callback/[provider]` with an authorization code.
5. NextAuth exchanges the code for an access token and retrieves the user's profile (provider ID, email if available, display name).
6. NextAuth checks the database: does a user with this provider link exist?
   - **Yes:** Sign in. Create a session.
   - **No, but email matches an existing user:** Link this provider to the existing account (auto-link on verified email — see Account Linking below). Create a session.
   - **No match at all:** Create a new user record, link the provider, create a session.
7. Session cookie is set (HttpOnly, Secure, SameSite=Lax) and the user is redirected to their destination (account page, library, or wherever they initiated sign-in).

**Magic link flow (Email):**

1. User enters their email address on the sign-in page.
2. NextAuth generates a cryptographically random token, stores it in the database with the email and a 10-minute expiry, and sends an email containing a link to `/api/auth/callback/email?token=[token]`.
3. User clicks the link in their email.
4. NextAuth validates the token (exists, not expired, not already used), marks it as consumed, and resolves the email to a user account (creating one if necessary).
5. Session cookie is set and the user is redirected.

**Godot client authentication flow:**

1. The game client opens a system browser window (not an embedded webview — embedded webviews are a phishing risk) to the sign-in page with a `redirect_uri` pointing to a localhost callback.
2. User completes the normal OAuth or magic link flow in their browser.
3. On successful authentication, the server redirects to the localhost callback with a short-lived authorization code.
4. The Godot client exchanges the authorization code for a session token via `/api/auth/token`.
5. The client stores the session token securely and includes it as a Bearer token in all subsequent API requests.
6. Token refresh is handled via `/api/auth/refresh` before expiry.

### Account Linking

A user may sign in via different providers at different times. The linking policy:

- **Auto-link on verified email match.** If a user signs in with Discord (email: player@example.com) and later signs in with Google (same email, verified by Google), the accounts are linked automatically. This is safe because both providers have verified ownership of the email.
- **No auto-link on unverified email.** If a provider does not verify the email (or the user uses Apple's private relay), no auto-link occurs. The user can manually link providers from their account settings page.
- **Steam special case.** Steam does not provide email. A Steam-only user has no email on file until they either link another provider or manually add one. Transactional emails (receipts, subscription notices) require an email — the account page prompts Steam-only users to add one.
- **Manual linking.** The account settings page allows a signed-in user to link additional providers. This requires signing in with the new provider (proving ownership) and confirming the link.

### Session Management

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| **Session strategy** | JWT (stateless) | No server-side session store needed. Session data (user ID, provider, expiry) is encoded in the JWT and stored in an HttpOnly cookie. Scales horizontally without shared state. |
| **Cookie flags** | `HttpOnly`, `Secure`, `SameSite=Lax` | HttpOnly prevents JavaScript access (blocks XSS-based theft). Secure ensures HTTPS-only transmission. SameSite=Lax prevents cross-site request attachment while allowing top-level navigation (OAuth redirects). |
| **Session lifetime** | 30 days (web), 90 days (game client) | Web sessions are shorter because browsers are shared devices. Game client sessions are longer because the client is a personal installation. Both use refresh tokens to extend without re-authentication. |
| **Refresh token** | Rotated on each use, 90-day absolute expiry | If a refresh token is used, a new one is issued and the old one is invalidated. This limits the window of a stolen refresh token. After 90 days with no activity, the user must re-authenticate. |
| **CSRF protection** | Built into NextAuth | NextAuth includes CSRF tokens in all authentication forms and validates them on submission. API routes that mutate state also validate the session JWT. |

---

## Database Schema

### Entity-Relationship Overview

```
User ──1:N── Account (provider links)
User ──1:N── Purchase (one-time era pack buys)
User ──1:1── Subscription (active Stripe subscription)
User ──1:N── KeyRedemption (redeemed access keys)
User ──1:N── SteamEntitlement (verified Steam DLC ownership)
User ──1:N── EraProgress (mastery tracking per era)

AccessKey ──1:1── KeyRedemption (each key redeemed once)
```

### Tables

**users**

| Column | Type | Notes |
|--------|------|-------|
| `id` | UUID (PK) | Internal user identifier. |
| `email` | VARCHAR, nullable, unique | Null for Steam-only users who haven't added an email. |
| `display_name` | VARCHAR | From provider profile or manually set. |
| `stripe_customer_id` | VARCHAR, nullable, unique | Created on first Stripe interaction (checkout or portal). |
| `created_at` | TIMESTAMP | Account creation time. |
| `updated_at` | TIMESTAMP | Last profile modification. |

**accounts** (NextAuth standard — provider links)

| Column | Type | Notes |
|--------|------|-------|
| `id` | UUID (PK) | |
| `user_id` | UUID (FK → users) | |
| `provider` | VARCHAR | `google`, `discord`, `steam`, `apple`, `email` |
| `provider_account_id` | VARCHAR | The user's ID on the provider's system. |
| `access_token` | VARCHAR, nullable | OAuth access token (encrypted at rest). |
| `refresh_token` | VARCHAR, nullable | OAuth refresh token (encrypted at rest). |
| `expires_at` | INTEGER, nullable | Token expiry epoch. |
| **Unique constraint** | `(provider, provider_account_id)` | One link per provider identity. |

**subscriptions**

| Column | Type | Notes |
|--------|------|-------|
| `id` | UUID (PK) | |
| `user_id` | UUID (FK → users, unique) | One active subscription per user. |
| `stripe_subscription_id` | VARCHAR, unique | Stripe's subscription object ID. |
| `status` | ENUM | `active`, `past_due`, `canceled`, `trialing`, `paused` |
| `current_period_start` | TIMESTAMP | Current billing period start. |
| `current_period_end` | TIMESTAMP | Current billing period end. Access continues until this date even after cancellation. |
| `cancel_at_period_end` | BOOLEAN | True if the user has canceled but the period hasn't ended. |
| `created_at` | TIMESTAMP | |
| `updated_at` | TIMESTAMP | |

**purchases** (one-time era pack buys)

| Column | Type | Notes |
|--------|------|-------|
| `id` | UUID (PK) | |
| `user_id` | UUID (FK → users) | |
| `era_id` | VARCHAR | Era identifier (e.g., `settled-reach`, `roman`, `1980s`). |
| `stripe_payment_intent_id` | VARCHAR, unique | Links to the Stripe payment for receipts and disputes. |
| `amount_cents` | INTEGER | Purchase price at time of sale (for historical records). |
| `currency` | VARCHAR | `usd` (or localized). |
| `purchased_at` | TIMESTAMP | |

**access_keys**

| Column | Type | Notes |
|--------|------|-------|
| `id` | UUID (PK) | |
| `code` | VARCHAR, unique | The alphanumeric key string. Variable length per the game bible. |
| `key_type` | ENUM | `permanent`, `time_limited`, `mission_limited` |
| `scope` | JSONB | Which eras the key unlocks. E.g., `{"eras": ["1980s"]}` or `{"eras": "all"}` for full access. |
| `duration_days` | INTEGER, nullable | For `time_limited` keys — how many days of access. |
| `mission_count` | INTEGER, nullable | For `mission_limited` keys — how many missions. |
| `created_at` | TIMESTAMP | |
| `expires_at` | TIMESTAMP, nullable | Key-level expiry (the key itself becomes unredeemable after this date, independent of the access it grants). |
| `redeemed_by` | UUID (FK → users), nullable | Null until redeemed. |
| `redeemed_at` | TIMESTAMP, nullable | |

**steam_entitlements**

| Column | Type | Notes |
|--------|------|-------|
| `id` | UUID (PK) | |
| `user_id` | UUID (FK → users) | |
| `steam_app_id` | VARCHAR | The Steam DLC app ID for the era. |
| `era_id` | VARCHAR | Mapped era identifier. |
| `verified_at` | TIMESTAMP | Last time ownership was confirmed via Steam API. |

**era_progress** (mastery tracking)

| Column | Type | Notes |
|--------|------|-------|
| `id` | UUID (PK) | |
| `user_id` | UUID (FK → users) | |
| `era_id` | VARCHAR | |
| `missions_completed` | INTEGER | |
| `mastery_points` | INTEGER | Accumulated mastery progress. |
| `tier` | INTEGER | Current mastery tier (1, 2, 3). |
| `updated_at` | TIMESTAMP | |
| **Unique constraint** | `(user_id, era_id)` | One progress record per user per era. |

### Entitlement Resolution

The core business logic. Given a `user_id`, determine which eras they can access:

```
function resolveEntitlements(userId):
    eras = Set()

    // 1. Always include free tier
    eras.add("roman")

    // 2. Active subscription → all eras
    sub = getSubscription(userId)
    if sub.status in ["active", "trialing", "past_due"]:
        eras.addAll(ALL_AVAILABLE_ERAS)
        return eras

    // 3. One-time purchases → permanent
    purchases = getPurchases(userId)
    for purchase in purchases:
        eras.add(purchase.era_id)

    // 4. Access keys → type-dependent
    keys = getRedeemedKeys(userId)
    for key in keys:
        if key.type == "permanent":
            eras.add(key.scope.eras)
        if key.type == "time_limited" and key.redeemed_at + key.duration_days > now():
            eras.add(key.scope.eras)
        if key.type == "mission_limited" and key.remaining_missions > 0:
            eras.add(key.scope.eras)

    // 5. Steam DLC ownership
    steamEntitlements = getSteamEntitlements(userId)
    for ent in steamEntitlements:
        eras.add(ent.era_id)

    return eras
```

This implements the game bible's platform-agnostic entitlement principle: the client receives a flat set of era IDs regardless of acquisition channel.

---

## API Surface

### Authentication Routes

Handled by NextAuth. These follow NextAuth's standard routing conventions:

| Route | Method | Purpose |
|-------|--------|---------|
| `/api/auth/signin` | GET | Renders the sign-in page with provider buttons and magic link form. |
| `/api/auth/callback/[provider]` | GET | OAuth callback handler. |
| `/api/auth/signout` | POST | Destroys the session. |
| `/api/auth/session` | GET | Returns current session state (user ID, email, linked providers). |
| `/api/auth/token` | POST | Exchanges an authorization code for a session token (Godot client flow). |
| `/api/auth/refresh` | POST | Refreshes an expiring session token (Godot client flow). |

### Application API Routes

| Route | Method | Auth | Purpose |
|-------|--------|------|---------|
| `/api/entitlements` | GET | Required | Returns the authenticated user's full entitlement set. The Godot client calls this on launch. Response: `{ eras: ["roman", "settled-reach", "1980s", ...], subscription_active: bool, trial_missions_remaining: { "1980s": 3, "settled-reach": 5 } }` |
| `/api/checkout/subscription` | POST | Required | Creates a Stripe Checkout session for subscription purchase. Redirects to Stripe's hosted payment page. |
| `/api/checkout/era/[eraId]` | POST | Required | Creates a Stripe Checkout session for a one-time era pack purchase. |
| `/api/portal` | POST | Required | Creates a Stripe Customer Portal session for subscription management (cancel, update payment, view invoices). Redirects to Stripe's hosted portal. |
| `/api/keys/redeem` | POST | Required | Redeems an access key. Body: `{ code: string }`. Validates the key, binds it to the user, records the entitlement. Returns the key type and scope for the client to display the appropriate celebration animation. |
| `/api/content/download/[eraId]` | GET | Required | Validates that the user is entitled to the era, then generates and returns a signed R2 URL for the era pack file. The Godot client downloads directly from R2 using this URL. |
| `/api/steam/verify` | POST | Required | Accepts a Steam auth ticket from the Godot client, verifies ownership of Steam DLC via the Steam Web API, and records any new entitlements. Called on launch for players who linked a Steam account. |
| `/api/webhooks/stripe` | POST | None (Stripe signature verification) | Receives Stripe webhook events. See Stripe Integration section. |

### Middleware Stack

Every API route (except `/api/webhooks/stripe`) passes through this middleware chain:

1. **Rate limiting.** Per-IP and per-user limits to prevent brute force and abuse. Suggested defaults: 60 requests/minute per IP for authenticated routes, 10 requests/minute for unauthenticated routes (sign-in, magic link request).
2. **CORS.** Allows requests from the marketing site domain and the game client's user-agent. Blocks other origins.
3. **Session validation.** Extracts and validates the JWT from the cookie or Authorization header. Rejects expired or malformed tokens.
4. **CSRF validation.** For cookie-based requests (browser), validates the CSRF token. For Bearer token requests (Godot client), CSRF is not applicable (tokens are not automatically attached by browsers).

The Stripe webhook route skips session/CSRF middleware and instead validates the Stripe webhook signature using the webhook signing secret.

---

## Stripe Integration

### Products and Prices

| Stripe Product | Type | Price | Notes |
|----------------|------|-------|-------|
| Ouroboros Manifold Subscription | Recurring | $3–5/month (final pricing TBD) | Grants access to all eras. Maps to the `subscriptions` table. |
| Era Pack: [Era Name] | One-time | $2–3 per era (final pricing TBD) | One Stripe product per era. Maps to the `purchases` table. |

Prices are configured in the Stripe Dashboard. The application references Stripe Price IDs (e.g., `price_abc123`) stored in environment variables or a configuration file, not hardcoded.

### Checkout Flow

1. User clicks "Subscribe" or "Buy [Era]" on the website or in-game Era Library.
2. The application calls `/api/checkout/subscription` or `/api/checkout/era/[eraId]`.
3. The API route creates a Stripe Checkout Session:
   - Sets `customer` to the user's `stripe_customer_id` (creating a Stripe Customer if this is their first interaction).
   - Sets `success_url` and `cancel_url` for post-checkout redirects.
   - Sets `metadata.user_id` for webhook correlation.
   - For subscriptions: sets `mode: "subscription"`.
   - For era packs: sets `mode: "payment"` with `metadata.era_id`.
4. The API returns the Checkout Session URL. The client (browser or Godot) opens this URL.
5. The user completes payment on Stripe's hosted page. The application never handles card numbers, CVVs, or any PCI-scoped data.
6. Stripe sends webhook events to `/api/webhooks/stripe`.

### Webhook Events

| Event | Action |
|-------|--------|
| `checkout.session.completed` | If subscription: create/update `subscriptions` record. If one-time: create `purchases` record. In both cases, resolve the `user_id` from session metadata and update entitlements. |
| `customer.subscription.updated` | Update `subscriptions` record (status changes, period changes, cancellation). |
| `customer.subscription.deleted` | Set subscription status to `canceled`. Entitlement resolution will exclude subscription eras on next check. |
| `invoice.payment_failed` | Set subscription status to `past_due`. Optionally send a notification email. Stripe's built-in dunning handles retry attempts. |
| `invoice.paid` | If previously `past_due`, restore to `active`. |

### Webhook Security

Every incoming webhook request is verified using `stripe.webhooks.constructEvent()` with the webhook signing secret. This confirms:
- The request genuinely came from Stripe (not a spoofed payload).
- The payload has not been tampered with in transit.
- The event is recent (Stripe includes a timestamp; the library rejects events older than a configurable tolerance, default 300 seconds).

Webhook processing is **idempotent** — receiving the same event twice produces the same database state. This is critical because Stripe may retry failed webhook deliveries.

---

## Access Key System

Implements the three key types defined in the game bible's monetization reference.

### Key Generation (Admin)

Keys are generated via a CLI tool or admin script — not through a web interface (no admin dashboard in v1). The script:
1. Generates a cryptographically random alphanumeric code (16–24 characters).
2. Inserts a record in `access_keys` with the specified type, scope, and parameters.
3. Outputs the key code for distribution.

Batch generation is supported for promotional campaigns (e.g., "generate 500 mission-limited keys for the 1980s era, 3 missions each").

### Redemption Flow

1. User enters a key code on the web redemption page (`/redeem`) or in-game.
2. The client calls `POST /api/keys/redeem` with `{ code: "ABC123..." }`.
3. The server validates: key exists, key is not expired, key is not already redeemed.
4. On success: sets `redeemed_by` and `redeemed_at`, returns the key type and scope.
5. The client triggers the appropriate celebration animation (per the game bible's UI personality section) based on key type.
6. Entitlement resolution now includes this key's scope.

### Mission-Limited Key Tracking

For `mission_limited` keys, the remaining mission count is tracked. When the Godot client reports a mission start (via a future `/api/missions/start` endpoint), the server decrements the counter for any active mission-limited keys covering that era. When the counter reaches zero, the entitlement expires at the next mission selection screen (per the bible: no mid-mission lockout).

---

## Content Delivery

Implements the website design doc's Phase 3 (Content Delivery) using Cloudflare R2.

### Storage Structure

```
r2-bucket/
├── eras/
│   ├── settled-reach/
│   │   ├── v1.0.0/
│   │   │   ├── manifest.json       (file listing, checksums, version)
│   │   │   ├── library.json        (naming, chronicles, briefings, events)
│   │   │   └── assets.tar.gz       (3D models, textures, audio)
│   │   └── latest.json             (points to current version)
│   ├── roman/
│   │   └── ...
│   └── 1980s/
│       └── ...
```

### Download Flow

1. Godot client calls `GET /api/entitlements` on launch. Receives the set of owned eras.
2. Client compares owned eras against locally cached content. Identifies eras that need downloading or updating.
3. For each needed era: client calls `GET /api/content/download/[eraId]`.
4. Server validates entitlement (is this user allowed to access this era?). If not, returns 403.
5. Server generates a signed R2 URL with a 15-minute expiry for the era pack files.
6. Server returns `{ manifest_url: "...", library_url: "...", assets_url: "..." }`.
7. Client downloads directly from R2 using the signed URLs. The application server never proxies file bytes.
8. Client verifies file checksums against the manifest and unpacks into the local content directory.

### Versioning

Each era pack has a semantic version. The `latest.json` file in each era's R2 directory points to the current version. The client checks this on launch and updates if a new version is available. Old versions are retained in R2 for a configurable period to support clients that haven't updated yet.

---

## Static Site Integration

### The Seam

Users should never notice the boundary between the static marketing site and the Next.js application. Both share:

- **The same domain.** All content lives under `ouroborosmanifold.com`.
- **The same visual language.** The Next.js pages import the same CSS variables, fonts (Cormorant Garamond + Sora), and component patterns (nav, footer, theme toggle) as the static pages.
- **The same navigation.** The nav bar is identical. Clicking "Account" from a static page navigates to the Next.js-served account page. Clicking "The Game" from the account page navigates back to the static page.

### Routing

The static site and Next.js app are deployed behind the same domain using path-based routing:

| Path Pattern | Served By | Notes |
|--------------|-----------|-------|
| `/` | Static (CDN) | Landing page. |
| `/the-game` | Static (CDN) | Deep pitch page. |
| `/era-library` | Static (CDN) | Marketing-only era catalog (pre-auth). |
| `/articles`, `/articles/*` | Static (CDN) | Article index and detail pages. |
| `/account`, `/account/*` | Next.js | Authenticated account management. |
| `/library` | Next.js | Authenticated era library (owned content, purchase buttons). |
| `/redeem` | Next.js | Access key redemption page. |
| `/api/*` | Next.js | All API endpoints. |

This routing is configured at the CDN/reverse proxy level (Cloudflare or Vercel). Static paths resolve to the CDN. Dynamic paths proxy to the Next.js application.

### Navigation State

The nav bar needs to show auth state (signed in vs. signed out) across both static and dynamic pages. On static pages, the nav makes a lightweight client-side fetch to `/api/auth/session` on page load. If the user is signed in, the nav updates to show their display name and a "Sign Out" option instead of the "Join Waitlist" CTA. This fetch is non-blocking — the page renders immediately with the default state and updates when the session check completes.

---

## Deployment Architecture

### Environments

| Environment | Purpose | Infrastructure |
|-------------|---------|----------------|
| **Development** | Local development and testing. | Next.js dev server, local Postgres (Docker), Stripe test mode, R2 emulated via local file system or MinIO. |
| **Staging** | Pre-production verification. | Vercel preview deployment, staging database, Stripe test mode with test keys, staging R2 bucket. |
| **Production** | Live. | Vercel production, production database, Stripe live mode, production R2 bucket, production domain. |

### Environment Variables

All secrets are stored in Vercel's encrypted environment variable store (not in code, not in `.env` files committed to Git):

- `DATABASE_URL` — Postgres connection string.
- `NEXTAUTH_SECRET` — Secret for JWT signing and encryption.
- `NEXTAUTH_URL` — Canonical URL of the application.
- `STRIPE_SECRET_KEY` — Stripe API key (test or live depending on environment).
- `STRIPE_WEBHOOK_SECRET` — Webhook signing secret.
- `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET` — Google OAuth credentials.
- `DISCORD_CLIENT_ID`, `DISCORD_CLIENT_SECRET` — Discord OAuth credentials.
- `STEAM_API_KEY` — Steam Web API key.
- `APPLE_CLIENT_ID`, `APPLE_CLIENT_SECRET` — Apple Sign In credentials.
- `EMAIL_SERVER_*` — SMTP/API credentials for magic link emails.
- `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`, `R2_BUCKET`, `R2_ENDPOINT` — R2 credentials.

### Cost Projection

| Component | Free Tier | Paid Tier | When Paid Kicks In |
|-----------|-----------|-----------|-------------------|
| Vercel (Next.js hosting) | 100GB bandwidth, 100 hrs compute | $20/month (Pro) | ~1000+ daily active users or heavy API traffic. |
| Postgres (Supabase/Neon) | 500MB storage, 50K monthly requests | $25/month | ~10K users or heavy write volume. |
| Cloudflare R2 | 10GB storage, 10M reads/month | $0.015/GB storage, $0.36/M reads | Hundreds of era pack uploads (unlikely near launch). |
| Stripe | No monthly fee | 2.9% + $0.30 per transaction | Costs scale linearly with revenue. |
| Email (Resend) | 3,000 emails/month | $20/month (50K emails) | ~3,000 magic link logins/month. |
| **Total at launch** | **~$0–15/month** | | |
| **Total at scale (1K subscribers)** | | **~$70–100/month + Stripe fees** | |

---

## Security Model

### Threat Surface and Mitigations

| Threat | Mitigation | Responsibility |
|--------|------------|----------------|
| **XSS (Cross-Site Scripting)** | React escapes all rendered content by default. HttpOnly session cookies prevent token theft even if XSS occurs. Content Security Policy headers restrict script sources. | Framework (React) + infrastructure (CSP headers). |
| **CSRF (Cross-Site Request Forgery)** | NextAuth includes CSRF tokens on all auth forms. API routes that mutate state require a valid session JWT. SameSite=Lax cookie attribute blocks cross-origin cookie attachment on non-GET requests. | Framework (NextAuth) + cookie configuration. |
| **SQL Injection** | Prisma ORM uses parameterized queries exclusively. No raw SQL in the codebase. | Framework (Prisma). |
| **Session hijacking** | HttpOnly + Secure + SameSite cookie flags. HTTPS everywhere. Short session lifetimes with refresh rotation. | Cookie configuration + infrastructure (HTTPS). |
| **Stripe webhook spoofing** | All webhook payloads verified via `stripe.webhooks.constructEvent()` with the signing secret. | Application logic. |
| **R2 content theft** | Signed URLs with 15-minute expiry. URLs are generated per-request after entitlement validation. No public bucket access. | Application logic + R2 configuration. |
| **OAuth account takeover** | Auto-linking only on verified email. Unverified providers require manual linking from an authenticated session. | Application logic (NextAuth callbacks). |
| **Brute force (magic link)** | Rate limiting on the email send endpoint (10/hour per email address). Token entropy (256-bit random) makes guessing infeasible. | Application logic (rate limiter). |
| **Enumeration attacks** | Sign-in page returns the same response regardless of whether an email exists in the database. "If you have an account, you'll receive a magic link." | Application logic. |
| **Key brute force** | Rate limiting on the redeem endpoint. Key codes are 16–24 characters with 62-character alphabet (a-z, A-Z, 0-9), yielding >10^28 possible codes. | Application logic (rate limiter) + key generation. |

### Security Checklist (Pre-Launch)

- [ ] All pages served over HTTPS. HTTP redirects to HTTPS.
- [ ] HSTS header enabled with long max-age.
- [ ] Content Security Policy header configured (restrict script-src, style-src, frame-ancestors).
- [ ] X-Content-Type-Options: nosniff.
- [ ] X-Frame-Options: DENY (prevent clickjacking).
- [ ] Referrer-Policy: strict-origin-when-cross-origin.
- [ ] All environment variables encrypted in deployment platform. No secrets in code or Git.
- [ ] Stripe webhook signature verification tested with replay attacks.
- [ ] Rate limiting tested on all public endpoints.
- [ ] OAuth callback URLs restricted to the production domain (no open redirectors).
- [ ] R2 bucket policy: no public access. Signed URLs only.
- [ ] Database backups automated (daily minimum).
- [ ] Dependency audit (`npm audit`) clean or all findings reviewed.
- [ ] Magic link email content reviewed (no sensitive data in the email body beyond the link itself).

---

## Open Architecture Questions

### 1. Godot Client Auth — Browser vs. Deep Link

The proposed flow opens a system browser for authentication and uses a localhost redirect to pass the token back to the game client. An alternative is a deep link / custom URI scheme (e.g., `ouroboros://auth?token=...`). Deep links are cleaner but require platform-specific setup (macOS, Windows, Linux). Decision deferred until Godot client work begins.

### 2. Steam OpenID vs. Steam Web API Auth

Steam's authentication uses OpenID 2.0, which is older than the OAuth 2.0 used by other providers. NextAuth has a community-maintained Steam provider, but it's less battle-tested than the official Google/Discord/Apple providers. Alternative: use Steam's Web API `AuthenticateUserTicket` endpoint for the Godot client (where the player is already signed into Steam) and reserve the NextAuth Steam provider for web-only sign-in. Decision deferred until implementation.

### 3. Email Service Provider

Magic links and transactional emails (receipts, subscription notifications) require an email sending service. Candidates: Resend (modern API, good DX, free tier), SendGrid (established, generous free tier), AWS SES (cheapest at scale, more setup). Decision deferred until implementation.

### 4. Database Hosting Provider

Supabase (managed Postgres + auth + REST), Neon (serverless Postgres, generous free tier), Railway (simple managed Postgres). Supabase's built-in auth is redundant with NextAuth — using both adds confusion. Neon's serverless model pairs well with Vercel's serverless functions. Decision deferred until implementation.

### 5. Admin Dashboard

v1 has no admin interface. Key generation, user lookup, and entitlement debugging happen via CLI scripts and direct database queries. An admin dashboard (user search, subscription management, key generation UI, analytics) is a Phase 4 consideration when operational complexity justifies the build time.

---

## Document Maintenance

### Rules

1. **This file is the technical architecture reference for the web application.** It does not override the website design doc's visual decisions or the game bible's monetization model. It implements them.
2. **Append-only unless Westley approves.**
3. **Technical specifics belong here.** API contracts, database schemas, deployment configuration, security checklists — all technical implementation details live in this document.
4. **Update, don't append.** When an architecture decision changes with Westley's approval, update the relevant section in place.
5. **Open questions move to resolved.** When resolved, write the answer into the appropriate section and remove from the open list.
6. **Version numbering.** `webapp_architecture_X_XX.md`. Same convention as all project documents.

### Relationship to Other Documents

- **Website design doc** — authoritative on what the user sees. This document is authoritative on how it works.
- **Game bible / monetization reference** — authoritative on what the business rules are. This document is authoritative on how those rules are enforced in code.
- **Future implementation docs** — specific component documentation (Prisma schema file, NextAuth configuration, Stripe webhook handler) will reference this document for architectural context.
