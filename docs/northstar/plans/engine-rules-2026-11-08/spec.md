# Engine rule fixes: units obey the written movement and targeting rules (2026-11-08)

Bug fixes, not a story (Westley 2026-11-04). Method: for each round, one test-writer agent writes the failing tests, then one different implementer agent builds against them; no cascade. The chat drives both. Evidence: `docs/reports/2026-11-07-rule-enforcement.md` and its appendices (A code, B tests, C sweep with its scripts under `docs/reports/2026-11-07-rule-enforcement/sweep/`). Rulings: `docs/northstar/story_reviews/westley/decisions.md`, rows of 2026-11-07 and 2026-11-08.

## What this fixes, and what it does not

The engine breaks rules the bible already states. Every fix below names its rule; where the bible is silent the spec says which DRAFT number it uses and whose it is.

In scope, two rounds:

Round 1 (the walking, the shooting, the Wardens, the gate)
- F0. A whole-run rule checker in the lab; a fight that trips it is marked invalid.
- F1. A unit never enters a blocked cell (E-13 Invariants, R-207-06, R-207-07), and a walker routes around obstacles (R-097-01, R-207-05, R-190-07).
- F2. A unit that moves under its own power does not fire that tick (R-087-04, R-096-02), and the 0.5 s pause after a shot holds for group members too (R-084-04).
- F3. A target lock holds (R-087-03, R-087-08 as rewritten 2026-11-08).
- F4. Wardens do not stack (R-083-03, Q-084-01 closed 2026-10-20).

Round 2 (starts after Round 1 is landed and the sweep is re-run)
- F5. A unit whose line to its target is blocked looks for a firing spot, and gives the target up after 1 s (R-087-09, ruled 2026-10-07, unbuilt).
- F6. A guard steps toward a target it sees, cross-layer too, within 200 wu of its post, and returns (R-096-08 as rewritten 2026-11-08, R-208-01).
- F7. Range and radius tests are spherical, layer height included (R-087-10, new 2026-11-08).
- F8. A unit changing layer does not jump (position continuity; R-004-06, R-004-08 allow the layer to flip at the midline, not the unit to teleport).

Out of scope, listed so nothing is lost: one shared line-of-sight test for sight and fire (O4; the corner, canvas-edge, ground-band and disc disagreements remain; the endpoint-in-cell disagreement disappears once F1 lands); a C-side invariant checker (O2); deleting the baseline switches and dead state (O5, O6); I13 overlap residue; I14 firing arc (R-100-04 is draft); I27 leash reading; I29 and I30 (judged by the checker after F1, see Acceptance); dead units keeping a target id (I7c, harmless, would change checksums); attack-move not resumed after a kill (unproven); the replay `%r` message; the ring-after-anchor question and the stage 4 rulings Westley pinned; the sight and fire disagreement I11nl is investigated inside F7, not ruled out.

## Constraints (CLAUDE.md, binding)

