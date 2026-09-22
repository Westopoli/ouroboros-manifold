---
project: /home/westopoli/Projects/ouroboros-manifold
goal: "csrc/tactical_move.c implements S-096 card 1 of 4 (om_unit_get_hp, om_unit_attack, om_unit_get_target, om_unit_get_pos, om_command_attack_move)"
acceptance:
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E13_S096_four_commands.py::test_R_096_01_it_acquires_no_target_returns"
allowed_files: "csrc/tactical_move.c"
snippet_file: csrc/tactical_move.c
snippet_symbol: "om_unit_get_hp,om_unit_attack,om_unit_get_target,om_unit_get_pos,om_command_attack_move"
header_file: csrc/ouroboros_sim.h
extra_context_files: csrc/om_internal.h
rules_file: projects/ouroboros/rules/E-13.md
test_file: tests/csim/test_E13_S096_four_commands.py
expected_lines: 60
max_wall_minutes: 45
---

## Brief for DeepSeek

Quoted verbatim from docs/bible/epics/E-13-movement-and-command.md (### S-096 — Four commands):

- R-096-01  Given a plain move, When the unit travels, Then it acquires no target, returns no fire, and does not stop when hit.

## Header slice

(run card_slice.py --write after the skeleton lands)
