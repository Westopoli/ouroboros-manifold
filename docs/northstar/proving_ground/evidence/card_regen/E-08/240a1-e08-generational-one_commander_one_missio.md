---
project: /home/westopoli/Projects/ouroboros-manifold
goal: "csrc/generational.c implements S-055 card 1 of 4 (om_chapter_start, om_chapter_current_phase, om_chapter_advance_phase, om_chapter_recon_has_clock, om_chapter_mission_realtime)"
acceptance:
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E08_S055_one_commander_one_mission_then_the_world_moves.py::test_R_055_01_order_mission_briefing_recon_free"
allowed_files: "csrc/generational.c"
snippet_file: csrc/generational.c
snippet_symbol: "om_chapter_start,om_chapter_current_phase,om_chapter_advance_phase,om_chapter_recon_has_clock,om_chapter_mission_realtime"
header_file: csrc/ouroboros_sim.h
extra_context_files: csrc/om_internal.h
rules_file: projects/ouroboros/rules/E-08.md
test_file: tests/csim/test_E08_S055_one_commander_one_mission_then_the_world_moves.py
expected_lines: 60
max_wall_minutes: 45
---

## Brief for DeepSeek

Quoted verbatim from docs/bible/epics/E-08-generational-structure.md (### S-055 — One commander, one mission, then the world moves):

- R-055-01  Given a new chapter, When it starts, Then the order is: mission briefing, recon (free camera, no mission clock), mission (real time, no pause), outcome resolution, time jump with chronicle, character selection, next briefing.

## Header slice

(run card_slice.py --write after the skeleton lands)
