# Control stubs triage (92 stubs), 2026-10-18

Read-only audit; no test or header edited. Architect's call B16 (b).

Reading the table. File = `tests/csim/controls/test_control_<name>.py`. The expected id is `OM_BUG_` plus the upper-cased name after the epic prefix (gen_controls.py `bug_name`). "id" = exists in `csrc/ouroboros_sim.h` or `OMBug*` (conftest.py). "Detector" = a clean-case test that would fail if the bug were present, or a C site. Verdict key: fill = rule live and unguarded by a positive control; retire = nothing to inject or already covered; defer = the rule's story carries "Direction changed, rewrite pending".

Findings that apply to all 92:
- 0 of 92 expected ids exist under the stub's long name. 9 (all E-03) have a header alias (300 to 310, see below). No other stub has any id.
- Every stub calls `OMBug.<NAME>`, and `OMBug` (conftest.py:89) has 9 members (0 to 8), so each stub fails with AttributeError before it reaches its `NotImplementedError`.
- 131 files in controls/ = 92 stubs + 39 real (the brief said 36).
- Header ids 300 to 310 exist, are mirrored in conftest `OMBugE03` (:1157), and have no C injection site and no test use (only 312 is wired). So the E-03 fills need no header edit, only the C hook and the stub renamed to the alias.
- No `OM_BUG_*` for E-08 (only 600), E-09 (only 700), E-10 (only 800), E-11 to E-15 except the real window controls. Rules with a clean-case test but no injectable bug are graded fill, because CLAUDE.md says a detector ships with a positive control.

## Table

