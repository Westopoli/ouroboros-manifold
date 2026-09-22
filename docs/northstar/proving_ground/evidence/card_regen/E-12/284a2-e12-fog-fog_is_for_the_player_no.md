---
project: /home/westopoli/Projects/ouroboros-manifold
goal: "csrc/fog.c implements S-093 card 2 of 2 (om_strategic_agent_read_region_field)"
acceptance:
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E12_S093_fog_is_for_the_player_not_the_engine.py::test_R_093_03_they_read_every_neighbor_region"
allowed_files: "csrc/fog.c"
snippet_file: csrc/fog.c
snippet_symbol: "om_strategic_agent_read_region_field"
header_file: csrc/ouroboros_sim.h
extra_context_files: csrc/om_internal.h
rules_file: projects/ouroboros/rules/E-12.md
test_file: tests/csim/test_E12_S093_fog_is_for_the_player_not_the_engine.py
expected_lines: 12
max_wall_minutes: 45
---

## Brief for DeepSeek

Quoted verbatim from docs/bible/epics/E-12-fog-and-sensors.md (### S-093 — Fog is for the player, not the engine):

- R-093-03  Given the strategic sim, When faction agents decide, Then they read every neighbor region's fields without fog (E-05).

## Header slice

(run card_slice.py --write after the skeleton lands)
