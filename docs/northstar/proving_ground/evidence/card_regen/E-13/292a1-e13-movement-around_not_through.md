---
project: /home/westopoli/Projects/ouroboros-manifold
goal: "csrc/tactical_move.c implements S-097 card 1 of 3 (om_navmesh_get_cell_size, om_map_set_obstacle_density, om_navmesh_is_cell_blocked, om_navmesh_find_path, om_navmesh_is_path_straightened)"
acceptance:
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E13_S097_around_not_through.py::test_R_097_01_it_100_wu_cells_per"
allowed_files: "csrc/tactical_move.c"
snippet_file: csrc/tactical_move.c
snippet_symbol: "om_navmesh_get_cell_size,om_map_set_obstacle_density,om_navmesh_is_cell_blocked,om_navmesh_find_path,om_navmesh_is_path_straightened"
header_file: csrc/ouroboros_sim.h
extra_context_files: csrc/om_internal.h
rules_file: projects/ouroboros/rules/E-13.md
test_file: tests/csim/test_E13_S097_around_not_through.py
expected_lines: 60
max_wall_minutes: 45
---

## Brief for DeepSeek

Quoted verbatim from docs/bible/epics/E-13-movement-and-command.md (### S-097 — Around, not through):

- R-097-01  Given a map, When the route grid is built, Then it is 100 wu cells per layer, a cell blocked where obstacle density > 0.7, and a route is the shortest path on that grid, straightened by line-of-sight where cells allow.

## Header slice

(run card_slice.py --write after the skeleton lands)
