# Card regen report -- E-07

Module: `csrc/lifecycle.c`. Rules file: `projects/ouroboros/rules/E-07.md`. Bible: `docs/bible/epics/E-07-civilizational-lifecycle.md`.

Old placeholder symbol(s) this epic's existing queue cards name: `om_lifecycle_step`.

Cards generated: 6. Distinct symbols carded: 15. Tests assigned to a card: 27.

## Numbering prefixes (per story, reused from the old queue)
- S-049: 230a-e07-lifecycle-a_revolt_can_birth_a_nat
- S-050: 231a-e07-lifecycle-old_loyalties
- S-051: 232a-e07-lifecycle-nations_that_never_were
- S-052: 233a-e07-lifecycle-no_plot_armor
- S-053: 234a-e07-lifecycle-every_faction_has_an_age
- S-054: 235a-e07-lifecycle-where_a_civilization_end

## Cards generated
### S-049
- `230a-e07-lifecycle-a_revolt_can_birth_a_nat`: symbols=[om_event_queue_external, om_tick_revolts, om_tick_pruned] tests=[test_R_049_01_one_draw_sets_success_rate, test_R_049_02_no_faction_forms, test_R_049_03_region_keeps_military_0_40, test_R_049_04_its_id_breakaway_tick_region, test_R_049_05_success_rate_1_0_with, test_R_049_06_nothing_happens_chain_pruned, test_R_049_07_every_edge_touching_it_becomes]

### S-050
- `231a-e07-lifecycle-old_loyalties`: symbols=[om_region_set_previous_owner, om_region_previous_owner, om_tick_reversions] tests=[test_R_050_01_with_probability_0_5_one, test_R_050_02_it_never_reverts, test_R_050_03_it_never_reverts, test_R_050_04_region_s_owner_b_held, test_R_050_05_it_records_original_restored_factions]

### S-051
- `232a-e07-lifecycle-nations_that_never_were`: symbols=[om_faction_set_created_tick, om_faction_is_active, om_tick_absorptions, om_faction_mark_conquered_this_tick, om_faction_remove] tests=[test_R_051_01_it_removed_from_registry_every, test_R_051_02_its_region_passes_to_bordering, test_R_051_03_nothing_happens, test_R_051_04_it_skipped_this_tick, test_R_051_05_it_never_removed, test_R_051_06_those_regions_become_unowned_with]

### S-052
- `233a-e07-lifecycle-no_plot_armor`: symbols=[om_player_faction_collapsed] tests=[test_R_052_01_it_has_zero_regions_its]

### S-053
- `234a-e07-lifecycle-every_faction_has_an_age`: symbols=[om_faction_set_event_window_counts, om_faction_phase] tests=[test_R_053_01_its_phase_fragmentation, test_R_053_02_its_phase_overextension, test_R_053_03_conflict, test_R_053_04_expansion, test_R_053_05_consolidation, test_R_053_06_equilibrium, test_R_053_07_they_evaluated_in_exactly_this]

### S-054
- `235a-e07-lifecycle-where_a_civilization_end`: symbols=[om_world_is_terminal] tests=[test_R_054_01_deferred_with_feature_no_rule]

## Tests with no unbuilt symbol (already satisfiable)
- S-052: test_R_052_02_no_rule_anywhere_checks_whether

## Symbols with no test (skipped)
Old placeholder symbol(s) no test in this epic calls (R22, re-confirmed): om_lifecycle_step. Not carried into the regenerated cards.

## Stories needing more than 6 cards (design-lane question, not decided)
none

## Cards with no acceptance test of their own (design-lane question, not decided)
A card can end up with symbols but zero tests when every test needing them also needs a later card's symbols (the test's own closure is wider than the 5-symbol cap covers in one card). Candidates: (a) merge such a card forward into the next one, exceeding the cap only for this story (needs approval -- sizing caps are fixed); (b) accept the card as a pure prerequisite with no acceptance of its own (needs a card-format change -- card_lint.py currently hard-errors on empty acceptance); (c) leave it as a real card_lint finding and re-cut the test itself so its assertions split the same way the symbols do.
none

## Cross-epic symbol ownership
none touching this epic
