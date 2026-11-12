# assemble.py validation report

## ids per epic (bible vs rows)

| epic | rules | invariants | rows parsed | missing | duplicate | unknown |
|---|---|---|---|---|---|---|
| E-01 | 87 | 7 | 94 | 0 | 0 | 0 |
| E-02 | 60 | 6 | 66 | 0 | 0 | 0 |
| E-03 | 31 | 5 | 36 | 0 | 0 | 0 |
| E-04 | 33 | 6 | 39 | 0 | 0 | 0 |
| E-05 | 62 | 6 | 68 | 0 | 0 | 0 |
| E-06 | 46 | 5 | 51 | 0 | 0 | 0 |
| E-07 | 28 | 5 | 33 | 0 | 0 | 0 |
| E-08 | 54 | 5 | 59 | 0 | 0 | 0 |
| E-09 | 40 | 5 | 45 | 0 | 0 | 0 |
| E-10 | 70 | 8 | 78 | 0 | 0 | 0 |
| E-11 | 64 | 6 | 70 | 0 | 0 | 0 |
| E-12 | 31 | 4 | 35 | 0 | 0 | 0 |
| E-13 | 53 | 5 | 58 | 0 | 0 | 0 |
| E-14 | 39 | 5 | 44 | 0 | 0 | 0 |
| E-15 | 41 | 6 | 47 | 0 | 0 | 0 |
| E-16 | 100 | 6 | 106 | 0 | 0 | 0 |
| E-17 | 122 | 9 | 131 | 0 | 0 | 0 |
| E-18 | 50 | 4 | 54 | 0 | 0 | 0 |
| E-19 | 35 | 5 | 40 | 0 | 0 | 0 |
| E-20 | 30 | 3 | 33 | 0 | 0 | 0 |
| E-21 | 30 | 3 | 33 | 0 | 0 | 0 |
| E-22 | 86 | 8 | 94 | 0 | 0 | 0 |

## header totals declared in the inputs vs recomputed (from parsed rows, before normalisation 1)

