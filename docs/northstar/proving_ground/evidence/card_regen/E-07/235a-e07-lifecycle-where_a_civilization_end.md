---
project: /home/westopoli/Projects/ouroboros-manifold
goal: "csrc/lifecycle.c implements S-054 card 1 of 1 (om_world_is_terminal)"
acceptance:
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E07_S054_where_a_civilization_ends_up.py::test_R_054_01_deferred_with_feature_no_rule"
allowed_files: "csrc/lifecycle.c"
snippet_file: csrc/lifecycle.c
snippet_symbol: "om_world_is_terminal"
header_file: csrc/ouroboros_sim.h
extra_context_files: csrc/om_internal.h
rules_file: projects/ouroboros/rules/E-07.md
test_file: tests/csim/test_E07_S054_where_a_civilization_ends_up.py
expected_lines: 12
max_wall_minutes: 45
---

## Brief for DeepSeek

Quoted verbatim from docs/bible/epics/E-07-civilizational-lifecycle.md (### S-054 — Where a civilization ends up):

- R-054-01  Deferred with the feature. No rule until Q-054-01 is answered.

## Header slice

(run card_slice.py --write after the skeleton lands)
