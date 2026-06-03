# Stage 0 — Simulation Core (Prove the World Lives)

## Goal

Prove that the simulation can generate a galaxy, run ticks, fire events, advance the antagonist, and produce meaningful state changes over hundreds of ticks. Python only. Console output. No Godot, no UI, no WebSocket.

## Context

**Read before starting:**
- `game_bible.md` — "The Simulation Backbone" section (architecture, region state model, drift formulas, event chains, antagonist agent, tick resolution sequence), "The Galaxy" section (galaxy generation, inter-region topology), and "Stage 0 — Simulation Core" subsection (development approach)
- `dev_rules.md` — all five development principles, stage spec format, rules for Claude Code sessions

**Design references within the bible (do NOT restate here — read the bible):**
- Region state model: 4 granular fields, 2 composite axes, derivation formulas
- Passive drift: all 4 field drift formulas with full equations
- Event chain architecture: template schema, chain spawns, delays, conditions
- Event collision resolution: simultaneous application, mutual exclusion tags
- Event probability: threshold triggers with per-region noise offsets
- Tick resolution sequence: 6-step order
- Antagonist agent: resource budget, attractiveness scoring, proportional distribution
- Galaxy generation: tiered templates (isolated start first)
- Inter-region topology: typed adjacency graph (untyped first)

**Builds on:** Nothing. This is the first stage. New project, fresh codebase.

**Repo strategy:** This is a new project. The old repo is preserved as reference. During this stage, Claude Code evaluates the existing simulation files (`vector_engine.py`, `region_model.py`, `world_state.py`, `config.py`, `antagonist_agent.py`, `coherence_ledger.py`, `template_assembler.py`) against the new design and decides what to copy, adapt, or rewrite. The decision is made with the code open, not speculatively.

---

## Development Methodology

This stage builds a complex system through **small, sequential, provable increments**. Each step adds exactly one thing. After each step, the system is run and the output is verified. If the output is wrong, the cause is the thing that was just added — nothing else changed. This is the only acceptable way to build the simulation.

### The Rules

1. **One system at a time.** Implement one module, test it in isolation, confirm it works. Do not start the next module until the current one is proven.
2. **Each step has expected output.** Before writing code, know what the console output should look like when it works. After writing code, run it and compare.
3. **If the output is wrong, fix it before moving on.** Do not pile the next step on top of broken output. Understand why it's wrong. The only new variable is the thing you just added.
4. **Integration is a separate, deliberate step.** Building module A and building module B are separate steps. Wiring A into B is a third step. Each is proven independently.
5. **All tuning values live in config.** Every coefficient, threshold, weight, penalty, rate, range, and scaling factor is a named value in `config.py`. Nothing is hardcoded in the formulas. This is non-negotiable.
6. **Dead code gets deleted.** If something is written and turns out to be unnecessary, remove it. Do not comment it out.
7. **Document interfaces, not internals.** Every module documents its input shape and output shape at the top of the file. Internal logic is readable code, not comment-heavy prose.
8. **Baby steps.** If a step feels like it needs 200+ lines across multiple files, it's too big. Break it down further.

### The Incremental Build Order

The simulation is built in the following order. Each numbered step is a single provable increment. Steps within a group must be completed in order. The group order is mandatory. Do not skip ahead.

**The "prove it" test for every step:** Run the test script, read the console output, verify the numbers make sense. "Make sense" means: fields move in the directions the formulas predict, values stay in bounds, the system doesn't explode or flatline.

---

## Build Steps

### Group A — Region State (Prove a region exists and has state)

**Step A1: Config foundation.**
Create `config.py` with all tuning values for the region state model. This includes: initial field values for each region tier (home, frontier), composite axis weights and thresholds, penalty multipliers. All values are named constants with comments explaining what they control. No logic — just values.
- **Prove:** File exists, imports cleanly, values are accessible.

