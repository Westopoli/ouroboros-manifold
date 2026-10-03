# 2026-10-03: Python-against-C parity, first divergence per scene (diagnosis only, nothing changed)

Build: worktree ParityDiag, branch `push/pp-parity-diag` = `push/pp-c2` at 7bd84dc6 (Phase A, A5 collision fix, `PURSUE_BY_STEERING` default 1, give-up R-099-05, leash-anchor and blocked-target fixes). Instrument: `cd tests/csim && python -m parity.measure` (and `--diagnose`, C ids shifted by 3 so the targeting cohort matches), plus per-tick dumps of both engines for the first unit to differ. Tolerance as fixed by Westley (A149): 0.05 wu position, 2e-3 rad facing; untouched. Requirement (Westley, 2026-10-02): "the same exact logic from the python".

Experiments were run in a scratch copy of the worktree (one-line edits to the C or the Python, never committed) only to prove a cause: "confirmed" below means the one-line change moved the first divergence later or removed it. No engine file or test in the repository was edited.

Classes: (a) C bug, (b) deliberate difference we keep, (c) Python-side change so parity holds, (d) harness or fixture.

## Result on this build (default harness)

| scene | max position | max facing | first out of tolerance (pos / target / facing) |
|---|---|---|---|
| control_lone_march, control_diagonal_march | 0 | 0 | none |
| behind_own_row | 0 | 0.0015 rad | none (facing is the om_atan2 error, inside 2e-3) |
| three_in_file | 0 | 0.0015 rad | none (same) |
| target_walks_out_of_range | 45 wu | 0.0067 rad | tick 1 / 1 / 1 |
| attack_move_group_of_8 | 114.4 wu | 0.501 rad | tick 10 / 10 / 10 |
| wall_with_a_gap | **889.9 wu** | 1.188 rad | tick 1 / none / 8 (new since the earlier "near 0") |
| return_fire_on_the_march | 3.69 wu | 0.9 rad | tick 166 / 165 / 165 |
| crowd_converges | 126 wu | 3.137 rad | tick 22 / none / 1 |

With `--diagnose` (cohort aligned) the same scenes read: target_walks 45 wu (pos@34), group_of_8 94 wu (pos@37), return_fire 0 wu (facing 0.7 rad from tick 165, target differs from 165), wall and crowd unchanged.

## Causes, in the order they bite

### Shared by three scenes: C1, targeting cohort by C id, not Python uid (class b, one-line C fix available)
Python picks who may look for a target this tick by `uid % 4 == tick % 4` (`simulation/damage.py:216`); the C by `unit_id % 4` (`csrc/unit.c:2053`, `om_unit_targeting_cohort` at 2823). C ids are Python uid + 1, so every unit takes its turn one tick off. Evidence: target_walks, unit 0: C acquires at tick 1, Python at tick 4; group_of_8: C unit 5 acquires at tick 10, Python on 9 or 13; return_fire: C Sniper reacts at a different tick. `--diagnose` (ids shifted so the cohorts agree) removes the tick-1 and tick-10 divergences and takes return_fire's position error from 3.69 to 0. This is the "cohort alignment" on the deliberate list; it stays deliberate until Westley says otherwise, but the exact-parity fix is two lines: use `(unit_id - 1) % 4` at `unit.c:2053` and `unit.c:2823`. Needs a ruling because it moves every golden that has a combat in it.

### Shared by two scenes: C2, a sensor sighting is not an anchor (class c)
R-087-05 as amended (A167, commit 7bd84dc6): a sighting that only becomes the move goal sets no anchor. The Python still anchors at the sighting (`simulation/movement.py:283-304`, `_update_attack_move_state`), and the target is more than 200 wu away by definition, so the leash drops the target in the same tick: the Python frame shows target -1 and the unit walks on, while the C keeps the target and holds the moment it is in range. Evidence: target_walks (cohort aligned) tick 28, Python target -1, C target 1; group_of_8 tick 90, Python unit 4 walks two more ticks to 1520.8 while the C holds at 1505.9 (target 8 at 194 wu, in range). Python fix: anchor only once the target is within attack range (the rule A167 states), and `_resolve_collisions` "moving" (`movement.py:600-606`) must then mean "has a target in range", not "has any target", or a walking unit with a sighting is treated as stationary and pushed instead of pushing (tried: the position deviation shows up at tick 89 as 0.158 wu on units 4 and 5 until that is also changed). Not confirmed to zero: with only the anchor change the group scene's first divergence moves from tick 90 to tick 89 (that collision effect), and it was not chased further.

