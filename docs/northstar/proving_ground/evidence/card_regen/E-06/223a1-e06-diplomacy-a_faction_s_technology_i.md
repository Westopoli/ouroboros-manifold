---
project: /home/westopoli/Projects/ouroboros-manifold
goal: "csrc/diplomacy.c implements S-045 card 1 of 2 (om_tech_step, om_gen_set_faction_count, om_gen_set_region_range, om_breakaway_create, om_faction_set_last_knowledge_lost)"
acceptance:
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E06_S045_a_faction_s_technology_is_one_number.py::test_R_045_04_nothing_changes"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E06_S045_a_faction_s_technology_is_one_number.py::test_R_045_05_it_equals_average_starting_population"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E06_S045_a_faction_s_technology_is_one_number.py::test_R_045_06_it_equals_parent_s_tech"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E06_S045_a_faction_s_technology_is_one_number.py::test_R_045_08_no_draw_made_tech_never"
allowed_files: "csrc/diplomacy.c"
snippet_file: csrc/diplomacy.c
snippet_symbol: "om_tech_step,om_gen_set_faction_count,om_gen_set_region_range,om_breakaway_create,om_faction_set_last_knowledge_lost"
header_file: csrc/ouroboros_sim.h
extra_context_files: csrc/om_internal.h
rules_file: projects/ouroboros/rules/E-06.md
test_file: tests/csim/test_E06_S045_a_faction_s_technology_is_one_number.py
expected_lines: 60
max_wall_minutes: 45
---

## Brief for DeepSeek

Quoted verbatim from docs/bible/epics/E-06-diplomacy-and-technology.md (### S-045 — A faction's technology is one number):

- R-045-04  Given a faction with no regions, When tech grows, Then nothing changes.
- R-045-05  Given a starting faction, When tech is set, Then it equals the average starting population of its regions · 0.25.
- R-045-06  Given a breakaway is created, When its tech is set, Then it equals the parent's tech at that tick.
- R-045-08  Given a faction not eligible under R-045-07, When the technology step runs, Then no draw is made and tech never falls.

## Header slice

(run card_slice.py --write after the skeleton lands)
