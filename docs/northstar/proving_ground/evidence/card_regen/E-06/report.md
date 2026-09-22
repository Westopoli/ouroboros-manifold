# Card regen report -- E-06

Module: `csrc/diplomacy.c`. Rules file: `projects/ouroboros/rules/E-06.md`. Bible: `docs/bible/epics/E-06-diplomacy-and-technology.md`.

Old placeholder symbol(s) this epic's existing queue cards name: `om_diplomacy_step, om_tech_step`.

Cards generated: 8. Distinct symbols carded: 33. Tests assigned to a card: 31.

## Numbering prefixes (per story, reused from the old queue)
- S-042: 220a-e06-diplomacy-three_ways_to_feel_about
- S-043: 221a-e06-diplomacy-peace_grows_out_of_quiet
- S-044: 222a-e06-diplomacy-peace_is_never_safe
- S-045: 223a1-e06-diplomacy-a_faction_s_technology_i
- S-046: 224a-e06-diplomacy-archetypes_spend_tech_di
- S-047: (none -- already satisfiable)
- S-048: 226a1-e06-diplomacy-three_tiers_of_technolog

## Cards generated
### S-042
- `220a-e06-diplomacy-three_ways_to_feel_about`: symbols=[om_diplomacy_init, om_tick_friction, om_diplomacy_step, om_world_generated, om_faction_create_breakaway] tests=[test_R_042_01_it_exactly_one_hostile_neutral, test_R_042_02_each_includes_other_s_regions, test_R_042_03_neither_attacks_other_no_friction, test_R_042_04_adjacency_bonus_crosses_their_trade, test_R_042_05_their_stance_hostile_if_their, test_R_042_06_it_hostile_toward_every_existing]

### S-043
- `221a-e06-diplomacy-peace_grows_out_of_quiet`: symbols=[om_faction_stance_counter, om_faction_set_stance_counter, om_faction_cooperative_since, om_archetype_peace_disposition] tests=[test_R_043_01_their_non_aggression_counter_increments, test_R_043_02_counter_does_not_move, test_R_043_03_overture_fires_if_both_sides, test_R_043_04_p_min_1_0_5, test_R_043_05_pair_becomes_cooperative_cooperative_since, test_R_043_06_pair_stays_neutral_counter_resets, test_R_043_07_conqueror_0_1_fortifier_2]

### S-044
- `222a-e06-diplomacy-peace_is_never_safe`: symbols=[om_faction_betrayal_chance, om_faction_betrayal_opportunity, om_archetype_betrayal_weight] tests=[test_R_044_02_p_0_005_2_5, test_R_044_03_opportunity_factor_3_0, test_R_044_04_opportunity_1_0_pressure_1, test_R_044_05_conqueror_2_5_fortifier_0]

### S-045
- `223a1-e06-diplomacy-a_faction_s_technology_i`: symbols=[om_tech_step, om_gen_set_faction_count, om_gen_set_region_range, om_breakaway_create, om_faction_set_last_knowledge_lost] tests=[test_R_045_04_nothing_changes, test_R_045_05_it_equals_average_starting_population, test_R_045_06_it_equals_parent_s_tech, test_R_045_08_no_draw_made_tech_never]
- `223a2-e06-diplomacy-a_faction_s_technology_i`: symbols=[om_world_set_tick, om_faction_last_knowledge_lost, om_tick_events] tests=[test_R_045_07_one_uniform_draw_made_if, test_R_045_09_mean_over_all_windows_between]

### S-046
- `224a-e06-diplomacy-archetypes_spend_tech_di`: symbols=[om_faction_tech_multipliers, om_faction_tech_attack, om_faction_tech_defense, om_faction_tech_economy] tests=[test_R_046_01_attack_1_096_defense_1, test_R_046_02_attack_1_018_defense_1, test_R_046_03_all_three_multipliers_1_0, test_R_046_05_q_048_01_nothing_in]

### S-047
(no card -- every test already satisfiable with built symbols)

### S-048
- `226a1-e06-diplomacy-three_tiers_of_technolog`: symbols=[om_tech_tier, om_faction_tech_tier, om_mission_start, om_mission_unit_tier, om_faction_next_mission_unit_tier] tests=[test_R_048_01_it_1_in_34_67]
- `226a2-e06-diplomacy-three_tiers_of_technolog`: symbols=[om_faction_unit_tier, om_chronicle_distill_candidates, om_tier_transition_candidate_exists, om_faction_tier_transition_candidate] tests=[test_R_048_02_units_use_tier_2_profile, test_R_048_03_units_use_tier_2_profile, test_R_048_04_tier_transition_entry_candidate_e]

## Tests with no unbuilt symbol (already satisfiable)
- S-044: test_R_044_01_each_faction_rolls_once_per, test_R_044_06_pair_hostile_at_once_every, test_R_044_07_q_045_01_decides_commit
- S-045: test_R_045_01_tech_0_35_0_6, test_R_045_02_population_factor_0_3_not, test_R_045_03_tech_100_0
- S-046: test_R_046_04_effective_attack_multiplied_by_it
- S-047: test_R_047_01_bonus_0_1_40_100, test_R_047_02_bonus_0, test_R_047_03_bonus_0, test_R_047_04_growth_applies_first_convergence_reads

## Symbols with no test (skipped)
none

## Stories needing more than 6 cards (design-lane question, not decided)
none

## Cards with no acceptance test of their own (design-lane question, not decided)
A card can end up with symbols but zero tests when every test needing them also needs a later card's symbols (the test's own closure is wider than the 5-symbol cap covers in one card). Candidates: (a) merge such a card forward into the next one, exceeding the cap only for this story (needs approval -- sizing caps are fixed); (b) accept the card as a pure prerequisite with no acceptance of its own (needs a card-format change -- card_lint.py currently hard-errors on empty acceptance); (c) leave it as a real card_lint finding and re-cut the test itself so its assertions split the same way the symbols do.
none

## Cross-epic symbol ownership
- `om_tick_friction`: E-03, E-06
- `om_world_generated`: E-03, E-06
- `om_world_set_tick`: E-06, E-10
