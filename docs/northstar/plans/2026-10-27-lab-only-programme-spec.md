# Lab-only programme: what 100% on the simulation lab looks like (spec, not a go)

Architect, 2026-10-27, for Westley. Nothing here is launched. Inputs: three Sonnet audits run today (beta plan, lab plan, token history over 2026-10-13 to 10-26; their reports are quoted below, unedited where numbers appear), `retro_2026-10-24/method_cost.md`, `method_rev3_2026-10-26/spec.md`. Westley's ask: all work on the lab until it is finished; understand how things ran before against how they run under the new harness; the parallelism that stays efficient; token targets per task from history so each day has a planned allotment; and an audit of the two north-star plans for position and completeness.

## 1. How it ran before, and how it runs now

| | Before (2026-10-07 to 10-24, measured) | Now (method rev 3, landed 10-27; Phase 4 fixes in flight) |
|---|---|---|
| Coordinators | Two long chats at once, Fable Architect and Sonnet Dispatcher, both over 200k context per call (median 279k and 228k, p90 605k and 545k), 14 to 26 M tokens per active hour each; 45% of W43's tokens | One Sonnet Dispatcher chat; Fable by brief only; context guard at 400k, compaction at 200k; M08 and M22 count breaches weekly |
| Roles per piece | 6 to 12 runs (spec, tests, audit, build, verify, land, records, ruler), tests plus audit about 70% of a piece's tokens | Four: spec (Sonnet), tests (sim, pipe, lab only), build, land; audit only on a contract spec or the beta list; the clerk rules test-defects and writes the one ledger row |
| Piece size | 100-line cards; median landing 0 product lines over five measurable merges | One responsibility, up to 1,000 lines; M10 floor of 40 product lines per landing |
| Records | 492 ledger rows in W43, 0 gate rows, 40 non-standard status rows; nothing could say what a landing cost | Gate rows (size, time, cause), run rows, `found-by=` and `ruler=` tokens, weekly `method_metrics.py` on a timer, FAILs on Westley's page |
| Launch | 20 of 32 Workflow runs stopped on spec or records gaps | `launch_check.sh` executable pre-flight; Tool line per spec (cascade for sim-side clusters) |
| Gate | 600 s suite timeout under QA load, 5 of 9 rejects were timeouts, 35 to 65 min per run, one lock | 2,400 s, holds the play lock, `suite-timeout` named in the row; still one lock and 35 to 65 min: landings are serial by physics |
| Method edits | 33 method-text commits in W43 without a retro | Only with a retro folder, pinned sentences |

What did not change: the gate is one lock and about an hour; Westley's verdicts serialise look pieces (his rule, kept); the subscription week is the budget.

## 2. The lab's remaining work (from the lab audit, sizes rough)

1. Records fix: `pieces.toml` LAB-REV3-B flip (merged 7dd4d8fc, still `queued`), a REV3-B ledger row, ROADMAP row 71. One records clerk. ~0.3 M tokens.
2. LAB-REV3-C: reach and vision as swept knobs, the paper prediction (positioning-decides in operational form), `no_reach_stall`, per-reach crossings. About 9 files in `scripts/skilllab`. One cascade or one tests-then-build pair. Estimate 15 M (median landed piece), ceiling 50 M.
3. FU-warden-no-stack: `csrc/unit.c`, small; needs Westley's D9 rule. 5 M.
4. Westley's answers: pass marks C0 to C9 and win margin, layer pairs for batch one, go for batch one, speed marks. No tokens; blocks 5.
5. Batch one: the coarse knob batch, 12 workers, under 4 h compute, then the artifact and diagrams, then Architect review. Waiting since 10-22. Compute, not tokens; the review ~10 M.
6. E2 arc and cone, E4 radius guard: two sim pieces in `unit.c` with three test files each; then batch two. 2 × 15 M.
7. R9 sight-engagement (VG-E-sightengage), retire the L8 stand-in. One sim piece, lab test churn. 15 M.
8. Layout run 1 chart and the ground scene batch. Compute plus one chart clerk. 3 M.
9. ALG rows from the batch analysis, close Q-008-03. Records. 1 M.
10. The search (Phase E): no spec, no stop rule, no definition of done. A spec first (Architect, by brief), then pieces; `search.py` exists. Medium to large; unestimated until specced.
11. A definition of "lab finished": the gate for the beta. Nobody has written it. Draft in section 5.

