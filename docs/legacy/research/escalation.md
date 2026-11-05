# R3 — Escalation and the Claude Flag

What happens when the local model is stuck, when DeepSeek cannot unstick it, and when the whole loop is making things worse. Feeds Stage 0 probe E and Stage 4's escalation ladder.

## Decided

- Flag file plus evidence bundle, read by Westley when he opens a chat. No unattended Claude (Agora decision D16).
- A pinned-chat `/loop` watcher is documented as an opt-in mode, off by default.

## Questions to answer

1. **Spiral signals.** Concrete, measurable signs the loop is making things worse: test pass count decreasing across attempts, diff churn on the same file, the same finding fingerprint recurring N times, DeepSeek budget burn rate, verify lanes red after a "fix". Thresholds, sourced from `~/Projects/agora/runs/metrics.jsonl` and `campaigns/*/assertions/`.
2. **Flag file spec.** `docs/northstar/ESCALATION.md` layout: English summary of the problem in three sentences, what was tried, failing test output, the diff, run ids, seed and replay command, screenshots if T2, last lessons injected. Written by Agora, never edited by hand.
3. **Notification.** ntfy, email, or Tailscale push from forge with zero unattended Claude. Which one probe E validates.
4. **Start-over protocol.** The defined steps: discard the `agora/` branch, restore the task to the queue with a new spec, record the reason in the lessons inbox. Respec template.
5. **Opt-in loop watcher.** How a pinned chat would poll the flag (interval, estimated subscription usage per day), what it may do without Westley (read and summarize) and may not (apply diffs, respec tasks).
6. **Agora changes required.** Listed as Agora PRs: spiral detector in `driver.py` or `next.py`, flag writer, notification hook, fences for `docs/northstar/`, `docs/bible/`, and `tests/`.

## Spike proof (gates Stage 0 probe E)

A deliberately unsatisfiable task reaches the flag file within budget and the notification arrives. Record the run id here.

## Findings

(empty until the Research Lane fills it)
