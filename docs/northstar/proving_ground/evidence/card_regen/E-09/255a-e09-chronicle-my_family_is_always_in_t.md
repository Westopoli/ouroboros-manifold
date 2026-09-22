---
project: /home/westopoli/Projects/ouroboros-manifold
goal: "csrc/chronicle.c implements S-070 card 1 of 1 (om_chronicle_score_event, om_event_fire_manual, om_event_get_attached_character, om_chronicle_render_character_rank)"
acceptance:
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E09_S070_my_family_is_always_in_the_story.py::test_R_070_01_it_receives_0_8_lineage"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E09_S070_my_family_is_always_in_the_story.py::test_R_070_02_lineage_member_attached_to_event"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E09_S070_my_family_is_always_in_the_story.py::test_R_070_03_it_military_rank_no_lineage"
allowed_files: "csrc/chronicle.c"
snippet_file: csrc/chronicle.c
snippet_symbol: "om_chronicle_score_event,om_event_fire_manual,om_event_get_attached_character,om_chronicle_render_character_rank"
header_file: csrc/ouroboros_sim.h
extra_context_files: csrc/om_internal.h
rules_file: projects/ouroboros/rules/E-09.md
test_file: tests/csim/test_E09_S070_my_family_is_always_in_the_story.py
expected_lines: 48
max_wall_minutes: 45
---

## Brief for DeepSeek

Quoted verbatim from docs/bible/epics/E-09-chronicle.md (### S-070 — My family is always in the story):

- R-070-01  Given an event fires in a region where a lineage member lives, When scored, Then it receives the +0.8 lineage term (R-066-02), no other special handling.
- R-070-02  Given an event of significance tier 3 or higher in a lineage region, When logged, Then the lineage member is attached to the event record (E-08 R-060-05).
- R-070-03  Given a lineage member appears in a fragment, When their rank is rendered, Then it is a military rank; no lineage member is ever framed as a governor, trader, or political leader.

## Header slice

(run card_slice.py --write after the skeleton lands)
