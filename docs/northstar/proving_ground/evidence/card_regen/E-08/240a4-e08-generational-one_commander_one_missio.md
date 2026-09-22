---
project: /home/westopoli/Projects/ouroboros-manifold
goal: "csrc/generational.c implements S-055 card 4 of 4 (om_campaign_start, om_campaign_opening_jump_length, om_chronicle_entry_count, om_chronicle_consequence_entry_count, om_chronicle_lineage_entry_count)"
acceptance:
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E08_S055_one_commander_one_mission_then_the_world_moves.py::test_R_055_05_opening_time_jump_runs_before"
allowed_files: "csrc/generational.c"
snippet_file: csrc/generational.c
snippet_symbol: "om_campaign_start,om_campaign_opening_jump_length,om_chronicle_entry_count,om_chronicle_consequence_entry_count,om_chronicle_lineage_entry_count"
header_file: csrc/ouroboros_sim.h
extra_context_files: csrc/om_internal.h
rules_file: projects/ouroboros/rules/E-08.md
test_file: tests/csim/test_E08_S055_one_commander_one_mission_then_the_world_moves.py
expected_lines: 60
max_wall_minutes: 45
---

## Brief for DeepSeek

Quoted verbatim from docs/bible/epics/E-08-generational-structure.md (### S-055 — One commander, one mission, then the world moves):

- R-055-05  Given the campaign's first chapter, When the world is generated, Then an opening time jump runs before the first briefing and its chronicle shows 3 to 5 world entries only.

## Header slice

(run card_slice.py --write after the skeleton lands)
