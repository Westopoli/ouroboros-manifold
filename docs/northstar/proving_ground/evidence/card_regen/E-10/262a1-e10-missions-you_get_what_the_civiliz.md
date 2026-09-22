---
project: /home/westopoli/Projects/ouroboros-manifold
goal: "csrc/mission.c implements S-074 card 1 of 2 (om_mission_compute_enemy_power, om_mission_compute_base_parity, om_mission_compute_difficulty_parity, om_mission_fill_player_force, om_mission_set_player_units)"
acceptance:
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E10_S074_you_get_what_the_civilization_can_spare.py::test_R_074_01_it_attacker_s_committed_budget"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E10_S074_you_get_what_the_civilization_can_spare.py::test_R_074_02_base_parity_piecewise_linear_through"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E10_S074_you_get_what_the_civilization_can_spare.py::test_R_074_03_it_max_base_0_95"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E10_S074_you_get_what_the_civilization_can_spare.py::test_R_074_04_its_budget_p_parity_filled"
allowed_files: "csrc/mission.c"
snippet_file: csrc/mission.c
snippet_symbol: "om_mission_compute_enemy_power,om_mission_compute_base_parity,om_mission_compute_difficulty_parity,om_mission_fill_player_force,om_mission_set_player_units"
header_file: csrc/ouroboros_sim.h
extra_context_files: csrc/om_internal.h
rules_file: projects/ouroboros/rules/E-10.md
test_file: tests/csim/test_E10_S074_you_get_what_the_civilization_can_spare.py
expected_lines: 60
max_wall_minutes: 45
---

## Brief for DeepSeek

Quoted verbatim from docs/bible/epics/E-10-missions.md (### S-074 — You get what the civilization can spare):

- R-074-01  Given an archetype driven by an attack, When enemy power is set, Then it is the attacker's committed budget × 300; given an insurgent archetype (suppression, counterinsurgency), Then it is a rolled insurgent military × 2000, where the roll is uniform in a range interpolated by population from [20, 50] at population ≤ 25 to [40, 70] at ≥ 70; otherwise it is the region's military × 2000.
- R-074-02  Given the mission region's capacity c in [0, 1], When parity is computed, Then base parity is piecewise linear through (0, 0.80), (0.3, 0.85), (0.5, 0.90), (0.7, 0.95), (1.0, 1.00).
- R-074-03  Given difficulty easy, When parity is computed, Then it is max(base, 0.95); hard: min(base, 0.85); medium: base; and never below 0.75.
- R-074-04  Given the enemy force total power P, When the player's force is filled, Then its budget is P · parity, filled per unit type in descending profile ratio, adding units while a unit's power ≤ 1.15 × remaining budget.

## Header slice

(run card_slice.py --write after the skeleton lands)
