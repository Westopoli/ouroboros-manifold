# Pre-flight scout 1-legacy-inventory (2026-10-07, Sonnet, read-only)

Scout 1 (legacy inventory for lane A) is done. Nothing was modified, and the worktree `~/Projects/om-push/wt/pf-vg1` is removed. All evidence is from origin/main `a612d1c8`, `009c99ac^` and `origin/push/tv-read` `9ab45bc9`.

**Key.** L = `scenes/tactical/` at `009c99ac^`. Legacy files are abbreviated: `ur` = unit_renderer.gd, `hud` = hud.gd, `ir` = input_router.gd, `tac` = tactical.gd, `tr` = terrain_renderer.gd, `mm` = mission_marker.gd, `ci` = command_indicator.gd. Visuals files are `avm` (attack_visual_manager), `pr` (projectile_renderer), `br` (beam_renderer), `apr` (area_pulse_renderer), `aom` (ability_overlay_manager), `ifm` (impact_feedback_manager), `dm` (destruction_manager), `adm` (ambient_density_manager), `ch` (combat_heatmap), `fsp` (flyby_ship_pool), `lo` (tactical_loading_overlay).

- **ser** = legacy `simulation/snapshot_serializer.py`, the Python frame source.
- **mf** = `assets/eras/settled_reach/manifest.json`, still on main.
- **pipe** = `csrc/pipe/om_pipe.c`. **arch** = `docs/architecture.md`. **cb** = `autoload/c_bridge.gd`.
- **tv** = push/tv-read (`unit_visuals.gd` = uv, `map_layer.gd` = ml). **tvm** = main's `scenes/tactical_c/tactical_view.gd`.

**C tactical frame today.**
- Unit object: `{id,faction,type,tier=0,x,y,hp,layer,facing,target,state=0}` (pipe:1251-1281).
- `units_removed` (pipe:1287); `visible{pf:[ids]}` (pipe:1313).
- `map{canvas,nodes[i,kind,x,y],cover[x,y,r,h],obstacles=[]}` (pipe:1146-1201).
- `objectives[{i,progress}]` (pipe:1124).
- The mission frame adds `objectives[{i,kind,node,primary,radius,progress}]` (pipe:828-835).
- Doubles print as `%.17g` (pipe:190), so a unit object is about 170 B and 500 units is about 85 KB per full frame. These are my estimates, not measurements.

