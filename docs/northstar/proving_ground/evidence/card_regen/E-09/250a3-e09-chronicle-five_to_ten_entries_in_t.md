---
project: /home/westopoli/Projects/ouroboros-manifold
goal: "csrc/chronicle.c implements S-065 card 3 of 3 (om_chronicle_add_cluster_direct, om_chronicle_select_clusters, om_chronicle_selected_category_count, om_chronicle_build_opening_scroll, om_chronicle_count_by_type)"
acceptance:
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E09_S065_five_to_ten_entries_in_the_right_order.py::test_R_065_05_they_taken_in_descending_peak"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E09_S065_five_to_ten_entries_in_the_right_order.py::test_R_065_06_skipped_clusters_added_in_score"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E09_S065_five_to_ten_entries_in_the_right_order.py::test_R_065_07_it_has_3_to_5"
allowed_files: "csrc/chronicle.c"
snippet_file: csrc/chronicle.c
snippet_symbol: "om_chronicle_add_cluster_direct,om_chronicle_select_clusters,om_chronicle_selected_category_count,om_chronicle_build_opening_scroll,om_chronicle_count_by_type"
header_file: csrc/ouroboros_sim.h
extra_context_files: csrc/om_internal.h
rules_file: projects/ouroboros/rules/E-09.md
test_file: tests/csim/test_E09_S065_five_to_ten_entries_in_the_right_order.py
expected_lines: 60
max_wall_minutes: 45
---

## Brief for DeepSeek

Quoted verbatim from docs/bible/epics/E-09-chronicle.md (### S-065 — Five to ten entries, in the right order):

- R-065-05  Given the remaining clusters, When the budget is filled, Then they are taken in descending peak score, skipping any category that already has 2 entries, until 10 entries.
- R-065-06  Given fewer than 5 entries after ranking, When the budget is filled, Then skipped clusters are added in score order until 5 or the clusters run out.
- R-065-07  Given the opening jump of a campaign, When the scroll is built, Then it has 3 to 5 entries and no consequence or lineage cluster.

## Header slice

(run card_slice.py --write after the skeleton lands)
