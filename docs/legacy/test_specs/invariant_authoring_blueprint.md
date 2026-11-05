# Invariant Authoring Blueprint — How to Validate New Game Mechanics

## Purpose

This document teaches a future Claude Code session (or any implementer) how to extend the simulation validator when new mechanics are added to Ouroboros Manifold. It explains the methodology used to build the original invariant library so the same approach can be applied to any future game system — diplomacy evolution, lifecycle stages, era transitions, chronicle triggers, mission systems, or anything else.

This is not a spec for a specific feature. It's a reusable recipe.

---

## The Core Idea

Every game mechanic produces **observable behavioral consequences** in the simulation's field values, faction states, and event logs over time. An invariant is a formal statement that one of these consequences **should always hold** (or should never happen). When you add a new mechanic, your job is to answer: "What should always be true if this mechanic is working correctly?" Then encode those answers as invariant functions.

---

## Step 1: Identify the Behavioral Claims

Before writing any code, list the behavioral claims the new mechanic makes. These come from the game bible and the stage spec. Every mechanic implies a set of "if X then Y" statements about what the simulation should do.

**How to extract claims from a spec:**

Read the spec and highlight every sentence that describes a *consequence* — something that happens as a result of the mechanic operating. Ignore implementation details (data structures, function signatures). Focus on outcomes.

**Example — if the new mechanic is "faction lifecycle stages":**

The spec might say:
- "A faction in the Growth stage should expand territory faster than one in Decline."
- "When a faction enters Decline, its economy growth rate should slow."
- "A faction cannot enter Ascendancy unless it controls at least 5 regions."
- "The transition from Growth to Peak should take at least 50 ticks."

Each of these is a behavioral claim that becomes one or more invariants.

**Template for listing claims:**

```
Mechanic: [name]
Config keys introduced: [list all new config.py values]
Fields/state affected: [which region fields, faction attributes, or logs change]

Claim 1: [plain English statement of what should happen]
  When: [trigger condition]
  Then: [expected outcome]
  Over: [time window — "immediately", "within N ticks", "over the full run"]
  
Claim 2: ...
```

---

## Step 2: Classify Each Claim into an Invariant Pattern

Every behavioral claim maps to one of three invariant patterns. Pick the right one:

### Pattern A: Threshold Bound

**Use when:** The claim says a value should stay within a range, or should never reach an extreme for too long.

**Shape:** "Field F for faction/region X should never be [above/below] V for more than T consecutive ticks [under condition C]."

**Template:**

```python
def invariant_name(log: TrajectoryLog) -> InvariantResult:
    for faction_id in log.all_faction_ids():
        series = log.field_series(faction_id, "field_name")
        
        # Count consecutive ticks violating the threshold
        consecutive = 0
        worst_tick = None
        for tick, value in enumerate(series):
            # Optional: check condition C first
            if not _condition_holds(log, faction_id, tick):
                consecutive = 0
                continue
            if value [< or >] THRESHOLD:
                consecutive += 1
                if consecutive > MAX_CONSECUTIVE:
                    worst_tick = tick
                    break
            else:
                consecutive = 0
        
        if worst_tick is not None:
            return InvariantResult(
                name="invariant_name",
                passed=False,
                severity="critical" or "warning",
                message=f"...",
                details={
                    "tick": worst_tick,
                    "faction_id": faction_id,
                    "field": "field_name",
                    "actual_value": series[worst_tick],
                    "threshold": THRESHOLD,
                    "consecutive_ticks": consecutive,
                    "governing_configs": ["CONFIG_KEY_1", "CONFIG_KEY_2"],
                }
            )
    
    return InvariantResult(name="invariant_name", passed=True, ...)
```

**Examples from the original library:** A1 (no_field_flatline), A2 (no_premature_collapse), C2 (recruitment_prevents_military_zero), D4 (budget_pressure_prevents_hoarding)

### Pattern B: Relational Constraint

**Use when:** The claim says one measurement should be greater/less than another, or two things should correlate/diverge.

