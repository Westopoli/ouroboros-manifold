# Movement side-step landing: BEFORE and AFTER on the approved fights

Piece LS3, read-only. BEFORE is `git archive origin/main` at 893a5af7f (the 45245ff88 tree plus the artifact ledger, docs only). AFTER is branch `s/movement-sidestep` at 0b07e3030, committed head (the implementer's later commits are not in it). `scripts/` and `docs/northstar/research/` are byte-identical in the two archives, so both ran the same runner, manifest and layouts; only `csrc/` differs. Seed 1, the orders each layout names, no controls (the regression command's controls are in its own section). Method and tools are under Not measured.

## Summary

1. Ten of the sixteen approved rows changed (all eight flyer rows and two walker rows); six walker rows are identical to the tick.
2. Three flyer rows change winner and lose the manifest's expected winner: L-0054 (expected draw; BEFORE ended apart with 14:22 alive at tick 10860, AFTER B wins 0:17 at tick 6408), SIT-0104 (A to B) and SIT-0106 (A to B); the other five flyer rows keep winner and expectation, SIT-0108 stays a mutual wipe.
3. Walker rows L-0080 and L-0083 changed without a flipped winner and both already disagreed with their expected A before (B wins before and after): L-0080 ends 0:25 at tick 1540, then 0:21 at tick 2296; L-0083 0:39 at 1823, then 0:38 at 1811; both are marked drift under review and not re-pinned.
4. Both clip fights equal variant A's recorded results: L-0054 B 0:17 at tick 6408 and SIT-0106 B 0:13 at tick 2301.
5. The give-up pass is gone: BEFORE gave up 54 times on L-0054, 1 on SIT-0104, 7 on L-0080 and 15 on L-0083 (none elsewhere), and L-0054 goes from 31 never-fired to 0, from 35 idle (200+ ticks) to 5, and from 5 overlap pairs to 2.
6. `python -m scripts.skilllab.arena.regression` on AFTER exits 1 with 8 failed lines, all R-097-05 checker reports (L-0054, L-0055, L-0084, L-0080, L-0083 and the L-0073, L-0080 and L-0083 controls); every one of the five main rows reported R-097-05 on BEFORE too, and SIT-0104 stops reporting it, so no main row newly fails.

## Table 1: outcomes

Winner is the regression command's naming (apart is `none`); `A:B` is survivors; `t` is the last tick. Kind from `movement_kind` in the fight file (set on stages 3 and 4, absent on 1 and 2). "Expected holds": for an expected draw, yes means both sides alive at the end; "mutual wipe" means both sides dead (SIT-0108).

