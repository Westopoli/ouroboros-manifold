# 2026-10-03: Phase D, formation batch v2 (material, nothing decided)

**Pass marks provisional (A174).** The README draft marks and the 0.05 win margin are labelled drafts; the three statistic definitions are labelled unconfirmed. No threshold is chosen here.

## Tree

Worktree PD-formation2, branch `push/pd-formation2`. At start: origin/main 0b1ed3f4, origin/push/pl-land 1361db85 (A188 leash, not yet on main), origin/push/sl-land-5 b2ad5482. Merged pl-land, then sl-land-5; the only conflict was the ledger's appended rows (kept both). Merged tree HEAD (code) 6bb0e34a, C library built with `make OPT=-O2`. Command: `python -m scripts.skilllab batch formation --out docs/northstar/research/layer_dynamics/runs/2026-10-03_formation_v2/`. Runtime 28 min 12 s, single core, exit 0 (the first run took 18 min; the refinement runs 3 x the fights near each break-even). Files in `2026-10-03_formation_v2/`: `formation_run.md`, `formation.csv`, `formation_page.html`. Scene as the first page (sizes 8, 16, 32; Vanguard and Raider; 10 seeds in both spawn orders).

## Instrument defects from A187: which remain

1. Stand-off: fixed by A188 (pl-land merged). Measured below.
2. Formation held to contact: the harness does issue each side's play as an attack-move to the group's goal with slots (`fight._issue_orders`, chunks of at most 450 wu so the engine keeps the slots, R-095-03), and the concave's focus lands on the goal (c233caf4). It was NOT measured to hold the shape; see section 1: the shapes still change before contact. Treat as implemented but not confirmed effective.
3. Noise: implemented. Cells within 2 enemy units of a break-even run 3 x the fights; the page prints "pair spread", the lowest and highest per-seed mean margin of the side-swapped pairs. It is a spread of results, not a standard error, and no threshold is attached.

## 1. What each play does at contact (looked at before the numbers)

16 against 16, seed 0, from the trace (my own script reading `Setup.trace`, not part of the harness). Shapes are width x depth in wu (side 0 | side 1). "In range" = units with an enemy within attack range by straight distance, side 0, side 1.

Vanguard (range 300):

| play | tick 0 | 10 ticks before contact | at first contact | 10 ticks after | ~100 ticks after |
|---|---|---|---|---|---|
| line (contact 50) | 452 x 12 \| 222 x 200 | 380 x 39 \| 296 x 218 | 377 x 87 \| 308 x 224; in range 5, 2; closest 294 | 359 x 93 \| 311 x 184; 11, 4; closest 294 | 356 x 65 \| 363 x 55; 12, 11; closest 291 |
| blob (50) | 226 x 187 \| 222 x 200 | 263 x 217 \| 272 x 240 | 247 x 218 \| 255 x 247; 1, 1; closest 298 | 231 x 201 \| 255 x 209; 2, 3; 297 | 290 x 69 \| 299 x 66; 7, 9; 295 |
| concave (55) | 340 x 105 \| 222 x 200 | 319 x 168 \| 321 x 230 | 304 x 156 \| 328 x 217; 2, 2; closest 292 | 291 x 117 \| 324 x 177; 5, 5; 292 | 330 x 59 \| 408 x 52; 10, 12; 291 |
| counter (50) | 77 x 151 \| 454 x 19 | 243 x 216 \| 443 x 115 | 232 x 255 \| 441 x 119; 1, 2; closest 296 | 238 x 229 \| 430 x 108; 3, 6; 296 | 295 x 112 \| 345 x 157; 8, 12; 296 |

Raider (range 200): same pattern, contact at tick 40 to 45; closest pair at contact 190 to 194, then 180 to 185 (line 193 then 185; blob 190; concave 191 then 185; counter 194 then 181).

Plain words:
- **Stand-off is gone.** The closest pair now stops at 291 to 298 wu at range 300 and 180 to 194 at range 200 (first run: 162 to 190 for both). That is about range minus the closing step to a few wu inside it, as expected (Raider about 10 to 20 wu inside its range).
- **The shape is not held.** Everything is a thick body by contact. The line is 452 wide at spawn, 380 ten ticks before contact and 377 x 87 at contact (thin to 87 deep); the concave goes from 340 x 105 to 304 x 156 and has flattened to 59 deep within 100 ticks after; the blob spreads to about 250 x 220; the counter's column (77 x 151) is a 232 x 255 mass by contact and still is not at the enemy flank (the enemy line 441 wide stays 119 deep, the two bodies meet head-on in the middle). The slot offsets keep units from piling at one point but do not keep the drawn shape while walking: the units are different speeds-to-slot and re-form around their own movement.
- **Contact is sparse:** at the first tick anyone can shoot, 1 to 5 of 16 can, the same as before. No play gets a first volley that matters. At about 50 ticks later 7 to 12 of 16 can shoot. That is the same picture as the first run, now without the 190 wu stand-off.

