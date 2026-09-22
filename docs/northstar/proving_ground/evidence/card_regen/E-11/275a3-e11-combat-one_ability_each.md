---
project: /home/westopoli/Projects/ouroboros-manifold
goal: "csrc/unit.c implements S-086 card 3 of 3 (om_tactical_tick)"
acceptance:
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E11_S086_one_ability_each.py::test_R_086_09_explicit_ability_event_with_tick"
allowed_files: "csrc/unit.c"
snippet_file: csrc/unit.c
snippet_symbol: "om_tactical_tick"
header_file: csrc/ouroboros_sim.h
extra_context_files: csrc/om_internal.h
rules_file: projects/ouroboros/rules/E-11.md
test_file: tests/csim/test_E11_S086_one_ability_each.py
expected_lines: 12
max_wall_minutes: 45
---

## Brief for DeepSeek

Quoted verbatim from docs/bible/epics/E-11-units-and-combat.md (### S-086 — One ability each):

- R-086-09  Given any ability activation, When it fires, Then an explicit ability event with tick, unit, ability, target, duration, and radius is emitted for the renderer (E-18).

## Header slice

(run card_slice.py --write after the skeleton lands)
