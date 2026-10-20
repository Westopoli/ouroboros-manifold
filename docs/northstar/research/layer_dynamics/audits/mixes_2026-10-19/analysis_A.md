The harness refused to let me write `/tmp/claude-1000/-home-westopoli-Projects-ouroboros-manifold/b1e8769e-404e-4263-be23-8535a58b0e59/scratchpad/mix_A/analysis.md` (sub-agents may not write report files), so the full analysis is below. Save it there if you want the file. The scripts and raw results are in `/tmp/claude-1000/-home-westopoli-Projects-ouroboros-manifold/b1e8769e-404e-4263-be23-8535a58b0e59/scratchpad/mix_A/code/` (`mixlab.py`, `exp.py`, `exp2.py`, `exp3.py`) and `/tmp/claude-1000/-home-westopoli-Projects-ouroboros-manifold/b1e8769e-404e-4263-be23-8535a58b0e59/scratchpad/mix_A/exp_*.json`. The worktree `~/Projects/om-push/wt/mixA` has its `.wt-done` (`2026-10-19 detached 4c638fc0`). Total run time was about 5 minutes; no repo file was changed.

**Summary (15 lines)**
1. The mixes only ever pair Line with Strike (M1, M2) or Line with Siege (M3, M4). Strike against Siege, the matrix's biggest gap (1.5 one way, 0.20 the other), appears only through M3b's single Raider.
2. Batch one fights only Vanguard, Raider and Interceptor; Bombard, Bastion and Warden never fight in it. The Warden is in no mix at all, and the layout-search table leaves out Interceptor and Warden.
3. Measured: two layers below the enemy, 8 Interceptors with 8 Vanguards beat 48 (ceiling). The same units two layers above lose to 13. The shipped one-above play reaches 17/18. The Interceptor's two-up reach is never used today.
4. Measured: Bombards two layers above an enemy with no Interceptors beat 48, margin exactly 0.50 at every headcount. With enemy Interceptors the gain is gone (15/16).
5. Code defect: the lab copies every type that has a reach into a custom type, and the copy loses the Warden aura (unit.c:1129, :627) and the Bastion cap (unit.c:987). Built-in Wardens beat copies 8 of 8; a copied Bastion dies in 720 ticks instead of 1,057.
6. The fix is small: `om_roster_set_reach` works on built-in type ids (checked on ids 5 and 1). It belongs to fight.py, L2's row.
7. Measured: 8 Wardens a side make 6 of 8 mirror fights at 16 v 16 hit the tick cap, with both sides firing about 6,700 unit-seconds. Healing stacks per Warden (R-083-03), so this needs Westley's ruling.
8. Code: the `OM_TP_CATMULT_*` settings are never read (unit.c:2427-2438 uses compile-time constants). Margins are byte-identical at 0.2 and 0.8, so a category-matrix knob family needs an engine piece first.
9. The mirror control holds for all 12 mixes I tried (break-even 14 to 17 at 2 replicates; noise about ±1 unit).
10. The count and type predictions disagree in 9 to 12 of 36 fights for Strike/Siege and multi-type mixes, against 0 to 3 for M0 to M4. Only those mixes test ruling 5's second prediction.
11. Proposed: keep M0 to M4 and M3b; add M5 (8 Raider, 8 Bombard), M6 (8 Interceptor, 8 Bombard), M7 (6 Vanguard, 5 Raider, 5 Bombard), M8 (12 Vanguard, 4 Warden) and M9 (8 Raider, 8 built-in Bastion).
12. That covers every matrix cell at least three times, every type in at least two mixes, and every reach pairing the layer rules allow.
13. Proposed plays: Interceptors two below plus its blunder control, artillery above (with and without enemy Interceptors), Siege one above, Strike screen, Strike hunts Siege, each type on its prey, Wardens behind the line, Bastion wall. Vision, range-up and damage-up run only on the layer plays.
14. About 10,100 fights: roughly 6 minutes wall at 0.4 s per fight, or about 21 minutes at my measured 1.5 s mean (12 workers).
15. Risks: one-way plays always hit the ceiling, so their crossing must come from the knob sweep. The Warden stall waits for Westley. The type weight leaves out area damage, regen and the Bastion cap. Heavy mixes run 2 to 5 s per fight, above the 1.5 s mark.

