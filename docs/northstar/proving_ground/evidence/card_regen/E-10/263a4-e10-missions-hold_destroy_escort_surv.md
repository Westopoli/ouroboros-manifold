---
project: /home/westopoli/Projects/ouroboros-manifold
goal: "csrc/mission.c implements S-075 card 4 of 4 (om_mission_check_terminated)"
acceptance:
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E10_S075_hold_destroy_escort_survive_eliminate.py::test_R_075_07_it_ends_on_first_every"
allowed_files: "csrc/mission.c"
snippet_file: csrc/mission.c
snippet_symbol: "om_mission_check_terminated"
header_file: csrc/ouroboros_sim.h
extra_context_files: csrc/om_internal.h
rules_file: projects/ouroboros/rules/E-10.md
test_file: tests/csim/test_E10_S075_hold_destroy_escort_survive_eliminate.py
expected_lines: 12
max_wall_minutes: 45
---

## Brief for DeepSeek

Quoted verbatim from docs/bible/epics/E-10-missions.md (### S-075 — Hold, destroy, escort, survive, eliminate):

- R-075-07  Given the mission, When it ends, Then it ends on the first of: every primary objective complete or failed; the time limit reached; the player's force eliminated.

## Header slice

(run card_slice.py --write after the skeleton lands)
