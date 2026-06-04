# Simulation Validator & Auto-Tuning Harness — Implementation Plan

## Overview

This document is a Claude Code implementation spec for an automated simulation validation and tuning system for Ouroboros Manifold. It replaces the current workflow where Westley manually reads terminal output and adjusts config values. The system has three layers:

1. **Trajectory Recorder** — structured per-tick snapshots of all simulation state
2. **Invariant Library** — behavioral assertions over trajectories that encode "expected behavior"
3. **Tuning Loop** — when invariants fail, diagnose the cause and either auto-fix (config issue) or escalate (design issue)

The system integrates into the existing `sim_tuner.py` harness. It does not replace the graphing — it adds a pass/fail layer on top of it.

---

## File Structure

```
sim_validator.py          # Core: trajectory recorder, invariant runner, report generator
invariants.py             # Library of all behavioral invariant functions
tuning_loop.py            # Auto-diagnosis and config adjustment logic
test_validate.py          # Entry point: run scenarios → check invariants → report
```

All files live alongside the existing engine files (`config.py`, `sim_tuner.py`, etc.).

---

## Part 1: Trajectory Recorder (`sim_validator.py`)

### Purpose

Capture per-tick state into a structured format that invariant functions can query. The current `sim_tuner.py` already samples faction-averaged field values per tick — the recorder captures richer data.

### Data Structure: `TrajectoryLog`

```python
@dataclass
class TickSnapshot:
    tick: int
    regions: dict          # {region_id: {fields: {...}, faction_id: str, tier: str, composites: {...}}}
    factions: dict         # {faction_id: {budget: float, tech_level: float, archetype: str, 
                           #               owned_region_count: int, avg_fields: {field: float},
                           #               total_economy: float, total_military: float,
                           #               diplomatic_stance: dict}}
    events_fired: list     # [{template_id, region_id, name, field_deltas}]
    faction_actions: list  # [{faction_id, action, target_region, budget_committed, budget_spent, 
                           #   outcome_band, conquest: bool}]
    conquests: list        # [{region_id, old_faction_id, new_faction_id}]
    colonizations: list    # [{region_id, faction_id}]
    collisions: list       # [collision log dicts from intent_resolver]

class TrajectoryLog:
    seed: int
    scenario_name: str
    template: str
    total_ticks: int
    features: dict                    # which features were enabled
    config_snapshot: dict             # all config values at start of run
    snapshots: list[TickSnapshot]     # one per tick, 0..N
    
    # ── Query helpers (what invariants call) ──────────────────────────
    
    def field_series(self, faction_id: str, field: str) -> list[float]:
        """Return [avg_field_value_tick_0, avg_field_value_tick_1, ...] for a faction."""
        
    def region_field_series(self, region_id: str, field: str) -> list[float]:
        """Return [field_value_tick_0, field_value_tick_1, ...] for a specific region."""
    
    def budget_series(self, faction_id: str) -> list[float]:
        """Return [budget_tick_0, budget_tick_1, ...] for a faction."""
    
    def action_log(self, faction_id: str) -> list[dict]:
        """Return all actions taken by a faction, in tick order."""
    
    def attacks_by(self, faction_id: str) -> list[dict]:
        """Return all attack actions by a faction."""
    
    def conquests_by(self, faction_id: str) -> list[dict]:
        """Return all conquests where new_faction_id == faction_id."""
    
    def region_ownership_at(self, tick: int) -> dict:
        """Return {region_id: faction_id} at a given tick."""
    
    def owned_region_count_series(self, faction_id: str) -> list[int]:
        """Return [n_regions_tick_0, n_regions_tick_1, ...] for a faction."""
    
    def events_in_range(self, tick_start: int, tick_end: int) -> list[dict]:
        """Return all events that fired in [tick_start, tick_end]."""
    
    def field_at(self, faction_id: str, field: str, tick: int) -> float:
        """Single-point query."""
    
    def field_delta_series(self, faction_id: str, field: str) -> list[float]:
        """Return [delta_tick_1, delta_tick_2, ...] — per-tick change in avg field."""
    
    def ticks_where(self, faction_id: str, field: str, predicate) -> list[int]:
        """Return list of ticks where predicate(field_value) is True."""
```

### Integration with `sim_tuner.py`

The `run_scenario()` function already produces tick logs. The recorder wraps this: after each `run_tick()` or manual-drift tick, it captures a `TickSnapshot` from the live world state + the tick log dict. This is a thin shim — most data is already being computed.

