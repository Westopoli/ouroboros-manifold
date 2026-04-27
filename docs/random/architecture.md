# Architecture Notes

## MissionSetup.map_params schema

`MissionSetup.map_params` is a plain `dict` defined in `mission_contracts.py`. When Stage 7 map generation is active (`ENABLE_STAGE7_MAP_GEN = True` in `config.py`), the mission generator populates it with the following keys:

```python
map_params = {
    "archetype":  str,   # mission archetype, e.g. "defensive_stand"
    "region_id":  str,   # region ID from the simulation world
    "canvas_size": str,  # "small" | "medium" | "large"
    "seed":       int,   # generation seed (deterministic replay)
    "generated":  bool,  # True = produced by Stage 7 pipeline; False = hand-authored
}
```

When `generated=False` (Stage 6 hand-authored maps), `map_params` may be empty `{}` or absent — the engine reads `TacticalMap` directly without consulting these keys.

The `seed` value is carried on `MissionSetup` so that Stage 8 rewind logic can re-run map generation from the same seed and reproduce the identical `TacticalMap`. This is the contract between the mission generator, the tactical engine, and the save/rewind system.

---

## Stage 8 WebSocket tick delta shape

All packets are JSON, line-delimited (one object per line). The delta shape below supersedes the original Stage 8 spec draft, which sent position updates for every moving unit every tick. The dead-reckoning extension was adopted before Checkpoint F to avoid a 200v200 bandwidth problem (~320 KB/s in the approach phase). See Stage 8 spec §"Delta Wire Format — Dead-Reckoning" for the design rationale.

### Full snapshot (`type: "snapshot"`) — unchanged from spec

Unit entries include a `velocity` field (always `[0.0, 0.0]` in the snapshot; updated via deltas):

```json
{
  "uid": 17, "type": "vanguard", "pos": [4200.5, 3100.2], "layer": 1,
  "hp": 240, "max_hp": 300, "faction": 0,
  "facing_rad": 0.0, "ability_cd_sec": 4.2, "selection_eligible": true,
  "velocity": [0.0, 0.0]
}
```

### Tick delta (`type: "delta"`) — dead-reckoning protocol

```json
{
  "type": "delta",
  "tick": 1201,
  "units_updated": [
    {"uid": 17, "pos": [4205.1, 3101.0], "velocity": [102.0, 18.0], "hp": 238},
    {"uid": 22, "hp": 195}
  ],
  "units_added": [
    {"uid": 91, "type": "vanguard", "pos": [4200, 3100], "layer": 1,
     "hp": 300, "max_hp": 300, "faction": 0, "velocity": [0.0, 0.0]}
  ],
  "units_removed": [45],
  "structures_updated": [{"uid": 103, "capture_progress": 0.1}],
  "objectives_updated": [{"id": "hold_zone_alpha", "progress": 0.43}],
  "command_acks": [{"client_command_id": "c-7f2", "accepted": true}],
  "events": [{"kind": "unit_destroyed", "uid": 45, "at": [4210, 3105], "layer": 1}]
}
```

**Dead-reckoning contract (server-side — unchanged):**
- A unit absent from `units_updated` and `units_removed` is on course — the server's `DeadReckoningTracker` predicts the client extrapolates `pos += velocity * dt` each tick using the last known `velocity`.
- `pos` + `velocity` appear together in `units_updated` only when the server decides a position resync is needed (prediction error > `DR_RESYNC_THRESHOLD` world units, or velocity magnitude change > `DR_VEL_CHANGE_THRESHOLD` wu/s). Non-positional changes (`hp`, `layer`, `ability_cd_sec`) are sent independently with no `pos`/`velocity`.
- `units_added` always includes `velocity: [0.0, 0.0]` — newly spawned units start stationary.
- On every full snapshot (`type: "snapshot"`), the server resets its per-unit DR baselines.

**Client-side rendering — interpolation buffer (Stage 8.5 H.5, Option F):**

The Godot client does NOT predict the future. Instead it buffers the last several tick states and renders by interpolating between two known-good past states. Display is always ~150ms (3 ticks) behind the latest received tick. This matches the bible's stated architecture: "Linear interpolation between engine ticks (20/sec) for 60fps rendering."

