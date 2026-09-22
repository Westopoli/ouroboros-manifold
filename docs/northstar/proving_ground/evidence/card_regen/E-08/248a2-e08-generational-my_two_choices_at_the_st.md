---
project: /home/westopoli/Projects/ouroboros-manifold
goal: "csrc/generational.c implements S-063 card 2 of 2 (om_campaign_needs_onboarding)"
acceptance:
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E08_S063_my_two_choices_at_the_start.py::test_R_063_04_onboarding_screen_shows_again"
allowed_files: "csrc/generational.c"
snippet_file: csrc/generational.c
snippet_symbol: "om_campaign_needs_onboarding"
header_file: csrc/ouroboros_sim.h
extra_context_files: csrc/om_internal.h
rules_file: projects/ouroboros/rules/E-08.md
test_file: tests/csim/test_E08_S063_my_two_choices_at_the_start.py
expected_lines: 12
max_wall_minutes: 45
---

## Brief for DeepSeek

Quoted verbatim from docs/bible/epics/E-08-generational-structure.md (### S-063 — My two choices at the start):

- R-063-04  Given a new campaign after a terminal condition (S-054), When it starts, Then the onboarding screen shows again.

## Header slice

(run card_slice.py --write after the skeleton lands)
