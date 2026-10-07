# Pre-flight scout 4-land-3d (2026-10-07, Sonnet, read-only)

Scout 4 report (read-only). The worktree `pf-vg4` is removed. The sandbox denied two compound commands, so I re-ran the removal as a single `git -C` command and it succeeded. Everything below was read from origin refs. Line numbers cite `scenes/mockups/landscape/` (`landscape/`) on `push/proto-land-iter` and `scenes/tactical_c/tactical_view.gd` (`tactical_view.gd`) on `origin/main`.

**(1) Mockup structure (`landscape/`)**
- **Mesh:** `ground.gd:8` `GroundBuilder.build(field_map, kit)` returns one `MeshInstance3D`.
  - Input is `FieldMap.grid`, a flat Array of Dictionaries indexed `gy*dim+gx` (`field_map.gd:28`).
  - `dim = canvas/SPACING + 1` (`field_map.gd:64`). That is a vertex grid at corners `(gx,gy)*SPACING`, not cell centres.
  - `SPACING` is 100 wu up to a 64,000 wu canvas, coarser above that (`field_map.gd:11`).
  - Height is `cell.elevation`, a float in wu with sea level 0 and peaks 3,000 to 5,000 (`field_map.gd:15`).
  - Each quad is two triangles with normals from `SurfaceTool.generate_normals()` (`ground.gd:46-58`).
  - Colour is a per-vertex blend of 5 `zone` colours over a 3x3 vote, lerped toward the cliff colour by a blurred blocked mask (`ground.gd:33-36`, `:101-122`).
- **Water:** a flat plane at y=0 (`placer.gd:621`, `_place_water`) when the kit says `water_is=surface`. In `void` mode, water quads are dropped from the mesh instead (`ground.gd:49-50`).
- **Bands:** the mockup has none in the mesh. Colour comes from `zone` (moisture noise) and `district`, which the sim does not have.
- **Camera (`camera_rig.gd`):** `Node3D` rig plus `Camera3D`, perspective.
  - The rig keeps a constant height above the terrain under its pan target, smoothed over 0.2 s (`:60-80`).
  - WASD and arrows pan, plus edge-scroll within 60 px.
  - Wheel zoom is a height from 150 to about 1.2×canvas, 300 per step.
  - Pitch is 50° up to 6,000 height, easing to 90° (top-down) by the map maximum (`:176-183`).
  - Rotation is set directly, with no `look_at`, to avoid a flip at 90°.
  - There is no rotate or orbit. `set_top_down()` forces 90°.
- **Bands (modes):** `_update_band` (`:151`): micro below 1,200, tactical below 6,000, map above.
  - Only `MapView` reacts. In the map band it shows a 10x10 lettered grid, border lines and the unit-group chevrons, and hides them otherwise (`map_view.gd:66-71`, `:84-139`).
  - There is no mesh level of detail. One mesh serves all heights. That falls short of S-236, "no pop between detail levels".
- **Picking:** two paths.
  - `map_view.gd:176-183` intersects the ray with the flat plane y=0. That is wrong on hills.
  - `pass4_ui.gd:380` `_pick` is terrain-correct: it marches 60 wu steps along the ray, then bisects 10 times against `_height_at` (bilinear). Carry this one over.
- **Also draws:** kit props via `MultiMesh` (`placer.gd:141-200`): cell scatter, borders, nodes (objective, spawn_point and so on), backdrop, water. Mesh names come from a fixed vocabulary (`kits/README.md`).
  - Overlay chevrons and arrows are screen-space `_draw` projected with `unproject_position`.
  - There are no walkers or units, only two fake chevron groups, and an objective ring (`map_view.gd:~210`).
  - `landscape_mockup.gd:15-` `qa_state()` exposes `objective_px` and `band`.
  - The rest of the 8,634 lines is passes 4 to 6 UI and shaping (`pass4_*`, `pass5_*`, `pass6_*`, `hud.gd`) plus the space map (`field_map_space.gd`, 1,520 lines). None of that is needed for lane C.

