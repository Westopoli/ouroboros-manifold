---
project: /home/westopoli/Projects/ouroboros-manifold
goal: "csrc/tactical_support.c implements S-126 card 3 of 4 (om_structure_get_unit_type, om_mission_compute_starting_force, om_mission_compute_reinforcement_capacity, om_structure_get_hud_data, om_structure_unit_cost)"
acceptance:
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E15_S126_most_of_my_force_is_out_there.py::test_R_126_03_production_switches_to_it_at"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E15_S126_most_of_my_force_is_out_there.py::test_R_126_04_starting_force_0_20_f"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E15_S126_most_of_my_force_is_out_there.py::test_R_126_05_player_sees_timer_bar_next"
allowed_files: "csrc/tactical_support.c"
snippet_file: csrc/tactical_support.c
snippet_symbol: "om_structure_get_unit_type,om_mission_compute_starting_force,om_mission_compute_reinforcement_capacity,om_structure_get_hud_data,om_structure_unit_cost"
header_file: csrc/ouroboros_sim.h
extra_context_files: csrc/om_internal.h
rules_file: projects/ouroboros/rules/E-15.md
test_file: tests/csim/test_E15_S126_most_of_my_force_is_out_there.py
expected_lines: 60
max_wall_minutes: 45
---

## Brief for DeepSeek

Quoted verbatim from docs/bible/epics/E-15-reinforcement-supply-and-hazards.md (### S-126 — Most of my force is out there):

- R-126-03  Given the player clicks a held structure, When they pick a type, Then production switches to it at once and the current timer continues.
- R-126-04  Given a mission's expected full force F (E-10 force sizing), When forces are allocated, Then the starting force is 0.20 · F, and the reinforcement structures on the map can together produce at least 0.80 · F over the mission's time limit when all are held from the start; a player who holds every structure the whole mission fields at least F, and one who holds none fields 0.20 · F.
- R-126-05  Given a structure, When its production is read on the HUD, Then the player sees the timer bar, next unit, and HP (E-16 R-104-06).

## Header slice

(run card_slice.py --write after the skeleton lands)
