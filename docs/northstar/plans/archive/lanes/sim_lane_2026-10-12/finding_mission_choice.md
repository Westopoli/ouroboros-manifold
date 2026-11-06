# Finding: mission choice (sim lane step 1, ROADMAP 2b)

Run 2026-10-15 on origin/main fe5fe84e, debug build. Rule read: `docs/bible/epics/E-10-missions.md` R-072-01 to R-072-08, R-073-01, R-074-01. Q-072-02 (urgency weights cannot reach R-072-06's 0.8) is open in the register and is treated as open here.

## Counts

| Item | Count |
|---|---|
| Campaigns / seeds | 10 / seeds 1 to 10 (80 regions, features 0 to 7, as the viewer) |
| Missions run | 100 (10 per campaign; no campaign ended; all at chapter 11 after the last jump) |
| Outcomes applied in rotation | 100; band asked equals band reported 100 of 100 |
| Candidate rows recomputed (urgency, relevance, preference, score) | 1,196 across 100 pools (pool size 2 to 36) |
| Draws checked against the rule (in pool, in top 5, weighted) | 100 of 100 generator draws |
| Mismatches | 3 classes: 14 missions (class 1), 124 relevance rows in 10 first-mission pools (class 2), 3 terms never fed (class 3) |
| `quiet_world` fallbacks / empty-pool retries | 0 / 0 |

## Findings

| rule says | sim did | seed/tick | classification | proposed piece |
|---|---|---|---|---|
| R-072-05: one weighted draw from the top 5 picks the mission; R-073-01: Defensive Stand needs a player region targeted by an enemy attack this window | The draw is honoured, then `handle_mission_start` composes the mission and finds 0 player units and enemy power 0 for 14 of the 22 Defensive Stand draws (every draw with no pending telegraph on the region: 14 of 14; every draw with one: 8 of 8 kept). The pipe silently replaces it with the first (archetype, player region) pair that composes units: Siege Breaking at region 0 eight times (parity 0.97 to 0.997), Defensive Stand at another region six times (parity about 0.80). The `mission` frame says nothing: `quiet_world` false, no replaced flag. Cause, read from code: `om_mission_trigger_fires` fires Defensive Stand on any hostile neighbor above military 0 (not only on an attack), while `om_mission_compute_enemy_power` returns `committed_budget x 300` for it, and the budget is 0 without a telegraph. Pipe comment at `om_pipe.c` "Never compose a zero-unit mission silently" names the gap and defers it. | s2 t300, s2 t400, s3 t144, s6 t72, s6 t322, s7 t74, s7 t424, s7 t474, s8 t93, s8 t393, s8 t493, s10 t197, s10 t347, s10 t397 | Wrong choice reaching the player: the drawn pick is discarded 14% of the time and Siege Breaking at region 0 is over-represented (30 played against 22 drawn). A trigger-versus-force mismatch, not a draw bug. | Needs a ruling first, as a `Q-` row: (a) tighten the trigger to R-073-01 (attack only), (b) give a hostile-neighbor Defensive Stand the R-074-01 "otherwise" power (region military x 2000), (c) keep and surface the replacement. Then one mission.c piece; SV piece to expose the replacement (see gaps). |
| R-072-03: relevance = 0.4 lineage + 0.3 proximity + 0.3 fit, for the player's lineage | In the opening jump the pool is built before `om_character_selector_run` seats the first commander and records the lineage home. All 124 rows of the 10 first-mission pools store relevance 0.0; recomputed on the same state at mission_start, 0.06 to 0.70 (lineage 1.0 in 28 rows). The top-5 set differs for 3 of the 10 first-mission pools (seeds checked in `out.json`). Missions 2 to 10 match to 1e-9 (1,072 rows). One lineage (id 100000000) exists in every run, equal to `om_campaign_lineage`. | tick 20 to 50, first mission of each seed (all 10 seeds) | Order bug in `om_time_jump_run` (`generational.c` ~2141: `om_mission_generator_run` before `om_character_selector_run`, opening only matters because the lineage does not exist yet; later jumps use the standing lineage) | Piece after a one-line ruling that the opening pool must see the seated lineage; swap or rebuild in `generational.c`. |
| R-072-02 chain term, R-072-03 fit term and "ever operated" | Chain: 0 of 1,196 rows nonzero; `om_mission_set_revolt_events` has no production caller (so Counterinsurgency never enters a pool: 0 of 1,196 rows; Containment's revolt branch is dead). Fit: `om_mission_refresh_context` passes `times_run` as the literal 0, so the fit term is always 0 (the code comment says so). Recent attacks come from the 3-tick pending-telegraph list only, adjacent-lost from `previous_owner` with no window; lost is 0 in all rows, so Reconquest never entered a pool. Interception (0 rows) needs an attack with no hostile neighbor and Suppression drew 6 rows, 0 picks. | all seeds | Inputs never fed (known from the code comments; now measured). The urgency and relevance the player sees omit the chain term (0.2 of urgency) and the fit term (0.3 of relevance). Archetype coverage in 100 missions: 7 of 10 appear in pools, 6 are ever played. | Feed-in pieces, one per input (revolt events from the chronicle's revolt chain, lineage archetype history, windowed attack log). Related: Q-040-01 (5-tick revolt chain), Q-035-01. Needs Westley's order of priority. |

Rows that checked clean (no mismatch):

- R-072-02 urgency: recomputed in Python from region fields, hostile-neighbor military, pending telegraphs and previous owners; equals the sim's stored value in all 1,196 rows (tolerance 1e-9). Weights 0.4 / 0.4 / 0.2, conflict terms 70, 600, 0.5, 0.3.
- R-072-04: preference 0.5 in all rows (no player marks exist in the pipe).
- R-072-05 score: stored score equals 0.5u + 0.3r + 0.2p in all rows.
- R-072-05 draw: every draw sits in the top 5 by score (ties broken by lowest index, as the C scan does). Rank counts of the 100 draws 29 / 20 / 18 / 19 / 14; the expected counts from the scores are 25.9 / 24.1 / 19.6 / 15.9 / 14.5. Consistent with a draw proportional to score. The pick is the argmax only 29% of the time, which is the rule, not a mismatch.
- Design note, not a mismatch: urgency and relevance do not depend on the archetype, so every archetype that triggers on a region ties on score; one region with four triggers holds four of the top-5 slots (seed 1 tick 70, region 58). The rule's "(region, archetype) pair" reading allows it.

## Q-072-02, measured (stays open)

Max urgency over all 1,196 rows is 0.783; none reaches 0.8. 705 rows have the R-072-06 shape (stability composite at most 15, hostile neighbor military at least 80): the best has stability 1.7, neighbor military 85.9, urgency 0.776, and with chain always 0 the ceiling is 0.8 x (deficit) plus the capped conflict term, as the register says. R-072-06 is not satisfiable in play with the current weights. No classification and no fix; the numbers are added evidence for the open row. Not measured: whether such a candidate beat a quiet region in the draw (quiet regions are not candidates, so the comparison has no pool to read).

## Method

- Script: `/tmp/missionchoice/run.py` (raw rows in `/tmp/missionchoice/out.json`). Run with `.venv/bin/python /tmp/missionchoice/run.py`.
- Pipe, through `scripts/simviewer/pipe_session.py` `PipeSession` on `pipe/ouroboros_pipe_dbg`: `set_seed` (seed, n_regions 80, features 0 to 7, opening jump on), `snapshot`, `mission_start` (faction 0, era_kind 0), `objective_complete` (every objective), `mission_end` with `retention`, `jump` (50). Outcomes by `viewer.pick_to_inputs` bands 0 to 4 in rotation (`m % 5`). `mission_refuse` was not used (five outcomes only).
- The pipe does not expose the candidate pool, so a shadow world over `libouroboros_dbg.so` (same library the pipe links) replays the same verbs through the same calls as `handle_set_seed`, `handle_mission_start`, `handle_mission_end`, `handle_jump`. Before every `mission_start` the shadow's state checksum equalled the pipe snapshot's (100 of 100) and after it region and archetype equalled the `mission` frame (100 of 100), so the shadow is the same world. It reads `om_mission_candidates` (stored u, r, p, score), then recomputes u, r, p, score independently in Python from `om_region_field`, `om_region_composite`, neighbors, stance, telegraphs, previous owner and lineage history.
- First wrong attempt, kept for the record: `om_world_set_feature` was declared with two arguments, the shadow's checksum diverged from the pipe's, and the checksum gate caught it before any data was taken.
- The debug pipe already sets player unit HP from `retention` (`om_pipe.c` mission_end), so the band pick works here without SV-0.

## What the pipe could not expose (candidate SV pieces)

1. The candidate pool: region, archetype, urgency, relevance, preference, score per candidate, and the draw's rank (verb or `mission` frame extension; debug-only is enough). The whole check needed a ctypes shadow world because of this.
2. That the drawn pick was replaced: `mission` frame has no `replaced` / `drawn_region` / `drawn_archetype` field. The player sees a mission the generator did not choose.
3. The inputs behind a score: recent attacks, adjacent lost, revolt events, lineage connection, hops, times run (`om_mission_region_ctx`), so a viewer could show why a region ranked.
4. `quiet_world` stays false for the silent scan fallback; a second flag (or an enum `source`: pool, quiet_world, scan) would separate the three paths.
5. Fields the viewer would need to draw the pool on the map: none missing beyond 1 to 3; the `History.missions` rows already carry region and archetype.
