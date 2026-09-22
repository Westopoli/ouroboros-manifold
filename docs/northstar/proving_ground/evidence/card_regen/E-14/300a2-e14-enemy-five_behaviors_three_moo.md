---
project: /home/westopoli/Projects/ouroboros-manifold
goal: "csrc/enemy_macro.c implements S-120 card 2 of 3 (om_macro_get_behavior, om_macro_get_modifier, om_macro_enemy_leaves_trigger, om_macro_get_speed_multiplier, om_macro_get_phased_subgroups)"
acceptance:
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E14_S120_five_behaviors_three_moods.py::test_R_120_02_force_attack_moves_toward_its"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E14_S120_five_behaviors_three_moods.py::test_R_120_03_force_s_move_speed_0"
allowed_files: "csrc/enemy_macro.c"
snippet_file: csrc/enemy_macro.c
snippet_symbol: "om_macro_get_behavior,om_macro_get_modifier,om_macro_enemy_leaves_trigger,om_macro_get_speed_multiplier,om_macro_get_phased_subgroups"
header_file: csrc/ouroboros_sim.h
extra_context_files: csrc/om_internal.h
rules_file: projects/ouroboros/rules/E-14.md
test_file: tests/csim/test_E14_S120_five_behaviors_three_moods.py
expected_lines: 60
max_wall_minutes: 45
---

## Brief for DeepSeek

Quoted verbatim from docs/bible/epics/E-14-enemy-macro-behavior.md (### S-120 — Five behaviors, three moods):

- R-120-02  Given advance, When executed, Then the force attack-moves toward its target (a position, a spine node, or a unit group); given defend, Then it holds position and units auto-engage without pursuit; given patrol, Then it plain-moves through its waypoints in a cycle and auto-engages on contact; given ambush, Then it holds hidden until an enemy enters its trigger radius, then becomes advance_aggressive toward the trigger and never resets; given retreat, Then it plain-moves to its fallback point.
- R-120-03  Given cautious, When executed, Then the force's move speed is × 0.6, spacing wider, and it transitions to retreat or defend when force HP lost since state entry exceeds the contact threshold; given aggressive, Then speed × 1.2, spacing tighter, no break-off; given phased, Then the force is split into 2 or 3 sub-groups that advance one at a time, each starting when the previous engages or reaches its waypoint.

## Header slice

(run card_slice.py --write after the skeleton lands)
