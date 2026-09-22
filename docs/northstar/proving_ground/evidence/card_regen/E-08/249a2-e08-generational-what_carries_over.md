---
project: /home/westopoli/Projects/ouroboros-manifold
goal: "csrc/generational.c implements S-064 card 2 of 3 (om_progression_has_player_level, om_progression_carried_commander_stats_count, om_progression_supports_era_unlocks, om_save_state_size, om_save_state_write)"
acceptance:
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E08_S064_what_carries_over.py::test_R_064_03_there_no_player_level_no"
allowed_files: "csrc/generational.c"
snippet_file: csrc/generational.c
snippet_symbol: "om_progression_has_player_level,om_progression_carried_commander_stats_count,om_progression_supports_era_unlocks,om_save_state_size,om_save_state_write"
header_file: csrc/ouroboros_sim.h
extra_context_files: csrc/om_internal.h
rules_file: projects/ouroboros/rules/E-08.md
test_file: tests/csim/test_E08_S064_what_carries_over.py
expected_lines: 60
max_wall_minutes: 45
---

## Brief for DeepSeek

Quoted verbatim from docs/bible/epics/E-08-generational-structure.md (### S-064 — What carries over):

- R-064-03  Given progression, When read, Then there is no player level and no stat carried between commanders; the only unlock type at launch is era unlocks (E-20).

## Header slice

(run card_slice.py --write after the skeleton lands)
