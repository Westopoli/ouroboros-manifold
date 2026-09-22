---
project: /home/westopoli/Projects/ouroboros-manifold
goal: "csrc/fog.c implements S-093 card 1 of 2 (om_visibility_set_player_fog, om_command_attack_move, om_world_get_state_checksum, om_unit_acquire_target, om_unit_get_target)"
acceptance:
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E12_S093_fog_is_for_the_player_not_the_engine.py::test_R_093_01_traces_identical"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E12_S093_fog_is_for_the_player_not_the_engine.py::test_R_093_02_it_uses_its_own_visible"
allowed_files: "csrc/fog.c"
snippet_file: csrc/fog.c
snippet_symbol: "om_visibility_set_player_fog,om_command_attack_move,om_world_get_state_checksum,om_unit_acquire_target,om_unit_get_target"
header_file: csrc/ouroboros_sim.h
extra_context_files: csrc/om_internal.h
rules_file: projects/ouroboros/rules/E-12.md
test_file: tests/csim/test_E12_S093_fog_is_for_the_player_not_the_engine.py
expected_lines: 60
max_wall_minutes: 45
---

## Brief for DeepSeek

Quoted verbatim from docs/bible/epics/E-12-fog-and-sensors.md (### S-093 — Fog is for the player, not the engine):

- R-093-01  Given two identical battles differing only in the player's visibility, When resolved, Then the traces are identical.
- R-093-02  Given an enemy unit, When it acquires targets, Then it uses its own visible set with the same rules as the player's units.

## Header slice

(run card_slice.py --write after the skeleton lands)
