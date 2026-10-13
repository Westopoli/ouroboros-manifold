# Pre-flight scout 9-harness (2026-10-07, Sonnet, read-only)

**Scout 9: harness capacity, from today's gate logs and the workflow journals. Read-only.**

**Caveat on the data:** the `/tmp` gate logs (`gate_ls2.txt`, `gate_ls2d.log`, `t2c_gate.txt`) carry no timings, so I rebuilt gate times from the clerk transcripts. `merge_gate.sh` also has no `regression_lab` stage. The gate runs make, lints, `regression_csim`, `regression_qa_t1`, `specfactory_regression`, transport, playthrough and the two traces. Lab tests (`tests/skilllab`) run outside the gate, by builders and clerks.

**1. Gate wall time**
- Whole gate, launch to the last `GATE` line, taken from agent `.jsonl` timestamps in `.../subagents/workflows/wf_*/agent-*.jsonl`:

| Run | Minutes |
|---|---|
| ping-land | 25.2 |
| strand-land2 | 30.4 |
| terrain-land2 | 34.6 |
| lab-land3 | 34.2 |
| lockstep clerk | 30.1 |
| lab landing for the layout search | 20.7 |
| Steam clerk, first run | 41 |
| Steam clerk, final run | 26.5 |
| terrain-land | 12.7 |

- Median is 30 min and mean 28 min; range 12.7 to 41. Runs with a cached baseline (the `baseline: cached` line) come out at 12.7 to 21 min. Runs that compute the baseline (`baseline: computed`, which runs the suites twice) take 25 to 35.
- Stage times, from pytest summary lines in the same transcripts:
  - `tests/csim`: median 325 s (276 to 382, 45 runs).
  - `tests/specfactory`: 271 s (258 to 287, 6 runs).
  - `tests/transport`: 75 s (71 to 89, 13 runs).
  - playthrough: 156 s (`t2c_gate.txt`) and 159 s (Steam clerk), plus a Godot import of up to 300 s.
  - `regression_qa_t1`: one sample, 188 s.
  - make, lints, reach and owner checks: no per-stage time anywhere; together they finished within 289 s (lab-land3 had reached `placeholder_controls` by then).
  - `tests/skilllab`, outside the gate: median 741 s (639 to 1288, 16 runs). The 1288 s runs were under contention.
- Long poles: `regression_csim` (about 11 min with a computed baseline), `specfactory_regression` (about 9 min), then playthrough. Playthrough runs only when the diff touches `csrc/`, `autoload/`, `scenes/`, `project.godot` or `tests/qa/desktop/`.
- Gap: add elapsed time to every `GATE` line; today only the playthrough line reports a wall time.

**2. Gates per day and parallelism**
- Serial gates run about 30 min, which is roughly 48 a day. Under lab load I expect 40 to 45 min, which is 12 to 14 across a 10-hour day, plus about 28 overnight. The slowdown evidence is `tests/skilllab` at 1288 s against 640 s alone, and csim at its 382 s maximum against 276 s.
- The suites are single-process pytest with no xdist, so a gate averages about 1 to 2 cores. Playthrough software GL (llvmpipe) may use more; I did not measure it.
- Memory: each gate runs in a `MemoryMax=6G` scope (`systemd-run` in the clerk logs). I have no peak resident figure. The box shows about 15 GB available while a gate runs.
- Parallel inside one gate:
  - `regression_csim`, `specfactory_regression` and `regression_qa_t1` can run together. They are separate pytest processes on the same built library.
  - Playthrough cannot safely overlap the others. It uses `xvfb-run -a` and a random QA port (`tests/qa/desktop/daemon_client.py`), so the display is not the problem. The problem is that `playthrough_check` re-runs plain `make libouroboros.so pipe/ouroboros_pipe` in the candidate, while stage 1 built with `OPT=-O2`. That can overwrite the library the csim run has loaded. This comes from reading the code, not from a run.
- The cheapest saving is to run the baseline ("before") and candidate ("after") passes at once on a computed baseline. That saves about 10 min.

**3. Token spend**
- The harness `tokens` field is each agent's peak context size, not cumulative spend. I checked it: `tests:W0` shows 55,652 against a last-turn context of 55,628. So `totalTokens` understates real work by about 3x.
- Real work per workflow, from the `.jsonl` files: fresh tokens (input plus cache-write plus output), cache reads, and input-equivalent units ("eq" below). The eq weights (cache write 1.25, cache read 0.1, output 5) are my assumption.

| Workflow | Agents | Harness total | Fresh | Cache reads | Eq | Wall |
|---|---|---|---|---|---|---|
| lockstep | 35 | 1.215M (1.50M with 6 cached) | 3.93M | 25.4M | 8.6M | 152 min |
| terrain stage 2 (two runs) | 17 | 937k | 2.65M | 23.8M | 6.6M | 69 + 69 min |
| layout search (two runs) | 10 | 437k | 1.15M | 5.5M | 2.3M | 79 + 16 min |
| Steam phase A | 13 | 496k | 1.33M | 6.0M | 2.6M | 126 min |
| terrain stage 3 | 16 | 861k | 2.14M | 20.8M | 5.4M | 88 min |

