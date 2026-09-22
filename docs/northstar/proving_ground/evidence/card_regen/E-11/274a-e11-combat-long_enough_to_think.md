---
project: /home/westopoli/Projects/ouroboros-manifold
goal: "csrc/unit.c implements S-085 card 1 of 1 (om_tactical_disable_abilities, om_tactical_spawn_force_composition)"
acceptance:
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E11_S085_long_enough_to_think.py::test_R_085_01_fight_lasts_at_least_45"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E11_S085_long_enough_to_think.py::test_R_085_02_fight_lasts_150_to_200"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E11_S085_long_enough_to_think.py::test_R_085_03_it_lasts_more_than_120"
allowed_files: "csrc/unit.c"
snippet_file: csrc/unit.c
snippet_symbol: "om_tactical_disable_abilities,om_tactical_spawn_force_composition"
header_file: csrc/ouroboros_sim.h
extra_context_files: csrc/om_internal.h
rules_file: projects/ouroboros/rules/E-11.md
test_file: tests/csim/test_E11_S085_long_enough_to_think.py
expected_lines: 24
max_wall_minutes: 45
---

## Brief for DeepSeek

Quoted verbatim from docs/bible/epics/E-11-units-and-combat.md (### S-085 — Long enough to think):

- R-085-01  Given a 10v10 mirror of any single type at attack range with no abilities, When resolved, Then the fight lasts at least 45 s.
- R-085-02  Given a 50v50 mirror with the default balanced composition, When resolved, Then the fight lasts 150 to 200 s.
- R-085-03  Given a 100v100 balanced battle, When resolved, Then it lasts more than 120 s.

## Header slice

(run card_slice.py --write after the skeleton lands)
