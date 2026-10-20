<!-- Read-only audit for Westley's question of 2026-10-20 "every piece of code written had a parent test, is that not the case?"; measured by a Sonnet engineer on origin/main 2beff79c (sim, gcov) and the same tree (client and tooling, reference map); copied byte for byte by a records clerk, Architect 2026-10-20. Interpretation is in the Architect's report to Westley, not here. -->

# gcov coverage of the C sim at origin/main (audit-cov worktree)

TOTALS: functions 1842 / zero in A 108 / zero in B 594; lines 20637 / covered A 18177 (88.1%) / covered B 15312 (74.2%)

A = all of tests/csim except tests/csim/scale (3172 run: 3040 passed, 123 failed, 7 skipped, 2 xfailed). B = tests/transport (396 run: 388 passed, 8 skipped, 0 failed).
Scope: csrc/*.c and csrc/pipe/*.c (the pipe server is csrc too). `*` = reachable per scripts/specfactory/reach_lint.py call graph. `~` = `__attribute__((weak))` stub in region.c, overridden at link by a strong definition elsewhere (gcov counts the stub, not the strong one).

## 1. Per file (sorted by zero-in-A descending)

| file | funcs | zero A | zero B | lines | cov A % | cov B % |
|---|---:|---:|---:|---:|---:|---:|
| csrc/layout_engine.c | 20 | 20 | 20 | 229 | 0.0 | 0.0 |
| csrc/pipe/om_pipe.c | 50 | 19 | 2 | 1495 | 38.6 | 93.6 |
| csrc/tactical_mapgen.c | 101 | 16 | 52 | 544 | 89.0 | 55.7 |
| csrc/region.c | 22 | 9 | 13 | 241 | 94.6 | 81.3 |
| csrc/pipe/pipe_net.c | 17 | 8 | 0 | 270 | 37.8 | 93.3 |
| csrc/layout_terrain.c | 6 | 6 | 6 | 25 | 0.0 | 0.0 |
| csrc/fog.c | 95 | 4 | 37 | 699 | 89.7 | 53.8 |
| csrc/pipe/pipe_dumps.c | 4 | 4 | 0 | 142 | 0.0 | 92.3 |
| csrc/pipe/pipe_tactical.c | 13 | 4 | 0 | 508 | 72.8 | 97.2 |
| csrc/tactical_move.c | 185 | 3 | 47 | 2354 | 93.7 | 74.4 |
| csrc/diplomacy.c | 48 | 2 | 29 | 489 | 97.1 | 39.7 |
| csrc/mission.c | 162 | 2 | 37 | 1974 | 97.3 | 80.2 |
| csrc/terrain.c | 65 | 2 | 6 | 618 | 98.4 | 86.7 |
| csrc/walk_route.c | 10 | 2 | 10 | 185 | 89.2 | 0.0 |
| csrc/worldgen.c | 19 | 2 | 9 | 302 | 87.4 | 75.5 |
| csrc/checksum_full.c | 12 | 1 | 1 | 144 | 95.1 | 90.3 |
| csrc/enemy_macro.c | 101 | 1 | 48 | 836 | 95.5 | 65.0 |
| csrc/events.c | 64 | 1 | 16 | 870 | 93.0 | 79.5 |
| csrc/space_plates.c | 21 | 1 | 1 | 354 | 98.9 | 98.9 |
| csrc/space_raster.c | 15 | 1 | 1 | 353 | 93.2 | 93.2 |
| csrc/agent.c | 5 | 0 | 1 | 271 | 99.3 | 88.9 |
| csrc/chronicle.c | 131 | 0 | 54 | 1027 | 98.0 | 69.1 |
| csrc/cmd_stream.c | 23 | 0 | 1 | 170 | 94.7 | 91.2 |
| csrc/collision.c | 5 | 0 | 0 | 131 | 96.9 | 93.9 |
| csrc/economy.c | 6 | 0 | 1 | 31 | 100.0 | 90.3 |
| csrc/economy_density.c | 9 | 0 | 1 | 143 | 97.2 | 81.8 |
| csrc/economy_doctrine.c | 2 | 0 | 1 | 11 | 90.9 | 18.2 |
| csrc/economy_lots.c | 9 | 0 | 0 | 64 | 100.0 | 85.9 |
| csrc/economy_place.c | 2 | 0 | 0 | 30 | 100.0 | 83.3 |
| csrc/economy_waves.c | 5 | 0 | 0 | 31 | 93.5 | 87.1 |
| csrc/faction.c | 22 | 0 | 3 | 146 | 88.4 | 76.7 |
| csrc/friction.c | 4 | 0 | 1 | 95 | 100.0 | 91.6 |
| csrc/generational.c | 163 | 0 | 72 | 1393 | 96.4 | 65.8 |
| csrc/lifecycle.c | 23 | 0 | 10 | 306 | 92.2 | 63.1 |
| csrc/resolve.c | 10 | 0 | 5 | 333 | 98.8 | 79.6 |
| csrc/save.c | 27 | 0 | 0 | 517 | 98.1 | 87.2 |
| csrc/sim.c | 24 | 0 | 8 | 328 | 100.0 | 75.0 |
| csrc/space_field.c | 9 | 0 | 0 | 98 | 100.0 | 94.9 |
| csrc/space_noise.c | 5 | 0 | 0 | 51 | 100.0 | 100.0 |
| csrc/strongpoint.c | 7 | 0 | 1 | 48 | 100.0 | 93.8 |
| csrc/tactical_support.c | 105 | 0 | 52 | 797 | 94.4 | 55.2 |
| csrc/terrain_noise.c | 10 | 0 | 1 | 43 | 100.0 | 81.4 |
| csrc/unit.c | 206 | 0 | 47 | 1941 | 95.7 | 72.4 |

## 2. Functions with exec_count 0 in A (108; 43 starred = reachable from tick/pipe, live code with no csim test)

### csrc/layout_engine.c (20)
layout_age_u, layout_base, layout_better, layout_canvas_ok, layout_cell_centre, layout_dist, layout_next_town, layout_noise01, layout_noise_q16, layout_other_towns, layout_push, layout_resource_town,
layout_resource_towns, layout_richness, layout_satellite, layout_score, layout_town_age, layout_work_fill, layout_work_free, om_layout_places
### csrc/pipe/om_pipe.c (19)
*handle_assign_commander, *handle_command, *handle_inject, *handle_jump, *handle_list_saves, *handle_load, *handle_mission_end, *handle_mission_refuse, *handle_objective_complete,
*handle_place_structure, *handle_run_to, *handle_set_feature, *handle_space_field_dump, *handle_step, *handle_tactical_step, *write_chronicle, *write_debrief, *write_delta, *write_error
### csrc/tactical_mapgen.c (16)
om_gradient_combine_overlap, om_map_check_boundary_gradient_discontinuity, om_map_compute_economy_obstacle_delta, om_map_compute_tension_cover_delta, om_map_get_compatible_layouts,
om_map_has_flank_bypass, om_map_is_reachable_from_all_spawns, om_map_is_reachable_from_staging, om_map_layout_check_hazard_approaches, om_map_layout_check_vantage_reachability,
om_map_layout_matches_archetype_filter, om_map_node_get_owner, om_map_verify_flank_connections, *om_mgs_obstacle_at, om_proc_arch_resolve_section_piece, om_render_detect_repeated_tile_boundary
### csrc/region.c (9)
~om_debug_inject, ~om_region_drift, ~om_trace_enable, ~om_trace_len, ~om_trace_read, ~om_world_checksum, ~om_world_generate, ~om_world_run, ~om_world_step
### csrc/pipe/pipe_net.c (8)
*handle_net_log_dump, *handle_net_log_load, *handle_net_state_diff, *handle_net_state_get, *handle_net_state_put, *hex_get, *hex_nibble, *hex_put
### csrc/layout_terrain.c (6)
layout_world_height, layout_world_nearest, layout_world_walkable, om_layout_is_water, om_layout_slope, om_layout_terrain_from_world
### csrc/fog.c (4)
fog_sr_f64, fog_sr_u8, fog_sw_f64, fog_sw_u8
### csrc/pipe/pipe_dumps.c (4)
*handle_lots_dump, *handle_terrain_dump, *handle_terrain_generate, *handle_terrain_probe
### csrc/pipe/pipe_tactical.c (4)
*event_shown, *struct_in_sight, *unit_shown, *write_lot_row
### csrc/tactical_move.c (3)
*om_move_probe_gather, *om_move_probe_sure_blocked, *om_move_turn_rate_for
### csrc/diplomacy.c (2)
om_faction_tier_transition_candidate, om_tier_transition_candidate_exists
### csrc/mission.c (2)
om_mission_get_candidate_score, *om_mission_sum_faction_hp
### csrc/terrain.c (2)
om_terrain_cell_band, om_terrain_state_free
### csrc/walk_route.c (2)
*wr_compact, *wr_down
### csrc/worldgen.c (2)
om_gen_set_extra_edge_ratio, om_gen_set_home_range
### csrc/checksum_full.c (1)
om_checksum_unit_hashes
### csrc/enemy_macro.c (1)
om_mission_get_reinforcement_foreshadow_text
### csrc/events.c (1)
om_event_template_significance_tier
### csrc/space_plates.c (1)
om_space_plates_build
### csrc/space_raster.c (1)
*sr_drop_ring

## 3. Run in A, zero in B, name contains move/path/route/reach/layer/acquire/target/fire/attack/emission/stealth/elevation/formation/give_up (58): isolation only, not through the pipe

### csrc/tactical_move.c (19)
*om_command_attack_target_kiting, om_command_direct_move, om_command_queue_attack_move, om_command_queue_move, om_move_enqueue, *om_move_get_canvas_size, om_move_group_find, *om_move_route_aim,
om_move_route_get, om_move_route_len, *om_move_route_pt, *om_move_route_store, *om_move_route_tables, *om_move_terrain_epoch, *om_move_walk_blocked, *om_move_walker_step, om_navmesh_find_path,
om_navmesh_is_path_straightened, *om_roster_set_reach
### csrc/fog.c (9)
fog_player_faction_id, *om_command_set_emission, om_player_can_see, om_player_can_see_friendly, om_unit_acquire_target, om_unit_get_cross_layer_factor, om_unit_get_emission,
om_unit_spawn_with_elevation, om_visibility_set_player_fog
### csrc/unit.c (7)
om_era_elevation_damage_bonus_enabled, om_tactical_target_validation_runs_every_tick, om_unit_attack, om_unit_clear_target, om_unit_set_elevation_tier, om_unit_set_stealth, om_unit_targeting_cohort
### csrc/mission.c (5)
om_mission_apply_target_adjacent_player, om_mission_eval_destroy_targets, om_mission_get_player_units, om_mission_set_player_units, om_mission_setup_destroy_targets
### csrc/tactical_support.c (4)
om_enemy_production_adapt_target, om_mission_set_player_held_structures_count, om_unit_can_return_fire, *om_unit_order_move
### csrc/diplomacy.c (3)
*om__betrayal_fire, *om__pair_attacked_this_tick, *om_faction_tech_attack
### csrc/tactical_mapgen.c (3)
om_map_add_layer_restriction_zone, om_map_count_distinct_routes_staging_to_objective, om_map_sample_layer_accessibility
### csrc/events.c (2)
om_event_breached, om_event_last_fired
### csrc/generational.c (2)
om_player_faction_record_reassignment, om_progression_has_player_level
### csrc/enemy_macro.c (1)
om_macro_reads_player_visibility_set
### csrc/lifecycle.c (1)
om_player_faction_collapsed
### csrc/walk_route.c (1)
*om_walk_route
### csrc/worldgen.c (1)
om_gen_set_player_preference

## 4. Totals

- functions total 1842; zero in A 108; zero in B 594; zero in B but run in A 519; zero in both 75
- lines total 20637; covered A 18177; covered B 15312
- functions zero in A and reachable (starred): 43; zero in B and reachable: 95
## 5. Method caveats

Build: `make OPT="-O0 --coverage"` for libouroboros.so, libouroboros_dbg.so, pipe/ouroboros_pipe and pipe/ouroboros_pipe_dbg (86 .gcno files); gcov results from the release and dbg builds (and from the release and dbg pipes) are summed per (file, function, start line), and a line counts as covered if it ran in any of them; tests ran with the venv python of the live checkout (`.venv/bin/python -m pytest`, read as an interpreter only) because system python3 has no pytest. Run A excluded tests/csim/scale (29 files, slow) and ran 3172 csim tests including tests/csim/controls with 123 failures (92 of them in controls, e.g. `OMBug` has no `CONVOY_RETURNS_FIRE`; the rest are E17/E13 and one perf test under -O0), so code only those failing tests would reach counts as zero, and the machine was shared with other chats' test runs; run B ran all 396 tests/transport tests (388 passed, 8 skipped), and tests under tests/long, tests/push, tests/net, tests/skilllab and the Godot tests are in neither A nor B.
Not attributable by gcov: region.c's `__attribute__((weak))` stubs (marked `~`) are counted as the stub, not the strong definition that replaces them at link; zero-in-A counts also include the 9 such stubs; reachability (`*`) is reach_lint's static call graph from om_world_step, om_tactical_step, om_time_jump_run and the om_pipe.c dispatch loop, so calls through function pointers are invisible to it and a function not starred may still be live, and a starred function is only statically reachable; static inline functions in headers are not counted (only csrc/*.c and csrc/pipe/*.c), and the reachable flag is by name, so a static function sharing a name with an extern one in another file is matched by its `file:name` title first.
Raw gcov JSON is in cov/A and cov/B (one file per .gcno plus merged.json); pytest logs are cov/A/pytest.log and cov/B/pytest.log.
