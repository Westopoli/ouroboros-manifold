# 2026-10-02: Phase B first read with Westley (material, nothing decided)

Instrument: `scripts/skilllab/` (unchanged), the production C library built from `csrc/`, branch `push/pp-phaseb` at `404d6ab5` (the Phase A landing cut: `OM_TP_PURSUE_BY_STEERING`, `OM_TP_ROUTE_AROUND_TERRAIN`, `OM_TP_TARGET_BY_SIGHT`, `OM_TP_ROUTE_ACROSS_LAYERS` all default 1; `OM_TP_LEASH_BEFORE_DAMAGE` defaults 0). Linux x86-64. No threshold is chosen anywhere on this page; where a word like "line" or "blob" labels a number it says which rule it used, and the rule is only a label.

Unit used throughout: Vanguard (500 hp, 7.5 damage every 1.2 s, range 300 wu, sensor 700 wu, speed 80 wu/s) unless a section says otherwise.

How many fights: every "cell" of a controls scan is **20 fights** (10 seeds, each fought in both spawn orders). Section 1's table is **10 fights** per row (5 seeds, both spawn orders); its pictures are one fight (seed 0). Section 4's scans are 20 fights per cell; its tick tables are one fight each (seed 0), so they show what happens, not how often.

Files beside this page, in `docs/northstar/research/layer_dynamics/runs/2026-10-02_phase_b/`: `mirror_positions.md`, `controls.csv`, `controls_page.html`, `controls_leash0.csv`, `controls_leash1.csv`, `leash_table.md`, `choke_scan.md`/`.csv`, `choke_scan_raider.md`/`.csv`, `choke_ticks.md`.

## 0. First: do the harness tests still match the Mac's recorded hashes?

