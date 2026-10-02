# A99 round 2: sustained melee, aura regen, damage-reduction scans, 2026-10-02

Measurement and proposal. Base: origin/main at 96a9430c (A99 grid contact check landed). No csrc change committed; the prototype is `a99_round2_prototype.patch` (csrc/unit.c only, 137 insertions, 16 deletions, applies to 96a9430c). Harness: `a99_melee_harness.c` (this directory). gcc 15.2, Ryzen 7 3700X, one thread, box not idle (load about 4). Release flags as the Makefile. Phase timers and gprof used scratch builds (not committed).

## Summary of findings

1. **Idle is not idle.** In the Siege opening about 45 percent of units change position every step (1,139 of 2,501 at 2,501 units, counted at the position refresh). So any "nothing moved, skip" cache never fires. I tried it (dirty flag on aura counts): zero gain, discarded.
2. **The damage-reduction spike is combat, not idle, not the macro.** With no hits `om_unit_damage_reduction` is never called (0 calls in 400 idle steps at 990 and at 4,996). The idle spike of the A91 report is gone after round 1 (idle worst step now 2.5 ms in macro_tick at 4,996). In an engaged Siege opening the spike steps are volleys: at 2,501 units 4 consecutive steps in every 32. At 4,996 the worst step (241 ms of a 263 ms step, phase timer) is `om_unit_damage_reduction`, 32,223 calls in that one step, about 7.5 us a call (each call walks every unit in the cells around the target, 35 percent of the Siege force being Wardens). At 990 the same: worst step 21.4 ms, 21.5 ms of it in damage reduction.
3. **Aura regen is a per-Warden scan of everything around it.** `om_tactical_apply_aura_regen`: for each Warden (35 percent of the Siege force: 1,746 of 4,996), a circle query of 300 wu over a 400 wu grid, visiting about 280 candidate rows (one row load each, rows are large, pointer-chased through the cell lists) and keeping the same-faction ones. 495k candidate visits a step at 4,996 units = 6.8 of 10.1 ms. At 10,100 idle: 15.2 of 20.4 ms (76 percent). Cost per step grows about N^1.2 (units fill the same area).
4. **The real melee floor is neither of those.** Two lethal compositions without Wardens (plain Raider/Vanguard/Interceptor/Bombard mix, both sides attack-move into each other, 18 wu spacing) at 10,000 units: median 34 ms, worst 135 ms, 4,444 left of 10,000 after 800 steps. 85 percent of the step is `om_tactical_ai_tick`; gprof puts `om_tac_nearest_scan_cell` (39 percent self) and `om_grid_iter_next` (36 percent) on top: about 380 candidate visits per nearest-hostile query. Neither round-2 fix touches it. That is a candidate for a round 3; I did not design it.
5. **Prototype, two exact changes, verified byte-identical:** aura regen over cell-sorted flat arrays, and per-cell Warden/Bastion lists for the damage-reduction scans. Idle 10,100 units: median 21.6 to 7.4 ms, worst 34.4 to 12.8. Engaged Siege at 4,996: worst 273 to 35 ms, p95 171 to 23.

## Task 1: sustained melee, moving units

Harness: `a99_melee_harness.c MIL GAP STEPS`. Two compositions.
- **Siege**: the A91/A99 case (mission at region 0, seed 121), player block teleported to the enemy centroid plus a 300 wu clear gap, both sides given attack-move at the other centroid. Siege units are 35 percent Wardens and 8 percent Bastions, so the fight is slow: 2,501 units lost 19 in 400 steps, 4,996 lost 318 in 700, and at 10,100 nobody died in 700 steps (blocks had not engaged; I did not look for the reason). Treat the Siege runs as "sustained, barely lethal", the steady-state shape the player sees.
- **Bare**: no mission, N units a side in a plain grid, `BARE=N WARD=percent`. WARD=0 is the lethal case (units die), WARD=35 reproduces the Siege Warden share at 18 wu spacing (denser than the Siege).

Base (origin/main), ms per `om_tactical_step`. "Steady" is steps within 3x the median; "spike" steps are the rest. Period is 2 base ticks above 1,000 units, so 100 ms is the frame.

