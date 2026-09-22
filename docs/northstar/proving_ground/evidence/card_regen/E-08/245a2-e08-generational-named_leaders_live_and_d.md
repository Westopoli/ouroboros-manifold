---
project: /home/westopoli/Projects/ouroboros-manifold
goal: "csrc/generational.c implements S-060 card 2 of 3 (om_character_create_with_rank, om_world_set_strategic_tick, om_process_natural_deaths, om_time_jump_run_tracked, om_time_jump_death_pass_count)"
acceptance:
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E08_S060_named_leaders_live_and_die.py::test_R_060_03_it_becomes_historical_with_death"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E08_S060_named_leaders_live_and_die.py::test_R_060_04_it_happens_once_at_end"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E08_S060_named_leaders_live_and_die.py::test_R_060_06_it_holds_exactly_id_name"
allowed_files: "csrc/generational.c"
snippet_file: csrc/generational.c
snippet_symbol: "om_character_create_with_rank,om_world_set_strategic_tick,om_process_natural_deaths,om_time_jump_run_tracked,om_time_jump_death_pass_count"
header_file: csrc/ouroboros_sim.h
extra_context_files: csrc/om_internal.h
rules_file: projects/ouroboros/rules/E-08.md
test_file: tests/csim/test_E08_S060_named_leaders_live_and_die.py
expected_lines: 60
max_wall_minutes: 45
---

## Brief for DeepSeek

Quoted verbatim from docs/bible/epics/E-08-generational-structure.md (### S-060 — Named leaders live and die):

- R-060-03  Given a character's age reaches its lifespan, When natural deaths are processed, Then it becomes historical with a death tick, and if its rank is supreme or regional commander a successor is created with a fresh name and lifespan in the same faction and region (regional only if the faction still owns the region).
- R-060-04  Given natural deaths, When processed, Then it happens once at the end of each time jump, not every tick [Q-060-01].
- R-060-06  Given any character record, When read, Then it holds exactly: id, name, faction, region, rank (supreme_commander, regional_commander, garrison_officer, lineage_member), birth tick, lifespan, status, death tick, lineage id, parent id, generation, rival tags, children.

## Header slice

(run card_slice.py --write after the skeleton lands)
