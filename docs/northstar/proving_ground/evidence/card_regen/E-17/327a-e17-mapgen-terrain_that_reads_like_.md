---
project: /home/westopoli/Projects/ouroboros-manifold
goal: "csrc/tactical_mapgen.c implements S-119 card 1 of 1 (om_map_check_boundary_gradient_discontinuity, om_render_detect_repeated_tile_boundary, om_proc_arch_section_is_era_agnostic, om_proc_arch_resolve_section_piece)"
acceptance:
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E17_S119_terrain_that_reads_like_a_place.py::test_R_119_01_no_repeated_tile_boundary_visible"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E17_S119_terrain_that_reads_like_a_place.py::test_R_119_02_it_era_agnostic_at_section"
allowed_files: "csrc/tactical_mapgen.c"
snippet_file: csrc/tactical_mapgen.c
snippet_symbol: "om_map_check_boundary_gradient_discontinuity,om_render_detect_repeated_tile_boundary,om_proc_arch_section_is_era_agnostic,om_proc_arch_resolve_section_piece"
header_file: csrc/ouroboros_sim.h
extra_context_files: csrc/om_internal.h
rules_file: projects/ouroboros/rules/E-17.md
test_file: tests/csim/test_E17_S119_terrain_that_reads_like_a_place.py
expected_lines: 48
max_wall_minutes: 45
---

## Brief for DeepSeek

Quoted verbatim from docs/bible/epics/E-17-map-generation.md (### S-119 — Terrain that reads like a place):

- R-119-01  Given a T2 screenshot of any generated map, When inspected, Then no repeated tile boundary is visible and gradient regions blend without hard edges.
- R-119-02  Given the procedural architecture system Westley opened in Stage 1 (A-157), When designed, Then it is era-agnostic at the section level with an era-specific kit of pieces assembled by it [Q-119-01: scope and schedule].

## Header slice

(run card_slice.py --write after the skeleton lands)
