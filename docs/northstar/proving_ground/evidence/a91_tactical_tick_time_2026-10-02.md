# A91 tactical tick time on the Siege Breaking case, 2026-10-02

Measurement only. No csrc edits. Source tree: origin/main at 81e0c833, built in scratch worktree /home/westopoli/Projects/om-a91. Harness source: `docs/northstar/proving_ground/evidence/a91_tactical_tick_harness.c` (committed with this report; the profiling build is not).

## Result in one paragraph

Per `om_tactical_step`, release build, steady state (the median step): 1.07 ms at 502 units, 3.33 ms at 990, 14.6 ms at 2,501, 40.7 ms at 4,996. On top of that, one step in every 20 (every 40 base ticks) is a spike: 6.1, 21.4, 130.5 and 346 ms at the same four sizes. Spikes dominate p95 above 1,000 units and lift the mean to 1.14, 3.66, 20.2 and 55.2 ms. Growth is between linear and quadratic: a log-log fit gives a median exponent of about 1.6 (spikes about 1.8), and the exponent falls from 1.67 to 1.48 across the range. Against the E-13 scale requirement (1,000 units under 3 ms, 10,000 under 30 ms), the 990-unit median already misses (3.33 vs 3) and 5,000 units at 40.7 ms median already exceeds the 10,000-unit figure of 30 ms. The siege case from the A81 diagnosis is about 5,200 units in total (2,564 player + 2,638 enemy), not 2,564 + 217.

## Correction to the A81 diagnosis wording

The brief and the diagnosis say "2,564 player units + 217 enemy". Measured on the same mission (seed 121, 80 regions, features 0 to 7, step 10, Siege Breaking at region 0), the force is 2,564 player and 2,638 enemy units, 5,202 live in all. (217 is the player count of the cheap Evacuation mission on main.) So the diagnosis's 52 ms per tick belongs to about 5,200 units, which agrees with the 5,000-unit row below (mean 55 ms, median 41 ms). It is not a 2,781-unit case.

## How the unit count was controlled

A C harness linked to the release `libouroboros.so` (no pipe, no JSON), reproducing the pipe's `set_seed` then `mission_start` then `mission_begin` sequence:

1. `om_world_new(80, 121)`, features 0 to 7 on, `om_world_generate`, `om_events_load_launch`, `om_mission_load_launch_library`, `om_campaign_start(W, 1)`, 10 x `om_world_step`, `om_mission_refresh_context` on every region.
2. The Siege Breaking archetype (1) is forced at region 0 with `om_mission_setup(W, 0, 1, 0)` followed by `om_mission_begin`. With no override this gives exactly the diagnosis mission (2,564 + 2,638, enemy power 176,943).
3. Unit count is scaled by overwriting region 0's military with the hard-fixture setter `om_region_set` before `om_mission_setup` (tier, economy, tension, population, owner unchanged). Siege Breaking derives enemy power as military x 2000, and the player force is that times parity, so live units are about 58.5 per military point. Settings used: military 8.6 gives 502 units (245 player, 257 enemy), 17.0 gives 990 (483, 507), 42.8 gives 2,501 (1,225, 1,276), 85.0 gives 4,996 (2,461, 2,535).
4. 990 rather than exactly 1,000 for the third point, because 1,002 units switches the tactical period to 2 (R-099-03). A control run at 1,002 units (military 17.2) gave median 3.40 ms against 3.34 at 990, so the period switch does not change the cost of one `om_tactical_step` call.
5. Per size: 5 warm-up steps, then 200 timed `om_tactical_step` calls (CLOCK_MONOTONIC around each call), three repetitions. The three repetitions agree to within about 3 percent on the median and 1 percent on spike height.

A "tick" below means one `om_tactical_step` call, which is what `tactical_step n:1` runs in the pipe. Above 1,000 units one call advances base time by 2 ticks (10 ticks/s), so those calls are the 100 ms frame the budget is measured against.

## Build and machine

