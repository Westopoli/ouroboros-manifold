# Engine rules Round 6, part one (2026-11-18 to 2026-11-19)

Plan: `docs/northstar/plans/engine-rules-2026-11-08/round6.md`. Why the round was cut: `docs/reports/2026-11-18-lab-draws.md` and `docs/reports/2026-11-18-attack-move-drift.md`. Branch `s/draws-r6-engine`. Contracts untouched (`csrc/ouroboros_sim.h`, `signatures.toml`, the pipe frames: the diff against main is empty).

## What was built

| Piece | What a player or the lab sees | Where |
|---|---|---|
| E1 | A unit no longer loses its order in the half second after its own shot. Before, about 3 in 100 units that had just killed their target stood for good with their attack-move gone, and a move click given in that half second was dropped. | `om_move_walker_step`, `csrc/tactical_move.c` (`66fbc1ee9`) |
| E2 | A unit ordered alone that is held near its point for 2 s ends its order, as a group member does at its slot; before, it paced with no end (recorded: 10,000 ticks). The count, for group and lone alike, takes only ticks on which the unit came no nearer, so a slow unit still walking in is never stopped short; and an order given to the unit starts the count at zero. | `om_move_giveup_pass`, the order entry points (`64dacc0bc`, `7d2f839be`, `551b5acee`) |
| L2 | His approved fights are the lab's standing set: one command runs the 16 fights and their 8 controls, each under its one order per side, and fails on a draw or a checker report. The sweep reads the same list. | `docs/northstar/research/layer_dynamics/arena/approved.toml`, `scripts/skilllab/arena/regression.py` |
| L3 | Stage 2 situations SIT-0105 to SIT-0107 convert again, with the arc radii of the run he approved (DEC-sit-radii-2026-11-18). | `docs/northstar/research/layer_dynamics/situations/` |
| L4 | The checker reports two units of one layer standing closer than 28 wu for more than 3 ticks; and its count for R-087-09 (a held target that cannot be shot) is now the engine's own count, including a target taken by return fire. | `scripts/skilllab/invariants_r6.py`, `scripts/skilllab/invariants.py` |

Not built, each closed or put off with its reason in the plan: E3 (a walker wedged in a standing crowd overlaps; the trial of "a blocked walker waits" stalled every fight; Q-097-04 stays open), E4 and E5 (Westley, 2026-11-19, on Q-096-03: "B now": a group attack-mover resumes to its formation spot, as approved; DEC-formation-kept-2026-11-19). Part two of the round is piece L5: the lab names an end in which every survivor has finished its order.

## Rulings and corrections made on the way

- One order per side in a lab fight, never a second (DEC-one-click-2026-11-18). The Architect's plan to place the order again was withdrawn before any build.
- Targeting stays as Round 5 built it (DEC-targeting-confirmed-2026-11-18).
- Units stuck behind their own firing line are expected; the player micros them (DEC-stuck-behind-is-expected-2026-11-19).
- The give-up counts only ticks without progress, and a new order resets it (DEC-giveup-progress-2026-11-18). Found by the builder: counting every tick stopped a Bastion on a slope short of its point.
- Three readings by the Architect were refuted by traces before anything was built on them: that targeting had drifted; that the give-up counted while a unit stood to shoot; that halted pairs overlapped for want of a split. One draft of E2 (an arrival radius for a unit alone; a count not saved) was corrected before its build.

## Tests

New: `tests/csim/test_E13_R096_02_order_kept_through_shot_pause.py` (26), `tests/csim/test_E13_R099_05_lone_walker_arrives_and_gives_up.py` (14), `tests/csim/test_E13_R099_05_giveup_counts_only_ticks_without_progress.py` (9), `tests/csim/test_E13_R097_10_halted_pair_separates.py` (4, controls), `tests/skilllab/arena/test_regression_manifest.py`, `test_situations_convert_all.py`, `test_invariants_r6_same_layer_overlap.py`, `tests/skilllab/test_invariants_giveup_count.py` (24).

Corrected, each in a commit with a `Test-defect:` trailer: three assertions that a lone mover held at a unit keeps its destination for 100 ticks; the group give-up test that counted walk-in ticks; the unseen-fire stand measure; four pipe tests (below); recorded traces and fight numbers that moved, each traced to its first differing tick and unit before it was recorded again.

Found red on main and not from this round: four tests of `tests/transport` had been red since Round 4 (2026-11-12, idle units step aside), because Rounds 4 and 5 did not compare that folder with a baseline. Three were given a scene whose premise is true today; one, whose premise is the opposite of R-097-03 and R-097-10 and cannot be staged through the pipe, was retired with the csim test that holds the property named in the file. Every frame the client receives still rebuilds to the full state.

## Verification at `1e45e28ec` and after

