# Ouroboros Manifold — Expansion Packs and Monetization Reference

> **Extracted from game_bible.md v1.23.** This file is authoritative for expansion packs,
> distribution, pricing, and monetization model. If this file conflicts with game_bible.md,
> flag it for Westley — do not silently resolve the conflict.
>
> **Modification rule:** Same as the master bible — append-only unless Westley approves
> deletion. Resolved open questions get written here AND reflected back to the hub.

---

## Expansion Packs and Monetization

This section defines how the game makes money. The era-agnostic architecture (Sacred Principle #3) is not just an engineering nicety — it is the commercial engine of the entire project. The game is a **skeleton**. Expansion packs are the **skin**. The simulation, mission generator, event chains, combat system, and game loop are era-neutral machinery. A theme pack plugs into that machinery and reskins every surface the player sees: unit names, art, prose, music, chronicle templates, map aesthetics, cultural flavor. The skeleton ships once. The skins ship forever.

### Time Period Expansion Packs

Each expansion pack is a complete time period that the player can select at the start of a new game or cycle. The base game ships with the **sci-fi theme** — Asimov-inspired, set 10,000+ years in the future. This is the right starting era for both design (Foundation inspiration is the core thematic identity) and marketing (the target audience of strategy gamers on Steam over-indexes on sci-fi; Stellaris, Endless Space, FTL, Homeworld are the competitive neighborhood where an indie can differentiate). Sci-fi tech tiers are also easier to design than historical eras because there's no accuracy constraint — the progression is invented and baked into the era at design time. Expansion packs add additional eras — each with its own AI-generated library content (naming conventions, chronicle templates, mission briefing prose, unit flavor, visual style, tech tier definitions). Historical eras (Roman, WW2, Medieval, etc.) are expansion pack content.

**Example time periods** (illustrative, not exhaustive): Medieval, Caveman, Roman, Greek, Imperial China, Ark-style dinosaur world, WW2, Age of Sail, Aztec, Viking, Feudal Japan, Cyberpunk, Post-Apocalyptic — and many more. The era-agnostic engine means any historical or fictional setting that maps onto the simulation's abstractions (regions, military strength, economic output, factional tension, population, missions, faction agents) is a valid expansion pack. The list of possible eras is effectively unbounded.

### Isolated Time Period Chapters

Some expansion packs may feature an **isolated time period** — a chapter arc that takes place entirely within a single era (e.g., an expansion where every chapter is Roman, or every chapter is far-future). When a game uses an isolated time period, chapters are shorter than the base game's multi-era generational arcs. The simulation teleports forward when it reaches a configured threshold (a stability collapse, an extinction-level event, or an era-specific trigger), or a major event causes the cycle to restart from the beginning. The specific mechanics for time period isolation — threshold triggers, chapter length scaling, restart conditions — are to be determined during design of the first non-sci-fi expansion.

### Rotational AI-Generated Expansion (Post-Launch)

A single rotating expansion slot where AI generates an entire themed content pack on a weekly cadence. These packs draw inspiration from popular fiction universes and genre tropes — the spirit of Star Wars, Terminator, Alien, Dune, and similar — translated through the game's era-agnostic engine into playable theme packs. This is not a near-term feature. **This is a "after we finish the game" idea.** It is listed here so the architecture accounts for it — the library pipeline and theme pack interface should not make this impossible — but no design or implementation work should target it until the base game and first paid expansions ship.

### Monetization Model

**Free version:** The player gets the **Roman era** as the permanent free tier. The Roman era is a complete, genuine game experience — full simulation, all mission archetypes, the complete unit roster (all units restricted to ground-layer combat per the era's unit-type layer restrictions). The Roman era demonstrates the simulation depth and generational storytelling but does not showcase the 2.5D vertical layer system, which is a premium feature visible only in multi-layer eras.

**New player trial period.** On first download, the player receives a **trial key** granting access to both the **1980s era** (3–5 missions) and the **Settled Reach sci-fi era** (3–5 missions). The trial missions are fully featured — same simulation, same AI, same 2.5D layer combat — not a degraded preview. The trial exists to demonstrate the layer system and premium era quality. The 1980s era (submarines on layers 4–5, surface ships/land on layer 3, aircraft on layers 1–2) is the clearest possible showcase of why layers matter. The Settled Reach era shows the full sci-fi experience. After the trial missions are consumed, both eras lock and the player returns to the free Roman tier unless they subscribe or purchase era packs.

**Trial expiration.** The trial counter is per-mission, not time-based. Starting a mission in a trial era decrements the counter. If the player is mid-mission when the counter reaches zero, they complete that mission — no mid-game lockout. The lock activates at the next mission selection screen.

**Subscription ($3–5/month):** Full access to the complete game including the base sci-fi theme (Settled Reach) and all available time period expansion packs. Cancel anytime. This is the primary revenue model. Marketing material on the Steam page highlights subscription content — the rotating library, the expanding era catalog, the living game that grows over time. The subscription funds ongoing AI content generation and new expansion development.

**Cancellation behavior.** When a subscription lapses, the player loses access to all eras except the free Roman tier and any eras they have **purchased outright** as one-time buys. Eras accessed only through the subscription (including eras with grind progress — see "Era Mastery Grind" below) become unavailable until the player resubscribes or purchases them individually. Grind progress toward era mastery is preserved on the server — resubscribing restores the player's progress exactly where they left off. The subscription is the access layer. One-time purchases are the ownership layer. These are cleanly separated: subscribing grants temporary access to everything, purchasing grants permanent access to specific eras.

**Expansion packs (one-time purchase):** Individual time period packs sold as standalone purchases for players who want a specific era without subscribing. Purchased eras are permanent additions to the player's library regardless of subscription status. This is the secondary revenue channel.

### Access Key System

The game uses a **variable-length key system** for managing access to premium eras beyond the standard subscription and one-time purchase channels. Keys are alphanumeric codes redeemable through the in-game Era Library or a web redemption page.

**Three key types:**

- **Permanent key** — unlocks a specific era (or set of eras) forever. Equivalent to a one-time purchase. Used for giveaways, contest prizes, influencer partnerships, and promotional bundles.
- **Time-limited key** — grants full subscription-equivalent access for a fixed duration (e.g., 1 week, 1 month, 3 months). Used for promotional campaigns, social media giveaways, and Discord community events.
- **Mission-limited key** — grants access to a specific era for a fixed number of missions (e.g., 3, 5, 10). The new-player trial is implemented as an automatically redeemed mission-limited key. Used for targeted marketing (e.g., "try the 1980s era for 5 missions" codes distributed on social media).

**Key infrastructure.** Keys are generated server-side and tracked in the same entitlement database as subscriptions and purchases. Each key has: a unique code, a type (permanent/time/mission), a scope (which eras it unlocks), an expiration parameter (duration or mission count), and a redemption status. Keys are single-use — once redeemed, they are bound to the player's account. The system is lightweight and runs on the same infrastructure as the subscription auth server.

**Distribution channels.** Keys are distributed through social media posts, YouTube stream giveaways, Discord community events, influencer partnerships, and cross-promotion with other indie developers. Keys are the primary tool for zero-budget grassroots marketing — every key is a targeted conversion opportunity.

### Marketing Strategy — Product-Led Growth

The game's marketing model is **product-led growth (PLG)** — the product sells itself through quality, word of mouth, and community engagement. There is no paid advertising budget. Every marketing dollar equivalent is invested in the product itself.

**The 2.5D layer system is the hero marketing feature.** The vertical layer mechanic is visually distinctive, immediately comprehensible, and unlike anything in the current RTS market. Marketing material leads with the 1980s era (submarines/ships/aircraft across layers) and the Settled Reach era (full 3D space combat across layers) as demonstrations of the layer system. These two eras are the premium showcase — they exist in marketing material before the player downloads the game, and they are the first thing the player experiences in the trial period after download.

**Marketing channels (zero-budget):**

- **Social media** — short-form video content showing the layer system in action. Before/after comparisons (flat combat vs. layered combat), time-lapses of the generational simulation, and clips of decisive tactical moments. The 1980s era's submarine/ship/aircraft layer split is the most intuitive visual for a 15-second clip.
- **YouTube streams** — live gameplay sessions showing the simulation running, missions being played, and the generational arc unfolding. Commentary focuses on emergent stories — what the simulation produced, not what was scripted.
- **Discord** — community server for feedback, bug reports, and feature discussion. Active developer presence. Players who feel heard become evangelists.
- **The trial period is the conversion funnel.** The 3–5 mission trial of premium eras is the core marketing mechanism. The free Roman era gets players in the door. The trial shows them what they're missing. The subscription keeps them.

**UI as marketing.** The game's interface is part of the product-led growth strategy. The UI should be visually impressive and distinctively modern — clean, animated, and polished in a way that makes screenshots and clips shareable. Inspiration: Claude's interface aesthetic (simple foundations, hyper-modern execution), ASCII-rooted animations with smooth transitions. The Era Library, mission briefing screens, and chronicle scroll are all marketing surfaces — they should look good enough that players screenshot and share them unprompted.

### Target Audience

**Platform:** PC-only at launch. The game's command interface — control groups, modifier hotkeys, layer assignment shortcuts, box-select, right-click commands — is designed for keyboard and mouse. Controller adaptation would compromise the design. Console is not on the roadmap.

**Primary audience: the Stellaris-curious RTS player.** Someone who plays StarCraft 2 or Age of Empires and wishes the campaign had a living world behind it. Someone who plays Stellaris and wishes the combat was real-time tactical instead of auto-resolve. Someone who reads a Dwarf Fortress emergent story on Reddit and thinks "I want that, but I want to actually command the armies." These are PC strategy gamers, roughly 20–35, who follow indie games on Steam, watch strategy game content on YouTube, and are comfortable with mechanical depth but don't want StarCraft-level APM demands. The low micro barrier (units handle basics competently, player skill expression is in strategic direction) is critical for this audience — they want the *feel* of commanding without the APM tax.

**Secondary audience: the Homeworld/Sins of a Solar Empire crowd.** Drawn by the 2.5D vertical layer combat specifically. The layer system is visually distinctive and mechanically novel in the current RTS market. This audience clicks because the game *looks* different. They stay because the simulation gives each mission weight.

**Tertiary audience: grand strategy players** who want tactical combat that actually feels like commanding an army, not auto-resolving battles. The Crusader Kings and Europa Universalis players who have always wished the war screen was a real game. They care most about the simulation and the chronicle — the tactical combat is a bonus.

**Competitive vs. narrative.** The game serves both drives through natural rhythm separation. During missions: pure tactical skill expression. Low micro floor, high strategic ceiling. Competitive players optimize force positioning, ability timing, layer control, and reinforcement structure capture. Between missions: narrative reward. The chronicle scroll, the simulation advancing, the generational arc unfolding. Narrative players savor the emergent stories, the named characters, the faction dynamics. The two modes don't compete — they alternate. The mission briefing screen is the hinge point: it's where the narrative context becomes the tactical setup.

**The hook that gets them to click:** The 2.5D layer system in 1980s/Settled Reach marketing clips. Visual distinctiveness is the door-opener.

**The hook that gets them to stay:** The generational simulation — watching their actions ripple across centuries.

**The hook that converts free to paid:** The trial missions. Three to five missions in 1980s-era layer combat, then back to Roman ground-only. The absence of layers after the trial is the conversion pressure — they've tasted the full game and the free tier feels flat by comparison.

### UI Aesthetic — Terminal Meets Glass

The game's visual identity is **terminal aesthetics meets glass UI** — the feeling of a classified military dossier being rendered on a hyper-modern command terminal. Every screen should feel like it belongs in a world where someone built beautiful software for a civilization-spanning military command structure. The aesthetic is dark, information-dense, and precisely typeset, with warmth coming from era-specific accent colors rather than from bright backgrounds or playful elements.

**Core aesthetic principles:**

- **Dark-first.** Near-black backgrounds (#0a0a0c base, #111114 surface, #18181c card, #1f1f24 elevated). The darkness creates contrast for the data and makes the accent color sing. No light mode. The game is played in the dark.
- **Two-font system.** Monospace (JetBrains Mono) for all data, labels, system text, stat readouts, timestamps, and UI controls. Serif (Newsreader) for all narrative text — mission briefings, chronicle entries, intelligence reports, flavor prose. The split creates the "machine presents the data, a human wrote the narrative" feel. The monospace is the terminal. The serif is the dossier.
- **Era-owned accent colors.** Each era owns a single accent color that permeates every screen when that era is active. Roman: warm gold (#c9a84c). Settled Reach: cool blue-teal (TBD). 1980s: military olive or amber (TBD). The accent color is used sparingly — classification headers, faction names, key action buttons, the blinking cursor, important stat values. Everything else is near-monochrome (primary text #e8e6e1, secondary text at 55% opacity, tertiary at 30% opacity). The restraint makes the accent pop.
- **Semantic color only for data.** Red (#c44a3f) for danger/threat/high values. Blue (#5a8fbf) for info/player-side/neutral. Green (#4a9e6e) for healthy/positive. These appear only in stat readouts and progress bars where they carry meaning — never as decoration.
- **Subtle scanlines.** A faint repeating linear gradient (transparent/rgba(0,0,0,0.03) alternating at 2px/4px intervals) overlays every screen as a full-screen pseudo-element. Barely visible — felt more than seen. It's the ghost of a CRT monitor in a modern interface. It never interferes with readability.
- **Borders at 0.5px, rgba white at 6–10% opacity.** Thin enough to define structure without drawing attention. Cards and sections are bounded by structure, not by heavy lines.

**Animation philosophy — simple roots, hyper-modern execution:**

- **Staggered fade-slide-in on screen load.** Every element fades from 0 opacity and translates 8px upward, easing into position. Elements appear in visual hierarchy order: classification label first (0.2s delay), then title (0.4s), then subtitle (0.55s), then divider expands horizontally (0.5s), then narrative body (0.65s), then sidebar cards cascade top to bottom (0.7s, 0.85s, 1.0s, 1.15s), then footer action bar (1.2s). The total load sequence is ~1.5 seconds. Each element's animation is 0.5–0.6s with ease timing.
- **Stat bars animate to their values.** Horizontal progress bars (military strength, parity, tension) scale from 0 to their target width over 1 second with ease timing. The animation starts when the parent card fades in, so the bar grows as the card appears.
- **Blinking cursor on live data.** A 1px-wide accent-colored cursor blinks (1s step-end infinite) after timestamps, simulation tick counters, and any value that represents "the simulation is running." This is the heartbeat of the interface — the signal that the world is alive.
- **No gratuitous animation.** Hover effects are subtle (border opacity shift, text color brighten). No bounce, no overshoot, no parallax, no particle effects in the UI. The game world has visual effects. The UI is calm.

**Reference mockup — Mission Briefing Screen (Roman era):**

The mission briefing is the hinge screen between narrative and tactical gameplay and demonstrates all aesthetic principles at once. The layout is a two-column grid: left column for narrative, right column for data.

*Header zone:*
- Top-left: "MISSION BRIEFING" in 10px monospace, letter-spacing 3px, accent color. Below it, mission ID / chapter / generation in 10px monospace tertiary text.
- Title in 28px serif, weight 400, primary text color. Below it, a one-line subtitle in 14px serif italic, secondary text color. Example: title "The Siege of Thessalonica", subtitle "A Fortifier pushes south with overwhelming force".
- Top-right: era badge ("ROMAN ERA" in 9px monospace, accent color on accent-dim background with 0.5px accent-tinted border, 2px border-radius) and simulation tick counter with blinking cursor.
- A 0.5px horizontal divider spans full width below the header, animated with a horizontal scale expansion.

*Left column — narrative:*
- Section label "INTELLIGENCE REPORT" in 9px monospace, tertiary text, 2.5px letter-spacing.
- Briefing text in 14.5px serif, weight 300, line-height 1.75, secondary text color. Key data (military strength numbers, tick counts) highlighted in primary text weight 400. Faction and character names in accent color weight 400. The prose is generated by the chronicle pipeline and reads like a military intelligence briefing — factual, specific, grounded in simulation state.
- Below the narrative: mission objective block. Section label "MISSION OBJECTIVES" same style. The objective card has a 2px left border in accent color, 6px border-radius on right side only, card background, 12px 16px padding. Primary objective in 12px monospace primary text. Objective metadata (archetype, success spectrum) in 11px monospace tertiary text.

*Right column — four data cards stacked:*
- Each card: card background, 0.5px border, 6px border-radius, 14px 16px padding.
- Card 1 — "ENEMY ASSESSMENT": faction name (accent), archetype, military stat with progress bar (danger color for high values), tech tier, and an archetype behavior tag (e.g., "DEFENSIVE POSTURE — RARE COMMITTED ATTACK" in 9px monospace, info color on info-dim background, 0.5px info-tinted border).
- Card 2 — "YOUR FORCE": parity percentage with progress bar (info color), then a list of unit types with dot indicators and counts (e.g., "Vanguard x4", "Warden x2"). Dot indicators are 4px circles in accent color.
- Card 3 — "REGION STATE": region name, tier, economy/military/tension values with semantic colors (green for healthy economy, red for depleted military, accent for tension).
- Card 4 — "COMMANDER LINEAGE": current commander name (accent), generation number, predecessor name and status (e.g., "KIA — Naissus" in danger color).
- A serif italic note in tertiary text below region state communicates reinforcement expectations: "Local military infrastructure degraded — expect sparse reinforcements from regional garrisons."

*Footer zone:*
- Left: two buttons — "DEPLOY FORCES" (primary: accent background, dark text, 11px monospace weight 500, 3px border-radius) and "REVIEW CHRONICLE" (secondary: transparent background, secondary text, 0.5px border).
- Right: keyboard shortcut hints in 10px monospace tertiary text ("ESC to return to galaxy view // TAB for force details").

This mockup is the aesthetic north star. All other screens (Era Library, chronicle scroll, tactical HUD, galaxy view) derive their typography, color, animation, and layout principles from this reference. The specific content and layout of each screen will vary, but the visual language is consistent.

### UI Personality — Celebration Animations and Flavor Text

The game's UI has a **personality layer** — moments where the interface breaks its military-professional tone to acknowledge the player with warmth, humor, or congratulation. These moments are rare and deliberate, which is what makes them land. The personality is expressed through ASCII-consistent animated sequences and contextual flavor text rendered in the monospace terminal aesthetic. Think Claude Code's buddy character — a small personality that lives inside the system and occasionally speaks to you.

**Key redemption personality.** When a player redeems an access key, the UI responds with a brief animated sequence and a context-aware flavor message before the standard entitlement confirmation. The animation and message vary based on key type:

- **Permanent full-access key:** The terminal aesthetic renders a brief ASCII animation — a wink, a nod, a conspiratorial gesture built from monospace characters. The flavor text acknowledges the key's origin with personality: something in the vein of *"huh — you must know somebody"* rendered in monospace with the accent color, followed by a beat, then the standard confirmation ("1980s Era — permanently unlocked"). The tone is playful and knowing — the player received this key from a person or event, and the game acknowledges that human connection. The specific ASCII art and message pool are authored content, not AI-generated — a curated set of 5–10 variants per key type so the experience doesn't feel canned on repeat.
- **Time-limited key (1 week, 1 month, etc.):** Similar personality beat but with a time-aware flavor: the system acknowledges the temporary nature with warmth rather than pressure. No countdown timers, no urgency language — just a welcome and a wink.
- **Mission-limited trial key (new player trial):** Lighter touch — a brief welcome animation that doesn't overwhelm a new player who's still learning the interface. The personality ramps up on subsequent key redemptions once the player is familiar with the game's tone.

**Era unlock celebration.** When a player gains access to a new era — through any channel (key redemption, one-time purchase, subscription activation, or tier/mastery milestone) — the Era Library plays a **celebration animation** specific to that era. The animation is ASCII-rooted and consistent with the Terminal Meets Glass aesthetic: monospace characters assemble, transform, or cascade into a visual that evokes the era's identity (Roman columns assembling from pipe characters, submarine silhouettes surfacing from tilde waves for 1980s, starfield resolving from dots for Settled Reach). The animation is brief (2–4 seconds), visually impressive, and runs once per unlock event.

The celebration sequence:
1. The Era Library card for the unlocked era pulses with the era's accent color.
2. A full-screen ASCII animation plays — era-themed, monospace-built, smooth-animated. The animation fills the screen briefly and resolves into the era's title rendered large in the serif font.
3. A flavor message appears below in monospace: congratulatory, context-aware (different text for purchased vs. key-redeemed vs. mastery-earned), and brief.
4. The animation fades and the Era Library returns to its normal state with the new era now accessible.

**Design principles for the personality layer:**

- **Rarity is the point.** These moments happen only at key redemption and era unlock — events that occur a handful of times over the player's lifetime with the game. The personality is memorable *because* the rest of the UI is composed and professional.
- **ASCII-consistent.** All animated sequences are built from monospace characters, box-drawing characters, and simple geometric shapes rendered at high resolution with smooth CSS/shader animation. The roots are plaintext. The execution is cinematic. This is the same "simple roots, hyper-modern execution" principle from the broader UI aesthetic.
- **Context-aware, not random.** The system knows how the player obtained the era (purchase, key, subscription, grind) and tailors the message accordingly. A player who ground out mastery over 3 months gets a different message than one who redeemed a giveaway key. The grinder gets acknowledged for their dedication. The key holder gets the knowing wink.
- **Curated, not generated.** Celebration animations and flavor text are hand-authored content, not AI-generated at runtime. A pool of variants per context (5–10 per key type, 1–2 per era unlock method) is sufficient. Quality over volume — each message should feel like it was written by a person who cares.

### Marketing Implications

The skeleton/skin model is the core marketing story. Every trailer, every Steam page screenshot, every community post reinforces the same message: **one game, infinite settings.** The simulation is deep enough that each era feels like a full game, not a reskin — but the player only needs to learn the mechanics once. The expansion catalog is the long tail. The subscription is the recurring revenue. The free version is the funnel.

### Distribution Infrastructure — Hybrid Steam + Direct Model

The game ships on Steam. Steam provides discoverability, community infrastructure, and a trusted storefront that players already have payment info on file with. However, era packs and subscription access are available through **two parallel purchase channels** — Steam DLC and a direct in-game storefront — with the player experience identical regardless of which channel they use.

**Why hybrid:** Steam takes a 30% cut on all sales including DLC. At the $2–3 price point per era pack, that means netting roughly $1.40–$2.10 per sale through Steam versus ~$1.94–$2.91 through direct payment processing (Stripe at ~3%). Across thousands of players buying multiple eras, the margin difference is significant. The hybrid model captures Steam's discoverability advantage for the base game while offering a higher-margin direct channel for ongoing content purchases. Players who prefer the Steam ecosystem buy there. Players who use the in-game store save a small amount and the project keeps more margin. Both channels deliver the same content, the same way, with no difference in the player's experience.

**Era pack delivery.** Era packs are JSON content libraries — naming conventions, chronicle templates, mission briefing prose, unit stat profiles, event templates, and visual asset references — plus the associated 3D model files and texture assets for units and environment objects. A complete era pack is a few megabytes for the data files, plus the 3D assets (low-poly models are lightweight — typically under 50MB total for a full era). This lightweight content profile means era packs do not require a dedicated content delivery network or game distribution infrastructure. Era pack files are hosted on **Cloudflare R2** (the same infrastructure already planned for the narrative content library). When a player purchases an era pack through either channel, the game downloads the content package from R2 on next launch, unpacks it into the local content directory, and the era becomes available for selection. Steam DLC purchases trigger the same download-from-R2 flow as direct purchases — Steam handles the entitlement check, R2 handles the content delivery.

**Subscription implementation.** Steam does not offer a native monthly subscription system. The subscription is handled through **external payment processing** (Stripe) via a lightweight account system. The infrastructure required is minimal: a basic authentication endpoint, a Stripe integration for recurring payments, and a database table tracking active subscriptions. This is not a content delivery server — Steam still delivers the base game, and R2 delivers era pack content. The subscription server answers one question: "does this player have an active subscription?" The game checks entitlement status on launch and unlocks the full feature set and included era catalog accordingly. Hosting costs for this service are negligible.

**Steam DLC as parallel channel.** Era packs are also listed as individual DLC items on the Steam store page. Players can browse and purchase era packs through Steam's native storefront without ever touching the direct purchase flow. The game checks both Steam DLC ownership and direct purchase entitlements at launch — if the player owns an era through either channel, the content is available. This means a player could buy some eras through Steam and others through the in-game store with no friction or inconsistency.

### In-Game Era Library

The game includes an **Era Library** screen accessible from the main menu. This serves as the in-game storefront for browsing, previewing, and purchasing era packs directly. The Era Library shows all available eras with preview content (thematic description, sample chronicle prose, visual style preview), the player's owned eras, and purchase options. Clicking "buy" on an unpurchased era redirects to a web checkout page (Stripe-hosted) for payment processing. After purchase, the game detects the new entitlement and downloads the era pack content automatically. The subscription option is also accessible from the Era Library — players can subscribe, manage their subscription, or check their subscription status from the same screen.

The Era Library is the primary surface for ongoing monetization after the initial Steam purchase. It is where returning players discover new eras, where the subscription value proposition is visible, and where bundle promotions and seasonal offers are presented. The library should feel like browsing a curated catalog — inviting, not aggressive.

### Platform-Agnostic Entitlement Principle

**The player's experience is identical regardless of purchase channel.** An era purchased through Steam DLC, through the in-game Era Library, or included via active subscription all appear in the game identically — same content, same integration, no extra activation steps, no license keys, no manual file management. The entitlement system is invisible to the player. If it works correctly, the player never thinks about *how* they bought something — they just have it.

This principle is non-negotiable. The moment a direct-purchase era feels like a second-class experience compared to a Steam DLC era (or vice versa), the hybrid model breaks. Both channels must resolve to the same local content state with zero player-facing friction.

### Future Consideration — Steam Workshop

If the game eventually supports community-created era packs or modding, **Steam Workshop** provides free hosting and distribution for user-generated content. The era-agnostic architecture — where the engine consumes theme pack JSON without caring about its origin — is directly compatible with Workshop distribution. This is a long-term affordance, not a near-term feature. No design or implementation work should target Workshop integration until the base game and first paid expansions have shipped and a modding community has expressed interest. It is noted here so the entitlement system and content directory structure do not make Workshop integration impossible.

---

## Player Progression System

The game uses a **three-layer progression system** operating at different timescales: tier progression (short-term, within an era), commander doctrines (medium-term, across games), and era mastery grind (long-term, across months). All three layers serve the same design goal: give players a reason to come back beyond the intrinsic pull of the simulation's emergent stories.

### Tier Progression — Per-Era Unit Tier Unlock

> **RESOLVED (v2.05).** Players start each era at Tier 1 and earn access to Tier 2 and Tier 3 through play. Resets per era.

When a player begins a new era (whether the free Roman era, a trial era, a subscribed era, or a purchased era), they start with access to **Tier 1 units only** for that era. Tier 2 and Tier 3 units are locked behind progression milestones earned through mission play within that era. This is a per-era reset — unlocking Tier 3 in the Roman era does not grant Tier 3 in the Settled Reach era. Each era has its own tier progression.

**What the player experiences:** Early missions feel scrappier. Tier 1 units have the roughest stat profiles and the baseline version of each ability. The player commands more numerous but less individually capable forces (the force parity system compensates for lower per-unit strength by allocating more units). As the player unlocks Tier 2 and eventually Tier 3, their forces become fewer but more capable, abilities potentially gain variant parameters, and the visual aesthetic shifts from the era's Tier 1 look (rough, early) to its Tier 3 look (refined, advanced). The progression is felt through both gameplay and visuals.

**Interaction with the simulation's tech level.** The simulation continues to track tech_level per faction (0–100) and map it to three tiers as currently designed. The player's tier unlock acts as a **cap** on the force allocation algorithm's unit selection. If the player has unlocked Tier 2 but the simulation's tech level has reached Tier 3, the force allocation draws from the Tier 2 library. If the simulation is at Tier 1 and the player has Tier 2 unlocked, the simulation's state wins — the civilization hasn't developed the technology yet. The player's unlock is a ceiling, the simulation's tech level is the floor. The player can never field units above the lower of (their unlock tier, the simulation's current tier).

**Tier unlock progression triggers.** The specific criteria for earning Tier 2 and Tier 3 are open tuning questions. Likely candidates include: missions completed within the era, success bands achieved (higher bands accelerate progression), generational arcs completed, or a combination weighted toward mission performance. The progression should feel like natural play — "I've been commanding Roman legions for a while and my forces are improving" — not like a grind checklist.

**Tier skip purchase ($1).** Players who want immediate access to all three tiers within a specific era can purchase a **tier skip** for approximately $1 per era. This is a one-time micro-purchase that permanently unlocks all tiers for that era (permanent means tied to the era purchase/subscription, not independent of it — if the player's subscription lapses and the era locks, the tier skip is preserved for when they regain access). The tier skip respects the player's time without undermining the progression for players who enjoy it.

**Open design questions (tier progression):**

- **Ability variants across tiers** — should each tier have differentiated ability parameters (e.g., Tier 1 Raider Surge is a simple speed burst, Tier 3 Surge leaves a sensor interference trail)? Or should abilities be identical across tiers with only stat changes? Ability variants create more compelling progression but require more design work per era. **Decision deferred.**
- **Progression pace** — how many missions to reach Tier 2? Tier 3? The target feel is: Tier 2 unlocked after roughly 5–10 missions in an era (the player has learned the era's character), Tier 3 after roughly 20–40 missions (the player is deeply invested). These are tuning values.
- **Progression currency or milestone-based?** — Does the player accumulate XP/points toward tier thresholds, or do they hit specific milestone conditions (e.g., "complete 3 missions at Decisive Victory or better")? A mixture is likely — base progression from missions completed, bonus acceleration from high performance.

### Commander Doctrines — Horizontal Tactical Customization

> **Future consideration.** Not a launch feature. Listed here to reserve the design space.

Commander doctrines are **small tactical modifiers** the player selects before each mission from their unlocked pool. Doctrines are horizontal (tradeoffs and preferences, not power increases) and persist across games. They give the player a customizable playstyle identity without distorting the force parity balance.

**Examples (illustrative, not final):** "Vanguard doctrine — Brace windup reduced by 0.5s." "Raider doctrine — Surge cooldown reduced by 10s but Surge duration halved." "Logistics doctrine — reinforcement structures produce 15% faster." "Intelligence doctrine — sensor pulse cooldown reduced." Each doctrine shifts how the player plays without making them strictly stronger.

**Unlock conditions** are tied to play achievements: completing missions with specific unit compositions, achieving specific success bands, winning with specific tactical approaches. Unlock conditions teach the player about the game's depth — "to unlock the Raider doctrine, win a mission with a Strike-heavy force" encourages the player to try compositions they might otherwise ignore.

**Limited slots** — the player picks 3–5 doctrines from their pool before each mission, creating a deck-building decision. **Era-specific doctrines** can be included in era packs alongside universal doctrines, adding another axis of content value per era.

### Era Mastery Grind — Long-Term Subscription Retention

> **RESOLVED (v2.05).** Subscribers can earn era mastery through sustained play. Grind progress requires an active subscription to access.

Active subscribers have access to all eras. In addition to playing them, subscribers can **earn mastery progress** toward individual eras through sustained play. Era mastery is a long-term progression track — visible in the Era Library as a progress bar per era — that rewards the player for deep engagement across hundreds of hours.

**What mastery earns.** Era mastery is not an alternative to purchasing or subscribing — it is a **subscriber-exclusive engagement reward** layered on top of access. Mastery progress unlocks cosmetic rewards, era-specific doctrines (when the doctrine system ships), achievement badges visible in the Era Library, and other recognition content. The specific reward track per era is a design question for post-launch. The mastery grind gives subscribers a long-term goal ("I'm 60% of the way through 1980s mastery") and a reason to return session after session, modeled after Deep Rock Galactic's extended progression pacing.

**Mastery pacing.** Full mastery of a single era should take approximately 2–4 months of active subscription play (hundreds of missions, dozens of generational arcs). This pacing ensures mastery feels like a genuine achievement, not a checkbox. When the era catalog reaches 5–10–20 eras, completing mastery across all eras becomes a multi-year project — the kind of long-tail engagement that sustains a subscription game.

**Mastery progress requires an active subscription.** If the player's subscription lapses, they cannot access non-purchased eras and therefore cannot advance mastery. Progress is preserved server-side — resubscribing restores all progress. Mastery rewards already earned remain visible (badges, cosmetics) but era access still requires either an active subscription or a one-time purchase.

**Mastery progress triggers.** Mastery advances through natural play within each era: missions completed, success bands achieved, generational arcs completed, tier progression milestones reached, specific tactical achievements. The progress formula weights variety and depth over raw repetition — the player who completes 50 different missions across multiple archetypes progresses faster than the player who grinds the same mission type 50 times.

### Future Consideration — 1980s Era Pack

The 1980s era is the primary marketing showcase for the 2.5D layer system and should be one of the first premium era packs developed. Its layer mapping is the most intuitive demonstration of vertical combat:

- **Layers 4–5 (bottom):** Underwater. Submarines operate here. Surface units cannot enter. Sensor interference is high (sonar-based detection with limited range).
- **Layer 3 (middle):** Surface. Ships and land units operate here. The "ground plane" of the era. Full sensor coverage at surface level.
- **Layers 1–2 (top):** Airspace. Aircraft operate here. Fast movement, high sensor range, vulnerable to surface-based anti-air.

The era's unit-type layer restrictions are strict: submarines cannot surface, surface vessels cannot submerge, aircraft cannot land. This creates clean, readable layer separation where each layer has a distinct force composition and the tactical decisions are about cross-layer interaction — how air power supports surface engagements, how submarines threaten ships from below, how surface escorts screen against submarine attacks.

The 6-unit roster maps naturally: Strike units become fast attack craft (Raiders as fighter jets on layers 1–2, Interceptors as ASW helicopters screening between layers), Line units become the surface backbone (Vanguards as destroyers/cruisers on layer 3, Wardens as support ships), Siege units become the heavy hitters (Bombards as strategic bombers on layers 1–2 or battleships on layer 3, Bastions as submarines on layers 4–5). The exact roster mapping is a design question for the era pack's development phase.

The 1980s era is also the trial-period showcase — new players experience this era for 3–5 missions before the trial expires, making it the single most important era for first impressions and conversion.

### Future Consideration — Unit Skins

The engine's abstract type → visual asset mapping naturally supports cosmetic variants. A "skin" is an alternate 3D model (or material/texture variant) for a given unit type within a given era. The engine already loads models by looking up the abstract type in the theme pack's asset map — skins extend that lookup to check whether the player owns an alternate visual and which one they've selected.

**Two tiers of skin complexity.** Material/color variants (same geometry, different color palette — a "winter" variant, a "gilded" variant) are trivial to produce: ~10 minutes per skin in Blender, priced at $0.50–$1.00. Model variants (different geometry that still reads as the same unit type at tactical zoom distance — a "veteran" unit with battle damage, an "elite" variant with a distinct silhouette) go through the standard Tier 1 asset pipeline at 30–45 minutes each, priced at $1.50–$2.00.

**Per-force, not per-unit-type.** The player picks a visual theme for their entire force within an era, rather than skinning individual unit types. This fits the narrative identity (you're a commander choosing your force's livery, not a unit customizer), simplifies the UI, and can be extended to per-unit-type granularity later if player demand justifies it.

**Distribution.** Skins flow through the existing hybrid purchase model — available both as Steam micro-DLC and through the in-game Era Library's customize tab via Stripe. Same platform-agnostic entitlement principle applies. Skins are high-margin, low-effort content that creates a steady drip of small-ticket purchases. A release cadence of 3–5 skins per era per month is achievable with minimal production time and compounds over the era catalog.

**When to build.** Not until the base game has finished 3D models for at least the sci-fi era, a working visual rendering pipeline in Godot, and the Era Library storefront. The engine architecture does not need to change to support skins — when the time comes, it's an extension of existing systems, not a new system.

### Future Consideration — Multiplayer

Multiplayer is not a launch feature. It is documented here because the game's architecture has properties that make multiplayer viable as a post-launch addition if player demand justifies it, and because certain architectural decisions made now (simulation determinism, symmetric faction agents) should be preserved to keep the option open.

**Why the architecture supports multiplayer.** The faction agent system is symmetric — every faction (player's civilization, Conqueror, breakaway factions) runs the same decision framework. Replacing an AI agent's `act()` call with a human player's decision is mechanically straightforward; the simulation doesn't care which entity made the choice. The simulation is also deterministic given the same inputs: same seed and same sequence of decisions produce the same world state. This property is the foundation that makes all multiplayer models work, because clients can compute state locally given synchronized inputs rather than streaming full state every tick.

**Three viable multiplayer models, in order of implementation cost:**

**Model 1 — Asynchronous shared world (cheapest, build first).** Players each run their own missions in their own time, sharing the same world. During time jumps, all human-controlled factions' autonomous agents run alongside the AI factions. When any player completes a mission, the world state syncs. This is "play-by-mail" at civilizational scale — players don't need to be online simultaneously. The shared chronicle scroll becomes the social glue: players see each other's mission outcomes, watch each other's civilizations rise and fall, and experience the Ouroboros together across centuries.

Infrastructure: a lightweight server stores the shared world state (a JSON blob — simulation state is small) and coordinates turn order. This can run on the same infrastructure as the subscription auth server. A single small cloud instance at $20–50/month supports hundreds of concurrent games. No real-time networking, no tick synchronization, no latency concerns. Engineering time: 2–4 weeks.

**Model 2 — Simultaneous missions in shared world (moderate).** Multiple players are active in the same world at the same time, each commanding their own faction's forces on independent missions. Missions run independently (no real-time interaction between players' tactical combat), but the world state reflects all players' outcomes. When Player A completes a mission in one region, the consequences are visible to Player B when their next mission generates.

Infrastructure: a persistent game server holds the authoritative world state, processes time jumps, and distributes mission briefings. Since missions themselves are single-player tactical experiences (no real-time PvP combat), standard web servers with WebSocket connections handle this — no low-latency game servers required. $50–200/month per active game cluster. Engineering time: 1–2 months.

**Model 3 — Real-time PvP combat (expensive, build last if ever).** Players encounter each other's forces during missions — two human commanders fighting over the same region in real-time tactical combat. This is the full multiplayer experience and the most complex to implement.

Infrastructure: real-time combat requires authoritative game servers with low latency (<100ms round-trip), tick-synchronized simulation, prediction and reconciliation netcode, dedicated server instances per active battle, and geographic distribution (US East, US West, EU, Asia minimum). $500–2,000+/month scaling with concurrent player count. Engineering time: 3–6 months.

**Why real-time PvP requires 3–6 months of engineering.** The core problem is latency. When Player A moves a Strike squad to flank, Player B needs to see that movement within ~100ms or the game feels broken, but the internet introduces 30–150ms of delay. Two established solutions exist, both substantial engineering efforts:

*Lockstep networking* (Starcraft's approach): both clients run the same simulation and only exchange player inputs. Bandwidth-efficient, but requires absolute cross-platform determinism (any floating-point divergence causes desync) and the game runs at the speed of the slower connection. Requires a deterministic command queue, synchronization protocol, desync detection and recovery, and extensive cross-platform testing.

*Client-server with prediction* (most modern real-time games): the server runs the authoritative simulation while clients predict outcomes locally and reconcile when the server's state arrives. Hides latency through prediction but produces visible corrections (rubber-banding, position snapping) when prediction is wrong. Requires a prediction system, a reconciliation/rollback system, an interpolation layer for smooth rendering, server-side hit detection, and bandwidth optimization.

Both approaches require rethinking how every combat interaction communicates about time. Contested actions (both players attack the same tick), layer transitions (one player sees stale position data and attacks a ghost), and ability timing (50ms disagreement on activation means a barrage hits or misses) all become negotiation problems between client prediction and server authority. The 2.5D layer system and unit abilities add additional synchronization complexity on top of the base netcode.

The timeline breaks down roughly as: month one for the networking layer (server, protocol, state sync, disconnect handling), month two for prediction and reconciliation (the iterative "feels right" tuning), month three for testing and edge cases, and months four through six for optimization, geographic deployment, and matchmaking.

**Recommendation.** If the game experiences high demand, launch Model 1 (async) first — it's cheap, fast to build, and the generational structure makes asynchronous play feel natural rather than compromised. Upgrade to Model 2 if sustained demand justifies a persistent server. Only commit to Model 3 if the player base is large enough to justify the infrastructure spend, and at that point the revenue likely supports hiring a dedicated netcode engineer — someone who has solved these problems before and knows which corners can be cut safely.

**Architectural preservation.** To keep multiplayer viable as a future option, the following properties of the simulation must be maintained: deterministic output given the same inputs (same seed + same decisions = same state), symmetric faction agent interface (human and AI agents are interchangeable), serializable world state (the full simulation state can be exported and imported as a compact data structure), and clean separation between the simulation backend and the Godot frontend (the WebSocket interface already enforces this).
