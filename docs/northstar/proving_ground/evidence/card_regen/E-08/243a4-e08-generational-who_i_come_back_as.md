---
project: /home/westopoli/Projects/ouroboros-manifold
goal: "csrc/generational.c implements S-058 card 4 of 4 (om_character_is_main_character, om_character_name_reuse_cooldown)"
acceptance:
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E08_S058_who_i_come_back_as.py::test_R_058_06_commander_marked_as_main_character"
allowed_files: "csrc/generational.c"
snippet_file: csrc/generational.c
snippet_symbol: "om_character_is_main_character,om_character_name_reuse_cooldown"
header_file: csrc/ouroboros_sim.h
extra_context_files: csrc/om_internal.h
rules_file: projects/ouroboros/rules/E-08.md
test_file: tests/csim/test_E08_S058_who_i_come_back_as.py
expected_lines: 24
max_wall_minutes: 45
---

## Brief for DeepSeek

Quoted verbatim from docs/bible/epics/E-08-generational-structure.md (### S-058 — Who I come back as):

- R-058-06  Given any selection, When it completes, Then the commander is marked as a main character so its name is reserved longer after death (E-21 naming).

## Header slice

(run card_slice.py --write after the skeleton lands)
