---
project: /home/westopoli/Projects/ouroboros-manifold
goal: "csrc/mission.c implements S-076 card 1 of 2 (om_mission_compute_time_limit, om_archetype_base_time_ticks, om_mission_setup_tactical, om_mission_set_objective_completion, om_tactical_tick)"
acceptance:
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E10_S076_the_clock.py::test_R_076_01_limit_max_b_1_0"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E10_S076_the_clock.py::test_R_076_02_they_minutes_in_table_q"
allowed_files: "csrc/mission.c"
snippet_file: csrc/mission.c
snippet_symbol: "om_mission_compute_time_limit,om_archetype_base_time_ticks,om_mission_setup_tactical,om_mission_set_objective_completion,om_tactical_tick"
header_file: csrc/ouroboros_sim.h
extra_context_files: csrc/om_internal.h
rules_file: projects/ouroboros/rules/E-10.md
test_file: tests/csim/test_E10_S076_the_clock.py
expected_lines: 60
max_wall_minutes: 45
---

## Brief for DeepSeek

Quoted verbatim from docs/bible/epics/E-10-missions.md (### S-076 — The clock):

- R-076-01  Given an archetype base time B in tactical ticks and urgency u, When the limit is set, Then limit = max(B · (1 − 0.2 · u), 0.6 · B).
- R-076-02  Given base times, When read, Then they are the minutes in the table [Q-076-01: the bible's table (3 to 4.5 minutes) is overridden in config by 250 to 450 ticks, 12 to 22 seconds].

## Header slice

(run card_slice.py --write after the skeleton lands)
