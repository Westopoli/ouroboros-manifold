# Card regen report -- E-03

Module: `csrc/worldgen.c`. Rules file: `projects/ouroboros/rules/E-03.md`. Bible: `docs/bible/epics/E-03-world-generation.md`.

Old placeholder symbol(s) this epic's existing queue cards name: `om_world_generate`.

Cards generated: 3. Distinct symbols carded: 8. Tests assigned to a card: 11.

## Numbering prefixes (per story, reused from the old queue)
- S-021: 211a1-e03-worldgen-a_fresh_galaxy_from_a_se
- S-022: (none -- already satisfiable)
- S-023: 213a-e03-worldgen-routes_carry_armies_trad
- S-024: (none -- already satisfiable)
- S-025: (none -- already satisfiable)

## Cards generated
### S-021
- `211a1-e03-worldgen-a_fresh_galaxy_from_a_se`: symbols=[om_world_generated, om_faction_template, om_gen_set_player_preference, om_gen_set_preference_weight, om_gen_set_extra_edges_enabled] tests=[test_R_021_01_region_count_integer_drawn_uniformly, test_R_021_02_faction_0_player_civilization_factions, test_R_021_03_it_draws_independently_from_isolated, test_R_021_04_it_one_isolated_twin_colony]
- `211a2-e03-worldgen-a_fresh_galaxy_from_a_se`: symbols=[om_region_neighbors, om_world_edge_count] tests=[test_R_021_05_isolated_one_home_region_plus, test_R_021_06_its_highest_numbered_frontier_region, test_R_021_07_each_links_to_one_already, test_R_021_08_exactly_max_1_floor_0, test_R_021_09_every_region_reachable_from_every, test_R_021_10_every_faction_s_template_roll]

### S-022
(no card -- every test already satisfiable with built symbols)

### S-023
- `213a-e03-worldgen-routes_carry_armies_trad`: symbols=[om_tick_friction] tests=[test_R_023_03_it_names_edge_type_drift]

### S-024
(no card -- every test already satisfiable with built symbols)

### S-025
(no card -- every test already satisfiable with built symbols)

## Tests with no unbuilt symbol (already satisfiable)
- S-022: test_R_022_01_population_uniform_in_55_75, test_R_022_02_economy_clamp_p_1_1, test_R_022_03_economy_phase_tension_phase_independent, test_R_022_04_rng_consumed_in_exactly_that, test_R_022_05_archetype_s_own_range_replaces
- S-023: test_R_023_01_edge_between_two_regions_same, test_R_023_02_it_returns_neighbors_whose_edge, test_R_023_04_both_directions_report_same_type
- S-024: test_R_024_01_every_edge_between_their_regions, test_R_024_02_every_edge_between_their_regions, test_R_024_03_its_edges_to_conqueror_s, test_R_024_04_its_edges_to_colonizer_s, test_R_024_05_no_edge_type_changed
- S-025: test_R_025_01_they_not_adjacent_npc_to, test_R_025_02_they_not_adjacent_npc_to, test_R_025_03_it_passes_through_at_least, test_R_025_04_that_draw_rejected_re_rolled

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
