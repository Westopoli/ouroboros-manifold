---
project: /home/westopoli/Projects/ouroboros-manifold
goal: "csrc/fog.c implements S-091 card 1 of 2 (om_map_add_vantage_node, om_unit_get_cross_layer_factor, om_set_era_flag, om_unit_spawn_with_elevation, om_unit_get_effective_sensor_radius_to_target_elevation)"
acceptance:
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E12_S091_standing_high.py::test_R_091_01_cross_layer_factors_double_extend"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E12_S091_standing_high.py::test_R_091_02_observer_s_effective_radius_multiplied"
allowed_files: "csrc/fog.c"
snippet_file: csrc/fog.c
snippet_symbol: "om_map_add_vantage_node,om_unit_get_cross_layer_factor,om_set_era_flag,om_unit_spawn_with_elevation,om_unit_get_effective_sensor_radius_to_target_elevation"
header_file: csrc/ouroboros_sim.h
extra_context_files: csrc/om_internal.h
rules_file: projects/ouroboros/rules/E-12.md
test_file: tests/csim/test_E12_S091_standing_high.py
expected_lines: 60
max_wall_minutes: 45
---

## Brief for DeepSeek

Quoted verbatim from docs/bible/epics/E-12-fog-and-sensors.md (### S-091 — Standing high):

- R-091-01  Given a unit within a vantage node's radius (default 100 wu), When visibility is computed, Then cross-layer factors double and extend one layer (E-01 R-005-06).
- R-091-02  Given an elevation tier difference of d between observer and target, When the era enables elevation sensor bonus, Then the observer's effective radius is multiplied by 1 + 0.15 · d [Q-092-01: nothing in code reads this].

## Header slice

(run card_slice.py --write after the skeleton lands)
