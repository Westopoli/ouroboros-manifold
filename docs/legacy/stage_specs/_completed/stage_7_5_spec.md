# Stage 7.5 — Enemy Macro Behavior Scripts

## Goal

Prove that the enemy's tactical behavior in missions can be fully authored as JSON state-machine scripts consumed by a shared Python runner — no per-archetype engine code, no special enemy-only commands. The runner reads each archetype's script, drives a state machine per enemy force group, evaluates timer + threshold + noise transitions every ~2 seconds, and dispatches the same 4-command vocabulary the player uses to the tactical engine. Stage 7.5 ships the runner, the schema, the condition expression language, four prototype archetype scripts (Defensive Stand, Assault, Multi-Front Defense, Counterinsurgency) covering all five base behaviors and exercising the trigger bus + ambush / sensor-interference patterns, and the four prototype archetype reinforcement-ownership baselines that override Stage 7's uniform 33/33/33 fallback.

Stage 7.5 sits between Stage 7 (procedurally generated maps + reinforcement structures) and Stage 8 (Godot renderer + command interface + persistence). After Stage 7.5, every prototype-archetype mission the simulation generates produces a tactically alive enemy that runs an authored plan, reacts to the player, and coordinates across multiple forces — instead of Stage 7's placeholder `attack_move` enemies.

**Not in scope:** the remaining 6 archetype scripts (Siege Breaking, Reconquest, Suppression, Interception, Evacuation, Containment — authored in a follow-up pass once the prototype set validates the vocabulary), Godot renderer / command UI (Stage 8), persistence (Stage 8), mission complications (deferred per Stage 7 design session), tuning of script timer ranges and threshold percentages (config tuning, post-stage), external reinforcement events (rare authored complications, deferred per bible).

**Architecture.** The behavior runner is a thin orchestrator. Per mission, it loads one JSON script per enemy force group, instantiates a state machine, and ticks at the script-eval cadence (~2 sec, config). Each tick: evaluate active state's transitions (threshold + timer + reactive hooks) against the trigger bus and tactical-state predicates; if a transition fires, switch state and emit any required engine commands; otherwise re-emit the active state's commands if they need refreshing. The runner reads tactical state through a documented interface (force HP fractions, unit positions, structure ownership, trigger-bus flags) — it never reaches into engine internals.

## Bible References

- **`docs/bible_history/bible_2_00_combat.md`** — §Enemy Macro Behavior System (full section: 5 base behaviors, 3 modifiers, transitions, trigger bus, multi-force coordination, relationship to Unit Behavior AI), §Command Vocabulary (the 4 commands the runner emits), §Tactical Reinforcement System (structure ownership baselines that the prototype scripts reference).
- **`docs/bible_history/bible_2_00_missions.md`** — §Mission Archetypes #1 Defensive Stand, #4 Assault, #6 Multi-Front Defense, #10 Counterinsurgency (the four prototype archetype tactical-feel descriptions that drive script content).
- **`game_bible.md` (hub)** — Sacred Design Principles (era-agnostic architecture: scripts reference abstract behaviors, never era-specific unit names).

Do NOT read `docs/bible_history/bible_2_00_world.md` (map-gen handled by Stage 7), `docs/bible_history/bible_2_00_chronicle.md`, `docs/bible_history/bible_2_00_simulation.md`, `docs/bible_history/bible_2_00_antagonist.md`, `bible_monetization.md` (deleted 2026-05-31; see docs/bible_history/), `docs/bible_history/bible_2_00_ai_pipeline.md` — not relevant to Stage 7.5.

## Cross-Stage References