---

# Roster mixes for the skill lab: coverage analysis (analyst A, Opus)

Date 2026-10-19. Code read on `origin/push/labrev2-lab` at `4c638fc0` (detached worktree `~/Projects/om-push/wt/mixA`). Docs read on `origin/main`. Every run used that tree's real C library through the lab's own `fight`, `scan` and `FightPool`.

Main findings, in soldiers:
- Strike never fights Siege in any mix except through one Raider in M3b.
- The Warden is in no mix. At 8 a side, its stacking heal stalls 6 of 8 fights.
- The Interceptor never stands where its two-up reach counts. Placed two below the enemy, 16 units beat 48.
- Bombards two layers up are untouchable unless the enemy has Interceptors.
- The lab's copied types lose the Warden aura and the Bastion cap.

## A. The six types
Stats from E-11 R-082-01 (`E-11:50-55`, `om_constants.h:479-515`). Reach from R-164-01 as the lab sets it (`plays_space.py:48`). Abilities are off in every lab fight (`contract.py:85`).

| Type | Role | Cat | HP | Dmg/int | Range | Sensor | Reach up/down | Speed | Special that acts in lab | Mixes |
|---|---|---|---|---|---|---|---|---|---|---|
| Vanguard | frontliner | Line | 500 | 7.5/1.2 | 300 | 700 | 0/0 | 80 | none | M0-M4, M3b |
| Raider | flanker | Strike | 250 | 9/0.8 | 200 | 800 | 1/1 | 150 | none | M1, M3b (1 unit) |
| Interceptor | screen | Strike | 325 | 6/1.0 | 250 | 1000 | **2**/1 | 130 | only type that fires 2 up | M2 only |
| Warden | support | Line | 375 | 4/1.5 | 350 | 800 | 0/0 | 70 | aura: −10% damage (diminishing) and +0.075 HP/tick per Warden, stacking (`unit.c:1057-1075, 1119-1135`) | **none** |
| Bombard | artillery | Siege | 400 | 17.5/3.0 | 1200 | 300 | 0/2 | 50 | area disc 150 wu, capped at 4× base | M3, M3b |
| Bastion | anchor | Siege | 1050 | 7/1.8 | 800 | 300 | 0/2 | 40 | never takes a multiplier above 1.0 (R-081-03, `unit.c:985-988`) | M4 only |

Which types go unused depends on where you look:

| Where | Types that never fight there | Source |
|---|---|---|
| Mixes M0 to M4 and M3b | Warden | `plays_space.py:116-119` |
| Batch one plays | Warden, Bombard, Bastion | `sweep.py:27-31` |
| Layout-search table | Warden, Interceptor | `batches.py:25` |

I read Westley's "two" as the Warden and the Interceptor's real job. The Interceptor's only play puts it one layer above, where its reach equals a Raider's. The Bastion is a close third: it appears only in `s1_outrange`, which no sweep runs, and only as a copy that drops its exception.

What the unused types would have shown:
- **Warden:** strength the firing count cannot see, which is the direct test of C2. It also exposes the stall (measured).
- **Interceptor two up:** the only counter to Siege two layers above (measured).
- **Bastion against Strike:** the one override of the damage matrix.

## B. What a line crossing is here
- **The fight.** 16 units against 8 to 48, the same mix and the same values on both sides. Only side 0's arrangement, orders and layer choice differ. The fight runs to elimination; the result is who is left standing.
- **The firing count.** A unit counts as able if it sees an enemy, the enemy's layer is inside its reach, the enemy is in range at that offset, and the line is clear. Over the first 40 ticks after contact this gives two predictions: by count, and by count weighted by category multiplier. `agreement` says whether each named the survivor.
- **The scan.** It gives the break-even ("beats 17, loses to 18"). A play's gain is its break-even minus the naive baseline's.
- **The crossing.** A line is the edge in knob space where a condition flips. A crossing is a region where all conditions hold; there may be several.

The three conditions:
- **C0:** in a mirror, the larger force wins and the break-even sits at equal numbers.
- **C1:** the skilled side wins the firing count by more than the mirror's noise.
- **C2:** results follow the firing count (rank agreement at least 0.8; no more than one fight in five more than 25% off the trend).

