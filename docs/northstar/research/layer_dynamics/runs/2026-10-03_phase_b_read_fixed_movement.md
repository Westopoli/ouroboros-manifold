# 2026-10-03: Phase B read again, on the fixed movement (material, nothing decided)

Build: worktree PhaseB2, branch `push/pp-phaseb2` = Phase A plus wave A5 (`OM_TP_PURSUE_BY_STEERING` default 1, every unit starts collision pairs with 10 passes). Instrument: `scripts/skilllab/` unchanged; the production C library from `csrc/`; Linux x86-64. Same five items as `2026-10-02_phase_b_read.md` (folder `2026-10-02_phase_b/`) plus the 20-unit formation printout (A161). No threshold is chosen here; where a word like "line" or "blob" labels a number it says which rule, and the rule is only a label.

Unit throughout: Vanguard (500 hp, 7.5 damage per 1.2 s, range 300 wu, sensor 700 wu, speed 80 wu/s). Every scan "cell" is **20 fights** (10 seeds, each in both spawn orders). Section 1's table is 10 fights per row (5 seeds, both orders); its pictures are one fight (seed 0). Tick tables in section 4 are one fight (seed 0): they show what happens, not how often.

Files in `2026-10-03_phase_b/`: `mirror_positions.md`, `controls.csv`, `controls_page.html`, `controls_leash0.csv`, `controls_leash1.csv`, `leash_table.md`, `choke_scan.md/.csv`, `choke_scan_raider.md/.csv`, `choke_ticks.md`, `s101_formation_printout.md`.

## The five findings and the milling picture, in one place

1. A line still keeps its shape (a wide row). A blob still flattens into a band (thick at tick 150, wide and thin at tick 300). Not changed by A5.
2. "Units stop about 185 wu apart where the range is 300": **still there** (186 wu). It is not the harness: at 268 wu, in range and in sight, the two front units have no target (see section 1).
3. Controls: same break-evens as before (identical 15/16, damage 17/18, reach 15/16). 7 golden hashes differ (listed in section 2); with the four switches at 0 all three recorded cells reproduce the Mac's hashes.
4. Leash on: margins move toward zero and fights run longer, as before; stalemates remain in some cells.
5. Choke: the wall does not help a defender who chases; helps one who stays; a unit blocked at the wall's corner **still does not step into the gap**.
6. Milling (S101, 20 units): units 1 and 4 never end their order; they pace at full speed in a small patch, 54 and 35 wu from their slots. Section 6.

## 1. Does a formation survive the walk?

**Context.** Two sides of 16, flat ground, 683 wu apart, each unit told to attack-move at the other side. A *line* has 30 wu between units; a *blob* is a round clump. Positions are printed from the trace. `o` is side 0, `x` side 1; left-right is the way they march (x), up-down is sideways (y). The full pictures at start, first contact and tick 150, for both plays, new and switches-0 ("old"), are in `mirror_positions.md`. Two of them here.

The line at tick 150 (walk over, first shots at tick 50; one character = 8 wu across, 40 wu down):
```
    |                        o                      x                        |
    |                         o                      x                       |
    |                        o                      x                        |
    |                        o                       x                       |
    |                      o  o                     x  x                     |
    |                        o                       x                       |
    |                    o                          x    x                   |
    |                         o                     x                        |
    |                     o  o                       x  x                    |
    |                         o                     x                        |
    |                    o   o                       x                       |
    |                        o                      x                        |
    |                        o                      x                        |
```

The blob at tick 150 (same scale):
```
    |                                                                        |
    |                                                                        |
    |                                                  x                     |
    |                       o                        x      x                |
    |                         o                      x     x                 |
    |                     o  oo                      x   x                   |
    |                   oo o  o                     x   x                    |
    |              o       o                       x   x                     |
    |                    o   o                      x                        |
    |                  o     o                      x                        |
    |                                               x                        |
    |                                                                        |
    |                                                                        |
```

Table, per side, mean of 10 fights. Width = sideways spread (y), depth = front-to-back spread (x). "In words" uses a label rule only: width over depth 4 or more is "a wide thin row", 2 to 4 "a thick band", under 2 "a clump".

