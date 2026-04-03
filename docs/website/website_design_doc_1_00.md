# Ouroboros Manifold — Website Design Document

> **This is the single source of truth for the website's design.** All visual direction, page architecture, content strategy, and infrastructure decisions live here. Implementation details (CSS values, component code, API schemas) belong in separate technical docs that reference this file. If something in another doc conflicts with this file, this file wins.
>
> **MODIFICATION RULE: This document is append-only unless Westley explicitly approves a deletion.** AI sessions may add new sections, expand existing sections, and resolve open questions by writing answers into the appropriate section. AI sessions may NOT delete, overwrite, or replace existing decided content. If new information conflicts with existing content, flag the conflict for Westley to resolve — do not silently overwrite.
>
> **RELATIONSHIP TO THE GAME BIBLE:** This document governs the website. The game bible (`game_bible_X_XX.md`) governs the game. Where this document references game mechanics, monetization structure, or distribution infrastructure, the game bible is authoritative. This document defines how those concepts are presented on the web — visual design, page layout, content structure, user flows. If the game bible's monetization model changes, this document's commerce sections update to match.
>
> **Last updated:** April 1, 2026 (v1.00) — Initial document. Site architecture, visual direction, page structure, content strategy, commerce architecture, infrastructure plan, and build sequence established. Astro vs. plain HTML resolved: plain HTML/CSS/JS, no build tools.

---

## Table of Contents

