---
project: /home/westopoli/Projects/ouroboros-manifold
goal: "csrc/mission.c implements S-078 card 3 of 3 (om_chronicle_has_mission_consequence_flag, om_set_neighbors, om_mission_apply_target_adjacent_player)"
acceptance:
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E10_S078_a_battle_becomes_history.py::test_R_078_06_resulting_events_carry_mission_consequence"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E10_S078_a_battle_becomes_history.py::test_R_078_07_delta_applies_to_every_player"
allowed_files: "csrc/mission.c"
snippet_file: csrc/mission.c
snippet_symbol: "om_chronicle_has_mission_consequence_flag,om_set_neighbors,om_mission_apply_target_adjacent_player"
header_file: csrc/ouroboros_sim.h
extra_context_files: csrc/om_internal.h
rules_file: projects/ouroboros/rules/E-10.md
test_file: tests/csim/test_E10_S078_a_battle_becomes_history.py
expected_lines: 36
max_wall_minutes: 45
---

## Brief for DeepSeek

Quoted verbatim from docs/bible/epics/E-10-missions.md (### S-078 — A battle becomes history):

- R-078-06  Given the applied deltas, When the time jump starts, Then the resulting events carry the mission-consequence flag for the chronicle (E-09).
- R-078-07  Given a target of `adjacent_player`, When applied, Then the delta applies to every player-owned neighbor of the mission region.

## Header slice

(run card_slice.py --write after the skeleton lands)
