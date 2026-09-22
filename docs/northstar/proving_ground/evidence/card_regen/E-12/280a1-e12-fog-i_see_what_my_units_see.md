---
project: /home/westopoli/Projects/ouroboros-manifold
goal: "csrc/fog.c implements S-089 card 1 of 2 (om_unit_spawn, om_map_add_interference_zone, om_map_add_cover, om_visibility_compute, om_unit_can_see)"
acceptance:
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E12_S089_i_see_what_my_units_see.py::test_R_089_01_its_effective_radius_r_1"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E12_S089_i_see_what_my_units_see.py::test_R_089_06_b_seeing_computed_independently_asymmetric"
allowed_files: "csrc/fog.c"
snippet_file: csrc/fog.c
snippet_symbol: "om_unit_spawn,om_map_add_interference_zone,om_map_add_cover,om_visibility_compute,om_unit_can_see"
header_file: csrc/ouroboros_sim.h
extra_context_files: csrc/om_internal.h
rules_file: projects/ouroboros/rules/E-12.md
test_file: tests/csim/test_E12_S089_i_see_what_my_units_see.py
expected_lines: 60
max_wall_minutes: 45
---

## Brief for DeepSeek

Quoted verbatim from docs/bible/epics/E-12-fog-and-sensors.md (### S-089 — I see what my units see):

- R-089-01  Given an observer with sensor radius r at interference i, When visibility is computed, Then its effective radius is r × (1 − i), and an enemy on the same layer is visible if its distance ≤ that radius and no cover blocks the line.
- R-089-06  Given visibility A sees B, When B's set is computed, Then B seeing A is computed independently (asymmetric sensors are normal).

## Header slice

(run card_slice.py --write after the skeleton lands)
