# Stage 2 — Event Chain Architecture

## Goal
Prove that events fire on threshold crossings, chain through follow-up events, resolve mutual exclusions correctly, and compound when simultaneous — using 10 hand-authored test templates that exercise every behavior the event system needs.

## Context
**Read in game_bible.md (v1.08):** "The Simulation Backbone" section, specifically:
- Event Chain Architecture (chain spawns, delay resolution, chain tags, condition checks)
- Event Collision Resolution (simultaneous delta application, mutual exclusion tags)
- Event Probability — Threshold Triggers with Noise (threshold direction, edge detection, deterministic triggers vs. probabilistic queue events, noise offsets)
- Tick Resolution Sequence (steps 1 and 2 are event-relevant; steps 3–7 are NOT part of Stage 2)

**Era-agnostic naming:** The bible's event section examples use themed placeholder names (e.g., "Factional Tension Rising," "Regional Revolt," "Garrison Vulnerable") for readability. Per Sacred Design Principle #3, the engine uses abstract mechanical vocabulary only. The template names defined in this spec (e.g., "Tension Threshold Breach," "Tension Crisis Escalation," "Military Threshold Breach") are authoritative for implementation. Do not use the bible's illustrative names in code, config, or log output.

**Builds on:** Stage 1 (world graph, multi-region drift with oscillation, adjacency bonus). Stage 2 reads region state produced by Stage 1's drift system and applies event effects on top of it.

**What Stage 2 does NOT include:** Faction agents (Stage 3), border friction (Stage 3), conquest events (Stage 3), coherence ledger (Stage 4). The event log produced here is a simple structured list, not the full ledger.

## What to Build

### Files to create:

**`event_templates.py`** — The 10 hand-authored test event templates as data structures. Each template defines: ID, name, trigger (field, threshold, direction, noise range) or None for chain-only templates, immediate effects (field deltas dict), chain spawns list (each with target template ID, delay range, probability, conditions), mutual exclusion tags list, and a narrative category tag.

**`event_engine.py`** — The core event processing system. Contains:
- Threshold trigger evaluator (edge detection, noise offsets, direction-aware)
- Pending event queue (insert, check due events, remove)
- Condition checker (evaluates a condition against current region state)
- Chain spawn roller (triangular delay distribution, queue insertion)
- Mutual exclusion resolver (tag comparison, probability tiebreak, coin flip on equal probability, loser pushed back 1–2 ticks)
- Collision resolver (snapshot start-of-tick state, compute all deltas independently, sum and apply)
- Economy floor clamp (applied unconditionally after all event deltas)
- Event logger (structured list of fired events with chain tags, causal links, pruned branches)

**`test_stage2.py`** — Test harness that generates a world from Stage 1's isolated start template, runs the simulation forward with events enabled, and prints the event log with chain tags and causal links. Includes targeted sub-tests for each behavior.

**Config additions to `config.py`** — New config values for Stage 2 (event noise range already exists as `EVENT_NOISE_RANGE = 10.0`). Feature flag: `ENABLE_EVENTS_STAGE2 = True`.

## Input/Output Shapes

### Event Template (data structure in event_templates.py):
```python
{
    "id": "T1",
    "name": "Tension Threshold Breach",
    "trigger": {
        "field": "tension",          # which granular field to watch
        "threshold": 55.0,           # base threshold before noise
        "direction": "above",        # "above" or "below"
        "noise_range": 10.0          # per-region offset in [-noise, +noise]
    },
    # trigger is None for chain-spawn-only templates (T2, T3, E2, E3, M2, X2)
    "effects": {
        "tension": +5.0
    },
    "chain_spawns": [
        {
            "template_id": "T2",
            "delay_range": (4, 10),      # triangular distribution, center-weighted
            "probability": 0.45,          # roll against this when tick arrives
            "conditions": [
                {"field": "tension", "operator": ">", "value": 58.0}
            ]
        },
        {
            "template_id": "T3",
            "delay_range": (6, 14),
            "probability": 0.35,
            "conditions": [
                {"field": "stability", "operator": ">", "value": 42.0}
            ]
        }
    ],
    "exclusion_tags": [],                # mutual exclusion tag strings
    "category": "tension"                # for logging/narrative grouping
}
```