- All 91 agents, peak context: mean 46.5k, p90 64.8k, max 112.9k (`build:3a`).
- All 91 agents, fresh tokens: mean 123k, p90 217k, max 781k. Eq: mean 281k, p90 473k, max 1.82M.
- By role, as eq mean, p90 and max (count in brackets). Roles come from the labels.

| Role | n | Eq mean | Eq p90 | Eq max | Peak ctx mean |
|---|---|---|---|---|---|
| test writer | 35 | 210k | 340k | 473k | 47.8k |
| doer | 43 | 337k | 537k | 1.82M | 49.5k |
| checker (check and gate agents) | 8 | 160k | 312k | 511k | 28.3k |
| clerk | 5 | 497k | 721k | 799k | 40.8k |

**4. Budget for 50 pieces (tests, build, check), 6 clerks and audits**
- One piece, on the role means: 210k + 337k + 160k = 707k eq (about 126k peak-context).
- 50 pieces is 35.4M eq, and 6 clerks is 3.0M.
- Retries add about 8.8M, from the stop rates in section 5. 16 of 43 doers stopped (37%) and each re-run costs about 437k, giving +8.1M. 2 of 35 test writers stopped (6%), giving +0.7M.
- Opus audits have no data in these runs. I reserve 5M as a placeholder.
- **Expected is about 52M eq** (about 8.3M harness-style tokens). **Ceiling is 75M eq**, about 1.5x expected. The 1.5x is my choice, not derived. The p90 sum alone is 59.5M plus 4.3M for clerks.
- Per lane (tests, build, check): expected 0.7M eq, ceiling 1.2M (the p90 sum). Hard stop for a lane including retries: 2.4M.
- Per agent: stop any agent whose context passes 120k (the observed maximum is 113k).
- Per workflow: observed maximum is 8.6M eq for 35 agents. Cap at 0.25M eq per planned agent, 10M for a 40-agent workflow.
- The Steam clerk is the clearest waste: 101 min, 38 tool calls and 484k fresh tokens, mostly polling. Clerks should run the gate detached and wait 5 min or more per poll.

**5. Stop causes**
Covers the five workflows plus their continuation and P4 runs (seven runs in all). The classification is mine.
- Existing test looks wrong: 10.
  - lockstep: `cksum`, `save-support`.
  - terrain stage 2 continuation: `lab:build`.
  - layout search: `P1`, `P2`, `P4`.
  - Steam: `W0`, `W7`.
  - stage 3: `3a`, `3e`.
- Missing precondition: 5.
  - lockstep: `save-mission`, `save-move`.
  - Steam: `W3`.
  - stage 3: `check:3b` and the clerk.
- Main moved or merge conflict: 4. Steam clerk (main was 52 commits ahead), terrain stage 2 `lab:tests`, and ledger conflicts for both the terrain-land2 clerk and the stage 3 clerk; clerks resolved three of the four.
- File outside list: 2 (`save-mapgen`, `3f`).
- Contract need: 1 (`hash-macro`).
- Flake: 2.
  - Steam clerk's playthrough REJECT on `test_c5_4_move_order_single_command_and_units_move` (31 passed, passes alone).
  - Layout-search `P1` timing failure.
- Footprint or owner row missing: 2 (terrain-land2 clerk, layout-search clerk). One gate REJECT on a new unreachable symbol, `om_set_era_kind` in `t2c_gate.txt`.
- Other: `save-unit` (cause not found within its 40-call budget) and terrain stage 2 `planner-b:tests` (tests were green, not red).
- Gate-run tool timeouts of 600 s on foreground waits hit the Steam, stage 3 and layout-search clerks several times. Each forced a kill and relaunch.

**6. Resume behaviour**
- Journals have no duplicate keys within a run. The cross-run evidence is below.
- Lockstep: 6 agents show `cached:true` (no re-run, no cost). 3 agents re-ran under new keys (`build:harness`, `tests:gd`, `build:gd`). They took 17 to 21 s each and found the branches already existed, costing about 98k fresh tokens. The first runs had cost 231k fresh.
- `land-overnight-1006` was relaunched 7 times, and the journals are per launch, so there is no cross-run cache. `lab:rerecord` ran 4 times (79k peak-context). `land:lab` and `runs:1006b` each ran twice, and `runs:1006b` took about 34 min each time. `terrain:pipe:tests` ran twice.

**Recommended numbers**
- **Concurrency per workflow:** at most 4 test-running agents by day with lab at 8 workers, and 8 at night. Run gates one at a time.
- **Gates per day:** plan 12 by day and 25 overnight. The programme needs about 12 to 18, counting 6 clerks and retries.
- **Token ceilings:** 75M eq overall, 1.2M eq per lane with a 2.4M hard stop, 10M per workflow, and a stop at 120k context per agent.
- **Flake rule:** on a single red that passes alone, re-run only that test id up to twice, never the whole gate. Count it as real only if it reds on a full-stage re-run. Also fix the baseline cache (key on main sha) and have the gate print per-stage times.