```python
def run_recorded_scenario(name: str, scenario: dict, seed_override=None) -> TrajectoryLog:
    """Same as run_scenario() but returns a TrajectoryLog instead of graph-ready data."""
    # ... same setup as run_scenario ...
    log = TrajectoryLog(seed=..., scenario_name=name, ...)
    for t in range(1, ticks + 1):
        tick_log = _tick.run_tick(...)  # or manual drift loop
        snapshot = _capture_snapshot(t, world, registry, tick_log)
        log.snapshots.append(snapshot)
    return log
```

The existing `run_scenario()` can optionally also return the `TrajectoryLog` as a side-output so the graphing pipeline continues working unchanged.

---

## Part 2: Invariant Library (`invariants.py`)

### Invariant Format

Each invariant is a function with this signature:

```python
def invariant_name(log: TrajectoryLog) -> InvariantResult:
    ...

@dataclass
class InvariantResult:
    name: str                       # e.g. "no_field_flatline"
    passed: bool
    severity: str                   # "critical" | "warning" | "info"
    message: str                    # human-readable explanation
    details: dict | None            # structured data for the tuning loop
    # details includes:
    #   tick: int                   # tick where the violation was detected (if applicable)
    #   faction_id: str             # which faction (if applicable)
    #   region_id: str              # which region (if applicable)
    #   field: str                  # which field (if applicable)
    #   actual_value: float         # what the value was
    #   expected_range: tuple       # what the value should have been
    #   governing_configs: list     # which config keys likely control this behavior
    #   trajectory_excerpt: list    # last N values leading to the failure
```

### Invariant Catalog

Below is the initial set of invariants, grouped by what they validate. Claude Code should implement all of these. Each invariant description includes the **governing config keys** — these are the config values that the tuning loop would adjust if the invariant fails.

#### Group A: Field Health (no degenerate states)

**A1. `no_field_flatline`** — No field for any faction should be stuck at the same value (within ±0.5) for more than 60 consecutive ticks, unless the field is at a floor/ceiling and there's a known reason (economy at ECONOMY_FLOOR during famine, military at 0 after conquest).

- Applies to: all 4 fields, all factions
- Severity: critical
- Governing configs: `ECONOMY_FLOOR`, `ECONOMY_BASE_GROWTH`, `MILITARY_DECAY_RATE`, `RECRUITMENT_RATE`, `POPULATION_GROWTH_RATE`

**A2. `no_premature_collapse`** — Home regions should not have all fields below 15 within the first 100 ticks from a healthy start (home population range 55–75). A healthy start collapsing immediately signals broken drift math.

- Applies to: factions starting from "home" tier regions
- Severity: critical
- Governing configs: `MILITARY_DECAY_RATE`, `ECONOMY_TENSION_PENALTY_RATE`, `POPULATION_SUBSISTENCE`, `TENSION_NATURAL_DECAY_RATE`

**A3. `fields_stay_bounded`** — All fields must remain in [0, 100] at all times. Economy must remain ≥ `ECONOMY_FLOOR` except during conquest (which has bypass_floor=True).

- Applies to: all regions, all ticks
- Severity: critical
- Governing configs: (this is a code bug, not a config issue — always escalate)

**A4. `frontier_more_volatile_than_home`** — Over a 200-tick window, frontier regions should have higher standard deviation in at least 2 of 4 fields compared to home regions of the same faction. Frontier starts weaker, so it should be more sensitive to perturbation.

- Applies to: factions with both home and frontier regions
- Severity: warning
- Governing configs: `STARTING_MIL_RATIO`, `STARTING_ECO_RATIO`, `FRONTIER_POPULATION_RANGE`

#### Group B: Economy Dynamics

**B1. `economy_recovers_from_famine`** — If average economy drops below 20, it should recover above 30 within 100 ticks (given population > 20 and tension < 70). The economy system has growth from population that should pull it out of famine.

- Applies to: all factions
- Severity: critical
- Governing configs: `ECONOMY_BASE_GROWTH`, `POPULATION_SUBSISTENCE`, `ECONOMY_TENSION_PENALTY_RATE`, `ECO_POP_RATIO`

**B2. `economy_population_coupling`** — Economy should be roughly correlated with population over long windows. Specifically: if population is above 50 and stable (std dev < 5 over 50 ticks), economy should converge toward `population * ECO_POP_RATIO` within ±20. Wide divergence means the overcapacity/growth coupling is broken.

