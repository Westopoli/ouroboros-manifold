# Movement / targeting / firing: architecture and structural fragility (read-only, main 53c25f5b)

All citations are file:line in /home/westopoli/Projects/ouroboros-manifold/csrc at that commit. "Unverified" marks anything read but not run. Prior report: docs/reports/2026-11-07-stage4-rerun-investigation.md (its findings are confirmed from the code, not re-run).

## 0. Shape of the system in one page

Three files own the question "where is a unit, may it be here, may it see/shoot":

- `tactical_move.c` (3985 lines): owns the live position (`om_move_unit.x/y`, plus a collision grid copy `slot_x/slot_y`), orders (`has_dest`, `dest`, `order_kind`, `group_id`, `engaged`, `kiting`), routing, steering, walker stepping, collision, layers, and `om_combat_can_shoot` (fire geometry).
- `unit.c` (3521): owns the unit row (`om_unit_row`: a CACHED `x,y`, `layer`, `target_id`, `order`, `order_x/y`, `issued_x/y`, `halted`, `am_gid`, `am_engaged`, `anchor_*`, `fire_pending`, `backswing_*`), target acquisition/keeping (`om_tac_unit_ai` 2086-2342), the fire pass (2346-2369), and the step (2405-2435).
- `fog.c` (1280): owns sight (`om_unit_can_see`, `om_fog_faction_sees`, `om_fog_grid_blocks` 353-387, `om_fog_cover_blocks` 311-329).

Per-step order (unit.c:2405-2435), the important fact: `om_tactical_ai_tick` (2423) decides on positions P_c; `om_ability_advance_all` (2426) does `current_tick++` (unit.c:1674); then `om_tac_fire_pass` (2427) starts with `om_tac_refresh_positions` -> `om_unit_get_pos` -> `om_move_sync` (tactical_move.c:2713), which runs the movement for tick c+1 NOW, using the orders/`engaged` flags the AI just set, and only then decides and lands shots on P_{c+1}. So: decide on P_c, move, shoot on P_{c+1}. This is intended (comment unit.c:2344 "the Python's order") and is the structural reason a unit can walk and fire in the same tick (see 2).

Behaviour is also switchable by three parameters, default all ON (tactical_move.c:400-404): PURSUE_BY_STEERING, ROUTE_AROUND_TERRAIN, TARGET_BY_SIGHT (plus LEASH_BEFORE_DAMAGE default 0). 13 sites carry "PP baseline only (switch = 0) / old path kept" (unit.c 8, tactical_move.c 4, fog.c 1). The lab's stage-1 floor sets TARGET_BY_SIGHT 0 on purpose (scripts/skilllab/arena/run.py:178). `om_fog_grid_blocks` returns 0 and `om_move_leave_blocked` is skipped (non-walkers) when ROUTE_AROUND_TERRAIN is 0 (fog.c:360, tactical_move.c:2412). So "rules can be broken" is partly designed in: each rule family is a runtime switch, and an invariant only holds in the switch configuration that enables its enforcing code.

## 1. POSITION WRITES

Four copies of a unit's position exist: `om_move_unit.x/y` (source of truth), the collision-grid slot `slot_x/slot_y` (read via `om_move_grid_x`, written by collision and copied back at tactical_move.c:1936-1937), the unit.c row `x/y` (cache, pushed in `om_move_push_positions` 2698 / `om_tac_unit_sync_position` unit.c:912, pulled in `om_tac_refresh_positions` unit.c:1901), and unit.c's own spatial grid (`om_grid_move`).

Guards: CL = canvas clamp (`om_move_clamp_axis`), CELL = blocked-cell check of the unit's layer, PUSH = stationary/collision rules, LAY = layer-aware, DISC = obstacle discs.

