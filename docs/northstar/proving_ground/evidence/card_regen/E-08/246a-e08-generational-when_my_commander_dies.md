---
project: /home/westopoli/Projects/ouroboros-manifold
goal: "csrc/generational.c implements S-061 card 1 of 1 (om_character_selector_resolve_commander_death, om_outcome_record_commander_death, om_ledger_commander_death_region, om_ledger_commander_death_outcome_band)"
acceptance:
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E08_S061_when_my_commander_dies.py::test_R_061_01_living_lineage_member_not_supreme"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E08_S061_when_my_commander_dies.py::test_R_061_02_successor_becomes_commander_same_lineage"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E08_S061_when_my_commander_dies.py::test_R_061_03_rotation_happens_with_reason_commander"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E08_S061_when_my_commander_dies.py::test_R_061_04_ledger_records_region_outcome_band"
allowed_files: "csrc/generational.c"
snippet_file: csrc/generational.c
snippet_symbol: "om_character_selector_resolve_commander_death,om_outcome_record_commander_death,om_ledger_commander_death_region,om_ledger_commander_death_outcome_band"
header_file: csrc/ouroboros_sim.h
extra_context_files: csrc/om_internal.h
rules_file: projects/ouroboros/rules/E-08.md
test_file: tests/csim/test_E08_S061_when_my_commander_dies.py
expected_lines: 48
max_wall_minutes: 45
---

## Brief for DeepSeek

Quoted verbatim from docs/bible/epics/E-08-generational-structure.md (### S-061 — When my commander dies):

- R-061-01  Given the commander died in the mission, When the next selection runs, Then a living lineage member (not a supreme commander) in the mission region is chosen first, then one in an adjacent region, then, only if the lineage has fewer than 2 chapters played, any living member anywhere.
- R-061-02  Given a successor is found, When assigned, Then the successor becomes the commander of the same lineage and the chapter counter continues.
- R-061-03  Given no successor, When selection runs, Then rotation happens with reason `commander_death`.
- R-061-04  Given a commander death, When recorded, Then the ledger records the region and outcome band and the chronicle frames it (E-09).

## Header slice

(run card_slice.py --write after the skeleton lands)
