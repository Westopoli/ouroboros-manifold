---
project: /home/westopoli/Projects/ouroboros-manifold
goal: "csrc/tactical_mapgen.c implements S-113 card 1 of 2 (om_map_get_node_count, om_map_get_node_type, om_map_count_nodes_of_type, om_map_get_nth_node_of_type, om_map_has_flank_bypass)"
acceptance:
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E17_S113_nine_kinds_of_place.py::test_R_113_01_it_exactly_one_objective_staging"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E17_S113_nine_kinds_of_place.py::test_R_113_02_it_has_at_least_one"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E17_S113_nine_kinds_of_place.py::test_R_113_03_at_least_one_flank_route"
allowed_files: "csrc/tactical_mapgen.c"
snippet_file: csrc/tactical_mapgen.c
snippet_symbol: "om_map_get_node_count,om_map_get_node_type,om_map_count_nodes_of_type,om_map_get_nth_node_of_type,om_map_has_flank_bypass"
header_file: csrc/ouroboros_sim.h
extra_context_files: csrc/om_internal.h
rules_file: projects/ouroboros/rules/E-17.md
test_file: tests/csim/test_E17_S113_nine_kinds_of_place.py
expected_lines: 60
max_wall_minutes: 45
---

## Brief for DeepSeek

Quoted verbatim from docs/bible/epics/E-17-map-generation.md (### S-113 — Nine kinds of place):

- R-113-01  Given any spine node, When typed, Then it is exactly one of objective, staging, transit, chokepoint, flank_route, vantage, hazard_anchor, spawn_point, extraction.
- R-113-02  Given any map, When checked, Then it has at least one objective and at least one staging node.
- R-113-03  Given a chokepoint, When checked, Then at least one flank route bypasses it.

## Header slice

(run card_slice.py --write after the skeleton lands)
