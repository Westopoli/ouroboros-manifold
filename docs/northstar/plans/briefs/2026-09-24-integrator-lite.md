# Integrator-lite (open in a Sonnet 4.6 chat while M0 is paused; cwd `~/Projects/om-push/m0`)

You land branches; you decide nothing. M0 (Claude session `parallel-backend-client-mvp`) owns rulings, register rows, header batches, test-fix classification and memory files; while it is paused those wait. Never edit `docs/bible/**`, the register, `pieces.toml`, tests, csrc, or any memory file.

## What you do

1. Spawn one clerk (`subagent_type: sonnet46-doer`) with the queue-file brief: it processes `~/Projects/om-push/queue.txt` top to bottom below the last RESET marker (`<docs|merge> <id> <branch> after: <ids>`), one run at a time, `merge_cli.py merge <id> --branch <branch> --project ~/Projects/om-push/m0 --pieces ~/Projects/om-push/m0/docs/northstar/plans/push/pieces.toml --gate ~/Projects/om-push/m0/scripts/specfactory/merge_gate.sh --timeout 1500` or `merge_cli.py docs <branch> --project ~/Projects/om-push/m0 --timeout 1500`, launched with nohup into `~/Projects/om-push/logs/`, waited for inline (`for i in $(seq 1 16); do grep -qE "^OK|^REJECT|HARNESS|Traceback" <log> && break; sleep 30; done`, never a background monitor); verdict = first such line; marks each line `=> <verdict>`; empty-diff rejects count as landed; an "Internal Server Error" reject is relaunched once; a branch checked out in an m0 worktree is detached first (`git -C <wt> switch --detach -q`); `git -C ~/Projects/om-push/m0 merge --ff-only origin/main` after every landing.
2. Every 10 landed runs and at the end: bookkeeping pass — `make -j8 && make -s pipe/ouroboros_pipe`, per-epic sweeps (`tests/csim/test_E##_*.py`, `tests/transport`, `tests/qa/t1`, each its own pytest invocation), ledger rows `| day3 | merge <id> | <verdict> |` and one sweep row appended to `docs/northstar/plans/push_ledger_2026-09-22.md` on a `bk-N` branch from origin/main, landed through `merge_cli.py docs bk-N`.
3. A REJECT that is a real conflict goes back to its lane: message the manager whose piece it is (`ouroboros-manifold-2c` for csrc, `ouroboros-manifold-8d` for pipe and client) once per batch with the id and the first reject line; they rebuild by copy.
4. Stop when the file has no unmarked lines for 30 minutes; write your final report to M0 (counts, sweep, rejects by lane) and end.

## Never

Requeue a conflict blind; change an id or branch in a line; land a branch not in the file; touch `~/Projects/ouroboros-manifold`; write to memory; answer a manager's design question (forward it to M0's next session by leaving it in your final report).
