# PX-07 — Whole-suite regression after DONE (proving the factory)

Run 2026-09-21. Claim (`docs/northstar/PLAN.md`, "The Factory" > "Gates"): whole-suite regression after every DONE, with revert on any new failure. Prototype module `scripts/specfactory/suite_regression.py`, tests `tests/specfactory/test_suite_regression.py` (7 new). Evidence: `docs/northstar/proving_ground/evidence/px07/`.

Result: **pass, with one correction to the incident record itself.** The whole-suite gate rejects the known-bad merge and accepts the known-good repair, as designed. But direct replay shows `test_R_034_06_it_excluded` was already red one card before card 203b1 — `DECISIONS.md`'s account of which card broke it is wrong — and the tool's correct red-after-green-before semantics therefore do not name that test as a "new" failure for 203b1's diff, the way the brief expected. The gate still catches a real new regression 203b1 introduces (`test_R_034_03_factor_one_0_80_tension`, plus a positive control), so the pass criterion "known-bad merge rejected" holds; the specific test named in the brief does not hold under a strict definition, and that discrepancy is the finding worth having.

## Correction to the incident record

`docs/northstar/research/harness_defects_2026-09-17/DECISIONS.md:15` states `test_R_034_06_it_excluded` "passes at `c4596ed` and `4cef8e5` and fails at `718e0fd`." Direct replay in fresh worktrees:

- `c4596ed` (203a1 DONE): `python -m pytest tests/csim/test_E05_S034_who_looks_worth_taking.py::test_R_034_05_it_scored_once tests/csim/test_E05_S034_who_looks_worth_taking.py::test_R_034_06_it_excluded` → **2 passed**.
- `4cef8e5` (203a2 DONE, one commit later): same command → **1 failed** (`test_R_034_06_it_excluded`), reproduced independently in two separate worktrees.
- `git diff c4596ed 4cef8e5 -- csrc/` shows card 203a2's own candidate rewrote `om_faction_candidates` and dropped the two-sided stance check card 203a1 had written (`if (stance_from == OM_STANCE_NEUTRAL || ... ) continue;` is present in the `c4596ed` body and absent in the `4cef8e5` body).

So the regression that broke `test_R_034_06_it_excluded` landed with card **203a2**, not 203b1. Both cards share `snippet_file: csrc/agent.c` and both edit `om_faction_candidates` (confirmed from the queue cards at `~/Projects/agora/queue/203a1-e05-candidate-enumeration.md`, `203a2-e05-candidate-scoring.md`, `203b1-e05-viability-scoring.md`) — 203b1 inherited an already-broken test, it did not break it itself. `git diff --stat 4cef8e5 718e0fd -- csrc/` confirms this brief's diff scope: only `csrc/agent.c` changed in that range (not `csrc/faction.c`, which the brief guessed; the file that actually owns `om_faction_candidates` is `csrc/agent.c` throughout — flagging the brief's file-name guess as wrong per its own instruction to note drifted facts).

## The tool

`scripts/specfactory/suite_regression.py`: `whole_suite_regression(worktree, diff_text)` records the failing-id set of `tests/csim` before applying a diff, applies it (`git apply`), records the failing-id set after, and reports `new_failures = after_failing - before_failing` (strict red-after-AND-green-before; a test already red before the diff is never counted as new even if it stays red). `predecessor_only_regression(worktree, diff_text, predecessor_tests)` mirrors Agora's real gate (`~/Projects/agora/scripts/build.py:514-556` `predecessor_checks`, `:955-999` `finalize_pass`, both confirmed at those exact line numbers): re-run only a given list of tests after the diff, accept iff none fail. `predecessor_tests` is supplied by the caller — recovering "which DONE cards shared this snippet_file at this historical instant" is a replay-time judgment call, documented below, not something the module infers.

