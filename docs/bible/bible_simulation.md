# Ouroboros Manifold — Simulation Backbone Reference

> **Extracted from game_bible.md v1.23.** This file is authoritative for simulation
> mechanics. If this file conflicts with game_bible.md, flag it for Westley — do not
> silently resolve the conflict.
>
> **Modification rule:** Same as the master bible — append-only unless Westley approves
> deletion. Resolved open questions get written here AND reflected back to the hub.

---

## In Flux

Emerging design captured here w/ rationale. Promotes into the main body when locked. Cross-refs to other spokes' In Flux entries listed per entry.

### WS3 Fork-B — Sim Dimensions on the Lieutenant Substrate (open, 2026-05-16, secondary spoke)

**REFRAMED 2026-05-16 mid-session.** Original sim-dimensions-first ordering treated *what lieutenants react to* as primary before deciding *how lieutenants think*. Player-experience goal made *lieutenant intelligence* primary. Lieutenant intelligence model now lives at `bible_combat.md ## In Flux` (Fork-A series, primary spoke). This entry holds the downstream sim-dimensions work (Fork-B series, secondary), gated on Fork-A1 + A2 locking.

**Substrate anchor.** Lieutenant System committed in `game_bible.md ## In Flux` (2026-05-16). Fork-B designs *what world state lieutenants perceive and act on*. Pick set is constrained by which decision-points the library indexes against (output of Fork-A2). **Open Fork-B only after Fork-A2 locks.**

**Prior research parked.** Earlier this session: market + implementation research completed for the sim-dimensions question. Synthesis matrix covered intel / morale / legitimacy / cohesion / diplomacy-deepen / ideology / logistics. Recommended package was "Cheap-Wide" (Foundation-core bundle [Legitimacy + Cohesion + Ideology-faction + Diplomacy-deepen] + Logistics-derived + Intel-Lite). Preserved as input to Fork-B1 when reached, not as a current pick.

**Fork-B order (gated on Fork-A2):**
- **B1.** New decision dimensions to add. Placement: faction scalar / per-region field / lieutenant trait / hybrid.
- **B2.** Cross-dimensional coupling direction. One-way / bidirectional / full graph w/ cascading triggers. Closes the "downhill seam."
- **B3.** Decision horizon + memory. Stateless per-tick / short N-tick / persistent multi-gen plans. Cross-refs Fork-A6.
- **B4.** Faction ↔ Lieutenant decision boundary. What `Faction.decide()` decides vs. what the lieutenant decides.
- **B5.** `Faction.decide()` shape. Keep 4 intents / expand to N / goal-plan-action hierarchy.
- **B6.** Fog / intel model. Perfect / imperfect / partial-w/-lieutenant-reporting. Cross-cuts B1.
- **B7.** Player decision surface. See AI reasoning / influence via doctrine + orders / react only. Reshaped by Fork-A picks.
- **B8.** Multi-pronged decision rep. Single intent / weighted mix / parallel plans.
- **B9.** Emergent vs authored cascades. Hand-authored / fully emergent / hybrid.

*Constraint (answer last):*
- **C1.** Per-tick performance budget. Covers Fork-A library lookup cost + Fork-B drift/intent-resolver cost.

**Rewind cross-cut.** Touches B3 + B8 (does AI remember rewound timelines?). Tracked inside those forks.

**Cross-ref.** Fork-A series (lieutenant intelligence model, primary) at `bible_combat.md ## In Flux`.

**Picks land below this entry as forks resolve.** When B-series + C1 lock, promote into main body and archive this entry per playbook.

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

**Population-first region initialization.** At world generation, inhabited regions (home and frontier) use a population-first initialization model. Population is rolled from a per-tier range, then all other fields are derived from population via config ratios (economy ratio, military ratio, tension ratio) with random jitter. This ensures field values are internally consistent — a populous region has proportionally higher economy, military, and tension — while still producing variety across runs. All factions use the same ratios; differentiation comes from archetype behavior after world generation, not from asymmetric starting values.

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
pop_factor = population / 100
tension_suppression = (1 - factional_tension / 100) ^ tension_recruitment_scale
headroom = max(0, (1 - military / recruitment_ceiling))
recruitment = recruitment_baseline
if economic_output > recruitment_threshold:
    recruitment += recruitment_rate * (economic_output / 100) * pop_factor * tension_suppression * headroom
recruitment *= headroom
drift = decay + recruitment
```
Military decays proportionally to how much the economy can't sustain it. High economy = no decay. Zero economy = full decay. Under good conditions (strong economy, low internal tension, healthy population), military slowly recovers through recruitment — representing a civilization rebuilding its forces during peacetime. Recruitment has a **baseline term** that always fires for inhabited regions regardless of economy, representing militia raised from the local population. This prevents frontier regions (which rarely reach the economy threshold) from collapsing to near-zero military through pure decay. The economy-scaled recruitment term adds on top of the baseline when the economy exceeds the recruitment threshold, scaled by population factor (more people = larger recruitment pool). Both terms share the same logistic headroom limiter: the `(1 - military/recruitment_ceiling)` term creates logistic saturation so recruitment slows as military approaches a ceiling. The tension suppression term uses a **configurable exponent** (`tension_recruitment_scale`) rather than linear scaling — a low exponent makes tension suppression weaker than linear, allowing meaningful recruitment even under moderate tension. Drift alone cannot push military past this ceiling — only direct spending (reinforcement actions, Emergency Levy events) can exceed it.

**Economic Output drift:**
```
owned_neighbors = adjacent regions owned by same faction
adjacency_bonus = sum(neighbor.economy / 100 * neighbor_economy_bonus for each owned neighbor)
tension_drag = factional_tension_trend / 100 * tension_penalty_rate    # reads de-oscillated tension
population_factor = population / 100
eco_capacity = eco_pop_ratio * population
overcapacity_decay = eco_overcapacity_rate * max(0, economy - eco_capacity) / 100
oscillation = econ_oscillation_amplitude * sin(2 * pi * tick / econ_oscillation_period + econ_phase_offset)

