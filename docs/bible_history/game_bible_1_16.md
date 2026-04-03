# Ouroboros Manifold — Game Bible

> **This is the single source of truth for the game's design.** All conceptual decisions live here. No implementation details — those belong in architecture and stage docs that reference this file. If something in another doc conflicts with this file, this file wins.
>
> **MODIFICATION RULE: This document is append-only unless Westley explicitly approves a deletion.** AI sessions may add new sections, expand existing sections, and resolve open questions by writing answers into the appropriate section. AI sessions may NOT delete, overwrite, or replace existing decided content. If new information conflicts with existing content, flag the conflict for Westley to resolve — do not silently overwrite. This rule exists because multiple AI sessions contribute to this document, and silent deletions have already caused loss of decided design work.
>
> **OPEN QUESTION GOVERNANCE:** The "Open Design Questions" section at the end of this document is a staging area, not a permanent home. When an open question is resolved through brainstorming, the answer must be written into its natural section in the bible, and the question must be removed from the open list. If you are an AI session reading this document and you notice decided design content that still appears as an open question (or vice versa — an unresolved question living only inline with no entry in the open questions section), flag it for Westley.
>
> **Last updated:** April 1, 2026 (v1.16) — Technology system added: single numeric tech_level (0–100) per faction, archetype-interpreted multipliers, breakaway inheritance. Tech tiers added: 3–4 tiers per era unlock visual and mechanical unit variants through era-specific theme pack content. Diplomacy system partially resolved: three diplomatic states (hostile/neutral/cooperative), cooperative benefits (adjacency sharing, border friction removal, tech convergence with diminishing returns per partner), event-driven peace formation through sustained non-aggression, per-tick archetype-scaled betrayal mechanic, no reputation consequences (future consideration). Starting era confirmed as sci-fi (Asimov-inspired); historical eras are expansion packs. Automated balance testing pipeline added to AI Integration Pillar. Tech sharing formula (Q6 sub-question) and tech growth formula/multiplier magnitude/tier boundaries (Q7) remain open. Previous: (v1.15) Simulation pacing overhaul, player civilization mortality, per-faction lifecycle model, time jump range reduced to 20–100 years. (v1.14) Chronicle template authoring framework fully resolved.

---

## Table of Contents

