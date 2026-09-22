---
project: /home/westopoli/Projects/ouroboros-manifold
goal: "csrc/lifecycle.c implements S-049 card 1 of 1 (om_event_queue_external, om_tick_revolts, om_tick_pruned)"
acceptance:
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E07_S049_a_revolt_can_birth_a_nation.py::test_R_049_01_one_draw_sets_success_rate"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E07_S049_a_revolt_can_birth_a_nation.py::test_R_049_02_no_faction_forms"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E07_S049_a_revolt_can_birth_a_nation.py::test_R_049_03_region_keeps_military_0_40"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E07_S049_a_revolt_can_birth_a_nation.py::test_R_049_04_its_id_breakaway_tick_region"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E07_S049_a_revolt_can_birth_a_nation.py::test_R_049_05_success_rate_1_0_with"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E07_S049_a_revolt_can_birth_a_nation.py::test_R_049_06_nothing_happens_chain_pruned"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E07_S049_a_revolt_can_birth_a_nation.py::test_R_049_07_every_edge_touching_it_becomes"
allowed_files: "csrc/lifecycle.c"
snippet_file: csrc/lifecycle.c
snippet_symbol: "om_event_queue_external,om_tick_revolts,om_tick_pruned"
header_file: csrc/ouroboros_sim.h
extra_context_files: csrc/om_internal.h
rules_file: projects/ouroboros/rules/E-07.md
test_file: tests/csim/test_E07_S049_a_revolt_can_birth_a_nation.py
expected_lines: 36
max_wall_minutes: 45
---

## Brief for DeepSeek

Quoted verbatim from docs/bible/epics/E-07-civilizational-lifecycle.md (### S-049 — A revolt can birth a nation):

- R-049-01  Given Revolt Entrenched fires in an owned region, When resolved, Then one draw sets the success rate uniform in [0.50, 0.95] and a second draw must be ≤ that rate, else no faction forms.
- R-049-02  Given the success draw passes but the region's population is below 25, When resolved, Then no faction forms.
- R-049-03  Given a breakaway forms, When the region is split, Then the region keeps military · 0.40 and economy · 0.60 (the revolt takes 60 percent of the army and 40 percent of the economy), then tension is capped at 40, population floored at 25, economy floored at 20.
- R-049-04  Given a breakaway forms, When the faction is created, Then its id is `breakaway_<tick>_<region>`, archetype `breakaway`, budget 0, growth rate 0.025, attack confidence uniform in [2, 5], tech equal to the parent's, stance hostile with every faction both ways, and a color distinct from every existing faction's hue by more than 0.08.
- R-049-05  Given Admin Breakaway fires (E-05 S-040), When resolved, Then the success rate is 1.0 with no population check, and the archetype is one draw from conqueror, fortifier, warlord, opportunist, schism.
- R-049-06  Given an admin chain whose region changed owner after the chain started, When Admin Breakaway fires, Then nothing happens (the chain is pruned).
- R-049-07  Given the region's edges, When ownership changes to the breakaway, Then every edge touching it becomes `border`.

## Header slice

(run card_slice.py --write after the skeleton lands)
