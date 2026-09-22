---
project: /home/westopoli/Projects/ouroboros-manifold
goal: "csrc/mission.c implements S-072 card 3 of 3 (om_mission_inject_candidate, om_mission_select, om_mission_get_candidate_score, om_mission_fallback_archetype, om_mission_fallback_region)"
acceptance:
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E10_S072_orders_come_from_where_the_world_hurts.py::test_R_072_05_score_0_5_urgency_0"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E10_S072_orders_come_from_where_the_world_hurts.py::test_R_072_06_urgency_0_8_it_beats"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E10_S072_orders_come_from_where_the_world_hurts.py::test_R_072_07_q_072_01"
allowed_files: "csrc/mission.c"
snippet_file: csrc/mission.c
snippet_symbol: "om_mission_inject_candidate,om_mission_select,om_mission_get_candidate_score,om_mission_fallback_archetype,om_mission_fallback_region"
header_file: csrc/ouroboros_sim.h
extra_context_files: csrc/om_internal.h
rules_file: projects/ouroboros/rules/E-10.md
test_file: tests/csim/test_E10_S072_orders_come_from_where_the_world_hurts.py
expected_lines: 60
max_wall_minutes: 45
---

## Brief for DeepSeek

Quoted verbatim from docs/bible/epics/E-10-missions.md (### S-072 — Orders come from where the world hurts):

- R-072-05  Given scored candidates, When one is selected, Then score = 0.5 · urgency + 0.3 · relevance + 0.2 · preference, the top 5 by score form the draw pool, and one weighted draw proportional to score picks the mission.
- R-072-06  Given a region with stability 15 under attack by a neighbor at military 80, When scored, Then urgency ≥ 0.8 and it beats any quiet region regardless of relevance and preference.
- R-072-07  Given no candidate in the pool, When selection runs, Then [Q-072-01].

## Header slice

(run card_slice.py --write after the skeleton lands)