1. [Vision and Identity](#vision-and-identity) — What the game is, what it feels like, what it's not
2. [The Simulation Backbone](#the-simulation-backbone) — SD model, event chains, region state, tick loop, composite axes, coherence ledger
3. [The Generational Structure](#the-generational-structure) — Chapters, cycles, what carries over
4. [Missions](#missions) — Generation, archetypes, objectives, difficulty, briefings, complications
5. [The Player's Toolkit](#the-players-toolkit) — Assets, force composition, economy, commanding forces
6. [Force and Combat Design](#force-and-combat-design) — Unit categories, unit differentiation, AI-generated variety, combat layers, tactical variety
7. [The Antagonist System](#the-antagonist-system) — External archetypes, internal threats, spatial manifestation, progression
8. [The Chronicle](#the-chronicle) — Narrative record, time jump montages, long memory
9. [The World](#the-world) — Scale, world generation, inter-region topology, era evolution, civilizational lifecycle, spatial navigation, map generation, visual style
10. [Tone and Feel](#tone-and-feel) — Elegiac, humorous, weighted by time
11. [What's Unique (Blue Ocean)](#whats-unique-blue-ocean) — The combination no other game offers
12. [Expansion Packs and Monetization](#expansion-packs-and-monetization) — The skeleton/skin model, time period expansions, subscription tiers, free version, distribution infrastructure, in-game Era Library, platform-agnostic entitlements, unit skins, multiplayer considerations
13. [AI Integration Pillar](#ai-integration-pillar) — Library pipeline, dynamic naming system, unit tuning, chronicle generation, 3D asset pipeline
14. [Transition from Previous Iteration](#transition-from-previous-iteration) — What survives, what's cut, what changes
15. [Open Design Questions](#open-design-questions) — Resolved design decisions (all current questions resolved as of v1.14)
16. [Document Maintenance](#document-maintenance) — Rules, workflow, governance

---

## Vision and Identity

### What This Game Is

Ouroboros Manifold is a single-player sci-fi strategy game set in a living, stochastic world. The player is not a god, not a king, and not the leader of a civilization. The player is **a commander** — one person given an impossible task by a civilization that has its own plans, its own politics, and its own momentum. The world does not revolve around the player. It moves on its own. The player is a piece of the puzzle.

The game is structured as a **generational chain of missions**. Each mission is a chapter. Between chapters, time jumps forward — decades or centuries — and the world evolves through the simulation. The player then returns as a new character: a descendant, a successor, or someone shaped by the consequences of what came before. The player's career across generations IS the story.

### The Core Fantasy

You are a commander in a vast civilization. You are given a force, a mission, and a deadline. The mission is difficult — perhaps impossible. While you work, the world keeps turning. Factions rise and fall. Threats emerge. History happens around you, and your mission is one thread in a much larger tapestry.

When your mission ends — success, failure, or something in between — time jumps forward. The simulation runs. The world changes in ways shaped by what you did, but not controlled by it. And then you return as someone new, in a world that remembers what happened even if your new character doesn't fully understand it.

Over the course of many chapters, you experience the arc of a civilization — its rise, its crises, its potential extinction — not from above, but from inside. You are always one person with limited tools, trying to make a difference in a universe that is genuinely uncertain.

### The Feeling

The tragedy of understanding something you can't fully control. You can read the situation, make the right call, commit your forces — and it still might not be enough. Not because the game cheated, but because the world is too big and too alive for one hand to hold it all. That's the Foundation feeling. You're not Hari Seldon. You're Hober Mallow — inside the machine, reading the currents, doing what you can.

### Closest References (What It's NOT)

- **Not Stellaris** — you don't manage a whole empire's economy, diplomacy, and military. You command a task force on assignment.
- **Not Total War** — there's no separate campaign map / battle map split. It's one continuous world.
- **Not a god-game** — you don't hover above the world pressing buttons. You're in it.
- **Closest comparisons** — the strategic layer of FTL (limited resources, hard choices, things going wrong), the emergent narrative of Crusader Kings (stories that emerge from systems), the spatial command of Homeworld (forces in 3D space), the living world of Dwarf Fortress (simulation that doesn't care about you), the unit control philosophy of Halo Wars (heavy units individual, light units as squads), the combat design of Immortal: Gates of Pyre (RPS-with-exceptions, accessible depth). But none of these are quite right. The game is its own thing.

### Design Inspiration

**Isaac Asimov's Foundation series** is the primary narrative and thematic inspiration for the game. The feeling of vast civilizational arcs, the tension between individual action and historical momentum, the sense of reading currents in a world too large for any one person to control — this is the Foundation feeling translated into interactive form. The game is set thousands of years in the future, in a world of humans, and the player experiences the rise and fall of civilizations from inside, not above.

Immortal: Gates of Pyre is a key source of inspiration for the game's combat and accessibility philosophy — particularly its approach to low skill floor with high skill ceiling, and its RPS-with-exceptions unit design. See the Force and Combat sections for how these ideas are adapted.

---

## The Simulation Backbone

The world simulation runs underneath everything. It is the engine that makes the world alive. The simulation is **not the game** — it is the world the game takes place in. The player interacts with it through missions, not through direct manipulation.

### What the Simulation Does

- Tracks the state of a civilization across multiple systems and regions, starting small and expanding over time
- Models each region's health through granular state fields (military strength, economic output, factional tension, population) and derives composite axes (stability, capacity) from them
- Fires events stochastically through an event chain architecture — events can spawn follow-up events with delays and conditions, producing coherent cause-and-effect sequences
- Generates emergent narrative through a coherence ledger that tracks named characters and their lifecycles. Cause-and-effect threads are tracked through the event log's chain tags, not duplicated in the ledger
- Runs an antagonist system with multiple external archetypes and emergent internal threats (revolts, breakaway factions, coups)
- Expands the inhabited world over time as the civilization grows — new regions and systems come online through expansion events
- Resolves toward macro outcomes: **Survival**, **Exodus** (civilization escapes to another world), or **Extinction with Amnesia** (civilization dies, relics remain)

### Sacred Design Principles

These are non-negotiable. Any feature that violates these is wrong.

1. **Genuine stochasticity.** Outcomes are truly uncertain. Multiple forces compete every tick — player effects, faction agent actions, and universe noise — and none fully controls the result. Never fake uncertainty.
2. **The simulation models civilizational state as a layered multi-dimensional space.** Granular per-region fields (military strength, economic output, factional tension, population) are the ground truth. Composite axes (stability, capacity) are derived from those fields and govern the simulation's big-picture decision-making. What is sacred is that the simulation tracks real, meaningful state at both granular and composite levels.
3. **Era-agnostic architecture — THE REVENUE PRINCIPLE.** This is not just an architectural guideline. It is the foundation of the game's entire commercial model. Every dollar the game makes after launch depends on this principle being maintained from day one. Violating it creates technical debt that blocks the expansion pack pipeline — the primary revenue engine.

   The simulation engine, mission generator, faction agents, event chains, combat system, and game loop operate on **abstract mechanical concepts only**. The sci-fi setting is a **theme pack** — a content layer that the AI library generates and the engine consumes. The engine never says "starship"; it says "heavy combat unit." The engine never says "star system"; it says "region." The engine never says "fleet"; it says "force group." The theme pack maps those abstractions to a battlecruiser in sci-fi, a trireme in a Greek theme, a Tiger tank in a WW2 theme, a dragon in a fantasy theme. The current and sole focus is the sci-fi theme — but the architecture must support any theme without engine changes.

   **What this means in practice for every AI session and every line of code:**
   - No simulation code, no event template schema, no faction agent logic, no drift formula, no config value name may reference a specific era, setting, or theme. "military_strength" is correct. "fleet_power" is wrong. "region" is correct. "star_system" is wrong. "heavy_combat_unit" is correct. "battleship" is wrong.
   - The theme pack is a separate content layer that maps abstract types to era-specific names, art, and prose. This layer does not exist yet and does not need to until visual work begins. But the simulation must never make it hard to add.
   - If you are an AI session writing code and you are tempted to use a sci-fi term because it's more readable — don't. Use the abstract term. Readability is solved with comments, not with era-specific vocabulary baked into the engine.
   - Future eras are cosmetic/superficial swaps with minimal functional differences — the same mechanics, same simulation, same event chains, different names, art, and prose.
   - **This principle applies to this document as well.** The game bible describes mechanics, not settings. Sections that describe the engine, the simulation, the combat system, the mission generator, and the game loop must use abstract vocabulary. Theme-specific terms (like "starship" or "galaxy") belong only in the Vision and Identity section (which describes the game's default sci-fi presentation to players) and in the Expansion Packs section (which discusses theme packs by name). Everywhere else, the bible speaks the engine's language.

   See "Expansion Packs and Monetization" for how this architecture becomes the revenue engine. The skeleton (engine) ships once. The skins (theme packs) ship forever. Every expansion pack is pure content — no engine changes required. That is only true if this principle is never violated.

### Simulation Architecture — System Dynamics with Stochastic Event Chains

The simulation is built on a **System Dynamics (SD) model** — an established mathematical framework using stocks and flows. Stocks are accumulating quantities (the region's state fields). Flows are rates of change between stocks, defined by rate equations that reference other stocks. The system evolves over discrete time steps (ticks).

On top of the SD foundation sits a **stochastic event chain layer**. Events are discrete dramatic moments that interrupt and redirect the continuous model. Events fire based on probability rolls weighted by current state, and events can spawn follow-up events with delays and conditions — producing coherent cause-and-effect chains rather than isolated random occurrences.

The SD layer handles the slow background hum of civilizational change (population growth, economic drift, military decay). The event chain layer handles the things that *happen* — famines, revolts, breakthroughs, invasions. Faction agents operate on top of both layers, making strategic decisions about attacks and defense. This separation means the simulation produces both gradual trends and dramatic moments, which gives the chronicle distiller rich material to work with.

**Why this architecture:** System Dynamics was chosen over Agent-Based Modeling (too computationally expensive and hard to tune for a solo dev) and brute-force rule engines (maintainable at 50 rules, nightmare at 500). SD is well-documented, has decades of literature on tuning and debugging, and its stock-and-flow structure maps directly to the game's needs. The event chain layer is the game-specific innovation that makes the output feel like history rather than graphs.

### Region State Model — Layered Architecture

Each region in the world carries two layers of state:

**Granular fields (ground truth)** — the raw data that events read and write. Starting set of four fields, with more added incrementally during development:

**Military Strength (0–100)** — the region's ability to defend itself and project force. Encompasses garrison size, force readiness, defensive infrastructure. Below ~30, a region can't meaningfully resist attacks from hostile factions or suppress internal unrest. Military strength decays when economic output is low — you can't maintain a force you can't feed.

**Economic Output (0–100)** — how much the region produces and contributes to the civilization's resource pool. Funds military maintenance, cultural projects, tech research, trade convoys. Suppressed by high factional tension (internal conflict disrupts production). Degraded by population loss.

**Factional Tension (0–100)** — how fractured and internally conflicted the region is. At 0, the population is unified (or quiet). At 100, the region is on the verge of civil war. This field drives internal antagonists: revolts, coups, breakaway factions, extremist movements. Factional tension has natural growth pressure — it tends to rise in prosperous, populated regions because success breeds competing interests. It rises faster under stress (low economy, military losses, hostile faction proximity). It decreases through cultural investment, successful crisis response, and stabilizing leadership.

**Population (0–100)** — normalized population relative to regional capacity. The foundation everything else scales from — a region with very low population can't sustain high military or economic output. Population is the slowest-moving field; it doesn't swing wildly tick to tick. It grows slowly under good conditions and drops from famine, plague, war, evacuation, and devastation. A region that loses population takes a long time to recover, which is what makes late-game collapse feel permanent.

**Key field interactions:**
- Military strength decays when economic output is low (can't maintain what you can't fund)
- Economic output is suppressed by high factional tension (internal conflict disrupts production)
- Factional tension rises when population is high but economic output is low (lots of people competing for scarce resources)
- Population slowly declines when economic output is very low (people leave or starve)
- Low military strength in a region with hostile factions nearby accelerates all negative trends (the region can't protect itself)

**Composite axes (derived lens)** — computed from the granular fields. The simulation's big-picture decision-making (event probability, mission generation, faction agent targeting) operates on these axes rather than raw fields. Starting set of two:

**Stability** — derived from military strength, factional tension (inverted), and population. Represents how secure and cohesive the region is. Used to determine whether the region is at risk of crisis events.

**Capacity** — derived from economic output, population, and military strength. Represents the region's ability to contribute to the civilization and sustain itself. Used to determine resource availability and mission asset allocation.

**Derivation method: weighted average with threshold penalties.** Each composite axis is a weighted average of its contributing fields, with critical-failure penalties when any single field drops below a dangerous threshold.

```
stability = (military * w1) + ((100 - factional_tension) * w2) + (population * w3)
if military < threshold_military: stability *= penalty_military
if population < threshold_population: stability *= penalty_population
```

The weights, thresholds, and penalty multipliers are tuning values in config. The structure of the formula is the design decision; the specific numbers are tuned during Stage 0 by running the simulation and reading output.

This layered model means the mission generator and event system can read specific fields when they need granularity ("is this a military problem or a political one?") while the simulation's macro behavior is governed by a small number of meaningful composite scores.

### Per-Tick Update Model

Each granular field updates per tick using the SD stock-and-flow pattern:

```
field_new = clamp(field_old + delta, 0, 100)
```

The delta for each field is the sum of three sources:

**Passive drift** — slow background forces driven by the field's relationships with other fields. Each field has its own drift formula:

**Military Strength drift:**
```
maintenance_cost = military * decay_rate
affordable = economic_output / 100
decay = -maintenance_cost * (1 - affordable)
recruitment = recruitment_baseline
if economic_output > recruitment_threshold:
    recruitment += recruitment_rate * (economic_output / 100) * (1 - factional_tension / 100) * max(0, (1 - military / recruitment_ceiling))
recruitment *= max(0, (1 - military / recruitment_ceiling))
drift = decay + recruitment
```
Military decays proportionally to how much the economy can't sustain it. High economy = no decay. Zero economy = full decay. Under good conditions (strong economy, low internal tension), military slowly recovers through recruitment — representing a civilization rebuilding its forces during peacetime. Recruitment has a **baseline term** that always fires for inhabited regions regardless of economy, representing militia raised from the local population. This prevents frontier regions (which rarely reach the economy threshold) from collapsing to near-zero military through pure decay. The economy-scaled recruitment term adds on top of the baseline when the economy exceeds the recruitment threshold. Both terms share the same logistic headroom limiter: the `(1 - military/recruitment_ceiling)` term creates logistic saturation so recruitment slows as military approaches a ceiling (config value, e.g. 70). The `(1 - tension/100)` term smoothly suppresses the economy-scaled recruitment as tension rises (no hard cutoff — high tension makes recruitment difficult but not impossible). Drift alone cannot push military past this ceiling — only direct spending (reinforcement actions, Emergency Levy events) can exceed it. This prevents the design hole where zero decay at high economy allows unbounded military growth. The baseline ensures a gradient: weak frontiers (economy ~25) settle at military ~8, average frontiers (economy ~35) at ~9, strong frontiers (economy ~50) at ~12, while home regions are unaffected because the baseline is negligible compared to their economy-scaled recruitment.

**Economic Output drift:**
```
owned_neighbors = adjacent regions owned by same faction
adjacency_bonus = sum(neighbor.economy / 100 * neighbor_economy_bonus for each owned neighbor)
tension_drag = factional_tension_trend / 100 * tension_penalty_rate    # reads de-oscillated tension
population_factor = population / 100
oscillation = econ_oscillation_amplitude * sin(2 * pi * tick / econ_oscillation_period + econ_phase_offset)

drift = (base_growth * population_factor) - tension_drag + adjacency_bonus + oscillation
```
Economy has natural growth scaled by population (more people = more production), dragged down by factional tension (internal conflict disrupts output). A stable, populated region slowly grows. A tense region bleeds output. Note: tension_drag reads the de-oscillated tension trend value to prevent feedback amplification (see "Economic oscillation" below). The adjacency bonus reads the neighbor's real oscillated economy value — adjacency is an external read, not a drift coupling, so it correctly reflects the neighbor's actual current state.

**Territorial adjacency bonus:** Each owned region benefits economically from connected faction territory. The bonus is proportional to each neighbor's economic output — a colony next to a booming core region develops faster than one next to another struggling frontier. This creates natural economic gradients where regions near the faction's center of power are more productive than those on the fringe. The adjacency bonus uses all edge types equally (typed adjacency bonuses are a potential refinement after the base mechanic is proven).

**Economic oscillation:** Economy oscillates around its trend line via a **feedback-isolated additive** mechanism, representing natural boom-bust cycles. The oscillation is additive on the field itself — agents, budget growth, and attractiveness scoring all read the real oscillated value, creating genuine windows of vulnerability during troughs. However, cross-field drift coupling (military decay, tension prosperity pressure, recruitment threshold checks) reads **de-oscillated values** — the underlying trend with the oscillation term subtracted out. This breaks the feedback loop that would otherwise amplify oscillation through coupled fields (early testing showed pure additive oscillation caused frontier economy to deviate ±24 from baseline and tension to hit zero through feedback amplification). Over a full cycle the oscillation sums to approximately zero, so the long-term trend is determined entirely by the base drift terms. Each region receives a random phase offset at world generation so regions oscillate out of sync — there is always somewhere peaking and somewhere dipping. Flat amplitude (same swing size regardless of economy level) means low-economy frontier regions experience proportionally larger swings, making them the natural flashpoints for conflict. Config values: `econ_oscillation_amplitude` (verified: 6.0, representing ±6 economy points per half-cycle), `econ_oscillation_period` (verified: 100 ticks per full cycle — long enough that a trough lasts ~50 ticks for agents to exploit, short enough that the long-term trend dominates).

**Factional Tension drift:**
```
prosperity_pressure = (population * economic_output_trend) / 10000 * prosperity_tension_rate    # reads de-oscillated economy
stress_pressure = max(0, stress_threshold - stability_composite) * stress_tension_rate
natural_decay = tension_natural_decay_rate * (factional_tension / 100)
oscillation = tension_oscillation_amplitude * sin(2 * pi * tick / tension_oscillation_period + tension_phase_offset)

drift = prosperity_pressure + stress_pressure - natural_decay + oscillation
```
Tension has two growth sources. Prosperity pressure: high population and high economy breed competing interests (success creates politics). Stress pressure: low stability creates fear and blame. Natural decay is **proportional to current tension** — higher tension produces stronger decay forces, representing the increasing pressure to resolve disputes as tension mounts. At low tension, grievances fester slowly; at high tension, the forces pushing toward resolution (war exhaustion, political compromise, population flight) are powerful. This proportional structure creates a real equilibrium where growth sources balance against decay, preventing the runaway tension spirals that occur with constant decay. Tension rises in both good times and bad, but for different reasons — it only truly drops when a region is stable but modest.

**Tension oscillation:** Tension carries its own smaller oscillation representing political cycles — periodic swells of unrest followed by periods of relative calm. Like economic oscillation, the mechanism is **feedback-isolated additive**: the oscillation is additive on the field itself (agents and event threshold checks see the real oscillated value), but other drift formulas that read tension as an input (e.g., economic tension drag) read the de-oscillated trend value. This prevents tension oscillation from feeding back into economic drift and vice versa. The amplitude is smaller than economy's (verified: 2.0 vs 6.0) because tension oscillation should be a contributing factor to crises, never the primary cause. A tension uptick alone shouldn't trigger a revolt — but a tension uptick that coincides with an economic trough and a military loss can push a region over an event threshold, creating the emergent compounding that produces unpredictable crises. Each region's tension phase offset is independent of its economic phase offset, so the two cycles drift in and out of alignment naturally. When they align unfavorably (economic trough + tension peak), the region is maximally vulnerable. Config values: `tension_oscillation_amplitude` (verified: 2.0), `tension_oscillation_period` (verified: 125 ticks — slightly longer than the economic cycle so the two don't lock into a fixed relationship).

**Population drift:**
```
if economic_output > subsistence_threshold:
    drift = growth_rate * (1 - population / 100)
else:
    deficit = subsistence_threshold - economic_output
    drift = -deficit * decline_rate
```
Population grows logistically when the economy can feed people (faster when low, slowing near capacity). Population declines when the economy drops below subsistence, proportional to the deficit. This makes population the slowest, most inertial field — sustained bad conditions to shrink it, sustained good conditions to grow it back.

**Event effects** — discrete changes from fired events. An event template specifies direct field modifications (e.g., "garrison reinforced: military +15" or "famine: population -10, economic output -20"). These are authored per event template in the library. No formula — just the event's impact applied directly. Attack events from hostile factions are a subset of event effects — they apply damage to the defending region's fields based on the attack's strength and the defender's resistance.

**Border friction** — regions bordering hostile factions experience per-tick negative effects scaled by the hostile neighbor's military strength. For each hostile border edge, friction applies: `tension_friction = base_tension_friction * (hostile_neighbor_military / 100)` and `economy_friction = base_economy_friction * (hostile_neighbor_military / 100)`. A hostile neighbor at military 80 produces 4× the border stress of one at military 20 — a massive hostile force on your border is genuinely more stressful than a token garrison. A region with multiple hostile borders accumulates friction from each edge. This creates a natural pressure gradient where the Conqueror's heavily militarized border regions radiate stress into adjacent player territory, softening it before an attack — border friction is how empires project power without fighting. Border friction is not military pressure — it's the background stress of living on a contested border: disrupted trade, civilian anxiety, military logistics overhead. The base rates (`base_tension_friction`, `base_economy_friction`) are small per-tick config values tuned during Stage 3. Regions with no hostile border neighbors experience no friction.

All coefficients (decay rates, drain rates, scaling factors) are tuning values in config. The formulas' *structures* are the design decision. The specific numbers are what gets tuned during Stage 0.

**Economy floor.** A region's economy cannot drop below a configured floor value (e.g., 8.0) from drift, border friction, or standard events. This represents subsistence-level economic activity that persists through normal crises — people still farm, local trade still happens. The floor prevents the permanent death trap where economy=0 locks out all recovery paths (no economy → no military maintenance → no recruitment → no stability → death spiral). **Conquest events bypass the floor entirely** — economy can drop to zero from conquest damage, representing total infrastructure destruction. A conquered region at economy=0 is not permanently dead: the additive adjacency bonus from neighboring regions and base population growth still apply through drift, so the region recovers slowly under its new owner. But recovery from zero is very slow (estimated 100–200 ticks to reach subsistence levels depending on neighbor strength), which means rapid conquest produces an empire of devastated territory that can't sustain itself — the natural overextension penalty. The floor is enforced as a clamp after computing drift and event effects: `economy = max(economy, economy_floor)`. Conquest events carry a bypass flag that skips this clamp.

**Reinforcement diminishing returns.** The reinforce agent action (spending faction budget to boost a region's military) has diminishing effectiveness as the region's military approaches a per-tier capacity ceiling. This represents logistical limits on how many reinforcements a region can absorb. The formula: `boost = budget_spent * reinforce_efficiency * max(0, (tier_cap - military) / tier_cap)`. Home regions have a high cap (100 — no practical limit), frontier regions have a lower cap (e.g., 60). The cap only limits what the reinforce action achieves — events, Emergency Levy, and other direct effects can push military above the cap. Without diminishing returns, the player civilization agent's constant reinforcement spending makes frontiers invincible (mil→90+), eliminating any possibility of conquest.

### Event Chain Architecture

Events are not isolated dice rolls — they are nodes in causal chains. When an event fires, it changes region state AND can schedule follow-up events into a pending queue with delays and conditions. The tick loop processes both the pending event queue (how existing chains continue) and fresh threshold triggers (how new chains start).

An event template contains: **immediate effects** (field changes applied when the event fires), **chain spawns** (a list of potential follow-up events, each with an event template ID, a tick delay range, a firing probability, and conditions that must be true when the scheduled tick arrives), **chain tags** (a label connecting all events in the same causal chain, so the coherence ledger and chronicle distiller can trace cause and effect), and **mutual exclusion tags** (see Event Collision Resolution below).

**Chain spawn delay resolution.** When a parent event fires, each of its chain spawns immediately rolls a specific delay from the spawn's configured delay range. The delay is sampled from a **triangular distribution** weighted toward the center of the range (e.g., a 3–8 tick range most often produces 5–6, with 3 and 8 being rarer). This center-weighting produces more natural clustering of chain timing and is more robust at scale with AI-generated templates — loose delay ranges still produce reasonable timing because extreme values are dampened. The rolled tick number is absolute (current tick + rolled delay) and goes into the pending queue immediately. Python's `random.triangular(low, high, midpoint)` implements this directly.

**Chain tags are for narrative tracking, not suppression.** A chain tag is generated when a new chain starts (from a threshold trigger) and propagates to all chain spawns and their descendants. The tag connects the entire causal lineage so the coherence ledger can trace cause and effect. Chain tags do NOT suppress re-firing of the root template — if the threshold is crossed again, a new independent chain starts with its own tag. Multiple chains from the same template can coexist in the same region, representing overlapping crises. This is historically authentic: real civilizations deal with concurrent crises that share root causes.

**Pending queue — condition checks and failed conditions.** When a pending queue event's scheduled tick arrives, the system checks whether the event's conditions are met against the current region state. If conditions are met, the event rolls against its authored firing probability. If conditions are NOT met, the event is **silently dropped** from the queue — the branch is pruned. The world moved on and the crisis resolved itself before it could escalate. This means player actions during missions that improve a region's state can prevent follow-up events from firing, making intervention feel meaningful. The coherence ledger logs pruned branches for narrative tracking ("the revolt that almost happened but didn't").

Example: "Factional Tension Rising" fires and applies factional_tension +10. It spawns three potential follow-ups: "Regional Revolt" in 3–8 ticks at 40% if factional tension is still above 60; "Political Compromise" in 5–12 ticks at 30% if stability has recovered above 40; "Extremist Movement Forms" in 8–15 ticks at 20% if factional tension has continued rising. Only the ones whose conditions are met when their tick arrives will roll for firing. The world's state at the moment of resolution determines the outcome — chains can be disrupted by intervening events or player mission outcomes.

### Event Collision Resolution

When multiple events are due on the same tick in the same region (from the pending queue, fresh triggers, or both), they resolve **simultaneously**. All events calculate their field deltas independently against the region's state at the start of the tick (before any of them apply), then all deltas are summed and applied at once. No ordering, no sequencing — events that land on the same tick genuinely happen at the same time.

This means compounding disasters happen naturally: a revolt and a hostile faction's attack hitting the same region on the same tick produce combined damage. This fits the Foundation-inspired feeling that the world is too vast for neat sequential cause-and-effect.

**Mutual exclusion tags** prevent logically contradictory events from co-firing. Event templates can carry exclusion tags (e.g., "political_resolution" and "political_crisis" are mutually exclusive). When two mutually exclusive events are both due on the same tick in the same region, the one with the higher firing probability wins; the other is pushed back 1–2 ticks (delayed, not canceled — the chain survives). **Tie-breaking: if two mutually exclusive events have equal firing probability, the winner is chosen by random coin flip** — consistent with the simulation's stochastic philosophy. Mutual exclusion applies based on the tags regardless of which chains the events belong to — it's about logical contradiction, not chain lineage. Most collisions don't involve contradictions and just compound naturally. The mutual exclusion system is a small, contained check, not a full priority ordering.

### Event Probability — Threshold Triggers with Noise

New event chains do not start from per-tick probability rolls. Instead, events fire when a region's field **crosses a threshold** defined in the event template. Factional tension crosses 60? That triggers "Tension Rising." Military drops below 25? That triggers "Garrison Vulnerable." The tick loop checks each region's fields against the threshold table after passive drift is applied.

**Threshold triggers are deterministic.** When a field crosses a noised threshold, the event fires — no probability roll. The stochasticity was already baked in when the noise offset was rolled at the start of the time jump. This is distinct from pending queue events (chain spawns), which DO roll against their authored firing probability when their scheduled tick arrives. The two mechanisms serve different roles: threshold triggers start chains deterministically (making every chain's origin explainable), while probability rolls filter which branches of an existing chain actually play out.

**Threshold direction.** Each event template's threshold specifies an explicit direction: `above` or `below`. "Tension Rising" triggers when factional tension crosses 60 going **above**. "Garrison Vulnerable" triggers when military crosses 25 going **below**. The direction is part of the template definition — there is no inference from delta signs or other indirect logic.

**Re-fire prevention — rising-edge detection only.** Events fire on the **transition** from one side of the threshold to the other (rising edge for `above` triggers, falling edge for `below` triggers). The system compares the field's value before and after the tick's updates: if it was below last tick and is at-or-above now, that's a crossing for an `above` trigger. If it was already above last tick, no fire — even if the field is still above the threshold. There are no cooldowns, no suppression timers, and no chain-based re-fire prevention on the trigger itself. If a field drops back below the threshold and crosses it again later, the event fires again as a new independent chain. Each firing applies full-strength deltas.

**The simulation's existing SD dynamics handle resilience and compounding.** Repeated firings of the same template are not artificially dampened. A region with strong economy and high stability absorbs a tension +10 and recovers through proportional decay. A region that's already fragile takes the same hit and spirals. The event system provides dramatic punctuation; the SD model determines whether the region absorbs it or breaks. This means the oscillation mechanics (which periodically swing fields through threshold zones) create natural windows where events fire — but each firing pushes the field further past the threshold, making the next crossing less likely until drift or oscillation brings it back. The event's own effect is self-regulating through the field dynamics.

**Noise prevents deterministic repetition.** Each event template's trigger threshold gets a random offset within a defined range (e.g., ±10) rolled once per region at the start of each time jump. So one region's "Tension Rising" might trigger at 52, another's at 67. The offset persists for the duration of the time jump, giving each region a consistent "personality" — a region that's sensitive to factional tension stays sensitive throughout the cycle.

The threshold-trigger model means every event is *explainable* — you can always trace why a chain started by looking at which field crossed which threshold. This makes debugging straightforward and produces clear causal material for the coherence ledger.

### Tick Resolution Sequence

Each tick processes in this order:

1. **Process the pending event queue** — check if any scheduled events are due this tick. For each, roll against its firing probability. Events that fire resolve immediately: state changes applied, event log updated with chain tags, named character attachments recorded in the coherence ledger, new chain spawns added to queue.
2. **Evaluate fresh event triggers** — for each region, check current field values against the event threshold table (with per-region noise offsets). Any threshold crossed triggers a new event chain. This is how new chains start.
3. **Run all faction agents** — each faction evaluates the current post-event state and makes its decision for this tick: accumulate budget, launch an attack, colonize, or reinforce a defensive position. **Attack events resolve immediately within step 3** — the attack resolution formula runs inline, field damage is applied to the target region, and if the defender's military drops below the conquest threshold, a Conquest event is inserted into the pending event queue for processing on the next tick. Conquest follow-up chains (resistance movements, refugee flows, morale effects) propagate through the event chain system's existing chain spawn infrastructure. Defensive reinforcements apply field changes to the target region directly. Faction agents act after events so they can exploit emerging crises — an agent sees the post-event state of regions (including damage from events that fired in steps 1–2), making attack timing strategically meaningful. The player's civilization runs the same agent framework as all other factions, with a conservative defensive posture.
4. **Apply border friction** — for each region bordering a hostile faction, apply minor per-tick tension and economic drag. This is the background stress of contested borders, not active military engagement.
5. **Apply passive drift** — the per-tick SD flow calculations for each field in each region. The slow background changes.
6. **Recompute composite axes** — recalculate stability and capacity for each region from the updated granular fields.
7. **Log everything** — write the tick's events, state changes, faction agent actions, and border friction to the event log with causal chain tags preserved. Update the coherence ledger with any named character involvement.

### Simulation Pacing Targets

The simulation is tuned for a **dynamic, WorldBox-inspired world** where civilizations rise and fall as a natural part of the game's rhythm. The world is always in motion. Territory changes hands regularly. Factions expand, clash, fragment, and new ones emerge from the wreckage. No faction — including the player's — has plot armor or guaranteed survival.

**Pacing goals for any 20–30 tick window** (the minimum time jump duration, representing roughly 20–30 years of in-world time):

- Multiple attacks should occur across factions on the map
- At least one conquest or territory change is typical
- Faction births (from revolts/breakaways) and faction collapses should be occasional but not rare
- The chronicle scroll for any time jump should have enough dramatic material to fill 5–10 entries without difficulty

**Why this matters for the player experience.** During the chronicle scroll between chapters, players watch faction territories change on an animated map — borders shifting, regions changing color, new factions appearing. This is the game's signature moment of "the world moved without you." If the map is static for 100 ticks, the scroll is boring and the game's core fantasy fails. The simulation must produce visible, dramatic change at every timescale.

**No faction is immortal.** The player's civilization can collapse — conquered, fragmented, or ground down to nothing. When this happens, the generational structure handles it by assigning the player to a new faction (see "Player Civilization Mortality" in The Generational Structure). This is not a failure state. It is a narrative event — one of the most dramatic the game can produce. The chronicle frames the fall, and the player continues as a commander in a different civilization that inherited the world shaped by everything that came before.

**The world is dangerous from the start.** There is no protected early game where external threats are absent. Faction agents begin making attack decisions as soon as budgets allow, which with proper tuning means first inter-faction military contact occurs within the first time jump. The player's very first chapter could be a defense mission against an aggressive neighbor. The world does not wait for the player to be ready.

**Tuning levers for pacing.** The simulation's event frequency is controlled by: budget growth rate (how fast factions can afford attacks), attack confidence thresholds (how much budget surplus is needed before attacking), reinforce budget reserve ratio (how much budget factions protect for offense vs. defense), resistance factor (how effective defenders are), and conquest consequences (how costly it is to hold new territory). These parameters are tuned together to hit the pacing targets above. If the world is too static, increase budget growth rate or decrease resistance factor. If factions collapse too fast, increase conquest consequences or reinforce efficiency.

### Multi-Faction Agent Decision Model

The world is a **free-for-all between multiple factions**. The player's civilization is one faction among several. External antagonist archetypes, breakaway factions from revolts, and the player's civilization all operate as faction entities within the same simulation framework. Every faction runs the same agent model — the system is symmetric and multiplayer-extensible.

**Faction entity model.** Each faction has: an ID, an archetype (or "player_civilization"), owned regions (tracked via faction_id on each region), a resource budget, a budget growth rate, a **tech_level** (0–100, see "Technology System" below), faction-level modifiers (e.g., a militaristic faction's regions get a military drift bonus, a trade-focused faction's regions get an economy drift bonus), a diplomatic stance toward other factions, and an **attack confidence threshold** rolled at world generation from an archetype-specific range. Faction-level modifiers influence region-level behavior — they are applied as small bonuses to the relevant drift terms in owned regions.

**Aggression variance — per-game faction personality.** Each faction's attack confidence threshold is rolled once at creation from a configured range per archetype (e.g., Conqueror: 12–18, player civilization: 40–60, breakaway: 8–14). The rolled value persists for the entire game and determines how cautiously or aggressively the faction fights. A low confidence threshold produces an aggressive faction that attacks with slim margins — more frequent attacks, more contested outcomes, grinding border wars. A high threshold produces a cautious faction that waits for overwhelming advantage — fewer but devastating attacks, more breakthroughs. This creates genuine stochastic divergence across playthroughs: the same archetype produces different war stories depending on its personality roll. The variance is rolled per faction, not per tick — it's the faction's strategic identity for this game.

**Budget accumulation.** Each faction's budget grows per tick based on the net economic contribution of its owned regions minus a per-region maintenance cost:

```
budget_growth = sum(region.economy - region_maintenance_cost for region in owned_regions) * archetype_growth_rate
```

The `region_maintenance_cost` is a flat per-region config value representing the administrative and logistical overhead of holding territory (garrison supply, governance, infrastructure upkeep). Each region must produce enough economy to cover its maintenance cost before it contributes to the faction's strategic budget. Regions that don't cover their cost are **net drains** — they actively reduce the faction's budget each tick.

This creates the core expansion risk/reward dynamic: a healthy home region (economy 60+) is a strong budget contributor. An established frontier (economy 30–40) is a modest contributor. A fresh colony (economy 8) is roughly breakeven or a slight drain. A conquered husk (economy 0–5) is a pure liability that bleeds the faction until it recovers. A faction that conquers five devastated regions watches its budget shrink tick by tick as maintenance on rubble outpaces income from its core — the natural overextension penalty. Expansion is an investment that must "come online" before it pays for itself, and if the faction loses the territory before that happens, it has wasted budget AND weakened itself.

The `region_maintenance_cost` starting point should be tuned so that fresh colonies are roughly breakeven (suggesting a value around 8–10, matching colony starting economy of 8). The `archetype_growth_rate` is a per-archetype multiplier that controls overall budget velocity — the Conqueror may grow budget slightly faster than the player's civilization, reflecting a war-economy focus. Both values are tuned during Stage 3.

**Faction agent decisions.** Each tick, every faction's agent evaluates its situation and makes one of four decisions:

- **Accumulate** — no viable attack or colonization target passes the expected outcome check (see below). Save the budget. The faction's borders are quiet this tick (minor border friction only, no military action). Factions accumulate to build toward offensive actions, but the simulation is tuned so that accumulation phases are finite — budget growth rates and attack thresholds are calibrated to produce regular attacks across the map within any given time jump window.
- **Launch attack** — the agent identifies a target where the expected outcome exceeds its rolled confidence threshold. The agent commits a fraction of its budget (config value, e.g. 70%) as attack strength. This spawns an **Attack event** targeting the enemy region.
- **Colonize** — an uninhabited region scores highest in the attractiveness evaluation and the agent has sufficient budget. The agent commits a portion of its budget as colonization investment. This spawns a **Colonization event** (see "Uninhabited Region Mechanics" below).
- **Reinforce** — the agent detects a threatened border and spends budget to boost a specific owned region's military, subject to diminishing returns based on the region's tier military capacity ceiling. This is a defensive spending action.

**Reinforce trigger — threat score evaluation.** For each owned border region adjacent to hostile territory, the agent computes a threat score based on adjacent hostile military strength, the region's own military relative to its tier cap, and the hostile faction's recent activity (attacks in the last N ticks). If any region's threat score exceeds a per-archetype config threshold, the agent reinforces it. The player's civilization has a low threshold (reinforces early — conservative defensive posture). The Conqueror has a high threshold (rarely reinforces, prefers attacking). Threat scores require the agent to read hostile neighbor military from the world graph — agents have perfect information about adjacent region military strength (see "Agent Information Model" below).

**Reinforce spending — threat-proportional with overreaction variance.** The agent computes a threat ratio for the target region: `adjacent_hostile_military / own_region_military`. The ratio drives a spending curve:

- Low threat (ratio below low_threat_ceiling, e.g., 0.8): spend nothing on this region, accumulate instead. The border is adequately defended.
- Moderate threat (ratio between low_threat_ceiling and high_threat_floor, e.g., 0.8–1.5): spend a moderate fraction of budget scaled by the ratio. The agent is matching the buildup.
- High threat (ratio above high_threat_floor, e.g., 1.5): spend aggressively — a large fraction of available budget. The civilization is scared.

On top of the computed spending amount, each reinforcement decision applies an **overreaction variance roll** — a random multiplier (config range, e.g. 0.5–1.5) representing institutional dysfunction. Sometimes the bureaucracy panics and sends twice what's needed. Sometimes it underfunds a critical frontier because the political class is distracted or the supply chain is strained. The variance range is modified by the region's current factional tension: high tension widens the range (more dysfunction, less predictable responses), low tension narrows it (stable government, rational allocation). This creates emergent behavior where a civilization under internal stress makes erratic defense decisions — over-reinforcing one border while neglecting another — which is exactly when it's most vulnerable to external attack.

The final budget spent (after variance roll) is subject to the existing diminishing returns formula: `boost = budget_spent * reinforce_efficiency * max(0, (tier_cap - military) / tier_cap)`. The spending curve breakpoints, variance range, and tension modifier are config values tuned during Stage 3.

**Expected outcome evaluation — smart attack decisions.** Before committing to an attack, the agent previews the attack resolution formula against the target's current military:

```
potential_commit = budget * commit_fraction
expected_attack = potential_commit * attack_efficiency
expected_defense = target_military * resistance_factor
expected_net = expected_attack - expected_defense

if expected_net > faction.attack_confidence:   # rolled per-game from archetype range
    attack is worth launching
else:
    keep accumulating
```

This self-calibrating logic means factions naturally adapt to the military reality. Against a weak frontier with military 20, the agent may attack with budget 40. Against a fortified core with military 70, the agent accumulates to budget 150 before striking. If the target's military is growing via recruitment, the agent sees the expected net declining each tick and either strikes before the window closes or redirects to a weaker target.

The colonize and attack decisions share a single candidate pool — the agent scores all eligible targets (enemy-owned and uninhabited), picks the best one, and the target type determines whether it's an attack or a colonization. This means a faction naturally shifts between expansion and aggression based on what opportunities the world presents.

**Agent decision selection — scored with archetype weights.** When multiple actions are viable on the same tick, the agent does not follow a fixed priority order. Instead, each viable action receives a score, and the highest score wins. The score incorporates both the *quality* of the action (how good is this attack? how urgent is this reinforcement?) and archetype-specific weights that bias the decision:

- Attack score = best_expected_net_force × `archetype_attack_weight`
- Colonize score = best_attractiveness_score × `archetype_expand_weight`
- Reinforce score = highest_threat_ratio × `archetype_defend_weight`
- Accumulate is the fallback when no other score exceeds a minimum viability threshold (config value)

The archetype weights express strategic personality. The Conqueror has high `attack_weight` and `expand_weight`, low `defend_weight` — it *usually* attacks but *can* defend when borders are critically threatened (high threat ratio overcomes low weight). The player's civilization has high `defend_weight`, low `attack_weight` — it *usually* reinforces but *can* counterattack when it has overwhelming advantage (high expected_net overcomes low weight). A breakaway faction has high `defend_weight` (survival mode) and moderate `attack_weight`.

The three raw scores (expected_net_force, attractiveness, threat_ratio) are on different scales. Each action type uses a normalization function (config-tunable) that maps its raw score to a 0–1 range before the archetype weight is applied. The normalization parameters and archetype weights are tuned during Stage 3, with per-tick decision logging that shows all four scores, the weighted results, and the winning action for debugging and tuning.

**Attractiveness scoring — archetype-specific.** Each archetype has its own function for evaluating which regions to attack:

- **The Conqueror** — uses **mixed attractiveness** across three factors: military weakness (easy targets), current economic and population value (worth taking), and strategic position (adjacency to valuable non-owned territory). The candidate pool includes both enemy-owned regions and uninhabited regions adjacent to the Conqueror's territory.

```
score = (w1 * weakness) + (w2 * current_value) + (w3 * strategic_position)

weakness = 1 - (target_military / 100)

current_value = (target_economy * we + target_population * wp) / 100

neighbors = [r for r in adjacent_regions if r.faction_id != conqueror.faction_id]
for each neighbor:
    if inhabited: neighbor_score = (neighbor.economy * we + neighbor.population * wp) / 100
    if uninhabited: neighbor_score = expansion_potential  # config value, e.g. 0.15
strategic_position = mean(neighbor_scores) if neighbors else 0
```

Starting config weights: `w1 = 0.40` (weakness — primarily opportunistic, which agrees with the attack resolution math that penalizes attacking strong targets), `w2 = 0.25` (current value — wealth matters but doesn't override caution), `w3 = 0.35` (strategic position — the Conqueror is an empire builder that values territorial contiguity). Sub-weights `we` and `wp` control the economy vs. population balance within the value calculations. The `expansion_potential` floor for uninhabited neighbors ensures empty regions that open up further expansion corridors are valued over dead ends. An uninhabited region scores: maximum weakness (1.0), zero current value, and strategic position based on what it borders — an empty region between the Conqueror and the player's wealthy core is a high-priority staging ground.
- **The Warlord** — uses the same three-factor formula as the Conqueror but with a reduced weakness weight (e.g., `w1 = 0.20`). The Warlord does not seek the strongest target, but doesn't prioritize the weakest either — reckless, not suicidal. Higher current value and strategic position weights mean the Warlord fights where it matters, not where it's easy.
- **The Fortifier** — uses the three-factor formula with a heavy strategic position bias toward regions that reduce the faction's border exposure (e.g., `w3 = 0.55`). Filling gaps in territorial contiguity and shortening the defensive perimeter score higher than raw economic value. Weakness weight is moderate — the Fortifier waits for overwhelming advantage, so it can afford to be selective about target quality.
- **The Opportunist** — uses the three-factor formula with an additional **recent damage multiplier**: regions that lost military or economy within the last N ticks (config value, e.g. 100–200 ticks) receive a score boost proportional to the magnitude of loss. When no recently-damaged targets exist, the multiplier is 1.0 and the Opportunist evaluates targets like a less aggressive Conqueror. The recent damage window and boost magnitude are config values tuned during Stage 3.
- **The Schism** — uses **factional tension** as the primary attractiveness factor instead of military weakness. `score = (w1 * target_tension / 100) + (w2 * current_value) + (w3 * weakness)`. High-tension regions score well regardless of military strength — the ideology spreads to the discontented. Does not evaluate uninhabited regions (the Schism only takes inhabited territory).

**Attack event resolution.** When a faction launches an attack, it fires as a discrete event in the target region. The outcome depends on the military comparison between attacker strength (the committed budget) and defender military, with a **resistance mechanic** and a stochastic element:

```
effective_attack = attack_strength * attack_efficiency
effective_defense = defender_military * resistance_factor
net_force = effective_attack - effective_defense
```

A stochastic modifier (random multiplier within a configured range, e.g. 0.7–1.3) is applied to net_force before outcome evaluation, ensuring evenly matched fights can go either way. The modified net_force determines both the outcome band and the magnitude of consequences — **damage scales proportionally to how decisive the outcome was**:

**Breakthrough** (net_force exceeds `breakthrough_threshold`, e.g. 15.0): The attacker overwhelms the defender. Damage scales with net_force magnitude — a narrow breakthrough is bad, a decisive one is devastating:
- Defender military: −(net_force × `breakthrough_mil_damage_scale`)
- Defender economy: −(net_force × `breakthrough_econ_damage_scale`)
- Defender tension: +(net_force × `breakthrough_tension_scale`)
- Attacker: committed budget fully spent
- If the defender's military drops below the conquest threshold as a result, a **Conquest event** fires (see below).

**Contested** (net_force positive but below breakthrough_threshold): The fight is inconclusive — both sides take moderate damage proportional to net_force, no territory changes:
- Defender military: −(net_force × `contested_mil_scale`)
- Defender economy: −(net_force × `contested_econ_scale`)
- Defender tension: +(net_force × `contested_tension_scale`)
- Attacker: committed budget fully spent, attacker's home region tension +(small fixed config value)

**Repelled** (net_force negative): The attack fails. The defender takes minor losses; the attacker suffers proportionally to how badly it miscalculated:
- Defender military: −(abs(net_force) × `repelled_defender_damage_scale`) — small, representing minor losses even in victory
- Attacker: committed budget fully spent, attacker's home region tension +(abs(net_force) × `repelled_tension_scale`) — a badly miscalculated attack causes significant domestic political fallout

All damage scale factors are config values tuned during Stage 3. The proportional scaling means a decisive breakthrough (net_force 60) is vastly more destructive than a narrow one (net_force 16), and a catastrophically failed attack (net_force −40) causes far more domestic unrest than a near-miss (net_force −5). If tuning reveals extreme blowout cases at very high net_force values, a diminishing returns curve (e.g., square root scaling or a hard cap) can be applied to individual damage components — this is a clean bolt-on that doesn't change the formula structure.

The breakthrough threshold is a config value (e.g., 15.0) — setting it equal to the typical attack confidence threshold means an attacker must perform at least as well as expected to achieve a breakthrough, with bad luck producing contested results instead.

The resistance mechanic means high defender military actively reduces incoming damage — not just making the region an unattractive target, but genuinely absorbing the blow. A region with military 80 under attack from strength 50 takes very little damage. A region with military 15 under the same attack is devastated.

**[Tuning consideration — entrenchment:]** If testing reveals that the existing defender's advantage (resistance mechanic + natural field growth through drift) is insufficient to prevent early-game snowballing, a **tenure-based entrenchment multiplier** can be added to the defense formula: `effective_defense = defender_military * resistance_factor * entrenchment`, where entrenchment scales from 1.0 (just colonized/conquered) to a capped maximum (e.g., 1.5) over a configurable number of ticks. This would make established territory structurally harder to take than newly claimed territory, rewarding consolidation over rapid expansion. The mechanic is a clean bolt-on — one multiplier in the existing formula, one new per-region field (ticks since acquisition, reset on conquest/colonization). Not committed to the design; noted here as a known option if the balance requires it.

**Conquest events.** Region ownership changes through Conquest events, which fire when an attack drives a region's military below the conquest threshold (config value, near zero). The conquered region transfers to the attacking faction. Consequences: tension spikes (conquered population resents new rulers), population may drop (refugees, casualties), economy is disrupted (infrastructure damage). The Conquest event can spawn follow-up chains — resistance movements, refugee flows to adjacent friendly regions, morale effects in the conquering faction's other regions.

### Uninhabited Region Mechanics

Uninhabited regions exist in the world at generation (defined by the starting template) with no field values and no faction ownership. They are activated through **colonization events** fired by faction agents.

**Colonization as an agent decision.** Colonization uses the same attractiveness scoring pipeline as attacks. Uninhabited regions adjacent to a faction's territory enter the candidate pool alongside enemy-owned regions. Each archetype's scoring function evaluates them through its own lens — the Conqueror sees an undefended gateway, the Fortifier sees a region that shortens its defensive perimeter. If an uninhabited region scores highest in the candidate pool, the agent colonizes it instead of attacking an enemy. If enemy targets consistently score higher, the faction fights instead of expanding. The scoring handles prioritization naturally without special-case logic. Note: the Schism does not colonize — it only targets inhabited regions.

**Colonization cost.** The agent spends a portion of its budget on colonization (config value: `colonization_cost`). This is typically cheaper than an attack (no resistance to overcome), which creates a natural tempo incentive — early in the game when factions are building up, cheap expansion into empty space is often the best use of limited budget. As the map fills up and empty regions become scarce, the budget increasingly goes toward military action. The colonization cost is deducted from the faction's budget the same way attack strength is committed.

**Starter field values.** A newly colonized region is initialized with flat config values representing a bare frontier outpost: `colony_start_military` (starting point: 5), `colony_start_economy` (starting point: 8), `colony_start_tension` (starting point: 0), `colony_start_population` (starting point: 10). All factions' colonies start identically — differentiation comes from what happens after colonization. The territorial adjacency bonus accelerates economic growth based on neighbor strength (a colony next to a booming core develops faster than one next to another weak frontier), the economic and tension oscillation cycles create dynamic vulnerability windows, and the existing passive drift formulas naturally grow the colony's fields over time. The colony is a long-term investment: it takes many ticks of drift before it contributes meaningfully to the faction's budget, but even modest economy contributes to budget growth and the territorial adjacency bonus rewards contiguous expansion. The existing defender's advantage systems (military resistance mechanic in attack resolution, recruitment drift rebuilding garrisons over time, tension mechanics braking runaway prosperity) handle the snowball concern — rapid expansion produces low-field regions that are expensive to defend and slow to develop.

**Contested uninhabited regions.** Two factions can target the same uninhabited region on the same tick. Since faction agents run sequentially in the tick resolution sequence (step 3), the first faction to act claims the region. The second faction's colonization attempt finds the region already claimed and the action fails — the committed budget is refunded (no cost for a failed colonization, unlike a failed attack which costs the committed budget). The tick processing order of faction agents is randomized each tick to prevent a fixed advantage.

**Why factions expand.** Uninhabited regions provide three forms of value once claimed: (1) **Strategic buffer** — an owned region between a faction and its enemies that must be conquered before reaching the core, even at low military. (2) **Long-term budget investment** — a fresh colony starts at roughly breakeven against maintenance cost, but the territorial adjacency bonus and passive drift grow its economy over time until it becomes a net contributor. Expansion is an investment that takes many ticks to pay off, not an immediate payoff — the faction must be able to absorb the short-term maintenance cost while the colony develops. (3) **Territorial adjacency bonus** — the economy drift adjacency bonus (see "Economic Output drift" above) means claiming a region between two existing territories connects them economically, boosting both. This creates a concrete incentive for contiguous territorial expansion and accelerates colony development near strong existing regions.

### Diplomatic Stance

Each faction maintains a diplomatic stance toward every other faction. Stances are a simple enum: **hostile**, **neutral**, or **cooperative**. Each archetype defines a default starting stance toward the player's civilization and toward other archetypes. The Conqueror starts hostile toward everyone. Breakaway factions from revolts start hostile toward their parent faction. The player's civilization's stance toward others mirrors their stance toward it (if they're hostile to you, you're hostile to them).

Stances are mutable through events. A diplomatic event chain could shift a neutral faction to hostile. A successful negotiation mission could shift a hostile breakaway to neutral. Stance changes are event effects, applied the same way as field changes — authored per event template in the library.

Mechanical effects of stance:
- **Hostile** — border friction applies, faction agents include each other's regions in attack candidate pools, the faction's territory is treated as enemy territory for all simulation calculations.
- **Neutral** — no border friction, no attacks, no economic bonuses. Factions coexist without interaction. Neutral factions' regions are excluded from attack candidate pools.
- **Cooperative** — no border friction, no attacks. Cooperative factions' adjacent regions contribute to the territorial adjacency bonus as if owned by the same faction (representing trade cooperation and economic partnership). Cooperative factions benefit from **technology convergence** — the lower-tech faction gains tech_level growth toward the higher-tech partner's level (see "Technology System — Tech Convergence in Cooperative Peace" below). Technology convergence benefits diminish per additional cooperative partner to prevent "peace coalition" snowballing (exact diminishing returns formula TBD — see Open Design Questions).

**[Future consideration, not for initial implementation:]** Cooperative factions may coordinate defensive reinforcement. Mutual defense coordination is a potential fourth diplomatic state ("allied") that adds military cooperation on top of the economic and technological cooperation in the cooperative state. This is deferred until the base cooperative/betrayal system is proven and fun.

#### Peace Formation — Event-Driven

Cooperative relationships form through the event chain system, not through explicit agent proposals. Peace emerges from behavior — sustained non-aggression is itself the peace offering.

When two neutral factions share a border for a configurable number of ticks without either faction attacking the other, and both factions have stability above a configurable threshold in their border regions, a **Diplomatic Overture** event fires. The event has a probability of succeeding, scaled by: economic compatibility (similar economic output levels in border regions), tension levels in both factions' border regions (low tension favors success), and archetype disposition (Fortifiers are more receptive to peace than Conquerors). If the event succeeds, both factions transition from neutral → cooperative. If it fails, the non-aggression timer resets and the process can begin again.

Peace formation requires tracking one value per neutral border pair: a tick counter for sustained non-aggression, which resets to zero if either faction attacks the other or if either faction's border region stability drops below the threshold. This is the only new per-pair state required.

The event-driven approach means peace is not a strategic decision factions optimize for — it's an emergent outcome of stable conditions. Factions that are busy fighting on other borders naturally don't form peace because they can't sustain the non-aggression window. Factions in a quiet corner of the map naturally drift toward cooperation. This produces organic diplomatic landscapes without agent-level diplomacy logic.

#### Betrayal Mechanic — Per-Tick Probability

Cooperative relationships can be broken through betrayal. Each tick, every cooperative pair is evaluated for betrayal. Each faction in the pair has an independent probability of betraying the other. Betrayal = the betraying faction launches a surprise attack on the partner's border region and the relationship immediately flips to hostile.

The betrayal probability per tick is:

```
betrayal_chance = base_betrayal_rate * archetype_betrayal_weight * opportunity_modifier * pressure_modifier
```

- **base_betrayal_rate** — a small per-tick config value (tuned so that cooperative relationships last long enough to be meaningful but are never permanent).
- **archetype_betrayal_weight** — per-archetype multiplier. The Conqueror has a high weight (betrays frequently). The Fortifier has a low weight (rarely betrays). The Opportunist has a high weight that spikes further when the partner is weakened. The Schism has a moderate weight. The player's civilization has a low weight (conservative posture — betrayal by the player's faction is rare but possible, creating dramatic moments when the simulation breaks a peace the player benefited from).
- **opportunity_modifier** — scales with military advantage over the partner at the shared border. A faction with military 80 facing a partner's military 20 has a much higher betrayal chance than a faction facing an equal partner. This ensures betrayals happen when they make strategic sense — "they struck when we were weak."
- **pressure_modifier** — scales with the betraying faction's internal factional tension. High tension increases betrayal chance, representing internal political pressure to find external enemies or seize resources. A faction under internal stress is more likely to break a peace agreement.

The per-tick roll is stateless — no accumulating pressure, no tracking beyond what already exists in faction and region data. The probability modifiers ensure betrayal is driven by circumstance: a Conqueror with military advantage over a weakened partner during a period of internal tension is very likely to betray. A Fortifier facing an equal partner during calm times almost never betrays. The unpredictability is the point — the player cannot be certain peace will hold, which creates the dramatic tension the system is designed for.

**Betrayal consequences.** Betrayal produces a surprise attack (the betraying faction attacks a cooperative partner's border region) and the relationship flips to hostile. There are no additional consequences — no reputation system, no memory, no other factions reacting to the betrayal. The attack itself, with its standard damage resolution, is the full consequence. This keeps the system simple and avoids a diplomatic memory layer.

**[Future consideration:]** If testing reveals that betrayal-spam is degenerate (factions repeatedly cooperating and betraying the same partner), a cooldown timer can be added as a clean bolt-on: after a betrayal, the victim marks the betrayer with a timer during which no cooperation can form between them. This is a known fix for a known potential problem, not committed to the design.

**The player's civilization agent.** The player's civilization runs the same agent framework as all other factions. During time jumps (when the player isn't present), it defaults to a **conservative defensive posture** — it prioritizes reinforcing threatened borders over launching attacks. If it has overwhelming military advantage at a border, it may launch attacks, but this is weighted low. The player's missions are how the civilization takes offensive action — the autonomous agent handles defense between chapters. The player may disagree with autonomous decisions ("why did my civilization abandon the Periphery?"), but the bible's core principle applies: the civilization has its own plans, and the world does not revolve around the player.

**[Future consideration, not for Stage 0:]** Random hyper-focus — occasionally a faction agent dumps disproportionate budget into a single attack regardless of normal scoring, creating unpredictable offensive surges.

**Agent information model.** All faction agents have perfect information about the military strength, economic output, and population of adjacent regions, regardless of faction ownership. This represents civilizational-level strategic intelligence — neighboring powers know roughly how strong each other are across decades and centuries. Agents do NOT have visibility into other factions' budget levels or internal decision-making, only the observable state of regions on the world graph. Fog of war is a **player-facing presentation layer** that affects tactical missions, not simulation-level agent behavior. During missions, the player's sensor coverage, layer visibility, and intelligence quality are constrained by mission parameters and assets. During time jumps, the simulation's agents operate with full neighbor visibility to produce coherent strategic behavior — a civilization that fails to defend an obvious threat fails because of political dysfunction or resource constraints (modeled through the reinforce variance mechanic), not because it literally couldn't see the army on its border.

### Technology System

Each faction has a **tech_level** — a single numeric value from 0 to 100 representing the faction's overall technological sophistication. Technology is a faction-level attribute, not a per-region attribute. All regions owned by a faction operate at that faction's tech_level.

**Archetype-interpreted technology.** The tech_level value is the same for every faction, but each archetype has a **config mapping** that distributes the tech benefit across different gameplay multipliers. The engine applies tech_level through per-archetype multiplier curves for attack efficiency, defense efficiency, and economic growth rate. A Conqueror at tech_level 60 gets most of its tech benefit as increased attack efficiency (its military technology focus). A Fortifier at tech_level 60 gets most of its tech benefit as increased defense efficiency and economic growth (its infrastructure technology focus). The player's civilization has a balanced distribution. The mapping is authored per archetype as config data — the engine reads "archetype X at tech_level Y gets these multipliers" from a lookup table. No special-case logic per archetype in the engine.

This means two factions at the same tech_level are not identical — they benefit from technology differently based on their strategic identity. A technologically advanced Conqueror is a terrifying military force. A technologically advanced Fortifier is an economic powerhouse with impenetrable defenses. The same number produces different stories through the archetype lens.

**Tech growth formula.** Tech_level grows per tick based on the faction's economic and population base (exact formula TBD — see Open Design Questions). The growth drivers are designed to make technology a natural byproduct of a thriving faction rather than a separate resource to manage. Factions that maintain healthy economies and populations advance technologically without explicit "research" actions.

**Tech convergence in cooperative peace.** Factions in a cooperative diplomatic relationship benefit from technology sharing. The lower-tech faction gains additional tech_level growth per tick proportional to the gap between its tech_level and its cooperative partner's tech_level. The exact sharing formula and diminishing returns per additional cooperative partner are TBD (see Open Design Questions). The design intent is that peace with an advanced faction accelerates the weaker faction's technological development, creating a concrete strategic incentive for cooperation — but the benefit diminishes with multiple partners to prevent "peace coalition" snowballing where a cluster of cooperative factions pulls away from isolated factions technologically.

**Multiplier magnitude.** How much tech advantage matters in absolute terms (e.g., whether a faction at tech 100 has a 10% or 30% edge over a faction at tech 0) is TBD and will be tuned during implementation (see Open Design Questions). The magnitude must be significant enough that tech_level creates meaningful asymmetry between factions, but not so dominant that it overrides military strength, budget, and positioning as the primary determinants of combat outcomes.

**Breakaway inheritance.** When a breakaway faction is created from a revolt, the new faction copies the parent faction's current tech_level. This represents the breakaway population taking their knowledge and skills with them. The breakaway then grows (or stagnates) its tech_level independently based on its own economic and population base. A breakaway from a high-tech faction starts advanced but may fall behind if it can't sustain the economic base needed for continued growth.

**Technology loss.** Tech_level can decrease through event chain effects — technology loss events that fire when a faction's conditions deteriorate. A faction whose economy collapses, whose population declines, or whose territory fragments may lose technological knowledge over time. This is consistent with the Foundation theme — civilizations can regress, and the knowledge of one generation is not guaranteed to survive to the next. Technology loss events are authored as event templates in the library, firing on threshold triggers like all other events.

#### Tech Tiers — Unit Variant Progression

Tech tiers are the player-facing manifestation of technology progression. As a faction's tech_level crosses tier boundaries, the units the faction fields change — not just in numbers, but in kind. Each tier unlocks a different set of stat ranges, trait pools, and ability variants for all 6 base unit types.

**3–4 tech tiers per era** (exact count TBD — see Open Design Questions). The tiers are keyed to tech_level ranges (e.g., tier 1 at tech_level 0–25, tier 2 at 25–50, tier 3 at 50–75, tier 4 at 75–100 — exact breakpoints TBD). Tier boundaries may be non-uniform if the design calls for it (e.g., a longer tier 1 representing slow early progression).

**The engine owns the 6 base types and the RPS triangle; the tier determines what the AI library generates.** The engine knows "this faction is at tech tier 2, generate units accordingly." The AI library generates stat profiles, trait pools, and ability variants appropriate to that tier. A tier-1 faction fields units with lower stat ranges, simpler traits, and basic ability variants. A tier-3 faction fields units with higher stat ranges, more specialized traits, and advanced ability variants. The 6 base unit types and the RPS triangle remain constant across all tiers — Strike still beats Siege, Siege still beats Line, Line still beats Strike. Tiers change what the units can do and how well they do it, not the fundamental combat relationships.

**Tech tiers are era-specific content.** Each theme pack defines what its tiers look and feel like. The engine's abstract tier system is era-agnostic. The sci-fi theme pack defines what a tier-1 "Raider" looks like (slow transit, laser weapons) versus a tier-3 "Raider" (near-instant transit, personal shielding). A Roman-era theme pack would define tier-1 as early republic (basic legions, coastal galleys) and tier-3 as late empire (professional army, corvus-equipped navy). The engine doesn't know "laser" or "corvus" — it knows stat ranges and ability tags. This is fully consistent with the existing skeleton/skin architecture.

**Tier regression.** Factions can regress tiers through technology loss. If a faction's tech_level drops below a tier boundary (through technology loss events or conquest-driven economic collapse), the faction drops to the lower tier and its units reflect the regression. This is one of the game's most dramatic moments — fielding degraded technology because the civilization that built the advanced units no longer exists in the same form. The chronicle frames this naturally: "The forces that once carried shielded armor now fought with patched relics."

**Cross-tier mission feel.** When the player's faction is at a different tech tier than the enemy, the force parity system (which already handles strength asymmetry) compensates: the player receives more units if their units are individually weaker, or fewer units if their units are individually stronger. A tier-2 player facing tier-3 enemies gets more units to compensate for the stat gap. This preserves the design principle that difficulty comes from constraint compression, not from enemy factions having objectively better units. The question of whether cross-tier matchups feel fun or frustrating is a tuning question to be resolved during implementation.

**Tier transitions.** Whether tier transitions happen smoothly (gradual stat interpolation between tiers) or in discrete jumps (units snap to the new tier's stat ranges when the boundary is crossed) is TBD. Discrete jumps are simpler to implement and create more visible chronicle moments ("our forces fielded new technology for the first time"). Smooth transitions are more realistic but harder to notice.

### Coherence Ledger — Named Character Registry

The coherence ledger is a **character registry with lifecycle management**. It tracks every named character in the simulation — who they are, where they are, whether they're alive or dead, and which faction they serve. It does NOT duplicate event data, track faction arcs, or maintain a separate chain index. The event log (with its chain tags and causal links) is the single source of truth for what happened. The ledger is the single source of truth for who exists.

**All named characters are military leaders.** Every character in the ledger — from faction supreme commanders to regional garrison officers — is a military figure. The scale of their command varies, but the type is uniform. Political crises, economic collapses, and cultural events are experienced through the lens of the military leader dealing with them. This simplifies the role model, chronicle framing, and succession logic. There are no governors, trade officials, or political leaders as named character roles.

**Role-based standing characters.** Characters are created when they assume a role, not when something dramatic happens to them. Faction leaders are named from faction creation. Regional commanders are named when a region is colonized or conquered. Lineage members are named when the lineage generator creates them during time jumps. This means characters can be referenced *before* dramatic events — a faction leader who's been accumulating budget for 200 ticks already has a name when they finally attack, and the chronicle can reference them by name in the buildup.

**Character record — identity and lifecycle only.** Each named character stores:

- `character_id` — unique identifier
- `name` — pulled from the naming library (deduplicated against all active names in the current game)
- `faction_id` — which faction they belong to
- `region_id` — where they're currently stationed
- `rank` — scale of command: `supreme_commander` (faction leader), `regional_commander` (regional authority), `garrison_officer` (local defense leader), `lineage_member` (player's family — rank may also carry one of the military ranks)
- `born_tick` — when the character was created
- `lifespan_ticks` — rolled at creation from a config range (representing natural lifespan mapped to simulation ticks)
- `status` — `active` or `historical`
- `death_tick` — null if active; set when the character dies
- `lineage_id` — null for non-player characters; links player family members to their lineage
- `parent_character_id` — for lineage members, who their parent was (null for non-lineage characters and lineage founders)

**The ledger does not store event history per character.** When a consumer needs "what events involved this character," it queries the event log filtered by character ID. The event log stores character attachments on each event entry — the ledger does not duplicate this. Single source of truth for event-character links is the event log.

**Lifespan and death.** Characters have a lifespan rolled at creation from a config range (e.g., representing 40–90 years of life mapped to tick scale). When a character's age reaches their lifespan, they die: status changes to `historical`, `death_tick` is recorded. Death is a ledger-level state change, not necessarily a discrete event in the event chain system. The chronicle distiller and template system can reference a character's death *if it's narratively relevant* — a faction leader dying mid-war is chronicle material; a garrison officer dying of old age in a quiet backwater probably isn't. The distiller makes this judgment through its existing significance scoring, not through a special death-event mechanism.

**Succession.** When a named character dies, their role is filled by a new named character. For faction leaders (`supreme_commander`), succession produces a new character in the same faction. For regional commanders, succession produces a new character in the same region. The new character is created with a fresh name from the library, a new lifespan roll, and the same faction and region assignments. Succession is automatic — the ledger handles it as part of its lifecycle management during each tick's logging step. Succession events that are narratively significant (a faction leader dying during a critical war) surface through the chronicle distiller's normal significance scoring of events in the event log.

**Lineage generation is a separate module.** The lineage generator runs during time jumps and produces new lineage member records. It hands these to the ledger for registration. The ledger does not contain lineage generation logic — it just files the new characters. See "The Generational Structure — Character Selector Algorithm — Step 3" for lineage generation details.

**Nemesis detection.** The ledger does not track rivalries as a first-class relationship. Nemesis relationships are detected by the character selector at query time: scan the event log for combat events where two named characters were on opposing sides. Characters who appear on opposite sides of multiple combat events are nemesis candidates. This keeps the ledger simple and avoids maintaining a relationship graph that duplicates information already in the event log.

**Cause-and-effect thread tracking.** The ledger does NOT maintain a separate chain index or thread tracker. The event log's chain tags (generated when chains start, propagated to all chain spawns) are the complete causal thread record. Consumers — the chronicle distiller, the mission generator, the character selector — query the event log by chain tag when they need causal thread data. This avoids redundancy between the ledger and the event log.

### What the Simulation Provides to Missions

The simulation runs between chapters, not during them. During missions, the simulation is stopped — the player is focused on their tactical problem, not monitoring a live world. The simulation's role relative to missions:

- Before each chapter: evaluates region composite axes and event chain state to identify where the world's most pressing needs are, and generates a mission from them
- Before each mission: pre-computes possible complications from the complication table (rare — roughly every third mission)
- After each mission: digests the outcome as a consequence bundle, then runs forward through the time jump
- Across the arc: determines the long-term trajectory of the civilization through the player's generational career

### Stage 0 — Simulation Core (Prove the World Lives)

The simulation is built and validated before any other system. No Godot, no UI, no WebSocket. Python only, console output. A test script generates a world, runs thousands of ticks, and prints a summary. This isolation provides the fastest possible feedback loop for tuning the SD model, event chains, and faction agent behavior.

**Timescale calibration.** All drift rates, border friction rates, budget growth rates, and event effect magnitudes are calibrated so that a full civilizational cycle (early expansion → mid-era conflict → late-era decline or dominance) plays out over 1,000–3,000 ticks. A healthy home region remains viable for 500+ ticks. Frontiers show meaningful pressure over 200–400 ticks. The conqueror's first attack on player territory lands around tick 600–900. Territory changes hands in the 800–1,400 range. The calibration was achieved by applying a uniform 5x divisor to all rate values simultaneously, preserving all equilibria and field ratios while stretching the timeline. Event magnitudes were halved (on top of earlier halving during structural fixes) to maintain proportional impact relative to the slower drift. Integration tests (M1–M3) run 2,000 ticks to cover a full cycle.

**Development approach: start with few variables, work upward.** Begin with the four granular fields (military strength, economic output, factional tension, population) and two composite axes (stability, capacity). Tune until the simulation produces coherent behavior at this resolution. Then add fields one at a time — each addition is a hypothesis ("adding infrastructure will make economic collapse cascade more realistically"), tested by running the simulation and reading output. If the new variable doesn't produce the expected change, tune or remove it before adding the next. This incremental approach keeps the simulation debuggable: when something weird happens, the only new thing is the variable that was just added.

### Stage 1 — World Generation and Multi-Region Drift (Prove Regions Interact)

Stage 1 builds on the single-region SD model proven in Stage 0 by introducing a **world graph** — multiple regions connected by adjacency, each running the same drift logic but producing different trajectories based on starting values and connections. The world is generated from the isolated start template (1 home, 2 frontier, 4–6 empty regions). Each region drifts independently through the proven Stage 0 formulas, with three new inter-region mechanics layered on top: baseline recruitment, territorial adjacency bonus, and feedback-isolated economic/tension oscillation.

**What was proven:** Home regions and frontier regions, starting from different field values within the same template, produce meaningfully different drift trajectories. Frontiers show more volatility than home (weaker starting position amplifies sensitivity to drift interactions). Multiple generations from the same template produce variety — different random seeds produce divergent outcomes that amplify over time rather than converging. Long-run behavior (500 ticks) is coherent: no degenerate states, no collapses from healthy starting positions, trajectories are explainable from the underlying mechanics.

**Key tuning decisions during Stage 1:**

- **Baseline recruitment** added to prevent frontier military freefall. At frontier economies (25–40), military decayed to near-zero because the economy-scaled recruitment term required economy above the threshold (~50). A constant baseline recruitment term fires for all inhabited regions regardless of economy, representing militia raised from the local population. Weak frontiers stabilize at military ~8–9 rather than collapsing to zero. Home regions are unaffected — the baseline is negligible at high economy.

- **Adjacency bonus tuned down from 0.5 to 0.05.** At 0.5, the bonus was 12x larger than frontier organic growth and every region hit economy 100 within 200 ticks, erasing the economic gradient. At 0.05, frontier growth roughly doubles near the core but frontiers don't catch up to home within 500 ticks. The gradient is preserved.

- **Home population range raised from (50, 65) to (70, 85).** At pop 50–65, home tension equilibrium was ~10 — correct behavior for the formula, but too low for the intended design. At pop 70–85, home tension equilibrium is ~12–13, closer to the Stage 0 reference. The formula weights were not changed — tension will increase further when border friction and factions arrive in Stage 3.

- **Oscillation mechanism changed from simple additive to feedback-isolated additive.** Simple additive oscillation caused feedback amplification through coupled fields (frontier economy deviated ±24, tension hit zero). Coefficient modulation was tried but was too subtle (±1.8 economy deviation). The feedback-isolated approach adds the oscillation to the stored field value (what agents see) but has cross-field drift coupling read de-oscillated trend values, breaking the feedback loop while keeping visible swings. Verified: economy deviation bounded at ±6 (max observed 6.23), oscillation does not prevent net growth, tension never hits zero from oscillation alone.

- **Oscillation config values verified:** Economy amplitude ±6.0 (period 100 ticks), tension amplitude ±2.0 (period 125 ticks). The economy period was lengthened from the original 20-tick starting point to 100 ticks, and amplitude raised from ±4 to ±6, based on tuning for agent-exploitable windows at the Stage 1 timescale. The tension period was lengthened from 25 to 125 ticks.

**Empty region topology.** The template generator creates empty regions in chains off each frontier (empty_1↔empty_2 off frontier_1, etc.) rather than as independent dead-ends. This creates expansion corridors — chains of uninhabited space that factions can colonize sequentially. The number of empty regions is randomized (4–6) per generation.

---

## The Generational Structure

### Chapters

A single playthrough consists of multiple **chapters**. Each chapter is one mission played by one commander. Chapters last approximately 30–60 minutes of real play time.

### The Cycle

1. **Mission briefing** — the civilization presents the player with a mission: objectives, forces assigned, context about what's happening in the world.
2. **Recon phase** — free camera over the mission area with no time pressure. The player observes terrain, known enemy positions (based on intelligence quality), points of interest, and their own starting deployment. The commander studies the map before giving the order. The mission clock does not start until the player hits "Begin Mission."
3. **The mission** — the player commands their forces to accomplish the objective. The simulation is stopped during missions — the player is focused on their tactical problem, not monitoring a live world. Rare pre-computed complications may fire (roughly every third mission) based on the archetype's complication table, but these are determined at mission generation, not driven by live simulation ticks.
4. **Mission resolution** — success exists on a spectrum, not a binary. The tactical layer classifies the outcome into one of the archetype's outcome bands, and the mission outcome resolver translates that into region stat changes applied to the mission region, scaled proportionally to the region's current state. There is no separate world-wide momentum or vector nudge — the simulation propagates local consequences naturally through inter-region dependencies during the subsequent time jump. The resolution also determines the **commander's fate**: survived, wounded, or killed. Commander death can result from catastrophic mission failure or specific tactical outcomes (e.g., the command unit is destroyed). A killed commander is logged in the coherence ledger and becomes part of the lineage's narrative — "Commander Tanaka went down with the ISV Resolute during the defense of Terminus." Death forces an early lineage decision: the character selector either continues through another family member or rotates to a new lineage. Commander death is not a fail state for the player — it's a narrative event that the generational structure absorbs naturally.
5. **Time jump** — the simulation fast-forwards through a random duration between a configurable min and max (targeting 20–100 years). The duration is a simple random roll, decoupled from mission urgency or world state — the simulation's existing drama-generation systems (passive drift, event chains, faction agent actions) produce interesting events over any duration naturally. The player has no agency over the gap length. The player experiences the jump as a **chronicle scroll** — a text-based vertical timeline of 5–10 entries summarizing what happened between chapters, presented alongside an **animated map view** where the player watches faction territories shift, borders redraw, and new factions emerge in real time as the scroll advances. Three kinds of entries, presented in order: **consequence entries** (direct results of the player's last mission, shown first so the player sees their impact), **world entries** (things that happened on their own — faction shifts, tech changes, inter-faction conflicts), and **setup entries** (the last one or two entries teeing up the new chapter). The player can click any entry to expand it slightly for extra detail. No voice acting, no cutscenes — just good prose, clean typography, the weight of time, and a map that moves.
6. **New chapter** — the player returns as a character selected by the simulation. **Lineage persistence:** the simulation keeps the player within the same bloodline for 2–4 chapters before rotating to a different family. Within a lineage run, each chapter is a descendant — the player sees the family name return and watches consequences compound across a career arc. The simulation rotates to a new lineage when: the character selector's rotation logic triggers (regional delta scoring, crisis veto, hard cap — see Character Selector Algorithm), the bloodline has died out, or the world's pressure points have shifted to a region where a different lineage is more narratively charged. When the lineage rotates, the new character is selected from the weighted pool: most commonly a **descendant of a previous commander from a different lineage** the player has already played. Less commonly a **descendant of a previous commander's rival or nemesis** (instant dramatic tension). Rarely, an **unrelated person elevated by circumstance** (signals the world has changed dramatically). The 2–4 chapter range is a soft target — the simulation aims for it, not enforces it rigidly. If a bloodline dies out after one mission, that is a meaningful moment, not a bug. The civilization assigns a new mission based on the current state of the world.

### Character Selector Algorithm

The character selector runs after the time jump completes and the mission generator has already selected the next mission's region and archetype. It determines whether to continue the current lineage or rotate, and if rotating, picks the new lineage. The selector is coupled to the mission generator — the mission region is already decided, and the selector finds the best commander for that mission.

**Step 1: Rotation decision.** The ledger tracks a chapter counter for the current lineage. The rotation decision uses three mechanisms:

**Regional delta scoring** — after the time jump, the selector computes how much the lineage's home region (and adjacent regions) changed in field values during the jump. High total delta means the region is active and the family's story is in motion — stay with this lineage. Low total delta means things are quiet — natural exit point. The delta score maps to a rotation probability: low delta = high rotation chance, high delta = low rotation chance. The mapping curve and thresholds are config values.

**Crisis veto** — if the lineage's home region is in an active crisis (stability below a config threshold, or an active event chain in a critical stage), rotation is vetoed regardless of what the delta score or chapter counter say. The family stays because their story isn't done.

**Hard cap** — a maximum chapter count (config value, ~6) forces rotation regardless of delta score or crisis state. Even if the family is mid-crisis at the cap, the game cuts away. The chronicle frames this naturally — the family's story continues in the background, but the world's attention shifts. This prevents a single crisis-locked lineage from dominating the playthrough.

**Forced rotation** — if the bloodline has no living members, or the commander died and no immediate family successor exists, rotation is forced immediately regardless of counter, delta, or crisis.

The flow: check forced rotation conditions → if chapter counter is below the eligible range (2), stay → if at or above the hard cap, rotate → compute regional delta score → map to rotation probability → roll → if rotation triggers, check crisis veto → if vetoed, stay another chapter → otherwise, rotate.

**Step 2: Lineage selection (on rotation).** The selector runs after the mission generator has already chosen the mission region. It finds the best lineage for that region:

**Priority 1 — Previous lineage descendant (most common, ~70%).** Check all previous lineages the player has played. Does any have living descendants in or near the mission region? If multiple qualify, score by: recency penalty (don't immediately return to a lineage you just left), number of living descendants in the region, and how many chapters ago the player last played them (moderate gap preferred over very recent or very distant). Weighted random draw from scored candidates.

**Priority 2 — Nemesis/rival descendant (rarer, ~20%).** Check the coherence ledger for named characters who were rivals or antagonists to any previous commander. Do any have descendants in or near the mission region? If yes, select from this pool. Instant dramatic tension — the player commands the descendant of someone who opposed them.

**Priority 3 — Unrelated person (rarest, ~10%).** No previous lineage or nemesis connection to the mission region. Generate a new character from that region. This signals the world has changed dramatically — the old families aren't relevant here.

The pool weights (~70/20/10) are config values. The selector rolls against the weights to pick a pool, then selects within that pool. If the selected pool has no valid candidates (e.g., no nemesis descendants exist near the mission region), it falls through to the next pool.

**Step 3: Lineage member generation during time jumps.** During each time jump, a **lineage generator module** (separate from the coherence ledger) runs a simple family tree update for the current lineage (and all tracked previous lineages). The update is minimal: N descendants produced (based on time jump length and a fertility config value), distributed across regions based on where the family currently lives. Each descendant gets a name (from the naming system), a region, and an age. No personality traits, no career simulation, no detailed life events. The generator hands the new character records to the coherence ledger for registration. The chronicle distiller and template system add narrative richness in prose — the ledger just tracks who exists and where. This keeps both systems lean while giving the character selector and distiller enough data to work with.

### Onboarding and First Chapter

**Single onboarding screen.** Before chapter 1, the player makes two permanent choices on one screen: **difficulty setting** (Easy/Medium/Hard) and **mission preference weights** (across the five categories, with one markable as "rare"). Both are permanent for the entire generational arc. The same onboarding screen fires at the start of each new cycle after Exodus or Extinction — the player can make different choices for the new civilization.

**Opening time jump.** After the player confirms their choices, the game generates the starting world and immediately runs a time jump (configurable, targeting 20–50 years — same minimum as standard time jumps). The simulation's fast pacing means even this initial jump produces meaningful history: factions expand, borders form, and first military contacts may occur. The player sees an abbreviated opening chronicle scroll — 3–5 entries, all world entries (no consequence entries since there's no previous mission). This serves as the player's introduction to both the world and the chronicle scroll format — and immediately establishes that the world is dangerous and in motion. The mission generator then runs normally against the post-jump state, and the character selector draws from the "unrelated person" pool since no previous lineages exist. Subsequent cycles after Exodus or Extinction use the same opening time jump — in post-Extinction cycles, the chronicle scroll includes ruin references and the world contains remnants of the previous civilization.

### What Carries Over

- **The world remembers everything.** The simulation state carries forward completely. Every mission outcome, every faction shift, every tech advance or cultural collapse persists.
- **The player starts mechanically fresh each chapter.** New character, new forces, new mission. No persistent "player level" or unlocks.
- **But the civilization evolves.** As the simulation progresses, technology advances (or regresses). The tools available to the player in later chapters may be significantly different from early chapters — better units, new asset types, or conversely, degraded capabilities if the civilization is declining.
- **The Ouroboros.** The game can cycle. If the civilization reaches Extinction with Amnesia, it restarts — and the player's next character exists in a world that contains the ruins of everything that came before. The Memory Burden mechanic: the player remembers what their new character does not.

### Player Civilization Mortality

The player's civilization has no plot armor. It can be conquered, fragmented, or ground into extinction by the same simulation forces that affect every other faction. This is a core design commitment, not an edge case.

**When the player's faction collapses** (loses all regions, or is reduced below a viability threshold), the generational structure absorbs it:

1. **The chronicle frames the fall.** The collapse becomes a major chronicle scroll entry — potentially the most dramatic moment in the playthrough. The prose treats it with weight: "The last garrison of [faction name] surrendered at [region]. Seven hundred years of history ended not with a battle, but with a signature."

2. **The character selector reassigns the player to a surviving faction.** The selector evaluates all surviving factions and picks one using modified lineage selection logic: prefer factions that the player has narrative connections to (previous lineages with descendants in that faction's territory, nemesis connections, geographic proximity to the fallen civilization's former territory). If no narrative connection exists, select the faction whose territory overlaps most with the player's former civilization — the player experiences the world their people built, now under new management.

3. **The player continues as a commander in the new faction.** New mission, new forces, new political context. The player's institutional knowledge of the world carries forward even though their character is new. The chronicle connects the threads — "Three decades after the fall of [old faction], a young officer in [new faction] was given command of a force..."

**Cross-faction lineage rotation.** Even when the player's civilization survives, the lineage rotation system can move the player to a different faction for variety. After the hard cap on lineage chapters (config value, ~6), the character selector considers candidates across all factions, not just the player's current one. A player who has spent four chapters commanding forces for one faction might rotate to a breakaway faction born from a revolt in their former territory, or to a rival faction where a nemesis descendant now serves. This prevents the player from being locked into a single faction's perspective and creates dramatic moments of seeing the world from the other side.

### Terminal Conditions and the Cycle

The game is designed to run indefinitely. Terminal conditions are not endpoints — they are **transitions** that the generational structure absorbs naturally. With player civilization mortality, even the "death" of the player's faction is a transition, not a game over.

- **Exodus** — the civilization escapes to a new region of the world (or a new world entirely). The simulation resets to an early-era state: small foothold, limited technology, dark unexplored space. But the chronicle carries forward, the coherence ledger remembers, and the player's new commander may inherit fragments of the old civilization's knowledge. A new early era begins.
- **Extinction with Amnesia** — the civilization dies. Cold restart with relics. A new civilization emerges in the same world, surrounded by the ruins of everything that came before. The simulation resets to early-era state. The Memory Burden mechanic: the player remembers what their new character does not. The relics of the old civilization are physically present but unlabeled — waypoints exist, but inspect panels read "Unknown."
- **The Unbroken Line** — the civilization endures through the late era without collapsing. Eventually the simulation's internal pressures (external faction escalation, internal fractures, resource exhaustion, technological complexity) force a transition — either an Exodus, a collapse into Extinction, or a **civilizational contraction** where the civilization voluntarily or involuntarily retreats to a smaller footprint, effectively resetting to a mid or early era state with the scars of what came before.

The game loops through expansion → conflict → fragmentation → renewal, but this cycle operates at the faction level, not the global level. Multiple factions cycle independently. The player threads through these cycles via lineage rotation, experiencing the world from different vantage points. Each cycle feels different because the world remembers: ruins from collapsed factions, chronicle entries spanning centuries, lineages that connect across faction boundaries. The player experiences the Ouroboros — civilizations rising, falling, and rising again, with the player as the thread of continuity across the cycles.

---

## Missions

### Mission Generation

Missions are generated from the simulation state using **a curated library of mission archetypes** with variables filled in by the current world context. The library is built by the AI library builder pipeline (same infrastructure that generates chronicle templates). This means missions are structurally recognizable (the player learns mission types over time) but contextually unique every time.

### Mission Generator Algorithm

After a time jump, the generator must select a (region, archetype) pair and fill variable slots to produce a mission briefing. The selection uses a **weighted random draw from scored candidates**, where each candidate is a possible (region, archetype) pairing.

**Step 1: Build the candidate pool.** Every region that crosses a minimum "mission-worthy" threshold on any composite axis, has active event chains in critical stages, or has active faction conflicts (hostile faction forces massing at borders, recent attack events, contested territory) is paired with each archetype that fits its pressure type (low military = military archetype, high factional tension = crisis response archetype, border under attack = military or containment archetype, etc.). Stable regions with no active pressure are excluded.

**Step 2: Score each candidate.** Each (region, archetype) pair receives a single score computed as a weighted sum of three factors:

```
score = (w1 * urgency) + (w2 * relevance) + (w3 * preference)
```

**Urgency (0–1)** — how much does this region need attention? Derived from how far its composite axes have dropped, how active faction conflicts are there (hostile forces at borders, recent attacks, territory recently lost), and whether event chains are in critical stages. A region with stability at 15 under active enemy assault scores near 1.0. A region with moderate tension and no immediate threat scores low.

**Relevance (0–1)** — how connected is this commander to this region and this type of problem? Combines lineage history (has this family operated in or near this region before? — read from the coherence ledger), regional proximity (distance from the commander's lineage "home" region), and archetype fit (does the pressure type align with what this lineage has historically been assigned to?). A frontier military family scoring against a military mission in their home region gets high relevance. The same family scoring against a political crisis across the world gets low relevance.

**Preference (0–1)** — the player's mission category weights from game start, mapped to this archetype's category. Preferred categories get a high value. The category marked "rare" gets a very low value (e.g., 0.1 — not zero, because extreme urgency can still pull it through).

The three weights (w1, w2, w3) are tuning values in config. In calm periods, urgency scores are modest across the board, so relevance and preference have significant influence — the commander gets sent where it makes sense for who they are. In crisis, one region's urgency score dominates the sum regardless of the other factors — the world stops caring about your specialty and sends whoever's available. This desperation behavior emerges naturally from the math without special-case logic.

**[Future consideration if tuning reveals the need:]** A desperation threshold toggle — when the world's worst urgency score exceeds a threshold, the formula switches to urgency-only: `score = urgency`. This would provide explicit control over the transition from "send the right person" to "send anyone" if the weighted sum's natural behavior proves too gradual or too abrupt during testing. The probable reason for needing this: if the w1 weight on urgency needs to be high enough to dominate in crisis, it might also dominate in calm periods, reducing the influence of relevance and preference below useful levels. The toggle would let urgency be weighted moderately during calm periods while still guaranteeing it takes over in crisis.

**Step 3: Select.** Take the top N candidates by score (configurable, ~5), and do a weighted random draw from those. The highest-scored candidate usually wins, but not always — maintaining stochasticity.

**Step 4: Fill variable slots.** The selected archetype template has variable slots (which system, which faction, what named characters are involved, what's the time pressure). The generator fills these from the selected region's current state, active event chains, and coherence ledger entries. The result is a structured mission briefing ready for presentation to the player.

### Mission Archetypes

Each archetype is a template with fixed structure and variable slots:

- **Objective shape** — what "done" looks like structurally. A defense mission is "hold X until Y." An escort mission is "get A from B to C." A containment mission is "keep Z from spreading past this boundary." These are the verbs of the mission grammar.
- **Asset profile** — what mix of assets the mission expects. A defense mission is force-heavy. An exploration mission is science-heavy with light escort. A crisis response is a grab bag. This is a recommendation to the civilization's allocation system, not a hard rule — if the civilization is broke, you get less.
- **Complication table** *(deferred — implement after core missions are working)* — a weighted list of mid-mission events this archetype is susceptible to. Defense missions might get "reinforcements from unexpected vector" or "political order to abandon position." Exploration missions might get "anomaly is not what it seemed" or "first contact goes sideways." Each complication is itself a mini-template with variables. **This system layers on top of working missions — missions must function successfully without complications first.**
- **Success spectrum** — how outcomes map to simulation feedback for this archetype. Each archetype defines 4–5 outcome bands (total success, strong success, partial success, partial failure, total failure). Each band produces a different consequence bundle of region stat changes applied to the mission region, with deltas scaled proportionally to the region's current state. Two players who both "partially succeeded" the same archetype could send the civilization in different directions depending on how the region absorbs the outcome. See "Mission Outcome Resolver" below for the full algorithm.

The **variable slots** are what the simulation fills in: which system, which faction, what are the hostile factions doing nearby, what named characters are involved, what's the time pressure. Same archetype, completely different feel depending on context. The library builder's job is authoring these archetypes — 15–20 to start across all categories. The simulation's job is picking one and filling the blanks.

### Mission Types

Five categories:

**Military** — defend this system, take that position, escort this force, break a blockade, hold a line while evacuation proceeds, pursuit, ambush, siege. The player commands forces and fights. The bread and butter.

**Exploration** — scout unknown territory, investigate an anomaly, make first contact with something unexpected, survey a system for colonization, salvage operations. The player commands science units and scouts, with military escort.

**Crisis response** — contain a famine, suppress or negotiate a revolt, evacuate a population before disaster, stabilize a failing system, plague quarantine. The player commands a mix of assets and must triage competing urgent needs.

**Intelligence & covert** — insert operatives behind enemy lines, extract a defector, disrupt hostile faction infrastructure. Small forces, high stakes. Open engagement is on the table when things go sideways — a clean covert op every time would get boring.

**Containment & denial** — a hostile faction or systemic threat is spreading through a region and you can't stop it, but you can choose where it spreads. Hold a spatial boundary against a timer — survive until reinforcements arrive or until the window closes. Pure triage at a strategic scale.

Diplomatic missions are notably absent as a player activity. Diplomacy happens *to* the player (a faction flips mid-mission, political orders change) but the player is a commander, not a diplomat.

**Inheritance missions** are not a separate category — they are a rare narrative modifier the coherence ledger can apply to any mission type. "This is a defense mission... defending a system your great-grandmother abandoned." The connection is highlighted in the chronicle, but mechanically it's still a standard mission of its base type.

### Mission Objectives

Missions have:
- **A primary objective** — what the civilization sent you to do
- **A time constraint** — you don't have forever; the world is moving
- **Success conditions that exist on a spectrum** — not binary pass/fail. You might secure the system but lose half your force. You might fail the primary but save something unexpected. The degree and nature of success/failure feeds back into the simulation differently.

### Difficulty Scaling

Difficulty scales primarily through **constraint compression** — tighter resources, shorter timelines, more frequent complications, heavier stakes. Easy/Medium/Hard is chosen at the start of a playthrough — a permanent choice for the entire generational arc.

As pressure mounts across generations, the simulation compresses what the player has to work with: time gets shorter, resources get thinner, objectives get compound, complications get more frequent, and stakes get heavier. A late-game defense mission and an early-game defense mission use the same archetype, but the late-game version is a desperate nightmare because you have half the force, two extra problems, and twenty fewer years of civilization health backing you up.

Note: because the AI library generates unit stat profiles (see AI-Generated Unit Variety and Unit Power Balancing), unit power levels do vary — but they vary equally for both the player and the enemy. Difficulty does not come from enemy factions having stronger units. It comes from the player having less to work with.

Difficulty setting adjusts: resource allocation generosity, complication frequency and overlap, time constraint width, and how quickly the constraint compression ramps across generations. It does **not** change: the simulation itself (same stochasticity, same faction agent behavior, same coherence ledger), mission archetypes and objective shapes, or narrative quality.

### Era Scaling

Tech era doesn't just mean "better units" — it means **different units.** Early era might be slow, tanky, short-range. Mid era opens up speed and range. Late era (if the civilization is thriving) might introduce exotic capabilities that change how you approach problems entirely. But if the civilization is declining, late era might mean losing capabilities — fielding patched-together relics because the production facilitys are gone. Better tools always come with harder problems.

Unit classes and roles are consistent across eras (there's always a Strike skirmisher, always a Siege artillery) but the specific units are fundamentally different — not just "the same unit with bigger numbers." AND within an era, the AI generates per-civilization variation based on civilization traits. The result: every playthrough's force feels authored without being mechanically unpredictable.

### Mission Preference

The player sets a **preference weight** across the five mission categories at game start. When the simulation has multiple viable pressure points, it biases toward the player's preferences. The player can also mark one category as **"rare"** — the simulation almost never picks it, but reserves the right in extreme world states where no other archetype fits.

The simulation always has final say. Preferences are a request, not a command. If the world is on fire and only a crisis response mission makes sense, that's what you get. The commander doesn't choose their orders — but command tries to play to their strengths when they can. Preferences are set at game start and not changeable mid-playthrough.

### Mission Briefing

The briefing comes from the civilization, not from a game menu. Delivered as if a superior officer is handing you your orders. Three sections:

- **Situation** — what's happening in the world that made this mission necessary. Drawn from the simulation state and the chronicle.
- **Objective** — what you're being sent to do, with the success spectrum made implicit through the framing. The player reads between the lines.
- **Assets** — what you're being given. Force composition, non-military assets, and a note on what the civilization couldn't spare.

The player reads, then accepts. No negotiation, no loadout screen — you get what the civilization gives you. The only choice is whether to refuse the mission entirely (rare, with consequences — the simulation treats refusal as a failed mission with its own consequence bundle).

### Complications (Deferred — implement after core missions work)

Mid-mission complications are **rare and pre-computed, not driven by a live simulation.** The simulation is stopped during missions. When a mission is generated, the archetype's complication table identifies what *could* go wrong based on the current world state. Probability determines whether a complication actually fires — roughly every third mission, not every mission. If one fires, the timing and nature are determined at generation, not dynamically.

This means complications feel like memorable disruptions, not background noise. A faction collapsing mid-evacuation is a story the player tells later. It shouldn't happen often enough to become routine.

**This entire system is implemented after missions work end-to-end without complications. Missions on their own should be a complete, satisfying experience first.**

### Mission Outcome Resolver

After a mission ends, the outcome resolver translates the tactical result into simulation consequences. The resolver sits between the tactical layer (which classifies what happened) and the simulation (which needs field deltas to process).

**Input: outcome band.** The tactical layer evaluates the player's performance and assigns one of 4–5 outcome bands defined by the mission's archetype. Bands represent the spectrum from total success to total failure. The resolver receives a single band classification — one value, thin interface.

**Transformation: proportional lookup table per archetype.** Each mission archetype defines a consequence table mapping each outcome band to field deltas for the mission region. Deltas are defined as **proportional to the region's current state** rather than absolute numbers. Instead of "military +10," the table says "military +10% of deficit from 100." A region at military 20 gets a bigger absolute boost from a successful defense mission than a region at military 80. A region already near collapse gets hit harder by failure.

This proportional scaling means consequences feel appropriate to the situation. Saving a desperate region has a bigger impact than reinforcing a strong one. Failing in a strong region is a setback; failing in a weak region is a catastrophe. The scaling emerges from one design choice (proportional vs. absolute) without special-case logic.

**Scope: mission region only.** The consequence bundle is field deltas applied to the mission region. There is no separate world-wide momentum, vector nudge, or ripple system. The simulation handles world-wide propagation naturally: improved stability in one region affects neighboring regions through existing inter-region dependencies (trade, military support, faction dynamics) as the time jump runs forward. The world "learns" about the mission outcome organically through hundreds of ticks of simulation, not through an artificial broadcast.

**Why no vector nudge:** The bible previously referenced "a direct vector nudge for intangible civilizational effect" as part of consequence bundles. This has been simplified away. Region stat changes applied to the mission region, processed through the simulation's existing composite axes and inter-region mechanics during the time jump, already capture the full civilizational impact. A military victory that boosts military strength and drops factional tension in a key region IS the civilizational impact — the composite axes propagate it, and the time jump's hundreds of ticks let it ripple through the world's interconnected systems.

---

## The Player's Toolkit

### What You Command

The player receives a **variable set of assets** for each mission. What you get depends on what the civilization can provide (shaped by simulation state, tech level, and mission type). Forces scale with the era — early chapters might feature basic units, late chapters might have advanced technology or, if the civilization is declining, desperate scraps.

Asset categories:

- **Forces** — combat units. Your hard power. Defend, attack, project force. The most expensive assets and the most painful to lose.
- **Science units** — extend knowledge. Explore, investigate anomalies, boost tech. Fragile but valuable for information advantage.
- **Trade/supply convoys** — economic backbone. Run supply to your forces and between regions. Disrupting enemy supply (or protecting yours) is a strategic lever.
- **Intelligence operatives** — eyes and saboteurs. Place them for better visibility or to disrupt enemy operations. Limited number, high value.
- **Cultural missions** — the long game. Slow, but they stabilize cultural memory in a region. The civilizational equivalent of planting a tree.

Not every mission includes every asset type. A military defense mission might be mostly forces with some supply units. An exploration mission might be one science unit with a small escort. A crisis response might be a grab bag of whatever was available.

Non-military assets sit **outside the combat RPS entirely**. They're not combat units — they're strategic tools. They have **no combat capability** and must be protected or evacuated when fighting starts.

### Commanding Forces

- **Top-down tactical view** — the player sees their forces from above and gives orders
- **Direct control** — click/select units, tell them where to go and what to do
- **Always real-time, no pause** — pacing is slow enough to think. Deliberate, not frantic. The skill is in reading the situation and making committed positioning decisions.

### Individual Units

Units feel real but are not deep characters. They have names. Losing one should sting — especially heavy Siege units — but the attachment is to the mission and the civilization, not to individual units. Think named tools you care about (like a favorite ship in FTL), not party members in an RPG.

### Light Economy

The player does not manage production queues, build individual units, or set resource priorities. The civilization allocates forces based entirely on the mission type and its own state. The player's influence over force composition is **front-loaded into the mission preference weights** set at game start — by telling the civilization what kind of commander they are (military-focused, exploration-focused, etc.), the player shapes which mission types they receive, and the mission type determines the asset profile. See "Force Allocation Algorithm" in the Force and Combat Design section for how this translates into concrete forces.

This is the "commander, not king" principle applied to logistics. You don't choose your loadout — you're handed orders and equipment. The civilization tries to give you what the mission calls for, constrained by what it can actually produce. A thriving civilization gives you a well-equipped force. A declining civilization gives you scraps and a note about what they couldn't spare. The gap between what you need and what you get is where the drama lives.

---

## Force and Combat Design

### Unit Combat Categories — Strike / Line / Siege

Three broad categories on a soft RPS spectrum:

**Strike** — fast, fragile, high burst damage. Good at flanking, raiding supply lines, picking off isolated targets. Weak in sustained engagements against heavy units. Think destroyers, interceptors, raider craft. Commanded as **squads** (Halo Wars model — groups of smaller units that move together).

**Line** — the backbone. Balanced durability and firepower. Wins through sustained engagement and formation. The units you build your force around. Think cruisers, frigates, standard combat units. Commanded as **individual units or small groups** depending on size.

**Siege** — slow, durable, massive damage at range. Dominates in set-piece engagements but vulnerable to flanking strikes. Think battleships, artillery platforms, carriers. Commanded as **individual high-value assets** — each one matters, losing one hurts.

**The RPS flow:** Strike flanks and kills Siege. Siege outranges and crushes Line. Line absorbs and overwhelms Strike. But it's **soft** — a well-positioned Siege unit with escort can survive a Strike attack. A Strike wing that catches Line units out of formation can win. The counters create pressure, not guarantees. Positioning and abilities can overcome a bad matchup, but you're fighting uphill.

### Unit Differentiation

Units differ through **stats + traits + abilities** (the full package):

- **Stats** — speed, firepower, durability, range, sensor radius. The baseline. AI-generated within defined ranges per unit type.
- **Traits** — passive characteristics. A unit might have "hardened hull" (extra resistance to Strike damage) or "long-range sensors" (sees further). One or two per unit type, AI-generated from a constrained trait pool.
- **Abilities** — one active ability per unit type. These are the mastery layer — a new player can ignore them and still play, a skilled player uses them to create decisive moments. See "Abilities — One Per Unit" below for the full design.

### Unit Roster — 6 Base Types

The base game ships with **6 unit types** — two per RPS category. This is the minimum viable roster that makes the RPS triangle work and produces real composition decisions. Additional unit types can be added through expansion packs (new types are expansion content, not engine changes — consistent with the skeleton/skin model).

**Strike (commanded as squads)**

**Raider** — the flanker. Fastest unit in the game, fragile, high burst damage against isolated targets. The unit you send around the side to kill artillery or cut supply lines. Excels when it catches something alone. Dies fast in a straight fight against Line. The defining Strike unit.

**Interceptor** — the screen. Fast, moderate durability for a Strike unit, lower damage than the Raider. Its job is denying enemy Strike units — it hunts Raiders and protects slower high-value assets. The defensive Strike option. Think destroyer escort.

**Line (commanded individually or in small groups)**

**Vanguard** — the frontliner. Durable, moderate damage, holds position. The unit you build your formation around. Wins through sustained engagement. Not flashy, but losing one hurts because it's holding the line.

**Warden** — the support. Lower damage, moderate durability, but provides area buffs (damage reduction, repair over time) to nearby friendly units. Force multiplier. A Vanguard next to a Warden is significantly harder to kill than a Vanguard alone. Makes positioning decisions matter — cluster for the buff, but clustering makes you vulnerable to Siege area damage.

**Siege (commanded as individual high-value assets)**

**Bombard** — long-range area damage. The classic artillery piece. Dominates open engagements at range. Crushes Line formations. Extremely vulnerable to Strike flanking — if a Raider reaches the Bombard, it dies fast. The unit that forces the enemy to move.

**Bastion** — slow, extremely durable, moderate damage at medium range. The anchor. Doesn't have the Bombard's range or area damage, but it survives Strike flanking. The Siege unit you bring when you expect to be attacked — it holds ground and absorbs punishment. Think mobile fortress.

**The soft RPS with this roster:**
- **Strike beats Siege:** Raiders flank and destroy Bombards. The Bastion is the exception — it survives Strike flanking, which is what makes it a meaningful choice over the Bombard.
- **Siege beats Line:** Bombard area damage shreds Vanguard formations. Warden buffs help but can't fully counter sustained Bombard fire. The player must close the distance or flank with Strike.
- **Line beats Strike:** Vanguards absorb and overwhelm Raiders in a straight fight. Interceptors fare better against Line than Raiders do, but they're still outmatched. Strike units need to avoid Line engagement, not win it.

### Abilities — One Per Unit

Each unit type has **one active ability** that defines its mastery ceiling. Abilities amplify what the unit already does — they don't give it a new role. A new player ignores abilities and still plays effectively. A skilled player uses them to create decisive moments. Every ability is a commitment with a tradeoff.

**The ability designs below are era-agnostic engine behaviors.** The names listed are sci-fi theme pack names for the base game. Other theme packs provide their own names and visual effects for the same mechanical behaviors. The engine knows "short burst of increased speed and damage on a Strike unit." The theme pack knows what that looks like and what it's called.

**Raider — "Surge" (sci-fi name).** Short burst of dramatically increased speed and damage. Lasts a few seconds. The Raider becomes a missile — close distance instantly, deliver a devastating alpha strike, then it's back to being fragile. Skill expression: timing the dive on an exposed, unescorted target. Cooldown: long (60–90 seconds). One or two uses per engagement.

**Interceptor — "Intercept" (sci-fi name).** Passive proximity trigger. When any enemy Strike unit moves within the Interceptor's detection radius, the Interceptor automatically gains a speed boost toward that unit and a damage bonus for the first engagement. No manual activation — it triggers on proximity. Cooldown after each trigger prevents chain-reacting to multiple Strike units simultaneously. Skill expression: positioning the Interceptor near what needs protecting. A new player parks it near their Bombard and it works. A skilled player positions multiple Interceptors to create overlapping denial zones across an entire flank.

**Vanguard — "Brace" (sci-fi name).** The Vanguard plants and becomes immobile. While braced, it takes significantly reduced damage from all sources and deals increased damage to anything in its engagement range. A braced Vanguard in a chokepoint is nearly immovable. Tradeoff: can't reposition while braced; if the threat shifts, you're stuck. **Transition time:** Brace has a windup delay (config value, e.g. 1.5–3 seconds) where the unit is immobile but does not yet have the defensive bonus. The same transition delay applies when canceling Brace. This punishes reactive Bracing (enemy already on you, panic-Brace, eat full damage during windup) and rewards predictive Bracing (read where pressure is coming, commit early). Both transition times are tuning values for playtesting. Cooldown: moderate (30–40 seconds).

**Warden — "Rally" (sci-fi name).** Burst area heal/repair to all friendly units within range. Instantly restores a chunk of durability. The emergency button — the Vanguard line is cracking under Bombard fire, Rally buys another 15 seconds. Skill expression: holding Rally for the critical moment when the line is about to break, rather than using it early. Cooldown: long (60–90 seconds). One, maybe two uses per engagement.

**Bombard — "Barrage" (sci-fi name).** Concentrated high-damage volley at a targeted area. Significantly more damage than normal fire, focused in a smaller area, over a short duration. Tradeoff: brief visual telegraph before impact gives the opponent a window to scatter. Skill expression: baiting the enemy into clustering before calling Barrage; reading the telegraph and scattering when the enemy uses theirs. Cooldown: long (75–100 seconds). One use per engagement in most cases.

**Bastion — "Fortify" (sci-fi name).** Deploys a temporary defensive zone around the Bastion. All friendly units within the zone gain moderate damage reduction for a significant duration. The Bastion can still move (slowly) while Fortify is active — the zone moves with it. Tradeoff: the zone is visible to the enemy, telegraphing where the protected area is. Skill expression: positioning the Bastion to create a safe pocket over what matters most (protecting a Bombard from Raiders, shielding a damaged Vanguard line). Cooldown: long (60–80 seconds).

### Roles Within Categories

The 6-unit roster uses a **sparse role matrix** — not every RPS category has every role. Each unit type fills exactly one role, and every cell in the matrix has a clear reason to exist:

- **Strike:** Raider (skirmisher/flanker), Interceptor (screen/escort)
- **Line:** Vanguard (frontliner), Warden (support)
- **Siege:** Bombard (artillery), Bastion (frontliner/anchor)

Deliberately absent from the base roster: Strike artillery, Strike frontliner, Line artillery, Line skirmisher, Siege support, Siege skirmisher. These are potential expansion content — each new unit type added to a category creates new composition decisions without changing the engine.

### AI-Generated Unit Variety

The engine owns the mechanics — the 6 unit types, their abilities, and their roles are hand-designed and consistent across all factions and eras. **AI tunes the numbers based on civilization traits.** A militaristic civilization's units skew toward higher firepower. An expansionist civilization gets faster, lighter units. A civilization in technological decline has units with degraded stats but maybe improvised traits.

The framework is:
- The 6 base unit types are fixed (always a Raider, always a Bombard, etc.)
- Stats within each type have defined ranges
- AI generates the specific stat profile, names, and flavor for this civilization's version
- The engine can handle any output because the constraints guarantee mechanical validity

### Unit Power Balancing and Force Parity

Because the AI library has a hand in unit stat values, the game needs a system for calculating a unit's overall **power rating** (strength value) based on its combined stats, traits, and abilities. This power rating serves as the currency for force allocation:

- Every unit generated by the library gets a computed strength score derived from its stat values, trait effects, and ability impact
- The strength score is the basis for **force parity** — ensuring every mission presents a winnable fight

**Force parity system.** When a mission is generated from a faction conflict, the enemy force's total strength is determined by the attacking faction's committed budget (translated from abstract budget into concrete unit strength). The player receives a force with a **comparable total strength**, adjusted by the civilization's current capacity:

- A thriving civilization (high capacity composite) gives the player close to 100% parity — a fair fight where skill determines the outcome
- A declining civilization gives the player 80–90% parity — still winnable, but the player is the underdog
- The capacity-to-parity curve is a config value. The penalty range is narrow enough that a skilled player can always win

**Difficulty setting** scales the parity penalty: Easy = minimal penalty even when civilization is weak (near-100% parity always), Hard = steeper penalty curve (a declining civilization gives you meaningfully less to work with). Difficulty never changes the enemy's strength — only the player's allocation.

Both sides receive their forces from the same **unit composition pools**. Each faction's units are drawn from the AI-generated library for that faction's civilization traits. Two forces with equal total strength but different unit mixes play differently — one might be heavy on Siege and weak on Strike, the other the reverse. The RPS system creates tactical decisions even at parity.

**Multi-faction battles (3–4 way).** When multiple hostile factions are in conflict in the same region (e.g., the player defending against both the Conqueror and a breakaway faction), each faction's force is sized by its own committed budget/strength. The player's force is sized to match the total enemy strength (with civilizational capacity adjustment). The hostile factions may fight each other as well as the player — exploiting inter-enemy conflict is a tactical opportunity.

The power rating formula is an implementation detail to be designed during the force/combat stages, but the principle is: **every mission should be a winnable fight where player skill is the deciding factor, not a math problem decided before the mission starts.**

### Force Allocation Algorithm

The player does not choose their force composition. The civilization decides what to give them based on the mission type and its own state. There is no loadout screen, no requisition interface, no economy management during gameplay. The player's influence over force composition is front-loaded into the **mission preference weights** set at game start — preferred mission types are received more often, and mission type determines the asset profile.

The allocation algorithm:

1. **Mission archetype defines the target asset profile.** Each mission archetype specifies what ratio of asset types the mission expects: a defense mission is force-heavy (mostly combat units, some supply), an exploration mission is science-heavy with light escort, a crisis response is a mixed grab bag. The asset profile is authored per archetype as part of the mission template library.

2. **Force parity system defines the total strength budget.** The enemy force's total strength (from committed faction budget) sets the baseline. The civilization's current capacity composite and the difficulty setting adjust the player's allocation as described above.

3. **The strength budget fills the asset profile.** The allocation system spends the strength budget filling the archetype's target ratio from the available unit types, drawn from the AI-generated library for the player's faction. Within the combat unit allocation, composition is determined by the faction's library — a militaristic civilization's library skews toward more Siege and Line, an expansionist civilization's skews toward more Strike.

4. **Capacity shortfalls reduce quantity, not quality.** If the civilization can't fill the full asset profile (declining economy, regions lost, low capacity), some slots go unfilled — the player receives fewer units, not weaker ones. The mission briefing notes what the civilization couldn't spare ("Command was unable to provide the full escort complement — the Periphery garrisons are stretched thin"). This communicates the civilization's state through the briefing prose and creates drama through scarcity, not through invisible stat penalties.

### 2.5D Vertical Layers

Combat uses **3–5 vertical layers** rather than a flat 2D plane or full 3D movement. Units exist on a layer and can transition between adjacent layers.

**Layers are a property of the map, not of units.** The map defines which layers are accessible at each position through a **layer accessibility mask**. Terrain features block specific layers — an obstacle occupying layers 1–2 forces units to maneuver over it on layers 3–5, or find a route around it on the blocked layers. All unit types can move to any layer the map says is accessible at their position — there are no category restrictions on layer transition. Transition between layers takes time (config value per unit type — Strike transitions faster than Siege), creating natural differences in how aggressively each unit type exploits vertical movement.

**Layer accessibility is era-agnostic.** The engine knows "terrain obstacle occupying layers 1–2 at position X." The theme pack determines what that looks like: an asteroid in sci-fi, a mountain in a land theme, a reef in a naval theme. The strategic decision (go over, go around, exploit the blocked layers for cover) is identical regardless of era.

**Layer visibility is tied to sensor coverage.** Sometimes you can see all layers (good intel mission). Sometimes you're partially blind (fog of war on layers above/below your sensor range). This creates tactical uncertainty — an enemy force on a layer you can't see is invisible until they strike or enter your sensor coverage.

**Layer design is part of map generation.** The spine + gradient system includes layer accessibility as a gradient property. See "Map Generation System" for how per-archetype generation scripts use layer blocking to create tactical terrain. Layer accessibility, like all gradient properties, can vary spatially (an area might have all 5 layers open while an adjacent area has layers 1–2 blocked) and can overlap with environmental hazards (a sensor interference zone on layer 3 but clear visibility on layers 1–2).

### Camera and Player View

The player controls a **standard RTS camera** — free pan and zoom at all times. No automatic anchoring, no camera modes, no forced following. The player manages their own viewport like Age of Empires 3 or StarCraft 2. A minimap provides strategic awareness of the broader tactical space.

The moving battlefield is communicated through **world-space movement under free camera.** Convoys move across the map, environmental features drift, gravitational effects shift unit positions — all happening in the world while the player pans freely to observe and react. The skill is in attention management: watching the convoy's front for incoming threats versus checking the rear for flanking Raiders. No special camera mechanics are needed — movement happens in the world, the player watches from wherever they choose.

### Moving Battlefields

Engagements are **not static arenas.** The tactical space shifts during combat:

- Battles can happen while forces are in transit — the convoy keeps moving, the fight happens around it
- Environmental features drift through the combat zone — terrain that provided cover shifts, opening or closing sightlines
- Gravitational or environmental forces can pull units in a direction (future expansion — noted as a natural extension of the movement drag hazard type at solar system scale)

This means positioning is never "solved" — the player must continuously adapt to a changing spatial situation.

### Environmental Hazards

The base game ships with **one environmental hazard type** as a gradient field property (position, radius, intensity, falloff) that can vary by layer and move over time. Era-agnostic — the engine defines the gameplay effect, the theme pack determines the visual presentation.

**Sensor interference zone** — units inside have reduced sensor radius. Units outside looking in can't see as far into the zone. Creates fog pockets on the map. Tactical use: hide forces inside for ambush, deny enemy information, or avoid the zone because you don't know what's inside. Era examples: nebula (sci-fi), fog bank (naval), dense forest (land), sandstorm (desert).

**[Future expansion:]** Additional hazard types (movement drag zones, damage zones, boost corridors, ability disruption zones) can be added as new gradient property tags without engine changes. The gradient field system is extensible by design — each new hazard type is a new property the engine samples, not a new system. These are noted as natural expansion points once the base game is proven and fun.

### Engagement Scale and Duration

- **Engagement scale** — the player is in the battle. Units are on screen. The player is positioning individual groups and squads.
- **Variable duration** — some engagements are quick skirmishes (a few minutes), others are prolonged campaigns within a single mission. Duration depends on mission type and what the player encounters.

### Tactical Variety — Mission Type Differentiation

Different mission types feel different through the combination of three existing systems, not through mission-type-specific tactical mechanics:

**Force composition** — the force allocation algorithm gives the player a different unit mix based on mission archetype. A military defense mission is combat-heavy. An exploration mission is a light escort with science units. A crisis response is a mixed grab bag. The units you have determine how you play.

**Map character** — the spine + gradient map generation system produces different maps per mission archetype. A defense mission generates defensible positions and chokepoints. An exploration mission generates open space with sensor interference zones and points of interest. A containment mission generates a boundary line to hold. Each archetype has a generation script that produces appropriate topology.

**Objective shape and pacing** — "hold X until Y" plays differently from "get A from B to C" even on identical maps. The timer, the success spectrum, and what counts as partial success create distinct pacing per archetype.

No additional mission-type-specific rules are needed. The combination of different forces + different maps + different objectives produces distinct tactical experiences through the same engine. This is consistent with the skeleton/skin principle — the engine is uniform, the content (force profiles, map scripts, objective templates) creates variety.

---

## The Antagonist System

### External Antagonists — Military Faction Archetypes

All external antagonists are **territorial military factions** running the same agent framework as every other faction (accumulate/attack/colonize/reinforce). They differ through config weights only: archetype attack/expand/defend weights, confidence threshold range, and attractiveness scoring priorities. No archetype has mechanical advantages — no special combat math, no faction-specific drift modifiers, no unique resource mechanics. The same engine, different knobs. Five base archetypes, with more generated by the library builder post-launch:

**The Conqueror** — empire builder. Expands aggressively, fights for territory, values strategic position. High attack and expand weights, low defend weight. Moderate confidence threshold range (12–18). Attractiveness scoring uses the three-factor formula: weakness + current value + strategic position (see "Multi-Faction Agent Decision Model" above for the full formula). The classic expansionist military threat. Simulation story: rapid early expansion into empty space, then grinding border wars, then potential overextension and fragmentation.

**The Warlord** — pure aggressor. Attacks frequently with slim margins. Less interested in colonizing empty space than in fighting whoever's nearby. High attack weight, low expand weight, low defend weight. Low confidence threshold range (8–14) — willing to commit with marginal expected outcomes. Attractiveness scoring uses the same three-factor formula as the Conqueror but with a reduced weakness weight — the Warlord doesn't specifically seek the strongest target, but doesn't shy away from them either. Reckless, not suicidal. Simulation story: doesn't expand much early game, launches repeated attacks once borders make contact, grinds defenders down through attrition rather than decisive breakthroughs.

**The Fortifier** — defensive empire builder. Expands cautiously into empty space, then reinforces borders heavily. Rarely attacks unless overwhelmingly strong. Low attack weight, moderate expand weight, very high defend weight. High confidence threshold range — only attacks when victory is near-certain. Attractiveness scoring biases toward regions that improve the faction's defensibility (reducing border exposure, filling gaps in territorial contiguity). Simulation story: quietly colonizes a compact cluster early game, becomes extremely hard to crack mid game, occasionally launches devastating attacks when massive budget has accumulated against a weakened neighbor.

**The Opportunist** — scavenger. Waits for other factions to weaken each other, then strikes the loser. Patient and reactive. Moderate attack/expand/defend weights. Moderate confidence threshold range (15–22). Attractiveness scoring adds a **recent damage weighting** — regions that have lost military or economy in the last N ticks (config value) score dramatically higher. Freshly conquered regions with low fields are prime targets. Falls back to standard weakness + value scoring when no recently-damaged targets exist, so the Opportunist is never completely inert. Simulation story: quiet in the early game, colonizes efficiently, lets other factions grind each other down in the mid game, then swoops in on the weakened victor.

**The Schism** — ideological insurgent. Does not start with territory at world generation — **spawns from revolts**. When a successful revolt creates a breakaway faction, there is a probability (scaling with game age — low early, higher late) that the breakaway is a Schism faction rather than a generic breakaway. The Schism then aggressively targets adjacent high-tension regions. High attack weight, low expand weight (doesn't colonize empty space — only takes inhabited regions), high defend weight (survival mode once established). Low confidence threshold range (10–16). Attractiveness scoring weights **factional tension** heavily — prioritizes discontented regions regardless of military strength. Simulation story: emerges mid-to-late game from internal dysfunction, spreads through already-stressed regions, creates civil war dynamics. The Schism's expansion is naturally self-limiting: each conquest is a high-tension, low-economy region that drains the faction's budget, and proportional tension decay in conquered regions gradually stabilizes them, reducing the ideological pressure on neighbors. A Schism that overextends faces the same overextension penalties as any other faction.

**[Tuning note:]** Each archetype's config weight profile (attack/expand/defend weights, confidence threshold range, attractiveness scoring weights) is tuned during Stage 3 implementation by running 500+ tick simulations across multiple seeds and verifying that each archetype produces distinct, non-degenerate behavior. Specific risks to watch for during tuning: the Warlord fizzling from repeated failed attacks (adjust confidence threshold or commit fraction), the Fortifier stagnating without producing chronicle material (adjust confidence threshold until they attack roughly once per 300–500 ticks), the Opportunist never finding damaged targets (verify template placement puts them near expected conflict zones, verify fallback scoring activates), and the Schism either never spawning (adjust spawn probability scaling) or cascading uncontrollably (verify proportional tension decay and overextension penalties limit expansion rate). These are tuning problems, not architectural problems — the shared mechanical framework handles all five archetypes without special cases.

**[Future consideration:]** Environmental and systemic threats (plagues, resource collapses, anomalies, technological crises) can be added as **event chain content** fired by the existing threshold trigger system — not as faction archetypes. These are a post-base-game addition, implemented only after the core territorial faction simulation is proven and fun. The event chain architecture already supports cascading regional crises without requiring a faction entity to drive them.

### Internal Antagonists

Not every threat comes from outside. The simulation generates **internal antagonists** from faction dynamics and regional stress:

- **Successful revolts** can splinter a region away from its faction. When a revolt event fires and succeeds, the revolting population rolls a **success rate** (randomly between ~10–70%, config range). The breakaway faction "steals" that percentage of the region's current military and economy — representing soldiers who defected and resources seized. The region's military and economy drop by the stolen amount, and a new breakaway faction entity is created owning that region, starting with the stolen field values. The breakaway faction then operates as its own faction with its own agent — it can be attacked, it can attack, it can be allied with or absorbed. Breakaway factions persist across chapters and evolve through the simulation.
- **Faction extremism** — a faction that was once a healthy part of the civilization's political ecosystem radicalizes under pressure. They pursue their own agenda, which may conflict with the player's missions.
- **Military coups** — if the civilization is unstable enough, a military leader (potentially a named character from the coherence ledger) seizes control of a region or system. The player may be sent to resolve this — or may *be* the descendant of the coup leader.

**Player-initiated revolts:** Occasionally, the mission briefing or the tactical situation presents the player with the option to support or trigger a revolt. This is not a menu choice — it emerges from mission context. If the player is sent to stabilize a region ruled by a corrupt or incompetent faction, they may have the option to overthrow it instead of propping it up. The consequences feed back into the simulation: the new faction may be better or worse, and the civilization's trust in the player's lineage may shift.

### Spatial Manifestation

Each archetype creates a different war story because their strategic priorities differ. The Conqueror produces border wars and territorial conquest. The Warlord produces grinding attrition and raiding. The Fortifier produces tense standoffs that erupt into sudden devastating strikes. The Opportunist produces betrayals and scavenging in the wake of other factions' conflicts. The Schism produces civil wars and ideological fracture from within.

All faction threats act through the same simulation framework. Their effects are spatial — they happen in specific places, driven by the agent decision model. The player encounters them during missions.

### Threat Progression

The external threat builds over the course of the generational arc. Early chapters might have no direct hostile faction contact. Mid-game chapters increasingly involve external threats. Late-game chapters may be desperate last stands or evacuation missions.

Multiple antagonists can be active simultaneously, and **factions fight each other, not just the player's civilization.** The Conqueror might be conquering breakaway factions while the player deals with the Warlord on another front. Two external threats might clash over the same region. The world is a free-for-all where the player's civilization is one participant, not the center.

**All external antagonist factions** can be pushed back, defeated, or eliminated — they own regions and can lose them. A faction that loses all its territory ceases to be an active threat. However, the simulation's long-term pressures (new Schism factions spawning from revolts, internal fractures, resource exhaustion) ensure that eliminating one threat doesn't guarantee safety — something else will rise to fill the vacuum.

Internal antagonists (breakaway factions, coups, extremist movements) can be resolved, absorbed, or turned into allies. This is core to the late-game feel: the civilization is fighting itself while also contending with external forces it may not be able to beat.

---

## The Chronicle

The chronicle is the player's window into the civilization's history. It serves two functions:

1. **During time jumps** — the narrative montage. The chronicle scroll is the player's window into what happened between chapters: consequence entries showing the impact of their last mission, world entries showing the world evolving, and setup entries bridging into the new chapter. Click-to-expand provides extra detail for the curious.
2. **Across generations** — the long memory. The chronicle is the record the player reads to understand how they got here. A new commander's briefing draws from it. The coherence ledger ensures entries connect through named characters and cause-and-effect threads tracked via chain tags in the event log.

The chronicle is generated by the AI library builder pipeline. Chronicle entries read like fragments of a real history. The emergent narrative system (coherence ledger and named characters, cause-and-effect chains in the event log) drives the content.

### Chronicle Scroll — Visual Presentation

The time jump is a **split-screen experience**. The left side of the screen shows the world view (or era-appropriate equivalent), visualizing the simulation's progression in real time — borders shift, regions change hands, faction territory expands or contracts, the player's civilization grows or retreats. The player watches history happen spatially. The right side of the screen displays the chronicle scroll text, printing **one word at a time** in the style of streaming AI text generation. Each scroll entry appears sequentially, the prose building word by word while the world view evolves alongside it. The pacing is synchronized — as a scroll entry describes a region falling to an invading faction, the player sees the border shift on the map.

This dual presentation means the player absorbs the time jump through two complementary channels: the spatial channel (watching the world change) and the narrative channel (reading what those changes mean). Neither channel is sufficient alone — the map shows *what* happened but not *why*, and the text explains *why* but not *where*. Together they produce the feeling of watching history unfold.

Click-to-expand still works during the scroll — the player can pause and expand any entry for additional detail. The world view holds its current state while the player reads.

### Chronicle Scroll Distiller Algorithm

The distiller takes the full event log from a time jump (potentially hundreds of events across dozens of ticks) and compresses it into 5–10 scroll entries. It operates in three passes.

**Pass 1: Significance Scoring.** Every event in the time jump log receives a significance score. Each event template in the library carries a pre-authored **significance tier** (1–5), representing how inherently notable that type of event is — a first contact is more notable than a routine trade fluctuation, regardless of mechanical impact. The event's actual **delta magnitude** (sum of absolute field changes it caused across all affected regions) acts as a boost. The tier sets a floor: an event always scores at least its tier value. Delta magnitude can push the score higher but never lower. A first contact with tiny deltas still makes the cut. A minor trade event with massive cascading deltas gets boosted well above its tier.

After the base score is computed, a single **context multiplier** is applied. Events receive a bonus if they: occurred in the player's last mission region, involve named characters from the coherence ledger, or are part of long causal chains (chain length as a factor). The context multiplier is one combined bonus, not multiple independent factors. All multiplier weights are config values.

**Pass 2: Lineage-First Clustering.** Clustering determines which scored events get merged into a single scroll entry. It operates in three tiers of priority:

**Tier 1 — Lineage clusters.** Pull out every event that touches the player's lineage: descendants, the commander's former region, the family name appearing in the coherence ledger, direct consequences of the last mission. These form lineage clusters that are **guaranteed scroll slots** — the player always sees what happened to their family. The player's lineage is the spine of the scroll. If the lineage had a genuinely quiet century (stable region, no events touched the family), the lineage cluster degrades gracefully into a "life went on" entry, which is itself a meaningful beat in a generational story.

**Tier 2 — Chain clusters.** Remaining events that share a chain tag are grouped into chain clusters. Each causal chain becomes one potential scroll entry. A famine → revolt → compromise reads as one story, not three. Chains that span multiple regions stay intact — the chain is the story, not the location.

**Tier 3 — Regional summary clusters.** Leftover standalone events (no lineage connection, no chain membership) are grouped by region. Regions with multiple standalone events get a summary cluster. This sweeps up background noise into coherent regional entries instead of scattering thin standalone entries across the scroll.

After clustering, clusters are ranked by their highest-scoring event and the top clusters fill the 5–10 entry budget, with lineage clusters always included regardless of score.

**Pass 3: Keyed Composable Template Selection.** Each cluster is matched to a **template category** based on its characteristics: "chain resolved positively," "chain resolved negatively," "lineage — family thrived," "lineage — family suffered loss," "regional summary — decline," "faction advance," and so on. The category determines which **fragment pools** the entry is assembled from.

Each entry is composed from compatible fragments: an **opening fragment** (sets the tone and context), a **detail fragment** (the specific events, with variable slots filled from the cluster's data), and a **closing fragment** (the implication or forward look). Fragments are authored per category, so combinations within a category are always coherent. The combinatorial variety (many openings × many details × many closings per category) ensures entries stay fresh across playthroughs.

Each entry has a **base form** and an **expanded form** for the click-to-expand interaction. The base form uses the opening + detail fragments (1–2 sentences). The expanded form adds the closing fragment plus specific names, numbers, and causal links pulled from the coherence ledger (2–3 additional sentences). Variable slots in all fragments reference coherence ledger entries for named characters and places.

### Chronicle Template Authoring Framework

> **RESOLVED (v1.14).** This section specifies the full authoring framework for chronicle template fragments: the category taxonomy, fragment structure, variable slot vocabulary, generation rules, compatibility model, and validation pipeline. The library builder generates all fragments offline as static data — zero runtime AI dependencies.

#### Template Category Taxonomy — 20 Categories

The distiller's Pass 2 produces three kinds of clusters (lineage, chain, regional summary), plus a special consequence cluster type that always appears first in the scroll. Each cluster type is subdivided by valence and content type. Each category carries an explicit **emotional register** that governs the tone of all fragments in its pools.

**Lineage clusters** (Tier 1 — guaranteed scroll slots):
- `lineage_thrived` — the family prospered, gained influence, descendants born. Register: warm, measured, historically appreciative.
- `lineage_suffered` — family members died, lost position, region declined around them. Register: somber, restrained grief, weight of loss.
- `lineage_quiet` — nothing dramatic happened. Register: reflective, peaceful, "life went on" as a meaningful beat.
- `lineage_military_action` — a family member was involved in combat. Register: tense, martial, duty-focused.
- `lineage_succession` — a key family member died and was succeeded. Register: transitional, generational weight, continuity.

**Chain clusters** (Tier 2 — causal chains kept intact):
- `chain_crisis_resolved_well` — a crisis chain played out and the region stabilized. Register: cautious relief, hard-won stability.
- `chain_crisis_resolved_badly` — a crisis chain escalated and the region suffered lasting damage. Register: grim, consequence-heavy, permanent loss.
- `chain_conflict_victory` — a faction conflict chain ended with a clear winner. Register: decisive, martial, territorial shift.
- `chain_conflict_stalemate` — a faction conflict chain ground on inconclusively. Register: exhausted, grinding, unresolved tension.
- `chain_conflict_defeat` — the player's civilization lost territory or position. Register: somber, measured, historical weight.
- `chain_revolt_spawned` — a revolt chain produced a breakaway faction. Register: fractured, ideological, internal rupture.
- `chain_expansion` — a colonization or territorial growth chain. Register: pioneering, forward-looking, cautious optimism.
- `chain_cascade` — multiple overlapping chains compounded. Register: ominous, overwhelming, "too many things at once."

**Regional summary clusters** (Tier 3 — background sweep):
- `regional_decline` — the region got worse across multiple fields. Register: erosion, slow decay, quiet deterioration.
- `regional_growth` — the region improved. Register: steady, constructive, quiet progress.
- `regional_stable` — the region held steady (used sparingly). Register: neutral, brief, background.
- `regional_faction_shift` — ownership or diplomatic stance changed. Register: political, realignment, new order.

**Consequence clusters** (special — always first in scroll):
- `consequence_success` — the player's last mission improved the region. Register: earned, direct cause-and-effect, the player's mark.
- `consequence_failure` — the player's last mission made things worse. Register: weight of failure, consequences faced honestly.
- `consequence_mixed` — partial success/failure with visible tradeoffs. Register: bittersweet, complicated, no clean answers.
- `consequence_ripple` — the mission's effects propagated to other regions during the time jump. Register: expanding consequence, the player's reach extending beyond the mission region.

#### Fragment Structure

Each scroll entry is assembled from three fragment types. Fragments are prose templates with variable slots that the assembler fills at scroll-build time.

**Opening** — sets tone and temporal context. One sentence, max 30 words. Anchors when and where. Used in both base and expanded form. Openings own the temporal language — they establish the time frame ("In the decades that followed," "A generation later," "Within a decade of {event_description}"). Details and closings do not re-anchor time; they continue from the opening's temporal frame.

**Detail** — the specific events, drawn from cluster data. One to two sentences, max 60 words. The substance of the entry. Used in both base and expanded form.

**Closing** — implication, forward look, or emotional beat. One to two sentences, max 50 words. Used only in expanded form. The closing adds the "so what" — what this means going forward, or what it felt like to live through.

**Base form** = opening + detail (1–2 sentences, tight, under 90 words). This is what the player sees in the scroll.
**Expanded form** = opening + detail + closing, with specific names, numbers, and causal links from the coherence ledger filled into all available slots (3–5 sentences, under 140 words). This is what the player sees on click-to-expand.

#### Fragment Compatibility Rule

**Any opening in a category can combine with any detail in that category and any closing in that category.** The category boundary is the compatibility guarantee. No runtime compatibility checks, no tag matching, no conditional pairing logic. Fragment authors must write to this contract: every fragment in a pool must be tone-compatible and structurally compatible with every other fragment in the same category's other pools.

This means each fragment assumes nothing about which other fragments it will be paired with, except that they share the same category and therefore the same emotional register.

#### Variable Slot Vocabulary

Every slot resolves to a string at assembly time. The assembler pulls data from three sources: the cluster's event data, the coherence ledger, and the simulation state snapshot.

**Identity slots** (from coherence ledger):
- `{character_name}` — a named character involved in the cluster's events
- `{character_rank}` — their rank (supreme_commander, regional_commander, garrison_officer, lineage_member)
- `{character_faction}` — faction name of the character
- `{lineage_name}` — the player's current lineage family name
- `{faction_name}` — a faction involved in the cluster
- `{region_name}` — the region where the cluster's events occurred
- `{adjacent_region}` — a neighboring region referenced by the events

**Event slots** (from cluster event data):
- `{event_description}` — a short label for the root/primary event in the cluster (authored per event template in the library)
- `{chain_length}` — how many events are in this causal chain
- `{duration_ticks}` — how many ticks the chain spanned
- `{duration_prose}` — duration mapped to a human-readable time phrase ("over three decades," "in a matter of years")

**State slots** (from simulation snapshot at cluster resolution):
- `{field_delta_summary}` — prose summary of which fields changed and by how much ("military strength collapsed," "the economy slowly recovered")
- `{stability_level}` — qualitative label for the region's stability at chain end (critical, low, moderate, high)
- `{capacity_level}` — qualitative label for capacity
- `{tension_level}` — qualitative label for factional tension

**Consequence-specific slots** (only available in consequence categories):
- `{mission_outcome}` — the outcome band as a prose phrase ("a decisive victory," "a pyrrhic success," "a catastrophic defeat")
- `{mission_archetype}` — the mission type that was completed
- `{mission_region}` — where the mission took place

**Relational slots** (for entries referencing past events or previous chapters):
- `{previous_event_reference}` — a short callback to an earlier chain ("the revolt that had begun under {character_name}'s watch")
- `{lineage_history_note}` — a callback to the lineage's earlier involvement ("where their grandfather had once held the line")

**Category-specific slot requirements.** Each category definition specifies which slots are **required** (every fragment in the pool must use at least these) and which are **optional** (fragments may use for variety). All `lineage_*` categories require `{lineage_name}`. All `consequence_*` categories require `{mission_outcome}`. All `chain_*` categories require `{region_name}`. The required slots ensure every assembled entry in a category hits the minimum narrative beats regardless of which fragments combine.

#### Fragment Generation Rules

The library builder generates all fragments offline. These rules govern what the builder produces — they are the authoring contract that all fragments (AI-generated or human-authored) must satisfy.

**Rule 1 — Tone lock.** Every fragment in a category must match that category's emotional register. The register is specified in the category definition and is part of the generation prompt.

**Rule 2 — Slot discipline.** Fragments may only use slots from the defined vocabulary. No invented slots, no inline data. If a fragment needs information not in the vocabulary, the vocabulary should be expanded — the fragment should not hardcode a value.

**Rule 3 — Slot optionality.** Not every fragment uses every slot. The assembler filters each fragment pool to only fragments whose required slots are resolvable from the current cluster's data. Fragments referencing `{character_name}` are excluded from selection when no named character is associated with the cluster. This filtering is how the system handles variable data availability without special-case logic.

**Rule 4 — No cross-fragment assumptions.** An opening cannot assume which detail follows it. A closing cannot reference something only mentioned in a specific opening. Each fragment is self-contained within its type. Shared context comes exclusively through the variable slots — if both the opening and detail reference `{character_name}`, they resolve to the same character because the assembler fills all slots from the same cluster data.

**Rule 5 — Prose quality floor.** Fragments read like excerpts from a real historical text. No game-speak ("the player's faction"), no mechanical language ("stability dropped to 23"), no meta-commentary ("in a dramatic turn of events"). The chronicle is an in-world document. State slots like `{stability_level}` resolve to qualitative prose ("precarious," "fragile"), never raw numbers.

**Rule 6 — Length hard limits.** Opening: max 30 words. Detail: max 60 words. Closing: max 50 words.

**Rule 7 — Temporal language conventions.** Openings own time-anchoring language. Details and closings continue from the opening's temporal frame without re-anchoring. This prevents assembled entries from feeling choppy when fragments combine.

**Rule 8 — Category-specific required slots.** Every fragment in a category must use all slots listed as required for that category. This is validated structurally during the validation pass.

#### Fragment Volume Per Category

Each category is authored with: **6 openings × 8 details × 5 closings = 240 unique assembled entries per category.** Across 20 categories, this produces 4,800 potential unique scroll entries from 380 total fragments. This is the launch target — pool sizes can be expanded post-launch by generating additional batches per category.

#### Library Builder Validation Pass

After generating a batch of fragments for a category, the builder runs a three-layer validation pass before the output ships.

**Layer 1 — Structural validation (deterministic, no AI).** Every fragment uses only slots from the defined vocabulary. Every fragment uses all required slots for its category. Word counts are within hard limits. No fragment contains mechanical or meta language from a rejection list. Fragment IDs are unique across the entire library.

**Layer 2 — Deduplication (algorithmic).** Levenshtein distance between every pair of fragments within the same type pool in the same category — fragments below a configurable edit distance threshold are flagged as near-duplicates and the duplicate is discarded. Cross-category deduplication on openings specifically, since temporal anchoring phrases ("In the decades that followed," "A generation later") are the highest duplication risk across categories. **Diminishing returns flag:** if a generation batch loses more than 30–40% (configurable threshold) of its output to dedup rejection, the builder flags it rather than silently shipping a thin pool. The flag signals that the generation prompts need diversification before the next batch — not that the builder should retry with the same inputs. This is especially relevant for openings, which lean on a naturally limited set of temporal anchoring phrases.

**Layer 3 — Tone and coherence validation (AI-assisted).** A second AI pass reads each fragment against the category's register description and flags fragments that don't match the intended tone (classification task, not generation). A sample of assembled entries (~10 random opening + detail + closing combinations per category) is evaluated for coherence — does the assembled entry read as a single prose passage or do the fragments clash? Sampling catches systematic compatibility issues without validating every possible combination.

**Validation output:** The builder produces the fragment library plus a validation report listing flags, rejections, thin pools, and diminishing returns alerts. The report is reviewed before the library ships. Flagged categories get prompt revision and regeneration. Clean categories ship as-is.

### Lineage Entanglement

The game revolves around the player living their lineage. The scroll is the player's primary window into their family's ongoing story across generations. To ensure the lineage is consistently woven into the world's events during time jumps, the simulation actively entangles the player's family with significant events.

**Mechanism: significance bonus for lineage-occupied regions.** The coherence ledger tracks where lineage members currently live. Events that fire in regions where lineage members reside receive a static significance bonus in Pass 1 of the distiller's scoring. This is not a new system — it is one additional term in the existing significance scoring formula, controlled by a single config value. Lineage events score higher, so they naturally bubble up to the top of the distiller's rankings and fill the Tier 1 lineage clusters.

When a significant event fires in a lineage-occupied region, the coherence ledger attaches the relevant family member to the event log entry — the same mechanism it already uses for any named character involved in an event.

**Lineage role: military family.** The player is a military commander. Their lineage is a military family. Lineage members attached to events are always framed as military figures — officers, force commanders, garrison leaders. If they're involved in a political crisis, they're the military leader dealing with it. If they're involved in an economic collapse, they're the commander watching their supply lines dry up. One role, one framing, consistent across all event types.

This is not fabricating history — it reflects the reality that a prominent military family (which the player's lineage is, by definition) would realistically be involved in major events in their region. The simulation makes this happen through a simple scoring bias rather than hard scripting.

---

## The World

### Scale

Small enough for a solo dev to build, large enough to feel vast:
- The number of systems, inhabited regions, and uninhabited space is **variable** — determined by the simulation's configuration and the needs of the current playthrough. The world should feel vast without being unmanageable.
- The civilization starts small — a handful of inhabited regions in a mostly dark world
- Expansion happens through the simulation over time, not given for free
- Uninhabited systems serve as locations for exploration missions
- The world is the same one across all chapters and cycles — it changes over time, but it's persistent. Ruins from previous cycles accumulate.

### World Generation — Tiered Templates

The world's starting state is generated from a **starting template** — a hand-designed topology skeleton with randomized field values within defined ranges. Templates ensure every start is playable while providing variety across playthroughs.

Each template defines: the number and arrangement of starting regions (home, frontier, empty/unexplored), the adjacency graph connecting them, and stat ranges per region tier. The home region starts with strong field values (the civilization's established core). Frontier regions start weaker (recently settled, resource-constrained). Empty regions have no state and are activated when expansion events fire during the simulation.

**Starting templates (2–3 to start, more added if needed):**

- **Isolated start** — 1 home region, 2 adjacent frontier regions, 4–6 empty regions beyond. The civilization is a single cluster pushing outward. Straightforward, good for learning the game.
- **Twin colony** — 2 home regions connected to each other, 1–2 frontier regions each, empty space around and between. The civilization has two centers of power from the start, creating natural factional dynamics and resource competition.
- **Archipelago** — 1 home region, 3 frontier regions with sparse connections (not all adjacent to each other or to home). The civilization is stretched across disconnected outposts with fragile supply lines. High early pressure, strategic isolation.

Field values within each template are randomized within ranges (e.g., home military 55–70, home economy 60–75) so two playthroughs on the same template feel different. The template is selected at game start — either player choice or random.

**Implementation approach (Stage 0):** Build one template first (isolated start). Get the simulation proven on it. Then add templates incrementally, verifying each produces meaningfully different simulation behavior before adding the next.

**Multi-faction starting positions.** Templates define starting territories for NPC factions alongside the player's civilization. For the isolated start template, the Conqueror starts with **1–2 regions on the far side of the empty space**, separated from the player's frontier by one uninhabited buffer region. This creates a natural early-game rhythm: both factions expand into empty space, the buffer region becomes a contested flashpoint, and first military contact is an emergent event rather than a starting condition. The Conqueror's starting regions use their own field value ranges (config values per archetype — e.g., Conqueror home military 50–65, economy 40–55), reflecting a different civilization with different strengths.

Other templates follow the same principle: NPC factions are placed with at least one uninhabited region separating them from the player's territory. The exact placement varies per template — the twin colony template might place the Conqueror between the player's two home regions (threatening to cut them off), while the archipelago template might place the Conqueror adjacent to the player's most isolated outpost.

Template extensions for additional archetypes (the Warlord, the Fortifier, the Opportunist, the Schism) are designed when those archetypes are implemented. The Schism does not have a starting template position — it spawns from revolts during gameplay. The template format supports any number of starting factions — each defined by archetype, starting region count, position in the graph, and field value ranges.

### Inter-Region Topology — Typed Adjacency Graph

Regions are nodes in a graph. Edges represent connections between regions and carry a **type tag** that determines what propagates through them:

- **Border** — military adjacency. Antagonist pressure spreads through border edges. Military reinforcement and garrison support propagate through borders. A region with no border connection to the civilization's core is militarily isolated.
- **Trade route** — economic connection. Trade, supply, and economic interdependence propagate through trade route edges. A region connected only by trade route receives economic benefits but no military support.
- **Both** — full connection. Military and economic effects both propagate.

This separation creates strategic situations where military and economic geography don't perfectly overlap. A frontier region might be economically connected to the core via trade but militarily exposed because no border edge exists. Cutting a trade route (through blockade, hostile faction action, or regional collapse) has different consequences than losing a border (through conquest or territorial withdrawal).

Effects that reference "nearby" or "adjacent" regions specify which edge types they care about. Passive drift modifiers, faction attack propagation, event chain propagation, and the character selector's "nearby region" checks all specify edge type in their queries.

The graph is defined at world generation (part of the starting template) and grows as expansion events add new regions and edges. New edges can also form during simulation (a trade route opens between previously disconnected regions) or break (a trade route collapses due to regional instability).

**Implementation approach (Stage 0):** Start with plain untyped adjacency — all edges are "both." Get passive drift, event propagation, and faction interactions working through simple adjacency. Then add edge types as a second step and verify that separating military and economic connections produces meaningfully different simulation behavior. If the distinction doesn't matter in practice, simplify back to untyped.

### World Evolution — Per-Faction Lifecycle

The world does not have global eras. Individual factions have lifecycles, and multiple factions at different lifecycle stages coexist simultaneously. A young breakaway faction expanding into empty space exists alongside a centuries-old empire in decline. The player experiences whatever lifecycle stage their current faction is in — the "era feeling" comes from faction state, not from a global game clock or chapter number.

**What the player experiences depends on their faction's state, not the world's age:**

- **In a young faction** (few regions, low budget, expanding into empty space): missions are about establishing footholds, defending fragile frontiers, first military contacts with neighbors. The feeling is pioneer survival — scrappy, resource-scarce, every mission matters because the faction can't absorb a loss.

- **In an established faction** (multiple mature regions, strong economy, contested borders): missions involve border wars, political maneuvering, choosing which fronts to prioritize. The feeling is strategic depth — the player is a commander in a real military with real logistics and real enemies.

- **In an overextended faction** (many regions including conquered husks, budget stretched thin, revolts brewing): missions are about holding crumbling frontiers, quelling revolts, choosing what to save and what to abandon. The feeling is imperial weight — too much territory, not enough resources, every solution creates a new problem.

- **In a declining faction** (losing territory, economy degraded, breakaways forming): missions are desperate — last stands, fighting former allies, protecting the last intact core regions. The feeling is elegiac — the player watches an institution die from the inside while trying to save what they can.

- **In a faction born from collapse** (breakaway from a revolt, inheriting fragments of a destroyed empire): missions are about survival and identity — a new faction finding its footing in a dangerous world, surrounded by the wreckage of what came before.

The player may experience all of these feelings across a single playthrough as the lineage rotation moves them between factions at different lifecycle stages. A player who spends three chapters defending an empire's borders might rotate to a breakaway faction that formed from a revolt they failed to prevent — experiencing the consequences of their own failure from the other side.

**Technology loss** remains a valid mechanic but attaches to faction state, not world age. A faction whose stability and economic infrastructure have been degrading may trigger technology loss events — losing the ability to produce certain unit types, experiencing equipment unreliability, or forgetting maintenance procedures for complex systems. A thriving faction retains its capabilities regardless of how many centuries have passed. Technology loss is a symptom of decline, not of age.

### Civilizational Lifecycle — Mechanical Drivers

The world evolution described above is not scripted — it emerges from the interaction of existing simulation mechanics. This section maps the full lifecycle to the specific mechanical drivers that produce each phase. These phases describe the lifecycle of **individual factions**, not the game as a whole — multiple factions at different phases coexist simultaneously, and the world is always a mix of expanding, consolidating, fighting, and fragmenting factions.

**Phase 1 — Expansion.** Factions start with few regions and low budgets. Empty regions adjacent to faction territory are cheap to colonize (no resistance) and score well in attractiveness evaluations (maximum weakness, strategic position value from what they border). Budget is too low for confident attacks against defended regions. Result: factions expand into empty space rather than fighting each other. The world fills up. Colonized regions start with minimal field values and grow slowly through passive drift. The territorial adjacency bonus accelerates development for colonies near strong core regions, creating natural economic gradients — rich core, developing middle, bare frontier.

**Phase 2 — Consolidation.** Empty regions become scarce. Faction budgets have grown from accumulated economic output across multiple regions. Colonization opportunities dry up, so the agent's candidate pool increasingly contains only enemy-owned targets. Factions that expanded aggressively have more territory but weaker per-region fields (colonies haven't matured). Factions that expanded cautiously have fewer but stronger regions. Border friction applies where factions share borders, slowly elevating tension and dragging economy in contested frontier regions.

**Phase 3 — Conflict.** Budgets are now large enough to pass the attack confidence threshold against degraded frontier regions. Inter-faction attacks begin. The attack resolution formula favors attackers against weak frontiers. Conquered regions suffer tension spikes, economy disruption, and population loss. The conquering faction gains territory but also gains a high-tension, low-economy region that drains reinforcement budget to hold. Successful conquest attracts further aggression — neighboring factions see the newly conquered region's low military as an attractive target.

**Phase 4 — Overextension.** A faction that has conquered multiple regions faces compounding costs. Each conquered region has high tension, low economy, and low military. The faction must choose between reinforcing these regions (spreading budget thin) or accumulating for the next attack (leaving conquered territory vulnerable). Reinforcement has diminishing returns approaching the frontier tier capacity ceiling, so even heavy spending can't make a conquered frontier as strong as the attacker's home region. Meanwhile, budget growth depends on total economic output across all owned regions — conquered regions sitting at the economy floor contribute almost nothing. The faction's effective budget growth per region *decreases* as it conquers more damaged territory.

**Phase 5 — Fragmentation.** Conquered regions with sustained high tension cross revolt event thresholds. Successful revolts spawn breakaway factions that seize a fraction of the region's military and economy. The parent faction loses territory and the breakaway becomes a new hostile neighbor, adding border friction to adjacent regions. This can cascade: a revolt in one region elevates tension in neighboring regions (through border friction from the now-hostile breakaway), pushing them closer to their own revolt thresholds. A faction that overextended may lose multiple regions in rapid succession, fragmenting into several smaller factions. The breakaway factions then operate as independent agents — they may fight each other, fight the parent faction, or be reconquered.

**Phase 6 — Equilibrium or collapse.** The simulation naturally tends toward one of several late-game states depending on the stochastic path: a dominant faction that managed overextension successfully (possible but requires favorable conditions), a fractured world of many small factions in shifting conflict, or a grinding multi-front war where no faction can achieve decisive advantage. The proportional tension decay mechanic prevents permanent runaway spirals — even high-tension regions eventually stabilize if external pressure stops. This means the world can reach dynamic equilibria where factions hold stable borders, punctuated by periodic wars when budget accumulation crosses attack thresholds again.

**Why this matters for the player.** The player experiences these phases from the inside — whichever faction they currently serve. In the expansion phase, missions are about establishing footholds. In the consolidation phase, missions involve border disputes and political maneuvering. In the conflict phase, the player commands forces in real wars with real stakes. In the overextension phase, the player is sent to hold crumbling frontiers or quell revolts in conquered territory. In the fragmentation phase, the player may be fighting former allies, choosing which fragments of their civilization to save, or leading a desperate defense of the last intact core region. Because the player can rotate between factions at different lifecycle stages, they experience the full range of these situations across a playthrough — not as a scripted progression, but as the world's natural churn viewed from different perspectives.

**Tuning the lifecycle.** The lifecycle's *shape* is emergent from the mechanics already designed. The *pacing* is tunable through existing parameters: conquest consequences control how costly expansion is, border friction rates control how fast contested borders degrade, revolt thresholds control when overextension triggers fragmentation, and reinforcement efficiency controls how effectively factions can hold distant territory. If testing shows a faction can conquer everything without fragmenting, increase the costs of holding territory. If fragmentation happens too fast, reduce them.

### Spatial Navigation

The player operates within the world spatially. During missions, you're in a system or a region, moving your forces. Between missions, the world map shows the broader picture.

The frontend is being rebuilt from scratch. No visual work from the previous iteration carries forward — ideas from it may inform future design, but the new game's visual layer will be purpose-built for the commander experience. The exact navigation model will depend on how the mission tactical layer works — to be designed.

### Map Generation System — Spine + Gradient Hybrid

> **RESOLVED.** All map generation design questions are decided. See below for gradient property vocabulary, topology templates, fog of war, recon phase, canvas sizing, and simulation-to-gradient mappings.

Mission maps are procedurally generated using a **spine + gradient hybrid** system. The generator produces a small data seed. The engine interprets that seed into a full traversable 3D space. Small data in, big interpretation out.

**The Spine** is a graph of waypoints that defines the map's strategic topology — where the objectives are, where the chokepoints are, how different areas connect, where the player starts, where enemies come from. A typical mission spine is 10–30 nodes with edges between them. Each node has a position, a type tag, and a few property values. Each edge has a connection type. The spine guarantees that the map has deliberate tactical structure — flanking routes exist because the generator placed them, not by accident.

**The Gradient Fields** fill the space between and around the spine nodes with organic navigational texture. A gradient field is a continuous function over the map space — a set of field sources, each with a position, a property type, radius, intensity, and falloff curve. The engine samples these fields to place geometry, apply environmental effects, and determine terrain character. Where a gradient says "obstacle_density 0.7," the engine places dense obstacles appropriate to the theme. Where it says "sensor_interference 0.6," the engine applies a moderate visibility reduction. Gradient fields overlap and combine naturally, producing organic terrain with no grid artifacts and no hard boundaries between zones.

#### Gradient Property Vocabulary — Five Properties

The map generator uses five gradient property types. Each is a continuous field sampled at any map position to determine terrain character at that point. All are era-agnostic — the engine defines the gameplay effect, the theme pack determines visual presentation.

**`sensor_interference`** — reduces unit sensor radius at that position. Creates fog pockets, ambush opportunities, and information denial zones. Era examples: nebula (sci-fi), fog bank (naval), dense forest (land), sandstorm (desert).

**`elevation`** — continuous height field. Higher elevation provides range bonuses, vision bonuses, and defensive advantage. Vantage spine nodes anchor elevation gradient peaks — the slope around them is a continuous advantage curve, not a binary flag. Era examples: hills and mountains (land), orbital plane advantage (space), ridgelines (naval).

**`obstacle_density`** — blocks unit movement. High density creates walls, barriers, and terrain that must be navigated around. Distinct from cover — obstacles impede movement, cover provides protection without necessarily blocking paths.

**`cover_density`** — reduces incoming damage for units in that area. Distinct from obstacles — cover protects without necessarily blocking movement. Enables terrain like trenches, low walls, and debris fields that are easy to traverse but provide protection. Era examples: fortifications (land), debris clouds (space), reefs (naval).

**`layer_accessibility_mask`** — defines which vertical layers (see 2.5D Vertical Layers) are open at each map position. Binary per-layer — a layer is either accessible or blocked at a given point. Terrain features that block layers force units to navigate over (on higher layers) or around (on the blocked layers).

**[Future expansion:]** Additional gradient properties (damage_intensity, movement_drag, ability disruption zones) can be added as new property tags without engine changes. The gradient field system is extensible by design — each new property is a new field the engine samples, not a new system.

**The division of labor:** The spine handles the decisions a level designer would make — "there should be a chokepoint here and a flanking path there." The gradient fields handle what a terrain artist would do — "this area should feel dense and dangerous, this area should feel open and exposed." Together they produce maps that are both tactically sound and visually organic.

**Why this hybrid:** The spine alone leaves the space between waypoints empty and uninteresting. Gradient fields alone produce organic terrain but can't guarantee specific tactical structures (chokepoints, flanking corridors, defensible positions). The hybrid solves both problems — the spine provides structure, the gradients provide texture.

#### Spine Node Type Vocabulary

Nine abstract node types define the tactical vocabulary for map generation. All are era-agnostic — the engine places them as abstract gameplay markers, the theme pack determines visual presentation.

**Objective** — a location the player must interact with to complete the mission. Defend this, capture this, reach this, extract from this. The mission archetype determines what the objective means. Every map has at least one.

**Staging** — a relatively safe area where the player starts or regroups. Usually near the player's entry point. Lower hazard density, defensible approaches. The recon phase starts focused here.

**Transit** — a connection area between more important nodes. Not a destination, a path. Can be open (fast movement, exposed) or constrained (slow but covered). Transit nodes define the map's circulation.

**Chokepoint** — a narrow passage between areas. Forces funnel through. Defensible from one side, dangerous to push through. The tactical structure that makes positioning matter.

**Flank route** — an alternate path bypassing a chokepoint or main approach. Longer, possibly hazardous, but avoids the obvious route. Rewards the player who reads the map and sends Strike units the long way around. Generation rules require at least one flank route per chokepoint to prevent pure-grind maps.

**Vantage** — an elevated or advantageous position. Units here get a combat bonus (range, damage, visibility). Controlling a vantage point is a positioning objective within the larger mission. Must be contestable (reachable by both sides) — never pre-owned by one side.

**Hazard zone anchor** — a node that anchors a gradient hazard field. Defines where the hazard is centered; the gradient defines falloff. Not a destination — a spatial anchor for environmental danger.

**Spawn point** — where enemy forces enter the map. Can be at the edge (enemies approach from outside) or at a node (enemies pre-positioned). Multiple spawn points create multi-vector threats.

**Extraction** — where the player needs to get something out. Different from an objective — the objective might be "retrieve the asset," the extraction point is "bring it here." Creates two-phase mission structure.

#### Generation Pipeline

The map generation pipeline transforms mission context into a unique, playable map seed in four stages.

**Stage 1 — Inputs.** The generation script receives: the **mission archetype** (which script to run), the **region state** (simulation field values for the mission region — drives simulation-flavored map character), **library hints** (optional per-archetype map modifiers from the AI-generated content library — small data packets that add specific flavor, e.g. "narrow canyon approach" or "debris-heavy area"), and a **random seed** (ensures reproducibility for replays and bug reports).

**Stage 2 — Archetype script execution.** Each mission archetype has a generation script — a **constrained random generator** (similar to AoE3's per-map-type generation scripts). The script:

1. **Picks a topology template** from a pool of structural patterns for this archetype (4–6 templates per archetype). A defense script might have: "single chokepoint with flank route," "two parallel approaches," "ring defense with central objective," "layered fallback positions." Library hints can bias template selection or add modifiers.

2. **Places spine nodes** according to the template's rules, with randomized positions within constraints. The template specifies node types and relationships ("place an objective, then 2–3 chokepoints between staging and objective, with at least one flank route per chokepoint"). Exact positions, distances, angles, and node count are randomized within ranges.

3. **Connects nodes with edges** following connectivity rules: minimum path count between staging and objective (never just one route), maximum dead-end count, flank routes must connect to at least two non-flank nodes.

4. **Places gradient field sources** based on node positions and library hint. Obstacle density gradients anchor around chokepoints. Sensor interference zones are placed according to the template's "ambush opportunity" budget. Elevation gradients anchor around vantage nodes. Cover density gradients are placed in defensible positions and approach corridors. Layer accessibility masks create vertical terrain features.

5. **Applies simulation flavoring.** Region state modifies gradient intensities through a two-layer mapping. **Composite axis baselines:** low stability → higher sensor_interference, more hazard zone anchors, higher cover_density (fortified terrain); high stability → cleaner sightlines, fewer hazards. High capacity → lower obstacle_density, smoother terrain; low capacity → higher obstacles (debris, degradation). **Individual field deltas** (bounded, cannot overwhelm baselines): economy → reduces obstacle_density along paths, adds cover from infrastructure. Tension → boosts cover_density (fortification, barricades). Military → increases obstacle_density near defensive positions. Population → scales overall feature density. All mapping values are config parameters.

6. **Applies library hint modifiers.** The hint adds specific flavor: "large sensor interference zone in the center," "vantage node overlooking primary approach," "elevated ridge along the eastern flank." Small tweaks that make each instance feel authored.

**Stage 3 — Fairness evaluation.** The generated map seed is scored by an **algorithmic fairness evaluator** before being accepted. The evaluator computes: path count from player staging to objectives vs. enemy spawns to objectives, average travel time balance for both sides, vantage point accessibility balance, hazard zone distribution symmetry. If the score falls outside an acceptable range (config thresholds), the map is regenerated with a new random seed. The evaluator runs on top of **hard constraint rules** baked into the generation scripts that prevent gross violations during generation (e.g., all player approaches can't be blocked by hazards while enemy approaches are clear, vantage points must be reachable by both sides). The constraint rules handle 90% of fairness; the evaluator catches edge cases. Map seeds are tiny (~400–500 bytes) and scripts are fast, so regenerating a few times is cheap.

**[Future consideration:]** A learned evaluator (neural network trained on playtested maps rated by fairness) can supplement or replace the algorithmic evaluator once sufficient playtest data exists. This is a post-launch evolution — the algorithmic evaluator is sufficient for launch.

**Stage 4 — Output.** The script outputs the map seed: spine (nodes + edges) and gradient field sources (position, type, radius, intensity, falloff). The engine interprets this into a traversable 3D space using the theme pack's visual vocabulary.

#### What Makes Each Mission Unique

Even within the same archetype, variety comes from four independent randomization layers:

1. **Topology template selection** — 4–6 structural patterns per archetype
2. **Node placement randomization** — positions, distances, angles, node count vary within constraints
3. **Library hint selection** — dozens of per-archetype flavor modifiers from a large AI-generated pool
4. **Simulation-driven flavoring** — region state produces different gradient intensities based on world history

The combinatorial space is large enough that effectively every map is unique while every map is guaranteed playable by the template constraints and fairness evaluator.

#### Generator Decides, Engine Interprets

The generator produces the spine and gradient fields as abstract gameplay data. The engine interprets that data into era-appropriate 3D geometry. Neither the spine nor the gradients contain any era-specific content.

The spine speaks in abstract types — "objective," "chokepoint," "vantage" — not "space station" or "fortress." The gradient fields speak in gameplay properties — "obstacle_density," "sensor_interference," "elevation," "cover_density" — not "asteroids" or "mountains." The theme pack maps abstract types to visual content: "obstacle_density 0.8" becomes a dense asteroid field in the sci-fi theme, a mountain pass in a land theme, a reef chain in a naval theme.

This is the same era-agnostic architecture the rest of the game uses. The map system never says "asteroid." It says "dense obstacle region." The theme pack decides what that looks like.

#### Continuous Movement and No Loading Screens

A single chapter may involve the player moving forces across a region or system. The map system supports this without loading screens. The spine and gradient fields define a continuous canvas — the player's forces move freely through rendered 3D space, and the engine streams geometry based on what's near the camera (standard LOD culling). There are no discrete zones to load, no boundaries to cross. The space is one continuous field from the player's perspective.

#### Moving Battlefields

The game specifies that engagements are not static arenas — the tactical space shifts during combat (see "Force and Combat Design — Moving Battlefields"). The spine + gradient system supports this naturally. Spine nodes can drift over time (the objective's position changes, the chokepoint narrows or widens). Gradient sources can move (the hazard zone drifts across the map, the obstacle density shifts as debris scatters). The result is smooth, continuous spatial change — the battlefield evolves under the player's feet without discontinuities.

#### Simulation State as Map Input

The simulation already tracks per-region state as continuous values (military strength, economic output, factional tension, population). These values feed into map generation parameters through the simulation flavoring step. A prosperous, stable region produces maps with more infrastructure and lower hazard intensity. A contested, declining region produces maps with debris, damaged structures, and higher hazard density. The map reflects the history of the region the player is operating in.

The specific simulation-to-gradient mappings use the two-layer approach described in the generation pipeline's simulation flavoring step: composite axes (stability, capacity) set baselines, individual fields (economy, tension, military, population) apply bounded deltas. The pipeline supports simulation flavoring from the start, but the generator can work with archetype scripts and library hints alone if simulation coupling is disabled.

#### Topology Templates — Node-Relationship Recipes

Each mission archetype has 4–6 topology templates. A template is a recipe — a set of constraints that the generator satisfies through randomized placement, not a fixed graph.

A recipe specifies: node type counts and required relationships ("place 1 objective, 2–3 chokepoints between staging and objective, at least 1 flank route per chokepoint, 2 spawn points from separate vectors"), spatial relationship hints ("objective behind staging," "objective central," "spawn points surrounding"), and structural constraints ("minimum 2 paths between staging and objective," "no more than 1 dead-end node").

Exact positions, distances, angles, and the specific node count within the recipe's range are randomized. The recipe guarantees the map's tactical structure; randomization guarantees variety within that structure.

Templates are data, not code — the constraint language is shared across all mission categories. New templates can be added to the library without engine changes. Templates are validated against the fairness evaluator's hard constraints during authoring. Total template count across all five mission categories: ~20–30.

#### Fog of War — Multiplicative Sensor Radius

Each unit has a base sensor radius defining a circle of revealed map around it. The `sensor_interference` gradient at the unit's current position scales that radius downward: interference 0.0 = full base radius, interference 1.0 = zero visibility. The revealed area on the map is the union of all friendly units' sensor circles.

**Cross-layer visibility.** Units reveal only their own layer by default. Vantage spine nodes grant cross-layer visibility — a unit at a vantage position can see units on adjacent layers within a reduced sensor radius.

#### Recon Phase — Terrain Visibility, Enemy Hidden

During the recon phase (pre-mission free camera, no time pressure), the player sees all terrain features: elevation contours, cover and obstacle density, hazard zones, spine node types (chokepoints, flanking routes, objectives, extraction points), and layer accessibility. Enemy positions and spawn points are hidden.

When the player hits "Begin Mission," fog of war activates based on sensor coverage rules. The player retains knowledge of the terrain they studied but must discover enemy positions through sensor contact.

This requires no new simulation variables. Recon quality is uniform across all missions — the player always gets full terrain visibility regardless of world state.

#### Canvas Sizing — Archetype Base with Simulation Modifier

Each mission archetype has a base canvas size category (small, medium, large) that maps to a dimension range. The simulation state of the mission region applies a bounded modifier (±30% of base) derived from existing region fields (economy, military, tension, population).

The modifier direction is per-archetype — the archetype determines whether a wealthy/stable region means bigger or smaller canvas for its tactical situation. A military defense in a wealthy core region produces a larger canvas (more developed space to defend). An intelligence mission in a wealthy region produces a smaller canvas (tight infrastructure environment). A defense on a devastated frontier produces a smaller, tighter canvas (less to work with, desperate engagement).

#### Data Budget

A complete mission map seed is approximately 400–500 bytes of data:
- **Spine:** ~15 nodes × ~14 bytes each (position, type, properties, layer mask) + ~25 edges × ~4 bytes each = ~310 bytes
- **Gradients:** ~12 field sources × ~8 bytes each (position, type, radius, intensity, falloff) = ~96 bytes
- **Library hint reference + simulation flavoring metadata:** ~50 bytes

The engine turns ~450 bytes into an entire traversable 3D space. Seeds are small enough to log for replay and bug reports.

### Visual Style

Low-poly, Art of Rally aesthetic. Solo developer. 3D stylized.

---

## Tone and Feel

### Elegiac, Not Grim

The game is about civilizations rising and falling over vast timescales. The tone is that of a real history being recorded. There is tragedy — the threat cannot be stopped, only delayed. But there is also humor, beauty, and unexpected moments of hope.

### The Humor

The game has a sense of humor. Easter eggs, dry observations, and unexpected moments of levity are intentional. The humor is in the writing, not in the events. Dry, earned, and occasionally absurd.

### The Weight of Time

The generational structure gives the game something almost no other game has: **the passage of centuries felt through play**. The player doesn't just read about time passing — they played the chapter that caused this. They remember the commander who failed, and now they're living with the consequences as someone new.

---

## What's Unique (Blue Ocean)

The combination that doesn't exist in any current game:

1. **Genuinely stochastic simulation** underneath a strategy game — you're not playing against scripted AI or deterministic systems. The world has its own probability space.
2. **Generational chapter structure** — you're not one persistent character or one persistent empire. You're a series of people inside a civilization that changes around you.
3. **Commander, not king** — you don't control everything. You control a task force on a mission, and the civilization has its own plans.
4. **AI-generated mission and narrative content** — every playthrough is contextually unique through library-built templates with simulation-driven variables.
5. **The tragedy of understanding** — you can read the system, master the patterns, and still face outcomes you can't prevent. Mastery means you understand WHY you lost, not that you always win.
6. **Cyclic civilizational arcs** — the game loops through early/mid/late eras, with each cycle carrying the scars and ruins of the last. The Ouroboros isn't a name — it's the structure.

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

---

## AI Integration Pillar

AI is a core differentiator for this game, not an add-on. AI integration points:

- **Library builder pipeline** — generates chronicle templates, mission archetypes, briefing content, complication templates, and event narratives offline. Pre-generated, stored in JSON, read at runtime. No runtime API calls during play.
- **Dynamic naming system** — generates names for everything in the game across four categories: people (commanders, faction leaders, regional commanders, lineage members), places (regions, systems, landmarks), units (individual named assets, task forces, squad designations), and factions (civilization names, breakaway faction names, external faction names). Draws from a vast cultural range (historical human naming conventions, Tolkien-esque construction, ancient Greek, Sumerian, invented linguistic roots, and beyond). See "Dynamic Naming System" section below for full design.
- **Unit stat tuning** — AI generates per-civilization stat profiles for unit classes within hand-designed mechanical constraints.
- **Unit power balancing** — AI-generated units are scored with strength values. The force parity system uses these scores to ensure missions present winnable fights: the player receives forces with comparable total strength to the enemy, adjusted by civilizational capacity and difficulty setting.
- **Mission variable filling** — AI helps generate the specific narrative context for mission briefs within archetype templates.
- **Chronicle generation** — AI-authored templates produce emergent narrative that reads like real history.
- **Chronicle scroll distillation** — AI-generated templates for compressing hundreds of time-jump events into 5–10 scroll entries.
- **Potential future** — AI-generated antagonist archetype variants, civilization personality profiles, faction flavor, additional mission archetypes.

The principle: **AI generates content within mechanical frameworks.** The engine defines the constraints. AI fills in the specifics. The engine can handle any output because the constraints guarantee validity.

### Automated Balance Testing via Self-Play

With 6 unit types, multiple tech tiers, and AI-generated stat variation, manual balance testing is impractical. The plan is an automated balance testing pipeline that runs headless simulated combat to detect gross imbalances and degenerate strategies.

**Phase 1 (earliest, pre-launch viable):** Scripted heuristic bots play the tactical layer in headless mode (pure Python, no Godot). Simple strategies ("move Strike toward nearest Siege, keep Bombard at max range"). Bots don't need to be good — they need to be consistent enough to reveal gross imbalances. Run thousands of engagements per hour across force compositions and tech tier matchups. Output: composition-vs-composition win rate matrix. Matchups outside a target band are flagged automatically.

**Phase 2 (post-launch):** Self-play reinforcement learning (PPO or AlphaZero-style MCTS) on the reduced tactical state. Networks discover emergent strategies that scripted bots miss. When a network finds a degenerate strategy (e.g., always rush with 6 Raiders wins), that's a balance flag.

**Phase 3 (ongoing):** Automated tournament brackets as a continuous integration tool. Every stat change triggers a rerun. The tactical layer's state space is small enough for CPU-based training.

This is a **post-tactical-layer tool** — prerequisites are a working tactical layer, stable unit stats, and representative map generation. Implementation is far future. Noted here so the design is not lost and so the tactical layer's architecture does not make headless simulation impossible.

### 3D Asset Pipeline — AI-Assisted Modeling with Human Cleanup

The game's low-poly, Art of Rally visual style is a deliberate design choice that also creates a significant production advantage: low-poly assets (200–500 polygons per model, flat or minimal shading, clean geometric forms) are dramatically easier to produce at scale than photorealistic models. This section defines the asset pipeline for producing the 3D models that populate each era — units, environment objects, and structures — at a cost and pace that supports the expansion pack business model.

**Pipeline philosophy: AI generates 70%, humans finish 30%.** Current AI 3D model generation tools (as of early 2026) produce base meshes that are usable starting points but not production-ready without cleanup. The low-poly art style minimizes the gap between AI output and final asset quality — a rough AI-generated shape needs less refinement to become a clean low-poly model than it would to become a detailed realistic one. The pipeline leverages this by using AI tools for rapid base mesh generation and Blender for standardization, cleanup, and visual consistency enforcement.

**Target asset counts per era pack.** Each era requires approximately 15–20 unique unit models (covering the Strike/Line/Siege categories and their sub-roles across the era's visual language) and 10–15 environment object types (mapped to the abstract types the spine + gradient map system places: obstacle, hazard, structure, resource node, debris). Total per era: roughly 25–35 unique 3D assets, all low-poly.

#### Tool Recommendations

Three AI 3D generation tools are viable for this pipeline, each with a different strength:

**Meshy** — the primary generation tool. Meshy offers a dedicated Low Poly Mode that produces efficient wireframes optimized for real-time engines, directly aligned with the game's art style. It has a native Godot plugin for direct scene import. Text-to-3D and image-to-3D modes are both available — image-to-3D produces more consistent results when fed concept art or reference sketches. Exports to GLB, OBJ, FBX, and BLEND. Pricing: free tier with 100 monthly credits; Pro at ~$20/month with 1,000 credits (~50 model generations per month, more than sufficient for a full era pack in a single billing cycle). Meshy is the fastest path from prompt to base mesh.

**3D-Agent** — the best option for Blender-integrated generation. 3D-Agent is a Blender plugin that generates models directly inside Blender using Blender's native modeling tools via Claude MCP integration. The critical advantage over web-based generators is topology quality: it produces clean quad-based wireframes rather than triangle soup, which makes post-generation cleanup significantly faster. Models appear directly in the Blender scene — no export/import cycle. Pricing: free tier at 15 prompts/month, paid tiers at $10–30/month. Best used for hero assets or models where topology quality matters most (units that need clean silhouettes at tactical zoom distance).

**Tripo** — the budget option with polycount control. Tripo offers explicit polycount and mesh density controls on output, allowing precise polygon budget targets per model (e.g., 300–500 polys for the game's low-poly style). Clean quad/triangle topology control. Pricing: ~$12/month. Best used as a secondary tool when Meshy's output needs a different geometric interpretation or when precise polycount control matters.

These tool recommendations reflect the state of AI 3D generation as of early 2026. The landscape is evolving rapidly. The pipeline design is tool-agnostic — any text-to-3D or image-to-3D tool that exports to standard formats (GLB, OBJ, FBX) can substitute into this workflow. The pipeline's value is in the workflow structure, not in any specific tool dependency.

#### Per-Era Production Workflow

**Step 1: Concept art generation.** Before any 3D work, produce 2D reference images for each unit and environment type in the era's visual language. These can be hand-sketched, AI-generated (image generation tools like those in Meshy's pipeline), or sourced from reference boards. The reference image defines the target silhouette, proportions, and visual identity for the asset. For a WW2 era: "low poly Panzer heavy tank, flat shaded, isometric view." For Imperial China: "low poly junk combat unit, flat shaded, top-down angle." The reference image is the creative control point — it's where art direction happens.

**Step 2: Base mesh generation.** Feed the reference images into Meshy's image-to-3D pipeline (or text prompts into text-to-3D) with Low Poly Mode enabled. Generate 3–4 variations per asset and select the best starting shape. This step takes roughly 1–2 minutes per asset. For a full era (25–35 assets), base mesh generation is a single work session.

**Step 3: Blender cleanup and standardization.** Import the selected base meshes into Blender. This is where visual consistency is enforced across the era. The cleanup pass includes: fixing topology issues (removing degenerate faces, ensuring clean edge flow), adjusting polygon count to match the game's target poly budget, standardizing the color palette and material assignments to the era's visual identity, ensuring distinctive silhouettes at tactical camera distance (units must read clearly when small on screen), and verifying export compatibility with Godot. For low-poly models, this cleanup pass is fast — typically 20–45 minutes per asset. No fine sculpting, no complex UV unwrapping, no PBR material authoring. Just clean geometry with flat colors.

**Step 4: Export and integration.** Export cleaned assets from Blender in GLB or GLTF format (Godot's preferred 3D format). Assets are organized into the era pack's content directory structure alongside the JSON data files (naming libraries, chronicle templates, event templates, unit stat profiles). The engine's existing era-agnostic loading system consumes the 3D assets through the same abstract type mapping it uses for everything else: the theme pack maps "heavy combat unit" to the WW2 era's heavy tank model, or the Roman era's war galley model, or the sci-fi era's battlecruiser model.

#### Environment Assets

Environment objects follow the same workflow but are simpler to produce. Environment pieces don't need rigging or animation — they're static geometry. A low-poly asteroid field, a cluster of Roman columns, a bombed-out WW2 building — these are geometrically simple shapes that current AI tools handle well with minimal cleanup. The spine + gradient map system places environment objects by abstract type ("dense obstacle region," "hazard zone," "structure cluster"), and the era pack maps those abstract types to the era's visual prefabs. Each era needs 10–15 environment object types, and cleanup time per object is typically under 15 minutes.

#### Cost and Time Per Era

Estimated production cost per era pack's 3D assets: one month of Meshy Pro ($20) covers all base mesh generation credits. Blender cleanup at 30 minutes average per asset across 30 assets totals roughly 15 hours of modeling time. If self-taught in Blender (the low-poly modeling learning curve is approximately 2–3 focused weeks for someone with prior game development experience), the ongoing per-era cost is $20 in tooling plus 15 hours of labor. If outsourced to a freelance low-poly 3D artist, the cleanup pass costs roughly $20–50 per asset, or $600–1,500 per era. Either path produces a complete set of 3D assets for an era pack at a cost well within the revenue the era pack generates at a $2–3 selling price across even modest player numbers.

#### Future Pipeline Evolution — Modular Kit-Bashing

As the era catalog grows, a modular kit-bashing approach may replace or supplement the per-asset generation workflow. Instead of generating complete models per era, the pipeline would build a library of modular parts — hull shapes, turret types, propulsion modules, weapon mounts, structural details — that are recombined per era through assembly recipes defined in the theme pack JSON. A Roman-era "Line" unit might combine a galley hull module, a ram prow module, and a sail module. A WW2 "Siege" unit might combine a heavy tank chassis, a large turret, and track modules. The parts are modeled once (or AI-generated and cleaned once), then recombined per era. This approach becomes increasingly efficient at scale because each new era reuses the modular library with new combinations rather than starting from scratch, and it naturally enforces visual consistency because every unit in every era is built from the same construction grammar. The modular approach is a natural evolution once the per-asset pipeline has produced enough eras to identify which part categories are universal across eras. It is not required for the first several era packs — the per-asset Tier 1 workflow described above is sufficient and simpler to execute.

### Dynamic Naming System

The naming system generates names for all named entities in the game: people, places, units, and factions. It uses a variable-driven prompt architecture that produces massive output diversity through combinatorial variety, drawing from historical human naming conventions, Tolkien-esque construction, ancient Greek, Sumerian, invented linguistic roots, and beyond.

**The naming library is completely separated from the game.** Generated offline by the library builder pipeline, shipped as static JSON data. Zero runtime AI dependencies. No runtime API calls, no regeneration, no redraw. The game reads from pre-generated pools. This separation is non-negotiable — the game must never depend on AI availability at runtime.

#### Variable-Driven Prompt Architecture

The system uses a multi-stage pipeline. An AI first generates a diverse set of naming variables across three categories. Those variables feed a prompt builder that constructs generation prompts. A second AI pass produces the actual names. The combinatorial variety of variable combinations means the output stays fresh across runs without handcrafting individual prompts.

**Three variable categories:**

**Linguistic roots** (~15–20 values) — the phonetic foundation. Values like: Semitic triconsonantal, Polynesian open syllables, Germanic compound, Sino-monosyllabic, Tolkien-esque (Elvish-inspired), ancient Greek, Sumerian, invented liquid-heavy, invented guttural-aspirated, and others spanning a vast cultural range.

**Phoneme patterns** (~10–15 values) — structural rules layered on top of roots. Values like: patronymic (-son, -ov, -ibn), place-derived (-of-[place]), title-prefix, two-part compound, single name only, and others.

**Cultural flavor tags** (~8–12 values) — aesthetic/tonal direction. Values like: martial, pastoral, mercantile, priestly, frontier/rough, imperial/formal, and others.

Era markers are deliberately excluded as a variable category — consistent with the era-agnostic engine principle. Era-appropriate name presentation is handled by the theme pack layer, not the name generator.

#### Per-Faction Variable Subsets

At world generation, each faction is assigned a curated subset of allowed values per variable category (e.g., 2–3 linguistic roots, 3–4 flavor tags). All names for that faction are generated from prompts assembled from its allowed subset. Each generation batch, the prompt builder randomly selects one value from each of the faction's subset categories — pure random selection, no rotation tracking.

Subset width is a tuning knob for faction personality: a large subset produces diverse, cosmopolitan-sounding names (appropriate for the player's multi-regional civilization). A narrow subset produces coherent, monocultural-sounding names (appropriate for an isolated aggressive faction).

**Schism cultural drift.** Breakaway Schism factions inherit their parent faction's variable subset with one value swapped — representing cultural divergence. The Schism's names sound *almost* like their parent faction but slightly off, producing emergent cultural worldbuilding through the naming system.

#### Era-Split Pools

50% of each naming pool is **era-agnostic** — names that work across all theme packs, generated without era-specific style constraints. 50% is **era-specific** — generated per theme pack, with style prompts appropriate to that setting.

At runtime, the game draws from the era-agnostic pool half the time and the current era's pool the other half. The base engine ships with the era-agnostic pool plus the sci-fi era pool. Each future theme pack expansion adds its own era-specific pool that slots in alongside the permanent era-agnostic names.

#### Library Sizing

Initial release pool sizes per faction: 500 people names, 200 places, 200 units, 100 faction names. These are starter values — pool sizes will increase for full release. Generated offline in batches by the library builder.

#### Deduplication

Levenshtein distance filter at library build time. Names below a configurable edit distance threshold (e.g., 3 edits) from any other name in the same batch are discarded — no redraw, no additional API calls on rejection. Matches are simply dropped. The pool ships pre-cleaned. No runtime deduplication.

#### Name Reuse

Names assigned to active characters in the coherence ledger are unavailable for new assignment. Once a character has been dead for 500+ ticks, their name returns to the available pool. Across long playthroughs (1,000–2,000+ ticks / 10–20 gameplay hours), occasional name reuse is natural and expected — the same way real human naming traditions produce many people with the same name across centuries.

#### Coherence Ledger Interface

The ledger calls the naming system on character creation with a thin interface: `get_name(faction_id, category)` → string. The naming system returns a name from the appropriate pool and marks it as used. Clean separation of concerns — the ledger doesn't know about linguistic roots or variable subsets; the naming system doesn't know about characters, roles, or lifespans. The naming system needs faction IDs at initialization (minor coupling to world generation).

---

## Transition from Previous Iteration

The game was previously an elegiac god-game where the player observed as "The Unseen Hand" and applied abstract declarations through a particle-based fate space. The redesign changes the player's role to commander, the interaction model to missions, and the game loop to generational chapters. This section captures what survives, what's cut, and what changes.

### New Project

The redesign starts a new project. Code from the old project is selectively copied during Stage 0 (see dev_rules.md), not inherited wholesale. The old repo is preserved as reference.

### Simulation Backend — Survives with Modification

The simulation backbone is the most valuable existing asset. **The simulation redesign is now resolved — see "The Simulation Backbone" section for the full architecture.** The engine uses a System Dynamics model with stochastic event chains, a layered region state model (granular fields + composite axes), and a defined tick resolution sequence. The core *concepts* from the previous iteration (multi-dimensional civilizational state, stochastic event firing, emergent narrative through a coherence ledger) survive in the new architecture. The specific old implementation (3D vector space with Entropy/Continuity/Reach, the old tick resolution model) is replaced by the new SD-based system.

**Likely to survive in some form:** The concept of a multi-dimensional state space for civilizational health. The outcome mapper concept (proximity-based probability). The coherence ledger (named character tracking — becomes more central as it drives character selection, inheritance missions, and chronicle scroll content). The region model and world state concepts. The library reader and its fallback contract. The template assembler's text generation machinery. Config values as a starting reference.

**Likely to need new operating mode:** The antagonist agent — replaced by the multi-faction agent model. All factions (including the player's civilization) run autonomous agents during time jumps, making discrete attack/defend/accumulate decisions each tick. The event firing system — runs in batch during time jumps. The tick system — must support autonomous batch processing (hundreds of ticks, no player input).

**Replaced conceptually:** The declaration resolver's force math is repurposed as the engine for translating mission outcomes into simulation inputs. Instead of six small per-tick player nudges, one consequence bundle of region stat changes is injected per mission. The per-tick player declaration interface is gone.

### Simulation Backend — New Systems Needed

Four new backend systems are required to support the mission-based game loop:

**Mission generator** — reads simulation state, identifies pressure points, matches them to library archetypes, fills variable slots, produces a structured mission briefing. This is the bridge between the simulation and the player.

**Chronicle scroll distiller** — takes hundreds of ticks of accumulated events from a time jump and compresses them into 5–10 scroll entries. Uses a three-pass algorithm: significance scoring (template tier as floor, delta magnitude as boost, context multiplier), lineage-first clustering (lineage → chain → regional summary), and keyed composable template selection (category-matched fragment assembly with base/expanded forms). See "The Chronicle" section for full algorithm.

**Character selector** — runs after the mission generator selects a mission region. Decides whether to continue the current lineage (delta-driven rotation probability with crisis veto and hard cap) or rotate to a new one (mission-coupled selection from three weighted pools: previous lineage descendant, nemesis descendant, unrelated). Manages minimal lineage member generation during time jumps (count + location, no traits). See "The Generational Structure" section for full algorithm.

**Mission outcome resolver** — takes the tactical layer's outcome band classification and produces region stat changes for the mission region using per-archetype proportional lookup tables. No separate vector nudge or world-wide momentum — consequences are region-local and the simulation propagates them naturally. See "Missions" section for full algorithm.

### Frontend — Fresh Start

All Godot frontend code is rebuilt from scratch. No visual work carries forward. The previous iteration's visuals were designed for a god-game observer — the new game needs a commander's interface. Ideas from the old visual work may inform future design but are not copied or ported.

**Cut entirely:** The fate space (particle visualization, declaration HUD, projection cones, counter-currents). The declaration UI (six buttons, hint system, resonance meter). All declaration feedback systems (ripple, bloom, comparison view). The role selection screen. The manifold line chart. The chronicle compression columns. The Unseen Hand identity.

**Will be rebuilt purpose-built:** World view, system view, planet view. Mission briefing screen. Recon phase view. Tactical mission layer (the biggest new frontend system). Chronicle scroll UI for time jump montages. Chronicle as intelligence feed during missions. Mission preference and difficulty selection in onboarding.

### Library Pipeline — Expands

The library builder architecture (offline generation, JSON storage, caching contract, API dispatcher) is the right pattern. The existing builder scripts and generated content survive. New builder scripts are needed for: mission archetype templates (15–20 across five categories), mission briefing prose, chronicle scroll entry templates, and complication templates per mission category. The existing 102 event templates still generate events during time jumps and feed the scroll distiller.

---

## Open Design Questions

> **Governance reminder:** This section is a staging area. When a question here gets resolved through brainstorming, write the answer into its natural section in the bible and remove the question from this list. If you are an AI session and you see decided content that still appears here as open, or an unresolved question living only inline elsewhere, flag it for Westley.
>
> **As of v1.15, the following new design questions are open.** Previous questions remain resolved.

### 1. Simulation Engine — Multi-Faction Design (RESOLVED across v1.01–v1.11)
*Fully resolved. Core architecture, faction agents, attack/conquest mechanics, colonization, diplomacy, oscillation, and all tuning passes complete. See "The Simulation Backbone" and "The Antagonist System" sections.*

### 2. Force and Asset Design (RESOLVED in v1.12)
*Fully resolved. 6-unit roster, one ability per unit, light economy, force allocation algorithm. See "Force and Combat Design" and "The Player's Toolkit" sections.*

### 3. Combat and Tactical Layer (RESOLVED in v1.12)
*Fully resolved. Layers are map-defined terrain, standard RTS camera, one base environmental hazard type (sensor interference), mission type differentiation through force comp + map + objectives. See "Force and Combat Design" sections.*

### 4. Map Generation System (RESOLVED in v1.13)
*Fully resolved. Five-gradient property vocabulary (sensor_interference, elevation, obstacle_density, cover_density, layer_accessibility_mask). Topology templates as node-relationship recipes (4–6 per mission category). Fog of war via multiplicative sensor radius reduction with cross-layer visibility at vantage nodes. Recon phase: terrain visible, enemies hidden. Canvas sizing: archetype base + bounded simulation modifier with per-archetype direction. Simulation-to-gradient mappings: composite axes for baseline intensities, individual fields for bounded texture deltas. See "Map Generation System" section.*

### 5. Dynamic Naming System (RESOLVED in v1.13)
*Fully resolved. Three variable categories (linguistic roots, phoneme patterns, cultural flavor tags — era markers excluded per era-agnostic principle). Per-faction variable subsets with Schism cultural drift inheritance. Levenshtein dedup at build time, no redraw. Era-split pools (50% agnostic / 50% era-specific). Library fully separated from game, zero runtime AI dependencies. Ledger pulls via thin interface. See "Dynamic Naming System" section under AI Integration Pillar.*

### 6. Diplomacy and Peace System (PARTIALLY RESOLVED — v1.16)

**Resolved in v1.16:** Three diplomatic states (hostile/neutral/cooperative). Cooperative benefits: adjacency bonus sharing, border friction removal, technology convergence. Peace formation: event-driven through sustained non-aggression and stability thresholds. Betrayal mechanic: per-tick probability roll scaled by archetype, opportunity, and internal pressure. Betrayal consequences: surprise attack + flip to hostile, no reputation system. See "Diplomatic Stance" section in The Simulation Backbone.

**Remaining open sub-question — tech sharing formula:**

The exact formula for technology convergence in cooperative peace is not yet resolved. The design intent is established (lower-tech faction gains toward higher partner, diminishing returns per additional partner), but the specific mechanic needs a decision:

- **Best-partner-only:** Only the highest-tech cooperative partner contributes convergence. Zero stacking. Simplest option.
- **Diminishing returns per partner:** Each additional partner contributes less (e.g., decay factor of 0.5 per additional partner). Slightly more complex, rewards multiple partnerships marginally.
- **Hard cap on total bonus:** All partners contribute equally, but total convergence per tick is capped at a maximum value.

This sub-question should be resolved before writing the tech sharing formula into the bible and before Stage 4+ implementation of the diplomacy system.

### 7. Technology System (PARTIALLY RESOLVED — v1.16)

**Resolved in v1.16:** Single numeric tech_level (0–100) per faction. Archetype-interpreted multipliers (attack efficiency, defense efficiency, economic growth). Breakaway inheritance (copy parent's tech_level). Technology loss through event chains. Tech tiers (3–4 per era) unlock unit variants through era-specific theme pack content. Tier regression possible. See "Technology System" section in The Simulation Backbone.

**Remaining open sub-questions:**

1. **Growth formula** — what drives tech growth per tick? Economy? Population? Combination? What's the formula structure?
2. **Multiplier magnitude** — how much does tech actually matter? 10% edge at max tech? 30%? This determines whether tech is one factor among many or a dominant force.
3. **Tech tier count and boundaries** — 3 tiers or 4? Where do the boundaries fall in the 0–100 range? Uniform spacing or non-uniform?
4. **Tier transition style** — discrete jumps or smooth interpolation between tiers?
5. **Sci-fi era tier sketch** — rough creative direction for what each tier looks and feels like in the base game's sci-fi setting. This is theme pack content, not engine design, but it needs to exist before the AI library can generate tier-specific unit profiles.

---

## Document Maintenance

### Rules

1. **This file is the single source of truth.** If something in another doc conflicts with this file, this file wins. Other docs should reference this file, not duplicate its content.
2. **Append-only unless Westley approves.** See the modification rule at the top of this document. AI sessions add and expand. They do not delete or replace.
3. **Conceptual only.** No implementation details (file paths, function signatures, JSON shapes, config values). Those belong in architecture and stage docs.
4. **Update, don't append.** When a design decision changes *with Westley's approval*, update the relevant section in place. Don't add a "revision note" at the bottom — the document should always read as current.
5. **Open questions move to resolved.** When a question from the "Open Design Questions" section gets answered through brainstorming, the answer gets written into the appropriate section of the bible and the question gets removed from the open list.
6. **One file, not many.** Resist the urge to split this into multiple docs until the design is stable enough that sections are genuinely independent. Splitting too early creates the doc clutter and conflicting information problem.
7. **Version numbering.** The bible filename includes a version number: `game_bible_X_XX.md`. Every time the document is modified, the version number increments (1.00 → 1.01 → 1.02, etc.). Major structural changes (new sections, significant redesigns) increment the whole number (1.xx → 2.00). Minor additions, resolved questions, and refinements increment the decimal. This makes it easy to confirm which version a Claude Code session or brainstorming conversation is working from.

### Workflow with AI

- **Brainstorming happens in Claude.ai conversations.** These are ephemeral — they're for exploration, not record.
- **Decisions get captured here.** After a brainstorming session produces decisions, this document gets updated. The conversation can be discarded.
- **Claude Code reads this file as its north star.** When implementation begins, Claude Code sessions start by reading this file to understand what the game is.
- **If a brainstorming session is long and needs to be continued across conversations, produce a `continuation_context.md`** that captures the current state of the discussion. This is temporary scaffolding — the decisions from it should be merged into this bible before implementation begins.
