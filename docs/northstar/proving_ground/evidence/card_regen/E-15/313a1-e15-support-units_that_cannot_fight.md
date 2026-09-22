---
project: /home/westopoli/Projects/ouroboros-manifold
goal: "csrc/tactical_support.c implements S-129 card 1 of 3 (om_unit_spawn_non_combat, om_unit_spawn_combat, om_unit_tick_decision_loop, om_unit_get_target, om_unit_deal_damage)"
acceptance:
allowed_files: "csrc/tactical_support.c"
snippet_file: csrc/tactical_support.c
snippet_symbol: "om_unit_spawn_non_combat,om_unit_spawn_combat,om_unit_tick_decision_loop,om_unit_get_target,om_unit_deal_damage"
header_file: csrc/ouroboros_sim.h
extra_context_files: csrc/om_internal.h
rules_file: projects/ouroboros/rules/E-15.md
test_file: tests/csim/test_E15_S129_units_that_cannot_fight.py
expected_lines: 60
max_wall_minutes: 45
---

## Brief for DeepSeek

Quoted verbatim from docs/bible/epics/E-15-reinforcement-supply-and-hazards.md (### S-129 — Units that cannot fight):


## Header slice

(run card_slice.py --write after the skeleton lands)
