# Invariant sweep of skill-lab fights, 2026-11-07 (read-only; nothing in the repo was edited)

Scope: 67 catalogue layouts (L-0034..0084 as they stand, plus 16 old denied open-field layouts L-0001..0031 with only rule R6 bypassed), each fought under `--sight off`, `--sight on` and the stage-4 `control` rule set (targeting by sight off): 199 fights, 23.9 million living unit-ticks, 12000-tick cap as the runner sets it. Every fight was checked after every tick by wrapping `Engine.step` (pre-state, post-state, tactical events). Determinism: 28 layout/sight pairs run twice in separate worker processes, 0 hash mismatches (per-tick position, hp, target of every unit).

**Seeds do nothing.** Seed 1 and seed 2 gave byte-identical fights in all 130 pairs of the first sweep (the tactical sim draws no random numbers; layout positions are the only variation). So "1 to 2 seeds" collapsed to one; the second pass was the `control` rule set instead.

"Clean" below means "not found in these 199 fights", not proof.

## Results (counts are unit-ticks or events; "layouts hit" is out of the layouts the invariant can apply to)

| inv | what | count | layouts hit | fights hit | rate per 100k unit-ticks (applicable fights) | verdict |
|---|---|---|---|---|---|---|
| I1 | living walker ends a tick inside a planar-blocked cell | 1,159,428 (1,020,718 deeper than 1 wu) | 19 of 28 block layouts | 51/83 | 8,296 | REAL, known (stage 4 report), wide: every chokepoint, city, flank-ridge and cover layout |
| I1b/c | walker ends tick on terrain not walkable on its layer | 3 | 1 of 14 terrain layouts (L-0045) | 3 | tiny | REAL, rare; the unit is ejected 24 wu next tick |
| I2a | unit moved >0.5 wu (not pushed) on a tick it fired | 1,168 | 55 of 67 | 137/199 | 4.9 | engine order is move then fire in one tick: the arrival step. Mostly by design, not a halt-then-fire |
| I2as | same, but target was already in range at the start of the tick (walked while able to shoot) | 79 | 15 of 67 | 22 | 0.3 | REAL, small: Vanguards mostly (52 of 79); L-0039 control 23 |
| I2b | unit moved 1 to 9 ticks after firing (backswing, ALG-60) | 786 | 30 of 67 | 60 | 3.3 | REAL, small; 535 are Bombards, 109 Bastions; the typical case: the shot kills its target and the unit marches on the next tick |
| I4b | target held >20 ticks, not shootable, not closing in (non-guards) | 3,547,771 | 20 of 67 | 52/199 | 14,867 | REAL, known (R-087-09 drop-after-1-s unbuilt). Only in layouts with blocks, hills or a slope; none in open fields |
| I4bg | same for guard units | 179,518 | 6 of 67 | 10 | 752 | by design? a guard may hold; listed for the record |
| I5b | per-tick displacement above max speed, unit starts or ends in a blocked cell | 19,814 (jumps 9 to 24 wu vs 2 to 7.5) | 15 of 28 | 28/83 | 142 | REAL: the "leave blocked cell" ejection teleports the unit |
| I5t | jump > 3x max speed + 15 wu in one tick, ignoring neighbours | 1,020 | 20 of 67 | 38 | 4.3 | REAL; 951 come with a layer change |
| I5tL | I5t together with a layer change | 951 | 13 of 14 terrain layouts | 28/42 | 27 | REAL: units cross a hill/ramp layer boundary by jumping 24 to 78 wu, landing on top of units (L-0061: 78 wu, ends 3.8 wu from a friend) |
| I8 | shot target not the nearest visible one, not the previously held target | 124 (36 with the nearer one nearer by >50 wu) | 22 of 67 | 45 | 0.5 | every one of the 124 follows damage to the shooter within 40 ticks, so return fire (R-087-06) can explain all of them: no unexplained break found |
| I10s | healing above 0.075 hp/tick (bible R-083-03: Wardens do not stack) | 859,729 | 52 of 55 Warden layouts | 143/164 | 4,510 | REAL, known-unbuilt (Q-084-01 closed "no stacking", engine piece FU-warden-no-stack): measured on 100% of 1-hit samples, heal = 0.075 x Wardens in 300 wu, damage reduction = 0.2 x (1 - 0.5^n) (diminishing, capped 0.2) which is neither the bible (flat 0.10) nor ALG-60 (0.10 per Warden) |
| I11 | sampled: can_see and in range but not can_shoot | 518,806 | 25 of 67 | 51 | | split below |
| I11x | an endpoint stands in a blocked cell | 333,402 | 14 of 28 | 29 | 2,386 | REAL, known (I1 consequence; sight skips endpoint cells, fire does not) |
| I11nl | no cell involved, units on different layers (hill): sees at 338 to 348 wu, cannot shoot | 184,976 | 11 of 14 terrain layouts | 22/42 | 5,283 | REAL, new: both calls test the terrain between them; they disagree. Not explained by range (can_shoot has no range test). Cause unproven |
| I11n | same layer, no cell, unexplained | 428 | 2 (L-0079, L-0083) | 4 | 1.8 | REAL, tiny, unexplained |
| I13 | two living same-layer units <28 wu apart after the step (rule says 30) | 741,270 | 46 of 67 | 107/199 | 3,106 | the push pass leaves residual overlap; the 2 wu slack is mine. Treat as soft |
| I13s | <20 wu apart | 2,264 | 15 of 67 | 30 | 9.5 | REAL: collisions the push pass does not resolve; includes 3.8 wu after a layer jump |
| I14 | fired while facing >90 deg off the target | 881 | 35 of 67 | 83 | 3.7 | known: the firing arc R-100-04 is DRAFT, not built; the unit fires first and turns after (also tick 1: facing never applied from the layout) |
| I23 | layer flipped and flipped back within 4 ticks | 31,839 | 13 of 14 terrain layouts | 28/42 | 909 | REAL: layer flicker at the hill rim, one flip per tick for many ticks (L-0063 unit 16 ticks 98 to 107 shows it) |
| I27 | unit pursued >25 wu beyond its sensor radius from its target-anchor (R-096-03) | 296,046; worst 493 wu over | 6 of 67 | 11 | 1,241 | medium confidence: only Bombards and Bastions (sensor 300 < weapon range 800 to 1200); anchor semantics are my reading (re-anchor on any target change) |
| I29 | walker with a destination, no target, moved <0.5 wu/tick for >40 ticks | 73,402 | 22 of 67 | 35 | 308 | REAL as jams; spot check found a 0.3 wu/tick crawl in an open field (L-0035), not a stand-still, so "stalled" overstates |
| I30 | pacing: 6 direction reversals within 600 ticks | 1,205 events | 36 of 67 | 61 | 5 | REAL, wide, includes open fields: L-0050 Vanguard 41 saws y 2100 to 2146 every 30 ticks holding target 12 |
| I7c | dead unit still reports a target id | 8.2 million | 62 of 67 | 174 | | engine does not clear `target_id` on death; the replay draws living units only, so harmless today. Dead units also answer `can_shoot` True |
| I12 | determinism | 0 mismatches in 28 pairs | | | | clean |
| I9 | idle unit with no order, target or neighbour moves | 0 | | | | clean here; one tick-1 case (L-0058 Warden jumped 4.6 wu at tick 1 with its nearest neighbour 40 wu away, then sat at 30.0 wu) was absorbed by my 40 wu push radius |

