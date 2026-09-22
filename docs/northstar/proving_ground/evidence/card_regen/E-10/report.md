# Card regen report -- E-10

Module: `csrc/mission.c`. Rules file: `projects/ouroboros/rules/E-10.md`. Bible: `docs/bible/epics/E-10-missions.md`.

Old placeholder symbol(s) this epic's existing queue cards name: `om_mission_step`.

Cards generated: 20. Distinct symbols carded: 87. Tests assigned to a card: 45.

## Numbering prefixes (per story, reused from the old queue)
- S-072: 260a1-e10-missions-orders_come_from_where_t
- S-073: 261a1-e10-missions-ten_kinds_of_trouble
- S-074: 262a1-e10-missions-you_get_what_the_civiliz
- S-075: 263a1-e10-missions-hold_destroy_escort_surv
- S-076: 264a1-e10-missions-the_clock
- S-077: 265a-e10-missions-five_ways_it_can_go
- S-078: 266a1-e10-missions-a_battle_becomes_history
- S-079: 267a-e10-missions-orders_not_menus
- S-080: 268a-e10-missions-difficulty_is_scarcity_n

## Cards generated
### S-072
- `260a1-e10-missions-orders_come_from_where_t`: symbols=[om_mission_build_candidate_pool, om_mission_candidates, om_mission_set_conflict_context, om_mission_set_revolt_events, om_mission_compute_urgency] tests=[test_R_072_01_each_region_archetype_pair_whose, test_R_072_02_urgency_clamp_0_4_deficit]
- `260a2-e10-missions-orders_come_from_where_t`: symbols=[om_mission_set_lineage_context, om_mission_compute_relevance, om_mission_compute_preference, om_mission_set_preference, om_mission_candidate_score] tests=[test_R_072_03_relevance_clamp_0_4_lineage, test_R_072_04_it_0_1_for_archetype]
- `260a3-e10-missions-orders_come_from_where_t`: symbols=[om_mission_inject_candidate, om_mission_select, om_mission_get_candidate_score, om_mission_fallback_archetype, om_mission_fallback_region] tests=[test_R_072_05_score_0_5_urgency_0, test_R_072_06_urgency_0_8_it_beats, test_R_072_07_q_072_01]

### S-073
- `261a1-e10-missions-ten_kinds_of_trouble`: symbols=[om_mission_load_launch_library, om_mission_archetype_count, om_mission_get_archetype_metadata, om_mission_set_archetype_profile, om_mission_allocate_force_profile] tests=[test_R_073_01_it_contains_exactly_these_archetypes, test_R_073_02_its_asset_profile_ratio_per]
- `261a2-e10-missions-ten_kinds_of_trouble`: symbols=[om_mission_get_compatible_layouts, om_mission_select_layout, om_mission_setup, om_mission_get_briefing_text, om_mission_get_enemy_power] tests=[test_R_073_03_its_compatibility_filters_select_layouts]
- `261a3-e10-missions-ten_kinds_of_trouble`: symbols=[om_mission_get_player_parity, om_mission_get_time_limit] tests=[test_R_073_04_briefing_notes_it_nothing_mechanical]

### S-074
- `262a1-e10-missions-you_get_what_the_civiliz`: symbols=[om_mission_compute_enemy_power, om_mission_compute_base_parity, om_mission_compute_difficulty_parity, om_mission_fill_player_force, om_mission_set_player_units] tests=[test_R_074_01_it_attacker_s_committed_budget, test_R_074_02_base_parity_piecewise_linear_through, test_R_074_03_it_max_base_0_95, test_R_074_04_its_budget_p_parity_filled]
- `262a2-e10-missions-you_get_what_the_civiliz`: symbols=[om_mission_apply_capacity_shortfall, om_mission_get_player_units, om_mission_get_shortfall_text, om_unit_power] tests=[test_R_074_05_20_percent_player_s_units, test_R_074_06_it_comes_from_interim_total]

### S-075
- `263a1-e10-missions-hold_destroy_escort_surv`: symbols=[om_mission_build_objectives, om_mission_objective_count, om_mission_get_objectives, om_mission_setup_hold_zone, om_mission_eval_hold_zone] tests=[test_R_075_01_there_exactly_one_primary_objective]
- `263a2-e10-missions-hold_destroy_escort_surv`: symbols=[om_mission_get_objective_completion, om_mission_setup_destroy_targets, om_mission_eval_destroy_targets, om_mission_setup_escort, om_mission_eval_escort] tests=[test_R_075_02_hold_timer_advances_only_while, test_R_075_03_completion_destroyed_designated_targets_total, test_R_075_04_completion_escort_units_that_reached]
- `263a3-e10-missions-hold_destroy_escort_surv`: symbols=[om_mission_setup_survive, om_mission_eval_survive, om_mission_setup_eliminate, om_mission_eval_eliminate, om_mission_setup_termination] tests=[test_R_075_05_completion_elapsed_required_0_if, test_R_075_06_completion_enemy_hp_destroyed_initial]
- `263a4-e10-missions-hold_destroy_escort_surv`: symbols=[om_mission_check_terminated] tests=[test_R_075_07_it_ends_on_first_every]

