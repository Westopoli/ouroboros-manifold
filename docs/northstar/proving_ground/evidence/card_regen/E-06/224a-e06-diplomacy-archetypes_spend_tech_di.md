---
project: /home/westopoli/Projects/ouroboros-manifold
goal: "csrc/diplomacy.c implements S-046 card 1 of 1 (om_faction_tech_multipliers, om_faction_tech_attack, om_faction_tech_defense, om_faction_tech_economy)"
acceptance:
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E06_S046_archetypes_spend_tech_differently.py::test_R_046_01_attack_1_096_defense_1"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E06_S046_archetypes_spend_tech_differently.py::test_R_046_02_attack_1_018_defense_1"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E06_S046_archetypes_spend_tech_differently.py::test_R_046_03_all_three_multipliers_1_0"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E06_S046_archetypes_spend_tech_differently.py::test_R_046_05_q_048_01_nothing_in"
allowed_files: "csrc/diplomacy.c"
snippet_file: csrc/diplomacy.c
snippet_symbol: "om_faction_tech_multipliers,om_faction_tech_attack,om_faction_tech_defense,om_faction_tech_economy"
header_file: csrc/ouroboros_sim.h
extra_context_files: csrc/om_internal.h
rules_file: projects/ouroboros/rules/E-06.md
test_file: tests/csim/test_E06_S046_archetypes_spend_tech_differently.py
expected_lines: 48
max_wall_minutes: 45
---

## Brief for DeepSeek

Quoted verbatim from docs/bible/epics/E-06-diplomacy-and-technology.md (### S-046 — Archetypes spend tech differently):

- R-046-01  Given a conqueror at tech 60, When multipliers are read, Then attack 1.096, defense 1.012, economy 1.012.
- R-046-02  Given a fortifier at tech 60, When read, Then attack 1.018, defense 1.054, economy 1.048.
- R-046-03  Given any archetype at tech 0, When read, Then all three multipliers are 1.0.
- R-046-05  Given the economy multiplier, When read, Then [Q-048-01: nothing in the sim consumes it today].

## Header slice

(run card_slice.py --write after the skeleton lands)
