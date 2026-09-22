---
project: /home/westopoli/Projects/ouroboros-manifold
goal: "csrc/enemy_macro.c implements S-123 card 2 of 2 (om_macro_reads_player_visibility_set, om_macro_mutates_unit_stats, om_macro_issues_illegal_command)"
acceptance:
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E14_S123_the_enemy_replays_like_i_do.py::test_R_123_03_it_never_reads_player_s"
allowed_files: "csrc/enemy_macro.c"
snippet_file: csrc/enemy_macro.c
snippet_symbol: "om_macro_reads_player_visibility_set,om_macro_mutates_unit_stats,om_macro_issues_illegal_command"
header_file: csrc/ouroboros_sim.h
extra_context_files: csrc/om_internal.h
rules_file: projects/ouroboros/rules/E-14.md
test_file: tests/csim/test_E14_S123_the_enemy_replays_like_i_do.py
expected_lines: 36
max_wall_minutes: 45
---

## Brief for DeepSeek

Quoted verbatim from docs/bible/epics/E-14-enemy-macro-behavior.md (### S-123 — The enemy replays like I do):

- R-123-03  Given the macro layer, When it acts, Then it never reads the player's visible set, never issues a command a player could not, and never changes a unit's stats.

## Header slice

(run card_slice.py --write after the skeleton lands)
