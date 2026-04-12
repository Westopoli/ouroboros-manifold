TASK: Surgically remove RVO/ORCA from movement.py and damage.py. Restore the
pre-RVO inline steering system. Do not touch any other file in the working
tree except where explicitly listed below.

BASELINE COMMIT: 2c29b0e ("mid-stage for 5 and 6, issue with both, hashing
out, design gaps identified"). This is the last commit before RVO was
introduced. Use this as the source of truth for the restored steering body.

Commands to inspect baseline files:
  git show 2c29b0e:simulation/movement.py > /tmp/movement_baseline.py
  git show 2c29b0e:simulation/damage.py > /tmp/damage_baseline.py
  git show 2c29b0e:simulation/unit.py > /tmp/unit_baseline.py
  git show 2c29b0e:simulation/config.py > /tmp/config_baseline.py

================================================================
movement.py
================================================================

REMOVE entirely from current movement.py:
- _compute_preferred_velocities
- _compute_orca_line
- _solve_lp_2d
- _solve_lp_2d_safe
- compute_rvo_velocities
- the current update_movement body (the one that calls compute_rvo_velocities)

RESTORE from 2c29b0e:simulation/movement.py:
- The original update_movement function with inline seek + separation +
  obstacle avoidance + arrival/waypoint consumption logic.
- _resolve_collisions (already in 2c29b0e baseline — should match exactly,
  copy from baseline if it differs).
- The HARD_COLLISION_ENABLED gate at the end of update_movement.

KEEP from current movement.py (Stage 6 work that is independent of RVO):
- _ATTACK_MOVE_LEASH_SQ constant
- _update_attack_move_state function
- has_combat_los function (the navmesh obstacle LOS export at the bottom)

INTEGRATION REQUIRED:
- Insert a call to _update_attack_move_state(store, active) inside the
  restored update_movement, after active = store.active_ids() is computed
  and before the main movement loop. This preserves the 6J attack_move
  fix on top of the restored steering.
- The restored update_movement must still call _resolve_collisions at the
  end if config.HARD_COLLISION_ENABLED is True. This should already be in
  the 2c29b0e baseline body — verify it's preserved through the restore.

================================================================
damage.py
================================================================

REMOVE from current damage.py:
- _friendly_blocks_shot function (entirely)
- The blocked / LINE_OF_FIRE_ENABLED branch at the top of the per-unit
  attack loop in resolve_damage. The post-revert flow should be: range
  check → navmesh obstacle LOS check (continue if blocked) → fire.
- The blocked_ticks increment/reset lines in resolve_damage.
- The blocked_ticks > BLOCKED_RETARGET_TICKS retarget block at the top
  of update_targeting.
- The import of _friendly_blocks_shot or any helper used only by it.

KEEP from current damage.py (real Stage 6 perf work, RVO-independent):
- The update_targeting(store, tmap, rng=None) signature with the tmap
  parameter.
- The spatial hash rebuild block at the top of update_targeting:
    tmap.spatial_hash.clear()
    for uid in active:
        tmap.spatial_hash.insert(uid, store.data[uid, FIELD_X], store.data[uid, FIELD_Y])
- The sorted(tmap.spatial_hash.query(mx, my_, engage_range)) replacing
  the old "for other in active" candidate loop in update_targeting.
- The navmesh obstacle LOS check in resolve_damage:
    if navmesh is not None and navmesh.has_obstacles:
        if not has_combat_los(navmesh, ax, ay, tx, ty):
            continue
  This is the obstacle LOS, NOT the friendly-occlusion LOS. It must be
  preserved. has_combat_los is imported from movement.

================================================================
unit.py
================================================================

REMOVE the blocked_ticks array from UnitStore.__init__. This array exists
only to support the LINE_OF_FIRE_ENABLED system being removed. Verify by
diffing against 2c29b0e:simulation/unit.py — the array should not be in
the baseline.

================================================================
config.py
================================================================

REMOVE these constants (lines ~581-583 in current config.py):
  RVO_NEIGHBOR_DIST
  RVO_TIME_HORIZON
  RVO_MAX_NEIGHBORS

REMOVE these constants (added with the LINE_OF_FIRE work):
  LINE_OF_FIRE_ENABLED
  BLOCKED_RETARGET_TICKS

KEEP these constants (pre-RVO hard collision system, still needed):
  HARD_COLLISION_ENABLED
  COLLISION_RESOLUTION_ITERATIONS
  UNIT_COLLISION_RADIUS
  STEERING_SEPARATION_RADIUS
  STEERING_OBSTACLE_AVOIDANCE_RANGE

================================================================
DELETE these test files (test bad behavior or RVO-specific scenarios):
================================================================

  simulation/test_6j_concavity_static.py
  simulation/test_6j_t3a_diagnostic.py
  simulation/test_6j_t3a_diagnostic.log

================================================================
DO NOT TOUCH any of these files under any circumstances:
================================================================

  simulation/invariants.py
  simulation/test_checkpoint_g5_claims.py
  simulation/character_selector.py
  simulation/sim_tuner.py
  simulation/sim_validator.py
  simulation/world.py
  simulation/mission_contracts.py
  simulation/outcome_resolver.py
  simulation/generational.py
  simulation/command.py

These contain Stage 5.5 work that is unrelated to RVO and must remain
exactly as it is in HEAD. If a diff against 2c29b0e shows changes in
any of these files, those changes are Stage 5.5 work and must be
preserved.

================================================================
VERIFICATION
================================================================

After the surgical edit, run:

  python -c "from simulation import movement, damage, unit, config; print('imports OK')"
  pytest simulation/test_checkpoint_6c.py -x
  pytest simulation/test_checkpoint_6d.py -x
  pytest simulation/test_checkpoint_6e.py -x
  pytest simulation/test_checkpoint_6k.py -x
  pytest simulation/test_checkpoint_g5_claims.py -x

Do NOT run these yourself. Report when the edits are complete and Westley
will run the test suite.

Expected post-revert state:
- 6C: pass
- 6D L5/L6: pass
- 6D L7: probably pass (the 175s drift was caused by RVO; if it still
  fails, that's a real bible question for Westley)
- 6E: pass
- 6K: pass trivially (cheap movement)
- G5 claims: must still pass (regression check that the surgical revert
  didn't touch Stage 5.5 work)
- All Stage 5.5 invariants M1-M19: must still pass

Do not run any tests. Do not write new tests. Do not refactor anything not
listed above. Report when complete.