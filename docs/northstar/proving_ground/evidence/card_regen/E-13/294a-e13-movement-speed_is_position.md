---
project: /home/westopoli/Projects/ouroboros-manifold
goal: "csrc/tactical_move.c implements S-099 card 1 of 1 (om_unit_engage)"
acceptance:
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E13_S099_speed_is_position.py::test_R_099_01_strike_wing_reaches_flank_slots"
allowed_files: "csrc/tactical_move.c"
snippet_file: csrc/tactical_move.c
snippet_symbol: "om_unit_engage"
header_file: csrc/ouroboros_sim.h
extra_context_files: csrc/om_internal.h
rules_file: projects/ouroboros/rules/E-13.md
test_file: tests/csim/test_E13_S099_speed_is_position.py
expected_lines: 12
max_wall_minutes: 45
---

## Brief for DeepSeek

Quoted verbatim from docs/bible/epics/E-13-movement-and-command.md (### S-099 — Speed is position):

- R-099-01  Given a Strike wing and a Line force both approaching an engaged, immovable friendly front, When they arrive, Then the Strike wing reaches the flank slots first, purely from the steering rules of S-097.

## Header slice

(run card_slice.py --write after the skeleton lands)