`tests/specfactory/test_suite_regression.py` proves the diffing logic on a synthetic two-file git repo before trusting it on the real replay (never touches `tests/csim` or `csrc/`): a bad diff that breaks a previously-green test is named in `new_failures` and rejected (positive control); a diff that changes nothing the tests exercise is accepted with an empty new-failure set (negative control); a test already red before the diff is never counted as new (proves the tool isn't just "any failure present"); and a synthetic analogue of the real predecessor-only gap — a predecessor-only rule that doesn't own the broken test accepts (misses) while whole-suite correctly rejects the same diff, and the same rule *does* reject when it owns the broken test (proves the miss is about test ownership, not a broken implementation). One defect found and fixed while building the fixture: two before/after pytest subprocess runs of a plain `.py` module can hit a stale `__pycache__` `.pyc` when the changed line is the same byte length (found empirically, `PYTHONDONTWRITEBYTECODE=1` fixes it) — this doesn't affect the real replay, which recompiles a C `.so` via `make`, not Python bytecode caching.

```
$ python -m pytest -q -p no:cacheprovider tests/specfactory/test_suite_regression.py
7 passed in 1.86s
```

## Replay 1 — known-bad merge (203b1)

Worktree at `4cef8e5`. Candidate diff = `git diff 4cef8e5 718e0fd -- csrc/` (`docs/northstar/proving_ground/evidence/px07/case1.diff`, confirmed single-file: `csrc/agent.c` only, `181 insertions(+), 59 deletions(-)`).

```
whole-suite: before 71p/598f (32.83s) -> after 79p/590f (33.29s)
new failures:
  tests/csim/controls/test_control_e05_entrench_current_tick.py::test_control_entrench_current_tick_trips_the_detector
  tests/csim/test_E05_S034_who_looks_worth_taking.py::test_R_034_03_factor_one_0_80_tension
accept: False
```

The 598/590 pre-existing failure counts are E-06..E-17 placeholder skeletons naming library symbols that don't exist yet at this commit (same class PX-15 found: not real regressions, just an unbuilt-epic backdrop that cancels out of the set difference). `test_R_034_06_it_excluded` does **not** appear in `new_failures` — it's red in both the before and after runs (see correction above), so it is correctly excluded by the tool's own red-after-green-before rule, not a tool bug. The gate still **rejects** the merge (`accept: False`) on the genuine new regression 203b1 introduces, `test_R_034_03_factor_one_0_80_tension`, plus a positive control it kills. Pass criterion "known-bad merge rejected" holds; the specific test the brief names does not appear in the set, for the reason given above.

## Replay 2 — known-good repair (203c), negative control

Worktree at `79e5c65^` (`9b524b3`, the commit immediately before 203c). Candidate diff = `git diff 79e5c65^ 79e5c65 -- csrc/`, single-file (`csrc/agent.c`, `70 insertions(+), 34 deletions(-)`).

```
whole-suite: before 79p/590f (34.97s) -> after 81p/588f (32.91s)
new failures: none
accept: True
```

Clean negative control, matching the pass criterion exactly.

## Replay 3 — predecessor-only rule over the same diff as Replay 1

Predecessor set = the acceptance tests of the two DONE cards sharing `snippet_file: csrc/agent.c` at the time 203b1 finalized (per the run order in `DECISIONS.md`'s "Overnight result" — 203a1 DONE, then 203a2 DONE, then 203b1 DONE): 203a1's `test_R_034_05_it_scored_once`, `test_R_034_06_it_excluded`; 203a2's `test_R_034_01_weakness_0_70_value_36`, `test_R_034_02_score_0_25_0_70`. Chose this over calling Agora's own `predecessor_checks` directly, to avoid running any part of the live dispatcher against this repo.

```
predecessor-only: 1 failed of 4 tests (0.21s)
failing: test_R_034_06_it_excluded
accept: False
```

Mechanically, the predecessor-only rule **does reject** this specific diff — but only because `test_R_034_06_it_excluded` was already broken by 203a2 (see correction above), not because it catches anything 203b1 itself introduced. Two things follow from that:

1. **If the predecessor-only gate had existed continuously since 203a1**, it would have caught this regression class at 203a2's own finalize (203a2 is itself a predecessor-sharing-`snippet_file` case relative to 203a1) — one card earlier than the incident reached, and before `4cef8e5` would ever have been allowed to merge un-repaired. Confirmed by running the same two 203a1 tests directly against `4cef8e5` in isolation: 1 failed (`test_R_034_06_it_excluded`), same result as at HEAD-of-diff.
2. **The regression 203b1 does introduce** (`test_R_034_03_factor_one_0_80_tension`) is **not** in the predecessor-only set at all — `test_R_034_03` was unowned by any card's acceptance at this point in the chain (`DECISIONS.md`'s Q3: "Tests no card owned (R-034-03, 04, 07)... card 203d for 03 and 04"). Predecessor-only cannot catch a regression in a test no DONE card's acceptance list happens to include; whole-suite catches it because it looks at the entire suite, not a per-card ownership list. This is the real, structural gap the brief asked to find, even though the specific replayed diff obscures it behind the already-broken 203a2 test.

Net: predecessor-only is not useless (it would have caught the 203a2-class break, had it existed then), but it is not a substitute for whole-suite regression — it structurally cannot see a regression that lands in a test no DONE predecessor owns, which is exactly the R-034-03 case documented in the real incident.

## Measure

HEAD (`98057d2`): 676 tests collected, whole `tests/csim` run **31.98s** wall (`563 failed, 108 passed, 4 skipped, 1 xfailed`), single process, `-p no:cacheprovider`. Well under the brief's 120s flag threshold; no finding to raise about gate placement on time alone. `pytest-xdist` is **not installed** in `~/Projects/agora/.venv` (`pip show` fails with `No module named pip`; `importlib.metadata` confirms no distribution present) — not installed per instructions, so no `-n auto` number exists to report.

## Design consequences

1. Whole-suite regression, as specified, is adopted on this evidence: it correctly rejects the known-bad merge and accepts the known-good repair, and at ~32s for 676 tests it is cheap enough to run after every DONE without threatening the CPU-slot budget PX-15 and PX-06 established (241ms/control, 50-95s/mutation pass).
2. The predecessor-only rule (build.py's real, already-implemented Q1 fix) is a strict subset of whole-suite: it only sees regressions in tests some DONE predecessor's acceptance list already names. Whole-suite is not redundant with it — replay 3's R-034-03 case is a real instance of the gap, not a hypothetical.
3. `DECISIONS.md:15`'s incident narrative needs a correction: the stance-exclusion regression originated at card 203a2 (`4cef8e5`), not 203b1 (`718e0fd`). This doesn't change the Q1/Q2/Q3 decisions taken (203c repaired the right function; 203d covered the right tests), but it does mean the predecessor-only gate, once live, would have caught this specific class of break earlier in the chain than the incident record credits it for.

4. Filled by the design lane, 2026-09-21: the gate compares the exact failing-id set, not counts, and records the first assertion line per failing test so a change in how a red test fails is visible (audit item 8). `DECISIONS.md:15` is corrected in the same commit as this note. An incident row that becomes a prototype fixture is replay-verified first; a doc claim is not evidence.