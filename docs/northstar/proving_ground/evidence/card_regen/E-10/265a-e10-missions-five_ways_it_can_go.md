---
project: /home/westopoli/Projects/ouroboros-manifold
goal: "csrc/mission.c implements S-077 card 1 of 1 (om_mission_compute_final_score, om_mission_compute_retention, om_mission_classify_band, om_mission_eval_commander_fate, om_mission_get_band)"
acceptance:
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E10_S077_five_ways_it_can_go.py::test_R_077_01_final_0_75_o_0"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E10_S077_five_ways_it_can_go.py::test_R_077_02_final_t1_total_failure_t2"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E10_S077_five_ways_it_can_go.py::test_R_077_03_commander_fate_killed_else_survived"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E10_S077_five_ways_it_can_go.py::test_R_077_04_band_revealed_only_at_mission"
allowed_files: "csrc/mission.c"
snippet_file: csrc/mission.c
snippet_symbol: "om_mission_compute_final_score,om_mission_compute_retention,om_mission_classify_band,om_mission_eval_commander_fate,om_mission_get_band"
header_file: csrc/ouroboros_sim.h
extra_context_files: csrc/om_internal.h
rules_file: projects/ouroboros/rules/E-10.md
test_file: tests/csim/test_E10_S077_five_ways_it_can_go.py
expected_lines: 60
max_wall_minutes: 45
---

## Brief for DeepSeek

Quoted verbatim from docs/bible/epics/E-10-missions.md (### S-077 — Five ways it can go):

- R-077-01  Given objective score o (weighted completion, failed objectives count 0) and retention r (surviving unit power/deployed power, capped at 1, with damaged units counted by HP fraction), When the final score is computed, Then final = 0.75 · o + 0.25 · r.
- R-077-02  Given the archetype's thresholds [t1, t2, t3, t4], When classified, Then final < t1 is total_failure, < t2 partial_failure, < t3 partial_success, < t4 strong_success, else total_success; thresholds: defensive_stand, siege_breaking, suppression, interception, containment, counterinsurgency [0.20, 0.40, 0.60, 0.80]; reconquest and assault [0.25, 0.45, 0.65, 0.82]; multi_front_defense [0.15, 0.35, 0.55, 0.75]; evacuation [0.30, 0.50, 0.65, 0.80].
- R-077-03  Given the mission ends, When the commander's unit is dead, Then commander fate is killed, else survived [Q-077-01: the hub also names wounded].
- R-077-04  Given the result, When shown, Then the band is revealed only at mission end, never during play.

## Header slice

(run card_slice.py --write after the skeleton lands)
