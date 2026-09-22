---
project: /home/westopoli/Projects/ouroboros-manifold
goal: "csrc/worldgen.c implements S-021 card 1 of 2 (om_world_generated, om_faction_template, om_gen_set_player_preference, om_gen_set_preference_weight, om_gen_set_extra_edges_enabled)"
acceptance:
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E03_S021_a_fresh_galaxy_from_a_seed.py::test_R_021_01_region_count_integer_drawn_uniformly"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E03_S021_a_fresh_galaxy_from_a_seed.py::test_R_021_02_faction_0_player_civilization_factions"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E03_S021_a_fresh_galaxy_from_a_seed.py::test_R_021_03_it_draws_independently_from_isolated"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E03_S021_a_fresh_galaxy_from_a_seed.py::test_R_021_04_it_one_isolated_twin_colony"
allowed_files: "csrc/worldgen.c"
snippet_file: csrc/worldgen.c
snippet_symbol: "om_world_generated,om_faction_template,om_gen_set_player_preference,om_gen_set_preference_weight,om_gen_set_extra_edges_enabled"
header_file: csrc/ouroboros_sim.h
extra_context_files: csrc/om_internal.h
rules_file: projects/ouroboros/rules/E-03.md
test_file: tests/csim/test_E03_S021_a_fresh_galaxy_from_a_seed.py
expected_lines: 60
max_wall_minutes: 45
---

## Brief for DeepSeek

Quoted verbatim from docs/bible/epics/E-03-world-generation.md (### S-021 — A fresh galaxy from a seed):

- R-021-01  Given a seed, When the world is generated, Then the region count is an integer drawn uniformly from [60, 110] and the faction count is 15.
- R-021-02  Given generation, When factions are placed, Then faction 0 is the player civilization and factions 1 through 14 cycle conqueror, fortifier, opportunist in that order.
- R-021-03  Given a faction, When its template is rolled, Then it draws independently from Isolated, Twin Colony, Archipelago with equal weight by default; the player faction's weights are swayed toward their chosen preference (R-021-04) and every NPC faction always uses equal weight.
- R-021-04  Given the player, When they set a template preference before generation, Then it is one of Isolated, Twin Colony, Archipelago, or no preference; a set preference gives that template probability `WORLD_PLAYER_PREFERENCE_WEIGHT`, default 0.50, and the other two templates split the remainder equally (default 0.25 each), in the player faction's own roll only — configurable for playtesting, never locking the outcome, never affecting any NPC faction's roll.

## Header slice

(run card_slice.py --write after the skeleton lands)
