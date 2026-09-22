# Card regen report -- E-14

Module: `csrc/enemy_macro.c`. Rules file: `projects/ouroboros/rules/E-14.md`. Bible: `docs/bible/epics/E-14-enemy-macro-behavior.md`.

Old placeholder symbol(s) this epic's existing queue cards name: `om_enemy_macro_step`.

Cards generated: 14. Distinct symbols carded: 60. Tests assigned to a card: 21.

## Numbering prefixes (per story, reused from the old queue)
- S-120: 300a1-e14-enemy-five_behaviors_three_moo
- S-121: 301a1-e14-enemy-timers_and_thresholds_wi
- S-122: 302a1-e14-enemy-forces_that_notice_each_
- S-123: 303a1-e14-enemy-the_enemy_replays_like_i
- S-124: 304a1-e14-enemy-rare_surprises
- S-125: 305a1-e14-enemy-how_hard_the_enemy_tries

## Cards generated
### S-120
- `300a1-e14-enemy-five_behaviors_three_moo`: symbols=[om_macro_validate_state, om_macro_execute_behavior, om_macro_set_state, om_macro_is_hidden, om_macro_trigger_ambush] tests=[test_R_120_01_its_behavior_one_advance_defend]
- `300a2-e14-enemy-five_behaviors_three_moo`: symbols=[om_macro_get_behavior, om_macro_get_modifier, om_macro_enemy_leaves_trigger, om_macro_get_speed_multiplier, om_macro_get_phased_subgroups] tests=[test_R_120_02_force_attack_moves_toward_its, test_R_120_03_force_s_move_speed_0]
- `300a3-e14-enemy-five_behaviors_three_moo`: symbols=[om_macro_evaluation_interval_ticks, om_macro_tick, om_macro_has_evaluated, om_macro_get_last_issued_command_type] tests=[test_R_120_04_it_runs_every_40_ticks]

### S-121
- `301a1-e14-enemy-timers_and_thresholds_wi`: symbols=[om_macro_get_threshold_noise, om_macro_get_timer_noise, om_macro_eval_timer_transition, om_macro_resolve_conflict, om_macro_resolve_conflict_types] tests=[test_R_121_01_condition_compared_against_its_noised, test_R_121_02_it_fires_regardless_tactical_state, test_R_121_03_threshold_wins_except_that_retreat]
- `301a2-e14-enemy-timers_and_thresholds_wi`: symbols=[om_macro_set_hook_true, om_macro_set_base_transition_true, om_macro_eval_transitions, om_macro_validate_condition_name] tests=[test_R_121_04_force_transitions_at_once_before, test_R_121_05_q_121_01_code_returns]

### S-122
- `302a1-e14-enemy-forces_that_notice_each_`: symbols=[om_macro_init_force, om_macro_bus_set_flag, om_macro_bus_get_flag, om_macro_bind_hook_flag, om_macro_eval_hook_flag] tests=[test_R_122_01_it_runs_its_own_script, test_R_122_02_any_other_force_s_hook]
- `302a2-e14-enemy-forces_that_notice_each_`: symbols=[om_macro_bus_register_vocab, om_macro_validate_bus_flag, om_macro_set_force_hp_pct, om_macro_update_bus_runner, om_macro_player_enter_objective] tests=[test_R_122_03_every_flag_it_reads_or]
- `302a3-e14-enemy-forces_that_notice_each_`: symbols=[om_macro_bus_get_active_flags_count] tests=[test_R_122_04_typical_script_fires_2_to]

### S-123
- `303a1-e14-enemy-the_enemy_replays_like_i`: symbols=[om_mission_init_seed, om_tactical_tick, om_replay_command_count, om_replay_get_commands, om_replay_log_command] tests=[test_R_123_01_every_enemy_command_identical_on, test_R_123_02_they_appear_in_same_replay]
- `303a2-e14-enemy-the_enemy_replays_like_i`: symbols=[om_macro_reads_player_visibility_set, om_macro_mutates_unit_stats, om_macro_issues_illegal_command] tests=[test_R_123_03_it_never_reads_player_s]

### S-124
- `304a1-e14-enemy-rare_surprises`: symbols=[om_mission_get_external_reinforcement_prob, om_mission_schedule_external_reinforcement, om_mission_get_reinforcement_foreshadow_text, om_mission_set_external_reinforcement, om_tactical_tick_to] tests=[test_R_124_01_wave_scheduled_with_probability_p]
- `304a2-e14-enemy-rare_surprises`: symbols=[om_mission_check_external_reinforcements, om_mission_is_reinforcement_spawned, om_mission_get_reinforcement_spawn_pos, om_map_is_edge_coord] tests=[test_R_124_02_units_enter_at_map_edge]

### S-125
- `305a1-e14-enemy-how_hard_the_enemy_tries`: symbols=[om_mission_compute_parity, om_macro_get_eval_interval, om_unit_get_decision_loop_ptr, om_unit_get_base_hp, om_session_capture_enable] tests=[test_R_125_01_only_force_parity_e_10, test_R_125_02_their_decision_loop_stats_abilities]
- `305a2-e14-enemy-how_hard_the_enemy_tries`: symbols=[om_session_capture_is_enabled, om_mission_end, om_session_capture_get_size, om_session_capture_read] tests=[test_R_125_03_command_streams_outcomes_captured_for]

## Tests with no unbuilt symbol (already satisfiable)
- S-122: test_R_122_05_each_force_s_timer_noise

## Symbols with no test (skipped)
Old placeholder symbol(s) no test in this epic calls (R22, re-confirmed): om_enemy_macro_step. Not carried into the regenerated cards.

## Stories needing more than 6 cards (design-lane question, not decided)
none

## Cards with no acceptance test of their own (design-lane question, not decided)
A card can end up with symbols but zero tests when every test needing them also needs a later card's symbols (the test's own closure is wider than the 5-symbol cap covers in one card). Candidates: (a) merge such a card forward into the next one, exceeding the cap only for this story (needs approval -- sizing caps are fixed); (b) accept the card as a pure prerequisite with no acceptance of its own (needs a card-format change -- card_lint.py currently hard-errors on empty acceptance); (c) leave it as a real card_lint finding and re-cut the test itself so its assertions split the same way the symbols do.
none

## Cross-epic symbol ownership
- `om_mission_compute_parity`: E-10, E-14
- `om_mission_end`: E-10, E-14
- `om_tactical_tick`: E-10, E-11, E-14, E-15, E-17
- `om_tactical_tick_to`: E-14, E-15, E-17