| # | Row | Kind | Expected | BEFORE (winner A:B tick end) | AFTER | Result | Expected holds before / after |
|---|---|---|---|---|---|---|---|
| 1 | S1 L-0054 | FLYER | draw | none 14:22 t10860 apart | B 0:17 t6408 wipe | CHANGED, accepted (flyer) | yes / no |
| 2 | S2 SIT-0101 | FLYER | B | B 0:32 t586 wipe | B 0:28 t640 wipe | CHANGED, accepted (flyer) | yes / yes |
| 3 | S2 SIT-0103 | FLYER | B | B 0:7 t3046 wipe | B 0:7 t3525 wipe | CHANGED, accepted (flyer) | yes / yes |
| 4 | S2 SIT-0104 | FLYER | A | A 10:0 t6254 wipe | B 0:2 t10128 wipe | CHANGED, accepted (flyer) | yes / no |
| 5 | S2 SIT-0105 | FLYER | A | A 24:0 t1048 wipe | A 21:0 t1111 wipe | CHANGED, accepted (flyer) | yes / yes |
| 6 | S2 SIT-0106 | FLYER | A | A 5:0 t2543 wipe | B 0:13 t2301 wipe | CHANGED, accepted (flyer) | yes / no |
| 7 | S2 SIT-0107 | FLYER | B | B 0:19 t1788 wipe | B 0:20 t1418 wipe | CHANGED, accepted (flyer) | yes / yes |
| 8 | S2 SIT-0108 | FLYER | draw | none 0:0 t5438 wipe | none 0:0 t5365 wipe | CHANGED, accepted (flyer) | mutual wipe / mutual wipe |
| 9 | S3 L-0055 | WALKER | A | A 19:0 t1963 wipe | A 19:0 t1963 wipe | SAME | yes / yes |
| 10 | S3 L-0073 | WALKER | A | A 19:0 t2516 wipe | A 19:0 t2516 wipe | SAME | yes / yes |
| 11 | S3 L-0084 | WALKER | A | A 18:0 t2097 wipe | A 18:0 t2097 wipe | SAME | yes / yes |
| 12 | S3 L-0039 | WALKER | B | A 2:0 t3081 wipe | A 2:0 t3081 wipe | SAME | no / no |
| 13 | S4 L-0061 | WALKER | A | A 23:0 t1415 wipe | A 23:0 t1415 wipe | SAME | yes / yes |
| 14 | S4 L-0080 | WALKER | A | B 0:25 t1540 wipe | B 0:21 t2296 wipe | CHANGED, drift under review (not re-pinned) | no / no |
| 15 | S4 L-0083 | WALKER | A | B 0:39 t1823 wipe | B 0:38 t1811 wipe | CHANGED, drift under review (not re-pinned) | no / no |
| 16 | S4 L-0039 | WALKER | B | A 3:0 t2213 wipe | A 3:0 t2213 wipe | SAME | no / no |

## Table 2: other measures

Give-ups: BEFORE counts come from a scratch copy of BEFORE with a log line at the give-up site (verified: all 16 rows byte-equal in every other field to the unpatched BEFORE); AFTER has no give-up pass, n/a. Idle 200+ at the end: flyer rows by `r6-compare/tmp/stats.py` (standing, no target, 200+ ticks, split by the orders point: behind a mate nearer to it, or front; arrived units not in the split); walker rows by `walkers/tools/meas.py` (a unit with an order and no target that stood 200+ ticks). Overlap: `check_overlap`, radius 15, more than 3 consecutive frames, frames every 2 ticks.

| Row | Give-ups B / A | Never fired A+B (B / A) | Idle 200+ at end, behind/front (B / A) | Overlap pairs (B / A) | Checker rules (B / A) |
|---|---|---|---|---|---|
| S1 L-0054 | 54 / n/a | 31 / 0 | 35 (12/23) / 5 (1/4) | 5 / 2 | R-097-05 / R-097-05 |
| S2 SIT-0101 | 0 / n/a | 12 / 12 | 12 (4/5) / 10 (1/6) | 0 / 0 | none / none |
| S2 SIT-0103 | 0 / n/a | 0 / 0 | 0 (0/0) / 0 (0/0) | 0 / 0 | none / none |
| S2 SIT-0104 | 1 / n/a | 0 / 0 | 0 (0/0) / 0 (0/0) | 0 / 0 | R-097-05 / none |
| S2 SIT-0105 | 0 / n/a | 3 / 3 | 0 (0/0) / 0 (0/0) | 0 / 0 | none / none |
| S2 SIT-0106 | 0 / n/a | 2 / 2 | 0 (0/0) / 0 (0/0) | 0 / 0 | none / none |
| S2 SIT-0107 | 0 / n/a | 4 / 0 | 0 (0/0) / 0 (0/0) | 0 / 0 | none / none |
| S2 SIT-0108 | 0 / n/a | 0 / 0 | 0 (0/0) / 0 (0/0) | 0 / 0 | none / none |
| S3 L-0055 | 0 / n/a | 0 / 0 | 0 (0/0) / 0 (0/0) | 0 / 0 | R-097-05 / R-097-05 |
| S3 L-0073 | 0 / n/a | 0 / 0 | 0 (0/0) / 0 (0/0) | 0 / 0 | none / none |
| S3 L-0084 | 0 / n/a | 8 / 8 | 0 (0/0) / 0 (0/0) | 0 / 0 | R-097-05 / R-097-05 |
| S3 L-0039 | 0 / n/a | 0 / 0 | 0 (0/0) / 0 (0/0) | 0 / 0 | none / none |
| S4 L-0061 | 0 / n/a | 0 / 0 | 0 (0/0) / 0 (0/0) | 0 / 0 | none / none |
| S4 L-0080 | 7 / n/a | 0 / 1 | 0 (0/0) / 0 (0/0) | 0 / 0 | R-097-05 / R-097-05 |
| S4 L-0083 | 15 / n/a | 0 / 0 | 0 (0/0) / 0 (0/0) | 1 / 0 | R-097-05 / R-097-05 |
| S4 L-0039 | 0 / n/a | 0 / 0 | 0 (0/0) / 0 (0/0) | 0 / 0 | none / none |


