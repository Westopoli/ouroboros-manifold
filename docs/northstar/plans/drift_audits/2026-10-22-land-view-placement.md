# Land view placement and facing, measured 2026-10-22 (Westley's live look at F-S140)

Line numbers in the client report for `tactical_view.gd` are offset by the probe's 43 added lines; the corrected cites are in the spec and ledger.

Westley played the land era live (OM_GODOT_GUI=1, greek placeholder, seed 1) and reported marks displaced from bodies, marks sliding against the camera, a facing arrow pointing backwards, invisible obstacles, unnamed grey lines and a uniform grey-blue backdrop; two Sonnet investigators measured the client (xvfb 1920x1080, origin/main bd814657) and the sim; their reports follow verbatim; the rulings are in `story_reviews/westley/decisions.md` (DEC-landview-one-projection, DEC-facing-travel, DEC-Q087-02, DEC-single-giveup) and the pieces in the visible-game spec.

## Client report

# Land view investigation (worktree inv-landview, xvfb 1920x1080, greek_placeholder seed default, 176 units in probe, 10 own measured)
Probe: temporary qa_state "probe" key + verbs probe_cam/probe_move/probe_vis (tactical_view.gd, qa_daemon.gd; thrown away). Scripts /tmp/probe_landview.py, /tmp/probe2.py, /tmp/probe3.py; logs /tmp/inv_landview/run*.log; shots /tmp/inv_landview/{lv_default,lv_pan600,lv_h300,lv_h300pan,lv_facing,a_default,b_no2d_except_terrainlayer,c_nofog}.png.
Runner note: pytest is absent from system python; I ran the driver with ~/Projects/ouroboros-manifold/.venv/bin/python (read only use).

## Corrections to the static read (verify)
- UnitVisuals/UnitSquads do use the flat formula (unit_visuals.gd:62-63, unit_squads.gd:47), BUT in the ground era UnitVisuals nodes are re-placed every frame by _apply_motion (tactical_view.gd:977-993) with `_to_screen` = ground projection (:1307-1311). Measured: UnitVisuals.position == units_px == projected 3D body, 0.0 px at all three cameras. That override only holds when `_live_stepped` and the unit is in UnitMotion; _redraw() alone (e.g. a pan) re-sets the flat position until the next _process.
- UnitSquads is the one mark that stays on the flat formula and is not hidden: `_hide_2d_units()` (:322-336, hides squads, Body, LayerRing) runs only under `if _space_hosted` (:1378), and _space_hosted is set only by _host_space_view (:308). Ground era never sets it, so the 2D bodies, layer rings and squads ALL draw on top of the 3D bodies.
- The marks Westley sees (teal chevron stacks, yellow rings) are those 2D nodes, not the 3D bodies: 3D body radius 11.5 wu (ground_units.gd:17) is about 2 px at scale 0.18.

## Part 1 inventory (world->screen; projector?; facing; pinning test)
| node | file:line | mapping | projector | facing | pinned by |
|---|---|---|---|---|---|
| Ground3D (SubViewportContainer z=-1, fixed 1920x1080) | ground3d.gd:36-42 | 3D mesh, Camera3D | is the projector (to_screen :133, projection.gd:11) | n/a | test_vg_c5_ground3d_host.gd (host) |
| ground_mesh | ground_mesh.gd:28-37 | 3D mesh, band vertex colours | n/a | n/a | test_vg_c2_ground_mesh.gd |
| ground_units (3D darts) | ground_units.gd:83-84 | 3D placement at height | n/a | rotation.y=-facing, 3D frame | test_vg_c6_ground_units.gd (3D positions only) |
| slope_view | slope_view.gd:35-43 | 3D white BoxMesh bars (length=slope length, 2x4 wu) = the THICK white bars; circles for transit | n/a | bar yaw | test_vg_c7_slope_view.gd |
| ground_lod | ground_lod.gd | not instantiated by ground3d.gd or tactical_view.gd (grep empty) | - | - | test_vg_c8_ground_lod.gd |
| TerrainLayer (_ground_layer, 2D, still added at :355-357 in ground era) | terrain_layer.gd:60-67 | flat formula, texture + 2px white tick lines = THIN white lines | no, never gets set_projector | n/a | test_tactical_terrain_layer.gd |
| MapLayer (cover discs, obstacle discs, red boundary) | map_layer.gd:28-31 | projector | yes (:1322-1326) | n/a | test_vg_c10_map_layer.gd (two mock projectors) |
| ObjectiveMarkers, FogLayer, LayerView, Shots | tactical_view.gd:1322-1326 | projector | yes | n/a | test_vg_c10_*.gd |
| UnitVisuals (2D Body, LayerRing, HpBar) | unit_visuals.gd:62-63, :190; position overwritten :991 | flat in set_frame, projected after _apply_motion | no (position copied from _display_px) | Body.rotation = facing + facing_offset_rad (:~182), screen 2D | test_vg_a_unit_visuals.gd |
| UnitSquads | unit_squads.gd:47-49 | flat formula | no | facing + offset, screen 2D | test_vg_a_unit_squads.gd |
| StructuresLayer, Deaths, Abilities, Ambient | tactical_view.gd:1385-1392 | called with flat scale/camera (not in set_projector list); not measured | no | - | their test_vg_a_* |
| HUD panels, Clock, Selection | tactical_view.gd:178-196 | screen px | n/a | n/a | test_vg_a_* |
Grey lines: thick = SlopesView bars (3D, white); thin horizontal/diagonal = TerrainLayer slope ticks (2D, white, flat formula, 2 px). Seen in lv_default.png (horizontal thin lines, left) and lv_h300.png (diagonal group).

