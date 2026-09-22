---
project: /home/westopoli/Projects/ouroboros-manifold
goal: "csrc/enemy_macro.c implements S-124 card 1 of 2 (om_mission_get_external_reinforcement_prob, om_mission_schedule_external_reinforcement, om_mission_get_reinforcement_foreshadow_text, om_mission_set_external_reinforcement, om_tactical_tick_to)"
acceptance:
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E14_S124_rare_surprises.py::test_R_124_01_wave_scheduled_with_probability_p"
allowed_files: "csrc/enemy_macro.c"
snippet_file: csrc/enemy_macro.c
snippet_symbol: "om_mission_get_external_reinforcement_prob,om_mission_schedule_external_reinforcement,om_mission_get_reinforcement_foreshadow_text,om_mission_set_external_reinforcement,om_tactical_tick_to"
header_file: csrc/ouroboros_sim.h
extra_context_files: csrc/om_internal.h
rules_file: projects/ouroboros/rules/E-14.md
test_file: tests/csim/test_E14_S124_rare_surprises.py
expected_lines: 60
max_wall_minutes: 45
---

## Brief for DeepSeek

Quoted verbatim from docs/bible/epics/E-14-enemy-macro-behavior.md (### S-124 — Rare surprises):

- R-124-01  Given mission generation, When the external-reinforcement roll is made, Then the wave is scheduled with probability p [Q-124-01: 1 in 10 to 20 in the bible; nothing in code], its direction is named in the briefing, its arrival tick is fixed at generation and not shown.

## Header slice

(run card_slice.py --write after the skeleton lands)
