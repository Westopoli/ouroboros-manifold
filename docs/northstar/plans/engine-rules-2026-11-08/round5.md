# Engine rule fixes, Round 5 (2026-11-17)

Continues `spec.md` in this directory; its sections Constraints and Test architecture bind this round unchanged. Round 5 builds Westley's rulings of 2026-11-17 and leaves the stage 4 rules it touches with a qualifying proof, so that stage 4 can be judged on an engine that obeys its rules.

Pre-flight (2026-11-17, `origin/main` `ade315c0b`): the rules below read as quoted in `docs/bible/epics/E-11-units-and-combat.md` (R-087-01, R-087-03, R-087-04, R-087-10) and `E-13-movement-and-command.md` (R-096-02, R-096-08, R-097-03, R-097-05, R-208-01) on this branch's first commit; no `Q-` row is open on S-087, S-096, S-097 or S-208; `csrc/ouroboros_sim.h`, `signatures.toml` and the pipe frames are not touched by any piece; the work list (engine sites, tests that go red, checker predicates) is `docs/reports/2026-11-17-targeting-rulings-check.md`, read against the engine at `2f2faa223`, which is the engine on this tip; the near-proof candidates are `docs/reports/2026-11-17-requirement-audit.md`. Not checked by running: that every candidate test is green today (the verifier's first step).

Run: one workflow from the Architect chat (DEC-round5-workflow-2026-11-17). Worktree `~/Projects/om-wt/er5`, branch `s/engine-rules-r5`. Every agent reads `~/Projects/om-wt/engine-rules-baseline/AGENT_RULES_R5.md` first.

## Pieces

Each piece names its rule, what is built, the kind of proof and the configuration the proof runs in. "Lab configuration" is what `scripts/skilllab/arena` launches for stage 4: walking units, obstacles, sight on.

### G1. Notice distance (E-11 R-087-04, E-13 R-096-02)
An idle or attack-moving unit with no target acquires the nearest enemy its side sees within its notice distance, and no enemy beyond it. The notice distance is the weapon's reach to that enemy (attack range with the reach table's multiplier for the target's layer, slant as R-087-10 has it) times `1 + OM_NOTICE_MARGIN`, `OM_NOTICE_MARGIN = 0.1` (`DRAFT-notice-margin`): one named constant, new, in an internal header; no public header changes. The leash (`om_tac_leash`) is not changed: it stays the larger of sensor radius and attack range and is no longer the acquisition radius.
Proof: scenario in `tests/csim/` (a Vanguard, range 300: an enemy standing at 340 is never acquired over 200 ticks; at 320 it is acquired at the next cohort turn, walked to 300 and fired on; a plain mover never acquires; an attack-mover passing an enemy at 340 walks on); whole-run in the lab configuration through the checker predicate of G7 on a catalogue layout.

### G2. The lock ends at the notice distance (E-11 R-087-03)
A lock ends when the target dies, leaves the side's sight, leaves the unit's notice distance, or the player orders the unit; the leash and the give-up of R-087-09 end it as before. A target taken by return fire (R-087-06) is exempt from the distance break until that lock ends some other way. After a drop for distance an idle unit holds where it stands and an attack-mover resumes toward its point (R-087-04, R-096-02); the leash return of DEC-leash-anchor-return-2026-11-01 applies to leash drops only. Threat first is not built.
Proof: scenario (a locked target walks away faster than the unit: the lock drops on the tick the target is beyond the notice distance and the unit does not follow; a slower target is followed until the leash; a unit shot from 500 wu by an enemy it sees pursues it past its notice distance, bounded by the leash); whole-run through G7.

### G3. Guard (E-13 R-096-08, R-208-01)
A guard acquires within its notice distance as every unit does, no longer anything its side sees; it follows no farther than `GUARD_RADIUS` from its post; its lock ends as G2; it returns to its post when the lock ends or the chase would pass the radius. Return fire and the readings of DEC-engine-rules-round2-2026-11-11 are unchanged.
Proof: scenario (an enemy seen at 450 from a guard of range 300 leaves the guard at its post for 200 ticks; an enemy at 320 is engaged; a retreating target is followed to 200 wu from the post and no farther, per tick); whole-run through the existing guard predicate, adjusted.

### G4. Unseen fire (E-11 R-087-01)
An attack-mover still on its way to its point is neither moved nor stopped by a hit it cannot see or reach: no move away, no halt, its destination unchanged. An idle unit and an attack-mover that has arrived move 200 wu away and hold there; while holding they acquire and return fire as an idle unit; a repeat hit they cannot answer moves them again. Plain movers, guards and units holding a target are unchanged.
Proof: scenario (an attack-mover hit from a hill it cannot see up keeps closing on its point every tick; an arrived one moves away about 200 wu and is still there 400 ticks later with no hits; an idle one the same); whole-run in the lab configuration on L-0061 or L-0080: no walker with an attack-move destination stands still under unseen fire, and no unit moves away more than once without a new hit.

