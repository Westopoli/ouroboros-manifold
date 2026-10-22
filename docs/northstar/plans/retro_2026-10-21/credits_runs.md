# Credits runs, 2026-10-21

Console credits, tools from `scripts/specfactory/` (README_credits.md). Keys never printed or exported.

Running total (actual, batch and SDK): $13.70 of $200; hard stop $190; expires 2026-10-24.
Metering rule: DEC-credits-2026-10-22 (decisions.md); one row per run below, estimate before, actual after.

## SDK runs (from 2026-10-22)

| Date | Purpose | Model | Cap | Actual | Report |
|---|---|---|---|---|---|

## Batches (submitted 2026-10-21 22:11:58Z to 22:12:17Z)

| Job | Batch id | Model | Requests | Estimate (ceiling, batch rates) | State | Actual at batch rates |
|---|---|---|---|---|---|---|
| audit-epics, 22 epics x 3 samples | msgbatch_01Hh4pu5oK7rsts75i3hX1p3 | claude-fable-5-1 | 66 (0 skipped) | ~$16.28 (input ~616k tok $3.08, output at most 528k tok $13.20) | ended, fetched at the first poll (22:18Z), 66 succeeded | $11.31 (in 942,674 tok, out 263,930 tok) |
| story-reviews | msgbatch_01Ts2W8PDVQdfMa3KuGdZX8o | claude-sonnet-5-5 | 34 (16 skipped at build, no story id or no state json) | ~$1.32 (input ~1.06M tok, output at most 51k tok) | ended, fetched at the first poll (22:18Z), 34 succeeded | $2.20 (in 2,111,611 tok, out 17,483 tok) |

The shots' input estimate was a floor, as the README says: actual input was twice the estimate, so the stories batch cost $0.88 over its estimate.
Digests: `epics_audit_digest.md`, `story_reviews_digest.md` (same directory). Out dirs: `~/Projects/om-push/tmp-arch/batch-epics`, `batch-stories` (not committed).

Story reviews: 2 yes, 9 no, 23 unclear.

## SDK engineer trial (spec stand-ins)

Worktree `wt/sdk-trial-standins` at origin/main 410990f3, brief `tmp-arch/sdk_brief_standins.md`, claude-sonnet-5-5, caps $5 and 40 turns.
Result: success, 10 turns, $0.183 (SDK client-side estimate), about 51 s. `standins_batch_1.md` written with 30 rows; copied here as `standins_batch_1_proposals.md`. The agent rates only one row high confidence (it did not grep to verify its file:line cites), so the table is a start for a clerk, not an edit list.