## Part 2 measured (10 own units; px distance min / median / max)
| pair | default h3000 | pan600 | h300 | h300 pan600 |
|---|---|---|---|---|
| UnitVisuals vs units_px | 0/0/0 | 0/0/0 | 0/0/0 | 0/0/0 |
| 3D body projected vs units_px | 0/0/0 | 0/0/0 | 0/0/0 | 0/0/0 |
| flat formula vs units_px | 75.6/78.6/268.2 | 77.0/80.2/281.3 | 3464/4502/5714 | 4006/5377/6837 |
| UnitSquads centre vs units_px (2 squad units) | 263/266/268 | 275/278/281 | 3464/3509/3554 | 4006/4064/4121 |
Ground height under units: 1711 to 1979 wu (so the flat formula ignores up to 270 wu of relief spread).
Slide for a pan of 600 wu in x (px moved per unit): default units_px -70.1 to -114.1 (0.12 to 0.19 px/wu), flat/squads -107.8 each (0.180). h300: units_px -169 to -2337 (med -3.44 px/wu), flat/squads -1078 (1.797). Squads move at one constant rate while bodies move at 13 different rates, so against the camera the squads drift 38 to 1259 px at default and h300.
Facing (facing_offset_rad, assets/eras/greek_placeholder/manifest.json:12-37: raider pi, bombard -pi/2, rest 0): unit at facing 0 (type 0 raider, id 1): 3D nose on screen -20.7 deg, 2D icon 180 deg = pointing the other way. Bombard (type 4): 3D nose -0.3 deg, 2D icon 270 deg (90 off). Type 1 id 15 moved 10 wu at world 9.8 deg, facing -0.3: travel on screen -15.6, 3D nose -17.6, 2D icon 359.7 (the 2D icon ignores perspective, 3D nose follows it). 3D body_rot_y = -facing exactly (test run: 0.810 vs -0.810). Facing +/-: for non-offset types 3D and 2D agree to within perspective; for raider (the type of unit 1, a squad type, count 4) and bombard the drawn 2D dart is backwards or sideways. Type 3 warden 3D nose read 140 deg at facing 0: projection on a steep slope, not a rotation fault. Picture: lv_facing.png (one 40 tick order; the unit went the other way round an obstacle: moved (-375,+30) towards target (13520,2714)).

## Part 3 backdrop and obstacles
- Ground mesh IS drawn under xvfb (lv_h300.png: orange band 3 under units, magenta steep tint, pink peak; lv_default.png lower half brown/orange). Dominant colour under the units at h300: orange-brown (about 0.75,0.5,0.35).
- The "uniform grey-blue" is FogLayer: top 300 px of the default shot are (48,64,80) dominant with fog; with FogLayer hidden they are (128,160,208) = SKY_COLOUR (ground3d.gd:17) (c_nofog.png). Fog is black alpha 0.55 outside sight (fog_layer.gd:5, :19-20); whole void above the map and the unseen mesh get dimmed.
- Real seat differences in code: window/size/mode=3, stretch canvas_items, aspect expand (project.godot:47-49); Ground3D fixed SCREEN_SIZE 1920x1080 and `stretch = true` container (ground3d.gd:36-42, 21); rendering driver d3d12 only set for windows (project.godot:61). Nothing in code makes the mesh skip drawing; I did not test a real seat.
- Blocked cells: the only draw is the mesh tint (GroundBands.STEEP_MIX 0.5 magenta, ground_bands.gd:3-4, applied ground_mesh.gd:17) and MapLayer obstacle discs (color 0.35,0.3,0.3,0.8, map_layer.gd:10; flat-ground discs in the projector). slope_view `_blocked` is stored (slope_view.gd:45-48) and counted in qa_state but nothing draws it. At h300 the discs and tint are the only marks; the magenta is visible at the horizon only (lv_h300.png).
- Stalls measured (probe3): ordered +600 x. Unit 15 moved 10 wu then 0 for 180 ticks (12390,952), 590 short; unit 16 stopped at 12850 y1050, 130 short, facing -26 deg. Cause not measured (no blocked cell overlay to compare).

