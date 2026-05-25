# leaf-05 Assumption Log

## Gate location in damage.py

`resolve_damage` calls `compute_visibility(store, tactical_map)` at top (line 17).
Per-attacker loop (line 38): `if target not in visibility.get(uid, ()): continue`.
Gate present. No edit needed.

## resolve_damage signature

`def resolve_damage(store: UnitStore, tactical_map, dt: float)` — confirmed line 14.
Returns `(deaths: list, kill_sources: dict)`.

## How visibility_map supplied

`compute_visibility` (fog_of_war.py) takes `(store, tactical_map)`.
Returns `dict[uid → set[uid]]` — enemy-only visible sets.
Since Wave 2.5R (leaf-04 / fog_of_war.py lines 112-116): if `tactical_map` has `asteroid_field`,
calls `tactical_map.asteroid_blocks_los(ox, oy, oz, tx, ty, tz)` per pair.
Blocked pairs excluded from visible set → damage gate fires.

## (1.0 - cover) term

Regex sweep: no match in damage.py. Term never existed or was removed before this wave.

## Fixture approach

Built minimal UnitStore by hand via `spawn(unit_type, faction, x, y, layer, stats)`.
Avoided L7 fixture (asteroid_integration_fixture.py) per brief constraint.
Blocking asteroid: radius_xy=40wu, height=500wu, centered at ray midpoint (100,0).
Layer 0 z-midpoint = 15.0wu — well within asteroid height — ensures z-check passes.
Clear map: `AsteroidField([])` — spatial hash returns empty bbox query.

## Wave 2.5 compatibility

Gate already L4-compatible: `compute_visibility` uses `asteroid_blocks_los` per-pair.
No damage.py changes needed; tests went GREEN on first run.
