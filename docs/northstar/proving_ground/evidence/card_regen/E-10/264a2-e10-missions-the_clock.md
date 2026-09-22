---
project: /home/westopoli/Projects/ouroboros-manifold
goal: "csrc/mission.c implements S-076 card 2 of 2 (om_mission_is_ended, om_mission_get_objective_score, om_mission_end)"
acceptance:
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E10_S076_the_clock.py::test_R_076_03_current_objective_completion_values_final"
allowed_files: "csrc/mission.c"
snippet_file: csrc/mission.c
snippet_symbol: "om_mission_is_ended,om_mission_get_objective_score,om_mission_end"
header_file: csrc/ouroboros_sim.h
extra_context_files: csrc/om_internal.h
rules_file: projects/ouroboros/rules/E-10.md
test_file: tests/csim/test_E10_S076_the_clock.py
expected_lines: 36
max_wall_minutes: 45
---

## Brief for DeepSeek

Quoted verbatim from docs/bible/epics/E-10-missions.md (### S-076 — The clock):

- R-076-03  Given the deadline passes, When the mission ends, Then the current objective completion values are final; finishing early never raises the score.

## Header slice

(run card_slice.py --write after the skeleton lands)