Clean (never seen in 199 fights): I3a..e (fire at a dead target, out of range, beyond layer reach, with can_shoot false, or across a blocked cell with neither end inside one), I4a (target kept a full step after it died), I6 (outside canvas), I7a/b/d (dead unit moved or fired, alive flag vs hp), I9, I10 (hp rose with no Warden near), I11c, I15 (turn rate), I16a/b/c (ALG-60 damage per hit, for units not covered by a Warden; Bombard layouts skipped), I17 (fire cadence), I20 (sight beyond sensor radius), I21/I21x/I22 (sight or fire across a blocked cell without an endpoint inside), I26 (guard leash 200 wu).

So: the lines that are clean are the ones the shot itself obeys (range, target alive, can_shoot, cadence, damage) and sight range. What breaks is movement against ground (cells, layers, ramps, crowds), targets that cannot be shot, and the two Warden rules.

## False positives and how I handled them (spot checks, one per invariant)
- I1 (L-0039 on, unit 1 tick 73): trace shows x 1999.69 oscillating across the cell edge x=2000 over ticks 70 to 78 with the box at 1900..2000 x 1900..2100; depth 0.31 wu at the first violation. The "deeper than 1 wu" column (1,020,718 of 1,159,428) strips the edge noise; another unit sat 5.4 to 6.4 wu inside.
- I2a: L-0034 off unit 8, tick 1102: steps 6.3 wu and fires in the same tick, then holds for 10+ ticks. That is the arrival step (move happens before the fire pass in `om_tactical_step`), so I2a alone is not a violation; I2as is the strict reading.
- I2b: L-0034 off unit 29: fires tick 1372 (target dies), tick 1373 moves 2.5 wu. Window 1..9 only; offset 10 is the first free tick (605 of 1,947 hits in the first pass were offset 10 and are no longer counted).
- I4b: L-0074 on unit 18 (Raider, city): target 8 held, can_shoot false, boxed in by a neighbour at 30.0 wu, hovers. Matches R-087-09 unbuilt.
- I5/I5b/I5t: L-0045 on unit 68 tick 190: (1601.9,2102.3) in an unwalkable cell, next tick (1587.65,2121.65): 24 wu for a unit that moves 4. The first pass flagged pushes; neighbours within 40 wu (pre or post) are now excluded from plain I5, which left 36 events, all within 1.3 wu of the limit (noise). I5t ignores neighbours and shows the layer jumps.
- I8: first pass flagged 301 with a tick-2 case; visibility now has to hold before and after the step and the margin is 10 wu; all 124 left are explained by return fire.
- I9: see table.
- I10s: confirmed by a controlled 1-hit-per-tick sample: 100% of 34,668 (n=4+), 9,806 (n=3), 9,627 (n=2) samples match heal = 0.075 n and reduction 0.2(1-0.5^n); n=1 fits everything.
- I11nl: L-0061 on tick 59 to 61, Warden 2 (layer 1) and 26 (layer 0), 2D distance 352, 348, 344: `can_see` a->b True, `can_shoot` False both ways, no blocked cell on the line. Cause unproven.
- I13: L-0061 unit 37 and 39: 3.8 wu apart straight after a 78 wu layer jump.
- I14: L-0004 on unit 23 tick 3618: facing 7.65 rad (about 1.37) against bearing -1.57, fires then turns 0.2 rad/tick; L-0067 unit 13 tick 2 same (turn rate respected: I15 clean).
- I23: L-0063 unit 16 tick 98 to 107: layer 0, 0, 0, 1, 0, 0, 1, 0, 1, 1 while walking at the rim, position moving back and forth 6 to 11 wu.
- I29: L-0035 on unit 38: moves 0.3 wu/tick toward a destination 1,100 wu away, nn 30.0: a jam crawl, not a stand-still.
- I30: L-0050 off unit 41: confirmed saw-tooth.
- I7c: dead unit 25 in L-0067 shows hp 0, target 14, can_shoot True.

