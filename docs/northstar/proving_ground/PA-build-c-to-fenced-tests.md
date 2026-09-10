# Probe A — Build C to fenced tests

**Proves.** The local worker can write C against a fenced pytest-via-ctypes suite; the harness and fences hold.

**Fixture.** `~/Projects/agora-proving-ground`/probe_a: `toy_drift.h` (PCG32 RNG + one economy drift equation from `simulation/drift.py`, constants named after `config.py`), `toy_drift.c` stub (compiles, wrong), `reference/toy_drift_ref.c` (green), `tests/test_toy_drift.py` (17 tests, fenced).

**Planted condition.** None. Clean TDD.

**Agora task.** `agora/queue/101-probe-a-toy-drift.md`. Acceptance: pytest on `probe_a/tests`; `git diff --quiet HEAD -- probe_a/tests probe_a/toy_drift.h Makefile conftest.py`. Budget 8 iterations, 60 min.

**Pass criterion.** 17 passed within budget; fence check green; diff touches only `probe_a/toy_drift.c`; worktree branch only.

**Fail-look-fors.** Worker edits tests or header (fence check red); planner lists a test file in a subtask's `files`; MODEL-MISSING; parked after 2 runs.

**Negative control.** `TOY_LIB=ref` runs the same tests against the reference: 17 passed. Stub: 13 failed, 4 passed.

**If it fails.** Inspect `runs/101-probe-a-*/plan-*.json` and worker replies. Likely fixes: card prose (PCG32 details), planner prompt for C, or the worker model tier. Record on the scorecard.