**Step A2: Region model.**
Create `region.py`. A Region holds four granular fields (military, economy, tension, population) and two composite axes (stability, capacity). Implements `recompute_composites()` using the weighted-average-with-threshold-penalties formula from the bible. All weights, thresholds, and penalties read from config.
- **Prove:** Create a Region with known field values, call `recompute_composites()`, verify the composite values match hand-calculated expected results. Print the region state. Test with values above and below threshold boundaries to verify penalty application.

**Step A3: Galaxy generation — isolated start template.**
Create `galaxy.py`. Implements the "isolated start" template: 1 home region, 2 frontier regions, 4–6 empty regions. Each region gets field values randomized within config ranges for its tier. Regions are stored in a dict keyed by region ID. Empty regions exist in the graph but have no field state (they're placeholders for future expansion).
- **Prove:** Generate a galaxy, print all region states. Verify home region has higher stats than frontiers. Verify empty regions exist but are inert. Run it multiple times — verify randomization produces different values within expected ranges.

**Step A4: Adjacency graph — untyped.**
Add an adjacency list to the galaxy. The isolated start template defines which regions are adjacent. At this step, all edges are untyped ("both"). The galaxy exposes a method to query a region's neighbors.
- **Prove:** Generate a galaxy, print the adjacency list. Verify home is adjacent to both frontiers. Verify frontiers are adjacent to some empty regions. Verify the graph matches the template's intended topology.

### Group B — Passive Drift (Prove the world changes on its own)

**Step B1: Military strength drift.**
Create `drift.py`. Implements the military strength drift formula from the bible. Takes a region's current field values, returns the military drift delta. Reads decay_rate from config.
- **Prove:** Call with known inputs (e.g., military=50, economy=80), verify the delta matches hand-calculation. Test edge cases: economy=0 (maximum decay), economy=100 (no decay), military=0 (no decay because nothing to maintain).

**Step B2: Economic output drift.**
Add economic output drift to `drift.py`. Takes region fields, returns economy drift delta. Reads base_growth and tension_penalty_rate from config.
- **Prove:** Test with known inputs. Verify growth with low tension, drag with high tension, population scaling. Edge cases: population=0, tension=100, tension=0.

**Step B3: Factional tension drift.**
Add factional tension drift. Two growth sources (prosperity pressure, stress pressure), one natural decay. Reads prosperity_tension_rate, stress_tension_rate, stress_threshold, natural_decay from config. Note: stress_pressure uses the stability composite, so this formula depends on composites being computed.
- **Prove:** Test with known inputs covering all three terms. Verify prosperity pressure activates with high population + high economy. Verify stress pressure activates with low stability. Verify natural decay pulls tension down in quiet conditions.

**Step B4: Population drift.**
Add population drift. Logistic growth above subsistence, proportional decline below. Reads growth_rate, subsistence_threshold, decline_rate from config.
- **Prove:** Test growth above subsistence (verify logistic shape — fast when low, slow near capacity). Test decline below subsistence (proportional to deficit). Edge cases: population near 0, population near 100, economy exactly at subsistence.

**Step B5: Apply all drift to a region for one tick.**
Add `apply_drift(region)` function that computes all four deltas and applies them (clamped 0–100), then recomputes composites.
- **Prove:** Start a region at known values, apply drift for 1 tick, verify all four fields moved in expected directions. Apply for 10 ticks in a loop, print state each tick. Verify trends: a healthy region stays healthy and slowly grows. An unhealthy region spirals. Fields stay in 0–100 bounds.

**Step B6: Apply drift across the full galaxy for multiple ticks.**
Wire `apply_drift` into a tick loop that processes all inhabited regions. Run the isolated start galaxy forward 50 ticks with drift only (no events, no antagonist).
- **Prove:** Print a tick-by-tick summary of all regions. Verify: home region is stable or slowly growing. Frontier regions are struggling or slowly declining depending on starting values. No fields hit NaN, no infinite loops, no explosions. The galaxy's trajectory over 50 ticks tells a readable story — you can see which regions are thriving and which are struggling.

### Group C — Event System (Prove things happen)

**Step C1: Event template schema.**
Create `events.py`. Define the event template data structure: ID, name, trigger field, trigger threshold, immediate effects (dict of field deltas), chain spawns (list of {template_id, delay_range, probability, conditions}), chain tags, mutual exclusion tags, significance tier (1–5). Create 5–8 simple test templates by hand (not from the old library yet): a tension-triggered revolt, a military-triggered garrison collapse, an economy-triggered trade boom, etc. Templates are plain dicts or dataclasses.
- **Prove:** Templates load and are queryable by ID. Print all templates and verify their structure is complete.

**Step C2: Threshold trigger evaluation.**
Add a function that takes a region's current fields and the event template table, and returns which event templates have their threshold crossed. Implement per-region noise offsets: each region gets a random offset per template, rolled once and stored.
- **Prove:** Set up a region with military=20 and a template that triggers at military<25. Verify it triggers. Change military to 30, verify it doesn't. Test with noise offsets — verify the effective threshold shifts within the expected range. Run the same region against all 5–8 templates, verify only the expected ones trigger.

**Step C3: Event firing and state application.**
Add a function that fires an event: applies its immediate effects to the region (field deltas), returns the chain spawns to be queued. Field changes are applied as direct additions, clamped 0–100.
- **Prove:** Fire a known event on a region with known state. Verify field values change by the expected amounts. Verify chain spawns are returned with correct delay ranges and probabilities.

**Step C4: Pending event queue.**
Create the pending event queue. It holds scheduled events: {template_id, region_id, due_tick, probability, conditions, chain_tag}. Add functions to enqueue events, query events due on a given tick, and remove events after processing.
- **Prove:** Enqueue 3 events with different due ticks. Query tick 5 — verify only the events due on tick 5 are returned. Process them — verify they're removed from the queue.

**Step C5: Pending event resolution.**
Add the full pending event resolution logic: for each event due this tick, check its conditions against the region's current state. If conditions are met, roll against its firing probability. If it fires, apply effects and enqueue its own chain spawns. If conditions are not met or the roll fails, the event expires (chain branch dies).
- **Prove:** Set up a pending event with conditions (e.g., "factional_tension > 60"). Test with a region where the condition is met — verify the roll happens. Test where the condition is not met — verify the event is skipped. Test a chain: fire an event that spawns a follow-up, advance ticks until the follow-up is due, verify it resolves correctly.

**Step C6: Event collision resolution.**
Add simultaneous resolution: when multiple events fire on the same tick in the same region, all read the region's state at tick start, all compute deltas independently, all deltas are summed and applied at once. Add mutual exclusion check: if two events on the same tick share a mutual exclusion tag, the one with higher probability wins, the other is delayed 1–2 ticks.
- **Prove:** Fire two non-exclusive events simultaneously on a region. Verify both deltas apply (sum, not sequential). Fire two mutually exclusive events. Verify the higher-probability one fires and the other is pushed back. Verify the pushed-back event appears in the queue at the correct later tick.

**Step C7: Fresh triggers + pending queue in a tick loop.**
Wire both trigger evaluation (Step C2) and pending event resolution (Step C5) into the tick loop alongside drift. The tick now does: process pending events → evaluate fresh triggers → apply drift → recompute composites. (Antagonist is not yet included — that's Group D.)
- **Prove:** Run the galaxy forward 100 ticks with drift AND events. Print a per-tick event log: which events fired, in which regions, what field changes resulted, what follow-ups were scheduled. Verify: events trigger when fields cross thresholds. Chains propagate — a revolt spawns follow-up events that fire on later ticks. The galaxy's story over 100 ticks has dramatic moments interspersed with gradual drift. Fields stay in bounds. No orphaned events in the queue (events that were scheduled but whose conditions are impossible should expire, not accumulate forever).

### Group D — Antagonist Agent (Prove the threat exists)

**Step D1: Antagonist state and budget.**
Create `antagonist.py`. The antagonist has: an archetype tag (e.g., "conqueror"), a resource budget (starts at 0, grows per tick), and a growth rate curve (config values). Implement budget growth per tick.
- **Prove:** Create an antagonist, advance 50 ticks, print the budget each tick. Verify it grows along the expected curve. Verify it starts at 0 (or near 0) and increases.

**Step D2: Attractiveness scoring.**
Add attractiveness scoring. Implement one archetype's scoring function (the Conqueror — scores by low military strength). Takes a region's state, returns an attractiveness score. The function is keyed by archetype so additional archetypes can be added later.
- **Prove:** Score three regions with different military values. Verify the lowest-military region scores highest. Verify a region with military=100 scores near 0.

**Step D3: Budget distribution.**
Add proportional budget distribution across regions based on attractiveness scores. Output: a dict of {region_id: allocated_pressure} that sums to the total budget.
- **Prove:** With three regions of varying attractiveness and a budget of 10, verify the distribution is proportional. Verify the sum equals the budget. Test edge case: all regions have equal attractiveness — budget should split evenly. Test edge case: one region has all the attractiveness — budget should concentrate there.

**Step D4: Pressure application.**
Add per-tick field drain from allocated pressure. The drain reduces relevant fields (for the Conqueror: primarily military, secondarily economy) scaled by the pressure amount. Drain rates are config values.
- **Prove:** Apply pressure=5 to a region for 1 tick. Verify the expected fields decrease by the expected amounts. Apply for 10 ticks, verify cumulative drain. Verify the antagonist feels like a targeted threat — the weakest region gets weaker while strong regions are relatively untouched.

**Step D5: Wire antagonist into the tick loop.**
Insert the antagonist's action step into the tick resolution sequence between fresh event triggers and passive drift (step 3 of the 6-step sequence from the bible). The tick now does: pending events → fresh triggers → antagonist → drift → composites → log.
- **Prove:** Run the galaxy forward 200 ticks with drift, events, AND the antagonist. Print a per-tick summary including antagonist budget, allocation, and pressure applied per region. Verify: early ticks have low/no antagonist activity. As the budget grows, pressure increases. The antagonist concentrates on weak regions. Regions under pressure deteriorate faster. Events triggered by the deterioration (low military → garrison collapse, high tension → revolt) should fire in response. The galaxy's 200-tick story should have a visible arc: early stability → growing external pressure → cascade of crises in weak regions.

### Group E — Coherence Ledger (Prove history is recorded)

**Step E1: Event log.**
Create `coherence_ledger.py`. The ledger is an append-only log of events. Each entry records: tick number, region ID, event template ID, event name, field deltas applied, chain tag, and any chain spawn references. Add a method to log an event and a method to query events by region, by chain tag, or by tick range.
- **Prove:** Run the simulation 50 ticks. Query the ledger for all events in region 0. Verify they match what the event system reported. Query by chain tag — verify a complete chain is retrievable (the initial trigger and all its follow-ups). Query by tick range — verify correct filtering.

**Step E2: Antagonist action logging.**
Add antagonist action entries to the ledger: tick, budget, per-region allocation, pressure applied.
- **Prove:** Run 50 ticks, query antagonist actions from the ledger. Verify they match the antagonist's actual behavior each tick.

**Step E3: Tick state snapshots.**
Add per-tick state snapshots: after each tick completes, log the full state of all regions (field values + composite axes). This is the raw material the chronicle distiller will eventually consume.
- **Prove:** Run 50 ticks, retrieve the snapshot for tick 25. Verify all region states match expectations. Verify the snapshot at tick 50 reflects the cumulative effects of 50 ticks of drift, events, and antagonist.

### Group F — Typed Adjacency (Prove topology matters)

> **Only begin this group after Groups A–E are fully proven and Westley is satisfied with the simulation's behavior on untyped adjacency.** If the simulation already produces interesting behavior without edge types, discuss with Westley before adding this complexity.

**Step F1: Add edge types.**
Modify the adjacency graph to support typed edges (border, trade_route, both). Update the isolated start template to assign edge types. The home region's connections to frontiers are "both." Connections between frontiers and empty regions are "border" only (military frontier, no established trade).
- **Prove:** Print the typed adjacency list. Verify types match the template intent.

**Step F2: Add neighbor-influenced drift.**
Modify passive drift to include a neighbor influence term. Economic drift gets a small bonus from trade-route-connected neighbors with high economy (trade benefit). Military drift gets a small penalty if border-connected neighbors have very low military (threat contagion). Influence scales by a config multiplier.
- **Prove:** Run two scenarios side by side — one with a frontier connected only by border (no trade benefit), one connected by "both" (gets trade benefit). Verify economic trajectories diverge as expected. If the divergence is trivially small, the feature isn't worth keeping — flag for Westley.

**Step F3: Antagonist spread through borders.**
Modify antagonist pressure to only spread through border-connected regions. A region that is trade-connected but not border-connected to an antagonist-pressured neighbor doesn't receive military pressure (but could lose economic output if the trade route is to a collapsing region).
- **Prove:** Set up a scenario where one region is border-connected and another is only trade-connected to an antagonist-targeted region. Run 100 ticks. Verify the border-connected region receives pressure and the trade-connected one doesn't (militarily). Verify the trade-connected one still suffers economically if its trade partner declines.

### Group G — Additional Galaxy Templates (Prove variety works)

> **Only begin this group after Groups A–F are proven.** Each template is a standalone addition — if it produces uninteresting behavior, it can be cut.

**Step G1: Twin colony template.**
Add the twin colony template to galaxy generation. Two home regions, 1–2 frontiers each, empty space between.
- **Prove:** Generate and run 200 ticks. Print the trajectory. Verify the two home regions develop independently, with interaction along their shared connections. The story should feel different from isolated start — competition or cooperation between the two cores.

**Step G2: Archipelago template.**
Add the archipelago template. One home region, 3 frontier regions with sparse connections.
- **Prove:** Generate and run 200 ticks. Verify the disconnected topology produces different behavior — isolated regions that can't easily support each other, higher vulnerability to localized antagonist pressure.

### Group H — Full Integration Test (Prove the world lives)

**Step H1: The 500-tick test.**
Run the full simulation (drift, events, antagonist, typed adjacency, coherence ledger) for 500 ticks on the isolated start template. Print a comprehensive summary:
- Per-region field trajectories (start → end, with min/max over the run)
- Total events fired, by type
- Antagonist budget growth and final allocation
- Longest event chain (from initial trigger to final resolution)
- Any regions that hit field extremes (0 or 100 on any field)
- Coherence ledger entry count

**Prove:** The output tells a readable story. Regions that started healthy may have declined under pressure. Regions that started weak may have collapsed or stabilized depending on events. The antagonist's influence is visible in the trajectories. Event chains produced multi-step causal stories. The simulation didn't explode, flatline, or produce nonsensical values. **Westley reads the output and says "yes, this world is alive."**

**Step H2: Multi-template comparison.**
Run the same 500-tick test on all three templates. Compare the trajectories.
- **Prove:** Each template produces a meaningfully different story. Isolated start, twin colony, and archipelago all feel like different galaxies with different strategic situations. If two templates produce nearly identical behavior, one of them isn't earning its existence — flag for review.

**Step H3: Stochastic consistency test.**
Run the isolated start template 5 times with different random seeds. Compare trajectories across runs.
- **Prove:** No two runs are identical (genuine stochasticity). But all runs are plausible — no run produces obviously broken behavior (a field jumping from 10 to 90 in one tick, all regions collapsing simultaneously on tick 3, etc.). The range of outcomes demonstrates that the simulation is genuinely uncertain, not deterministic with cosmetic noise.

---

## What to Build

Concrete list of files, in the order they're needed:

| File | Purpose | Created in Step |
|------|---------|-----------------|
| `config.py` | All tuning values. Central authority for every coefficient, threshold, weight, and rate. | A1 |
| `region.py` | Region data model. Four fields, two composites, recomputation. | A2 |
| `galaxy.py` | Galaxy generation. Templates, adjacency graph, region container. | A3–A4, F1, G1–G2 |
| `drift.py` | Passive drift formulas. Four field drift functions plus `apply_drift`. | B1–B5 |
| `events.py` | Event system. Templates, trigger evaluation, firing, collision resolution, pending queue. | C1–C6 |
| `antagonist.py` | Antagonist agent. Budget growth, attractiveness scoring, distribution, pressure application. | D1–D4 |
| `coherence_ledger.py` | Event log, antagonist log, state snapshots. Append-only with query methods. | E1–E3 |
| `tick.py` | Tick loop. Orchestrates the 6-step resolution sequence. Calls into all other modules. | B6, C7, D5 |
| `test_stage_0.py` | Test script for the full integration test (Group H). | H1–H3 |

Additional test files are created as needed for per-module testing during earlier steps. These are lightweight scripts, not a test framework.

---

## Input/Output Shapes

**Region state (the core data structure everything reads and writes):**
```python
{
    "id": "region_0",
    "name": "Heartworld",
    "tier": "home",  # home, frontier, empty
    "fields": {
        "military": 65.0,
        "economy": 70.0,
        "tension": 15.0,
        "population": 50.0
    },
    "composites": {
        "stability": 72.3,
        "capacity": 61.8
    }
}
```

**Event template:**
```python
{
    "id": "evt_revolt",
    "name": "Regional Revolt",
    "trigger_field": "tension",
    "trigger_threshold": 60,  # fires when tension crosses above this
    "trigger_direction": "above",  # "above" or "below"
    "immediate_effects": {"military": -10, "tension": +15, "economy": -5},
    "chain_spawns": [
        {
            "template_id": "evt_revolt_crushed",
            "delay_range": [3, 8],
            "probability": 0.4,
            "conditions": {"military": {"above": 40}}
        },
        {
            "template_id": "evt_revolt_succeeds",
            "delay_range": [5, 12],
            "probability": 0.3,
            "conditions": {"tension": {"above": 70}}
        }
    ],
    "chain_tags": ["political_unrest"],
    "exclusion_tags": ["political_resolution"],
    "significance_tier": 4
}
```

**Pending event queue entry:**
```python
{
    "template_id": "evt_revolt_crushed",
    "region_id": "region_1",
    "due_tick": 47,
    "probability": 0.4,
    "conditions": {"military": {"above": 40}},
    "chain_tag": "political_unrest_region_1_tick_42"
}
```

**Antagonist state:**
```python
{
    "archetype": "conqueror",
    "budget": 3.7,
    "allocation": {
        "region_0": 0.5,
        "region_1": 2.4,
        "region_2": 0.8
    }
}
```

**Coherence ledger entry (event):**
```python
{
    "type": "event",
    "tick": 42,
    "region_id": "region_1",
    "template_id": "evt_revolt",
    "event_name": "Regional Revolt",
    "field_deltas": {"military": -10, "tension": +15, "economy": -5},
    "chain_tag": "political_unrest_region_1_tick_42",
    "spawned": ["evt_revolt_crushed@tick_47", "evt_revolt_succeeds@tick_52"]
}
```

**Coherence ledger entry (antagonist):**
```python
{
    "type": "antagonist",
    "tick": 42,
    "budget": 3.7,
    "allocation": {"region_0": 0.5, "region_1": 2.4, "region_2": 0.8},
    "pressure_applied": {"region_1": {"military": -1.2, "economy": -0.6}}
}
```

**Coherence ledger entry (state snapshot):**
```python
{
    "type": "snapshot",
    "tick": 42,
    "regions": {
        "region_0": {"fields": {...}, "composites": {...}},
        "region_1": {"fields": {...}, "composites": {...}},
        ...
    }
}
```

---

## Integration Points

**This is Stage 0. There are no previous stages to integrate with.**

All modules in this stage are integrated with each other through the tick loop (`tick.py`), which orchestrates the 6-step resolution sequence. The integration is additive:

- `tick.py` calls `events.py` (pending queue processing + fresh trigger evaluation)
- `tick.py` calls `antagonist.py` (agent action)
- `tick.py` calls `drift.py` (passive drift application)
- `tick.py` calls `region.py` (composite recomputation)
- `tick.py` calls `coherence_ledger.py` (logging)

Each module is independently testable with mock inputs. The tick loop is the only place they come together.

**Config flags:**
- `config.ENABLE_EVENTS` — if False, tick loop skips event processing. Drift and composites still run.
- `config.ENABLE_ANTAGONIST` — if False, tick loop skips antagonist step. Events and drift still run.
- `config.ENABLE_TYPED_EDGES` — if False, all edges are treated as "both" regardless of template. Simplifies to untyped adjacency.
- `config.ENABLE_NEIGHBOR_DRIFT` — if False, drift formulas ignore neighbor influence. Each region drifts in isolation.

Default state for all flags: ON once their respective group is proven. OFF during earlier groups when the system doesn't exist yet.

---

## Future Stage Dependencies — Design Awareness

The following capabilities are **not built in Stage 0** but will be needed by later stages. They are listed here so that Stage 0's data structures are designed to be extensible in these directions. No implementation work — just don't paint yourself into a corner.

**Civilization-wide aggregates (needed by Stage 2+).** The mission generator's asset allocation and difficulty scaling need to know "how rich/strong is the civilization overall" — total economy, total military capacity, total population across all regions. This is trivially computed by summing region fields, but the concept doesn't exist as a formal query yet. When building the galaxy and region modules, ensure it's easy to aggregate across all inhabited regions.

**Tech level / era tracking (needed by Stage 4+).** The bible describes technology advancing and regressing, eras changing what ships are available, and technology loss events in the late era. There is no tech level field in the current simulation. The bible says eras emerge from simulation state (number of regions, factional divergence, antagonist presence), but downstream systems (ship variety, asset types, era scaling) will need some way to ask "what tech era is this civilization in?" This might be a composite axis derived from existing fields, a standalone tracked value, or a heuristic query — to be designed when those stages approach. Ensure the region and galaxy data models can accommodate a new field or composite without restructuring.

**Faction entities (needed by Stage 4+).** The bible describes breakaway factions from successful revolts that persist across chapters and evolve — they become entities the player contends with, not just field value changes. The current simulation models revolts as events that change field values, but has no concept of a faction as a persistent entity with its own state. When building the coherence ledger and galaxy model, ensure there's room to add a faction registry later — a list of named entities with region affiliations, attitudes, and histories, queryable by the character selector and mission generator.

**Lineage tracking in the coherence ledger (needed by Stage 3).** The chronicle distiller's lineage-first clustering and the character selector both need to know where lineage members live. The Stage 0 coherence ledger logs events and state snapshots but doesn't track individual people. The ledger's append-only, typed-entry design supports adding a "lineage_member" entry type later without restructuring. Just ensure the ledger isn't built in a way that assumes all entries are events.

**Expansion events (needed by Stage 2+).** The bible says the civilization starts small and expands through expansion events — new regions activate and adjacency edges form. The event chain architecture supports this (an event's immediate effects could activate an empty region and add edges), but no expansion event templates are authored in Stage 0's hand-built test set. The galaxy model should support adding regions and edges at runtime, not just at generation time.

---

## Done Condition

**The simulation passes all three tests in Group H:**

1. **500-tick test (H1):** The isolated start galaxy runs 500 ticks and produces a readable story. Regions diverge meaningfully. Events fire and chain. The antagonist escalates. Fields stay in bounds. The coherence ledger captures everything.

2. **Multi-template comparison (H2):** All three templates (isolated, twin colony, archipelago) produce meaningfully different 500-tick trajectories. Each galaxy feels like a different strategic situation.

3. **Stochastic consistency test (H3):** Five runs on the same template with different seeds produce five different but plausible stories. No degenerate runs. Genuine uncertainty.

**Westley reads the output of all three tests and says: "Yes, this world is alive." That is the gate. Nothing else counts.**

---

## Files Created

*Filled in after implementation.*

| File | Purpose | Lines | Status |
|------|---------|-------|--------|
| | | | |