## Caveats on the invariants themselves
- "Pushed" is my heuristic: any other unit within 40 wu of the start or end position, before or after the step. It hides real faults inside a crowd (the 78 wu jump above was excluded from I5 for this reason; I5t catches it).
- Sight-on fights draw hill terrain; `--sight off` builds no hills, so I11nl and I23 are almost all sight-on and control.
- Planar cells are the engine's 100 wu cells from `features._engine_boxes` (exact snap under sight on/control, padded under off), rounded outward as `om_map_block_rect` does. Terrain checks use `Engine.terrain_walk_mask` per layer.
- I8 uses side visibility (`om_player_can_see`) on the sight-on runs and range only on off/control.
- I27 re-anchors on any target change; a drop-and-reacquire in one tick is invisible to the API, so it may over-count.
- I16 skips any unit under a Warden (healing and reduction would confound it) and any layout with a Bombard (area damage), so the damage formula is only checked for a subset.

## Could not test through the Engine API
Everything outside the tactical engine (E-07 lifecycle, E-17 generation, economy); command validation (R-096-06) and plain move / attack-target orders (the lab only issues attack-move and guard); the stage-4 hold-release trigger; formation slots and group move completion (R-095, R-099-05 gave-up-at-75-wu: only the proxy I29); R-087-01 flinch and R-087-06 pursuit target selection (only seen through I8r); ability effects (disabled); layer-transition timing and cross-layer fire geometry (fog and fire layer numbering, see I11nl); ping/fog memory; R-099-04 arrival exactness (clean I9 is a weak proxy); a replay-vs-sim agreement (the client reads fight files, not the sim).

