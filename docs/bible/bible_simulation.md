# Ouroboros Manifold — Simulation Backbone Reference

> **Extracted from game_bible.md v1.23.** This file is authoritative for simulation
> mechanics. If this file conflicts with game_bible.md, flag it for Westley — do not
> silently resolve the conflict.
>
> **Modification rule:** Same as the master bible — append-only unless Westley approves
> deletion. Resolved open questions get written here AND reflected back to the hub.

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

**Reinforcement diminishing returns — continuous capacity cap.** The reinforce agent action (spending faction budget to boost a region's military) has diminishing effectiveness as the region's military approaches a **continuous capacity ceiling** derived from the region's current development. The cap replaces the old binary home/frontier tier distinction — there are no discrete region tiers. Instead, the cap floats based on the region's economic output and population, reflecting that a developed region can logistically absorb more reinforcements than a bare outpost. The formula: `effective_cap = cap_floor + (economy * w_econ) + (population * w_pop)`, clamped to `[cap_floor, cap_ceiling]`. The reinforce formula uses this cap: `boost = budget_spent * reinforce_efficiency * max(0, (effective_cap - military) / effective_cap)`. The cap reads **raw oscillated economy** — a region in an economic boom can absorb slightly more reinforcements than one in a bust, which creates genuine micro-windows of vulnerability during economic troughs consistent with the oscillation system's design philosophy. If the cap dips below current military (e.g., during a sustained economic decline), reinforce efficiency goes to zero but existing military is not destroyed — it simply cannot be topped up until the cap rises again or natural decay brings military back down. The cap is **automatically reversible**: a conquered region's economy craters, its population drops, and the cap drops with it — no demotion logic needed. A region becomes mechanically fragile the moment its fields collapse. Conversely, a frontier held for hundreds of ticks with growing economy and population gradually becomes harder to crack as its cap rises, representing the natural maturation of a frontier into a homeland. Config values: `cap_floor`, `cap_ceiling`, `w_econ`, `w_pop` — tuned empirically during implementation to produce reasonable caps across the range of field values the simulation generates (fresh colonies should be very fragile, mature frontiers moderately tough, developed home regions strong but not invincible).

**Reinforce scoring — military shortfall model.** The reinforce action's attractiveness is scored by **absolute military shortfall** at border regions, not by threat ratio. Shortfall = `adjacent_hostile_military - own_region_military`. A shortfall of 2.0 scores low (near parity, don't bother). A shortfall of 20.0 scores high (serious gap, reinforce now). The shortfall floor (config value, e.g. 3.0) filters out negligible gaps — below the floor, the border is considered adequately defended and reinforce does not enter the scoring pool. Reinforce spending is proportional to the gap: `committed = min(budget × spend_fraction, shortfall × spend_scale)`. The `min()` cap means small gaps produce small spending regardless of budget, and large gaps produce larger spending capped by a budget fraction. This prevents symmetric arms-race traps where two factions pump budget into a near-parity border indefinitely. The shortfall model scales naturally to N factions because it's a per-border calculation with no dependency on global budget math.

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