- Applies to: all factions in drift-only or low-conflict scenarios
- Severity: warning
- Governing configs: `ECO_POP_RATIO`, `ECO_OVERCAPACITY_DECAY`, `ECONOMY_BASE_GROWTH`

**B3. `tension_responds_to_economy`** — When economy is below `TENSION_ECONOMY_MIDPOINT` for 30+ ticks, tension should trend upward (positive average delta). When economy is above the midpoint for 30+ ticks, tension should trend downward or stabilize. This validates the economic_tension driver in `tension_drift()`.

- Applies to: all factions
- Severity: warning
- Governing configs: `TENSION_ECONOMY_RATE`, `TENSION_ECONOMY_MIDPOINT`, `TENSION_NATURAL_DECAY_RATE`

#### Group C: Military & Recruitment

**C1. `military_decays_without_economy`** — If a faction's average economy is below 15 for 50+ ticks, military should be trending downward. Military maintenance costs should eat into strength when economy can't support it.

- Applies to: all factions
- Severity: warning
- Governing configs: `MILITARY_DECAY_RATE`, `RECRUITMENT_THRESHOLD`, `RECRUITMENT_RATE`

**C2. `recruitment_prevents_military_zero`** — In a non-combat scenario (no attacks received), if economy > 30 and population > 30, military should never drop below 10 for more than 20 consecutive ticks. Recruitment should floor military at a reasonable baseline.

- Applies to: factions not under attack
- Severity: warning
- Governing configs: `RECRUITMENT_BASELINE`, `RECRUITMENT_RATE`, `RECRUITMENT_THRESHOLD`, `RECRUITMENT_CEILING`

**C3. `military_ceiling_respected`** — Military should rarely exceed `RECRUITMENT_CEILING` (90) through drift/recruitment alone. Events and Emergency Levy can push it higher, but drift-only military should approach the ceiling asymptotically, not blow past it.

- Applies to: all factions in drift-only scenarios
- Severity: warning
- Governing configs: `RECRUITMENT_CEILING`, `RECRUITMENT_RATE`

#### Group D: Budget & Agent Behavior

**D1. `budget_accumulates_monotonically_between_actions`** — Between any two spending actions (attack, colonize, reinforce), budget should increase every tick (or stay flat if economy - maintenance ≤ 0). No unexpected resets, no sawtooth patterns. This is the bug class Westley already fixed — the invariant prevents regression.

- Applies to: all factions with agents enabled
- Severity: critical
- Governing configs: `BUDGET_GROWTH_RATE`, `REGION_MAINTENANCE_COST`

**D2. `conqueror_attacks_eventually`** — The conqueror archetype should launch at least one attack within the first 150 ticks. A conqueror that never attacks means the confidence threshold is too high or budget growth is too slow.

- Applies to: conqueror archetype factions
- Severity: critical
- Governing configs: `ATTACK_CONFIDENCE_RANGE["conqueror"]`, `BUDGET_GROWTH_RATE`, `ATTACK_COMMIT_FRACTION`, `BUDGET_PRESSURE_THRESHOLD`

**D3. `player_civ_is_conservative`** — The player_civilization archetype should attack less frequently than the conqueror (if both have targets). Over 500 ticks, player_civ should have fewer attack actions than conqueror. The high confidence range (40–60) and low attack weight (0.3) should ensure this.

- Applies to: scenarios with both player and conqueror factions
- Severity: warning
- Governing configs: `ATTACK_CONFIDENCE_RANGE["player_civilization"]`, `ARCHETYPE_DECISION_WEIGHTS`

**D4. `budget_pressure_prevents_hoarding`** — No faction should accumulate budget above 5× the cost of their cheapest viable attack for more than 50 consecutive ticks. The budget pressure mechanic should lower confidence and force spending.

- Applies to: all factions with agents enabled
- Severity: warning
- Governing configs: `BUDGET_PRESSURE_THRESHOLD`, `ATTACK_CONFIDENCE_RANGE`

#### Group E: Combat & Conquest

**E1. `attacks_produce_damage`** — Every attack that fires (action == "attack") should produce non-zero military damage to the target region, regardless of outcome band. Even repelled attacks deal `effective_attack * 0.10` damage.

- Applies to: all attack actions in the trajectory
- Severity: critical
- Governing configs: (code bug if violated — always escalate)

