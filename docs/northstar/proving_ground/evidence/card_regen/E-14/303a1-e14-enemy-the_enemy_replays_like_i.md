---
project: /home/westopoli/Projects/ouroboros-manifold
goal: "csrc/enemy_macro.c implements S-123 card 1 of 2 (om_mission_init_seed, om_tactical_tick, om_replay_command_count, om_replay_get_commands, om_replay_log_command)"
acceptance:
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E14_S123_the_enemy_replays_like_i_do.py::test_R_123_01_every_enemy_command_identical_on"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E14_S123_the_enemy_replays_like_i_do.py::test_R_123_02_they_appear_in_same_replay"
allowed_files: "csrc/enemy_macro.c"
snippet_file: csrc/enemy_macro.c
snippet_symbol: "om_mission_init_seed,om_tactical_tick,om_replay_command_count,om_replay_get_commands,om_replay_log_command"
header_file: csrc/ouroboros_sim.h
extra_context_files: csrc/om_internal.h
rules_file: projects/ouroboros/rules/E-14.md
test_file: tests/csim/test_E14_S123_the_enemy_replays_like_i_do.py
expected_lines: 60
max_wall_minutes: 45
---

## Brief for DeepSeek

Quoted verbatim from docs/bible/epics/E-14-enemy-macro-behavior.md (### S-123 — The enemy replays like I do):

- R-123-01  Given seed, script, map, and the command stream, When run twice, Then every enemy command is identical on identical ticks.
- R-123-02  Given the enemy, When its commands are logged, Then they appear in the same replay stream as player commands with a force id.

## Header slice

(run card_slice.py --write after the skeleton lands)
