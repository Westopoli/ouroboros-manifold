---
project: /home/westopoli/Projects/ouroboros-manifold
goal: "csrc/generational.c implements S-055 card 2 of 4 (om_chapter_set_phase, om_world_strategic_tick, om_tactical_step, om_outcome_apply_consequences, om_time_jump_start_tick)"
acceptance:
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E08_S055_one_commander_one_mission_then_the_world_moves.py::test_R_055_02_no_strategic_tick_runs_strategic"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E08_S055_one_commander_one_mission_then_the_world_moves.py::test_R_055_03_those_field_changes_land_before"
allowed_files: "csrc/generational.c"
snippet_file: csrc/generational.c
snippet_symbol: "om_chapter_set_phase,om_world_strategic_tick,om_tactical_step,om_outcome_apply_consequences,om_time_jump_start_tick"
header_file: csrc/ouroboros_sim.h
extra_context_files: csrc/om_internal.h
rules_file: projects/ouroboros/rules/E-08.md
test_file: tests/csim/test_E08_S055_one_commander_one_mission_then_the_world_moves.py
expected_lines: 60
max_wall_minutes: 45
---

## Brief for DeepSeek

Quoted verbatim from docs/bible/epics/E-08-generational-structure.md (### S-055 — One commander, one mission, then the world moves):

- R-055-02  Given a mission is running, When any tactical tick passes, Then no strategic tick runs; the strategic sim is stopped for the mission's duration.
- R-055-03  Given the mission resolves, When the outcome resolver applies its consequence bundle (E-10), Then those field changes land before the first tick of the time jump.

## Header slice

(run card_slice.py --write after the skeleton lands)
