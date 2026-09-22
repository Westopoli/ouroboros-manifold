---
project: /home/westopoli/Projects/ouroboros-manifold
goal: "csrc/chronicle.c implements S-066 card 1 of 1 (om_chronicle_score_base, om_chronicle_context_multiplier, om_chronicle_calculate_score)"
acceptance:
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E09_S066_what_counts_as_notable.py::test_R_066_01_base_t_min_d_50"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E09_S066_what_counts_as_notable.py::test_R_066_02_context_multiplier_gains_0_5"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E09_S066_what_counts_as_notable.py::test_R_066_03_score_5_0_04_1"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E09_S066_what_counts_as_notable.py::test_R_066_04_score_2_3_0_1"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E09_S066_what_counts_as_notable.py::test_R_066_05_score_never_below_its_tier"
allowed_files: "csrc/chronicle.c"
snippet_file: csrc/chronicle.c
snippet_symbol: "om_chronicle_score_base,om_chronicle_context_multiplier,om_chronicle_calculate_score"
header_file: csrc/ouroboros_sim.h
extra_context_files: csrc/om_internal.h
rules_file: projects/ouroboros/rules/E-09.md
test_file: tests/csim/test_E09_S066_what_counts_as_notable.py
expected_lines: 36
max_wall_minutes: 45
---

## Brief for DeepSeek

Quoted verbatim from docs/bible/epics/E-09-chronicle.md (### S-066 — What counts as notable):

- R-066-01  Given an event whose template has significance tier T and whose field deltas sum in absolute value to D, When scored, Then base = T + min(D/50, 3.0).
- R-066-02  Given the event is in the last mission's region, When scored, Then the context multiplier gains +0.5; given it has an attached character, +0.3; given it has chain length L > 1, +0.1 · min(L, 5); given a lineage member lives in its region, +0.8; the multiplier starts at 1.0 and the score is base · multiplier.
- R-066-03  Given a tier-5 event with deltas summing to 2 in a quiet region, When scored, Then score = (5 + 0.04) · 1.0 = 5.04.
- R-066-04  Given a tier-2 event with deltas summing to 200, chain length 6, in the mission region with a character attached, When scored, Then score = (2 + 3.0) · (1 + 0.5 + 0.3 + 0.5) = 11.5.
- R-066-05  Given any event, When scored, Then the score is never below its tier.

## Header slice

(run card_slice.py --write after the skeleton lands)
