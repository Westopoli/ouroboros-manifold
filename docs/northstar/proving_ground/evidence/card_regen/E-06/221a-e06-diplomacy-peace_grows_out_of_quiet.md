---
project: /home/westopoli/Projects/ouroboros-manifold
goal: "csrc/diplomacy.c implements S-043 card 1 of 1 (om_faction_stance_counter, om_faction_set_stance_counter, om_faction_cooperative_since, om_archetype_peace_disposition)"
acceptance:
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E06_S043_peace_grows_out_of_quiet.py::test_R_043_01_their_non_aggression_counter_increments"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E06_S043_peace_grows_out_of_quiet.py::test_R_043_02_counter_does_not_move"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E06_S043_peace_grows_out_of_quiet.py::test_R_043_03_overture_fires_if_both_sides"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E06_S043_peace_grows_out_of_quiet.py::test_R_043_04_p_min_1_0_5"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E06_S043_peace_grows_out_of_quiet.py::test_R_043_05_pair_becomes_cooperative_cooperative_since"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E06_S043_peace_grows_out_of_quiet.py::test_R_043_06_pair_stays_neutral_counter_resets"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E06_S043_peace_grows_out_of_quiet.py::test_R_043_07_conqueror_0_1_fortifier_2"
allowed_files: "csrc/diplomacy.c"
snippet_file: csrc/diplomacy.c
snippet_symbol: "om_faction_stance_counter,om_faction_set_stance_counter,om_faction_cooperative_since,om_archetype_peace_disposition"
header_file: csrc/ouroboros_sim.h
extra_context_files: csrc/om_internal.h
rules_file: projects/ouroboros/rules/E-06.md
test_file: tests/csim/test_E06_S043_peace_grows_out_of_quiet.py
expected_lines: 48
max_wall_minutes: 45
---

## Brief for DeepSeek

Quoted verbatim from docs/bible/epics/E-06-diplomacy-and-technology.md (### S-043 — Peace grows out of quiet):

- R-043-01  Given a neutral pair that shares at least one border edge, When a tick passes with no attack between them, Then their non-aggression counter increments by 1; an attack between them resets it to 0.
- R-043-02  Given a neutral pair that shares no border, When ticks pass, Then the counter does not move.
- R-043-03  Given the counter reaches 80, When peace formation is checked, Then an overture fires if both sides' average border-region stability is at least 35; otherwise the counter resets to 0 with no overture.
- R-043-04  Given an overture between factions with average economies 60 and 40, minimum border stability 50, dispositions 2.0 and 1.5, When success is rolled, Then p = min(1, 0.5 · (1 − 0.2) · 0.5 · 2.0 · 1.5) = 0.6, one draw.
- R-043-05  Given the overture succeeds, When applied, Then the pair becomes cooperative, cooperative-since is the current tick, and every shared edge becomes `both`.
- R-043-06  Given the overture fails, When applied, Then the pair stays neutral and the counter resets to 0.
- R-043-07  Given dispositions, When read, Then conqueror 0.1, fortifier 2.0, warlord 0.2, opportunist 1.0, schism 0.3, player 1.5, breakaway 0.8.

## Header slice

(run card_slice.py --write after the skeleton lands)
