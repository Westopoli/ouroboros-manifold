---
project: /home/westopoli/Projects/ouroboros-manifold
goal: "csrc/tactical_support.c implements S-130 card 2 of 3 (om_structure_init_drifting, om_structure_get_position, om_structure_is_in_capture_radius, om_hazard_spawn_moving_interference, om_hazard_sample_interference)"
acceptance:
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E15_S130_the_battlefield_moves.py::test_R_130_03_its_capture_radius_spawn_position"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E15_S130_the_battlefield_moves.py::test_R_130_04_interference_at_any_point_follows"
allowed_files: "csrc/tactical_support.c"
snippet_file: csrc/tactical_support.c
snippet_symbol: "om_structure_init_drifting,om_structure_get_position,om_structure_is_in_capture_radius,om_hazard_spawn_moving_interference,om_hazard_sample_interference"
header_file: csrc/ouroboros_sim.h
extra_context_files: csrc/om_internal.h
rules_file: projects/ouroboros/rules/E-15.md
test_file: tests/csim/test_E15_S130_the_battlefield_moves.py
expected_lines: 60
max_wall_minutes: 45
---

## Brief for DeepSeek

Quoted verbatim from docs/bible/epics/E-15-reinforcement-supply-and-hazards.md (### S-130 — The battlefield moves):

- R-130-03  Given a drifting structure, When it moves, Then its capture radius and spawn position move with it.
- R-130-04  Given a sensor interference source with motion, When ticks pass, Then interference at any point follows the source (E-12 R-090-04).

## Header slice

(run card_slice.py --write after the skeleton lands)
