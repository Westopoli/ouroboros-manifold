# Architecture — Cross-Stage Contracts

## MissionSetup.map_params

`MissionSetup.map_params` uses the `MapParams` TypedDict defined in `simulation/mission_contracts.py`.

```python
class MapParams(TypedDict, total=False):
    seed: int
    archetype: str
    region_id: str
    canvas_size: int
    generated: bool
```

### `seed` field lifecycle

- **Produced by:** `simulation/mission_generator.py` — generates `rng.randint(0, 2**31 - 1)` at mission creation time, stored in `map_params["seed"]`.
- **Consumed by:** `simulation/pipe_transport.py` — reads `setup.map_params.get("seed", current_tick)` when building `GeneratorInput` for the map generator.
- **Persisted by:** Stage 8's save/load system — `MissionSetup` is part of the tactical save blob; `map_params` round-trips through JSON transparently.
- **Fallback:** `current_tick` is used only for pre-Stage-11b saves that have empty `map_params`. This is temporary compatibility debt; once old saves are no longer supported, a missing seed should raise.

### Design authority

`bible_world.md:178` — *"…and a random seed (ensures reproducibility for replays and bug reports)."*
`bible_world.md:196` — *"the map is regenerated with a new random seed"* on fairness failure.

Added in Stage 11b (`stage_11b_map_variety_spec.md`).