## Part 4 why tests were green
- test_vg_a_unit_visuals.gd:192 `n10.position.distance_to(_scr(Vector2(1000, 1500))) < 0.5` with _scr = flat formula (:84-85): compares the node to its own formula; cannot catch a flat mark on perspective ground.
- test_vg_a_unit_squads.gd:183-193 asserts model count and offsets only; no position or projection at all.
- test_vg_c6_ground_units.gd: 3D node positions/heights only; says nothing about 2D marks.
- test_vg_c10_map_layer.gd (and fog/markers/shots c10): mock projectors, would catch a flat formula on that node but only for pieces given set_projector.
- test_vg_d_view.gd:1089 `got2.distance_to(want2) <= ONE_PX` pins units_px to cam.unproject_position: real projection, but only under the space era (_space_hosted); it never reads UnitVisuals or Squads.
- tests/qa/desktop/test_tactical_play.py:88-92 asserts units_px lie inside the canvas: cannot detect a displaced mark.
- No test places the 2D UnitVisuals/UnitSquads nodes against the 3D body in the ground era, nor checks `_hide_2d_units` runs there; no test asserts facing_offset_rad vs 3D nose.

## Sim report

# inv/simfacing report (Sonnet investigator, 2026-10-22; measured on origin/main bd814657, `make` clean, probes were throwaway pytest files, deleted)

Setup caveat: the mission-ground fixture (`test_E01_T3_mission_ground._scene`) spawns 301 own units on a 24000 wu map and walkers I added to it never ticked, so I did NOT use it. I used the terrain-only ground world the T2 tests use (`om_terrain_generate`, walking kind, `PURSUE_BY_STEERING` on = the default, tactical_move.c:382, abilities off, one Vanguard). "Home anchor" therefore = a stand-in (see 3). Not the greek placeholder mission seed 1.

## 1. Facing vs velocity (terrain seed 1, 12000 canvas, start (2000,2000), goal 2000 wu away, 60 ticks)
| order | tick | facing | displacement heading (last 5 ticks) | diff |
|---|---|---|---|---|
| +x | 10 / 30 / 60 | -0.4 / -1.2 / -1.6 deg | 18.4 / 18.4 / 2.0 deg | -18.8 / -19.6 / -3.6 |
| +y | 10 / 30 / 60 | 90.8 / 92.6 / 95.4 | 45.0 / 45.0 / 45.0 | +45.8 / +47.6 / +50.4 |
| diag 45 | 10 / 30 / 60 | 45.5 / 46.6 / 47.1 | 18.4 / 18.4 / 40.9 | +27.1 / +28.1 / +6.1 |
Meaning: `facing` is the heading to the unit's FINAL destination (goal heading), turn-rate capped, not the velocity heading. The face pass (`om_move_face_pass`, tactical_move.c:2476) sets it by priority: engaged target within 1.5x range, else `dest - pos` (:2465-2468, `has_dest`), else the last 1 wu of displacement (:2470-2472). Walkers move along route waypoints/steering (heading from `om_move_walker_step`, :2437 straight-line case), so wherever the route bends round terrain the body travels up to ~50 deg off the arrow (+y run: moved 45 deg the whole 60 ticks while facing 90). Turn caps: Strike 6.0 rad/s, Line 4.0, Siege 2.5 (om_constants.h:599-603) at 20 ticks/s units via `rate*period/OM_TACTICAL_TICK_RATE` (:508); the lag is small (~0.2-0.3 rad per tick cap), so lag is NOT the cause; the target choice is. Other writes: :2346 kiting faces the kite target; :2412 detour snaps facing to the sweep heading (pinned, :2439); :2439 non-deflect branch turns to the waypoint `heading` at the speed-band rate, but the face pass then overwrites it each tick. I did not reproduce a full 180-degree reversal; worst measured is ~50 deg, but a route that doubles back round a ridge would flip it (not measured).

