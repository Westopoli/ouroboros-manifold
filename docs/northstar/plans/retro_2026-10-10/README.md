# Visible game programme: retrospective after three days (2026-10-10)

Written while the programme is paused (Westley, 2026-10-10 09:15). Sources: the programme plan and spec (rev 1 to 8), the three Opus audits and the parallelism audit, the four drift checks, the 83-step execution log in the Architect's continuation memory, the workflow scripts and journal, origin/main at 1a8bbe19, the session transcripts under `~/.claude/projects` (token counts), and a literature pass on how large parallel organisations integrate (`research_orgs.md` beside this file, sources cited inline below). Numbers are measured unless marked estimate.

## 1. Plan versus reality

| Item | Plan (2026-10-07) | Reality (paused 2026-10-10 09:15) |
|---|---|---|
| Pieces | 118 per-file pieces in six lanes plus contract gates | 98 of 118 landed (83%), 11 not started (E1k/E1l/E1o/E1p, the D hook, B8, G5/G6/G8, D7a/b), 3 held, 6 unmapped; plus 37 unplanned pieces landed (K-c6, K-e2, K-e3, the pipe split, D6, the pipe-field fix, D8, C-wire, C6b, A19 to A21, B17 to B21, G-project, three HARNESS gate pieces, and others) |
| Workflow scripts | 6 waves | 34 scripts (29 wave, 5 resume); lane B alone 13 scripts and 12 landings |
| Contract gates | K0, K-a, K-f, K-h, K-d, K-e | those plus K-c6, K-e2, K-e3 and the pipe/bridge split, each discovered by a builder stopping; ABI 5 to 6 and save format 7 to 9 inside 24 hours |
| "Lanes share no files" | sequencing only | 12 owner rows added after launch, 25 shared owned-file entries, 30 to 31 owner overlaps with no `depends_on` ordering at the pause |
| Tests as the spec | fenced, written first by a separate agent | 62 distinct test-defect rulings (TD-VG-*) in three days, every one a Fable ruling with a ledger row |
| Critical path | "about 18 h of agent time at 8 slots"; the parallelism audit said 29.5 h, 37 h with retries, "3.5 to 4 days by day only", utilisation about 40% | 63 h wall clock from launch to pause, continuous; the parallelism audit was right, the 18 h line was wrong by three to four times |
| Tokens | expected 117M "input-equivalent", ceiling 150M, per piece 0.7M expected and 1.2M p90; the Architect chat was not budgeted | 847M raw tokens in the window (93% cache reads); 141M at the CLAUDE.md weighting of a cache read as a tenth of fresh input, so the agent budget held; 430 Sonnet agents, median 373k tokens each, p90 1.59M; $1,487 at list prices, of which the two Fable Architect sessions are $1,130 (76%) |
| Integration frequency | one clerk per lane | 60 merged landing branches in 66 hours (about 22 per day); highest attempt numbers: lane A 14, B 12, F 6, C 4, D 4, E1 4 |
| Lines | not stated | +57,187 lines on main: tests 20,825, docs 24,445, product (csrc, scenes, autoload) 11,000, scripts 842; product is 19% |
| Drift checks | after every compaction | four, after landing rounds, not after compactions; the first was blocking (C6 and C7 landed unwired), the other three found stale status lines and duplicate bookkeeping |
| Definition of done | every lane's stories Seen by Westley; six verification items | 0 of 240 stories Seen; 33 story plays exist; reviewer verdicts so far: lane A first review 11 of 12 "no" with every test green (units, fog and HUD did not draw), lane B 3 of 3 "no" then no/no/unclear, lane C ground era magenta patches and no units; 0 of 6 verification items met |

**The 75% claim.** By pieces it is true and now low: 83% of the planned pieces are on main, 87% if the unplanned ones are counted. By the plan's own definition of done it is 0%: nothing is Seen, and the remaining pieces are the integrative ones (the economy's client half, the D hook, the Steam steps) plus every story review. The first 80% of pieces passed their tests and then failed the first look in all three lanes that reached one, so piece counts overstate progress in this programme more than usual.

