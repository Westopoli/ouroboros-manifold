---
project: /home/westopoli/Projects/ouroboros-manifold
goal: "csrc/chronicle.c implements S-071 card 2 of 3 (om_chronicle_fragment_check_near_duplicate, om_chronicle_fragment_batch_exceeds_rejection_limit, om_events_load_launch, om_chronicle_validate_event_template_prose, om_event_template_count)"
acceptance:
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E09_S071_the_fragment_library_contract.py::test_R_071_03_later_rejected_batch_losing_more"
allowed_files: "csrc/chronicle.c"
snippet_file: csrc/chronicle.c
snippet_symbol: "om_chronicle_fragment_check_near_duplicate,om_chronicle_fragment_batch_exceeds_rejection_limit,om_events_load_launch,om_chronicle_validate_event_template_prose,om_event_template_count"
header_file: csrc/ouroboros_sim.h
extra_context_files: csrc/om_internal.h
rules_file: projects/ouroboros/rules/E-09.md
test_file: tests/csim/test_E09_S071_the_fragment_library_contract.py
expected_lines: 60
max_wall_minutes: 45
---

## Brief for DeepSeek

Quoted verbatim from docs/bible/epics/E-09-chronicle.md (### S-071 — The fragment library contract):

- R-071-03  Given two fragments in the same pool, When their edit distance is below the threshold, Then the later is rejected; a batch losing more than 35 percent to rejection is flagged, not shipped.

## Header slice

(run card_slice.py --write after the skeleton lands)
