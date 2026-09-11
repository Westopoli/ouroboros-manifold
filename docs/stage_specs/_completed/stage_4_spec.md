# Stage 4 — Civilizational Lifecycle and Generational Structure

## Goal

Prove that the simulation produces a complete civilizational arc: factions expand into empty space, consolidate, fight, overextend, fragment through revolts, and reach dynamic equilibrium or collapse — with the player's faction subject to the same forces as every other faction, including mortality. Administrative revolts enforce a hard ceiling on sustainable empire size, preventing the total-dominance outcome currently observed in Stage 3 testing. The generational structure (time jumps, lineage rotation, player faction reassignment on collapse) operates on top of the simulation, reading its output to drive chapter transitions.

This is the stage where the simulation becomes a *world* rather than a *combat sandbox*. Stages 1–3.5 proved that regions drift, events fire, factions fight, and technology grows. Stage 4 proves that these mechanics interact over long timescales to produce the lifecycle phases described in the bible: Expansion → Consolidation → Conflict → Overextension → Fragmentation → Equilibrium/Collapse.

## Bible References

Read these spoke sections before implementing:

- **`docs/bible_history/bible_2_00_simulation.md`**: "Administrative revolt system — faction size pressure", "Administrative revolt chain", "Breakaway faction from admin revolt", "Coexistence with tension revolts", "Budget accumulation" (maintenance cost dynamics), "Conquest consequence chain", "Reinforcement diminishing returns — continuous capacity cap"
- **`docs/bible_history/bible_2_00_world.md`**: "World Evolution — Per-Faction Lifecycle", "Civilizational Lifecycle — Mechanical Drivers" (all 6 phases)
- **`game_bible.md` (hub)**: "The Generational Structure" (full section — chapters, cycle, character selector, what carries over), "Player Civilization Mortality", "Terminal Conditions and the Cycle", "Simulation Pacing Targets"

## What to Build

### Files to create

**`admin_revolt.py`** — Administrative revolt system. Contains:
- Per-tick, per-region revolt probability computation: `admin_revolt_chance = base_rate + scaling_rate * max(0, territory_count - inflection_point)^2`
- Roll against probability for each region in each faction
- On fire: spawn a non-interruptible separatist movement event chain (variable length 3–8 ticks, rolled at spawn)
- Chain templates: Separatist Movement → [Political Crisis →] [Popular Support Shifts →] Military Defection → Breakaway
- Terminal event creates a new independent breakaway faction (zero budget, archetype rolled from pool, region keeps current fields minus chain degradation)
- Reduce parent faction territory count by 1 (self-correcting floor)

**`time_jump.py`** — Time jump controller. Contains:
- Run N ticks of simulation (N drawn from configurable range, targeting 20–100 years mapped to tick scale)
- Collect chronicle-relevant events during the jump (significant events logged by the tick loop)
- Return a structured summary: events fired, territory changes, faction births/deaths, field deltas per faction
- Does NOT generate chronicle prose (that's Stage 5) — just collects the raw material

**`generational.py`** — Generational structure controller. Contains:
- Chapter state tracking (current lineage, chapter counter within lineage, faction assignment)
- Lineage rotation decision logic (regional delta scoring, crisis veto, hard cap, forced rotation on bloodline death)
- Faction reassignment on player faction collapse (prefer narrative connections, fall back to geographic overlap)
- Cross-faction lineage rotation after hard cap (consider all factions, not just current)
- Does NOT contain the character selector's lineage generation or naming (that's Stage 5 coherence ledger work) — uses placeholder character IDs

**`lifecycle.py`** — Lifecycle phase classifier. Contains:
- Per-faction phase classification based on current simulation state: Expansion, Consolidation, Conflict, Overextension, Fragmentation, Equilibrium
- Phase is *derived*, not stored — computed on demand from region count, budget trajectory, border counts, recent conquest/revolt history
- Used by the time jump summary and (later) the mission generator to understand faction context
- Phase classification thresholds are config values

### Files to modify

**`tick.py`** — Add admin revolt check as a new step in the tick resolution sequence, after border friction and before drift. The admin revolt fires event chains into the existing pending queue.

