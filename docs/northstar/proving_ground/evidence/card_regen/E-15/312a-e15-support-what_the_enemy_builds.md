---
project: /home/westopoli/Projects/ouroboros-manifold
goal: "csrc/tactical_support.c implements S-128 card 1 of 1 (om_enemy_production_select_category, om_enemy_production_adapt_target)"
acceptance:
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E15_S128_what_the_enemy_builds.py::test_R_128_01_it_produces_category_most_below"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E15_S128_what_the_enemy_builds.py::test_R_128_02_15_percent_target_shifts_to"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E15_S128_what_the_enemy_builds.py::test_R_128_03_it_never_deviates_from_ratio"
allowed_files: "csrc/tactical_support.c"
snippet_file: csrc/tactical_support.c
snippet_symbol: "om_enemy_production_select_category,om_enemy_production_adapt_target"
header_file: csrc/ouroboros_sim.h
extra_context_files: csrc/om_internal.h
rules_file: projects/ouroboros/rules/E-15.md
test_file: tests/csim/test_E15_S128_what_the_enemy_builds.py
expected_lines: 24
max_wall_minutes: 45
---

## Brief for DeepSeek

Quoted verbatim from docs/bible/epics/E-15-reinforcement-supply-and-hazards.md (### S-128 — What the enemy builds):

- R-128-01  Given the enemy's target ratio (per archetype script), When a structure's timer fires, Then it produces the category most below its target share.
- R-128-02  Given the player's composition has a category at 70 percent or more, When the target is computed, Then 15 percent of the target shifts to the counter category (Strike counters Siege, Line counters Strike, Siege counters Line), taken proportionally from the others, then renormalized.
- R-128-03  Given the enemy, When it produces, Then it never deviates from the ratio otherwise.

## Header slice

(run card_slice.py --write after the skeleton lands)
