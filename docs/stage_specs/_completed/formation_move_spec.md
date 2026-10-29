# Formation Movement — Group Offsets + Group-Level Completion
# COMPLETE — implemented and signed off. FORMATION_MOVE_ENABLED = True (live default).

> **Note on filing:** This is a sub-spec, not a roadmap stage. It targets a specific bug surfaced during Stage 6 attack_move debugging (units pile on a shared target pixel and oscillate). Filed here because `docs/stage_specs/` is the project's canonical home for implementation specs; `dev_rules.md` says stage specs are disposable once complete.

## Goal

Replace the current "every unit in a group seeks the same pixel" movement with SC2-style formation movement: each unit gets a personal destination offset from the group centroid, and the group terminates when the centroid reaches the click target (not when every straggler has arrived). Prove this fixes the pile-up / oscillation visible in the 10v10 Strike-vs-Line scenario without regressing `update_movement` cost.

## Bible References

Read:
- `docs/bible/game_bible.md` — hub, including Design Experience Guide.
- `docs/bible_history/bible_2_00_combat.md` — only the Unit Roster and movement-related sections. Don't read the whole file.

Do not read other spokes. Movement is mechanical; no bible design question is at stake.

## Context

**Observed bug** (from Stage 6 attack_move debug session):
- `plain_move` mode: Raider unit group sent to a waypoint; units pile on the shared pixel at (2000, 1610) and oscillate y=1640 → 1621 → 1634 → 1640 for ~100 ticks before the attack_move trigger fires.
- Root cause: `apply_group_move` calls `set_move_target(uid, tx, ty)` for every uid with the same (tx, ty). All units seek the same point. Collision resolver shoves them off, probe steering redirects, they re-seek. No group concept exists post-command.
- Arrival is tested per-unit at `distance < collision_radius`. Because the arrival ring is shared, units repeatedly enter and get pushed out.

**Unrelated bug observed in the same session** (out of scope for this spec):
- The waypoint at y=1610 sends Strike into the middle of the Line's column (y=[1404–1747]) rather than the tip. That's a waypoint-authoring bug in whichever system is issuing the move. Flag only — do not fix in this spec.

**Builds on:** Stage 6 movement / command infrastructure (`movement.py`, `command.py`, `unit.py`). Does not touch navmesh, path cache, or combat.

**Protected files touched:** None. `movement.py`, `command.py`, `unit.py`, `config.py` are all not on the protected engine-file list in `CLAUDE.md`.

## What to Build

### Files to modify

**`unit.py`**
- Add `self.move_group_id: np.ndarray[int]` (default -1, one per uid).
- Add `self.move_groups: dict[int, MoveGroup]` and `self._next_move_group_id: int`.
- Modify `kill(uid)` to remove uid from any group it's in.
- Modify `set_move_target(uid, tx, ty)` to remove uid from any current group (re-command drops the unit from its old group). `apply_group_move` re-adds the unit to its new group after this call.

**`movement.py`**
- Rewrite `apply_group_move` to compute centroid, freeze per-unit offsets, create a group record, assign `move_group_id` to every member, set each unit's target to `(tx + ox, ty + oy)`.
- Apply the same logic in `apply_fast_move`.
- Handle unwalkable slots: if `path_cache.get(...)` returns `None` for a unit's slot, fall back to `(tx, ty)` for that unit (still in the group).
- Add `_update_move_groups(store)`: per-tick pass over all active groups. For each group, compute centroid over members that are alive, in this group, still moving (`has_move_target` True, not `auto_engage_target >= 0`). If centroid within `GROUP_ARRIVAL_RADIUS` of target OR the moving set is empty: clear `has_move_target`, `effective_speed`, `detour_remaining`, `waypoints`, and `move_group_id` for all surviving members; remove the group.
- Call `_update_move_groups` from `update_movement`, after the per-unit movement loop and before `_resolve_collisions`.
- Change per-unit arrival radius at final slot (no waypoints remaining) from `collision_radius` to `ARRIVAL_TOLERANCE_MULT × collision_radius`. Waypoint-to-waypoint arrival (pathfinding nodes) stays at `collision_radius` so chains still resolve cleanly. When a unit arrives at its slot, remove it from the group's moving set.