| file (after test_control_) | id | detector (clean-case test or C site) | rule | verdict | why |
|---|---|---|---|---|---|
| e03_a_faction_s_own_template_roll | alias 309 BUDGET_DRIFT | test_E03_S021 :57 draw order; no C site | R-021 count budget | fill | header id there, no hook |
| e03_archipelago_s_at_least_one_sparse | alias 308 ARCHIPELAGO_DENSE | test_E03_S021 :96 | R-021 template | fill | as above |
| e03_extra_edge_loop_links_a_home | nearest 301/302 (confirm) | none by name | R-025-04 | fill | confirm which alias |
| e03_corridor_chaining_leaves_a_faction_unreachable | alias 303 | none by name | R-025 | fill | no hook |
| e03_edge_type_defaults_to_both_for | alias 304 | test_E03_S024 :168 (edge types) | R-024 | fill | no hook |
| e03_factions_all_get_the_same_phase | alias 306 | test_E03_S022 :65 | R-022 phase | fill | no hook |
| e03_twin_colony_s_second_home_rolls | alias 307 | test_E03_S022 :101 | R-022-05 | fill | no hook |
| e03_frontier_rolled_from_the_home_range | alias 305 | test_E03_S022 :101 | R-022 | fill | no hook |
| e03_generator_consumes_the_rng_in_a | alias 300 | test_E03_S021 :248 | R-022-04 | fill | no hook |
| e06_both_partners_betray_in_the_same | no | test_E06_S044 | ALG-40 | fill | diplomacy.c:152 |
| e06_betrayal_opportunity_computed_from_whole_faction | no | test_E06_S044 | ALG-40 | fill | |
| e06_breakaway_tech_copied_before_the_parent | no | test_E06_S045 :116 | R-045 | fill | |
| e06_overture_rolled_before_the_stability_check | no | test_E06_S043 :89 | R-043-03 | fill | |
| e06_counter_increments_for_pairs_that_share | no | test_E06_S043 :69 | R-043 | fill | |
| e06_tier_computed_with_inclusive_upper_bounds | no | test_E06_S048 | R-048 | fill | |
| e06_convergence_pulls_toward_the_sum_of | no | test_E06_S047 :25 | ALG-28 | fill | |
| e07_breakaway_colors_collide_with_an_existing | no | none by name | ALG-41 | fill | rule unguarded |
| e07_ghost_removal_counts_from_creation_tick | no | real control zombie_ge_not_gt (501) is a different bug | ALG-42 | fill | |
| e07_absorption_picks_the_neighbor_with_the | no | test_E07_S051 | R-051 | fill | |
| e07_success_roll_made_before_the_population | no | none by name | ALG-41 | fill | |
| e07_phase_order_evaluated_differently_so_an | no | test_E07_S053 :85,:106 | ALG-44 | fill | |
| e07_reversion_draw_made_when_the_previous | no | none by name | ALG-43 | fill | |
| e08_onboarding_permanence_still_enforced | no | test_E08_S063 R_063_04; core_chapter_lifecycle :475 | R-063-04 | fill | |
| e08_natural_deaths_never_processed_so_the | no | test_E08_S060 R_060_03/04 | R-060 | fill | |
| e08_hard_cap_still_enforced_after_westley | no | test_E08_S057 R_057_04 | R-057-04 | fill | |
| e08_lineage_counter_incremented_twice_on_a | no | test_E08_S057 R_057_02/08 | R-057 | fill | |
| e08_selector_runs_before_the_mission_generator | no | test_E08_S055 R_055_04 | R-055-04 | fill | |
| e08_rotation_probability_inverted_active_regions_rotate | no | test_E08_S057 R_057_03/04 | ALG-46 | fill | |
| e08_rival_tags_applied_to_friendly_characters | no | test_E08_S058 R_058_05 | R-058-05 | fill | |
| e08_reassignment_picks_the_player_s_own | no | test_E08_S062 `control_the_player_never_rejoins...` | R-062-02 | fill | |
| e08_successor_search_ignores_the_2_hop | no | test_E08_S062 `beyond_2_hops`; S061 R_061_01 | R-058-03/061-01 | fill | |
| e09_a_digit_leaks_through_a_slot | no | test_E09_S068 :65-69 (no `\d`) | R-068 | fill | |
| e09_chain_clusters_split_by_region_breaking | no | test_E09_B5_chain_tags R_067_03 | R-067-03 | fill | |
| e09_consequence_cluster_ranked_by_score_and | no | test_E09_B5_consequence_entry | R-065-02 | fill | |
| e09_cross_entry_dedup_keeps_the_later | no | test_E09_S068 R_068_07 | R-068-07 | fill | |
| e09_category_cap_applied_to_lineage_clusters | no | test_E09_B5_category_cap | R-065-05 | fill | |
| e09_first_mention_qualifier_applied_on_every | no | test_E09_S068 R_068_05/06; GC2_mentions | R-068 | fill | |
| e09_lineage_cluster_omitted_when_the_family | no | test_E09_S065 R_065_04 | R-065-04 | fill | |
| e09_assembler_seeded_from_wall_clock_breaking | no | R_068_08 text identical; real `OM_BUG_RNG_UNSEEDED` (test_E02_S020) | R-068-08 | retire | determinism class covered |
| e09_map_waits_for_the_scroll_or | no | test_E09_S069_watching R_069_03/04 | R-069-03 | retire | client master clock; story play covers it |
| e10_deficit_and_current_forms_swapped_for | no | test_E10_S078 R_078_01 | R-078-01 | fill | |
| e10_parity_computed_from_the_faction_s | no | test_E10_S074 R_074_01/02 | R-074 | fill | |
| e10_refusal_deploys_a_force | no | test_E10_S078 R_078_05; test_pipe_mission_refuse | R-078-05 | fill | |
| e10_time_limit_uses_the_overridden_250 | no | test_E10_S076 R_076_02 | ALG-56 | fill | |
| e10_weighted_draw_uses_rank_instead_of | no | test_E10_S072 R_072_05/06 | ALG-55 | fill | |
| e10_retention_computed_from_unit_count_instead | no | test_E10_S077_RET1 | R-077 | fill | |
| e10_band_thresholds_applied_inclusively | no | test_E10_S077 R_077_01/02 | R-077 | fill | |
| e10_pool_includes_regions_two_hops_away | no | test_E10_S072 R_072_01 | ALG-54 | fill | |
| e10_transfer_applied_on_partial_success_for | no | test_E10_S078 R_078_04 | R-078-04 | fill | |
| e11_aoe_cap_applied_per_target_instead | no | test_E11_S086 :143 | R-082-05 | defer | R-082-05 rewrite pending |
| e11_brace_bonus_applied_during_windup | no | test_E11_S086 :82 (real 901 is another bug) | ALG-63 | fill | |
| e11_cohort_stagger_skips_validation_so_a | no | test_E11_S087 :180 | R-087 | fill | |
| e11_warden_aura_applies_to_enemies_or | no | test_PP_C_g67_support | ALG-63 | fill | |
| e11_matchup_matrix_transposed_attacker_and_target | no | test_E11_S081; S086 :170 | ALG-60 | fill | |
| e11_intercept_triggers_on_line_or_siege | no | test_E11_S086 | ALG-63 | fill | |
| e11_backswing_pauses_attacking_as_well_as | no | test_PP_group_cap_base_speed | R-084 | fill | |
| e11_return_fire_overrides_an_existing_engagement | no | test_PP_unit_guard (R-087-06) | R-087-06 | fill | |
| e12_fog_applied_during_recon_or_terrain | no | test_E12_S092 R_092_02/04 | R-092 | fill | |
| e12_interference_sampled_at_the_target_instead | no | test_E12_S090 R_090_03 (real 1000 is another bug) | R-090-03 | fill | |
| e12_union_computed_from_enemy_units_sets | no | test_PP_C_g3_fire_by_sight | R-089-02 | fill | |
| e12_visibility_computed_all_pairs_and_falls | no | scale/test_scale_E12.py | ALG-65 perf | retire | scale gate covers it |
| e12_enemy_ai_reads_the_player_s | no | test_E12_S093 R_093_02 | R-093-02 | fill | |
| e12_last_seen_markers_implemented_as_live | no | test_E12_S089 R_089_04 | R-089-04 | fill | |
| e13_offsets_recomputed_per_tick_so_formations | no | test_E13_S095 | ALG-66 | fill | |
| e13_probe_angle_order_differs_between_platforms | no | test_E13_S097 :67, S102 :71 | R-102 | retire | cross-platform, not injectable in one build |
| e13_plain_move_returns_fire | no | test_core_group_pace :235 | R-096 | fill | |
| e13_scatter_fallback_triggered_by_any_unit | no | test_E13_S095 | R-095 | fill | |
| e13_stationary_rule_ignored_so_engaged_units | no | test_PP_move_collision_a5 | ALG-68 | fill | |
| e13_slowest_unit_pace_capped_per_tick | no | test_core_group_pace; test_PP_group_cap_base_speed | R-095-01 | fill | |
| e13_leash_measured_from_the_target_s | no | test_PP_unit_pursuit (R-087-05) | R-087-05 | fill | |
| e13_route_grid_shared_across_layers | no | test_VG_D_d4 | S-097 | defer | route grid rewrite pending |
| e14_ambush_resets_after_the_trigger_leaves | no | test_E14_S120_B1_3/B1_4 | ALG-74 | fill | |
| e14_cautious_break_off_measured_against_mission | no | test_E14_S120 :79 | ALG-74 | fill | |
| e14_bus_flags_never_set_so_multi | no | test_E14_S121 :24; S124 :48 | R-121/124 | fill | |
| e14_timer_measured_from_mission_start_instead | no | test_E14_S121 | ALG-74 | fill | |
| e14_macro_reads_true_enemy_positions_the | no | none by name | S-125 | defer | S-125 rewrite pending |
| e14_noise_re_rolled_per_evaluation_so | no | test_E14_S121 | ALG-74 | fill | |
| e14_hooks_evaluated_after_base_transitions | no | test_E14_S120_B1_1 | ALG-74 | fill | |
| e15_production_timer_resets_on_type_change | no | test_E15_S126 :57 | S-126 | defer | production rule rewrite pending |
| e15_convoy_returns_fire | no | test_E15_S130 :240 | R-129 | fill | |
| e15_structure_takes_matchup_multipliers | no | test_E15_S127 :56,:97 | ALG-75 | fill | |
| e15_drifting_objective_s_zone_stays_at | no | test_E17_S118 :23 | R-130 | retire | duplicate of e17 drifting_node (deferred) |
| e15_two_enemy_factions_inside_count_as | no | test_PP_move_capture | ALG-75 | fill | |
| e15_spawn_position_from_an_unseeded_rng | no | test_E15_S126 :76; real RNG_UNSEEDED | R-126 | retire | determinism class covered |
| e15_capture_progresses_with_the_owner_present | no | test_E15_S127 :16; test_PP_move_capture | ALG-75 | fill | |
| e17_drifting_node_moves_but_the_objective | no | test_E17_S118 :23 | R-118 | defer | E-17 :136 pending |
| e17_flavoring_multipliers_unbounded_so_a_dead | no | test_E17_S115 | R-115 | defer | E-17 :90 pending |
| e17_layer_masks_emitted_for_listed_layers | no | test_E17_S190_walk_mask | R-114 | defer | E-17 :72 pending |
| e17_layout_chosen_by_index_instead_of | no | test_E17_S112 | ALG-70 | defer | E-17 :36 pending; C site not located |
| e17_fairness_evaluator_rejects_and_silently_regenerates | no | none; ALG-72 fairness is log-only, retries unused | ALG-72 | retire | no C behaviour to inject |
| e17_jitter_applied_after_edges_are_laid | no | none; no OM_LAYOUT_JITTER use in .c | ALG-70 | defer | E-17 :152 pending |
| e17_sources_placed_at_layout_percentages_instead | no | test_E17_S114 | ALG-71 | defer | E-17 :72 pending |