- E-01.md: declared `proven 4, MISSING 64, MISSING? 6, unbuilt 20`; recomputed `proven 4, MISSING 64, MISSING? 6, unbuilt 20`
- E-02.md: declared `proven 3, MISSING 54, MISSING? 0, unbuilt 9`; recomputed `proven 3, MISSING 54, MISSING? 0, unbuilt 9`
- E-03.md: declared `proven 0, MISSING 34, MISSING? 0, unbuilt 2`; recomputed `proven 0, MISSING 34, MISSING? 0, unbuilt 2`
- E-04.md: declared `proven 5, MISSING 30, MISSING? 0, unbuilt 4`; recomputed `proven 5, MISSING 30, MISSING? 0, unbuilt 4`
- E-05.md: declared `proven 7, MISSING 57, MISSING? 0, unbuilt 4`; recomputed `proven 7, MISSING 57, MISSING? 0, unbuilt 4`
- E-06.md: declared `proven 0, MISSING 47, MISSING? 0, unbuilt 4`; recomputed `proven 0, MISSING 47, MISSING? 0, unbuilt 4`
- E-07.md: declared `proven 0, MISSING 32, MISSING? 0, unbuilt 1`; recomputed `proven 0, MISSING 32, MISSING? 0, unbuilt 1`
- E-08.md: declared `proven 2, MISSING 55, MISSING? 0, unbuilt 2`; recomputed `proven 2, MISSING 55, MISSING? 0, unbuilt 2`
- E-09.md: declared `proven 5, MISSING 35 (rules) + 5 (Invariants) = 40, MISSING? 0, unbuilt 0`; recomputed `proven 5, MISSING 40, MISSING? 0, unbuilt 0`  <-- DIFFERENT
- E-10.md: declared `proven 1, MISSING 52, MISSING? 1, unbuilt 24`; recomputed `proven 1, MISSING 52, MISSING? 1, unbuilt 24`
- E-11.md: declared `proven 0, MISSING 51, MISSING? 2, unbuilt 17`; recomputed `proven 0, MISSING 51, MISSING? 2, unbuilt 17`
- E-12.md: declared `proven 1, MISSING 28, MISSING? 0, unbuilt 6`; recomputed `proven 1, MISSING 28, MISSING? 0, unbuilt 6`
- E-13.md: declared `proven 0, MISSING 46, MISSING? 0, unbuilt 12`; recomputed `proven 0, MISSING 46, MISSING? 0, unbuilt 12`
- E-14.md: declared `proven 0, MISSING 26, MISSING? 0, unbuilt 18`; recomputed `proven 0, MISSING 26, MISSING? 0, unbuilt 18`
- E-15.md: declared `proven 0, MISSING 36, MISSING? 0, unbuilt 11`; recomputed `proven 0, MISSING 36, MISSING? 0, unbuilt 11`
- E-16a.md: declared `proven 0, MISSING 32, MISSING? 8, unbuilt 10`; recomputed `proven 0, MISSING 32, MISSING? 8, unbuilt 10`
- E-16b.md: declared `proven 0, MISSING 27, MISSING? 3, unbuilt 26`; recomputed `proven 0, MISSING 27, MISSING? 3, unbuilt 26`
- E-17a.md: declared `proven 0, MISSING 19, MISSING? 6, unbuilt 36`; recomputed `proven 0, MISSING 19, MISSING? 6, unbuilt 36`
- E-17b.md: declared `proven 0, MISSING 36, MISSING? 5, unbuilt 29`; recomputed `proven 0, MISSING 36, MISSING? 5, unbuilt 29`
- E-18.md: declared `proven 0, MISSING 30, MISSING? 4, unbuilt 20`; recomputed `proven 0, MISSING 30, MISSING? 4, unbuilt 20`
- E-19.md: declared `proven 0, MISSING 24, MISSING? 2, unbuilt 14`; recomputed `proven 0, MISSING 24, MISSING? 2, unbuilt 14`
- E-20.md: declared `proven 0, MISSING 16, MISSING? 2, unbuilt 15`; recomputed `proven 0, MISSING 16, MISSING? 2, unbuilt 15`
- E-21.md: declared `proven 0, MISSING 14, MISSING? 0, unbuilt 19`; recomputed `proven 0, MISSING 14, MISSING? 0, unbuilt 19`
- E-22.md: declared `proven 0, MISSING 17, MISSING? 1, unbuilt 76`; recomputed `proven 0, MISSING 17, MISSING? 1, unbuilt 76`

## repo reference faults (0)


## normalised on qualification 1 (13 proven rows dropped to MISSING)

- E-01 R-002-05: tests/csim/test_PP_C_g4_transfer.py::test_R_002_05_a_transfer_to_the_current_layer_completes_at_once_with_no_window
- E-01 R-004-07: tests/csim/test_E01_R004_07_slope_time.py::test_R_004_07_raider_up_the_slope
- E-01 R-007-01: tests/skilllab/arena/test_stage4_run.py::test_cover_hides_every_pair_whose_segment_crosses_a_box
- E-02 R-013-04: tests/csim/test_E02_S013_military.py::test_R_013_04_recruit_threshold_strictly_greater
- E-02 R-018-04: tests/csim/test_E02_S018_oscillation.py::test_R_018_04_oscillator_nets_zero_over_every_15_tick_window
- E-02 R-160-01: tests/csim/test_E02_S160_drift_gate.py::test_R_160_01_drift_off_leaves_fields_unchanged
- E-08 R-057-02: tests/transport/test_pipe_u_observable.py::test_commander_stays_then_rotates
- E-08 R-061-02: tests/transport/test_pipe_u_observable.py::test_commander_death_ends_the_chapter_and_seats_a_successor
- E-09 R-065-05: tests/transport/test_pipe_u_observable.py::test_chronicle_selection_quotas
- E-09 R-066-01: tests/transport/test_pipe_u_observable.py::test_chronicle_significance_scoring
- E-09 R-068-04: tests/transport/test_pipe_u_observable.py::test_chronicle_entry_text_assembly
- E-09 R-068-06: tests/transport/test_pipe_u_observable.py::test_chronicle_entry_text_assembly
- E-09 R-068-07: tests/transport/test_pipe_u_observable.py::test_chronicle_entry_text_assembly

