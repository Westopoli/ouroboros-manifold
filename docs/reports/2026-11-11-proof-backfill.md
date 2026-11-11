# Proof backfill and the proof bill (2026-11-11)

Requested by Westley: every built rule points at the test that enforces it (H-089, H-090), and what that costs for lab stage 4. Fifteen read-only Sonnet agents read all 22 epics against the six qualifications of `docs/method/requirements.md` Proof; four more audited the stage 4 rules in depth. The Proof lines are now in the epic files. Evidence is in `2026-11-11-proof-backfill/`: `all.csv` (one row per rule: proof, candidate test, the qualifications it fails, evidence), `totals.md`, `conflicts.md`, the stage 4 audits `stage4/C1.md` to `C4.md`, and the scripts that built and applied it.

Read at the tip that landed as `53f6b053`. The agents read tests; they did not run them, except where this page says a suite was run.

## The count

| | Rules and Invariants | Share |
|---|---|---|
| All | 1,314 (1,192 rules, 122 Invariants) | |
| Proven: a test meets all six qualifications | 15 | 1% |
| MISSING: code exists, no test qualifies | 920 | 70% |
| unbuilt | 379 | 29% |

40 of the MISSING rows are uncertain whether code exists (`MISSING?` in `all.csv`). No Invariant of any epic is named by any test.

Why the 920 fail (each row in one group):

| Reason | Rows |
|---|---|
| No test names the rule | 158 |
| Not run in the shipped setup, or a never/always rule with no every-tick check | 183 |
| Only missing a record that it fails against wrong code | 221 |
| Only wording: the test does not quote the rule's current text | 27 |
| Wording and the missing record | 38 |
| Several reasons | 253 |
| Uncertain | 40 |

Only 3 tests record the line they failed on before the code existed, so counting "written failing first" as proof would rescue 3 rows, not 221.

## Stage 4

165 rules and Invariants that the stage 4 fights depend on: 4 proven, 135 weak, 9 with no test, 17 unbuilt.

| Slice | Rules | Proven | Weak | No test | Unbuilt |
|---|---|---|---|---|---|
| Engage and fire | 45 | 0 | 38 | 1 | 6 |
| Sight | 31 | 1 | 21 | 3 | 6 |
| Movement and orders | 50 | 0 | 45 | 1 | 4 |
| Layers, reach, obstacles | 39 | 3 | 31 | 4 | 1 |

The cheapest route for stage 4 is the lab's whole-run checker: one predicate per never/always rule proves it in the shipped setup in every lab fight. Round 1 gave it seven rules; Round 2 adds nearest-at-pick, fire only at what the side sees, the guard radius, slant range, and narrows two checks that over- and under-reported.

## Findings beyond the count

Reported by the reading agents; the Architect has not confirmed these against the source.

- **Tested, never called.** Functions with passing tests and no caller in the game: about 45 map-generator functions the bible calls "built and tested today" are stubs (E-17 S-114 to S-119); `csrc/layout_engine.c` is in no build target; seven enemy-macro and mission helpers (E-14, E-15); the time-jump length chooser, regional commander assignment and player reassignment record (E-08).
- **Features that do nothing.** Emitting and silent (E-01 R-163-01, R-163-02) ship with multipliers of 1.0.
- **Tests that cannot fail.** Three damage tests pass a hand-typed damage number, so range, cover and elevation never enter; the 0.9 damage-reduction cap cannot trigger; a strategic sight function ignores its viewer; several controls are placeholders that raise "not implemented".
- **Reused or stale ids.** A test proves the old four-doctrines list under R-179-01, which now means something else; R-097-09 is cited for what is now R-207-06; many tests quote superseded rule text.
- **Stories marked Seen with rules the reader found no code for:** R-103-05, R-103-06, R-103-07, R-107-03.
- **Nine tests red on main on no known-red list:** two detector controls in `tests/qa/t1/test_detectors.py`, one case of `tests/qa/test_pipe_abi_check.py`, six in `tests/qa/test_unit_scale_readthrough.py`.
- **156 places** where the bible disagrees with itself, its tests or the code: `conflicts.md`, numbered.

## Proposed changes to the method (Westley's to approve)

1. A seventh qualification: the test reaches the behaviour through the tick, the jump or a pipe handler, or the Proof line names a second test that does.
2. A form of the pointer for client rules: a Godot test is a script, not a named function, so the pointer names the script and the check inside it, and the script quotes the rule at that check.
3. Rules with no testable outcome (six in E-17 S-166) become prose and lose their ids.

## What the bill is, in work

- Break checks for the 221 rows that lack only the record: mechanical, one agent per epic.
- Wording fixes for the 65 rows that lack the quote: mechanical.
- Checker predicates for the never/always rules of stage 4: under way in Round 2.
- New tests for the 158 rules nothing names, as each stage reaches them.
- The 379 unbuilt rules need code first; no test work is owed.