drift = (base_growth * population_factor) - tension_drag - overcapacity_decay + adjacency_bonus + oscillation
```
Economy has natural growth scaled by population (more people = more production), dragged down by factional tension (internal conflict disrupts output) and **overcapacity decay** (economy that outstrips what the population can sustain decays back toward a population-derived ceiling). The overcapacity ceiling is `eco_pop_ratio * population` — a region with low population cannot sustain a high economy indefinitely. When economy exceeds this ceiling, the decay term pulls it back down. A stable, populated region slowly grows. A tense or overstretched region bleeds output. Note: tension_drag reads the de-oscillated tension trend value to prevent feedback amplification (see "Economic oscillation" below). The adjacency bonus reads the neighbor's real oscillated economy value — adjacency is an external read, not a drift coupling, so it correctly reflects the neighbor's actual current state.

**Territorial adjacency bonus:** Each owned region benefits economically from connected faction territory. The bonus is proportional to each neighbor's economic output — a colony next to a booming core region develops faster than one next to another struggling frontier. This creates natural economic gradients where regions near the faction's center of power are more productive than those on the fringe. The adjacency bonus uses all edge types equally (typed adjacency bonuses are a potential refinement after the base mechanic is proven).

**Economic oscillation:** Economy oscillates around its trend line via a **feedback-isolated additive** mechanism, representing natural boom-bust cycles. The oscillation is additive on the field itself — agents, budget growth, and attractiveness scoring all read the real oscillated value, creating genuine windows of vulnerability during troughs. However, cross-field drift coupling (military decay, tension economic pressure, recruitment threshold checks) reads **de-oscillated values** — the underlying trend with the oscillation term subtracted out. This breaks the feedback loop that would otherwise amplify oscillation through coupled fields (early testing showed pure additive oscillation caused feedback amplification through coupled fields). Over a full cycle the oscillation sums to approximately zero, so the long-term trend is determined entirely by the base drift terms. Each region receives a random phase offset at world generation so regions oscillate out of sync ��� there is always somewhere peaking and somewhere dipping. Flat amplitude (same swing size regardless of economy level) means low-economy frontier regions experience proportionally larger swings, making them the natural flashpoints for conflict.

**Factional Tension drift:**
```
economic_tension = ((tension_economy_midpoint - economy) / 100) * tension_economy_rate * (population / 100)
stress_pressure = max(0, stress_threshold - stability_composite) * stress_tension_rate
subsistence_crisis = subsistence_tension_rate * crisis_severity * (population / 100)    # when economy near floor
natural_decay = tension_natural_decay_rate * (factional_tension / 100)
oscillation = tension_oscillation_amplitude * sin(2 * pi * tick / tension_oscillation_period + tension_phase_offset)

drift = economic_tension + stress_pressure + subsistence_crisis - natural_decay + oscillation
```
Tension has three growth sources. Economic pressure: tension rises when the economy deviates below a midpoint — economic hardship drives unrest, while prosperity calms it. The pressure is scaled by population (more people affected = more tension). Stress pressure: low stability creates fear and blame. Subsistence crisis: when economy is near the floor, additional tension pressure represents desperation (see "Economy floor" below). Natural decay is **proportional to current tension** — higher tension produces stronger decay forces, representing the increasing pressure to resolve disputes as tension mounts. At low tension, grievances fester slowly; at high tension, the forces pushing toward resolution (war exhaustion, political compromise, population flight) are powerful. This proportional structure creates a real equilibrium where growth sources balance against decay, preventing the runaway tension spirals that occur with constant decay. **Open question:** at very high tension (70+), natural decay can outpace economic pressure even when economy is critically low, preventing the intended death spiral where low economy → high tension → revolt/breakaway. A cap on natural decay (e.g., decay stops scaling above tension 70) may be needed to preserve the feedback loop at crisis levels. Investigate during tuning.

**Tension oscillation:** Tension carries its own smaller oscillation representing political cycles — periodic swells of unrest followed by periods of relative calm. Like economic oscillation, the mechanism is **feedback-isolated additive**: the oscillation is additive on the field itself (agents and event threshold checks see the real oscillated value), but other drift formulas that read tension as an input (e.g., economic tension drag) read the de-oscillated trend value. This prevents tension oscillation from feeding back into economic drift and vice versa. The amplitude is smaller than economy's because tension oscillation should be a contributing factor to crises, never the primary cause. A tension uptick alone shouldn't trigger a revolt — but a tension uptick that coincides with an economic trough and a military loss can push a region over an event threshold, creating the emergent compounding that produces unpredictable crises. Each region's tension phase offset is independent of its economic phase offset, so the two cycles drift in and out of alignment naturally. When they align unfavorably (economic trough + tension peak), the region is maximally vulnerable. The tension oscillation period is slightly longer than the economic cycle so the two don't lock into a fixed relationship.

**Population drift:**
```
if economic_output > subsistence_threshold:
    drift = growth_rate * (1 - population / 100)
else:
    deficit = subsistence_threshold - economic_output
    drift = -deficit * decline_rate

# Subsistence crisis — near the economy floor
if economic_output < economy_floor + subsistence_crisis_range:
    crisis_severity = 1.0 - (economic_output - economy_floor) / subsistence_crisis_range
    drift -= subsistence_pop_rate * crisis_severity
    # Also adds extra tension via the tension drift subsistence_crisis term