## C. The gap

**C.1 Category cells.** With the same mix on both sides, a cell fights only if the mix holds both categories.

| Cell | Mult | Covered by | In batch one? |
|---|---|---|---|
| Line to Line | 1.0 | all mixes | yes |
| Strike to Strike | 1.0 | M1, M2 | yes |
| Line to Strike | 1.5 | M1, M2 | yes |
| Strike to Line | 0.75 | M1, M2 | yes |
| Siege to Siege | 1.0 | M3, M4 | no |
| Line to Siege | 0.75 | M3, M4 | no |
| Siege to Line | 1.5 | M3, M4 | no |
| Strike to Siege | 1.5 | 1 Raider in M3b | no |
| Siege to Strike | 0.20 | 1 Raider in M3b | no |

Measured: the two predictions disagree in only 0 to 3 of 36 mirror-scan fights for M0 to M4. They disagree in 9 to 12 of 36 for the Strike/Siege and multi-type mixes. Only those mixes can tell the predictions apart.

**C.2 Reach pairings.** Side 0 on layer L, the enemy on L+d. Read across the three columns.

| Side 0 type and where it stands | Fires? | Which enemy types fire back | Played today |
|---|---|---|---|
| Raider one above | yes | Raider, Interceptor | yes, three plays with the same geometry |
| Interceptor one above | yes | Raider, Interceptor | `s3_types_by_reach`; in M2 this is the Raider case again |
| Siege two above | yes | Interceptor only | `s3_over_the_choke`, untouchable in M3b |
| Siege one above | yes | Raider, Interceptor | no |
| Raider or Interceptor one below | yes | Raider, Interceptor, Siege | **no**: the enemy is always on layer 0 |
| Interceptor two below | yes | Siege only | **no** |
| Interceptor two above | no | Interceptor | no (blunder control) |
| Line type off its layer | never | | correctly refused (`no_reach`) |

- At a two-layer offset, only Siege above and Interceptor below can fire.
- Batch one sweeps the two-layer vision, range and damage knobs (`sweep.py:66-80`). No unit in its plays stands two layers from an enemy, so those halves are inert.
- No play puts a unit below the enemy.

**C.3 Per type and per layer.**
- The Warden's aura numbers are compile-time constants (`om_constants.h:528-558`). The lab can measure the aura but not sweep it.
- The Bastion's exception is lost on the copy, and no mix pairs Bastion with Strike.
- The Bombard's area damage is not in the weight.
- Only layers 0 to 2 are used. There is no control showing that a fight on layers 2 to 4 gives the same result.

**C.4 Two code facts that block coverage.**
1. **Copies lose type-keyed specials.** `plays_space._types` (`:51-52`) and `fight._register_types` (`fight.py:35-45`) copy every type that has a reach into custom id 100 and up. The engine keys the aura and the Bastion cap on built-in ids (`unit.c:1129`, `:627`, `:987`). `sweep._reach_zero` (`:273-282`) copies every type, so a Warden null control would lose its aura too. `om_roster_set_reach` works on built-in ids (verified), so the fix is small and sits in L2's row.
2. **The category matrix is not a live knob.** The `OM_TP_CATMULT_*` settings exist (`ouroboros_sim.h:1022-1030`), but `om_tactical_category_multiplier` ignores the world (`unit.c:2427-2438`, `(void)w;`).

## D. Proposed layouts

**Mixes** (DRAFT, 16 heads, largest-remainder scaling, the same mix on both sides). Keep M0 to M4 and M3b unchanged, and add:

| Id | Composition | Job |
|---|---|---|
| M5 | 8 Raider, 8 Bombard | Strike/Siege cells (1.5 and 0.20); Siege one above with Raiders answering |
| M6 | 8 Interceptor, 8 Bombard | the two-layer duel |
| M7 | 6 Vanguard, 5 Raider, 5 Bombard | all nine cells |
| M8 | 12 Vanguard, 4 Warden | C2 stress test; 4 rather than 8 because of the stall |
| M9 | 8 Raider, 8 built-in Bastion | R-081-03 exception; needs fix C.4.1 |

**Plays** (side 0 arranged, side 1 the same mix in a naive blob on one layer):

