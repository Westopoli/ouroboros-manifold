# Card regen report -- E-13

Module: `csrc/tactical_move.c`. Rules file: `projects/ouroboros/rules/E-13.md`. Bible: `docs/bible/epics/E-13-movement-and-command.md`.

Old placeholder symbol(s) this epic's existing queue cards name: `om_movement_step`.

Cards generated: 14. Distinct symbols carded: 47. Tests assigned to a card: 33.

## Numbering prefixes (per story, reused from the old queue)
- S-095: 290a1-e13-movement-a_force_moves_as_one
- S-096: 291a1-e13-movement-four_commands
- S-097: 292a1-e13-movement-around_not_through
- S-098: 293a-e13-movement-firing_through_friends
- S-099: 294a-e13-movement-speed_is_position
- S-100: 295a-e13-movement-facing
- S-101: 296a-e13-movement-movement_that_reads
- S-102: 297a-e13-movement-same_commands_same_battl

## Cards generated
### S-095
- `290a1-e13-movement-a_force_moves_as_one`: symbols=[om_unit_spawn, om_command_group_move, om_unit_get_current_speed, om_unit_get_destination, om_map_add_obstacle] tests=[test_R_095_01_every_unit_s_speed_capped, test_R_095_02_each_unit_s_destination_click, test_R_095_03_every_unit_s_destination_raw, test_R_095_04_that_unit_s_destination_raw]
- `290a2-e13-movement-a_force_moves_as_one`: symbols=[om_group_is_active, om_command_move] tests=[test_R_095_05_group_terminated, test_R_095_06_that_subset_forms_new_group, test_R_095_07_it_moves_at_its_own]

### S-096
- `291a1-e13-movement-four_commands`: symbols=[om_unit_get_hp, om_unit_attack, om_unit_get_target, om_unit_get_pos, om_command_attack_move] tests=[test_R_096_01_it_acquires_no_target_returns]
- `291a2-e13-movement-four_commands`: symbols=[om_unit_set_hp, om_unit_set_pos, om_command_attack_target, om_unit_set_visible_to_faction, om_visibility_compute] tests=[test_R_096_02_unit_halts_fires_target_dies, test_R_096_03_unit_drops_target_resumes, test_R_096_04_unit_moves_toward_e_if]
- `291a3-e13-movement-four_commands`: symbols=[om_command_activate_ability, om_unit_is_braced, om_unit_has_active_buff, om_command_issue_named, om_command_queue_move] tests=[test_R_096_05_each_unit_with_its_ability, test_R_096_06_it_rejected_with_reason_no]
- `291a4-e13-movement-four_commands`: symbols=[om_command_queue_attack_move, om_unit_get_order_kind, om_replay_get_command_count_at_tick] tests=[test_R_096_07_all_them_applied_before_any]

### S-097
- `292a1-e13-movement-around_not_through`: symbols=[om_navmesh_get_cell_size, om_map_set_obstacle_density, om_navmesh_is_cell_blocked, om_navmesh_find_path, om_navmesh_is_path_straightened] tests=[test_R_097_01_it_100_wu_cells_per]
- `292a2-e13-movement-around_not_through`: symbols=[om_navmesh_get_cache_hits, om_unit_get_facing, om_collision_pass, om_unit_compute_terrain_speed, om_command_direct_move] tests=[test_R_097_02_route_computed_once_cached, test_R_097_03_it_probes_40_wu_ahead, test_R_097_04_it_keeps_that_heading_for, test_R_097_05_they_pushed_apart_along_line, test_R_097_06_its_speed_multiplied_by_1, test_R_097_06_it_moves_0_other_takes, test_R_097_07_lower_unit_id_moves_in, test_R_097_08_they_collide_like_allies_nobody]
- `292a3-e13-movement-around_not_through`: symbols=[om_steering_get_obstacle_repulsion] tests=[test_R_097_09_repulsion_opposes_move_units_following]

### S-098
- `293a-e13-movement-firing_through_friends`: symbols=[om_combat_can_shoot, om_map_add_cover] tests=[test_R_098_01_shot_lands_friendly_units_never, test_R_098_02_shot_blocked_exactly_as_vision]

### S-099
- `294a-e13-movement-speed_is_position`: symbols=[om_unit_engage] tests=[test_R_099_01_strike_wing_reaches_flank_slots]

### S-100
- `295a-e13-movement-facing`: symbols=[om_unit_clear_orders, om_unit_set_facing, om_command_attack_target_kiting] tests=[test_R_100_01_it_faces_target_moving_with, test_R_100_02_turn_rate_capped_at_6, test_R_100_03_it_faces_pursuer]

### S-101
- `296a-e13-movement-movement_that_reads`: symbols=[om_renderer_interpolate_position, om_renderer_interpolate_facing] tests=[test_R_101_02_position_facing_linearly_interpolated_from]

### S-102
- `297a-e13-movement-same_commands_same_battl`: symbols=[om_world_get_state_checksum, om_steering_get_sweep_angle_count, om_steering_get_sweep_angle_at] tests=[test_R_102_01_every_position_facing_target_identical, test_R_102_02_order_fixed_documented_no_wall]

## Tests with no unbuilt symbol (already satisfiable)
- S-099: test_R_099_02_it_covers_150_wu_per
- S-101: test_R_101_01_no_unit_overlaps_another_no

## Symbols with no test (skipped)
Old placeholder symbol(s) no test in this epic calls (R22, re-confirmed): om_movement_step. Not carried into the regenerated cards.

## Stories needing more than 6 cards (design-lane question, not decided)
none

## Cards with no acceptance test of their own (design-lane question, not decided)
A card can end up with symbols but zero tests when every test needing them also needs a later card's symbols (the test's own closure is wider than the 5-symbol cap covers in one card). Candidates: (a) merge such a card forward into the next one, exceeding the cap only for this story (needs approval -- sizing caps are fixed); (b) accept the card as a pure prerequisite with no acceptance of its own (needs a card-format change -- card_lint.py currently hard-errors on empty acceptance); (c) leave it as a real card_lint finding and re-cut the test itself so its assertions split the same way the symbols do.
none

## Cross-epic symbol ownership
- `om_command_activate_ability`: E-11, E-13
- `om_command_attack_move`: E-11, E-12, E-13
- `om_command_attack_target`: E-11, E-13
- `om_command_move`: E-11, E-12, E-13
- `om_map_add_cover`: E-11, E-12, E-13
- `om_map_add_obstacle`: E-12, E-13
- `om_unit_attack`: E-12, E-13
- `om_unit_get_hp`: E-12, E-13
- `om_unit_get_pos`: E-12, E-13
- `om_unit_get_target`: E-12, E-13, E-15
- `om_unit_set_hp`: E-11, E-13
- `om_unit_spawn`: E-11, E-12, E-13
- `om_visibility_compute`: E-12, E-13
- `om_world_get_state_checksum`: E-12, E-13
