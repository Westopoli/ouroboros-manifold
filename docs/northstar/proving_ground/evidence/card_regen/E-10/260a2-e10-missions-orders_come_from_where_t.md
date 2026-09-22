---
project: /home/westopoli/Projects/ouroboros-manifold
goal: "csrc/mission.c implements S-072 card 2 of 3 (om_mission_set_lineage_context, om_mission_compute_relevance, om_mission_compute_preference, om_mission_set_preference, om_mission_candidate_score)"
acceptance:
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E10_S072_orders_come_from_where_the_world_hurts.py::test_R_072_03_relevance_clamp_0_4_lineage"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E10_S072_orders_come_from_where_the_world_hurts.py::test_R_072_04_it_0_1_for_archetype"
allowed_files: "csrc/mission.c"
snippet_file: csrc/mission.c
snippet_symbol: "om_mission_set_lineage_context,om_mission_compute_relevance,om_mission_compute_preference,om_mission_set_preference,om_mission_candidate_score"
header_file: csrc/ouroboros_sim.h
extra_context_files: csrc/om_internal.h
rules_file: projects/ouroboros/rules/E-10.md
test_file: tests/csim/test_E10_S072_orders_come_from_where_the_world_hurts.py
expected_lines: 60
max_wall_minutes: 45
---

## Brief for DeepSeek

Quoted verbatim from docs/bible/epics/E-10-missions.md (### S-072 — Orders come from where the world hurts):

- R-072-03  Given a candidate, When relevance is computed, Then relevance = clamp(0.4 · lineage + 0.3 · proximity + 0.3 · fit, 0, 1), lineage = 1.0 if a lineage member lives in the region, 0.5 if the lineage ever operated there, else 0; proximity = 1 − hops from the lineage home/5 (capped at 5 hops); fit = min(1, times the lineage has run this archetype/3).
- R-072-04  Given a candidate, When preference is computed, Then it is 0.1 for an archetype the player marked rare, else the player's weight, default 0.5.

## Header slice

(run card_slice.py --write after the skeleton lands)