| Play | Mix | Arrangement | Targets | Result |
|---|---|---|---|---|
| P1 `s3_interceptor_below2` | M2 | Interceptors on L0, Vanguards on L2 level with the enemy | Interceptor two below, one-way | **measured: ceiling 48** |
| P1n blunder control | M2 | Interceptors two above | negative control | **measured: 12/13** |
| P1c | M6 | as P1 | enemy Bombards fire down 2 | not run |
| P2 `s3_artillery_above` | M6 | Bombards on L2, Interceptor spotters level | countered by enemy Interceptors | **measured: 15/16** |
| P2u | M3 | as P2 with Vanguard spotters | untouchable control | **measured: ceiling, margin 0.50 at every headcount** |
| P3 `s3_siege_above1` | M5 | Bombards one above | Raiders fire up 1 | not run |
| P4 `s5_strike_screen` | M5 | Raiders in front, Bombards behind | Strike to Siege | **measured: 14/15, same as mirror** |
| P5 `s5_hunt_siege` | M5 | Raiders flank to the enemy Bombards | Strike to Siege 1.5 | not run |
| P6 `s5_each_on_its_prey` | M7 | Vanguards front, Bombards back, Raiders flank | all nine cells | **measured: 15/16, same as mirror** |
| P7 `s2_warden_behind_line` | M8 | 4 Wardens 150 behind the line, 110 apart | aura coverage | **measured: 15/16 vs mirror 14/15** |
| P8 `s1_bastion_wall` | M9 | Bastions guard a line in front of the Raiders | Strike to Bastion capped at 1.0 | not run |

**Knob families per play:**

| Family | Run on | Inert on | Why it bites there |
|---|---|---|---|
| vision (1 and 2 layers) | P1, P1c, P2, P2u, P3 | same-layer plays | decides whether a one-way shot exists at all |
| range-up and damage-up (1 and 2) | P1, P1c, P3 | P2u and same-layer plays | the only plays where someone fires up |
| emitting | `s3_dark_striker`, plus a dark P1 | same-layer plays | silence hides the Interceptors below |
| arc | P4 to P7, after E2 | layer-only plays | facing decides whether a screen or a flank pays |
| category matrix | M5, M7, M9 | | needs an engine piece first |
| Warden aura | M8 | | needs an engine piece first |

**Fight count.** Assumptions: a bisection scan at 3 replicates is about 54 fights (36 when it hits the ceiling), and each play runs with about two baselines, so about 162 fights per play per knob point.

| Batch | Contents | Fights |
|---|---|---|
| Coverage at base values | 11 plays × 162 + 5 new mirrors × 54 | about 2,050 |
| Knobs | vision 4 pts × 5 plays; range-up 4 × 3; damage-up 4 × 3; all × 162 | about 6,480 |
| Refinement | about +25% | about 1,600 |
| **Total** | | **about 10,100** |
| Arc (batch two, after E2) | 5 pts × 3 plays × 162 | about 2,430 |

CPU estimates:
- At 0.4 s per fight: about 4,040 CPU-seconds, about 6 minutes wall at 12 workers.
- At my measured rates: 0.6 to 1.2 s per fight for Strike and Siege mixes, 2.2 to 4.6 s for Vanguard-, Bastion- and Warden-heavy mixes, 9.6 s for the 8-Warden mirror. At a 1.5 s mean that is about 4.2 CPU-hours, about 21 minutes wall.
- Both are well under ruling 13's 4-hour mark.

## E. Evidence
Setup: `git worktree add --detach ~/Projects/om-push/wt/mixA origin/push/labrev2-lab`, then `make -j8` (19.6 s). All runs used 14 workers, `timeout 600 ~/Projects/ouroboros-manifold/.venv/bin/python exp.py engine|mirror|plays`, `exp2.py` and `exp3.py`; about 1,000 fights in about 5 minutes.

My builders add `point` = canvas centre, the shared meeting point of ruling 6. Without it the M0 mirror capped 3 of 8 fights (`exp_mirror_nopoint.json`). The shipped `plays_space` plays also leave `point` unset and rely on `scenes.placed_scene` (`scenes.py:347`) to fill it.

**E.1 Engine checks** (labelled asymmetric, instrument only; 8 fights each):

