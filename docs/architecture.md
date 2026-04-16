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

**Dead-reckoning contract:**
- A unit absent from `units_updated` and `units_removed` is on course — client extrapolates `pos += velocity * dt` each tick using the last known `velocity`.
- `pos` + `velocity` appear together in `units_updated` only when the server decides a position resync is needed (prediction error > `DR_RESYNC_THRESHOLD` world units, or velocity magnitude change > `DR_VEL_CHANGE_THRESHOLD` wu/s). Non-positional changes (`hp`, `layer`, `ability_cd_sec`) are sent independently with no `pos`/`velocity`.
- `units_added` always includes `velocity: [0.0, 0.0]` — newly spawned units start stationary.
- On every full snapshot (`type: "snapshot"`), the client resets all unit velocities to the snapshot values and discards dead-reckoning state.

**Tuning constants** (in `config.py`):

| Constant | Default | Meaning |
|---|---|---|
| `DR_RESYNC_THRESHOLD` | `3.0` | Position prediction error (world units) before forcing a resync |
| `DR_VEL_CHANGE_THRESHOLD` | `20.0` | Velocity magnitude change (wu/s) before forcing a resync |
