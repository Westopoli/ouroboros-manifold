---
project: /home/westopoli/Projects/ouroboros-manifold
goal: "csrc/worldgen.c implements S-021 card 2 of 2 (om_region_neighbors, om_world_edge_count)"
acceptance:
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E03_S021_a_fresh_galaxy_from_a_seed.py::test_R_021_05_isolated_one_home_region_plus"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E03_S021_a_fresh_galaxy_from_a_seed.py::test_R_021_06_its_highest_numbered_frontier_region"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E03_S021_a_fresh_galaxy_from_a_seed.py::test_R_021_07_each_links_to_one_already"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E03_S021_a_fresh_galaxy_from_a_seed.py::test_R_021_08_exactly_max_1_floor_0"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E03_S021_a_fresh_galaxy_from_a_seed.py::test_R_021_09_every_region_reachable_from_every"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E03_S021_a_fresh_galaxy_from_a_seed.py::test_R_021_10_every_faction_s_template_roll"
allowed_files: "csrc/worldgen.c"
snippet_file: csrc/worldgen.c
snippet_symbol: "om_region_neighbors,om_world_edge_count"
header_file: csrc/ouroboros_sim.h
extra_context_files: csrc/om_internal.h
rules_file: projects/ouroboros/rules/E-03.md
test_file: tests/csim/test_E03_S021_a_fresh_galaxy_from_a_seed.py
expected_lines: 24
max_wall_minutes: 45
---

## Brief for DeepSeek

Quoted verbatim from docs/bible/epics/E-03-world-generation.md (### S-021 — A fresh galaxy from a seed):

- R-021-05  Given a faction's rolled template, When its regions are placed, Then: Isolated is one home region plus two frontier regions, both adjacent to the home; Twin Colony is two home regions adjacent to each other, each with its own count of 1 or 2 frontier regions (drawn uniformly per home) adjacent to that home; Archipelago is one home region plus three frontier regions, arranged so at least one frontier is not adjacent to the home or to another frontier (reached only through a chain of frontiers). Every region outside a faction's template is empty with no owner and no fields.
- R-021-06  Given a faction's template is placed, When corridors are laid, Then its highest-numbered frontier region (Isolated/Archipelago: numbered in placement order; Twin Colony: the second home's highest-numbered frontier) links to a chain of exactly 1 empty region, and the 15 factions' corridor ends are linked in faction order into one chain.
- R-021-07  Given generation, When the remaining empties are attached, Then each links to one already-connected region chosen uniformly at random, re-rolling up to 20 times to avoid a home region.
- R-021-08  Given a world of N regions, When extra edges are added, Then exactly max(1, floor(0.12 · N)) extra edges are attempted between distinct non-adjacent regions, never between two home regions, with at most 10 times that many draws.
- R-021-09  Given any generated world, When connectivity is checked, Then every region is reachable from every other.
- R-021-10  Given the same seed, When generated twice, Then every faction's template roll, the region ids, adjacency lists, edge types, and starting fields are identical.

## Header slice

(run card_slice.py --write after the skeleton lands)
