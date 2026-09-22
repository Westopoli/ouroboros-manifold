---
project: /home/westopoli/Projects/ouroboros-manifold
goal: "csrc/diplomacy.c implements S-042 card 1 of 1 (om_diplomacy_init, om_tick_friction, om_diplomacy_step, om_world_generated, om_faction_create_breakaway)"
acceptance:
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E06_S042_three_ways_to_feel_about_a_neighbor.py::test_R_042_01_it_exactly_one_hostile_neutral"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E06_S042_three_ways_to_feel_about_a_neighbor.py::test_R_042_02_each_includes_other_s_regions"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E06_S042_three_ways_to_feel_about_a_neighbor.py::test_R_042_03_neither_attacks_other_no_friction"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E06_S042_three_ways_to_feel_about_a_neighbor.py::test_R_042_04_adjacency_bonus_crosses_their_trade"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E06_S042_three_ways_to_feel_about_a_neighbor.py::test_R_042_05_their_stance_hostile_if_their"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E06_S042_three_ways_to_feel_about_a_neighbor.py::test_R_042_06_it_hostile_toward_every_existing"
allowed_files: "csrc/diplomacy.c"
snippet_file: csrc/diplomacy.c
snippet_symbol: "om_diplomacy_init,om_tick_friction,om_diplomacy_step,om_world_generated,om_faction_create_breakaway"
header_file: csrc/ouroboros_sim.h
extra_context_files: csrc/om_internal.h
rules_file: projects/ouroboros/rules/E-06.md
test_file: tests/csim/test_E06_S042_three_ways_to_feel_about_a_neighbor.py
expected_lines: 60
max_wall_minutes: 45
---

## Brief for DeepSeek

Quoted verbatim from docs/bible/epics/E-06-diplomacy-and-technology.md (### S-042 — Three ways to feel about a neighbor):

- R-042-01  Given any two distinct factions, When their stance is read, Then it is exactly one of hostile, neutral, cooperative, symmetric for the pair; a faction's stance toward itself reads cooperative.
- R-042-02  Given a hostile pair, When agents decide and friction applies, Then each includes the other's regions as attack candidates and friction applies on their shared borders.
- R-042-03  Given a neutral pair, When agents decide and friction applies, Then neither attacks the other, no friction applies, and no adjacency bonus crosses their edges.
- R-042-04  Given a cooperative pair, When drift and tech run, Then adjacency bonus crosses their trade edges (E-02 R-015-03), tech convergence applies (S-047), and no friction or attacks occur.
- R-042-05  Given two starting factions, When the world begins, Then their stance is hostile if their archetype pair is in the override table (conqueror with anyone; fortifier with player and opportunist; opportunist with player; schism with player, fortifier, opportunist, warlord) and neutral otherwise; at launch every starting pair is hostile.
- R-042-06  Given a breakaway faction is created, When stances are set, Then it is hostile toward every existing faction and every existing faction is hostile toward it.

## Header slice

(run card_slice.py --write after the skeleton lands)