**`events.py`** — Add admin revolt chain templates (SEPARATIST_MOVEMENT, POLITICAL_CRISIS, POPULAR_SUPPORT_SHIFTS, MILITARY_DEFECTION, ADMIN_BREAKAWAY). These follow the same template structure as existing event chains. The chain is non-interruptible: no condition checks on intermediate events (they always fire).

**`faction.py`** — Add breakaway faction creation from admin revolt terminal event (similar to existing revolt faction creation in tick.py, but with archetype rolled from full pool instead of always "breakaway").

**`config.py`** — Add all new config values (see Behavioral Claims for the full list).

**`sim_tuner.py`** — Add new scenarios:
- `06_lifecycle_2faction` — 2 factions, 1500 ticks, admin revolts enabled. Prove fragmentation occurs.
- `07_lifecycle_4faction` — 4 factions, 2000 ticks, all systems enabled. Prove full lifecycle arc.
- `08_time_jump` — Run 3 consecutive time jumps from a mid-game state. Prove jumps produce meaningful change.

**`invariants.py`** — Add Group J invariants (see below).

### Files NOT to create or modify

The coherence ledger, chronicle generation, character naming, mission system, and combat system are all Stage 5 or 6. Stage 4 uses placeholder character IDs in the generational controller. The time jump collects raw event data but does not produce prose. The lifecycle classifier outputs phase labels but does not feed them to a mission generator.

## Behavioral Claims

### Administrative Revolts

**Claim J1: Admin revolts fire for large factions.** A faction holding 7+ regions should experience at least one administrative revolt within 200 ticks.
- When: faction owns ≥7 regions for 200+ consecutive ticks
- Then: at least one admin revolt chain should have fired in one of its regions
- Over: any 200-tick window where the faction holds 7+ regions
- Pattern: threshold bound
- Governing configs: `ADMIN_REVOLT_BASE_RATE`, `ADMIN_REVOLT_SCALING_RATE`, `ADMIN_REVOLT_INFLECTION_POINT`
- Severity: critical

**Claim J2: Admin revolts are rare for small factions.** A faction holding 3 or fewer regions should experience admin revolts very rarely — no more than 1 per 500 ticks on average.
- When: faction owns ≤3 regions
- Then: admin revolt count should be ≤ total_ticks / 500
- Over: full run
- Pattern: threshold bound
- Governing configs: `ADMIN_REVOLT_BASE_RATE`
- Severity: warning

**Claim J3: Admin revolt chains always complete.** Once an admin revolt fires, the full chain should always reach the terminal breakaway event. No chain should be interrupted or pruned.
- When: SEPARATIST_MOVEMENT event fires
- Then: ADMIN_BREAKAWAY event fires 3–8 ticks later in the same region
- Over: every admin revolt chain in the run
- Pattern: trajectory shape
- Governing configs: (code bug if violated — always escalate)
- Severity: critical

**Claim J4: Admin revolts produce breakaway factions.** Every completed admin revolt chain should result in a new faction appearing in the registry and the revolting region changing ownership.
- When: ADMIN_BREAKAWAY event fires
- Then: new faction exists in registry, region.faction_id changed
- Over: every admin revolt chain
- Pattern: threshold bound
- Governing configs: (code bug if violated — always escalate)
- Severity: critical

**Claim J5: No faction holds all regions for 200+ ticks.** Total dominance (one faction owning every region) should be impossible to sustain. If a faction conquers everything, admin revolts should fragment it within 200 ticks.
- When: one faction owns all regions in the world
- Then: within 200 ticks, at least one other faction should exist
- Over: any point in the run
- Pattern: trajectory shape
- Governing configs: `ADMIN_REVOLT_SCALING_RATE`, `ADMIN_REVOLT_INFLECTION_POINT`
- Severity: critical
- Note: this directly addresses the D4 finding from Stage 3 validation

**Claim J6: Quadratic scaling is detectable.** A faction holding 8 regions should lose territory to admin revolts at least 3× faster than a faction holding 5 regions (measured as revolts per 100 ticks).
- When: comparing two factions of different sizes in the same run, or the same faction before/after expansion
- Then: revolt rate scales roughly quadratically with territory count above inflection point
- Over: 500+ tick windows
- Pattern: relational constraint
- Governing configs: `ADMIN_REVOLT_SCALING_RATE`, `ADMIN_REVOLT_INFLECTION_POINT`
- Severity: warning

