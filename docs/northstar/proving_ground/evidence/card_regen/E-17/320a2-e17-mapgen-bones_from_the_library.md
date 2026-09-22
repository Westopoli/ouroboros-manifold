---
project: /home/westopoli/Projects/ouroboros-manifold
goal: "csrc/tactical_mapgen.c implements S-112 card 2 of 3 (om_map_generate_spine, om_map_count_distinct_routes_staging_to_objective, om_map_verify_flank_connections, om_map_library_total_layouts, om_map_layout_file_has_forbidden_fields)"
acceptance:
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E17_S112_bones_from_the_library.py::test_R_112_04_layout_s_connectivity_honored_there"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E17_S112_bones_from_the_library.py::test_R_112_05_it_holds_between_10_20"
allowed_files: "csrc/tactical_mapgen.c"
snippet_file: csrc/tactical_mapgen.c
snippet_symbol: "om_map_generate_spine,om_map_count_distinct_routes_staging_to_objective,om_map_verify_flank_connections,om_map_library_total_layouts,om_map_layout_file_has_forbidden_fields"
header_file: csrc/ouroboros_sim.h
extra_context_files: csrc/om_internal.h
rules_file: projects/ouroboros/rules/E-17.md
test_file: tests/csim/test_E17_S112_bones_from_the_library.py
expected_lines: 60
max_wall_minutes: 45
---

## Brief for DeepSeek

Quoted verbatim from docs/bible/epics/E-17-map-generation.md (### S-112 — Bones from the library):

- R-112-04  Given the instantiated nodes, When edges are laid, Then the layout's connectivity is honored, there are at least 2 distinct routes from staging to every objective, at most the layout's allowed dead ends, and every flank route connects to at least 2 non-flank nodes.
- R-112-05  Given the library at launch, When loaded, Then it holds between 10 and 20 layouts and each archetype has at least 4 compatible layouts [Q-112-01: current count].

## Header slice

(run card_slice.py --write after the skeleton lands)
