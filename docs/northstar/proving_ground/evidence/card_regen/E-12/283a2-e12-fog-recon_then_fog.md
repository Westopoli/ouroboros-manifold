---
project: /home/westopoli/Projects/ouroboros-manifold
goal: "csrc/fog.c implements S-092 card 2 of 4 (om_map_add_spawn_point, om_recon_is_feature_visible, om_recon_is_enemy_visible, om_recon_is_structure_ownership_visible, om_recon_is_spawn_point_visible)"
acceptance:
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E12_S092_recon_then_fog.py::test_R_092_01_every_obstacle_cover_cluster_hazard"
allowed_files: "csrc/fog.c"
snippet_file: csrc/fog.c
snippet_symbol: "om_map_add_spawn_point,om_recon_is_feature_visible,om_recon_is_enemy_visible,om_recon_is_structure_ownership_visible,om_recon_is_spawn_point_visible"
header_file: csrc/ouroboros_sim.h
extra_context_files: csrc/om_internal.h
rules_file: projects/ouroboros/rules/E-12.md
test_file: tests/csim/test_E12_S092_recon_then_fog.py
expected_lines: 60
max_wall_minutes: 45
---

## Brief for DeepSeek

Quoted verbatim from docs/bible/epics/E-12-fog-and-sensors.md (### S-092 — Recon, then fog):

- R-092-01  Given the recon phase, When the map is shown, Then every obstacle, cover cluster, hazard zone, spine node type, layer accessibility, and elevation contour is visible, and no enemy unit, structure ownership, or spawn point is.

## Header slice

(run card_slice.py --write after the skeleton lands)