**Shape:** "Measurement A should be [greater than / less than / correlated with] Measurement B [under condition C] [over window W]."

**Template:**

```python
def invariant_name(log: TrajectoryLog) -> InvariantResult:
    # Compute measurement A
    measure_a = _compute_metric(log, ...)
    
    # Compute measurement B  
    measure_b = _compute_metric(log, ...)
    
    # Compare
    if not (measure_a [> or < or correlates_with] measure_b):
        return InvariantResult(
            name="invariant_name",
            passed=False,
            severity="warning",
            message=f"Expected A ({measure_a:.2f}) > B ({measure_b:.2f}), got opposite",
            details={
                "measure_a": measure_a,
                "measure_b": measure_b,
                "governing_configs": ["CONFIG_KEY_1"],
            }
        )
    
    return InvariantResult(name="invariant_name", passed=True, ...)
```

**Examples from the original library:** A4 (frontier_more_volatile_than_home), D3 (player_civ_is_conservative), F1 (border_friction_raises_tension), I1 (tech_grows_with_economy)

### Pattern C: Trajectory Shape Predicate

**Use when:** The claim says the system should *respond* to a condition — something should trend upward, recover, converge, or diverge after a trigger.

**Shape:** "After condition C holds for T ticks, field F should [increase / decrease / recover to V] within W ticks."

**Template:**

```python
def invariant_name(log: TrajectoryLog) -> InvariantResult:
    series = log.field_series(faction_id, "field_name")
    
    # Find windows where the trigger condition holds for T+ ticks
    trigger_windows = _find_windows(log, faction_id, 
                                      condition_fn, 
                                      min_duration=T)
    
    for window_start, window_end in trigger_windows:
        # Check the response in the W ticks after the trigger window
        response_start = window_end
        response_end = min(window_end + W, len(series))
        response = series[response_start:response_end]
        
        if not _expected_response(response):  
            # e.g., "average delta should be positive" or "should reach value V"
            return InvariantResult(
                name="invariant_name",
                passed=False,
                severity="critical",
                message=f"...",
                details={
                    "trigger_window": (window_start, window_end),
                    "response_window": (response_start, response_end),
                    "trajectory_excerpt": response,
                    "governing_configs": ["CONFIG_KEY_1"],
                }
            )
    
    return InvariantResult(name="invariant_name", passed=True, ...)
```

**Examples from the original library:** B1 (economy_recovers_from_famine), B3 (tension_responds_to_economy), C1 (military_decays_without_economy), H1 (oscillation_present)

### Special Pattern: Cross-Run Comparison

**Use when:** The claim is about stochastic divergence — different seeds should produce different outcomes.

**Shape:** "Running with N different seeds should produce meaningfully different [metric]."

This invariant doesn't run on a single TrajectoryLog. It runs across multiple logs. The test runner handles this by running the same scenario N times with different seeds and passing all N logs to the invariant.

**Example from the original library:** H3 (stochastic_divergence_across_seeds)

---

## Step 3: Define Governing Configs and Direction Hints

For each invariant, identify which `config.py` values control the behavior being tested. Ask: "If this invariant fails, which config knob would I turn to fix it, and in which direction?"

**Rules:**

- If the invariant tests a behavior that's purely code logic (ownership transfer, field clamping), there are no governing configs. A failure is a code bug — always escalate.
- If the invariant tests a tunable behavior (growth rate, threshold, scaling factor), list the 1–3 most relevant config keys.
- For each config key, specify the direction: "increase" means raising the config value should help the invariant pass; "decrease" means lowering it.
- If two invariants want opposite directions on the same config, that's a design tension. Flag it explicitly in the CONFIG_EFFECTS map with a comment.

**Template for adding to `tuning_loop.py`:**

```python
# In CONFIG_EFFECTS, add entries for each new config key:
"NEW_CONFIG_KEY": {
    "new_invariant_1": "increase",   # raising this value helps invariant_1 pass
    "new_invariant_2": "decrease",   # but lowering it helps invariant_2 pass ← TENSION
},

# In CONFIG_BOUNDS, add safe ranges:
"NEW_CONFIG_KEY": (min_safe_value, max_safe_value),
```

