---
project: /home/westopoli/Projects/ouroboros-manifold
goal: "csrc/tactical_move.c implements S-096 card 2 of 4 (om_unit_set_hp, om_unit_set_pos, om_command_attack_target, om_unit_set_visible_to_faction, om_visibility_compute)"
acceptance:
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E13_S096_four_commands.py::test_R_096_02_unit_halts_fires_target_dies"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E13_S096_four_commands.py::test_R_096_03_unit_drops_target_resumes"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E13_S096_four_commands.py::test_R_096_04_unit_moves_toward_e_if"
allowed_files: "csrc/tactical_move.c"
snippet_file: csrc/tactical_move.c
snippet_symbol: "om_unit_set_hp,om_unit_set_pos,om_command_attack_target,om_unit_set_visible_to_faction,om_visibility_compute"
header_file: csrc/ouroboros_sim.h
extra_context_files: csrc/om_internal.h
rules_file: projects/ouroboros/rules/E-13.md
test_file: tests/csim/test_E13_S096_four_commands.py
expected_lines: 60
max_wall_minutes: 45
---

## Brief for DeepSeek

Quoted verbatim from docs/bible/epics/E-13-movement-and-command.md (### S-096 — Four commands):

- R-096-02  Given an attack-move, When an enemy enters attack range on the unit's layer, Then the unit halts and fires; when the target dies or leaves range it resumes toward the point.
- R-096-03  Given an attack-move engagement, When the target moves more than 200 wu from the unit's anchor (its position at acquisition), Then the unit drops the target and resumes.
- R-096-04  Given attack-target on enemy E, When issued, Then the unit moves toward E if out of range and attacks E in range until E dies or a new order arrives; if E becomes invisible the unit moves to E's last known position and idles there.

## Header slice

(run card_slice.py --write after the skeleton lands)