**`command.py`**
- Change `move` and `attack_move` handlers to route through `apply_group_move` once for the alive-unit list, then set per-unit attack flags (`attack_moving`, `engage_anchor_set`) in a follow-up loop for the attack_move case.
- `apply_group_move` is the single entry point for multi-unit target orders.

**`config.py`**
- `FORMATION_MOVE_ENABLED: bool` — default `False` during Steps 1–6, flipped to `True` in Step 7.
- `ARRIVAL_TOLERANCE_MULT: float = 1.5`.
- `GROUP_ARRIVAL_RADIUS: float` — default `2.0 * UNIT_COLLISION_RADIUS`. Tune in Step 4 if the diagnostic suggests otherwise.

### Traceability comments (required per `CLAUDE.md`)

- `movement.py apply_group_move`: comment pointing to `_update_move_groups` and to `command.py` move/attack_move handlers.
- `command.py` move/attack_move branches: comment pointing to `apply_group_move` as the formation logic site.
- `unit.py set_move_target` and `kill`: comment noting the group-membership cleanup and pointing to `movement.py _update_move_groups`.

## Input/Output Shapes

### MoveGroup record (in-memory, lives on `UnitStore`)

```python
{
    "uids": [7, 8, 9, 10, 11, 12],        # all members, alive or dead
    "target_x": 2000.0,
    "target_y": 1610.0,
    "offsets": {                            # frozen at order time
        7:  (-55.0,  0.0),
        8:  (  0.0,  0.0),
        9:  ( 55.0,  0.0),
        10: (-55.0, 40.0),
        11: (  0.0, 40.0),
        12: ( 55.0, 40.0),
    },
}
```

Indexed by integer `group_id`. Lifetime: from `apply_group_move` call until either centroid-arrival completion or all members have left the group (dead / re-commanded / individually arrived).

### Per-unit store fields added

- `move_group_id[uid]: int` — `-1` if not in a group, else the group id.

### Command flow (unchanged shape, new routing)

```
move / attack_move / fast_move / group_move
  → apply_group_move(store, unit_ids, tx, ty)
      → compute centroid
      → for each uid: set_move_target(uid, tx + offset_x, ty + offset_y)
      → register group in store.move_groups
```

No JSON / network shape changes. No tick delta shape changes. `docs/architecture.md` does not need an update.

## Integration Points

- **Kill switch:** `config.FORMATION_MOVE_ENABLED = False` restores pre-change behavior exactly. When off, `apply_group_move` sets the shared target for every uid (old path); `_update_move_groups` is a no-op because no groups are ever registered.
- **Single-unit orders:** `apply_group_move` with `len(unit_ids) == 1` skips offset math and does not register a group. Single-unit `move` / `attack_move` behavior is bit-identical to pre-change.
- **Replay determinism:** centroid and offsets are pure functions of unit positions at order time. No RNG. Replays are stable.
- **Attack_move engagement:** a unit that acquires `auto_engage_target` is already held in place by `movement.py:258`. The group pass excludes it from the centroid and from "still moving" — engaged units effectively count as arrived-in-place. If the whole group engages before centroid arrival, the group completes immediately.

## Steps (each is a mandatory checkpoint)

Every step ends with: run prove-it, show output to Westley, **STOP** and wait for approval. Do not batch steps. Per `dev_rules.md` this is the most important rule in the project.

### Step 1 — Baseline diagnostic

Write `simulation/test_formation_baseline.py`. Strike-vs-Line 10v10 at the same spawn layout as `test_t2_diagnostic.py`. At ticks {50, 100, 150, 200, 250}, print per-unit position, distance-to-shared-target, detour_remaining, has_move_target. Also print centroid and mean-distance-to-target at each sample. Measure wall time of `update_movement` in ms/tick averaged over the run.

Purpose:
- Confirm pile-up / oscillation numerically before touching code.
- Establish ms/tick baseline for the Step 6 performance budget.

**Stop. Show output. Wait.**

### Step 2 — Store fields + config flag

`unit.py`: add `move_group_id` array, `move_groups` dict, `_next_move_group_id` counter. Modify `kill` and `set_move_target` to drop the uid from any group (cleanup only — no group creation yet).

`config.py`: add `FORMATION_MOVE_ENABLED = False`, `ARRIVAL_TOLERANCE_MULT = 1.5`, `GROUP_ARRIVAL_RADIUS = 2.0 * UNIT_COLLISION_RADIUS`.

