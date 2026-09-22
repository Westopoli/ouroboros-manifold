---
project: /home/westopoli/Projects/ouroboros-manifold
goal: "csrc/diplomacy.c implements S-048 card 1 of 2 (om_tech_tier, om_faction_tech_tier, om_mission_start, om_mission_unit_tier, om_faction_next_mission_unit_tier)"
acceptance:
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E06_S048_three_tiers_of_technology.py::test_R_048_01_it_1_in_34_67"
allowed_files: "csrc/diplomacy.c"
snippet_file: csrc/diplomacy.c
snippet_symbol: "om_tech_tier,om_faction_tech_tier,om_mission_start,om_mission_unit_tier,om_faction_next_mission_unit_tier"
header_file: csrc/ouroboros_sim.h
extra_context_files: csrc/om_internal.h
rules_file: projects/ouroboros/rules/E-06.md
test_file: tests/csim/test_E06_S048_three_tiers_of_technology.py
expected_lines: 60
max_wall_minutes: 45
---

## Brief for DeepSeek

Quoted verbatim from docs/bible/epics/E-06-diplomacy-and-technology.md (### S-048 — Three tiers of technology):

- R-048-01  Given tech in [0, 34), When the tier is read, Then it is 1; in [34, 67) it is 2; in [67, 100] it is 3.

## Header slice

(run card_slice.py --write after the skeleton lands)
