# Card regen report -- E-09

Module: `csrc/chronicle.c`. Rules file: `projects/ouroboros/rules/E-09.md`. Bible: `docs/bible/epics/E-09-chronicle.md`.

Old placeholder symbol(s) this epic's existing queue cards name: `om_chronicle_step`.

Cards generated: 16. Distinct symbols carded: 69. Tests assigned to a card: 39.

## Numbering prefixes (per story, reused from the old queue)
- S-065: 250a1-e09-chronicle-five_to_ten_entries_in_t
- S-066: 251a-e09-chronicle-what_counts_as_notable
- S-067: 252a1-e09-chronicle-stories_not_events
- S-068: 253a1-e09-chronicle-written_from_fragments_n
- S-069: 254a1-e09-chronicle-watching_history_happen
- S-070: 255a-e09-chronicle-my_family_is_always_in_t
- S-071: 256a1-e09-chronicle-the_fragment_library_con

## Cards generated
### S-065
- `250a1-e09-chronicle-five_to_ten_entries_in_t`: symbols=[om_chronicle_mock_populate_events, om_chronicle_distill_and_assemble, om_chronicle_entry_count, om_chronicle_add_consequence_event, om_chronicle_get_cluster] tests=[test_R_065_01_it_has_at_least_5, test_R_065_02_they_form_one_consequence_cluster]
- `250a2-e09-chronicle-five_to_ten_entries_in_t`: symbols=[om_lineage_create, om_chronicle_add_lineage_event, om_chronicle_add_event, om_lineage_record_history_region, om_chronicle_category_name] tests=[test_R_065_03_every_lineage_cluster_included_regardless, test_R_065_04_one_lineage_quiet_cluster_included]
- `250a3-e09-chronicle-five_to_ten_entries_in_t`: symbols=[om_chronicle_add_cluster_direct, om_chronicle_select_clusters, om_chronicle_selected_category_count, om_chronicle_build_opening_scroll, om_chronicle_count_by_type] tests=[test_R_065_05_they_taken_in_descending_peak, test_R_065_06_skipped_clusters_added_in_score, test_R_065_07_it_has_3_to_5]

### S-066
- `251a-e09-chronicle-what_counts_as_notable`: symbols=[om_chronicle_score_base, om_chronicle_context_multiplier, om_chronicle_calculate_score] tests=[test_R_066_01_base_t_min_d_50, test_R_066_02_context_multiplier_gains_0_5, test_R_066_03_score_5_0_04_1, test_R_066_04_score_2_3_0_1, test_R_066_05_score_never_below_its_tier]

### S-067
- `252a1-e09-chronicle-stories_not_events`: symbols=[om_character_create, om_chronicle_is_lineage_event, om_chronicle_categorize_lineage_cluster, om_chronicle_add_chain_event, om_chronicle_build_chain_clusters] tests=[test_R_067_01_event_lineage_event_if_lineage, test_R_067_02_any_template_with_succession_or, test_R_067_03_events_sharing_chain_tag_form]
- `252a2-e09-chronicle-stories_not_events`: symbols=[om_chronicle_categorize_chain_cluster, om_chronicle_categorize_regional_cluster, om_chronicle_lineage_category_count, om_chronicle_chain_category_count, om_chronicle_regional_category_count] tests=[test_R_067_04_any_revolt_template_gives_chain, test_R_067_05_they_group_by_region_into, test_R_067_06_it_exactly_5_lineage_8]

### S-068
- `253a1-e09-chronicle-written_from_fragments_n`: symbols=[om_chronicle_assemble_cluster_entry, om_chronicle_render_region_mention, om_chronicle_apply_slot_echo_anaphora, om_chronicle_apply_word_echo_synonym, om_chronicle_add_raw_entry] tests=[test_R_068_01_opening_detail_closing_each_drawn, test_R_068_02_openings_at_most_30_words, test_R_068_03_it_comes_only_from_vocabulary, test_R_068_04_it_reads_region_held_by, test_R_068_05_second_becomes_anaphoric_form_what, test_R_068_06_second_occurrence_replaced_by_synonym]
- `253a2-e09-chronicle-written_from_fragments_n`: symbols=[om_chronicle_dedup_content_words, om_chronicle_entry_is_retained, om_chronicle_assemble_with_seed, om_chronicle_get_full_scroll_text] tests=[test_R_068_07_later_one_dropped_first_always, test_R_068_08_text_identical]

### S-069
- `254a1-e09-chronicle-watching_history_happen`: symbols=[om_chronicle_presentation_slide_in_sec, om_chronicle_presentation_slide_out_sec, om_chronicle_presentation_map_width_ratio, om_chronicle_presentation_word_cadence_sec, om_chronicle_presentation_word_fade_sec] tests=[test_R_069_01_it_slides_in_from_right, test_R_069_02_each_word_arrives_every_0]
- `254a2-e09-chronicle-watching_history_happen`: symbols=[om_chronicle_map_is_master_clock, om_chronicle_presentation_entry_hold_sec, om_chronicle_set_entry_state, om_chronicle_handle_click, om_chronicle_is_paused] tests=[test_R_069_03_that_entry_begins_printing_map]
- `254a3-e09-chronicle-watching_history_happen`: symbols=[om_chronicle_dismiss_expanded, om_chronicle_add_mock_entry, om_chronicle_add_ownership_change_event, om_chronicle_generate_map_keyframes, om_chronicle_has_keyframe_in_range] tests=[test_R_069_04_nothing_happens_it_printed_blinking]
- `254a4-e09-chronicle-watching_history_happen`: symbols=[om_chronicle_has_keyframe_at_tick, om_chronicle_rendered_entry_count] tests=[test_R_069_05_map_has_keyframe_within_entry, test_R_069_06_number_entries_on_screen_equals]

### S-070
- `255a-e09-chronicle-my_family_is_always_in_t`: symbols=[om_chronicle_score_event, om_event_fire_manual, om_event_get_attached_character, om_chronicle_render_character_rank] tests=[test_R_070_01_it_receives_0_8_lineage, test_R_070_02_lineage_member_attached_to_event, test_R_070_03_it_military_rank_no_lineage]

### S-071
- `256a1-e09-chronicle-the_fragment_library_con`: symbols=[om_chronicle_fragment_library_load_launch, om_chronicle_fragment_category_count, om_chronicle_fragment_pool_counts, om_chronicle_fragment_library_validate, om_chronicle_fragment_inject_invalid_slot] tests=[test_R_071_01_every_category_has_at_least, test_R_071_02_every_fragment_uses_only_vocabulary]
- `256a2-e09-chronicle-the_fragment_library_con`: symbols=[om_chronicle_fragment_check_near_duplicate, om_chronicle_fragment_batch_exceeds_rejection_limit, om_events_load_launch, om_chronicle_validate_event_template_prose, om_event_template_count] tests=[test_R_071_03_later_rejected_batch_losing_more]
- `256a3-e09-chronicle-the_fragment_library_con`: symbols=[om_event_template_chronicle_prose] tests=[test_R_071_04_it_has_chronicle_prose_phrase]

## Tests with no unbuilt symbol (already satisfiable)
none

## Symbols with no test (skipped)
Old placeholder symbol(s) no test in this epic calls (R22, re-confirmed): om_chronicle_step. Not carried into the regenerated cards.

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
