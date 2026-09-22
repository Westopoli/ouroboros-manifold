---
project: /home/westopoli/Projects/ouroboros-manifold
goal: "csrc/mission.c implements S-079 card 1 of 1 (om_mission_assemble_briefing, om_mission_get_briefing_controls, om_mission_can_edit_loadout, om_mission_get_debrief)"
acceptance:
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E10_S079_orders_not_menus.py::test_R_079_01_it_has_exactly_situation_objective"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E10_S079_orders_not_menus.py::test_R_079_02_only_controls_accept_refuse_there"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E10_S079_orders_not_menus.py::test_R_079_03_it_shows_band_objectives_with"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E10_S079_orders_not_menus.py::test_R_079_04_it_contains_no_raw_field"
allowed_files: "csrc/mission.c"
snippet_file: csrc/mission.c
snippet_symbol: "om_mission_assemble_briefing,om_mission_get_briefing_controls,om_mission_can_edit_loadout,om_mission_get_debrief"
header_file: csrc/ouroboros_sim.h
extra_context_files: csrc/om_internal.h
rules_file: projects/ouroboros/rules/E-10.md
test_file: tests/csim/test_E10_S079_orders_not_menus.py
expected_lines: 48
max_wall_minutes: 45
---

## Brief for DeepSeek

Quoted verbatim from docs/bible/epics/E-10-missions.md (### S-079 — Orders, not menus):

- R-079-01  Given a mission setup, When the briefing is assembled, Then it has exactly Situation, Objective, and Assets, in that order, each from authored fragments with slots filled from the trigger context, ledger, and force composition; Assets states parity in prose and names shortfall types.
- R-079-02  Given the briefing, When shown, Then the only controls are Accept and Refuse; there is no loadout or force editing.
- R-079-03  Given the mission ends, When the debrief is shown, Then it shows the band, the objectives with completion, force retention, and commander fate.
- R-079-04  Given any briefing or debrief text, When rendered, Then it contains no raw field numbers.

## Header slice

(run card_slice.py --write after the skeleton lands)
