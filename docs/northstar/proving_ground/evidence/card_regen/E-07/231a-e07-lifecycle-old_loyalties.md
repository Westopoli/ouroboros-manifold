---
project: /home/westopoli/Projects/ouroboros-manifold
goal: "csrc/lifecycle.c implements S-050 card 1 of 1 (om_region_set_previous_owner, om_region_previous_owner, om_tick_reversions)"
acceptance:
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E07_S050_old_loyalties.py::test_R_050_01_with_probability_0_5_one"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E07_S050_old_loyalties.py::test_R_050_02_it_never_reverts"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E07_S050_old_loyalties.py::test_R_050_03_it_never_reverts"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E07_S050_old_loyalties.py::test_R_050_04_region_s_owner_b_held"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E07_S050_old_loyalties.py::test_R_050_05_it_records_original_restored_factions"
allowed_files: "csrc/lifecycle.c"
snippet_file: csrc/lifecycle.c
snippet_symbol: "om_region_set_previous_owner,om_region_previous_owner,om_tick_reversions"
header_file: csrc/ouroboros_sim.h
extra_context_files: csrc/om_internal.h
rules_file: projects/ouroboros/rules/E-07.md
test_file: tests/csim/test_E07_S050_old_loyalties.py
expected_lines: 36
max_wall_minutes: 45
---

## Brief for DeepSeek

Quoted verbatim from docs/bible/epics/E-07-civilizational-lifecycle.md (### S-050 — Old loyalties):

- R-050-01  Given a region conquered from B 15 ticks ago and B still exists, When a revolt succeeds there, Then with probability 0.5 (one draw) the region reverts to B instead of forming a breakaway.
- R-050-02  Given the conquest was 21 or more ticks ago, When a revolt succeeds, Then it never reverts.
- R-050-03  Given B no longer exists, When a revolt succeeds, Then it never reverts.
- R-050-04  Given a reversion, When applied, Then the region's owner is B, held-since is the current tick, previous owner is cleared, and the same split and floors as R-049-03 apply.
- R-050-05  Given a reversion, When the log is read, Then it records the original and restored factions and the stolen amounts.

## Header slice

(run card_slice.py --write after the skeleton lands)
