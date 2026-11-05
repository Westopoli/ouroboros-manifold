# ALG coverage (step 3, report only)

HEAD checked on main; 78 ALG rows. Counts: {'covered': 38, 'uncovered': 37, 'C not found': 3}.

Test count = files under tests/csim, tests/transport, tests/long named test*.py that mention the id, excluding tests/csim/controls/ and conftest.py. "ctl" = controls files mentioning it (stubs or real). Mention-only: a file naming the id may only touch it in passing; not audited per assertion.

| ALG id | name | C site | tests naming it (count, first path) | ctl | status | epics citing it |
|---|---|---|---|---|---|---|
|ALG-01|Oscillator kernel|sim.c:124|5, test_E02_S014_economy.py|1 ctl|covered|E-02|
|ALG-02|Military decay|sim.c:378|1, test_E02_S013_military.py|0 ctl|covered|
|ALG-03|Recruitment|sim.c:100|4, test_E02_S013_military.py|1 ctl|covered|
|ALG-04|Faction modifier|sim.c:378|1, test_E02_S013_military.py|0 ctl|covered|
|ALG-05|Economy growth, drag, overcapacity|sim.c:407|2, test_E02_S014_economy.py|0 ctl|covered|E-06|
|ALG-06|Adjacency bonus|sim.c:407|1, test_E02_S015_adjacency.py|0 ctl|covered|
|ALG-07|Tension drift|sim.c:464|1, test_E02_S016_tension.py|0 ctl|covered|
|ALG-08|Population drift|sim.c:486|2, test_E02_S017_population.py|0 ctl|covered|
|ALG-09|Stability|mission.c:1442|7, test_E02_S012_composites.py|2 ctl|covered|E-10|
|ALG-10|Capacity|sim.c (composites; header const om_constants.h:49)|1, test_E02_S012_composites.py|0 ctl|covered|E-02|
|ALG-11|Attractiveness|enemy_macro.c:21|2, test_E05_S032_every_faction_is_a_person.py|0 ctl|covered|E-05|
|ALG-12|Budget pressure|agent.c:195-199,329-332|0|0 ctl|uncovered|
|ALG-13|Entrenchment|resolve.c:357|1, test_E05_S038_taking_a_region.py|1 ctl|covered|
|ALG-14|Viability and scoring|agent.c:220,288|0|1 ctl|uncovered|
|ALG-15|Attack intent|agent.c:385|1, test_E05_S034_who_looks_worth_taking.py|0 ctl|covered|
|ALG-16|Colonize intent|agent.c colonize path not located|0|0 ctl|uncovered|
|ALG-17|Budget accumulation|hdr om_constants.h:144|4, test_E05_S033_territory_pays_or_costs.py|1 ctl|covered|E-02|
|ALG-18|Reactive reinforce|resolve.c:264-321 (om_step_reinforce)|0|0 ctl|uncovered|
|ALG-19|Reinforce|no .c site located; om_reinforce struct resolve.c:311-321, header const only|0|0 ctl|uncovered|
|ALG-20|Attack|hdr om_constants.h:156|2, test_E05_S039_when_everyone_wants_the_same_region.py|0 ctl|covered|
|ALG-21|Damage split|diplomacy.c:48|1, test_E05_S034_who_looks_worth_taking.py|0 ctl|covered|
|ALG-22|Conquest|diplomacy.c:272|3, test_E02_S019_floor.py|0 ctl|covered|E-04|
|ALG-23|Multi-faction collision|collision.c:60|1, test_E05_S039_when_everyone_wants_the_same_region.py|0 ctl|covered|
|ALG-24|Colonize|resolve.c:525|1, test_E05_S039_when_everyone_wants_the_same_region.py|0 ctl|covered|
|ALG-25|Border friction (row unnamed)|friction.c:2|0|0 ctl|uncovered|E-05|
|ALG-26|Multipliers|faction.c:8|3, test_E06_S044_peace_is_never_safe.py|0 ctl|covered|E-06|
|ALG-27|Growth|diplomacy.c:782|1, test_core_worldgen_tech_multipliers.py|1 ctl|covered|
|ALG-27b|Knowledge Lost|diplomacy.c:567|3, test_E04_S030_external_templates.py|0 ctl|covered|
|ALG-28|Convergence|diplomacy.c:669|0|0 ctl|uncovered|E-06|
|ALG-29|Admin revolt (row unnamed)|events.c:940|1, test_E05_S040_empires_fracture.py|0 ctl|covered|E-04,E-05|
|ALG-30|Starting fields|region.c:51|1, test_E03_wiring_storage.py|1 ctl|covered|E-03|
|ALG-31|Graph|worldgen.c:3|1, test_E03_wiring_storage.py|1 ctl|covered|E-03|
|ALG-32|Noise offsets|events.c:2|1, test_E04_wiring.py|1 ctl|covered|E-04|
|ALG-33|Threshold triggers|hdr om_constants.h:274|1, test_E04_S030_the_launch_event_library.py|1 ctl|covered|
|ALG-34|Probability triggers|events.c:845|1, test_E04_S027_one_thing_leads_to_another.py|0 ctl|covered|
|ALG-35|Firing and spawning|events.c:3|0|0 ctl|uncovered|
|ALG-36|Pending resolution|enemy_macro.c:85|1, test_E05_S040_empires_fracture.py|1 ctl|covered|
|ALG-37|Mutual exclusion|events.c:212 (tag read), resolver not located|0|0 ctl|uncovered|E-04|
|ALG-38|Starting stance and timers|diplomacy.c:308|1, test_E02_S015_adjacency.py|0 ctl|covered|E-06|
|ALG-39|Peace formation|diplomacy.c:184|0|0 ctl|uncovered|
|ALG-40|Betrayal|diplomacy.c:152|1, test_E06_S044_peace_is_never_safe.py|0 ctl|covered|E-06|
|ALG-41|Breakaway creation|diplomacy.c:435|0|0 ctl|uncovered|E-07|
|ALG-42|Zombie cleanup|lifecycle.c:245|0|1 ctl|uncovered|
|ALG-43|Latent loyalty|lifecycle.c:181|0|0 ctl|uncovered|
|ALG-44|Lifecycle phase|lifecycle.c:459|0|0 ctl|uncovered|E-07|
|ALG-45|Time jump|generational.c:107|2, test_E09_S069_jump_replay_ownership.py|1 ctl|covered|E-08|
|ALG-46|Rotation decision|generational.c:1785|0|0 ctl|uncovered|
|ALG-47|Commander pools|generational.c:136,910|0|0 ctl|uncovered|
|ALG-48|Lineage generation|generational.c:1532|0|0 ctl|uncovered|
|ALG-49|Lifespan and succession|diplomacy.c:641|0|0 ctl|uncovered|E-08|
|ALG-50|Significance|chronicle.c:50|0|1 ctl|uncovered|E-09|
|ALG-51|Clustering|chronicle.c:1586|0|0 ctl|uncovered|
|ALG-52|Selection|chronicle.c:52|0|0 ctl|uncovered|
|ALG-53|Assembly|chronicle.c:55|0|0 ctl|uncovered|E-09|
|ALG-54|Candidate pool|not found|0|0 ctl|C not found|E-10|
|ALG-55|Scoring and selection|mission.c:109|0|1 ctl|uncovered|
|ALG-56|Time limit|mission.c:640|0|0 ctl|uncovered|
|ALG-57|Force parity|mission.c:172|0|0 ctl|uncovered|
|ALG-58|Outcome|mission.c:1272|1, test_E10_S079_orders_not_menus.py|0 ctl|covered|
|ALG-59|Consequences|mission.c:224|1, test_core_mission_consequence_table.py|0 ctl|covered|E-10|
|ALG-60|Damage|unit.c:84|2, test_E11_S083_stats_traits_ability.py|1 ctl|covered|E-11|
|ALG-61|Area damage|unit.c:101|0|0 ctl|uncovered|E-11|
|ALG-62|Targeting|unit.c:115|0|0 ctl|uncovered|
|ALG-63|Abilities|unit.c:132|0|0 ctl|uncovered|
|ALG-64|Squads|not found|0|0 ctl|C not found|E-11|
|ALG-65|Visibility|fog.c:273|0|1 ctl|uncovered|E-12|
|ALG-66|Group move|unit.c:59|0|0 ctl|uncovered|E-13|
|ALG-67|Routing|tactical_mapgen.c:814|0|1 ctl|uncovered|
|ALG-68|Steering and collision|tactical_move.c:75|6, test_PP_collision_settle.py|0 ctl|covered|E-13|
|ALG-69|Facing|tactical_move.c:489-498|0|0 ctl|uncovered|E-13|
|ALG-70|Layout selection and instantiation|not located (no OM_LAYOUT_JITTER use in .c)|0|0 ctl|uncovered|E-17|
|ALG-71|Gradient sources|tactical_mapgen.c:310-327 (gradient fns look like stubs, unverified)|0|0 ctl|uncovered|
|ALG-72|Fairness|tactical_mapgen.c:289-305 (fairness fns, log only)|0|0 ctl|uncovered|
|ALG-73|Spine drift|not found|0|0 ctl|C not found|E-17|
|ALG-74|Behavior runner|enemy_macro.c:248|0|0 ctl|uncovered|E-14|
|ALG-75|Capture and production|enemy_macro.c:130|3, test_E15_S127_taking_a_garrison.py|1 ctl|covered|E-14,E-15|
|ALG-76|Macro rout and external reinforcement|enemy_macro.c:128|2, test_E14_S122_B1_5_rout_and_contested_live.py|0 ctl|covered|E-14|
|ALG-77|Selector history decay|generational.c:119|0|0 ctl|uncovered|

