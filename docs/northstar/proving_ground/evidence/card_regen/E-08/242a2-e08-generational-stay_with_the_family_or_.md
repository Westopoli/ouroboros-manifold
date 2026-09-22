---
project: /home/westopoli/Projects/ouroboros-manifold
goal: "csrc/generational.c implements S-057 card 2 of 2 (om_rng_force_selector_draw, om_lineage_record_history_region, om_lineage_home_region, om_character_selector_force_rotate)"
acceptance:
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E08_S057_stay_with_the_family_or_move_on.py::test_R_057_05_rotation_vetoed_player_stays"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E08_S057_stay_with_the_family_or_move_on.py::test_R_057_07_it_first_region_in_lineage"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E08_S057_stay_with_the_family_or_move_on.py::test_R_057_08_chapter_counter_for_new_lineage"
allowed_files: "csrc/generational.c"
snippet_file: csrc/generational.c
snippet_symbol: "om_rng_force_selector_draw,om_lineage_record_history_region,om_lineage_home_region,om_character_selector_force_rotate"
header_file: csrc/ouroboros_sim.h
extra_context_files: csrc/om_internal.h
rules_file: projects/ouroboros/rules/E-08.md
test_file: tests/csim/test_E08_S057_stay_with_the_family_or_move_on.py
expected_lines: 48
max_wall_minutes: 45
---

## Brief for DeepSeek

Quoted verbatim from docs/bible/epics/E-08-generational-structure.md (### S-057 — Stay with the family or move on):

- R-057-05  Given the roll says rotate and the lineage home region's stability is below 20, When selection runs, Then the rotation is vetoed and the player stays.
- R-057-07  Given the home region, When it is looked up, Then it is the first region in the lineage's history.
- R-057-08  Given a rotation, When it is recorded, Then the chapter counter for the new lineage starts at 1 and the record carries the reason (`forced`, `normal`, `commander_death`) and the pool used.

## Header slice

(run card_slice.py --write after the skeleton lands)
