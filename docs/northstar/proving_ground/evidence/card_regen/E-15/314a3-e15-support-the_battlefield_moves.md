---
project: /home/westopoli/Projects/ouroboros-manifold
goal: "csrc/tactical_support.c implements S-130 card 3 of 3 (om_unit_order_move, om_unit_get_order_destination)"
acceptance:
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E15_S130_the_battlefield_moves.py::test_R_130_05_convoy_keeps_its_move_order"
allowed_files: "csrc/tactical_support.c"
snippet_file: csrc/tactical_support.c
snippet_symbol: "om_unit_order_move,om_unit_get_order_destination"
header_file: csrc/ouroboros_sim.h
extra_context_files: csrc/om_internal.h
rules_file: projects/ouroboros/rules/E-15.md
test_file: tests/csim/test_E15_S130_the_battlefield_moves.py
expected_lines: 24
max_wall_minutes: 45
---

## Brief for DeepSeek

Quoted verbatim from docs/bible/epics/E-15-reinforcement-supply-and-hazards.md (### S-130 — The battlefield moves):

- R-130-05  Given a battle in transit (convoy moving), When engaged, Then the convoy keeps its move order and the fight happens around it.

## Header slice

(run card_slice.py --write after the skeleton lands)
