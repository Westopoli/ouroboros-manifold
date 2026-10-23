# The drift audit (CLAUDE.md guard 7, the semantic half)

Status lives in one place and the bible is rewritten, never appended; the drift audit is how the repo checks that the week's rulings landed everywhere they belong and nowhere they were not asked. It is the third half of guard 7, beside `scripts/specfactory/status_check.py` (mechanical, after every landing) and `scripts/specfactory/method_check.py` (the chat's own method, at every compaction, rules in `method_check.md`). This file is the whole procedure, so it is the same on every machine and in every chat; a chat's memory holds no part of it.

## When

At least weekly, and before any new lane launches after drift was found. The Architect chat spawns it (or the Dispatcher by brief); it never waits for a quiet moment. Record the date of the last run in ROADMAP section 1's programme row or in this file's log below.

Weekly cleanup: the weekly run invokes merge_gate.sh --prune-evidence, which deletes only run directories under MERGE_GATE_EVIDENCE_ROOT (default ~/Projects/om-push/gate-evidence/) older than 7 days (DRAFT-evidence-age); it touches nothing in the repo; the auditor stays read-only for the repo.

## Who

A fresh Sonnet engineer (`subagent_type: engineer`), read-only, that has not seen the author's reasoning. It edits nothing and commits nothing. Its report goes to Westley unedited (quoted in full in the chat, then committed under `docs/northstar/plans/drift_audits/<date>.md`); drift found is fixed before new lanes launch, by the Architect or a clerk, as doc edits with the audit named in the commit.

## Scope

1. **Rulings against every epic they touch.** Every ruling made since the last audit: register rows closed or amended, `R-` rules added, rewritten or retired, `stories.md` status changes, hub changes. Found by `git log --since=<last audit> --format='%h %cs %s' -- docs/bible docs/northstar/ambiguity_register.md docs/northstar/plans` and the diffs. For each: every place the same fact lives (epic rule, epic open-flag lists and header counts, `stories.md` status, register status and answer, hub, `algorithms.md`, other epics that cite the rule) says the same thing. A stale copy, a flag listed open after closing, a rule retired in one place and live in another, two rules with one id, or a malformed register row is DRIFT.
2. **Unasked scope.** Commits since the last audit whose message names no spec row, piece id, `FINDING-`, `TD-` ledger row, `Q-` flag or Westley go line; test files changed with no `TD-` row; cosmetic refactors inside another change. Each is a scope candidate, cited by sha.
3. **The one-status rule.** Every sha the programme lane table cites is on `origin/main` (`git merge-base --is-ancestor`); `status_check.py` tail quoted.
4. **Threshold ownership.** Any number in a rule, test or spec since the last audit that no bible row, Westley line or named `DRAFT-` carries.

## The brief (copy verbatim, fill the dates)

> Model: Sonnet 5.5 (engineer). Read-only drift audit for /Users/westley/ouroboros per `docs/northstar/plans/workflows_2026-10-07/drift_audit.md`. Edit nothing, commit nothing. Scope: rulings made <last audit date> to <today>, unasked scope, the one-status rule, threshold ownership, exactly as that file's "Scope" lists. Method: that file's four steps, with the commands it names. Report once, under 1,500 words, in that file's schema. STOP rules: propose no fixes; read no code beyond what a ruling names; a command that hangs is skipped and named. Exception: after the report, run merge_gate.sh --prune-evidence once; it deletes only run directories under MERGE_GATE_EVIDENCE_ROOT older than 7 days and touches nothing in the repo.

## The schema (the report)

```
DRIFT | <rule, story, flag or sha> | <file:line> | <what differs: both texts, short>
...
SCOPE | <sha> | <message> | <why it looks unasked>
...
STATUS | <status_check.py tail, verbatim>
THRESHOLD | <number> | <file:line> | <no owner found>
COUNT | rulings checked N | drift M | scope K | thresholds T
```

## What is not drift

A ruling recorded in the register and the epic but not yet in a spec that has not been rewritten since (specs are rewritten at their next rev; the register and the epic are the record). A `DRAFT-` number. A "Direction changed, rewrite pending" banner that names the ruling. A test red under a named `TD-` or `FINDING-` row.

## Log

| Date | Range | Found | Fixed in |
|---|---|---|---|
| 2026-10-07 | the first week of the programme | stale status copies (rev 1 retro) | the one-table rule, method rev 2 |
| 2026-10-15 | 2026-10-08 to 10-15 | 15 drift lines, 7 scope candidates (brief then in chat only; this file written 2026-10-18) | `fe5fe84e`, `0f0c6b4b` |
| 2026-10-18 | 2026-10-15 to 10-18 | 13 drift lines (12 stale copies of the 10-15 closings, 3 malformed register rows), 3 scope candidates (all asked, under-cited), 0 threshold violations (`drift_audits/2026-10-18.md`) | the commit after the report |
| 2026-10-23 | 2026-10-18 to 10-23 | 12 drift lines, 6 scope candidates accepted (the Architect's own scope decisions of the week), 1 threshold finding (`drift_audits/2026-10-23.md`) | `44c74a99` |