- Engine (`tests/csim`, `tests/transport`), from a clean build of the archived tip: no red outside the baseline; 26 baseline reds green; two runs of the determinism and byte-identity tests agree test for test. Each of the four engine changes, taken out on a scratch copy, turns its named tests red (23 of 26; 7 of 13; 3 of 9 and the slope test; 4 of 9).
- Client and method (`tests/qa`, `tests/method`, `tests/specfactory`): no red from this round. `scripts/play.sh --check` reaches the game's first scene and cannot capture under a virtual display, as in Round 5; the gate's playthrough directory (`tests/qa/desktop`) is green.
- Lab (`tests/skilllab`): outside the arena no red beyond the baseline. In the arena thirteen tests were red: two checker reports (traced: the engine is right in both, the measure was off; corrected as above) and recorded numbers that moved with the fights.
- One order per side, counted: the stage 1 fight receives two attack-moves at tick 0 and nothing after; a trap receives its guards and one attack-move at tick 0 and the three holding groups' attack-moves when it springs.

- Final pass at `66c937833` (engine source unchanged since `1e45e28ec`): `tests/skilllab` arena 759 passed and none red; top level, integration and ground red only where the baseline is; the csim files touched since, 67 passed; `tests/specfactory` its eight known reds; `tests/method` green; the four new Proof lines name tests that collect and pass; the standing set's output byte-identical to the earlier run. Not settled: `tests/skilllab/integration/test_planted_advantage.py` did not finish inside the verifier's 595 s when run alone (four full scans at about 300 s each; neither it nor the scan changed in this round, and the earlier verifier's integration run completed); `test_speed.py` (scan 307 s against 30 s; one fight 1.9 s against 1.5 s) and `test_umbrella.py` (over 590 s) are over their marks as on main.
- Recorded numbers that moved were recorded again only after the first differing tick and unit of each fight had been tied to one of the four engine changes (eight arena tests, seven csim recordings). Two arena controls whose fights no longer held what they looked for were re-anchored so their neighbours are not vacuous: the move-away tests now use L-0080 (units 46, 23 and 44 move away after their orders end) with L-0081 kept for the attack-movers that are not stopped; the idle-yield control asserts unit 18 walking past an idle unit of its own side on ticks 1038 to 1054. One tolerance changed with that and is Westley's: a move away from unseen fire is accepted from 195 wu (`DRAFT-move-away-short` 5, was 1), since on hills the path curves and the three units end 196.6 to 199.5 wu from where they began.
- The stage 4 folder (`docs/northstar/story_reviews/westley/arena_stage4/`) was re-made on this engine by the commands of 2026-11-17: same winners; L-0080 0:25 at tick 1540, L-0083 0:39 at 1823, the L-0039 control at 2412. The page marks both trap fights invalid for the overlapped pairs (R-097-05).

## The standing set on this engine

Same winners as on main's engine in every fight. Two ends with both sides alive, both carried to part two: the stage 1 fight L-0054 (14 against 22 at tick 10,860: every survivor has finished its order, the kind of end DEC-formation-kept names as expected) and the ground control of L-0084 (40 against 56 at tick 820, not yet traced). The overlap check reports on L-0054, SIT-0104, L-0055, L-0084, L-0080, L-0083 and three controls: E3, put off. The sight controls of L-0061, L-0080 and L-0083 end exactly as their fights do; winners differ from his expectation on SIT-0106, L-0039 (both stages), L-0080 and L-0083: both told to him, neither traced.

## Part two (2026-11-19, lab only; branch `s/draws-r6b-lab`)

- L5: a quiet end is written `end: "apart"`, and is not a failure, when the sides fought (a shot was fired), no living unit holds a destination or a target, and no two living enemies stand within the notice distance of either. The stage 1 fight ends so: 14 against 22 at tick 10,860. A quiet end with no shot fired stays a stall: the sides never met, which is a fault of where the order was placed. Pages show "apart: nearest enemies N wu: bring to Westley"; a rated block lists its apart seeds.
- L6: the ground control of L-0084 fired no shot (traced: the twin removed the slope and left the holders on layer 1 and the attackers on layer 0; with sight off nobody shoots across layers). A control's units now stand on the layer the featureless ground has under them. The control ends by elimination, B 27 left at tick 1361, against A 18 left with the slope. The other three stage 3 twins are byte-identical.
- The standing set after part two: 14 fights and 8 controls end by elimination, the stage 1 fight ends apart, no draw. The command still exits non-zero, on the overlap reports of E3 alone (nine rows).
- Checked: all 54 arena files green; the lab's top-level files that touch the arena, snapshot, page and rate green; the lab docs lint green; no pinned fight hash moved. The stage folders he approved were not re-made.

## Open after the round

- Done in part two: piece L5; the L-0084 ground control.
- Q-097-04: overlapped pairs in a jam (141 pairs in the stage 1 fight, the closest 6 wu apart): a design of its own for the push pass and the steering.
- With Westley: whether stage 4 approval waits on the overlap; why sight changes nothing in three stage 4 fights; the point at which a trap springs; the expected winner of a mirrored fight on a generated map.
- Noted, not traced: the checker reports a planted 300 wu jump as a continuity break with sight off and not with sight on; the pipe has no working guard or hold verb; `test_speed.py` and `test_umbrella.py` remain over their marks.