On each delta arrival, the client builds a complete tick state by advancing all units from the previous state by `vel × TICK_DURATION`, then applying the delta's corrections. This complete state is pushed into a ring buffer. Each render frame, the client finds the two buffer entries bracketing `(latest_time - buffer_delay)` and linearly interpolates all unit positions between them.

Because the client never predicts ahead of the server, there is no over-prediction and no backward correction — eliminating the visible "hitch" that DR-forward architectures produce when units decelerate unexpectedly.

The server's DR protocol is unchanged. It still decides when to send pos updates based on its tracker's comparison of predicted vs actual. The client simply absorbs those corrections into the buffer as part of building each tick's complete state.

**Tuning constants** (in `config.py`):

| Constant | Default | Meaning |
|---|---|---|
| `DR_RESYNC_THRESHOLD` | `1.0` | Position prediction error (world units) before server forces a resync |
| `DR_VEL_CHANGE_THRESHOLD` | `20.0` | Velocity magnitude change (wu/s) before server forces a resync |
| `INTERPOLATION_BUFFER_TICKS` | `3` | Client render delay in ticks (150ms at 20Hz). Higher = more jitter absorption, more input lag |

---

## Stage 7.5 — Behavior Runner Integration

### MissionSetup additions

`MissionSetup` (in `mission_contracts.py`) carries one Stage 7.5 field:

```python
behavior_script_id: str   # e.g. "defensive_stand_v1", "multi_front_defense_3front_v1"
```

The spec also called for `enemy_force_groups: list[ForceGroupSpec]` on `MissionSetup`. This was **not implemented** — the mission generator (Stage 5.5) does not yet populate force groups from the script manifest. Force group setup is handled ad-hoc by the mission launcher using the script's `forces[]` array directly. This is a known gap to close when Stage 5.5 is wired to the behavior runner in a future pass.

### Script dispatch

`script_loader.load_script(archetype, seed=None, front_count=None)` returns the validated script dict.

- **counterinsurgency** — rolls a fragmentation bucket (`concentrated` / `dispersed` / `fragmented`) using `seed`; dispatches to `counterinsurgency_{bucket}.json`.
- **multi_front_defense** — dispatches to `multi_front_defense_2front.json` when `front_count == 2`, otherwise `multi_front_defense_3front.json`. The caller (mission launcher) is responsible for counting approach vectors from the `TacticalMap` and passing `front_count`.
- All other prototypes — loads `{archetype}.json` directly.
- Non-prototype archetypes — falls back to `_stub_default.json` with a logged warning.

### BehaviorRunner engine hook

`TacticalEngine.step()` calls each runner when `ENABLE_BEHAVIOR_SCRIPTS = True`:

```python
if config.ENABLE_BEHAVIOR_SCRIPTS and self.behavior_runners:
    for runner in self.behavior_runners:
        runner.step(self.tick, self.store, self.command_queue)
```

Runners self-throttle to `SCRIPT_EVAL_INTERVAL_TICKS` (40 ticks / 2 sec). Commands emitted by the runner flow through the existing engine command path — no new command types.

### Trigger bus serialization

`TriggerBus` state (flags + values dicts) must be included in the Stage 8 `engine_state` snapshot for quit-and-resume. Shape:

```json
{
  "trigger_bus": {
    "flags": {"force_b_broken": true, "inner_breach": false},
    "values": {}
  }
}
```

### Spec variations

| Item | Spec said | What shipped |
|---|---|---|
| `MissionSetup.enemy_force_groups` | Add `ForceGroupSpec` list to `MissionSetup` | Not added — force groups read directly from script `forces[]` at runtime |
| `multi_front_defense.json` | Single file, 2-force/3-force selected internally | Two files: `multi_front_defense_2front.json` + `multi_front_defense_3front.json`; dispatch in loader |
| `BehaviorRunnerState` fields | `script_id`, `state_entered_tick`, `timer_noise_pct`, `threshold_noise_pct`, `pending_commands`, `is_terminal` | `force_id`, `current_state`, `mission_start_tick`, `faction_id`, `last_eval_tick`, `trans_noise` — functional equivalents, different names |
| `test_force_composition.py` | Listed as a test file to create | Not created — composition templates are validated indirectly through per-script tests |
