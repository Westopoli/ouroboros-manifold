---
project: /home/westopoli/Projects/ouroboros-manifold
goal: "csrc/tactical_support.c implements S-126 card 2 of 4 (om_structure_tick_production, om_structure_pop_spawned_unit, om_structure_get_timer, om_structure_get_last_spawn_distance, om_structure_switch_unit_type)"
acceptance:
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E15_S126_most_of_my_force_is_out_there.py::test_R_126_02_one_unit_that_type_spawns"
allowed_files: "csrc/tactical_support.c"
snippet_file: csrc/tactical_support.c
snippet_symbol: "om_structure_tick_production,om_structure_pop_spawned_unit,om_structure_get_timer,om_structure_get_last_spawn_distance,om_structure_switch_unit_type"
header_file: csrc/ouroboros_sim.h
extra_context_files: csrc/om_internal.h
rules_file: projects/ouroboros/rules/E-15.md
test_file: tests/csim/test_E15_S126_most_of_my_force_is_out_there.py
expected_lines: 60
max_wall_minutes: 45
---

## Brief for DeepSeek

Quoted verbatim from docs/bible/epics/E-15-reinforcement-supply-and-hazards.md (### S-126 — Most of my force is out there):

- R-126-02  Given a held structure with a chosen unit type, When its production timer reaches 30 s × (that type's power / 100), Then one unit of that type spawns within half the capture radius of the structure on the structure's layer (position from two world-stream draws, angle then distance; never from any other generator) and the timer subtracts the interval.

## Header slice

(run card_slice.py --write after the skeleton lands)