| # | Site (file:line) | Writes | CL | CELL | Other | Notes |
|---|---|---|---|---|---|---|
| 1 | steer step, `om_move_steer_step` tactical_move.c:2231-2236 | mu->x,y | yes | only `if (route)` via `om_move_terrain_guard` 2148 (slide one axis else stay, drops plan) | LAY (unit layer) | The ONLY step writer with the E-13 guard. Cells only, no DISC. |
| 2 | walker step, `om_move_walker_step` 2356-2357 (snap to aim), 2370-2371 (advance) | mu->x,y | no (goal clamped at 2308; route points are cell centres) | NONE. Relies on `om_walk_route` having avoided blocked cells | slope speed only | Lab units are walkers. The router cannot see mapgen boxes (walk_route.c:3 "no terrain = all open"). Root of the box-entry defect. |
| 3 | kiting move 2422-2428 | mu->x,y | no | none | backswing via effective_speed | Used by attack-target in range (unit.c:2291). |
| 4 | PP baseline move 2495-2503 | mu->x,y | no | none | | switch 0 only; dead in default config, still compiled. |
| 5 | `om_move_leave_blocked` 2138-2139 (R-207-06) | mu->x,y | no | repair only: nearest open cell, at least `ms->radius` inside it | walker-aware (`cell_blocked_for`) | Runs at the START of the unit's tick (2412) only if walker or ROUTE on. It is the repair for the missing guard in 2/3/4; it moves a unit up to a cell (about 15-100 wu), producing the saw-tooth. Uses global `ms->radius`, not per-unit radius; ignores DISC. |
| 6 | collision pair `om_move_collide_pair` 1688-1751 -> `om_move_grid_set`; copied back 1936-1937 | slot -> mu->x,y | if col_pursue | slide (`om_move_slide` 1678) only if `(col_route && !col_open)` or the unit is a walker (and only in the non-exact-overlap branch for non-walkers) | PUSH (stationary takes 0, 1688-1740), same start-layer only (`col_pursue`) | Slide checks CELL (walker: walk mask) AND DISC. Exact-overlap branch (R-097-07) is clamped but not slid for non-walkers (1702-1707 then 1743 only slides walkers). A slid-back mover can stay overlapping (no recheck). |
| 7 | `om_unit_set_pos` 3273-3288 | mu->x,y, prev, pushed, row | no | no | none | Public contract function (ouroboros_sim.h:2004). Used by unit.c `om_tac_step_toward` and by tests. |
| 8 | `om_unit_teleport` 3301-3317 | same | no | no | `layer` arg ignored (`(void)layer`) | Public contract. |
| 9 | `om_tac_step_toward` unit.c:1914-1930 (flinch 2149; baseline seen-step 2336) | row->x,y then `om_unit_set_pos` | no | no | speed via effective_speed | Flinch walks 200 wu away (unit.c:2026-2033) with NO clamp and NO cell/disc check: can leave the map or enter a box. Writes the row first, then pushes to the move side (reverse direction to every other writer). Reachable in play (idle unit hit by something it cannot reach). |
| 10 | `om_unit_spawn_internal` unit.c:949-955 | row->x,y | no | only walker + terrain present (`walkable_at`, 930-941) | | Non-walkers, and walkers when no terrain is generated, can spawn in a box or off-canvas. Duplicate of the check in mission.c:3133 (comment "FU-spawn-terrain-check-shared"). Callers: mission.c 2504/2512/2518, enemy_macro.c:981, tactical_support.c:877, unit.c:2689, fog.c:802. |
| 11 | `om_move_touch` first touch 1155-1156 | mu->x,y from row | - | - | | Lazy init: the move row is created by whichever getter touches the unit first. |
| 12 | `om_tac_unit_sync_position` unit.c:916-917, `om_tac_refresh_positions` 1907 | row cache | - | - | | Mirrors only; no guard needed, but they are what makes copies 1-4 desyncable. |
| 13 | save load tactical_move.c:3879, unit.c `om_unit_sr_row` | mu/row | no | no | format check only | Load can place a unit anywhere. |
| 14 | `om_tac_unit_set_layer` unit.c:923 (layer, not xy) | row->layer | - | - | called from `om_move_layer_unit` 2619 and `om_move_walker_tick` 3480 | A layer change re-evaluates which cells are "blocked" for the unit with no recheck of the unit's cell on the new layer (the transfer code checks `cell_blocked(lay_to)` before beginning, 2610, but not at the cross-over write 2619). Unverified whether reachable. |

Reading: of 8 position-changing sites inside the movement tick (1-6, plus 9 and 5), exactly one (steer step) prevents entry to a blocked cell, one (leave_blocked) repairs after the fact, one (collision) slides. The walker, which is what every lab unit is, is guarded only by repair (5) and slide (6). The E-13 invariant "A unit never enters a blocked cell" (E-13 line 215) has no single enforcement site.

