---
project: /home/westopoli/Projects/ouroboros-manifold
goal: "csrc/worldgen.c implements S-023 card 1 of 1 (om_tick_friction)"
acceptance:
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E03_S023_routes_carry_armies_trade_or_both.py::test_R_023_03_it_names_edge_type_drift"
allowed_files: "csrc/worldgen.c"
snippet_file: csrc/worldgen.c
snippet_symbol: "om_tick_friction"
header_file: csrc/ouroboros_sim.h
extra_context_files: csrc/om_internal.h
rules_file: projects/ouroboros/rules/E-03.md
test_file: tests/csim/test_E03_S023_routes_carry_armies_trade_or_both.py
expected_lines: 12
max_wall_minutes: 45
---

## Brief for DeepSeek

Quoted verbatim from docs/bible/epics/E-03-world-generation.md (### S-023 — Routes carry armies, trade, or both):

- R-023-03  Given every "nearby" or "adjacent" read in the sim (drift adjacency, border friction, faction targeting, event propagation, character selector), When it runs, Then it names an edge type; drift adjacency reads `trade`, border friction reads `border`, faction targeting reads all.

## Header slice

(run card_slice.py --write after the skeleton lands)
