# Ouroboros Manifold — Web Application Setup Log

> **Date:** April 23, 2026
> **Author:** Westley (Westopoli)
> **Purpose:** Implementation record for the webapp scaffold. Documents what was built, why, and how it's configured. Reference this when debugging auth flows, adding providers, changing infrastructure, or onboarding help.

---

## Architecture Decisions

Three design questions were resolved before implementation began. These are permanent decisions — changing them later means re-architecting.

### Database: Neon (serverless Postgres)

**Chosen over:** Supabase, Railway.

**Why:** Supabase bundles its own auth layer, which would conflict with NextAuth — two auth systems to reason about, plus temptation to use Supabase-specific features creates vendor lock-in. Railway has no free tier beyond trial and no built-in connection pooling (matters for serverless). Neon is serverless Postgres with a generous free tier (0.5 GB, 190 compute hours/month), scales to zero when idle, has built-in connection pooling, and strong Prisma support. No redundant features to ignore.

**Scale plan:** Neon free tier covers launch and early growth. Upgrade to Neon's paid tier if storage or compute limits are hit.

### Email: Resend (with AWS SES fallback)

**Chosen over:** SendGrid, AWS SES (for launch).

**Why:** Resend has 3,000 emails/month free tier, excellent developer experience, and native custom domain support (emails come from `noreply@ouroborosmanifold.com`, not a third-party domain — important for deliverability and user trust). SendGrid's free tier is rate-limited to 100/day and their deliverability reputation has declined. AWS SES is cheapest at volume ($0.10/1,000) but requires significant setup (IAM roles, sandbox escape) — overkill for a solo dev at launch.

**Scale plan:** Switch to AWS SES if email volume exceeds Resend's free/paid tier cost-effectively.

### Deployment: Single Vercel deployment

**Chosen over:** Separate Cloudflare Pages (static) + Vercel (app) deployments.

**Why:** One origin eliminates an entire category of cross-origin security concerns — no CORS configuration, no cookie scoping across subdomains, no dual security header auditing. Vercel's CDN handles static files well. The operational simplicity of one deploy pipeline far outweighs the minor inconvenience of coupled deploys for a solo developer. Can always split later if traffic justifies it.

---

## Technology Stack

| Layer | Technology | Version | Purpose |
|-------|-----------|---------|---------|
| Framework | Next.js | 16.2.4 | App Router, TypeScript, server components |
| Runtime | React | 19.2.5 | UI rendering |
| Language | TypeScript | 6.0.3 | Type safety |
| Database | Neon | — | Serverless Postgres |
| ORM | Prisma | 7.8.0 | Schema management, type-safe queries |
| Auth | NextAuth (Auth.js v5) | 5.0.0-beta.31 | OAuth + magic link, JWT sessions |
| Steam Auth | authjs-steam-provider | 1.0.0 | Steam OpenID 2.0 → Auth.js adapter |
| Payments | Stripe | 22.0.2 | Hosted checkout, subscription management |
| Email | Resend | 6.12.2 | Magic link delivery, transactional emails |
| Neon Driver | @neondatabase/serverless | 1.1.0 | WebSocket connection for serverless |
| Hosting | Vercel | — | Deployment, CDN, HTTPS |
| Domain | Cloudflare Registrar | — | Domain registration (in progress) |

### Known Dependency Issues

- **`authjs-steam-provider`** has a peer dependency on `next >=13 <16`, but we're on Next.js 16. The actual code is compatible — it's just HTTP requests and string parsing. Resolved with `.npmrc` containing `legacy-peer-deps=true`.
- **`next-auth@beta`** shows 6 moderate severity vulnerabilities in `npm audit`. These are known issues in the pre-release package. Do NOT run `npm audit fix --force` — it breaks the dependency tree. Will resolve when next-auth reaches stable release.

---

## Project Structure

