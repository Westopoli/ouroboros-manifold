---
project: /home/westopoli/Projects/ouroboros-manifold
goal: "csrc/tactical_mapgen.c implements S-118 card 1 of 2 (om_map_setup_drifting_node, om_map_get_node_pos, om_tactical_tick_to, om_objective_get_center, om_gradient_add_moving_source)"
acceptance:
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E17_S118_the_battlefield_moves.py::test_R_118_01_its_position_follows_path_ping"
allowed_files: "csrc/tactical_mapgen.c"
snippet_file: csrc/tactical_mapgen.c
snippet_symbol: "om_map_setup_drifting_node,om_map_get_node_pos,om_tactical_tick_to,om_objective_get_center,om_gradient_add_moving_source"
header_file: csrc/ouroboros_sim.h
extra_context_files: csrc/om_internal.h
rules_file: projects/ouroboros/rules/E-17.md
test_file: tests/csim/test_E17_S118_the_battlefield_moves.py
expected_lines: 60
max_wall_minutes: 45
---

## Brief for DeepSeek

Quoted verbatim from docs/bible/epics/E-17-map-generation.md (### S-118 — The battlefield moves):

- R-118-01  Given a spine node of type objective or reinforcement_structure with a drift path, When ticks pass, Then its position follows the path (ping-pong or loop over waypoints with a period in ticks) and the objective zone moves with it.

## Header slice

(run card_slice.py --write after the skeleton lands)
