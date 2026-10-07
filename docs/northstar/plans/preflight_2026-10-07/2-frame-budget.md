# Pre-flight scout 2-frame-budget (2026-10-07, Sonnet, read-only)

Scout 2 results, seed 3 (archetype 7, region 62, 343 units at begin: 166 player, 177 enemy). The worktree is removed and `~/Projects/ouroboros-manifold` was not touched. The scripts are in `/tmp/pf-vg2/` (`measure.py`, `shim.c`, `gd/*.gd`).

**Method.** Pipe driven through an LD_PRELOAD shim lifted from `scripts/bench_tactical_pipe.py`. It spawns extra units; 100 units means the extras killed down with `om_unit_set_hp`. Medians over 95 to 100 steps, `nice -n 10`, box load 1.4 to 4. "Godot" is `godot.real --headless`, `JSON.new().parse` on the captured text (the `c_bridge.gd` path). "Py" is `json.loads`, a lower bound. Command: `measure.py N spread|clash idle|move|fight 100 1 pipe/ouroboros_pipe out`.

**Q1. Frame size and parse (full / delta)**

| Units in frame | Scenario | Full frame | Delta (median bytes, units changed) | Godot parse full / delta | Py parse |
|---|---|---|---|---|---|
| 100 (150 by t=100, reinforcements) | move/fight | 23.8 KB | 23.7 KB, 150 changed | 0.63 / 0.59 ms | 0.28 ms |
| 500 (550 at capture) | idle | 80 KB | 38.6 KB, 243 changed | 2.30 / 1.29 ms | 1.1 / 0.6 ms |
| 500 | move or fight | 87 KB | 79 KB, about 500 changed | 2.4 to 2.5 / 2.5 ms | 1.2 ms |
| 2000 (2036) | idle | 330 KB | 124 KB, 712 changed | 9.5 / 3.1 ms | 5.3 / 2.1 ms |
| 2000 | move or fight | 326 to 332 KB | 310 to 332 KB, 1942 to 2048 changed | 9.3 to 9.9 / 8.7 to 9.4 ms | 5.0 to 5.4 ms |

- A unit object averages 155 B in steady state and 115 to 132 B at begin.
- 46% of that is x, y and facing printed at 17 digits.
- `tier` and `state` are 17 B of zeros per unit today.
- Godot parse costs about 29 µs/KB, 4.7 µs per unit, 0.43 µs per key. Number arrays cost about 50 ns each.
- Extra points: 1000 units gives 161 KB and 4.6 ms. 5000 units gives 818 KB and 24 to 28 ms.

**Q2. Full period and delta.**
- `OM_PIPE_FULL_PERIOD` is 20 (`om_pipe.c:79`). A full frame goes out when `steps/20` crosses a boundary (`:1690`), on `full:true`, on `n:0`, and on `mission_begin` and `snapshot`.
- The count is calls, not base ticks. That is every 1 s at 20 calls/s, and every 2 s above 1000 units, where each call spans 2 base ticks (10 calls/s).
- A delta carries only units whose id, faction, type, layer, target, x, y, hp or facing differ from the last frame written (`:1196` onward).
- Idle units are skipped, but any moving or fighting unit changes every tick. Delta is then 95 to 100% of a full frame: 332 KB against 332 KB at 2000 units moving.
- `visible` (5.8 KB at 1078 ids) and `objectives` are never diffed.
- `tier` and `state` are not in the changed test (the `tac_unit` struct lacks them). Real values mean extending it.
- Finding: `write_tactical` scans up to 1,000,000 unit slots every frame once any unit has died. Dead units stay `in_use` (nothing sets `in_use = 0`), so `n_ids < count` for the rest of the mission. Confirmed with a counter on a throwaway copy: `iterations=1000000` with 100 alive. The cost is about 2.8 ms per frame (serialise at 100 units with dead slots, 2.83 ms; at 343 with none, 0.11 ms). It is a free win to fix, but I did not touch it.

**Q4. The 50 ms budget (median; p95 in brackets)**

| Units | Pipe round trip (sim / serialise+io) | Godot parse + reconstruct | Real client `tactical_step_n(1)` | `load_frame` (view) |
|---|---|---|---|---|
| 343 idle (no deaths) | 0.34 (0.22 / 0.11) | n/a | 5.4 | n/a |
| 500 move | 4.96 [6.4] (1.2 / 3.8) | 2.5 + 0.2 | 10.8 [11.1] | 1.5 |
| 500 fight | 2.1 [2.8] (0.9 / 1.2) | 2.4 + 0.2 | 5.9 | 1.5 |
| 2000 move | 11.8 [15.1] (3.6 / 8.1) | 9.4 + 0.8 | 24.0 [29.3] | 6.6 |
| 2000 fight | 10.9 [13.3] (3.4 / 7.3) | 8.7 + 0.7 | 23.9 | 6.6 |
| 2000, n=2 per call, move | 13.4 (6.1 / 7.2) | n/a | 29.1 [34.5] | n/a |
| 5000 move | 21.1 [26.9] (6.9 / 14.2) | 23.6 + 2.3 | not run | not run |

- The real-client column comes from `c_bridge.gd` itself (`gd/bridge_bench.gd`). It sits on a 5 ms floor and rounds to multiples of 5 ms, because `tactical_step_n` polls with `OS.delay_msec(5)` on the main thread.
- At 2000 units the view calls 10 times a second, so the budget is 100 ms. Today's path is about 31 ms (24.0 plus 6.6 view), leaving about 70 ms. At 500 units it is 12 of 50 ms.
- The 5000-unit request-to-parsed time is about 46 to 56 ms. That meets the 100 ms line in `architecture.md` but misses the 50 ms line in the A7 test docstring. The two docs disagree.
- The tactical call blocks the main thread. At 2000 units that is a roughly 30 ms stall every 100 ms, which drops frames at 60 fps whatever the 50 ms budget says.
- The sim itself is cheap: 1 ms at 500 units, 3.5 ms at 2000. Cost scales with bytes: about 24 µs/KB to serialise, about 29 µs/KB to parse, about 52 µs/KB combined.

