# 2026-10-03: Phase D, focus fire batch v2 (material, nothing decided)

**Pass marks provisional (A174).** The README draft marks and the 0.05 win margin are drafts; the three statistic definitions stay unconfirmed. No threshold is chosen here.

**Tree.** Worktree PD-focus2, branch `push/pd-focus2`. HEAD `ee8ae9c69defd2df477e99ecc2c2c9f70e3874e3` = origin/main `0b1ed3f4a7292ec174c494470b4fc194af49d3d5` plus merged origin/push/pl-land `1361db85ea08ca8cfc61f0162746bd2beacf8c2f` (A188 leash lane, not yet on main) plus origin/push/sl-land-5 `b2ad548272b9705189c04eb6007e5edcd9139f30`. Both merges conflicted only in `docs/northstar/plans/push_ledger_2026-09-22.md` (rows appended by both sides; resolved by keeping all rows); no code conflicts. C library built with `make OPT=-O2`. Command: `python -m scripts.skilllab batch focus_fire --out docs/northstar/research/layer_dynamics/runs/2026-10-03_focus_fire_v2/`. Runtime 9 min 36 s, exit 0, 5800 fights. Files in `2026-10-03_focus_fire_v2/`: `focus_fire_run.md`, `focus_fire.csv`, `focus_fire_page.html`.

## 1. What the batch is (and is not)

16 Vanguards on side 0 against 8 to 24 on side 1, open map, both blobs, attack-move at each other. The only thing varied is `OM_TP_TARGET_POLICY` (0 nearest, 1 most damaged in range), a single world parameter. It therefore applies to **both sides at once**. Side 0's play is the cell (identical, damage +20 percent, reach +20 percent, S2 skilled, S2 counter). "Focus fire" here means "everyone re-picks the most damaged" versus "everyone re-picks the nearest"; one side focusing against a side spreading cannot be expressed.

Code reading (csrc/unit.c): a unit picks a target only when it has none, or when it pursues and its target is out of range. A living in-range target is kept. So the policy decides only the first acquisition and re-acquisition after a kill.

## 2. What each play does, looked at before the numbers

Seed 0, 16 against 16, side 0 spawned first, from the trace (target id per unit per tick).

| cell | policy | first contact | targets in use, side 0 / side 1 (tick 300) | first kill | first-kill ordering |
|---|---|---|---|---|---|
| identical | nearest | 60 | 7 / 6 distinct | 674 (a side 0 unit) | side 1's first loss 850 |
| identical | most damaged | 60 | 7 / 6 | 674 | identical to nearest up to tick 850, same 8 first losses |
| damage | nearest | 60 | 7 / 6 | 674 | side 1 loses units from 709 |
| damage | most damaged | 60 | 7 / 6 | 674 | same first four losses as nearest, diverges at tick 785 |
| reach | nearest | 50 | 8 / 3 | 249 (side 1) | side 1 loses first at 249, side 0 at 389 |
| reach | most damaged | 50 | 5 / 3 | 249 | same first kill; second side 1 loss 338 against 459 under nearest |

Across seeds 0 to 5, identical and reach: first-kill ticks and first-loss ticks per seed are the same under both policies (identical 674, 587, 747, 588, 849, 586; reach 249, 322, 316, 316, 249, 314). Mean distinct targets under fire from tick 100 to the first kill: identical 7.3 / 7.6 (side 0 / side 1) under both policies; reach 5.6 / 3.3 under both.

Plain words. With 16 shooters, 6 to 8 distinct targets are chosen from the first volleys and the choice is then held until that target dies, so damage is spread across half the enemy and the first kill arrives late (tick 586 to 849, about 10 to 14 seconds after contact at tick 60). The policy does not change that spreading at all, because at first acquisition everyone is undamaged and "most damaged" falls back to nearest. It only matters after kills, when the shooters of a dead target re-pick. This is why the nearest and most damaged runs are indistinguishable in first-kill time. In the reach cell (side 0 outranges by 20 percent) side 1 sits on 3 targets, side 0 on 5 to 8, and the reach side kills first at tick 249.

Closest pair at ticks 60, 100, 200 and 400 (identical, seed 0): 293 wu every time, Vanguard range is 300. So the units stop just inside range; the 162 to 190 wu stand-off of the formation batch is not present on this tree (see section 6).

