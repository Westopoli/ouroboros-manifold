---
project: /home/westopoli/Projects/ouroboros-manifold
goal: "csrc/chronicle.c implements S-068 card 2 of 2 (om_chronicle_dedup_content_words, om_chronicle_entry_is_retained, om_chronicle_assemble_with_seed, om_chronicle_get_full_scroll_text)"
acceptance:
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E09_S068_written_from_fragments_never_the_same_twice.py::test_R_068_07_later_one_dropped_first_always"
  - "/home/westopoli/Projects/agora/.venv/bin/python -m pytest -q -p no:cacheprovider tests/csim/test_E09_S068_written_from_fragments_never_the_same_twice.py::test_R_068_08_text_identical"
allowed_files: "csrc/chronicle.c"
snippet_file: csrc/chronicle.c
snippet_symbol: "om_chronicle_dedup_content_words,om_chronicle_entry_is_retained,om_chronicle_assemble_with_seed,om_chronicle_get_full_scroll_text"
header_file: csrc/ouroboros_sim.h
extra_context_files: csrc/om_internal.h
rules_file: projects/ouroboros/rules/E-09.md
test_file: tests/csim/test_E09_S068_written_from_fragments_never_the_same_twice.py
expected_lines: 48
max_wall_minutes: 45
---

## Brief for DeepSeek

Quoted verbatim from docs/bible/epics/E-09-chronicle.md (### S-068 — Written from fragments, never the same twice):

- R-068-07  Given the finished entries in order, When two entries share 40 percent or more of their content words (relative to the shorter), Then the later one is dropped; the first always survives.
- R-068-08  Given the assembler seed equals the jump's start tick, When run twice on the same clusters, Then the text is identical.

## Header slice

(run card_slice.py --write after the skeleton lands)
