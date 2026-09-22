---
project: /home/westopoli/Projects/ouroboros-manifold
goal: "csrc/tactical_move.c implements S-095 card 1 of 2 (om_unit_spawn, om_command_group_move, om_unit_get_current_speed, om_unit_get_destination, om_map_add_obstacle)"
acceptance:
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E13_S095_a_force_moves_as_one.py::test_R_095_01_every_unit_s_speed_capped"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E13_S095_a_force_moves_as_one.py::test_R_095_02_each_unit_s_destination_click"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E13_S095_a_force_moves_as_one.py::test_R_095_03_every_unit_s_destination_raw"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E13_S095_a_force_moves_as_one.py::test_R_095_04_that_unit_s_destination_raw"
allowed_files: "csrc/tactical_move.c"
snippet_file: csrc/tactical_move.c
snippet_symbol: "om_unit_spawn,om_command_group_move,om_unit_get_current_speed,om_unit_get_destination,om_map_add_obstacle"
header_file: csrc/ouroboros_sim.h
extra_context_files: csrc/om_internal.h
rules_file: projects/ouroboros/rules/E-13.md
test_file: tests/csim/test_E13_S095_a_force_moves_as_one.py
expected_lines: 60
max_wall_minutes: 45
---

## Brief for DeepSeek

Quoted verbatim from docs/bible/epics/E-13-movement-and-command.md (### S-095 — A force moves as one):

- R-095-01  Given a selection of 2 or more units given a move or attack-move, When they move, Then every unit's speed is capped at the slowest member's speed for that order [Q-095-01: A-557, not built].
- R-095-02  Given the selection, When destinations are assigned, Then each unit's destination is the click point plus its offset from the selection's centroid at command time; offsets are computed once and never updated.
- R-095-03  Given any unit farther than 450 wu from the centroid at command time, When destinations are assigned, Then every unit's destination is the raw click point (scatter fallback).
- R-095-04  Given a slot destination that is not walkable, When assigned, Then that unit's destination is the raw click point.

## Header slice

(run card_slice.py --write after the skeleton lands)
