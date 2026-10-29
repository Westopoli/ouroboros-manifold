# Brief: records clerk, RECORDS-mm-1 (Phase 2, runs in parallel with the builders)

Model: claude-sonnet-5-5 (engineer). No sub-agents. Terse thinking, one final report, first line `RESULT success|stop:<reason>`. Worktree under `~/Projects/om-push/wt/` from origin/main; never the live checkout. Records only, no code, no tests. Push under `flock -w 1800 ~/Projects/om-push/records.lock` after `status_check.py`, `owner_lint.py` and `pieces.py --check` are clean (DEC-records-lock-2026-10-23).

1. `docs/northstar/plans/push/pieces.toml`: every row whose `status` is not the dict form `{ state = "<attached|queued|superseded|landed|pending>" ... }` (40 rows, spec G17 M19b) becomes that form. Rule: if the row's acceptance tests exist on origin/main and its owned files' last change is on origin/main, `attached` with `attach_sha` = the first-parent commit on origin/main that last touched its first owned file; otherwise `queued`. Never change a row that already has the dict form. List every row you changed with the evidence (test path exists, sha).
2. Add `contract = true` to the rows that own `csrc/ouroboros_sim.h`, `csrc/signatures.toml`, the pipe-frame section of `docs/architecture.md`, or a save-format file (grep `owns` for those paths); list them.
3. `scripts/specfactory/rule_pins.toml`: one entry per new sentence in spec.md "Rule-text diffs", pinned to the file and the sentence as the spec gives it (pattern: existing entries; `rule_pins.py check` must stay clean, the sentences are not on main yet so pin with the `pending` form the file documents, or if none exists, stop with `RESULT stop:spec` and say so).
4. `docs/northstar/plans/push/gate_runs.csv`: the header line only, columns exactly as spec.md "Design" item 1.
5. Ledger row `RECORDS-mm-1` naming every change; `pieces.toml` attach flip for RECORDS-mm-1 itself.
Report: the sha on main, the row count changed in step 1, the contract ids, the pin count, the status_check line.