### Pending Queue Entry (internal to event_engine.py):
```python
{
    "template_id": "T2",
    "region_id": "region_alpha",
    "scheduled_tick": 147,           # absolute tick number
    "chain_tag": "chain_0042",       # propagated from parent
    "parent_event_id": "evt_0039",   # for causal link tracking
    "probability": 0.45,
    "conditions": [
        {"field": "tension", "operator": ">", "value": 58.0}
    ]
}
```

### Fired Event Log Entry (output of event_engine.py):
```python
{
    "event_id": "evt_0041",
    "template_id": "T2",
    "template_name": "Tension Crisis Escalation",
    "region_id": "region_alpha",
    "tick": 147,
    "chain_tag": "chain_0042",
    "parent_event_id": "evt_0039",       # None for root threshold triggers
    "trigger_type": "chain_spawn",       # "threshold" or "chain_spawn"
    "effects_applied": {
        "tension": +7.0,
        "military": -4.0,
        "economy": -3.0
    },
    "field_state_before": {              # snapshot at start of tick
        "military": 32.0,
        "economy": 41.0,
        "tension": 62.0,
        "population": 55.0
    },
    "field_state_after": {               # after all simultaneous deltas applied
        "military": 28.0,
        "economy": 38.0,
        "tension": 69.0,
        "population": 55.0
    }
}
```

### Pruned Branch Log Entry:
```python
{
    "event_id": "evt_pruned_0043",
    "template_id": "T3",
    "template_name": "Tension Resolution",
    "region_id": "region_alpha",
    "tick": 155,
    "chain_tag": "chain_0042",
    "parent_event_id": "evt_0039",
    "reason": "condition_failed",        # or "probability_failed"
    "failed_condition": {"field": "stability", "operator": ">", "value": 42.0},
    "actual_value": 38.5
}
```

### Noise Offset Map (generated once per time jump):
```python
{
    ("region_alpha", "T1"): -3.7,    # region_alpha's T1 triggers at 55 + (-3.7) = 51.3
    ("region_alpha", "E1"): +6.2,    # region_alpha's E1 triggers at 30 + 6.2 = 36.2 (below direction)
    ("region_beta", "T1"):  +8.1,    # region_beta's T1 triggers at 55 + 8.1 = 63.1
    # ... one entry per (region, threshold-template) pair
}
```

## The 10 Test Event Templates

### Tension Family

**T1 — "Tension Threshold Breach"**
- Trigger: tension `above` 55, noise ±10
- Effects: tension +5
- Chain spawns: T2 (delay 4–10, prob 0.45, condition: tension > 58), T3 (delay 6–14, prob 0.35, condition: stability > 42)
- Exclusion tags: none
- Tests: above-direction threshold trigger, chain spawning with conditions

**T2 — "Tension Crisis Escalation"**
- Trigger: none (chain-spawn only, from T1 and X2)
- Effects: tension +7, military -4, economy -3
- Chain spawns: none
- Exclusion tags: `political_crisis`
- Tests: multi-field chain follow-up, mutual exclusion participant

**T3 — "Tension Resolution"**
- Trigger: none (chain-spawn only, from T1)
- Effects: tension -6
- Chain spawns: none
- Exclusion tags: `political_resolution`
- Tests: branch pruning target (stability > 42 often fails in stressed regions), mutual exclusion participant

**Mutual exclusion pair:** `political_crisis` (T2) vs `political_resolution` (T3)

### Economic Family

**E1 — "Economy Threshold Breach"**
- Trigger: economy `below` 30, noise ±10
- Effects: economy -3, tension +3
- Chain spawns: E2 (delay 5–12, prob 0.40, condition: economy < 25), E3 (delay 8–18, prob 0.30, condition: economy > 35)
- Exclusion tags: none
- Tests: below-direction threshold trigger, cross-field deltas

**E2 — "Economy Crisis Escalation"**
- Trigger: none (chain-spawn only, from E1)
- Effects: population -3, economy -4, tension +4
- Chain spawns: none
- Exclusion tags: `economic_collapse`
- Tests: major multi-field crisis, compounding collision candidate with T2

**E3 — "Economy Recovery"**
- Trigger: none (chain-spawn only, from E1)
- Effects: economy +5, tension -2
- Chain spawns: none
- Exclusion tags: `economic_recovery`
- Tests: branch pruning target (economy > 35 very hard to meet after E1 pushed it down)

**Mutual exclusion pair:** `economic_collapse` (E2) vs `economic_recovery` (E3)

### Military Family