| # | Element | Legacy file:line | Python field / query | C today | Contract add if NONE | In tv-read? |
|---|---|---|---|---|---|---|
|1|Unit mesh per type, 6 types x 3 tiers|ur:131,173,194-237; mf:7-36|`type` string (ser:322)|`type` int 0..5 (pipe:1257; arch:256), client table|none|Partly: flat polygon, corners [3,4,5,6] by `type mod 4` (uv:13,30-35). Types 4 and 5 reuse the Raider and Interceptor shapes, which is a defect against S-132.|
|2|Tier look: matte / metallic / emissive|ur:132,240-256; mf:58-88|none. ser:319-339 never sent `tier`, so legacy always drew tier 1.|`tier` exists but is reserved 0 (pipe:1260; arch:270, A30)|NONE: fill `tier` per unit (0 extra B). Needs a sim tier source.|No|
|3|Visual scale per type|ur:141,297-300; mf (Warden 200.0, others 1.0-2.0)|`type`|`type` + manifest|none|No (fixed radius 12, uv:6)|
|4|Squad offsets, squad count, facing offset|ur:24-29,140,144-146,299; mf squad 4 for Raider and Interceptor, facing offset Raider pi, Bombard -pi/2|`type`, `facing_rad`|`type`, `facing` (pipe:1275); `om_unit_render_craft_count` (unit.c:2859) not on pipe|none (manifest mirrors it)|No|
|5|Position and facing smoothing (display 3 ticks back)|tactical_bridge.gd:36-123; ser:12-61|`pos`, `velocity`|`x`,`y`,`facing` per frame, no velocity; `n>1` writes one frame (arch:276)|none, but the client needs its own interpolation buffer|No. tvm:612-618 snaps to the frame.|
|6|Layer height (y = layer x 250)|ur:295; era_config.gd:4|`layer`|`layer` (pipe:1272)|none in 2D. Fitted bands (R-010-01) come from lane C's height contract.|No (2D)|
|7|Layer ring (colour per layer 1-4, r44-50)|ur:9-15,356-411|`layer`|`layer`|none|Yes, as an outline tint (uv:9,38-39,55-60), not a ring|
|8|Layer dimming (inactive alpha 0.4)|ur:267-268,303,399; era_config.gd:7|`layer` + client `active_layer` (ir:14)|`layer`|none|No|
|9|Preference ring|ur:414-471|`preferred_layer` (ser:328)|NONE. Nearest is `om_unit_get_target_layer` (tactical_move.c:3166, in-transit target only). No standing-preference accessor.|`tl` per unit; the standing preference needs a sim accessor first (flag F4).|No|
|10|Layer-change progress (rise / drop)|Not in legacy: snaps (ur:295)|none|NONE. `om_unit_transition_progress` (tactical_move.c:3157) is unwired.|`tl` int + `lp` 0..1, only for units in flight, ~35 B each|No|
|11|Selection ring (faction colour, r60-66)|ur:307-353|client selection|none|none|Yes (uv:110-124)|
|12|Fog gate (unseen enemies hidden)|ur:285-289,362; scripts/tactical/visibility.gd:9-24; ir:326|`fog_of_war.player_visible_unit_uids` (ser:127-130)|`visible` (pipe:1313; arch:275)|none|Yes (uv:68-75)|
|13|Sight circle and fog dim (legacy had none, units were only hidden)|none|none|NONE. `om_fog_get_drawn_sensor_circle_radius` (fog.c:504) is unwired.|`sight` per own unit, ~22 B, so ~11 KB per full frame at 500 own units|Draft: constant 600 and a shader (ml:6,14-28,72-112)|
|14|Cover asteroids, 3 meshes by class (tiny/small to small, medium, huge)|tr:296-342; era_theme_resolver.gd:99-111|`cover_asteroids{id,cluster,x,y,r,h,class}` (ser:425-437)|`map.cover[x,y,r,h]` (pipe:1174-1197). A live mission has 1 disc (mission.c:2404).|NONE: `class` int per cover (or a client threshold on `r`, which needs a ruling)|Discs only, no class (ml:68-69,107)|
|15|Obstacle scatter / obstacle discs|tr:218-289, seeded by `map_seed` (tr:60)|`gradient_sources` (ser:93-100)|`map.obstacles` always `[]`. No C enumerator (pipe:1198).|NONE: ABI count/at accessor, then fill. Cap 3136 (tactical_mapgen.c:111), ~45 B each.|Discs if non-empty (ml:70-71,109)|
|16|Density gradient discs and zone kinds (obstacle / cover / sensor colours)|tr:11-16,85-107|`gradient_sources{property,pos,radius,intensity}`|NONE. `om_gradient_*` and `om_map_generate_gradients` are STUBs (tactical_mapgen.c:310-333,500). Zone adders exist (ouroboros_sim.h:1532-1535) with no reader.|`zones[{kind,x,y,r,intensity}]`, once per mission, ~70 B each. Blocked on the sim generating any (F1).|No|
|17|Spine node markers (6 colours, ring, label)|tr:18-29,110-158|`spine_nodes{id,type,pos,layer}` (ser:84-91)|`map.nodes[i,kind,x,y]` (pipe:1146-1172). Live: 1 objective node + 2 spawn points (mission.c:2403-2406). Kind enum is E-17's, not the legacy six (tactical_mapgen.c:115).|none for the frame; the kind-to-look table is client-side|Nodes only place objective rings (ml:61-67)|
|18|Structure in world (settlement model, capture ring r108-120 by owner, HP/cap label)|tr:161-211; rebuild on `structures_updated` (tr:46)|`structures{uid,pos,layer,hp,max_hp,owner,capture_progress,production_timer_sec,production_target,capture_radius}` (ser:342-354)|NONE ("no frame exposes placed structures", arch:256). Sim has `om_structure_*` (ouroboros_sim.h:1947-1976), 2-8 per mission (tactical_support.c:342-343; mission.c:2371-2386). No count accessor.|`structures[]` per full frame, ~150 B each, <=1.2 KB. Delta carries changed `hp`/`owner`/`cap`. Send `next_spawn_tick`, not a countdown, or ~0.3 KB churn per frame.|No|
|19|Map boundary slabs|tr:64-82|`canvas_size`|`map.canvas` (pipe:1146)|none|No (tvm:220-222 scales by canvas)|
|20|Mission marker: beam, label, primary/secondary colour|mm:6-55; tac:297-333|`objectives{id,type,is_primary,status,location}` (ser:357-374)|mission `primary`, `node`, `radius`, `kind`, plus `nodes[]` for position|none|Partly: ring only, one colour (ml:62-67,113)|
|21|Hold / clear zone ring|mm:72-95|`location.radius` (ser:379)|mission `radius` + `node`|none|Yes (ml:62-67)|
|22|Objective status complete / failed (markers dropped)|tac:303-306,326-329; hud:258-261|`status` (ser:358-363)|`{i,progress}` only. Sim has `is_complete`/`is_failed` (ouroboros_sim.h:1226-1227).|NONE: `done` 0/1/2 per objective per frame, ~10 B x <=4|No|
|23|eliminate_force marker location (enemy centroid)|ser:390-398|centroid of live enemies|NONE, no node|none without leaking fog (F5)|No|
|24|HUD objectives panel (primary 15pt vs secondary 12pt, bars, sort)|hud:242-279,287-318,445-468|objectives list|mission `primary` + frame `progress`|none|main: primary only, text and % (tvm:195-199; names tvm:28-31). No bars, no secondary.|
|25|Events ticker (4 lines)|hud:101-137|`events[]`: `unit_destroyed{uid,at,layer}` (ser:238-247)|NONE. `units_removed` is ids only (pipe:1287) and cannot tell kill from despawn.|`events[]`, see group B|No|
|26|Banner top-centre (4 s)|hud:140-146,471-478|`structure_captured`/`structure_lost`/`objective_threshold`. ser never emitted them (ser:238-248); dead branches (hud:107-116).|NONE|group B|No|
|27|Clock|hud:151-156,481-503|`tick` minus start tick|`tick` (pipe:1105)|none|Main only: tvm:190-191|
|28|Minimap (units, structures by owner, objective shapes, frustum quad)|hud:506-514,592-674|units, `structures`, objectives|units and `visible` yes; structures NONE|structures (row 18). The bible replaces it with the map view (R-104-05).|No|
|29|Selection panel (type x count, HP sum / max)|hud:159-199,534-545|`hp`,`max_hp`,`type`,`ability_cd_sec` (ser:329-336)|`hp`,`type` only; no `max_hp`|`profiles[type].max_hp`, see group C|Main: count only (tvm:200)|
|30|Ability ring (cooldown arc, 30 s hard-coded)|hud:556-589|`ability_cd_sec`|NONE. `om_unit_ability_cooldown`/`_active` (ouroboros_sim.h:2028-2029) are unwired.|`acd` (ready tick) + `aa` per unit; `profiles[].acd_max`|No|
|31|Reinforcement list (own structures: HP, next unit, timer)|hud:282-356,517-532|`structures` with `owner==0`|NONE. `om_structure_get_hud_data` (ouroboros_sim.h:1303) is unwired.|structures (row 18)|No|
|32|Control-group bar (type icon, count)|hud:214-239,677-696|client groups|client only|none|No|
|33|Layer selector L0-L4 and readout|hud:202-211,699-721,733-772|client `active_layer`|client only|none|No|
|34|Camera: edge-pan 60 px, wheel +-300, zoom 150-12000, 65 deg pitch, pan speed from settings, initial centroid of own units|tac:7-26,83-84,108-129,187-226|client, canvas, own units|`map.canvas` + units|none|Main: 2D pan/zoom, canvas clamp, initial framing (tvm:478-536,466-470)|
|35|Click pick (30 px) and box select (6 px drag, shift additive, box drawn)|ir:23-25,43-64,110-164|display positions, `visible`|`x`,`y`,`visible`,`faction`|none|Main: box select (tvm:442-456,555-567), no box drawn|
|36|Double-click select same type|ir:54-56,170-198|`type`,`selection_eligible`|`type`,`faction`|none|No|
|37|Control groups bind / recall (exclusive)|ir:89-99,213-241|client|client only. Legacy sent `control_group_bind`/`_recall` commands (ir:228,241); C has no verb and needs none.|none|No|
|38|Select-all-army (`~`)|ir:82-83,201-205|-|forbidden by R-105-04 (E-16:91); main has a permanent-negative plant (tvm:314-318)|do not port|-|
|39|Move (right-click) and ground decal|ir:65-67,268-273; tac:335-347; ci:37-48|command|`command` verb `move` (pipe:1740; cb:420)|none|Move marker (uv:131-143)|
|40|Attack-move (A) and crosshair decal|ir:74-75,276-283; ci:50-58|command|verb `attack_move` (pipe:1749)|none|Main: A then click + feedback (tvm:547-563,578-585)|
|41|Layer commands: X hard transfer, shift+1..5 preference|ir:80-81,96-97,250-263|command|NONE as a `command` verb. `om_command_set_layer` (tactical_move.c:3130) is reachable only via `net_submit` verb 4 (ouroboros_sim.h:283).|`command` verb `set_layer{units,layer}`|No|
|42|Ability keys W/S/D/C/E (`slot_N`)|ir:11,102-105,287-292|command|verb `activate_ability` (pipe:1758), no slot id; cb:423 whitelists only move / attack_move / attack_target|client wrapper only|No|
|43|Attack beam (Warden, 0.4 s, shimmer)|avm:14,97-113; br:26-101|`attack_target`,`attack_range`,`attack_interval`,`type`. Timing is inferred locally (avm:1-6,57-95), not sent per attack.|`target` (pipe:1278) + `type`; no range or interval|`profiles[]` + per-unit `state` fired bit (`om_unit_in_backswing`), see group C|No|
|44|Projectile, volley, trail, LOD cull|avm:10-17,115-147; pr:6-193|same as row 43|same|same|No|
|45|Impact burst (damage-scaled) and target bloom|ifm:122-154,160-173,176-236|`hp` drop >= 0.5; attacker faction by scanning `attack_target`|`hp`,`target` per frame|none (derive from deltas)|No|
|46|Destruction: bloom, wreck box, drift, 5/15/30 s lifecycle|dm:129-144,147-215,218-277|alive transition; cached type / faction; `facing`|`units_removed` (ids); client caches type, faction, pos, facing|none; a kill flag is group B|No|
|47|Area pulse, ability rings and glows, FOV nudge|apr:28-88; aom:6-13,77-106,109-165,229-244|ability events `{ability_id,uid,faction,target_pos,radius,duration_ticks}` (tactical_bridge.gd:308-310; ability.py:49-60)|NONE. `om_tick_read_ability_events` (unit.c:2949, cap 256) is never drained by the pipe.|group B|No|
|48|Ambient haze, flyby ships, combat heatmap|adm:58-195; fsp:6-159; ch:6-72|canvas, `attack_target` per unit|`map.canvas`,`target`|none|No|
|49|Loading overlay "DEPLOYING FORCES"|lo:21-61; tac:72-73,108-111|first snapshot|first tactical frame (arch:344)|none|No|

