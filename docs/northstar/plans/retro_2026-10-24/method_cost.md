# Method cost: six hypotheses measured from the records (retro 2026-10-24, internal half)

Window 2026-09-10 to 2026-10-24. Origin/main at 8201a87a. Scripts: /tmp/retro-measure/*.py (h1.py, h2a.py, h2c4.py, asm.py). "Game code" = .c .h .gd .tscn under csrc/ autoload/ scenes/. "Tests" = every file under tests/ (all extensions, goldens included). "northstar" = every file under docs/northstar/.

## H1 Verification tax

### H1a Lines on origin/main at the last commit before each date (`git rev-list -1 --before=<date> origin/main`, `git ls-tree -r`, `git cat-file --batch`; script h1.py)

| Date | Commit | Test lines | Game-code lines | Tests / game | docs/northstar lines |
|---|---|---|---|---|---|
| 2026-09-10 | d355021c | 1402 | 17889 | 0.08 | 0 |
| 2026-09-14 | 5cf1fe68 | 1402 | 17891 | 0.08 | 2436 |
| 2026-09-21 | 0ee67a44 | 30260 | 20810 | 1.45 | 11051 |
| 2026-09-28 | d366a42b | 58521 | 62809 | 0.93 | 150703 |
| 2026-10-05 | ab25d9d3 | 111565 | 70116 | 1.59 | 497327 |
| 2026-10-12 | 5a820fba | 148418 | 85300 | 1.74 | 782098 |
| 2026-10-19 | db03e776 | 158368 | 86659 | 1.83 | 1448762 |
| 2026-10-24 (HEAD) | 8201a87a | 195573 | 87280 | 2.24 | 1393060 |

Growth 2026-09-10 to HEAD: tests +194,171 lines, game code +69,391 lines (same script, same output). Weeks 2026-09-28 to 10-24: game code 62,809 to 87,280 (+24,471) while tests went 58,521 to 195,573 (+137,052).

### H1b Ledger rows by week (file docs/northstar/plans/push_ledger_2026-09-22.md, 1631 rows starting `| day`; week = ISO week of the row's `git blame` author date; script in this session, ids in the appendix)

| ISO week | `day` rows | Rows whose Event cell starts `TD-` and text says test-defect / assumption / rule-changed / stale | Other `TD-` rows (re-record, unrequested, no test-defect found) | Rows with a `FINDING-` id | Rows containing the word "caught" |
|---|---|---|---|---|---|
| 2026-W39 (09-21 to 09-27) | 518 | 0 | 0 | 0 | 2 |
| 2026-W40 (09-28 to 10-04) | 323 | 97 | 23 | 0 | 1 |
| 2026-W41 (10-05 to 10-11) | 116 | 96 | 4 | 5 | 5 |
| 2026-W42 (10-12 to 10-18) | 182 | 34 | 3 | 44 | 0 |
| 2026-W43 (10-19 to 10-24) | 492 | 121 | 23 | 133 | 3 |
| Total | 1631 | 348 | 53 | 182 | 11 |

Rows that name a test catching a real defect before main: not measurable as a count. The ledger has no field for it. Proxies: the word "caught" (11 rows, ids in the appendix; most are test-defect rows, not catches), the word "REJECT" with "real failure" or "real test failure" (0 rows), and `FINDING-` rows (182; these include harness, disk and process findings, so they are an upper bound for test catches). Stage-level gate catches are in H3.

### H1c Programme 2026-10-07 to 10-10 (docs/northstar/plans/retro_2026-10-10/README.md)

| Quote | Line |
|---|---|
| "62 distinct test-defect rulings (TD-VG-*) in three days, every one a Fable ruling with a ledger row" | retro_2026-10-10/README.md:13 |
| "847M raw tokens in the window (93% cache reads); 141M at the CLAUDE.md weighting ... 430 Sonnet agents, median 373k tokens each, p90 1.59M; $1,487 at list prices, of which the two Fable Architect sessions are $1,130 (76%" | retro_2026-10-10/README.md:15 |
| "Tests here were written against spec text and fixture shapes, not the built tree, and were wrong 62 times. Each wrong test stopped a builder and needed a ruling from the most expensive model." | retro_2026-10-10/README.md:33 |
| Programme session: 422 turns, context median 465k, p90 882k, max 964k, about $550. Resumed session: 610 turns, median 319k, p90 682k, max 762k, about $580 | retro_2026-10-10/README.md:44-50 |
| "Judgement work in those turns: 62 test-defect rulings, eight spec revisions, 34 scripts, and about ten cross-cutting diagnoses" | retro_2026-10-10/README.md:52 |

Verdict: supported, because tests grew from 0.08 to 2.24 lines per game-code line (H1a), the ledger holds 348 test-defect rows in five weeks plus 62 in one three-day programme (H1b, H1c); the value side (real defects caught before main) is not measurable, because the ledger has no tests-caught-a-real-defect field.

## H2 Coordination tax

### H2a SDK reports, scratch/drafts-2026-10-22/report_*.md (167 reports, all dated 2026-10-23 or 10-24; cost is the "SDK client-side estimate, not a bill" on the `- success, N turns, $X` line, which is line 4 or 5 of each file; script h2a.py; model column from the report header)

| Piece | Role | Model | Reports | Cost $ | Turns |
|---|---|---|---|---|---|
| (audit) | audit | Fable | 1 | 4.07 | 38 |
| (audit) | audit | Sonnet | 22 | 5.97 | 219 |
| (fable) | architect(Fable) | Fable | 38 | 132.23 | 835 |
| (records batches) | records | Sonnet | 13 | 13.21 | 492 |
| (verify) | verify | Fable | 5 | 1.05 | 50 |
| (verify) | verify | Sonnet | 7 | 1.17 | 55 |
| b25 | landing | Sonnet | 2 | 6.28 | 86 |
| cl | landing | Sonnet | 3 | 0.51 | 5 |
| costreport | builder | Sonnet | 1 | 0.22 | 12 |
| costreport | tests-writer | Sonnet | 1 | 0.43 | 19 |
| ctxguard | builder | Sonnet | 4 | 0.45 | 26 |
| ctxguard | landing | Sonnet | 1 | 0.22 | 5 |
| ctxguard | records | Sonnet | 1 | 0.20 | 12 |
| ctxguard | tests-writer | Sonnet | 1 | 0.21 | 11 |
| ctxguard2 | builder | Sonnet | 2 | 0.13 | 9 |
| ctxguard2 | landing | Sonnet | 1 | 0.18 | 2 |
| ctxguard2 | tests-writer | Sonnet | 2 | 0.16 | 9 |
| diskclean | other | Sonnet | 1 | 0.12 | 12 |
| fst | builder | Sonnet | 1 | 0.41 | 21 |
| fst | tests-writer | Sonnet | 1 | 0.23 | 11 |
| harness-costreport | review | Fable | 1 | 1.87 | 15 |
| harness-flow-spine-teardown | review | Fable | 1 | 1.77 | 16 |
| harness-pieces-cycle | review | Fable | 1 | 1.10 | 9 |
| io | tests-writer | Sonnet | 1 | 0.15 | 8 |
| lakefill | builder | Sonnet | 1 | 0.15 | 11 |
| lakefill | tests-writer | Sonnet | 1 | 0.24 | 12 |
| land3b | landing | Sonnet | 2 | 0.60 | 30 |
| land5 | landing | Sonnet | 1 | 0.37 | 13 |
| lm | builder | Sonnet | 1 | 0.14 | 12 |
| lm | landing | Sonnet | 5 | 1.46 | 19 |
| lm | tests-writer | Sonnet | 1 | 0.18 | 12 |
| pcyc | builder | Sonnet | 1 | 0.22 | 11 |
| pcyc | tests-writer | Sonnet | 1 | 0.21 | 12 |
| pcyc_rerun | other | Sonnet | 1 | 0.10 | 7 |
| proto-lakefill | review | Fable | 1 | 1.34 | 14 |
| qafix | other | Sonnet | 1 | 0.08 | 6 |
| qafix2 | other | Sonnet | 1 | 0.07 | 4 |
| qafix3 | other | Sonnet | 1 | 0.08 | 5 |
| retro | records | Sonnet | 1 | 0.10 | 4 |
| s132_scout | other | Sonnet | 1 | 0.15 | 9 |
| sc-fl2 | other | Sonnet | 1 | 0.20 | 11 |
| sc-qa2 | other | Sonnet | 1 | 0.43 | 19 |
| sd | builder | Sonnet | 4 | 0.92 | 71 |
| sd | landing | Sonnet | 3 | 1.27 | 56 |
| sd | tests-writer | Sonnet | 3 | 0.53 | 35 |
| sdkbuf | builder | Sonnet | 1 | 0.30 | 16 |
| sdkbuf | tests-writer | Sonnet | 1 | 0.18 | 14 |
| tmpclean | other | Sonnet | 1 | 0.07 | 4 |
| vg-a-sightdisc | review | Fable | 1 | 2.05 | 15 |
| vg-b25 | review | Fable | 1 | 2.91 | 18 |
| vg-c-landmarks | review | Fable | 1 | 2.66 | 14 |
| vg-e-facingtravel | review | Fable | 1 | 1.81 | 17 |
| vg-e-idleown | review | Fable | 1 | 2.80 | 29 |
| wtcap | builder | Sonnet | 1 | 0.57 | 19 |
| wtcap | landing | Sonnet | 4 | 0.53 | 17 |
| wtcap | partb | Sonnet | 1 | 0.16 | 12 |
| wtcap | partc | Sonnet | 1 | 0.27 | 18 |
| wtcap | records | Sonnet | 1 | 0.37 | 17 |
| wtcap | tests-writer | Sonnet | 1 | 0.38 | 9 |
| wtcap2 | builder | Sonnet | 1 | 0.09 | 9 |
| wtcap2 | landing | Sonnet | 2 | 0.44 | 9 |
| wtcap2 | tests-writer | Sonnet | 1 | 0.14 | 7 |

Totals by role (all 167 reports):

| Role | Reports | Cost $ | Share of total | Turns |
|---|---|---|---|---|
| architect(Fable) | 38 | 132.23 | 67.1% | 835 |
| review | 9 | 18.31 | 9.3% | 147 |
| records | 16 | 13.88 | 7.0% | 525 |
| landing | 24 | 11.86 | 6.0% | 242 |
| audit | 23 | 10.05 | 5.1% | 257 |
| builder | 18 | 3.60 | 1.8% | 217 |
| tests-writer | 15 | 3.06 | 1.6% | 159 |
| verify | 12 | 2.22 | 1.1% | 105 |
| other | 9 | 1.29 | 0.7% | 77 |
| partc | 1 | 0.27 | 0.1% | 18 |
| partb | 1 | 0.16 | 0.1% | 12 |
| all | 166 | 196.91 | 100% | 2594 |

Per piece, share among the four named roles (tests-writer / builder / landing / records), pieces that have both a tests-writer and a builder report:

| Piece | Sum $ | tests-writer | builder | landing | records | partb+partc |
|---|---|---|---|---|---|---|
| costreport | 0.65 | 66% | 34% | 0% | 0% | 0% |
| ctxguard | 1.09 | 20% | 42% | 20% | 18% | 0% |
| ctxguard2 | 0.47 | 34% | 28% | 37% | 0% | 0% |
| fst | 0.65 | 36% | 64% | 0% | 0% | 0% |
| lakefill | 0.39 | 62% | 38% | 0% | 0% | 0% |
| lm | 1.78 | 10% | 8% | 82% | 0% | 0% |
| pcyc | 0.42 | 49% | 51% | 0% | 0% | 0% |
| sd | 2.72 | 20% | 34% | 47% | 0% | 0% |
| sdkbuf | 0.48 | 38% | 62% | 0% | 0% | 0% |
| wtcap | 2.29 | 17% | 25% | 23% | 16% | 19% |
| wtcap2 | 0.68 | 21% | 13% | 66% | 0% | 0% |

Note: review_push_* reports (role review) and records batches (rec22a to rec29b, role records) are not tied to a piece key; they are in the role totals above. The piece keys land3b, land5, b25, cl, lm, sd are the landing reruns (run1..run5).

### H2b Method weight on origin/main at 8201a87a

| Measure | Number | Source |
|---|---|---|
| Lines under docs/northstar/ | 1,393,060 | h1.py (`git ls-tree -r` + `git cat-file --batch`) |
| Lines of game code (csrc/ autoload/ scenes/) | 87,280 | h1.py |
| Ratio northstar / game code | 15.96 | 1,393,060 / 87,280 |
| Ledger rows | 1631 | `grep -c '^| day' docs/northstar/plans/push_ledger_2026-09-22.md` |
| Pieces in pieces.toml | 306 | `grep -c '^\[\[piece' docs/northstar/plans/push/pieces.toml` |
| Pieces by state | attached 171, queued 89, superseded 3, landed 1, pending 1 (265 of 306 carry an inline `state = "..."`; 40 use another status form, not counted) | `grep -oE 'state = "[a-z-]+"' docs/northstar/plans/push/pieces.toml \| sort \| uniq -c` |

### H2c Non-merge commits on origin/main since 2026-09-10 (3842 commits, all parents, so branch commits count; 1616 merge commits excluded; `git log --since=2026-09-10 --no-merges --name-only`; script h2c4.py)

Classes: product = touches csrc/ autoload/ scenes/; docs-only = every file under docs/; tests-only = touches tests/ and no product; other = scripts/, root files, assets, empty.

| ISO week | product | docs-only | tests-only | other |
|---|---|---|---|---|
| 2026-W37 | 2 | 13 | 0 | 1 |
| 2026-W38 | 58 | 96 | 27 | 22 |
| 2026-W39 | 397 | 256 | 126 | 18 |
| 2026-W40 | 270 | 417 | 312 | 146 |
| 2026-W41 | 196 | 263 | 235 | 62 |
| 2026-W42 | 36 | 202 | 76 | 23 |
| 2026-W43 | 18 | 332 | 169 | 69 |
| Total | 977 | 1579 | 945 | 341 |

Verdict: supported, because the coordination layer outweighs the product in every measure: Fable architect/draft sessions are $132.23 of $196.91 in SDK reports (H2a), docs/northstar is 15.96 times the game code (H2b), and docs-only commits are 1579 against 977 product commits (H2c), with product commits falling from 397 in W39 to 18 in W43.

## H3 Gate tax

Logs: /var/tmp/om-push/*gate*.log (18 files, 2026-10-23 13:42 to 10-24 22:35; no gate logs from before 10-23 survive there; scratch/drafts-2026-10-22/run_*.out hold no `gate rc=` or `GATE ... REJECT` lines: `grep -lE 'gate rc=|GATE .* REJECT' run_*.out` returned nothing). Stage time = sum of the `[N s]` figures in the log; wall and queue come from the `.start` and `.locked` epoch markers and the log mtime, present only for the three newest gates. Rejects counted from `GATE <stage> REJECT` and `PRE_GATE ... REJECT` lines.

| Gate log | Stage minutes | Wall minutes | Queue minutes (start to lock) | Rejects by stage | rc | Cause of the reject |
|---|---|---|---|---|---|---|
| landb25_gate2 | 34.5 | n/a (no markers) | n/a | regression_csim, specfactory_regression | none logged | suite timeout (600 s subprocess.TimeoutExpired in the baseline run) |
| landcl_gate | 27.8 | n/a | n/a | regression_csim, specfactory_regression | none logged | suite timeout (same 600 s TimeoutExpired) |
| landlm_gate3 | 49.7 | n/a | n/a | regression_csim, specfactory_regression, lane_plays | none logged | two suite timeouts; lane_plays: red test_S_088_squads_are_in_the_inventory outside the known-red list (1034.3 s) |
| landsd_gate2 | 51.6 | n/a | n/a | regression_csim, specfactory_regression | none logged | suite timeout (600 s TimeoutExpired, line 49) |
| landsd_gate3 | 52.0 | n/a | n/a | regression_csim, specfactory_regression | none logged | suite timeout (same) |
| landctxguard_gate | 66.1 | 66.1 | 0.0 | none | 0 | pass |
| landctxguard2_gate | 67.1 | 195.1 | 128.0 | none logged | 2 | no REJECT line in the log; cause not in the log |
| landwtcap_gate | 50.8 | n/a | n/a | none | 0 | pass |
| landwtcap2_gate | 64.9 | 117.4 | 52.4 | none | 0 | pass |
| pregate (lf_pregate, pregate, sdkbuf-pregate) | 0.7 | n/a | n/a | noise (asset .import files, 2), gate --revert exit 1 (2), base lacks origin/main (GATE base REJECT, lf_pregate and sdkbuf-pregate); verdict REJECT x3 | n/a | lint/noise and base-sync, before any suite ran |
| landlm_gate, landsd-gate | 0.7 each | n/a | n/a | none | n/a | early stop before the suites (no reject line) |
| landb25_gate2_flock4, landcl_gate2_flock4, landsd_gate3_flock4, landcl_gate2 | 0.0 | n/a | n/a | none | n/a | lock-wait stubs (20 bytes or empty) |

Counts across the 18 logs: suite-timeout rejects 10 stage lines in 5 logs (regression_csim and specfactory_regression in each of landb25_gate2, landcl_gate, landlm_gate3, landsd_gate2, landsd_gate3); real test failure rejects 1 (lane_plays, landlm_gate3); provenance rejects 0; footprint rejects 0; lint/noise rejects 3 (PRE_GATE noise REJECT 2, verdict REJECT 3 over the three pregate logs); base-sync rejects 2 (GATE base REJECT, lf_pregate and sdkbuf-pregate). Of 9 logs that ran the full suites, 3 passed (rc=0), 5 were rejected (no rc line) and landctxguard2 ended rc=2 with no reject line. Note: 4 of the 5 rejected logs died on suite timeout; landlm_gate3 also had the lane_plays red.

Record "20 of 32 Workflow runs stopped on spec or records gaps": docs/northstar/plans/retro_2026-10-21/workflows_vs_manager_mode.md:22 ("20 of 32 stops (spec gaps, stale pins, records state) are defects in the spec-and-records layer the Architect writes"); lines 8-9 same file: "2 of 32 runs completed clean; about 11 pieces landed on main", "15 of 32 runs stopped after one agent". The figure is not in docs/northstar/plans/2026-10-21-tool-split-spec.md (grep for "20 of", "of 32", "32 Workflow" returns nothing there).

Verdict: supported, because a passing gate costs 51 to 67 stage minutes with two of three timed gates waiting 52 and 128 minutes in the queue, and 5 of the 9 full-suite logs were rejected, 5 of 5 by the 600 s suite timeout under load, not on a product defect; the one real test failure rejected a lane play (landlm_gate3).

## H4 Batch size

Merge commits on first-parent origin/main since 2026-10-14 whose subject names a piece id and is not a sync of origin/main (`git log --since=2026-10-14 --merges --first-parent`, then `git diff --numstat <sha>^1 <sha>`; script h2c4.py and the follow-up in this session): 7 of 39 first-parent merges. Most landings are fast-forwards with no merge commit, so this table is the merges only. Added lines only. A scripts/ column is added because the lab landings put their product code in scripts/skilllab/, outside csrc/ autoload/ scenes/.

| Date | Merge | Subject | Product lines | Test lines | Docs lines | scripts/ lines |
|---|---|---|---|---|---|---|
| 2026-10-19 | 3f2e4e9f | Merge remote-tracking branch 'origin/push/vg-rec-sprint7' into push/vg-rec- | 0 | 0 | 115 | 0 |
| 2026-10-19 | ef5a8ef4 | Merge origin/push/vg-rec-sprint8 (records batch 8) into batch 7 landing | 0 | 0 | 20 | 0 |
| 2026-10-22 | 1938aefd | Merge origin/push/labrev2-l8m2 (LAB-REV2-L8M + LAB-REV2-L8M2); ledger confl | 0 | 610 | 1 | 28 |
| 2026-10-22 | 5aa9b40e | Merge push/labrev2-landLab-fix: lab rev2 landing (SPEED, SPEED-1B, window f | 48 | 20794 | 303 | 3013 |
| 2026-10-22 | 7b91383c | Merge origin/push/labrev3-a-pbuild (LAB-REV3-A) into main | 0 | 1849 | 11 | 185 |
| 2026-10-22 | e93d31ba | Merge origin/push/labrev2-vc (LAB-VISION-CONTROL) into main | 0 | 270 | 17 | 13 |
| 2026-10-23 | 7dd4d8fc | Merge origin/push/labrev3-ab (LAB-REV3-B) into main | 0 | 1806 | 101 | 207 |
| Median (7 merges) | | | 0 | 610 | 20 | 28 |
| Median (5 code merges, records batches excluded) | | | 0 | 1806 | 17 | 185 |

Verdict: supported, because the five code merges added a median 1,806 test lines against a median 0 lines under csrc/ autoload/ scenes/ (and 185 scripts/ lines); the piece-sized merge is test-heavy. Not measurable for fast-forward landings, because no merge commit marks their extent.

## H5 Context shape (numbers already recorded)

| Source | Quote |
|---|---|
| docs/northstar/story_reviews/westley/decisions.md:59 (DEC-context-guard-2026-10-24) | "Measured 2026-10-24: the Dispatcher chat made 638 of 1456 calls above 400k (peak 965k) since 2026-10-21, the Architect chat 1016 calls at a median 273k; the two were about 85 percent of a week's subscription usage that stood at 62 percent on day 3." |
| docs/northstar/story_reviews/westley/decisions.md:60 (DEC-no-chat-polls-2026-10-24) | "149 Dispatcher calls in the 14:00 hour of 2026-10-23 at 600k to 900k context, reading `.sdk_engineer_report.md` files every 25 seconds." |
| CLAUDE.md:26 (Usage discipline) | "Measured 2026-10-07 to 10-10: two Architect sessions polled gates at a median 319k to 465k tokens per turn and cost $1,130 of the programme's $1,487" |

Verdict: supported, because the records give 319k to 465k median context per turn, 638 of 1456 Dispatcher calls above 400k and 149 polling calls in one hour at 600k to 900k; no new measurement was made.

## H6 Counterfactual (single session)

Not measurable from the records: no single-session run exists to compare.

| Measure | Number | Source |
|---|---|---|
| Stories in docs/bible/stories.md | 240 | `grep -cE '^\| *S-[0-9]+' docs/bible/stories.md` |
| Status Seen | 8 (S-103, S-106, S-107, S-110, S-132, S-141, S-143, S-241) | awk on the status cell of stories.md |
| Other statuses of note | Ready 15, Tested 13, Spec'd 90, the rest design-decided or deferred rows | same awk |
| Seen verdict dates | 2026-10-13: S-103, S-106, S-141 (stories.md commit "Records 2026-10-13: S-103 approved and Seen", "S-106 and S-141 Seen"); 2026-10-20: S-107 (commit "Verdicts: Batch A answers applied"); 2026-10-21: S-110, S-143, S-241 (docs/northstar/story_reviews/westley/README.md:63-65, "Westley, 2026-10-21"); 2026-10-22: S-132 (stories.md cell "Seen (Westley 2026-10-22"). S-005 was approved then rejected 2026-10-22 and reads Spec'd | git log -S on docs/bible/stories.md; westley/README.md |
| Seen per ISO week | W42: 3, W43: 5 (none before 2026-10-13) | dates above |

Verdict: not measurable, because no single-session run exists to compare; the records show 8 of 240 stories Seen, all first seen from 2026-10-13, 34 days after the method reset.

## Appendix: ids counted in H1b (ledger row numbers in docs/northstar/plans/push_ledger_2026-09-22.md at 8201a87a)

**W39 caught (2):** 188 attach; 353 tests-fix-6c

**W40 TD (test-defect text) (97):** 596 TD-missionover; 614 TD-missionover3; 615 TD-tacview-seed; 622 TD-collapse-lifecycle; 627 TD-G4-H2; 640 TD-A3fb-tie-eps; 669 TD-A74-proceed-route; 673 TD-A69-chronicle-scroll-live; 681 TD-A87-runner-declared-time; 683 TD-A94-allowlist; 688 TD-A94-expected-module; 691 TD-A89-1; 692 TD-A89-2; 694 TD-A89-3; 695 TD-A89-4; 696 TD-A89-5; 700 TD-A99-F3; 705 TD-A108-R-078-06; 706 TD-A109-R-130-02; 721 TD-A114-b7-real-repo; 722 TD-SKILLLAB-mirror; 723 TD-SKILLLAB-planted; 724 TD-SKILLLAB-placement; 725 TD-SKILLLAB-extras; 729 TD-A103-e13-live-units; 736 TD-A122-composite-pre-clamp; 737 TD-A122-e03-fixture; 745 TD-A128-liveness-real-repo; 747 TD-A128-e04-polarity; 752 TD-SKILLLAB-trace-field-order; 753 TD-PP-abi4-test_E02_S020_abi; 754 TD-PP-abi4-test_pipe_shapes; 755 TD-PP-capture-test_core_support_driver; 756 TD-PP-capture-test_core_tick_period_modules; 759 TD-PP-setup; 760 TD-PP-F2-run_search-route; 761 TD-PP-patrol-excursion; 762 TD-PP-tables-route-destination; 765 TD-PP-parity-control; 766 TD-PP-transport-test_pipe_assign_commander; 767 TD-PP-transport-test_pipe_tactical_delta_frame; 769 TD-PP-default0-test_PP_move_capture.py; 770 TD-PP-default0-test_PP_move_collision.py; 771 TD-PP-default0-test_PP_move_cover.py; 772 TD-PP-default0-test_PP_move_group.py; 773 TD-PP-default0-test_PP_move_route.py; 774 TD-PP-default0-test_PP_move_steer_face.py; 775 TD-PP-default0-test_PP_unit_attack_move_group.py; 776 TD-PP-default0-test_PP_unit_first_shot.py; 777 TD-PP-default0-test_PP_unit_leash.py; 778 TD-PP-default0-test_PP_unit_pursuit.py; 779 TD-PP-default0-test_PP_unit_return_fire.py; 780 TD-PP-default0-test_E13_S097_around_not_through.py; 781 TD-PP-default0-parity_c.py; 782 TD-PP-default0-test_PP_settings.py; 783 TD-PP-default0-test_pp_contract.py; 784 TD-PP-default0-test_settings_real.py; 786 TD-PP-default0-test_F1_fog_per_faction_observers.py; 787 TD-PP-default0-test_F2_nearest_hostile_search.py; 799 TD-PP-S101-arrival-narrow; 803 TD-SKILLLAB-states-dead-unit-ids; 804 TD-SKILLLAB-states-fake-trace; 807 TD-SKILLLAB-choke-line-stale; 813 TD-PP-guard-rename; 814 TD-PP-guard-step-in-flight; 829 TD-PP-settle-rerecord; 830 TD-PP-settle-rerecord-2; 831 TD-PP-C-switch0-pursuit; 832 TD-PP-C-transition-timing; 833 TD-PP-C-ping-notarget; 834 TD-PP-C-r08704-sideset; 837 TD-PP-C-invariant-goldens; 838 TD-PP-C-r08102-standoff; 839 TD-SKILLLAB-asym-skilled-goal; 840 TD-PP-A191-e11-dense-touching; 843 TD-SKILLLAB-landscape-guard-defects; 844 TD-PP-A188-leash-repins; 846 TD-PP-A188-g3-invariant-reference; 847 TD-SKILLLAB-approach-rerecord; 848 TD-PP-A196-settings-count; 849 TD-SKILLLAB-mirror-control-18; 850 TD-SKILLLAB-fight-spy-alive; 853 TD-SKILLLAB-outcome-labels; 854 TD-SKILLLAB-matchup-layered-defects; 856 TD-A69-simsession; 857 TD-GATE-playthrough-import; 858 TD-SKILLLAB-batch-workers-fake; 859 TD-PP-A199-line-fixture; 860 TD-PP-A199-parity-route; 861 TD-PP-A199-shape-measure; 862 TD-PP-A199-parity-scope; 864 TD-PP-A199-parity-route; 865 TD-SL-mopup-field-order; 866 TD-SL-A199-approach-control; 867 TD-PP-A199-repin; 916 TD-C5-pan-speed; 918 TD-C5-A56

**W40 TD other (23):** 617 TD-missionover3; 757 TD-PP-baseline-rerecord; 758 TD-PP-defaults-rerecord; 763 TD-PP-R101-01-floor; 785 TD-PP-default0-a99_tactical_hashes.json; 788 TD-PP-a99-rerecord-c-prime; 789 TD-PP-default0-doc; 792 TD-A5-rerecord-A99; 793 TD-A5-rerecord-F1; 794 TD-A5-rerecord-F2; 795 TD-A5-rerecord-F3; 796 TD-A5-S101-floor; 797 TD-A5-collision-rule; 798 TD-A5-collision-reference; 800 TD-PP-F2-run_search-restore; 801 TD-PP-A5-opt-exact; 802 TD-PP-skilllab-goldens-rerecord; 823 TD-PP-R085-02-window; 835 TD-PP-C-rerecord; 836 TD-PP-C-rerecord-2; 845 TD-PP-A188-rerecord; 852 TD-SKILLLAB-approach-default-off; 868 TD-PP-A199-rerecord

**W40 caught (1):** 699 A99

**W41 TD (test-defect text) (96):** 869 TD-NET-save-version-6; 871 TD-TERRAIN-param-count; 876 TD-PING-param-count; 878 TD-SL1-registry-batches; 879 TD-TERRAIN-param-count-2; 880 TD-TERRAIN2-param-count; 881 TD-SL-goldens-rerecord-1006; 882 TD-LAB-tick-cap; 883 TD-LAB-tick-cap-goldens; 884 TD-LAB-features-fields; 885 TD-LAB-batch-names; 886 TD-TERRAIN2-cross-lane; 887 TD-TERRAIN2-corner-rule; 888 TD-SAVE-7; 889 TD-NET-probe-pins; 890 TD-NET-packet-shape; 891 TD-NET-catchup-cap; 892 TD-LAB-layout-shift; 893 TD-LAB-sample-map-pin; 894 TD-T3-terrain-clear; 895 TD-T3-menu-era-toggle; 896 TD-T3-pack-movement; 897 TD-T3-ground-roster-flying; 898 TD-T3-ground-keys; 899 TD-T3-bridge-call; 900 TD-LAB-layout-shift; 901 TD-LAB-scan-build-flags; 902 TD-LAB-mopup-anchor; 903 TD-NET-probe-pins-2; 904 TD-NET-steam-singleton; 906 TD-LAB-twelve-scans; 907 TD-LAB-fit-after-shift; 908 TD-LAB-trace-index; 909 TD-VG-GUARD-1; 910 TD-VG-K-4; 911 TD-VG-K-5; 912 TD-VG-K-6; 913 TD-VG-K-7; 914 TD-VG-K-8; 915 TD-VG-K-9; 920 TD-VG-B-1; 921 TD-VG-B-2; 922 TD-VG-B-3; 923 TD-VG-B-4; 924 TD-VG-B-5; 925 TD-VG-B-6; 926 TD-VG-B-7; 927 TD-VG-B-8; 928 TD-VG-F-1; 930 TD-VG-A-2; 931 TD-VG-K-10; 932 TD-VG-K-11; 933 TD-VG-A-5; 934 TD-VG-A-6; 935 TD-VG-A-7; 936 TD-VG-A-8; 937 TD-VG-A-4; 938 TD-VG-D-2; 939 TD-VG-D-6; 940 TD-VG-D-8; 941 TD-VG-D-9; 942 TD-VG-D-7; 943 TD-VG-A-3; 944 TD-HARNESS-gdreach-1; 946 TD-VG-A-10; 947 TD-VG-A-9; 948 TD-VG-C-1; 949 TD-VG-C-2; 950 TD-VG-C-3; 951 TD-HARNESS-gdreach-2; 953 TD-VG-E-1; 954 TD-VG-B-9; 956 TD-VG-B-11; 958 TD-VG-D-10; 959 TD-VG-D-11; 960 TD-VG-E-4; 961 TD-VG-E-2; 962 TD-VG-E-3; 963 TD-VG-E-5; 964 TD-VG-E-6; 965 TD-VG-E-7; 966 TD-VG-E-8; 967 TD-VG-E-9; 968 TD-VG-E-10; 969 TD-VG-E-11; 970 TD-VG-E-12; 971 TD-VG-E-13; 972 TD-VG-E-14; 973 TD-VG-E-15; 977 TD-VG-E-16; 984 TD-VG-B-12; 989 TD-PP-A200-rerecord-R095; 990 TD-VG-E-17; 991 TD-VG-E-18; 992 TD-VG-E-19; 993 TD-VG-E-20

**W41 TD other (4):** 872 TD-TERRAIN-save-slot; 874 TD-PP-ping-follows-units; 877 TD-SL1-registry-drafts; 955 TD-VG-B-10

**W41 FINDING (5):** 957 FINDING-sim-movement-kind-default; 975 FINDING-walk-route-replan; 976 FINDING-specfactory-7; 978 FINDING-pipe-save-version; 988 FINDING-goldens-stale-main

**W41 caught (5):** 874 TD-PP-ping-follows-units; 875 PP-ping-follow; 886 TD-TERRAIN2-cross-lane; 946 TD-VG-A-10; 984 TD-VG-B-12

**W42 TD (test-defect text) (34):** 929 TD-VG-A-1; 986 TD-VG-B-13; 995 TD-VG-E-22; 996 TD-VG-E-23; 998 TD-VG-E-21; 1024 TD-VG-E-25; 1040 TD-VG-C-4; 1041 TD-HARNESS-sig-1; 1049 TD-VG-B-14; 1081 TD-VG-F-NETTICK-1; 1082 TD-VG-F-NETTICK-2; 1087 TD-VG-A-12; 1088 TD-VG-B-15; 1090 TD-VG-A-13; 1091 TD-VG-A-14; 1094 TD-VG-E-30; 1098 TD-VG-E-32; 1100 TD-VG-A-15; 1104 TD-VG-B-16; 1105 TD-VG-B-17; 1107 TD-VG-B-18; 1109 TD-VG-A-16; 1112 TD-HARNESS-qadir; 1114 TD-VG-A-17; 1122 TD-VG-W-2; 1123 TD-VG-W-4; 1167 TD-VG-B-20; 1171 TD-VG-W-5; 1172 TD-VG-W-6; 1176 TD-LAB-REV2-E1-1; 1177 TD-LAB-REV2-E1-2; 1178 TD-LAB-REV2-E1-3; 1179 TD-LAB-REV2-L3-hash; 1180 TD-VG-B-21

**W42 TD other (3):** 997 TD-VG-E-24; 1023 TD-VG-A-11; 1120 TD-VG-W-1

**W42 FINDING (44):** 994 FINDING-E1q-spec-conflicts; 1010 FINDING-contact-distance; 1011 FINDING-dead-camera-gd; 1013 FINDING-gd-red-main-2026-10-12; 1020 FINDING-delta-death-unit; 1025 FINDING-lots-full-frame; 1030 FINDING-camera-start-framing; 1031 FINDING-net-first-tick; 1033 FINDING-space-field-seed; 1035 FINDING-lockstep-order-cap; 1036 FINDING-netmatch-backend-lifetime; 1037 FINDING-lobby-setup-arity; 1042 FINDING-sig-rows-red-on-base; 1045 FINDING-layer-view-numbering; 1046 FINDING-alt-narrow-missing; 1051 FINDING-delta-death-unit,; 1065 FINDING-unit-draw-overlap; 1067 FINDING-walker-jitter-arrival; 1068 FINDING-host-tick-stall; 1069 FINDING-view-c53-framing-pin; 1071 FINDING-dot-colour-pixels; 1072 FINDING-settings-writer-flips; 1080 FINDING-gd-red-main-2026-10-12,; 1083 FINDING-ground-unit-1-stuck; 1084 FINDING-ambient-user-dir; 1086 FINDING-net-first-tick,; 1089 FINDING-edge-scroll-xvfb; 1093 FINDING-pixel-test-forward-plus; 1101 FINDING-edge-scroll-restore-overshoot; 1108 FINDING-b24-spacing-relax; 1110 FINDING-a18-ground-centre; 1115 FINDING-settlement-square; 1117 FINDING-camera-start-framing; 1121 FINDING-mockup-verify-timing; 1127 FINDING-block-rect-walk-mask; 1128 FINDING-unit-read-touches-move-state; 1152 FINDING-k-plays-red-2026-10-14; 1153 FINDING-k-lane-plays-unmapped; 1155 FINDING-userdir-out-of-scope-sites; 1157 FINDING-match-set-layer-no-layer; 1168 FINDING-space-view-frame-time; 1169 FINDING-mac-landscape-aspect; 1174 FINDING-perf-test-load; 1175 FINDING-cone-state

**W43 TD (test-defect text) (121):** 1028 TD-VG-E-26; 1064 TD-VG-E-29; 1181 TD-LAB-REV2-L4-flip; 1182 TD-LAB-REV2-L4-layers; 1183 TD-LAB-REV2-L4-fullscan; 1184 TD-LAB-REV2-L4-winmargin; 1187 TD-LAB-REV2-E1b-1; 1188 TD-LAB-REV2-E1b-2; 1191 TD-LAB-REV2-BASE-1; 1193 TD-LAB-REV2-BASE-3; 1195 TD-LAB-REV2-L6-flyer; 1196 TD-LAB-REV2-L8-columns; 1197 TD-LAB-REV2-L8-golden; 1198 TD-LAB-REV2-L8-fix; 1201 TD-LAB-REV2-E1b-4; 1202 TD-LAB-REV2-E1b-tests-3; 1203 TD-LAB-REV2-L5-maplabels; 1204 TD-LAB-REV2-L5-point; 1205 TD-LAB-REV2-L5-basis; 1207 TD-LAB-REV2-L5-verdicts; 1208 TD-LAB-REV2-L5-cutscan; 1211 TD-LAB-REV2-L5-verdicts-2; 1213 TD-VG-P-2; 1216 TD-LAB-REV2-S-fullscan; 1219 TD-LAB-REV2-L7-1; 1220 TD-LAB-REV2-L7-2; 1230 TD-LAB-REV2-FIX-roles-arg; 1231 TD-LAB-REV2-FIX-anchor; 1232 TD-LAB-REV2-FIX-nofit; 1233 TD-LAB-REV2-FIX-states; 1234 TD-LAB-REV2-FIX-maxticks; 1235 TD-LAB-REV2-FIX-drafts; 1236 TD-LAB-REV2-L7-3; 1238 TD-LAB-REV2-FIX-l7deps; 1239 TD-LAB-REV2-L7-test-later-rows; 1240 TD-LAB-REV2-FIX-hash; 1241 TD-LAB-REV2-FIX-docs; 1242 TD-LAB-REV2-FIX-reengage-orders; 1243 TD-LAB-REV2-FIX-moved; 1244 TD-LAB-REV2-FIX-blind-keys; 1246 TD-LAB-REV2-FIX-blind-post-retired-name; 1247 TD-LAB-REV2-FIX-blind-post-anchor; 1253 TD-LAB-REV2-FIX-roles-layer; 1254 TD-LAB-REV2-pollution; 1255 TD-VG-E-33; 1261 TD-LAB-REV2-FIX5-fakes; 1262 TD-LAB-REV2-FIX5-probe-bound; 1263 TD-LAB-REV2-FIX5-draft-names; 1267 TD-LAB-REV2-FIX5-arc30; 1268 TD-LAB-REV2-FIX5-docs; 1269 TD-LAB-REV2-FIX5-arc-grid; 1285 TD-LAB-REV2-FIX5-arc-lo; 1287 TD-LAB-REV2-FIX5-header-names; 1288 TD-VG-B-22; 1289 TD-LAB-REV2-L8M-moved; 1290 TD-LAB-VISION-CONTROL-handfed; 1291 TD-LAB-VISION-CONTROL-registry; 1299 TD-LAB-REV2-g3-skilllab; 1304 TD-VG-F-s140-click; 1305 TD-HARNESS-C1; 1308 TD-LAB-REV2-golden; 1309 TD-LAB-REV2-parity; 1310 TD-LAB-REV2-pins; 1311 TD-HARNESS-C235-finding-re; 1321 TD-VG-T-7; 1322 TD-VG-P-1; 1346 TD-VG-E-35; 1357 TD-VG-E-prodslot-pins; 1359 TD-U-PIPE-fixtures; 1386 TD-VG-C2-5-patch; 1405 TD-LAB-REV2-E11-window; 1406 TD-VG-E-36; 1416 TD-VG-B-25-pins; 1427 TD-LAB-REV3-C-scale-gated; 1446 TD-VG-C2-5-scope; 1454 TD-gate-base-fixtures; 1461 TD-gate-known-red-empty-form; 1472 TD-LAB-REV2-capability-tests-move; 1479 TD-gate-venv-unlink; 1481 TD-LAB-REV2-pin-restamp; 1490 TD-LAB-REV2-q008-closed; 1491 TD-LAB-REV2-l7-exclusions; 1493 TD-SHOWCASE-legacy-skip; 1494 TD-HARNESS-home-paths; 1497 TD-VG-C-one-colour; 1508 TD-VG-E-idle-own; 1509 TD-VG-A-sightdisc; 1522 TD-VG-D-s246-import; 1526 TD-VG-C-ground-lift; 1528 TD-VG-C-land-one-projection; 1535 TD-LAB-REV3-A-probe-tests; 1536 TD-LAB-REV3-A-dark-striker; 1537 TD-LAB-REV3-A-naive-attacker; 1538 TD-LAB-REV3-A-probe-premise; 1539 TD-LAB-REV3-A-vc-merge; 1540 TD-LAB-REV3-B-registry; 1541 TD-LAB-REV3-B-report; 1542 TD-LAB-REV3-B-a-tests; 1543 TD-LAB-REV3-B-smoke; 1546 TD-VG-C-land-one-projection-2; 1547 TD-VG-C-facing-arrow-offset; 1555 TD-VG-C-land-marks-fixture; 1556 TD-pin-refresh-2026-10-23; 1557 TD-VG-C-ground-one-colour; 1558 TD-VG-E-facing-travel; 1559 TD-HARNESS-lane-plays-known-red-detail; 1564 TD-HARNESS-record-files; 1578 TD-VG-C-land-one-projection-3; 1579 TD-VG-A-sightdisc-2; 1582 TD-VG-E-37; 1592 TD-VG-M-SKEL-lanes; 1607 TD-VG-E-39; 1608 TD-VG-E-40; 1613 TD-pin-refresh-2026-10-23-R104; 1620 TD-pin-refresh-2026-10-23-R084; 1621 TD-pin-refresh-2026-10-23-R094; 1622 TD-pin-refresh-2026-10-23-R218; 1629 TD-VG-U-0; 1630 TD-VG-E-38; 1647 TD-HARNESS-wt-cap-1; 1654 TD-HARNESS-context-guard-1

**W43 TD other (23):** 1029 TD-VG-E-27; 1043 TD-VG-E-28; 1189 TD-LAB-REV2-E1b-3; 1190 TD-LAB-REV2-E1b-tests; 1192 TD-LAB-REV2-BASE-2; 1194 TD-LAB-REV2-BASE-4; 1200 TD-LAB-REV2-E1b-tests-2; 1206 TD-LAB-REV2-L5-audit-interface; 1237 TD-LAB-REV2-FIX-parity; 1245 TD-LAB-REV2-FIX-blind; 1248 TD-LAB-REV2-FIX-blind-post; 1249 TD-LAB-REV2-FIX-round3-audit; 1250 TD-LAB-REV2-FIX-roles; 1251 TD-LAB-REV2-FIX-parity-default; 1252 TD-LAB-REV2-FIX-refused-beside; 1256 TD-VG-E-34; 1264 TD-LAB-REV2-FIX5-mixes; 1265 TD-LAB-REV2-FIX5-shifted-posts; 1266 TD-LAB-REV2-FIX5-header-notes; 1286 TD-LAB-REV2-FIX5-audit-fix; 1345 TD-VG-E-31; 1347 TD-VG-LS-1; 1510 TD-VG-C-facing-arrow

**W43 FINDING (133):** 1019 FINDING-gd-red-main-2026-10-12b; 1066 FINDING-production-stack; 1113 FINDING-chronicle-concurrent-print; 1185 FINDING-group-orders-cap; 1186 FINDING-damage-up-layer-above; 1199 FINDING-attackmove-idle-cap; 1217 FINDING-speed-marks-unmet; 1218 FINDING-speed-rev2-3x; 1257 FINDING-a8-captured-never-shows; 1259 FINDING-specfactory-reds-2026-10-19; 1273 FINDING-lab-d1; 1274 FINDING-lab-d2; 1275 FINDING-lab-d3; 1276 FINDING-lab-d4; 1277 FINDING-lab-d5; 1278 FINDING-lab-d6; 1279 FINDING-lab-d7; 1280 FINDING-lab-d8; 1281 FINDING-lab-d9; 1282 FINDING-lab-d10; 1292 FINDING-damage-up-caps; 1293 FINDING-blocked-destination-never-times-out; 1294 FINDING-lab-vision-poscontrol; 1295 FINDING-lab-d11; 1296 FINDING-lab-golden-cap-after-E1; 1297 FINDING-r085-02-after-lab-landing; 1298 FINDING-lab-landing-g3; 1301 FINDING-S140-move-no-progress; 1302 FINDING-sim-move-blocked-by-idle-own; 1303 FINDING-gate-lane-plays-scope; 1306 FINDING-gate-userdir-test6-setup-error; 1307 FINDING-gate-baseline-build-flake; 1328 FINDING-pipe-hold-verb; 1335 FINDING-e1n-home-base-follows-army; 1336 FINDING-builder-pkill-xvfb; 1337 FINDING-clerk-glob-rm-xdg; 1339 FINDING-admin-chain-template-dropped; 1340 FINDING-map-obstacles-unwired; 1349 FINDING-gate-base-before-lock; 1350 FINDING-c2-5-pixels-red-under-gate; 1351 FINDING-p2r-gate-starves-front; 1354 FINDING-checksum-factions-after-load; 1360 FINDING-u-pipe-events-save-load; 1362 FINDING-undertest-lots-remove-row; 1378 FINDING-s246-unit-scale; 1379 FINDING-s246-obstacles-too-sparse; 1380 FINDING-s246-scale-prototype-ask; 1382 FINDING-s126-units-in-a-line; 1383 FINDING-s126-count-still-large; 1384 FINDING-s126-vision-circle-orientation; 1385 FINDING-pipe-vs-client-force; 1387 FINDING-qa-galaxy-shot-720p; 1391 FINDING-baseline-cache-perturb-key; 1394 FINDING-mockups-no-verdict; 1407 FINDING-rig-fov-lost; 1408 FINDING-look-stage-warns-only; 1421 FINDING-red-first-unverified; 1422 FINDING-pins-stale-at-merge; 1423 FINDING-size-guides-unenforced; 1424 FINDING-commit-identity; 1425 FINDING-controls-missing; 1429 FINDING-landscape-lakefill-stripes; 1431 FINDING-obey-flattens-far; 1433 FINDING-sim-A-conquest-unrest; 1434 FINDING-sim-B-admin-revolt-chain; 1435 FINDING-sim-C-chronicle-count; 1436 FINDING-sim-D-no-consequence-entries; 1437 FINDING-sim-E-keyframes-missing; 1438 FINDING-sim-F-no-collisions; 1439 FINDING-sim-G-capacity-penalty-threshold; 1440 FINDING-sim-H-population-over-100; 1441 FINDING-sim-I-income-multiplier; 1442 FINDING-sim-J-faction-list-stale; 1443 FINDING-sim-K-threshold-events-on-first-tick; 1444 FINDING-sim-L-commander-never-changes; 1445 FINDING-sim-small; 1448 FINDING-uid-untracked-main; 1450 FINDING-fog-dim-close-zoom; 1451 FINDING-squad-markers-float; 1452 FINDING-icons-hide-bodies; 1453 FINDING-gate-venv-link-vs-fresh-checkout; 1455 FINDING-s140-count-shift-is-e7; 1462 FINDING-s140-own-frame-vs-play-facts; 1473 FINDING-g3-positive-control-red; 1482 FINDING-s132-body-clip; 1483 FINDING-s001-marks-through-terrain; 1484 FINDING-s001-steep-face-flat; 1488 FINDING-s005-building-yaw-random; 1492 FINDING-dev-build-spawns-python-pipe; 1498 FINDING-s140-legend-unstated-marks; 1499 FINDING-land-2d-layer-never-hidden; 1500 FINDING-land-pan-resets-icons; 1501 FINDING-land-terrain-layer-2d; 1502 FINDING-sim-facing-goal-not-travel; 1503 FINDING-facing-offset-2d-only; 1504 FINDING-land-tests-self-referential; 1505 FINDING-sim-walker-waits-forever; 1520 FINDING-sdk-engineer-buffer-1mb; 1523 FINDING-gate-userdir-error; 1525 FINDING-b25-star-size; 1527 FINDING-groundpick-march-skips-crest; 1532 FINDING-overnight-idle-2026-10-23; 1533 FINDING-lop-263px-not-reproduced; 1534 FINDING-lop-flat-tests-unlisted; 1548 FINDING-lop-terrain-reshow; 1550 FINDING-s246-lane-plays-skipped; 1560 FINDING-docs-legacy-live-refs; 1561 FINDING-showcase-junk-docstring; 1562 FINDING-gate-userdir-error; 1563 FINDING-desktop-tests-need-pipe; 1565 FINDING-s132-one-pixel; 1568 FINDING-laneU-inject-scope; 1569 FINDING-architect-stale-drafts; 1571 FINDING-gate-dirt-after-gate; 1572 FINDING-sdk-runs-need-wake; 1580 FINDING-sightdisc-mask-behind-camera; 1581 FINDING-sightdisc-rings-fail-triangulation; 1593 FINDING-M-orphan-screens; 1605 FINDING-landmarks-space-host; 1606 FINDING-flow-spine-tmp-leak; 1609 FINDING-pieces-cycle-undetected; 1617 FINDING-e14-defend-moves-to-objective; 1623 FINDING-flow-spine-c8-07-leak; 1624 FINDING-s088-cluster-one-body; 1625 FINDING-s104-commander-portrait; 1626 FINDING-batch-review-plants-key; 1633 FINDING-qa-clone-stale-since-10-08; 1634 FINDING-qa-refresh-tmp-pack-leak; 1635 FINDING-root-disk-full-2026-10-23; 1636 FINDING-landing-gate-child-of-session; 1646 FINDING-wt-foreign-trees; 1653 FINDING-subscription-usage-2026-10-24; 1659 FINDING-wt-unmerged-branches-2026-10-24

**W43 caught (3):** 1335 FINDING-e1n-home-base-follows-army; 1473 FINDING-g3-positive-control-red; 1605 FINDING-landmarks-space-host

