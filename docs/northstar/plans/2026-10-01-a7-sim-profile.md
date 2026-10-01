# A7 sim and serialise profile at 5,000 units

Profile and report only. No csrc edit, nothing tuned (round 1 A7 ruling). Base: origin/main 1e0421d (A7 delta frame and player-only `visible` already landed), `-O2` with the repo determinism flags, 16-core box, 2026-10-01.

## How measured

- `perf` is blocked, valgrind is absent. Two scratch instruments, both outside the repo (scratchpad, never committed):
  - gprof: `-pg` build of every `csrc/*.c` plus `csrc/pipe/om_pipe.c` (main renamed) linked with a C harness into one binary. Run twice, `-O2 -pg` and `-O2 -pg -fno-inline` (the second so small helpers get their own rows). Call counts are exact; times are sampled and inflated about 1.45x by instrumentation (8.2 s for 200 steps, against 28 ms per step unprofiled), so read the percentages, not the seconds.
  - `clock_gettime` around each phase call inside `om_tactical_step`, in a scratch copy of `unit.c`. These are the unprofiled numbers in the tables below.
- Harness drives the same setup as `scripts/bench_tactical_pipe.py` (seed 1, 80 regions, mission begun, 572 baseline units, N extra units spawned by the same xorshift stream, `spread` and `clash` layouts). 200 steps per run. Serialise path = `write_tactical(0)` (delta) and `write_tactical(1)` (full) called in-process, output to /dev/null.
- Cross-check: the real pipe bench (`bench_tactical_pipe.py 5000 100 clash`) on current main gives roundtrip median 57.0 / p95 71.4 ms, sim 27.9, serialise+io 29.0, `visible` 18.2. The harness agrees (sim 27.6, delta frame 22.7, visible 17.3). Spread: roundtrip 16.1 / p95 27.5 (the A7 delta frame took spread from 36 to 16 ms).
- Caveat: the serialise gprof run (`flat/graph_*_2`) has no sim steps, so unit positions are the initial clash layout, not mid-fight. Visible cost in that state matched the stepped harness (17.9 vs 17.3 ms), so it is representative.

## Time per step per phase (ms, in-process, unprofiled, medians; mean and max for the spiky one)

5,000 extra units (5,572 in the world):

| phase | spread med | clash med | clash mean | clash max |
|---|---|---|---|---|
| `om_tac_refresh_positions` (incl. grid rebuild) | 0.16 | 0.16 | 0.20 | 0.77 |
| `om_tactical_ai_tick` | 1.70 | 15.06 | 15.06 | 31.9 |
| `om_tactical_apply_aura_regen` | 0.64 | 2.15 | 2.25 | 3.94 |
| `om_tactical_advance_backswing` | 0.02 | 0.01 | 0.03 | 0.22 |
| `om_ability_advance_all` (autotrigger scan) | 0.40 | 8.38 | 9.48 | 20.8 |
| `om_macro_tick` | 0.00 | 0.00 | 0.77 | 37.1 |
| `om_support_tick` | 0.00 | 0.00 | 0.00 | 0.01 |
| `om_mission_tactical_tick` | 1.23 | 1.83 | 1.96 | 6.0 |
| step total | 4.4 | 27.6 | 29.8 | 65.0 (p95 41.3) |

Serialise path, same worlds:

| frame | spread | clash |
|---|---|---|
| delta frame (`write_tactical(0)`), median | 8.7 | 22.7 |
| of which `visible[]` (`om_player_can_see_unit` over every id) | 2.1 | 17.3 |
| delta frame without `visible` (JSON, accessors, diff) | 6.6 | 5.4 |
| full frame (every 20th step), median | 16.2 | 29.6 |

Macro spike: `om_macro_tick` is zero on 19 steps in 20 and 18 to 42 ms on the 20th (1,000 units 18 ms, 2,500 units 25 to 35 ms, 5,000 units 37 to 42 ms, both layouts). It is the step max and sets the sim p95 in spread scenes.

## Scaling with unit count (ms, medians; units = world count)

| extra units (world) | layout | sim step | `ai_tick` | autotrigger | delta frame | `visible[]` | full frame |
|---|---|---|---|---|---|---|---|
| 1,000 (1,572) | spread | 2.1 | 0.95 | 0.32 | 3.7 | 0.56 | 6.0 |
| 1,000 (1,572) | clash | 3.5 | 1.77 | 0.65 | 4.9 | 1.16 | 6.4 |
| 2,500 (3,072) | spread | 2.8 | 1.25 | 0.27 | 5.2 | 0.97 | 9.2 |
| 2,500 (3,072) | clash | 10.6 | 6.18 | 2.14 | 9.9 | 5.03 | 12.9 |
| 5,000 (5,572) | spread | 4.4 | 1.70 | 0.40 | 8.7 | 2.12 | 16.2 |
| 5,000 (5,572) | clash | 27.6 | 15.06 | 8.38 | 22.7 | 17.26 | 29.6 |