Total before the search, at medians: about 85 M tokens of agent work plus the Dispatcher's hours, roughly one subscription week at the proposed allotment, if nothing is re-done.

## 3. Parallelism that stays efficient

Physical limits: one gate lock (about an hour per landing, so at most 6 to 8 landings in a working day, serial); one Dispatcher chat; Westley's attention for the four answers and batch reviews; the machine's 12 lab workers for batches (a batch and a gate run contend for CPU; the gate holds the play lock, not the batch lock).

Shape that fits the lab (sim-side, no frame, tests run without Godot): a `/manager-mode` cascade per cluster, three to nine file-disjoint leaves on one spec and one umbrella test (the one measured cascade: 9 leaves in 90 minutes), landed as one branch through one gate run. So the unit of parallelism is the cascade, not the piece: 3 to 9 builders in flight, one landing. Items 2, 6 and 7 above are each one cascade (C: 9 files; E2 plus E4: two leaves plus tests; R9: one leaf). Items 1, 8 and 9 are single clerks. Items 4 and 5 are Westley and compute.

Steady state: one cascade building while the previous one lands, one clerk on records in parallel, batches overnight. That is the "at most one build and one landing" rule already in CLAUDE.md, read with a cascade as the build. More than that buys nothing: the gate queue grows and the coordinator's context grows with it (W43's two peak days were exactly that, 154 sub-agents on 10-20 with 1,077 M tokens over two days and little landed).

## 4. Token targets and the daily allotment

Measured (the token audit; totals include cache reads, which are 96% of the volume and cheaper than fresh input, so these are planning units, not dollars):

| Task | Budget (median) | Ceiling (p90) | What blows the ceiling |
|---|---|---|---|
| Tests writer | 3.8 M | 16 M | 124-call writers on a big lab piece; "fix pass" reruns cost a full writer again |
| Builder | 1.2 M | 6.3 M | sweep or batch code in one large file |
| Landing clerk | 1.6 M | 5.5 M | gate waits (93 min wall, 29 active), reruns |
| Records clerk | 0.2 M | 1.2 M | multi-batch records runs |
| Auditor | 4.7 M | 13.8 M | "audit fix passes" (retired by rev 3 except contract specs) |
| Research, drift audit | 1.4 M, 10.9 M | 6.4 M, 15 M | pre-flights that read the whole sim |
| One landed piece (tests plus build) | 15.2 M | 52.7 M | the three dearest were lab pieces: L4 95 M, L2 73 M, L5 53 M; tests plus audit were 70% |
| Coordinator chat | 14 to 26 M per active hour | | context size times calls |

Week and day, observed: W43 1,835 M; the two days that exhausted the week, 10-19 and 10-20, 1,077 M; a light day 20 to 90 M.

