---
project: /home/westopoli/Projects/ouroboros-manifold
goal: "csrc/unit.c implements S-084 card 1 of 3 (om_unit_set_brace_active, om_unit_set_fortify_active, om_unit_set_warden_aura_active, om_unit_fire_aoe_attack, om_command_move)"
acceptance:
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E11_S084_flat_damage.py::test_R_084_01_one_attack_lands_for_base"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E11_S084_flat_damage.py::test_R_084_03_every_enemy_on_bombard_s"
allowed_files: "csrc/unit.c"
snippet_file: csrc/unit.c
snippet_symbol: "om_unit_set_brace_active,om_unit_set_fortify_active,om_unit_set_warden_aura_active,om_unit_fire_aoe_attack,om_command_move"
header_file: csrc/ouroboros_sim.h
extra_context_files: csrc/om_internal.h
rules_file: projects/ouroboros/rules/E-11.md
test_file: tests/csim/test_E11_S084_flat_damage.py
expected_lines: 60
max_wall_minutes: 45
---

## Brief for DeepSeek

Quoted verbatim from docs/bible/epics/E-11-units-and-combat.md (### S-084 — Flat damage):

- R-084-01  Given an attacker in range of its target every tick, When its attack timer elapses (interval × 20 ticks), Then one attack lands for base × matchup × output multiplier × (1 − reduction), with reduction the sum of Brace 0.50, Fortify 0.20, and Warden aura 0.10 where they apply, capped at 0.9.
- R-084-03  Given a Bombard attack centered on a target, When resolved, Then every enemy on the Bombard's layer within 150 wu of the target takes full per-target damage, and the total across all targets is capped at 4 × base damage (70), applied in target order until the cap.

## Header slice

(run card_slice.py --write after the skeleton lands)