### target_walks_out_of_range
| item | value |
|---|---|
| max deviation | 45 wu, 0.0067 rad |
| first divergence | tick 1 (C acquires a target 3 ticks early) |
| causes in order | C1 cohort (tick 1); C2 sighting anchor (tick 28, aligned run); C3 backswing lock length (tick 34); C4 fire after move (tick 44) |
| class | b, c, c/b, a |
| proposed | see C1, C2; C3 and C4 below |

C3, backswing is 10 ticks in the C (`unit.c:158`, `0.5 * 20`), 11 in the Python: the Python counts it down with floats, `0.5 - 0.05` ten times is `6.9e-17`, still `> 0`, so it moves one tick later (`movement.py:330-338`, `damage.py:46`). Confirmed: with the C set to 11 the first divergence moves from tick 34 to tick 55. Which side is right is a ruling: the stated intent is 0.5 s = 10 ticks, so the fix that keeps the intent is on the Python side (compare against an epsilon, or count ticks); "exactly the Python" means the C takes 11. The same float residue is in the attack timer (`damage.py:21`): `0.8 - 16 * 0.05` is `-9.7e-17`, so 16 ticks fire on time, fine today, a trap for other intervals (class c).

C4, the C decides "in range, fire" from the positions at the start of its tick (AI first, movement after); the Python fires in `resolve_damage` after this tick's movement. With C3 set to 11 both units reach the same spot on tick 44 and the Python hits on tick 44, the C on tick 45 (hp trace: Python 479.75 at 44, C 486.5 until 45; repeats at 66/69, 87/92, 108/116). Likely class a (fire after movement in `om_tactical_step` order, `csrc/unit.c:2146-2156`); it is a step-order change, so it needs the Architect before anyone touches it. This one I inferred from the hp timeline and did not isolate with a one-line experiment.

### attack_move_group_of_8
| item | value |
|---|---|
| max deviation | 114.4 wu, 0.501 rad |
| first divergence | tick 10 (C1 cohort, unit 5) |
| next, cohort aligned | tick 37, unit 1: C5 detour reset (a) |
| next, detour fixed | tick 90, units 4 and 7: C2 sighting hold (c) |

C5, `om_command_move` clears the unit's steering detour (`csrc/tactical_move.c:2516`, `mu->deflecting = 0`; the same reset sits in the other order entry points, lines 997, 1723, 2400, 2419, 2485, 2698). The cohort turn of an attack-moving unit with a sighting calls it every 4 ticks (`unit.c:1910`, `om_tac_pursue_goal`), so a detour that should run 60 wu is cut short on the next cohort turn and the unit turns back toward its goal. The Python never clears a detour on a new target (`unit.py:131-142` `set_move_target` leaves `detour_remaining` alone; it is zeroed only on arrival, `movement.py:401`, 530). Unit 1 at tick 37: Python keeps stepping along the 52.5 wu detour (+6.2, +4.2), the C steps straight (+7.5, +0.5). Confirmed: removing the reset at 2516 moves the first position divergence from tick 37 to tick 90 (max 114 to 63 wu at the aligned run). Smallest fix: do not clear `deflecting` in `om_command_move` (and decide the same for the sibling resets, since a fresh player order in the Python also keeps its old detour). Class a.

### wall_with_a_gap
| item | value |
|---|---|
| max deviation | 889.9 wu, 1.188 rad |
| first divergence | tick 1 (the C walks straight through the wall) |
| cause | W1: layer transfer routing is on by default, the fixture does not turn it off (class d) |
| after W1, first divergence | tick 194, 4 wu, then 8 wu |
| causes | W2 lost tick per waypoint (a), W3 final waypoint radius (a) |

W1: `OM_TP_ROUTE_ACROSS_LAYERS` defaults to 1 (G4, merged in e1027c0f). The harness blocks the wall on layer 0 only, so the C unit "goes over" on layer 1 and ends 22 wu short at (1000, 903) behind a wall it ignored; the Python has no layers. Confirmed: setting the parameter (index 5) to 0 in the fixture gives max 8 wu / 0.006 rad, first out at tick 194. Fix is one line in `tests/csim/parity/parity_c.py`: `h.om_tactical_set_param(w, 5, 0.0)` beside the existing LEASH_BEFORE_DAMAGE line (the earlier "near 0" reading predates G4 reaching this branch). Class d.

