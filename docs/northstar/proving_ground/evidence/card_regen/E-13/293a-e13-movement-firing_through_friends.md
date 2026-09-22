---
project: /home/westopoli/Projects/ouroboros-manifold
goal: "csrc/tactical_move.c implements S-098 card 1 of 1 (om_combat_can_shoot, om_map_add_cover)"
acceptance:
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E13_S098_firing_through_friends.py::test_R_098_01_shot_lands_friendly_units_never"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E13_S098_firing_through_friends.py::test_R_098_02_shot_blocked_exactly_as_vision"
allowed_files: "csrc/tactical_move.c"
snippet_file: csrc/tactical_move.c
snippet_symbol: "om_combat_can_shoot,om_map_add_cover"
header_file: csrc/ouroboros_sim.h
extra_context_files: csrc/om_internal.h
rules_file: projects/ouroboros/rules/E-13.md
test_file: tests/csim/test_E13_S098_firing_through_friends.py
expected_lines: 24
max_wall_minutes: 45
---

## Brief for DeepSeek

Quoted verbatim from docs/bible/epics/E-13-movement-and-command.md (### S-098 — Firing through friends):

- R-098-01  Given a ranged unit with an ally between it and its target, When it fires, Then the shot lands; friendly units never block fire.
- R-098-02  Given terrain or cover between them, When it fires, Then the shot is blocked exactly as vision is (E-12, E-01 S-007).

## Header slice

(run card_slice.py --write after the skeleton lands)
