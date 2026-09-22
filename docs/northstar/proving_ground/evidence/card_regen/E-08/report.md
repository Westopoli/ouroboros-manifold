# Card regen report -- E-08

Module: `csrc/generational.c`. Rules file: `projects/ouroboros/rules/E-08.md`. Bible: `docs/bible/epics/E-08-generational-structure.md`.

Old placeholder symbol(s) this epic's existing queue cards name: `om_generational_step`.

Cards generated: 25. Distinct symbols carded: 101. Tests assigned to a card: 50.

## Numbering prefixes (per story, reused from the old queue)
- S-055: 240a1-e08-generational-one_commander_one_missio
- S-056: 241a1-e08-generational-decades_pass_while_i_am_
- S-057: 242a1-e08-generational-stay_with_the_family_or_
- S-058: 243a1-e08-generational-who_i_come_back_as
- S-059: 244a1-e08-generational-the_family_grows_while_i
- S-060: 245a1-e08-generational-named_leaders_live_and_d
- S-061: 246a-e08-generational-when_my_commander_dies
- S-062: 247a1-e08-generational-when_my_civilization_fal
- S-063: 248a1-e08-generational-my_two_choices_at_the_st
- S-064: 249a1-e08-generational-what_carries_over

## Cards generated
### S-055
- `240a1-e08-generational-one_commander_one_missio`: symbols=[om_chapter_start, om_chapter_current_phase, om_chapter_advance_phase, om_chapter_recon_has_clock, om_chapter_mission_realtime] tests=[test_R_055_01_order_mission_briefing_recon_free]
- `240a2-e08-generational-one_commander_one_missio`: symbols=[om_chapter_set_phase, om_world_strategic_tick, om_tactical_step, om_outcome_apply_consequences, om_time_jump_start_tick] tests=[test_R_055_02_no_strategic_tick_runs_strategic, test_R_055_03_those_field_changes_land_before]
- `240a3-e08-generational-one_commander_one_missio`: symbols=[om_time_jump_run, om_mission_generator_run, om_mission_generator_chosen_region, om_character_selector_run, om_character_selector_input_region] tests=[test_R_055_04_character_selector_runs_after_it]
- `240a4-e08-generational-one_commander_one_missio`: symbols=[om_campaign_start, om_campaign_opening_jump_length, om_chronicle_entry_count, om_chronicle_consequence_entry_count, om_chronicle_lineage_entry_count] tests=[test_R_055_05_opening_time_jump_runs_before]

### S-056
- `241a1-e08-generational-decades_pass_while_i_am_`: symbols=[om_time_jump_choose_length, om_time_jump_interrupt, om_time_jump_report_faction_field_deltas_count, om_time_jump_choose_opening_length, om_lineage_create] tests=[test_R_056_01_it_integer_number_ticks_in, test_R_056_02_exactly_that_many_strategic_ticks, test_R_056_03_report_lists_territory_changes_faction, test_R_056_04_it_in_20_50]
- `241a2-e08-generational-decades_pass_while_i_am_`: symbols=[om_character_create, om_time_jump_lineage_generation_tick, om_time_jump_death_processing_tick] tests=[test_R_056_05_lineage_members_generated_s_059]

### S-057
- `242a1-e08-generational-stay_with_the_family_or_`: symbols=[om_lineage_set_chapter_count, om_character_kill, om_character_selector_run_for_lineage, om_selector_base_rotation_prob, om_selector_decayed_rotation_prob] tests=[test_R_057_01_rotation_forced_with_reason_forced, test_R_057_02_player_stays, test_R_057_03_p_0_8_min_1, test_R_057_04_it_decays_with_c_never, test_R_057_06_it_first_living_lineage_member]
- `242a2-e08-generational-stay_with_the_family_or_`: symbols=[om_rng_force_selector_draw, om_lineage_record_history_region, om_lineage_home_region, om_character_selector_force_rotate] tests=[test_R_057_05_rotation_vetoed_player_stays, test_R_057_07_it_first_region_in_lineage, test_R_057_08_chapter_counter_for_new_lineage]

### S-058
- `243a1-e08-generational-who_i_come_back_as`: symbols=[om_selector_roll_pool, om_selector_clear_pools, om_selector_resolve_fallback_pool, om_selector_score_previous_lineage, om_character_tag_rival] tests=[test_R_058_01_one_draw_picks_previous_descendant, test_R_058_02_each_previously_played_lineage_with]
- `243a2-e08-generational-who_i_come_back_as`: symbols=[om_character_create_child, om_selector_gather_nemesis_candidates, om_selector_get_nemesis_candidate, om_selector_draw_unrelated, om_character_faction] tests=[test_R_058_03_they_living_descendants_within_2]
- `243a3-e08-generational-who_i_come_back_as`: symbols=[om_character_lineage_id, om_character_set_faction, om_mission_tag_rivals, om_character_has_rival_tag, om_character_selector_confirm_commander] tests=[test_R_058_04_new_character_created_in_mission, test_R_058_05_every_named_enemy_faction_character]
- `243a4-e08-generational-who_i_come_back_as`: symbols=[om_character_is_main_character, om_character_name_reuse_cooldown] tests=[test_R_058_06_commander_marked_as_main_character]

