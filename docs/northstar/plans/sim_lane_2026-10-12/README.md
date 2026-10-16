# Simulation lane: findings ledger (ROADMAP 2b step 1)

Mandate: `2026-10-12-sim-lane-context.md`. Verify the C sim follows `docs/bible/algorithms.md` and the simulation epics; find regressions in mission choice and in the chronicle's source. Find and show first; a fix is built as a piece only after Westley reads its row (his word, 2026-10-12). A rule question is a `Q-` row with candidates, never a guess.

First pass run 2026-10-15 on the Mac (the Linux box was down): four Sonnet engineers, read-only on code, one file each. The C sim builds on the Mac; bit-for-bit checks against Linux (A99 hashes, `-msse2` probes) and the merge gate still need the Linux box.

## Ledger

One row per finding class. `Piece` is a name only until Westley reads the row; `Needs` says what has to happen first.

| # | Rule says | Sim did | Evidence | Class | Piece | Needs |
|---|---|---|---|---|---|---|
| 1 | R-045-09: Knowledge Lost 1.0 to 2.0 events per 50-tick window | 4.41 (seeds 1 to 3: 3.84, 4.64, 4.63); C matches ALG-27b verbatim | `finding_knowledge_lost.md` | tuning target never fitted; held red by Westley (A90, A95) | KL-RETUNE | count which eligibility leg feeds it; the balance simulation |
| 2 | R-085-04: fight length Strike < Line < Siege | Strike 2170, Line 4226, Siege 1800; no ALG row behind it; fixture is three unlike mirrors | `finding_knowledge_lost.md` | threshold with no bible source (Q-085-01/02 pairs) | TACT-ORDER-RULING | lab rev 2 settles it |
| 3 | R-072/R-073: the mission played is the one the generator drew | 14 of 100 missions silently swapped: an unattacked Defensive Stand composes 0 units and 0 enemy power (power = committed budget x 300), so `mission.c` takes the first pair that composes; Siege Breaking at region 0 eight times; the frame shows no swap | `finding_mission_choice.md` | sim defect, rule question first | MC-1 | `Q-` row: tighten the trigger to R-073-01, or give the unattacked stand the R-074-01 fallback power, or surface the swap |
| 4 | S-072: missions weighted toward where I belong | opening pool scores relevance 0.0 in all 124 first-mission rows: the generator runs before the selector seats the lineage; top-5 differs in 3 of 10 campaigns | `finding_mission_choice.md` | order defect in `generational.c` | MC-2 | ruling on the order, then a small fix |
| 5 | R-072-02: chain and fit terms weigh the score | chain term 0 in every row; `times_run` a literal 0; adjacent-lost always 0, so Reconquest and Counterinsurgency never enter a pool; Interception never appears; 6 of 10 archetypes ever played | `finding_mission_choice.md` | inputs never fed (ties to Q-040-01, Q-035-01) | MC-3 (one feed-in piece per input) | Westley sets the order |
| 6 | R-072-06: a region at stability 15 under a military-80 neighbour scores urgency >= 0.8 | best of 705 such rows 0.776; max of 1,196 rows 0.783 | `finding_mission_choice.md` | evidence for open Q-072-02 | none | Westley's answer to Q-072-02 |
| 7 | R-065-03/-04: the scroll always carries the family | 1 lineage entry in 25 jumps | `finding_chronicle_source.md` | hypothesis: `chron_push_candidate` drops past `CHRON_MAX_CANDIDATES` 256 (`chronicle.c:134,1590`), lineage pushed late | CH-1 | log candidate count and drops, then fix |
| 8 | R-067-03: a famine, its revolt and its end are one entry | 0 chain entries against 1,749 multi-event chains; chain clusters pushed with peak score 0.0 (`chronicle.c:1641`) | `finding_chronicle_source.md` | sim defect | CH-2 | after CH-1's log |
| 9 | R-068-07: every entry reads | 49 of 243 entries are blank shells (empty text, fragment ids -1); `n_entries = n_clusters` while `entry_valid` is 0 (`chronicle.c:1869-1896`) and the pipe emits them | `finding_chronicle_source.md` | frame-contract bug | CH-3 (contract piece) | second Fable audit |
| 10 | R-065-05: ripple entries capped at 2 | 50 ripple entries, 9 jumps with 3 or 4; consequence clusters selected first and uncapped; ripples on any adjacent event, not flagged consequences | `finding_chronicle_source.md` | rule question | CH-4 | `Q-` row: one cluster or one per region, capped or not |
| 11 | R-066-02: context multiplier (mission region, character, chain length) | all three fixed at 0 (`chronicle.c:1669`, comment admits it); 124 of 243 entries score exactly 5.20 | `finding_chronicle_source.md` | sim defect | CH-5 | |
| 12 | R-067-05: faction shift classified | classifier called with `has_conquest_or_revolt` 0 (`generational.c:2065`); 636 of 761 faction-creating events in regions with no entry | `finding_chronicle_source.md` | sim defect | CH-6 | |
| 13 | R-071: no sentence repeated word for word in a campaign | 147 verbatim repeats in 5 campaigns; 126 of 332 fragment ids reused | `finding_chronicle_source.md` | library size (E-21) | CH-7 | `Q-` row on pool size and reuse rule |
| 14 | architecture: `mission_start` falls back to a quiet-world mission | `no viable mission` in 3 of 25 chapters | `finding_chronicle_source.md` | sim defect, overlaps F-rulings | MC-4 | |
| 15 | ALG rows each have a test | 78 rows: 38 covered, 37 uncovered, 3 no C site; E-08, E-09, E-10 cores nearly untested; 92 control stubs raise NotImplementedError | `coverage_algorithms.md` | coverage gap | TEST-ALG batch (test writer) | Westley's thresholds per row |
| 16 | constants verbatim (`om_constants.h`) | `OM_BUDGET_PRESSURE_THRESHOLD`, `OM_REINFORCE_*`, `OM_ATTACK_CONFIDENCE_*` never used in any `.c`; literals 0.8, 0.5, 1.5 inline in `agent.c`, `resolve.c` | `coverage_algorithms.md` | verbatim-constants question | CONST-2 | |
| 17 | ALG-57 text | says shortfall "confirmed at 25", states `CAPACITY_SHORTFALL_THRESHOLD = 0.4` | `coverage_algorithms.md` | bible row contradicts itself | none | Westley |

Passes worth recording: urgency, preference and score match the rule in all 1,196 candidate rows; the draw is a weighted draw over the top 5 as written; 22 of 22 mission jumps open with the mission result in the right category; no entry without an event behind it; at most 10 entries, never a digit, never over 90 words.

## Pipe gaps (candidate SV pieces)

From the two sweeps, in the order they would have saved the most work: the candidate pool with per-candidate scores and the draw's rank; a flag when the pick was replaced; the score inputs (recent attacks, adjacent lost, revolt events, lineage connection, hops, times run); a `source` field (pool, quiet_world, scan); per-entry lineage ref, chain tag, event ids and dropped state; the opening-jump chronicle (`set_seed` is silent); `revolts[]` as fired revolts with outcome, not every admin roll.

## Method notes

`jump` streams no deltas: the chronicle run used a twin (`save`, `step` 50, `load`, `jump` 50), checksums equal in 25 of 25. The mission run used a shadow world over `libouroboros_dbg.so` to see the pool; its checksum matched the pipe before every `mission_start`. The debug pipe already sets unit HP from `retention`, so the band pick works without SV-0. Scratch scripts were under `/tmp/` and are not kept; the next pass writes them under `scripts/simviewer/probes/` as a piece.