**E2. `conquest_changes_ownership`** — Every conquest event should result in the target region's `faction_id` changing to the attacker's `faction_id` on the next tick.

- Applies to: all conquest events
- Severity: critical
- Governing configs: (code bug if violated — always escalate)

**E3. `conquest_causes_disruption`** — After a conquest, the conquered region should show tension increase and economy decrease on the tick of conquest. Validates that `CONQUEST_TENSION_SPIKE` and `CONQUEST_ECONOMY_DISRUPTION` are being applied.

- Applies to: all conquest events
- Severity: critical
- Governing configs: `CONQUEST_TENSION_SPIKE`, `CONQUEST_ECONOMY_DISRUPTION`, `CONQUEST_POPULATION_LOSS`

**E4. `no_faction_eliminated_too_fast`** — No faction should lose all regions within the first 80 ticks from a standard start. An immediate wipe means combat is too lopsided or starting positions are unbalanced.

- Applies to: all factions
- Severity: warning
- Governing configs: `RESISTANCE_FACTOR`, `ATTACK_EFFICIENCY`, `BREAKTHROUGH_THRESHOLD`, starting field ranges

#### Group F: Border Friction

**F1. `border_friction_raises_tension`** — Regions bordering hostile factions should have higher average tension than interior regions of the same faction over a 100-tick window. If border friction isn't creating detectable tension differences, it's too weak.

- Applies to: scenarios with hostile borders
- Severity: warning
- Governing configs: `BORDER_FRICTION_TENSION`, `BORDER_FRICTION_ECONOMY`

**F2. `border_friction_drags_economy`** — Same as F1 but for economy: border regions should have lower average economy than interior regions.

- Applies to: scenarios with hostile borders
- Severity: warning
- Governing configs: `BORDER_FRICTION_ECONOMY`

#### Group G: Colonization

**G1. `colonization_happens`** — In a scenario with uninhabited regions adjacent to faction territory, at least one colonization should occur within 200 ticks. Factions with `can_colonize: True` and sufficient budget should expand.

- Applies to: scenarios with uninhabited regions
- Severity: warning
- Governing configs: `COLONIZE_COST`, `ARCHETYPE_DECISION_WEIGHTS`, `MIN_ACTION_THRESHOLD`

**G2. `colonies_start_weak`** — Newly colonized regions should start with fields at or below the colony starter values (`COLONY_START_MILITARY`, etc.). They should not immediately be at home-region levels.

- Applies to: all colonization events
- Severity: critical
- Governing configs: `COLONY_START_MILITARY`, `COLONY_START_ECONOMY`, `COLONY_START_TENSION`, `COLONY_START_POPULATION`

#### Group H: Trajectory Shape

**H1. `oscillation_present`** — When `ENABLE_OSCILLATION=True`, economy and tension should show periodic fluctuation. Compute the autocorrelation at the configured period — it should be significantly positive (> 0.3). If oscillation is enabled but undetectable, the amplitude is too low or something is overwriting it.

- Applies to: all factions when oscillation is on
- Severity: warning
- Governing configs: `ECON_OSCILLATION_AMPLITUDE`, `ECON_OSCILLATION_PERIOD`, `TENSION_OSCILLATION_AMPLITUDE`

**H2. `no_universal_convergence`** — In a 4-faction scenario, not all factions should converge to the same field values (within ±5) by tick 300. The simulation should produce genuine divergence — different archetypes, different starting conditions, different trajectories.

- Applies to: multi-faction scenarios
- Severity: warning
- Governing configs: `ARCHETYPE_DECISION_WEIGHTS`, faction modifier dicts, starting field ranges

**H3. `stochastic_divergence_across_seeds`** — Running the same scenario with 3 different seeds should produce meaningfully different outcomes (different territory counts, different conquest timing, different final field averages). If all seeds produce identical trajectories, the RNG isn't being used or isn't influential enough.

- Applies to: multi-seed comparison (special invariant — the runner calls this across runs)
- Severity: warning
- Governing configs: `STOCHASTIC_RANGE`, `ATTACK_CONFIDENCE_RANGE`, starting field jitter ranges

#### Group I: Technology (when ENABLE_TECHNOLOGY=True)

**I1. `tech_grows_with_economy`** — Factions with higher average economy should have higher tech_level after 200 ticks. Technology growth is economy-driven; if a poor faction out-techs a rich one, the formula is wrong.

