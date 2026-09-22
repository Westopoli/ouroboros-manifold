---
project: /home/westopoli/Projects/ouroboros-manifold
goal: "csrc/enemy_macro.c implements S-121 card 2 of 2 (om_macro_set_hook_true, om_macro_set_base_transition_true, om_macro_eval_transitions, om_macro_validate_condition_name)"
acceptance:
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E14_S121_timers_and_thresholds_with_noise.py::test_R_121_04_force_transitions_at_once_before"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E14_S121_timers_and_thresholds_with_noise.py::test_R_121_05_q_121_01_code_returns"
allowed_files: "csrc/enemy_macro.c"
snippet_file: csrc/enemy_macro.c
snippet_symbol: "om_macro_set_hook_true,om_macro_set_base_transition_true,om_macro_eval_transitions,om_macro_validate_condition_name"
header_file: csrc/ouroboros_sim.h
extra_context_files: csrc/om_internal.h
rules_file: projects/ouroboros/rules/E-14.md
test_file: tests/csim/test_E14_S121_timers_and_thresholds_with_noise.py
expected_lines: 48
max_wall_minutes: 45
---

## Brief for DeepSeek

Quoted verbatim from docs/bible/epics/E-14-enemy-macro-behavior.md (### S-121 — Timers and thresholds, with noise):

- R-121-04  Given a hook (when-expression, to_state), When its expression is true, Then the force transitions at once, before base transitions are checked.
- R-121-05  Given the conditions "player force in zone" and "enemy in range", When evaluated, Then [Q-121-01: code returns constants 1.0 and False; the real evaluation must be defined].

## Header slice

(run card_slice.py --write after the skeleton lands)