Fitted exponents in world units, 1,572 to 5,572 (3.5x units): spread sim about n^0.6 (fixed overhead dominates), spread visible n^0.9, clash sim n^1.6, clash visible n^2.1.

Is any hotspot O(n^2)? Yes, in contact-dense scenes, for three separate reasons, all the same shape: one spatial query per unit, where the number of candidates per query is proportional to local density, and the clash blobs sit in a fixed area so density scales with n.

1. `om_fog_faction_sees` (the `visible[]` loop): clash visible time grows n^2.1. Counts at 5,000: 2,935 fog queries per frame, about 663 grid candidates walked per query (780M `om_grid_iter_next` calls over 401 frames), mostly rejected on the faction test afterwards. The query radius is `om_fog_world_bound` (max sensor 1,000 times slack), so each query touches every unit of either faction within about 1,000 units, whereas it only wants own-faction observers.
2. Nearest-hostile and in-range scans (`om_tac_nearest_hostile`, `om_tac_nearest_enemy_within_range`, `om_tac_hostile_within`, `om_tac_enemy_within_range`): per step about 2,360 `nearest_hostile` calls with a sensor-radius circle (700 to 1,000 units), each scanning about 24 grid cells and about 50 units per cell. Clash ai_tick plus autotrigger grow n^1.6.
3. `om_macro_issue_group_orders` contact test: literal all-pairs `om_unit_can_see(force x player)`, capped at 2,048 x 2,048 = 4.2M calls, every 20 steps (the spike above). It only exits early when contact is found.

`om_tac_refresh_positions` and the grid rebuild (0.16 ms at 5,000) are linear. `tactical_move.c` collision/avoidance is not a top cost: `om_move_tick_once` 6.3% of the profiled step (`om_move_collision_pass_internal` 4.3%, `om_move_grid_rebuild` 0.6 ms), dominated by the same grid walk and not quadratic in this scene. Target selection is the `nearest_hostile` family above.

## Ranked functions: sim step (gprof `-pg -fno-inline`, clash 5,000, 200 steps, share of total profiled time)

Inclusive:

| # | function | inclusive | calls | note |
|---|---|---|---|---|
| 1 | `om_tactical_step` | 97.3% | 200 | whole step |
| 2 | `om_tactical_ai_tick` / `om_tac_unit_ai` | 43.5% | 200 / 1.10M | 5,524 units per step |
| 3 | `om_grid_iter_next` (all callers) | 36.9% | 243M | the circle-query iterator |
| 4 | `om_tac_nearest_scan_cell` | 33.6% | 11.2M | per-cell scan inside nearest_hostile |
| 5 | `om_ability_advance_all` / `om_ability_autotrigger_scan` | 28.3% | 200 | runs for every unit every step |
| 6 | `om_tac_nearest_hostile` | 24.5% | 472k | called from ai_tick (target selection) |
| 7 | `om_tac_nearest_enemy_within_range` | 17.8% | 111k | called from autotrigger |
| 8 | `om_tac_hostile_within` | 13.6% | 357k | called from ai_tick |
| 9 | `om_grid_rebuild` | 10.1% | 201 | incl. refresh_positions; 0.16 ms unprofiled, inflated here |
| 10 | `om_macro_tick` | 9.9% | 200 | 10 evaluations, all the time in the macro spike |

Self:

| # | function | self | calls |
|---|---|---|---|
| 1 | `om_grid_iter_next` | 27.4% | 243M |
| 2 | `om_tac_nearest_scan_cell` | 26.1% | 11.2M |
| 3 | `om_tac_dist_le` | 17.2% | 810M |
| 4 | `om_tac_enemy_in_cell` | 3.4% | 1.5M |
| 5 | `om_grid_cell_gap2` | 1.7% | 9.9M |
| 6 | `om_tac_reserve` | 1.7% | 268M |
| 7 | `om_registry_find_in` | 1.7% | 24.7M |
| 8 | `om_move_near_mask` (tactical_move.c) | 1.6% | 5.0M |
| 9 | `om_tac_hostile_within` | 1.5% | 357k |
| 10 | `om_tac_nearest_enemy_within_range` | 1.2% | 111k |

