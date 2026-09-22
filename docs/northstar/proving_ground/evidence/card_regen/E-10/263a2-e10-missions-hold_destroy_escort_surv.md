---
project: /home/westopoli/Projects/ouroboros-manifold
goal: "csrc/mission.c implements S-075 card 2 of 4 (om_mission_get_objective_completion, om_mission_setup_destroy_targets, om_mission_eval_destroy_targets, om_mission_setup_escort, om_mission_eval_escort)"
acceptance:
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E10_S075_hold_destroy_escort_survive_eliminate.py::test_R_075_02_hold_timer_advances_only_while"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E10_S075_hold_destroy_escort_survive_eliminate.py::test_R_075_03_completion_destroyed_designated_targets_total"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E10_S075_hold_destroy_escort_survive_eliminate.py::test_R_075_04_completion_escort_units_that_reached"
allowed_files: "csrc/mission.c"
snippet_file: csrc/mission.c
snippet_symbol: "om_mission_get_objective_completion,om_mission_setup_destroy_targets,om_mission_eval_destroy_targets,om_mission_setup_escort,om_mission_eval_escort"
header_file: csrc/ouroboros_sim.h
extra_context_files: csrc/om_internal.h
rules_file: projects/ouroboros/rules/E-10.md
test_file: tests/csim/test_E10_S075_hold_destroy_escort_survive_eliminate.py
expected_lines: 60
max_wall_minutes: 45
---

## Brief for DeepSeek

Quoted verbatim from docs/bible/epics/E-10-missions.md (### S-075 — Hold, destroy, escort, survive, eliminate):

- R-075-02  Given hold_zone, When evaluated per tick, Then the hold timer advances only while no enemy unit is inside the zone radius; completion = elapsed/required.
- R-075-03  Given destroy_targets, When evaluated, Then completion = destroyed designated targets/total.
- R-075-04  Given escort_to_extraction, When evaluated, Then completion = escort units that reached the extraction point alive/total escort units.

## Header slice

(run card_slice.py --write after the skeleton lands)
