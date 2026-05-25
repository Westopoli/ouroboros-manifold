# leaf-02 assumptions

## ASTEROID_SPATIAL_HASH_CELL missing from config

`config.py` lacks `ASTEROID_SPATIAL_HASH_CELL` (L3 leaf lands it). Hardcoded `_CELL = 100.0` in `_AsteroidSpatialHash`. Brief says: "if config lacks it, hardcode 100.0 and note." Done.

## _AsteroidSpatialHash as private class, not exposed in API

Brief says SpatialHash can be "tiny private class inside tactical_map.py". Named `_AsteroidSpatialHash` (underscore prefix) to avoid collision with existing `SpatialHash` (unit sensor/target hash). `AsteroidField.spatial_hash` attribute is typed as `_AsteroidSpatialHash` — tests access it via `field.spatial_hash.query_bbox(...)`. If swarm-review requires a public alias, parent can rename.

## cover_polygons param kept as silent kwarg

`map_generator.py` passes `cover_polygons=cover_polys` to `TacticalMap.__init__`. Brief says retire the polygon API from `tactical_map.py`, but `map_generator.py` is not in `do_not_edit` and not in this leaf's scope. Kept `cover_polygons=None` in signature, silently ignored, with comment pointing to the cross-dependency. Prevents test_j_* + test_facing import-time crash from `map_generator.py` passing the kwarg. L3 leaf should clean up `map_generator.py` call site.

## fog_of_war.py breakage (expected, not fixed)

`fog_of_war.py` is in `do_not_edit`. It calls `cover_polygon_containing` (Wave 2.5 polygon API). Removing that method from `tactical_map.py` causes `fog_of_war.py`-dependent tests to fail at call time (not import time). These tests were already Wave-2.5-only and not passing on main. L4 leaf updates `fog_of_war.py` — breakage is expected cross-leaf dependency.

## Degenerate ray (oz==tz + ox==tx + oy==ty in 2D)

When observer == target in 2D (`ray_len_sq == 0.0`), return False (no block). Spec doesn't address this edge case. Chose False: if observer and target are co-located, "no asteroid between them."

## z-range check: only checks min(z_enter, z_exit) > h

Spec line 178: "if min(z_enter, z_exit) > h → ray passes over top." Does NOT check if max(z_enter, z_exit) < 0 (ray entirely below ground). Asteroid vertical extent is [0, h]; all units have z >= 0 per layer model. Assuming z >= 0 always for in-play rays; no under-ground check needed.

## s_enter/s_exit clamped to [0, 1]

After quadratic solve, `s_enter = max(0, ...)` and `s_exit = min(1, ...)`. This clips intersection to segment only (not infinite ray). Correct per spec: ray is from observer to target, not infinite.