### G5. Slope collision and the probe (E-13 R-097-05, R-097-03)
Two units within 30 wu that both stand on the same slope collide whichever side of its midline each is on; the steering probe treats such a unit as a unit on its layer. Units on different layers that are not on one slope still do not collide.
Proof: scenario on a slope (two walkers meeting across the midline are pushed to 30 wu apart; a walker on flat ground under a flyer is not pushed); whole-run on the six hill layouts of the Round 3 trial: no two units on one slope closer than 30 wu after the pass except at the iteration cap, and no unit flips layer back and forth across a midline (three or more changes within 20 ticks).

### G6. Hill layouts (`lab-staircase.md` stage 4, DEC-hill-order-points-2026-11-17)
In a catalogue layout where one side must climb a slope to reach the other, that side's attack-move point lies at least `DRAFT-hill-order-margin` = 30 wu past the slope's midline, on the high side.
Proof: a lint test over `docs/northstar/research/layer_dynamics/catalogue/L-*.toml` that computes, from the layout's own geometry and orders, each climbing side's point against the midline. Layouts that fail are corrected by moving the point up the slope and nothing else; each correction is listed in the report with the old and new point, for Westley's veto.

### G7. The lab checker (`scripts/skilllab/invariants.py`, `tests/skilllab/arena/engine_rules_oracle.py`)
- acquire: a pick is legal only if the target was the nearest enemy the side saw within the picker's notice distance at the pick.
- lock: a lock that ends because the target left the notice distance is a legal end, not a swap; a lock kept on a target beyond the notice distance for more than one cohort period is reported, except a return-fire lock.
- unseen fire (new, R-087-01): as G4's whole-run statement.
- slope collision (new, R-097-05): as G5's whole-run statement.
- guard: a guard's pick obeys the notice distance.
Each predicate has a planted case that it reports and a legal case it does not, on fights it was not designed around (the lesson of Round 2: a check that agrees with its own description can still be wrong).

### G8. Seven near-proofs (`docs/reports/2026-11-17-requirement-audit.md`, the table "What is closest")
R-093-02, R-008-04, R-084-04, R-083-03, R-097-10, R-007-01, R-096-08: each candidate is brought to all seven qualifications of `docs/method/requirements.md` Proof, or the report says which qualification cannot be met and why. One named function per rule that quotes the rule's text as it reads on this branch; the Then asserted, not a neighbour of it; the lab configuration; a recorded break that turns it red. A per-tick check is never replaced by a final-state check.

## Order

1. Tests, three writers at once on disjoint files: G1 to G3; G4 and G5; G6 and G7. Each writes its new tests red, and rewrites the existing tests that assert the old rule (list: the check report, section B) in `Test-defect:` commits naming the ruling.
2. Lab builder: G7, then G6's layout corrections.
3. Engine builder one: G1, G2, G3 (`csrc/unit.c`).
4. Engine builder two: G4, G5 (`csrc/unit.c`, `csrc/tactical_move.c`).
5. Near-proofs: G8.
6. Verify: every suite against the baselines; recorded hashes and pinned fight lengths that moved are re-pinned in `Test-defect:` commits after the checker passes the new run; one deliberate break per piece, each turning its test red.
7. Sweep of 199 fights, the four stage 4 fights with controls and their pictures, the stand-off count on the hill and trap fights.

A builder that finds a test wrong reports it and builds the rest. A piece that needs a public header change stops and is reported.

## Acceptance (the Architect, before the merge)

- New tests green; no red outside the baselines except re-pins, each in its own commit.
- Sweep: the checker reports nothing under the new predicates, or each count is explained; end reasons (wipe, cap, stand-off) set beside Round 4's.
- Stage 4 fights re-made into `docs/northstar/story_reviews/westley/arena_stage4/`; outcome of each beside Round 4's; no fight invalid.
- `docs/bible/algorithms.md` ALG-62 and ALG-68 rewritten by the Architect to what the engine now does; Proof lines written for every rule whose test qualifies; the "not built" notes removed from E-11 S-087 and R-097-05; report `docs/reports/2026-11-17-engine-rules-round-5.md`.

## Second pass (2026-11-17, after the first run)

The first run built G1 to G7 and six of the seven proofs of G8; verification found reds outside the baselines, so the pictures were not made. The Architect's rulings on what the agents reported; each agent of the second pass follows them.