**Unplanned findings the programme surfaced** (none in the plan, all real): the pipe regenerated the space field with a different seed than the mission (335 of 487 units spawning in blocked cells), rubble as cover discs made the fog scan 17 times slower, the walk-route planner runs a full-map Dijkstra per waypoint (150 ms per tick with 600 walkers), seven pre-existing specfactory reds, a movement-kind default of FLYING, a power loss that corrupted 13 git objects, and Xvfb's Vulkan renderer washing out colours so pixel tests and plays needed a renderer split.

## 2. What large parallel organisations do, and where this programme diverged

The literature pass (sources in `research_orgs.md` beside this file) is thin on game-studio internals but consistent on the mechanics:

1. **Thin end-to-end first, then fan out.** Walking skeleton (Cockburn), tracer bullets (Hunt and Thomas), "first playable" (Double Fine's term for an area built to test the pipeline across departments). Contracts are derived from a running slice, then frozen. This programme froze six contract headers from read-only scouts and text audits, fanned six lanes out, and the first pixel anyone saw came about 30 hours in and was wrong in every lane. The contracts were amended four times by builders who stopped.
2. **Small batches, fast gate, red mainline fixed first.** Fowler: twice the code to integrate takes four times as long; a ten-minute build. DORA: merge at least daily, three or fewer active branches. Riot's Legends of Runeterra runs about 100 pipeline runs a day at 60 minutes, with a cheap "merge readiness" build before the expensive one. Here the gate took 20 to 40 minutes at best and 2,400-second timeouts at worst, every reject cost a full re-run, and most rejects were non-semantic (staged `.import` noise, a missing owner row, a bare numeric literal, a file outside a list). Lane A needed 14 attempts, lane B 12. Integration frequency was high; the cost per integration and what each integration proved (nodes exist, keys present, not pixels) were the problem.
3. **A single lock is fine until it is the constraint; then WIP must be capped at its capacity.** Theory of Constraints, Little's law, Reinertsen. Cursor's agent-scaling write-up: lock-based coordination made twenty agents run at the throughput of two or three. The parallelism audit said gate throughput would not bind at 12 gates a day and 16 to 18 gates total; the programme ran about 70 landing attempts, serialised them on one flock after three concurrent gates filled `/tmp` and interfered, and the Architect spent 140 scheduled wakeups polling the lock.
4. **Coordination roles only after a measured failure.** Anthropic's agent guidance: the simplest design that works. Cursor removed its dedicated integrator because it created more bottlenecks than it solved. This programme ran test writer, builder, checker, goldens agent, landing clerk, scout, auditor, drift auditor, record clerk, reviewer, profiler and bisect agents: 430 agents for 135 landed pieces, 3.2 per piece, and 24,445 lines of docs against 11,000 of product. Three of four drift checks found drift that the bookkeeping itself created (status lines kept in the programme file, the ROADMAP, the journal and the memory).
5. **The verifier must be near-perfect, because agents solve exactly the test they are given** (Carlini's compiler run). Tests here were written against spec text and fixture shapes, not the built tree, and were wrong 62 times. Each wrong test stopped a builder and needed a ruling from the most expensive model. The spec's own self-healing clause ("an in-script Sonnet ruling agent applies the rulebook") was never implemented in the scripts; every stop went to the Architect.
6. **Component lanes, not streams.** Team Topologies and the Conway evidence (organisation structure predicted Vista's failure-prone binaries better than any code metric): lanes split by file ownership are component teams, and hand-offs at their boundaries (frame field to bridge to view to wiring) are where the cost appeared. Every "landed unwired" finding, the missing layer floors, the missing economy entry points, the fog-filter boolean shape, sat on a lane boundary.
7. **The human is the scarcest resource; size work to review bandwidth.** The plan's done state is Westley seeing each story; the programme ran "until completion" while he was away, so it could never complete, and 23 items queued on him (a label number stopped lane B for a day). Big organisations put the human check early and small (the first playable), not at the end and in bulk.

Where the programme matched good practice: one owner per file, tests before code, fresh-context auditors, determinism as a gate, a single-writer main with frequent landings, small self-contained briefs, and the drift check that caught the first unwired landing.

**Did we bite off more than we could chew?** The scope was fine as a roadmap. The order was the error: all six lanes at once against unproven contracts, with "done" measured by green tests per lane and "seen" only at the very end. A walking skeleton per lane (frame field, bridge, view, screenshot, Westley's eyes) in the first six hours would have proven each contract, caught the three look failures at hour 6 instead of hour 30, and let the fan-out run on known ground.

## 3. Was Fable the right overlord?

Measured, window 2026-10-07 to 2026-10-10 10:00, the two Architect sessions (the programme session that died with the power and the resumed one):

| | Programme session | Resumed session |
|---|---|---|
| Turns | 422 | 610 |
| Context per turn (median, p90, max) | 465k, 882k, 964k | 319k, 682k, 762k |
| Tool calls | Bash 160, Agent 43, Workflow 40, Edit 22, Write 19, SendMessage 12 | Bash 302 (mostly "check lane X gate"), ScheduleWakeup 140, Agent 95, SendMessage 23, Workflow 17 |
| Tokens, dollars (list) | 208M, about $550 | 223M, about $580 |

Judgement work in those turns: 62 test-defect rulings, eight spec revisions, 34 scripts, and about ten cross-cutting diagnoses (the pipe-field double generation, the cover-disc blow-up, the walk-route cost, the galaxy renderer bisect, the fog-filter shape, the K-e2 entry-point gap). That is the work Sonnet is on record getting wrong (2026-09-24: a design document becomes a build list, invented constants, blind merges, bookkeeping instead of running the game), so Fable earned its keep there. The other two thirds of the turns were dispatcher work: launching, polling the gate lock, messaging clerks, recording 83 memory steps, at 300k to 900k tokens of context each. That is where about $750 of the $1,130 went (estimate: dispatcher share of turns times the Fable cache-read rate). The same mechanics on Sonnet would have cost about $170 for the whole 432M tokens. CLAUDE.md's own rule to restart a coordinator chat from its continuation memory once its context grows large was not followed; both sessions ran close to the million-token limit.

Verdict: neither "Fable overlord" nor "Sonnet overlord". Split the role. A Sonnet dispatcher with a runbook and a small context (restart at about 150k) launches, polls, lands and records. Fable is on call through short briefs for rulings, diagnoses and spec changes, each a fresh context of 30k to 60k tokens (estimate: 60 consults at that size is under $100). The larger lever is upstream: with tests written on the built tree and a fast pre-gate, most of the 62 rulings and 70 gate rounds do not happen, so the overlord has far less to decide.

## 4. Changes proposed (for Westley to pick; nothing applied)

Big:
1. **Walking skeleton per lane before fan-out.** The first piece of every lane is the thinnest end-to-end path with a screenshot Westley sees. Contracts are frozen after that piece runs, not before.
2. **Two-tier gate.** A five-minute pre-gate (lints, footprint, owner rows, the lane's own tests) runs in the builder's worktree before any push; the full gate runs once per landing batch. A non-semantic reject never costs a full gate.
3. **Dispatcher and on-call Architect** as in section 3; the Architect chat restarts at 150k context; the overlord is budgeted in the spec in dollars.
4. **Tests written on the built tree.** The test writer runs the red test against the stub or the previous piece and states the failing line; a ruling agent in the script handles the rulebook cases; only new rule meaning goes to Fable.
5. **WIP capped at gate capacity.** Two or three lanes in flight, not six; the next lane starts when a landing slot is free.

Small:
6. One status location (the programme file), the journal generated from git, no step log in memory beyond the last three steps; drift checks become a diff of that one file against main.
7. "Done" for a player-facing piece includes its screenshot seen, as guard 1 already says; apply it per piece, not per lane.
8. Pace the look work to Westley's review bandwidth: a lane's next look pass waits for his verdict on the previous one; while he is away, build sim and harness pieces, not looks.
9. Keep: one owner per file, tests first, determinism gate, fresh-context auditors, the rules file cited by every brief, the flock line, `.wt-done`.
