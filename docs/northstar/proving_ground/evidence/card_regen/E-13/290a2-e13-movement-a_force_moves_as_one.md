---
project: /home/westopoli/Projects/ouroboros-manifold
goal: "csrc/tactical_move.c implements S-095 card 2 of 2 (om_group_is_active, om_command_move)"
acceptance:
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E13_S095_a_force_moves_as_one.py::test_R_095_05_group_terminated"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E13_S095_a_force_moves_as_one.py::test_R_095_06_that_subset_forms_new_group"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E13_S095_a_force_moves_as_one.py::test_R_095_07_it_moves_at_its_own"
allowed_files: "csrc/tactical_move.c"
snippet_file: csrc/tactical_move.c
snippet_symbol: "om_group_is_active,om_command_move"
header_file: csrc/ouroboros_sim.h
extra_context_files: csrc/om_internal.h
rules_file: projects/ouroboros/rules/E-13.md
test_file: tests/csim/test_E13_S095_a_force_moves_as_one.py
expected_lines: 24
max_wall_minutes: 45
---

## Brief for DeepSeek

Quoted verbatim from docs/bible/epics/E-13-movement-and-command.md (### S-095 — A force moves as one):

- R-095-05  Given a move group, When its centroid reaches the destination or every unit reaches its slot (within 1.5 × collision radius), Then the group is terminated.
- R-095-06  Given the player selects a subset and issues a new move, When they do, Then that subset forms a new group at its own slowest pace and the old group continues without it.
- R-095-07  Given a single unit, When moved, Then it moves at its own speed to the click point.

## Header slice

(run card_slice.py --write after the skeleton lands)