### S-059
- `244a1-e08-generational-the_family_grows_while_i`: symbols=[om_lineage_generate_descendants, om_rng_force_descendant_spread, om_lineage_spawn_single_descendant, om_character_get_record, om_character_set_generation] tests=[test_R_059_01_max_1_floor_n_0, test_R_059_02_its_parent_uniform_draw_among, test_R_059_04_nothing_created]
- `244a2-e08-generational-the_family_grows_while_i`: symbols=[om_lineage_spawn_descendant_at_tick] tests=[test_R_059_03_it_has_name_region_faction]

### S-060
- `245a1-e08-generational-named_leaders_live_and_d`: symbols=[om_faction_create_named, om_faction_supreme_commander, om_region_assign_regional_commander, om_region_regional_commander, om_character_create_random] tests=[test_R_060_01_it_gets_supreme_commander_in, test_R_060_02_it_uniform_integer_in_150]
- `245a2-e08-generational-named_leaders_live_and_d`: symbols=[om_character_create_with_rank, om_world_set_strategic_tick, om_process_natural_deaths, om_time_jump_run_tracked, om_time_jump_death_pass_count] tests=[test_R_060_03_it_becomes_historical_with_death, test_R_060_04_it_happens_once_at_end, test_R_060_06_it_holds_exactly_id_name]
- `245a3-e08-generational-named_leaders_live_and_d`: symbols=[om_event_fire_manual, om_event_attached_character_count, om_event_get_attached_character, om_character_has_event_history] tests=[test_R_060_05_region_s_named_characters_attached]

### S-061
- `246a-e08-generational-when_my_commander_dies`: symbols=[om_character_selector_resolve_commander_death, om_outcome_record_commander_death, om_ledger_commander_death_region, om_ledger_commander_death_outcome_band] tests=[test_R_061_01_living_lineage_member_not_supreme, test_R_061_02_successor_becomes_commander_same_lineage, test_R_061_03_rotation_happens_with_reason_commander, test_R_061_04_ledger_records_region_outcome_band]

### S-062
- `247a1-e08-generational-when_my_civilization_fal`: symbols=[om_player_faction_check_collapse, om_chapter_end_reason_for_collapse, om_player_faction_reassign_on_collapse, om_campaign_check_surviving_factions, om_player_faction_record_reassignment] tests=[test_R_062_01_chapter_ends_with_reason_faction, test_R_062_02_q_062_01_code_picks, test_R_062_03_campaign_ends_with_reason_no]
- `247a2-e08-generational-when_my_civilization_fal`: symbols=[om_chronicle_has_faction_fall_entry] tests=[test_R_062_04_chronicle_carries_major_entry_framing]

### S-063
- `248a1-e08-generational-my_two_choices_at_the_st`: symbols=[om_onboarding_validate, om_onboarding_save_to_slot, om_onboarding_load_from_slot, om_onboarding_update_choices, om_campaign_trigger_terminal_restart] tests=[test_R_063_01_it_offers_difficulty_easy_medium, test_R_063_02_choices_stored_per_save_slot, test_R_063_03_q_063_02_where_westley]
- `248a2-e08-generational-my_two_choices_at_the_st`: symbols=[om_campaign_needs_onboarding] tests=[test_R_063_04_onboarding_screen_shows_again]

### S-064
- `249a1-e08-generational-what_carries_over`: symbols=[om_chapter_transition_start, om_chapter_transition_complete, om_force_allocator_run, om_force_set_surviving_units, om_force_allocated_unit_count] tests=[test_R_064_01_every_region_field_ownership_faction, test_R_064_02_they_come_only_from_mission]
- `249a2-e08-generational-what_carries_over`: symbols=[om_progression_has_player_level, om_progression_carried_commander_stats_count, om_progression_supports_era_unlocks, om_save_state_size, om_save_state_write] tests=[test_R_064_03_there_no_player_level_no]
- `249a3-e08-generational-what_carries_over`: symbols=[om_load_state_read] tests=[test_R_064_04_next_time_jump_produces_same]

## Tests with no unbuilt symbol (already satisfiable)
none

## Symbols with no test (skipped)
Old placeholder symbol(s) no test in this epic calls (R22, re-confirmed): om_generational_step. Not carried into the regenerated cards.

## Stories needing more than 6 cards (design-lane question, not decided)
none

## Cards with no acceptance test of their own (design-lane question, not decided)
A card can end up with symbols but zero tests when every test needing them also needs a later card's symbols (the test's own closure is wider than the 5-symbol cap covers in one card). Candidates: (a) merge such a card forward into the next one, exceeding the cap only for this story (needs approval -- sizing caps are fixed); (b) accept the card as a pure prerequisite with no acceptance of its own (needs a card-format change -- card_lint.py currently hard-errors on empty acceptance); (c) leave it as a real card_lint finding and re-cut the test itself so its assertions split the same way the symbols do.
none

## Cross-epic symbol ownership
- `om_character_create`: E-08, E-09
- `om_chronicle_entry_count`: E-08, E-09
- `om_event_fire_manual`: E-08, E-09
- `om_event_get_attached_character`: E-08, E-09
- `om_lineage_create`: E-08, E-09
- `om_lineage_record_history_region`: E-08, E-09
- `om_tactical_step`: E-08, E-11, E-12
- `om_time_jump_run`: E-08, E-10