- **Stage 6** — runner emits `move`, `attack_move`, `attack_target`, `activate_ability` commands through the existing engine command protocol. Engine code unchanged. Determinism preserved (same script + same seed + same player commands → same enemy commands tick-for-tick).
- **Stage 7** — runner reads `TacticalMap.spine_nodes` to position forces relative to authored map structure (objectives, chokepoints, ambush zones, vantage nodes). Stage 7's reinforcement structure system + the S7-5 simulation-state delta operate on top of Stage 7.5's authored ownership baselines (Stage 7 had a uniform 33/33/33 fallback; Stage 7.5 overrides with the 4 prototype baselines). Stage 7's `archetype_filters.py` is extended with the per-archetype baselines.
- **Stage 8** — no direct dependency. Stage 8 renders enemy commands the same way it renders player commands; behavior scripts are server-side and invisible to the renderer.
- **Beyond Stage 7.5** — the 6 non-prototype archetype scripts and their ownership baselines are authored in a follow-up pass once the prototype set validates the vocabulary. Stage 7.5 ships them as stubs that fall back to a generic `advance_cautious → advance_aggressive` script and the 33/33/33 ownership fallback.

## What to Build

### Files to create

**`behavior_runner.py`** — The shared state-machine orchestrator. One instance per enemy force group per mission.
- `BehaviorRunner(script: dict, force_id: str, engine: TacticalEngine, trigger_bus: TriggerBus)` — constructor; loads the JSON script, validates against the schema, instantiates the initial state.
- `evaluate(tick: int) → list[Command]` — called every `SCRIPT_EVAL_INTERVAL_TICKS` (config; ~2 sec at 20 Hz = 40 ticks). Evaluates the active state's transitions in priority order (survival → threshold → timer per `docs/bible_history/bible_2_00_combat.md`); on match, switches state and emits any required commands; otherwise re-emits the active state's commands if the engine-side command queue has drained.
- `is_terminal() → bool` — returns True when the script reaches a terminal state (force destroyed, retreated off-map, mission ended).
- Reactive hooks evaluate independently of state transitions on each `evaluate()` call; a fired hook may trigger an immediate state switch outside the normal transition flow.

**`condition_language.py`** — The restricted expression language for transition conditions and reactive hook predicates. Not arbitrary Python.
- Supported primitives: numeric comparisons (`<`, `<=`, `==`, `>=`, `>`), boolean logic (`and`, `or`, `not`), trigger-bus flag access (`bus.<flag_name>`), tactical-state predicates (`force_hp_fraction`, `force_unit_count`, `enemy_unit_in_range(zone_id, radius_wu)`, `player_force_hp_fraction_in_zone(zone_id)`, `structure_owner(structure_id)`), timer access (`timer.elapsed_sec`, `timer.expired`), and literal numbers / strings / booleans.
- `evaluate(expression: str, context: EvaluationContext) → bool | float` — parses the expression once (cached), then evaluates against the runtime context.
- `validate(expression: str) → list[ValidationError]` — schema-time pass that catches stale flag references, undefined predicates, and syntax errors before runtime.
- Implementation: a small recursive-descent parser producing an AST, plus a tree walker. Not a full Python `eval` — that's a security and reasoning hazard.

