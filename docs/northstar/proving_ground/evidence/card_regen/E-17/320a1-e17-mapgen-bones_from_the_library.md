---
project: /home/westopoli/Projects/ouroboros-manifold
goal: "csrc/tactical_mapgen.c implements S-112 card 1 of 3 (om_map_get_compatible_layout_count, om_map_get_compatible_layouts, om_map_layout_matches_archetype_filter, om_map_select_layout_uniform, om_map_instantiate_zone_pos)"
acceptance:
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E17_S112_bones_from_the_library.py::test_R_112_01_every_layout_satisfying_at_least"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E17_S112_bones_from_the_library.py::test_R_112_02_it_drawn_uniformly_at_random"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E17_S112_bones_from_the_library.py::test_R_112_03_its_zone_positions_percentages_canvas"
allowed_files: "csrc/tactical_mapgen.c"
snippet_file: csrc/tactical_mapgen.c
snippet_symbol: "om_map_get_compatible_layout_count,om_map_get_compatible_layouts,om_map_layout_matches_archetype_filter,om_map_select_layout_uniform,om_map_instantiate_zone_pos"
header_file: csrc/ouroboros_sim.h
extra_context_files: csrc/om_internal.h
rules_file: projects/ouroboros/rules/E-17.md
test_file: tests/csim/test_E17_S112_bones_from_the_library.py
expected_lines: 60
max_wall_minutes: 45
---

## Brief for DeepSeek

Quoted verbatim from docs/bible/epics/E-17-map-generation.md (### S-112 — Bones from the library):

- R-112-01  Given an archetype, When candidates are gathered, Then every layout satisfying at least one of the archetype's compatibility filters (structural checklists, 2 to 3 per archetype) enters the pool.
- R-112-02  Given the pool, When one is chosen, Then it is drawn uniformly at random [Q-113-01: hints as bias, fairness as gate].
- R-112-03  Given a layout, When instantiated, Then its zone positions (percentages of canvas) scale to the canvas dimensions with jitter of up to 3 percent of canvas per zone, spatial ratios preserved.

## Header slice

(run card_slice.py --write after the skeleton lands)
