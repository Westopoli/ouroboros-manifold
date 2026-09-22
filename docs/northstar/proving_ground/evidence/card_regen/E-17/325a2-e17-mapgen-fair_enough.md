---
project: /home/westopoli/Projects/ouroboros-manifold
goal: "csrc/tactical_mapgen.c implements S-117 card 2 of 2 (om_map_layout_check_hazard_approaches, om_map_layout_check_vantage_reachability)"
acceptance:
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E17_S117_fair_enough.py::test_R_117_03_it_passes_hard_constraints_no"
allowed_files: "csrc/tactical_mapgen.c"
snippet_file: csrc/tactical_mapgen.c
snippet_symbol: "om_map_layout_check_hazard_approaches,om_map_layout_check_vantage_reachability"
header_file: csrc/ouroboros_sim.h
extra_context_files: csrc/om_internal.h
rules_file: projects/ouroboros/rules/E-17.md
test_file: tests/csim/test_E17_S117_fair_enough.py
expected_lines: 24
max_wall_minutes: 45
---

## Brief for DeepSeek

Quoted verbatim from docs/bible/epics/E-17-map-generation.md (### S-117 — Fair enough):

- R-117-03  Given a layout in the library, When authored, Then it passes the hard constraints: no side's every approach blocked by hazards while the other's is clear; every vantage reachable by both sides.

## Header slice

(run card_slice.py --write after the skeleton lands)
