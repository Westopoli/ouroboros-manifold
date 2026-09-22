---
project: /home/westopoli/Projects/ouroboros-manifold
goal: "csrc/mission.c implements S-075 card 1 of 4 (om_mission_build_objectives, om_mission_objective_count, om_mission_get_objectives, om_mission_setup_hold_zone, om_mission_eval_hold_zone)"
acceptance:
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E10_S075_hold_destroy_escort_survive_eliminate.py::test_R_075_01_there_exactly_one_primary_objective"
allowed_files: "csrc/mission.c"
snippet_file: csrc/mission.c
snippet_symbol: "om_mission_build_objectives,om_mission_objective_count,om_mission_get_objectives,om_mission_setup_hold_zone,om_mission_eval_hold_zone"
header_file: csrc/ouroboros_sim.h
extra_context_files: csrc/om_internal.h
rules_file: projects/ouroboros/rules/E-10.md
test_file: tests/csim/test_E10_S075_hold_destroy_escort_survive_eliminate.py
expected_lines: 60
max_wall_minutes: 45
---

## Brief for DeepSeek

Quoted verbatim from docs/bible/epics/E-10-missions.md (### S-075 — Hold, destroy, escort, survive, eliminate):

- R-075-01  Given a mission, When objectives are built, Then there is exactly one primary objective and 0 to 3 secondary ones, weights summing to 1.0, the primary carrying at least 0.6.

## Header slice

(run card_slice.py --write after the skeleton lands)