Judgement calls for the Architect: the E-17 defers (the story notes say "rules below are what the game does today"; I deferred because the generator is being rebuilt, so a control on the old one is wasted), and the two determinism retires (covered by `OM_BUG_RNG_UNSEEDED`). Reverse either and the counts shift.

## Counts

| epic | stubs | fill | retire | defer |
|---|---|---|---|---|
| E-03 | 9 | 9 | 0 | 0 |
| E-06 | 7 | 7 | 0 | 0 |
| E-07 | 6 | 6 | 0 | 0 |
| E-08 | 9 | 9 | 0 | 0 |
| E-09 | 9 | 7 | 2 | 0 |
| E-10 | 9 | 9 | 0 | 0 |
| E-11 | 8 | 7 | 0 | 1 |
| E-12 | 6 | 5 | 1 | 0 |
| E-13 | 8 | 6 | 1 | 1 |
| E-14 | 7 | 6 | 0 | 1 |
| E-15 | 7 | 4 | 2 | 1 |
| E-17 | 7 | 0 | 1 | 6 |
| total | 92 | 75 | 7 | 10 |

Of the 75 fills, 9 (E-03) need no header edit, 66 need new `OM_BUG_*` ids.

## First batch: E-08, E-09, E-10 (25 fills), header ids for one contract piece

