---
project: /home/westopoli/Projects/ouroboros-manifold
goal: "csrc/mission.c implements S-073 card 2 of 3 (om_mission_get_compatible_layouts, om_mission_select_layout, om_mission_setup, om_mission_get_briefing_text, om_mission_get_enemy_power)"
acceptance:
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E10_S073_ten_kinds_of_trouble.py::test_R_073_03_its_compatibility_filters_select_layouts"
allowed_files: "csrc/mission.c"
snippet_file: csrc/mission.c
snippet_symbol: "om_mission_get_compatible_layouts,om_mission_select_layout,om_mission_setup,om_mission_get_briefing_text,om_mission_get_enemy_power"
header_file: csrc/ouroboros_sim.h
extra_context_files: csrc/om_internal.h
rules_file: projects/ouroboros/rules/E-10.md
test_file: tests/csim/test_E10_S073_ten_kinds_of_trouble.py
expected_lines: 60
max_wall_minutes: 45
---

## Brief for DeepSeek

Quoted verbatim from docs/bible/epics/E-10-missions.md (### S-073 — Ten kinds of trouble):

- R-073-03  Given an archetype, When its map is generated, Then its compatibility filters select layouts from the shared library (E-17).

## Header slice

(run card_slice.py --write after the skeleton lands)
