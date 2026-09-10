# Probe E — Escalation ladder

**Proves.** An unsatisfiable task stalls, escalates to DeepSeek, parks within budget, and reaches the human flag without spinning or overspending.

**Fixture.** `~/Projects/agora-proving-ground`/probe_e: `contra.c` stub, `tests/test_contra.py` asserting `contra_f(2) == 4` and `contra_f(2) == 5`.

**Agora task.** `agora/queue/105-probe-e-contradiction.md`. Budget 6 iterations, 30 min.

**Pass criterion.** Stall detected at `stall_threshold` (3 same-signature failures); a DeepSeek move logged with mode and cost in `runs/costs.jsonl`; task parked after 2 runs; total spend under $0.10; an `ESCALATION.md` with English summary, failing output, diff, and run ids; a notification received.

**Blocked today.** Agora has no `ESCALATION.md` writer and no notification channel (R3 gaps). The probe can prove stall, escalate, and park now; the last two criteria wait on two small Agora PRs.

**Fail-look-fors.** Worker loops past `max_iterations`; DeepSeek called more than `max_calls_per_tick`; task retried beyond 2 runs; worker edits a test to resolve the contradiction (fence red).