```
Population grows logistically when the economy can feed people (faster when low, slowing near capacity). Population declines when the economy drops below subsistence, proportional to the deficit. This makes population the slowest, most inertial field — sustained bad conditions to shrink it, sustained good conditions to grow it back.

**Subsistence crisis.** When a region's economy is within a configured range of the economy floor, an additional crisis penalty applies to both population (extra decline) and tension (extra pressure). The severity scales linearly from 0 at the top of the crisis range to 1.0 at the floor itself. This makes the economy floor painful rather than a safe equilibrium — a region sitting at the floor experiences accelerating population decline and tension growth, creating a death spiral that can only be broken by external support (adjacency bonus, faction spending, or conquest by a healthier faction).

**Event effects** — discrete changes from fired events. An event template specifies direct field modifications (e.g., a garrison event boosts military, a famine event reduces population and economy). These are authored per event template in the library. No formula — just the event's impact applied directly. Attack events from hostile factions are a subset of event effects — they apply damage to the defending region's fields based on the attack's strength and the defender's resistance.

**Border friction** — regions bordering hostile factions experience flat per-tick negative effects for each hostile border edge: a config amount of tension added and economy subtracted per hostile neighbor. A region with multiple hostile borders accumulates friction from each edge. Border friction is not military pressure — it's the background stress of living on a contested border: disrupted trade, civilian anxiety, military logistics overhead. This creates a natural softening effect where border regions are chronically stressed, making them easier targets for attacks. Regions with no hostile border neighbors experience no friction.

All coefficients (decay rates, drain rates, scaling factors) are tuning values in config. The formulas' *structures* are the design decision. The specific numbers are what gets tuned during Stage 0.

**Field floors.** A region's economy cannot drop below a configured floor value from drift, border friction, or standard events. This represents subsistence-level economic activity that persists through normal crises — people still farm, local trade still happens. The floor prevents the permanent death trap where economy=0 locks out all recovery paths (no economy → no military maintenance → no recruitment → no stability → death spiral). **Conquest events bypass the economy floor entirely** — economy can drop to zero from conquest damage, representing total infrastructure destruction. A conquered region at economy=0 is not permanently dead: the additive adjacency bonus from neighboring regions and base population growth still apply through drift, so the region recovers slowly under its new owner. But recovery from zero is very slow, which means rapid conquest produces an empire of devastated territory that can't sustain itself — the natural overextension penalty. The economy floor is enforced as a clamp after computing drift and event effects: `economy = max(economy, economy_floor)`. Conquest events carry a bypass flag that skips this clamp.

**Tension floor.** A separate configured floor prevents tension from dropping below a minimum value. This ensures regions always maintain a baseline level of political friction — no region is ever perfectly calm. The tension floor is applied during event resolution but not during drift, so drift can push tension toward the floor but events cannot push it below.

**Reactive reinforcement — telegraph defense.** Reinforce is not a proactive faction decision. Factions do not preemptively spend budget to bolster borders. Instead, reinforcement is **purely reactive** — it fires only when an incoming telegraphed attack is detected against a faction's territory. When a telegraphed attack is pending, the defending faction may commit a fraction of its budget (capped by config) to boost the target region's military before the attack lands. The reactive commit is further capped at a fraction of the attacker's committed budget, preventing defenders from trivially outspending attackers. Whether a faction reinforces reactively is weighted by its archetype's `defend_weight` — defensive archetypes (Fortifier, player civilization) reinforce more reliably than aggressive ones (Conqueror, Warlord). See "Telegraph vs. Surprise Attacks" below for the full system.

**Reinforce resolution.** When reactive reinforcement fires, the military boost is: `boost = commit * reinforce_efficiency * headroom * variance`. Headroom is derived from a per-tier military capacity cap (config value per region tier) — as a region's military approaches its tier cap, reinforcement efficiency drops toward zero. The variance term is a random multiplier within a config range, extended by the region's current tension (high tension → more variance → less predictable defensive responses).

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

**Noise prevents deterministic repetition.** Each event template's trigger threshold gets a random offset within a configured range rolled once per region at the start of each time jump. The offset persists for the duration of the time jump, giving each region a consistent "personality" — a region that's sensitive to factional tension stays sensitive throughout the cycle.

The threshold-trigger model means every event is *explainable* — you can always trace why a chain started by looking at which field crossed which threshold. This makes debugging straightforward and produces clear causal material for the coherence ledger.

**Probability-mode triggers.** A second trigger type exists alongside threshold triggers for events where continuous probabilistic pressure is more appropriate than a discrete threshold crossing. Probability-mode events roll each tick with a formula: `probability = base_probability * (field / 100) ^ exponent`. The exponent controls the curve shape — values below 1.0 make low-field rolls more likely than a linear model, values above 1.0 concentrate rolls at high field values. Probability triggers have a per-region cooldown to prevent rapid re-firing. The regional revolt uses this mode: revolt probability scales with tension each tick rather than firing deterministically when tension crosses a fixed threshold. This produces a more organic revolt pattern where high-tension regions face escalating risk rather than a binary trigger point.

### Tick Resolution Sequence

Each tick processes in this order:

1. **Process the pending event queue** — check if any scheduled events are due this tick. For each, roll against its firing probability. Events that fire resolve immediately: state changes applied, event log updated with chain tags, named character attachments recorded in the coherence ledger, new chain spawns added to queue.
2. **Evaluate fresh event triggers** — for each region, check current field values against the event threshold table (with per-region noise offsets). Any threshold crossed triggers a new event chain. This is how new chains start.
3. **Run all faction agents** — each faction evaluates the current post-event state and makes its decision for this tick: accumulate budget, launch an attack, or colonize an uninhabited region. Attacks are either **telegraphed** (declared this tick, resolved next tick after a reactive defense window) or **surprise** (resolved immediately at reduced efficiency). Telegraphed attacks are registered in a pending list. Defending factions then get a reactive reinforce window — they may spend budget to boost the target region's military before the telegraphed attack lands. **Surprise attacks resolve immediately within step 3** — the attack resolution formula runs inline, field damage is applied to the target region, and if the defender's military drops below the conquest threshold, a Conquest event is inserted into the pending event queue for processing on the next tick. **Telegraphed attacks from the previous tick** also resolve in this step after reactive reinforcement is applied. Conquest follow-up chains (resistance movements, refugee flows, morale effects) propagate through the event chain system's existing chain spawn infrastructure. Faction agents act after events so they can exploit emerging crises — an agent sees the post-event state of regions (including damage from events that fired in steps 1–2), making attack timing strategically meaningful. The player's civilization runs the same agent framework as all other factions, with a conservative defensive posture.
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

**Tuning levers for pacing.** The simulation's event frequency is controlled by: budget growth rate (how fast factions can afford attacks), attack confidence thresholds (how much budget surplus is needed before attacking), telegraph vs. surprise preference (how often defenders get a reactive defense window), resistance factor (how effective defenders are), and conquest consequences (how costly it is to hold new territory). These parameters are tuned together to hit the pacing targets above. If the world is too static, increase budget growth rate or decrease resistance factor. If factions collapse too fast, increase conquest consequences or entrenchment scaling.

### Multi-Faction Agent Decision Model

The world is a **free-for-all between multiple factions**. The player's civilization is one faction among several. External antagonist archetypes, breakaway factions from revolts, and the player's civilization all operate as faction entities within the same simulation framework. Every faction runs the same agent model — the system is symmetric and multiplayer-extensible.

**Faction entity model.** Each faction has: an ID, an archetype (or "player_civilization"), owned regions (tracked via faction_id on each region), a resource budget, a budget growth rate, a **tech_level** (0–100, see "Technology System" below), faction-level modifiers (e.g., a militaristic faction's regions get a military drift bonus, a trade-focused faction's regions get an economy drift bonus), a diplomatic stance toward other factions, and an **attack confidence threshold** rolled at world generation from an archetype-specific range. Faction-level modifiers influence region-level behavior — they are applied as small bonuses to the relevant drift terms in owned regions.

**Aggression variance — per-game faction personality.** Each faction's attack confidence threshold is rolled once at creation from a configured range per archetype. The rolled value persists for the entire game and determines how cautiously or aggressively the faction fights. A low confidence threshold produces an aggressive faction that attacks with slim margins — more frequent attacks, more contested outcomes, grinding border wars. A high threshold produces a cautious faction that waits for overwhelming advantage — fewer but devastating attacks, more breakthroughs. This creates genuine stochastic divergence across playthroughs: the same archetype produces different war stories depending on its personality roll. The variance is rolled per faction, not per tick — it's the faction's strategic identity for this game.

**Budget accumulation.** Each faction's budget grows per tick based on the net economic contribution of its owned regions minus a per-region maintenance cost:

```
budget_growth = sum(region.economy - region_maintenance_cost for region in owned_regions) * archetype_growth_rate
```

The `region_maintenance_cost` is a flat per-region config value representing the administrative and logistical overhead of holding territory (garrison supply, governance, infrastructure upkeep). Each region must produce enough economy to cover its maintenance cost before it contributes to the faction's strategic budget. Regions that don't cover their cost are **net drains** — they actively reduce the faction's budget each tick.

This creates the core expansion risk/reward dynamic: healthy home regions are strong budget contributors, established frontiers are modest contributors, fresh colonies are roughly breakeven or a slight drain, and conquered husks are pure liabilities that bleed the faction until they recover. A faction that conquers five devastated regions watches its budget shrink tick by tick as maintenance on rubble outpaces income from its core — the natural overextension penalty. Expansion is an investment that must "come online" before it pays for itself, and if the faction loses the territory before that happens, it has wasted budget AND weakened itself.

The `region_maintenance_cost` is tuned so that fresh colonies are roughly breakeven. The `archetype_growth_rate` is a per-archetype multiplier that controls overall budget velocity — the Conqueror may grow budget slightly faster than the player's civilization, reflecting a war-economy focus.

**Faction agent decisions.** Each tick, every faction's agent evaluates its situation and makes one of three proactive decisions:

- **Accumulate** — no viable attack or colonization target passes the expected outcome check (see below). Save the budget. The faction's borders are quiet this tick (minor border friction only, no military action). Factions accumulate to build toward offensive actions, but the simulation is tuned so that accumulation phases are finite — budget growth rates and attack thresholds are calibrated to produce regular attacks across the map within any given time jump window.
- **Launch attack** — the agent identifies a target where the expected outcome exceeds its rolled confidence threshold. The agent commits a fraction of its budget as attack strength, choosing either telegraph or surprise mode (see "Telegraph vs. Surprise Attacks" below). This spawns an **Attack event** targeting the enemy region.
- **Colonize** — an uninhabited region scores highest in the attractiveness evaluation and the agent has sufficient budget. The agent commits a portion of its budget as colonization investment. This spawns a **Colonization event** (see "Uninhabited Region Mechanics" below).

Reinforcement is not a proactive decision — it is a **reactive response** to incoming telegraphed attacks. When a telegraphed attack targets a faction's territory, the faction may spend a fraction of its budget to boost the target region's military before the attack resolves. See "Reactive reinforcement — telegraph defense" in the Per-Tick Update Model section above.

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

This self-calibrating logic means factions naturally adapt to the military reality. Against a weak target, the agent may attack early. Against a fortified core, the agent accumulates longer before striking. If the target's military is growing via recruitment, the agent sees the expected net declining each tick and either strikes before the window closes or redirects to a weaker target.

**Budget pressure — preventing infinite accumulation.** When a faction's budget greatly exceeds the break-even cost for its best available attack, the agent's effective confidence threshold decreases. This prevents defensive factions (which have high base confidence) from hoarding budget indefinitely while doing nothing. When `budget / break_even_budget > pressure_threshold`, effective confidence scales down by `pressure_threshold / budget_ratio`. The faction never attacks with negative expected outcome — it just becomes willing to accept slimmer margins when sitting on excess resources. Aggressive archetypes (low base confidence) barely notice the pressure. Defensive archetypes (high base confidence) benefit most because they're the ones who accumulate excessively. The break-even budget is target-relative, so pressure scales with the difficulty of available targets.

The colonize and attack decisions share a single candidate pool — the agent scores all eligible targets (enemy-owned and uninhabited), picks the best one, and the target type determines whether it's an attack or a colonization. This means a faction naturally shifts between expansion and aggression based on what opportunities the world presents.

**Agent decision selection — scored with archetype weights.** When multiple actions are viable on the same tick, the agent does not follow a fixed priority order. Instead, each viable action receives a score, and the highest score wins. The score incorporates both the *quality* of the action and archetype-specific weights that bias the decision:

- Attack score = best_expected_net_force × `archetype_attack_weight`
- Colonize score = best_attractiveness_score × `archetype_expand_weight`
- Accumulate is the fallback when no other score exceeds a minimum viability threshold (config value)

The archetype weights express strategic personality. The Conqueror has high `attack_weight` and `expand_weight` — it attacks frequently and expands aggressively. The player's civilization has low `attack_weight` — it rarely initiates attacks but can counterattack when it has overwhelming advantage. Defensive behavior is expressed through the separate reactive reinforce system (archetype `defend_weight` governs how reliably a faction reinforces against telegraphed attacks) rather than through the proactive decision loop.

The two raw scores (expected_net_force, attractiveness) are on different scales. Each action type uses a normalization function (config-tunable) that maps its raw score to a 0–1 range before the archetype weight is applied.

**Attractiveness scoring — archetype-specific.** Each archetype has its own function for evaluating which regions to attack:

- **The Conqueror** — uses **mixed attractiveness** across three factors: military weakness (easy targets), current economic and population value (worth taking), and strategic position (adjacency to valuable non-owned territory). The candidate pool includes both enemy-owned regions and uninhabited regions adjacent to the Conqueror's territory.

```
score = (w1 * weakness) + (w2 * current_value) + (w3 * strategic_position)