- Applies to: multi-faction scenarios with tech enabled
- Severity: warning
- Governing configs: `BASE_TECH_RATE`, `TECH_POPULATION_FLOOR`

---

## Part 3: Tuning Loop (`tuning_loop.py`)

### Purpose

When invariants fail, diagnose whether the root cause is a tunable config value or a design/code issue. If it's config, propose (and optionally apply) an adjustment.

### Config-Invariant Mapping

Each invariant declares its `governing_configs`. The tuning loop uses this to know which knobs to turn. The mapping also includes **direction hints**:

```python
CONFIG_EFFECTS = {
    # config_key: {invariant_name: "increase" | "decrease" | "either"}
    # meaning: to fix the invariant failure, try adjusting this config in the given direction
    
    "ECONOMY_BASE_GROWTH": {
        "economy_recovers_from_famine": "increase",
        "economy_population_coupling": "either",
    },
    "MILITARY_DECAY_RATE": {
        "no_premature_collapse": "decrease",
        "military_decays_without_economy": "increase",
        "recruitment_prevents_military_zero": "decrease",
    },
    "RECRUITMENT_RATE": {
        "recruitment_prevents_military_zero": "increase",
        "military_ceiling_respected": "decrease",
    },
    "BUDGET_GROWTH_RATE": {
        "budget_accumulates_monotonically_between_actions": "increase",
        "conqueror_attacks_eventually": "increase",
    },
    "BORDER_FRICTION_TENSION": {
        "border_friction_raises_tension": "increase",
    },
    "BORDER_FRICTION_ECONOMY": {
        "border_friction_drags_economy": "increase",
    },
    "TENSION_NATURAL_DECAY_RATE": {
        "no_premature_collapse": "increase",
        "tension_responds_to_economy": "decrease",  # if decay is too strong, tension won't respond
    },
    # ... etc. for all governing config keys across all invariants
}
```

### Config Bounds

Every tunable config has a safe range. The tuning loop will never adjust outside these bounds:

```python
CONFIG_BOUNDS = {
    "ECONOMY_BASE_GROWTH":          (0.5, 8.0),
    "MILITARY_DECAY_RATE":          (0.001, 0.05),
    "RECRUITMENT_RATE":             (0.5, 10.0),
    "RECRUITMENT_BASELINE":         (0.01, 0.5),
    "BUDGET_GROWTH_RATE":           (0.005, 0.05),
    "BORDER_FRICTION_TENSION":      (0.01, 0.5),
    "BORDER_FRICTION_ECONOMY":      (0.001, 0.05),
    "TENSION_NATURAL_DECAY_RATE":   (0.05, 0.5),
    "TENSION_ECONOMY_RATE":         (0.1, 1.5),
    "POPULATION_GROWTH_RATE":       (0.5, 8.0),
    "ECONOMY_TENSION_PENALTY_RATE": (0.1, 1.5),
    "ECONOMY_FLOOR":                (2.0, 15.0),
    # ... etc.
}
```

### Tuning Algorithm

When an invariant fails:

1. **Classify** — Is it a "code bug" (invariant says `governing_configs` is empty → always escalate) or a "tuning issue" (has governing configs)?

2. **Prioritize** — If multiple invariants fail, sort by severity (critical first), then by number of shared governing configs (fix the config that affects the most failures first).

3. **Propose** — For each governing config of the failing invariant:
   - Look up the direction hint from `CONFIG_EFFECTS`
   - Compute a step size: `current_value * 0.15` (15% adjustment)
   - Clamp to `CONFIG_BOUNDS`
   - If two failing invariants want opposite directions for the same config → **escalate** (this is a design tension, not a simple tuning issue)

4. **Test** — Re-run the scenario with the proposed config change. Check if:
   - The failing invariant now passes
   - No previously-passing invariants now fail (regression check)

5. **Report** — Output a structured report:

```python
@dataclass
class TuningReport:
    scenario: str
    seed: int
    total_invariants: int
    passed: int
    failed: int
    
    failures: list[InvariantResult]          # all failing invariants
    proposed_changes: list[ConfigChange]      # what the tuner wants to adjust
    conflicts: list[str]                      # invariants wanting opposite directions on same config
    escalations: list[str]                    # issues that need human review
    
    # After re-run with proposed changes:
    retest_passed: bool | None               # None if not yet tested
    regressions: list[str]                   # invariants that broke after applying changes

@dataclass 
class ConfigChange:
    config_key: str
    old_value: float
    proposed_value: float
    direction: str
    triggered_by: list[str]     # invariant names that motivated this change
    confidence: str             # "high" | "medium" | "low"
```

