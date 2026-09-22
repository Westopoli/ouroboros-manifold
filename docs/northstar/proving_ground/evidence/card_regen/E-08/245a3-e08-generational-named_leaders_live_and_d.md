---
project: /home/westopoli/Projects/ouroboros-manifold
goal: "csrc/generational.c implements S-060 card 3 of 3 (om_event_fire_manual, om_event_attached_character_count, om_event_get_attached_character, om_character_has_event_history)"
acceptance:
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E08_S060_named_leaders_live_and_die.py::test_R_060_05_region_s_named_characters_attached"
allowed_files: "csrc/generational.c"
snippet_file: csrc/generational.c
snippet_symbol: "om_event_fire_manual,om_event_attached_character_count,om_event_get_attached_character,om_character_has_event_history"
header_file: csrc/ouroboros_sim.h
extra_context_files: csrc/om_internal.h
rules_file: projects/ouroboros/rules/E-08.md
test_file: tests/csim/test_E08_S060_named_leaders_live_and_die.py
expected_lines: 48
max_wall_minutes: 45
---

## Brief for DeepSeek

Quoted verbatim from docs/bible/epics/E-08-generational-structure.md (### S-060 — Named leaders live and die):

- R-060-05  Given an event of significance tier 3 or higher fires in a region, When logged, Then the region's named characters are attached to the event record; the ledger never stores event history itself.

## Header slice

(run card_slice.py --write after the skeleton lands)