Stale ids (named by a test, absent from algorithms.md): none. (Ids 27b is present. ALG21/ALG_26 in csrc are constant prefixes.)

## Controls stubs (92 files that raise NotImplementedError), bug id by epic


### E03 (9)
- test_control_e03_archipelago_s_at_least_one_sparse.py : OM_BUG_ARCHIPELAGO_S_AT_LEAST_ONE_SPARSE
- test_control_e03_a_faction_s_own_template_roll.py : OM_BUG_A_FACTION_S_OWN_TEMPLATE_ROLL
- test_control_e03_corridor_chaining_leaves_a_faction_unreachable.py : OM_BUG_CORRIDOR_CHAINING_LEAVES_A_FACTION_UNREACHABLE
- test_control_e03_factions_all_get_the_same_phase.py : OM_BUG_FACTIONS_ALL_GET_THE_SAME_PHASE
- test_control_e03_extra_edge_loop_links_a_home.py : OM_BUG_EXTRA_EDGE_LOOP_LINKS_A_HOME
- test_control_e03_frontier_rolled_from_the_home_range.py : OM_BUG_FRONTIER_ROLLED_FROM_THE_HOME_RANGE
- test_control_e03_twin_colony_s_second_home_rolls.py : OM_BUG_TWIN_COLONY_S_SECOND_HOME_ROLLS
- test_control_e03_edge_type_defaults_to_both_for.py : OM_BUG_EDGE_TYPE_DEFAULTS_TO_BOTH_FOR
- test_control_e03_generator_consumes_the_rng_in_a.py : OM_BUG_GENERATOR_CONSUMES_THE_RNG_IN_A