### Autonomy Levels

The tuning loop supports three autonomy modes, set by a flag:

- **`report_only`** (default) — Run invariants, report failures, propose changes. Do not apply anything. This is the starting mode. Claude Code outputs the report; Westley reviews.

- **`propose_and_test`** — Run invariants, propose changes, re-run with changes, report whether the fix worked. Still does not persist config changes. Claude Code shows before/after.

- **`auto_tune`** — Full autonomous loop. Apply changes, re-run, verify no regressions, persist to `config.py` if all invariants pass. This mode should only be enabled once Westley trusts the invariant coverage.

---

## Part 4: Entry Point (`test_validate.py`)

### CLI Interface

```bash
# Run all scenarios, check all invariants, output report
python test_validate.py

# Run specific scenario
python test_validate.py 04_four_way

# Run with auto-tune (propose + test, don't persist)
python test_validate.py --mode propose_and_test

# Run multi-seed divergence check
python test_validate.py --seeds 3

# Run only specific invariant groups  
python test_validate.py --groups A,D,E

# List all invariants
python test_validate.py --list-invariants
```

### Output Format

The report prints to terminal in a clear format:

```
══════════════════════════════════════════════════════════════
  Simulation Validator — Ouroboros Manifold
  Scenario: 04_four_way  |  Seed: 1  |  Ticks: 500
══════════════════════════════════════════════════════════════

  ✓ A1 no_field_flatline
  ✓ A2 no_premature_collapse
  ✓ A3 fields_stay_bounded
  ✗ A4 frontier_more_volatile_than_home
      WARN: fortifier frontier std_dev(economy)=2.3, home std_dev(economy)=4.1
      → Frontier should be MORE volatile, not less. 
      → Governing: FRONTIER_POPULATION_RANGE, STARTING_MIL_RATIO
  ✓ B1 economy_recovers_from_famine
  ...
  ✗ D2 conqueror_attacks_eventually
      CRIT: conqueror launched 0 attacks in 150 ticks. Budget at tick 150: 3.2.
      → Budget growth too slow to reach attack threshold.
      → Governing: BUDGET_GROWTH_RATE (current: 0.012), ATTACK_CONFIDENCE_RANGE
      → Proposed: BUDGET_GROWTH_RATE 0.012 → 0.014

──────────────────────────────────────────────────────────────
  SUMMARY: 18/22 passed  |  2 critical  |  2 warning
  Proposed changes: 1 config adjustment
  Escalations: 0
══════════════════════════════════════════════════════════════
```

### Also: PNG graph generation continues as before

The validator calls `sim_tuner.py`'s graph generation alongside the invariant check, so Westley still gets the visual output for any run. The invariant report tells you *what's wrong*; the graphs show you *what it looks like*.

---

## Implementation Order for Claude Code

### Phase 1: Foundation (do first)

1. Create `sim_validator.py` with `TrajectoryLog`, `TickSnapshot`, and `InvariantResult` dataclasses
2. Implement `run_recorded_scenario()` — same flow as `sim_tuner.py:run_scenario()` but captures `TrajectoryLog`
3. Implement all query helpers on `TrajectoryLog` (`field_series`, `budget_series`, etc.)
4. Write a smoke test: run scenario `03_contested` for 50 ticks, print the trajectory log summary

**Checkpoint: Westley verifies the trajectory log captures correct data by comparing it to existing terminal output.**

### Phase 2: Core Invariants (do second)

5. Create `invariants.py` with the `InvariantResult` format
6. Implement Group A invariants (A1–A4) — these are the most fundamental
7. Implement Group D invariants (D1–D4) — budget/agent behavior, catches the sawtooth class of bugs
8. Implement Group E invariants (E1–E4) — combat correctness
9. Create `test_validate.py` entry point — run all scenarios, check all implemented invariants, print report
10. Run against current codebase. Expect all invariants to pass (since Westley just tuned these). If any fail, investigate — it means the invariant thresholds need calibration or there's a real issue.

**Checkpoint: Westley reviews the first report. Calibrate any invariant thresholds that are too tight or too loose.**

### Phase 3: Remaining Invariants (do third)