Prove-it: existing tests pass with no behavior change. Flag is off. Print the new config values and a dump of `store.move_group_id[:10]` after a baseline run to confirm the field exists and stays at -1.

**Stop. Show output. Wait.**

### Step 3 — Formation offsets in `apply_group_move`

Implement the offset + group-registration logic in `apply_group_move` behind the flag. Implement per-unit arrival-radius change (`ARRIVAL_TOLERANCE_MULT`) at final slot. Handle unwalkable-slot fallback.

Do **not** implement the group-completion pass yet. Goal of this step is to verify that units spread across their slots instead of piling — completion semantics are still per-unit arrival.

Prove-it: re-run Step 1 diagnostic with flag ON. Expect units distributed across slots, no oscillation, each unit arriving at its slot cleanly.

**Stop. Show output. Wait.**

### Step 4 — Group-level completion pass

Add `_update_move_groups(store)` and call it from `update_movement`. Implement centroid-arrival and empty-moving-set termination. Handle engaged units (excluded from moving set). Tune `GROUP_ARRIVAL_RADIUS` if the diagnostic suggests the default is wrong (flag the suggested value for Westley's approval — do not change the default without approval per `dev_rules.md` invariant-modification rule).

Prove-it: re-run Step 1 diagnostic. Expect the group to terminate at centroid arrival; stragglers stop in place; `store.move_groups` empties.

**Stop. Show output. Wait.**

### Step 5 — Route `move` / `attack_move` / `fast_move` through formation logic

Modify `command.py` handlers to call `apply_group_move` once per command. `attack_move` still sets `attack_moving` / `engage_anchor_set` per uid after the group call.

Prove-it:
- `test_attack_move_basic.py` (single-unit attack_move): expect bit-identical output to pre-change (single-unit path skips offset math).
- Re-run the 10v10 diagnostic in attack_move mode: expect clean formation march, engagement on contact, group completion.

**Stop. Show output. Wait.**

### Step 6 — Performance budget check

Per `dev_rules.md` "Performance regression discipline" this is mandatory. Add a scenario to `test_checkpoint_6k_engine_step.py` (or the closest sibling — confirm in Step 1 which file measures `update_movement` cost) that:

1. Runs a 10v10 group-order scenario at representative load.
2. Asserts a hard ms/tick ceiling on `update_movement` derived from the Step 1 baseline × 1.3.
3. Fails the checkpoint if exceeded.

Both formation offsets (O(n) once at order time) and the group-completion pass (O(groups × group_size) per tick) are linear. A regression is unlikely but the rule requires the check regardless.

**Stop. Show output. Wait.**

### Step 7 — Flip the default

Separate commit: `FORMATION_MOVE_ENABLED = True`. Kill switch remains.

**Stop. Wait for sign-off.**

### Step 8 — Docs

Update `docs/stage_specs/stage_6_spec.md` to describe the new group-move semantics (formation offsets + group-level completion). Do not touch `docs/architecture.md` — the tick delta shape is unchanged. Update `docs/project_state.md` if it references movement behavior.

Mark this spec file as COMPLETE at the top with the landing commit hash.

## Done Condition

All of the following must be observable from terminal output (not inferred from code review):

1. Step 1 baseline shows pile-up / oscillation numerically.
2. Step 3 with flag ON shows units spread across slots, no oscillation.
3. Step 4 shows group centroid-arrival terminating the order cleanly; `store.move_groups` reaches empty.
4. Step 5 shows single-unit attack_move unchanged and 10v10 attack_move marching in formation and engaging on contact.
5. Step 6 performance check passes with `update_movement` under the budget ceiling.
6. `FORMATION_MOVE_ENABLED = False` restores pre-change behavior bit-for-bit (quick sanity run).

Westley signs off after seeing all six.

## Out of Scope (flag only, do not build)

- The y=1610 waypoint-authoring bug (contact geometry — Strike hits Line's column middle instead of tip). Separate spec.
- Formation rotation to face movement direction.
- Adaptive spacing through corridors.
- Leader/follower flocking.
- Replacing `_probe_is_blocked` probe steering.
- Any ORCA/RVO revisit (see `docs/legacy/random/cc_paste_rvo_revert.md`).

## Files Created

Filled in after implementation:

- `simulation/test_formation_baseline.py` (Step 1)
- (any other new files — list here, one per line)