### E06 (7)
- test_control_e06_breakaway_tech_copied_before_the_parent.py : OM_BUG_BREAKAWAY_TECH_COPIED_BEFORE_THE_PARENT
- test_control_e06_betrayal_opportunity_computed_from_whole_faction.py : OM_BUG_BETRAYAL_OPPORTUNITY_COMPUTED_FROM_WHOLE_FACTION
- test_control_e06_convergence_pulls_toward_the_sum_of.py : OM_BUG_CONVERGENCE_PULLS_TOWARD_THE_SUM_OF
- test_control_e06_counter_increments_for_pairs_that_share.py : OM_BUG_COUNTER_INCREMENTS_FOR_PAIRS_THAT_SHARE
- test_control_e06_tier_computed_with_inclusive_upper_bounds.py : OM_BUG_TIER_COMPUTED_WITH_INCLUSIVE_UPPER_BOUNDS
- test_control_e06_both_partners_betray_in_the_same.py : OM_BUG_BOTH_PARTNERS_BETRAY_IN_THE_SAME
- test_control_e06_overture_rolled_before_the_stability_check.py : OM_BUG_OVERTURE_ROLLED_BEFORE_THE_STABILITY_CHECK

### E07 (6)
- test_control_e07_breakaway_colors_collide_with_an_existing.py : OM_BUG_BREAKAWAY_COLORS_COLLIDE_WITH_AN_EXISTING
- test_control_e07_phase_order_evaluated_differently_so_an.py : OM_BUG_PHASE_ORDER_EVALUATED_DIFFERENTLY_SO_AN
- test_control_e07_absorption_picks_the_neighbor_with_the.py : OM_BUG_ABSORPTION_PICKS_THE_NEIGHBOR_WITH_THE
- test_control_e07_success_roll_made_before_the_population.py : OM_BUG_SUCCESS_ROLL_MADE_BEFORE_THE_POPULATION
- test_control_e07_reversion_draw_made_when_the_previous.py : OM_BUG_REVERSION_DRAW_MADE_WHEN_THE_PREVIOUS
- test_control_e07_ghost_removal_counts_from_creation_tick.py : OM_BUG_GHOST_REMOVAL_COUNTS_FROM_CREATION_TICK