- Contracts frozen: no change to `csrc/ouroboros_sim.h`, `signatures.toml` or the pipe frames. If a fix cannot be done without one, the implementer stops that fix, says why in the report, and moves to the next; the chat opens a contract story.
- New code in new files; wiring is its own commit, last for that fix. The position-commit function lives in a new `csrc/move_commit.c` with an internal header.
- Determinism: same seed and command stream, byte-identical trace; no fast-math, no platform transcendentals (spherical distance uses `sqrt` only if the existing code does; follow the file's practice), no hash-order or wall-clock input.
- Tests are the spec. The test-writer writes them red first, each naming the `R-###-##` it proves. The implementer never edits a test except in a commit with a `Test-defect:` trailer naming why. Goldens and hash pins that change because behaviour changed legitimately are re-pinned in their own `Test-defect:` commits naming the fix (F-number) that moved them, with the old and new value; the implementer checks that the new run passes the F0 checker before re-pinning (the lesson of Appendix B: "something diverged" is not "the new run is legal").
- Stale-doc tripwire: any doc claim a fix makes wrong is rewritten in the same change (`docs/bible/` rule text is not edited by agents; they list it in the report and the chat does it).
- Thresholds and DRAFT numbers are Westley's: each is a named constant with a `DRAFT-` comment and a row in the report.
- One fix at a time: hypothesis, log, targeted fix. Agents work in a worktree under `~/Projects/om-wt/`; never the repository checkout; no push, no merge.

## Test architecture (what the test-writer builds, every round)

The old tests were scenarios in a configuration the game does not ship. These tests must be:
1. Whole-run, per tick: they run a real fight (lab engine, `scripts/skilllab/engine.py`) with walkers, planar boxes, sight on, 6 to 24 units a side, hundreds to thousands of ticks, and assert the invariant on every tick through the F0 checker. At least one layout per fix is a lab catalogue layout (L-0039 for boxes, L-0061 for hills).
2. Specific, as C-level csim tests in `tests/csim/` for one unit pair or one geometry (the form the existing suite uses), including a positive control that fails when the guard is removed (mutate and watch it go red is the implementer's check, recorded in the report).
3. Named `R-###-##`, with `Rule pins:` lines where the file's neighbours have them.
4. Never weakened: a `Test-defect:` commit may not replace a per-tick assertion with a final-state assertion (what A172 did to `test_PP_unit_blocked_target.py`); a replacement per-tick invariant must be named.

## Round 1

### F0. Whole-run rule checker (lab, Python, no C change)
New `scripts/skilllab/invariants.py`; wiring in `scripts/skilllab/arena/run.py` (`fight`) and `closeup.py` as its own commit, last. The predicates already exist in `tests/skilllab/arena/stage4bug_*` and in `docs/reports/2026-11-07-rule-enforcement/sweep/inv_check.py`; reuse, do not copy the 39 KB file whole. Checks, each with its rule id, called after every `Engine.step`:
- `R-207-06` (E-13 Invariants): no living walker ends a tick inside a planar blocked cell on its layer (the engine's own `om_navmesh_is_cell_blocked`, not a Python re-derivation), tolerance 1 wu depth (DRAFT-inv-cell-depth 1, Westley's).
- `R-207-07`: position inside the canvas.
- `R-087-04`: a unit that fires on a tick did not move under its own power that tick (pushes by neighbours excluded: another unit within 40 wu, DRAFT-inv-push-radius 40).
- `R-084-04`: no own-power displacement in ticks 1 to 9 after a shot.
- `R-087-03`: a unit's target changes only when the previous target died, left its side's sight, the unit was given a new order, the leash dropped it (R-087-05), or R-087-09 gave it up.
- `R-087-09`: a held target not shootable for more than 20 ticks while the unit does not close in (DRAFT-inv-stuck-ticks 20).
- `R-083-03`: heal and damage reduction from Wardens do not stack.
- continuity: per-tick displacement at most max speed plus 1.3 wu unless pushed (DRAFT-inv-step-slack 1.3), layer change included.
A violation is `{rule, tick, unit, detail}`. The fight document gains optional `violations` (first 20) and `invalid` (bool) on `om-fight-2` (`snapshot.validate` accepts both absent or present, rejects on `om-fight-1`; `scripts/skilllab/arena/SNAPSHOT.md` documents them). `run.py` prints `INVALID <id> <rule> tick N unit U` per distinct rule and exits 2 when any fight is invalid unless `--allow-invalid`; `page.py` marks an invalid fight "INVALID: <rule> tick N unit U" and does not rank it; a layout whose check depends on a switch the run turned off (sight off) reports `suspended: <switch>` for that check, never a silent pass. Tests: each check fires on a planted bad trace and stays silent on a clean one (the positive control), and the L-0039 fight run on today's engine is `invalid` with `R-207-06` (red until F1).

### F1. Never enter an obstacle; walkers route around them
Bible: E-13 Invariants (line "A unit never enters a blocked cell"), R-207-06, R-207-07, R-097-01, R-207-05, R-190-07 ("an obstacle is a detour, never a full stop"). Ruled by Westley 2026-11-07: lab boxes are obstacles, never entered.
Facts (Appendix A section 1, 4): of the 14 position writers only the steer step guards entry; the walker step (`tactical_move.c:2296`), the kiting move (`:2414`), the flinch step (`unit.c:1914`, `om_tac_step_toward`) and the baseline move have none; `om_move_leave_blocked` (`:2127`) ejects the unit next tick (the saw-tooth and the 9 to 24 wu jumps, I5b); the router `walk_route.c` does not see mapgen boxes when there is no terrain (`walk_route.c:3`); the walker's blocked test ignores boxes once terrain exists (`:1276-1280`); five definitions of "blocked".
Build:
1. New `csrc/move_commit.c` (+ internal header): `om_move_commit(world, state, unit, nx, ny, reason)`: clamp to the map (R-207-07), refuse a step into a cell blocked for that unit on its layer (one `om_move_blocked_for(unit, cell)` that both mapgen cells and the walk mask feed; discs as the slide does), slide along the face else stay, return what it did. Reasons: STEER, WALK, KITE, FLINCH, EJECT, PUSH. `set_pos`, `teleport` and spawn are unchanged in behaviour.
2. Wiring, its own commit: the walker step, the kiting move, the flinch step (route it through the move side, not the row first) and the steer step call it. Delete nothing else.
3. Router: walkers path around mapgen blocked cells (R-097-01 shortest path on the 100 wu grid, straightened by line of sight where cells allow) with and without terrain; the walker's blocked test and the router agree on one definition.
4. Keep `om_move_leave_blocked` as the R-207-06 repair (a unit placed inside a cell, such as a wall built on it), but it must never fire for a unit that walked in (the checker proves it: after F1 no `R-207-06` violation in any lab fight).
Tests (red first): per-tick no unit in a blocked cell for 12 walkers attack-moving through a 100 x 800 wu box, fliers and walkers, sight on and off; a walker ordered across a box face arrives on the far side (routing; L-0039 geometry); a kiting unit and a flinching unit beside a box and at the canvas edge do not enter or leave; `leave_blocked` still ejects a unit a wall was placed on; the F0 checker reports 0 `R-207-06` on L-0039, L-0050, a chokepoint and a city layout. `om_navmesh_is_cell_blocked` knows planar boxes only, not the terrain walk mask, so R-207-06 covers boxes, walls and buildings, not unwalkable slope cells (Round 2 F8 looks at those). Flinching into a box or off the canvas does not enter today (a green control); the unguarded writer in play is the kiting move. Stop condition: if routing around planar cells needs a change to the header or pipe frames, ship the guard and report; the units will then stall on faces and the chat decides.

### F2. A unit that moves does not fire; backswing for groups
Bible: R-087-04 ("walks toward it until the enemy is within attack range, then halts and fires"), R-096-02, R-084-04, ALG-60.
Facts (Appendix A 2.3): the AI decides at P_c, movement runs, the fire pass shoots at P_{c+1} without testing whether the unit moved (`unit.c:2346-2369`); a unit released because its line was blocked walks one step and fires if the line cleared (the L-0039 blue Vanguard that drifted 4 wu every 4 to 6 ticks); group members use a frozen `speed_cap` and ignore backswing (`tactical_move.c:2168`, `:2491`) and Brace.
Build: the fire pass skips a unit that took a movement step under its own power in this tick (it fires on the next tick, when halted); a unit pushed by collision while halted still fires; backswing, Brace and Fortify speed rules apply to group members as to lone units (one source for effective speed). The first shot of every engagement is one tick later than today: all fight goldens that include a first shot change, which is expected (see Constraints on re-pinning).
Tests: a unit released by a blocked line that walks and whose line clears fires only on a tick it did not move (whole-run on L-0039 control and sight-on, `R-087-04` check 0); no own-power displacement in the 9 ticks after a shot, for a lone unit and for two attack-moved together (`R-084-04`); a pushed halted unit still fires; a plain mover never fires.

### F3. Target lock
Bible: R-087-03 and R-087-08 (rewritten 2026-11-08, `DEC-target-lock-nearest-2026-11-08`): a unit locks the nearest enemy its side sees and keeps the lock until the target dies, leaves its side's sight, or the unit gets a new order; acquisition runs only while the unit has no lock, at its cohort turn; the leash (R-087-05) and R-087-09 are their own rules and still break a lock.
Facts: `unit.c:2236-2240` also re-acquires at a cohort turn when `pursue && target not in attack range`, so a locked target that steps out of range is swapped for whatever is nearest; no test catches it (mutation M6, Appendix B: only goldens go red).
Build: remove that re-acquire-while-locked clause; the unit keeps chasing its locked target as R-087-04 says (walks until in range). Leave the `most_damaged` policy as it is (Q-008-05, lab-only) and say so in the report.
Tests: a unit locks the nearest of three; a nearer enemy appears (and another steps out of the target's way); it keeps firing or chasing the lock until the target dies; a locked target leaving range is chased, not swapped; a locked target leaving the side's sight is dropped and the next nearest visible one taken; a new order breaks the lock; the lock holds over 300 ticks in a fight (`R-087-03` check 0 over L-0039 and L-0050).

### F4. Wardens do not stack
Existing tests that pin the old stacking and must be rewritten in `Test-defect:` commits naming `R-083-03` and Q-084-01 closed (the bible is right, the tests are stale): `tests/csim/test_E11_S083_stats_traits_ability.py::test_R_083_03_that_unit_takes_10_percent`, `tests/csim/test_PP_unit_bugfix_G04_G15.py::test_R_083_03_a_second_warden_adds_005_not_009` and `::test_R_083_03_healing_stacks_per_warden`.
Bible: R-083-03, R-084-01 (reduction sum of Brace 0.50, Fortify 0.20, Warden aura 0.10), Q-084-01 closed "no stacking" 2026-10-20. The engine applies diminishing stacking (`OM_WARDEN_AURA_DIMINISH_FACTOR` 0.5, heal 0.075 per Warden). Build: one Warden in range counts; two or more do the same as one (heal 0.075 per tick once, reduction 0.10 once). Tests: 1, 2 and 3 Wardens in range of one unit give the same heal per tick and the same damage taken; the aura of a Warden out of range does not count; remove the dead `OM_WARDEN_AURA_DIMINISH_FACTOR` only if nothing else reads it.

### Round 1 acceptance (chat runs it after the implementer reports)
- `pytest` of the new tests green; `tests/csim` subset (PP, E13, E11 S08x, E01 R00x/T2, VG W/D, core) as red as before and no more (12 known reds on HEAD) apart from the re-pinned goldens, each re-pin in its `Test-defect:` commit; `tests/skilllab`; `tests/qa/test_fight_replay*.py`; `tests/method`.
- Re-run the sweep: `docs/reports/2026-11-07-rule-enforcement/sweep/` (about 9 minutes). Expect I1 0, I5b near 0, I2as 0, I2b 0, I10s 0, I11x 0; report what remains (I4b, I5tL, I23, I11nl are Round 2) and any new rule the sweep now trips.
- The four stage 4 fights re-run with controls (as `docs/reports/2026-11-06-stage4-fix-plan.md` step 5) into a scratch directory, not over Westley's `arena_stage4` files, with F0 on: zero violations of `R-207-06`, `R-207-07`, `R-087-04`, `R-084-04`, `R-087-03` and `R-083-03`. `R-087-09` and `continuity` violations are expected until Round 2 (F5, F8), so a fight may still be `invalid` for those two rules only; the report lists the counts.
- Mutation spot check by the implementer, three mutations on a scratch copy: delete the F1 guard, remove the F2 skip, restore the F3 re-acquire clause; each must turn a new test red.

## Round 2

### F5. R-087-09, blocked line: find a firing spot, give up after 1 s
Bible: R-087-09 (Westley 2026-10-07: "a unit gives up to pick another target if it can't find a firing spot within 1 second"), E-17 R-190-07. A unit whose target is in range but whose line is blocked steers by the blocked-movement probe (R-097-03) to a spot with a clear line; if none within 20 ticks it drops the target and acquires another. Number not in the bible: the dropped target is not eligible for that unit until the unit has a clear line to it again or DRAFT-giveup-exclusion-ticks 100 pass (Westley's to change); without it the unit would re-acquire the same nearest target at once. Facts: 3.5 million unit-ticks hold an unshootable target in the sweep (I4b), only in layouts with blocks, hills or slopes. Tests: a unit behind a box face with a target on the far side gives it up within 20 ticks, takes the next nearest, and does not re-take the first for 100 ticks; a unit that finds a clear spot by steering keeps the target; whole-run `R-087-09` check 0 over L-0039, L-0074 (city), L-0061.

### F6. Guard
Bible: R-096-08 as rewritten (`DEC-guard-cross-layer-2026-11-08`), R-208-01. The engine's guard holds and never steps (A170 comment `unit.c:2163`). Build: a guard engages any target its side sees, on its own layer or another, within vision; steps toward it up to `GUARD_RADIUS` 200 wu from its post; fires when reach and range allow; returns to its post when the target dies or when engaging it would take it past the radius; a move, attack-move, attack-target or layer order ends the guard. Tests: L-0061's four idle guard Vanguards with a seen enemy 301 to 357 wu away step and fire; a guard never ends a tick more than 200 wu from its post (R-096-08 leash check, the sweep's I26 stays clean); a guard returns; a cross-layer target out of vision is not engaged.

### F7. Spherical distance
Bible: R-087-10 (`DEC-range-spherical-2026-11-08`): every range and radius test is the horizontal distance and the height difference of the two units' layers together. `om_terrain_band_heights` (`csrc/ouroboros_sim.h:2092`, `terrain.c:1048`) already gives the band heights, so no contract change is expected; a world with no terrain has no heights and measures flat, as now. Start with the investigation the sweep left open (I11nl: `can_see` true and `can_shoot` false at 338 to 348 wu between layers on L-0061, ticks 59 to 61, Wardens 2 and 26, no blocked cell on the line): write the test for that pair first, find the cause (hypothesis, log, fix), then apply the one metric to attack range, sensor radius, leash and area radius (R-084-03). Stop condition: if a height cannot be read for a slope position, use the band of the unit's side of the midline (R-004-06) and say so. Tests: two units 300 wu apart horizontally, one layer up (band height h): in range for a 320 wu weapon only if sqrt(300² + h²) <= 320; sight and fire agree on the same pair; a flat world is unchanged.

### F8. Layer change without a jump
Bible: R-004-06, R-004-08 (a unit at the midline may change layer twice; position is continuous). Facts: 951 jumps of 24 to 78 wu with a layer change (I5tL) and 31,839 flickers (I23), 13 of 14 hill layouts; the flicker is allowed, the jump is not. After F1, re-measure first: if the jumps were `leave_blocked` ejections they are gone; otherwise find the writer (Appendix A table row 14: the cross-over write at `tactical_move.c:2619` has no cell recheck on the new layer). Tests: per-tick displacement at most max speed plus slack through a hill ramp, up and down, for each role (checker `continuity` 0 over L-0061, L-0063, L-0080, L-0083).

### Round 2 acceptance
As Round 1, plus: the sweep re-run shows I4b, I5tL, I11nl, I4bg at 0 or each remaining count explained in the report; stage 4 fights re-run into scratch, none invalid; the agent reports how every change moved the four fights' outcomes (winner, ticks) so Westley can judge the trap results against the new engine.

## Reports and records (the chat, after each round)

`docs/reports/2026-11-08-engine-rules-round-N.md`: what changed (file:line), tests added, re-pinned goldens with old and new values, sweep table before and after, the DRAFT constants, anything stopped. Bible text the agents listed as stale is rewritten by the chat. Decision rows for every choice left open here. Memory index updated.
