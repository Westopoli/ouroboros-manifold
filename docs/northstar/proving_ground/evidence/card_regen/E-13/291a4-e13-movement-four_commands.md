---
project: /home/westopoli/Projects/ouroboros-manifold
goal: "csrc/tactical_move.c implements S-096 card 4 of 4 (om_command_queue_attack_move, om_unit_get_order_kind, om_replay_get_command_count_at_tick)"
acceptance:
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E13_S096_four_commands.py::test_R_096_07_all_them_applied_before_any"
allowed_files: "csrc/tactical_move.c"
snippet_file: csrc/tactical_move.c
snippet_symbol: "om_command_queue_attack_move,om_unit_get_order_kind,om_replay_get_command_count_at_tick"
header_file: csrc/ouroboros_sim.h
extra_context_files: csrc/om_internal.h
rules_file: projects/ouroboros/rules/E-13.md
test_file: tests/csim/test_E13_S096_four_commands.py
expected_lines: 36
max_wall_minutes: 45
---

## Brief for DeepSeek

Quoted verbatim from docs/bible/epics/E-13-movement-and-command.md (### S-096 — Four commands):

- R-096-07  Given commands for tick t, When the tick runs, Then all of them are applied before any state advances, in arrival order, and recorded with the tick number for replay.

## Header slice

(run card_slice.py --write after the skeleton lands)