### E08 (9)
- test_control_e08_hard_cap_still_enforced_after_westley.py : OM_BUG_HARD_CAP_STILL_ENFORCED_AFTER_WESTLEY
- test_control_e08_natural_deaths_never_processed_so_the.py : OM_BUG_NATURAL_DEATHS_NEVER_PROCESSED_SO_THE
- test_control_e08_reassignment_picks_the_player_s_own.py : OM_BUG_REASSIGNMENT_PICKS_THE_PLAYER_S_OWN
- test_control_e08_rotation_probability_inverted_active_regions_rotate.py : OM_BUG_ROTATION_PROBABILITY_INVERTED_ACTIVE_REGIONS_ROTATE
- test_control_e08_successor_search_ignores_the_2_hop.py : OM_BUG_SUCCESSOR_SEARCH_IGNORES_THE_2_HOP
- test_control_e08_lineage_counter_incremented_twice_on_a.py : OM_BUG_LINEAGE_COUNTER_INCREMENTED_TWICE_ON_A
- test_control_e08_onboarding_permanence_still_enforced.py : OM_BUG_ONBOARDING_PERMANENCE_STILL_ENFORCED
- test_control_e08_rival_tags_applied_to_friendly_characters.py : OM_BUG_RIVAL_TAGS_APPLIED_TO_FRIENDLY_CHARACTERS
- test_control_e08_selector_runs_before_the_mission_generator.py : OM_BUG_SELECTOR_RUNS_BEFORE_THE_MISSION_GENERATOR

### E09 (9)
- test_control_e09_category_cap_applied_to_lineage_clusters.py : OM_BUG_CATEGORY_CAP_APPLIED_TO_LINEAGE_CLUSTERS
- test_control_e09_consequence_cluster_ranked_by_score_and.py : OM_BUG_CONSEQUENCE_CLUSTER_RANKED_BY_SCORE_AND
- test_control_e09_cross_entry_dedup_keeps_the_later.py : OM_BUG_CROSS_ENTRY_DEDUP_KEEPS_THE_LATER
- test_control_e09_lineage_cluster_omitted_when_the_family.py : OM_BUG_LINEAGE_CLUSTER_OMITTED_WHEN_THE_FAMILY
- test_control_e09_assembler_seeded_from_wall_clock_breaking.py : OM_BUG_ASSEMBLER_SEEDED_FROM_WALL_CLOCK_BREAKING
- test_control_e09_a_digit_leaks_through_a_slot.py : OM_BUG_A_DIGIT_LEAKS_THROUGH_A_SLOT
- test_control_e09_map_waits_for_the_scroll_or.py : OM_BUG_MAP_WAITS_FOR_THE_SCROLL_OR
- test_control_e09_chain_clusters_split_by_region_breaking.py : OM_BUG_CHAIN_CLUSTERS_SPLIT_BY_REGION_BREAKING
- test_control_e09_first_mention_qualifier_applied_on_every.py : OM_BUG_FIRST_MENTION_QUALIFIER_APPLIED_ON_EVERY

### E10 (9)
- test_control_e10_deficit_and_current_forms_swapped_for.py : OM_BUG_DEFICIT_AND_CURRENT_FORMS_SWAPPED_FOR
- test_control_e10_parity_computed_from_the_faction_s.py : OM_BUG_PARITY_COMPUTED_FROM_THE_FACTION_S
- test_control_e10_refusal_deploys_a_force.py : OM_BUG_REFUSAL_DEPLOYS_A_FORCE
- test_control_e10_time_limit_uses_the_overridden_250.py : OM_BUG_TIME_LIMIT_USES_THE_OVERRIDDEN_250
- test_control_e10_weighted_draw_uses_rank_instead_of.py : OM_BUG_WEIGHTED_DRAW_USES_RANK_INSTEAD_OF
- test_control_e10_retention_computed_from_unit_count_instead.py : OM_BUG_RETENTION_COMPUTED_FROM_UNIT_COUNT_INSTEAD
- test_control_e10_band_thresholds_applied_inclusively.py : OM_BUG_BAND_THRESHOLDS_APPLIED_INCLUSIVELY
- test_control_e10_pool_includes_regions_two_hops_away.py : OM_BUG_POOL_INCLUDES_REGIONS_TWO_HOPS_AWAY
- test_control_e10_transfer_applied_on_partial_success_for.py : OM_BUG_TRANSFER_APPLIED_ON_PARTIAL_SUCCESS_FOR