## 2. Pipe
`pipe_tactical.c:493` `cur.facing = om_unit_get_facing(...)`, emitted as key `"facing"` (:567-568), raw `mu->facing`: the same number. `om_renderer_interpolate_facing` (tactical_move.c:2987) is not called by the pipe or any csrc/client file; only the header, `tests/csim/conftest.py:2498` and `test_E13_S101_movement_that_reads.py:153`. Client: `scenes/ground3d/ground_units.gd:83` `rotation.y = -facing` with x->x, y->z (:80-82); sign convention is consistent, the manifest `facing_offset_rad` is read by `era_theme_resolver.gd:77` (not looked at in the ground3d node: ground_units.gd does not apply it; bombard has -1.5708). tactical_bridge.gd reads key `facing_rad` (:167,:264) while the pipe sends `facing`: a key mismatch to check on the tactical (non-ground3d) path.

## 3. Obstacles (layer-2 walk mask, 100 wu cells, grid terrain seeds 11,1,2,3; anchor = centre-most cell of the largest layer-2 mask component)
Blocked cells within 1500 wu of the anchor: seed 11: 480 of 625 (components 470 + 10, 0 singles); seed 1: 470 of 709 (one component); seed 2: 667 of 709; seed 3: 698 of 708. So blocked cells are large contiguous masses, never scattered singles (singles = 0 in every seed); the walkable band is a small plateau. Caveat: `om_terrain_walkable_at` ignores layer, so it reported ~half the area walkable that the layer-2 mask blocks (my first run had walkers aimed at mask-blocked goals); use `om_terrain_walk_mask`.
20 individually ordered walkers (min 60 wu apart, one goal, 300 ticks), seeds 11 / 1 / 2 / 3: stopped >75 wu short at tick 300: 7 / 4 / 10 / 0 (the rest end ~30 wu, the crowd's collision radius, around the goal); detour (path/straight > 1.5): 0 / 0 / 0 / 4; jitter (>2 direction reversals in 100 ticks): 0 / 0 / 0 / 2 (seed 3: only a 10 cell plateau, 10 walkers, path up to 4.9x straight, 6 reversals). Most "short" ones in seeds 11/1 were still walking (start 1000-1300 wu from the goal, 300 ticks), seed 2 ones have path/straight 0.76-0.9 with ~1400 start distance and are also still in transit; I did not run longer, so "stop short" is unproven for open ground. The measured jitter is confined to cramped plateaus.
What decides a stop short (code, not measured): (a) `om_move_giveup_pass` tactical_move.c:2572-2587: only units with `group_id != 0` and `has_dest`, inside 75 wu of their slot for 40 consecutive ticks, drop the order where they stand (:2581). My walkers were single orders (group 0), so this did not fire; a group order hits it. (b) Fully blocked probe: `if (!found) { mu->waiting = 1; return; }` (:2417): the unit waits in place, forever, with no timeout; the bible calls this the open mechanism in FINDING-sim-move-blocked-by-idle-own (ledger row day37, line 1223: 42 units ordered past 26 idle own units stop 30 wu short as a packed column and never move or give up; ruled 2026-10-20 Q-087-02 b: idle own units are obstacles; fix piece not built). (c) Walker steering sweep (+-30/60/90 deg, `OM_PP_SWEEP_*`) treats other units as blockers, so idle own units are the likely "invisible obstacle": they are bodies the player cannot see as a wall.

## 4. Tests pinning facing
- `test_E13_S100_facing.py:34` `assert pytest.approx(facing_move, abs=1e-3) == 0.0` (a unit ordered along +x for 5 ticks with no obstacle: facing equals goal = heading, so it can't tell goal from velocity); :107 retreating unit faces pi; :56 faces target.
- `test_PP_move_steer_face.py:291` `assert abs(_angle_diff(facing, 0.0)) < ANGLE_TOL_RAD` ("plain move never faces an enemy"); :265 idle keeps last facing; :280 engaged target outranks move target.
- `test_E13_S101_movement_that_reads.py:163` pins only render interpolation of facing between ticks.
No csim test asserts facing equals the velocity heading along a route that bends (every pin has a straight, unobstructed goal), and none passes through the terrain-route case where measured divergence reaches ~50 deg. So the arrow is "correct by the rule as tested" (faces where it is going to, R-100-01) and wrong against the body's actual direction round obstacles; whether R-100-01 wants the next waypoint instead is a rule-meaning question for Westley/Architect, not mine.
