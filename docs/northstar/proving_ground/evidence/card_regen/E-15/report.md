# Card regen report -- E-15

Module: `csrc/tactical_support.c`. Rules file: `projects/ouroboros/rules/E-15.md`. Bible: `docs/bible/epics/E-15-reinforcement-supply-and-hazards.md`.

Old placeholder symbol(s) this epic's existing queue cards name: `om_support_step`.

Cards generated: 16. Distinct symbols carded: 65. Tests assigned to a card: 25.

## Numbering prefixes (per story, reused from the old queue)
- S-126: 310a1-e15-support-most_of_my_force_is_out_
- S-127: 311a1-e15-support-taking_a_garrison
- S-128: 312a-e15-support-what_the_enemy_builds
- S-129: 313a1-e15-support-units_that_cannot_fight
- S-130: 314a1-e15-support-the_battlefield_moves
- S-131: 315a1-e15-support-reading_hazards_and_stru

## Cards generated
### S-126
- `310a1-e15-support-most_of_my_force_is_out_`: symbols=[om_structure_compute_count, om_structure_assign_owners, om_structure_production_interval_ticks, om_structure_init, om_structure_set_timer] tests=[test_R_126_01_count_clamp_floor_region_military]
- `310a2-e15-support-most_of_my_force_is_out_`: symbols=[om_structure_tick_production, om_structure_pop_spawned_unit, om_structure_get_timer, om_structure_get_last_spawn_distance, om_structure_switch_unit_type] tests=[test_R_126_02_one_unit_that_type_spawns]
- `310a3-e15-support-most_of_my_force_is_out_`: symbols=[om_structure_get_unit_type, om_mission_compute_starting_force, om_mission_compute_reinforcement_capacity, om_structure_get_hud_data, om_structure_unit_cost] tests=[test_R_126_03_production_switches_to_it_at, test_R_126_04_starting_force_0_20_f, test_R_126_05_player_sees_timer_bar_next]
- `310a4-e15-support-most_of_my_force_is_out_`: symbols=[om_mission_set_player_held_structures_count, om_mission_get_reinforcement_trickle] tests=[test_R_126_06_units_have_no_cost_player]

### S-127
- `311a1-e15-support-taking_a_garrison`: symbols=[om_structure_set_owner, om_structure_set_capturing_faction, om_structure_tick_capture, om_structure_get_capture_progress, om_structure_get_owner] tests=[test_R_127_01_capture_progress_rises_by_dt]
- `311a2-e15-support-taking_a_garrison`: symbols=[om_structure_set_capture_progress, om_structure_set_contested, om_structure_get_hp, om_structure_apply_damage, om_structure_is_destroyed] tests=[test_R_127_02_progress_resets_to_0]
- `311a3-e15-support-taking_a_garrison`: symbols=[om_tactical_tick, om_structure_on_owner_changed, om_ticker_pop_message, om_structure_get_base_max_hp, om_structure_get_matchup_multiplier] tests=[test_R_127_03_it_takes_damage_like_unit, test_R_127_04_structure_captured_or_structure_lost, test_R_127_05_it_3_000_alg_75]

### S-128
- `312a-e15-support-what_the_enemy_builds`: symbols=[om_enemy_production_select_category, om_enemy_production_adapt_target] tests=[test_R_128_01_it_produces_category_most_below, test_R_128_02_15_percent_target_shifts_to, test_R_128_03_it_never_deviates_from_ratio]

### S-129
- `313a1-e15-support-units_that_cannot_fight`: symbols=[om_unit_spawn_non_combat, om_unit_spawn_combat, om_unit_tick_decision_loop, om_unit_get_target, om_unit_deal_damage] tests=[]
- `313a2-e15-support-units_that_cannot_fight`: symbols=[om_unit_can_return_fire, om_unit_is_flinching, om_mission_setup_extraction_point, om_mission_check_extraction_objectives, om_mission_get_objective_completion] tests=[test_R_129_01_it_never_acquires_target_never, test_R_129_02_it_counts_toward_completion_e]
- `313a3-e15-support-units_that_cannot_fight`: symbols=[om_unit_has_non_combat_visual_tag, om_unit_is_non_combat_supported] tests=[test_R_129_03_it_reads_as_non_combat, test_R_129_04_q_129_01_only_convoys]

### S-130
- `314a1-e15-support-the_battlefield_moves`: symbols=[om_drift_interpolate, om_objective_setup_drifting, om_objective_get_center, om_tactical_tick_to, om_objective_is_contested] tests=[test_R_130_01_its_position_interpolation_along_its, test_R_130_02_hold_zone_moves_with_it]
- `314a2-e15-support-the_battlefield_moves`: symbols=[om_structure_init_drifting, om_structure_get_position, om_structure_is_in_capture_radius, om_hazard_spawn_moving_interference, om_hazard_sample_interference] tests=[test_R_130_03_its_capture_radius_spawn_position, test_R_130_04_interference_at_any_point_follows]
- `314a3-e15-support-the_battlefield_moves`: symbols=[om_unit_order_move, om_unit_get_order_destination] tests=[test_R_130_05_convoy_keeps_its_move_order]

### S-131
- `315a1-e15-support-reading_hazards_and_stru`: symbols=[om_render_get_structure_silhouette_id, om_render_get_unit_silhouette_id, om_render_get_owner_color, om_render_is_volume_obscuring, om_hazard_launch_type_count] tests=[test_R_131_01_structures_distinguishable_by_owner_color]
- `315a2-e15-support-reading_hazards_and_stru`: symbols=[om_hazard_get_launch_types, om_hazard_is_enabled_at_launch] tests=[test_R_131_02_it_exactly_one_type_sensor]

## Tests with no unbuilt symbol (already satisfiable)
none

## Symbols with no test (skipped)
Old placeholder symbol(s) no test in this epic calls (R22, re-confirmed): om_support_step. Not carried into the regenerated cards.

## Stories needing more than 6 cards (design-lane question, not decided)
none

## Cards with no acceptance test of their own (design-lane question, not decided)
A card can end up with symbols but zero tests when every test needing them also needs a later card's symbols (the test's own closure is wider than the 5-symbol cap covers in one card). Candidates: (a) merge such a card forward into the next one, exceeding the cap only for this story (needs approval -- sizing caps are fixed); (b) accept the card as a pure prerequisite with no acceptance of its own (needs a card-format change -- card_lint.py currently hard-errors on empty acceptance); (c) leave it as a real card_lint finding and re-cut the test itself so its assertions split the same way the symbols do.
- S-129: `313a1-e15-support-units_that_cannot_fight`

## Cross-epic symbol ownership
- `om_mission_get_objective_completion`: E-10, E-15
- `om_objective_get_center`: E-15, E-17
- `om_tactical_tick`: E-10, E-11, E-14, E-15, E-17
- `om_tactical_tick_to`: E-14, E-15, E-17
- `om_unit_deal_damage`: E-11, E-15
- `om_unit_get_target`: E-12, E-13, E-15
- `om_unit_spawn_combat`: E-15, E-17
