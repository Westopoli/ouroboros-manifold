---
project: /home/westopoli/Projects/ouroboros-manifold
goal: "csrc/enemy_macro.c implements S-125 card 2 of 2 (om_session_capture_is_enabled, om_mission_end, om_session_capture_get_size, om_session_capture_read)"
acceptance:
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E14_S125_how_hard_the_enemy_tries.py::test_R_125_03_command_streams_outcomes_captured_for"
allowed_files: "csrc/enemy_macro.c"
snippet_file: csrc/enemy_macro.c
snippet_symbol: "om_session_capture_is_enabled,om_mission_end,om_session_capture_get_size,om_session_capture_read"
header_file: csrc/ouroboros_sim.h
extra_context_files: csrc/om_internal.h
rules_file: projects/ouroboros/rules/E-14.md
test_file: tests/csim/test_E14_S125_how_hard_the_enemy_tries.py
expected_lines: 48
max_wall_minutes: 45
---

## Brief for DeepSeek

Quoted verbatim from docs/bible/epics/E-14-enemy-macro-behavior.md (### S-125 — How hard the enemy tries):

- R-125-03  Given external playtesters, When sessions run, Then command streams and outcomes are captured for the future learned-opponent target (A-156, data capture only).

## Header slice

(run card_slice.py --write after the skeleton lands)
