---
project: /home/westopoli/Projects/ouroboros-manifold
goal: "csrc/tactical_move.c implements S-101 card 1 of 1 (om_renderer_interpolate_position, om_renderer_interpolate_facing)"
acceptance:
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E13_S101_movement_that_reads.py::test_R_101_02_position_facing_linearly_interpolated_from"
allowed_files: "csrc/tactical_move.c"
snippet_file: csrc/tactical_move.c
snippet_symbol: "om_renderer_interpolate_position,om_renderer_interpolate_facing"
header_file: csrc/ouroboros_sim.h
extra_context_files: csrc/om_internal.h
rules_file: projects/ouroboros/rules/E-13.md
test_file: tests/csim/test_E13_S101_movement_that_reads.py
expected_lines: 24
max_wall_minutes: 45
---

## Brief for DeepSeek

Quoted verbatim from docs/bible/epics/E-13-movement-and-command.md (### S-101 — Movement that reads):

- R-101-02  Given the renderer, When it draws between ticks, Then position and facing are linearly interpolated from the last two ticks.

## Header slice

(run card_slice.py --write after the skeleton lands)
