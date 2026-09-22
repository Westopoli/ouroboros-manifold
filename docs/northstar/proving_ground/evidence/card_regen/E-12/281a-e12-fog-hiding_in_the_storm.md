---
project: /home/westopoli/Projects/ouroboros-manifold
goal: "csrc/fog.c implements S-090 card 1 of 1 (om_zone_sample_interference, om_map_add_moving_interference_zone)"
acceptance:
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E12_S090_hiding_in_the_storm.py::test_R_090_01_interference_0_3"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E12_S090_hiding_in_the_storm.py::test_R_090_02_combined_interference_clamped_to_0"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E12_S090_hiding_in_the_storm.py::test_R_090_03_only_observer_s_own_interference"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E12_S090_hiding_in_the_storm.py::test_R_090_04_interference_at_fixed_point_changes"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E12_S090_hiding_in_the_storm.py::test_R_090_05_value_per_layer"
allowed_files: "csrc/fog.c"
snippet_file: csrc/fog.c
snippet_symbol: "om_zone_sample_interference,om_map_add_moving_interference_zone"
header_file: csrc/ouroboros_sim.h
extra_context_files: csrc/om_internal.h
rules_file: projects/ouroboros/rules/E-12.md
test_file: tests/csim/test_E12_S090_hiding_in_the_storm.py
expected_lines: 24
max_wall_minutes: 45
---

## Brief for DeepSeek

Quoted verbatim from docs/bible/epics/E-12-fog-and-sensors.md (### S-090 — Hiding in the storm):

- R-090-01  Given a zone source with intensity 0.6 at its center and linear falloff to 0 at its radius, When sampled at half radius, Then interference is 0.3.
- R-090-02  Given overlapping zones, When sampled, Then the combined interference is clamped to [0, 1] [Q-090-01: sum vs max].
- R-090-03  Given an observer outside a zone looking at a target inside it, When visibility is computed, Then only the observer's own interference applies [Q-090-01: the bible says outsiders "can't see as far into the zone"; code samples the observer's position only].
- R-090-04  Given a zone source that moves over the mission, When ticks pass, Then interference at a fixed point changes as the source moves.
- R-090-05  Given a zone that varies by layer, When sampled, Then the value is per layer.

## Header slice

(run card_slice.py --write after the skeleton lands)
