# Proving Ground Scorecard

One row per run. Pass means every criterion in the probe file held.

| Probe | Date | Run id | Result | Iterations | DeepSeek $ | Notes |
|---|---|---|---|---|---|---|
| C | 2026-09-10 | pytest local | pass | n/a | 0 | 20 passed; controls clean on seeds 1–5 |
| D | 2026-09-10 | pytest local (xvfb) | pass | n/a | 0 | software GL; GPU virtual screen not yet exercised |
| A | 2026-09-10 | 101-probe-a-toy-drift-20260910-1521 | fail (harness) | 1/8 | 0 | Planner checks `python3 -m pytest` (no pytest in system python) + invented test ids; exit 1 not 127 so AC-16 fallback never fired; stalled. Worker 9/17 green. Agora fix: missing-module and bad-test-id classify as harness errors. |
| A | 2026-09-10 | 101-probe-a-toy-drift-20260910-1600 | fail (harness) | 8/8 | 0 | Worker switched to qwen3-coder:30b; Ollama 400 "does not support thinking" on every worker call. Agora fix: send `think` only when /api/show lists the capability. |
| A | 2026-09-10 | 101-probe-a-toy-drift-20260910-1606 | fail (harness) | 1/8 | 0 | Fallback fired; then stall signature hashed stderr only (pytest reports on stdout) so 3 differing attempts looked identical; and whole-suite fallback unreachable for subtask 1 of 5. Agora fix: stdout-aware signature + reinterpret planner check under acceptance interpreter. Task parked; escalation flag + ntfy fired (E mechanism live). |
| A | | 103-probe-a-toy-drift-r2 | pending | | | queued after the three fixes |
| B | | | pending | | | card 102 staged, not queued |
| E | 2026-09-10 | 101 park at 16:08 | partial pass | n/a | 0 | Flag `escalations/101-probe-a-toy-drift.md` written once with goal, per-run stall tails, branch and worktree pointers; ntfy sent:200. Still unproven: DeepSeek escalate move on the contradiction fixture (card 105 not run). |
| F | | | pending | | | after A passes |
| G | | | blocked | | | needs director mode + desktop tool |