## 2. STATE MACHINE

### 2.1 Stored state (what the decision uses)

unit.c row: `order` (NONE/ATTACK_MOVE/ATTACK_TARGET), `order_x/y`, `issued_x/y`, `halted`, `am_gid`, `am_engaged`, `anchor_set` (0/1/2 tri-state), `anchor_x/y`, `target_id`, `guard`, `flinching`, `fire_pending` (0/1/2), `fired`, `fired_tick`, `cooldown`, `backswing_ticks_remaining`, `backswing_active`, `last_attacker`.
move row: `has_dest`, `dest_x/y`, `order_kind` (0 move, 1 attack-move queued, 2 kiting), `group_id`, `speed_cap`, `engaged`, `kiting`, `direct_move`, `plan_valid`, `route_*`, `lay_*`.

### 2.2 Duplicated / derivable / desyncable

- `halted` (unit.c) vs `engaged` (move): both set together in `om_tac_hold` (unit.c:1935-1940: `om_unit_engage` sets mu->engaged, then u->halted=1). They are cleared in different places: `halted=0` by `om_tac_release`, `om_tac_chase`, `om_tac_drop_orders` (unit.c:2064-2072, which does NOT clear mu->engaged), `om_tac_end_pursuit`; `engaged=0` by every move command (tactical_move.c:1957, 2844, 2864, 2930, 2962), `om_unit_clear_orders` 3145, `om_tac_move_resume` 3529. Each unit.c path that clears halted relies on a following move-side call to clear engaged. `om_tac_hold` early-returns when `halted` is already 1, so if engaged was cleared elsewhere while halted stayed 1 the unit would walk while the AI believes it is held (and the reverse: drop_orders then no move command leaves engaged=1, i.e. a frozen unit). Whether either is reachable today is unverified; the structure permits both.
- `am_engaged` (unit.c:252): written at 1939 and 2070, saved (3242, 3372) and hashed, NEVER READ. Dead state in the checksum.
- `order` (unit.c) vs `order_kind` (move): two copies of "what is this unit doing". `om_tac_unit_ai` reconciles them each tick by comparing floats: a player order is recognised as "the route has a dest unit.c did not issue": `dest_x != issued_x` (unit.c:2114), `kind == 1` (2107), `kind == 2` (2115). Detection by float equality of two stored copies of a destination. A player move to exactly the issued point is invisible.
- Destination memory exists three times: move `dest_x/y`, unit `issued_x/y`, unit `order_x/y`. "Pursuing" is derived as `issued != order` (`om_tac_pursuing` 1964-1967). The current mode is an implicit combination of {order, halted, anchor_set, am_gid, guard, flinching, issued==order, target_id!=0, has_dest}. About 9 fields encode what is really about 8 modes (idle, plain move, attack-move walking, attack-move held, pursuing, returning (anchor_set 2), kiting/attack-target, flinching, guard). Transitions are spread across one 260-line function with 12 early/late exits plus `om_tac_hold/release/chase/return/end_pursuit` helpers.
- Position: 4 copies (section 1). Fire geometry reads the row cache (`om_unit_position_x`, tactical_move.c:2802-2805); sight reads the move row via `om_unit_get_pos` (fog.c:389-391). They agree only because `om_move_push_positions` runs at the end of each sync and `om_tac_refresh_positions` before decisions.
- Layer: row `layer` is the truth, but the move side keeps `plan_layer`, `lay_state`, `transit_home`.

### 2.3 Where one rule's outcome depends on another system's per-tick answer

