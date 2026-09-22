---
project: /home/westopoli/Projects/ouroboros-manifold
goal: "csrc/enemy_macro.c implements S-122 card 2 of 3 (om_macro_bus_register_vocab, om_macro_validate_bus_flag, om_macro_set_force_hp_pct, om_macro_update_bus_runner, om_macro_player_enter_objective)"
acceptance:
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E14_S122_forces_that_notice_each_other.py::test_R_122_03_every_flag_it_reads_or"
allowed_files: "csrc/enemy_macro.c"
snippet_file: csrc/enemy_macro.c
snippet_symbol: "om_macro_bus_register_vocab,om_macro_validate_bus_flag,om_macro_set_force_hp_pct,om_macro_update_bus_runner,om_macro_player_enter_objective"
header_file: csrc/ouroboros_sim.h
extra_context_files: csrc/om_internal.h
rules_file: projects/ouroboros/rules/E-14.md
test_file: tests/csim/test_E14_S122_forces_that_notice_each_other.py
expected_lines: 60
max_wall_minutes: 45
---

## Brief for DeepSeek

Quoted verbatim from docs/bible/epics/E-14-enemy-macro-behavior.md (### S-122 — Forces that notice each other):

- R-122-03  Given a script, When validated, Then every flag it reads or sets is in the script's declared bus vocabulary, else validation fails.

## Header slice

(run card_slice.py --write after the skeleton lands)
