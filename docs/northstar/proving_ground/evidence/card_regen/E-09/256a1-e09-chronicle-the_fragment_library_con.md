---
project: /home/westopoli/Projects/ouroboros-manifold
goal: "csrc/chronicle.c implements S-071 card 1 of 3 (om_chronicle_fragment_library_load_launch, om_chronicle_fragment_category_count, om_chronicle_fragment_pool_counts, om_chronicle_fragment_library_validate, om_chronicle_fragment_inject_invalid_slot)"
acceptance:
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E09_S071_the_fragment_library_contract.py::test_R_071_01_every_category_has_at_least"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E09_S071_the_fragment_library_contract.py::test_R_071_02_every_fragment_uses_only_vocabulary"
allowed_files: "csrc/chronicle.c"
snippet_file: csrc/chronicle.c
snippet_symbol: "om_chronicle_fragment_library_load_launch,om_chronicle_fragment_category_count,om_chronicle_fragment_pool_counts,om_chronicle_fragment_library_validate,om_chronicle_fragment_inject_invalid_slot"
header_file: csrc/ouroboros_sim.h
extra_context_files: csrc/om_internal.h
rules_file: projects/ouroboros/rules/E-09.md
test_file: tests/csim/test_E09_S071_the_fragment_library_contract.py
expected_lines: 60
max_wall_minutes: 45
---

## Brief for DeepSeek

Quoted verbatim from docs/bible/epics/E-09-chronicle.md (### S-071 — The fragment library contract):

- R-071-01  Given the launch library, When loaded, Then every category has at least 6 openings, 8 details, and 5 closings (240 assemblies per category).
- R-071-02  Given the library, When validated, Then every fragment uses only vocabulary slots, uses all of its category's required slots (lineage categories require lineage name; consequence categories require mission outcome; chain categories require region name), is within its word limit, contains no banned mechanical or meta phrase, and has a unique id.

## Header slice

(run card_slice.py --write after the skeleton lands)
