# Card regen report -- E-12

Module: `csrc/fog.c`. Rules file: `projects/ouroboros/rules/E-12.md`. Bible: `docs/bible/epics/E-12-fog-and-sensors.md`.

Old placeholder symbol(s) this epic's existing queue cards name: `om_fog_step`.

Cards generated: 12. Distinct symbols carded: 46. Tests assigned to a card: 23.

## Numbering prefixes (per story, reused from the old queue)
- S-089: 280a1-e12-fog-i_see_what_my_units_see
- S-090: 281a-e12-fog-hiding_in_the_storm
- S-091: 282a1-e12-fog-standing_high
- S-092: 283a1-e12-fog-recon_then_fog
- S-093: 284a1-e12-fog-fog_is_for_the_player_no
- S-094: 285a-e12-fog-how_fog_looks

## Cards generated
### S-089
- `280a1-e12-fog-i_see_what_my_units_see`: symbols=[om_unit_spawn, om_map_add_interference_zone, om_map_add_cover, om_visibility_compute, om_unit_can_see] tests=[test_R_089_01_its_effective_radius_r_1, test_R_089_06_b_seeing_computed_independently_asymmetric]
- `280a2-e12-fog-i_see_what_my_units_see`: symbols=[om_player_can_see, om_client_snapshot_read, om_tactical_step, om_unit_teleport, om_player_can_see_friendly] tests=[test_R_089_02_player_visible_enemy_list_their, test_R_089_03_it_not_drawn_its_hp, test_R_089_04_it_recomputed_every_tick_from, test_R_089_05_friendly_units_always_visible_to]

### S-090
- `281a-e12-fog-hiding_in_the_storm`: symbols=[om_zone_sample_interference, om_map_add_moving_interference_zone] tests=[test_R_090_01_interference_0_3, test_R_090_02_combined_interference_clamped_to_0, test_R_090_03_only_observer_s_own_interference, test_R_090_04_interference_at_fixed_point_changes, test_R_090_05_value_per_layer]

### S-091
- `282a1-e12-fog-standing_high`: symbols=[om_map_add_vantage_node, om_unit_get_cross_layer_factor, om_set_era_flag, om_unit_spawn_with_elevation, om_unit_get_effective_sensor_radius_to_target_elevation] tests=[test_R_091_01_cross_layer_factors_double_extend, test_R_091_02_observer_s_effective_radius_multiplied]
- `282a2-e12-fog-standing_high`: symbols=[om_set_era_name, om_unit_get_hp, om_unit_attack] tests=[test_R_091_03_it_affects_sensors_only_never]

### S-092
- `283a1-e12-fog-recon_then_fog`: symbols=[om_mission_set_phase, om_map_add_obstacle, om_map_add_hazard_zone, om_map_add_spine_node, om_map_add_structure] tests=[]
- `283a2-e12-fog-recon_then_fog`: symbols=[om_map_add_spawn_point, om_recon_is_feature_visible, om_recon_is_enemy_visible, om_recon_is_structure_ownership_visible, om_recon_is_spawn_point_visible] tests=[test_R_092_01_every_obstacle_cover_cluster_hazard]
- `283a3-e12-fog-recon_then_fog`: symbols=[om_command_move, om_mission_get_clock, om_mission_is_started, om_unit_get_pos, om_mission_begin] tests=[test_R_092_02_it_has_not_started_no]
- `283a4-e12-fog-recon_then_fog`: symbols=[om_mission_get_phase, om_player_can_see_unit, om_recon_get_terrain_visibility_ratio] tests=[test_R_092_03_fog_applies_per_s_089, test_R_092_04_terrain_visibility_complete_regardless_world]

### S-093
- `284a1-e12-fog-fog_is_for_the_player_no`: symbols=[om_visibility_set_player_fog, om_command_attack_move, om_world_get_state_checksum, om_unit_acquire_target, om_unit_get_target] tests=[test_R_093_01_traces_identical, test_R_093_02_it_uses_its_own_visible]
- `284a2-e12-fog-fog_is_for_the_player_no`: symbols=[om_strategic_agent_read_region_field] tests=[test_R_093_03_they_read_every_neighbor_region]

### S-094
- `285a-e12-fog-how_fog_looks`: symbols=[om_fog_get_treatment_at, om_fog_get_drawn_sensor_circle_radius] tests=[test_R_094_01_revealed_area_fogged_area_interference, test_R_094_02_its_own_sensor_circle_visibly]

## Tests with no unbuilt symbol (already satisfiable)
none

## Symbols with no test (skipped)
Old placeholder symbol(s) no test in this epic calls (R22, re-confirmed): om_fog_step. Not carried into the regenerated cards.

## Stories needing more than 6 cards (design-lane question, not decided)
none

## Cards with no acceptance test of their own (design-lane question, not decided)
A card can end up with symbols but zero tests when every test needing them also needs a later card's symbols (the test's own closure is wider than the 5-symbol cap covers in one card). Candidates: (a) merge such a card forward into the next one, exceeding the cap only for this story (needs approval -- sizing caps are fixed); (b) accept the card as a pure prerequisite with no acceptance of its own (needs a card-format change -- card_lint.py currently hard-errors on empty acceptance); (c) leave it as a real card_lint finding and re-cut the test itself so its assertions split the same way the symbols do.
- S-092: `283a1-e12-fog-recon_then_fog`

## Cross-epic symbol ownership
- `om_command_attack_move`: E-11, E-12, E-13
- `om_command_move`: E-11, E-12, E-13
- `om_map_add_cover`: E-11, E-12, E-13
- `om_map_add_obstacle`: E-12, E-13
- `om_tactical_step`: E-08, E-11, E-12
- `om_unit_attack`: E-12, E-13
- `om_unit_get_hp`: E-12, E-13
- `om_unit_get_pos`: E-12, E-13
- `om_unit_get_target`: E-12, E-13, E-15
- `om_unit_spawn`: E-11, E-12, E-13
- `om_unit_teleport`: E-11, E-12
- `om_visibility_compute`: E-12, E-13
- `om_world_get_state_checksum`: E-12, E-13
