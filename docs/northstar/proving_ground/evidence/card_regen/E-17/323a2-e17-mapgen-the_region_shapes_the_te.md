---
project: /home/westopoli/Projects/ouroboros-manifold
goal: "csrc/tactical_mapgen.c implements S-115 card 2 of 2 (om_map_get_simulation_coupling, om_map_generate, om_map_is_valid)"
acceptance:
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E17_S115_the_region_shapes_the_terrain.py::test_R_115_03_layouts_hints_alone_produce_valid"
allowed_files: "csrc/tactical_mapgen.c"
snippet_file: csrc/tactical_mapgen.c
snippet_symbol: "om_map_get_simulation_coupling,om_map_generate,om_map_is_valid"
header_file: csrc/ouroboros_sim.h
extra_context_files: csrc/om_internal.h
rules_file: projects/ouroboros/rules/E-17.md
test_file: tests/csim/test_E17_S115_the_region_shapes_the_terrain.py
expected_lines: 36
max_wall_minutes: 45
---

## Brief for DeepSeek

Quoted verbatim from docs/bible/epics/E-17-map-generation.md (### S-115 — The region shapes the terrain):

- R-115-03  Given simulation coupling disabled, When a map is generated, Then layouts and hints alone produce a valid map.

## Header slice

(run card_slice.py --write after the skeleton lands)