**`script_schema.py`** — JSON schema definition + validator for behavior script files.
- Schema fields: `script_id`, `archetype`, `forces[]` (each with `force_id`, `composition_template`, `initial_state`, `states{}` keyed by state name), `trigger_bus_vocabulary[]` (declared flag names — referenced flags not in this list are validation errors), `terminal_states[]`.
- Per-state fields: `behavior` (one of advance/defend/patrol/ambush/retreat), `modifier` (cautious/aggressive/phased), `target_resolution` (spine-node-id / map-position / waypoint-list / dynamic), `transitions[]`, `reactive_hooks[]`.
- Per-transition fields: `condition` (expression string), `to_state`, `noise_pct` (the per-mission noise applied to numeric thresholds in the condition).
- `validate_script(script_dict) → list[ValidationError]` — runs all schema checks: dead states, missing transitions out of non-terminal states, stale flag references, undefined target nodes (cross-validated against a layout's spine_node ids when available), missing initial state, unreachable states.

**`trigger_bus.py`** — Lightweight shared mission-state dictionary.
- `TriggerBus()` — constructor; mission-scoped instance.
- `set_flag(name: str)`, `clear_flag(name: str)`, `get_flag(name: str) → bool`.
- `set_value(name: str, value: float | str)`, `get_value(name: str)`.
- The bus is read by every force's behavior runner; writes from one force are visible to all others on the next `evaluate()` call. No write contention (single-threaded engine).

**`force_composition.py`** — Per-archetype enemy force composition templates.
- `COMPOSITION_TEMPLATES: dict[str, dict[str, float]]` — keyed by archetype, value is the unit-type-to-ratio dict (e.g., Defensive Stand: `{"vanguard": 0.35, "raider": 0.20, ...}`).
- `instantiate_force(template_name: str, total_power: float, count_split: list[float] | None) → list[list[Unit]]` — given a template, total power budget (from the force-allocation system), and an optional split (e.g., `[0.6, 0.4]` for two forces), produces concrete unit lists per force preserving ratios and total power within ±5%.

**`scripts/`** — JSON behavior script files.
- `defensive_stand.json` — Force A (main thrust) + Force B (flanker), per DQ-A capture in `docs/legacy/design_questions/stage_7_8_design.md`.
- `assault.json` — Force A (garrison) + Force B (reserve), per DQ-B.
- `multi_front_defense.json` — 2-force and 3-force variants selected at mission start by approach-vector count, per DQ-C.
- `counterinsurgency.json` — Variable cell count via fragmentation roll (Concentrated / Dispersed / Fragmented), per DQ-D.
- `_stub_default.json` — Generic `advance_cautious → advance_aggressive` two-state script. Used as the fallback for the 6 non-prototype archetypes until their dedicated scripts land.

**`script_loader.py`** — Loader + per-archetype dispatcher.
- `load_script(archetype: str) → dict` — returns the parsed JSON for the named archetype, validated. Falls back to `_stub_default.json` for non-prototype archetypes with a logged warning.
- `load_all_scripts() → dict[str, dict]` — eager preload at engine start; catches schema errors before mission generation.

**Test files** (alongside each system): `test_behavior_runner.py`, `test_condition_language.py`, `test_script_schema.py`, `test_trigger_bus.py`, `test_force_composition.py`, `test_script_defensive_stand.py`, `test_script_assault.py`, `test_script_multi_front.py`, `test_script_counterinsurgency.py`, `test_stage7_5_integration.py`.

### Files to modify

**`archetype_filters.py`** (Stage 7) — Extend with per-archetype reinforcement-ownership baselines for the 4 prototypes. Stage 7 ships with uniform `{0.33, 0.33, 0.34}` for all 10. Stage 7.5 adds:
- Defensive Stand: `{player: 0.50, neutral: 0.20, enemy: 0.30}`
- Assault: `{player: 0.30, neutral: 0.20, enemy: 0.50}`
- Multi-Front Defense: `{player: 0.50, neutral: 0.20, enemy: 0.30}`
- Counterinsurgency: `{player: 0.30, neutral: 0.50, enemy: 0.20}`

The S7-5 simulation-state delta math (military drives player↔enemy axis, tension drives neutral share, ±15% per coefficient, clamp + renormalize) is unchanged — Stage 7.5 only changes the baseline the delta is applied against.

**`mission_contracts.py`** — Add `behavior_script_id: str` and `enemy_force_groups: list[ForceGroupSpec]` fields to `MissionSetup`. `ForceGroupSpec` carries `force_id`, `composition_template`, `initial_position` (spine_node_id or map coord), `power_share` (fraction of total enemy power for this force). The mission generator (Stage 5.5) populates these from the archetype + canvas variant.

**`tactical_engine.py`** — One additive call per tick at the script-eval cadence: `for runner in self.behavior_runners: commands += runner.evaluate(self.tick)`. Otherwise unchanged. The runner emits commands that flow through the existing engine command path — no new command types, no special enemy-only command dispatch.

**`config.py`** — New constants:

```python
SCRIPT_EVAL_INTERVAL_TICKS = 40       # 2 sec at 20 Hz
SCRIPT_NOISE_DEFAULT_PCT = 0.15       # ±15% default noise on threshold values
SCRIPT_TIMER_NOISE_DEFAULT_PCT = 0.20 # ±20% default noise on timer durations
COUNTERINSURGENCY_FRAGMENTATION_WEIGHTS = {
    "concentrated": 0.25,  # 3 cells (2 ambush + 1 patrol)
    "dispersed":    0.50,  # 4 cells (2 ambush + 1 patrol + 1 sleeper)
    "fragmented":   0.25,  # 5-6 cells (3 ambush + 1 patrol + 1-2 sleepers)
}
SCRIPT_FALLBACK_OWNERSHIP = (0.33, 0.33, 0.34)  # used by the 6 non-prototype archetypes
```

### Files NOT to modify

- **Protected engine files** (per `CLAUDE.md`): `tick.py`, `drift.py`, `faction.py`, `region.py`, `events.py`, `event_engine.py`, `intent_resolver.py`, `border_friction.py`, `technology.py`, `diplomacy.py`, `world.py`, `templates.py`, `theme_scifi.py`. None touched in Stage 7.5.
- **`socket_server.py`** — protected per CLAUDE.md. Not touched (Stage 7.5 is engine-side only; Stage 8 owns the socket).
- **Stage 7 reinforcement.py** — not touched. Ownership baselines plug into the existing resolver via `archetype_filters.py`.
- **Stage 6 unit decision loop (`unit.py`)** — not touched. The macro layer issues commands; the unit layer executes them through the existing flinch → command → auto-engage loop. No new unit-level behavior.

## Input/Output Shapes

### Behavior script JSON shape

```json
{
  "script_id": "defensive_stand_v1",
  "archetype": "defensive_stand",
  "trigger_bus_vocabulary": ["force_b_broken", "primary_chokepoint_contested", "objective_reached"],
  "terminal_states": ["destroyed", "retreated_off_map", "objective_reached"],
  "forces": [
    {
      "force_id": "force_a_main_thrust",
      "composition_template": "defensive_stand_attacker",
      "power_share": 0.65,
      "initial_position": {"type": "spine_node", "node_kind": "enemy_spawn", "selector": "primary"},
      "initial_state": "advance_cautious_to_chokepoint",
      "states": {
        "advance_cautious_to_chokepoint": {
          "behavior": "advance",
          "modifier": "cautious",
          "target_resolution": {"type": "spine_node", "node_kind": "chokepoint", "selector": "primary"},
          "transitions": [
            {"condition": "timer.elapsed_sec >= 180", "to_state": "advance_aggressive", "noise_pct": 0.15},
            {"condition": "player_force_hp_fraction_in_zone('chokepoint_primary') < 0.30", "to_state": "advance_aggressive", "noise_pct": 0.10},
            {"condition": "force_hp_fraction < 0.40", "to_state": "retreat_cautious", "noise_pct": 0.10}
          ],
          "reactive_hooks": [
            {"when": "bus.force_b_broken", "to_state": "advance_aggressive"}
          ]
        },
        "advance_aggressive": { "behavior": "advance", "modifier": "aggressive", "target_resolution": {"type": "spine_node", "node_kind": "objective"}, "transitions": [
            {"condition": "force_hp_fraction < 0.25", "to_state": "retreat_cautious", "noise_pct": 0.10}
        ]},
        "retreat_cautious": { "behavior": "retreat", "modifier": "cautious", "target_resolution": {"type": "spine_node", "node_kind": "enemy_spawn", "selector": "primary"}, "transitions": [
            {"condition": "force_unit_count == 0", "to_state": "destroyed"}
        ]},
        "destroyed": {"behavior": "defend", "modifier": "cautious", "transitions": []}
      }
    },
    { "force_id": "force_b_flanker", "composition_template": "defensive_stand_attacker_light", "power_share": 0.35, "initial_position": {"type": "spine_node", "node_kind": "enemy_spawn", "selector": "secondary"}, "initial_state": "wait", "states": {
      "wait": { "behavior": "defend", "modifier": "cautious", "transitions": [
          {"condition": "timer.elapsed_sec >= 45", "to_state": "advance_cautious_to_objective", "noise_pct": 0.15}
      ]},
      "advance_cautious_to_objective": { "behavior": "advance", "modifier": "cautious", "target_resolution": {"type": "spine_node", "node_kind": "objective"}, "transitions": [
          {"condition": "enemy_unit_in_range('force_b_self', 800)", "to_state": "advance_aggressive"},
          {"condition": "force_hp_fraction < 0.30", "to_state": "retreat_set_flag", "noise_pct": 0.10}
      ]},
      "advance_aggressive": { "behavior": "advance", "modifier": "aggressive", "target_resolution": {"type": "spine_node", "node_kind": "objective"}, "transitions": [
          {"condition": "force_hp_fraction < 0.25", "to_state": "retreat_set_flag", "noise_pct": 0.10}
      ]},
      "retreat_set_flag": { "behavior": "retreat", "modifier": "cautious", "target_resolution": {"type": "spine_node", "node_kind": "enemy_spawn", "selector": "secondary"}, "on_enter": [{"set_flag": "force_b_broken"}], "transitions": [
          {"condition": "force_unit_count == 0", "to_state": "destroyed"}
      ]},
      "destroyed": {"behavior": "defend", "modifier": "cautious", "transitions": []}
    }}
  ]
}
```

### Engine-side runner state

```python
@dataclass
class BehaviorRunnerState:
    script_id: str
    force_id: str
    current_state: str
    state_entered_tick: int
    timer_noise_pct: dict[str, float]      # per-state noise rolls, frozen at mission start
    threshold_noise_pct: dict[str, float]  # per-transition noise rolls, frozen at mission start
    pending_commands: list[Command]
    is_terminal: bool
```

### Trigger bus shape

```python
TriggerBus.flags = {"force_b_broken": True, "primary_chokepoint_contested": False, ...}
TriggerBus.values = {"counterinsurgency_fragmentation": "dispersed", ...}
```

### Counterinsurgency fragmentation roll output

```python
{
    "fragmentation_bucket": "dispersed",
    "cell_count": 4,
    "cell_roles": ["ambush", "ambush", "patrol", "sleeper"],
    "per_cell_power": 0.25  # share of total counterinsurgency enemy power per cell
}
```

Rolled once at mission start in `script_loader.load_script("counterinsurgency", seed)`. Result stored in `MissionSetup.enemy_force_groups` so the rest of the engine and the deterministic replay system see the same partitioning.

### Force composition resolution example

```python
# Defensive Stand, total enemy power = 4500, two-force split [0.65, 0.35]
instantiate_force("defensive_stand_attacker", total_power=4500 * 0.65, count_split=None)
# Returns roughly:
# [Vanguard × 4, Raider × 3, Bombard × 2, Interceptor × 2, Line × 1]  # power ~2900
```

The composition resolver picks integer unit counts that hit the ratio targets within ±5% of the budget. Rounding bias goes to whichever unit type is closest to its target ratio after integer assignment.

## Integration Points

- **Engine ↔ runner.** `TacticalEngine` constructs one `BehaviorRunner` per `MissionSetup.enemy_force_groups` entry at mission start. Each tick, the engine calls `runner.evaluate(self.tick)` for runners whose force still has units; emitted commands flow through the existing engine command path. Kill switch: `ENABLE_BEHAVIOR_SCRIPTS = False` in `config.py` falls back to Stage 7's placeholder enemy AI (attack-move toward objective). Default ON after Checkpoint G; OFF before.
- **Runner ↔ trigger bus.** Single bus per mission, passed to every runner at construction. No cross-mission state. The bus is also serializable for Stage 8's tactical-state snapshot (stored under `engine_state.trigger_bus`).
- **Stage 7 ↔ Stage 7.5.** `archetype_filters.py` is shared. Stage 7.5 extends it with prototype ownership baselines. The S7-5 simulation-state delta resolver in `reinforcement.py` reads the same `BASELINE_OWNERSHIP[archetype]` map; the only change is which entries are populated.
- **Stage 5.5 ↔ Stage 7.5.** Mission generator constructs `MissionSetup.enemy_force_groups` per the chosen archetype's `forces` declaration in the JSON script. For Counterinsurgency, the generator also rolls the fragmentation bucket and attaches the resulting `cell_count` + `cell_roles` to `MissionSetup`.

## Implementation Checkpoints

Each checkpoint is a hard stop per `dev_rules.md` § Mandatory Checkpoints. Run test, show output, wait for Westley approval. Do not batch.

### Checkpoint A — Trigger Bus + Condition Language

**Build:** `trigger_bus.py` + `condition_language.py`. No runner yet, no scripts.

**Test:** `test_trigger_bus.py` — set/get/clear flags and values; `test_condition_language.py` — parse + evaluate every supported primitive against a mock context; adversarial inputs (arbitrary Python, unknown predicates, malformed expressions) all rejected at parse.

**Print:** Per-test: input expression, expected result, actual result, parser error (if any). Adversarial-rejection table.

**Verify:** Every supported primitive parses + evaluates correctly. Every adversarial input rejected without raising. Expression parse cache works (re-parse of seen expression returns cached AST).

⛔ STOP.

### Checkpoint B — Schema + Script Loader

**Build:** `script_schema.py` + `script_loader.py`. Author `_stub_default.json` as the bare-minimum valid script.

**Test:** `test_script_schema.py` — load `_stub_default`, validate; load deliberately broken scripts (dead state, missing initial state, undeclared bus flag, undefined predicate, unreachable state) and verify each is rejected with a specific error.

**Print:** Validation results per script. Per broken script: which validator caught the issue, error message text.

**Verify:** Stub loads clean. Every broken script is caught by the right validator. Error messages are specific enough that an author can fix the file.

⛔ STOP.

### Checkpoint C — Behavior Runner Against Stub

**Build:** `behavior_runner.py`. Wire into `tactical_engine.py` behind `ENABLE_BEHAVIOR_SCRIPTS = True`.

**Test:** `test_behavior_runner.py` — single force, stub script, run a Stage 6 hand-authored test map. Verify the runner emits `attack_move` commands toward the objective each evaluation cycle.

**Print:** Per evaluation tick: active state, transitions evaluated, command emitted (if any). Force unit count over time.

**Verify:** Runner ticks at `SCRIPT_EVAL_INTERVAL_TICKS` cadence. State machine advances through `advance_cautious → advance_aggressive` per the stub script. Engine receives commands and units act on them.

⛔ STOP.

### Checkpoint D — Defensive Stand Script

**Build:** `scripts/defensive_stand.json` per the DQ-A capture. Update `force_composition.py` with the `defensive_stand_attacker` template.

**Test:** `test_script_defensive_stand.py` — run a Defensive Stand mission on a Stage 7 generated map with two approach vectors. Capture the runner's state-by-state log + emitted commands. Run the same script + seed 5 times to verify determinism (same noise rolls, same behavior).

**Print:** Per force: state transitions (with timer/threshold values that fired), command emission timeline, force HP curve. Trigger-bus flag timeline. Determinism check (5 runs hash-equal).

**Verify:** Force A probes, commits, and either retreats or pushes per the script. Force B starts at T+45s noise window and behaves accordingly. `force_b_broken` flag fires when Force B retreats; Force A's reactive hook fires in response. Determinism holds across 5 reruns with the same seed.

⛔ STOP.

### Checkpoint E — Assault Script

**Build:** `scripts/assault.json` per the DQ-B capture. Update `force_composition.py` with the `assault_defender` template.

**Test:** `test_script_assault.py` — run an Assault mission on a Stage 7 generated map. Verify the garrison force defends aggressively from the start; verify the reserve force stays in reserve until trigger conditions; verify reserve commitment locks the garrison into hold-position. Three scenarios: player breaches inner ring fast (test inner_breach trigger), player attrits the garrison slowly (test HP < 50% trigger), player stalls (test T+240s timer trigger).

**Print:** Per scenario: state timeline for both forces, trigger-bus flag fires, reserve-commitment moment, mission outcome.

**Verify:** Each of the three reserve-commitment triggers fires correctly in its scenario. Reserve commitment locks Force A out of `defend_cautious` for the rest of the mission. No false triggers.

⛔ STOP.

### Checkpoint F — Multi-Front Defense Script (Multi-Force Coordination Stress Test)

**Build:** `scripts/multi_front_defense.json` per the DQ-C capture, with both 2-force and 3-force variants selected by approach-vector count.

**Test:** `test_script_multi_front.py` — run on a 3-vector Large canvas with the 3-force variant. Two scenarios: (1) player crushes Force A early — verify Force B and Force C both escalate via cascading-aggression hooks; (2) player ignores all fronts — verify staggered escalation timeline.

**Print:** Per force: full state + transition timeline. Trigger-bus flag fires (`force_a_broken`, `any_front_broke_through`, etc.) with timestamps. Per-force commit-aggression moments.

**Verify:** Cascading-aggression hooks fire in the right direction (broken Force A → other forces escalate, NOT retreat). Staggered timer offsets land within noise. `any_front_broke_through` fires when ANY force reaches an inner-ring objective. 2-force variant works on 2-vector maps without crashing.

⛔ STOP.

### Checkpoint G — Counterinsurgency Script (Variable Cell Count)

**Build:** `scripts/counterinsurgency.json` per the DQ-D capture. Implement the fragmentation roll in `script_loader.py`.

**Test:** `test_script_counterinsurgency.py` — run 50 Counterinsurgency missions; verify the fragmentation roll distribution matches `COUNTERINSURGENCY_FRAGMENTATION_WEIGHTS` within ±5%. Three targeted scenarios: (1) Concentrated bucket — 3 cells, no sleeper; (2) Dispersed default — 4 cells, sleeper triggers when both ambush cells are engaged-or-destroyed; (3) Fragmented — 5–6 cells, multiple sleepers chain.

**Print:** Bucket distribution over 50 runs. Per scenario: cell roster + position, ambush trigger moments, patrol detection moments, sleeper activation moments, mission outcome.

**Verify:** Bucket weights statistically correct. Ambush cells trigger only on player proximity. Patrol cell retreats after detection per script. Sleeper activates only when its bus condition is met. Total enemy power constant across buckets within ±5%.

⛔ STOP.

### Checkpoint H — Ownership Baselines + S7-5 Delta Integration

**Build:** Update `archetype_filters.py` with the 4 prototype baselines per the DQ captures. No new code — just data.

**Test:** `test_stage7_5_integration.py::test_ownership_baselines` — for each prototype archetype, generate 20 mission setups across varied region states (high military / low military / high tension / low tension). Verify the S7-5 delta math layers correctly on top of the new baselines and produces sensible distributions (player share never < 0.05 or > 0.95, etc.).

**Print:** Per archetype: baseline ratio, sample of (region_state → final ratio) pairs, distribution of resulting structure counts per ownership.

**Verify:** Baselines are read from the new entries (not the 33/33/33 fallback) for the 4 prototypes. Fallback still applied to the other 6 archetypes. Delta math produces no clamp violations or NaN values.

⛔ STOP.

### Checkpoint I — End-to-End + Performance (Final)

**Build:** Final wiring. Stub script for the 6 non-prototype archetypes; verify they fall back gracefully.

**Test:** Run one mission per prototype archetype on a Stage 7 generated map, end-to-end through the Stage 6 engine. Record: per-tick runner cost (ms), total mission tick count, mission outcome band, determinism check (3 reruns of one mission with the same seed). Run one mission per non-prototype archetype to verify the stub fallback doesn't crash.

**Print:** Per-archetype mission summary: outcome band, runner-cost stats (p50/p95/p99). Determinism: tick-by-tick command-stream hash equality across 3 reruns. Stub-fallback table.

**Verify:** All four prototype missions complete with classified outcomes. Runner cost p95 < 5ms per evaluation tick (config: every 40 engine ticks → ~125ms budget per second of mission, well under 50ms-per-engine-tick budget). Determinism holds. Stub fallback works for all 6 non-prototypes.

⛔ STOP.

## Invariants

- **I1 — Script schema validation.** Every shipped JSON script (4 prototype + 1 stub) loads clean. Every deliberately-broken script (6+ broken cases in the test suite) is rejected with a specific, identifiable error.
- **I2 — Determinism preserved.** Same script + same seed + same player commands → same enemy command stream tick-for-tick. Verified across all 4 prototype archetypes with 3 reruns each.
- **I3 — Runner performance budget.** Per-evaluation cost p95 < 5ms across all 4 prototype scripts on Stage 7 generated maps. Aggregate across the engine tick budget: behavior runners contribute < 10% of the per-tick cost.
- **I4 — Trigger bus correctness.** Flag-set order is mission-deterministic (forces evaluated in `force_id` order). No flag write contention. Bus state serialization round-trips correctly (for Stage 8 quit-and-resume).
- **I5 — Ownership baselines applied.** The 4 prototype archetypes use the authored baselines (not the 33/33/33 fallback). The 6 non-prototypes use the fallback. S7-5 delta math layered correctly on top.
- **I6 — Composition fidelity.** `instantiate_force` produces unit lists that match the template ratios within ±5% by power, with total power within ±5% of the requested budget.
- **I7 — Fragmentation distribution.** Counterinsurgency fragmentation roll over 50 missions matches `COUNTERINSURGENCY_FRAGMENTATION_WEIGHTS` within ±5% per bucket.
- **I8 — No engine modifications beyond the documented additive call.** `git diff` shows only the one-line `behavior_runners` evaluation hook in `tactical_engine.py`. No protected-file edits. No new command types in `command.py`.
- **I9 — Cascading-aggression direction correctness.** Multi-Front Defense's broken-fronts-cause-others-to-escalate hooks fire in the correct direction (escalate, not retreat) in Checkpoint F's targeted scenarios.
- **I10 — Counterinsurgency total enemy power constant.** Across all three fragmentation buckets, total enemy power across all cells is within ±5% of the force-allocation budget. Only granularity changes, not total.

Per CLAUDE.md: if an invariant fails, you may not widen thresholds or weaken tests. Escalate real bugs, or narrow scope (skip-cases never meant to be caught).

## Done Condition

- All 9 checkpoints (A–I) run, shown, approved by Westley.
- All 10 invariants (I1–I10) pass.
- 4 prototype scripts authored, validated, and end-to-end exercised on Stage 7 generated maps.
- 4 prototype ownership baselines authored in `archetype_filters.py`; the 6 non-prototypes still use the 33/33/33 fallback (their dedicated baselines are a Beyond-Stage-7.5 follow-up).
- A full set of 4 prototype-archetype missions runs end-to-end through the Stage 6 engine with classified `MissionResult` outcomes.
- No protected engine file modified.
- `MissionSetup.behavior_script_id` and `enemy_force_groups` schema additions documented in `docs/architecture.md` (per CLAUDE.md tick-delta-shape rule applied analogously to the mission-shape contract).

## Files Created

(Filled in after implementation.)

## Notes for the Implementing Session

- **Scripts are content, not code.** Treat the four JSON scripts as authored artifacts. When tuning, change the JSON, not the runner. The runner's job is to faithfully execute the script; if a behavior feels wrong, re-author the script.
- **Condition language is restricted on purpose.** Resist adding "just one more" predicate. Every new predicate widens the runtime contract and increases the schema-validation surface. If a script needs a predicate that doesn't exist, that's a real design conversation — not a quick add.
- **Trigger bus is per-mission, not global.** No cross-mission state. The bus dies when the mission ends. This keeps determinism clean and matches the bible's per-mission framing.
- **Counterinsurgency fragmentation is a single roll.** Don't roll per-cell or per-force — one roll picks the bucket, and the bucket determines the cell roster. Per the bible's noise philosophy: rolled once, persists for the duration.
- **Ownership baselines vs. delta vs. count.** Three independent layers: (1) baseline ratio per archetype (Stage 7.5 authors the 4 prototype values); (2) S7-5 simulation-state delta nudges the ratio (Stage 7); (3) total structure count derives from region military (Stage 7's STRUCTURE_COUNT_RANGES, clamped by canvas size). Stage 7.5 only touches (1).
- **Six non-prototype archetypes are stubbed for a reason.** Don't try to author all 10 in this stage. Per the resolved S75-2 decision, the prototype set validates the vocabulary first; the remaining 6 land in a follow-up pass once the vocabulary holds up. Stub fallback is a cautious advance + simple retreat — playable but not authored.
