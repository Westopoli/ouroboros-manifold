# PX batch A finishing report (for Westley)

2026-09-21. PX-19, PX-7, PX-14, PX-4 — the order the brief specified. Evidence only, no design recommendations; that's the design lane's call. Full write-ups: `PX-19-prefetch-resident-model.md`, `PX-07-whole-suite-regression.md`, `PX-14-parent-patch-fence.md`, `PX-04-t1-trace-detectors.md`. First two built by Sonnet doers (this chat planned/reviewed, per the then-current manager pattern); [[feedback-thinker-doer-split]] landed mid-batch — PX-14 and PX-4 were executed directly by this Sonnet chat with no sub-agents, per the corrected rule.

## PX-19 — prefetch and resident model: partial pass

**Pass criteria:** median/p90 gap today, prep time prefetch would hide, load seconds/card, projected gap with prefetch+keep_alive. All four numbers reported.

- Whole-`cron.log` gap distribution (468 pairs): median **134s**, p90 **2205s**, max 1.43M s (~16.6 days — real, pre-continuous-dispatcher history, not a parser artifact). 45% exceed the 300s keep-alive window. Split: 37 "loose" pairs (queue-idle or dispatcher-down) carry almost all the tail (median 5627s); 431 back-to-back pairs median **62s**, matching the brief's own worked examples (63/131/62s) exactly.
- CPU prep for a real stub card (208a1, `csrc/events.c`): worktree add + make + baseline pytest + lint + slice = **2.23s total** — negligible next to any observed gap.
- `keep_alive` is confirmed sent nowhere (neither `ollama_client.py`'s payload nor the systemd unit). The only `load_duration` samples found on disk are 6 distinct values duplicated 672 times (this repo's own harness-defects evidence files, not live per-card telemetry) — real per-card load timing does not exist in `runs/` today. A live sanity pair (qwen3-coder:30b) gave load times 44.55s/49.66s, median **47.1s**.
- Projected gap (median/p90 minus prep minus load, floor 60s from the dispatcher's own `sleep 60`): whole-log median 134s → ~85s; p90 barely moves, 2205s → ~2156s, because the tail is queue-idle/downtime, not prep or load at all.

**Verdict: partial pass.** Prep is real but tiny; load time is real but unmeasured at scale (no telemetry exists to confirm it repeats per card); most of the gap distribution the claim would need to shrink isn't prep or load time in the first place. **Argues against the claim:** cron.log carries no timestamps that separate "waiting for the next card" from "the current card's own multi-candidate build" — a real, unresolved measurement limit stated in the write-up, not papered over.

## PX-07 — whole-suite regression after DONE: pass, with a correction to the incident record

**Pass criteria:** known-bad merge rejected with the right test named; known-good merge accepted; wall time reported.

- Whole-suite gate correctly **rejects** 203b1's merge (`4cef8e5→718e0fd`): new failures `test_R_034_03_factor_one_0_80_tension` plus one control test. Correctly **accepts** 203c's repair (`79e5c65` onto its parent): empty new-failure set.
- **Correction found and confirmed in two fresh worktrees:** `DECISIONS.md:15` names the wrong card. `test_R_034_06_it_excluded` — the test the incident record blames on 203b1 — was already red one card earlier, at `4cef8e5` (203a2 dropped the stance-exclusion check 203a1 had written), not introduced by 203b1 at all. The real regression 203b1 introduced is `test_R_034_03_factor_one_0_80_tension`, which the whole-suite gate does correctly name.
- Predecessor-only replay (mirrors Agora's live `build.py:514-556`/`:955-999` gate) rejects the same diff too, but only via the already-broken `test_R_034_06` — it structurally misses `test_R_034_03`, which no DONE card's acceptance owned at the time. This is the real gap the whole-suite gate closes.
- Wall time at HEAD: **676 tests, 31.98s**, single process. `pytest-xdist` not installed (not installed per instructions, not measured with `-n auto`).

**Verdict: pass.** Named-test literal match to the brief's own phrasing doesn't hold (brief expected `test_R_034_06` named; the real new regression is `test_R_034_03`), documented as the headline finding rather than silently substituted.

## PX-14 — parent-patch fence: partial pass

**Pass criteria:** (a) `a493cfd` rejected, 204b1 named; (b) `c7f4a5d` accepted; (c) `4945db8` accepted; (d) synthetic negative control rejected.

- **(a)** `a493cfd` onto `0d65f9e` under 204a1: check 1 (function ownership) **passes blind** — the diff touches only `om_step_telegraphs`, genuinely 204a1's own symbol, exactly as the brief predicts a bare ownership check would. Check 2 (scope capture: 524 other-card node ids, 66.9s combined) **rejects**, naming `204b1-e05-conquest-garrison` (`test_R_038_03_no_conquest_ever_happens`) among 7 captured tests. Fence overall: **rejected**, 204b1 named — pass criterion met.
- **(b)** `c7f4a5d` (the repair) onto `31199d2` under 204a1: **accepted** cleanly, both checks pass, zero captures.
- **(c)** `4945db8` (bare `#include <math.h>` fix) onto `e024dde`: **accepted** — the diff's single hunk falls before any function definition, so check 1 has zero functions to check. Reported plainly: includes have no owning card in the current `snippet_symbol` data model; not a bug in this probe's tool, a real gap in the ownership schema.
- **(d)** Synthetic negative control (two-card fixture, `om_step_a`/`om_step_b`): a diff editing card B's function under card A's name is **rejected** by check 1 alone, and the same fixture separately reproduces `a493cfd`'s actual mechanism (check 1 blind, check 2 catches) rather than just its outcome.

**Verdict: partial pass.** All four literal Pass criteria hold. Two caveats found and reported, not resolved:
- Two of the seven case-(a) captures (`204a3-e05-core-attack`/`-battle-damage-bands`) are **legitimate downstream unblocking** (they depend on the same formula `a493cfd` correctly fixed), not scope theft. Check 2's mechanical red-before/green-after signal cannot tell the two cases apart; only the 204b1 capture is the real violation.
- Mid-run: Agora's queue is shared across 5 unrelated projects (`agora`, `agora-proving-ground`, `ouroboros-manifold`, `switchboard`, `the-best-salesmen`). An unfiltered first run picked up a `the-best-salesmen` card naming a nonexistent test file, which made `pytest` abort the whole combined invocation and silently report a false 0-failed/0-failed (indistinguishable from a clean pass) instead of erroring. Fixed with a project filter and a returncode guard before any real replay number is reported above.

## PX-04 — T1 detectors on the C trace: pass

**Pass criteria:** each detector fires on its own planted build, silent on the clean build, 500 ticks/60 regions, under 2s/run, wall times and finding text reported.

- `empty_region_drifted`: **0** findings clean, **2** findings under `OM_BUG_EMPTY_DRIFTS` (region 0's economy and tension both non-constant across the run; economy's Finding-recorded first/last happen to coincide at 8.0 by chance of sampling, the detector still correctly flags it via the full sequence, not just the endpoints).
- `oscillator_as_level`: **0** findings clean, **118** findings under `OM_BUG_OSC_AS_LEVEL` (every one of 59 non-empty regions × both oscillator fields).
- Each detector confirmed silent on the OTHER bug's build too (four-way cross-check, not assumed). Wall time **0.012–0.017s** traced-step per run, well under the 2s budget.
- **Two real detector defects found and fixed before trusting either control** (both documented with unit-test proof in the write-up): (1) reusing economy's hardcoded 15-tick oscillator window against tension false-positived on every region of a genuinely clean build, because ALG-01 gives tension an 18-tick period, not 15; (2) `OM_BUG_EMPTY_DRIFTS` promotes a region's live tier from EMPTY to FRONTIER within its first drifting tick, and a clean build never traces an EMPTY-tier region at all, so the first draft's `row.tier == EMPTY` gate was vacuously silent on BOTH builds — it reported zero findings on the planted build, the exact "a check that cannot fail is a defect" failure the project's own rule warns about.

**Verdict: pass.** **Argues against the claim, mildly:** R11 (bug id 0 collides with "no bug", PX-15) means any future T1 detector built against an un-injected debug-build world is not testing a clean baseline; this probe avoided it by using the release lib for the clean case, not by R11 being fixed.

## Everything that argues against the batch-A claims as a set

- **PX-19 and PX-7 together show the factory's own telemetry is thinner than the design assumes.** No real per-card load-time or model-call-timestamp data exists in `runs/` today (PX-19); `cron.log` can't separate "waiting" from "building" (PX-19); the incident record that motivated PX-7 (`DECISIONS.md:15`) named the wrong card, found only by direct replay, not by reading the doc (PX-07).
- **PX-14's scope-capture check has a real false-positive class** (legitimate cross-card dependency unblocking) that this probe reports but does not resolve — automating away that ambiguity is a design decision, not a mechanical one.
- **All four PX use pytest's own FAILED/ERROR-line parsing as ground truth for pass/fail**, inherited from PX-7's `suite_regression.py` and reused directly in PX-14. PX-14 found and worked around one real failure mode of that assumption (a hard pytest abort silently reporting 0/0); no other batch member independently re-checked whether that class of failure could affect its own numbers.
- **Wall-clock numbers throughout are single-machine, single-run** (no repeated-run variance reported for any of the four probes) — stated as a limitation, not remeasured.

## Verification, batch-wide

- `pytest tests/specfactory/` — **172 passed** (PX-19's `test_prefetch_measure.py`, PX-07's `test_suite_regression.py`, PX-14's `test_parent_patch_fence.py`, all in one directory).
- `pytest tests/qa/t1/` — **20 passed** (PX-04's `test_detectors.py` plus the pre-existing `test_desync_detector.py`, PX-05).
- `git worktree list` — clean of every `/tmp/pxA` entry, confirmed after each PX.
- E-02 baseline (`test_E02_S0*.py test_E02_gate_drift_trajectory.py test_E02_S160_drift_gate.py`) — **52 passed, 4 skipped**, unchanged from before the batch.
- Four commits, four SCORECARD rows, all pushed to `main`: `1ce08f1` (PX-19), `51e976c` (PX-07), `5cb32ba` (PX-14), `2387912` (PX-04).
