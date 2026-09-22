---
project: /home/westopoli/Projects/ouroboros-manifold
goal: "csrc/enemy_macro.c implements S-124 card 2 of 2 (om_mission_check_external_reinforcements, om_mission_is_reinforcement_spawned, om_mission_get_reinforcement_spawn_pos, om_map_is_edge_coord)"
acceptance:
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E14_S124_rare_surprises.py::test_R_124_02_units_enter_at_map_edge"
allowed_files: "csrc/enemy_macro.c"
snippet_file: csrc/enemy_macro.c
snippet_symbol: "om_mission_check_external_reinforcements,om_mission_is_reinforcement_spawned,om_mission_get_reinforcement_spawn_pos,om_map_is_edge_coord"
header_file: csrc/ouroboros_sim.h
extra_context_files: csrc/om_internal.h
rules_file: projects/ouroboros/rules/E-14.md
test_file: tests/csim/test_E14_S124_rare_surprises.py
expected_lines: 48
max_wall_minutes: 45
---

## Brief for DeepSeek

Quoted verbatim from docs/bible/epics/E-14-enemy-macro-behavior.md (### S-124 — Rare surprises):

- R-124-02  Given the wave arrives, When it spawns, Then units enter at a map-edge spawn point, set a bus flag, and run their own script.

## Header slice

(run card_slice.py --write after the skeleton lands)
