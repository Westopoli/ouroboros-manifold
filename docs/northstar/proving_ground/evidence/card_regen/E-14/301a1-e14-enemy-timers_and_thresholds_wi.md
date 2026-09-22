---
project: /home/westopoli/Projects/ouroboros-manifold
goal: "csrc/enemy_macro.c implements S-121 card 1 of 2 (om_macro_get_threshold_noise, om_macro_get_timer_noise, om_macro_eval_timer_transition, om_macro_resolve_conflict, om_macro_resolve_conflict_types)"
acceptance:
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E14_S121_timers_and_thresholds_with_noise.py::test_R_121_01_condition_compared_against_its_noised"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E14_S121_timers_and_thresholds_with_noise.py::test_R_121_02_it_fires_regardless_tactical_state"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E14_S121_timers_and_thresholds_with_noise.py::test_R_121_03_threshold_wins_except_that_retreat"
allowed_files: "csrc/enemy_macro.c"
snippet_file: csrc/enemy_macro.c
snippet_symbol: "om_macro_get_threshold_noise,om_macro_get_timer_noise,om_macro_eval_timer_transition,om_macro_resolve_conflict,om_macro_resolve_conflict_types"
header_file: csrc/ouroboros_sim.h
extra_context_files: csrc/om_internal.h
rules_file: projects/ouroboros/rules/E-14.md
test_file: tests/csim/test_E14_S121_timers_and_thresholds_with_noise.py
expected_lines: 60
max_wall_minutes: 45
---

## Brief for DeepSeek

Quoted verbatim from docs/bible/epics/E-14-enemy-macro-behavior.md (### S-121 — Timers and thresholds, with noise):

- R-121-01  Given a transition with a threshold condition (force HP fraction, unit count, elapsed time, timer expired, bus flag, player force in zone, enemy in range), When evaluated, Then the condition is compared against its noised value: noise is one uniform draw in ±noise_pct (default ±0.15 for thresholds, ±0.20 for timers) made at mission start and held for the mission.
- R-121-02  Given a timer transition with duration D, When elapsed × (1 + noise) ≥ D, Then it fires regardless of tactical state.
- R-121-03  Given a threshold and a timer both firing on the same evaluation, When resolved, Then the threshold wins, except that a retreat transition always wins over an escalation.

## Header slice

(run card_slice.py --write after the skeleton lands)
