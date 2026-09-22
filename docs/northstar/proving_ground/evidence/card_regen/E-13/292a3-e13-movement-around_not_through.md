---
project: /home/westopoli/Projects/ouroboros-manifold
goal: "csrc/tactical_move.c implements S-097 card 3 of 3 (om_steering_get_obstacle_repulsion)"
acceptance:
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E13_S097_around_not_through.py::test_R_097_09_repulsion_opposes_move_units_following"
allowed_files: "csrc/tactical_move.c"
snippet_file: csrc/tactical_move.c
snippet_symbol: "om_steering_get_obstacle_repulsion"
header_file: csrc/ouroboros_sim.h
extra_context_files: csrc/om_internal.h
rules_file: projects/ouroboros/rules/E-13.md
test_file: tests/csim/test_E13_S097_around_not_through.py
expected_lines: 12
max_wall_minutes: 45
---

## Brief for DeepSeek

Quoted verbatim from docs/bible/epics/E-13-movement-and-command.md (### S-097 — Around, not through):

- R-097-09  Given a direct-move unit (no route waypoints), When obstacle density ahead within 50 wu exceeds 0.3, Then a repulsion opposes the move; units following route waypoints are exempt.

## Header slice

(run card_slice.py --write after the skeleton lands)
