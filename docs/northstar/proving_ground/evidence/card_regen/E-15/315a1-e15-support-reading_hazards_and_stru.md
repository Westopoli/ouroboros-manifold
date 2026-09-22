---
project: /home/westopoli/Projects/ouroboros-manifold
goal: "csrc/tactical_support.c implements S-131 card 1 of 2 (om_render_get_structure_silhouette_id, om_render_get_unit_silhouette_id, om_render_get_owner_color, om_render_is_volume_obscuring, om_hazard_launch_type_count)"
acceptance:
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E15_S131_reading_hazards_and_structures.py::test_R_131_01_structures_distinguishable_by_owner_color"
allowed_files: "csrc/tactical_support.c"
snippet_file: csrc/tactical_support.c
snippet_symbol: "om_render_get_structure_silhouette_id,om_render_get_unit_silhouette_id,om_render_get_owner_color,om_render_is_volume_obscuring,om_hazard_launch_type_count"
header_file: csrc/ouroboros_sim.h
extra_context_files: csrc/om_internal.h
rules_file: projects/ouroboros/rules/E-15.md
test_file: tests/csim/test_E15_S131_reading_hazards_and_structures.py
expected_lines: 60
max_wall_minutes: 45
---

## Brief for DeepSeek

Quoted verbatim from docs/bible/epics/E-15-reinforcement-supply-and-hazards.md (### S-131 — Reading hazards and structures):

- R-131-01  Given a T2 screenshot, When inspected, Then structures are distinguishable by owner color and from every unit silhouette; interference zones read as obscuring volumes; convoys read as non-combat.

## Header slice

(run card_slice.py --write after the skeleton lands)