## Reproduce
Repo root, repo venv, one command each (about 9 minutes with 4 workers; results go next to the scripts):
```
cd ~/Projects/ouroboros-manifold   # run with the repo venv
S=docs/reports/2026-11-07-rule-enforcement/sweep   # results are written next to the scripts; do not commit them
.venv/bin/python $S/sweep.py                              # writes $S/sweep_results.jsonl (one JSON per fight incl. up to 3 examples per invariant)
PYTHONPATH=$S .venv/bin/python $S/agg.py                  # invariant table, clean list, determinism
.venv/bin/python $S/agg2.py                               # per-layout matrix
.venv/bin/python $S/spot.py L-0039 1 on 70 78 1,4         # per-tick trace of units: tick unit role x y layer alive hp target can_shoot dest fired nn
.venv/bin/python $S/spot_pair.py L-0061 on 60 2 26        # can_see / can_shoot of one pair, three ticks
.venv/bin/python $S/spot_face.py L-0004 on 3615 3621 23   # facing vs bearing
```
Scripts: `$S/inv_check.py` (all invariants; `NAMES` maps ids to wording), `$S/sweep.py` (layout list, 4 workers, 25 minute cap), `$S/agg.py`, `$S/agg2.py`. Older runs: `sweep_results_v1..v4.jsonl` (superseded by the final `sweep_results.jsonl`; v1 to v3 predate fixes listed under false positives).