---

## Step 4: Determine Severity

- **Critical:** The invariant tests something that, if violated, means the simulation is producing nonsensical or broken output. Field clamping violations, ownership not transferring on conquest, budget resetting unexpectedly. A critical failure blocks further tuning — fix it first.

- **Warning:** The invariant tests a qualitative behavior that should hold but isn't catastrophic if it doesn't. Frontier-vs-home volatility, archetype personality differences, oscillation detectability. A warning means "this is suboptimal, tune it when you can."

- **Info:** Reserved for metrics you want to track but that don't have a pass/fail threshold. "Average conqueror attack frequency: 1 per 47 ticks." Useful for dashboards, not for automated tuning.

**Rule of thumb:** If a human looking at the simulation output would say "that's broken," it's critical. If they'd say "that doesn't feel right," it's a warning.

---

## Step 5: Calibrate Thresholds

This is the hardest part and the one most likely to need iteration. Every invariant has numeric thresholds (how many ticks, what value range, what correlation strength). These need to be calibrated against actual simulation runs.

**Process:**

1. Write the invariant with your best-guess thresholds based on the spec and your understanding of the sim.
2. Run it against 3–5 seeds of the relevant scenario.
3. If it passes all seeds: good, but consider tightening.
4. If it fails some seeds: examine the failures. Is the invariant wrong (threshold too tight) or is the sim wrong (genuine issue)?
5. If it fails all seeds: either the threshold is way off, or the mechanic genuinely doesn't work yet.

**Thresholds should be generous at first, then tightened over time.** A lenient invariant that catches real bugs is infinitely better than a strict invariant that cries wolf.

---

## Step 6: Register and Group

Add new invariants to `invariants.py` following the existing group structure:

```python
# ── Group [LETTER]: [Mechanic Name] ────────────────────────────────────

def [group_letter][number]_[descriptive_name](log: TrajectoryLog) -> InvariantResult:
    """[One-line description of what this checks.]"""
    ...
```

Add the new group letter to the `INVARIANT_GROUPS` registry:

```python
INVARIANT_GROUPS = {
    "A": [a1_no_field_flatline, a2_no_premature_collapse, ...],
    "B": [b1_economy_recovers_from_famine, ...],
    # ...
    "J": [j1_new_mechanic_invariant, j2_another_invariant, ...],  # ← new group
}
```

This lets the CLI filter by group: `python test_validate.py --groups J` to run only the new mechanic's invariants during development.

---

## Step 7: Add Scenario Coverage

If the new mechanic needs its own test scenario (not already covered by existing ones), add it to `sim_tuner.py`'s `SCENARIOS` dict:

```python
"06_new_mechanic": {
    "template":     "...",
    "ticks":        ...,
    "seed":         1,
    "description":  "...",
    "use_tick_engine": True,
    "features": {
        # ... enable the new mechanic's feature flag
    },
    "overrides": {},
},
```

The validator will automatically pick it up and run all applicable invariants against it.

---

## Worked Example: Adding Invariants for a Hypothetical "War Weariness" Mechanic

Suppose a future stage adds war weariness: factions that fight too many consecutive battles suffer escalating tension and economy penalties.

### Step 1: Behavioral Claims

