---
project: /home/westopoli/Projects/ouroboros-manifold
goal: "csrc/mission.c implements S-073 card 1 of 3 (om_mission_load_launch_library, om_mission_archetype_count, om_mission_get_archetype_metadata, om_mission_set_archetype_profile, om_mission_allocate_force_profile)"
acceptance:
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E10_S073_ten_kinds_of_trouble.py::test_R_073_01_it_contains_exactly_these_archetypes"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E10_S073_ten_kinds_of_trouble.py::test_R_073_02_its_asset_profile_ratio_per"
allowed_files: "csrc/mission.c"
snippet_file: csrc/mission.c
snippet_symbol: "om_mission_load_launch_library,om_mission_archetype_count,om_mission_get_archetype_metadata,om_mission_set_archetype_profile,om_mission_allocate_force_profile"
header_file: csrc/ouroboros_sim.h
extra_context_files: csrc/om_internal.h
rules_file: projects/ouroboros/rules/E-10.md
test_file: tests/csim/test_E10_S073_ten_kinds_of_trouble.py
expected_lines: 60
max_wall_minutes: 45
---

## Brief for DeepSeek

Quoted verbatim from docs/bible/epics/E-10-missions.md (### S-073 — Ten kinds of trouble):

- R-073-01  Given the launch library, When loaded, Then it contains exactly these archetypes with these triggers, base canvas, objective types, and transfer outcomes, and a contract test checks the table:
- R-073-02  Given an archetype, When its forces are allocated, Then its asset profile (ratio per unit type) is read from the library, not hard-coded.

## Header slice

(run card_slice.py --write after the skeleton lands)