**M1 — "Military Threshold Breach"**
- Trigger: military `below` 25, noise ±10
- Effects: military -3, tension +3
- Chain spawns: M2 (delay 3–8, prob 0.50, condition: military < 22)
- Exclusion tags: none
- Tests: below-direction threshold on military, military-domain chain

**M2 — "Military Crisis Escalation"**
- Trigger: none (chain-spawn only, from M1)
- Effects: military -6, economy -3, population -2
- Chain spawns: none
- Exclusion tags: none
- Tests: major crisis, compounding candidate, deep chain potential (T1→tension rise→triggers M1→M2)

### Cross-Domain Family

**X1 — "Population Threshold Breach"**
- Trigger: population `above` 75, noise ±10
- Effects: economy -3, tension +2
- Chain spawns: X2 (delay 6–15, prob 0.35, condition: tension > 50)
- Exclusion tags: none
- Tests: above-direction on population field, cross-domain cascade

**X2 — "Population Crisis Escalation"**
- Trigger: none (chain-spawn only, from X1)
- Effects: tension +6, economy -4, military -2
- Chain spawns: T2 (delay 3–7, prob 0.40, condition: tension > 60)
- Exclusion tags: `political_crisis`
- Tests: 3-deep chain (X1→X2→T2), cross-family chain spawn, shares exclusion tag with T2

### Chain Topology
```
T1 (tension > 55) ──→ T2 "Tension Crisis Escalation" [political_crisis]
                  └──→ T3 "Tension Resolution" [political_resolution]

E1 (economy < 30) ──→ E2 "Economy Crisis Escalation" [economic_collapse]
                  └──→ E3 "Economy Recovery" [economic_recovery]

M1 (military < 25) ──→ M2 "Military Crisis Escalation"

X1 (population > 75) ──→ X2 "Population Crisis Escalation" [political_crisis]
                                └──→ T2 "Tension Crisis Escalation" [political_crisis]
```

### Behavior Coverage Matrix
| Behavior | Tested By |
|----------|-----------|
| Threshold trigger, above direction | T1, X1 |
| Threshold trigger, below direction | E1, M1 |
| Edge detection (no re-fire while above) | T1 over sustained high tension |
| Edge detection re-fire (field drops and re-crosses) | T1 with oscillation |
| Chain spawn with conditions | T1→T2, T1→T3, E1→E2, E1→E3, M1→M2, X1→X2, X2→T2 |
| Branch pruning (condition fails) | T3 (stability check), E3 (economy check) |
| Probability roll on queue event | All chain spawns |
| Triangular delay distribution | All chain spawns (verify center-weighting over many runs) |
| Mutual exclusion resolution | T2 vs T3, E2 vs E3 |
| Mutual exclusion tie-breaking | E2 vs E3 (probabilities 0.40 vs 0.30 — not equal; force equal-prob test separately) |
| Simultaneous collision (compounding) | E2 + T2 on same tick, M2 + any |
| Cross-domain cascade | X1 (population) → economy/tension → may trigger T1 |
| 3-deep chain | X1 → X2 → T2 |
| Cross-family chain spawn | X2 spawns T2 |
| Economy floor enforcement | E1 + E2 on low-economy region |
| All four trigger fields | tension (T1), economy (E1), military (M1), population (X1) |
| Chain tag propagation | All chains — verify tag links parent to children to grandchildren |
| Multiple independent chains from same template | T1 fires, field drops, T1 fires again with new chain tag |

## Integration Points

**Reads from Stage 1:**
- Region state (military, economy, tension, population fields)
- World graph (to iterate over all regions)
- Composite axes (stability, capacity — used in event conditions)
- Oscillation state (events read the real oscillated field values, not de-oscillated trend values — events respond to the actual current state)

**Writes to Stage 1 regions:**
- Field deltas applied after event resolution
- Economy floor clamp applied after all deltas

**Does NOT touch:**
- Drift formulas (Stage 1 — unchanged)
- Faction agents (Stage 3)
- Border friction (Stage 3)
- Coherence ledger (Stage 4)

**Config flag:** `ENABLE_EVENTS_STAGE2`. When False, the tick loop skips steps 1 and 2 entirely and the simulation behaves identically to Stage 1. Default: True.

**Tick loop integration:** Stage 2 inserts two steps at the beginning of the existing tick loop:
1. Process pending event queue (new — Stage 2)
2. Evaluate fresh threshold triggers (new — Stage 2)
3. Apply passive drift (existing — Stage 1)
4. Recompute composite axes (existing — Stage 1)