| play | engine | moment | units alive (side 0, side 1) | width, wu (side 0 / 1) | depth, wu (side 0 / 1) | width over depth | in words |
|---|---|---|---|---|---|---|---|
| line | new | start | 16.0, 16.0 | 446 / 454 | 17 / 17 | 25.7 | a wide thin row |
| line | new | first contact | 16.0, 16.0 | 445 / 439 | 37 / 35 | 12.3 | a wide thin row |
| line | new | tick 150 | 16.0, 16.0 | 451 / 439 | 41 / 45 | 10.4 | a wide thin row |
| line | new | tick 300 | 16.0, 16.0 | 453 / 439 | 39 / 44 | 10.8 | a wide thin row |
| line | old | start | 16.0, 16.0 | 446 / 454 | 17 / 17 | 25.7 | a wide thin row |
| line | old | first contact | 16.0, 16.0 | 432 / 430 | 17 / 15 | 26.4 | a wide thin row |
| line | old | tick 150 | 16.0, 16.0 | 431 / 429 | 8 / 8 | 57.0 | a wide thin row |
| line | old | tick 300 | 16.0, 16.0 | 431 / 429 | 8 / 8 | 57.0 | a wide thin row |
| blob | new | start | 16.0, 16.0 | 228 / 228 | 191 / 191 | 1.2 | a clump |
| blob | new | first contact | 16.0, 16.0 | 224 / 224 | 224 / 219 | 1.0 | a clump |
| blob | new | tick 150 | 16.0, 16.0 | 248 / 264 | 87 / 80 | 3.1 | a thick band |
| blob | new | tick 300 | 15.6, 15.9 | 294 / 284 | 63 / 62 | 4.6 | a wide thin row |
| blob | old | start | 16.0, 16.0 | 228 / 228 | 191 / 191 | 1.2 | a clump |
| blob | old | first contact | 16.0, 16.0 | 179 / 174 | 202 / 207 | 0.9 | a clump |
| blob | old | tick 150 | 16.0, 16.0 | 161 / 156 | 6 / 6 | 25.8 | a wide thin row |
| blob | old | tick 300 | 15.9, 15.7 | 161 / 156 | 6 / 6 | 27.3 | a wide thin row |

**In words.** The line stays a line: width about 445 wu throughout, depth grows from 17 to about 40 wu (it was 33 on the previous build; the old switches give 8). The blob does not stay a blob: a round clump about 228 wide and 191 deep becomes a band about 250 wide and 85 deep at tick 150, and about 290 wide and 62 deep at tick 300. Compared with the previous build the numbers are nearly the same (blob tick 150: 251/263 wide, 89/73 deep then; 248/264, 87/80 now). So **"a blob flattens into a thick band" is not fixed by this build**; it is just as before. The picture a player sees: two ragged vertical columns facing each other, the blob's columns a bit thicker.

