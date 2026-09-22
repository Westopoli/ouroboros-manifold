---
project: /home/westopoli/Projects/ouroboros-manifold
goal: "csrc/enemy_macro.c implements S-125 card 1 of 2 (om_mission_compute_parity, om_macro_get_eval_interval, om_unit_get_decision_loop_ptr, om_unit_get_base_hp, om_session_capture_enable)"
acceptance:
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E14_S125_how_hard_the_enemy_tries.py::test_R_125_01_only_force_parity_e_10"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E14_S125_how_hard_the_enemy_tries.py::test_R_125_02_their_decision_loop_stats_abilities"
allowed_files: "csrc/enemy_macro.c"
snippet_file: csrc/enemy_macro.c
snippet_symbol: "om_mission_compute_parity,om_macro_get_eval_interval,om_unit_get_decision_loop_ptr,om_unit_get_base_hp,om_session_capture_enable"
header_file: csrc/ouroboros_sim.h
extra_context_files: csrc/om_internal.h
rules_file: projects/ouroboros/rules/E-14.md
test_file: tests/csim/test_E14_S125_how_hard_the_enemy_tries.py
expected_lines: 60
max_wall_minutes: 45
---

## Brief for DeepSeek

Quoted verbatim from docs/bible/epics/E-14-enemy-macro-behavior.md (### S-125 — How hard the enemy tries):

- R-125-01  Given difficulty, When the enemy force is generated, Then only force parity (E-10 R-074-03) changes at launch [Q-125-01: A-156 interim knob; whether unit counts or script aggression also scale].
- R-125-02  Given any difficulty, When the enemy's units act, Then their decision loop, stats, and abilities are identical to the player's.

## Header slice

(run card_slice.py --write after the skeleton lands)
