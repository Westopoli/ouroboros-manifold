---
project: /home/westopoli/Projects/ouroboros-manifold
goal: "csrc/tactical_mapgen.c implements S-116 card 1 of 1 (om_map_archetype_canvas_category, om_map_get_canvas_base_dimension, om_map_compute_modified_canvas)"
acceptance:
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E17_S116_canvas.py::test_R_116_01_its_base_category_e_10"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E17_S116_canvas.py::test_R_116_02_its_direction_archetype_s_defensive"
allowed_files: "csrc/tactical_mapgen.c"
snippet_file: csrc/tactical_mapgen.c
snippet_symbol: "om_map_archetype_canvas_category,om_map_get_canvas_base_dimension,om_map_compute_modified_canvas"
header_file: csrc/ouroboros_sim.h
extra_context_files: csrc/om_internal.h
rules_file: projects/ouroboros/rules/E-17.md
test_file: tests/csim/test_E17_S116_canvas.py
expected_lines: 36
max_wall_minutes: 45
---

## Brief for DeepSeek

Quoted verbatim from docs/bible/epics/E-17-map-generation.md (### S-116 — Canvas):

- R-116-01  Given an archetype, When the canvas is chosen, Then its base category is the E-10 S-073 table, and its dimension is drawn from small [8,000, 12,000], medium [12,000, 20,000], large [20,000, 28,000] wu square [Q-118-01: bible says fixed 8/16/24k ± 30 percent].
- R-116-02  Given the region's fields, When the ±30 percent modifier applies, Then its direction is the archetype's (defensive stand grows with wealth, counterinsurgency grows with tension, suppression shrinks).

## Header slice

(run card_slice.py --write after the skeleton lands)