| case | live units start to end (steps) | median | p95 | p99 | max | steady p95 / max | spike steps (mean) |
|---|---|---|---|---|---|---|---|
| Siege 2,501 | 2,501 to 2,482 (700) | 9.2 | 93.7 | 101.8 | 104.1 | 11.9 / 19.3 | 72 (84) |
| Siege 4,996 | 4,996 to 4,678 (700) | 14.0 | 159.8 | 231.6 | 243.2 | 18.1 / 39.8 | 56 (169) |
| Siege 10,100 | 10,100 to 10,100 (700) | 21.6 | 25.1 | 29.4 | 30.1 | 25.1 / 30.1 | 0 |
| Bare 2,500 W0 | 2,500 to 382 (800) | 1.0 | 11.0 | 12.6 | 16.2 | 2.4 / 3.0 | 212 (7) |
| Bare 5,000 W0 | 5,000 to 1,254 (800) | 5.5 | 31.4 | 36.1 | 47.0 | 13.3 / 16.3 | 149 (26) |
| Bare 10,000 W0 | 10,000 to 4,444 (800) | 33.6 | 89.0 | 107.9 | 128.6 | 79.6 / 100.1 | 14 (110) |
| Bare 2,500 W35 | 2,500 to 2,500 (800) | 14.8 | 107.6 | 160.8 | 189.6 | 17.8 / 44.5 | 65 (113) |
| Bare 5,000 W35 | 5,000 to 5,000 (800) | 43.0 | 103.6 | 739.3 | 789.0 | 53.5 / 120.7 | 25 (716) |
| Bare 10,000 W35 | 10,000 to 8,146 (800) | 87.9 | 140.6 | 736.4 | 769.3 | 123.6 / 170.8 | 25 (669) |

Where the time goes (phase timers, whole run; bare W0 and Siege shares are of total time):

| case | refresh_positions | ai_tick (all targeting, hits) | of which damage reduction | aura_regen | rest |
|---|---|---|---|---|---|
| Bare 10,000 W0 (300 steps) | 14.4 % | 85.3 % | 0.0 % | 0.1 % | 0.2 % |
| Bare 10,000 W35 (200 steps) | 10.2 % | 66.0 % | 14.1 % | 23.6 % | 0.2 % |
| Siege 4,996 (700 steps) | 14.2 % | 60.3 % | 49.7 % | 24.5 % | 0.9 % |
| Siege 990 (800 steps) | 5.5 % | 58.9 % | 38.5 % | 35.1 % | 0.4 % |
| Siege idle 4,996 | 19.2 % | 8.3 % | 0 | 68.9 % | 3.5 % |
| Siege idle 10,100 | 14.4 % | 5.4 % | 0 | 76.2 % | 4.0 % |

Median step per phase: Bare 10,000 W0 ai_tick 47.6 of 57.2 ms (instrumented run). Falling unit count does cut cost (Bare 10,000 W0 step goes 90 ms at the start to 28 ms at 4,400 left), so the worst step of a fight is its first contact, not its tail.

## Task 2: 990 units, the combat spike

Idle 990 (no hits): median 1.19, max 1.74 ms, no spike at all (round 1 removed it). Engaged 990 (Siege, gap 300, 800 steps): median 2.13, p95 19.6, max 21.3 ms; worst step 22.4 ms ai_tick of which 21.5 ms damage reduction; 143,139 calls over the run. So the "10 to 20 ms combat spike" is real and is entirely damage reduction (two scans per hit: Warden count within 300, then a Fortify scan within 350 that is walked in full whenever no active Bastion is near, which is nearly always). The splash path (ALG-61, `om_unit_damage_reduction` per candidate in an AoE) multiplies the calls: 32k in one step at 4,996.

## Task 3: aura regen at 4,996

See finding 3. Why: for each of N_w Wardens, one grid circle query that visits all units in the covered cells (about 3x3 cells of 400 wu) and filters by faction and radius afterwards. Cost is N_w x units-per-circle, linear in N while the density is bounded; measured 2.66 ms at 2,501, 6.83 at 4,996, 15.2 at 10,100 (exponents 1.38 then 1.19). The iterator cost is the row load per candidate (cache miss per candidate), not the arithmetic.

## Task 4: proposal

Both changes are inside `csrc/unit.c` (owner of the file; no header change, no `signatures.toml` change, no contract change).

**A. Aura regen over cell-sorted flat arrays.** At the start of `om_tactical_apply_aura_regen`, counting-sort the linked living units by grid cell into flat arrays (x, y, faction, index). A Warden's circle is then one contiguous run per cell row: `[cstart[row*cols+cx0], cstart[row*cols+cx1+1])`, scanned with `count += (faction == wf) & (dx*dx+dy*dy <= r*r)`. Same candidate set as the iterator (same `om_grid_coord` cell range with the same pad, same `dist_le` expression, integer counts), no row load per candidate, vectorisable without changing results. The heal loop is untouched. The prototype mallocs six arrays per step; the real build keeps them in the grid struct (grown in `om_tac_reserve`).
Measured (prototype): aura phase 15.2 to about 1.3 ms at 10,100; whole step 21.6 to 7.4 ms median at 10,100 idle, 10.1 to 4.0 at 4,996, 4.17 to 1.73 at 2,501. Exponent unchanged (about 1.2 then 1.1); the constant falls about 10x. Expected at 10,000: 7.4 ms median (measured), worst 12.8.