### E11 (8)
- test_control_e11_aoe_cap_applied_per_target_instead.py : OM_BUG_AOE_CAP_APPLIED_PER_TARGET_INSTEAD
- test_control_e11_brace_bonus_applied_during_windup.py : OM_BUG_BRACE_BONUS_APPLIED_DURING_WINDUP
- test_control_e11_cohort_stagger_skips_validation_so_a.py : OM_BUG_COHORT_STAGGER_SKIPS_VALIDATION_SO_A
- test_control_e11_warden_aura_applies_to_enemies_or.py : OM_BUG_WARDEN_AURA_APPLIES_TO_ENEMIES_OR
- test_control_e11_matchup_matrix_transposed_attacker_and_target.py : OM_BUG_MATCHUP_MATRIX_TRANSPOSED_ATTACKER_AND_TARGET
- test_control_e11_intercept_triggers_on_line_or_siege.py : OM_BUG_INTERCEPT_TRIGGERS_ON_LINE_OR_SIEGE
- test_control_e11_backswing_pauses_attacking_as_well_as.py : OM_BUG_BACKSWING_PAUSES_ATTACKING_AS_WELL_AS
- test_control_e11_return_fire_overrides_an_existing_engagement.py : OM_BUG_RETURN_FIRE_OVERRIDES_AN_EXISTING_ENGAGEMENT

### E12 (6)
- test_control_e12_fog_applied_during_recon_or_terrain.py : OM_BUG_FOG_APPLIED_DURING_RECON_OR_TERRAIN
- test_control_e12_interference_sampled_at_the_target_instead.py : OM_BUG_INTERFERENCE_SAMPLED_AT_THE_TARGET_INSTEAD
- test_control_e12_union_computed_from_enemy_units_sets.py : OM_BUG_UNION_COMPUTED_FROM_ENEMY_UNITS_SETS
- test_control_e12_visibility_computed_all_pairs_and_falls.py : OM_BUG_VISIBILITY_COMPUTED_ALL_PAIRS_AND_FALLS
- test_control_e12_enemy_ai_reads_the_player_s.py : OM_BUG_ENEMY_AI_READS_THE_PLAYER_S
- test_control_e12_last_seen_markers_implemented_as_live.py : OM_BUG_LAST_SEEN_MARKERS_IMPLEMENTED_AS_LIVE

### E13 (8)
- test_control_e13_offsets_recomputed_per_tick_so_formations.py : OM_BUG_OFFSETS_RECOMPUTED_PER_TICK_SO_FORMATIONS
- test_control_e13_probe_angle_order_differs_between_platforms.py : OM_BUG_PROBE_ANGLE_ORDER_DIFFERS_BETWEEN_PLATFORMS
- test_control_e13_plain_move_returns_fire.py : OM_BUG_PLAIN_MOVE_RETURNS_FIRE
- test_control_e13_scatter_fallback_triggered_by_any_unit.py : OM_BUG_SCATTER_FALLBACK_TRIGGERED_BY_ANY_UNIT
- test_control_e13_stationary_rule_ignored_so_engaged_units.py : OM_BUG_STATIONARY_RULE_IGNORED_SO_ENGAGED_UNITS
- test_control_e13_slowest_unit_pace_capped_per_tick.py : OM_BUG_SLOWEST_UNIT_PACE_CAPPED_PER_TICK
- test_control_e13_leash_measured_from_the_target_s.py : OM_BUG_LEASH_MEASURED_FROM_THE_TARGET_S
- test_control_e13_route_grid_shared_across_layers.py : OM_BUG_ROUTE_GRID_SHARED_ACROSS_LAYERS

