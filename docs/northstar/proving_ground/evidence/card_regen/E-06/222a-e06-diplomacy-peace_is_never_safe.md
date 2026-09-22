---
project: /home/westopoli/Projects/ouroboros-manifold
goal: "csrc/diplomacy.c implements S-044 card 1 of 1 (om_faction_betrayal_chance, om_faction_betrayal_opportunity, om_archetype_betrayal_weight)"
acceptance:
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E06_S044_peace_is_never_safe.py::test_R_044_02_p_0_005_2_5"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E06_S044_peace_is_never_safe.py::test_R_044_03_opportunity_factor_3_0"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E06_S044_peace_is_never_safe.py::test_R_044_04_opportunity_1_0_pressure_1"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E06_S044_peace_is_never_safe.py::test_R_044_05_conqueror_2_5_fortifier_0"
allowed_files: "csrc/diplomacy.c"
snippet_file: csrc/diplomacy.c
snippet_symbol: "om_faction_betrayal_chance,om_faction_betrayal_opportunity,om_archetype_betrayal_weight"
header_file: csrc/ouroboros_sim.h
extra_context_files: csrc/om_internal.h
rules_file: projects/ouroboros/rules/E-06.md
test_file: tests/csim/test_E06_S044_peace_is_never_safe.py
expected_lines: 36
max_wall_minutes: 45
---

## Brief for DeepSeek

Quoted verbatim from docs/bible/epics/E-06-diplomacy-and-technology.md (### S-044 — Peace is never safe):

- R-044-02  Given a conqueror with border military 60 facing a partner's border military 20, average tension 60, When its chance is computed, Then p = 0.005 · 2.5 · min(3.0, 3.0) · max(1, 1.2) = 0.045.
- R-044-03  Given the partner's border military is 0, When computed, Then the opportunity factor is 3.0.
- R-044-04  Given border military 20 facing 60 and tension 20, When computed, Then opportunity = 1.0 and pressure = 1.0, so p = 0.005 · weight.
- R-044-05  Given weights, When read, Then conqueror 2.5, fortifier 0.3, warlord 2.0, opportunist 2.0, schism 1.5, player 0.5, breakaway 1.0.

## Header slice

(run card_slice.py --write after the skeleton lands)
