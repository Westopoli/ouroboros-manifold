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

## FairnessScore — metric skip semantics (Stage 11e)

`FairnessScore` in `simulation/fairness_evaluator.py` carries a `*_skipped` bool per metric (`path_balance_skipped`, `travel_time_skipped`, `vantage_skipped`, `hazard_skipped`).

When a layout has zero of a fairness-relevant node type on **both sides** (e.g., zero vantage nodes total), the corresponding metric is **skipped** — not counted toward the aggregate pass/fail. `is_acceptable()` passes when all non-skipped metrics fall within their tolerances.

This is a scope-narrowing fix per CLAUDE.md: balance of an absent node type is undefined, not "balanced." One-side-zero (e.g., player has 0 vantage, enemy has 3) is a real imbalance and still fails.

Added in Stage 11e (`stage_11e_fairness_reconciliation_spec.md`).

## Map Generation — Simple Picker (Stage 11e pivot)

`simulation/map_generator.py:generate_map()` uses a single-pass random picker:

1. Run archetype compatibility filter → candidate pool.
2. Pick one layout uniformly at random (seeded by `GeneratorInput.seed`).
3. Instantiate, assign reinforcement ownership, place gradients.
4. Evaluate fairness (score logged to `tuning_output/fairness_log/<date>.jsonl`, **not used for rejection**).
5. Return result.

No retry loop. `generation_metadata["fairness_retries"]` is always 0. The evaluator infrastructure (`FairnessScore`, `FairnessTargetProfile`, all four metrics) is preserved intact for the future redesign (`stage_11f_fairness_redesign_spec.md`).

## Objective Snapshot Extension (Stage 11d)

Each objective entry in the `objectives` array of a full snapshot now carries two additional fields:

### `is_primary` (bool)
Whether this is a primary objective. Always present.

### `location` (optional object)
Present only for objective types with a meaningful geographic center:
- `hold_zone`, `clear_zone` → `{"x": <zone_x>, "y": <zone_y>}`
- `escort_to_extraction` → `{"x": <extraction_x>, "y": <extraction_y>}`
- `eliminate_force` → centroid of living target unit positions; omitted if all targets are dead.
- `survive_duration`, `destroy_targets` → omitted (no location).

Shape when present: `{"x": float, "y": float}`

Renderer must tolerate missing `location`. Delta objective updates may carry `location` if it has changed since the last update; static-location objective types (`hold_zone`, `escort_to_extraction`) carry it only on full snapshots.

See also: `scenes/tactical/hud.gd` — consumes `objective.location` for marker rendering.