Steps 3–7 from the bible's full tick sequence are NOT all present yet. Faction agents (step 3) and border friction (step 4) are Stage 3. The Stage 2 tick loop is: events → drift → composites → log.

## Build Order and Checkpoints

Each numbered step is a mandatory checkpoint. After completing each step, run the specified test, show the output to Westley, and **STOP. Do not continue to the next step until Westley approves.**

---

### A — Event Template Data Structure and Loader

**A1. Define the event template data structure and load all 10 templates.**
Create `event_templates.py` with all 10 templates as defined in this spec. Create a loader function that returns a dict keyed by template ID. Create a function that returns only the threshold-trigger templates (those with a non-None trigger).

**Test:** Print all 10 templates. Confirm each has the correct fields, chain spawn references are valid (target template IDs exist), and mutual exclusion tags are consistent (both sides of each pair are present). Print the threshold-trigger subset (should be T1, E1, M1, X1).

**🛑 CHECKPOINT A1 — STOP and show output to Westley.**

---

### B — Noise Offset Generation

**B1. Implement per-region noise offset generation.**
For each (region, threshold-template) pair, roll a random offset from a uniform distribution in [-noise_range, +noise_range] using the template's configured noise range. Store as a dict keyed by (region_id, template_id). Roll once per simulation run (simulating "per time jump" behavior). The noise offset is added to the template's base threshold to produce the effective threshold for that region.

**Test:** Generate a world from Stage 1's isolated start template. Roll noise offsets for all (region, threshold-template) pairs. Print the offset map. Confirm offsets are within ±10 of each template's base threshold. Confirm different regions get different offsets for the same template. Run twice with different seeds and confirm offsets change.

**🛑 CHECKPOINT B1 — STOP and show output to Westley.**

---

### C — Threshold Trigger System

**C1. Implement the threshold trigger evaluator with edge detection.**
For each region, for each threshold-trigger template, check whether the field crossed the effective threshold (base + noise offset) this tick. Edge detection: compare the field's value at the start of the tick (before drift was applied) against the value after drift. For `above` triggers: fire if previous < effective AND current >= effective. For `below` triggers: fire if previous > effective AND current <= effective. When a trigger fires, generate a new chain tag (incrementing counter: "chain_0001", "chain_0002", etc.), create a fired event log entry, and apply the template's effects to the region.

**Test:** Generate a world. Manually set one region's tension to 53. Run a few ticks of drift only (no events yet) until tension crosses a reasonable T1 threshold (effective threshold = 55 ± noise). Confirm T1 fires exactly on the crossing tick — not before, not on subsequent ticks while tension remains above. Print the event log entry with chain tag, field state before/after.

**🛑 CHECKPOINT C1 — STOP and show output to Westley.**