11. Implement Groups B, C, F, G (economy dynamics, military, border friction, colonization)
12. Implement Group H (trajectory shape — oscillation, divergence, stochastic spread)
13. Implement Group I (technology — only runs when `ENABLE_TECHNOLOGY=True`)
14. Full run across all 5 scenarios. Report should be clean.

**Checkpoint: Westley reviews the full report. All invariants should pass. If any don't, discuss whether the invariant or the simulation needs adjusting.**

### Phase 4: Tuning Loop (do last)

15. Create `tuning_loop.py` with `CONFIG_EFFECTS`, `CONFIG_BOUNDS`, and the diagnosis algorithm
16. Implement `report_only` mode — fails just get reported with proposed changes
17. Implement `propose_and_test` mode — re-run with proposed changes, check for regressions
18. Test by deliberately breaking a config value (e.g., set `BUDGET_GROWTH_RATE = 0.001`) and verifying the tuner identifies and proposes the correct fix

**Checkpoint: Westley verifies the tuner's proposals are sensible. If approved, enable `auto_tune` mode.**

---

## File Protection Policy

**CRITICAL CONSTRAINT: The tuning system may ONLY modify `config.py`. It must NEVER modify any other engine file.**

This is the single most important rule in the entire system. The tuning loop exists to adjust numeric parameters. It does not exist to fix code. The following files are **read-only** to the tuning system and must never be edited by any automated process:

```
PROTECTED FILES — do not modify:
  region.py
  drift.py
  faction.py
  tick.py
  events.py
  event_engine.py
  intent_resolver.py
  border_friction.py
  technology.py
  diplomacy.py
  world.py
  templates.py
  theme_scifi.py
  (and any future engine files)

TUNING-WRITABLE — the ONLY file the tuning loop may edit:
  config.py
```

### Enforcement

The tuning loop (`tuning_loop.py`) must enforce this at the code level:

```python
WRITABLE_FILES = {"config.py"}

def apply_config_change(key: str, value: float) -> None:
    """The ONLY mutation the tuning system is allowed to make."""
    assert hasattr(config, key), f"Unknown config key: {key}"
    assert key in CONFIG_BOUNDS, f"Config key {key} has no defined safe bounds"
    lo, hi = CONFIG_BOUNDS[key]
    assert lo <= value <= hi, f"{key}={value} outside bounds [{lo}, {hi}]"
    setattr(config, key, value)
```

There is no function for editing any other file. The tuning loop has no file-write capability beyond `config.py`. If a code change is needed, the system outputs a report describing the problem, and Westley makes the change.

### What happens when the tuning loop can't fix a failure through config

If all governing configs have been adjusted to their bounds and the invariant still fails, the report must say:

```
ESCALATION REQUIRED — cannot resolve through config tuning alone.
  Invariant: [name]
  Attempted: [list of config changes tried]
  Result: still failing after exhausting config bounds
  
  This likely requires a code change to: [file(s) involved based on the invariant]
  Westley must review and decide.
```

The tuning system stops. It does not attempt to "help" by editing game code. It waits.

### Why this matters

Config values are safe to experiment with — they're numbers with known bounds, and reverting is trivial (restore the previous value). Engine code changes can introduce subtle bugs, break invariants that were passing, and create states that are hard to roll back from. The entire value proposition of this tuning system is that it can iterate quickly on config without risking the codebase.

---

## Invariant Modification Policy

**The validator files (`sim_validator.py`, `invariants.py`, `tuning_loop.py`, `test_validate.py`) are owned by Claude Code — but modifications to invariants that weaken them require Westley's approval.**

The File Protection Policy above covers engine files. This section covers the validator's *own* files, which present a different and more subtle risk: Claude Code may "fix" a failing invariant by loosening it, making a real problem invisible.

### The Three Valid Responses to a Failing Invariant

When an invariant fails, there are exactly three valid responses. Claude Code must classify every failure into one of these categories before acting:

**Response 1: Tune config.** The invariant correctly identified a behavioral problem. The fix is adjusting a config value. Claude Code may do this autonomously within the bounds defined by the tuning loop. No invariant code changes.

**Response 2: Escalate to Westley.** The invariant correctly identified a problem that cannot be fixed through config — it's a code bug, a design flaw, or a conflict between competing goals. Claude Code reports it and stops. No invariant code changes, no engine code changes.