**B. Damage-reduction scans over per-cell kind lists.** The grid keeps, besides the unit list per cell, a list of Wardens and a list of Bastions (maintained in `om_grid_link`/`om_grid_unlink`, the same sites that keep the per-cell faction counts, so rebuild, move, death and spawn are all covered). `om_warden_aura_reduction_for` and the Fortify scan walk only those lists (count and any-of are order free, so list order cannot matter). The prototype also tested a faction-filtered iterator for these scans: it gained nothing measurable alone, and is dropped from the patch by the lists.
Measured: engaged Siege 4,996: max 273 to 35 ms, p95 171 to 23, spike-step mean 169 to 29; Siege 2,501: max 104 to 23; Siege 990: max 21.3 to 4.2, median 2.13 to 0.96. Bare W35 at 10,000: max 769 to 309, p99 736 to 291, median 87.9 to 60.9.
What is left in those spikes I did not phase-time on the new build. The remaining option, a per-hit cache or per-tick snapshot of the Warden count per unit, is faster again but is NOT byte-identical: positions change inside `om_tactical_ai_tick` (`om_tac_step_toward` writes x and y mid-tick) and units die mid-tick, so a snapshot would count a Warden that has moved or died. It would need a ruling on the order semantics; I do not propose it.

**Determinism and equivalence (prototype, verified).**
- `tests/csim/test_E13_A99_tactical_equivalence.py`: 10 passed. `tests/csim/scale/test_scale_A99_tactical_equivalence.py` with OM_SCALE=1: 6 passed. Every recorded per-step hash unchanged.
- My own chained FNV over every unit's alive, x, y, hp bits plus the world checksum, every step, base build vs prototype, identical for: bare 800 per side with 3, 8, 15, 35 percent Wardens (600 steps, units and Wardens dying in the 3 and 8 cases), Siege 990 and Siege 4,996 engaged (700 and 300 steps).
- Strategic checksum trace, 500 ticks, seed 121, 80 regions, features 0 to 7: final 12966767929705903382, O0 body equal to O2 body (the header line differs only by the lib path). The tactical step is not in that trace; the tactical equivalence is the two test files and my chains above.
- 20 pre-existing failures in `-k "warden or aura or fortify or bastion or grid or E11 or E13 or damage_reduction"` (controls needing the debug lib, E11 S085 fights), identical list with and without the patch.

## E-13 budget comparison

Budget: 1,000 live units 3 ms, 10,000 live units 30 ms at 10 ticks/s; `assert_budget` divides by 1.35, so the bars are 2.22 ms and 22.2 ms. `test_scale_E13_siege_breaking.py` times idle, median, 41 steps after 3 warm-up (military 178 gives the 10,100 cap; "live" is `om_unit_alive` over all slots).

| case (idle, the test's case) | base median | base worst | prototype median | prototype worst | scaled bar |
|---|---|---|---|---|---|
| 10,100 live units, period 2 | 20.8 to 21.6 (test run 19.8) | 26.8 (500 steps) | 7.4 (300 steps) | 12.8 | 22.2 |
| 4,996 (no stated budget) | 10.1 | 13.9 | 4.0 | 6.9 | |
| 996 in the test (mine reads 1,027 at 17.6 by field index, a harness difference) | 1.74 (test) | 1.9 | not run | not run | 2.22 |

At 10,100 the base idle worst step (26.8 ms over 500 steps; 25.4 in the earlier measure) is over the scaled 22.2 ms bar, the median is under it. Engaged (not what the test times), base: Siege 4,996 worst 243 to 273 ms, bare lethal 10,000 median 33.6 ms and worst 128.6 ms (over the 22.2 median bar and over the 100 ms frame); prototype Siege 4,996 worst 35 ms, bare lethal 10,000 unchanged (34.5, worst 135.5), bare W35 10,000 median 60.9, worst 309.

Steady vs spike at 10,100 idle: no spike steps at all (0 of 497 over 1.5x the median). Base p95 24.5, p99 25.3, max 26.8; every 41-step window median 20.1 to 21.4, max 24.1 to 26.8, so a test of the worst step against 22.2 ms would fail on base in most windows and pass on the prototype (12.8).

## Could not measure or not done

- The tactical step at 10,100 units in an actual engaged Siege: the blocks did not engage in 700 steps (0 deaths), cause not examined. Bare mixes stand in for it; they are denser than the Siege and are not the Siege composition.
- Prototype numbers for the lethal bare case (target search): unchanged by design, not worked on.
- No phase timer on the prototype build; the residual spike (29 ms mean at 4,996) is not attributed.
- No Windows or macOS run; no -O0 timing; noise from other processes on the box (load about 4) not controlled; each configuration run once (earlier repeats in A91 agreed to about 3 percent).
- `perf` blocked, gprof self-time shares are approximate under -O2 inlining.
- The prototype's per-step malloc and the missing positive control for the Warden-death case in the committed A99 tests (my chains cover it, the committed hashes mostly do not: Siege fights lose few units) are for the build unit. A kept chain test for Warden death and Bastion Fortify would close it.