**(2) Sim terrain data (`origin/main`)**
- A height per cell exists. `st->height_cm` is `int32`, in cm (100 cm = 1 wu), `cells_w × cells_h` (`csrc/terrain.c:758`, `om_internal.h:~370`).
  - `ts_height_q` (`terrain.c:804`) interpolates bilinearly between cell centres, so the sim samples at `(i+0.5)*100`. The mockup's vertices sit at `i*100`. That is a half-cell offset the client mesh must honour.
  - `om_terrain_height_at` is in `ouroboros_sim.h:1991` and reaches the pipe only as a single-point `terrain_probe` (`om_pipe.c:2380`).
- `terrain_dump` (`om_pipe.c:2324`) sends `cells_w`, `cells_h`, `bands` (hex u8), `walkable` (hex u8) and `slopes[]`. It sends no heights.
- Sizes:
  - `OM_TERRAIN_MAX_CELLS` is 280 (`om_internal.h:364`), so 78,400 cells.
  - **Discrepancy:** `TG_MAX_CANVAS_WU` is 24,000 (`terrain.c:345`, "provisional"), so the generator caps at 240×240 = 57,600 cells today. Only the loader accepts 280.
- Contract piece for heights (the Architect's call on the shape): add `"heights"` to the `terrain` frame as hex of LE `int32` cm. The `om_terrain_dump_bands` pattern gives a cheap `om_terrain_dump_heights(w,int32*,cap)`.
  - Size at 280² is 313 KB raw, 627 KB hex. It is a once-per-mission pull, like `bands` (157 KB hex). Q16 is unnecessary.
  - `int16` wu would lose sub-wu precision, so keep `int32` cm.
  - Touches: `csrc/ouroboros_sim.h` + `signatures.toml` (one declaration and one row), `om_pipe.c` `handle_terrain_dump`, the `docs/architecture.md` frame, and `c_bridge.gd` `_fetch_terrain` (terrain3 `:518`).
  - Bands can be derived client-side from heights and `band_floor_cm`, but the dump already carries them.
- **Regenerate from the seed: no.**
  - The mockup uses Godot `FastNoiseLite` `TYPE_VALUE` (`field_map.gd:294-299`), seeded `p_seed+0..7`, frequency `N/canvas`.
  - The sim uses its own integer hash noise: splitmix `tn_mix`/`tn_lattice`, quintic fade, Q16 (`terrain_noise.c`). `terrain.c:333-338` says outright "Not bit-identical to the GDScript: value noise, the sine table and the exponents differ".
  - The sim also ports only pass 4 (shape, mesa, canyon, islands, relief, bench) and the band fit. It has no water, rivers, zones, districts, pass 5 layout or pass 6 shape. A client regeneration would not match the sim's field or its walkable mask.
  - The client must receive the heights. The sim is the authority for `walkable`.
- Consequence for look: the sim gives no zone, water or district, so ground colour has to come from height band, slope and walkability. The walkers mockup already does this (`BAND_COLOURS`, `STEEP_COLOUR`). Whether to add a sea level or water plane is a design call for the Architect. The sim has no water cells.

**(3) What `tactical_view.gd` becomes**
- Today it is a `Node2D` (672 lines).
  - Units are `Polygon2D` at `_to_screen()` pixels (`:595`, `:612-` `_display_px`, `_redraw:637`).
  - `_to_world` (`:574`) inverts the flat map.
  - The camera is a `Vector2` plus `_world_scale` (`:64-65`), on a fixed 1920×1080 canvas (`:12-13`; the project stretch mode is `canvas_items`).
  - Terrain3's `terrain_layer.gd` is a `Node2D` that draws the band texture and slope ticks into the same flat pixel space.
- Smaller change: option (a), a `SubViewport` (or a `Node3D` sibling under a `CanvasLayer`) with the 3D world, with `tactical_view` staying the 2D `Node2D` shell.
  - It keeps HUD, `_unhandled_input`, `send_command`, real-time stepping, `qa_state` and `qa_box_select` unchanged.
  - Only `_to_screen` and `_to_world` change. `_to_screen` becomes `cam.unproject_position(Vector3(wx, h(wx,wy), wy))`. `_to_world` becomes a ray-march pick, the `pass4_ui._pick` pattern.
  - `_display_px` is then still screen pixels, so these keep working: `units_px`, `qa_box_select` (compares `_display_px` to a screen rect), `tests/test_tactical_view.gd`, and the QA daemon's click verb. That verb is the generic `input click x y` in `autoload/qa_daemon.gd` / `daemon_client.py:91-93`, a Godot `InputEventMouseButton`. It needs no change as long as `units_px` stays in screen pixels. `scenes/mockups/_shared/qa_driver.gd` is the mockup driver, not the game's.
  - Unit visuals would be either 2D overlays at the projected positions (cheapest, and keeps tv-read) or 3D nodes.
- (b) A full `Node3D` rewrite breaks box-select, `units_px`, `test_tactical_view.gd`, the HUD labels and the real-time loop. It is the larger change.
- (c) 2D units projected onto the 3D ground is what (a) amounts to if the unit shapes stay 2D. The brief says no to that for the visuals. I would still keep the position projection, because it is what preserves the QA contract.
- Breakage under (a):
  - **Camera:** `qa_pan`, `_zoom_by`, `_force_camera` and `_pan_input` need a rig port (`camera_rig.gd`, about 200 lines), and `qa_state.camera {x,y}` and `scale` need re-meaning.
  - **tv-read** (`push/tv-read`, `9ab45bc9`): `unit_visuals.gd` (146 lines) and `map_layer.gd` (134 lines) are `Node2D`s that take `world_scale` and `camera` and compute `_to_screen` themselves.
    - They would need the projection injected, or a `Node3D` port of the shapes.
    - Their fog (a full-screen `draw_rect` masked by discs) and rings are in screen space. Fog and rings project, but the radii do not scale with perspective, so they would have to be re-derived.
    - `tv-read` also rewrites `tactical_view.gd` `_redraw` and `_ensure_layers`, so lane C's view edit has to rebase on it. Lane A lands first, per the plan.
  - **Terrain3:** `terrain_layer.gd` becomes dead as the ground, or stays as the map-band fallback. Its `ground_layer` `qa_state` key needs a successor.
  - `qa_state` needs new 3D fields (camera height, band, mesh stats) and a visual inventory under the programme's Guard 1.

**(4) Walkers mockup (`push/proto-walkers`, `walkers_mockup.gd`)**
- It does not draw a height offset or a shadow, and the brief's premise does not hold. It is a 2D top-down `Node2D` with a `Camera2D` (`:3`, `:54`), and the header says the land mockup is 3D so the ground is redrawn from band data (`:3-4`).
  - Walkers are 10-px squares in `WALKER_COLOUR` and flyers are triangles in `FLYER_COLOUR`, with a black outline and a white selection arc (`:128-137`).
  - A flyer's altitude is only a layer number 1 to 5, set with the keys 1 to 5 and shown as text (`_layers_text`, `:174`).
  - A walker's layer is the band under it, `grid.band_at(pos)` (`walker_units.gd:78-79`).
  - Routes are polylines with white crossing ticks, transfer dots and a red X for unreachable (`:113-127`).
- To carry into 3D (a design decision for the Architect, not in the mockup):
  - Walker Y = ground height at the unit's `(x,y)`.
  - Flyer Y = the height of its layer, from `om_terrain_band_heights` (`band_floor_cm`), plus a clearance.
  - A ground shadow or ground marker is needed for flyer readability, since pure perspective hides altitude. A mockup is cheaper than guessing here.
  - Keep the square and triangle shapes plus the faction colour and tv-read's layer tint.

**(5) Stories: what each needs visibly**
- **S-236:**
  - R-236-01: continuous detail from one unit up to the map view, with no level-of-detail pop.
  - R-236-02: steps between the five bands drawn as real height difference, with benched and natural ground both showing, and cliffs and mountainsides reading as landforms.
  - R-236-03: land only, no cliffs or waterfalls in the Settled Reach.
  - The mockup has no level-of-detail system (one mesh, `ground.gd`). Mesh chunking and level of detail are new work.
- **S-001:** blocked and open layers visible per position. A unit on a layer-1/2-blocked spot detours or changes layer (R-001-01..05). Slopes are drawn as ground joining layers with a midline (R-001-06). The `walkable` mask and `slopes[]` are already in the dump, but terrain3 draws only ticks. The 3D view needs a visible slope band and a midline.
- **S-004:** a unit mid-transition is visibly in transition (R-004-01..02). The slope midline is "a place I can see and hold" (R-004-06). Unit speed on slopes is 1.1× slower uphill and 1.1× faster downhill (R-004-07). That needs a transition indicator on the unit and a visible midline.
- **S-207:** no unit stuck in terrain or off the map (R-207-06/07). Routes follow slopes and steep ground (R-207-05). Buildings that block belong to lane E.

**Lane C piece list** (6 to 8 pieces plus 1 contract, per the plan)

| # | Piece | Content | Tests |
|---|---|---|---|
| C0 | Contract (lands first) | `terrain_dump` gains `heights`: `om_terrain_dump_heights` in `ouroboros_sim.h`, `signatures.toml`, `om_pipe.c`, `docs/architecture.md` | `tests/transport/test_pipe_terrain_verbs.py` extended: length is `cells*4`, a known value matches `terrain_probe`, and determinism |
| C1 | Bridge | `c_bridge.gd` `_fetch_terrain` decodes `heights` into a `PackedInt32Array` | extend `test_c_bridge_terrain.gd` |
| C2 | Ground mesh | new `scenes/tactical_c/ground_mesh.gd`, ported from `ground.gd`, with heights from cell centres, colour by band, slope and walkable, no zones | `test_ground_mesh.gd`: vertex count, height at known cells matches `terrain_probe`, a blank-frame guard |
| C3 | Camera rig | new `camera_rig_3d.gd` ported from `camera_rig.gd`, with `project_to_screen` and `pick_ground` | pan, zoom, band, and `unproject(pick)≈screen` |
| C4 | Picking and projection | `_to_screen` / `_to_world` rewritten in the view, with `pick_ground` using the `_pick` ray-march | `test_tactical_view.gd` unchanged and green, and a box-select regression |
| C5 | View wiring | `tactical_view.gd` hosts the 3D `SubViewport`, `qa_state` gains `ground3d`, and `terrain_layer` is retired or demoted to the map band | element-inventory test |
| C6 | Units in 3D | walker, flyer and shadow placement, and tv-read's `unit_visuals` / `map_layer` ported or re-projected | extend `test_tactical_readability.gd` |
| C7 | Slopes and layers | slope bands with midline, a transition indicator, and the blocked-layer view (S-001/S-004) | `qa_state` slope inventory |
| C8 | Level of detail and look gate | mesh chunking, a no-pop test (S-236), and a screenshot set for the `look` stage | histogram guard, plus screenshots seen by Westley |

Order: C0 → C1 → C2, C3 → C4 → C5 → C6, C7 → C8. C5 and C6 come after lane A's `tv-read`, and `terrain3-land-2` lands first.

**Owner rows touched** (from `pieces.toml` on origin/main)
- **C5** owns `scenes/tactical_c/**` and `autoload/c_bridge.gd` (`pieces.toml:457`, attached `d429d15`). **C8** also owns `scenes/tactical_c/**` (`:515`). The two overlap on `tactical_c/**`. That is existing, so the lane C pieces need a new owning row, or a hand-off from C5/C8, before any in-flight piece can touch `tactical_view.gd`.
- **TERRAIN-3** (`pending`) owns `scenes/tactical_c/terrain_layer.gd` and `tests/test_c_bridge_terrain.gd`. It must land before C1, C2 and C5, since all three touch those files.
- **PP-contract** owns `csrc/ouroboros_sim.h`, `signatures.toml` and `docs/architecture.md` (`:793`, `:1057`). C0 needs a contract piece row or a PP-contract extension, plus `csrc/pipe/om_pipe.c` (owned at `:349`) and `csrc/terrain.c` (TERRAIN-1/2, `:1274`).
- New rows are needed for `ground_mesh.gd`, `camera_rig_3d.gd` and the 3D tests.
- `push/tv-read` has no row visible on main. Its files `unit_visuals.gd` and `map_layer.gd` sit under C5's glob. Lane A should claim them.
- **MK-harness** owns `scenes/mockups/_shared/**` and `scenes/mockups/landscape/qa/**`. The mockup files themselves are read-only inputs.

**Open questions for the Architect:** ground colour without zones or water (band and slope only?); flyer altitude scale (layer to height); how the 240-cell generator cap (`TG_MAX_CANVAS_WU`) relates to the 280-cell loader cap.
