---
project: /home/westopoli/Projects/ouroboros-manifold
goal: "csrc/lifecycle.c implements S-053 card 1 of 1 (om_faction_set_event_window_counts, om_faction_phase)"
acceptance:
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E07_S053_every_faction_has_an_age.py::test_R_053_01_its_phase_fragmentation"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E07_S053_every_faction_has_an_age.py::test_R_053_02_its_phase_overextension"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E07_S053_every_faction_has_an_age.py::test_R_053_03_conflict"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E07_S053_every_faction_has_an_age.py::test_R_053_04_expansion"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E07_S053_every_faction_has_an_age.py::test_R_053_05_consolidation"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E07_S053_every_faction_has_an_age.py::test_R_053_06_equilibrium"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E07_S053_every_faction_has_an_age.py::test_R_053_07_they_evaluated_in_exactly_this"
allowed_files: "csrc/lifecycle.c"
snippet_file: csrc/lifecycle.c
snippet_symbol: "om_faction_set_event_window_counts,om_faction_phase"
header_file: csrc/ouroboros_sim.h
extra_context_files: csrc/om_internal.h
rules_file: projects/ouroboros/rules/E-07.md
test_file: tests/csim/test_E07_S053_every_faction_has_an_age.py
expected_lines: 24
max_wall_minutes: 45
---

## Brief for DeepSeek

Quoted verbatim from docs/bible/epics/E-07-civilizational-lifecycle.md (### S-053 — Every faction has an age):

- R-053-01  Given a faction's recent event window, When the revolt-and-reversion share of events is at least 0.02, Then its phase is fragmentation.
- R-053-02  Given not fragmentation, When maintenance (regions · 8) divided by total economy exceeds 0.4, Then its phase is overextension.
- R-053-03  Given neither, When the share of attack events is at least 0.05, Then conflict.
- R-053-04  Given none of the above, When empty regions bordering the faction number at least 30 percent of all inhabited regions, Then expansion.
- R-053-05  Given none of the above, When the window holds colonizations and no attacks, Then consolidation.
- R-053-06  Given none of the above, or a faction with no regions, Then equilibrium.
- R-053-07  Given the six checks, When evaluated, Then they are evaluated in exactly this order and the first match wins.

## Header slice

(run card_slice.py --write after the skeleton lands)