`pytest -q tests/skilllab` on this build: **1227 passed, 7 failed**. All 7 are the golden-hash comparisons: `test_cross_machine.py::test_control_hash_matches_golden[mirror, numbers, planted]` and `test_trace_real.py::test_control_rows_equal_golden_with_trace_off_and_on[mirror-16-16, numbers-16-8, each with trace off and on]`. So **all three recorded cells moved** (mirror 16 v 16, numbers 16 v 8, planted = the two 17-cell scans). Nothing else moved. `golden_hashes.json` is untouched here (the harness chat's).

Is that the movement change or the machine? Same three hashes recomputed with the four switches above set to 0: **all three equal the Mac's**. So Linux and the Mac produce byte-identical rows on the old behaviour, and the moves come from Phase A alone. (Not a proof for every cell; it is the three that exist.)

## 1. Does a formation survive the walk?

**Context.** Both sides start about 683 wu apart, each unit told to attack-move at the other side. The old engine ended with two flat rows whatever the start (LEAVE_OFF). Here: the same two plays (a 16-unit *line*, 30 wu between units, and a 16-unit *blob*), equal sides, flat ground, no terrain, fought with the new movement and again with both movement switches 0 (the old movement), positions printed from the trace.

`o` = side 0, `x` = side 1. Up-down is the sideways spread (y), left-right is toward the enemy (x).

**The line, new movement, at tick 150 (the walk is over; first shots were at tick 50):**
```
walk done (tick 150), window x -300..300 wu (one character = 8 wu across, 40 wu down):
```
    |                                               x                        |
    |                         o                      x                       |
    |                        o                      x                        |
    |                        o                       x                       |
    |                   o    oo                     xx                       |
    |                        o                      x                        |
    |                                               x   x                    |
    |                        o                      x                        |
    |                        o                     x     x                   |
    |                    o    o                      x                       |
    |                        o                       x                       |
    |                        o                       x                       |
    |                        o                      x                        |
```
```
Words: **the line stayed a line.** Each side is still one wide column of units, with a few that stepped out a little. Width stayed about 440 wu all the way (table below); depth went from 17 wu to about 30. Old movement also kept a line (depth 8).

**The blob, new movement, tick 150:**
```
walk done (tick 150), window x -300..300 wu (one character = 8 wu across, 40 wu down):
```
    |                                                                        |
    |                                                                        |
    |                                                  x                     |
    |                       o                        x                       |
    |                         o                      x     x                 |
    |                     o  oo                      x   x                   |
    |                   oo o  o                     x   xx                   |
    |              o     o  o                      x  xx                     |
    |                        o                      x                        |
    |                 o      o                      x                        |
    |                                               x                        |
    |                                                                        |
    |                                                                        |
```
```
**The blob, old movement, tick 150:**
```
walk done (tick 150), window x -300..300 wu (one character = 8 wu across, 40 wu down):
```
    |                                                                        |
    |                                                                        |
    |                                                                        |
    |                                                                        |
    |                  o                                   x                 |
    |                  o                                   x                 |
    |                  o                                   x                 |
    |                  o                                  xx                 |
    |                  o                                   x                 |
    |                                                                        |
    |                                                                        |
    |                                                                        |
    |                                                                        |
```
```
Words: with the old movement the 16-unit round clump was squeezed into a single thin row about 160 wu long and 6 wu deep. With the new movement the clump has spread **sideways into a thick band** (about 255 wu wide, 80 wu deep at tick 150, and still thinning to about 290 wide, 60 deep at tick 300) but it is not a single row. So: **a blob does not survive as a round blob; it flattens into a band, much less than before.**

**Per-side numbers, mean of 10 fights.** Width = sideways spread (y), depth = front-to-back spread (x). "In words" uses my label rule, which is only a label: width over depth 4 or more "a wide thin row", 2 to 4 "a thick band", under 2 "a clump".

| play | engine | moment | units alive (side 0, side 1) | width, wu (side 0 / 1) | depth, wu (side 0 / 1) | width over depth | in words |
|---|---|---|---|---|---|---|---|
| line | new | start | 16.0, 16.0 | 446 / 454 | 17 / 17 | 25.7 | a wide thin row |
| line | new | first contact | 16.0, 16.0 | 445 / 438 | 36 / 33 | 12.9 | a wide thin row |
| line | new | tick 150 | 16.0, 16.0 | 446 / 435 | 33 / 27 | 14.9 | a wide thin row |
| line | new | tick 300 | 16.0, 16.0 | 446 / 435 | 32 / 24 | 15.8 | a wide thin row |
| line | old | start | 16.0, 16.0 | 446 / 454 | 17 / 17 | 25.7 | a wide thin row |
| line | old | first contact | 16.0, 16.0 | 432 / 430 | 17 / 15 | 26.4 | a wide thin row |
| line | old | tick 150 | 16.0, 16.0 | 431 / 429 | 8 / 8 | 57.0 | a wide thin row |
| line | old | tick 300 | 16.0, 16.0 | 431 / 429 | 8 / 8 | 57.0 | a wide thin row |
| blob | new | start | 16.0, 16.0 | 228 / 228 | 191 / 191 | 1.2 | a clump |
| blob | new | first contact | 16.0, 16.0 | 224 / 224 | 224 / 219 | 1.0 | a clump |
| blob | new | tick 150 | 16.0, 16.0 | 251 / 263 | 89 / 73 | 3.2 | a thick band |
| blob | new | tick 300 | 15.7, 15.9 | 290 / 289 | 59 / 60 | 4.9 | a wide thin row |
| blob | old | start | 16.0, 16.0 | 228 / 228 | 191 / 191 | 1.2 | a clump |
| blob | old | first contact | 16.0, 16.0 | 179 / 174 | 202 / 207 | 0.9 | a clump |
| blob | old | tick 150 | 16.0, 16.0 | 161 / 156 | 6 / 6 | 25.8 | a wide thin row |
| blob | old | tick 300 | 15.9, 15.7 | 161 / 156 | 6 / 6 | 27.3 | a wide thin row |


**Questions about the instrument, not explained away.**
- *Units stop 185 wu apart, but the range is 300.* In the new movement the closest enemy pair at tick 100 to 200 is 185 wu apart (line play); in the old movement it was 296. Everything at range 300 should already be shooting at 300. Hypothesis, not tested: units that already have a target keep walking until their next targeting turn (only 8 of the 32 units had a target at ticks 30 to 70), so they overshoot the range by up to about a second and a half. If true, it is the targeting turns, not the harness. Not confirmed.
- *First-contact tick* (first tick any unit can fire) is 50 to 60 in both movements (seed 0), so the plays start the sides at about the right place for first fire; the question whether the plays' contact placement should change is not answered by this: the line keeps its shape over this 380 wu walk, the blob does not. That is for the decision, not for me.

## 2. The controls (`python3 -m scripts.skilllab controls`)

**Run:** `python3 -m scripts.skilllab controls --out <dir>`, 680 fights (2 plays x 17 enemy sizes x 20 fights), 57 s. Rows: `controls.csv` (committed; identical to `controls_leash0.csv` margin for margin and tick for tick, so the leash-0 run below IS this run). Page: `controls_page.html` (194 KB, committed, under the 200 KB limit).

"identical" = both sides the same unit. "damage" = our 16 units deal 1.2 times the damage.

| What the control asks | Result | Reading |
|---|---|---|
| Identical 16 against 16 (mirror) | mean margin +0.005 | even, as it should be |
| Identical 16 against N | beats 15, loses to 16 | one unit's difference decides it; the Mac's measurement on the old engine was the same: "16 beat 15" |
| Damage x1.2, 16 against N | beats 17, loses to 18 | the 20 percent damage is worth 2 soldiers |
| Reach x1.2 (not in the CLI; one extra scan, same size, 20 fights per cell) | beats 15, loses to 16; margin at 16 v 16 is +0.027 | the old engine had this side **worse** than identical (beat 14, margin about -0.34 at 16 v 16); now it is the same as identical, not better |

Break-evens are the same as the Mac's old-engine break-evens for the two CLI controls (15/16 and 17/18), though the whole run's rows differ (the hash moved).

**Instrument note: the page's firing chart** has its x axis labels piled on top of each other (a solid grey bar under the chart; seen by screenshot). Harness chat's to fix; the data table beneath it is fine.

## 3. The leash both ways

**What it is.** An attack-moving unit leaves a spot (its anchor) to chase. At **0** (the default) it may shoot a target that is more than 200 wu from its anchor and drops it next tick. At **1** (the Python's order) it drops that target first and does not shoot it. Plain test: at 1 a unit stops shooting an enemy that has led it too far from where it began.

Margin per cell, 20 fights per cell each side of the table. "Won" is the harness's rule: mean margin above 0.05 **and** all 20 fights decided (no stalemate, no 6000-tick cap).

#### identical: 16 units (side 0) against N enemy units; 20 fights per cell (10 seeds, both spawn orders)

| enemy N | mean margin, leash 0 | won (leash 0) | stalemate/cap fights (0) | mean margin, leash 1 | won (leash 1) | stalemate/cap fights (1) | mean ticks (0 / 1) |
|---|---|---|---|---|---|---|---|
| 8 | +0.822 | yes | 0 | +0.782 | yes | 0 | 890 / 1134 |
| 9 | +0.776 | yes | 0 | +0.734 | yes | 0 | 1012 / 1300 |
| 10 | +0.734 | yes | 0 | +0.638 | yes | 0 | 1124 / 1561 |
| 11 | +0.678 | yes | 0 | +0.580 | yes | 0 | 1257 / 1730 |
| 12 | +0.606 | yes | 0 | +0.518 | yes | 0 | 1439 / 1919 |
| 13 | +0.541 | yes | 0 | +0.445 | yes | 0 | 1644 / 2226 |
| 14 | +0.447 | yes | 0 | +0.331 | yes | 0 | 1898 / 2627 |
| 15 | +0.304 | yes | 0 | +0.227 | no | 3 | 2381 / 3243 |
| 16 | +0.005 | no | 0 | -0.003 | no | 3 | 3425 / 3309 |
| 17 | -0.271 | no | 0 | -0.171 | no | 6 | 2536 / 3371 |
| 18 | -0.390 | no | 0 | -0.333 | no | 0 | 2015 / 2554 |
| 19 | -0.478 | no | 0 | -0.420 | no | 0 | 1785 / 2329 |
| 20 | -0.538 | no | 0 | -0.487 | no | 0 | 1644 / 2106 |
| 21 | -0.579 | no | 0 | -0.525 | no | 0 | 1541 / 2005 |
| 22 | -0.630 | no | 0 | -0.567 | no | 0 | 1421 / 1922 |
| 23 | -0.666 | no | 0 | -0.601 | no | 0 | 1341 / 1856 |
| 24 | -0.703 | no | 0 | -0.615 | no | 0 | 1260 / 1792 |

- leash 0: beats 15, loses to 16
- leash 1: beats 14, loses to 15

#### damage: 16 units (side 0) against N enemy units; 20 fights per cell (10 seeds, both spawn orders)

| enemy N | mean margin, leash 0 | won (leash 0) | stalemate/cap fights (0) | mean margin, leash 1 | won (leash 1) | stalemate/cap fights (1) | mean ticks (0 / 1) |
|---|---|---|---|---|---|---|---|
| 8 | +0.852 | yes | 0 | +0.814 | yes | 0 | 750 / 970 |
| 9 | +0.814 | yes | 0 | +0.777 | yes | 0 | 848 / 1087 |
| 10 | +0.783 | yes | 0 | +0.695 | yes | 0 | 935 / 1331 |
| 11 | +0.736 | yes | 0 | +0.654 | yes | 0 | 1034 / 1451 |
| 12 | +0.682 | yes | 0 | +0.605 | yes | 0 | 1154 / 1557 |
| 13 | +0.634 | yes | 0 | +0.549 | yes | 0 | 1303 / 1759 |
| 14 | +0.564 | yes | 0 | +0.467 | yes | 0 | 1456 / 1959 |
| 15 | +0.478 | yes | 0 | +0.418 | yes | 0 | 1666 / 2157 |
| 16 | +0.369 | yes | 0 | +0.292 | yes | 0 | 1942 / 2525 |
| 17 | +0.244 | yes | 0 | +0.148 | no | 6 | 2454 / 3390 |
| 18 | -0.094 | no | 0 | -0.040 | no | 1 | 2851 / 3099 |
| 19 | -0.305 | no | 0 | -0.265 | no | 1 | 2128 / 2688 |
| 20 | -0.404 | no | 0 | -0.371 | no | 0 | 1885 / 2277 |
| 21 | -0.473 | no | 0 | -0.427 | no | 0 | 1667 / 2129 |
| 22 | -0.537 | no | 0 | -0.464 | no | 0 | 1523 / 2048 |
| 23 | -0.582 | no | 0 | -0.517 | no | 0 | 1422 / 1920 |
| 24 | -0.632 | no | 0 | -0.532 | no | 0 | 1306 / 1848 |

- leash 0: beats 17, loses to 18
- leash 1: beats 16, loses to 17



**In plain words.**
- With the leash on, **margins move toward zero**: where our side wins it wins by less (+0.734 to +0.638 at 16 v 10; 0.04 to 0.12 less across the winning cells) and where it loses it loses by less (-0.390 to -0.333 at 16 v 18; 0.04 to 0.10 less across the losing cells). Fights are even-er. At exactly 16 v 16 nothing changes. Fights last **a quarter to two-fifths longer** (890 against 1134 ticks at 16 v 8; 1260 against 1792 at 16 v 24).
- The break-evens each move down by one soldier (15 to 14, 17 to 16). **Part of that is the "won" rule, not strength:** at 15 enemies the leash-on mean margin is +0.227 (our side clearly ahead) but 3 of the 20 fights ended in stalemate, so the cell counts as not won. Same at 17 for the damage side (+0.148, 6 stalemates).
- **Instrument question I looked into once:** a leash-on stalemate (identical, 16 v 15, seed 3, other spawn order): the last two units, one per side, stand 210 wu apart, range is 300, both with no target, for 400 ticks until the harness calls it. A target dropped by the leash and not picked up again. I have not traced why. It is exactly the sort of number that is about the engine's rule, not a surprise about soldiers, and the choice of which side of the switch to delete is Westley's.

## 4. A choke defence, tick by tick (the guard-stance question, Q-096-01)

**Scene (made with the harness's terrain, which calls `om_map_block_rect`).** Canvas 3000 x 1600 wu. One wall, 100 wu thick, running north-south across the middle, with a **200 wu gap** in it. Defenders (8 Vanguards in a row across the gap, 30 wu apart) stand 100 wu behind the gap on the east. Attackers (a blob, N units) start 700 wu west of the wall and attack-move toward the defenders, so they have to come through the gap. Defender orders compared: **attack-move** (as the game gives today: chase what you see) and **idle** (the register's option (b): placed and never steps forward; this is what the lab can express today; the guard order itself (a) does not exist in the engine).

```
   west                      wall                  east
                          ##########
   x x x x                ##########
   x x x                  ##########                 o o   <- defenders, 100 wu behind the gap
   x x x x  --->     (gap, 200 wu, open)             o o
                          ##########                 o o
                          ##########
```

**Does the wall help the defender? Break-evens, 8 defenders against N attackers, 20 fights per cell, four set-ups** (open ground = same placements, no wall):

| attackers | open ground, defenders attack-move (margin, won, undecided/20) | open ground, defenders idle (margin, won, undecided/20) | choke, defenders attack-move (margin, won, undecided/20) | choke, defenders idle (margin, won, undecided/20) |
|---|---|---|---|---|
| 6 | +0.606, yes, 0 | +0.577, yes, 0 | +0.608, yes, 0 | +0.593, no, 4 |
| 7 | +0.447, yes, 0 | +0.392, yes, 0 | +0.444, yes, 0 | +0.429, no, 7 |
| 8 | +0.156, yes, 0 | +0.089, yes, 0 | +0.166, yes, 0 | +0.175, no, 3 |
| 9 | -0.275, no, 0 | -0.321, no, 0 | -0.279, no, 0 | -0.164, no, 6 |
| 10 | -0.479, no, 0 | -0.491, no, 0 | -0.471, no, 0 | -0.404, no, 1 |
| 11 | -0.582, no, 0 | -0.583, no, 0 | -0.584, no, 0 | -0.526, no, 1 |
| 12 | -0.656, no, 0 | -0.648, no, 0 | -0.656, no, 0 | -0.585, no, 0 |
| 13 | -0.710, no, 0 | -0.708, no, 0 | -0.705, no, 0 | -0.676, no, 0 |
| 14 | -0.752, no, 0 | -0.751, no, 0 | -0.753, no, 0 | -0.721, no, 0 |
| 15 | -0.784, no, 0 | -0.784, no, 0 | -0.785, no, 0 | -0.753, no, 0 |
| 16 | -0.810, no, 0 | -0.815, no, 0 | -0.815, no, 0 | -0.785, no, 0 |

- open ground, defenders attack-move: defenders (8) beat 8 attackers, lose to 9
- open ground, defenders idle: defenders (8) beat 8 attackers, lose to 9
- choke, defenders attack-move: defenders (8) beat 8 attackers, lose to 9
- choke, defenders idle: defenders (8) beat None attackers, lose to None


Same, with **Raiders** (range 200 instead of 300) on both sides, because at range 300 the wall hardly matters:

| attackers | open ground, defenders attack-move (margin, won, undecided/20) | open ground, defenders idle (margin, won, undecided/20) | choke, defenders attack-move (margin, won, undecided/20) | choke, defenders idle (margin, won, undecided/20) |
|---|---|---|---|---|
| 6 | +0.603, yes, 0 | +0.465, yes, 0 | +0.603, yes, 0 | +0.521, no, 2 |
| 7 | +0.470, yes, 0 | +0.252, yes, 0 | +0.476, yes, 0 | +0.353, no, 10 |
| 8 | +0.178, yes, 0 | -0.062, no, 0 | +0.167, yes, 0 | +0.094, no, 5 |
| 9 | -0.220, no, 0 | -0.290, no, 0 | -0.229, no, 0 | -0.139, no, 2 |
| 10 | -0.447, no, 0 | -0.481, no, 0 | -0.451, no, 0 | -0.327, no, 0 |
| 11 | -0.556, no, 0 | -0.571, no, 0 | -0.560, no, 0 | -0.434, no, 1 |
| 12 | -0.618, no, 0 | -0.610, no, 0 | -0.630, no, 0 | -0.520, no, 0 |
| 13 | -0.667, no, 0 | -0.674, no, 0 | -0.677, no, 0 | -0.575, no, 0 |
| 14 | -0.721, no, 0 | -0.714, no, 0 | -0.716, no, 0 | -0.630, no, 0 |
| 15 | -0.747, no, 0 | -0.745, no, 0 | -0.753, no, 0 | -0.669, no, 0 |
| 16 | -0.781, no, 0 | -0.779, no, 0 | -0.781, no, 0 | -0.688, no, 0 |

- open ground, defenders attack-move: defenders (8) beat 8 attackers, lose to 9
- open ground, defenders idle: defenders (8) beat 7 attackers, lose to 8
- choke, defenders attack-move: defenders (8) beat 8 attackers, lose to 9
- choke, defenders idle: defenders (8) beat None attackers, lose to None


**Plain words.**
- **Vanguards, defenders chasing: the wall does not help.** Defenders beat 8 and lose to 9 in open ground and with the wall. Their margins at every N match to within 0.01.
- **Why, from the ticks (one fight, 8 defenders against 9, seed 0, in `choke_ticks.md`):** with attack-move the defenders **walk out through the gap**; at tick 77 all 8 are already on the attackers' side of the wall, so the fight is the open-ground fight. The wall was never held. This is exactly what Q-096-01 says (R-087-04 defeats the choke for attack-moving defenders), and now it is seen.
- With defenders **idle** the wall does act: the defenders hold, and the attackers get funnelled. Over ticks 145 to 225 all 8 defenders are firing while only 1 to 6 of the 9 attackers can (1 blocked by the wall, up to 7 waiting with no target). But by tick 285 7 of the 9 attackers are firing against 8 and the strengths are equal (0.92 against 0.91), and the fight ends close to the open-ground result. With the wall, idle defenders lose by less than the same idle defenders in open ground, 0.03 to 0.16 less margin lost (-0.164 against -0.321 at 9 attackers; -0.585 against -0.648 at 12). Against chasing defenders in open ground (-0.275 at 9) the gain is about 0.11 at 9 and smaller after. But...
- **...the idle-defender cells at 6 to 11 attackers are marked "not won"** because 1 to 7 of the 20 fights in each ended in a stalemate. That is the harness's rule, and it hides a real thing.
- **With Raiders** (range 200) the wall matters more for idle defenders: they lose by 0.08 to 0.15 less margin than the same idle defenders in open ground at every attacker count from 9 up (for example -0.139 against -0.290 at 9; -0.327 against -0.481 at 10). With attack-move defenders the wall changes nothing (within 0.012 of open ground at every N).
- So: **a choke helps a defender who stays behind it, by a modest margin (never enough, here, to move a break-even), more so the shorter the range; it does nothing for defenders who chase.** Whether to build a guard order (a) or to have no new order (b) is Westley's; what the lab shows is that (b) holds the wall and (a) is not measured.

**Instrument question, looked at once, not explained away:** in the stalemates (Raider, 8 idle defenders, 7 attackers, seed 3) the last attacker stands **at the corner of the wall** (x 1495, y 696) with its target 200 wu away exactly **in range but behind the wall's edge**, so it cannot fire; it stays there to the end of the fight rather than stepping into the gap for a clear shot. Both sides stay still until the harness calls it a stalemate. This is a unit with a target in range by distance whose shot is blocked, and it does not move: the engine's rule, or a gap in the rule (Q-088-01, visible but unreachable, is a related existing row, not the same case), not a result about soldiers. It is also what makes the "won" column for the idle cells read "no".

Tick table for the idle-defender fight, and the other two, in `choke_ticks.md` (columns: how many on each side are firing, blocked by the wall, walking, with no target yet, and each side's strength).

## 5. The one-page chart

The chart in LEAVE_OFF "Charts" is the controls page, `controls_page.html`, link: `docs/northstar/research/layer_dynamics/runs/2026-10-02_phase_b/controls_page.html` (open in a browser; viewed once by screenshot). What it has: a heading that states the finding in soldiers ("identical: 16 units beat 15", "damage: 16 units beat 17"); one dot per enemy size, coloured won or lost, with the break-even marked as a dashed line and labelled ("beats 15, loses to 16"); a table with a plain-words column ("16 units beat 8"); and a second chart of units able to fire through one 16 v 16 fight (labelled side 0 and side 1, the gap between them shaded).

What it does not do (all the harness chat's, nothing changed here):
- the y axis is margin, not soldiers; the heading and the table carry the soldiers;
- the labels "identical" and "damage" are harness words;
- the firing chart's x axis labels overlap (section 2);
- one page for the leash both ways was not made: `leash_table.md` carries it, and the leash-on page is 215 KB so it is not committed (re-make with the same run).

## What the harness could not express

- **A guard order** (Q-096-01 option (a)): not in the engine, so only (b) idle is measured.
- **Per-tick "who fires / who is blocked"** is not in the trace (the trace holds position, target, facing, alive); I used a thin wrapper around the library calls in a scratch script (`Engine.can_shoot` per unit per tick) and nothing under `scripts/skilllab`. If this is wanted again it belongs in the harness.
- **A per-fight tick table for a whole scan cell**: only single fights are tick-printed.
- **A reach control** in the CLI: it is not one of the two `controls` plays.