**Response 3: Recalibrate the invariant.** The invariant itself has a bug — it's testing the wrong condition, using a threshold that's too tight, or checking state that doesn't apply (e.g., checking empty regions that have no fields). The invariant code needs to change. **This is the dangerous case.**

### Rules for Response 3 (Invariant Recalibration)

Claude Code MAY fix an invariant without approval ONLY if ALL of the following are true:

1. **The fix is purely additive scope reduction** — skipping a case the invariant was never meant to check. Examples: skipping empty-tier regions in a field health check, skipping factions with zero regions, skipping runs shorter than the invariant's minimum window. The invariant still checks everything it was designed to check; it just stops checking things that are out of scope.

2. **The fix does not change the pass threshold for in-scope cases.** Widening a tolerance (±0.5 → ±3.0), raising a tick window (60 → 120), lowering a required count — these all make the invariant more permissive for cases it *is* supposed to catch. These changes require approval.

3. **The fix does not reclassify a finding from "real" to "skip."** If Claude Code investigates a failure and concludes "this is a real bug in the engine, but I'll adjust the invariant to not flag it" — that is never acceptable. That is papering over a bug. The correct response is Response 2: escalate.

**If any of those conditions are NOT met, Claude Code must stop and present the proposed invariant change to Westley before applying it.** The presentation must include:

```
INVARIANT RECALIBRATION REQUEST
  Invariant: [name]
  Current behavior: [what the invariant checks now]
  Proposed change: [what Claude Code wants to change and why]
  
  Failing case that triggered this:
    Scenario: [name], Seed: [N], Tick: [T]
    Details: [what the invariant found]
  
  Classification:
    [ ] Scope reduction (skip out-of-scope case) — auto-approve candidate
    [x] Threshold change (widen tolerance / extend window) — NEEDS REVIEW
    [ ] Finding reclassification (real issue → skip) — NEVER ALLOWED
  
  Risk: [what real problems might this change mask?]
```

### Why This Matters

The invariant library is the system's definition of "working correctly." If Claude Code can freely weaken invariants, the system degrades over time — each loosening makes the definition of "correct" a little more permissive, until the invariants pass on broken simulations. This is the equivalent of deleting unit tests to make the build green.

The specific failure mode from the first run illustrates this perfectly: Claude Code found that the conqueror was attacking empty regions (a real decision-logic bug in `faction.py`), but instead of escalating, it adjusted invariant E1 to skip attacks with `deltas=None`. The bug is now invisible to the validator. The correct response was:

```
ESCALATION REQUIRED
  E1 found: conqueror attacking uninhabited region_e1 with no damage deltas.
  Root cause: faction.decide() scores uninhabited regions as attack candidates
              instead of colonize candidates when diplomatic stance check passes
              vacuously (no faction to be hostile toward).
  This is a code bug in faction.py, not a config issue.
  Westley must review.
```

### Summary Table

| Situation | Claude Code may act autonomously? | Example |
|-----------|-----------------------------------|---------|
| Config value needs adjusting | Yes (within bounds) | BUDGET_GROWTH_RATE too low |
| Engine code has a bug | No — escalate | Conqueror attacks empty regions |
| Invariant checks out-of-scope case | Yes — narrow scope | Skip empty-tier regions |
| Invariant threshold too tight | No — request approval | Flatline tolerance ±0.5 → ±3.0 |
| Invariant catches real bug but Claude Code wants to skip it | **Never** | E1 skip attacks with no deltas |

---

## Design Principles

1. **Invariants are conservative.** It's better to have an invariant that passes when it shouldn't (false negative) than one that fails when it shouldn't (false positive). False positives erode trust in the system.

2. **The tuning loop is cautious.** 15% config adjustments per iteration, never outside bounds, always regression-tested. One change at a time.

3. **Conflicts escalate to Westley.** When two invariants want opposite config directions, that's a design tension — it means the system has competing goals, and a human needs to decide the priority.

4. **Code bugs always escalate.** If an invariant with no governing configs fails (like `fields_stay_bounded` or `attacks_produce_damage`), that's a code defect, not a tuning issue. The report flags it clearly.

5. **The system is additive.** New invariants can be added at any time. When a new behavior is expected (e.g., after implementing a new stage), add invariants that capture it. The library grows with the simulation.

6. **Determinism is sacred.** All runs use seeded RNG. Every invariant failure is reproducible. The trajectory log captures the exact config state, so any failure can be re-investigated.
