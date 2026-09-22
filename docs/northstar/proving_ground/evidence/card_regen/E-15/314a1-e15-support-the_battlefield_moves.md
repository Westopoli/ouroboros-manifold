---
project: /home/westopoli/Projects/ouroboros-manifold
goal: "csrc/tactical_support.c implements S-130 card 1 of 3 (om_drift_interpolate, om_objective_setup_drifting, om_objective_get_center, om_tactical_tick_to, om_objective_is_contested)"
acceptance:
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E15_S130_the_battlefield_moves.py::test_R_130_01_its_position_interpolation_along_its"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E15_S130_the_battlefield_moves.py::test_R_130_02_hold_zone_moves_with_it"
allowed_files: "csrc/tactical_support.c"
snippet_file: csrc/tactical_support.c
snippet_symbol: "om_drift_interpolate,om_objective_setup_drifting,om_objective_get_center,om_tactical_tick_to,om_objective_is_contested"
header_file: csrc/ouroboros_sim.h
extra_context_files: csrc/om_internal.h
rules_file: projects/ouroboros/rules/E-15.md
test_file: tests/csim/test_E15_S130_the_battlefield_moves.py
expected_lines: 60
max_wall_minutes: 45
---

## Brief for DeepSeek

Quoted verbatim from docs/bible/epics/E-15-reinforcement-supply-and-hazards.md (### S-130 — The battlefield moves):

- R-130-01  Given a spine node of type objective or reinforcement_structure with waypoints, a period in ticks, and a mode, When ticks pass, Then its position is the interpolation along its waypoints, ping-pong (out and back) or loop, at tick mod period.
- R-130-02  Given a drifting objective, When it moves, Then the hold zone moves with it and progress continues only while no enemy is inside the moved zone.

## Header slice

(run card_slice.py --write after the skeleton lands)