weakness = 1 - (target_military / 100)

current_value = (target_economy * we + target_population * wp) / 100

neighbors = [r for r in adjacent_regions if r.faction_id != conqueror.faction_id]
for each neighbor:
    if inhabited: neighbor_score = (neighbor.economy * we + neighbor.population * wp) / 100
    if uninhabited: neighbor_score = expansion_potential
strategic_position = mean(neighbor_scores) if neighbors else 0
```

The weights `w1`, `w2`, `w3` are config values per archetype (weakness, value, position). Sub-weights `we` and `wp` control the economy vs. population balance within the value calculations. The `expansion_potential` floor for uninhabited neighbors ensures empty regions that open up further expansion corridors are valued over dead ends. An uninhabited region scores: maximum weakness (1.0), zero current value, and strategic position based on what it borders — an empty region between the Conqueror and the player's wealthy core is a high-priority staging ground.
- **The Warlord** — uses the same three-factor formula as the Conqueror but with a reduced weakness weight. The Warlord does not seek the strongest target, but doesn't prioritize the weakest either — reckless, not suicidal. Higher current value and strategic position weights mean the Warlord fights where it matters, not where it's easy.
- **The Fortifier** — uses the three-factor formula with a heavy strategic position bias toward regions that reduce the faction's border exposure. Filling gaps in territorial contiguity and shortening the defensive perimeter score higher than raw economic value. Weakness weight is moderate — the Fortifier waits for overwhelming advantage, so it can afford to be selective about target quality.
- **The Opportunist** — uses the three-factor formula with an additional **recent damage multiplier**: regions that lost military or economy within a recent config window receive a score boost proportional to the magnitude of loss. When no recently-damaged targets exist, the multiplier is 1.0 and the Opportunist evaluates targets like a less aggressive Conqueror.
- **The Schism** — uses **factional tension** as the primary attractiveness factor instead of military weakness. `score = (w1 * target_tension / 100) + (w2 * current_value) + (w3 * weakness)`. High-tension regions score well regardless of military strength — the ideology spreads to the discontented. Does not evaluate uninhabited regions (the Schism only takes inhabited territory).

**Attack event resolution.** When a faction launches an attack, it fires as a discrete event in the target region. The outcome depends on the military comparison between attacker strength (the committed budget) and defender military, with a **resistance mechanic** and a stochastic element:

```
effective_attack = attack_strength * attack_efficiency * tech_attack_mult * surprise_mult
effective_defense = defender_military * resistance_factor * tech_defense_mult * entrenchment
net_force = effective_attack - effective_defense
```

The `surprise_mult` is 1.0 for telegraphed attacks and a reduced config value for surprise attacks. The `entrenchment` multiplier ramps from base to max based on how long the defender has held the region (see "Entrenchment" below). Tech multipliers are derived from each faction's tech level and archetype (see "Technology System"). A stochastic modifier (random multiplier within a configured range) is applied to net_force before outcome evaluation, ensuring evenly matched fights can go either way. The modified net_force determines both the outcome band and the magnitude of consequences — **damage scales proportionally to how decisive the outcome was**:

**Breakthrough** (net_force exceeds `breakthrough_threshold`): The attacker overwhelms the defender. Damage scales with net_force magnitude — a narrow breakthrough is bad, a decisive one is devastating:
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

All damage scale factors are config values. The proportional scaling means a decisive breakthrough is vastly more destructive than a narrow one, and a catastrophically failed attack causes far more domestic unrest than a near-miss. If tuning reveals extreme blowout cases at very high net_force values, a diminishing returns curve can be applied to individual damage components — this is a clean bolt-on that doesn't change the formula structure.

The breakthrough threshold is set so that an attacker must perform at least as well as expected to achieve a breakthrough, with bad luck producing contested results instead.

The resistance mechanic means high defender military actively reduces incoming damage — not just making the region an unattractive target, but genuinely absorbing the blow. A region with military 80 under attack from strength 50 takes very little damage. A region with military 15 under the same attack is devastated.

**Telegraph vs. surprise attacks.** Attacks come in two modes, chosen per-attack based on the faction's archetype preference and the target's military strength:

- **Telegraphed** — the attack is declared one tick before resolution. The attacker commits budget and announces the target. During the intervening tick, the defending faction gets a reactive reinforce window (see "Reactive reinforcement — telegraph defense" above). Telegraphed attacks resolve at full efficiency. Archetypes with methodical military doctrine (Fortifier, Conqueror) prefer telegraphed attacks.
- **Surprise** — the attack resolves immediately with no defender reaction window, but at reduced efficiency (a config multiplier on attack strength). Archetypes that favor raids and opportunism (Warlord, Schism, Breakaway) prefer surprise attacks.

Each archetype has a base telegraph preference (0.0 = always surprise, 1.0 = always telegraph). The preference is adjusted per-attack based on the target's military strength — factions lean more toward surprise against heavily defended targets (where giving the defender time to react would be costly) and toward telegraph against weak targets (where full-strength execution matters more than the element of surprise). The final telegraph/surprise decision is a weighted random roll based on the adjusted preference.

**Entrenchment — tenure-based defense bonus.** Regions gain a defense multiplier based on how long the current faction has held them. The multiplier ramps from a base value (freshly conquered/colonized) to a capped maximum over a configurable number of ticks: `effective_defense = defender_military * resistance_factor * entrenchment`. Entrenchment resets to the base value on conquest or colonization. This makes established territory structurally harder to take than newly claimed territory, rewarding consolidation over rapid expansion and creating a natural asymmetry between attacker and defender.

**Conquest events.** Region ownership changes through Conquest events, which fire when an attack drives a region's military below the conquest threshold. The conquered region transfers to the attacking faction. Consequences: tension spikes (conquered population resents new rulers), population may drop (refugees, casualties), economy is disrupted (infrastructure damage). The Conquest event can spawn follow-up chains — resistance movements, refugee flows to adjacent friendly regions, morale effects in the conquering faction's other regions.

**Conquest trigger — outcome-independent.** Conquest fires when defender military drops below the conquest threshold after attack damage, regardless of whether the attack outcome was classified as breakthrough or contested. The outcome bands (breakthrough/contested/repelled) determine *damage scaling*, not *territorial outcomes*. A contested attack that reduces defender military from 2.0 to 0.0 triggers conquest just as a breakthrough would — the defender's army is destroyed either way. Repelled attacks (negative net_force) never trigger conquest. This matters because sustained attrition warfare (many small contested attacks) can grind a defender's military below the conquest threshold without any single attack producing net_force above the breakthrough threshold.

**Garrison placement.** When a faction conquers a region, a fraction of the committed attack budget converts into military garrison in the conquered region: `garrison = committed_budget × garrison_fraction`. This represents surviving attack forces occupying the territory. A decisive breakthrough leaves a meaningful garrison requiring real effort to overcome. A cheap contested conquest leaves a token garrison — easily retaken, which correctly reflects the fragility of an opportunistic grab. Without garrison placement, conquered regions have zero military and change hands every tick as adjacent factions trivially reconquer them.

**Conquest consequence chain.** When a conquest occurs, there is a config probability of spawning a CONQUEST_UNREST event after a delay in the conquered region. Conquest Unrest represents post-conquest civil instability: tension spike, economy disruption, military attrition. The unrest event can chain into a Regional Revolt (if tension exceeds threshold), which can chain into a Revolt Entrenched event that creates a breakaway faction. The full chain — conquest → unrest → revolt → breakaway — means that conquering territory carries long-term instability risk, especially if the conquering faction cannot manage the tension in its new territory.

**Administrative revolt system — faction size pressure.** Independent of tension-triggered revolts, every faction faces a per-tick, per-region probability of an administrative revolt — a separatist movement that emerges not from popular unrest but from institutional fracture, regional self-sufficiency, or distant-province autonomy. The probability scales **quadratically** with faction size: `admin_revolt_chance = base_rate + scaling_rate * max(0, territory_count - inflection_point)^2`. The `base_rate` is small but nonzero for all factions regardless of size — even a 2-region faction can lose a province to secession, it's just rare. The `inflection_point` is where the quadratic acceleration begins, not where revolt becomes possible. Above the inflection point, each additional region dramatically increases revolt risk everywhere in the faction. The roll is **uniform across all regions** — home regions and frontiers are equally likely to revolt from administrative pressure. This is intentionally aggressive: the quadratic scaling guarantees that large empires hemorrhage territory, keeping the world fractured and dynamic. The config values (`base_rate`, `scaling_rate`, `inflection_point`) are tuned so that sustainable empire size is limited before admin revolts become a serious recurring problem, while still producing occasional revolts below that range.

**Administrative revolt chain.** When the admin revolt roll fires, it spawns a separatist movement event chain of **variable length** (3–8 ticks, rolled at spawn time). Shorter chains represent swift coups; longer chains represent political secessions that build over months. The chain length is determined at ignition and sets the pacing of intermediate events:

- **Short chain (3–4 ticks):** Separatist Movement → Military Defection → Breakaway. Fast coup. Almost no time to respond.
- **Medium chain (5–6 ticks):** Separatist Movement → Political Crisis → Military Defection → Breakaway. Some warning, narrow response window.
- **Long chain (7–8 ticks):** Separatist Movement → Political Crisis → Popular Support Shifts → Military Defection → Breakaway. The slow version — still much faster than the tension revolt pipeline.

Each intermediate event applies field effects to the revolting region (tension spike, economy disruption, military split), so the region is degraded by the time it breaks away. **The chain is non-interruptible** — once an admin revolt fires, it always completes and produces a new independent faction. The owning faction cannot suppress it by reinforcing the region or improving conditions. This is the critical design distinction from tension revolts: tension revolts are disruptable (improve conditions before the follow-up's condition check, prune the chain). Admin revolts are institutional fractures — inevitable once they begin. The faction's only defense is not being too large, or getting lucky on the per-tick roll.

**Breakaway faction from admin revolt.** The chain's terminal event creates a new independent faction holding the revolting region. The new faction spawns with zero budget. The region keeps its current field values minus whatever the chain events degraded, then receives **viability buffs** (tension capped, population and economy floored to config minimums) to ensure the new faction spawns in a survivable state. The new faction's archetype is rolled from the archetype pool. The former owner loses the region and all its economic contribution immediately. The loss reduces the former owner's territory count by one, which slightly reduces admin revolt pressure on its remaining regions — a natural self-correcting dynamic where losing territory to secession makes the remaining empire slightly more stable.

**Coexistence with tension revolts.** Administrative revolts and tension-triggered revolts are independent systems that coexist. A large, high-tension empire gets hit by both — tension revolts in stressed regions and admin revolts everywhere. They represent different failure modes (popular unrest vs. institutional fracture) that share the same consequence: new factions appearing on the map. A large faction in crisis can cascade rapidly as both systems fire simultaneously, producing the dramatic civilizational collapse the bible's pacing model requires.

**Latent loyalty.** Recently conquered regions retain loyalty to their previous faction. If a revolt fires in a region that was conquered within a config window and the previous faction still exists, there is a probability the region reverts to the previous faction instead of creating a new breakaway. The reverted region receives the same viability buffs as a standard breakaway (tension capped, population and economy floored). This creates a "reconquest" dynamic — conquering territory near a surviving faction is riskier than conquering territory from a faction you've already eliminated, because successful revolts can restore the old owner's borders.

### Uninhabited Region Mechanics

Uninhabited regions exist in the world at generation (defined by the starting template) with no field values and no faction ownership. They are activated through **colonization events** fired by faction agents.

**Colonization as an agent decision.** Colonization uses the same attractiveness scoring pipeline as attacks. Uninhabited regions adjacent to a faction's territory enter the candidate pool alongside enemy-owned regions. Each archetype's scoring function evaluates them through its own lens — the Conqueror sees an undefended gateway, the Fortifier sees a region that shortens its defensive perimeter. If an uninhabited region scores highest in the candidate pool, the agent colonizes it instead of attacking an enemy. If enemy targets consistently score higher, the faction fights instead of expanding. The scoring handles prioritization naturally without special-case logic. Note: the Schism does not colonize — it only targets inhabited regions.

**Colonization cost.** The agent spends a portion of its budget on colonization (config value: `colonization_cost`). This is typically cheaper than an attack (no resistance to overcome), which creates a natural tempo incentive — early in the game when factions are building up, cheap expansion into empty space is often the best use of limited budget. As the map fills up and empty regions become scarce, the budget increasingly goes toward military action. The colonization cost is deducted from the faction's budget the same way attack strength is committed.

**Starter field values.** A newly colonized region is initialized with flat config values representing a bare frontier outpost (`colony_start_military`, `colony_start_economy`, `colony_start_tension`, `colony_start_population`). All factions' colonies start identically — differentiation comes from what happens after colonization. The territorial adjacency bonus accelerates economic growth based on neighbor strength (a colony next to a booming core develops faster than one next to another weak frontier), the economic and tension oscillation cycles create dynamic vulnerability windows, and the existing passive drift formulas naturally grow the colony's fields over time. The colony is a long-term investment: it takes many ticks of drift before it contributes meaningfully to the faction's budget, but even modest economy contributes to budget growth and the territorial adjacency bonus rewards contiguous expansion. The existing defender's advantage systems (military resistance mechanic in attack resolution, recruitment drift rebuilding garrisons over time, tension mechanics braking runaway prosperity) handle the snowball concern — rapid expansion produces low-field regions that are expensive to defend and slow to develop.

**Contested regions — collision resolution.** When two or more factions target the same region on the same tick (whether through attacks, colonization, or a mix), the intent resolver runs a collision resolution. Each participant's effective strength is computed from their committed budget, weighted by an economy factor (factions with stronger economies fight more effectively in collisions) and tech multipliers. The winner is chosen probabilistically — higher effective strength means higher probability of winning, but upsets are possible. The victory margin determines consequences: a dominant victory leaves the winner with retained budget and a strong garrison, while a narrow victory produces a weakened claim with reduced military. Losers spend their committed budget and take a tension hit to their home regions. For uninhabited region collisions, the winner colonizes with margin-adjusted starter values — a narrow win produces a weaker colony than an uncontested claim.

**Why factions expand.** Uninhabited regions provide three forms of value once claimed: (1) **Strategic buffer** — an owned region between a faction and its enemies that must be conquered before reaching the core, even at low military. (2) **Long-term budget investment** — a fresh colony starts at roughly breakeven against maintenance cost, but the territorial adjacency bonus and passive drift grow its economy over time until it becomes a net contributor. Expansion is an investment that takes many ticks to pay off, not an immediate payoff — the faction must be able to absorb the short-term maintenance cost while the colony develops. (3) **Territorial adjacency bonus** — the economy drift adjacency bonus (see "Economic Output drift" above) means claiming a region between two existing territories connects them economically, boosting both. This creates a concrete incentive for contiguous territorial expansion and accelerates colony development near strong existing regions.

### Diplomatic Stance

Each faction maintains a diplomatic stance toward every other faction. Stances are a simple enum: **hostile**, **neutral**, or **cooperative**. Starting stances are defined as per-archetype-pair overrides in config. The default stance between any two factions is neutral unless an override exists. The starting world is significantly hostile: the Conqueror starts hostile toward all other factions, the Schism starts hostile toward most factions, and several other archetype pairs (Fortifier–player, Opportunist–player) begin hostile. Breakaway factions from revolts start hostile toward their parent faction and all existing factions. The full set of starting stance overrides is in config — the intent is a dangerous, contested world from tick 1.

Stances are mutable through events. A diplomatic event chain could shift a neutral faction to hostile. A successful negotiation mission could shift a hostile breakaway to neutral. Stance changes are event effects, applied the same way as field changes — authored per event template in the library.

Mechanical effects of stance:
- **Hostile** — border friction applies, faction agents include each other's regions in attack candidate pools, the faction's territory is treated as enemy territory for all simulation calculations.
- **Neutral** — no border friction, no attacks, no economic bonuses. Factions coexist without interaction. Neutral factions' regions are excluded from attack candidate pools.
- **Cooperative** — no border friction, no attacks. Cooperative factions' adjacent regions contribute to the territorial adjacency bonus as if owned by the same faction (representing trade cooperation and economic partnership). Cooperative factions benefit from **technology convergence** — the lower-tech faction gains tech_level growth toward its highest-tech cooperative partner's level (see "Technology System — Tech Convergence in Cooperative Peace" below). Only the best partner contributes tech benefit; multiple cooperative relationships stack economically (adjacency bonus) but not technologically.

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

**Tech growth formula.** Tech_level grows per tick based on the faction's economic base, with a population floor preventing double-penalty death traps:

```
tech_growth = base_tech_rate * (avg_faction_economy / 100) * max(population_floor, avg_faction_population / 100)
```

Economy is the primary driver — a faction with a healthy economy advances; a faction with ruined economy stagnates. Population acts as a secondary scaling factor, but the floor ensures that a faction with depleted population but strong economy still advances, just more slowly. This prevents the scenario where a post-plague or post-conquest faction is permanently stuck at low tech because both economy and population are suppressed simultaneously. The averages are computed across all owned regions. The `base_tech_rate` is a config value tuned so that tech growth is gradual — technology is a slow-moving civilizational attribute, not a per-tick resource race.

**Tech convergence in cooperative peace — best-partner-only.** Factions in a cooperative diplomatic relationship benefit from technology sharing. The lower-tech faction gains additional tech_level growth per tick based on the gap between its tech_level and its **single highest-tech cooperative partner's** tech_level:

```
tech_sharing_bonus = convergence_rate * max(0, best_partner_tech - own_tech) / 100
```

Only the highest-tech cooperative partner contributes to convergence. Additional cooperative partners provide zero additional tech benefit — their value is purely economic (adjacency bonus sharing, border friction removal). This completely prevents "peace coalition" snowballing where a cluster of cooperative factions accelerates away from isolated factions technologically. The `convergence_rate` is a config value tuned so that tech sharing provides a meaningful but not dominant growth boost — a faction at peace with an advanced neighbor should noticeably close the gap over hundreds of ticks, but should not catch up entirely through sharing alone. The advanced faction receives no tech benefit from the partnership — its incentive for cooperation is the economic adjacency bonus and border friction removal.

**Multiplier magnitude — asymmetrically distributed.** Each archetype has a total tech multiplier budget distributed across its favored axes according to its strategic identity. A Conqueror allocates most of its tech benefit to attack efficiency with a sliver to economic growth. A Fortifier splits roughly evenly across defense efficiency and economic growth with a small attack allocation. The player's civilization has a balanced distribution.

At tech_level 0, all multipliers are 1.0 (baseline). The multipliers scale linearly with tech_level — a faction at tech 50 gets roughly half the maximum benefit. The per-archetype multiplier distributions are config data (see `ARCHETYPE_TECH_MULTIPLIERS` in config.py).

The total tech budget is calibrated to produce a meaningful but not dominant advantage. Tech advantage should be one significant factor among several (budget, military strength, positioning, archetype matchup), not the deciding factor on its own. A faction with a large tech advantage that overextends or mismanages its budget still loses. The same tech multipliers feed both the simulation's attack resolution formula and the tactical layer's unit stat generation, ensuring the player experiences the same tech edge the simulation calculates.

The per-archetype multiplier distributions are config data — a table of (archetype, axis, weight) tuples. No special-case logic per archetype in the engine. The distributions are tuned during implementation by running the simulation and verifying that tech advantages produce the intended 60/40-neighborhood edge without dominating outcomes.

**Breakaway inheritance.** When a breakaway faction is created from a revolt, the new faction copies the parent faction's current tech_level. This represents the breakaway population taking their knowledge and skills with them. The breakaway then grows (or stagnates) its tech_level independently based on its own economic and population base. A breakaway from a high-tech faction starts advanced but may fall behind if it can't sustain the economic base needed for continued growth.

**Technology loss.** Tech_level can decrease through event chain effects — technology loss events that fire when a faction's conditions deteriorate. A faction whose economy collapses, whose population declines, or whose territory fragments may lose technological knowledge over time. This is consistent with the Foundation theme — civilizations can regress, and the knowledge of one generation is not guaranteed to survive to the next. Technology loss events are authored as event templates in the library, firing on threshold triggers like all other events.

#### Tech Tiers — Unit Variant Progression

Tech tiers are the player-facing manifestation of technology progression. As a faction's tech_level crosses tier boundaries, the units the faction fields change — not just in numbers, but in kind. Each tier unlocks a different set of stat ranges, trait pools, and ability variants for all 6 base unit types.

**3 tech tiers per era**, with uniform boundaries across the tech_level range:

- **Tier 1:** tech_level 0–33 — baseline technology. Functional but limited units. The "frontier era" feeling for a young or recovering faction.
- **Tier 2:** tech_level 34–66 — established technology. Improved stats, more specialized traits, broader ability variants. The "consolidation era" feeling for a stable, growing faction.
- **Tier 3:** tech_level 67–100 — advanced technology. Highest stat ranges, most specialized traits, most powerful ability variants. The "peak era" feeling for a thriving faction — or the tier a declining faction is desperately trying to hold onto.

Three tiers means two tier transitions per game — each one a meaningful chronicle moment. The uniform spacing keeps the boundaries simple to reason about and balance. Each transition represents a real qualitative shift in what units look and feel like, not just a stat bump.

**The engine owns the 6 base types and the RPS triangle; the tier determines what the AI library generates.** The engine knows "this faction is at tech tier 2, generate units accordingly." The AI library generates stat profiles, trait pools, and ability variants appropriate to that tier. A tier-1 faction fields units with lower stat ranges, simpler traits, and basic ability variants. A tier-3 faction fields units with higher stat ranges, more specialized traits, and advanced ability variants. The 6 base unit types and the RPS triangle remain constant across all tiers — Strike still beats Siege, Siege still beats Line, Line still beats Strike. Tiers change what the units can do and how well they do it, not the fundamental combat relationships.

**Tech tiers are era-specific content.** Each theme pack defines what its tiers look and feel like. The engine's abstract tier system is era-agnostic. The sci-fi theme pack defines what a tier-1 "Raider" looks like (slow transit, laser weapons) versus a tier-3 "Raider" (near-instant transit, personal shielding). A Roman-era theme pack would define tier-1 as early republic (basic legions, coastal galleys) and tier-3 as late empire (professional army, corvus-equipped navy). The engine doesn't know "laser" or "corvus" — it knows stat ranges and ability tags. This is fully consistent with the existing skeleton/skin architecture.

**Tier regression.** Factions can regress tiers through technology loss. If a faction's tech_level drops below a tier boundary (through technology loss events or conquest-driven economic collapse), the faction drops to the lower tier and its units reflect the regression. This is one of the game's most dramatic moments — fielding degraded technology because the civilization that built the advanced units no longer exists in the same form. The chronicle frames this naturally: "The forces that once carried shielded armor now fought with patched relics."

**Cross-tier mission feel.** When the player's faction is at a different tech tier than the enemy, the force parity system (which already handles strength asymmetry) compensates: the player receives more units if their units are individually weaker, or fewer units if their units are individually stronger. A tier-2 player facing tier-3 enemies gets more units to compensate for the stat gap. This preserves the design principle that difficulty comes from constraint compression, not from enemy factions having objectively better units. The question of whether cross-tier matchups feel fun or frustrating is a tuning question to be resolved during implementation.

**Tier transitions — discrete jumps.** When a faction's tech_level crosses a tier boundary, new units generated for that faction use the new tier's stat ranges, trait pool, and ability variants. Existing units already fielded do not retroactively change — they remain at their generation-time tier until lost in combat or retired. The transition is visible to the player through the force composition: after a tier transition, newly assigned forces include units that are qualitatively different from previous chapters' forces. The chronicle frames tier transitions as significant moments: "For the first time, our forces carried technology that would have been unrecognizable to the commanders who fought here a century ago." Discrete jumps are simpler than smooth interpolation, create clearer narrative beats, and align with how the AI library already works — generate from a tier profile, not interpolate between two.

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

**Lifespan and death.** Characters have a lifespan rolled at creation from a config range. When a character's age reaches their lifespan, they die: status changes to `historical`, `death_tick` is recorded. Death is a ledger-level state change, not necessarily a discrete event in the event chain system. The chronicle distiller and template system can reference a character's death *if it's narratively relevant* — a faction leader dying mid-war is chronicle material; a garrison officer dying of old age in a quiet backwater probably isn't. The distiller makes this judgment through its existing significance scoring, not through a special death-event mechanism.

**Succession.** When a named character dies, their role is filled by a new named character. For faction leaders (`supreme_commander`), succession produces a new character in the same faction. For regional commanders, succession produces a new character in the same region. The new character is created with a fresh name from the library, a new lifespan roll, and the same faction and region assignments. Succession is automatic — the ledger handles it as part of its lifecycle management during each tick's logging step. Succession events that are narratively significant (a faction leader dying during a critical war) surface through the chronicle distiller's normal significance scoring of events in the event log.

### Character Selector Data Contract

> **RESOLVED (v2.05).** This section specifies the implementation-level data structures and mechanisms for the character selector algorithm described in game_bible.md. The design intent (2–4 chapter lineage persistence, three-pool selection, cross-faction rotation) is documented in the hub. This section documents how those mechanisms interact with the coherence ledger.

**CommanderSelection record.** The character selector returns a structured record after each selection:

```python
@dataclass
class CommanderSelection:
    character_id: str           # Coherence ledger character ID
    lineage_id: str             # Lineage ID (new or continued)
    faction_id: str             # Faction the commander serves
    rotated: bool               # True if lineage rotation occurred
    rotation_reason: str | None # "forced", "hard_cap", "delta_roll", None if no rotation
    pool_used: str | None       # "previous_descendant", "nemesis_descendant", "unrelated", None if continued
