---
project: /home/westopoli/Projects/ouroboros-manifold
goal: "csrc/tactical_move.c implements S-096 card 3 of 4 (om_command_activate_ability, om_unit_is_braced, om_unit_has_active_buff, om_command_issue_named, om_command_queue_move)"
acceptance:
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E13_S096_four_commands.py::test_R_096_05_each_unit_with_its_ability"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E13_S096_four_commands.py::test_R_096_06_it_rejected_with_reason_no"
allowed_files: "csrc/tactical_move.c"
snippet_file: csrc/tactical_move.c
snippet_symbol: "om_command_activate_ability,om_unit_is_braced,om_unit_has_active_buff,om_command_issue_named,om_command_queue_move"
header_file: csrc/ouroboros_sim.h
extra_context_files: csrc/om_internal.h
rules_file: projects/ouroboros/rules/E-13.md
test_file: tests/csim/test_E13_S096_four_commands.py
expected_lines: 60
max_wall_minutes: 45
---

## Brief for DeepSeek

Quoted verbatim from docs/bible/epics/E-13-movement-and-command.md (### S-096 — Four commands):

- R-096-05  Given activate-ability, When issued to a selection, Then each unit with its ability ready activates it; Brace toggles.
- R-096-06  Given any other command name (patrol, hold, stop, follow), When received, Then it is rejected with a reason and no state changes.

## Header slice

(run card_slice.py --write after the skeleton lands)