**Reinforce trigger — threat score evaluation.** **[Superseded by the shortfall model in v1.18 — see "Reinforce scoring — military shortfall model" above. The threat-ratio approach described below was replaced during Stage 3 tuning because the ratio couldn't distinguish near-parity from serious gaps, producing permanent reinforce drain cycles at scale. The overreaction variance concept remains a valid future consideration but is not currently implemented.]** For each owned border region adjacent to hostile territory, the agent computes a threat score based on adjacent hostile military strength, the region's own military relative to its tier cap, and the hostile faction's recent activity (attacks in the last N ticks). If any region's threat score exceeds a per-archetype config threshold, the agent reinforces it. The player's civilization has a low threshold (reinforces early — conservative defensive posture). The Conqueror has a high threshold (rarely reinforces, prefers attacking). Threat scores require the agent to read hostile neighbor military from the world graph — agents have perfect information about adjacent region military strength (see "Agent Information Model" below).

**Reinforce spending — threat-proportional with overreaction variance.** The agent computes a threat ratio for the target region: `adjacent_hostile_military / own_region_military`. The ratio drives a spending curve:

- Low threat (ratio below low_threat_ceiling, e.g., 0.8): spend nothing on this region, accumulate instead. The border is adequately defended.
- Moderate threat (ratio between low_threat_ceiling and high_threat_floor, e.g., 0.8–1.5): spend a moderate fraction of budget scaled by the ratio. The agent is matching the buildup.
- High threat (ratio above high_threat_floor, e.g., 1.5): spend aggressively — a large fraction of available budget. The civilization is scared.

On top of the computed spending amount, each reinforcement decision applies an **overreaction variance roll** — a random multiplier (config range, e.g. 0.5–1.5) representing institutional dysfunction. Sometimes the bureaucracy panics and sends twice what's needed. Sometimes it underfunds a critical frontier because the political class is distracted or the supply chain is strained. The variance range is modified by the region's current factional tension: high tension widens the range (more dysfunction, less predictable responses), low tension narrows it (stable government, rational allocation). This creates emergent behavior where a civilization under internal stress makes erratic defense decisions — over-reinforcing one border while neglecting another — which is exactly when it's most vulnerable to external attack.

The final budget spent (after variance roll) is subject to the existing diminishing returns formula: `boost = budget_spent * reinforce_efficiency * max(0, (effective_cap - military) / effective_cap)`, where `effective_cap` is the region's continuous capacity cap derived from economy and population (see "Reinforcement diminishing returns — continuous capacity cap"). The spending curve breakpoints, variance range, and tension modifier are config values tuned during Stage 3.

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

**Budget pressure — preventing infinite accumulation.** When a faction's budget greatly exceeds the break-even cost for its best available attack, the agent's effective confidence threshold decreases. This prevents defensive factions (which have high base confidence) from hoarding budget indefinitely while doing nothing. When `budget / break_even_budget > pressure_threshold` (config value, e.g. 1.5), effective confidence scales down by `pressure_threshold / budget_ratio`. At 2× break-even, confidence is halved. At 4× break-even, quartered. The faction never attacks with negative expected outcome — it just becomes willing to accept slimmer margins when sitting on excess resources. Aggressive archetypes (low base confidence) barely notice the pressure. Defensive archetypes (high base confidence) benefit most because they're the ones who accumulate excessively. The break-even budget is target-relative, so pressure scales with the difficulty of available targets.

The colonize and attack decisions share a single candidate pool — the agent scores all eligible targets (enemy-owned and uninhabited), picks the best one, and the target type determines whether it's an attack or a colonization. This means a faction naturally shifts between expansion and aggression based on what opportunities the world presents.

**Agent decision selection — scored with archetype weights.** When multiple actions are viable on the same tick, the agent does not follow a fixed priority order. Instead, each viable action receives a score, and the highest score wins. The score incorporates both the *quality* of the action (how good is this attack? how urgent is this reinforcement?) and archetype-specific weights that bias the decision:

- Attack score = best_expected_net_force × `archetype_attack_weight`
- Colonize score = best_attractiveness_score × `archetype_expand_weight`
- Reinforce score = highest_military_shortfall × `archetype_defend_weight` **[Updated in v1.18: was threat_ratio, now uses shortfall model]**
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

**Conquest trigger — outcome-independent.** Conquest fires when defender military drops below the conquest threshold after attack damage, regardless of whether the attack outcome was classified as breakthrough or contested. The outcome bands (breakthrough/contested/repelled) determine *damage scaling*, not *territorial outcomes*. A contested attack that reduces defender military from 2.0 to 0.0 triggers conquest just as a breakthrough would — the defender's army is destroyed either way. Repelled attacks (negative net_force) never trigger conquest. This matters because sustained attrition warfare (many small contested attacks) can grind a defender's military below the conquest threshold without any single attack producing net_force above the breakthrough threshold.

**Garrison placement.** When a faction conquers a region, a fraction of the committed attack budget converts into military garrison in the conquered region: `garrison = committed_budget × garrison_fraction` (config value, e.g. 0.30). This represents surviving attack forces occupying the territory. A decisive breakthrough (committed budget 30) leaves garrison ~9 — a meaningful defensive presence requiring real effort to overcome. A cheap contested conquest (committed budget 3) leaves garrison ~0.9 — easily retaken, which correctly reflects the fragility of an opportunistic grab. Without garrison placement, conquered regions have zero military and change hands every tick as adjacent factions trivially reconquer them.

**Conquest consequence chain.** When a conquest occurs, there is a 60% chance of spawning a CONQUEST_UNREST event 4–8 ticks later in the conquered region. Conquest Unrest represents post-conquest civil instability: tension spike, economy disruption, military attrition. The unrest event can chain into a Regional Revolt (if tension exceeds threshold), which can chain into a Revolt Entrenched event that creates a breakaway faction. The full chain — conquest → unrest → revolt → breakaway — means that conquering territory carries long-term instability risk, especially if the conquering faction cannot manage the tension in its new territory.

**Administrative revolt system — faction size pressure.** Independent of tension-triggered revolts, every faction faces a per-tick, per-region probability of an administrative revolt — a separatist movement that emerges not from popular unrest but from institutional fracture, regional self-sufficiency, or distant-province autonomy. The probability scales **quadratically** with faction size: `admin_revolt_chance = base_rate + scaling_rate * max(0, territory_count - inflection_point)^2`. The `base_rate` is small but nonzero for all factions regardless of size — even a 2-region faction can lose a province to secession, it's just rare. The `inflection_point` is where the quadratic acceleration begins, not where revolt becomes possible. Above the inflection point, each additional region dramatically increases revolt risk everywhere in the faction. The roll is **uniform across all regions** — home regions and frontiers are equally likely to revolt from administrative pressure. This is intentionally aggressive: the quadratic scaling guarantees that large empires hemorrhage territory, keeping the galaxy fractured and dynamic with 4–8 factions in play at any given time. A faction holding 9 regions should be constantly losing periphery. Config values: `base_rate`, `scaling_rate`, `inflection_point` — tuned so that sustainable empire size is roughly 4–6 regions before admin revolts become a serious recurring problem, while still producing occasional revolts below that range.

**Administrative revolt chain.** When the admin revolt roll fires, it spawns a separatist movement event chain of **variable length** (3–8 ticks, rolled at spawn time). Shorter chains represent swift coups; longer chains represent political secessions that build over months. The chain length is determined at ignition and sets the pacing of intermediate events:

- **Short chain (3–4 ticks):** Separatist Movement → Military Defection → Breakaway. Fast coup. Almost no time to respond.
- **Medium chain (5–6 ticks):** Separatist Movement → Political Crisis → Military Defection → Breakaway. Some warning, narrow response window.
- **Long chain (7–8 ticks):** Separatist Movement → Political Crisis → Popular Support Shifts → Military Defection → Breakaway. The slow version — still much faster than the tension revolt pipeline.

Each intermediate event applies field effects to the revolting region (tension spike, economy disruption, military split), so the region is degraded by the time it breaks away. **The chain is non-interruptible** — once an admin revolt fires, it always completes and produces a new independent faction. The owning faction cannot suppress it by reinforcing the region or improving conditions. This is the critical design distinction from tension revolts: tension revolts are disruptable (improve conditions before the follow-up's condition check, prune the chain). Admin revolts are institutional fractures — inevitable once they begin. The faction's only defense is not being too large, or getting lucky on the per-tick roll.

**Breakaway faction from admin revolt.** The chain's terminal event creates a new independent faction holding the revolting region. The new faction spawns with zero budget. The region keeps its current field values minus whatever the chain events degraded. The new faction's archetype is rolled from the archetype pool. The former owner loses the region and all its economic contribution immediately. The loss reduces the former owner's territory count by one, which slightly reduces admin revolt pressure on its remaining regions — a natural self-correcting dynamic where losing territory to secession makes the remaining empire slightly more stable.

**Coexistence with tension revolts.** Administrative revolts and tension-triggered revolts are independent systems that coexist. A large, high-tension empire gets hit by both — tension revolts in stressed regions and admin revolts everywhere. They represent different failure modes (popular unrest vs. institutional fracture) that share the same consequence: new factions appearing on the map. A large faction in crisis can cascade rapidly as both systems fire simultaneously, producing the dramatic civilizational collapse the bible's pacing model requires.

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

Economy is the primary driver — a faction with a healthy economy advances; a faction with ruined economy stagnates. Population acts as a secondary scaling factor, but the floor (config value, e.g. 0.3) ensures that a faction with depleted population but strong economy still advances, just more slowly. This prevents the scenario where a post-plague or post-conquest faction is permanently stuck at low tech because both economy and population are suppressed simultaneously. The averages are computed across all owned regions. The `base_tech_rate` is a config value tuned so that tech growth is gradual — technology is a slow-moving civilizational attribute, not a per-tick resource race.

**Tech convergence in cooperative peace — best-partner-only.** Factions in a cooperative diplomatic relationship benefit from technology sharing. The lower-tech faction gains additional tech_level growth per tick based on the gap between its tech_level and its **single highest-tech cooperative partner's** tech_level:

```
tech_sharing_bonus = convergence_rate * max(0, best_partner_tech - own_tech) / 100
```

Only the highest-tech cooperative partner contributes to convergence. Additional cooperative partners provide zero additional tech benefit — their value is purely economic (adjacency bonus sharing, border friction removal). This completely prevents "peace coalition" snowballing where a cluster of cooperative factions accelerates away from isolated factions technologically. The `convergence_rate` is a config value tuned so that tech sharing provides a meaningful but not dominant growth boost — a faction at peace with an advanced neighbor should noticeably close the gap over hundreds of ticks, but should not catch up entirely through sharing alone. The advanced faction receives no tech benefit from the partnership — its incentive for cooperation is the economic adjacency bonus and border friction removal.

**Multiplier magnitude — ~20% total budget, asymmetrically distributed.** Each archetype has a total tech multiplier budget of approximately 20% at maximum tech_level (tech 100 vs. tech 0). The budget is distributed across the archetype's favored axes according to its strategic identity. A Conqueror might allocate most of its 20% to attack efficiency with a sliver to economic growth. A Fortifier might split roughly evenly across defense efficiency and economic growth with a small attack allocation. The player's civilization has a balanced distribution.

At tech_level 0, all multipliers are 1.0 (baseline). At tech_level 100, the archetype's favored axis reaches approximately 1.18–1.20× while less-favored axes reach 1.02–1.05×. The multipliers scale linearly with tech_level — a faction at tech 50 gets roughly half the maximum benefit.

The ~20% budget target is calibrated to produce a meaningful but not dominant advantage — roughly equivalent to a 60/40 edge in an otherwise-even engagement before the stochastic modifier is applied. Tech advantage should be one significant factor among several (budget, military strength, positioning, archetype matchup), not the deciding factor on its own. A faction with a large tech advantage that overextends or mismanages its budget still loses. The same tech multipliers feed both the simulation's attack resolution formula and the tactical layer's unit stat generation, ensuring the player experiences the same tech edge the simulation calculates.

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

### Stage 3 Tuning Observations

These observations emerged from running the simulation at 4-faction scale (500 ticks, 5 seeds) during Stage 3 tuning. They document known behavioral patterns and their implications for later stages. None are bugs — they are characteristics of the current mechanical design that should be monitored as later systems come online.

**Observation: Factions with strong economy tend to dominate.** A faction with a highly developed region (economy 60+) generates substantially more budget than factions with only undeveloped regions (economy 25–50). Over hundreds of ticks, the budget advantage compounds: more budget → more attacks → territory gains → more economy → more budget. The tech system will amplify this (economy drives tech growth, tech multipliers improve attack efficiency). Existing counter-pressures include: conquest consequence chains (conquered territory is unstable), overextension penalties (maintaining devastated territory is costly), the revolt/breakaway system (high-tension regions may splinter), and the **administrative revolt system** (quadratic scaling with territory count guarantees that large empires hemorrhage territory regardless of tension management — see "Administrative revolt system" in the Simulation Backbone). The mission generator and player-facing systems should also be evaluated against this pattern — a dominant faction produces fewer mission hooks and less chronicle material during time jumps.

**Observation: Low-economy factions can become functionally inert.** Factions with net economy barely above maintenance threshold generate minimal budget surplus. If reinforce spending consumes most of this income, the faction never accumulates enough for offensive action. The shortfall model limits reinforce drain, but a faction with only undeveloped regions and no economic advantage may still struggle to reach attack viability within 500 ticks. The diplomacy system's cooperative mechanics (adjacency bonus sharing, tech convergence) are the designed escape hatch, but only if the faction can sustain the stability needed for peace formation. Worth monitoring whether the budget growth formula needs a minimum growth floor or whether maintenance cost should scale with economy rather than being flat.

**Observation: Attack timing is regular when conditions are stable.** When a faction's territory, economy, and borders don't change, its attack cadence becomes metronomic — same accumulation time, same commit amount, same cycle. This is expected in a two-faction stalemate but would produce repetitive chronicle material during time jumps. The diplomacy system (peace formation, betrayal) introduces timing disruption. Decision noise (small random perturbation on action scores or probability-weighted selection instead of argmax) is a noted future consideration (see "random hyper-focus" in the antagonist system section) that would add further timing variation.