## Per-layout matrix (counts over all three rule sets; `.` = none)
| layout | a:b | orders | feature | land | I1 | I2a | I2as | I2b | I4b | I4bg | I5b | I5t | I8 | I10s | I11x | I11nl | I13 | I14 | I23 | I27 | I29 | I30 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| L-0001 | 16:16 | both_same_point | - | small_flat | . | 16 | . | 19 | . | . | . | . | . | 3674 | . | . | . | 8 | . | . | . | . |
| L-0002 | 16:32 | both_same_point | - | small_flat | . | 23 | . | 16 | . | . | . | . | . | 14953 | . | . | . | . | . | . | 572 | . |
| L-0003 | 32:16 | both_same_point | - | small_flat | . | 47 | . | 2 | . | . | . | . | . | . | . | . | 362 | . | . | . | . | 11 |
| L-0004 | 16:16 | both_same_point | - | small_tiered | . | . | . | . | . | . | . | . | . | 35852 | . | . | . | 2 | . | . | . | . |
| L-0005 | 16:32 | both_same_point | - | small_tiered | . | . | . | 9 | . | . | . | . | . | . | . | . | . | . | . | . | 2709 | . |
| L-0006 | 32:16 | both_same_point | - | small_tiered | . | . | . | 102 | . | . | . | . | . | . | . | . | . | . | . | . | 5715 | . |
| L-0007 | 16:16 | both_same_point | - | small_flat | . | 26 | . | 16 | . | . | . | . | . | . | . | . | . | . | . | . | . | . |
| L-0010 | 16:16 | both_same_point | - | small_flat | . | 17 | . | . | . | . | . | . | . | . | . | . | 2 | . | . | . | . | 1 |
| L-0013 | 16:16 | both_same_point | - | small_flat | . | 16 | . | 50 | . | . | . | . | . | 21936 | . | . | . | . | . | . | . | . |
| L-0016 | 16:16 | both_same_point | - | small_flat | . | 25 | . | 33 | . | . | . | . | . | 5992 | . | . | . | . | . | . | . | . |
| L-0019 | 16:16 | both_same_point | - | large_tiered | . | 32 | . | 56 | . | . | . | . | . | 33254 | . | . | . | 3 | . | . | 386 | . |
| L-0020 | 16:32 | both_same_point | - | large_tiered | . | 33 | . | 40 | . | . | . | . | 1 | 2375 | . | . | 4 | . | . | . | 19 | . |
| L-0022 | 16:16 | both_same_point | - | small_flat | . | 55 | . | 6 | . | . | . | . | . | 5739 | . | . | . | . | . | . | . | . |
| L-0025 | 16:16 | both_same_point | - | small_tiered | . | . | . | . | . | . | . | . | . | 26270 | . | . | . | 4 | . | . | . | . |
| L-0028 | 16:16 | both_same_point | - | large_tiered | . | 13 | . | 22 | . | . | . | . | . | . | . | . | 10 | 5 | . | . | 27038 | 53 |
| L-0031 | 16:16 | both_same_point | - | small_flat | . | 52 | . | 22 | . | . | . | . | . | 2839 | . | . | 440 | . | . | . | 2687 | 1 |
| L-0034 | 16:16 | both_same_point | - | large_flat | . | 21 | . | 15 | . | . | . | . | . | 6473 | . | . | . | . | . | . | 680 | . |
| L-0035 | 16:32 | both_same_point | - | large_flat | . | 27 | . | 21 | . | . | . | . | . | . | . | . | . | . | . | . | 16 | . |
| L-0036 | 32:16 | both_same_point | - | large_flat | . | 25 | . | 52 | . | . | . | . | . | 1696 | . | . | . | . | . | . | 15 | 2 |
| L-0037 | 16:32 | both_same_point | chokepoint | small_flat | 7184 | 4 | 2 | 4 | 25484 | . | 1 | . | 1 | 11218 | 4609 | . | 5521 | . | . | 2590 | . | . |
| L-0038 | 24:24 | both_same_point | vantage | small_tiered | . | 6 | . | 11 | . | . | . | 114 | . | 10619 | . | . | 2 | . | 441 | . | . | 4 |
| L-0039 | 8:8 | both_same_point | cover | small_flat | 50436 | 32 | 23 | 15 | 195465 | . | . | . | . | 2972 | 14757 | . | 10654 | . | . | 70413 | . | 59 |
| L-0040 | 32:32 | both_same_point | objective | small_flat | . | 23 | . | 24 | . | . | . | . | . | 5018 | . | . | 12 | 30 | . | . | . | 1 |
| L-0041 | 8:64 | both_same_point | staging | small_flat | . | 15 | . | . | . | . | . | . | . | 253 | . | . | . | . | . | . | . | . |
| L-0042 | 64:8 | both_same_point | transit | small_flat | . | 32 | . | 17 | . | . | . | . | . | 1715 | . | . | 4752 | 4 | . | . | 359 | 20 |
| L-0043 | 48:12 | both_same_point | flank_route | small_tiered | 398614 | . | . | . | 509730 | . | 10061 | 2 | . | . | . | . | 376580 | . | . | 140632 | . | 105 |
| L-0044 | 12:48 | both_same_point | hazard_anchor | small_flat | . | 56 | . | 8 | . | . | . | . | . | . | . | . | 72 | . | . | . | 530 | 15 |
| L-0045 | 40:56 | both_same_point | slope | small_tiered | . | 6 | . | 59 | 1639 | . | . | 248 | 2 | 13045 | . | . | 1874 | . | 647 | 5477 | . | . |
| L-0046 | 64:64 | both_same_point | city | small_flat | 180496 | 2 | . | 15 | 814604 | . | 136 | 3 | 6 | 15193 | 1273 | . | 13706 | 7 | . | 76845 | 19 | 4 |
| L-0047 | 16:16 | both_same_point | trap | small_flat | . | . | . | . | . | . | . | . | . | 6554 | . | . | 4 | . | . | . | . | . |
| L-0048 | 32:16 | both_same_point | - | small_flat | . | 23 | . | 53 | . | . | . | . | . | 25469 | . | . | . | . | . | 89 | 2541 | . |
| L-0049 | 16:16 | both_same_point | - | small_flat | . | 12 | . | . | . | . | . | . | . | . | . | . | . | . | . | . | . | 10 |
| L-0050 | 16:32 | both_same_point | - | small_flat | . | 20 | . | . | . | . | . | . | . | . | . | . | 12 | . | . | . | . | 11 |
| L-0051 | 32:16 | both_same_point | - | small_flat | . | 20 | . | . | . | . | . | . | . | . | . | . | 16 | . | . | . | . | 11 |
| L-0052 | 8:64 | both_same_point | - | small_flat | . | 11 | . | . | . | . | . | . | . | . | . | . | 67 | . | . | . | 3 | 6 |
| L-0053 | 64:8 | both_same_point | - | small_flat | . | 11 | . | . | . | . | . | . | . | . | . | . | 213 | . | . | . | 3 | 6 |
| L-0054 | 128:128 | both_same_point | - | small_flat | . | 75 | . | . | . | . | . | . | . | . | . | . | 28461 | . | . | . | 2469 | 62 |
| L-0055 | 24:24 | hold:A | chokepoint | small_flat | 5209 | 18 | 2 | . | 32698 | . | 237 | . | 1 | 12953 | 2393 | . | 1444 | 47 | . | . | . | 3 |
| L-0056 | 16:32 | hold:A | chokepoint | small_flat | 28785 | 22 | 11 | . | 109071 | 2523 | 724 | . | 1 | 30188 | 12470 | . | 11282 | 32 | . | . | . | 80 |
| L-0057 | 12:48 | hold:A | chokepoint | small_flat | 25372 | 20 | 9 | . | 90339 | . | 501 | 1 | . | 10055 | 12108 | . | 21168 | 28 | . | . | . | 35 |
| L-0058 | 32:16 | hold:A | chokepoint | small_flat | 15025 | 5 | 1 | . | 58312 | 37677 | 503 | . | . | 2857 | 21658 | . | 3577 | 32 | . | . | . | 34 |
| L-0059 | 24:24 | hold:A | chokepoint | small_flat | 3065 | 29 | 4 | . | 11578 | . | 3 | . | . | 21105 | 437 | . | 724 | 32 | . | . | . | . |
| L-0060 | 20:40 | hold:A | chokepoint | small_flat | 178515 | 5 | 3 | . | 701894 | . | 331 | 2 | 1 | 23926 | 71817 | . | 97185 | 17 | . | . | . | 173 |
| L-0061 | 24:24 | hold:A | vantage | small_tiered | . | . | . | . | . | . | . | 32 | 4 | 6682 | . | 38278 | 10 | 2 | 2414 | . | . | 1 |
| L-0062 | 16:32 | hold:A | vantage | small_tiered | . | . | . | . | . | . | . | 26 | . | 15620 | . | 45780 | 28 | . | 6410 | . | . | 21 |
| L-0063 | 12:48 | hold:A | vantage | small_tiered | . | 2 | . | . | . | . | . | 110 | . | 7370 | . | 31926 | 970 | . | 7284 | . | 770 | 11 |
| L-0064 | 32:16 | hold:A | vantage | small_tiered | . | . | . | . | . | . | . | 8 | 2 | 2870 | . | 18072 | . | 4 | 632 | . | . | 2 |
| L-0065 | 24:24 | hold:A | vantage | small_tiered | . | . | . | . | . | . | . | 22 | . | 7406 | . | 15672 | 6 | 16 | 2412 | . | 19401 | 236 |
| L-0066 | 24:24 | hold:A | vantage | small_tiered | . | . | . | . | . | . | . | 32 | 2 | 13510 | . | 32284 | 24 | . | 2302 | . | . | . |
| L-0067 | 24:24 | hold:B | flank_route | small_tiered | . | 1 | . | . | . | . | . | . | 9 | 21455 | . | . | 468 | 59 | . | . | . | . |
| L-0068 | 24:24 | hold:B | flank_route | small_tiered | . | 2 | . | . | . | . | . | . | 13 | 29651 | . | . | . | 47 | . | . | . | . |
| L-0069 | 32:32 | hold:B | flank_route | small_tiered | . | 8 | . | . | . | . | . | . | 25 | 31318 | . | . | . | 67 | . | . | . | . |
| L-0070 | 12:24 | hold:B | flank_route | small_tiered | . | 2 | . | . | . | . | . | . | 9 | 43213 | . | . | 3232 | 39 | . | . | . | . |
| L-0071 | 16:32 | hold:B | flank_route | small_tiered | . | 9 | . | . | . | . | . | . | 21 | 44029 | . | . | 2 | 40 | . | . | . | . |
| L-0072 | 12:36 | hold:B | flank_route | small_tiered | . | . | . | . | . | . | . | . | 3 | 15663 | . | . | 34 | 54 | . | . | . | . |
| L-0073 | 24:24 | hold:A | city,transit | small_flat | 61058 | 7 | 3 | . | 288831 | 32218 | 2272 | 2 | 2 | 32948 | 69214 | . | 24068 | 22 | . | . | . | 23 |
| L-0074 | 16:32 | hold:A | city,transit | small_flat | 33573 | 15 | 6 | . | 160828 | 2537 | 265 | 1 | . | 24953 | 22804 | . | 18160 | 35 | . | . | . | 12 |
| L-0075 | 12:48 | hold:A | city,transit | small_flat | 16028 | 24 | 1 | . | 54069 | . | 2 | . | . | 4786 | 799 | . | 13624 | 24 | . | . | . | 9 |
| L-0076 | 32:16 | hold:A | city,transit | small_flat | 36353 | 16 | 5 | . | 117219 | 80953 | 4 | . | . | 17839 | 45416 | . | 22542 | 19 | . | . | . | 1 |
| L-0077 | 24:24 | hold:A | city,transit | small_flat | 85870 | 13 | 5 | . | 374250 | 23610 | 4361 | 2 | . | 31304 | 53647 | . | 61577 | 19 | . | . | . | 54 |
| L-0078 | 16:32 | hold:A | city,transit | small_flat | . | 36 | . | . | . | . | . | . | . | 38018 | . | . | . | 32 | . | . | . | . |
| L-0079 | 24:24 | both_same_point | trap,vantage | small_tiered | 27293 | 27 | 2 | 23 | 818 | . | . | 26 | 3 | 24762 | . | 126 | 4179 | 12 | 534 | . | . | 62 |
| L-0080 | 16:32 | groups | trap,vantage | small_tiered | . | 29 | . | 4 | 70 | . | . | 14 | 1 | 16574 | . | 1118 | 6024 | 12 | 14 | . | 1178 | . |
| L-0081 | 12:48 | both_same_point | trap,vantage | small_tiered | 834 | 28 | . | . | . | . | 413 | . | 9 | 8853 | . | 48 | 585 | 27 | . | . | 1542 | . |
| L-0082 | 32:16 | both_same_point | trap,vantage | small_tiered | 5694 | 14 | . | 62 | 450 | . | . | 8 | 6 | 12791 | . | 8 | 108 | 11 | 234 | . | . | 22 |
| L-0083 | 24:48 | groups | trap,vantage | small_tiered | 24 | 50 | 2 | 2 | 422 | . | . | 18 | 2 | 12588 | . | 1664 | 1170 | 22 | 8 | . | 4750 | . |
| L-0084 | 40:56 | hold:A | slope | small_tiered | . | 10 | . | 8 | . | . | . | 349 | . | 41333 | . | . | 6315 | 67 | 8507 | . | . | 44 |
on fights 67 layouts 67 unit-ticks 8318650
off fights 67 layouts 67 unit-ticks 9405934
control fights 65 layouts 65 unit-ticks 6138125

