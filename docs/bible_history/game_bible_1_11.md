# Ouroboros Manifold — Game Bible

> **This is the single source of truth for the game's design.** All conceptual decisions live here. No implementation details — those belong in architecture and stage docs that reference this file. If something in another doc conflicts with this file, this file wins.
>
> **MODIFICATION RULE: This document is append-only unless Westley explicitly approves a deletion.** AI sessions may add new sections, expand existing sections, and resolve open questions by writing answers into the appropriate section. AI sessions may NOT delete, overwrite, or replace existing decided content. If new information conflicts with existing content, flag the conflict for Westley to resolve — do not silently overwrite. This rule exists because multiple AI sessions contribute to this document, and silent deletions have already caused loss of decided design work.
>
> **OPEN QUESTION GOVERNANCE:** The "Open Design Questions" section at the end of this document is a staging area, not a permanent home. When an open question is resolved through brainstorming, the answer must be written into its natural section in the bible, and the question must be removed from the open list. If you are an AI session reading this document and you notice decided design content that still appears as an open question (or vice versa — an unresolved question living only inline with no entry in the open questions section), flag it for Westley.
>
> **Last updated:** March 30, 2026 (v1.11) — Stage 3 design decisions continued: attack damage formulas specified (scaled proportional to net_force across all three outcome bands — breakthrough, contested, repelled — with diminishing returns as a noted tuning fallback); border friction formula specified (scales with hostile neighbor military strength, not flat constant); budget accumulation formula specified (economy minus per-region maintenance cost, creating expansion risk/reward where conquered territory is a net drain until it recovers); agent decision selection model added (scored decision with archetype weights replacing fixed priority order, normalization to common scale, per-tick decision logging for tuning); "Why factions expand" updated to reflect maintenance cost dynamics. Previous: (v1.10) Added two future consideration subsections to Expansion Packs and Monetization: Unit Skins and Multiplayer. Previous: (v1.09) Stage 3 design decisions added.

---

## Table of Contents