About 71% of self time is three functions, all circle-query candidate walking. Not a fog or movement problem.

## Ranked functions: pipe serialise path (same method, 401 frames of `write_tactical`)

Inclusive:

| # | function | inclusive | calls |
|---|---|---|---|
| 1 | `write_tactical` | 92.0% | 401 |
| 2 | `om_fog_faction_sees` (from `om_player_can_see_unit`, the `visible[]` loop) | 91.5% | 1.18M |
| 3 | `om_grid_iter_next` | 71.2% | 780M |
| 4 | `om_tac_dist_le` | 24.2% | 1.22G |
| 5 | `om_unit_get_faction` | 11.4% | 795M |
| 6 | `om_unit_can_see` | 6.4% | 5.5M |
| 7 | `om_unit_get_pos` | 5.0% | 25M |
| 8 | `om_registry_find_in` | 4.4% | 835M |
| 9 | `om_fog_effective_radius` | 2.0% | 5.5M |
| 10 | `jb_putc` (JSON writing) | 1.6% | 101M |

Self top 10: `om_grid_iter_next` 47.0%, `om_tac_dist_le` 24.2%, `om_unit_get_faction` 5.0%, `om_registry_find_in` 4.4%, `om_tac_ro` 2.5%, `om_move_touch` 2.3%, `om_fog_faction_sees` 2.2%, `jb_reserve` 1.2%, `om_ms` 1.0%, then `om_unit_get_pos`. JSON writing proper (`jb_*` rows) totals under 5% of the serialise path in this scene, matching the in-process split: delta frame body without `visible[]` is 5.4 ms against 17.3 ms for `visible[]`. `om_tac_refresh_positions` is not in the serialise path.

Serialise is therefore 76% fog (clash delta frame) and nearly all of that is walking candidates that are the wrong faction.

## One negative experiment (scratch, not committed)

Cell size is not the lever. Changing `OM_GRID_CELL_SIZE` 400 to 200 and 100 in a scratch copy of the constants header, clash 5,000: step medians 29.4 / 27.0 / 31.6 ms, `visible[]` 17.9 / 17.7 / 21.1 ms. The unit-position hash after 200 steps was identical across all three (`563520dd80915e21`), so the cell size does not alter this scene's trace either, but it buys nothing: the cost is the number of units inside the query radius, not cell overhead. Do not spend a piece on grid retuning.

## Candidate fixes (not implemented; savings are estimates from the counts above, not prototypes)

None of these may change the trace. Each must pass `scripts/specfactory/checksum_trace.py` and the existing csim tests before landing. Rough savings are for clash at 5,000.

| # | fix | owning file / piece | saves (est.) | changes trace? |
|---|---|---|---|---|
| 1 | Per-faction observer search for `om_fog_faction_sees`: link the queried faction's units into their own grid (or a per-faction index in fog.c) so the query never walks enemy rows, and drop `om_unit_get_faction` from the inner loop. Optionally try seen-likely observers first (nearest cell first). Halves candidates at 2 factions; ring-ordered search cuts more for visible targets. | `csrc/fog.c`, piece B11 (needs a read-only per-faction accessor from `unit.c`, B10; a new piece must claim both files in turn, one owner at a time) | `visible[]` 17 to about 6 to 9 ms | No. `om_fog_faction_sees` is an any-of, the answer does not depend on visit order; `visible` frame content identical |
| 2 | Order cells nearest-first in `om_tac_nearest_hostile`, and skip same-faction rows by walking an enemy-only index (or at least test faction before `dist_le`). The existing gap2 prune only bites after a best is found and the own cell is first, then row-major; nearest-ring order prunes most of the 24 cells in the clash front and almost all for rear units. The same applies to `om_tac_nearest_enemy_within_range` in the autotrigger scan | `csrc/unit.c`, pieces B10/B10b/B10c (all list `unit.c`) | ai_tick 15 to about 9 to 11, autotrigger 8.4 to about 4 to 6: sim step 27.6 to about 18 to 21 ms | No, if (d2, id) tie-break and the `OM_TIE_SCAN_WINDOW` fallback to `om_tac_nearest_hostile_ordered` are kept: result is order-independent by construction. Prove with the trace checksum |
| 3 | `om_macro_issue_group_orders`: skip the force x player `om_unit_can_see` loop when `f->has_contact` is already set (the result `contact_now` only feeds the sticky `has_contact`, already true), and in the no-contact case search nearest candidate instead of all pairs | `csrc/enemy_macro.c`, piece B13 | removes the 18 to 42 ms spike every 20th step (sim p95 in spread and in clash) | No: `has_contact` is already 1 so the OR is unchanged. The no-contact search is any-of on a pure function |
| 4 | Autotrigger scan: skip units whose unit-type ability cannot fire (no autotrigger for that type) before any grid query; run threshold scans only on units whose hp changed | `csrc/unit.c`, B10 family | part of #2's autotrigger saving; unknown without reading `om_ability_autotrigger_scan` per type | No if the skipped units provably cannot trigger; otherwise yes. Needs the ability rules checked |
| 5 | Compute `visible[]` for changed units only (cache by tick, recompute dirty cells) | `csrc/fog.c` B11 and `csrc/pipe/om_pipe.c` T1 | on top of #1, little in a clash (everything moves); real in calm scenes | No for sim; pipe frame contract unchanged only if the full list is still sent |
| 6 | Pipe: write only the last frame for `tactical_step n>1` | `csrc/pipe/om_pipe.c` T1, contract in `docs/architecture.md` first | zero for n=1; helps catch-up bursts only | No sim effect; contract change |

