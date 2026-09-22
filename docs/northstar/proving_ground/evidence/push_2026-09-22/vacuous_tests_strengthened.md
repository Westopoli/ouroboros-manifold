## Vacuous-pass strengthening — 44 class (a) rows from stub_green_audit.md

Source: `docs/northstar/proving_ground/evidence/push_2026-09-22/stub_green_audit.md`. Rule: fix ADDS an
assertion/precondition that makes the test fail on the current STUB build for its own rule's reason;
never removes/weakens an existing assertion; rule id and test name kept; numbers taken from
`csrc/ouroboros_sim.h` / `docs/bible/epics/E-*.md` / `docs/bible/algorithms.md`, never invented.

Per row: file, edit, assert-count before -> after, new failure line. Rows skipped listed at the end.

### E-06

| Test | Edit | asserts before -> after | New failure |
|---|---|---|---|
| `test_E06_S042_three_ways_to_feel_about_a_neighbor.py::test_R_042_01_it_exactly_one_hostile_neutral` | added `assert s01 == OMStance.NEUTRAL` (DEFAULT/DEFAULT not in R-042-05 override table) | 32 -> 33 | `AssertionError: DEFAULT/DEFAULT pair not in the hostile-override table must be neutral` / `assert 0 == 1` |
| `test_E06_S042_three_ways_to_feel_about_a_neighbor.py::test_R_042_06_it_hostile_toward_every_existing` | pre-set stance(0,2) and (1,2) to COOPERATIVE before `om_faction_create_breakaway` | 32 -> 33 (net; no new assert line, added 2 preconditions) | `assert 2 == 0` (stance stays COOPERATIVE, stub never flips to HOSTILE=0) |
| `test_E06_S043_peace_grows_out_of_quiet.py::test_R_043_06_pair_stays_neutral_counter_resets` | added round-trip `assert lib.om_faction_stance_counter(w,0,1) == 80` right after the setter call | 16 -> 17 | `assert 0 == 80` |
| `test_E06_S045_a_faction_s_technology_is_one_number.py::test_R_045_06_it_equals_parent_s_tech` | added `assert breakaway_fid != 0` before reading its tech | 14 -> 15 | `AssertionError: breakaway id must differ from parent id 0` / `assert 0 != 0` |

