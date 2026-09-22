---
project: /home/westopoli/Projects/ouroboros-manifold
goal: "csrc/enemy_macro.c implements S-120 card 1 of 3 (om_macro_validate_state, om_macro_execute_behavior, om_macro_set_state, om_macro_is_hidden, om_macro_trigger_ambush)"
acceptance:
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E14_S120_five_behaviors_three_moods.py::test_R_120_01_its_behavior_one_advance_defend"
allowed_files: "csrc/enemy_macro.c"
snippet_file: csrc/enemy_macro.c
snippet_symbol: "om_macro_validate_state,om_macro_execute_behavior,om_macro_set_state,om_macro_is_hidden,om_macro_trigger_ambush"
header_file: csrc/ouroboros_sim.h
extra_context_files: csrc/om_internal.h
rules_file: projects/ouroboros/rules/E-14.md
test_file: tests/csim/test_E14_S120_five_behaviors_three_moods.py
expected_lines: 60
max_wall_minutes: 45
---

## Brief for DeepSeek

Quoted verbatim from docs/bible/epics/E-14-enemy-macro-behavior.md (### S-120 — Five behaviors, three moods):

- R-120-01  Given a script state, When read, Then its behavior is one of advance, defend, patrol, ambush, retreat and its modifier one of cautious, aggressive, phased; any other value fails script validation.

## Header slice

(run card_slice.py --write after the skeleton lands)
