---
project: /home/westopoli/Projects/ouroboros-manifold
goal: "csrc/tactical_mapgen.c implements S-114 card 2 of 2 (om_gradient_get_anchor_radius, om_map_add_layer_restriction_zone, om_map_sample_layer_accessibility, om_route_grid_is_cell_blocked)"
acceptance:
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E17_S114_texture_from_gradients.py::test_R_114_03_obstacle_density_anchors_at_chokepoints"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E17_S114_texture_from_gradients.py::test_R_114_04_every_layer_not_listed_gets"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E17_S114_texture_from_gradients.py::test_R_114_05_cell_blocked"
allowed_files: "csrc/tactical_mapgen.c"
snippet_file: csrc/tactical_mapgen.c
snippet_symbol: "om_gradient_get_anchor_radius,om_map_add_layer_restriction_zone,om_map_sample_layer_accessibility,om_route_grid_is_cell_blocked"
header_file: csrc/ouroboros_sim.h
extra_context_files: csrc/om_internal.h
rules_file: projects/ouroboros/rules/E-17.md
test_file: tests/csim/test_E17_S114_texture_from_gradients.py
expected_lines: 48
max_wall_minutes: 45
---

## Brief for DeepSeek

Quoted verbatim from docs/bible/epics/E-17-map-generation.md (### S-114 — Texture from gradients):

- R-114-03  Given the instantiated spine, When sources are placed, Then obstacle density anchors at chokepoints (intensity 0.85, radius 600) and staging (0.60, 800); elevation at vantage nodes (0.90, 700); interference at hazard anchors (0.75, 500); cover at chokepoints (0.55, 550), objectives (0.50, 400), hazard anchors (0.35, 400); flank routes get light obstacles (0.35, 450) and cover (0.40, 450).
- R-114-04  Given a zone with layer restrictions, When masks are placed, Then every layer not listed gets a full-intensity blocking source of radius 600 at the zone, and accessibility at a point is open unless a blocking source's sampled value ≥ 0.5.
- R-114-05  Given obstacle density > 0.7 at a cell, When the route grid is built (E-13 R-097-01), Then the cell is blocked.

## Header slice

(run card_slice.py --write after the skeleton lands)
