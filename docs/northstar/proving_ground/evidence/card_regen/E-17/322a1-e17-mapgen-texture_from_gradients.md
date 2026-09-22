---
project: /home/westopoli/Projects/ouroboros-manifold
goal: "csrc/tactical_mapgen.c implements S-114 card 1 of 2 (om_map_generate_gradients, om_map_sample_gradients, om_gradient_sample_single, om_gradient_combine_overlap, om_gradient_get_anchor_intensity)"
acceptance:
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E17_S114_texture_from_gradients.py::test_R_114_01_each_obstacle_density_cover_density"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E17_S114_texture_from_gradients.py::test_R_114_02_its_contribution_intensity_falloff_r"
allowed_files: "csrc/tactical_mapgen.c"
snippet_file: csrc/tactical_mapgen.c
snippet_symbol: "om_map_generate_gradients,om_map_sample_gradients,om_gradient_sample_single,om_gradient_combine_overlap,om_gradient_get_anchor_intensity"
header_file: csrc/ouroboros_sim.h
extra_context_files: csrc/om_internal.h
rules_file: projects/ouroboros/rules/E-17.md
test_file: tests/csim/test_E17_S114_texture_from_gradients.py
expected_lines: 60
max_wall_minutes: 45
---

## Brief for DeepSeek

Quoted verbatim from docs/bible/epics/E-17-map-generation.md (### S-114 — Texture from gradients):

- R-114-01  Given the five properties, When sampled anywhere, Then each of obstacle_density, cover_density, sensor_interference, elevation is a float in [0, 1] and layer_accessibility is binary per layer.
- R-114-02  Given a gradient source (position, type, radius, intensity, falloff), When sampled at distance r ≤ radius, Then its contribution is intensity × falloff(r/radius), and overlapping sources combine [Q-115-01: sum clamped or max].

## Header slice

(run card_slice.py --write after the skeleton lands)
