---
project: /home/westopoli/Projects/ouroboros-manifold
goal: "csrc/tactical_mapgen.c implements S-112 card 3 of 3 (om_map_layout_file_has_required_fields)"
acceptance:
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E17_S112_bones_from_the_library.py::test_R_112_06_it_contains_only_zone_positions"
allowed_files: "csrc/tactical_mapgen.c"
snippet_file: csrc/tactical_mapgen.c
snippet_symbol: "om_map_layout_file_has_required_fields"
header_file: csrc/ouroboros_sim.h
extra_context_files: csrc/om_internal.h
rules_file: projects/ouroboros/rules/E-17.md
test_file: tests/csim/test_E17_S112_bones_from_the_library.py
expected_lines: 12
max_wall_minutes: 45
---

## Brief for DeepSeek

Quoted verbatim from docs/bible/epics/E-17-map-generation.md (### S-112 — Bones from the library):

- R-112-06  Given a layout file, When loaded, Then it contains only zone positions, relationships, chokepoint specs, node placement, and connectivity; never gradient values, era visuals, absolute coordinates, enemy behavior, or difficulty.

## Header slice

(run card_slice.py --write after the skeleton lands)
