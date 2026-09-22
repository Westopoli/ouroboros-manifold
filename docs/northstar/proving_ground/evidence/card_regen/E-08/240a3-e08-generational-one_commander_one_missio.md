---
project: /home/westopoli/Projects/ouroboros-manifold
goal: "csrc/generational.c implements S-055 card 3 of 4 (om_time_jump_run, om_mission_generator_run, om_mission_generator_chosen_region, om_character_selector_run, om_character_selector_input_region)"
acceptance:
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E08_S055_one_commander_one_mission_then_the_world_moves.py::test_R_055_04_character_selector_runs_after_it"
allowed_files: "csrc/generational.c"
snippet_file: csrc/generational.c
snippet_symbol: "om_time_jump_run,om_mission_generator_run,om_mission_generator_chosen_region,om_character_selector_run,om_character_selector_input_region"
header_file: csrc/ouroboros_sim.h
extra_context_files: csrc/om_internal.h
rules_file: projects/ouroboros/rules/E-08.md
test_file: tests/csim/test_E08_S055_one_commander_one_mission_then_the_world_moves.py
expected_lines: 60
max_wall_minutes: 45
---

## Brief for DeepSeek

Quoted verbatim from docs/bible/epics/E-08-generational-structure.md (### S-055 — One commander, one mission, then the world moves):

- R-055-04  Given the time jump completes, When the mission generator runs, Then the character selector runs after it and reads the chosen mission region.

## Header slice

(run card_slice.py --write after the skeleton lands)
