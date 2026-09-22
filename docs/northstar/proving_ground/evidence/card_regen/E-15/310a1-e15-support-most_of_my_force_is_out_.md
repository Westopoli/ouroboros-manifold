---
project: /home/westopoli/Projects/ouroboros-manifold
goal: "csrc/tactical_support.c implements S-126 card 1 of 4 (om_structure_compute_count, om_structure_assign_owners, om_structure_production_interval_ticks, om_structure_init, om_structure_set_timer)"
acceptance:
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E15_S126_most_of_my_force_is_out_there.py::test_R_126_01_count_clamp_floor_region_military"
allowed_files: "csrc/tactical_support.c"
snippet_file: csrc/tactical_support.c
snippet_symbol: "om_structure_compute_count,om_structure_assign_owners,om_structure_production_interval_ticks,om_structure_init,om_structure_set_timer"
header_file: csrc/ouroboros_sim.h
extra_context_files: csrc/om_internal.h
rules_file: projects/ouroboros/rules/E-15.md
test_file: tests/csim/test_E15_S126_most_of_my_force_is_out_there.py
expected_lines: 60
max_wall_minutes: 45
---

## Brief for DeepSeek

Quoted verbatim from docs/bible/epics/E-15-reinforcement-supply-and-hazards.md (### S-126 — Most of my force is out there):

- R-126-01  Given a mission, When structures are placed, Then count = clamp(floor(region military × 0.06), small [2, 4], medium [3, 6], large [4, 8]) and the archetype's split assigns player, enemy, and neutral owners (defensive stand 50/25/25, siege 33/33/34, reconquest and assault 25/50/25, suppression and counterinsurgency 40/30/30, multi-front 40/35/25, interception and containment 33/34/33, evacuation 50/25/25), player at least 1.

## Header slice

(run card_slice.py --write after the skeleton lands)