1. [Vision and Identity](#vision-and-identity) — What the site is, who it's for, what it communicates
2. [Visual Direction](#visual-direction) — Aesthetic philosophy, typography, color, spatial composition, motion
3. [Site Architecture](#site-architecture) — Navigation model, page hierarchy, URL structure
4. [Page 1 — Landing](#page-1--landing) — Hero, pitch panels, skeleton/skin, chronicle teaser, article preview, footer
5. [Page 2 — The Game](#page-2--the-game) — Deep pitch, blue ocean pillars, simulation philosophy, generational structure
6. [Page 3 — Era Library](#page-3--era-library) — Era catalog, preview content, purchase flow, subscription CTA
7. [Page 4 — Account](#page-4--account) — Registration, login, subscription management, purchase history, entitlements
8. [Page 5 — Articles](#page-5--articles) — Index, individual article pages, content strategy, editorial guidelines
9. [Content Strategy](#content-strategy) — Voice, target audience, article pipeline, Reddit integration
10. [Commerce Architecture](#commerce-architecture) — Stripe integration, subscription flow, era pack purchases, entitlement system
11. [Infrastructure](#infrastructure) — Hosting, content delivery, cost projections, technology decisions
12. [Build Sequence](#build-sequence) — Phased implementation plan, dependencies, milestones
13. [Open Design Questions](#open-design-questions) — Unresolved decisions
14. [Document Maintenance](#document-maintenance) — Rules, workflow, governance

---

## Vision and Identity

### What the Site Is

The Ouroboros Manifold website is the game's home on the open web — independent of Steam, independent of any platform. It serves four purposes in priority order:

1. **Marketing and conversion.** Convince strategy game players that this game is different and worth their attention. The landing page is the top of the funnel. Every visitor should leave understanding what makes this game unlike anything else on the market.
2. **Commerce.** Facilitate subscription purchases, era pack sales, and skin purchases through Stripe — bypassing Steam's 30% cut on ongoing content. The website is the high-margin sales channel described in the game bible's hybrid distribution model.
3. **Content and trust.** Host design articles, development logs, and editorial content that establishes credibility. A solo dev asking players to subscribe needs to demonstrate depth of thought and commitment. The articles are proof of quality.
4. **Account management.** Let players manage their subscription, view their entitlements, and access purchase history. This is invisible when it works correctly — the player never thinks about the plumbing.

### Who It's For

The target audience is **strategy game players who are dissatisfied with the current landscape.** These are people who have played Stellaris, Crusader Kings, Total War, Civilization, and Age of Empires — and who feel that something is missing. They are systems thinkers who enjoy understanding how mechanics interact. They read patch notes. They watch design analysis videos. They appreciate depth over spectacle.

Within this audience, the highest-value segment is **the lapsed strategy player** — someone who played hundreds of hours of Paradox or Firaxis games, got burned out on the formula, and is waiting for something genuinely new. The blue ocean positioning (commander not king, generational chapters, stochastic simulation, the tragedy of understanding) speaks directly to this person. They've felt the limitations of the existing genre. They just didn't know an alternative was possible.

Secondary audience: **the Foundation reader.** People who love Asimov's Foundation series and wish someone would make a game that captures that feeling — vast civilizational arcs experienced from inside, not above. This audience may not be traditional strategy gamers, but the narrative hook is powerful enough to pull them in.

### What the Site Communicates

The site communicates three things, in this order:

1. **This game is genuinely different.** Not a Stellaris clone, not a Total War fork, not another 4X. Something new. The blue ocean pillars are the proof.
2. **This developer knows what they're building.** The design articles, the depth of the pitch, the quality of the writing — all signal that the game is being built with intention and expertise, not thrown together.
3. **The value proposition is clear and fair.** Free version to try, subscription for full access, individual era packs if you prefer. No predatory monetization, no pay-to-win, no hidden costs. The skeleton/skin model is transparent and player-friendly.

---

## Visual Direction

### Aesthetic Philosophy

**Apple-minimal. The game is the spectacle, not the website.** The site's visual identity is built on restraint, precision, and generous space. Every element earns its place. Nothing decorative exists without purpose. The design should feel expensive and confident — the visual equivalent of speaking quietly in a room where everyone else is shouting.

This philosophy serves a strategic purpose: when game visuals (screenshots, trailers, concept art, in-engine footage) are placed on the site, they become the undeniable focal point. The site's restraint makes the game's visuals pop. A busy, effects-heavy website would compete with the game for attention. A minimal site frames the game like a gallery frames a painting.

**The site must be designed expecting visuals.** Layouts, spacing, and emphasis are built around the assumption that compelling game imagery exists. Placeholder images during development are stand-ins, not design constraints — the layout should feel slightly incomplete without real visuals, because the visuals are the point.

### Typography

Typography carries the design in the absence of visual clutter. Two typefaces maximum:

**Display typeface** — used for the game title, section headers, and hero text. This must be distinctive, memorable, and tonally aligned with the game's identity: elegiac, weighty, civilizational. Not generic sans-serif. Not sci-fi cliché. Something that feels like it belongs on the cover of a serious novel about the rise and fall of empires. Serif or semi-serif preferred — it signals gravitas without being stuffy. Candidates should be evaluated against the criterion: "does this font feel like it could title an Asimov novel?"

**Body typeface** — used for all running text, article content, UI labels, and navigation. Highly legible at body sizes, clean at small sizes, and tonally neutral enough to disappear. The body font's job is to not be noticed — it should read effortlessly so the content does the work. A refined sans-serif or humanist sans that pairs well with the display serif without competing.

**Typographic scale:** Large. Headers should be commanding — not timid. Body text should be generous (16–18px minimum on desktop). Line height should be open enough to breathe. The overall feeling should be "editorial luxury" — closer to a Monocle magazine spread than a SaaS landing page.

### Color

**Restrained palette, high contrast.** The site operates in a narrow color range:

**Primary surface:** Near-white or very light warm gray. Not pure white (#fff) — pure white is clinical. A warm off-white creates subtle depth without being noticeable.

**Primary text:** Near-black. Not pure black (#000) — a very dark warm gray reduces eye strain and pairs with the warm surface.

**Accent color:** One. Used sparingly for CTAs, interactive elements, and moments of emphasis. The accent should feel intentional — not decorative. It appears on buttons, links, and occasional typographic highlights. Nothing else. The accent color should connect to the game's identity without being literally "space blue" or "sci-fi green" — subtlety over cliché.

**Visual content framing:** When game imagery appears, the site's neutral palette ensures maximum visual impact. Screenshots and trailers are the only sources of rich color on the page. This is by design — the game's visuals are the most compelling content the site has, and the palette ensures they dominate.

**Dark mode:** Included from v1 via a three-state toggle: Auto, Light, Dark. Auto reads the user's system `prefers-color-scheme` setting and applies the matching theme automatically. The user can override to Light or Dark explicitly. The preference is persisted in `localStorage` so it survives page reloads and navigation. The toggle sits in the nav bar next to the logo — three small buttons, the active one visually highlighted. The dark theme is a true inversion: dark warm surface (#111110), light warm text (#E8E6E1), and a slightly brighter accent gold (#D4A017) for contrast. The inverted sections (skeleton/skin, footer) adjust to be even darker than the surface in dark mode, maintaining the visual rhythm. All colors are defined as CSS custom variables on `[data-theme]` selectors, so the theme switch is a single attribute change with smooth CSS transitions.

### Spatial Composition

**Generous negative space.** The site should feel like it has room to breathe. Sections are separated by significant vertical space. Content blocks don't crowd each other. The scroll experience should feel unhurried — each section gets its moment before the next begins.

**Full-width visual moments.** Game imagery (hero shots, screenshots, trailer embeds) breaks out of the content column to fill the viewport width. This creates rhythm: contained text sections alternate with expansive visual moments. The text column is narrow enough for comfortable reading (max ~720px for body text, ~1200px for wider layout sections). Visuals fill edge to edge.

**Asymmetry where it serves the content.** Not every section is centered. The pitch panels can alternate image-left/text-right and image-right/text-left. The skeleton/skin section can use an off-center split. Controlled asymmetry creates visual interest without chaos.

### Motion and Interaction

**Minimal, purposeful animation.** No parallax scrolling. No floating particles. No background video loops. Motion is reserved for:

- **Scroll-triggered reveals.** Content sections fade or slide into view as the user scrolls to them. Subtle — opacity and slight vertical translation, not dramatic fly-ins. The effect should feel like the page is breathing, not performing.
- **Hover states on interactive elements.** Buttons, article cards, and era pack cards respond to hover with restrained transitions — color shift, subtle scale, underline animation. Enough to confirm interactivity, not enough to distract.
- **Page transitions.** If technically feasible, smooth transitions between pages (a brief fade or slide) rather than hard cuts. This contributes to the feeling of a cohesive experience rather than separate documents.

**No animation for animation's sake.** Every motion must answer the question "what does this help the user understand or feel?" If the answer is "nothing, it just looks cool," cut it.

---

## Site Architecture

### Navigation Model

The site uses **separate pages with a persistent top navigation bar.** Clicking a nav link loads a new page. The landing page scrolls through its own sections, but "The Game," "Era Library," "Account," and "Articles" are distinct pages with distinct URLs.

**Why separate pages, not a single-page scroll:**
- Articles need individual, shareable URLs for Reddit posts and external linking.
- The Era Library / store needs its own distinct space — mixing commerce into a marketing scroll creates friction and tonal confusion.
- The landing page should be tight and focused. A 20-screen scroll buries the CTA and exhausts attention.
- SEO benefits from distinct pages with targeted content.

### Navigation Bar

Persistent across all pages. Fixed to the top of the viewport (becomes sticky on scroll). Contains:

**Left:** Game logo / wordmark (links to landing page).

**Right:** Navigation links in this order: **The Game** · **Era Library** · **Account** · **Articles**

This ordering reflects the user journey priority: learn about the game → see what's available → manage your account → read deeper content. "Articles" is last in the nav because it's the deepest engagement layer — but paradoxically may be the most common entry point (via Reddit links), so it must be prominent enough to find.

**CTA button:** A single call-to-action button in the nav bar, visually distinct from the navigation links. Pre-launch: "Join Waitlist" or "Join Discord." Post-launch: "Subscribe" or "Play Free." This button is the persistent conversion opportunity on every page.

### URL Structure

```
ouroborosmanifold.com/                  → Landing page
ouroborosmanifold.com/the-game          → Deep pitch page
ouroborosmanifold.com/era-library       → Era catalog and store
ouroborosmanifold.com/account           → Account management (login, subscription, history)
ouroborosmanifold.com/articles          → Article index
ouroborosmanifold.com/articles/[slug]   → Individual article page
```

Clean, human-readable, no trailing slashes. Article slugs are derived from article titles (lowercase, hyphenated).

---

## Page 1 — Landing

The landing page is the conversion funnel. Every first-time visitor arrives here (unless they came via an article link). The page scrolls through six sections, each with a distinct job:

### Section 1 — Hero

**Job:** Stop the scroll. Communicate what this is in under 5 seconds.

**Layout:** Full-viewport height. Game title large and centered (display typeface). One-line pitch beneath the title. A dominant visual behind or below the title — this is where the best screenshot, key art, or trailer thumbnail lives. When real visuals exist, this image should be arresting. Single CTA button below the pitch line.

**The one-liner:** Must communicate the game's identity and blue ocean position in one sentence. It should make a strategy gamer stop and think "wait, what?" Current direction to refine — needs to capture: one game engine + infinite era settings + a world that doesn't revolve around you. The one-liner is an open design question (see Open Design Questions section).

**CTA:** Pre-launch: "Join the Waitlist" (email capture) or "Join Discord." Post-launch: "Play Free on Steam" (primary) with a secondary "Subscribe" link. The CTA must be above the fold on all screen sizes.

### Section 2 — The Pitch Panels

**Job:** Explain what makes this game different in three beats. This is the "why should I care" section.

**Layout:** Three panels, each containing a heading, a short paragraph (2–3 sentences max), and a supporting visual. Panels can stack vertically on mobile or arrange in a staggered layout on desktop (alternating image/text alignment). Each panel represents one blue ocean differentiator:

**Panel 1 — "Commander, Not King."** You don't control a civilization. You command a task force inside one. The world has its own plans. Your job is to execute a mission in a world that doesn't revolve around you.

**Panel 2 — "Generations, Not Campaigns."** Each mission is a chapter. Between chapters, decades or centuries pass. The world evolves through the simulation. You return as someone new — a descendant, a successor — in a world shaped by what you did before.

**Panel 3 — "A Living, Stochastic World."** The simulation underneath is genuinely uncertain. Multiple forces compete every tick. You can read the currents, make the right call, and still face outcomes you couldn't prevent. Mastery means understanding why, not always winning.

Each panel's visual should eventually show an in-game moment that embodies the concept: a tactical mission view for "Commander," a chronicle scroll for "Generations," a world map with faction territories shifting for "Living World."

### Section 3 — The Skeleton/Skin Story

**Job:** Explain the expansion model and "one game, infinite settings" value proposition.

**Layout:** A visual section showing the abstract engine concept on one side and a cascade of era themes on the other. The engine side could be a minimal diagram or abstract representation of the simulation. The era side shows a grid or cascade of era identities — Medieval, Sci-Fi, Roman, WW2, Age of Sail, Feudal Japan, etc. — each represented by a small visual card or icon with the era name.

**Copy:** Short and punchy. The message is: the engine is era-neutral. Every era plays the same deep game with different aesthetics. You learn the mechanics once. The eras are infinite. This is the "one game, infinite settings" beat from the game bible's marketing implications section.

This section primes the visitor for the subscription model without explicitly mentioning price. The goal is to make them think "I want access to ALL of those" before they ever see a dollar figure.

### Section 4 — The Chronicle Teaser

**Job:** Show, don't tell. Demonstrate emergent narrative with an example.

**Layout:** A styled block of text — a fake chronicle scroll entry — presented as if the player is reading it in-game. This should feel like a page from a historical record. The visual treatment should be distinct from the rest of the page — perhaps a slightly different background, a border treatment, or a different typeface — to signal "this is from the game."

**Content:** A short (3–5 sentence) chronicle entry that demonstrates the game's emergent storytelling. It should reference named characters, specific events, consequences from a previous chapter, and the passage of time. The entry should make someone think "this story emerged from gameplay? I want to experience that." Example beats: a descendant inheriting a crisis their ancestor caused, a frontier that was saved three generations ago now facing a new threat, a political rival's lineage still holding a grudge from a decision made 200 years ago.

The chronicle teaser is one of the most powerful marketing tools on the site. It translates the simulation's mechanical depth into something emotionally resonant. This is the "Foundation feeling" made tangible.

### Section 5 — Articles Preview

**Job:** Tee up the blog section. Show that there's depth behind the pitch.

**Layout:** 2–3 article cards in a row (or stacked on mobile). Each card shows: article title, a header image, publication date, and a 1–2 sentence excerpt or subtitle. Clicking a card navigates to the full article page.

**Content:** The most recent or most compelling articles. These are the same articles being posted to Reddit — seeing them on the official site after clicking through from a Reddit discussion reinforces credibility.

### Section 6 — Footer

**Job:** Capture remaining interest. Provide essential links.

**Layout:** Full-width, visually distinct from the page content (darker background or subtle separation). Contains:

- **Mailing list signup.** Email input + subscribe button. Short pitch: "Get notified when the game launches" or similar. This is the bottom-of-funnel capture for visitors who scrolled all the way down but aren't ready to join Discord.
- **Social links.** Discord, Reddit community, Twitter/X, YouTube (for eventual trailers/devlogs). Icons only, not text links.
- **Legal links.** Privacy policy, terms of service. Required for Stripe integration and GDPR compliance.
- **Copyright notice.**

---

## Page 2 — The Game

### Purpose

The deep pitch for visitors who are already interested and want to understand the game fully. This is the page linked when someone asks "what IS this game?" It expands on the landing page's three-panel pitch with full explanations of each blue ocean pillar.

### Structure

A long-form scroll page with six sections, one per blue ocean differentiator from the game bible:

**1. Genuinely Stochastic Simulation.** The world has its own probability space. You're not playing against scripted AI or deterministic systems. The System Dynamics model with stochastic event chains produces outcomes that are genuinely uncertain — not random, but emergent from competing forces. This section explains what "stochastic" means in plain language and why it matters for gameplay. Supporting visual: a diagram or animation showing how the simulation produces emergent outcomes.

**2. Generational Chapter Structure.** You're not one persistent character or one persistent empire. You're a series of people inside a civilization that changes around you. Each mission is a chapter. Between chapters, time jumps forward. The world evolves. You return as someone new. This section explains the chapter/cycle structure and what carries over between generations. Supporting visual: a timeline showing chapters, time jumps, and the changing world.

**3. Commander, Not King.** You don't control everything. You control a task force on a mission, and the civilization has its own plans. This section explains the mission structure — the player receives a briefing, commands a force, and operates within a world that has its own momentum. Supporting visual: a mission briefing screen or tactical view.

**4. AI-Generated Content.** Every playthrough is contextually unique. The library pipeline generates mission briefings, chronicle entries, unit flavor, and narrative content that responds to the simulation's state. No two playthroughs read the same story. This section explains how AI integration creates variety without runtime dependencies. Supporting visual: examples of generated content that differ based on different simulation states.

**5. The Tragedy of Understanding.** You can read the system, master the patterns, and still face outcomes you can't prevent. Mastery means you understand WHY you lost, not that you always win. This section explains the emotional core of the game — the Foundation feeling. Why this is more satisfying than a game you can "solve." Supporting visual: a chronicle entry showing a well-played mission that still led to unexpected consequences.

**6. Cyclic Civilizational Arcs.** The game loops through expansion, consolidation, conflict, overextension, and fragmentation. Each cycle carries the scars and ruins of the last. The Ouroboros isn't a name — it's the structure. This section explains the civilizational lifecycle and how each playthrough produces a different arc. Supporting visual: a world map showing territorial change over time.

Each section follows the same layout pattern: heading, 2–3 paragraphs of explanation, a full-width visual. The rhythm is text → visual → text → visual. Consistent but not monotonous.

### Tone

Confident and specific. Not hype-speak, not vague promises. Every claim is backed by a concrete mechanical explanation. The tone should feel like a designer explaining their craft to a smart audience — the same tone as the design articles. Strategy gamers can smell bullshit. Respect their intelligence.

---

## Page 3 — Era Library

### Purpose

The web-facing version of the in-game Era Library described in the game bible. This is where visitors browse the era catalog, preview expansion content, and — post-launch — purchase era packs and manage their subscription.

### Pre-Launch State

Before the commerce system is live, this page serves as a **catalog and wishlist.** It shows the era concept grid — all planned and available eras with thematic descriptions, visual previews, and status indicators (Available, Coming Soon, In Development). No purchase buttons, no price display. The goal is to make visitors think "I want all of these" and convert them to the mailing list or Discord.

### Post-Launch State

The full storefront experience. Each era card expands to show:

- Thematic description (2–3 sentences capturing the era's flavor).
- Sample chronicle prose in the era's voice.
- Visual style preview (concept art, in-game screenshots in this era's aesthetic).
- Unit roster preview (the six unit types rendered in the era's visual style).
- Price and purchase button (for individual era pack purchase).
- "Included with subscription" badge (for eras included in the active subscription tier).

**Subscription CTA:** Prominently placed on this page — not aggressive, but clearly visible. The framing is: "Why buy eras one at a time? Subscribe and get them all." The subscription value proposition is most compelling when the player is looking at a catalog of 10+ eras and doing the mental math on buying them individually.

### Layout

A grid of era cards. Each card is a visual tile with the era name, a representative image, and a brief tagline. Cards have hover states that reveal additional information. Clicking a card opens a detail view (either a modal or a dedicated sub-page) with the full preview content.

The grid should feel like browsing a curated bookstore — inviting exploration, not pushing transactions. Visual density is moderate — enough cards visible to convey the breadth of the catalog, enough spacing that each era feels like a distinct identity.

---

## Page 4 — Account

### Purpose

Player account management. Registration, login, subscription status, purchase history, and entitlement overview.

### Pre-Launch State

Not built. The nav link either doesn't appear pre-launch or redirects to a "Coming Soon" page with a mailing list signup.

### Post-Launch State

**Registration / Login:** Simple form — email and password. OAuth options (Google, Discord) if feasible. No username required for account creation — the account is a billing identity, not a social identity.

**Subscription Dashboard:** Current subscription status (active, canceled, past due). Next billing date. Payment method on file. Upgrade/downgrade options (if multiple subscription tiers exist). Cancel button with retention flow (a brief "are you sure?" with an option to pause instead of cancel).

**Purchase History:** List of all purchases — subscription payments, individual era pack purchases, skin purchases. Dates, amounts, receipt links.

**Entitlement Overview:** A grid showing all owned content — which eras are owned (purchased or included via subscription), which skins are owned. This mirrors the in-game Era Library's ownership state and serves as a web-accessible record.

**Account Settings:** Email, password, payment method updates. Account deletion option (GDPR compliance).

### Design

Functional and clean. This is not a marketing page — it's a utility page. The design should be unobtrusive and efficient. No selling on this page. The player is already a customer; respect their time.

---

## Page 5 — Articles

### Purpose

The content marketing engine. Design articles, development logs, and editorial content that establishes credibility, attracts organic search traffic, and provides shareable content for Reddit and social media.

### Article Index Page

**Layout:** A clean list or card grid of all published articles, ordered by publication date (most recent first). Each entry shows: article title, header image, publication date, estimated read time, and a 1–2 sentence excerpt. Filtering by category/tag is available but not prominent — the default chronological view is sufficient for most visitors.

**Categories:** Broad, not granular. Three to start: **Design** (game design methodology, mechanical deep dives), **Development** (technical progress, implementation stories), **Insights** (industry analysis, the "why" behind decisions). More categories can be added as the content library grows, but resist over-categorizing early — it creates empty shelves.

### Individual Article Page

**Layout:** Full editorial treatment. A full-width header image at the top. Article title in display typeface. Publication date and estimated read time below the title. Body content in the body typeface at a comfortable reading width (~680–720px). Generous line height and paragraph spacing.

**Content formatting:** Articles support standard markdown elements — headers, paragraphs, block quotes, inline code, images, and embedded media. No sidebar. No related articles cluttering the reading experience. At the bottom of the article: author attribution, a "next article" / "previous article" navigation link, and a CTA (mailing list signup or Discord link).

**Shareability:** Each article has a clean, memorable URL (`/articles/the-stochastic-simulation-philosophy`). Open Graph meta tags for attractive social media previews (title, description, header image). This is critical for Reddit — when someone shares an article link, the preview card must look professional and compelling.

### Editorial Voice

The articles are written in the same voice as the game bible — confident, specific, technically precise but accessible. Not academic, not casual. The tone of a designer explaining their craft to a peer who happens to be interested. No hype-speak, no buzzwords, no "we're so excited to announce." State what is, explain why, show the work.

---

## Content Strategy

### Target Audience Mapping

**Reddit communities for distribution:** r/gamedesign (design methodology articles), r/indiegaming (development milestones), r/strategygames and r/4Xgaming (game pitch and blue ocean positioning), r/RealTimeStrategy (combat design articles), r/scifi and r/asimov (the Foundation connection, narrative design). Each community has different norms and expectations — articles should be tailored or titled to fit the community's interests, not cross-posted identically.

**Content-first marketing.** The articles are the marketing. Not ads, not paid promotion, not influencer deals. Every article is a standalone piece of value — someone should be able to read it, find it interesting, and share it even if they never buy the game. The game's existence is the context, not the pitch. Articles that feel like advertisements will be downvoted on Reddit and ignored everywhere else.

### Article Pipeline — Foundational Content

The following articles should exist before the site goes live, listed in rough priority order:

1. **The article that already exists.** (First published piece, topic TBD by Westley.)
2. **The Stochastic Simulation Philosophy.** Why genuine uncertainty makes better strategy games than scripted AI. The System Dynamics + event chain architecture explained for a lay audience. Why this approach was chosen over alternatives.
3. **Commander, Not King: A Different Kind of Strategy Game.** The blue ocean pitch as a standalone essay. What's missing from Stellaris/CK/TW/Civ and what this game does instead.
4. **One Game, Infinite Settings: The Skeleton/Skin Architecture.** The era-agnostic design as a deliberate commercial and creative decision. How the engine separates mechanics from theme. Why this produces better expansions than traditional DLC.
5. **The Generational Problem.** Why generational gameplay is hard, how most games fail at it, and how the chapter/cycle/chronicle structure solves it.

Each article serves a dual purpose: it's interesting content for its target Reddit community AND it's a permanent marketing asset on the website.

### Ongoing Content Cadence

Post-launch target: 1–2 articles per month. Topics emerge naturally from development — every significant design decision, every interesting implementation challenge, every mechanical deep dive is a potential article. The bible's resolved design questions are a goldmine of article material. Each one represents a problem that was identified, analyzed, and solved — exactly the kind of content strategy game players love reading.

---

## Commerce Architecture

### Relationship to Game Bible

This section implements the monetization model and distribution infrastructure defined in the game bible's "Expansion Packs and Monetization" section. The game bible is authoritative on the commercial model (subscription pricing, era pack pricing, skin pricing, the hybrid Steam + direct model, the platform-agnostic entitlement principle). This section defines how that model manifests on the website.

### Payment Processing — Stripe

All direct purchases (not through Steam) are processed through **Stripe.** Stripe handles: recurring subscription billing, one-time era pack purchases, unit skin micro-transactions, payment method storage, receipt generation, and tax calculation.

**Why Stripe:** Industry-standard payment processing at ~3% per transaction versus Steam's 30%. Stripe handles PCI compliance, fraud detection, international payments, and subscription lifecycle management. No monthly fee — Stripe charges per transaction only. For a solo dev, Stripe eliminates the need to handle sensitive payment data directly.

### Subscription Flow

1. Player clicks "Subscribe" (from the landing page CTA, Era Library page, or in-game Era Library).
2. Redirected to a Stripe Checkout session (Stripe-hosted payment page — no custom payment form needed, which eliminates PCI scope).
3. Player enters payment details on Stripe's page.
4. Stripe processes payment, creates a subscription record, and sends a webhook to the backend.
5. Backend receives the webhook, creates/updates the player's entitlement record in the database.
6. Player is redirected back to the website (or the game detects the new entitlement on next launch).

**Subscription management** (cancel, pause, update payment method) happens through Stripe's Customer Portal — a Stripe-hosted page that handles all subscription lifecycle actions. This eliminates the need to build custom subscription management UI for v1. The Account page links to the Customer Portal.

### Era Pack Purchase Flow

1. Player clicks "Buy" on an era pack card (from the Era Library page or in-game).
2. Redirected to a Stripe Checkout session for a one-time payment.
3. Stripe processes payment and sends a webhook.
4. Backend records the era entitlement in the database.
5. Game client downloads the era pack content from Cloudflare R2 on next launch.

### Entitlement System

The backend maintains a **single source of truth for entitlements:** a database table mapping player IDs to owned content. The game client queries this on launch to determine what content to unlock.

**Entitlement sources:** An era can be owned through three channels — active subscription (includes a set of eras), individual direct purchase (via Stripe), or Steam DLC purchase (detected via Steam API). The entitlement system resolves all three into a single unified content state per the game bible's platform-agnostic entitlement principle.

**API contract:** The game client calls a single endpoint (e.g., `GET /api/entitlements?player_id=X`) and receives a list of all content the player is entitled to, regardless of how they acquired it. The client does not know or care whether an era was subscribed, purchased directly, or bought on Steam. The backend resolves this internally.

### Content Delivery

Era pack files (JSON libraries + 3D assets) are stored on **Cloudflare R2.** When the game client needs to download content, the backend generates a **signed URL** with a short expiry (e.g., 15 minutes) and returns it to the client. The client downloads directly from R2 — the backend never proxies file bytes. This keeps bandwidth costs near zero regardless of player count.

**The website server and the content storage are separate concerns on shared infrastructure.** The website/backend is a web application (auth, Stripe webhooks, entitlement DB, API endpoints). R2 is an object store. They don't need to be on the same machine — the backend just needs network access to generate R2 signed URLs.

---

## Infrastructure

### Phase 1 — Static Marketing Site

**Hosting:** Cloudflare Pages (free tier) or Vercel (free tier). Both serve static sites from global CDNs with custom domain support, HTTPS, and fast deploy from Git.

**Domain:** A `.com` domain for the game. Registered through Cloudflare Registrar or Namecheap. Cost: ~$10–15/year.

**Tooling:** Plain HTML/CSS/JS. No build tools, no static site generator, no framework. The expected article count (10–20 total) does not justify the overhead of a build tool like Astro — duplicating an HTML template and pasting in article content takes ~2 minutes per article, which is negligible at this volume. Plain HTML keeps the project dead simple: open a file, edit it, see the result in a browser. No build step, no dependency management, no toolchain to debug. If the article count ever grows past 30+, a static site generator can be introduced retroactively — the HTML templates will inform the generator's templates.

**Cost:** $0–20/month (domain + hosting free tier).

### Phase 2 — Backend + Commerce

**Server:** A lightweight web application running either FastAPI (Python) or Express/Fastify (Node.js). FastAPI keeps the project in one language (Python, same as the simulation backend). Node is more conventional for web + Stripe integration and has better Stripe SDK support. Either works — this is a preference call.

**Database:** PostgreSQL. Supabase provides a free tier with managed Postgres, built-in auth, and a REST API — reducing the amount of custom backend code needed. Alternatively, a small managed Postgres instance on Railway, Render, or Fly.io.

**Auth:** Supabase Auth (if using Supabase) or a simple JWT-based auth flow. OAuth providers (Google, Discord) for convenience. Email/password as the baseline. Do not roll custom auth crypto.

**Hosting:** The backend runs on a small cloud instance. Options: Railway (free tier → $5/month), Fly.io (free tier → $5/month), Render (free tier → $7/month), or a Hetzner VPS ($4/month for a dedicated machine with more control). Any of these is sufficient — the backend is tiny (handles auth checks and Stripe webhooks, not heavy computation).

**Cost:** $5–25/month.

### Phase 3 — Content Delivery

**Storage:** Cloudflare R2. Free for the first 10GB stored and 10 million read requests per month. Zero egress fees (unlike AWS S3). A full era pack is ~50MB — 200 era packs fit in the free tier. Millions of downloads before costs become meaningful.

**Signed URLs:** Generated by the backend when an authenticated player requests content. The signed URL has a short expiry (15 minutes) and points directly to the R2 object. The backend generates but does not serve the content.

**Cost:** $0–5/month for the foreseeable future.

### Total Infrastructure Cost

Pre-launch (Phase 1 only): **~$15/year** (domain registration).
At launch (Phases 1–3): **$10–50/month** depending on hosting choices.
At scale (thousands of active subscribers): costs grow linearly with Stripe transaction volume (3% per payment) and R2 storage (pennies per GB beyond free tier). Infrastructure costs remain negligible relative to subscription revenue at any meaningful player count.

---

## Build Sequence

### Phase 1 — Design Prototype and Marketing Site

**Step 1: Visual design lockdown.** Build a local prototype of the landing page to establish the visual language — typography, color, spacing, layout rhythm. Iterate until the design feels right. This prototype is a throwaway artifact, not production code.

**Step 2: Full static site build.** Expand the prototype to all five pages in plain HTML/CSS/JS. Shared elements (nav bar, footer) are duplicated across pages — at five pages this is manageable and avoids tooling complexity. Write content for all pages — landing copy, The Game deep pitch, Era Library placeholder grid, Articles index with initial articles.

**Step 3: Deploy.** Push to Cloudflare Pages or Vercel. Point the custom domain. Verify HTTPS, Open Graph tags, mobile responsiveness. The site is live and linkable.

**Step 4: Content seeding.** Publish 3–5 foundational articles. Begin Reddit distribution. Collect mailing list signups.

**Dependencies:** None. This phase is entirely independent of the game's development state. It can be done now.

### Phase 2 — Backend and Commerce

**Step 5: Backend scaffolding.** Set up the server (FastAPI or Node), database (Supabase or managed Postgres), and Stripe integration. Implement: user registration, login, subscription creation, subscription management (via Stripe Customer Portal), era pack purchase, entitlement recording.

**Step 6: API endpoints.** Build the entitlement API that the game client will call. `GET /api/entitlements` returns a player's full content access list. `POST /api/auth/login` returns a session token. Stripe webhook endpoints for payment events.

**Step 7: Web integration.** Connect the website's Account page and Era Library page to the backend. Login/registration forms. Subscription CTA links to Stripe Checkout. Era pack purchase buttons link to Stripe Checkout. Account page links to Stripe Customer Portal.

**Dependencies:** Stripe account setup (requires a business entity — the Florida LLC discussed in previous sessions). Domain must be live (Stripe requires a website URL for account verification).

### Phase 3 — Content Delivery

**Step 8: R2 setup.** Create a Cloudflare R2 bucket. Upload a test era pack file. Implement signed URL generation in the backend.

**Step 9: Download flow.** Build the endpoint that validates a player's entitlement and returns a signed R2 URL for the requested era pack. Test the full flow: purchase → entitlement recorded → client requests download → backend validates → signed URL returned → client downloads from R2.

**Step 10: Game client integration.** The Godot frontend calls the backend API to check entitlements on launch and download any new content. This is a Godot-side task, not a website task, but it completes the end-to-end loop.

**Dependencies:** Phase 2 must be complete (auth and entitlements must exist before content delivery can gate on them). At least one era pack must exist in a downloadable format (JSON + assets bundled into a package).

### Phase 4 — Polish and Iteration

Ongoing after launch. Analytics integration (privacy-respecting — Plausible or Fathom, not Google Analytics). A/B testing the landing page conversion funnel. Article publishing workflow refinement. Community features if demand warrants (forums, user profiles). Performance optimization. Accessibility audit.

---

## Open Design Questions

> Questions that need resolution before implementation. When resolved, write the answer into the appropriate section above and remove the question from this list.

### 1. Hero Section One-Liner

The landing page hero needs a one-line pitch that captures the game's identity. Current direction to explore: the sentence must communicate the combination of (a) one game engine with infinite era settings, (b) a world that moves without the player, and (c) the commander identity. The one-liner cannot be generic strategy game hype — it must make a lapsed Stellaris/CK player stop scrolling.

Candidates to evaluate:
- "One game. Infinite settings. A civilization that doesn't need you." — captures skeleton/skin and commander-not-king, but "doesn't need you" might read as dismissive rather than intriguing.
- Needs further brainstorming.

### 2. Astro vs. Plain HTML (RESOLVED in v1.00)
*Resolved: plain HTML/CSS/JS. Article volume (10–20 expected) does not justify build tooling. See Infrastructure section.*

### 3. Backend Language — Python (FastAPI) vs. Node (Express/Fastify)

Both are viable. FastAPI keeps the project in one language (Python, matching the simulation backend). Node has better Stripe SDK support and is more conventional for web development. This is a preference decision with no wrong answer. Decision deferred until Phase 2 begins.

### 4. Auth Provider — Supabase vs. Custom JWT

Supabase provides managed Postgres + auth + REST API on a free tier, reducing custom code. Custom JWT gives full control but requires more implementation. Decision deferred until Phase 2 begins.

### 5. Dark Mode (RESOLVED in v1.00)
*Resolved: three-state theme toggle included from v1. Auto (reads system `prefers-color-scheme`), Light, and Dark. Auto is the default. User preference is persisted in localStorage. The toggle sits in the nav bar next to the logo. See Visual Direction section.*

---

## Document Maintenance

### Rules

1. **This file is the single source of truth for the website.** If something in another doc conflicts with this file, this file wins. The game bible is authoritative for game mechanics and monetization structure; this file is authoritative for how those concepts are presented on the web.
2. **Append-only unless Westley approves.** See the modification rule at the top of this document.
3. **Conceptual only.** No CSS values, no component code, no API schemas. Those belong in implementation docs.
4. **Update, don't append.** When a design decision changes with Westley's approval, update the relevant section in place. The document should always read as current.
5. **Open questions move to resolved.** When an open question is answered, write the answer into the appropriate section and remove it from the open list.
6. **Version numbering.** The filename includes a version number: `website_design_doc_X_XX.md`. Same convention as the game bible — minor changes increment the decimal, major structural changes increment the whole number.

### Relationship to Other Documents

- **Game bible** (`game_bible_X_XX.md`) — authoritative on game design, monetization model, distribution infrastructure. This document references it but does not duplicate it.
- **Implementation docs** (future) — technical specs for the backend API, Stripe integration, Godot client integration, deployment configuration. These reference this document for design intent.
- **Article drafts** — individual article content. These follow the editorial guidelines in this document but are not governed by it.