### Test defects accepted (the test fixers apply them, each in a `Test-defect:` commit naming the rule line)

- Scenes that place an enemy beyond the notice distance and expect it acquired, chased or stepped toward: re-placed inside the notice distance, or turned into the assertion that it is not acquired. This covers the guard files (`test_E13_R096_08_guard_steps_and_returns.py`, `test_PP_unit_guard.py`), the leash scenes of `test_E11_S087_engage_on_sight.py` and `test_E11_R087_10_spherical_distance.py`, `test_PP_unit_pursuit.py`, `test_PP_C_g3_pursuit_by_sight.py`, the sight-loss control of `test_E11_R087_03_target_lock.py` and the premise of `test_E11_R087_01_move_away_completes.py`.
- A leash scene needs a target the unit can keep inside its notice distance: one slower than the unit, or one taken by return fire.
- A scene in which a unit must follow a target uses a type that does not auto-Brace (a Vanguard that halts in range braces and needs about 15 ticks to walk again; that is the ability's rule, R-086-03, not a defect).
- `test_PP_C_g5_direct_fire.py` and the return-fire cases of `test_PP_C_g5_area_return_fire.py`: the engagement edge is the reach to that layer times 1.1 (the notice distance), and the firing edge stays the reach itself; assert both. An idle unit that returns fire holds its attacker as its target from the hit (R-087-06); a test that expects a destination instead is rewritten.
- `test_R_087_04_two_16_unit_blobs_attack_moved_to_one_point_fight_to_elimination`: rewritten to the rule as it stands. The blobs fight while enemies are inside a unit's notice distance; survivors that have arrived and stand beyond each other's notice distance do not fight (R-087-04, last sentence). The test asserts that and records the survivors and their distance; the report names it as a stand-off for Westley.
- Arrival: a unit that followed route waypoints has arrived within 30 wu and its destination is cleared (R-099-04); tests that ask for 20 wu or for a destination after arrival are corrected.
- The return-fire exemption test of G2 measures the gap at the first hit, not the second.
- Lab: `RULES` has 13 entries; the planted guard cases of `test_invariants_give_up.py` and `test_invariants_nearest.py` follow the notice-distance guard; the oracle's `_hit_by` counts splash hits as hits; the unseen-fire premise moves from L-0061 (where every victim is now an attack-mover on its way) to a layout where idle or arrived units are hit; pinned unit pairs that no longer describe a fight are re-derived from the new run, never deleted.

### Spec statements withdrawn or changed

- G5, "no unit flips layer back and forth": withdrawn. A unit's layer on a slope is its side of the midline (E-01 R-004-06), so a push across the midline is a legal change. The whole-run test asserts instead, on every tick, that each unit on a slope has the layer of its side of the midline, and reports the flip count without asserting it. The engine's wait on a third layer change within 20 ticks (`om_move_layer_flip_allowed`, commits `ec3305704` and `a2d968771`) contradicts R-004-06 and is removed.
- G5, "no two units on one slope closer than 30 wu after the pass": the step limit on a slope (the no-jump rule of Round 2, `om_move_slope_clamp`) may leave a pair closer than 30 wu at the end of a tick; such a pair is apart again within `DRAFT-ramp-settle-ticks` = 3 ticks. The test and the checker predicate assert that.
- Recorded csim hashes that moved: re-pinned with the trailer `Test-defect: re-pinned after Round 5 (G1 to G5), old <value>, new <value>; green on main b23e605c9`. The lab checker cannot read a csim scene, so the control is the suite's green state on main.
- Lab pins (fight lengths, close-up files, stage 4 files): re-pinned only after the lab checker reports nothing on the new run of that fight.

### Engine items found (builders, one at a time, each checked by breaking)

1. The move away steps straight through a standing friend (L-0045, units 71 and 57): the move-away step goes through the same steering and collision as every other step.
2. Walkers stand 16 wu from their attack-move point with the destination still set, beside idle friends on the other side of a slope's midline (L-0028 units 5 and 10; L-0045 units 67 and 74): arrival inside the radius of R-099-04 ends the move, and an idle unit yields (R-097-10) to a mover on the same slope as it does on the same layer.
3. L-0084 tick 1691: three units acquire and fire at an enemy on the tick it first comes into sight. The tracer decides from the engine's own order of work in a tick whether the side saw the target when the unit picked it. If it did, the checker is wrong and reads the same tick's sight for a pick; if it did not, the engine is wrong.
4. R-087-01 reports on L-0084 (an attack-mover standing 6 to 7 frames after a hit, unit 94) and L-0045 (unit 87 moved again with no new hit): traced, then fixed where the engine is wrong.

### Not built, recorded for the landing

- The return-fire mark on a lock is not saved in save files; a loaded game ends that lock at the notice distance (as the give-up state, DEC-engine-rules-round2-2026-11-11 reading 8).
- L-0083 has two overlapping hill records that give opposite layers at one point: a layout defect, listed for Westley.
- `tests/skilllab/integration/test_speed.py` (1.6 s against a mark of 1.5 s): Westley's threshold; measured three times without the memory cap's `nice`, and reported.

## Third pass (2026-11-17)

The second pass left csim, integration, ground, qa and method clean, and twelve reds in the lab arena plus the speed mark. The tracer found the engine right and the checker wrong in all three traced reports: the engine moves every unit, then the cohort picks, then shots are fired, all in one tick, and sight is read live; so a pick or a shot on tick N is judged against frame N's positions and visible set.

Rulings:
- Checker (`scripts/skilllab/invariants.py`, `invariants_r5.py`): the predicate that reports "changed layer N times in M frames on a slope" is removed (withdrawn in the second pass). The nearest enemy and the notice distance of a pick are judged on frame N's positions, as the visible set already is. The slope pair predicate reports a pair under 30 wu only when it has stayed under 30 wu for more than `DRAFT-ramp-settle-ticks` = 3 ticks.
- Tests: `test_invariants_visible.py::test_R_093_02_the_set_before_the_step_decides` follows the tracer's verdict (frame N's set decides). The planted ticks of `test_invariants_r5_notice_and_lock.py` carry `hits`. In `test_engine_rules_r3_sight_lock.py` a lock that ends because the target left the notice distance is a legal end. The floor of cross-layer shots in `test_engine_rules_f7_spherical.py` is a premise floor of the detector, not Westley's threshold: it is set from the new run as a named `DRAFT-` with the old and new fight length beside it. The L-0045 control of `test_engine_rules_r4_idle_yield.py` counts a stall only when the unit in the walker's way is idle; a walker queued behind friends that hold a target is the queue on a narrow ramp that Westley accepted with the slope collision (DEC-slope-collision-2026-11-17). Planted cases are added for the two checker excuses the tracer named (a halt to fire at a seen target after an unseen hit; a hit from an attacker the side sees and the unit cannot reach).
- Speed: `tests/skilllab/integration/test_speed.py` (1.6 s against 1.5 s, green in Round 4). One attempt to win it back in the engine without changing behaviour: every recorded hash stays as re-pinned. The mark is not changed.