### E14 (7)
- test_control_e14_ambush_resets_after_the_trigger_leaves.py : OM_BUG_AMBUSH_RESETS_AFTER_THE_TRIGGER_LEAVES
- test_control_e14_cautious_break_off_measured_against_mission.py : OM_BUG_CAUTIOUS_BREAK_OFF_MEASURED_AGAINST_MISSION
- test_control_e14_bus_flags_never_set_so_multi.py : OM_BUG_BUS_FLAGS_NEVER_SET_SO_MULTI
- test_control_e14_timer_measured_from_mission_start_instead.py : OM_BUG_TIMER_MEASURED_FROM_MISSION_START_INSTEAD
- test_control_e14_macro_reads_true_enemy_positions_the.py : OM_BUG_MACRO_READS_TRUE_ENEMY_POSITIONS_THE
- test_control_e14_noise_re_rolled_per_evaluation_so.py : OM_BUG_NOISE_RE_ROLLED_PER_EVALUATION_SO
- test_control_e14_hooks_evaluated_after_base_transitions.py : OM_BUG_HOOKS_EVALUATED_AFTER_BASE_TRANSITIONS

### E15 (7)
- test_control_e15_production_timer_resets_on_type_change.py : OM_BUG_PRODUCTION_TIMER_RESETS_ON_TYPE_CHANGE
- test_control_e15_convoy_returns_fire.py : OM_BUG_CONVOY_RETURNS_FIRE
- test_control_e15_structure_takes_matchup_multipliers.py : OM_BUG_STRUCTURE_TAKES_MATCHUP_MULTIPLIERS
- test_control_e15_drifting_objective_s_zone_stays_at.py : OM_BUG_DRIFTING_OBJECTIVE_S_ZONE_STAYS_AT
- test_control_e15_two_enemy_factions_inside_count_as.py : OM_BUG_TWO_ENEMY_FACTIONS_INSIDE_COUNT_AS
- test_control_e15_spawn_position_from_an_unseeded_rng.py : OM_BUG_SPAWN_POSITION_FROM_AN_UNSEEDED_RNG
- test_control_e15_capture_progresses_with_the_owner_present.py : OM_BUG_CAPTURE_PROGRESSES_WITH_THE_OWNER_PRESENT

### E17 (7)
- test_control_e17_drifting_node_moves_but_the_objective.py : OM_BUG_DRIFTING_NODE_MOVES_BUT_THE_OBJECTIVE
- test_control_e17_flavoring_multipliers_unbounded_so_a_dead.py : OM_BUG_FLAVORING_MULTIPLIERS_UNBOUNDED_SO_A_DEAD
- test_control_e17_layer_masks_emitted_for_listed_layers.py : OM_BUG_LAYER_MASKS_EMITTED_FOR_LISTED_LAYERS
- test_control_e17_layout_chosen_by_index_instead_of.py : OM_BUG_LAYOUT_CHOSEN_BY_INDEX_INSTEAD_OF
- test_control_e17_fairness_evaluator_rejects_and_silently_regenerates.py : OM_BUG_FAIRNESS_EVALUATOR_REJECTS_AND_SILENTLY_REGENERATES
- test_control_e17_jitter_applied_after_edges_are_laid.py : OM_BUG_JITTER_APPLIED_AFTER_EDGES_ARE_LAID
- test_control_e17_sources_placed_at_layout_percentages_instead.py : OM_BUG_SOURCES_PLACED_AT_LAYOUT_PERCENTAGES_INSTEAD

## Uncovered ALG rows by epic, with the constants the row states

Epic assigned by the algorithms.md section (E-05 faction/intent, E-06 diplomacy/tech, E-04 events, E-07 lifecycle, E-08 time jump/selector, E-09 chronicle, E-10 missions, E-11 to E-13 tactical, E-14 enemy macro, E-17 map generation). Status U = uncovered, N = C not found. "no bible value" marks a quantity the row uses but does not number.