## Budget conclusion: can 50 ms at 5,000 units in a clash be met by the top two fixes?

Current: roundtrip median 57 ms, p95 71 ms (pipe bench, current main). Sim 27.6 + serialise and IO 29, of which `visible[]` 17.3.

- Fix 1 alone: about 17 ms to 6 to 9 ms, so roundtrip median about 46 to 49 ms. Already near 50 and p95 about 60.
- Fixes 1 and 2 together (fog per-faction observers plus ordered nearest-hostile): roundtrip median roughly 57 minus 8 to 11 minus 6 to 9, so about 37 to 43 ms. The median meets 50 ms with 7 to 13 ms of margin on these estimates.
- p95 is not assured. Current p95 is 71 ms, 14 ms above the median, and the tail comes from the macro spike (37 ms every 20th step) and the full frame every 20th step (+7 ms), which fall on the same steps only by chance. With fixes 1 and 2 the estimated p95 is about 50 to 58 ms: borderline. Adding fix 3 (macro spike) is what makes p95 under 50 plausible; I would treat fixes 1, 2, 3 together as the set that meets 50 ms on median and probably p95.
- Not covered by any of these: client JSON parse (34 ms at 5,000 per the A7 measure report, runs on the reader thread) and the 10 calls per second the client already uses above 1,000 live units (100 ms budget, at which even today's p95 is over only by the tail). Westley's pending budget question (50 ms at 20 Hz or 100 ms at 10 Hz) still decides whether this work is needed for the median or only for the tail.
- Savings are estimated from call counts and the observed per-query candidate numbers; none was prototyped. The cell-size experiment above is the only thing actually run, and it showed no gain.

## Reproduce

Scratch harness lives in the session scratchpad only (`h.c`: includes `csrc/pipe/om_pipe.c` with `main` renamed, replays the bench setup, calls `om_tactical_step` and `write_tactical` N times; `unit.c` copy with `clock_gettime` around each phase call). Build: `cc -std=gnu11 -O2 -pg -fno-inline` plus the repo determinism flags over `h.c csrc/*.c -lm`; `gprof -b -p` and `-b -q` for flat and graph. Raw outputs not committed.

## Fix 3 re-measure (push/F3, B13-N)

`om_macro_issue_group_orders`: contact loop now skips once `has_contact` is set. Checksum final 12966767929705903382, O0 = O2 = main. Bench: `scripts/bench_tactical_pipe.py 5000 40`, pipe, ms.

| layout | metric | before (profile) | after |
|---|---|---|---|
| clash | roundtrip median / p95 | 57 / 71 | 59.7 / 67.2 |
| clash | sim step median / p95 | 27.6 / n.a. | 29.7 / 31.8 |
| spread | roundtrip median / p95 | n.a. | 16.4 / 27.6 |
| spread | sim step median / p95 | n.a. | 3.6 / 6.6 |

Step 20 sim spike: clash 69.9 ms, spread 45.6 ms (steps 1-19 about 20 and 2.5). Step 40 has no spike (clash 30.2, spread 4.6), so the recurring every-20th spike is gone; the first evaluation at step 20 still pays the full all-pairs scan because no contact is set yet (spread never gets contact). 50 ms budget: clash median and p95 both over (60 / 67); spread under. Fixes 1 and 2 still needed for clash. Clash steps after 20 run about 10 ms above steps 1-19 (more units in range after the clash starts), not macro.
