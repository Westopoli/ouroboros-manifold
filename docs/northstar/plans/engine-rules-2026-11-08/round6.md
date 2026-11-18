# Round 6: no lab fight ends in a draw (2026-11-18)

Continues `spec.md` and `round5.md` in this directory; the Constraints and Test architecture of `spec.md` bind this round. Why: `docs/reports/2026-11-18-lab-draws.md` (causes, evidence, the tracers' tables beside it). Westley, 2026-11-18: a lab fight that ends with both sides alive is a bug; it is either unit behaviour not following a requirement or the placement of the attack-move not following one. Round 6 fixes the unit behaviour, makes his approved fights the lab's standing set, and holds the placement fix (pieces E4 and L1) until he picks one of three ways (DEC-standoff-fix-open-2026-11-18); until then the stage 1 fight is expected to stay a draw and the standing set's command reports it.

Pre-flight (2026-11-18, `origin/main` `08c757a6e`): the rule lines quoted below read so in `docs/bible/epics/E-13-movement-and-command.md` and `E-11-units-and-combat.md` on this round's first commit; `docs/stories/H-040.md` "Orders and fight end" carries the new fight-end text; no `Q-` row is open on S-087, S-096, S-097 or S-099; `csrc/ouroboros_sim.h`, `signatures.toml` and the pipe frames are not touched by any piece (a piece that needs them stops and is reported). Run on `08c757a6e`: the approved fights of stages 2, 3 and 4 end by elimination, L-0054 with sight off ends as a stall at tick 11,020, and `scripts/skilllab/arena/situations.py` rejects SIT-0105, SIT-0106 and SIT-0107.

Two tracks in two worktrees, built at the same time and merged by the Architect: the engine in `~/Projects/om-wt/er6-engine` (branch `s/draws-r6-engine`), the lab in `~/Projects/om-wt/er6-lab` (branch `s/draws-r6-lab`). Every agent reads `~/Projects/om-wt/engine-rules-baseline/AGENT_RULES_R6.md` first. Test writers and builders are different agents.

## Engine track

### E1. An attack-move is resumed after every lock end (E-13 R-096-02)
"Given an attack-move ... when the lock ends ... it resumes toward the point ... an attack-move is not finished until the unit reaches its point". Today a unit sometimes loses its destination 1 to 4 ticks after its target dies and never gets another: about 3 percent of lock ends, 51 of 115 when the unit fired within 2 ticks of the lock end. A tracer finds the cause first (the comment above `om_tac_chase` in `csrc/unit.c` about a move refused in the pause after a shot is the lead). Built: the resume happens for every lock end (death of the target, loss of sight, the notice distance, the give-up of a blocked target), at once or as soon as the unit may move again; the unit keeps its original ordered point and slot.
Proof: scenario in `tests/csim/` (an attack-mover kills its target with a shot and, after the nine-tick pause, walks on to its point: asserted every tick, for a lone unit and for a group member, with the kill on the tick of the shot and one, two and three ticks after it; control: a unit whose target is alive does not resume). Whole-run through the checker predicate of L6 on the approved stage fights.

### E2. A unit walking alone arrives and gives up (E-13 R-099-04, R-099-05)
A walker ordered alone has arrived within its arrival radius (1.5 radii of its point, 2 radii when it followed route waypoints) and its destination is cleared; held within 75 wu of its point for 40 consecutive ticks without arriving it ends its order where it stands. The count is not written to a save file (a loaded game starts the count again; as the give-up state of Round 2). Round 5's first try at the 2-radius check on routed lone walkers turned 14 csim tests red: read `git show fd342241c` and its builder's note in `docs/reports/2026-11-17-engine-rules-round-5.md` before building.
Proof: scenario (a lone walker pushed back by a standing friend 18 wu from its point has no destination within 3 ticks; a lone walker held 60 wu from its point by a standing enemy ends its order on tick 40 and not on tick 39; a group member's give-up is unchanged). Whole-run: L-0028 sight control on the Round 5 engine has units 6, 9 and 10 holding a destination 16 to 19 wu from their point for 10,000 ticks; after the fix no unit holds a destination inside its arrival radius for more than 3 ticks in any regression fight.

### E3. Two halted units do not stay overlapped (E-13 R-097-10, the collision Invariant)
"given both are stationary, they split the displacement equally": the gate "and either was displaced earlier in the tick" is removed. The rule's other clauses are unchanged (a stationary unit moves 0 against a mover; an idle unit yields to a mover of its own side).
Proof: scenario (two units halted by engagement placed 20 wu apart are 30 wu apart within `DRAFT-ramp-settle-ticks` 3 ticks and do not move after; a stationary unit beside a mover still moves 0). Whole-run on L-0080 and L-0083, sight on: no two units on one layer closer than 28 wu for more than 3 ticks (today: 13 and 21 pairs, the longest 99 and 136 ticks). `tests/csim/test_E13_R097_10_proof_idle_yield.py` models the old gate in its fourth clause and is corrected by the test writer.

### E4. The two-groups scene (HELD: waits on Westley's pick, DEC-standoff-fix-open-2026-11-18; no agent builds or writes tests for this piece)
`tests/csim/test_E11_S087_engage_on_sight.py::test_R_087_04_two_16_unit_blobs_attack_moved_to_one_point_fight_to_elimination` asserts today that survivors standing apart are the correct end. Rewritten: after the scripted removal the scene places the attack-move again as the lab does (each side onto the living enemy nearest its centroid, when 200 ticks pass with no shot) and asserts that one side is eliminated; its control shows that without the second placement the survivors stand beyond each other's notice distance, as the reason the lab places it again, not as a correct end.

## Lab track

### L1. The runner places the attack-move again (HELD: one of three ways put to Westley, DEC-standoff-fix-open-2026-11-18; no agent builds or writes tests for this piece)
`scripts/skilllab/arena/run.py` (and `groups.py` for `orders = "groups"`): the quiet test is "no shot by either side for `SILENCE_TICKS` and no living unit came more than `DRAFT-closing-wu` 5 wu nearer its destination over those ticks" (a unit with no destination is not closing); the old "moved more than `MOVED_WU`" clause goes. When the fight is quiet and both sides are alive, every side that is not holding by its order (the holder of `hold:A` or `hold:B`; a group whose `hold` has not been released) is attack-moved, as one group, onto the position of the living enemy unit nearest that side's centroid; the quiet clock starts again. The fight document's `orders` gains `placed_again: [{tick, side, point}]`; the result gains `placements`. After `DRAFT-replace-max` 5 placements in a row with no shot between them the fight ends with `end: "silence"` and `stall: true`. A fight that never falls quiet is byte-identical to today's.
Proof: tests in `tests/skilllab/arena/` on real fights: L-0054 seed 1 sight off ends by elimination, with at least one placement recorded; a fight that ends by elimination today (L-0039 sight on) writes the same bytes as before; a planted fixture whose attacker can never reach the holder ends as a stall after exactly five placements; the trap layouts' unreleased groups are not re-ordered. The older stall fixtures of `test_run.py` are corrected to the new end rule.

### L2. The approved fights are the standing set (DEC-regression-set-2026-11-18)
A manifest `docs/northstar/research/layer_dynamics/arena/approved.toml`: one row per fight with its stage, layout or situation, sight setting, control kind, his expected winner and rate where he gave one, and the decision that approved it. Rows: stage 1 L-0054 (sight off); stage 2 SIT-0101 and SIT-0103 to SIT-0108 (sight off; SIT-0102 was denied as a roster finding); stage 3 L-0055, L-0073, L-0084, L-0039 (sight off) each with its ground control; stage 4 L-0061, L-0080, L-0083, L-0039 (sight on) each with its sight control. `python3 -m scripts.skilllab.arena.regression` runs every row (seed 1), prints one line per fight (end, winner, survivors, ticks, agreement with his expectation, checker reports) and exits non-zero if any fight ends without an elimination or the checker reports a rule. The sweep under `docs/reports/2026-11-07-rule-enforcement/sweep/` reads the manifest instead of its own layout lists and no longer switches the catalogue's rejection rule off.
Proof: a test that the manifest names exactly the fights of the stage decisions (DEC-stage1-seen-2026-11-01, DEC-stage2-seen-2026-11-02, DEC-stage3-layouts-2026-11-05, DEC-stage4-layouts-2026-11-05) and that every row loads; a slow test that runs the command and expects exit 0, carrying a named expected-draw list of exactly one row, stage 1 L-0054, with the decision id DEC-standoff-fix-open-2026-11-18 beside it (the list is emptied when the held piece lands); red until both tracks are merged; say so.

### L3. His stage 2 situations convert (`scripts/skilllab/arena/situations.py`)
SIT-0105, SIT-0106 and SIT-0107 are rejected today with "arc too small: 8 units at pitch 40 on 32 degrees need radius 502". They converted and were approved on 2026-11-02. Find the change that began rejecting them (`git log -S` on the message) and restore conversion without changing what the converted layout was on 2026-11-02; if the check is right and his numbers are wrong, do not change his files: report the three with the numbers.
Proof: a test that all of SIT-0101 to SIT-0109 convert.

### L4. The checker reports a dropped attack-move and an overlapped pair (`scripts/skilllab/invariants_r6.py`, wired into `invariants.py` last)
- R-096-02: a unit that held an attack-move destination and now has none, holds no target, is farther than its arrival radius from the point it was ordered to, and neither arrived nor gave up (within 75 wu for 40 ticks), is reported once, on the fourth tick it stands so.
- R-097-05, same layer: two units on one layer closer than 28 wu for more than `DRAFT-ramp-settle-ticks` 3 ticks are reported, as the slope pair is.
Each with a planted case it reports and a legal case it does not. On real fights both report until the engine track is merged: expected, and listed.

## Order

1. At once: the tracer (E1), two engine test writers (E1; E2 and E3), one lab test writer (L2 to L4).
2. Engine builder one (E1), then engine builder two (E2, E3), in the engine worktree; the lab builder (L2 to L4) in the lab worktree at the same time.
3. The Architect merges the lab branch into the engine branch. Verifiers: csim and transport with determinism; lab arena and top level with the pins; integration, ground, qa, method and specfactory. Recorded hashes and pins that move are re-pinned as Round 5's second pass rules.
4. The regression command on the merged tip: exit 0. The stage 4 fights and pictures are re-made if any stage 4 outcome moved.

## Acceptance (the Architect, before the merge to main)

- No fight of the manifest ends in a draw except stage 1 L-0054, which waits on the held piece; the checker reports nothing on them, or each report is explained.
- No red outside the baselines except re-pins; the two timing marks of Round 5 are reported with their new times.
- Each engine piece taken out on a scratch copy turns a named test red.
- The "not built" notes in R-099-04, R-099-05 and R-097-10 become what is built; `docs/bible/algorithms.md` ALG-68 follows E2 and E3; report `docs/reports/2026-11-18-engine-rules-round-6.md`.

Not in this round: a rule for a unit pacing farther than 75 wu from a slot it can never reach; weapon reach in the sight-off setting; the order points of layouts outside the manifest (L-0043, L-0077); a pursuer that never fires at a retreating target; firing units pushed by neighbours in a crowd.
