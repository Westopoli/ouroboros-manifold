---
project: /home/westopoli/Projects/ouroboros-manifold
goal: "csrc/chronicle.c implements S-068 card 1 of 2 (om_chronicle_assemble_cluster_entry, om_chronicle_render_region_mention, om_chronicle_apply_slot_echo_anaphora, om_chronicle_apply_word_echo_synonym, om_chronicle_add_raw_entry)"
acceptance:
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E09_S068_written_from_fragments_never_the_same_twice.py::test_R_068_01_opening_detail_closing_each_drawn"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E09_S068_written_from_fragments_never_the_same_twice.py::test_R_068_02_openings_at_most_30_words"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E09_S068_written_from_fragments_never_the_same_twice.py::test_R_068_03_it_comes_only_from_vocabulary"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E09_S068_written_from_fragments_never_the_same_twice.py::test_R_068_04_it_reads_region_held_by"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E09_S068_written_from_fragments_never_the_same_twice.py::test_R_068_05_second_becomes_anaphoric_form_what"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E09_S068_written_from_fragments_never_the_same_twice.py::test_R_068_06_second_occurrence_replaced_by_synonym"
allowed_files: "csrc/chronicle.c"
snippet_file: csrc/chronicle.c
snippet_symbol: "om_chronicle_assemble_cluster_entry,om_chronicle_render_region_mention,om_chronicle_apply_slot_echo_anaphora,om_chronicle_apply_word_echo_synonym,om_chronicle_add_raw_entry"
header_file: csrc/ouroboros_sim.h
extra_context_files: csrc/om_internal.h
rules_file: projects/ouroboros/rules/E-09.md
test_file: tests/csim/test_E09_S068_written_from_fragments_never_the_same_twice.py
expected_lines: 60
max_wall_minutes: 45
---

## Brief for DeepSeek

Quoted verbatim from docs/bible/epics/E-09-chronicle.md (### S-068 — Written from fragments, never the same twice):

- R-068-01  Given a cluster with category C, When its entry is assembled, Then an opening, a detail, and a closing are each drawn uniformly from C's pools among fragments whose required slots resolve from the cluster; base form = opening + detail, expanded form = opening + detail + closing.
- R-068-02  Given fragment length limits, When the library is validated, Then openings are at most 30 words and details and closings at most 35 [Q-068-01]; base form under 90 words, expanded under 140.
- R-068-03  Given a slot, When resolved, Then it comes only from the vocabulary: identity (character name, rank, faction, lineage name, faction name, region name, adjacent region), event (event description as a lowercase noun phrase, chain length, duration prose), state (field delta summary, stability, capacity, tension as qualitative words), consequence (mission outcome phrase, archetype, mission region), relational (previous event reference, lineage history note); no raw numbers ever appear.
- R-068-04  Given a region's first mention in a scroll, When rendered, Then it reads "<region>, held by <faction display name>", and later mentions use the bare name; an unowned region gets no qualifier.
- R-068-05  Given an assembled entry, When two adjacent fragments resolve the same slot value of 6 or more words, Then the second becomes an anaphoric form ("what followed", "the outcome").
- R-068-06  Given an assembled entry, When a significant word (4+ letters, not a stop word) appears twice, Then the second occurrence is replaced by a synonym from the curated map if one exists.

## Header slice

(run card_slice.py --write after the skeleton lands)
