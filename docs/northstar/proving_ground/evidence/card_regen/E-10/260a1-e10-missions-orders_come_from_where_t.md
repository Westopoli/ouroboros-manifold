---
project: /home/westopoli/Projects/ouroboros-manifold
goal: "csrc/mission.c implements S-072 card 1 of 3 (om_mission_build_candidate_pool, om_mission_candidates, om_mission_set_conflict_context, om_mission_set_revolt_events, om_mission_compute_urgency)"
acceptance:
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E10_S072_orders_come_from_where_the_world_hurts.py::test_R_072_01_each_region_archetype_pair_whose"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E10_S072_orders_come_from_where_the_world_hurts.py::test_R_072_02_urgency_clamp_0_4_deficit"
allowed_files: "csrc/mission.c"
snippet_file: csrc/mission.c
snippet_symbol: "om_mission_build_candidate_pool,om_mission_candidates,om_mission_set_conflict_context,om_mission_set_revolt_events,om_mission_compute_urgency"
header_file: csrc/ouroboros_sim.h
extra_context_files: csrc/om_internal.h
rules_file: projects/ouroboros/rules/E-10.md
test_file: tests/csim/test_E10_S072_orders_come_from_where_the_world_hurts.py
expected_lines: 60
max_wall_minutes: 45
---

## Brief for DeepSeek

Quoted verbatim from docs/bible/epics/E-10-missions.md (### S-072 — Orders come from where the world hurts):

- R-072-01  Given the player's regions and every region adjacent to them, When the candidate pool is built, Then each (region, archetype) pair whose trigger condition holds enters the pool; a region with no trigger produces nothing.
- R-072-02  Given a candidate, When urgency is computed, Then urgency = clamp(0.4 · deficit + 0.4 · conflict + 0.2 · chain, 0, 1), where deficit = mean of (100 − military, 100 − economy, 100 − stability)/100, conflict = clamp(min(1, max hostile neighbor military/70) + 0.5 · min(1, 0.5 · recent attacks + Σ attack budget/600) + 0.3 · min(1, 0.5 · adjacent regions lost), 0, 1), chain = min(1, 0.3 · recent revolt events in the region).

## Header slice

(run card_slice.py --write after the skeleton lands)
