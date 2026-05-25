# leaf-04 assumptions

## LAYER_Z constants absent from config.py

`config.LAYER_Z_FLOORS` + `config.LAYER_Z_CEILINGS` not present (leaf-03 lands them). Both `fog_of_war.py` and `test_asteroid_visibility.py` use `try/except AttributeError` / `try/except ImportError` fallbacks to inline `[0.0, 30.0, 100.0]` / `[30.0, 100.0, 300.0]`. Will auto-upgrade when leaf-03 merges — no manual cleanup needed.

## fog_of_war check ordering (original)

Order in `compute_visibility` inner loop, preserved exactly:
1. Same-faction short-circuit (`store.faction[other] == my_faction`) — BEFORE any LOS check. Asteroid raycast does NOT apply to same-faction pairs. Spec line 273 convention held.
2. Distance + pulse short-circuit — pulse bypass adds directly to `visible` without LOS gate.
3. Layer cone factor check — 0.0 factor skips.
4. Detection radius check — only then do we reach asteroid raycast.
5. Asteroid raycast (new) — replaces polygon block.

## Polygon code retired

Removed `cover_polygon_containing` call at original lines 100-104. No dead code left — those 4 lines replaced entirely by the 4-line asteroid raycast block. No other polygon references exist in `fog_of_war.py`.

## Store field names used

`FIELD_X=0, FIELD_Y=1, FIELD_LAYER=2, FIELD_SENSOR_RADIUS=8` — imported from `unit.py`. Observer fields accessed as `store.data[uid, FIELD_*]`, target as `store.data[other, FIELD_*]`. `store.faction[uid]` for faction id.

## Observer iteration

`store.active_ids()` returns all alive unit ids. Inner loop also over `active_ids()`. Same set for both observer + target — same-faction skip is the only early exit before distance check.

## TacticalMap fixture strategy

Used `TacticalMap.__new__(TacticalMap)` to bypass `__init__` (avoids map_generator dependency). Manually set `tm.asteroid_field`, stubbed `tm.sensor_interference` and `tm.get_spine_nodes_by_type` as lambdas. `hasattr(tactical_map, "asteroid_field")` guard in `fog_of_war.py` means maps without `asteroid_field` (pre-Wave-2.5R) degrade gracefully (no LOS block, no crash).

## Unit spawn fixture

`UnitStore.spawn` requires `stats["category"]` to be a key in `CATEGORY_MAP = {"Strike", "Line", "Siege"}`. Used `"Strike"` in `_STATS`. `sensor_radius=99999` ensures distance never gates the pair (isolation test — asteroid gate only).

## hasattr guard for backward compat

`if tactical_map is not None and hasattr(tactical_map, "asteroid_field")` — allows existing callers passing a non-upgraded TacticalMap to skip raycast silently. Parent can strip guard once all callers are upgraded.

## Layer clamp

`min(layer, len(_LAYER_Z_FLOORS) - 1)` clamps layers above index 2 to index 2. Spec only defines 3 layers; defensive clamp prevents IndexError if a unit somehow ends up at layer 3+.
