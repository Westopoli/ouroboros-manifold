---
project: /home/westopoli/Projects/ouroboros-manifold
goal: "csrc/fog.c implements S-092 card 1 of 4 (om_mission_set_phase, om_map_add_obstacle, om_map_add_hazard_zone, om_map_add_spine_node, om_map_add_structure)"
acceptance:
allowed_files: "csrc/fog.c"
snippet_file: csrc/fog.c
snippet_symbol: "om_mission_set_phase,om_map_add_obstacle,om_map_add_hazard_zone,om_map_add_spine_node,om_map_add_structure"
header_file: csrc/ouroboros_sim.h
extra_context_files: csrc/om_internal.h
rules_file: projects/ouroboros/rules/E-12.md
test_file: tests/csim/test_E12_S092_recon_then_fog.py
expected_lines: 60
max_wall_minutes: 45
---

## Brief for DeepSeek

Quoted verbatim from docs/bible/epics/E-12-fog-and-sensors.md (### S-092 — Recon, then fog):


## Header slice

(run card_slice.py --write after the skeleton lands)
