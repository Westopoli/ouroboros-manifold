---
project: /home/westopoli/Projects/ouroboros-manifold
goal: "csrc/tactical_support.c implements S-127 card 3 of 3 (om_tactical_tick, om_structure_on_owner_changed, om_ticker_pop_message, om_structure_get_base_max_hp, om_structure_get_matchup_multiplier)"
acceptance:
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E15_S127_taking_a_garrison.py::test_R_127_03_it_takes_damage_like_unit"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E15_S127_taking_a_garrison.py::test_R_127_04_structure_captured_or_structure_lost"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E15_S127_taking_a_garrison.py::test_R_127_05_it_3_000_alg_75"
allowed_files: "csrc/tactical_support.c"
snippet_file: csrc/tactical_support.c
snippet_symbol: "om_tactical_tick,om_structure_on_owner_changed,om_ticker_pop_message,om_structure_get_base_max_hp,om_structure_get_matchup_multiplier"
header_file: csrc/ouroboros_sim.h
extra_context_files: csrc/om_internal.h
rules_file: projects/ouroboros/rules/E-15.md
test_file: tests/csim/test_E15_S127_taking_a_garrison.py
expected_lines: 60
max_wall_minutes: 45
---

## Brief for DeepSeek

Quoted verbatim from docs/bible/epics/E-15-reinforcement-supply-and-hazards.md (### S-127 — Taking a garrison):

- R-127-03  Given a structure at HP 3,000, When attacked, Then it takes damage like a unit with no matchup multiplier; at 0 HP it is removed for the rest of the mission and never rebuilt.
- R-127-04  Given a structure changes owner, When the ticker runs, Then "structure captured" or "structure lost" appears (E-16 R-104-01).
- R-127-05  Given a structure's HP, When read, Then it is 3,000 (ALG-75) with no category multiplier applied to structures; a single Bombard at 70 per attack needs about 43 attacks, so splash alone does not destroy it in one engagement.

## Header slice

(run card_slice.py --write after the skeleton lands)
