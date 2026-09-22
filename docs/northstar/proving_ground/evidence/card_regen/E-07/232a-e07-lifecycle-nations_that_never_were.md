---
project: /home/westopoli/Projects/ouroboros-manifold
goal: "csrc/lifecycle.c implements S-051 card 1 of 1 (om_faction_set_created_tick, om_faction_is_active, om_tick_absorptions, om_faction_mark_conquered_this_tick, om_faction_remove)"
acceptance:
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E07_S051_nations_that_never_were.py::test_R_051_01_it_removed_from_registry_every"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E07_S051_nations_that_never_were.py::test_R_051_02_its_region_passes_to_bordering"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E07_S051_nations_that_never_were.py::test_R_051_03_nothing_happens"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E07_S051_nations_that_never_were.py::test_R_051_04_it_skipped_this_tick"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E07_S051_nations_that_never_were.py::test_R_051_05_it_never_removed"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E07_S051_nations_that_never_were.py::test_R_051_06_those_regions_become_unowned_with"
allowed_files: "csrc/lifecycle.c"
snippet_file: csrc/lifecycle.c
snippet_symbol: "om_faction_set_created_tick,om_faction_is_active,om_tick_absorptions,om_faction_mark_conquered_this_tick,om_faction_remove"
header_file: csrc/ouroboros_sim.h
extra_context_files: csrc/om_internal.h
rules_file: projects/ouroboros/rules/E-07.md
test_file: tests/csim/test_E07_S051_nations_that_never_were.py
expected_lines: 60
max_wall_minutes: 45
---

## Brief for DeepSeek

Quoted verbatim from docs/bible/epics/E-07-civilizational-lifecycle.md (### S-051 — Nations that never were):

- R-051-01  Given a breakaway faction with zero regions, When 5 or more ticks have passed since its creation tick, Then it is removed from the registry and every faction's stance table.
- R-051-02  Given a breakaway with exactly one region, created 50 or more ticks ago, with budget below 20, When cleanup runs, Then its region passes to the bordering faction with the most regions, held-since resets, previous owner is the breakaway, and the breakaway is removed.
- R-051-03  Given the same breakaway with budget 20 or more, or with two or more regions, or created fewer than 50 ticks ago, When cleanup runs, Then nothing happens.
- R-051-04  Given a breakaway that conquered a region this tick, When cleanup runs, Then it is skipped this tick.
- R-051-05  Given a non-breakaway faction (starting faction) with zero regions, When cleanup runs, Then it is never removed.
- R-051-06  Given a removed faction still owned regions, When removal happens, Then those regions become unowned with held-since cleared.

## Header slice

(run card_slice.py --write after the skeleton lands)
