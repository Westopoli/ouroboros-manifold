---
project: /home/westopoli/Projects/ouroboros-manifold
goal: "csrc/fog.c implements S-092 card 4 of 4 (om_mission_get_phase, om_player_can_see_unit, om_recon_get_terrain_visibility_ratio)"
acceptance:
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E12_S092_recon_then_fog.py::test_R_092_03_fog_applies_per_s_089"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E12_S092_recon_then_fog.py::test_R_092_04_terrain_visibility_complete_regardless_world"
allowed_files: "csrc/fog.c"
snippet_file: csrc/fog.c
snippet_symbol: "om_mission_get_phase,om_player_can_see_unit,om_recon_get_terrain_visibility_ratio"
header_file: csrc/ouroboros_sim.h
extra_context_files: csrc/om_internal.h
rules_file: projects/ouroboros/rules/E-12.md
test_file: tests/csim/test_E12_S092_recon_then_fog.py
expected_lines: 36
max_wall_minutes: 45
---

## Brief for DeepSeek

Quoted verbatim from docs/bible/epics/E-12-fog-and-sensors.md (### S-092 — Recon, then fog):

- R-092-03  Given the player presses Begin Mission, When the first tactical tick runs, Then fog applies per S-089 and terrain stays visible.
- R-092-04  Given any mission, When recon runs, Then terrain visibility is complete regardless of world state.

## Header slice

(run card_slice.py --write after the skeleton lands)