Excluded as dev or non-lane items: perf label/logger (tac:228-264, perf_logger.gd), F12 label (hud:775-802), tutorial triggers (tac:167-184), `qa_state` (tac:350-356).

**NONE list, grouped into the smallest contract set.** Sizes are per frame at 500 units, my estimates.

- **A. `structures[]`** (rows 18, 28, 31). It needs a sim count accessor and a pipe writer. Full frame is <=1.2 KB. Deltas carry changed fields only, with `next_spawn_tick` instead of a countdown.
- **B. `events[]`** (rows 25, 26, 46, 47).
  - Ability events from the existing sim feed, ~110 B each, typically <=1 KB, worst case 256 per frame.
  - A unit-destroyed kill flag.
  - Structure captured/lost, derived from A's `owner` change.
  - "Force routed" and "objective threshold" have no C event source. A sim piece comes first.
- **C. Per-type `profiles[6]`**, once per full frame, ~0.7 KB.
  - Fields: `max_hp`, `attack_range`, `attack_interval`, `sensor_radius`, ability id and `acd_max`.
  - It feeds shots (with `target` and `state`), the selection HP sum and the ability-ring denominator.
- **D. Per-unit fields on the existing object**, up to +45 B per unit, so ~+22 KB on a 500-unit full frame. Deltas stay changed-only.
  - `tier` (fill the reserved field).
  - `state` bits (fired, braced, in flight) with an enum table.
  - `acd` as a ready tick, plus `aa`.
  - `sight` (own faction only).
  - `tl` and `lp` (in-flight units only).
