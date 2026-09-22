---
project: /home/westopoli/Projects/ouroboros-manifold
goal: "csrc/tactical_mapgen.c implements S-115 card 1 of 2 (om_map_flavoring_stability_multiplier, om_map_clamp_flavoring_delta, om_map_compute_economy_obstacle_delta, om_map_compute_tension_cover_delta, om_map_set_simulation_coupling)"
acceptance:
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E17_S115_the_region_shapes_the_terrain.py::test_R_115_01_interference_hazard_anchor_count_cover"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E17_S115_the_region_shapes_the_terrain.py::test_R_115_02_economy_lowers_obstacle_density_along"
allowed_files: "csrc/tactical_mapgen.c"
snippet_file: csrc/tactical_mapgen.c
snippet_symbol: "om_map_flavoring_stability_multiplier,om_map_clamp_flavoring_delta,om_map_compute_economy_obstacle_delta,om_map_compute_tension_cover_delta,om_map_set_simulation_coupling"
header_file: csrc/ouroboros_sim.h
extra_context_files: csrc/om_internal.h
rules_file: projects/ouroboros/rules/E-17.md
test_file: tests/csim/test_E17_S115_the_region_shapes_the_terrain.py
expected_lines: 60
max_wall_minutes: 45
---

## Brief for DeepSeek

Quoted verbatim from docs/bible/epics/E-17-map-generation.md (### S-115 — The region shapes the terrain):

- R-115-01  Given region stability s and capacity c, When baselines are set, Then interference, hazard anchor count, and cover scale with (100 − s)/100 and obstacle density with (100 − c)/100, each within a bounded multiplier [Q-117-01: exact multipliers].
- R-115-02  Given individual fields, When deltas are applied, Then economy lowers obstacle density along routes and adds cover from infrastructure, tension raises cover, military raises obstacle density near defensive positions, population scales total feature density; deltas are bounded so they never overwhelm the baseline.

## Header slice

(run card_slice.py --write after the skeleton lands)