W2: when the Python reaches a waypoint it pops it and ends that unit's turn without moving (`simulation/movement.py:386-392`, the `continue`), so each waypoint costs it one tick. The C replans the aim and moves in the same tick (`csrc/tactical_move.c:1923-1928`). From tick 194 the C is one step (4 wu) ahead, two after the second waypoint. Confirmed: returning after the replan on a waypoint arrival gives 4 wu, first out at tick 462. Class a (to be exact the C should skip the step).

W3: the Python's last waypoint is the goal and is arrived at within 2 radii = 30 wu (`movement.py:370`); the C stops the final leg within 1.5 radii = 22.5 wu (`tactical_move.c:1936`) even when it is steering at a waypoint. At tick 462 the Python stops 26.2 wu from the goal at (975.67, 915.20); the C walks one more step. Class a: while the aim is a waypoint, finish at `OM_MOVE_WAYPOINT_ARRIVE_MULT` radii.

### return_fire_on_the_march
| item | value |
|---|---|
| max deviation | 3.69 wu, 0.9 rad |
| first divergence | tick 165 target and facing, 166 position |
| causes | C1 cohort (the Sniper's acquiring tick); R1 turn rate from speed (a) |

With the cohort aligned the positions agree to 0 wu for all 300 ticks. What remains is R1: the C picks the turn rate from native speed bands (`tactical_move.c:429-433`: at least 100 Strike 6 rad/s, at least 60 Line 4, else Siege 2.5, constants `om_constants.h:598-602`); the Python picks it from the unit category (`simulation/facing.py:9-13,98`). The harness Sniper is category Strike with speed 60, so the C turns it at 4 rad/s (0.2 per tick) and the Python at 6 (0.3 per tick): facing 6.0832 against 5.9832 on tick 165, the gap growing to 0.7 rad. For the stock roster the two rules agree, so this only bites custom units. Class a, smallest fix: take the rate from `om_unit_profile_category` instead of the speed. (A harness-side alternative, giving the Sniper a speed of 100 or more, would hide it; it is not a fix.) Also seen: Python's Picket carries target 1 on tick 165 (damage sets it in the same step), the C one tick later; that is C4 again (AI before movement and fire).

### crowd_converges (not one of the six)
| item | value |
|---|---|
| max deviation | 126 wu, 3.137 rad |
| first divergence | facing tick 1; position tick 22 |
| causes | X1 facing tie at exactly pi (a); X2 collision pair order (b) |

X1: unit 0 must turn from 0 to exactly pi. The Python's `_shortest_arc` returns -pi, so it turns clockwise (facing 6.0832); the C's `om_wrap_pi` maps to the range (-pi, pi] (`tactical_move.c:408-411`) and turns anticlockwise (0.2). A pure tie-break, only on an exactly opposite heading; one-line fix: wrap to [-pi, pi) as the Python does. Class a.

X2: collision pair order. The Python takes a unit's partners cell by cell (3 x 3 neighbourhood, row then column), the C in id order. Evidence that the order alone explains the position drift: the Python reversed against the Python diverges first at tick 21 (135 wu max), the C against the Python at tick 22 (126 wu), the C against the reversed Python at tick 21 (127 wu). The six scenes are insensitive (reversed Python vs Python is 0 wu on all six, `--sensitivity`). Class b, as listed; exact parity through a pile-up would need the C to visit partners in the Python's cell order, which is a decision, not a bug.

## What closes what, in plain words

- Closed by a fixture line (d): wall's 889.9 wu (W1).
- Closed by small C fixes (a): C5 detour reset, W2, W3, R1 turn-rate source, X1 pi tie.
- Needs a Python change or a ruling to settle which side is "the logic" (c): C2 sighting anchor (the amended rule is Westley's, the Python predates it), C3 backswing length (floats vs ticks).
- Needs the Architect (step order): C4 fire after movement.
- Needs Westley (a deliberate difference becomes a bug if "exact" wins): C1 cohort by `id - 1`, X2 pair order.

Not verified: that everything above together takes all six scenes inside tolerance. Each cause was shown one at a time and each removed its own divergence, but the later ones (group_of_8 after tick 90, target_walks after tick 55) were not run to the end.