`make -j8` at the repo root (libouroboros.so): `cc -std=c11 -Wall -Wextra -Icsrc -fPIC -O2 -fno-fast-math -ffp-contract=off -fexcess-precision=standard -msse2 -mfpmath=sse -fno-math-errno -shared`. Harness `gcc -O2`. gcc 15.2.0, AMD Ryzen 7 3700X, Linux 7.0, one thread, other processes on the box not controlled.

## Numbers (ms per `om_tactical_step`, 200 steps, three repetitions shown as a range)

| live units | median | p95 | p99 | mean | max | non-spike p95 | spike (every 20th step) |
|---|---|---|---|---|---|---|---|
| 502 | 1.03 to 1.08 | 1.13 to 1.24 | 6.1 to 6.2 | 1.12 to 1.15 | 6.2 to 6.5 | 1.12 to 1.13 | 5.9 to 6.2 (5 of 200) |
| 990 | 3.31 to 3.34 | 3.55 to 4.10 | 21.3 to 22.3 | 3.64 to 3.68 | 21.8 to 23.1 | 3.4 to 3.5 | 21.3 to 22.1 (5 of 200) |
| 2,501 | 14.5 to 14.7 | 126 to 130 | 133 to 134 | 20.0 to 20.3 | 134 to 137 | 15.2 to 15.8 | 130 to 132 (10 of 200) |
| 4,996 | 40.3 to 40.8 | 329 to 335 | 345 to 355 | 55.1 to 55.4 | 346 to 364 | 41.4 to 41.8 | 344 to 349 (10 of 200) |
| 5,202 (the diagnosis mission, unscaled) | 43.2 to 43.5 | 345 to 358 | | | 360 to 374 | | |

Spike cadence: at or below 1,000 units 5 spikes in 200 steps (every 40 steps), above 1,000 units 10 in 200 (every 20 steps); both are every 40 base ticks, equal to `OM_SCRIPT_EVAL_INTERVAL_TICKS` (40, csrc/om_constants.h) which gates the enemy macro evaluation in `om_macro_tick` (csrc/enemy_macro.c). The profile below is consistent with that (om_macro_tick is 22 percent inclusive over a 205-step run, nearly all in om_unit_can_see), but I did not time the spike step on its own, so the attribution of the spike to the macro evaluation is inferred, not isolated.

No unit died in any run (live units after the run equal live units at start), so the numbers are for a static opening with no player commands, as in the pipe tests.

## Scaling shape (four points, using the median; mean and spike in brackets)

- Log-log slope over all four points: 1.58 (mean 1.71, spike 1.78).
- Pairwise exponents 502 to 990, 990 to 2,501, 2,501 to 4,996: 1.67, 1.59, 1.48 (mean 1.72, 1.84, 1.45; spike 1.85, 1.95, 1.41).
- Cost divided by n squared falls from 4.25 to 1.63 (x 1e-6 ms) for the median, so it is not a pure n squared; a straight line fits worse than a parabola (RMSE 1.68 ms against 0.17 ms for the median; the quadratic fit is -1.49 + 0.00433 n + 8.24e-07 n squared).
- Reading: super-linear, between n^1.5 and n^2, with the exponent drifting down at the top of the range. That is what a spatial-grid neighbour scan gives when cells fill and then the scan radius saturates the map. I did not test that explanation by varying the grid or radius; four points cannot distinguish n^1.5 from a quadratic with a large linear term.

## Profile (function shares)

