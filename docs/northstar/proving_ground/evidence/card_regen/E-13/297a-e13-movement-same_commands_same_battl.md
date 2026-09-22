---
project: /home/westopoli/Projects/ouroboros-manifold
goal: "csrc/tactical_move.c implements S-102 card 1 of 1 (om_world_get_state_checksum, om_steering_get_sweep_angle_count, om_steering_get_sweep_angle_at)"
acceptance:
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E13_S102_same_commands_same_battle.py::test_R_102_01_every_position_facing_target_identical"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E13_S102_same_commands_same_battle.py::test_R_102_02_order_fixed_documented_no_wall"
allowed_files: "csrc/tactical_move.c"
snippet_file: csrc/tactical_move.c
snippet_symbol: "om_world_get_state_checksum,om_steering_get_sweep_angle_count,om_steering_get_sweep_angle_at"
header_file: csrc/ouroboros_sim.h
extra_context_files: csrc/om_internal.h
rules_file: projects/ouroboros/rules/E-13.md
test_file: tests/csim/test_E13_S102_same_commands_same_battle.py
expected_lines: 36
max_wall_minutes: 45
---

## Brief for DeepSeek

Quoted verbatim from docs/bible/epics/E-13-movement-and-command.md (### S-102 — Same commands, same battle):

- R-102-01  Given a seed, a map, and a command stream, When two machines run 5,000 ticks, Then every position, facing, and target is identical at every tick and the checksums match.
- R-102-02  Given the steering sweep, When angles are tried, Then the order is fixed and documented; no wall-clock or hash-order input reaches movement.

## Header slice

(run card_slice.py --write after the skeleton lands)