1. Hold/release flips with geometry: unit.c:2301-2310. `in_range` (row geometry) and `om_combat_can_shoot` (move.c, grid walk) decide hold (`engaged=1`) versus release (`engaged=0`, walk the goal). Any per-tick change in the target's position or the unit's own cell changes the answer next tick. Nothing damps it (no hysteresis, no minimum hold).
2. Decide-then-move-then-fire (see section 0): the release/hold is decided at P_c; `fire_pending=1` is set whenever a target exists (unit.c:2314-2315); `om_tac_fire_pass` (2346-2369) re-tests only `in_range`, cooldown and `can_shoot` at P_{c+1} (2356-2358). It never tests `halted`/`engaged`/"did I move this tick". So a unit released at c (can_shoot false) walks one step in c+1 and, if the line has cleared at P_{c+1}, fires in that same tick. Ground truth for "walks while shooting" in the stage-4 L-0039 trace (Vanguard 1: 92 move ticks, every one with can_shoot false at decision time, a shot every 24 ticks). The bible states "halts and fires" (R-087-04) but no rule or code says "does not fire in a tick it moved". Unverified by run; derived from reading plus the prior report's trace.
3. Backswing is enforced inconsistently. `om_unit_effective_speed` returns 0 while `backswing_active` (unit.c:2836-2842), and every ungrouped mover uses it (`om_move_member_pace` tactical_move.c:2164-2169, kiting 2420). But a GROUP member returns `mu->speed_cap` (2168, 2491) which was frozen at order time, so grouped units ignore backswing (R-084-04, ALG-60) and also ignore Vanguard Brace "immobile" (unit.c:2849-2850) and Fortify speed multiplier. Attack-moves of two or more units are groups (E-13 R-096-02). Likely real for any grouped unit released after a shot; unverified by run.
4. Backswing set in two places: `om_tactical_apply_hit` sets `OM_BACKSWING_TICKS` and active=1 (unit.c:1043-1044); `om_tac_fire_pass` then overwrites with `OM_BACKSWING_TICKS - 1` (2367); AoE and `om_unit_deal_damage` set it again (2832-2833, 2907-2908). Value is a one-off-by-one depending on path. Duplicate writes of one rule's state.
5. Target keep/drop vs sight: `drop` when `!om_tac_may_act_on` (unit.c:2213), tested EVERY tick; re-acquire only on the unit's cohort tick (every 4th: 2242-2244). A target whose sight flips every tick (unit in/out of a cell) is dropped and re-acquired with 0-3 ticks of no target, so hold/release toggles. That is the bounce/untarget-retarget the prior report proved.
6. `fire_pending` three-valued scratch (0/1/2) is written in the AI pass and consumed in the fire pass inside one step; stored and saved/hashed though always 0 between steps.
7. Acquisition never asks fire geometry: `om_tac_nearest_actable` (2058) filters on the SIDE's visible set (`om_tac_may_act_on` -> `om_tac_faction_sees`: any friendly sees it, unit.c:1181-1197) and range. Whether THIS shooter has a clear line is first asked at hold/release (2302) and at fire (2358). R-087-09 (drop within 1 s) would join them and is unbuilt.

## 3. INVARIANT TABLE

"Enforced at": code site(s). "Test": whether a test cites the id (grep of tests/csim and tests/skilllab for the rule id; absence means no test cites the id, not that none exists).

