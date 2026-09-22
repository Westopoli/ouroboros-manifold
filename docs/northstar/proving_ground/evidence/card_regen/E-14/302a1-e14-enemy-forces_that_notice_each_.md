---
project: /home/westopoli/Projects/ouroboros-manifold
goal: "csrc/enemy_macro.c implements S-122 card 1 of 3 (om_macro_init_force, om_macro_bus_set_flag, om_macro_bus_get_flag, om_macro_bind_hook_flag, om_macro_eval_hook_flag)"
acceptance:
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E14_S122_forces_that_notice_each_other.py::test_R_122_01_it_runs_its_own_script"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E14_S122_forces_that_notice_each_other.py::test_R_122_02_any_other_force_s_hook"
allowed_files: "csrc/enemy_macro.c"
snippet_file: csrc/enemy_macro.c
snippet_symbol: "om_macro_init_force,om_macro_bus_set_flag,om_macro_bus_get_flag,om_macro_bind_hook_flag,om_macro_eval_hook_flag"
header_file: csrc/ouroboros_sim.h
extra_context_files: csrc/om_internal.h
rules_file: projects/ouroboros/rules/E-14.md
test_file: tests/csim/test_E14_S122_forces_that_notice_each_other.py
expected_lines: 60
max_wall_minutes: 45
---

## Brief for DeepSeek

Quoted verbatim from docs/bible/epics/E-14-enemy-macro-behavior.md (### S-122 — Forces that notice each other):

- R-122-01  Given a mission with 2 or more enemy forces, When each is created, Then it runs its own script instance, its own faction id if the script assigns one, and its own noise draws.
- R-122-02  Given the trigger bus, When a force sets a flag (for example force_a_routed, objective_alpha_contested), Then any other force's hook reading that flag can fire on its next evaluation.

## Header slice

(run card_slice.py --write after the skeleton lands)