### S-076
- `264a1-e10-missions-the_clock`: symbols=[om_mission_compute_time_limit, om_archetype_base_time_ticks, om_mission_setup_tactical, om_mission_set_objective_completion, om_tactical_tick] tests=[test_R_076_01_limit_max_b_1_0, test_R_076_02_they_minutes_in_table_q]
- `264a2-e10-missions-the_clock`: symbols=[om_mission_is_ended, om_mission_get_objective_score, om_mission_end] tests=[test_R_076_03_current_objective_completion_values_final]

### S-077
- `265a-e10-missions-five_ways_it_can_go`: symbols=[om_mission_compute_final_score, om_mission_compute_retention, om_mission_classify_band, om_mission_eval_commander_fate, om_mission_get_band] tests=[test_R_077_01_final_0_75_o_0, test_R_077_02_final_t1_total_failure_t2, test_R_077_03_commander_fate_killed_else_survived, test_R_077_04_band_revealed_only_at_mission]

### S-078
- `266a1-e10-missions-a_battle_becomes_history`: symbols=[om_consequence_eval_delta_deficit, om_consequence_eval_delta_current, om_consequence_apply_clamped, om_mission_apply_consequences, om_world_set_tick] tests=[test_R_078_01_each_delta_either_deficit_form, test_R_078_02_military_12_0_tension_5, test_R_078_03_military_3_0]
- `266a2-e10-missions-a_battle_becomes_history`: symbols=[om_region_get_owner, om_region_get_held_since, om_mission_resolve_refusal, om_mission_get_deployed_force_count, om_time_jump_run] tests=[test_R_078_04_region_s_owner_becomes_player, test_R_078_05_band_refusal_no_force_deployed]
- `266a3-e10-missions-a_battle_becomes_history`: symbols=[om_chronicle_has_mission_consequence_flag, om_set_neighbors, om_mission_apply_target_adjacent_player] tests=[test_R_078_06_resulting_events_carry_mission_consequence, test_R_078_07_delta_applies_to_every_player]

### S-079
- `267a-e10-missions-orders_not_menus`: symbols=[om_mission_assemble_briefing, om_mission_get_briefing_controls, om_mission_can_edit_loadout, om_mission_get_debrief] tests=[test_R_079_01_it_has_exactly_situation_objective, test_R_079_02_only_controls_accept_refuse_there, test_R_079_03_it_shows_band_objectives_with, test_R_079_04_it_contains_no_raw_field]

### S-080
- `268a-e10-missions-difficulty_is_scarcity_n`: symbols=[om_unit_get_profile, om_mission_compute_parity, om_mission_get_archetype_preference_weight, om_mission_set_candidate_viable, om_mission_select_candidate] tests=[test_R_080_01_both_sides_draw_from_same, test_R_080_02_r_074_03_applies_nothing, test_R_080_03_rare_archetype_can_still_be]

## Tests with no unbuilt symbol (already satisfiable)
none

## Symbols with no test (skipped)
Old placeholder symbol(s) no test in this epic calls (R22, re-confirmed): om_mission_step. Not carried into the regenerated cards.

## Stories needing more than 6 cards (design-lane question, not decided)
none

## Cards with no acceptance test of their own (design-lane question, not decided)
A card can end up with symbols but zero tests when every test needing them also needs a later card's symbols (the test's own closure is wider than the 5-symbol cap covers in one card). Candidates: (a) merge such a card forward into the next one, exceeding the cap only for this story (needs approval -- sizing caps are fixed); (b) accept the card as a pure prerequisite with no acceptance of its own (needs a card-format change -- card_lint.py currently hard-errors on empty acceptance); (c) leave it as a real card_lint finding and re-cut the test itself so its assertions split the same way the symbols do.
none

## Cross-epic symbol ownership
- `om_mission_compute_parity`: E-10, E-14
- `om_mission_end`: E-10, E-14
- `om_mission_get_objective_completion`: E-10, E-15
- `om_tactical_tick`: E-10, E-11, E-14, E-15, E-17
- `om_time_jump_run`: E-08, E-10
- `om_world_set_tick`: E-06, E-10