```
ouroboros-manifold-scaffold/
├── .env                          ← Secrets (Prisma reads this)
├── .env.local                    ← Secrets (Next.js reads this, takes priority)
├── .env.example                  ← Template — never has real values
├── .gitignore
├── .npmrc                        ← legacy-peer-deps=true
├── next.config.ts                ← Security headers (HSTS, CSP, X-Frame-Options)
├── package.json
├── prisma.config.ts              ← Prisma 7 config (datasource URL)
├── tsconfig.json
├── prisma/
│   └── schema.prisma             ← Database schema (9 tables)
├── scripts/
│   └── generate-key.ts           ← CLI tool for access key generation
├── public/                       ← Static assets (empty, will hold marketing pages)
└── src/
    ├── middleware.ts              ← Route protection (needs rename to proxy.ts)
    ├── app/
    │   ├── layout.tsx             ← Root layout (fonts, theme script)
    │   ├── page.tsx               ← Placeholder home page
    │   ├── account/               ← (empty, will hold account dashboard)
    │   ├── library/               ← (empty, will hold authenticated era library)
    │   ├── redeem/                ← (empty, will hold key redemption page)
    │   └── api/
    │       ├── auth/[...nextauth]/route.ts  ← Auth route handler
    │       ├── entitlements/route.ts         ← GET user entitlements
    │       ├── checkout/
    │       │   ├── subscription/route.ts     ← POST create subscription checkout
    │       │   └── era/[eraId]/route.ts      ← POST create era purchase checkout
    │       ├── portal/route.ts              ← POST create Stripe billing portal
    │       ├── keys/redeem/route.ts          ← POST redeem access key
    │       ├── content/download/[eraId]/route.ts  ← GET signed download URL
    │       └── webhooks/stripe/route.ts     ← POST Stripe webhook handler
    └── lib/
        ├── auth.ts               ← NextAuth config (all 5 providers)
        ├── db.ts                 ← Prisma client singleton
        ├── entitlements.ts       ← Entitlement resolution logic
        ├── rate-limit.ts         ← Per-IP sliding window rate limiter
        └── stripe.ts             ← Stripe client singleton
```

---

## Database Schema

9 tables, all created in Neon via `npm run db:push`. Schema defined in `prisma/schema.prisma`.

| Table | Purpose | Key Fields |
|-------|---------|------------|
| `users` | User accounts | `id` (UUID), `email` (nullable — Steam-only users), `display_name`, `stripe_customer_id` |
| `accounts` | Provider links (NextAuth standard) | `user_id`, `provider`, `provider_account_id`. Unique on `(provider, provider_account_id)` |
| `sessions` | Active sessions | `session_token`, `user_id`, `expires` |
| `verification_tokens` | Magic link tokens | `identifier`, `token`, `expires`. Unique on `(identifier, token)` |
| `subscriptions` | Stripe subscriptions | `user_id` (unique — one per user), `stripe_subscription_id`, `status` (enum), `current_period_end` |
| `purchases` | One-time era pack buys | `user_id`, `era_id`, `stripe_payment_intent_id` (unique), `amount_cents` |
| `access_keys` | Promotional/distribution keys | `code` (unique), `key_type` (enum: permanent/time_limited/mission_limited), `scope` (JSONB), `redeemed_by`, `redeemed_at` |
| `steam_entitlements` | Verified Steam DLC ownership | `user_id`, `steam_app_id`, `era_id`. Unique on `(user_id, steam_app_id)` |
| `era_progress` | Per-era mastery tracking | `user_id`, `era_id`, `missions_completed`, `mastery_points`, `tier`. Unique on `(user_id, era_id)` |

### Prisma 7 Configuration

Prisma 7 moved the database URL out of `schema.prisma` and into `prisma.config.ts` (project root). The schema's `datasource` block has no `url` field — just `provider = "postgresql"`. The connection URL is loaded via dotenv in `prisma.config.ts`:

```ts
import "dotenv/config";
import { defineConfig, env } from "prisma/config";

export default defineConfig({
  schema: "prisma/schema.prisma",
  migrations: { path: "prisma/migrations" },
  datasource: { url: env("DATABASE_URL") },
});
```

The Prisma client (`src/lib/db.ts`) receives the URL via `datasourceUrl: process.env.DATABASE_URL`.

---

## Authentication

### Providers

Five authentication providers, all delegated identity (no passwords):

| Provider | Protocol | Email Provided | Auto-Link Policy |
|----------|----------|---------------|-----------------|
| Google | OAuth 2.0 | Yes (verified) | Auto-link on verified email match |
| Discord | OAuth 2.0 | Yes (if verified on Discord) | Auto-link only if Discord reports email as verified |
| Apple | OAuth 2.0 (Sign in with Apple) | Yes (always verified, may be private relay) | Auto-link (Apple always verifies) |
| Steam | OpenID 2.0 | **No** (synthetic email stripped) | **Never auto-link** |
| Email (Magic Link) | Email verification | Yes (by definition) | Auto-link (the email IS the verification) |

### Steam Provider — Security Details

Steam uses OpenID 2.0 (legacy protocol, not OAuth2). The `authjs-steam-provider` package handles the assertion exchange and profile enrichment via the Steam Web API. Critical security nuance:

**The provider generates a synthetic email** (`{steamid}@steamcommunity.com`) because Auth.js requires an email field internally. This is NOT a real email. If allowed to reach the database, it could:
- Pollute the user record with a fake email
- Accidentally trigger auto-link logic

**Solution:** The `signIn` callback in `src/lib/auth.ts` detects emails ending in `@steamcommunity.com` and strips them to `null` before they touch the database. Steam-only users have no email on record until they link another provider or add one manually. This matches the architecture doc's spec for Steam users.

