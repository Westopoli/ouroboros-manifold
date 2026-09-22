---
project: /home/westopoli/Projects/ouroboros-manifold
goal: "csrc/enemy_macro.c implements S-120 card 3 of 3 (om_macro_evaluation_interval_ticks, om_macro_tick, om_macro_has_evaluated, om_macro_get_last_issued_command_type)"
acceptance:
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E14_S120_five_behaviors_three_moods.py::test_R_120_04_it_runs_every_40_ticks"
allowed_files: "csrc/enemy_macro.c"
snippet_file: csrc/enemy_macro.c
snippet_symbol: "om_macro_evaluation_interval_ticks,om_macro_tick,om_macro_has_evaluated,om_macro_get_last_issued_command_type"
header_file: csrc/ouroboros_sim.h
extra_context_files: csrc/om_internal.h
rules_file: projects/ouroboros/rules/E-14.md
test_file: tests/csim/test_E14_S120_five_behaviors_three_moods.py
expected_lines: 48
max_wall_minutes: 45
---

## Brief for DeepSeek

Quoted verbatim from docs/bible/epics/E-14-enemy-macro-behavior.md (### S-120 — Five behaviors, three moods):

- R-120-04  Given a macro evaluation, When it runs, Then it runs every 40 ticks (2 s) and issues commands only through move, attack_move, attack_target, activate_ability.

## Header slice

(run card_slice.py --write after the skeleton lands)
