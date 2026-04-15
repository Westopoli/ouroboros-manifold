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
