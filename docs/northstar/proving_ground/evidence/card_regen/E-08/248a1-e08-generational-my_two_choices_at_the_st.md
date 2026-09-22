---
project: /home/westopoli/Projects/ouroboros-manifold
goal: "csrc/generational.c implements S-063 card 1 of 2 (om_onboarding_validate, om_onboarding_save_to_slot, om_onboarding_load_from_slot, om_onboarding_update_choices, om_campaign_trigger_terminal_restart)"
acceptance:
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E08_S063_my_two_choices_at_the_start.py::test_R_063_01_it_offers_difficulty_easy_medium"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E08_S063_my_two_choices_at_the_start.py::test_R_063_02_choices_stored_per_save_slot"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E08_S063_my_two_choices_at_the_start.py::test_R_063_03_q_063_02_where_westley"
allowed_files: "csrc/generational.c"
snippet_file: csrc/generational.c
snippet_symbol: "om_onboarding_validate,om_onboarding_save_to_slot,om_onboarding_load_from_slot,om_onboarding_update_choices,om_campaign_trigger_terminal_restart"
header_file: csrc/ouroboros_sim.h
extra_context_files: csrc/om_internal.h
rules_file: projects/ouroboros/rules/E-08.md
test_file: tests/csim/test_E08_S063_my_two_choices_at_the_start.py
expected_lines: 60
max_wall_minutes: 45
---

## Brief for DeepSeek

Quoted verbatim from docs/bible/epics/E-08-generational-structure.md (### S-063 — My two choices at the start):

- R-063-01  Given the onboarding screen, When shown, Then it offers difficulty (easy, medium, hard) and, for each of the 10 mission archetypes, a preference weight with a "rare" mark; at least one archetype must stay unmarked [Q-063-01: bible says at most two rare marks, code allows up to nine].
- R-063-02  Given the player confirms, When saved, Then the choices are stored per save slot and read by the mission generator (E-10) and difficulty scaling.
- R-063-03  Given the player wants to change the choices later, When they do, Then [Q-063-02: where and when; Westley removed permanence, A-058].

## Header slice

(run card_slice.py --write after the skeleton lands)