**C2. Verify edge detection prevents re-fire while above threshold.**
Continue running ticks after T1 has fired. Tension should remain above the threshold (T1's own +5 delta pushed it further up). Confirm T1 does NOT fire again on subsequent ticks.

**Test:** Run 20 more ticks after C1's trigger. Print per-tick tension values and event log. Confirm zero additional T1 firings while tension stays above threshold.

**🛑 CHECKPOINT C2 — STOP and show output to Westley.**

**C3. Verify re-fire on field drop and re-cross.**
Manually push the region's tension below the effective threshold (simulating drift or other events bringing it down). Then run ticks until it crosses again. Confirm T1 fires a second time with a NEW chain tag.

**Test:** Set tension to 5 below the effective threshold. Run ticks until oscillation or drift pushes it back across. Confirm T1 fires again. Print both event log entries — confirm different chain tags. If drift and oscillation don't naturally push it back across within a reasonable number of ticks, manually nudge tension to just below threshold and run one more tick of drift to trigger the crossing.

**🛑 CHECKPOINT C3 — STOP and show output to Westley.**

---

### D — Pending Event Queue and Chain Spawns

**D1. Implement the pending event queue and chain spawn roller.**
When an event fires (threshold or chain spawn), process its chain spawns: for each spawn, roll a delay from the triangular distribution `random.triangular(low, high, midpoint)` where midpoint = (low + high) / 2, compute the absolute scheduled tick, and insert into the pending queue with the parent's chain tag, the spawn's probability, and the spawn's conditions.

**Test:** Fire T1 manually in a region. Confirm two entries appear in the pending queue (T2 and T3 spawns). Print the queue entries showing scheduled ticks, chain tags (same as T1's), probabilities, and conditions. Run the delay roller 100 times for T1→T2's range (4–10) and print the distribution — confirm center-weighting (values near 7 more frequent than 4 or 10).

**🛑 CHECKPOINT D1 — STOP and show output to Westley.**

**D2. Implement pending queue processing — condition check then probability roll.**
Each tick, check if any pending events are due (scheduled_tick == current_tick). For each due event: first check conditions against the region's current state. If conditions fail, log a pruned branch entry and remove from queue. If conditions pass, roll against the event's firing probability. If the roll fails, log a pruned branch entry (reason: "probability_failed") and remove from queue. If the roll succeeds, fire the event: apply effects, log the fired event entry, process any chain spawns of the fired event.

**Test:** Set up a region where T1 has fired and T2 and T3 are in the queue. Manually set the region state so that T2's condition (tension > 58) is met but T3's condition (stability > 42) is NOT met. Advance to T3's scheduled tick. Confirm T3 is pruned with reason "condition_failed" and the actual stability value logged. Advance to T2's scheduled tick. Confirm T2 either fires (probability roll succeeded) or is pruned with reason "probability_failed". Run this 20 times with different seeds to confirm T2 fires roughly 45% of the time.

**🛑 CHECKPOINT D2 — STOP and show output to Westley.**

---

### E — Mutual Exclusion Resolution

**E1_step. Implement mutual exclusion checking.**
(Named E1_step to avoid confusion with template E1.)
Before applying effects for events due on the same tick in the same region, check for mutual exclusion conflicts. Compare exclusion tags across all events due this tick in this region. If two events have conflicting tags (the `political_crisis` / `political_resolution` pair or the `economic_collapse` / `economic_recovery` pair), the one with higher firing probability wins. Equal probability: random coin flip. The loser is pushed back by a random 1–2 ticks (uniform) — re-inserted into the pending queue at the new tick, retaining its chain tag and conditions.

**Note on which events carry exclusion tags:** Threshold-triggered events that have just fired AND pending queue events that passed their condition/probability checks are both candidates for mutual exclusion. All events due on a tick are collected, then exclusion is checked before deltas are applied.

**Test:** Manually schedule T2 (exclusion: `political_crisis`, prob 0.45) and T3 (exclusion: `political_resolution`, prob 0.35) to fire on the same tick in the same region, with both conditions met. Confirm T2 wins (higher probability). Confirm T3 is pushed back 1–2 ticks in the queue (not dropped). Advance to T3's new tick — confirm it fires normally. Print the full event log showing the exclusion resolution.

**🛑 CHECKPOINT E1_step — STOP and show output to Westley.**

**E2_step. Test equal-probability tie-breaking.**
Manually set two events with the same exclusion tag pair and identical probabilities to the same tick. Run 50 times. Confirm the winner is roughly 50/50 (random coin flip).

**🛑 CHECKPOINT E2_step — STOP and show output to Westley.**

---

### F — Simultaneous Collision Resolution

**F1. Implement start-of-tick snapshot and simultaneous delta application.**
At the beginning of each tick's event processing: snapshot all region field values. All events that fire this tick (both threshold triggers and queue events, after mutual exclusion resolution) compute their deltas against the snapshot — NOT against each other's modifications. After all events are resolved, sum all deltas per region per field, apply the summed deltas to the actual region state, then clamp economy to `max(economy, ECONOMY_FLOOR)`.

**Test:** Manually schedule T2 (tension +7, military -4, economy -3) and E2 (population -3, economy -4, tension +4) to fire on the same tick in the same region. Set the region to known starting values. Confirm both events compute deltas against the SAME starting state (not sequentially). Confirm the final field values are: starting + T2 deltas + E2 deltas applied simultaneously. Print the snapshot, each event's deltas, and the final state. Verify economy floor clamp if economy would drop below 8.0.

**🛑 CHECKPOINT F1 — STOP and show output to Westley.**

---

### G — Economy Floor Enforcement

**G1. Verify economy floor clamp on event deltas.**
Set a region's economy to 12.0. Fire E1 (economy -3) and E2 (economy -4) simultaneously. Total delta: -7. Expected result: economy = max(12 - 7, 8.0) = 8.0, not 5.0.

**Test:** Run the scenario above. Print the pre-event economy, the raw delta sum, the clamped result. Confirm economy = 8.0. Then run with economy starting at 30.0 and the same events — confirm economy = 23.0 (no clamping needed).

**🛑 CHECKPOINT G1 — STOP and show output to Westley.**

---

### H — Event Logging with Chain Tags and Causal Links

**H1. Implement complete event logging with chain tag propagation.**
Every fired event gets a log entry with: event_id, template_id, template_name, region_id, tick, chain_tag, parent_event_id (None for root threshold triggers), trigger_type ("threshold" or "chain_spawn"), effects_applied, field_state_before, field_state_after. Every pruned branch gets a pruned entry with: reason, failed condition or probability info, actual field value. Chain tags propagate: if T1 fires with chain_tag "chain_0001" and spawns T2 which fires and spawns nothing, both T1 and T2 carry "chain_0001". If T1 fires again later, it gets "chain_0002".

**Test:** Run a full sequence: T1 fires (threshold) → spawns T2 and T3 → T2 fires (chain spawn) → T3 is pruned (condition failed). Print the complete event log. Confirm chain_tag is the same across T1 and T2. Confirm T1's parent_event_id is None. Confirm T2's parent_event_id is T1's event_id. Confirm T3's pruned entry shows the correct chain_tag and reason.

**🛑 CHECKPOINT H1 — STOP and show output to Westley.**

---

### I — Full Integration Test

**I1. Run a full simulation with all 10 templates active across the world.**
Generate a world from Stage 1's isolated start template. Roll noise offsets. Run 300 ticks with events enabled alongside drift and oscillation. Print a summary event log: total events fired per template, total branches pruned per template, total mutual exclusion resolutions, total simultaneous collisions. Print the full chronological event log with chain tags and causal links.

**Test:** Confirm:
- Events fire on threshold crossings across multiple regions
- Chain spawns propagate (T1→T2, T1→T3, E1→E2, etc.)
- At least one branch pruning occurs (T3 or E3 condition fails)
- At least one mutual exclusion resolution occurs (or note if none happened naturally and explain why)
- Simultaneous events on the same tick compound their deltas
- Chain tags correctly link parent→child→grandchild
- Economy floor is respected (no region below 8.0 from events)
- Edge detection works (no template fires twice in the same region without the field dropping below and re-crossing)
- Cross-domain effects are visible (X1 firing affects economy/tension, potentially triggering T1 or E1)

**🛑 CHECKPOINT I1 — STOP and show output to Westley.**

**I2. Run 5 seeds and confirm stochastic divergence.**
Run the same 300-tick simulation with 5 different random seeds. Print per-seed summary: event counts per template, territory outcomes, which regions experienced which chains. Confirm genuine divergence — different seeds produce different event histories due to noise offsets, probability rolls, and delay rolls.

**🛑 CHECKPOINT I2 — STOP and show output to Westley.**

**I3. Verify 3-deep chain (X1 → X2 → T2).**
If the 300-tick run did not naturally produce a 3-deep chain, set up a targeted test: place a region at population 76+ (to trigger X1), with tension ~48 (so X2's condition "tension > 50" can be met after X1 applies tension +2), and then tension rising above 60 for T2's condition. Run until the full X1→X2→T2 chain plays out. Print the chain with all three events linked by the same chain tag.

**🛑 CHECKPOINT I3 — STOP and show output to Westley.**

---

## Done Condition

Run the Stage 2 simulation (300+ ticks, 5 seeds) and confirm:
1. Threshold triggers fire deterministically on field crossings — not before, not every tick while above
2. Chain spawns propagate through follow-up events with correct delay distribution and condition checking
3. Failed conditions produce silent drops (pruned branches logged)
4. Mutually exclusive events resolve correctly (higher probability wins, equal probability coin flip, loser pushed back)
5. Simultaneous events on the same tick compound their deltas against start-of-tick snapshot
6. Economy floor is enforced on all event deltas
7. Chain tags link entire causal lineages from root trigger through all descendants
8. Event log is a complete, structured record of all firings and prunings with causal links
9. Different random seeds produce genuinely different event histories
10. All four trigger fields (tension, economy, military, population) produce events
11. At least one 3-deep chain is demonstrated (X1→X2→T2)

Westley signs off on the full integration test output before Stage 3 begins.

## Files Created
*(Filled in after implementation)*