### Lifecycle Phases

**Claim J7: Expansion phase occurs early.** In the first 200 ticks, factions should colonize more than they attack. Colonization events should outnumber attack events across all factions.
- When: ticks 0–200
- Then: total colonizations > total attacks
- Over: first 200 ticks
- Pattern: relational constraint
- Governing configs: `COLONIZE_COST`, `ATTACK_CONFIDENCE_RANGE`, `BUDGET_GROWTH_RATE`
- Severity: warning

**Claim J8: Conflict phase follows expansion.** After empty regions are exhausted (all regions owned), inter-faction attacks should increase. The attack rate in the 200 ticks after the last colonization should be at least 2× the attack rate before.
- When: last colonization fires at tick T
- Then: attacks in [T, T+200] > 2 × attacks in [T-200, T]
- Over: 200-tick windows around the colonization-to-conflict transition
- Pattern: relational constraint
- Governing configs: `ATTACK_CONFIDENCE_RANGE`, `BUDGET_GROWTH_RATE`
- Severity: warning

**Claim J9: Fragmentation occurs after overextension.** A faction that has conquered 3+ regions should lose at least 1 region (to revolt or reconquest) within 500 ticks of reaching peak territory.
- When: faction reaches maximum territory count ≥ 6
- Then: territory count decreases by at least 1 within 500 ticks
- Over: any peak-territory event
- Pattern: trajectory shape
- Governing configs: `ADMIN_REVOLT_SCALING_RATE`, `CONQUEST_TENSION_SPIKE`, `CONQUEST_ECONOMY_DISRUPTION`
- Severity: warning

**Claim J10: The world maintains faction diversity.** At no point after tick 300 should the world have fewer than 2 factions. The combination of admin revolts and tension revolts should keep the faction count above 1.
- When: tick > 300
- Then: faction count (factions owning ≥1 region) ≥ 2
- Over: every tick after 300
- Pattern: threshold bound
- Governing configs: `ADMIN_REVOLT_BASE_RATE`, `ADMIN_REVOLT_SCALING_RATE`
- Severity: critical

### Time Jumps

**Claim J11: Time jumps produce meaningful change.** A 100-tick time jump should produce at least 2 territory changes (conquests or colonizations) and at least 1 faction birth or death.
- When: time_jump runs for 100 ticks
- Then: territory changes ≥ 2, faction_births + faction_deaths ≥ 1
- Over: each time jump
- Pattern: threshold bound
- Governing configs: `BUDGET_GROWTH_RATE`, `ATTACK_CONFIDENCE_RANGE`, `ADMIN_REVOLT_SCALING_RATE`
- Severity: warning

**Claim J12: Time jumps don't destroy the world.** After a time jump, at least 2 factions should still exist and the player's faction (or its successor) should own at least 1 region.
- When: time_jump completes
- Then: ≥2 factions exist, player faction (or reassigned faction) owns ≥1 region
- Over: every time jump
- Pattern: threshold bound
- Governing configs: (design issue if violated — escalate)
- Severity: critical

### Player Faction Mortality

**Claim J13: Player faction can die.** Across 5 runs of 2000 ticks with different seeds, the player's faction should lose all regions in at least 1 run. If the player faction survives all 5 runs, it may have hidden advantages or the simulation may not be aggressive enough.
- When: 5 runs, 2000 ticks each, different seeds
- Then: player faction eliminated in ≥1 run
- Over: cross-run comparison
- Pattern: cross-run comparison (special)
- Governing configs: starting field ranges, `RESISTANCE_FACTOR`, `ATTACK_EFFICIENCY`
- Severity: warning

**Claim J14: Player faction collapse triggers reassignment.** When the player's faction loses all regions, the generational controller should reassign the player to a surviving faction within the same tick.
- When: player faction region count drops to 0
- Then: generational controller assigns player to a different faction that owns ≥1 region
- Over: every player faction collapse event
- Pattern: threshold bound
- Governing configs: (code bug if violated — always escalate)
- Severity: critical

### Regression Guards

**Claim J15: All Stage 3/3.5 invariants still pass.** No regression in previously validated behavior.
- Over: full run
- Pattern: regression check
- Severity: critical

## Scenarios to Add

