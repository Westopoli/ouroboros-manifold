---
project: /home/westopoli/Projects/ouroboros-manifold
goal: "csrc/fog.c implements S-094 card 1 of 1 (om_fog_get_treatment_at, om_fog_get_drawn_sensor_circle_radius)"
acceptance:
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E12_S094_how_fog_looks.py::test_R_094_01_revealed_area_fogged_area_interference"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E12_S094_how_fog_looks.py::test_R_094_02_its_own_sensor_circle_visibly"
allowed_files: "csrc/fog.c"
snippet_file: csrc/fog.c
snippet_symbol: "om_fog_get_treatment_at,om_fog_get_drawn_sensor_circle_radius"
header_file: csrc/ouroboros_sim.h
extra_context_files: csrc/om_internal.h
rules_file: projects/ouroboros/rules/E-12.md
test_file: tests/csim/test_E12_S094_how_fog_looks.py
expected_lines: 24
max_wall_minutes: 45
---

## Brief for DeepSeek

Quoted verbatim from docs/bible/epics/E-12-fog-and-sensors.md (### S-094 — How fog looks):

- R-094-01  Given a T2 screenshot, When inspected, Then revealed area, fogged area, and interference zones are three distinguishable treatments.
- R-094-02  Given a unit inside interference, When drawn, Then its own sensor circle is visibly smaller.

## Header slice

(run card_slice.py --write after the skeleton lands)
