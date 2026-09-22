---
project: /home/westopoli/Projects/ouroboros-manifold
goal: "csrc/chronicle.c implements S-071 card 3 of 3 (om_event_template_chronicle_prose)"
acceptance:
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E09_S071_the_fragment_library_contract.py::test_R_071_04_it_has_chronicle_prose_phrase"
allowed_files: "csrc/chronicle.c"
snippet_file: csrc/chronicle.c
snippet_symbol: "om_event_template_chronicle_prose"
header_file: csrc/ouroboros_sim.h
extra_context_files: csrc/om_internal.h
rules_file: projects/ouroboros/rules/E-09.md
test_file: tests/csim/test_E09_S071_the_fragment_library_contract.py
expected_lines: 12
max_wall_minutes: 45
---

## Brief for DeepSeek

Quoted verbatim from docs/bible/epics/E-09-chronicle.md (### S-071 — The fragment library contract):

- R-071-04  Given every event template, When the library is validated, Then it has a chronicle prose phrase (lowercase noun phrase), else validation fails.

## Header slice

(run card_slice.py --write after the skeleton lands)