## client form, unresolved (0: kind client or a .gd test; not normalised)


## proven rows not decidable from the table (1)

- E-01 E-01 Invariant 4: tests/csim/test_E13_R207_06_never_enter_blocked.py::test_R_207_06_twelve_attack_moving_walkers_never_end_a_tick_in_a_blocked_cell (pair absent from table)

## MISSING rows whose candidate the table says does not quote the rule, fails cell without 1 (99)

- E-01 R-001-01: tests/csim/test_PP_move_route.py::test_R_001_01_02_blocked_layers_detour_other_layers_pass_straight_ fails 2,3
- E-01 R-001-02: tests/csim/test_PP_move_route.py::test_R_001_01_02_blocked_layers_detour_other_layers_pass_straight_ fails 3,5
- E-01 R-001-06: tests/csim/test_E01_R001_06_slopes.py::test_R_001_06_every_slope_joins_adjacent_bands_edge_to_edge fails 2,3
- E-01 R-001-07: tests/csim/test_E01_R001_07_walking_kind.py::test_R_001_07_a_walker_never_leaves_masked_cells_over_2 fails 3
- E-01 R-004-02: tests/csim/test_PP_C_g4_transfer.py::test_R_004_02_old_layer_may_attack_until_halfway_new_layer_from fails 2,3
- E-01 R-004-06: tests/csim/test_E01_R004_06_midline.py::test_R_004_06_a_walker_going_up_changes_layer_at_the_midline fails 2
- E-01 R-007-02: tests/csim/test_PP_move_cover.py::test_R_007_01_02_06_vision_follows_cover_height_and_endpoint_exemp fails 3
- E-01 R-007-04: tests/csim/test_E11_S084_flat_damage.py::test_R_084_05_damage_unmodified_e_01_r fails 2,3
- E-01 R-007-05: tests/csim/test_PP_move_cover.py::test_R_007_05_cover_never_blocks_movement fails 3,4
- E-01 R-007-06: tests/csim/test_PP_move_cover.py::test_R_007_01_02_06_vision_follows_cover_height_and_endpoint_exemp fails 3
- E-01 R-008-02: tests/csim/test_PP_C_g5_direct_fire.py::test_R_008_02_idle_and_attack_moving_units_engage_one_layer_ fails 3
- E-01 R-008-04: tests/csim/test_PP_C_g3_direct_fire.py::test_R_008_04_reach_is_not_sight_a_target_in_reach_but_unsee fails 3,4
- E-01 R-162-01: tests/transport/test_pipe_u_observable.py::test_command_ping_reveals_the_enemy_it_is_cast_at fails 2
- E-01 R-164-02: tests/csim/test_PP_C_g5_direct_fire.py::test_R_164_02_a_target_is_engaged_exactly_when_its_offset_is fails 3,4
- E-02 R-012-01: tests/csim/test_E02_S012_composites.py::test_R_012_01_fields_ranged_and_composites_rounded fails 4,5
- E-02 R-012-02: tests/csim/test_E02_S012_composites.py::test_R_012_02_stability_exact fails 5
- E-02 R-012-03: tests/csim/test_E02_S012_composites.py::test_R_012_03_stability_military_penalty fails 5
- E-02 R-012-04: tests/csim/test_E02_S012_composites.py::test_R_012_04_stability_both_penalties fails 5
- E-02 R-012-05: tests/csim/test_E02_S012_composites.py::test_R_012_05_capacity_exact fails 5
- E-02 R-012-06: tests/csim/test_E02_S012_composites.py::test_R_012_06_capacity_both_penalties fails 5
- E-02 R-012-07: tests/csim/test_E02_S012_composites.py::test_R_012_07_empty_region_zeroed_and_never_drifts fails 4
- E-02 R-013-01: tests/csim/test_E02_S013_military.py::test_R_013_01_decay_leg_exact fails 5
- E-02 R-013-02: tests/csim/test_E02_S013_military.py::test_R_013_02_decay_leg_zero_at_full_economy fails 5
- E-02 R-013-03: tests/csim/test_E02_S013_military.py::test_R_013_03_recruit_leg_within_tolerance fails 5
- E-02 R-013-05: tests/csim/test_E02_S013_military.py::test_R_013_05_recruit_zero_at_and_above_ceiling fails 4,5
- E-02 R-013-06: tests/csim/test_E02_S013_military.py::test_R_013_06_conqueror_faction_modifier fails 5
- E-02 R-014-01: tests/csim/test_E02_S014_economy.py::test_R_014_01_growth_drag_no_overcap fails 5
- E-02 R-014-02: tests/csim/test_E02_S014_economy.py::test_R_014_02_overcapacity_decay_exact fails 5
- E-02 R-014-03: tests/csim/test_E02_S014_economy.py::test_R_014_03_overcapacity_zero_at_capacity_boundary fails 5
- E-02 R-014-04: tests/csim/test_E02_S014_economy.py::test_R_014_04_economy_floor_holds_under_negative_drift fails 5
- E-02 R-015-01: tests/csim/test_E02_S015_adjacency.py::test_R_015_01_two_friendly_neighbors_sum fails 5
- E-02 R-015-02: tests/csim/test_E02_S015_adjacency.py::test_R_015_02_single_friendly_neighbor_edge_type_irrelevant fails 5
- E-02 R-015-03: tests/csim/test_E02_S015_adjacency.py::test_R_015_03_hostile_default_contributes_nothing fails 2,5,6
- E-02 R-015-04: tests/csim/test_E02_S015_adjacency.py::test_R_015_04_empty_neighbor_contributes_nothing fails 5
- E-02 R-016-01: tests/csim/test_E02_S016_tension.py::test_R_016_01_full_tension_delta_below_stress_threshold fails 5
- E-02 R-016-02: tests/csim/test_E02_S016_tension.py::test_R_016_02_stress_pressure_exact fails 5
- E-02 R-016-03: tests/csim/test_E02_S016_tension.py::test_R_016_03_subsistence_pressure_exact fails 5
- E-02 R-016-04: tests/csim/test_E02_S016_tension.py::test_R_016_04_subsistence_threshold_at_11 fails 5
- E-02 R-016-05: tests/csim/test_E02_S016_tension.py::test_R_016_05_prosperity_calms_tension fails 5
- E-02 R-017-01: tests/csim/test_E02_S017_population.py::test_R_017_01_growth_branch_exact fails 5
- E-02 R-017-02: tests/csim/test_E02_S017_population.py::test_R_017_02_decline_branch_with_subsistence fails 5
- E-02 R-017-03: tests/csim/test_E02_S017_population.py::test_R_017_03_growth_threshold_at_15 fails 5
- E-02 R-017-04: tests/csim/test_E02_S017_population.py::test_R_017_04_growth_zero_at_population_ceiling fails 5
- E-02 R-018-01: tests/csim/test_E02_S018_oscillation.py::test_R_018_01_oscillator_delta_at_tick_two fails 5
- E-02 R-018-02: tests/csim/test_E02_S018_oscillation.py::test_R_018_02_tick_one_previous_oscillator_is_zero fails 5
- E-02 R-018-03: tests/csim/test_E02_S018_oscillation.py::test_R_018_03_coupling_reads_trend_not_raw fails 2,4
- E-02 R-018-05: tests/csim/test_E02_S018_oscillation.py::test_R_018_05_different_phases_peak_on_different_ticks fails 5
- E-02 R-019-01: tests/csim/test_E02_S019_floor.py::test_R_019_01_economy_floor_holds_under_drift fails 2,5
- E-02 R-019-02: tests/csim/test_E02_S019_floor.py::test_R_019_02_conquest_may_go_below_floor fails 2,5,6
- E-02 R-019-03: tests/csim/test_E02_S019_floor.py::test_R_019_03_subsistence_at_the_floor fails 5
- E-02 R-019-04: tests/csim/test_E02_S019_floor.py::test_R_019_04_drift_alone_may_fall_below_twelve fails 2,5,6
- E-02 R-019-05: tests/csim/test_E02_S019_floor.py::test_R_019_05_population_never_goes_negative fails 4,5
- E-02 R-020-01: tests/csim/test_E02_S020_determinism.py::test_R_020_01_two_runs_same_seed_byte_identical fails 5
- E-02 R-020-02: tests/csim/test_E02_S020_determinism.py::test_R_020_02_same_machine_proxy_repeat_determinism fails 2,5,6
- E-02 R-020-03: tests/csim/test_E02_S020_determinism.py::test_R_020_03_checksum_emitted_only_on_cadence fails 5
- E-02 R-160-02: tests/csim/test_E02_S160_drift_gate.py::test_R_160_02_default_world_has_only_drift_on fails 2,5
- E-02 R-160-03: tests/csim/test_E02_S160_drift_gate.py::test_R_160_03_budget_step_reads_pre_drift_economy fails 5
- E-02 R-160-04: tests/csim/test_E02_S160_drift_gate.py::test_R_160_04_drift_off_emits_no_trace_rows fails 2,5?
- E-04 R-030-01: tests/csim/test_E04_S030_the_launch_event_library.py::test_R_030_01_it_contains_exactly_26_templates fails 2,5
- E-08 R-055-02: tests/csim/test_core_mission_phase_gate.py::test_R_055_02_no_strategic_tick_runs_with_tactical_map_l fails 4,5
- E-08 R-058-02: tests/csim/test_E08_S058_previous_pool_chapter_ago.py::test_R_058_02_only_the_lineage_played_a_chapt fails 2,5
- E-08 R-058-05: tests/csim/test_E08_S058_B3_rivals_wired_through_mission_end.py::test_R_058_05_mission_end_tags_the_ fails 5
- E-08 R-061-04: tests/csim/test_core_commander_death_ledger.py::test_R_061_04_commander_death_records_the_mission_re fails 2,5?
- E-08 R-062-02: tests/csim/test_E08_S062_collapse_pick.py::test_R_062_02_q_062_01_the_collapse_jump_applies_the_pool fails 2,5
- E-09 R-065-01: tests/transport/test_pipe_u_observable.py::test_chronicle_selection_quotas fails 5
- E-09 R-065-02: tests/csim/test_E09_B5_consequence_entry.py::test_R_065_02_entry_one_is_the_consequence_after_a_succ fails 2,5
- E-09 R-066-05: tests/transport/test_pipe_u_observable.py::test_chronicle_significance_scoring fails 2,4
- E-09 R-068-01: tests/transport/test_pipe_u_observable.py::test_chronicle_entry_text_assembly fails 2,5
- E-09 R-069-07: tests/csim/test_E09_GC2_mentions.py::test_R_069_07_offsets_point_at_the_exact_name_in_the_text_as_se fails 2
- E-13 R-095-01: tests/csim/test_PP_move_group.py::test_R_095_01_group_moves_at_the_slowest_members_pace fails 3,5
- E-13 R-095-06: tests/csim/test_PP_move_group.py::test_R_095_06_a_subset_forms_its_own_group_and_the_old_group_conti fails 5
- E-13 R-097-03: tests/csim/test_PP_move_steer_face.py::test_R_097_03_sweep_order_first_clear_none_clear_straight fails 3,5
- E-13 R-097-04: tests/csim/test_PP_move_steer_face.py::test_R_097_04_detour_held_for_60_wu_of_distance_moved fails 3,5
- E-13 R-097-05: tests/csim/test_PP_move_collision.py::test_R_097_05_two_moving_units_split_the_push_to_30_apart fails 3,5
- E-13 R-097-06: tests/csim/test_PP_move_route.py::test_R_097_06_terrain_slow_in_density_0_3_to_0_7 fails 3,5
- E-13 R-097-10: tests/csim/test_PP_move_collision_a5.py::test_R_097_10_unit_walking_into_a_stopped_one_is_pushed_out fails 3
- E-13 R-099-03: tests/csim/test_core_tick_period.py::test_R_099_03_period_2_above_1000_live_units fails 5
- E-13 R-099-04: tests/csim/test_PP_move_collision.py::test_R_099_04_within_slot_radius_arrives_where_it_stands fails 3,5
- E-13 R-099-05: tests/csim/test_PP_unit_giveup.py::test_R_099_05_blocked_slot_gives_up_at_exactly_40_ticks_within_75 fails 3,5
- E-13 R-101-01: tests/csim/test_PP_move_collision_a5.py::test_R_101_01_shared_scene_keeps_every_pair_at_29_over_200_ fails 2,3,5
- E-15 R-127-01: tests/csim/test_PP_move_capture.py::test_R_127_01_exactly_one_nonowner_faction_captures_in_10_s fails 5?
- E-15 R-127-02: tests/csim/test_PP_move_capture.py::test_R_127_02_a_second_faction_arriving_resets_progress_to_zero fails 2,5?
- E-15 R-218-02: tests/csim/test_VG_E_e1h.py::test_owner_and_state_mirror_the_structure fails 2,5
- E-15 R-218-06: tests/csim/test_VG_E_ke2.py::test_R_218_06_starting_force_at_half_share_is_600 fails 2,5
- E-16 R-103-01: tests/test_tactical_camera.gd::_test_a18_home_key_R103_01 fails 2,3,5?
- E-16 R-103-02: tests/test_tactical_camera.gd::_test_wheel_zoom_bounded_R103_01_R103_02 fails 3,4,5
- E-16 R-103-04: tests/test_vg_a_a16.gd::_test_camera fails 4,5?
- E-16 R-104-09: tests/test_vg_a_a16.gd::_test_five_buttons fails 2,5?
- E-16 R-105-03: tests/test_vg_a_a16.gd::_test_focus_key fails 5?
- E-17 R-191-01: tests/csim/test_VG_P_p1_layout.py::test_two_seeds_differ_on_the_flat_stub fails 2,3,5?
- E-17 R-191-02: tests/csim/test_VG_P_p1_layout.py::test_order_of_places fails 3,5?
- E-17 R-191-03: tests/csim/test_VG_P_p1_layout.py::test_no_two_settlements_or_bases_within_4000 fails 2,3,5?
- E-17 R-191-04: tests/csim/test_VG_P_p1_layout.py::test_resource_sites_are_equidistant fails 2,3,5?
- E-17 R-191-05: tests/csim/test_VG_P_p1_layout.py::test_expansion_sites_only_for_towns_without_a_resource_site fails 2,3,5?
- E-17 R-191-06: tests/csim/test_VG_P_p1_layout.py::test_ages_sides_and_richness_by_kind fails 2,3,5?
- E-17 R-193-03: tests/csim/test_VG_E_e1r.py::test_the_natural_lots_under_the_footprint_are_gone_and_the_placed_lot_i fails 2,5?
- E-17 R-246-04: tests/qa/desktop/plays/D/S-246.py::test_s246_space_sheets_rings_tube fails 3,5?
- E-19 R-139-01: tests/csim/test_net_checksum.py::test_R_139_01_combined_stable_across_two_processes fails 2,5
- E-19 R-143-03: tests/qa/desktop/plays/F/S-143.py::test_s143_two_players_lobby_narrows_to_common_era fails 5

