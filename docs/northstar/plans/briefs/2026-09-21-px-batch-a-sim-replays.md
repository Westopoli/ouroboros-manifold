# HANDOFF BRIEF — PX batch A: PX-4, PX-7, PX-14, PX-19 (replays on existing fixtures, no GPU)

Self-contained. Program context: `2026-09-21-factory-program.md`; design under test: `docs/northstar/PLAN.md` section "The Factory". Results go in `docs/northstar/proving_ground/` as `PX-04-*.md`, `PX-07-*.md`, `PX-14-*.md`, `PX-19-*.md` in the style of the existing `PX-*.md` files (claim, fixture, result table, limits, "Design consequences" left blank for the design lane), plus one row each in `SCORECARD.md`. Normal prose in the write-ups.

## Rules for the implementor

- Sub-agents are Sonnet; you plan and review, they build. Ask Westley about his Claude usage before a batch of more than two doers.
- Nobody writes game code. These are replays and measurements. New files allowed: `scripts/specfactory/<tool>.py` with tests in `tests/specfactory/`, the write-ups, evidence under `docs/northstar/proving_ground/evidence/px04|px07|px14|px19/`. Touch nothing under `csrc/`, `tests/csim/`, `docs/bible/`, `docs/northstar/PLAN.md`, or `~/Projects/agora` except reading (PX-19 reads its logs).
- Scratch worktrees only: `git worktree add --detach /tmp/pxA/<case> <commit>` from `~/Projects/ouroboros-manifold`; remove every one when done (`git worktree remove --force`, `git worktree prune`).
- Python: `~/Projects/agora/.venv/bin/python`. Tests: `-m pytest -q -p no:cacheprovider`. The C library builds through `tests/csim/conftest.py` (`make -s libouroboros.so libouroboros_dbg.so`).
- No Ollama calls at all in this batch. No `agy`. Do not stop or start `agora-dispatcher.service`.
- Commit on `main` and push per PX. Trailer `Co-Authored-By: Claude <model> <noreply@anthropic.com>`. Never stage files you did not create.
- Every detector or gate you build ships with a positive control (it must fire on the planted case) and a negative control (silent on the clean case). A check that cannot fail is a defect.

## PX-4 — T1 detectors on the C trace

**Claim (Factory, "Oracles"):** T1 trace detectors and invariants over the trace API are an oracle class for the sim from rung P0, with `OM_BUG_*` builds as positive controls.

**Facts.** Trace API in `csrc/ouroboros_sim.h:81-95` (`om_trace_row`: tick, region_idx, faction_id, tier, military, economy, tension, population, stability, capacity, drift row, checksum) and `:145-148` (`om_trace_enable`, `om_trace_len`, `om_trace_read`). The probe-C detectors (`rubberband`, `stuck`, `backwards`, `dropped_order`) live only in an archived run worktree, `~/Projects/agora/runs/101-probe-a-toy-drift-20260910-1521/worktree/probe_c/detectors/rts.py`, and expect a unit-movement trace; the C sim has no units yet, so the port is of the *shape* (a detector is a pure function over a trace that returns fingerprinted findings), not of the movement rules. The desync detector `tests/qa/t1/desync.py` (PX-05) shows the harness shape: `run_pair(lib, seed, commands, ticks, ...)` builds worlds through the ctypes `lib` fixture and returns a report dataclass. Bug ids with a real C branch today (from `grep OM_BUG_ csrc/*.c`): `OSC_AS_LEVEL`, `RAW_NOT_TREND`, `COMPOSITE_PRE_CLAMP`, `EMPTY_DRIFTS`, `GE_NOT_GT`, `SLOW`, `DRIFT_GATE_IGNORED`, `TELEGRAPH_AFTER_REINFORCE`, `SAME_TICK_REDECLARE`, `INJECT_IGNORED`. Note R11: bug id 0 collides with "no bug" in the debug world's default; check how `tests/csim` fixtures inject before relying on `OSC_AS_LEVEL`.

