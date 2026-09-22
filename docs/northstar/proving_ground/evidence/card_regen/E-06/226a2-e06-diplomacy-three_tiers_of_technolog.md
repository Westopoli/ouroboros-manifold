---
project: /home/westopoli/Projects/ouroboros-manifold
goal: "csrc/diplomacy.c implements S-048 card 2 of 2 (om_faction_unit_tier, om_chronicle_distill_candidates, om_tier_transition_candidate_exists, om_faction_tier_transition_candidate)"
acceptance:
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E06_S048_three_tiers_of_technology.py::test_R_048_02_units_use_tier_2_profile"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E06_S048_three_tiers_of_technology.py::test_R_048_03_units_use_tier_2_profile"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E06_S048_three_tiers_of_technology.py::test_R_048_04_tier_transition_entry_candidate_e"
allowed_files: "csrc/diplomacy.c"
snippet_file: csrc/diplomacy.c
snippet_symbol: "om_faction_unit_tier,om_chronicle_distill_candidates,om_tier_transition_candidate_exists,om_faction_tier_transition_candidate"
header_file: csrc/ouroboros_sim.h
extra_context_files: csrc/om_internal.h
rules_file: projects/ouroboros/rules/E-06.md
test_file: tests/csim/test_E06_S048_three_tiers_of_technology.py
expected_lines: 48
max_wall_minutes: 45
---

## Brief for DeepSeek

Quoted verbatim from docs/bible/epics/E-06-diplomacy-and-technology.md (### S-048 — Three tiers of technology):

- R-048-02  Given a faction crosses from 33.9 to 34.1, When the next mission generates its forces, Then units use the tier 2 profile; units already fielded in a running mission do not change.
- R-048-03  Given a faction's tech falls from 67.5 to 66.5, When the next mission generates forces, Then units use the tier 2 profile.
- R-048-04  Given a tier change on tick t, When the chronicle distills the window containing t, Then a tier-transition entry is a candidate (E-09).

## Header slice

(run card_slice.py --write after the skeleton lands)