| Epic | ALG | St | Constants stated in the row |
|---|---|---|---|
| E-05 | 12 Budget pressure | U | ATTACK_COMMIT_FRACTION 0.70; RESISTANCE_FACTOR 0.55; ATTACK_EFFICIENCY 1.0; BUDGET_PRESSURE_THRESHOLD 0.8; confidence ranges conqueror (2,6), fortifier (4,10), player_civilization (3,8), breakaway (2,5), default (4,8) |
| E-05 | 14 Viability/scoring | U | ATTACK_NORM_RANGE (0,40); COLONIZE_NORM_RANGE (0,1); weights attack/expand/defend: conqueror 1.2/1.0/0.4, warlord 1.4/0.6/0.3, fortifier 0.8/0.8/1.5, opportunist 1.0/0.7/0.6, schism 1.3/0.0/0.5, player_civ 0.3/0.5/1.5, default 0.8/0.6/0.8; MIN_ACTION_THRESHOLD 0.05; COLONIZE_COST 20.0 |
| E-05 | 16 Colonize intent | U | COLONIZE_COST 20.0 |
| E-05 | 18 Reactive reinforce | U | reinforce_prob min(1, w_defend/1.5); REACTIVE_REINFORCE_BUDGET_FRACTION 0.30; telegraph_commit factor 0.5; min commit 1.0 |
| E-05 | 19 Reinforce | U | REINFORCE_MIL_CAP home 100, frontier 60; REINFORCE_EFFICIENCY 0.5; variance base (0.85,1.15); tension scale 0.20 |
| E-05 | 25 Border friction | U | BORDER_FRICTION_TENSION 0.15; BORDER_FRICTION_ECONOMY 0.05; FIELD_MAX 100; ECONOMY_FLOOR 8.0 |
| E-04 | 35 Firing/spawning | U | ECONOMY_FLOOR 8.0; TENSION_FLOOR 12.0; others floor 0; delay = clamp(round(triangular(a,b,(a+b)/2)),a,b); chain counter chain_NNNN; a,b per template |
| E-04 | 37 Mutual exclusion | U | tie draw <0.5 keeps earlier; loser requeue due = tick + randint(1,2) |
| E-06 | 28 Convergence | U | TECH_CONVERGENCE_RATE 0.1 |
| E-06 | 39 Peace formation | U | PEACE_FORMATION_THRESHOLD 80; PEACE_STABILITY_THRESHOLD 35.0; PEACE_BASE_PROBABILITY 0.5; dispositions conqueror 0.1, fortifier 2.0, warlord 0.2, opportunist 1.0, schism 0.3, player_civ 1.5, breakaway 0.8 |
| E-07 | 41 Breakaway creation | U | REVOLT_SUCCESS_RANGE (0.50,0.95); REVOLT_BREAKAWAY_POP_FLOOR 25.0; REVOLT_MILITARY_STEAL 0.60; REVOLT_ECONOMY_STEAL 0.40; REVOLT_TENSION_CAP 40.0; REVOLT_ECONOMY_FLOOR 20.0; admin success 1.0; color retries 30, hue distance 0.08 |
| E-07 | 42 Zombie cleanup | U (a control exists, stub-or-real not checked) | ZOMBIE_GHOST_TICKS 5; ZOMBIE_CLEANUP_TICKS 50; COLONIZE_COST 20.0 |
| E-07 | 43 Latent loyalty | U | LATENT_LOYALTY_TICKS 20; LATENT_LOYALTY_REVERT_CHANCE 0.5 |
| E-07 | 44 Lifecycle phase | U | FRAGMENTATION_REVOLT_RATE 0.02; OVEREXTENSION_DRAIN_RATIO 0.4; CONFLICT_ATTACK_RATE 0.05; EXPANSION_EMPTY_THRESHOLD 0.3; REGION_MAINTENANCE_COST 8.0 |
| E-08 | 46 Rotation decision | U | SELECTOR_PROXIMITY_HOPS 2; MIN_CHAPTERS 2; DELTA_SAFE 200; MAX_ROTATION_PROB 0.8; MIN_ROTATION_PROB 0.1; CRISIS_THRESHOLD 20.0; (HARD_CAP 6 removed) |
| E-08 | 47 Commander pools | U | POOL_PREVIOUS 0.70; NEMESIS 0.20; UNRELATED 0.10; RECENCY_PENALTY_WINDOW 1; GAP_BONUS_PEAK 4; DENSITY_PEAK 5; GAP_WEIGHT 0.6; DENSITY_WEIGHT 0.4; hops 2 |
| E-08 | 48 Lineage generation | U | LINEAGE_FERTILITY_RATE 0.03; LINEAGE_SPREAD_PROBABILITY 0.1 |
| E-08 | 49 Lifespan/succession | U | LIFESPAN_MIN 150, MAX 350; NAME_REUSE_COOLDOWN_TICKS 500 (main 4500); CHARACTER_ATTACHMENT_TIER_THRESHOLD 3 |
| E-08 | 77 Selector history decay | U | SELECTOR_DECAY_BASE 0.75 |
| E-09 | 50 Significance | U | DELTA_SCALE 50.0; DELTA_CAP 3.0; mission-region bonus 0.5; character 0.3; chain 0.1 per link, CHAIN_LENGTH_CAP 5; lineage region 0.8; template tier table (26 values listed in the row) |
| E-09 | 51 Clustering | U | no numeric constants (rules only) |
| E-09 | 52 Selection | U | CHRONICLE_MAX_ENTRIES 10; MIN_ENTRIES 5; category cap 2 |
| E-09 | 53 Assembly | U | dedup overlap 0.40; slot echo >= 6 words; warning base >= 90, expanded >= 140 words |
| E-10 | 54 Candidate pool | N | 10 archetypes; no numeric constants |
| E-10 | 55 Scoring/selection | U | urgency weights 0.4/0.4/0.2; relevance weights 0.4/0.3/0.3; max hops 5; fit threshold 3; rare preference 0.1; default 0.5; score weights 0.5/0.3/0.2; TOP_N 5; conflict constants 70, 0.5, 600, 0.3 |
| E-10 | 56 Time limit | U | TIME_PRESSURE_SCALING 0.2; TIME_LIMIT_FLOOR_PCT 0.6; base minutes 60/60/52.5/52.5/45/37.5/37.5/37.5/30/30; TACTICAL_TICK_RATE no bible value in row |
| E-10 | 57 Force parity | U | BUDGET_TO_POWER_SCALE 300; MILITARY_TO_POWER_SCALE 2000; insurgent ranges (20,50)@pop<=25, (40,70)@pop>=70; PARITY_BREAKPOINTS 5 pairs; easy 0.95, hard 0.85; PARITY_FLOOR 0.75; fill 1.15; shortfall threshold 0.4, reduction 0.20 (row text says "confirmed at 25" for the threshold while the stated constant is 0.4: reader to check) |
| E-11 | 61 Area damage | U | aoe_radius 150; AOE_DAMAGE_CAP_MULTIPLIER 4.0 (row flags rewrite pending) |
| E-11 | 62 Targeting | U | TARGETING_COHORT_COUNT 4; flee distance 200 (row flags rewrite pending) |
| E-11 | 63 Abilities | U | Surge 60t x2.5 spd x2.0 dmg cd 1500; Intercept radius 350, x1.8, x1.5, cd 600; Brace windup 40, reduction 0.50, dmg x1.3, cd 700; Rally 112 HP r400 cd 1500; Barrage 30t telegraph, x3.0, r100, cd 1800; Fortify 400t, 0.20, r350, speed x0.4, cd 1400; WARDEN_AURA_REPAIR_RATE 0.075 r300 |
| E-11 | 64 Squads | N | none (rendering only; likely no sim code to test) |
| E-12 | 65 Visibility | U | vantage default radius 100; VANTAGE_CONE_MULTIPLIER 2.0; CONE_LAYER_1 0.50, _2 0.20; VANTAGE_EXTRA_LAYER 1; PULSE_RADIUS 500; PULSE_REVEAL_TICKS 40; PULSE_COOLDOWN_TICKS 400 (rewrite pending) |
| E-13 | 66 Group move | U | MAGIC_BOX_SPREAD_RADIUS 450; ARRIVAL_TOLERANCE_MULT 1.5; UNIT_COLLISION_RADIUS 15 (rewrite pending) |
| E-13 | 67 Routing | U | NAVMESH_CELL_SIZE 100; OBSTACLE_THRESHOLD 0.7; canvas 280x280 cells; cache 16 destinations; replan 2*15 wu |
| E-13 | 69 Facing | U | rotation rad/s strike 6.0, line 4.0, siege 2.5 |
| E-17 | 70 Layout selection | U | LAYOUT_JITTER_PERCENT 0.03; CANVAS_SIZE_RANGES small (8000,12000), medium (12000,20000), large (20000,28000); library counts 8 layouts |
| E-17 | 71 Gradient sources | U | pairs (intensity, radius): choke obstacle (0.85,600), staging (0.60,800), vantage elev (0.90,700), hazard interference (0.75,500), flank obstacle (0.35,450), cover (0.40,450), choke cover (0.55,550), objective cover (0.50,400), hazard cover (0.35,400); LAYER_MASK_RADIUS 600, intensity 1.0, block >= 0.5 |
| E-17 | 72 Fairness | U | FAIRNESS_MAX_RETRIES 5 (unused); acceptance thresholds: no bible value |
| E-17 | 73 Spine drift | N | period P, waypoints and mode are data; no constants |
| E-14 | 74 Behavior runner | U | SCRIPT_NOISE_DEFAULT_PCT 0.15; TIMER_NOISE 0.20; EVAL_INTERVAL 40 ticks |