## parse notes (49)

- E-02.md:7 R-012-01 candidate file given without directory, resolved test_E02_S012_composites.py -> tests/csim/test_E02_S012_composites.py
- E-02.md:8 R-012-02 candidate file given without directory, resolved test_E02_S012_composites.py -> tests/csim/test_E02_S012_composites.py
- E-02.md:9 R-012-03 candidate file given without directory, resolved test_E02_S012_composites.py -> tests/csim/test_E02_S012_composites.py
- E-02.md:10 R-012-04 candidate file given without directory, resolved test_E02_S012_composites.py -> tests/csim/test_E02_S012_composites.py
- E-02.md:11 R-012-05 candidate file given without directory, resolved test_E02_S012_composites.py -> tests/csim/test_E02_S012_composites.py
- E-02.md:12 R-012-06 candidate file given without directory, resolved test_E02_S012_composites.py -> tests/csim/test_E02_S012_composites.py
- E-02.md:13 R-012-07 candidate file given without directory, resolved test_E02_S012_composites.py -> tests/csim/test_E02_S012_composites.py
- E-02.md:14 R-013-01 candidate file given without directory, resolved test_E02_S013_military.py -> tests/csim/test_E02_S013_military.py
- E-02.md:15 R-013-02 candidate file given without directory, resolved test_E02_S013_military.py -> tests/csim/test_E02_S013_military.py
- E-02.md:16 R-013-03 candidate file given without directory, resolved test_E02_S013_military.py -> tests/csim/test_E02_S013_military.py
- E-02.md:18 R-013-05 candidate file given without directory, resolved test_E02_S013_military.py -> tests/csim/test_E02_S013_military.py
- E-02.md:19 R-013-06 candidate file given without directory, resolved test_E02_S013_military.py -> tests/csim/test_E02_S013_military.py
- E-02.md:20 R-014-01 candidate file given without directory, resolved test_E02_S014_economy.py -> tests/csim/test_E02_S014_economy.py
- E-02.md:21 R-014-02 candidate file given without directory, resolved test_E02_S014_economy.py -> tests/csim/test_E02_S014_economy.py
- E-02.md:22 R-014-03 candidate file given without directory, resolved test_E02_S014_economy.py -> tests/csim/test_E02_S014_economy.py
- E-02.md:23 R-014-04 candidate file given without directory, resolved test_E02_S014_economy.py -> tests/csim/test_E02_S014_economy.py
- E-02.md:24 R-015-01 candidate file given without directory, resolved test_E02_S015_adjacency.py -> tests/csim/test_E02_S015_adjacency.py
- E-02.md:25 R-015-02 candidate file given without directory, resolved test_E02_S015_adjacency.py -> tests/csim/test_E02_S015_adjacency.py
- E-02.md:26 R-015-03 candidate file given without directory, resolved test_E02_S015_adjacency.py -> tests/csim/test_E02_S015_adjacency.py
- E-02.md:27 R-015-04 candidate file given without directory, resolved test_E02_S015_adjacency.py -> tests/csim/test_E02_S015_adjacency.py
- E-02.md:28 R-016-01 candidate file given without directory, resolved test_E02_S016_tension.py -> tests/csim/test_E02_S016_tension.py
- E-02.md:29 R-016-02 candidate file given without directory, resolved test_E02_S016_tension.py -> tests/csim/test_E02_S016_tension.py
- E-02.md:30 R-016-03 candidate file given without directory, resolved test_E02_S016_tension.py -> tests/csim/test_E02_S016_tension.py
- E-02.md:31 R-016-04 candidate file given without directory, resolved test_E02_S016_tension.py -> tests/csim/test_E02_S016_tension.py
- E-02.md:32 R-016-05 candidate file given without directory, resolved test_E02_S016_tension.py -> tests/csim/test_E02_S016_tension.py
- E-02.md:33 R-017-01 candidate file given without directory, resolved test_E02_S017_population.py -> tests/csim/test_E02_S017_population.py
- E-02.md:34 R-017-02 candidate file given without directory, resolved test_E02_S017_population.py -> tests/csim/test_E02_S017_population.py
- E-02.md:35 R-017-03 candidate file given without directory, resolved test_E02_S017_population.py -> tests/csim/test_E02_S017_population.py
- E-02.md:36 R-017-04 candidate file given without directory, resolved test_E02_S017_population.py -> tests/csim/test_E02_S017_population.py
- E-02.md:37 R-018-01 candidate file given without directory, resolved test_E02_S018_oscillation.py -> tests/csim/test_E02_S018_oscillation.py
- E-02.md:38 R-018-02 candidate file given without directory, resolved test_E02_S018_oscillation.py -> tests/csim/test_E02_S018_oscillation.py
- E-02.md:39 R-018-03 candidate file given without directory, resolved test_E02_S018_oscillation.py -> tests/csim/test_E02_S018_oscillation.py
- E-02.md:41 R-018-05 candidate file given without directory, resolved test_E02_S018_oscillation.py -> tests/csim/test_E02_S018_oscillation.py
- E-02.md:42 R-019-01 candidate file given without directory, resolved test_E02_S019_floor.py -> tests/csim/test_E02_S019_floor.py
- E-02.md:43 R-019-02 candidate file given without directory, resolved test_E02_S019_floor.py -> tests/csim/test_E02_S019_floor.py
- E-02.md:44 R-019-03 candidate file given without directory, resolved test_E02_S019_floor.py -> tests/csim/test_E02_S019_floor.py
- E-02.md:45 R-019-04 candidate file given without directory, resolved test_E02_S019_floor.py -> tests/csim/test_E02_S019_floor.py
- E-02.md:46 R-019-05 candidate file given without directory, resolved test_E02_S019_floor.py -> tests/csim/test_E02_S019_floor.py
- E-02.md:47 R-020-01 candidate file given without directory, resolved test_E02_S020_determinism.py -> tests/csim/test_E02_S020_determinism.py
- E-02.md:48 R-020-02 candidate file given without directory, resolved test_E02_S020_determinism.py -> tests/csim/test_E02_S020_determinism.py
- E-02.md:49 R-020-03 candidate file given without directory, resolved test_E02_S020_determinism.py -> tests/csim/test_E02_S020_determinism.py
- E-02.md:51 R-160-02 candidate file given without directory, resolved test_E02_S160_drift_gate.py -> tests/csim/test_E02_S160_drift_gate.py
- E-02.md:52 R-160-03 candidate file given without directory, resolved test_E02_S160_drift_gate.py -> tests/csim/test_E02_S160_drift_gate.py
- E-02.md:53 R-160-04 candidate file given without directory, resolved test_E02_S160_drift_gate.py -> tests/csim/test_E02_S160_drift_gate.py
- E-02.md:67 E-02 Invariant 1 candidate file given without directory, resolved test_E02_gate_drift_trajectory.py -> tests/csim/test_E02_gate_drift_trajectory.py
- E-02.md:68 E-02 Invariant 2 candidate file given without directory, resolved test_E02_gate_drift_trajectory.py -> tests/csim/test_E02_gate_drift_trajectory.py
- E-02.md:70 E-02 Invariant 4 candidate file given without directory, resolved test_E02_S018_oscillation.py -> tests/csim/test_E02_S018_oscillation.py
- E-02.md:71 E-02 Invariant 5 candidate file given without directory, resolved test_E02_S020_determinism.py -> tests/csim/test_E02_S020_determinism.py
- E-02.md:72 E-02 Invariant 6 candidate file given without directory, resolved test_E02_gate_drift_trajectory.py -> tests/csim/test_E02_gate_drift_trajectory.py
