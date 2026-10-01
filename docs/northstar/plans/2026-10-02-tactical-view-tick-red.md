# tests/test_tactical_view.gd realtime tick red on the B6 candidate

Status: diagnosis only, nothing fixed. Candidate = origin/push/B6-loadscreen 271c2eaa merged with push/TD-missionover3 ca3dc10 (tip 0ae5738). Baseline = origin/main 0f88fad1.

## Root cause

Hypothesis A confirmed with a twist of B. B6 moves the weighted mission draw into the jump, so the Godot live fixture (`ensure_session(1, DEFAULT_N_REGIONS, DEFAULT_FEATURES)` then `step(10)`, seed 1) now draws a mission with 1,073 live units; on main the same fixture draws 859. 1,073 is above OM_TACTICAL_HIGH_LOAD_UNITS (1,000), so `tactical_view.gd` `_tactical_tick_period()` returns 2 and `_process()` requests 10 `tactical_step_n` calls per second instead of 20 (R-099-03, working as written). The pipe's tactical frame `tick` is the pipe's own call counter (`g_tactical_tick`, csrc/pipe/om_pipe.c), +1 per `om_tactical_step` call, not the sim's `base_tick` (+2 per call at high load, csrc/unit.c). So the test's `qa_state().tick` advances 10 in one second. Sim base ticks still advance at 20 per second; the client is correct.

## Evidence (probe scripts in a scratch copy, removed afterwards)

- Candidate, seed 1: units=1073 period=2, 60 x `_process(1/60)` advanced tick by 9 to 10 (rerun; test reports 10). Main, seed 1: units=859 period=1, advanced 20.
- Per-step pipe time is not the cause: candidate qa_step(1) 9-21 ms, qa_step(10) 55 ms; main 11-18 ms and 41 ms. 10 calls fit in a second easily, and the cap TACTICAL_MAX_STEPS_PER_FRAME=10 is not hit.
- Same fixture other seeds (units, candidate / main): 2: 348/675, 3: 491/514, 4: 753/3174, 5: 1481/685, 6: 570/652, 7: 759/460, 11: 438/814. Only the drawn size moves; both trees hit the high-load branch for some seed.
- `SimBridge: _read_framed header err=14 after 0 bytes` appears on both main and the candidate at pipe shutdown. Unrelated noise.

## Rule or fixture

The assertion (test_tactical_view.gd line ~507) states the rule value: 20 base ticks per second (R-099-02, `TACTICAL_BASE_TICKS_PER_SECOND`). But it measures the frame call counter, which equals base ticks only at 1,000 live units or fewer. So the red is a fixture-assumption failure: the fixture's drawn mission is big. The mission size is a drawn value, not a rule. No threshold is wrong and the view code is not wrong.

## Proposed fix (propose only)

Pick a fixture that draws at most 1,000 live units on the candidate, with no threshold change. On the candidate, seeds 2, 3, 4, 6, 7 and 11 all do (348, 491, 753, 570, 759, 438), but seed 4 is above 3,000 on main, and seeds 1 and 5 are above 1,000 on one side. Seed 2, 3, 6, 7 or 11 gives period 1 on the candidate; of these 3 and 6 are under 1,000 on main too, so use 3 or 6 for both trees. The change is the seed argument in `_run_realtime_step_tests` (and `ensure_session` + comments in `_run_c54_tests`, which cites "seed 1 ... 572 units" and is already stale) in tests/test_tactical_view.gd. Also worth a test-defect ledger row: the comment at line 470 says the base rate holds regardless, but the frame tick is a call counter. A second option is to assert on a high-load pair (a >1,000-unit seed expects ~10 calls) as its own test; that adds coverage for R-099-03 but needs a Westley look.

Owners: tests/test_tactical_view.gd is a fenced test file (test-defect class, fix by the test owner with a ledger row, not by a builder). scenes/tactical_c/tactical_view.gd (client) and csrc/pipe/om_pipe.c need no change.