gprof, a separate scratch build of all csrc/*.c plus the harness with the same flags and `-pg` (not committed), whole run of 205 steps (200 timed plus 5 warm-up, so spikes are included). Self time shares. gprof's attribution is approximate here because the build is -O2 with static functions inlined and sampling at 10 ms; treat shares as indicative to a few points.

| function (csrc/unit.c unless noted) | 2,501 units | 4,996 units |
|---|---|---|
| om_grid_iter_next | 45.7 percent (245 M calls) | 44.9 percent (642 M calls) |
| om_tac_nearest_scan_cell (line 1342) | 16.1 percent (3.9 M calls) | 18.8 percent (8.9 M calls) |
| om_tactical_step itself | 6.9 percent | 7.9 percent |
| om_unit_get_pos | 5.2 percent | 4.0 percent |
| om_move_sync | 3.7 percent | 2.9 percent |
| om_unit_can_see (via om_macro_tick) | 2.6 percent | 2.9 percent |
| om_fog_effective_radius | | 1.9 percent |
| om_tac_enemy_in_cell | | 2.3 percent |

Call counts rise 2.6 times for om_grid_iter_next and 2.3 times for the nearest scan when units double, against about 2.0 for linear, so the call volume itself is the super-linear part. Callers (from the call graph): om_tac_nearest_hostile calls om_tac_nearest_scan_cell (8.9 M calls over 615 K nearest queries, about 14.5 cells per query at 5,000 units); om_macro_tick calls om_unit_can_see 41.9 M times at 5,000 units (that is 4.2 M per spike step). The iterator's caller shows as om_tactical_step in the call graph; that is an inlining artefact and not evidence of who owns the loop.

Non-spike-only profile (19 steps, warm-up 0, too few samples to trust beyond rough order): om_grid_iter_next 57 percent at 2,501 and 66 percent at 5,000, om_tac_enemy_in_cell 13 and 10 percent, om_tac_nearest_scan_cell 9 percent at both. So the grid iterator dominates the steady step as well as the spike. This matches the diagnosis profile (45 percent and 19 percent).

## Against the E-13 budget

Source: docs/bible/epics/E-13-movement-and-command.md, section "Scale requirements" (no R- rule id; it is the section's own statement), "Confirmed by Westley, 2026-09-14 (never loosened by Agora; a miss is escalated): movement and collision for 1,000 units in under 3 ms per tick, 10,000 in under 30 ms; route queries under 1,000 per second at 60 wu cells. The 10,000-unit figure is measured at the 10 ticks/s rate the sim drops to above 1,000 live units (E-13 R-099-03), a 100 ms tick; the 1,000-unit figure at 20 ticks/s."

| units | budget | measured median | measured mean | measured worst step |
|---|---|---|---|---|
| 990 | under 3 ms (20 ticks/s) | 3.33 ms | 3.66 ms | 22 ms |
| 5,000 | none stated (10,000 units: under 30 ms; a straight line between the two stated points would give about 15 ms) | 40.7 ms | 55.2 ms | 346 ms |
| 10,000 | under 30 ms | not measured | | |

What the numbers imply, and no more: at 990 units the median is 11 percent over the 3 ms figure and the 20th-step spike is 7 times it. At 5,000 units the median is already above the 10,000-unit figure (30 ms) and the spike (346 ms) is over three times the 100 ms frame. At 2,501 units the median (14.6 ms) is inside a 100 ms frame but the spike (130 ms) is not.

## What I could not measure or that differs from the budget's wording

- **Scope of the budget versus the measurement.** The budget says "movement and collision". I timed the whole `om_tactical_step` (movement, collision, targeting, fog, enemy macro AI, mission tick). I did not time movement and collision alone, so the table above is an upper bound for the budgeted subset. The profile suggests the grid and nearest-hostile scan (targeting) dominate, which is outside "movement and collision" strictly read; whether that scan counts against the budget is a ruling, not something I decided.
- **10,000 units.** Not run (the brief asked 500 to 5,000). Siege Breaking at military 170 would give about 10,000 units; I did not run it.
- **Moving or fighting units.** All runs are the opening formation with no player commands and no casualties, as in the pipe tests. Cost in a live fight (units moving, dying, targets changing) is not measured.
- **Pipe path.** Timings exclude the pipe's JSON frame writing (`write_tactical`) and the GDScript client. The 52 ms diagnosis figure was measured through the pipe, so it includes serialization; this harness number for the same mission (mean 55 ms, median 43 ms) is close, which suggests serialization is a small part, but I did not measure it separately.
- **Spike attribution.** Timed per step, but the spike step was not profiled on its own; the link to the 40-tick macro evaluation rests on cadence and on the call graph.
- **perf.** `perf` is installed but blocked here (no access to performance counters or cpu-clock without privileges), so the profile is gprof, not perf.
- **Noise.** One machine, one thread, background load not controlled; repetitions agree to about 3 percent.
