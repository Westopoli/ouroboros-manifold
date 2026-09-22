---
project: /home/westopoli/Projects/ouroboros-manifold
goal: "csrc/tactical_move.c implements S-100 card 1 of 1 (om_unit_clear_orders, om_unit_set_facing, om_command_attack_target_kiting)"
acceptance:
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E13_S100_facing.py::test_R_100_01_it_faces_target_moving_with"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E13_S100_facing.py::test_R_100_02_turn_rate_capped_at_6"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E13_S100_facing.py::test_R_100_03_it_faces_pursuer"
allowed_files: "csrc/tactical_move.c"
snippet_file: csrc/tactical_move.c
snippet_symbol: "om_unit_clear_orders,om_unit_set_facing,om_command_attack_target_kiting"
header_file: csrc/ouroboros_sim.h
extra_context_files: csrc/om_internal.h
rules_file: projects/ouroboros/rules/E-13.md
test_file: tests/csim/test_E13_S100_facing.py
expected_lines: 36
max_wall_minutes: 45
---

## Brief for DeepSeek

Quoted verbatim from docs/bible/epics/E-13-movement-and-command.md (### S-100 — Facing):

- R-100-01  Given a unit attacking a target, When facing updates, Then it faces the target; given moving with no target, it faces its heading; given idle with no target, it keeps its last facing.
- R-100-02  Given a facing change, When it turns, Then the turn rate is capped at 6.0 rad/s for Strike, 4.0 for Line, 2.5 for Siege.
- R-100-03  Given a unit retreating from a pursuer under attack-target, When facing updates, Then it faces the pursuer.

## Header slice

(run card_slice.py --write after the skeleton lands)