```
Mechanic: War Weariness
Config keys: WAR_WEARINESS_THRESHOLD (consecutive attacks before penalty kicks in),
             WAR_WEARINESS_TENSION_RATE (tension added per battle beyond threshold),
             WAR_WEARINESS_ECONOMY_RATE (economy lost per battle beyond threshold),
             WAR_WEARINESS_DECAY_RATE (how fast weariness fades during peace)
Fields affected: tension (increase), economy (decrease), faction.weariness_counter (new)

Claim 1: Factions that attack more than WAR_WEARINESS_THRESHOLD times in 50 ticks 
         should have higher tension than peaceful factions.
  When: attack count in trailing 50-tick window > threshold
  Then: avg tension should be at least 10 points higher than a faction with 0 attacks
  Over: any 50-tick window
  
Claim 2: War weariness should decay during peace.
  When: a faction stops attacking for 30+ ticks after being above threshold
  Then: weariness_counter should decrease toward 0
  Over: the 30-tick peace window
  
Claim 3: The conqueror archetype should trigger war weariness more often than fortifier.
  When: both factions have hostile borders and similar territory
  Then: conqueror's weariness_counter should be higher on average
  Over: full run

Claim 4: War weariness should not make factions completely unable to fight.
  When: weariness is at maximum
  Then: faction should still be able to launch attacks (just with penalties)
  Over: any tick
```

### Step 2: Classify

- Claim 1 → **Pattern B** (relational: warring faction tension > peaceful faction tension)
- Claim 2 → **Pattern C** (trajectory shape: after peace period, weariness should trend down)
- Claim 3 → **Pattern B** (relational: conqueror weariness > fortifier weariness)
- Claim 4 → **Pattern A** (threshold: even at max weariness, attacks should still be possible)

### Step 3: Governing Configs

```python
"WAR_WEARINESS_TENSION_RATE": {
    "j1_warring_faction_higher_tension": "increase",
},
"WAR_WEARINESS_DECAY_RATE": {
    "j2_weariness_decays_during_peace": "increase",
},
"WAR_WEARINESS_THRESHOLD": {
    "j1_warring_faction_higher_tension": "decrease",   # lower threshold = triggers more easily
    "j3_conqueror_more_weary_than_fortifier": "decrease",
},
```

### Step 4: Severity

- Claim 1 → **warning** (qualitative behavior)
- Claim 2 → **critical** (if weariness never decays, factions get permanently crippled — broken)
- Claim 3 → **warning** (archetype personality difference)
- Claim 4 → **critical** (if factions can't fight at all, the game stalls)

### Step 5: Calibrate

Run scenario `04_four_way` with war weariness enabled, 3 seeds. Check that Claim 1's "10 points higher" threshold is reasonable. Maybe it's 15 on some seeds and 5 on others — adjust the threshold to 5 so it passes consistently.

---

## Extending the TrajectoryLog

If the new mechanic introduces state that the existing `TickSnapshot` doesn't capture, extend it:

```python
# In sim_validator.py, add to TickSnapshot:
@dataclass
class TickSnapshot:
    # ... existing fields ...
    custom_state: dict    # {key: value} for mechanic-specific state
```

Then add a query helper to `TrajectoryLog`:

```python
def custom_series(self, key: str) -> list:
    """Return [custom_state[key] at tick 0, at tick 1, ...] for a custom tracked value."""
    return [snap.custom_state.get(key) for snap in self.snapshots]
```

The capture function in `run_recorded_scenario()` populates `custom_state` from whatever the new mechanic exposes. Keep it generic — the recorder doesn't need to know what the mechanic is, just what values to grab.

---

## Checklist: Adding Invariants for a New Mechanic

Use this checklist every time you add a new mechanical system to the simulation:

- [ ] Read the spec and game bible section for the new mechanic
- [ ] List all behavioral claims (Step 1)
- [ ] Classify each claim into a pattern: threshold, relational, or trajectory shape (Step 2)
- [ ] Identify governing config keys and direction hints (Step 3)
- [ ] Assign severity: critical or warning (Step 4)
- [ ] Write the invariant functions in `invariants.py` under a new group
- [ ] Add config entries to `CONFIG_EFFECTS` and `CONFIG_BOUNDS` in `tuning_loop.py`
- [ ] Add a test scenario to `sim_tuner.py` if needed
- [ ] Run against 3+ seeds; calibrate thresholds (Step 5)
- [ ] Extend `TickSnapshot` if the mechanic introduces new tracked state
- [ ] Register the new group in `INVARIANT_GROUPS`
- [ ] Verify all existing invariants still pass (regression check)