## 3. Break-evens, whole units

Side 0 of 16 beats an enemy of the first number and loses to the second (refined lab break-even). 20 fights per cell, 60 within 2 enemy units of the break-even.

| cell | nearest | most damaged | change |
|---|---|---|---|
| identical | 15 / 16 | 15 / 16 | none |
| damage | 17 / 18 | 17 / 18 | none |
| reach | 16 / 17 | 17 / 18 | +1 unit |
| S2 skilled (unconfirmed draft) | 15 / 16 | 15 / 16 | none |
| S2 counter (unconfirmed draft) | 15 / 16 | 15 / 16 | none |

A mirror reads 15 / 16 here, not 16 / 17: the 0.05 win margin makes a 16 against 16 fight (mean margin -0.01) a non-win. Interpolating mean margin from the CSV, the reach cell moves from about 16.5 to about 17.3 enemy units (+0.7). Margin differences between the policies in the other four cells are 0.01 or less except damage at 19 (0.02); inside noise. Both policies produced the exact same fight (ticks and margin) in 24 of 2860 paired fights, so the policy does change fights, just not their result.

Both sides use the policy, so the reach gain may come from either side's retargeting; it cannot be attributed.

## 4. Noise and the 3 x rule (A187)

The harness does it: cells within 2 enemy units of a break-even run 3 times the fights (60 instead of 20), and the page prints the pair spread (the per-seed mean margin of the two side-swapped fights, lowest to highest). At the edge: identical -0.07 to 0.39 and -0.16 to 0.40, damage -0.17 to 0.38 and -0.18 to 0.35, reach 0.01 to 0.39 and -0.07 to 0.31, S2 skilled -0.06 to 0.43 and 0.02 to 0.43, S2 counter -0.23 to 0.30 and -0.25 to 0.29 (nearest, then most damaged). Per-seed standard deviation of margin at the edge is 0.12 to 0.25, so the mean over 60 fights is about 0.02 to 0.03 either way, well below the spreads. Reach is the only cell with a margin difference (0.13 at 16, 0.20 at 17, 0.12 at 18, standard errors about 0.02) clearly beyond that.

## 5. Stalled counts

0 in all 10 variant scans (5800 fights). Outcomes: side 0 won 3093, side 1 2707; no stalemate, no cap. Fight length 2.2 to 3.4 thousand ticks at the edge.

## 6. Instrument defects of the formation batch, still relevant?

- **Stand-off (162 to 190 wu): not present.** Closest pair 293 wu at range 300 on this tree, held from tick 60. Likely the pl-land leash change; I did not isolate which change did it. The new feature is that fights are slow: first kill only after about 600 ticks.
- **Formation at spawn only:** relevant in principle (blobs spread into bands during the walk); not a factor for a blob-versus-blob focus test, but the blob shape at contact is not controlled.
- **Noise:** the 3 x rule now exists (section 4). Its remaining weakness: only the cell, not the variants, controls its own noise; 60 fights for nearest at enemy 14 but 20 for most damaged in the reach cell, because the break-even moved.
- **New:** the policy is global, not per side (section 1).

## 7. What could not be expressed

- S1, S3, S4, S5 have no skilled play (A145). Not run.
- Asymmetric focus (one side focusing, the other not), and focus on a chosen target (attack-target orders). No play issues them.
- Target re-evaluation: units keep a living target in range, so "switch to the weakest now" does not exist in the engine; "most damaged" is only an acquisition rule.
- S2 skilled and counter are the unconfirmed drafts; S2 has no effect on target choice in this batch (its break-evens equal the identical cell).
- Damage focus on units of different type or HP (all Vanguards).

## 8. Instrument questions

1. Is the global policy parameter acceptable for a "focus fire" batch, or does Phase D need a per-side policy (engine change, harness chat)?
2. Does focus fire mean re-picking targets only after a kill? If the skill is meant to switch mid-engagement, the engine as built cannot show it.
3. Mirror break-even 15 / 16 comes from the 0.05 margin; the pair spread is as wide as +-0.2 per seed. Is a one-unit step meaningful here? Only the reach cell moves.
4. The 20-unit mirrors take 3000 ticks and first kill about 600 ticks after contact; is that intended pace after A188? Not diagnosed.