Notes. (a) Walker rows by stats.py's definition instead (standing, no target, no order needed): L-0073 13 (2/11) in both trees (the holding side); L-0084 1 (0/1) in both; L-0083 1 front BEFORE, 0 AFTER; L-0080 0 BEFORE, 16 AFTER (11 behind, 3 front, 2 arrived), units standing without an order, which meas.py's definition does not count. (b) Never-fired B/A: L-0054 12+19 to 0, SIT-0107 4 to 0, L-0080 0 to 1 (side B).

## Clip fights

| Fight | Variant A recorded | AFTER |
|---|---|---|
| L-0054 | B 0:17 tick 6408, wipe; never fired 0; idle 5 (1 behind, 4 front); overlap 2 pairs | B 0:17 tick 6408, wipe; never fired 0; idle 5 (1/4); overlap 2 pairs. Equal. |
| SIT-0106 | B 0:13 tick 2301 | B 0:13 tick 2301. Equal. |

Source of the recorded values: `r6-compare/out/L-0054-A.facts.json` and the clip log. BEFORE (L-0054: apart at tick 10860, 14:22, 31 never fired, 35 idle, 5 pairs) equals the recorded "today" facts.

## Regression command on AFTER

`python -m scripts.skilllab.arena.regression`, run in an archive of 0b07e3030, exit code 1, "regression: 16 fights, 8 failed". Failing ids (all `checker=R-097-05`, the overlap rule): L-0054, L-0055, L-0084, L-0080, L-0083, L-0073-control, L-0080-control, L-0083-control. Every fight ended by wipe, none refused or "cannot fight". `agree=no` (not a failure): SIT-0104, SIT-0106, L-0039 (both), L-0080, L-0083. The run at 7592df8 printed the identical output; the head had moved to 0b07e3030 mid-task and the rows were re-run.

## Not measured

- BEFORE's regression command (exit code, controls): not run. The controls were run on AFTER only, so a before/after comparison of the three failing controls (L-0073, L-0080, L-0083) is not available.
- Seeds other than 1; both trees run at seed 1 only (the walker survey also used 10).
- Give-ups on AFTER: n/a, the pass is deleted (BEFORE needed a scratch log patch; no unpatched tree can count them).
- Idle uses two definitions (flyers stats.py, walkers meas.py), as the brief named; meas.py's own frames are every 10 ticks, here every 10th of every-2 frames (same ticks). Overlap on every-2 frames for all rows, so "3 frames" is 6 ticks, unlike the every-10 survey files.
- check_overlap was loaded by file path from `rig-fixes/scripts/look/state_checks.py` (it imports only `math`) rather than via PYTHONPATH, since both trees have their own `scripts` package.
- The implementer's worktree `/home/westopoli/Projects/om-wt/sidestep` was not entered; uncommitted work there (a `csrc/tactical_move.c` edit was uncommitted when first looked at) is not in AFTER. Committed head only.
- main's `893a5af7f` (artifact ledger, docs only) is not in AFTER; AFTER is not merged with it.
- No clips or pictures rendered or opened; no cross-platform determinism check; no tests run.
- Scratch: `/home/westopoli/Projects/om-wt/engine-rules-baseline/ls3/` (archives, tools, `out/rows-*.jsonl`, `out/regression-after.txt`).
