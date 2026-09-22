---
project: /home/westopoli/Projects/ouroboros-manifold
goal: "csrc/tactical_move.c implements S-097 card 2 of 3 (om_navmesh_get_cache_hits, om_unit_get_facing, om_collision_pass, om_unit_compute_terrain_speed, om_command_direct_move)"
acceptance:
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E13_S097_around_not_through.py::test_R_097_02_route_computed_once_cached"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E13_S097_around_not_through.py::test_R_097_03_it_probes_40_wu_ahead"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E13_S097_around_not_through.py::test_R_097_04_it_keeps_that_heading_for"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E13_S097_around_not_through.py::test_R_097_05_they_pushed_apart_along_line"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E13_S097_around_not_through.py::test_R_097_06_its_speed_multiplied_by_1"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E13_S097_around_not_through.py::test_R_097_06_it_moves_0_other_takes"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E13_S097_around_not_through.py::test_R_097_07_lower_unit_id_moves_in"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E13_S097_around_not_through.py::test_R_097_08_they_collide_like_allies_nobody"
allowed_files: "csrc/tactical_move.c"
snippet_file: csrc/tactical_move.c
snippet_symbol: "om_navmesh_get_cache_hits,om_unit_get_facing,om_collision_pass,om_unit_compute_terrain_speed,om_command_direct_move"
header_file: csrc/ouroboros_sim.h
extra_context_files: csrc/om_internal.h
rules_file: projects/ouroboros/rules/E-13.md
test_file: tests/csim/test_E13_S097_around_not_through.py
expected_lines: 60
max_wall_minutes: 45
---

## Brief for DeepSeek

Quoted verbatim from docs/bible/epics/E-13-movement-and-command.md (### S-097 — Around, not through):

- R-097-02  Given a destination shared by several units, When routes are computed, Then the route is computed once and cached.
- R-097-03  Given a moving unit, When it steps, Then it probes 40 wu ahead; if an ally blocks the probe it sweeps alternate angles left and right in a fixed order and takes the first clear one; if none, it waits.
- R-097-04  Given a unit that took a deflected angle, When it moves, Then it keeps that heading for at least 60 wu before re-evaluating.
- R-097-05  Given two units on the same layer within 30 wu (2 × radius 15), When the collision pass runs, Then they are pushed apart along the line between them until 30 wu apart, over up to 3 iterations per tick.
- R-097-06  Given one unit of the pair is stationary (no move target, or halted by engagement), When pushed, Then it moves 0 and the other takes the full displacement.
- R-097-07  Given two units at exactly the same position, When pushed, Then the lower unit id moves in the canonical direction (+x).
- R-097-08  Given enemy units, When colliding, Then they collide like allies; nobody passes through anybody.

## Header slice

(run card_slice.py --write after the skeleton lands)
