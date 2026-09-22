# Card regen report -- E-11

Module: `csrc/unit.c`. Rules file: `projects/ouroboros/rules/E-11.md`. Bible: `docs/bible/epics/E-11-units-and-combat.md`.

Old placeholder symbol(s) this epic's existing queue cards name: `om_unit_step`.

Cards generated: 15. Distinct symbols carded: 61. Tests assigned to a card: 42.

## Numbering prefixes (per story, reused from the old queue)
- S-081: 270a1-e11-combat-three_categories_a_soft_
- S-082: 271a1-e11-combat-the_six
- S-083: 272a-e11-combat-stats_traits_ability
- S-084: 273a1-e11-combat-flat_damage
- S-085: 274a-e11-combat-long_enough_to_think
- S-086: 275a1-e11-combat-one_ability_each
- S-087: 276a1-e11-combat-every_unit_thinks_the_sa
- S-088: 277a-e11-combat-reading_units_on_screen

## Cards generated
### S-081
- `270a1-e11-combat-three_categories_a_soft_`: symbols=[om_tactical_category_multiplier, om_unit_spawn_for_category, om_unit_hp, om_unit_deal_damage, om_unit_spawn] tests=[test_R_081_01_damage_base_damage_m_b]
- `270a2-e11-combat-three_categories_a_soft_`: symbols=[om_tactical_run_until_eliminated, om_unit_alive, om_tactical_reset, om_command_attack_target, om_tactical_run] tests=[test_R_081_02_line_wins_with_at_least, test_R_081_03_bastion_survives_at_least_20, test_R_081_04_time_to_kill_at_1]

### S-082
- `271a1-e11-combat-the_six`: symbols=[om_unit_profile_category, om_unit_profile_max_hp, om_unit_profile_base_damage, om_unit_profile_attack_interval, om_unit_profile_attack_range] tests=[test_R_082_03_bastion_has_most_by_at]
- `271a2-e11-combat-the_six`: symbols=[om_unit_profile_speed, om_unit_profile_sensor_radius, om_unit_profile_layer_transition_time, om_unit_profile_aoe_radius, om_roster_register_custom_unit] tests=[test_R_082_01_it_exactly_this_table_contract, test_R_082_02_every_strike_unit_faster_than, test_R_082_04_both_strike_units_see_farther, test_R_082_05_only_bombard_has_area_attack, test_R_082_06_it_declares_category_role_stats]

### S-083
- `272a-e11-combat-stats_traits_ability`: symbols=[om_unit_profile_trait_count, om_unit_profile_ability_count, om_unit_apply_trait_modifier, om_unit_set_hp, om_tactical_step] tests=[test_R_083_01_it_has_stats_s_082, test_R_083_02_it_modifies_one_stat_or, test_R_083_03_that_unit_takes_10_percent]

### S-084
- `273a1-e11-combat-flat_damage`: symbols=[om_unit_set_brace_active, om_unit_set_fortify_active, om_unit_set_warden_aura_active, om_unit_fire_aoe_attack, om_command_move] tests=[test_R_084_01_one_attack_lands_for_base, test_R_084_03_every_enemy_on_bombard_s]
- `273a2-e11-combat-flat_damage`: symbols=[om_unit_in_backswing, om_unit_effective_speed, om_map_add_cover, om_era_elevation_damage_bonus_enabled, om_unit_set_elevation_tier] tests=[test_R_084_04_unit_pauses_movement_for_0, test_R_084_05_damage_unmodified_e_01_r, test_R_084_06_no_elevation_bonus_applies_engine]
- `273a3-e11-combat-flat_damage`: symbols=[om_unit_profile_dps] tests=[test_R_084_07_it_base_damage_interval]

### S-085
- `274a-e11-combat-long_enough_to_think`: symbols=[om_tactical_disable_abilities, om_tactical_spawn_force_composition] tests=[test_R_085_01_fight_lasts_at_least_45, test_R_085_02_fight_lasts_150_to_200, test_R_085_03_it_lasts_more_than_120]

### S-086
- `275a1-e11-combat-one_ability_each`: symbols=[om_command_activate_ability, om_unit_output_multiplier, om_unit_ability_cooldown, om_unit_ability_active, om_tactical_run_until_engagement_ends] tests=[test_R_086_01_for_60_ticks_3_s, test_R_086_02_it_triggers_automatically_speed_1, test_R_086_04_every_friendly_unit_within_400, test_R_086_08_it_activates_no_other_enemy]
- `275a2-e11-combat-one_ability_each`: symbols=[om_unit_damage_reduction, om_tactical_telegraph_active, om_tactical_zone_visible_to_enemy, om_unit_set_ability_cooldown, om_tick_read_ability_events] tests=[test_R_086_03_it_immobile_at_once_has, test_R_086_05_after_30_tick_1_5, test_R_086_06_for_400_ticks_20_s, test_R_086_07_command_rejected_nothing_changes]
- `275a3-e11-combat-one_ability_each`: symbols=[om_tactical_tick] tests=[test_R_086_09_explicit_ability_event_with_tick]

### S-087
- `276a1-e11-combat-every_unit_thinks_the_sa`: symbols=[om_unit_set_stealth, om_unit_position_x, om_unit_teleport, om_unit_target, om_command_attack_move] tests=[test_R_087_01_it_moves_200_wu_directly, test_R_087_02_order_wins_over_auto_engagement, test_R_087_03_it_attacks_nearest_such_enemy, test_R_087_04_it_moves_toward_nearest_visible, test_R_087_05_it_anchors_at_its_position, test_R_087_06_it_targets_attacker_return_fire]
- `276a2-e11-combat-every_unit_thinks_the_sa`: symbols=[om_unit_in_flinch, om_unit_targeting_cohort, om_tactical_target_validation_runs_every_tick] tests=[test_R_087_07_it_never_attacks_it_flinches, test_R_087_08_each_unit_re_acquires_on]

### S-088
- `277a-e11-combat-reading_units_on_screen`: symbols=[om_unit_position_y, om_unit_render_craft_count, om_cue_lookup, om_unit_render_silhouette_size] tests=[test_R_088_01_it_appears_as_3_to, test_R_088_02_cue_plays_at_that_tick, test_R_088_03_category_distinguishable_by_silhouette_size]

## Tests with no unbuilt symbol (already satisfiable)
- S-084: test_R_084_02_damage_identical_no_falloff
- S-085: test_R_085_04_strike_vs_strike_resolves_before, test_R_085_05_at_least_30_percent_force

## Symbols with no test (skipped)
Old placeholder symbol(s) no test in this epic calls (R22, re-confirmed): om_unit_step. Not carried into the regenerated cards.

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
- `om_tactical_step`: E-08, E-11, E-12
- `om_tactical_tick`: E-10, E-11, E-14, E-15, E-17
- `om_unit_deal_damage`: E-11, E-15
- `om_unit_set_hp`: E-11, E-13
- `om_unit_spawn`: E-11, E-12, E-13
- `om_unit_teleport`: E-11, E-12
