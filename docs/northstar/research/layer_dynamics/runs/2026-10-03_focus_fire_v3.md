# 2026-10-03: Phase D, focus fire batch v3 (material, nothing decided)

**Pass marks provisional (A174).** The README draft marks and the 0.05 win margin are drafts; the three statistic definitions stay unconfirmed. No threshold is chosen here. S2 skilled and S2 counter are the unconfirmed drafts.

**Tree.** Worktree PD-focus3, branch `push/pd-focus3`, HEAD at run time `097da951e9a6c4ddcdd04540595b1ddd8633f40d` = origin/push/sl-land-8 (main-ish, pl-land and pt-land inside, per-side policy A196, A198 hold-to-contact opening present but off: `Setup.approach` 0.0). origin/main at the time `0c53bdd310456e4bc9629beb6d51d16a2818e8ca`. C library built by the harness (`cc -O2`, as the tests do). Docs-only commit on top. Driver `run_v3.py` in `2026-10-03_focus_fire_v3/` (not in `scripts/skilllab`); `batches.py` untouched. Runtime 183 s with 8 worker processes, 9280 fights, exit 0.

## 1. What is run

Same cells and scans as v2 (16 against 8 to 24, side-swapped pairs of 10 seeds, 3 times the fights within 2 units of a break-even), headline cells only: identical (control), reach, S2 skilled, S2 counter. Side 0 is the cell's play (the skilled side in S2). Policy pair (side 0, side 1) through `Setup.target_policy`: 0 spread (nearest, kept while alive and in range), 1 focus (most damaged in range, re-evaluated every cohort turn, A196). Four pairs per cell: (0,0) baseline, (1,0) skilled focuses, (0,1) the enemy focuses (the swapped assignment), (1,1) both focus. Damage cell dropped (not headline).

## 2. What focus does per tick, looked at before the numbers

From the trace, seeds 0 to 9, 16 against 16, side 0 spawned first. Distinct targets = different enemy ids chosen by side 0's living units, per tick, from first contact to the first enemy loss. Switches = side 0 unit changes target while its old target still lives (a kept target is never dropped at policy 0, so those at (0,0) come from range losses and the walk).

| cell | pair | first enemy loss (mean tick) | first own loss | side 0 distinct targets | side 0 switches per fight |
|---|---|---|---|---|---|
| identical | (0,0) | 599 | 575 | 6.0 | 38 |
| identical | (1,0) | 576 | 575 | 5.4 | 50 |
| reach | (0,0) | 306 | 365 | 5.2 | 13 |
| reach | (1,0) | 249 | 364 | 4.5 | 39 |
| S2 skilled | (0,0) | 348 | 339 | 4.4 | 20 |
| S2 skilled | (1,0) | 340 | 339 | 4.2 | 32 |
| S2 counter | (0,0) | 387 | 378 | 6.5 | 39 |
| S2 counter | (1,0) | 350 | 378 | 5.4 | 58 |

