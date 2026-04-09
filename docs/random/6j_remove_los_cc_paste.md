# CC Paste: Remove Friendly LOS Blocking, Adopt SC2-Style Attack Model

## Context

Friendly LOS blocking was added during 6J to make positioning matter, but it's producing the opposite effect — Strike units arriving from a flank LOS-block *each other* and perform worse than head-on (T2 TTW 824 vs T1 TTW 1163). Research confirms SC2 does NOT have friendly LOS blocking for ranged attacks. SC2's concave formations emerge from collision avoidance + attack-move targeting (stop and shoot nearest enemy in range), not from shot occlusion. The bible never specifies friendly LOS blocking. Removing it.

## Remove — 3 systems

### 1. Friendly LOS blocking in `damage.py`
- Delete `_friendly_blocks_shot()` function entirely
- Delete the call to `_friendly_blocks_shot()` in `resolve_damage()` and the `continue` branch that skips damage when blocked
- Delete the import of `has_combat_los` and `_ensure_navmesh` from movement (ONLY if these are not also used for terrain/obstacle LOS — check before deleting)
- Delete the attack timer reset to 0 on blocked shots

### 2. Blocked retarget system
- Delete `blocked_ticks` array from `UnitStore.__init__` in `unit.py`
- Delete blocked-tick increment/reset logic in `resolve_damage()` in `damage.py`
- Delete the blocked retarget check in `update_targeting()` in `unit.py` (the branch that clears `auto_engage_target` when `blocked_ticks > BLOCKED_RETARGET_TICKS`)

### 3. Config flags
- Delete `LINE_OF_FIRE_ENABLED` from `config.py`
- Delete `BLOCKED_RETARGET_TICKS` from `config.py`
- Delete any `if LINE_OF_FIRE_ENABLED:` guards in `damage.py`

## Keep — 2 systems

### 1. Hard collision in `movement.py`
- `_resolve_collisions()` stays. SC2 has unit collision. This is what produces concave formations naturally — units can't stack, so they spread around the engagement.
- `HARD_COLLISION_ENABLED`, `COLLISION_RESOLUTION_ITERATIONS`, `UNIT_COLLISION_RADIUS` all stay.
- Soft separation weight (currently 0.5, was lowered from 0.8 when hard collision was added) — stays at 0.5.

### 2. Terrain/obstacle LOS
- `has_combat_los(navmesh, ...)` for terrain obstacles (Bresenham on navmesh grid) — keep IF it's used for terrain blocking. SC2 has terrain LOS (can't shoot through cliffs). Only friendly-unit occlusion is being removed.
- Check: if `has_combat_los` is ONLY called from `_friendly_blocks_shot`, it can stay as dead code or be kept for future terrain LOS use. Don't delete the function itself.

## Verify existing behavior is correct

The bible's auto-engage (line 215): "nearest enemy in range, hold target, hold position if nothing in range." Confirm this is how `update_targeting()` works after the removal:
- Unit has enemy in weapon range → shoot nearest, hold that target until it dies or leaves range
- Unit has no enemy in range → continue moving toward waypoint/command target
- Collision avoidance pushes units laterally as they move forward through friendly groups
- No friendly shot blocking — rear-rank units with enemies in weapon range fire freely

## Test sequence

1. Run `test_checkpoint_6j.py` — verify no crashes after removal
2. Run `test_6j_gradient.py` — the key check is whether T2 (flank vs formed) now outperforms T1 (head-on). Without LOS blocking, Strike's speed advantage should let it form a concave around Line faster, giving it higher effective DPS in flanking scenarios.
3. Run `test_checkpoint_6d.py` — engagement durations may change (more units shooting = faster kills). Check L5/L6/L7.
4. Run `test_checkpoint_6c.py` — RPS directions should still hold.

## Expected outcome

- T1 (head-on): Similar or slightly faster than before (both sides shoot freely, no LOS blocking either way)
- T2 (flank): Should improve significantly — Strike units no longer block each other on approach
- T3a/T3b: Should still show strong gradient (column/distracted Line are still geometrically disadvantaged because collision avoidance means Strike concentrates fire on nearest enemies while rear Line units are physically far away)
- The gradient T1 < T2 < T3 should now hold because the advantage comes from collision-driven concave formation (speed-dependent) rather than LOS blocking (which hurt the faster, more clustered side)

## If durations break (L5/L6/L7)

More units shooting simultaneously = faster kills. If engagement durations drop below targets, the fix is HP increase, not re-adding LOS blocking. Flag for discussion — don't adjust HP without checking in.
