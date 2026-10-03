# 2026-10-03: the four "stalled" fights of formation v2 (A197)

Result: none of the four is a stall. Three are 32 against 32 fights still being fought when the 6000-tick cap hit; one is a mutual kill on the same tick. No engine fault found. The harness's stalled count is wrong for both kinds.

## Trees

- The v2 batch tree is 6bb0e34a (pl-land + sl-land-5). All four fights reproduce there exactly (same outcome, ticks, survivors, margin as the csv row), built `make OPT=-O2`, using the batch's own cell builder (`batches._formation()`), `BASE_SETTINGS` and `fight()`.
- On origin/push/sl-land-8 (097da951, the v3 tree) none of the four reproduces: they are decided fights (counter@8 seed 16: side 1, 1975 ticks; blob@32/31: side 0, 4989; blob@32/32: side 0, 3443; concave@32: side 1, 2761). The trees differ in 74 files (approach, group-move order, guard, target policy, A196 in csrc); the fights themselves differ. Not traced further. All analysis below is on 6bb0e34a.

## Which fights (csv row order per cell: swap False seeds 0..9, then refinement seeds 10..29, then swap True the same way)

| cell | enemy heads | csv fight index | swap | seed | csv outcome | ticks | survivors |
|---|---|---|---|---|---|---|---|
| counter@8 (Vanguard) | 8 | 16 | no | 16 | stalemate | 3385 | 0, 0 |
| blob@32 | 31 | 36 | yes | 6 | cap | 6000 | 1, 1 |
| blob@32 | 32 | 45 | yes | 15 | cap | 6000 | 1, 1 |
| concave@32 | 32 | 55 | yes | 25 | cap | 6000 | 1, 1 |

## What makes a fight "stalled" in the harness

`fight._run`: outcome "stalemate" if both sides have 0 living, or no unit's hp changed for `stalemate_ticks` (400); outcome "cap" at `max_ticks` (6000). `batches._STALLED = ("stalemate", "cap")` counts both as stalled, and `scan.cell_result` marks a cell undecided if any fight is either.

## Cause per fight

**counter@8, seed 16 (d: mutual kill, labelled stalemate).** The last two units (u1 side 0, u13 side 1), both hp 12.5 at tick 3350, 299.85 wu apart at range 300, each targeting the other, firing every 24 ticks; both die on tick 3385. Damage never stopped; the "both sides 0 living" branch calls a draw "stalemate". Ruled behaviour: the shots of a tick are all chosen before any hit lands (A178, `om_tac_fire_pass`), so equal-hp opponents die together.

**blob@32 (31) seed 6, blob@32 (32) seed 15, concave@32 (32) seed 25 (d: tick cap on a slow 1 against 1 duel).** Near-even 32 against 32 fights; the last two units (seed 6: u21 and u36) stand 285 to 300 wu apart, each holding on the other: order attack-move, halted, anchor set, target set, in range, `can_shoot` true, fire pending every tick. They are not stuck: a hit of 7.5 hp lands every 24 ticks on 500 hp units, so a duel from full hp takes about 1600 ticks. Measured with debug prints in a scratch copy of the library (not committed): seed 6 u21 357.5 / u36 327.5 at tick 5000, 50 / 20 at 6000; seed 15 u10 65 / u50 132.5 at 6000; seed 25 u27 65 / u41 117.5 at 6000. Rerun with `max_ticks` 20000: seed 6 side 1 wins at tick 6055 (0, 1); seed 15 side 0 at 6207 (1, 0); seed 25 side 0 at 6208 (1, 0). Damage lands every 24 ticks up to the cap; the 400-tick quiet detector never fires. The csv margins (0.004, -0.002, 0.003) are just the 1 against 1 leftover.

None of (a) leash deadlock, (b) group order finished with enemies out of reach, (c) collision pile applies: no unit holds without a target or with a target out of reach, and everyone left is in range and shooting.

## Against the rules

R-087-04/05 and R-096-02/03 (A188): an attack-moving unit with a target in attack range that it can shoot holds and fires; the leash measures the unit's own distance from its anchor. The duels are exactly that. Ruled behaviour, no engine fault, so no reproducing description.

## The harness detector

Wrong in two ways (instrument defects; not changed here):
1. `cap` is counted as stalled. A fight still in progress at 6000 ticks is not a stall; near-even 32 against 32 fights run to about 4500 to 6200 ticks, and a last 1 against 1 needs about 1600 more.
2. Both sides dead on the same tick is a draw, reported as "stalemate".
The real quiet-stalemate rule (400 ticks without hp change) fired for none of the 480 fights.

## Architect

- Rule: is a draw its own outcome, and is a cap on an active fight a "stalled" fight? Suggested instrument change (not made): report draw and cap separately from the quiet-stalemate count, or raise `max_ticks` for size 32 (a threshold, Westley's).
- v3 (sl-land-8) no longer has these cases because its fights differ; the cause of the change was not traced.