```

This record is consumed by the generational loop (`generational.py`) to set up the next mission's commander identity, and by the chronicle distiller to frame rotation events in the scroll ("a new family takes up the burden").

**Nemesis tagging.** When the player completes a mission, the enemy faction's named characters in the mission region gain a `rival_of` tag in the coherence ledger, linking them to the player's current commander. This is the mechanism that populates the character selector's Priority 2 (nemesis/rival descendant) pool. The tag is a lightweight annotation on the character record — it does not create a bidirectional relationship graph or duplicate event log data. The character selector queries these tags at selection time to find rival descendants in or near the mission region.

**Chapter counter.** The coherence ledger tracks a `chapter_counter` per lineage — incremented each time the character selector continues or begins a lineage. The counter is read by the selector's rotation decision cascade (minimum stay check, hard cap check) and reset to 1 when a new lineage begins.

**Generational loop position.** The character selector runs after the mission generator in the generational loop:

```
mission → outcome resolver → time jump (N ticks + chronicle distiller) → mission generator → character selector → next mission
```

The selector runs *after* the mission generator because it needs the mission region to make its selection. The mission generator selects based on simulation pressure; the character selector finds the best person to send to the already-selected mission.

**Lineage generation is a separate module.** The lineage generator runs during time jumps and produces new lineage member records. It hands these to the ledger for registration. The ledger does not contain lineage generation logic — it just files the new characters. See "The Generational Structure — Character Selector Algorithm — Step 4" in game_bible.md for lineage generation details.

**Nemesis detection.** Nemesis relationships are tracked via the `rival_of` tag described above — a lightweight annotation applied during mission resolution. The character selector queries these tags at selection time rather than scanning the event log. This keeps nemesis detection fast (tag lookup vs. event log scan) while maintaining the principle that the ledger stores only identity and lifecycle data, not duplicated event history. The tag is the minimum viable annotation needed to support the Priority 2 nemesis pool.

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

Stage 1 builds on the single-region SD model proven in Stage 0 by introducing a **world graph** — multiple regions connected by random adjacency, each running the same drift logic but producing different trajectories based on starting values and connections. The world is generated procedurally: 40-60 regions per game (randomized), with 4 factions each starting with a home region and one frontier region. The remaining regions start empty. The adjacency graph is built from a random spanning tree plus extra edges, ensuring connectivity while maintaining sparse corridors. Faction home regions are separated by a minimum buffer of empty regions. Each region drifts independently through the proven Stage 0 formulas, with three new inter-region mechanics layered on top: baseline recruitment, territorial adjacency bonus, and feedback-isolated economic/tension oscillation.

**What was proven:** Home regions and frontier regions, starting from different field values, produce meaningfully different drift trajectories. Frontiers show more volatility than home (weaker starting position amplifies sensitivity to drift interactions). Different random seeds produce divergent outcomes that amplify over time rather than converging. Long-run behavior (500 ticks) is coherent: no degenerate states, no collapses from healthy starting positions, trajectories are explainable from the underlying mechanics.

**Key tuning decisions during Stage 1:**

- **Baseline recruitment** added to prevent frontier military freefall. At low frontier economies, military decayed to near-zero because the economy-scaled recruitment term required economy above the threshold. A constant baseline recruitment term fires for all inhabited regions regardless of economy, representing militia raised from the local population. Weak frontiers stabilize at low-but-nonzero military rather than collapsing to zero. Home regions are unaffected — the baseline is negligible at high economy.

- **Adjacency bonus tuned down** from its initial value. The original value was too large — every region hit economy 100 quickly, erasing the economic gradient. The tuned value roughly doubles frontier growth near the core but preserves the gradient over hundreds of ticks.

- **Home population range raised** from its initial value. The original range produced tension equilibrium below the intended design target. The raised range produces tension equilibrium closer to the Stage 0 reference. The formula weights were not changed — tension increases further when border friction and factions arrive in Stage 3.

- **Oscillation mechanism changed from simple additive to feedback-isolated additive.** Simple additive oscillation caused feedback amplification through coupled fields. Coefficient modulation was tried but was too subtle. The feedback-isolated approach adds the oscillation to the stored field value (what agents see) but has cross-field drift coupling read de-oscillated trend values, breaking the feedback loop while keeping visible swings. Economy deviation is bounded, oscillation does not prevent net growth, and tension never hits zero from oscillation alone.

- **Oscillation config values** were tuned iteratively — periods and amplitudes were adjusted from their original starting points to create agent-exploitable windows at the simulation's timescale while keeping long-term trends dominant. See config.py for current values.

**World topology.** Each new game generates a random connected graph of 40-60 regions. Four factions are placed with separation guarantees — no faction home is adjacent to another faction's territory. Empty regions form natural corridors and chokepoints through the random spanning tree structure. The player does not choose a starting template — every game produces a unique topology.

### Stage 3 Tuning Observations

These observations emerged from running the simulation at 4-faction scale (500 ticks, 5 seeds) during Stage 3 tuning. They document known behavioral patterns and their implications for later stages. None are bugs — they are characteristics of the current mechanical design that should be monitored as later systems come online.

**Observation: Factions with strong economy tend to dominate.** A faction with a highly developed region (economy 60+) generates substantially more budget than factions with only undeveloped regions (economy 25–50). Over hundreds of ticks, the budget advantage compounds: more budget → more attacks → territory gains → more economy → more budget. The tech system will amplify this (economy drives tech growth, tech multipliers improve attack efficiency). Existing counter-pressures include: conquest consequence chains (conquered territory is unstable), overextension penalties (maintaining devastated territory is costly), the revolt/breakaway system (high-tension regions may splinter), and the **administrative revolt system** (quadratic scaling with territory count guarantees that large empires hemorrhage territory regardless of tension management — see "Administrative revolt system" in the Simulation Backbone). The mission generator and player-facing systems should also be evaluated against this pattern — a dominant faction produces fewer mission hooks and less chronicle material during time jumps.

**Observation: Low-economy factions can become functionally inert.** Factions with net economy barely above maintenance threshold generate minimal budget surplus. If reinforce spending consumes most of this income, the faction never accumulates enough for offensive action. The shortfall model limits reinforce drain, but a faction with only undeveloped regions and no economic advantage may still struggle to reach attack viability within 500 ticks. The diplomacy system's cooperative mechanics (adjacency bonus sharing, tech convergence) are the designed escape hatch, but only if the faction can sustain the stability needed for peace formation. Worth monitoring whether the budget growth formula needs a minimum growth floor or whether maintenance cost should scale with economy rather than being flat.

**Observation: Attack timing is regular when conditions are stable.** When a faction's territory, economy, and borders don't change, its attack cadence becomes metronomic — same accumulation time, same commit amount, same cycle. This is expected in a two-faction stalemate but would produce repetitive chronicle material during time jumps. The diplomacy system (peace formation, betrayal) introduces timing disruption. Decision noise (small random perturbation on action scores or probability-weighted selection instead of argmax) is a noted future consideration (see "random hyper-focus" in the antagonist system section) that would add further timing variation.