| Invariant (source) | Enforced at | Verdict |
|---|---|---|
| A unit never enters a blocked cell (E-13 Invariants line 215; ALG-67) | steer step guard only (2233, route on). Walker 2296, kiting 2414, flinch unit.c:1914, spawn, set_pos, teleport: none. Collision: slide if walker or col_route (1678). Repair: `leave_blocked` | SEVERAL, INCONSISTENT. Violated by walkers every tick of pressing (proven by prior report). |
| A unit found in a blocked cell is moved out (R-207-06) | `om_move_leave_blocked` 2127, called 2412 (walker or ROUTE on) | One site; works but is a repair that fights the missing guard each tick. No test cites R-207-06. |
| Position clamped to map, push slid along cells (R-207-07) | steer 2231, collision 1706/1722 (col_pursue), slide 1678 | SEVERAL. Not on walker, kiting, flinch, baseline. No test cites R-207-07. |
| Stationary unit never pushed by a mover; two stationary split (R-097-10, E-13 line 213) | `om_move_collide_pair` 1709-1740 via `ms->stat[]` computed once per pass (1915-1917) | ONE site. Tests: 6 files cite it. Note `stat` is `engaged || !has_dest` (1201-1206): depends on the engaged flag staying in step with `halted`. |
| No two same-layer units within 30 wu after the pass (R-097-05, E-13 line 212) | collision loop; ends at pass cap | Best effort, documented exception. A slide-back mover (1678-1685) can stay overlapping. |
| Halt to fire: walk toward target until in range, then halt and fire (R-087-04) | unit.c:2299-2310 (hold/release), 2300 chase | Hold exists; fire (2346-2369) does not require hold. The "do not fire while moving" half is nowhere. Violated by the release-then-fire path (2.3 item 2). |
| Movement pauses 0.5 s after a shot (R-084-04, ALG-60) | `om_unit_effective_speed` zero in backswing (unit.c:2840) via ungrouped pace (2167), kiting (2420) | Several paths; skipped for group members (2168, 2491). |
| Nearest target (R-087-03) | `om_tac_nearest_actable` / `nearest_visible` (unit.c:2037-2062), cohort tick only | One site, but only re-evaluated when `target_id == 0` or most-damaged policy or pursue-out-of-range (2243); "an engaged target still alive and in range is kept" matches. |
| Target must be in the side's visible set (R-093-02, R-008-04) | `om_tac_may_act_on` at acquisition (1228-1262 pick paths), keep (2213), fire: NOT in fire_pass (2356) | Acquire and keep: one predicate, called from several places; fire relies on the keep. Tested (10 files). |
| Blocked line of fire blocks the shot "exactly as vision" (R-098-02) | fire: `om_combat_can_shoot` 2789; sight: `om_fog_can_see_at` 753 | TWO implementations that disagree (section 4). Tests cite it but on the shared cases. |
| Standing inside cover: seen and fired at as normal (R-007-06, R-098-02 tail) | sight: endpoint cells skipped (fog.c:379) and endpoint discs skipped (fog.c:320). Fire: discs skipped (tactical_move.c:2779); CELLS NOT skipped (`om_move_los_clear` 1355-1380 tests start and end cell) | Half enforced. The exemption for cells exists on sight and not fire. |
| Blocked fire line -> steer around, drop in 1 s (R-087-09) | none | NONE (ruled, unbuilt; no test). |
| Guard steps toward target within 200 wu (R-096-08) | none (comment unit.c:2163 says never walks) | NONE; bible contradicts itself (prior report). |
| Plain move never acquires (R-096-01, E-13 line 216) | unit.c:2137-2143 early return | One site. |
| Same seed + commands -> same trace (E-13 line 214) | design + checksum goldens | Tests only (golden/net checksum). |
| 1,000-unit move+collision < 3 ms | perf tests | Tests only. |

Nothing at runtime checks any of these. There is no `assert`, no violation counter, no "invariant" symbol in csrc (grep). The only runtime check macros are `OM_DEBUG_INJECT` positive controls in agent.c, events.c, fog.c:831.

## 4. SAME-CLASS DEFECTS (sibling path lacks the guard, or two systems answer one geometric question differently)

Geometric question 1: "may a unit stand here?"
- Steer guard 2148: cells (mapgen OR density) of unit layer, no discs. `leave_blocked` 2127: cells via walk-aware test, no discs, global radius. Collision slide 1678: cells (walk-aware) PLUS discs. Spawn: only walkers with terrain. Router (walk_route.c): walk mask only, no mapgen cells. `om_move_walk_blocked` (1276) uses the terrain walk mask ONLY once terrain is present, so a mapgen box is invisible to a walker's blocked-cell tests in a terrain world (falls back to mapgen only with no terrain, 1278). Meanwhile `om_move_cell_blocked` (1270, used by fire/LOS and non-walkers) is mapgen+density and ignores the walk mask. So in a terrain world boxes block shots but not walkers; in a terrain-free world (the lab) the walker's slide/leave_blocked test works but the router and `walker_step` do not use it. Five definitions of "blocked" for one concept.