**Request requirement:** The Steam provider needs the incoming HTTP `Request` object to validate the OpenID assertion parameters. The auth config is built per-request via `buildHandlers(req)` in the route handler, rather than exported as a static object.

### Session Configuration

| Setting | Value | Rationale |
|---------|-------|-----------|
| Strategy | JWT (stateless) | No server-side session store needed |
| Cookie name | `om-session` | Custom name for clarity |
| Cookie flags | HttpOnly, Secure (prod), SameSite=Lax | Prevents XSS theft, HTTPS-only in prod, allows OAuth redirects |
| Max age | 30 days | Web sessions |
| Sign-in page | `/account` | Custom page (not NextAuth default) |

### Account Linking Policy

Auto-link on verified email is the core security policy. The linking rules are enforced in the `signIn` callback:

1. Steam → never auto-link (synthetic email stripped to null)
2. Google → auto-link if Google reports `email_verified: true`
3. Discord → auto-link if Discord reports `verified: true`
4. Apple → always auto-link (Apple always verifies email)
5. Magic link → always auto-link (the email IS the verification)
6. Any provider with unverified email → block auto-link, user must link manually from account settings

---

## Security Architecture

### Attack Surface Minimization (by design)

- **No passwords.** All identity is delegated to trusted providers. No credential storage, no hashing, no comparison logic to get wrong.
- **No credit card handling.** Stripe-hosted checkout pages handle all payment data. The application never sees card numbers, CVVs, or any PCI-scoped data. PCI scope is eliminated entirely.
- **No admin dashboard.** Access keys are generated via CLI script (`scripts/generate-key.ts`). No web-exposed admin surface to attack.

### Security Headers (next.config.ts)

Applied to all routes:

| Header | Value | Purpose |
|--------|-------|---------|
| X-Content-Type-Options | `nosniff` | Prevent MIME-type sniffing |
| X-Frame-Options | `DENY` | Prevent clickjacking |
| Referrer-Policy | `strict-origin-when-cross-origin` | Control referrer leakage |
| Strict-Transport-Security | `max-age=63072000; includeSubDomains; preload` | Enforce HTTPS |
| Permissions-Policy | `camera=(), microphone=(), geolocation=(), interest-cohort=()` | Disable unnecessary browser APIs |
| Content-Security-Policy | Restricts script/style/font/connect/frame sources | Prevent XSS, data exfiltration |

### Rate Limiting (src/lib/rate-limit.ts)

In-memory sliding window rate limiter. Four tiers:

| Tier | Limit | Window | Applied To |
|------|-------|--------|-----------|
| Authenticated | 60 req | 1 min | All authenticated API routes |
| Unauthenticated | 10 req | 1 min | Sign-in, magic link request |
| Key redemption | 5 req | 1 min | `/api/keys/redeem` — extra restrictive to prevent brute force |
| Magic link | 3 req | 10 min | Per-email rate limit on magic link sends |

**Scale plan:** Replace with Redis (Upstash) when traffic exceeds single-server memory.

### Route Protection (src/middleware.ts)

Middleware checks for session cookie presence on protected paths. Protected paths get 401 (API routes) or redirect to `/account` (page routes) when no session cookie exists. Full JWT validation happens in the route handler via `auth()`.

**Note:** Next.js 16 deprecated the "middleware" file convention in favor of "proxy". The file needs to be renamed from `middleware.ts` to `proxy.ts`. Both still work; the rename is cosmetic for now.

### Stripe Webhook Security