Proposed numbers sit in the existing per-epic blocks (E-08 600s, E-09 700s, E-10 800s; 600, 700 and 800 are taken). Each also needs an `OMBug` mirror in conftest and a C hook site. Names are proposals.

E-08 (generational.c, diplomacy.c): 601 ONBOARDING_PERMANENCE_ENFORCED, 602 NATURAL_DEATHS_SKIPPED, 603 HARD_CAP_ENFORCED, 604 LINEAGE_COUNTER_TWICE_ON_STAY, 605 SELECTOR_BEFORE_GENERATOR, 606 ROTATION_PROB_INVERTED, 607 RIVAL_TAG_ON_FRIENDLY, 608 REASSIGN_OWN_DEAD_FACTION, 609 SUCCESSOR_IGNORES_2HOP.

E-09 (chronicle.c): 701 DIGIT_LEAKS_THROUGH_SLOT, 702 CHAIN_CLUSTER_SPLIT_BY_REGION, 703 CONSEQUENCE_CLUSTER_DROPPED, 704 DEDUP_KEEPS_LATER, 705 CATEGORY_CAP_ON_LINEAGE, 706 FIRST_MENTION_ON_EVERY_MENTION, 707 LINEAGE_QUIET_OMITTED.

E-10 (mission.c): 801 DELTA_FORMS_SWAPPED, 802 PARITY_FROM_FACTION_CAPACITY, 803 REFUSAL_DEPLOYS_FORCE, 804 TIME_LIMIT_USES_250_TABLE, 805 DRAW_BY_RANK, 806 RETENTION_BY_UNIT_COUNT, 807 BAND_THRESHOLDS_INCLUSIVE, 808 POOL_TWO_HOPS, 809 TRANSFER_ON_PARTIAL_ASSAULT.

Each fill renames its stub to the new id (the long gen_controls names are not kept), per the real-control pattern in `tests/csim/controls/test_control_e04_*.py`.

## Retire (not run)

```
cd /Users/westley/ouroboros/tests/csim/controls && git rm test_control_e09_assembler_seeded_from_wall_clock_breaking.py test_control_e09_map_waits_for_the_scroll_or.py test_control_e12_visibility_computed_all_pairs_and_falls.py test_control_e13_probe_angle_order_differs_between_platforms.py test_control_e15_drifting_objective_s_zone_stays_at.py test_control_e15_spawn_position_from_an_unseeded_rng.py test_control_e17_fairness_evaluator_rejects_and_silently_regenerates.py
```