| Fight | Result |
|---|---|
| 8 V + 8 built-in Warden vs 8 V + 8 copied Warden | built-in side wins 8 of 8, 14 to 16 survivors, margin 0.944 |
| 8 Raiders vs 4 built-in Bastions | Raiders win in 1,057 ticks on average |
| 8 Raiders vs 4 copied Bastions | Raiders win in 720 ticks on average |

**E.2 Mirror control per mix** (scan 8 to 48 by bisection at 2 replicates, 36 fights; "split" = fights where the two predictions disagree):

| Mix | Break-even | 16 v 16 (side 0 – side 1) | Split of 36 |
|---|---|---|---|
| M0 | 16/17 | 5-3 | 0 |
| M1 | 14/15 | 2-6 | 2 |
| M2 | 14/15 | 7-1 | 2 |
| M3 | 15/16 | 1-7 | 3 |
| M3b | 15/16 | 2-6 | 3 |
| M4 | 15/16 | 2-5, 1 cap | 3 |
| M5 (R+Bo) | 14/15 | 1-6, 1 cap | 12 |
| M6 (I+Bo) | 14/15 | 3-5 | 12 |
| M7 (V+R+Bo) | 15/16 | 6-2 | 9 |
| M8 (12V+4W) | 14/15, 1 cap in scan | 3-5 | 0 |
| M9 (R+Ba) | 14/15 | **0-8** | 9 |
| all six types | 15/16 | 5-3 | 12 |

Notes on E.2:
- **M9 0-8 is suspicious.** In a mirror, side 1 won all 8 fights. Side 0 is always on the left and only the spawn order swaps, so check for a left/right bias before M9 runs.
- **The weight may mislead in the new mixes.** "Count right, type wrong" outnumbers the reverse: 9 to 3, 8 to 4, 7 to 2, 11 to 1. This is a lead on small samples. The weight leaves out Bombard area damage and the Bastion cap (`firing.py` reads `om_tactical_category_multiplier`).

**E.3 Reach and Warden runs:**

| Play | Break-even | Note |
|---|---|---|
| Interceptors two below (M2) | ceiling 48 | |
| Interceptors two above (M2) | 12/13 | 1 cap at 16 v 16 |
| `s3_types_by_reach` as shipped | 17/18 | |
| Bombards two above, Vanguard spotters (M3) | ceiling 48 | margin 0.500 at every headcount |
| Bombards two above, Interceptor spotters (M6) | 15/16 | |
| Mirror 8 V + 8 W | 10/11 | 6 of 8 capped at 16 v 16 (e.g. 11-11 survivors after 12,000 ticks, 6,785 vs 6,660 firing unit-seconds); scan cells 11, 16 and 24 hold caps |

**E.4 Category multiplier knob:** `OM_TP_CATMULT_SIEGE_STRIKE` at 0.2 and at 0.8, 16 v 20, gives identical margins and ticks on M1 (−0.277), M5 (−0.472) and M7 (−0.419).

**Reasoning only, not run:** the reach table in C.2 (from R-164-01 and `firing.py:62-75`), the fight counts, P1c, P3, P5 and P8, and which knobs are inert where.

## F. Risks, and what I would not change
**Kept as is:**
- the same mix on both sides (my two copy-vs-built-in fights are instrument checks only);
- elimination only;
- the 8-to-48 scan;
- every band 0.25× to 4× from the bible value, with firing up as a penalty only;
- M0 to M4 and M3b unchanged.

**Risks:**
1. **One-way plays always hit the ceiling.** Their crossing must come from the two-layer vision, range and damage sweeps.
2. **The Warden stall traces to a rule (R-083-03 stacking).** Westley rules before any Warden-heavy mix runs.
3. **Copied types are wrong** for the Warden and the Bastion until fight.py sets reach on built-in ids.
4. **The weight omits area damage, regen and the Bastion cap.** Under ruling 5, `both_wrong` rows in M5 to M9 are expected findings. Whether the Bastion cap counts as part of "the category multiplier" is a question for Westley: the bare matrix, or the matrix as resolved for that target.
5. **Heavy mixes are slow:** 2 to 5 s CPU per fight against the 1.5 s mark. Run them last.
6. **My draft P4, P6 and P7 arrangements showed no gain beyond noise.** The formations need a builder's eye before they enter a batch.