per sight (count / fights hit / fights):
I1 on: 320325 / 17 / 67 | off: 583648 / 18 / 67 | control: 255455 / 16 / 65
I2a on: 228 / 46 / 67 | off: 690 / 48 / 67 | control: 250 / 43 / 65
I2as on: 6 / 6 / 67 | off: 44 / 10 / 67 | control: 29 / 6 / 65
I2b on: 188 / 22 / 67 | off: 420 / 20 / 67 | control: 178 / 18 / 65
I4b on: 687086 / 19 / 67 | off: 2154525 / 15 / 67 | control: 706160 / 18 / 65
I4bg on: 38247 / 4 / 67 | off: 0 / 0 / 67 | control: 141271 / 6 / 65
I5b on: 6771 / 9 / 67 | off: 11566 / 13 / 67 | control: 1477 / 6 / 65
I5t on: 338 / 17 / 67 | off: 315 / 7 / 67 | control: 367 / 14 / 65
I8 on: 47 / 18 / 67 | off: 40 / 14 / 67 | control: 37 / 13 / 65
I10s on: 304173 / 52 / 67 | off: 259327 / 41 / 67 | control: 296229 / 50 / 65
I11x on: 50972 / 9 / 67 | off: 226300 / 12 / 67 | control: 56130 / 8 / 65
I11nl on: 92488 / 11 / 67 | off: 0 / 0 / 67 | control: 92488 / 11 / 65
I13 on: 243108 / 34 / 67 | off: 294816 / 37 / 67 | control: 203346 / 36 / 65
I14 on: 372 / 33 / 67 | off: 165 / 17 / 67 | control: 344 / 33 / 65
I23 on: 12837 / 13 / 67 | off: 5884 / 2 / 67 | control: 13118 / 13 / 65
I27 on: 19030 / 2 / 67 | off: 166612 / 5 / 67 | control: 110404 / 4 / 65
I29 on: 10119 / 11 / 67 | off: 52310 / 13 / 67 | control: 10973 / 11 / 65
I30 on: 358 / 17 / 67 | off: 654 / 31 / 67 | control: 193 / 13 / 65

layouts with planar blocks (approx): 32
