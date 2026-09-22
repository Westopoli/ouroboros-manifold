---
project: /home/westopoli/Projects/ouroboros-manifold
goal: "csrc/tactical_mapgen.c implements S-118 card 2 of 2 (om_map_sample_obstacle_density, om_unit_spawn_combat, om_unit_order_hold_node, om_tactical_tick, om_unit_get_position)"
acceptance:
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E17_S118_the_battlefield_moves.py::test_R_118_02_its_position_moves_every_sampled"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E17_S118_the_battlefield_moves.py::test_R_118_03_no_unit_teleports_units_path"
allowed_files: "csrc/tactical_mapgen.c"
snippet_file: csrc/tactical_mapgen.c
snippet_symbol: "om_map_sample_obstacle_density,om_unit_spawn_combat,om_unit_order_hold_node,om_tactical_tick,om_unit_get_position"
header_file: csrc/ouroboros_sim.h
extra_context_files: csrc/om_internal.h
rules_file: projects/ouroboros/rules/E-17.md
test_file: tests/csim/test_E17_S118_the_battlefield_moves.py
expected_lines: 60
max_wall_minutes: 45
---

## Brief for DeepSeek

Quoted verbatim from docs/bible/epics/E-17-map-generation.md (### S-118 — The battlefield moves):

- R-118-02  Given a gradient source with motion, When ticks pass, Then its position moves and every sampled field updates.
- R-118-03  Given a moving node, When it moves, Then no unit teleports; units path to the new position under their standing orders.

## Header slice

(run card_slice.py --write after the skeleton lands)
