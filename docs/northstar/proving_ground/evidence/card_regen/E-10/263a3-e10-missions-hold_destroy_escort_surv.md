---
project: /home/westopoli/Projects/ouroboros-manifold
goal: "csrc/mission.c implements S-075 card 3 of 4 (om_mission_setup_survive, om_mission_eval_survive, om_mission_setup_eliminate, om_mission_eval_eliminate, om_mission_setup_termination)"
acceptance:
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E10_S075_hold_destroy_escort_survive_eliminate.py::test_R_075_05_completion_elapsed_required_0_if"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E10_S075_hold_destroy_escort_survive_eliminate.py::test_R_075_06_completion_enemy_hp_destroyed_initial"
allowed_files: "csrc/mission.c"
snippet_file: csrc/mission.c
snippet_symbol: "om_mission_setup_survive,om_mission_eval_survive,om_mission_setup_eliminate,om_mission_eval_eliminate,om_mission_setup_termination"
header_file: csrc/ouroboros_sim.h
extra_context_files: csrc/om_internal.h
rules_file: projects/ouroboros/rules/E-10.md
test_file: tests/csim/test_E10_S075_hold_destroy_escort_survive_eliminate.py
expected_lines: 60
max_wall_minutes: 45
---

## Brief for DeepSeek

Quoted verbatim from docs/bible/epics/E-10-missions.md (### S-075 — Hold, destroy, escort, survive, eliminate):

- R-075-05  Given survive_duration, When evaluated, Then completion = elapsed/required, and 0 if every player unit is dead before the time.
- R-075-06  Given eliminate_force, When evaluated, Then completion = enemy HP destroyed/initial enemy HP.

## Header slice

(run card_slice.py --write after the skeleton lands)