**Q3. Additions at 500 units, and recommended shape**

Sample size is what I measured where noted. The rest is my arithmetic from the measured per-unit and per-key costs.

| Addition | Bytes per frame at 500 units | Shape |
|---|---|---|
| Unit tier, ability state, layer-change progress | `tier` and `state` already ride the frame (+0). Three new keys on every unit is about +14 KB (+16%), +0.7 ms parse. Omitting defaults is about +1.4 KB. | Per tick, inside the unit object. Omit defaults. Send absolute ticks (`ability_ready_tick`, `layer_done_tick`) so the client derives progress. A 17-digit progress fraction would mark the unit changed every tick. Accessors exist: `om_unit_ability_active` and `om_unit_ability_cooldown` (`ouroboros_sim.h:2028-9`). |
| Structures (id, type, owner, x, y, hp, stage) | About 75 to 110 B each: 50 structures is 4 to 5 KB, 200 is 15 to 22 KB. Today's mission has 2 to 8 (`tactical_support.c:343`). | Full list in the periodic full frame. `structures_changed` and `structures_removed` in deltas, same rule as A7. Quiet deltas cost about 0. |
| Tactical events (shots, deaths) | Compact `[shooter,target,hit]` is about 14 B. Measured shots per step: 0.1 to 2 at 500 units. At 2000 units, mean 8, p95 31, peak 49. That is 0.1 to 0.7 KB, under 0.2% of the frame. | Per tick only, never diffed. Accumulate across `n>1` steps with tick stamps and a cap. Deaths are already in `units_removed`. The sim has no accessor today (`om_tac_fire`, `unit.c:1924`, is static), so this needs a small event ring in C. |
| Terrain height array, up to 280×280 | Hex uint16: 230 KB at 240², 314 KB at 280². A JSON float array is 370 to 503 KB. The existing `terrain_dump` is 235 KB at 240² (5.4 ms round trip). | Once per mission, as a `terrain_dump`-style verb. Sampling takes 0.7 ms in C (57,600 cells). Godot parse is 1.7 to 2.2 ms plus 0.5 to 0.7 ms hex decode. It must not go in `map`, which rides every full frame. The current limit is 24,000 wu (240²); 28,000 returns code -1. |
| Space-kit geometry | About 85 KB bit-packed hex (5 layers × 240², plus tunnels and crossings). About 590 KB at one byte per cell. Computed from the spec, not measured. | Once per mission. The 10 MB frame cap at `c_bridge.gd:595` is not an issue. |
| Workers | About 155 B per moving worker per tick, so 200 workers is +31 KB. | Ordinary units in the same lists, per tick. If workers pass about 300, send walk legs (start tick, destination) instead of positions. |
| Lots | About 70 B each: 20 to 100 lots is 1.4 to 7 KB. | Once per mission; changes as `lots_changed` in deltas. |
| Resources per side | About 60 B. | Every tick, or every N ticks. |

- Worst case at 500 units plus 200 workers, 200 structures and the per-unit fields comes to about 140 to 160 KB per frame. At 52 µs/KB that adds about 3.4 ms, so about 13 ms of 50.
- At 2000 units with the lot added, about 520 KB and about +10 ms, so about 41 ms of 100.
- It fits both budgets. The risk is main-thread stall, not the budget.
- Lever: rounding x and y to 0.1 and facing to 0.01 cuts a unit from 155 to 117 B (-24%). I did not test it for contract or test impact. Thresholds are Westley's.

**Q5. `qa_state()` cost**

| Units | `qa_state` | `JSON.stringify` | `QADaemon.state` verb | JSON size | `QADaemon.tree()` |
|---|---|---|---|---|---|
| 150 | 0.46 ms | 1.07 ms | 1.5 ms | 23 KB | 0.19 ms |
| 550 | 1.9 ms | 3.9 ms | 5.3 ms | 86 KB | 0.29 ms |
| 2035 | 6.8 ms | 14.6 ms | 20.8 ms | 327 KB | 0.87 ms |

- Measured with the real view loaded in headless Godot (`gd/qa_bench.gd`).
- Today `qa_state` reports (`tactical_view.gd:244`): scene, tick, canvas, scale, `unit_count`, a 9-field dict for every unit, `units_px` (visible units only), `local_faction`, `selected`, camera, `last_command` and `error_panel`. It has no HUD, fog, marker or structure inventory.
- The `units` dict is built from the unfiltered frame, so it includes units the player cannot see. A fog guard has to read `units_px` or add visible ids.
- `QADaemon.tree()` lists only visible `Control` and `Node3D` nodes (`qa_daemon.gd:301-320`). The unit shapes are `Polygon2D`, so no `Node2D` element (units, fog, rings, markers) can be seen by `tree()`.
- Recommendation: inventory as counts and presence flags per node class and group (under 2 KB, well under 1 ms). Keep per-unit detail behind a flag. It is fine once per story moment, but about 21 ms and 327 KB per call at 2000 units would hurt if polled every tick.

**Not measured or not exact**
- Actual render time.
- The Godot read loop sleeps 5 ms whenever `get_buffer` returns 0 bytes. That is included in the real-client column but not isolated.
- Structure, lot and space-kit sizes are estimates.
- Shot counts come from a counter patched into a copy of the sim in `/tmp/pf-vg2/patched`, not the repo.
