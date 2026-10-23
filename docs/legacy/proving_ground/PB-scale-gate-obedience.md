# Probe B — Scale gate obedience

**Proves.** The loop treats a perf threshold as a real failure and keeps iterating past a green-but-slow solution.

**Fixture.** `~/Projects/agora-proving-ground`/probe_b: `neighbors.h` (`nb_count_pairs_within`), `neighbors.c` stub, `reference/neighbors_naive.c` (O(n²), correct, slow), `reference/neighbors_ref.c` (uniform grid), `tests/test_neighbors.py` (11 tests, fenced; perf gate n=50,000, r=5, under 50 ms, min of 3 runs).

**Planted condition.** Card prose nudges toward comparing every pair.

**Agora task.** `agora/queue/102-probe-b-neighbors.md`. Budget 8 iterations, 60 min.

**Pass criterion.** 11 passed; the run log shows at least one attempt that passed correctness and failed only the perf gate before the final green; perf test untouched.

**Fail-look-fors.** Worker declares done at 10/11; worker edits the threshold (fence red); planner splits the perf test into its own subtask and drops it.

**Controls.** Reference: 11 passed at 1.8 ms. Naive: 10 passed, perf gate failed at 408–443 ms (8x over). Margins measured on this machine.

**If it fails.** Tighten the card so the perf test is named explicitly, or raise n. Record.

**Result 2026-09-10, run 1 (build loop, card 108).** Inconclusive for the stated claim: with DeepSeek authoring the brief from the header and tests, the naive nudge in the card is overridden and the brief goes straight to a spatial hash grid. The workers then failed the grid's pair de-duplication and the inclusive distance comparison (best 4/11 over 12 candidates, two hints, no reset). Two consequences for the plan: the obedience claim needs the naive brief forced (`build.py --brief-file`) so a green-but-slow candidate actually appears; and the brief prompt should ask DeepSeek for the simplest algorithm that meets the gate, since a dense grid with counting sort passes at 1.8 ms and is far easier for an 8B–30B worker than a hashed bucket list.

**Result 2026-09-10, runs 2 and 3 (naive brief forced).** Run 2: twelve green-but-slow candidates, none accepted; DeepSeek's single reset restated the naive loop and its correct grid reset was refused by the reset cap. Plan fix: `MAX_RESETS` 1 → 2, `MAX_INTERVENTIONS` 2 → 3, intervene prompt treats a red timing test as a wrong-algorithm signal. Run 3: pass at candidate 9 via a sort-by-x sweep that `gpt-oss:20b` produced on its own after eight naive rejections. The gate half of the claim is proven twice; the steering half is proven by the ladder, not yet by the driver.