**Build.** `tests/qa/t1/detectors.py` (fenced QA path beside `desync.py`): two region-level detectors over `om_trace_row` sequences:
1. `frozen_field(rows, field, window)`: a region whose `field` does not change over `window` ticks while the feature that drives it is on (positive control: `OM_BUG_DRIFT_GATE_IGNORED` inverted is not usable; use `OM_BUG_EMPTY_DRIFTS` with an empty-tier region, whose fields must stay frozen on the clean build and move on the planted one, so the detector's *negative* is the planted build; state this inversion in the write-up).
2. `oscillation_as_level(rows, field)`: the oscillator component appears as a level shift rather than a zero-mean delta (positive control `OM_BUG_OSC_AS_LEVEL`; the E-02 control suite has the reference numbers).
Plus `run_all(rows)` and `fingerprint(finding)` mirroring `rts.py:21,99`. A runner `tests/qa/t1/run_trace.py` that builds a world through `lib`, enables the trace, steps N ticks with a fixed seed, reads rows, runs the detectors.

**Pass.** Each detector: fires on its planted build, silent on the clean build, over 500 ticks at 60 regions, under 2 s per run. Report wall time and the finding text.

**Argues against the claim:** if a detector needs anything not in `om_trace_row` (say, which feature was on, or the attack list), say so: that is a trace-schema finding for the design lane.

## PX-7 — whole-suite regression after DONE

**Claim (Factory, "Gates"):** whole-suite regression after every DONE with revert on any new failure.

**Facts.** The incident (`harness_defects_2026-09-17/DECISIONS.md:15`): `test_R_034_06_it_excluded`, 203a1's acceptance test, passes at `c4596ed` and `4cef8e5` and fails at `718e0fd`, where 203b1's accepted candidate rewrote `om_faction_candidates` and dropped the stance exclusion; the harness ran only the current card's `checks[0]`. Agora's gate today (`~/Projects/agora/scripts/build.py:514-556` `predecessor_checks`, `:955-999` `finalize_pass`) re-runs only DONE predecessors sharing the card's `snippet_file`; **no whole-suite mode exists** (decision D4 unimplemented). 203c (`79e5c65`, `50dc6bb`) was the repair.

**Build.** `scripts/specfactory/suite_regression.py`: given a worktree at a pre-merge commit and a candidate diff, record the failing-id set of `tests/csim` before, apply the diff, record after, report new failures (ids red after and green before) and wall time for each run. Tests in `tests/specfactory/` with a synthetic two-test fixture.

**Replay.** Worktree at `4cef8e5`; the candidate diff is `git diff 4cef8e5 718e0fd -- csrc/` (203b1's merge; confirm it is the only change in that range, otherwise narrow to `csrc/faction.c`). Expected: `test_R_034_06_it_excluded` in the new-failure set, so the gate rejects. Negative control: replay 203c's own diff (`79e5c65`) onto its parent; new-failure set empty, gate accepts. Also replay the predecessor-only rule (`predecessor_checks` logic: only tests of DONE cards sharing `csrc/faction.c`) over the same diff to show whether it would have caught it (it did not, live).

**Measure.** Wall time of the whole `tests/csim` run at HEAD (`-p no:cacheprovider`, single process) and with `-n auto` if `pytest-xdist` is installed in the venv (check; do not install). The design says "seconds"; report the real number and the count of tests at HEAD. If the whole suite is over 120 s, say so: that changes where the gate sits (per candidate vs per DONE).

**Pass.** Known-bad merge rejected with the right test named; known-good merge accepted; wall time reported.

## PX-14 — parent-patch fence

**Claim (Factory, "Gates"):** parent patches obey the same ownership check as cards; a patch may touch only the function the diagnosis names and never another card's scope.

**Facts, corrected from the program text.** R7j (`DECISIONS.md:84`): the offending change was `a493cfd` (`fix(csrc): om_step_telegraphs implemented the wrong damage formula`, R7g's hand patch), which, while fixing 204a1's damage formula in `om_step_telegraphs`, also added conquest detection, garrison and ownership transfer, which are 204b1's job in `om_step_resolve`. The fix that removed them is `c7f4a5d`. (`c3aa447` is a different, later event: 204b1 hand-implemented in its own function, an escalation with sign-off, not a fence violation.) Cards: `~/Projects/agora/queue/204a1-e05-telegraph-maturation.md` (`snippet_file: csrc/resolve.c`, `snippet_symbol: "om_step_telegraphs, om_tick_attacks"`); `queue/parked/204b1-e05-conquest-garrison.md.retired` (`snippet_symbol: "om_step_resolve"`, same file). Ownership map: `scripts/specfactory/card_lint.py:261-278` `find_owning_card(queue, symbol, exclude_path, this_snippet_file)`.

**The important subtlety.** `a493cfd` touched only `om_step_telegraphs`, which 204a1 owns. A function-ownership check alone would *accept* it. What makes it a violation is that it did another card's job. Two checks, both built:
1. **Function ownership:** every function changed by the diff is in the named card's `snippet_symbol` (reuse `find_owning_card` and the card parser from `card_lint.py`). Catches a patch that edits `om_step_resolve` under 204a1's name.
2. **Scope capture:** run every *other* queued or parked card's acceptance tests (their `checks` from the card frontmatter; the acceptance commands are in the card files) before and after the patch in the worktree; any other card's test that goes red to green means the patch implemented that card's scope. Catches `a493cfd`.

**Build.** `scripts/specfactory/parent_patch_fence.py <card-id> <diff> --queue <agora queue dir> --worktree <path>`: prints OK or names the violation (check 1: function and owning card; check 2: the other card and the tests it turned green). Tests in `tests/specfactory/` with synthetic cards.

**Replay.** (a) `a493cfd` onto its parent under card 204a1: expected rejection by check 2 naming 204b1 and its conquest/garrison tests (find which of 204b1's acceptance tests go green; if none do because 204b1's tests were themselves broken at that date, R7k, say so and use the tests as they stood at `c3aa447` instead, and report both). (b) `c7f4a5d` onto its parent under 204a1: accept. (c) `4945db8` (R7a include fix) under whatever card owned `resolve.c` includes: accept, or report that includes have no owner and how the fence should treat them. (d) Negative control for check 1: a synthetic diff editing `om_step_resolve` under 204a1's name, rejected.

**Pass.** (a) rejected with 204b1 named; (b), (c) accepted; (d) rejected. Wall time of check 2 (it runs many cards' tests; report the count).

## PX-19 — prefetch and resident model

**Claim (Factory, "Pipelining"):** the CPU slot prepares the next card while the GPU builds, so the next attempt starts within one tick of the previous outcome; the worker stays resident (`OLLAMA_KEEP_ALIVE=-1`).

**Facts.** Measured gaps in `~/Projects/agora/runs/cron.log` between a DONE line and the next card's release: 63 s (`cron.log:114249-114252`, 21:50:30 to 21:51:33) and 131 s (`:113276-113278`, 14:40:31 to 14:42:42), then 62 s to the next. `OLLAMA_KEEP_ALIVE` is set nowhere (`/etc/systemd/system/ollama.service` has only `PATH`; `scripts/ollama_client.py:28-39` sends no `keep_alive`), so the 5-minute default applies and the model unloads during long CPU stages. One measured `load_duration` is 14.16 s (`runs/203e-*/.../evidence/tokens/resp_t2.json`). In `build.py`: worktree at `:691-693`, baseline at `:747-756`, prompt at `:870-877`, first model call at `:886-888`.

**Measure, no harness edits.**
1. Over the whole `cron.log`, the distribution of "outcome line to next card's first model call" gaps (write a small parser; the first model call is the first `candidate`/`rung` line of the next run, or the run dir's `state.json` first timestamp; state which you used). Report count, median, p90, max, and how many exceed 300 s (the keep-alive window).
2. By hand, in a scratch worktree of a real parked card (any `queue/parked/*.md.hold` that lints), time each CPU prep step: `git worktree add`, `make -s libouroboros.so`, baseline pytest of `checks[0]`, `card_lint.py`, `card_slice.py --write`, prompt assembly token count (reuse whatever `build.py` uses to count; do not call the model). Sum = the prep time the CPU slot would hide.
3. Model load: from every `resp_*.json` or `state.json` in `runs/` that carries `load_duration`, list the values; compute how much of the per-card wall is loads (count of loads times median load).

**Do not** run Ollama to test `keep_alive` in this batch. Write the one-line change that would set it (`keep_alive: -1` in the `chat_full` payload, or `Environment=OLLAMA_KEEP_ALIVE=-1` in the unit) as a proposal in the write-up for the executor.

**Pass.** Numbers reported: median and p90 gap today; prep time that prefetch would hide; load seconds per card; the projected gap with prefetch plus keep-alive (gap minus prep minus load, floor at the dispatcher's poll interval, which you find in `next.py` or the systemd timer and quote).

## Order and budget

PX-19 first (pure measurement, half a day), then PX-7, PX-14, PX-4. Each is a day or less of doer work. Every PX gets its own commit and SCORECARD row.

## Verification

- `pytest tests/specfactory/` green including new tests; `pytest tests/qa/t1/` green.
- `git worktree list` shows no `/tmp/pxA` entries afterwards; `git status --short` clean of anything but deliverables before each commit.
- E-02 baseline untouched: `pytest tests/csim/test_E02_S0*.py tests/csim/test_E02_gate_drift_trajectory.py tests/csim/test_E02_S160_drift_gate.py` on `main` still 52 passed / 4 skipped.
- Finishing report for Westley: per PX the pass/fail against the stated number, every replay's verdict, wall times, anything that argues against the claim. No design recommendations.