Proposed allotment (DRAFT, Westley's numbers): a planned week of 1,000 M raw tokens, 5 days of 200 M with a weekend taper to zero (his DEC-weekend-taper), split per day:
- Dispatcher chat: 40 M (about three active hours at the measured rate; the rest of the day it is idle on notifications).
- Pieces: 120 M (eight median pieces, or two at the ceiling, or one cascade of six leaves with its tests and landing).
- Reserve: 40 M for a rerun, a ruling, a records fix. Unspent reserve does not roll over.

How it is planned and checked:
- The day's plan is a table in the Dispatcher's status file: piece, task type, estimate from the table above, then actual. Written before the first launch, from the estimate table in `method_thresholds.toml` (`[estimates]`, new).
- Actuals come from the transcripts the same way the token audit computed them: one harness piece, HARNESS-mm-12 `token_ledger.py` (about 150 lines, reusing `method_metrics_runs.py`'s loader), prints per day and per piece: planned, actual, over or under, and the week's running total against the allotment. Two new weekly metrics: M25 tokens per landed piece against its estimate (FAIL above the ceiling), M26 week total against the allotment (report only, like M17).
- A piece that passes its ceiling mid-run is stopped by its own brief ("STOP at N calls") and reported, not retried; the Dispatcher's next day plans it smaller or asks for a ruling.
- The estimates are re-fitted monthly from the ledger (the drift auditor's cadence), so the table learns.

What the data cannot give: the subscription's cap in tokens (Anthropic reports a percentage, not a count), and the cache hit rate across sessions. The first live week calibrates the 1,000 M figure against the percentage Westley sees; after that the allotment is in his units.

## 5. The two north-star plans: position and completeness

Position. The beta plan (`~/.claude/plans/cozy-tumbling-pony.md`, 10-06) is held whole in the repo: `plans/2026-10-07-visible-game-programme.md` carries every section plus the lane table; nobody needs the `~/.claude/plans` copy. The lab plan (`lovely-purring-wozniak.md`, 10-13) is held as derivatives: the rev 2 spec supersedes it by its own header, rev 3 has its own plan file, the search exists only as a README line and an unspecced `LAB-SEARCH` row, and no single file links rev 2, rev 3 and the search. Both `~/.claude/plans` files are drafts that stopped being updated the day their repo counterparts were written. Recommendation: a plan of record per north star under `docs/northstar/plans/`, with a status head (state, last landing, what waits on Westley), ROADMAP section 1 pointing at exactly those two files, and `~/.claude/plans` treated as scratch.

Completeness, beta (audit verdict: revise, do not re-plan). The plan is intact; the records around it drifted: no PAUSED marker despite DEC-lab-before-beta; the 10-27 verdicts (sight disc rejected, 2D placeholders, map edge) not in the lane table; `stories.md` still says S-132 Seen against the mixed verdict; the baseline folder the plan required was never committed; lanes W, P, U, V, HARNESS and LAB were built outside the plan's lane list; gate timeouts and the cost retro not in its budget; 8 of 239 stories Seen after 20 days. Seven record fixes, no re-plan, and W8 (still versus pannable scene) answered before any look piece.

Completeness, lab (audit verdict: revise, do not re-plan). Rev 2 landed (43bf9462), rev 3 A landed, rev 3 B merged but recorded as queued, rev 3 C not started, batch one not run since 10-22, E2 and E4 not built, the search unspecced, "finished" undefined. Lessons not fed back: positioning-decides is not in the README's principle or measure (only in rev 3's unbuilt paper prediction); the ten coverage defects are in the rev 3 plan, not the README status; the viewer is unmentioned by the lab; the "tests are weak" audit changed no test rule.

Draft definition of "lab finished" (Westley's to confirm): the five skills each have at least one skilled play with a counter on both labs; batch one and batch two run with the diagrams reviewed; the search reports every region where the firing-count conditions hold for the roster mixes he set; the pass marks are his; the ALG rows for Q-008-03 are written; the README's principle states positioning-decides and its measure matches.

## 6. Recommendation

Step back for one records-and-spec pass before resuming the lab, not a re-plan: (1) the lab plan of record with the status head and the finished definition; (2) the records fixes (B flip, ROADMAP row 71, the beta PAUSED marker and the 10-27 verdicts); (3) Westley's four answers; (4) HARNESS-mm-12 and the `[estimates]` table so the first lab week is planned and measured. Then batch one the first night, and rev 3 C as the first cascade. All records and spec work in this list is Sonnet clerks and the Architect's writing, about 5 M tokens; nothing of it builds the lab.

## 7. What waits on Westley

- The allotment numbers (1,000 M per week, 200 per day, the 40/120/40 split).
- The definition of "lab finished" above.
- The four lab answers (pass marks and margin, layer pairs, batch-one go, speed marks) and the D9 Warden rule.
- W8: still or pannable scene for look verdicts.
- Whether `~/.claude/plans` copies are retired in favour of the plan-of-record files.