Geometric question 2: "can A see B / can A shoot B" (fog.c vs tactical_move.c)
- Endpoint cells: sight skips both (fog.c:379), fire tests both (1371/`om_move_los_clear` start cell loop top). PROVEN by the prior report (114,212 of 115,416 pairs seen, can_shoot 0).
- Corner touches: sight clips each 100 wu column and treats a segment only touching a corner as NOT blocking (fog.c:347-349); fire uses a supercover walk where a pure corner crossing needs both side cells open (tactical_move.c:1349, 1375-1377). Opposite policies on diagonal lines past a box corner.
- Canvas edge: fire uses `om_move_cell_at` which clamps the last cell for coordinates at the canvas edge (1343-1351); sight uses raw floor (`om_fog_cell_floor`), so a unit at x == canvas_w is in an off-canvas cell (blocked per `om_mapgen_cell_blocked` 267) for sight but exempt as an endpoint there.
- Ground band: sight skips cells whose band is above the line's low layer (fog.c:380-382); fire's los_clear has no such skip (the terrain sight test `om_terrain_sight_blocks` runs separately in both, fog.c:779, tactical_move.c:2815).
- Obstacle discs: fire samples every 1 wu and returns 0 on `obstacle_density > threshold` even with ROUTE on (2825); sight has no obstacle test at all (no "obstacle" token in fog.c). A disc blocks fire and not sight (and the bible says exactly as vision).
- Cover: `om_combat_cover_blocks` (tactical_move.c:2772) is a hand copy of `om_fog_cover_blocks` (fog.c:311); the comment says "must agree" (fog.c:310) with no mechanism. Same for the three copies of LOS stepping (fog column clip, fire supercover, 1-wu sampler).
- Observer set: sight for targeting is the SIDE's union (R-093-02: `om_tac_faction_sees` unit.c:1181); fire is the shooter's own line. By design a target can be "seen" and unshootable; today nothing resolves that except the unbuilt R-087-09. So acquisition-keep-fire are three different predicates (side-sees+range / side-sees+range+leash / range+own line+cooldown).
- Which positions: sight reads move rows via `om_unit_get_pos` (calls sync); fire reads the row cache (`om_unit_position_x`).

Geometric question 3: "which tick's positions?"
- AI decides at P_c, shot at P_{c+1} (section 2.3 item 2).
- `om_tac_step_toward` (flinch) moves the row and the move side inside the AI loop, so units later in the loop observe the post-flinch position and earlier units observe pre-flinch. Order-dependent within a tick (deterministic but asymmetric).

Guard on one path, absent on its sibling:
- Steer step has `terrain_guard` + canvas clamp; walker step (same function family, the one the lab uses) has neither.
- Kiting move (same file) has no clamp or guard; steer/collision do.
- `leave_blocked` runs only if `walker || ROUTE on`; collision slide only if `col_route && !col_open` or walker; so a non-walker with ROUTE off is unprotected end to end (that is the switch-0 baseline, by design).
- Group members honour speed cap but not backswing/Brace (2.3 item 3); ungrouped honour both.
- Spawn duplicates the terrain refusal in unit.c:934-941 and mission.c:3133, and non-walkers have none.
- Flinch (unit.c:2145-2153) ignores every position guard.
- The `unit.c` getters `om_unit_get_*` in tactical_move.c each call `om_move_sync` and `om_move_touch`; touching can CREATE move state (`om_move_touch` 1148) and syncing runs movement. A read can therefore advance the simulation (by design: lazy catch-up, but any new diagnostic that reads through these functions can perturb checksums; `om_move_route_get` 2383 documents the exception pattern: use `om_move_get`).

Smaller notes: leave_blocked and the router both resolve ties by cell id, fine; `om_tac_chase` re-issues a move every time the target's xy changes (unit.c:1981), forcing a replan per target step (perf, not correctness).

## 5. DESIGN OPTIONS TO FAIL LOUDER

Constraints respected below: no change to ouroboros_sim.h/signatures.toml/pipe frames unless stated; new code in new files; wiring its own last commit; no fast-math / no wall-clock; read-only checks must not touch `om_move_touch`/`om_move_sync` (use `om_move_get`-style raw reads) or they change the checksum. Westley owns every tolerance.

