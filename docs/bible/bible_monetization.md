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

**Free version:** The player gets access to a significantly limited experience. Reduced unit variety, less dynamic simulation behavior, and a limited pool of AI-generated content. The free version includes an opportunity to try a set number of simulations using the paid-tier AI-generated content library — enough to feel the difference — after which the player needs to subscribe to keep receiving new content. The free version is a genuine taste of the game, not a crippled demo, but the depth gap with the paid version should be obvious and enticing.

**Subscription ($3–5/month):** Full access to the complete game including the base sci-fi theme and a selection of included time period expansion packs. Cancel anytime. This is the primary revenue model. Marketing material on the Steam page highlights subscription content — the rotating library, the expanding era catalog, the living game that grows over time. The subscription funds ongoing AI content generation and new expansion development.

**Expansion packs (one-time purchase):** Individual time period packs sold as standalone purchases for players who want a specific era without subscribing. This is the secondary revenue channel. Expansion packs are permanent additions to the player's library.

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
