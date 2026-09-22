---
project: /home/westopoli/Projects/ouroboros-manifold
goal: "csrc/fog.c implements S-092 card 3 of 4 (om_command_move, om_mission_get_clock, om_mission_is_started, om_unit_get_pos, om_mission_begin)"
acceptance:
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E12_S092_recon_then_fog.py::test_R_092_02_it_has_not_started_no"
allowed_files: "csrc/fog.c"
snippet_file: csrc/fog.c
snippet_symbol: "om_command_move,om_mission_get_clock,om_mission_is_started,om_unit_get_pos,om_mission_begin"
header_file: csrc/ouroboros_sim.h
extra_context_files: csrc/om_internal.h
rules_file: projects/ouroboros/rules/E-12.md
test_file: tests/csim/test_E12_S092_recon_then_fog.py
expected_lines: 60
max_wall_minutes: 45
---

## Brief for DeepSeek

Quoted verbatim from docs/bible/epics/E-12-fog-and-sensors.md (### S-092 — Recon, then fog):

- R-092-02  Given the recon phase, When the mission clock is read, Then it has not started, and no unit moves.

## Header slice

(run card_slice.py --write after the skeleton lands)
