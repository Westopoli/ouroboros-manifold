---
project: /home/westopoli/Projects/ouroboros-manifold
goal: "csrc/enemy_macro.c implements S-122 card 3 of 3 (om_macro_bus_get_active_flags_count)"
acceptance:
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E14_S122_forces_that_notice_each_other.py::test_R_122_04_typical_script_fires_2_to"
allowed_files: "csrc/enemy_macro.c"
snippet_file: csrc/enemy_macro.c
snippet_symbol: "om_macro_bus_get_active_flags_count"
header_file: csrc/ouroboros_sim.h
extra_context_files: csrc/om_internal.h
rules_file: projects/ouroboros/rules/E-14.md
test_file: tests/csim/test_E14_S122_forces_that_notice_each_other.py
expected_lines: 12
max_wall_minutes: 45
---

## Brief for DeepSeek

Quoted verbatim from docs/bible/epics/E-14-enemy-macro-behavior.md (### S-122 — Forces that notice each other):

- R-122-04  Given a mission, When flags are counted, Then a typical script fires 2 to 5 flags [Q-122-01: who sets force_a_routed and the like; no code sets flags today].

## Header slice

(run card_slice.py --write after the skeleton lands)