Plain words. Focus works as ruled: the switch count goes up 12 to 26 per fight (side 0 only; side 1's count is unchanged, so the policy is per side). Concentration is mild, not dramatic: 0.2 to 1.1 fewer distinct targets and the first enemy loss comes 3 to 57 ticks (about 0 to 3 seconds) earlier, most in the reach cell (306 to 249). The reason is geometry. At first contact every enemy is undamaged, so "most damaged" is nearest, and the first kill is 250 to 600 ticks away; each shooter has only the front of the enemy blob in range, so different shooters see different damaged units and cannot all pile on one. Focus helps once damage exists and the blobs are in contact, not before. Seed 0 identical, side 0 at (1,0): the first four losses are 586, 589, 615, 765, with the third arriving 91 ticks earlier than at (0,0) (706).

## 3. Break-evens, whole units

Side 0 of 16 beats an enemy of the first number and loses to the second (refined harness break-even, same rule as v2). In brackets the interpolated enemy size where the mean margin crosses the 0.05 win margin (from the CSV), which shows moves smaller than one unit.

| cell | (0,0) spread v spread | (1,0) skilled focuses | (0,1) enemy focuses | (1,1) both focus |
|---|---|---|---|---|
| identical | 15 / 16 [15.60] | 15 / 16 [15.94] | 15 / 16 [15.29] | 15 / 16 [15.58] |
| reach | 16 / 17 [16.41] | 17 / 18 [17.50] | 16 / 17 [16.32] | 17 / 18 [17.35] |
| S2 skilled | 15 / 16 [15.69] | 16 / 17 [16.09] | 15 / 16 [15.43] | 15 / 16 [15.72] |
| S2 counter | 14 / 15 [14.78] | 15 / 16 [15.13] | 14 / 15 [14.57] | 14 / 15 [14.97] |

Pair spread at the edge (per-seed mean margin of the side-swapped pair, lowest to highest, at the "beats" size): identical -0.20 to 0.48, -0.10 to 0.47, -0.22 to 0.48, -0.19 to 0.47; reach -0.01 to 0.35, 0.02 to 0.30, -0.06 to 0.28, -0.07 to 0.30; S2 skilled -0.16 to 0.41, -0.22 to 0.38, -0.15 to 0.37, -0.16 to 0.40; S2 counter -0.15 to 0.42, -0.19 to 0.29, -0.16 to 0.39, 0.09 to 0.41 (order as the columns). The spreads are 0.3 to 0.7 wide; the means over 60 fights have standard errors of 0.02 to 0.03 (reach 0.005 to 0.02), so shifts of 0.05 to 0.1 in mean margin are real, a one-unit step is a threshold crossing, not necessarily a large move.

## 4. What changes against v2

- **Skilled focusing against a spreading side gains 0.3 to 1.1 units; both focusing adds nothing beyond that.** Interpolated gain of (1,0) over (0,0): identical +0.34, reach +1.09, S2 skilled +0.40, S2 counter +0.35. Whole-unit moves: reach +1, S2 skilled +1, S2 counter +1, identical none (its margin at 16 rises from -0.044 to 0.040, just under the 0.05 line).
- **The reverse assignment is the mirror, smaller:** the enemy focusing against a spreading side 0 costs side 0 0.1 to 0.3 units (identical -0.31, reach -0.09, S2 skilled -0.26, S2 counter -0.21). Same-sign everywhere, so the effect is not an artefact of the side; it is not exactly symmetric (focus helps more than it hurts in the reach cell).
- **v2's reach gain (+1 unit) is the reach side's focusing.** In v2 both sides switched together and the source could not be told; here (1,0) gives +1.09 and (0,1) gives -0.09, so it came from side 0.
- **v2 found nothing in S2 skilled and S2 counter; v3 finds +1 unit each.** In v2 both sides focused, which cancelled. Against a spreading enemy the gain shows. The size, 0.35 to 0.40 interpolated, is small next to the pair spreads.
- **The control stays a control:** identical (0,0) and (1,1) agree (15.60 and 15.58); mirror at (1,0) is 15.94, a skilled-side advantage of 0.34 units, about one third of the reach cell's.
- **Baseline reproduction:** (0,0) reproduces v2's nearest break-evens for identical (15/16), reach (16/17) and S2 skilled (15/16). S2 counter reads 14/15 against v2's 15/16; its margin at 15 is -0.007, one unit under the line (v2 was above). See 6.

## 5. Stalled counts

0 in all 16 scans (9280 fights). Fight length at the edge 2.2 to 2.5 thousand ticks mean; no stalemate, no cap.

## 6. Instrument questions

1. **The (0,0) per-seed traces do not match v2's.** v2 page: identical first kill by seed 0 to 5 was 674, 587, 747, 588, 849, 586; this tree gives 586, 587, 587, 587, 458, 586 (swap False, the same plain `OM_TP_TARGET_POLICY` 0 setting, the `(0,0)` pair and the unset pair give identical fights here). Aggregate break-evens agree in three of four cells and S2 counter differs by one unit. Not isolated; the trees differ by sl-land-6..8, pt-land and the formation work. Needs the harness lane to say which change moved the walk, or a v2 re-run on this tree.
2. First contact is tick 50 to 60 and the first kill 250 to 600 ticks later, as in v2 (A196 left the pace to Westley).
3. The pair assignment (0,1) is exactly the side-swapped test of (1,0) only if the cell's plays are symmetric; in S2 they are not (side 0 is skilled, side 1 the opponent play), so (0,1) is "the opponent focuses", not the same fight with sides exchanged.
4. Unit-id to side in the trace is inferred (first 16 ids side 0 when side 0 spawns first), not verified against the engine ids; if the harness numbers ids differently the distinct-target counts shift, the break-evens do not.

## 7. What could not be expressed

- S1, S3, S4, S5 skilled plays (A145), attack-target orders, mixed types, focus on a chosen target: still none, still waiting for their batches.
- "Focus" is the engine's most-damaged-in-range rule, a lab instrument (A196), not a skill with a cost or a decision; Q-008-05 stays Westley's.
- Focus by one side in the damage cell: not run (not headline).

## 8. Files

`2026-10-03_focus_fire_v3/`: `run_v3.py` (driver), `focus_fire_v3.csv` (9280 fights, columns cell, p0, p1), `focus_fire_v3_run.md`, `focus_fire_v3_page.html`, `trace_v3.py` and `trace_agg.py` (who shoots whom) with `trace_agg.log`, `interp.txt` (interpolated crossings and margins with standard errors), `run.log`.