So the answer to the question "do these plays differ at contact": they differ at spawn and they hardly differ at contact. Break-evens below should be read with that in mind.

## 2. Break-evens, whole units

Cell: "beats / loses to", the harness's wording (side 0 of size N beats an enemy of the first number and loses to the second). Higher means a stronger side 0. A pure mirror is about N-1 / N or N / N+1 (the 20-fight cell and the 0.05 margin put it there).

| play | Vanguard 8 | Vanguard 16 | Vanguard 32 | Raider 8 | Raider 16 | Raider 32 |
|---|---|---|---|---|---|---|
| line, new | 8 / 9 | 15 / 16 | 34 / 35 | 8 / 9 | 16 / 17 | 33 / 34 |
| line, first run | 8 / 9 | 16 / 17 | 32 / 33 | 8 / 9 | 16 / 17 | 33 / 34 |
| blob, new | 7 / 8 | 15 / 16 | 30 / 31 | 7 / 8 | 15 / 16 | 31 / 32 |
| blob, first run | 7 / 8 | 15 / 16 | 31 / 32 | 8 / 9 | 15 / 16 | 32 / 33 |
| concave (draft), new | 8 / 9 | 15 / 16 | 30 / 31 | 7 / 8 | 15 / 16 | 30 / 31 |
| concave, first run | 8 / 9 | 16 / 17 | 32 / 33 | 8 / 9 | 15 / 16 | 30 / 31 |
| counter (draft), new | 7 / 8 | 15 / 16 | 28 / 29 | 7 / 8 | 15 / 16 | 29 / 30 |
| counter, first run | 7 / 8 | 15 / 16 | 31 / 32 | 7 / 8 | 15 / 16 | 28 / 29 |

Pair spread (lowest to highest per-seed mean margin of the side-swapped pairs) at the edge cells, new run: roughly -0.3 to +0.4 in nearly every cell (examples: line@16 0.09 to 0.40, blob@16 -0.21 to 0.40, counter@32 -0.14 to 0.36, concave@32:Raider -0.27 to 0.32). The win margin mark is 0.05. So a single seed pair swings by several times the margin that decides a win, and one-unit differences between plays are inside that noise.

What changed against the first run, in units (higher = stronger): the Vanguard line at 32 is two units stronger (34 against 32); the Vanguard blob at 32 is one weaker (30 against 31) and the concave two weaker (30 against 32); the Vanguard counter at 32 is three weaker (28 against 31); the Raider counter at 32 is one stronger (29 against 28); the Raider blob and concave at 8 are one weaker. All other cells within a unit of the first run. The largest spread across plays is the Vanguard 32 row: line 34, blob 30, concave 30, counter 28, a six-unit range, against a pair spread of about -0.3 to +0.4; it is a suggestion that the counter does worse and the line does better against a blob at 32, not a result. Direction is the opposite of the draft's intent for the counter.

Firing unit-seconds (mean, side 0 against side 1): the counter fires less than its enemy in every size (Vanguard 16: 892 against 991, a 10 percent deficit; 32: 1664 against 2013, 17 percent; Raider 32: 473 against 537, 12 percent) and still breaks even at or below an even fight. A187 noted this for C2; still unexplained here.

## 3. Vanguard against Raider

Cell by cell (new): Raider larger at line@16 (16 against 15), blob@32 (31 against 30) and counter@32 (29 against 28); Raider smaller at concave@8 (7 against 8) and line@32 (33 against 34); same in the other seven. Every gap is one unit. Raider fights are about 3.4 times shorter (about 660 against 2250 ticks at 16 line).

## 4. Stalled counts

4 stalled fights in 480: Vanguard counter@8 1, blob@32 2, concave@32 1 (first run: 0). New with the leash change; not traced.

## 5. What the instrument could not express

- Skills S1, S3, S4, S5 have no formation play.
- The concave curves around the goal (the first anchor of the enemy side, c233caf4); not an arrival point tracked in play.
- The shapes are not kept to contact (section 1), so "line", "concave" and "counter" are starting layouts that merge into a thick body within about 50 ticks.
- The counter does not reach the flank (the two bodies meet head-on).
- Layers, terrain, focus fire (next batch) and mixed unit types.

## 6. Instrument questions

1. Why is the shape not held? Slots are issued, but the units' positions at contact show the engine re-forms around movement. Is a group-slot order reproducible by the engine for a 450 wu wide line, and does the harness chunk (it splits wider than 450 wu into several groups) change the shape? A second trace with one chunk (n small) would tell.
2. The pair spread is wide (per-seed margins -0.3 to +0.4). Can the number of seeds be raised, or is the harness' per-seed variance coming from the spawn jitter alone?
3. Line@32 moved two units against the first run with no formation change; the batch is not stable across the leash change, so none of the differences between plays is separately established yet.
4. Counter fires less and still breaks even (A187 C2 check): open.
5. The new stalled fights (4) have not been traced.