### O1. Lab-side per-tick invariant checker (Python, no C change). RECOMMENDED FIRST.
What: new `scripts/skilllab/invariants.py`, called from the lab tick loop right after `step(w)` (scripts/skilllab/fight.py:355-360, beside `record()`; engine.py already binds `om_unit_get_pos` 121, `om_combat_can_shoot` 132, `om_unit_can_see` 133, `om_navmesh_is_cell_blocked` is a public symbol at tactical_move.c:3045). Each check names its rule id and returns a `Violation(rule, tick, unit_ids, xy, switch_state)`:
- INV-E13-cell (R-207-06, E-13): no live unit's end-of-tick cell is blocked on its layer.
- INV-R207-07: x,y inside canvas.
- INV-R087-04-fire-while-moving: a unit with a FIRE event this tick has |P_{c+1} - P_c| = 0 (needs per-tick position diff, available from the same loop). Whether this is a rule is Westley's call: the bible says "halts and fires"; record as a flagged check with its own id so he can enable it.
- INV-ALG60-backswing: no displacement in the 10 ticks after a FIRE event.
- INV-R087-09-unshootable: a held target with can_shoot false for more than the DRAFT 20 ticks.
- INV-R098-02-sight-fire: for pairs with `can_see` true and in range, `can_shoot` true unless a documented exemption (this is the existing test `..._sight_fire_agree.py` made continuous).
- INV-R097-10 no stationary displacement (position changes of a unit with engaged=1 and no dest).
Run policy: on any trip the FightResult carries `invariants=[...]` and `tainted=True`; the batch/pool/page code (scripts/skilllab/batches.py, pool.py, page) refuses to aggregate or rank a tainted fight and stamps the page "INVALID: R-207-06 at tick 1503 unit 14". Conditional invariants are tagged with the switch they depend on (ROUTE_AROUND_TERRAIN, TARGET_BY_SIGHT) and reported as "suspended: sight off" rather than silently passing, so a control arm cannot masquerade as a clean run.
Cost: small. About 300-400 lines Python + tests; the six `test_stage4bug_*` files (docs/reports/2026-11-07 list) already contain these predicates and become the checker's unit tests. Runtime: one ctypes call per unit per tick for position (already done by `record()`), one `is_cell_blocked` per unit per tick, `can_shoot` only for units with a target. At 256 v 256 and 12k ticks that is millions of ctypes calls; mitigate with per-tick check only for units whose cell index changed, and `can_shoot` only on FIRE events. Estimated 10-30% lab slowdown (unmeasured).
Risk: zero determinism risk, zero contract change. Weakness: sees only end-of-tick state (a unit that enters and is ejected next tick is seen at the end of the entering tick, which is what we want); it detects, it does not prevent; and it re-derives geometry in Python, so the cell test must call the engine's own `om_navmesh_is_cell_blocked`, not re-implement it.
Value: answers Westley's "cannot contaminate lab data" directly and is the oracle that makes O3/O4 safe.

### O2. C-side invariant checker in a new file, read-only, behind a build flag/runtime param
What: `csrc/invariants.c` (new), `om_inv_check(w)` called once at the end of `om_tactical_step` (one-line wiring commit in unit.c, last). Reads move rows with `om_move_get` (no touch/sync), compares each unit's cell with `om_move_cell_blocked`, plus fire-while-moving using `fired_tick` and `prev_x/prev_y` (already stored, tactical_move.c:2407), engaged/halted agreement, row-vs-move position agreement (catches desync of copies), canvas bounds. Violations go to a small ring in new state (not saved, not hashed, so no checksum or save-format change) with an internal getter declared in om_internal.h next to `om_move_route_get` (precedent: tactical_move.c:2378). `OM_INVARIANT_MODE`: 0 off, 1 log, 2 abort (assert with rule id in message) selected by compile flag like `OM_DEBUG_INJECT`.
Cost: medium. 400-600 lines C, build and golden tests; per-tick O(N). It can see mid-step state (after movement, before fire) which O1 cannot, and catches row/move desync. Needs `signatures.toml`/header only if the getter must be public to ctypes; internal symbols are already callable from the lab through ctypes, so no contract story if kept internal.
Risk: must be strictly read-only or checksums change (the `om_unit_*` public getters are not read-only). Determinism safe if the ring is excluded from save/checksum. Mode 2 (abort) is only for tests/nightly, never the shipped game.

### O3. One position-commit function with the guard inside (the class fix at the writer end)
What: in tactical_move.c, introduce `static void om_move_commit(om_world*, om_move_state*, om_move_unit*, double nx, double ny, int why)` and route sites 1, 2, 3, 4, 5, 6 through it (and make `om_tac_step_toward` call a move-side function instead of writing the row). It does the canvas clamp (R-207-07), the blocked-cell check for the unit's layer using the unit's own definition (walker mask vs cells, unified into one `om_move_blocked_for(unit, cell)` replacing the five variants in section 4), slide-else-stay, and in strict mode records a violation with `why` (STEER, WALK, KITE, PUSH, EJECT, TELEPORT). `set_pos`/`teleport`/spawn pass `why=EXPLICIT` and are only checked/logged, not refused (contract behaviour unchanged).
Cost: high. Behaviour change: every walker now stops at a box face instead of entering it, so every trace that touched a box changes: goldens re-record (ledger rows), Westley owns it. The guard alone will make the pressing visible and permanent (units pile on the face) unless walker routing knows mapgen boxes (a separate engine item in the prior report). Hot path: one cell read per mover per tick; budget is 3 ms/1000 units, so measure.
Risk: medium-high (touches the hot path and all goldens). Do it after O1 gives a regression oracle. It is the only option that removes the class rather than detecting it.

