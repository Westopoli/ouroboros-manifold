---
project: /home/westopoli/Projects/ouroboros-manifold
goal: "csrc/tactical_support.c implements S-126 card 4 of 4 (om_mission_set_player_held_structures_count, om_mission_get_reinforcement_trickle)"
acceptance:
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E15_S126_most_of_my_force_is_out_there.py::test_R_126_06_units_have_no_cost_player"
allowed_files: "csrc/tactical_support.c"
snippet_file: csrc/tactical_support.c
snippet_symbol: "om_mission_set_player_held_structures_count,om_mission_get_reinforcement_trickle"
header_file: csrc/ouroboros_sim.h
extra_context_files: csrc/om_internal.h
rules_file: projects/ouroboros/rules/E-15.md
test_file: tests/csim/test_E15_S126_most_of_my_force_is_out_there.py
expected_lines: 24
max_wall_minutes: 45
---

## Brief for DeepSeek

Quoted verbatim from docs/bible/epics/E-15-reinforcement-supply-and-hazards.md (### S-126 — Most of my force is out there):

- R-126-06  Given any mission, When production is read, Then units have no cost, and a player holding zero structures receives no trickle; the only reinforcement is R-126-02's structure production.

## Header slice

(run card_slice.py --write after the skeleton lands)