- **E. Objective `done`**, ~10 B x <=4 objectives.
- **F. Map data, once per mission rather than on every 20th-step full frame.**
  - Obstacle enumerator.
  - Cover `class`.
  - A zones array (blocked, F1).
  - Cover and obstacles are capped at 3136 each (tactical_mapgen.c:111), so worst case is ~190 KB and ~140 KB on every full frame. Today a live mission has 1 disc.
- **G. `command` verb `set_layer`.**

**Legacy elements with no C equivalent (open flags).**

- **F1. The Python tactical map generator.**
  - Spine nodes of six types, gradient sources, drifting nodes and asteroid clusters have no C source.
  - `om_map_generate`, `om_map_generate_spine`, `om_map_generate_gradients` and `om_gradient_*` are STUBs (tactical_mapgen.c:310-333,495-505).
  - A live mission lays 1 objective node, 1 cover disc and 2 spawn points (mission.c:2403-2406).
  - Rows 14-17 therefore have no data in play. Terrain stage 2's `om_terrain_generate` is a different thing (lane C).
- **F2. `map_seed` and obstacle scatter.** `tr:60` read `map_seed`, which ser never sent, so legacy scatter always used seed 0. C's `om_map_get_active_seed` is a STUB (tactical_mapgen.c:510).
- **F3. Unit tier.** Python never sent it (ser:319-339), so the legacy tier meshes and tier materials never ran. C's tier is reserved (A30) and the per-unit sim source is missing. `om_mission_get_force_unit` (ouroboros_sim.h:1751) has a roster tier for the player's force only.
- **F4. Standing layer preference.** There is no accessor, and the C layer-change state is only the transit target. The legacy `preferred_layer` ring (R-003) has no C counterpart.
- **F5. Python-computed visuals with no C source.**
  - The `eliminate_force` enemy centroid, computed in the serializer ignoring fog (ser:390-398).
  - Ticker events `structure_captured`, `structure_lost` and `objective_threshold`, which ser never emitted.
  - "Force routed" (R-104-01).
- **F6. Slot-based abilities.** Legacy sent `slot_N` ids and a hard-coded 30 s ring (hud:557). C has one ability per unit type and no slot id on the wire.
- **F7. Dead-reckoning stream.** The legacy 20 Hz delta plus velocity feed (ser:12-61) has no C counterpart. C sends positions only, and `n>1` steps coalesce into one frame, so hits and fire timing are coarser.
- **F8. Legacy rows the current bible contradicts, so do not re-derive them.**
  - Select-all-army (R-105-04).
  - The minimap (R-104-05 uses the map view).
  - The "force routed" ticker beat.
  - The layer readout on the right sidebar (R-104-09: strip only).
  - The legacy HUD has no HP bar above units (R-104-10), no commander portrait (R-104-08), and no Comb or Angle Rack.

**Stale doc, noted not fixed.** The `om_pipe.c` header comment (lines 31-47) says nodes, cover and units are "always empty". The code now fills nodes, cover and units. Only obstacles stay `[]`.