**"Units stop 185 wu apart where the range is 300": not fixed.** Closest enemy pair, line play, seed 0: 436 wu at tick 30, 282 at 50, 268 at 60, 208 at 70, then **186 from tick 78 on** (switches 0: 296). A second look at why, because the number is first a question about the instrument:
- At tick 50 the front pair (units 6 and 27, 282 wu apart, range 300) both fire. At ticks 55 to 65 the same pair, 268 to 236 wu apart, **have no target** and walk on (their `target` reads 0); at tick 70 and 75 they have a target again and fire from 208 and 188 wu. So a unit that has a target loses it for several ticks and the attack-move walk carries it forward.
- With `OM_TP_LEASH_BEFORE_DAMAGE` = 1 and the same fight, **nobody has a target before tick 60**, though the front pair is inside range from tick 50 (273 wu); they walk to 191 wu, then fire, and stop at 177 wu.
- Plain reading: the stopping distance is set by when a target is held, not by the range, and the leash rule (a target more than 200 wu from the unit's anchor is dropped) is the likely cause: the sides start 341 wu from the middle each, so units are more than 200 wu from their anchors by the time they are in range. Not proven; the switch result is consistent with it. Which side of the switch to keep is Westley's.

## 2. The controls (`python3 -m scripts.skilllab controls --out <dir>`)

680 fights (2 plays x 17 enemy sizes x 20 fights). Rows `controls.csv`, page `controls_page.html` (177 KB). Break-evens, from the page headings:

| What the control asks | Result | Reading |
|---|---|---|
| Identical 16 against N | beats 15, loses to 16; margin at 16 v 16 is -0.007 | one unit decides it; even on a mirror |
| Damage x1.2, 16 against N | beats 17, loses to 18 | 20 percent damage is worth about 2 soldiers |
| Reach x1.2 (not in the CLI; one extra scan, `plays.reach_play`) | beats 15, loses to 16; margin at 16 v 16 +0.026 | same as identical, not better |

Margins per cell (identical): 8 +0.823, 10 +0.734, 12 +0.604, 14 +0.434, 15 +0.321, 16 -0.007, 17 -0.288, 20 -0.545, 24 -0.697 (all cells in the csv). No cell is a stalemate. Same break-evens as the previous read.

**Goldens.** `pytest -q tests/skilllab`: 1227 passed, **7 failed**, all golden-hash comparisons, the harness chat regenerates them: `tests/skilllab/integration/test_cross_machine.py::test_control_hash_matches_golden[mirror|numbers|planted]` and `tests/skilllab/integration/test_trace_real.py::test_control_rows_equal_golden_with_trace_off_and_on[mirror-16-16-False|True]` and `[numbers-16-8-False|True]`. With the four switches at 0 the three recorded cells (mirror, numbers, planted) reproduce the Mac's hashes (checked), so the moves come from the movement change, not the machine.

**Instrument note.** The page's firing chart still has a solid grey bar under it where the x labels should be (seen by screenshot, headless Chrome). The data table beneath it is fine. Harness chat's to fix.

## 3. The leash both ways

**What it is.** An attack-moving unit leaves its anchor spot to chase. At **0** (default) it may shoot a target more than 200 wu from its anchor and drops it next tick. At **1** (the Python's order) it drops that target first and does not shoot it. Plain test: at 1 a unit stops shooting an enemy that has led it too far from where it began.

"Won" is the harness rule: mean margin above 0.05 and all 20 fights decided (no stalemate, no 6000-tick cap). Full tables, both plays, 20 fights per cell: `leash_table.md`. Identical 16 against N:

| N | margin leash 0 | margin leash 1 | stalemate fights (0 / 1) | mean ticks (0 / 1) |
|---|---|---|---|---|
| 8 | +0.823 | +0.760 | 0 / 0 | 893 / 1294 |
| 10 | +0.734 | +0.628 | 0 / 0 | 1128 / 1775 |
| 12 | +0.604 | +0.512 | 0 / 0 | 1434 / 2138 |
| 14 | +0.434 | +0.278 | 0 / 2 | 1932 / 3034 |
| 15 | +0.321 | +0.182 | 0 / 2 | 2332 / 3693 |
| 16 | -0.007 | +0.073 | 0 / 3 | 3246 / 3540 |
| 17 | -0.288 | -0.249 | 0 / 1 | 2476 / 3299 |
| 18 | -0.389 | -0.329 | 0 / 0 | 2009 / 2848 |
| 20 | -0.545 | -0.429 | 0 / 0 | 1631 / 2533 |
| 24 | -0.697 | -0.602 | 0 / 0 | 1260 / 2080 |

Damage x1.2, 16 against N: 8 +0.852 / +0.799, 16 +0.359 / +0.326, 17 +0.244 / +0.058 (6 stalemates at leash 1), 18 -0.079 / -0.040, 24 -0.627 / -0.514.

Break-evens: identical leash 0 beats 15, loses to 16; **leash 1 beats 13, loses to 14**. Damage: leash 0 beats 17, loses to 18; leash 1 beats 16, loses to 17.

**In plain words.** With the leash on, margins move toward zero (winners win by less by 0.05 to 0.16, losers lose by less by 0.04 to 0.12) and fights last 40 to 70 percent longer (893 against 1294 ticks at 16 v 8). At 16 v 16 the mean margin is +0.073 with the leash on: about even, but 3 of 20 fights stall. Part of the break-even moving down is the "won" rule, not strength: at 14 and 15 enemies the leash-on margins are +0.278 and +0.182 (clearly ahead) but 2 fights each stalled, so the cell counts "not won". The leash-on mean is also longer than on the previous build (1294 against 1134 at 16 v 8): the A5 movement makes leash-on fights slower. Surprising number, first a question about the instrument: leash-on, 16 v 16, margin +0.073 with 3 stalemates; the previous build had -0.003. Cell is 20 fights with 3 undecided, so the mean is carried by 17 fights; I did not trace the stalls here.

## 4. A choke defence, tick by tick (guard stance, Q-096-01)

**Scene.** Canvas 3000 x 1600 wu. One wall (x 1500 to 1600, 100 wu thick) across the middle with a **200 wu gap** (y 700 to 900), built with `om_map_block_rect`. Defenders (8 Vanguards in a row, 30 wu apart) stand 100 wu behind the gap on the east. Attackers (a blob of N) start 700 wu west and attack-move, so they must pass the gap. Defender orders: attack-move (as the game gives today) and idle (placed, never steps forward; the guard order itself does not exist).
```
   west                      wall                  east
                          ##########
   x x x x                ##########
   x x x                  ##########                 o o   <- defenders, 100 wu behind the gap
   x x x x  --->     (gap, 200 wu, open)             o o
                          ##########                 o o
                          ##########
```

Break-evens, 8 defenders against N attackers, 20 fights per cell. Cell: margin, won, fights undecided. Full columns in `choke_scan.md`, `choke_scan_raider.md`.

| N | open, defenders attack-move | open, defenders idle | choke, attack-move | choke, idle |
|---|---|---|---|---|
| 7 | +0.440, yes, 0 | +0.401, yes, 0 | +0.427, yes, 0 | +0.421, no, 8 |
| 8 | +0.124, yes, 0 | +0.074, yes, 0 | +0.136, yes, 0 | +0.176, no, 4 |
| 9 | -0.278, no, 0 | -0.306, no, 0 | -0.283, no, 0 | -0.150, no, 3 |
| 10 | -0.488, no, 0 | -0.480, no, 0 | -0.495, no, 0 | -0.372, no, 1 |
| 12 | -0.663, no, 0 | -0.654, no, 0 | -0.665, no, 0 | -0.608, no, 0 |

Same with Raiders (range 200), 8 defenders:

| N | open, attack-move | open, idle | choke, attack-move | choke, idle |
|---|---|---|---|---|
| 7 | +0.395, yes, 0 | +0.193, yes, 0 | +0.424, yes, 0 | +0.309, no, 9 |
| 8 | +0.108, yes, 0 | -0.110, no, 0 | +0.091, yes, 0 | +0.141, no, 9 |
| 9 | -0.281, no, 0 | -0.322, no, 0 | -0.298, no, 0 | -0.025, no, 7 |
| 10 | -0.452, no, 0 | -0.459, no, 0 | -0.463, no, 0 | -0.275, no, 2 |
| 12 | -0.606, no, 0 | -0.606, no, 0 | -0.605, no, 0 | -0.434, no, 0 |

**Tick by tick (8 defenders against 9, seed 0; `choke_ticks.md` has all three set-ups and a picture each).** Idle defenders, behind the wall:

| tick | defenders firing / blocked / walking / no target | attackers firing / blocked / walking / no target | strength def / att |
|---|---|---|---|
| 135 | 1 / 0 / 0 / 7 | 1 / 0 / 2 / 6 | 1.00 / 1.00 |
| 155 | 8 / 0 / 0 / 0 | 0 / 1 / 1 / 7 | 0.99 / 0.99 |
| 185 | 8 / 0 / 0 / 0 | 3 / 0 / 0 / 6 | 0.98 / 0.97 |
| 225 | 8 / 0 / 0 / 0 | 5 / 1 / 0 / 3 | 0.96 / 0.95 |
| 285 | 8 / 0 / 0 / 0 | 7 / 1 / 0 / 1 | 0.92 / 0.91 |
| 435 | 8 / 0 / 0 / 0 | 6 / 1 / 0 / 2 | 0.83 / 0.83 |

Attack-moving defenders (same fight): by tick 67 **all 8 are already west of the wall's face** (x 1500), so it plays as the open-ground fight; margin -0.283 against -0.281 in open ground.

**Plain words.**
- Does the choke help the defender? **Not one who chases:** within 0.02 of open ground at every N, Vanguard or Raider. **For one who stays behind it, a little:** against 9 Vanguard attackers idle behind the wall loses by -0.150 against -0.306 idle in open ground; with Raiders -0.025 against -0.322 (a near-even fight). No break-even moves in the lab's "won" rule, because the idle-behind-the-wall cells are the stalled ones (below). The shorter the range the more the wall helps.
- Do corner-blocked units now get through the gap? **No.** Idle defenders, 7 Raider attackers, seed 0: the fight ends in stalemate at 1158 ticks (margin 0.45, 6 defenders and 1 attacker left). The last attacker stands at x 1499, y 690, 10 wu north of the gap's edge at the wall's west face, its target (a defender) in range by distance, the engine saying the shot is **blocked**, and it stays. The undecided counts above (up to 9 of 20 in a cell) are this. So the earlier finding stands: it is the engine's rule (a unit with a blocked target does not path to a clear shot), not a result about soldiers; Q-088-01 is a related row.

## 5. The one-page chart

`controls_page.html` (177 KB, under the 200 KB limit; open in a browser, viewed by headless-Chrome screenshot). It has a heading that states the finding in soldiers ("identical: 16 units beat 15", "damage: 16 units beat 17"), one dot per enemy size coloured won or lost with the break-even as a dashed line and its label ("beats 15, loses to 16"), a table with a plain-words column ("16 units beat 8"), and a chart of units able to fire through one 16 v 16 fight, side 0 and side 1 with the gap shaded. Not done by it: y axis is margin not soldiers; "identical" and "damage" are harness words; the grey bar under the firing chart; no leash page (the leash-on page is 232 KB, `leash_table.md` carries it).

## 6. The 20-unit formation printout (A161)

Scene: `tests/csim/test_E13_S101_movement_that_reads.py`: 20 Raiders in a 4x5 block (35 wu apart) at x 0 to 105, one `om_command_group_move` to (1000, 70). Slot of unit i: x = 947.5 + 35 x (i div 5), y = 35 x (i mod 5). A unit's order ends when `om_unit_get_destination` stops reporting a destination (within 22.5 wu of its slot). Watched 700 ticks. The R-101-01 test fails today on this build (18 of 20 arrive).

Full output with legend, six pictures, per-unit table, neighbours and the pacing detail: `2026-10-03_phase_b/s101_formation_printout.md`. The picture at tick 125 (first order ends) and tick 600 (nothing changes after 200), one character = 5 wu across, 10 wu down, `.` an empty slot, `X` unit 1, `Y` unit 4:

Tick 125:
```
    |                                                |
    |   5                                            |
    |                                                |
    |                 .    a .      .   f  .         |
    |6                                               |
    |                                                |
    |                b.      .      .   g  .         |
    |                                                |
    |                                                |
    |                                                |
    |                 . c    .      .   h  .         |
    |                                                |
    |                                                |
    |                 . d    .      .   i  .         |
    |   3                                            |
    |                                                |
    |                                                |
    |                 .   e  .      .   j  .         |
    |                                                |
    |                                                |
    |       9                                        |
    |                                                |
    |                                                |
```

Tick 600:
```
    |                                                |
    |                     5                          |
    |         X                                      |
    |                 .      .      .   f  .         |
    |              0              a                  |
    |                                                |
    |                 .   6  .      .   g  .         |
    |                                                |
    |                             b                  |
    |             2       7                          |
    |                 .      .      .   h  .         |
    |                              c                 |
    |                                                |
    |             3   .  8   .      .   i  .         |
    |                                                |
    |                             d                  |
    |                                                |
    |                 .      .      .   j  .         |
    |                      9     e                   |
    |             Y                                  |
    |                                                |
    |                                                |
    |                                                |
```

Order-end tick per unit (slot = x, y):

| unit | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 |
|---|---|---|---|---|---|---|---|---|---|---|
| ended at tick | 147 | never | 199 | 133 | never | 138 | 140 | 147 | 178 | 137 |

| unit | 10 | 11 | 12 | 13 | 14 | 15 to 19 |
|---|---|---|---|---|---|---|
| ended at tick | 135 | 138 | 152 | 134 | 140 | 125 (all five) |

18 of 20 end, from tick 125 to 199 (a 74-tick, 3.7 s spread; the test's window is 40 ticks). Closest any two units get: 29.1 wu (tick 173). Largest one-tick step: 9.4 wu (no teleport).

The two that never end, distance to their slot at tick 125 / 200 / 300 / 600:

| unit | slot | 125 | 200 | 300 | 600 | position at 600 |
|---|---|---|---|---|---|---|
| 1 | (947.5, 35) | 122.6 | 54.3 | 54.1 | 54.1 | (909.8, -3.7) |
| 4 | (947.5, 140) | 133.9 | 50.2 | 45.1 | 34.9 | (925.6, 167.2) |

Neighbours at tick 600: unit 1's slot is occupied by unit 6 (19.5 wu from that slot centre, 15.8 from its own, ended tick 140) and unit 0 (22.8 wu away, 21.8 from its own, ended 147): two units settled in or beside it. Unit 4's slot has unit 9 at 32.2 wu (20.7 from its own, ended 137) and unit 8 at 35.4 wu (ended 178): neighbours settled around, none on the slot.

**What a player would see.** A neat block of 20 sets off, rearranges into 5 columns by about tick 125 (6 seconds) and arrives; 18 settle by 10 seconds. Two units never settle: they walk at full speed (7.5 wu per tick every tick, 400 ticks, 3000 wu of walking) back and forth along a short line about 30 to 50 wu from their slot, beside the settled block, **forever**. Net movement in 400 ticks: 0.2 wu (unit 1) and 26 wu (unit 4). Two units of twenty pace on the spot with no end. This is the formation-arrival defect of A161; which rule to pick (seek the slot again, take the nearest free spot, give up after a time) is Westley's.

## What the harness could not express

A guard order (only idle is measured); per-tick "who fires / who is blocked" (the trace holds position, target, facing, alive; I used a thin recording wrapper around the engine in a scratch script, nothing under `scripts/skilllab`); a reach control in the CLI; order-end ticks (read through `om_unit_get_destination` in a scratch test, no harness support).
