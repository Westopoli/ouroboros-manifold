---
project: /home/westopoli/Projects/ouroboros-manifold
goal: "csrc/tactical_mapgen.c implements S-113 card 2 of 2 (om_map_node_get_owner, om_map_is_reachable_from_staging, om_map_is_reachable_from_all_spawns, om_map_compute_chokepoint_width)"
acceptance:
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E17_S113_nine_kinds_of_place.py::test_R_113_04_it_reachable_from_both_staging"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E17_S113_nine_kinds_of_place.py::test_R_113_05_passable_width_w_200_wu"
allowed_files: "csrc/tactical_mapgen.c"
snippet_file: csrc/tactical_mapgen.c
snippet_symbol: "om_map_node_get_owner,om_map_is_reachable_from_staging,om_map_is_reachable_from_all_spawns,om_map_compute_chokepoint_width"
header_file: csrc/ouroboros_sim.h
extra_context_files: csrc/om_internal.h
rules_file: projects/ouroboros/rules/E-17.md
test_file: tests/csim/test_E17_S113_nine_kinds_of_place.py
expected_lines: 48
max_wall_minutes: 45
---

## Brief for DeepSeek

Quoted verbatim from docs/bible/epics/E-17-map-generation.md (### S-113 — Nine kinds of place):

- R-113-04  Given a vantage node, When checked, Then it is reachable from both staging and every spawn point and pre-owned by nobody.
- R-113-05  Given a chokepoint spec of width ratio w, When instantiated, Then the passable width is w × 200 wu (standard formation width).

## Header slice

(run card_slice.py --write after the skeleton lands)
