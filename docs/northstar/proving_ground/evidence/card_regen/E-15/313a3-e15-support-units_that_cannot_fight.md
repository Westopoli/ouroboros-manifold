---
project: /home/westopoli/Projects/ouroboros-manifold
goal: "csrc/tactical_support.c implements S-129 card 3 of 3 (om_unit_has_non_combat_visual_tag, om_unit_is_non_combat_supported)"
acceptance:
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E15_S129_units_that_cannot_fight.py::test_R_129_03_it_reads_as_non_combat"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E15_S129_units_that_cannot_fight.py::test_R_129_04_q_129_01_only_convoys"
allowed_files: "csrc/tactical_support.c"
snippet_file: csrc/tactical_support.c
snippet_symbol: "om_unit_has_non_combat_visual_tag,om_unit_is_non_combat_supported"
header_file: csrc/ouroboros_sim.h
extra_context_files: csrc/om_internal.h
rules_file: projects/ouroboros/rules/E-15.md
test_file: tests/csim/test_E15_S129_units_that_cannot_fight.py
expected_lines: 24
max_wall_minutes: 45
---

## Brief for DeepSeek

Quoted verbatim from docs/bible/epics/E-15-reinforcement-supply-and-hazards.md (### S-129 — Units that cannot fight):

- R-129-03  Given a non-combat unit, When drawn, Then it reads as non-combat at a glance.
- R-129-04  Given the asset categories of the hub (science units, intelligence operatives, cultural missions), When a mission includes them, Then [Q-129-01: only convoys and evacuees exist in code; the others are undefined; cultural missions have an onboarding opt-out per A-074].

## Header slice

(run card_slice.py --write after the skeleton lands)