### O4. One engage query instead of three predicates
What: define one function, `om_combat_line_state(w, a, b)` (new file `csrc/combat_line.c`, internal header), that is the ONLY LOS walk for sight and fire (replaces fog.c grid walk, `om_move_los_clear`, `om_combat_cover_blocks`, and the 1-wu sampler) with one named endpoint-cell policy and one corner policy, returning {blocked_by_cell, blocked_by_cover, blocked_by_disc, blocked_by_ground, endpoint_exempt}. Sight = range test + that; fire = range test + that + own-line. Then compute once per unit per tick `shootable(u->target)` in the AI pass and store it on the row; `fire_pass` consumes the stored answer (and, to close 2.3 item 2, requires `!moved_this_tick || halted` or defers the shot one tick). hold/release (unit.c:2301) and fire (2356) then cannot disagree.
Cost: high and spans fog.c, tactical_move.c, unit.c: it changes sight and fire results on every map with boxes, ground, or cover (re-records, Westley decides the endpoint policy: R-007-06 vs "boxes block exactly their cells" is his open ruling per the prior report). Needs a new row field `shootable_tick` (save format bump, hashed) or recompute-only.
Risk: high; do only after the endpoint ruling and O1. Pays down sight/fire disagreement permanently.

### O5. Make the gating switches explicit and shrink them
Delete the 13 baseline-only branches already scheduled for deletion at end of Phase E (A140) and refuse switch values 0 for PURSUE/ROUTE in non-lab builds; keep TARGET_BY_SIGHT 0 only as a named lab arm and make the artifact print the switch state beside every invariant. Cost: medium, golden re-record. Risk: medium. Reduces "rules designed to be breakable" to one deliberate lab control.

### O6. Small structural cleanups that make desync impossible (cheap, but each changes save/checksum so batch them)
Delete `am_engaged` (dead, hashed); derive `halted` from `mu->engaged` (one accessor) so hold/release is one flag; replace `issued != dest` player-order detection with an explicit "order generation" counter set by commands. Cost: low-medium each; save format bump and checksum pins re-record. Risk: low, but each is a contract-adjacent change story.

### Recommendation and order
1. O1 (+ taint-and-reject in the lab batch path). No C, no determinism risk, turns the six existing red tests into a standing gate, and from the first run shows how many of the 14 sites in section 1 actually trip. Make the checker the acceptance oracle for everything below.
2. O2 in a later story if the Python cost is too high or Westley wants mid-step visibility and an abort mode in nightly. Optional.
3. Westley's rulings (endpoint exemption, whether fire-while-moving is a rule, R-087-09 in scope, walker routing around boxes) then O3 (single commit point) plus the walker-routing item as one cascade, then O4.
4. O5/O6 as cleanup stories after O3/O4 so the goldens are re-recorded once.
A small patch (a terrain_guard call in `om_move_walker_step`) would fix the proven symptom but leave sites 3, 4, 9, 10 unguarded, leave sight/fire disagreeing, and would likely turn the saw-tooth into units pressed flat against faces (the router still cannot see boxes), contaminating lab data differently. O1 makes that visible instead of arguable.

## 6. What I did not verify
- Everything is read from source; nothing was compiled or run. The decide-then-move-then-fire ordering (section 0, 2.3 item 2) is from reading `om_tactical_step`, `om_ability_advance_all` and `om_move_sync`; a one-unit trace test would confirm it in minutes.
- Group backswing bypass (2.3 item 3) and the `halted`/`engaged` desync (2.2) are structural readings, not shown reachable.
- Whether `om_map_add_obstacle` discs also set mapgen cell bits (which would make some disc/cell disagreements vanish) was not checked.
- Layer cross-over cell recheck (section 1 row 14) not checked.
- No test cites R-207-06, R-207-07 or R-087-09 by id; other tests (test_PP_move_route.py, test_VG_D_*.py) may cover the behaviour under different ids.
