# Credits runs, 2026-10-21

Console credits, tools from `scripts/specfactory/` (README_credits.md). Keys never printed or exported.

Running total (Dispatcher runs through batch 8 $1.44 + Architect runs through the SHOWCASE scan $1.66 + $13.70 base): $16.80 of $200; hard stop $190; expires 2026-10-24.
Metering rule: DEC-credits-2026-10-22 (decisions.md); one row per run below, estimate before, actual after.

## SDK runs (from 2026-10-22)

| Date | Purpose | Model | Cap | Actual | Report |
|---|---|---|---|---|---|
| 2026-10-22 | provscope script follow-up (PARA re-quote, C235-fail, bullets 57-60) | claude-sonnet-5-5 | $5 | $0.238 | 16 turns, success |
| 2026-10-22 | venv-link script re-check against main 5cc2e60e | claude-sonnet-5-5 | $5 | $0.278 | 17 turns, success; NOT READY: stale text |
| 2026-10-22 | venv-link script stale-text fixes | claude-sonnet-5-5 | $5 | $0.261 | 14 turns, success |
| 2026-10-22 | provscope final check (NOT READY: one comment cite) | claude-sonnet-5-5 | $5 | $0.234 | 18 turns, success |
| 2026-10-22 | (Architect) records clerk "land era named Greek, Q-147-01 closed", pushed c39f475f | claude-sonnet-5-5 | $5 | $0.140 | 8 turns, success |
| 2026-10-22 | (Architect) scout "unit icons and camera ladder in the 3D ground" | claude-sonnet-5-5 | $3 | $0.168 | 11 turns, success |
| 2026-10-22 | (Architect) records clerk "S-132 approved, FINDING-s132-body-clip, VG-C-unit-ground-fit row", pushed 9ddda023 | claude-sonnet-5-5 | $5 | $0.225 | 13 turns, success |
| 2026-10-22 | (Architect) records clerk "S-001 rejected, two findings, DEC-S001-facing-arrow and -no-layer-ring-land", pushed c764d7af | claude-sonnet-5-5 | $5 | $0.133 | 7 turns, success |
| 2026-10-22 | (Architect) scout "S-001 frame elements in code" | claude-sonnet-5-5 | $3 | $0.170 | 12 turns, success |
| 2026-10-22 | (Architect) records clerk "lane C paragraphs VG-C-land-marks, VG-C-facing-arrow, PROTO-ground-relief", pushed bdbe896f | claude-sonnet-5-5 | $5 | $0.187 | 10 turns, success |
| 2026-10-22 | records batch 7 (scripts, LAB-REV2 owns, credits rows) | claude-sonnet-5-5 | $5 | $0.195 | 14 turns, success |
| 2026-10-22 | records batch 7b (venvlink syntax, owner edges, credits row) | claude-sonnet-5-5 | $5 | (pending, this run) | |
| 2026-10-22 | records batch 8 (venv-link syntax, revert LAB-REV2 edges, VG-C7) | claude-sonnet-5-5 | $5 | $0.234 | 18 turns, success |
| 2026-10-22 | (Architect) records clerk "S-005 verdict flipped to rejected", pushed dbeefd25 | claude-sonnet-5-5 | $5 | $0.111 | 6 turns, success |
| 2026-10-22 | (Architect) engineer "secrets and personal-data scan of git history (SHOWCASE lane)" | claude-sonnet-5-5 | $5 | $0.162 | 9 turns, success |
| 2026-10-22 | records batch 9 (HARNESS-record-files paragraph and row, credits rows) | claude-sonnet-5-5 | $5 | (pending, this run) | |

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