- Every incoming webhook is verified via `stripe.webhooks.constructEvent()` with the webhook signing secret
- Rejects requests with missing or invalid signatures
- All handlers are idempotent — safe to receive the same event multiple times
- The webhook route skips session/CSRF middleware (Stripe can't send cookies)

### Access Key Redemption Security

- Extra-restrictive rate limiting (5/min per IP)
- Atomic redemption via Prisma `$transaction` (prevents race conditions)
- Constant-time error responses (same error for "key doesn't exist" and "key already redeemed" — prevents enumeration)
- Input sanitization: alphanumeric only, length bounds checked
- Key codes generated via `crypto.randomBytes` (CSPRNG), not `Math.random`

---

## Entitlement Resolution

The core business logic. Given a user ID, determines which eras they can access by combining five sources in priority order:

1. **Free tier** — always includes `"roman"`
2. **Active subscription** — grants all eras (short-circuits remaining checks)
3. **One-time purchases** — permanent per-era access
4. **Access keys** — type-dependent:
   - `permanent` → adds eras permanently
   - `time_limited` → adds eras if within `durationDays` of redemption
   - `mission_limited` → adds eras if `missionCount > 0`
5. **Steam DLC ownership** — adds eras verified via Steam API

All five sources are fetched in parallel (`Promise.all`) for a single DB round trip. The Godot client and account dashboard both consume the `/api/entitlements` endpoint.

---

## API Routes

| Route | Method | Auth | Purpose |
|-------|--------|------|---------|
| `/api/auth/*` | GET/POST | — | NextAuth handlers (sign-in, callbacks, session) |
| `/api/entitlements` | GET | Required | Returns user's full entitlement set |
| `/api/checkout/subscription` | POST | Required | Creates Stripe subscription checkout session |
| `/api/checkout/era/[eraId]` | POST | Required | Creates Stripe era purchase checkout session |
| `/api/portal` | POST | Required | Creates Stripe customer portal session |
| `/api/keys/redeem` | POST | Required | Redeems an access key |
| `/api/content/download/[eraId]` | GET | Required | Generates signed R2 download URL (stubbed) |
| `/api/webhooks/stripe` | POST | Stripe signature | Handles Stripe lifecycle events |

---

## Environment Variables

Two files: `.env` (Prisma reads this) and `.env.local` (Next.js reads this, takes priority). Both must contain `DATABASE_URL`. When adding or changing secrets, update both files.

| Variable | Set? | Source |
|----------|------|--------|
| `DATABASE_URL` | ✅ | Neon dashboard → Connection Details |
| `NEXTAUTH_SECRET` | ✅ | Generated via `openssl rand -base64 32` |
| `NEXTAUTH_URL` | ✅ | `http://localhost:3000` (change to real domain on deploy) |
| `GOOGLE_CLIENT_ID` | ❌ | Google Cloud Console → Credentials |
| `GOOGLE_CLIENT_SECRET` | ❌ | Google Cloud Console → Credentials |
| `DISCORD_CLIENT_ID` | ❌ | Discord Developer Portal |
| `DISCORD_CLIENT_SECRET` | ❌ | Discord Developer Portal |
| `APPLE_CLIENT_ID` | ❌ | Apple Developer Console |
| `APPLE_CLIENT_SECRET` | ❌ | Apple Developer Console |
| `STEAM_API_KEY` | ❌ | steamcommunity.com/dev/apikey |
| `RESEND_API_KEY` | ❌ | Resend dashboard |
| `EMAIL_FROM` | ❌ | `noreply@ouroborosmanifold.com` |
| `STRIPE_SECRET_KEY` | ❌ | Stripe dashboard (test mode) |
| `STRIPE_WEBHOOK_SECRET` | ❌ | Stripe dashboard → Webhooks |
| `STRIPE_PUBLISHABLE_KEY` | ❌ | Stripe dashboard |
| `R2_ACCESS_KEY_ID` | ❌ | Cloudflare R2 (future) |
| `R2_SECRET_ACCESS_KEY` | ❌ | Cloudflare R2 (future) |
| `R2_BUCKET` | ❌ | Cloudflare R2 (future) |
| `R2_ENDPOINT` | ❌ | Cloudflare R2 (future) |

---

## NPM Scripts

| Command | Purpose |
|---------|---------|
| `npm run dev` | Start development server at localhost:3000 |
| `npm run build` | Production build |
| `npm run start` | Start production server |
| `npm run lint` | Run ESLint |
| `npm run db:generate` | Generate Prisma client from schema |
| `npm run db:push` | Push schema changes to database (no migration history) |
| `npm run db:migrate` | Create and apply migration (with history) |
| `npm run db:studio` | Open Prisma Studio (database GUI) |
| `npm run generate-key` | Generate access keys via CLI |

---

## Costs

All services are free at current scale. No monthly fees until the game has paying users.

| Service | Free Tier | Paid Trigger |
|---------|-----------|-------------|
| Vercel | Hobby plan, custom domain, HTTPS, 100GB bandwidth | Team features or bandwidth exceeded |
| Neon | 0.5 GB storage, 190 compute hours/month | Storage or compute exceeded |
| Resend | 3,000 emails/month | Monthly email volume exceeded |
| Stripe | $0 until transactions | 2.9% + $0.30 per transaction |
| Domain | ~$10-15/year (Cloudflare Registrar) | Immediate (only upfront cost) |

---

## What's Not Yet Built

- [ ] Google OAuth credentials configured and tested
- [ ] Static HTML pages integrated into Next.js project
- [ ] Stripe test mode configured, webhook flow verified
- [ ] Vercel deployment with domain connected
- [ ] Mobile navigation (hamburger menu)
- [ ] OG meta tags on article pages
- [ ] Steam provider credentials configured and tested
- [ ] Discord, Apple provider credentials configured
- [ ] Resend configured with custom domain
- [ ] R2 content delivery (signed URLs for era pack downloads)
- [ ] Account dashboard page (authenticated)
- [ ] Authenticated era library page
- [ ] Key redemption page
- [ ] Rename `middleware.ts` → `proxy.ts` (Next.js 16 convention)
