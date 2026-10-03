# 2026-10-03: Phase D, formation batch (material, nothing decided)

**Pass marks provisional (A174).** The README draft marks and the 0.05 win margin are labelled drafts; the three statistic definitions are labelled unconfirmed. No threshold is chosen here.

Build: worktree PD-formation, branch `push/pd-formation` off origin/main 90c3f731 (settle landing in), C library built with `make OPT=-O2`. Command: `python -m scripts.skilllab batch formation --out docs/northstar/research/layer_dynamics/runs/2026-10-03_formation/`. Runtime 18 min 8 s, single core, exit 0. Files in `2026-10-03_formation/`: `formation_run.md` (the batch's own page), `formation.csv`, `formation_page.html`.

Scene: open map, no terrain, side 0 plays line, blob, 120-degree concave or column counter against a naive blob (the counter against a line). Sizes 8, 16, 32; enemy from half to one and a half times the size; 10 seeds in both spawn orders = 20 fights per cell. Units: Vanguard (range 300 wu, sensor 700, speed 80) and Raider (range 200, sensor 800, speed 150).

## 1. What each play does at contact (looked at before the numbers)

One fight each, 16 against 16, seed 0, from the trace. "In range" = a unit has an enemy within its attack range by straight distance. Width = sideways spread, depth = front-to-back spread, wu.

| play (Vanguard) | start | first contact (tick) | in range at contact | tick 100 | tick 250 |
|---|---|---|---|---|---|
| line | row 452 wide, 13 deep | 50; side 0 5/16 in range, side 1 2/16; the row has already bowed to 377 x 88 | 5 of 16 | all 16 and 16 in range; closest pair 188 | 331 x 71 vs 339 x 74, closest 188 |
| blob | clump 226 x 187 | 50; 1 and 1 | 1 of 16 | 13 and 16 in range; closest 162 | 327 x 40 vs 336 x 74: a band, not a clump |
| concave | arc 341 wide, 106 deep | 55; 2 and 2 | 2 of 16 | 16 and 16 in range; closest 168 | 357 x 57 vs 437 x 52 |
| counter | column 78 wide, 151 deep, starting at the flank of the enemy line (nearest unit to the far end, not the middle) | 50; 1 and 2 | 1 of 16 | 15 and 16 in range; closest 186 | 365 x 145 vs 366 x 180 |

Plain words. Contact is almost the same moment for all four (tick 50 to 55), and at that moment at most a third of one side can shoot, so nobody gets a first volley that matters. Within about 50 ticks every play has become a thick band roughly 330 to 440 wu wide, both sides in range of each other. The line keeps its width but loses its thinness; the concave arc is flattened by the time it arrives (it starts 106 deep, is 156 deep at contact, 57 at tick 250); the blob spreads into a band (the Phase B finding again); the counter's column does not hit a flank, it ends up a 365 x 145 body next to the enemy line. Raiders do the same, but meet at tick 40 and 45 and again stop about 181 to 190 wu apart.

Nothing stalls (stalled fights 0 in every cell). The suspicion is the instrument or engine, not the formations: **the closest pair stops at 162 to 190 wu for both Vanguard (range 300) and Raider (range 200)**, i.e. at the same distance for two different ranges, even though everyone is in range by distance. That is the Phase B finding 2 ("units stop about 185 wu apart where range is 300"), unresolved on main, and it means this batch measures formations that have all collapsed into the same band before the fight is decided. See `2026-10-03_phase_b_read_fixed_movement.md` section 1.

## 2. Break-evens, whole units

Each cell: side 0 (size N) beats an enemy of the first number and loses to the second (the lab's refined break-even, 20 fights per cell). Reading: "16 beat 16, lose to 17" means about 16.5. A pure mirror would be "beat N, lose to N+1".

| play | Vanguard 8 | Vanguard 16 | Vanguard 32 | Raider 8 | Raider 16 | Raider 32 |
|---|---|---|---|---|---|---|
| line | 8 / 9 | 16 / 17 | 32 / 33 | 8 / 9 | 16 / 17 | 33 / 34 |
| blob | 7 / 8 | 15 / 16 | 31 / 32 | 8 / 9 | 15 / 16 | 32 / 33 |
| concave (draft) | 8 / 9 | 16 / 17 | 32 / 33 | 8 / 9 | 15 / 16 | 30 / 31 |
| counter (draft) | 7 / 8 | 15 / 16 | 31 / 32 | 7 / 8 | 15 / 16 | 28 / 29 |

Per unit type, in words: for Vanguards every play is within one unit of an even fight at every size (line and concave about half a unit better than blob and counter, which is smaller than the lab's resolution of a whole unit). For Raiders it is the same at 8 and 16; at 32 the concave (30) and the counter (28) beat the naive blob with two and four units to spare, the only effect larger than one unit in the batch. Firing unit-seconds mirror this: the counter side 0 fires 812 against 929 for the enemy line at 16 Vanguards, yet still holds a break-even of 15 to 16, so firing advantage and strength lost are not telling the same story here (a note for the harness chat, not a finding).

## 3. Vanguard against Raider

From the batch (cell by cell, same size and play): line, blob 16, counter 16, line 8, counter 8 same; blob 8 Raider larger; line 32 and blob 32 Raider larger (one unit); concave 16, concave 32, counter 32 Raider smaller (1, 2 and 3 units: Raiders 15, 30, 28 against Vanguards 16, 32, 31). Raider fights are 2.5 to 3 times shorter (about 590 against 1610 ticks at 16). Whole-unit differences of 1 are inside the lab's resolution; the 32-unit concave and counter gaps are the only ones past that.

## 4. Stalled counts

0 in all 24 cells (480 fights). No stalemate and no cap.

## 5. What the instrument could not express

- Skills S1, S3, S4, S5 have no formation play.
- The concave curves around the middle of the enemy's front (the draft's default focus), not the enemy's first anchor or a tracked arrival point.
- Formation is set at spawn only; there is no way to hold it through the walk (units are ordered attack-move and re-form as the movement pleases), so "line" and "concave" mean "starting layout", not "formation at contact".
- The counter's flank approach is a single goal point; contact is as late and as sparse as the blob's.
- Nothing about layers, terrain, focus fire (the next batch) or mixed unit types.

## 6. Instrument questions

1. The 162 to 190 wu stand-off at range 300 and 200. If it is a targeting or approach limit, every formation result here is measured after the shapes have merged. Ask: does a fix move these break-evens?
2. A 20-fight break-even with one-unit steps has no stated noise; most differences here are one unit. A noise estimate (repeat the same cell with other seeds) would say which are real.
3. Counter side fires 12 percent less than its enemy yet breaks even about equal: check which of the two statistics is off trend.
4. Raider counter at 32 (28) is the biggest effect; one seed-0 picture does not explain it. Worth a traced look before anything is concluded.