1. [Vision and Identity](#vision-and-identity) — What the game is, what it feels like, what it's not
2. [The Simulation Backbone](#the-simulation-backbone) — SD model, event chains, region state, tick loop, composite axes
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
13. [AI Integration Pillar](#ai-integration-pillar) — Library pipeline, dynamic naming, unit tuning, chronicle generation, 3D asset pipeline
14. [Transition from Previous Iteration](#transition-from-previous-iteration) — What survives, what's cut, what changes
15. [Open Design Questions](#open-design-questions) — Unresolved design decisions awaiting brainstorming
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
- Generates emergent narrative through a coherence ledger that tracks named characters, faction arcs, and cause-and-effect threads
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

1. **Process the pending event queue** — check if any scheduled events are due this tick. For each, roll against its firing probability. Events that fire resolve immediately: state changes applied, coherence ledger updated, new chain spawns added to queue.
2. **Evaluate fresh event triggers** — for each region, check current field values against the event threshold table (with per-region noise offsets). Any threshold crossed triggers a new event chain. This is how new chains start.
3. **Run all faction agents** — each faction evaluates the current post-event state and makes its decision for this tick: accumulate budget, launch an attack, colonize, or reinforce a defensive position. **Attack events resolve immediately within step 3** — the attack resolution formula runs inline, field damage is applied to the target region, and if the defender's military drops below the conquest threshold, a Conquest event is inserted into the pending event queue for processing on the next tick. Conquest follow-up chains (resistance movements, refugee flows, morale effects) propagate through the event chain system's existing chain spawn infrastructure. Defensive reinforcements apply field changes to the target region directly. Faction agents act after events so they can exploit emerging crises — an agent sees the post-event state of regions (including damage from events that fired in steps 1–2), making attack timing strategically meaningful. The player's civilization runs the same agent framework as all other factions, with a conservative defensive posture.
4. **Apply border friction** — for each region bordering a hostile faction, apply minor per-tick tension and economic drag. This is the background stress of contested borders, not active military engagement.
5. **Apply passive drift** — the per-tick SD flow calculations for each field in each region. The slow background changes.
6. **Recompute composite axes** — recalculate stability and capacity for each region from the updated granular fields.
7. **Log everything** — write the tick's events, state changes, faction agent actions, and border friction to the coherence ledger with causal chain links preserved.

### Multi-Faction Agent Decision Model

The world is a **free-for-all between multiple factions**. The player's civilization is one faction among several. External antagonist archetypes, breakaway factions from revolts, and the player's civilization all operate as faction entities within the same simulation framework. Every faction runs the same agent model — the system is symmetric and multiplayer-extensible.

**Faction entity model.** Each faction has: an ID, an archetype (or "player_civilization"), owned regions (tracked via faction_id on each region), a resource budget, a budget growth rate, faction-level modifiers (e.g., a militaristic faction's regions get a military drift bonus, a trade-focused faction's regions get an economy drift bonus), a diplomatic stance toward other factions, and an **attack confidence threshold** rolled at world generation from an archetype-specific range. Faction-level modifiers influence region-level behavior — they are applied as small bonuses to the relevant drift terms in owned regions.

**Aggression variance — per-game faction personality.** Each faction's attack confidence threshold is rolled once at creation from a configured range per archetype (e.g., Conqueror: 12–18, player civilization: 40–60, breakaway: 8–14). The rolled value persists for the entire game and determines how cautiously or aggressively the faction fights. A low confidence threshold produces an aggressive faction that attacks with slim margins — more frequent attacks, more contested outcomes, grinding border wars. A high threshold produces a cautious faction that waits for overwhelming advantage — fewer but devastating attacks, more breakthroughs. This creates genuine stochastic divergence across playthroughs: the same archetype produces different war stories depending on its personality roll. The variance is rolled per faction, not per tick — it's the faction's strategic identity for this game.

**Budget accumulation.** Each faction's budget grows per tick based on the net economic contribution of its owned regions minus a per-region maintenance cost:

```
budget_growth = sum(region.economy - region_maintenance_cost for region in owned_regions) * archetype_growth_rate
```

The `region_maintenance_cost` is a flat per-region config value representing the administrative and logistical overhead of holding territory (garrison supply, governance, infrastructure upkeep). Each region must produce enough economy to cover its maintenance cost before it contributes to the faction's strategic budget. Regions that don't cover their cost are **net drains** — they actively reduce the faction's budget each tick.

This creates the core expansion risk/reward dynamic: a healthy home region (economy 60+) is a strong budget contributor. An established frontier (economy 30–40) is a modest contributor. A fresh colony (economy 8) is roughly breakeven or a slight drain. A conquered husk (economy 0–5) is a pure liability that bleeds the faction until it recovers. A faction that conquers five devastated regions watches its budget shrink tick by tick as maintenance on rubble outpaces income from its core — the natural overextension penalty. Expansion is an investment that must "come online" before it pays for itself, and if the faction loses the territory before that happens, it has wasted budget AND weakened itself.

The `region_maintenance_cost` starting point should be tuned so that fresh colonies are roughly breakeven (suggesting a value around 8–10, matching colony starting economy of 8). The `archetype_growth_rate` is a per-archetype multiplier that controls overall budget velocity — the Conqueror may grow budget slightly faster than the player's civilization, reflecting a war-economy focus. Both values are tuned during Stage 3.

**Faction agent decisions.** Each tick, every faction's agent evaluates its situation and makes one of four decisions:

- **Accumulate** — no viable attack or colonization target passes the expected outcome check (see below). Save the budget. The faction's borders are quiet this tick (minor border friction only, no military action). This is the most common decision — factions spend most ticks building up, not fighting.
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
- **The Plague** — scores by high population combined with trade connectivity (trade route edges). Fertile ground for spread.
- **The Exhaustion** — scores by high economic output. Thriving systems to degrade.
- **The Schism** — scores by high factional tension. Already-fractured regions are susceptible to ideological capture.
- **The Phenomenon** and **The Singularity** — these archetypes may not use the standard attack model. Their threats manifest differently (see "The Antagonist System" section). Their agent behavior is designed when those archetypes are implemented.

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

**Colonization as an agent decision.** Colonization uses the same attractiveness scoring pipeline as attacks. Uninhabited regions adjacent to a faction's territory enter the candidate pool alongside enemy-owned regions. Each archetype's scoring function evaluates them through its own lens — the Conqueror sees an undefended gateway, the Plague sees an empty region adjacent to a populated trade hub. If an uninhabited region scores highest in the candidate pool, the agent colonizes it instead of attacking an enemy. If enemy targets consistently score higher, the faction fights instead of expanding. The scoring handles prioritization naturally without special-case logic.

**Colonization cost.** The agent spends a portion of its budget on colonization (config value: `colonization_cost`). This is typically cheaper than an attack (no resistance to overcome), which creates a natural tempo incentive — early in the game when factions are building up, cheap expansion into empty space is often the best use of limited budget. As the map fills up and empty regions become scarce, the budget increasingly goes toward military action. The colonization cost is deducted from the faction's budget the same way attack strength is committed.

**Starter field values.** A newly colonized region is initialized with flat config values representing a bare frontier outpost: `colony_start_military` (starting point: 5), `colony_start_economy` (starting point: 8), `colony_start_tension` (starting point: 0), `colony_start_population` (starting point: 10). All factions' colonies start identically — differentiation comes from what happens after colonization. The territorial adjacency bonus accelerates economic growth based on neighbor strength (a colony next to a booming core develops faster than one next to another weak frontier), the economic and tension oscillation cycles create dynamic vulnerability windows, and the existing passive drift formulas naturally grow the colony's fields over time. The colony is a long-term investment: it takes many ticks of drift before it contributes meaningfully to the faction's budget, but even modest economy contributes to budget growth and the territorial adjacency bonus rewards contiguous expansion. The existing defender's advantage systems (military resistance mechanic in attack resolution, recruitment drift rebuilding garrisons over time, tension mechanics braking runaway prosperity) handle the snowball concern — rapid expansion produces low-field regions that are expensive to defend and slow to develop.

**Contested uninhabited regions.** Two factions can target the same uninhabited region on the same tick. Since faction agents run sequentially in the tick resolution sequence (step 3), the first faction to act claims the region. The second faction's colonization attempt finds the region already claimed and the action fails — the committed budget is refunded (no cost for a failed colonization, unlike a failed attack which costs the committed budget). The tick processing order of faction agents is randomized each tick to prevent a fixed advantage.

**Why factions expand.** Uninhabited regions provide three forms of value once claimed: (1) **Strategic buffer** — an owned region between a faction and its enemies that must be conquered before reaching the core, even at low military. (2) **Long-term budget investment** — a fresh colony starts at roughly breakeven against maintenance cost, but the territorial adjacency bonus and passive drift grow its economy over time until it becomes a net contributor. Expansion is an investment that takes many ticks to pay off, not an immediate payoff — the faction must be able to absorb the short-term maintenance cost while the colony develops. (3) **Territorial adjacency bonus** — the economy drift adjacency bonus (see "Economic Output drift" above) means claiming a region between two existing territories connects them economically, boosting both. This creates a concrete incentive for contiguous territorial expansion and accelerates colony development near strong existing regions.

### Diplomatic Stance

Each faction maintains a diplomatic stance toward every other faction. Stances are a simple enum: **hostile**, **neutral**, or **allied**. Each archetype defines a default starting stance toward the player's civilization and toward other archetypes. The Conqueror starts hostile toward everyone. Breakaway factions from revolts start hostile toward their parent faction. The player's civilization's stance toward others mirrors their stance toward it (if they're hostile to you, you're hostile to them).

Stances are mutable through events. A diplomatic event chain could shift a neutral faction to hostile (or allied). A successful negotiation mission could shift a hostile breakaway to neutral. Stance changes are event effects, applied the same way as field changes — authored per event template in the library.

Mechanical effects of stance:
- **Hostile** — border friction applies, faction agents include each other's regions in attack candidate pools, the faction's territory is treated as enemy territory for all simulation calculations.
- **Neutral** — no border friction, no attacks, no economic bonuses. Factions coexist without interaction. Neutral factions' regions are excluded from attack candidate pools.
- **Allied** — no border friction, no attacks. Allied factions' adjacent regions contribute to the territorial adjacency bonus as if owned by the same faction (representing trade cooperation and mutual support). Allied factions may coordinate defensive reinforcement (future consideration, not for initial implementation).

**The player's civilization agent.** The player's civilization runs the same agent framework as all other factions. During time jumps (when the player isn't present), it defaults to a **conservative defensive posture** — it prioritizes reinforcing threatened borders over launching attacks. If it has overwhelming military advantage at a border, it may launch attacks, but this is weighted low. The player's missions are how the civilization takes offensive action — the autonomous agent handles defense between chapters. The player may disagree with autonomous decisions ("why did my civilization abandon the Periphery?"), but the bible's core principle applies: the civilization has its own plans, and the world does not revolve around the player.

**[Future consideration, not for Stage 0:]** Random hyper-focus — occasionally a faction agent dumps disproportionate budget into a single attack regardless of normal scoring, creating unpredictable offensive surges.

**Agent information model.** All faction agents have perfect information about the military strength, economic output, and population of adjacent regions, regardless of faction ownership. This represents civilizational-level strategic intelligence — neighboring powers know roughly how strong each other are across decades and centuries. Agents do NOT have visibility into other factions' budget levels or internal decision-making, only the observable state of regions on the world graph. Fog of war is a **player-facing presentation layer** that affects tactical missions, not simulation-level agent behavior. During missions, the player's sensor coverage, layer visibility, and intelligence quality are constrained by mission parameters and assets. During time jumps, the simulation's agents operate with full neighbor visibility to produce coherent strategic behavior — a civilization that fails to defend an obvious threat fails because of political dysfunction or resource constraints (modeled through the reinforce variance mechanic), not because it literally couldn't see the army on its border.

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
5. **Time jump** — the simulation fast-forwards through a random duration between a configurable min and max (targeting 30–150 years). The duration is a simple random roll, decoupled from mission urgency or world state — the simulation's existing drama-generation systems (passive drift, event chains, faction agent actions) produce interesting events over any duration naturally. The player has no agency over the gap length. The player experiences the jump as a **chronicle scroll** — a text-based vertical timeline of 5–10 entries summarizing what happened between chapters. Three kinds of entries, presented in order: **consequence entries** (direct results of the player's last mission, shown first so the player sees their impact), **world entries** (things that happened on their own — faction shifts, tech changes, inter-faction conflicts), and **setup entries** (the last one or two entries teeing up the new chapter). The player can click any entry to expand it slightly for extra detail. No voice acting, no cutscenes — just good prose, clean typography, and the weight of time.
6. **New chapter** — the player returns as a character selected by the simulation. **Lineage persistence:** the simulation keeps the player within the same bloodline for 2–4 chapters before rotating to a different family. Within a lineage run, each chapter is a descendant — the player sees the family name return and watches consequences compound across a career arc. The simulation rotates to a new lineage when: the coherence ledger determines the current family's narrative arc has played out, the bloodline has died out, or the world's pressure points have shifted to a region where a different lineage is more narratively charged. When the lineage rotates, the new character is selected from the weighted pool: most commonly a **descendant of a previous commander from a different lineage** the player has already played. Less commonly a **descendant of a previous commander's rival or nemesis** (instant dramatic tension). Rarely, an **unrelated person elevated by circumstance** (signals the world has changed dramatically). The 2–4 chapter range is a soft target — the simulation aims for it, not enforces it rigidly. If a bloodline dies out after one mission, that is a meaningful moment, not a bug. The civilization assigns a new mission based on the current state of the world.

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

**Step 3: Lineage member generation during time jumps.** During each time jump, the coherence ledger generates a simple family tree update for the current lineage (and all tracked previous lineages). The update is minimal: N descendants produced (based on time jump length and a fertility config value), distributed across regions based on where the family currently lives. Each descendant gets a name (from the naming system), a region, and an age. No personality traits, no career simulation, no detailed life events. The chronicle distiller and template system add narrative richness in prose — the ledger just tracks who exists and where. This keeps the ledger lean while giving the character selector and distiller enough data to work with.

### Onboarding and First Chapter

**Single onboarding screen.** Before chapter 1, the player makes two permanent choices on one screen: **difficulty setting** (Easy/Medium/Hard) and **mission preference weights** (across the five categories, with one markable as "rare"). Both are permanent for the entire generational arc. The same onboarding screen fires at the start of each new cycle after Exodus or Extinction — the player can make different choices for the new civilization.

**Opening time jump.** After the player confirms their choices, the game generates the starting world and immediately runs a short time jump (configurable, targeting 20–50 years) to let the simulation produce initial history. The player sees an abbreviated opening chronicle scroll — 3–5 entries, all world entries (no consequence entries since there's no previous mission). This serves as the player's introduction to both the world and the chronicle scroll format. The mission generator then runs normally against the post-jump state, and the character selector draws from the "unrelated person" pool since no previous lineages exist. Subsequent cycles after Exodus or Extinction use the same opening time jump — in post-Extinction cycles, the chronicle scroll includes ruin references and the world contains remnants of the previous civilization.

### What Carries Over

- **The world remembers everything.** The simulation state carries forward completely. Every mission outcome, every faction shift, every tech advance or cultural collapse persists.
- **The player starts mechanically fresh each chapter.** New character, new forces, new mission. No persistent "player level" or unlocks.
- **But the civilization evolves.** As the simulation progresses, technology advances (or regresses). The tools available to the player in later chapters may be significantly different from early chapters — better units, new asset types, or conversely, degraded capabilities if the civilization is declining.
- **The Ouroboros.** The game can cycle. If the civilization reaches Extinction with Amnesia, it restarts — and the player's next character exists in a world that contains the ruins of everything that came before. The Memory Burden mechanic: the player remembers what their new character does not.

### Terminal Conditions and the Cycle

The game is designed to run indefinitely through cycles of early, mid, and late eras. Terminal conditions are not endpoints — they are **transitions** that reset the civilization into a new cycle while preserving the player's memory and the world's history.

- **Exodus** — the civilization escapes to a new region of the world (or a new world entirely). The simulation resets to an early-era state: small foothold, limited technology, dark unexplored space. But the chronicle carries forward, the coherence ledger remembers, and the player's new commander may inherit fragments of the old civilization's knowledge. A new early era begins.
- **Extinction with Amnesia** — the civilization dies. Cold restart with relics. A new civilization emerges in the same world, surrounded by the ruins of everything that came before. The simulation resets to early-era state. The Memory Burden mechanic: the player remembers what their new character does not. The relics of the old civilization are physically present but unlabeled — waypoints exist, but inspect panels read "Unknown."
- **The Unbroken Line** — the civilization endures through the late era without collapsing. Eventually the simulation's internal pressures (external faction escalation, internal fractures, resource exhaustion, technological complexity) force a transition — either an Exodus, a collapse into Extinction, or a **civilizational contraction** where the civilization voluntarily or involuntarily retreats to a smaller footprint, effectively resetting to a mid or early era state with the scars of what came before.

The game loops through early → mid → late → transition → early. Each cycle feels different because the world remembers: ruins from previous cycles, chronicle entries spanning centuries, lineages that connect across resets. The player experiences the Ouroboros — civilizations rising, falling, and rising again, with the player as the thread of continuity across the cycles.

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

The player does not manage production queues or build individual units. The civilization builds things based on its own state — prosperous regions with high tech produce more, unstable regions produce less. The player sets **broad priorities** that influence what the civilization provides: more military capacity vs. more science vs. more trade. These are a few meaningful choices, not a spreadsheet. The tradeoff is real (military priority means fewer trade units means less economic resilience) but the interface is minimal.

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

- **Stats** — speed, firepower, durability, range, sensor radius. The baseline.
- **Traits** — passive characteristics. A unit might have "hardened hull" (extra resistance to Strike damage) or "long-range sensors" (sees further). One or two per class.
- **Abilities** — active things the player can trigger. A Siege unit might have a "barrage" ability for area damage. A Strike squad might have "afterburner" for a speed burst. These are the mastery layer — a new player can ignore them and still play, a skilled player uses them to create decisive moments.

### Roles Within Categories

Within each RPS category, units fill different **roles** that create positioning decisions:

- **Frontliner** — absorbs damage, holds the line
- **Skirmisher** — harasses flanks, disrupts formations
- **Artillery** — long range damage, needs protection
- **Support** — repairs, buffs, disrupts enemies

A "Strike skirmisher" plays very differently from a "Strike frontliner" even though they're in the same broad category.

### AI-Generated Unit Variety

The engine owns the mechanics — unit classes, abilities, and roles are hand-designed and consistent. **AI tunes the numbers based on civilization traits.** A militaristic civilization's units skew toward higher firepower. An expansionist civilization gets faster, lighter units. A civilization in technological decline has units with degraded stats but maybe improvised traits.

The framework is:
- Base classes and roles are fixed (always a Strike skirmisher, always a Siege artillery)
- Stats within each class have defined ranges
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

### 2.5D Vertical Layers

Combat uses **3–5 vertical layers** rather than a flat 2D plane or full 3D movement. Units exist on a layer and can transition between layers.

- **Layer visibility is tied to sensor coverage.** Sometimes you can see all layers (good intel mission). Sometimes you're partially blind (fog of war on layers above/below your sensor range). This creates tactical uncertainty — an enemy force lurking two layers away is invisible until they strike.
- **Layer positioning matters tactically.** High-layer advantage, ambush from below, units that can't fire across layers, abilities that affect specific layers. This adds a spatial dimension without the full complexity of 3D control.
- **Layer awareness can vary by mission.** Some missions give full sensor coverage across all layers. Others restrict it. This is one way the game creates unpredictability — your intel quality depends on what assets and infrastructure exist in the area.

### Moving Battlefields

Engagements are **not static arenas.** The tactical space shifts during combat:

- Battles can happen while forces are in transit
- Convoy escort missions mean the entire engagement zone is moving
- Gravitational effects near planets or stars can pull the battlespace in a direction
- Environmental features drift through the combat zone

This means positioning is never "solved" — the player must continuously adapt to a changing spatial situation. This creates the World of Combat units feeling where your angle and position relative to a shifting environment is always your most important decision.

### Engagement Scale and Duration

- **Engagement scale** — the player is in the battle. Units are on screen. The player is positioning individual groups and squads.
- **Variable duration** — some engagements are quick skirmishes (a few minutes), others are prolonged campaigns within a single mission. Duration depends on mission type and what the player encounters.

### Tactical Variety

What makes one battle feel different from another (mixed depending on mission):

- **Environmental** — asteroids, gravity wells, nebulae that block sensors, radiation zones
- **Dynamic objectives** — a station to capture, a gate to defend, a convoy to intercept
- **Enemy reinforcements** — new contacts arriving mid-battle, changing the balance
- **Layer uncertainty** — varying sensor coverage means different engagements have different information landscapes

---

## The Antagonist System

### External Antagonists

Six base antagonist archetypes, with more generated by the library builder post-launch:

- **The Conqueror** — a conquering force with its own forces. Military threat. The player fights them directly.
- **The Exhaustion** — ecological and resource collapse. No enemy forces — the threat manifests as cascading system failures, supply shortages, regions going dark. The player's engineers and logistics race to contain it.
- **The Phenomenon** — an unknowable event. No explanation ever given. Effects only. Scouts report fragments that don't fully make sense. Intentionally unsettling.
- **The Singularity** — a technological event the civilization created and cannot control. Knowledge stays high but the knowledge is no longer human.
- **The Plague** — a biological or memetic contagion that spreads between regions through trade routes and population movement. Quarantine and triage. The player must decide what to seal off and what to sacrifice. Regions that are saved may resent the ones that were abandoned.
- **The Schism** — an ideological fracture within the civilization itself. Not a revolt (those are internal antagonists — see below) but a fundamental philosophical split that creates two competing visions for the civilization's future. Both sides believe they are right. The player is caught in the middle, and missions may require choosing a side — or trying to hold both together.

### Internal Antagonists

Not every threat comes from outside. The simulation generates **internal antagonists** from faction dynamics and regional stress:

- **Successful revolts** can splinter a region away from its faction. When a revolt event fires and succeeds, the revolting population rolls a **success rate** (randomly between ~10–70%, config range). The breakaway faction "steals" that percentage of the region's current military and economy — representing soldiers who defected and resources seized. The region's military and economy drop by the stolen amount, and a new breakaway faction entity is created owning that region, starting with the stolen field values. The breakaway faction then operates as its own faction with its own agent — it can be attacked, it can attack, it can be allied with or absorbed. Breakaway factions persist across chapters and evolve through the simulation.
- **Faction extremism** — a faction that was once a healthy part of the civilization's political ecosystem radicalizes under pressure. They pursue their own agenda, which may conflict with the player's missions.
- **Military coups** — if the civilization is unstable enough, a military leader (potentially a named character from the coherence ledger) seizes control of a region or system. The player may be sent to resolve this — or may *be* the descendant of the coup leader.

**Player-initiated revolts:** Occasionally, the mission briefing or the tactical situation presents the player with the option to support or trigger a revolt. This is not a menu choice — it emerges from mission context. If the player is sent to stabilize a region ruled by a corrupt or incompetent faction, they may have the option to overthrow it instead of propping it up. The consequences feed back into the simulation: the new faction may be better or worse, and the civilization's trust in the player's lineage may shift.

### Spatial Manifestation

Each archetype creates a fundamentally different game because the tools the player needs are different. The Conqueror requires military strategy. The Exhaustion requires logistics and triage. The Phenomenon requires exploration and adaptation. The Singularity requires figuring out what's even happening. The Plague requires sacrifice and containment. The Schism requires politics navigated through military reality.

Faction threats act through the simulation. Their effects are spatial — they happen in specific places. The player encounters them during missions.

### Threat Progression

The external threat builds over the course of the generational arc. Early chapters might have no direct hostile faction contact. Mid-game chapters increasingly involve external threats. Late-game chapters may be desperate last stands or evacuation missions.

Multiple antagonists can be active simultaneously, and **factions fight each other, not just the player's civilization.** The Conqueror might be conquering breakaway factions while the player deals with the Plague. Two external threats might clash over the same region. The world is a free-for-all where the player's civilization is one participant, not the center.

**Territorial factions** (the Conqueror, the Schism, breakaway factions) can be pushed back, defeated, or eliminated — they own regions and can lose them. A Conqueror that loses all its territory ceases to be an active threat. However, the simulation's long-term pressures (new external threats emerging, internal fractures, resource exhaustion) ensure that eliminating one threat doesn't guarantee safety — something else will rise to fill the vacuum.

**Systemic threats** (the Exhaustion, the Plague, the Phenomenon, the Singularity) cannot be eliminated through military force — they are environmental or civilizational-scale problems that manifest as event chains and field effects rather than as territorial factions. They can be contained, mitigated, or outlasted, but not conquered. This is core to the elegiac tone — some threats are bigger than any army.

Internal antagonists (breakaway factions, coups, extremist movements) can be resolved, absorbed, or turned into allies. This is core to the late-game feel: the civilization is fighting itself while also contending with external forces it may not be able to beat.

---

## The Chronicle

The chronicle is the player's window into the civilization's history. It serves two functions:

1. **During time jumps** — the narrative montage. The chronicle scroll is the player's window into what happened between chapters: consequence entries showing the impact of their last mission, world entries showing the world evolving, and setup entries bridging into the new chapter. Click-to-expand provides extra detail for the curious.
2. **Across generations** — the long memory. The chronicle is the record the player reads to understand how they got here. A new commander's briefing draws from it. The coherence ledger ensures entries connect through named characters, faction arcs, and cause-and-effect threads.

The chronicle is generated by the AI library builder pipeline. Chronicle entries read like fragments of a real history. The emergent narrative system (coherence ledger, named characters, faction arcs) drives the content.

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

Template extensions for additional archetypes (the Plague, the Schism, etc.) are designed when those archetypes are implemented. The template format supports any number of starting factions — each defined by archetype, starting region count, position in the graph, and field value ranges.

### Inter-Region Topology — Typed Adjacency Graph

Regions are nodes in a graph. Edges represent connections between regions and carry a **type tag** that determines what propagates through them:

- **Border** — military adjacency. Antagonist pressure spreads through border edges. Military reinforcement and garrison support propagate through borders. A region with no border connection to the civilization's core is militarily isolated.
- **Trade route** — economic connection. Trade, supply, and economic interdependence propagate through trade route edges. A region connected only by trade route receives economic benefits but no military support.
- **Both** — full connection. Military and economic effects both propagate.

This separation creates strategic situations where military and economic geography don't perfectly overlap. A frontier region might be economically connected to the core via trade but militarily exposed because no border edge exists. Cutting a trade route (through blockade, hostile faction action, or regional collapse) has different consequences than losing a border (through conquest or territorial withdrawal).

Effects that reference "nearby" or "adjacent" regions specify which edge types they care about. Passive drift modifiers, faction attack propagation, event chain propagation, and the character selector's "nearby region" checks all specify edge type in their queries.

The graph is defined at world generation (part of the starting template) and grows as expansion events add new regions and edges. New edges can also form during simulation (a trade route opens between previously disconnected regions) or break (a trade route collapses due to regional instability).

**Implementation approach (Stage 0):** Start with plain untyped adjacency — all edges are "both." Get passive drift, event propagation, and faction interactions working through simple adjacency. Then add edge types as a second step and verify that separating military and economic connections produces meaningfully different simulation behavior. If the distinction doesn't matter in practice, simplify back to untyped.

### World Evolution Across Eras

The world feels different at different points in the civilization's history. This isn't triggered by flags — it emerges naturally from simulation state. A civilization that has expanded to 5+ systems with deep factional divergence and active hostile factions produces fundamentally different pressure points than a 1-system frontier civilization.

**Early era (roughly chapters 1–3):** The civilization occupies 1–2 systems. Most of the world is dark. Missions are frontier-flavored — exploration, first settlements, establishing footholds. External threats are absent or a distant signal. Resources are scarce because the civilization is young, not because it's failing. The simulation's event pool is narrow: succession disputes, resource conflicts, expansion opportunities. Simple problems, limited tools. The player feels like a pioneer.

**Mid era (roughly chapters 4–7):** Hundreds of years have passed. The civilization has expanded to 3–5 systems. Trade routes exist, factions have formed with competing interests. External threats are becoming visible — first encounters, early pressure on frontier regions. The simulation introduces emergent complexity at scale: inter-system rivalries, cultural divergence between distant colonies, supply chain dependencies that create vulnerability. The player feels like a commander in a real military with real politics.

**Late era (roughly chapters 8+):** The civilization spans most of the inhabitable world. It's powerful but stretched thin. External threats are active, known forces with their own territory and armies. Internal fractures are deep — factions that were aligned in the mid-era now have competing survival strategies. Internal antagonists (breakaway factions, coups, extremist movements) compound the external threat. New simulation behaviors emerge from scale: cascade failures (a region collapsing destabilizes adjacent regions through supply and morale dependencies), resource competition between systems, and the constraint compression described in the mission difficulty design. The player feels the weight of an old civilization trying not to fall apart.

**Technology loss:** In the late era, a declining civilization may begin **forgetting how its own technology works.** If technological complexity is high but the civilization's stability and knowledge infrastructure are degrading, the simulation can trigger technology loss events — a production facility loses the ability to produce a class of unit, a weapons system becomes unreliable, a navigation method is no longer understood. This affects gameplay directly: the player may receive a force with degraded or unpredictable capabilities, or may lose access to asset types that were available in previous chapters. Technology loss is not guaranteed — a thriving late-era civilization retains its capabilities. But a civilization that is simultaneously advanced and collapsing produces the haunting scenario of people surrounded by machines they can no longer maintain.

These era descriptions are approximate guidelines, not scripted phases. The simulation drives the pace — a player who fails catastrophically in the early era might see mid-era complexity arrive sooner as the civilization scrambles to recover. A player who succeeds brilliantly might enjoy a longer early era of stable expansion.

### Civilizational Lifecycle — Mechanical Drivers

The world evolution described above is not scripted — it emerges from the interaction of existing simulation mechanics. This section maps the full lifecycle to the specific mechanical drivers that produce each phase, so that each phase can be verified as emergent behavior during testing.

**Phase 1 — Expansion (early era).** Factions start with few regions and low budgets. Empty regions adjacent to faction territory are cheap to colonize (no resistance) and score well in attractiveness evaluations (maximum weakness, strategic position value from what they border). Budget is too low for confident attacks against defended regions. Result: factions expand into empty space rather than fighting each other. The world fills up. Colonized regions start with minimal field values and grow slowly through passive drift. The territorial adjacency bonus accelerates development for colonies near strong core regions, creating natural economic gradients — rich core, developing middle, bare frontier.

**Phase 2 — Consolidation (mid era).** Empty regions become scarce. Faction budgets have grown from accumulated economic output across multiple regions. Colonization opportunities dry up, so the agent's candidate pool increasingly contains only enemy-owned targets. Factions that expanded aggressively have more territory but weaker per-region fields (colonies haven't matured). Factions that expanded cautiously have fewer but stronger regions. Border friction applies where factions share borders, slowly elevating tension and dragging economy in contested frontier regions.

**Phase 3 — Conflict (mid-to-late era).** Budgets are now large enough to pass the attack confidence threshold against degraded frontier regions. First inter-faction attacks begin. The attack resolution formula favors attackers against weak frontiers. Conquered regions suffer tension spikes, economy disruption, and population loss. The conquering faction gains territory but also gains a high-tension, low-economy region that drains reinforcement budget to hold. Successful conquest attracts further aggression — neighboring factions see the newly conquered region's low military as an attractive target.

**Phase 4 — Overextension (late era).** A faction that has conquered multiple regions faces compounding costs. Each conquered region has high tension, low economy, and low military. The faction must choose between reinforcing these regions (spreading budget thin) or accumulating for the next attack (leaving conquered territory vulnerable). Reinforcement has diminishing returns approaching the frontier tier capacity ceiling, so even heavy spending can't make a conquered frontier as strong as the attacker's home region. Meanwhile, budget growth depends on total economic output across all owned regions — conquered regions sitting at the economy floor contribute almost nothing. The faction's effective budget growth per region *decreases* as it conquers more damaged territory.

**Phase 5 — Fragmentation (late era).** Conquered regions with sustained high tension cross revolt event thresholds. Successful revolts spawn breakaway factions that seize a fraction of the region's military and economy. The parent faction loses territory and the breakaway becomes a new hostile neighbor, adding border friction to adjacent regions. This can cascade: a revolt in one region elevates tension in neighboring regions (through border friction from the now-hostile breakaway), pushing them closer to their own revolt thresholds. A faction that overextended may lose multiple regions in rapid succession, fragmenting into several smaller factions. The breakaway factions then operate as independent agents — they may fight each other, fight the parent faction, or be reconquered.

**Phase 6 — Equilibrium or collapse.** The simulation naturally tends toward one of several late-game states depending on the stochastic path: a dominant faction that managed overextension successfully (possible but requires favorable conditions), a fractured world of many small factions in shifting conflict, or a grinding multi-front war where no faction can achieve decisive advantage. The proportional tension decay mechanic prevents permanent runaway spirals — even high-tension regions eventually stabilize if external pressure stops. This means the world can reach dynamic equilibria where factions hold stable borders, punctuated by periodic wars when budget accumulation crosses attack thresholds again.

**Why this matters for the player.** The player's civilization experiences these phases from the inside. In the expansion phase, missions are about establishing footholds. In the consolidation phase, missions involve border disputes and political maneuvering. In the conflict phase, the player commands forces in real wars with real stakes. In the overextension phase, the player is sent to hold crumbling frontiers or quell revolts in conquered territory. In the fragmentation phase, the player may be fighting former allies, choosing which fragments of their civilization to save, or leading a desperate defense of the last intact core region. The lifecycle is the game's dramatic arc — and because it emerges from mechanics rather than scripts, it plays out differently every time.

**Tuning the lifecycle.** The lifecycle's *shape* is emergent from the mechanics already designed. The *pacing* is tunable through existing parameters: conquest consequences control how costly expansion is, border friction rates control how fast contested borders degrade, revolt thresholds control when overextension triggers fragmentation, and reinforcement efficiency controls how effectively factions can hold distant territory. If testing shows a faction can conquer everything without fragmenting, increase the costs of holding territory. If fragmentation happens too fast, reduce them.

### Spatial Navigation

The player operates within the world spatially. During missions, you're in a system or a region, moving your forces. Between missions, the world map shows the broader picture.

The frontend is being rebuilt from scratch. No visual work from the previous iteration carries forward — ideas from it may inform future design, but the new game's visual layer will be purpose-built for the commander experience. The exact navigation model will depend on how the mission tactical layer works — to be designed.

### Map Generation System — Spine + Gradient Hybrid

> **INCOMPLETE DESIGN.** The core concept is decided. Implementation details, specific vocabularies, and several interaction questions remain open — see "Open Design Questions" section.

Mission maps are procedurally generated using a **spine + gradient hybrid** system. The generator produces a small data seed. The engine interprets that seed into a full traversable 3D space. Small data in, big interpretation out.

**The Spine** is a graph of waypoints that defines the map's strategic topology — where the objectives are, where the chokepoints are, how different areas connect, where the player starts, where enemies come from. A typical mission spine is 10–30 nodes with edges between them. Each node has a position, a type tag, and a few property values. Each edge has a connection type. The spine guarantees that the map has deliberate tactical structure — flanking routes exist because the generator placed them, not by accident.

**The Gradient Fields** fill the space between and around the spine nodes with organic navigational texture. A gradient field is a continuous function over the map space — a set of field sources, each with a position, a property type, radius, intensity, and falloff curve. The engine samples these fields to place geometry, set movement costs, apply environmental effects, and determine sensor interference. Where a gradient says "obstacle density 0.7," the engine places dense obstacles appropriate to the theme. Where it says "hazard intensity 0.4," the engine applies a moderate environmental danger. Gradient fields overlap and combine naturally, producing organic terrain with no grid artifacts and no hard boundaries between zones.

**The division of labor:** The spine handles the decisions a level designer would make — "there should be a chokepoint here and a flanking path there." The gradient fields handle what a terrain artist would do — "this area should feel dense and dangerous, this area should feel open and exposed." Together they produce maps that are both tactically sound and visually organic.

**Why this hybrid:** The spine alone leaves the space between waypoints empty and uninteresting. Gradient fields alone produce organic terrain but can't guarantee specific tactical structures (chokepoints, flanking corridors, defensible positions). The hybrid solves both problems — the spine provides structure, the gradients provide texture.

#### Generator Decides, Engine Interprets

The generator (a per-archetype script, similar to AoE3's per-map-type generation scripts) produces the spine and gradient fields as abstract gameplay data. The engine interprets that data into era-appropriate 3D geometry. Neither the spine nor the gradients contain any era-specific content.

The spine speaks in abstract types — "objective node," "staging area," "boundary," "transit point" — not "space station" or "fortress." The gradient fields speak in gameplay properties — "obstacle density," "hazard intensity," "sensor interference," "resource abundance" — not "asteroids" or "mountains." The theme pack maps abstract types to visual content: "obstacle density 0.8" becomes a dense asteroid field in the sci-fi theme, a mountain pass in a land theme, a reef chain in a naval theme.

This is the same era-agnostic architecture the rest of the game uses. The map system never says "asteroid." It says "dense obstacle region." The theme pack decides what that looks like.

#### Continuous Movement and No Loading Screens

A single chapter may involve the player moving forces across a region or system. The map system supports this without loading screens. The spine and gradient fields define a continuous canvas — the player's forces move freely through rendered 3D space, and the engine streams geometry based on what's near the camera (standard LOD culling). There are no discrete zones to load, no boundaries to cross. The space is one continuous field from the player's perspective.

#### Moving Battlefields

The game specifies that engagements are not static arenas — the tactical space shifts during combat (see "Force and Combat Design — Moving Battlefields"). The spine + gradient system supports this naturally. Spine nodes can drift over time (the objective's position changes, the chokepoint narrows or widens). Gradient sources can move (the hazard zone drifts across the map, the obstacle density shifts as debris scatters). The result is smooth, continuous spatial change — the battlefield evolves under the player's feet without discontinuities.

#### Simulation State as Map Input

The simulation already tracks per-region state as continuous values (military strength, economic output, factional tension, population). These values can feed directly into map generation parameters. A prosperous, stable region produces maps with more resource nodes, more infrastructure (structures, stations, supply points), and lower hazard intensity. A contested, declining region produces maps with debris, damaged structures, and higher hazard density. The map reflects the history of the region the player is operating in.

This is not a required coupling — the map generator can work with archetype scripts alone. Simulation-driven flavoring is an additional layer that enriches the output when it's ready.

#### Data Budget

A complete mission map seed is approximately 350 bytes of data:
- **Spine:** ~15 nodes × ~12 bytes each (position, type, properties) + ~25 edges × ~4 bytes each = ~280 bytes
- **Gradients:** ~10 field sources × ~7 bytes each (position, type, radius, intensity, falloff) = ~70 bytes

The engine turns 350 bytes into an entire traversable 3D space. Seeds are small enough to log for replay and bug reports.

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

Each expansion pack is a complete time period that the player can select at the start of a new game or cycle. The base game ships with the sci-fi theme. Expansion packs add additional eras — each with its own AI-generated library content (naming conventions, chronicle templates, mission briefing prose, unit flavor, visual style).

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
- **Dynamic naming system** — generates names for everything in the game: people, places, units, factions, technologies, relics, systems. Draws from a vast cultural range (historical human naming conventions, Tolkien-esque construction, ancient Greek, Sumerian, invented linguistic roots, and beyond). The system uses a multi-stage pipeline: an AI first generates a diverse set of naming variables (linguistic roots, phoneme patterns, cultural flavor tags, era markers), those variables feed a prompt builder that constructs generation prompts, and a second AI pass produces the actual names. Prompts rotate through variable combinations so the output stays fresh across runs. A deduplication check ensures no cloned names enter the library. The result is a naming library that feels authored across many traditions without repeating itself.
- **Unit stat tuning** — AI generates per-civilization stat profiles for unit classes within hand-designed mechanical constraints.
- **Unit power balancing** — AI-generated units are scored with strength values. The force parity system uses these scores to ensure missions present winnable fights: the player receives forces with comparable total strength to the enemy, adjusted by civilizational capacity and difficulty setting.
- **Mission variable filling** — AI helps generate the specific narrative context for mission briefs within archetype templates.
- **Chronicle generation** — AI-authored templates produce emergent narrative that reads like real history.
- **Chronicle scroll distillation** — AI-generated templates for compressing hundreds of time-jump events into 5–10 scroll entries.
- **Potential future** — AI-generated antagonist archetype variants, civilization personality profiles, faction flavor, additional mission archetypes.

The principle: **AI generates content within mechanical frameworks.** The engine defines the constraints. AI fills in the specifics. The engine can handle any output because the constraints guarantee validity.

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

---

## Transition from Previous Iteration

The game was previously an elegiac god-game where the player observed as "The Unseen Hand" and applied abstract declarations through a particle-based fate space. The redesign changes the player's role to commander, the interaction model to missions, and the game loop to generational chapters. This section captures what survives, what's cut, and what changes.

### New Project

The redesign starts a new project. Code from the old project is selectively copied during Stage 0 (see dev_rules.md), not inherited wholesale. The old repo is preserved as reference.

### Simulation Backend — Survives with Modification

The simulation backbone is the most valuable existing asset. **The simulation redesign is now resolved — see "The Simulation Backbone" section for the full architecture.** The engine uses a System Dynamics model with stochastic event chains, a layered region state model (granular fields + composite axes), and a defined tick resolution sequence. The core *concepts* from the previous iteration (multi-dimensional civilizational state, stochastic event firing, emergent narrative through a coherence ledger) survive in the new architecture. The specific old implementation (3D vector space with Entropy/Continuity/Reach, the old tick resolution model) is replaced by the new SD-based system.

**Likely to survive in some form:** The concept of a multi-dimensional state space for civilizational health. The outcome mapper concept (proximity-based probability). The coherence ledger (thread tracking, named characters, faction arcs — becomes more central as it drives character selection, inheritance missions, and chronicle scroll content). The region model and world state concepts. The library reader and its fallback contract. The template assembler's text generation machinery. Config values as a starting reference.

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

### 1. Simulation Engine — Multi-Faction Design (HIGH PRIORITY — ACTIVE REDESIGN)
*Previously resolved as single-antagonist model. Now being redesigned as multi-faction free-for-all world. Core architecture decisions made: faction entity model with archetype-specific agents, discrete attack events replacing continuous pressure, military recovery through drift recruitment term, military resistance reducing attack damage, conquest events for territory transfer, revolt stolen-strength mechanic for breakaway factions, player's civilization autonomous defensive agent, force parity system for missions. Conqueror attractiveness scoring formula resolved (three-factor: weakness + current value + strategic position). Uninhabited region colonization mechanics resolved (colonization as agent decision variant, contested regions, territorial adjacency bonus). Diplomatic stance system resolved (hostile/neutral/allied enum, mutable through events). World template Conqueror placement resolved (separated by one uninhabited buffer region). Economic and tension oscillation mechanics added to drift formulas. See "The Simulation Backbone" and "The Antagonist System" sections.*

*Stage 0 tuning pass complete (v1.02): recruitment formula updated (logistic ceiling, smooth tension suppression replacing hard cap), tension decay changed from constant to proportional (stable equilibria under friction), economy floor added, reinforcement diminishing returns added (per-tier caps), aggression variance added (per-game confidence roll), breakthrough threshold added to attack resolution, timescale calibrated (5x rate divisor, 2000-tick integration tests). Multi-faction simulation verified across 5 seeds with genuine stochastic divergence in outcomes.*

*Stage 1 complete (v1.07): world graph and multi-region drift proven on isolated start template (1 home, 2 frontier, 4–6 empty regions). Baseline recruitment added to military drift (prevents frontier military freefall). Adjacency bonus tuned to 0.05 (preserves economic gradient). Home population range raised to (70, 85). Oscillation mechanism changed from simple additive to feedback-isolated additive (economy ±6.0/100 ticks, tension ±2.0/125 ticks — cross-field coupling reads de-oscillated values). Long-run behavior verified at 500 ticks with all mechanics enabled. 5-seed variety test passed — divergent outcomes, no degenerate seeds.*

Remaining sub-questions:
- How do non-territorial archetypes (Exhaustion, Plague, Phenomenon, Singularity) manifest in the multi-faction model? They aren't factions with territory — what is their agent behavior?

### 2. Force and Asset Design — Remaining Details (HIGH PRIORITY)
- Specific unit types within the Strike/Line/Siege framework
- Specific abilities and how they're triggered
- How the light economy interface works in practice
- How the civilization's allocation system decides what to give the player

### 3. Combat and Tactical Layer — Remaining Details (HIGH PRIORITY)
- How layer transitions work mechanically (can all units move between layers? Cost/time?)
- How the moving battlefield is communicated visually
- Specific environmental hazard types and effects
- How different mission types feel different mechanically in the tactical layer
- Specific abilities and how they're triggered

### 4. Map Generation System — Remaining Details (MEDIUM PRIORITY)
- What is the vocabulary of spine node types? (objective, staging, transit, boundary — what else?)
- What is the vocabulary of gradient property types? (obstacle_density, hazard_intensity, sensor_interference, resource_abundance — what else?)
- How does the 2.5D layer system interact with the spine + gradient model? Is it one spine per layer, one spine with layer tags on nodes, or gradient fields that vary by layer?
- How do per-archetype generation scripts compose spine + gradient maps? What rules constrain placement to guarantee playable topology (connectivity, no dead ends, minimum path count between objectives)?
- How does fog of war / sensor coverage interact with gradient fields?
- How does the recon phase camera work over this kind of continuous space?
- What determines the canvas size? (Region-spanning chapter = large canvas, tight tactical engagement = small canvas — but what are the actual parameters?)
- How does simulation-driven flavoring layer onto the base archetype scripts? What simulation values map to which gradient properties?

### 5. Dynamic Naming System — Design Details (MEDIUM PRIORITY)
- What are the specific naming variable categories (linguistic roots, phoneme patterns, cultural tags, era markers, or others)?
- How does the prompt rotation system work to ensure variety without repetition?
- How does deduplication work — exact match? Phonetic similarity? Levenshtein distance?
- How large should the pre-generated naming library be per category (people, places, units, etc.)?
- Should names have internal consistency rules per faction or region (e.g., all units from Region X share a linguistic family)?
- How does the naming system interact with the coherence ledger's named character tracking?

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
