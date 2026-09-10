# Probe F — Change protocol mid-run

**Proves.** A requirement change re-runs cleanly: old branch discarded, new acceptance picked up, green again.

**Fixture.** Probe A after it has passed. `probe_f/apply_v2.sh` raises the economy floor 8.0 → 10.0 in `toy_drift.h` and the fenced tests, commits.

**Agora task.** `agora/queue/106-probe-f-toy-drift-v2.md`. Budget 6 iterations, 30 min.

**Pass criterion.** Card 106 green; diff touches only `probe_a/toy_drift.c`; floor clamp test at 10.2 passes; the card-101 worktree branch is not reused.

**Fail-look-fors.** Worker hardcodes 10.0 instead of using the header constant (passes now, breaks the next change; inspect the diff); Agora re-runs card 101 instead of 106.
