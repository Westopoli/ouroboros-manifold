---
project: /home/westopoli/Projects/ouroboros-manifold
goal: "csrc/mission.c implements S-073 card 3 of 3 (om_mission_get_player_parity, om_mission_get_time_limit)"
acceptance:
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E10_S073_ten_kinds_of_trouble.py::test_R_073_04_briefing_notes_it_nothing_mechanical"
allowed_files: "csrc/mission.c"
snippet_file: csrc/mission.c
snippet_symbol: "om_mission_get_player_parity,om_mission_get_time_limit"
header_file: csrc/ouroboros_sim.h
extra_context_files: csrc/om_internal.h
rules_file: projects/ouroboros/rules/E-10.md
test_file: tests/csim/test_E10_S073_ten_kinds_of_trouble.py
expected_lines: 24
max_wall_minutes: 45
---

## Brief for DeepSeek

Quoted verbatim from docs/bible/epics/E-10-missions.md (### S-073 — Ten kinds of trouble):

- R-073-04  Given "inheritance" framing, When the ledger finds a lineage connection to the mission region, Then the briefing notes it and nothing mechanical changes.

## Header slice

(run card_slice.py --write after the skeleton lands)
