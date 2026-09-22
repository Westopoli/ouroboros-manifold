# Card regen report -- E-17

Module: `csrc/tactical_mapgen.c`. Rules file: `projects/ouroboros/rules/E-17.md`. Bible: `docs/bible/epics/E-17-map-generation.md`.

Old placeholder symbol(s) this epic's existing queue cards name: `om_mapgen_step`.

Cards generated: 15. Distinct symbols carded: 61. Tests assigned to a card: 29.

## Numbering prefixes (per story, reused from the old queue)
- S-112: 320a1-e17-mapgen-bones_from_the_library
- S-113: 321a1-e17-mapgen-nine_kinds_of_place
- S-114: 322a1-e17-mapgen-texture_from_gradients
- S-115: 323a1-e17-mapgen-the_region_shapes_the_te
- S-116: 324a-e17-mapgen-canvas
- S-117: 325a1-e17-mapgen-fair_enough
- S-118: 326a1-e17-mapgen-the_battlefield_moves
- S-119: 327a-e17-mapgen-terrain_that_reads_like_

## Cards generated
### S-112
- `320a1-e17-mapgen-bones_from_the_library`: symbols=[om_map_get_compatible_layout_count, om_map_get_compatible_layouts, om_map_layout_matches_archetype_filter, om_map_select_layout_uniform, om_map_instantiate_zone_pos] tests=[test_R_112_01_every_layout_satisfying_at_least, test_R_112_02_it_drawn_uniformly_at_random, test_R_112_03_its_zone_positions_percentages_canvas]
- `320a2-e17-mapgen-bones_from_the_library`: symbols=[om_map_generate_spine, om_map_count_distinct_routes_staging_to_objective, om_map_verify_flank_connections, om_map_library_total_layouts, om_map_layout_file_has_forbidden_fields] tests=[test_R_112_04_layout_s_connectivity_honored_there, test_R_112_05_it_holds_between_10_20]
- `320a3-e17-mapgen-bones_from_the_library`: symbols=[om_map_layout_file_has_required_fields] tests=[test_R_112_06_it_contains_only_zone_positions]

### S-113
- `321a1-e17-mapgen-nine_kinds_of_place`: symbols=[om_map_get_node_count, om_map_get_node_type, om_map_count_nodes_of_type, om_map_get_nth_node_of_type, om_map_has_flank_bypass] tests=[test_R_113_01_it_exactly_one_objective_staging, test_R_113_02_it_has_at_least_one, test_R_113_03_at_least_one_flank_route]
- `321a2-e17-mapgen-nine_kinds_of_place`: symbols=[om_map_node_get_owner, om_map_is_reachable_from_staging, om_map_is_reachable_from_all_spawns, om_map_compute_chokepoint_width] tests=[test_R_113_04_it_reachable_from_both_staging, test_R_113_05_passable_width_w_200_wu]

### S-114
- `322a1-e17-mapgen-texture_from_gradients`: symbols=[om_map_generate_gradients, om_map_sample_gradients, om_gradient_sample_single, om_gradient_combine_overlap, om_gradient_get_anchor_intensity] tests=[test_R_114_01_each_obstacle_density_cover_density, test_R_114_02_its_contribution_intensity_falloff_r]
- `322a2-e17-mapgen-texture_from_gradients`: symbols=[om_gradient_get_anchor_radius, om_map_add_layer_restriction_zone, om_map_sample_layer_accessibility, om_route_grid_is_cell_blocked] tests=[test_R_114_03_obstacle_density_anchors_at_chokepoints, test_R_114_04_every_layer_not_listed_gets, test_R_114_05_cell_blocked]

### S-115
- `323a1-e17-mapgen-the_region_shapes_the_te`: symbols=[om_map_flavoring_stability_multiplier, om_map_clamp_flavoring_delta, om_map_compute_economy_obstacle_delta, om_map_compute_tension_cover_delta, om_map_set_simulation_coupling] tests=[test_R_115_01_interference_hazard_anchor_count_cover, test_R_115_02_economy_lowers_obstacle_density_along]
- `323a2-e17-mapgen-the_region_shapes_the_te`: symbols=[om_map_get_simulation_coupling, om_map_generate, om_map_is_valid] tests=[test_R_115_03_layouts_hints_alone_produce_valid]

### S-116
- `324a-e17-mapgen-canvas`: symbols=[om_map_archetype_canvas_category, om_map_get_canvas_base_dimension, om_map_compute_modified_canvas] tests=[test_R_116_01_its_base_category_e_10, test_R_116_02_its_direction_archetype_s_defensive]

### S-117
- `325a1-e17-mapgen-fair_enough`: symbols=[om_fairness_evaluate, om_fairness_is_score_logged, om_fairness_force_score, om_map_get_active_seed, om_fairness_run_post_generation_check] tests=[test_R_117_01_it_scores_route_count_staging, test_R_117_02_q_113_01_map_regenerated]
- `325a2-e17-mapgen-fair_enough`: symbols=[om_map_layout_check_hazard_approaches, om_map_layout_check_vantage_reachability] tests=[test_R_117_03_it_passes_hard_constraints_no]

### S-118
- `326a1-e17-mapgen-the_battlefield_moves`: symbols=[om_map_setup_drifting_node, om_map_get_node_pos, om_tactical_tick_to, om_objective_get_center, om_gradient_add_moving_source] tests=[test_R_118_01_its_position_follows_path_ping]
- `326a2-e17-mapgen-the_battlefield_moves`: symbols=[om_map_sample_obstacle_density, om_unit_spawn_combat, om_unit_order_hold_node, om_tactical_tick, om_unit_get_position] tests=[test_R_118_02_its_position_moves_every_sampled, test_R_118_03_no_unit_teleports_units_path]

### S-119
- `327a-e17-mapgen-terrain_that_reads_like_`: symbols=[om_map_check_boundary_gradient_discontinuity, om_render_detect_repeated_tile_boundary, om_proc_arch_section_is_era_agnostic, om_proc_arch_resolve_section_piece] tests=[test_R_119_01_no_repeated_tile_boundary_visible, test_R_119_02_it_era_agnostic_at_section]

## Tests with no unbuilt symbol (already satisfiable)
none

## Symbols with no test (skipped)
Old placeholder symbol(s) no test in this epic calls (R22, re-confirmed): om_mapgen_step. Not carried into the regenerated cards.

## Stories needing more than 6 cards (design-lane question, not decided)
none

## Cards with no acceptance test of their own (design-lane question, not decided)
A card can end up with symbols but zero tests when every test needing them also needs a later card's symbols (the test's own closure is wider than the 5-symbol cap covers in one card). Candidates: (a) merge such a card forward into the next one, exceeding the cap only for this story (needs approval -- sizing caps are fixed); (b) accept the card as a pure prerequisite with no acceptance of its own (needs a card-format change -- card_lint.py currently hard-errors on empty acceptance); (c) leave it as a real card_lint finding and re-cut the test itself so its assertions split the same way the symbols do.
none

## Cross-epic symbol ownership
- `om_objective_get_center`: E-15, E-17
- `om_tactical_tick`: E-10, E-11, E-14, E-15, E-17
- `om_tactical_tick_to`: E-14, E-15, E-17
- `om_unit_spawn_combat`: E-15, E-17