```python
"06_lifecycle_2faction": {
    "template":     "contested_border",
    "ticks":        1500,
    "seed":         1,
    "description":  "Lifecycle — 2 factions, admin revolts, 1500 ticks, prove fragmentation",
    "use_tick_engine": True,
    "features": {
        "events": True, "factions": True, "border_friction": True,
        "recruitment": True, "adjacency_bonus": True, "oscillation": True,
        "technology": True, "diplomacy": True, "admin_revolts": True,
    },
},

"07_lifecycle_4faction": {
    "template":     "four_way",
    "ticks":        2000,
    "seed":         1,
    "description":  "Full lifecycle — 4 factions, all systems, 2000 ticks",
    "use_tick_engine": True,
    "features": {
        "events": True, "factions": True, "border_friction": True,
        "recruitment": True, "adjacency_bonus": True, "oscillation": True,
        "technology": True, "diplomacy": True, "admin_revolts": True,
    },
},

"08_time_jump": {
    "template":     "four_way",
    "ticks":        500,
    "seed":         1,
    "description":  "Time jump test — run to tick 500, then 3 consecutive 100-tick jumps",
    "use_tick_engine": True,
    "features": {
        "events": True, "factions": True, "border_friction": True,
        "recruitment": True, "adjacency_bonus": True, "oscillation": True,
        "technology": True, "diplomacy": True, "admin_revolts": True,
    },
    "time_jumps": [500, 600, 700],  # tick numbers where time jump summaries are captured
},
```

## Validation Criteria

- All J1–J15 invariants pass across 3+ seeds for scenarios 06 and 07
- All existing invariants (A through I) still pass (J15 regression check)
- Graphs for scenario 07 show: early colonization wave, mid-run conflict spike, late-run faction count increase (from revolts), no single-faction dominance sustained beyond ~200 ticks
- At least 1 of 5 seeds for scenario 07 produces a player faction collapse
- Time jump summaries (scenario 08) contain ≥2 territory changes per jump
- Westley reviews final validator report + graphs for scenarios 06, 07, 08

## Config Values to Add

```python
# ── Administrative revolts (Stage 4) ─────────────────────────────────
ENABLE_ADMIN_REVOLTS         = True
ADMIN_REVOLT_BASE_RATE       = 0.001   # per-region per-tick base probability (nonzero for all factions)
ADMIN_REVOLT_SCALING_RATE    = 0.0005  # quadratic scaling coefficient above inflection point
ADMIN_REVOLT_INFLECTION_POINT = 4      # territory count where quadratic acceleration begins
ADMIN_REVOLT_CHAIN_LENGTH_RANGE = (3, 8)  # ticks for the separatist chain to complete

# ── Lifecycle phase classification (Stage 4) ─────────────────────────
LIFECYCLE_EXPANSION_EMPTY_THRESHOLD   = 0.3   # faction classified as "expanding" if >30% of world regions are empty
LIFECYCLE_CONFLICT_ATTACK_RATE        = 0.05  # attacks per faction per tick threshold for "conflict" phase
LIFECYCLE_OVEREXTENSION_DRAIN_RATIO   = 0.4   # fraction of regions that are net budget drains → "overextended"
LIFECYCLE_FRAGMENTATION_REVOLT_RATE   = 0.02  # revolts per tick threshold for "fragmenting" phase

# ── Time jump (Stage 4) ─────────────────────────────────────────────
TIME_JUMP_MIN_TICKS = 20    # minimum jump duration
TIME_JUMP_MAX_TICKS = 100   # maximum jump duration

# ── Generational structure (Stage 4) ─────────────────────────────────
LINEAGE_MIN_CHAPTERS    = 2    # minimum chapters before rotation is considered
LINEAGE_HARD_CAP        = 6    # forced rotation after this many chapters
LINEAGE_DELTA_LOW       = 10.0  # regional delta below this → high rotation probability
LINEAGE_DELTA_HIGH      = 40.0  # regional delta above this → low rotation probability
CRISIS_VETO_STABILITY   = 25.0  # stability below this vetoes rotation
```

## Done Condition

All validation criteria met. Westley signs off on the final validator report, not intermediate terminal output. The D4 finding (total dominance) from Stage 3 validation should be resolved — J5 should pass where D4 previously failed.