Open, recorded for the landing and not built in this round:
- A unit moving away that is blocked by a standing friend that does not yield (a guard) presses against it and the move away never ends.
- A pursuer never fires at a target that walks away, however slowly: it stops at exactly its range, may not fire on a tick it moved, and the target is out of range again the next tick.

## Fourth pass (2026-11-17)

The third pass's ruling "a pick is judged on frame N's positions" was wrong and is withdrawn. Measured by the lab builder and by the test fixer: inside one tick the engine works unit by unit, so a picker reads a mixed state, some enemies at this tick's position and some at the last tick's, with sight to match. Judging on either whole frame reports picks the engine made correctly on what it read.

Ruling, replacing it (checker `_acquire`, the notice check, and the oracle on the test side):
- A pick is reported as "not the nearest" only when some other enemy, in the side's visible set in both frame N-1 and frame N, is nearer than the picked target under every pairing of positions: the picker at its N-1 or N position, that enemy at its N-1 or N position, the target at its N-1 or N position. In words: the other enemy is nearer whichever of the two states the engine read for each of the three units.
- A pick is reported as "beyond the notice distance" only when the target is beyond it under every such pairing; a lock is reported as "kept beyond the notice distance" likewise; the comparison at the boundary is the engine's (a target exactly at the notice distance is inside it).
- A pick is reported as "unseen" only when the target is in neither frame's visible set (as the R-093-02 predicate already reads).
- No tolerance number is added. A planted case that is wrong by more than both units' steps is still reported.
The earlier experiment that models the id order exactly is not taken: it ties the checker to the engine's loop order.

That the engine reads a mixed state inside a tick, so the side with the higher unit ids sees its enemies one step fresher, is recorded as an open finding for the landing; it is older than this round and is not changed here.

Also in this pass: the premises of `test_engine_rules_r3_sight_lock.py::test_control_the_fight_and_the_trace_premises_hold` (pinned on the 3,923-tick run of L-0084) are re-derived from the 1,955-tick run by a test fixer; the held run-length pins are re-pinned once the checker reports nothing on L-0061 and L-0084; the sweep and the stage 4 pictures are made whatever the checker still reports, with every report listed.
