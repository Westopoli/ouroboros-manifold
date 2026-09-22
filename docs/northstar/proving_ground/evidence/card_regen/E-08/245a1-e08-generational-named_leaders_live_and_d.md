---
project: /home/westopoli/Projects/ouroboros-manifold
goal: "csrc/generational.c implements S-060 card 1 of 3 (om_faction_create_named, om_faction_supreme_commander, om_region_assign_regional_commander, om_region_regional_commander, om_character_create_random)"
acceptance:
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E08_S060_named_leaders_live_and_die.py::test_R_060_01_it_gets_supreme_commander_in"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E08_S060_named_leaders_live_and_die.py::test_R_060_02_it_uniform_integer_in_150"
allowed_files: "csrc/generational.c"
snippet_file: csrc/generational.c
snippet_symbol: "om_faction_create_named,om_faction_supreme_commander,om_region_assign_regional_commander,om_region_regional_commander,om_character_create_random"
header_file: csrc/ouroboros_sim.h
extra_context_files: csrc/om_internal.h
rules_file: projects/ouroboros/rules/E-08.md
test_file: tests/csim/test_E08_S060_named_leaders_live_and_die.py
expected_lines: 60
max_wall_minutes: 45
---

## Brief for DeepSeek

Quoted verbatim from docs/bible/epics/E-08-generational-structure.md (### S-060 — Named leaders live and die):

- R-060-01  Given a faction is created, When named, Then it gets a supreme commander in its first region; Given a region is colonized or conquered, When named, Then it gets a regional commander.
- R-060-02  Given a character is created, When its lifespan is rolled, Then it is a uniform integer in [150, 350] ticks.

## Header slice

(run card_slice.py --write after the skeleton lands)
