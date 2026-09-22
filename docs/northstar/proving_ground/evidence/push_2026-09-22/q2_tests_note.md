# Q2 tests note — T1 tactical RTS detectors (2026-09-22 two-day push, wave-2 row Q2)

Fenced tests wrote, red now. Impl `scripts/qa/rts_detectors.py` M2 job, not exist yet.

## File and fixtures

`tests/qa/t1/test_rts_detectors.py` — 14 tests.

Fixtures (`tests/qa/t1/fixtures/*.json`, 9 files, plain JSON array = trace, no wrapper):

- `rubberband_planted.json` / `rubberband_clean.json` — uid 1, 2 ticks. Planted: teleport +40 wu backward against velocity at tick 2 (limit at 150 wu/s = 11.25 wu). Clean: normal 7.5 wu/tick step.
- `stuck_planted.json` / `stuck_clean.json` — uid 2, 40 ticks (= STUCK_WINDOW). Planted: frozen at origin, target 5000 wu away, `target_active` true whole window. Clean: steady 7.5 wu/tick toward a far target.
- `backwards_planted.json` / `backwards_clean.json` — uid 3, 5 ticks (= BACKWARDS_MIN_TICKS). Planted: facing fixed 0 while velocity points −x for all 5 ticks (dot negative every tick, streak hits 5 on tick 5). Clean: same motion, facing = pi (aligned).
- `dropped_order_planted.json` / `dropped_order_clean.json` — uid 4, 4 ticks (= DROPPED_GRACE+1). Command `ack=0` at tick 1 commanding (500,300). Planted: unit `tx,ty` never move off (0,0) inside grace. Clean: `tx,ty` snap to (500,300) by tick 2.
- `run_all_dedup.json` — uid 1 and uid 5, 2 ticks, both independently plant the rubberband bug (different uid/tick/position) — proves `fingerprint()` collapses both to one key via `run_all`.

Hand math checked against a throwaway reimplementation of probe-C's exact detector logic (rubberband/stuck/backwards/dropped_order) with the six constants below, run over all 9 fixtures plus the 4×4 cross matrix. Every planted fixture fires exactly once, right uid, right tick, on its own detector only; every clean fixture and every off-target planted fixture stays silent on all four. Dedup fixture gives two same-fingerprint rubberband hits. No surprises before writing the test file itself.

## Thresholds and their rule ids

Named constants live in `scripts/qa/rts_detectors.py` (M2 writes them); test file asserts exact expected value, cites rule:

| Constant | Value | Rule cited |
|---|---|---|
| `RUBBERBAND_FACTOR` | 1.5 | R-099-02 (Raider 150 wu/s = 7.5 wu/tick @ 20 ticks/s); factor gives 11.25 wu/tick backward ceiling, margin above R-097-05 collision-push jitter |
| `STUCK_WINDOW` | 40 | R-099-02 tick rate (40 ticks = 2 s); long enough past a single R-097-03 steering wait |
| `STUCK_MIN_DISP` | 0.05 | bug catalog #2 "zero displacement"; floor below even R-097-06's worst pre-block slow (×0.65 at d=0.7) |
| `STUCK_MIN_DIST` | 25.0 | R-095-05 arrival tolerance = 1.5 × collision radius 15 (R-097-05) = 22.5 wu; set just above so an arrived unit never reads stuck |
| `BACKWARDS_MIN_TICKS` | 5 | R-100-02 turn-rate caps (6.0/4.0/2.5 rad/s); outlasts one R-097-03 deflection so a mid-turn slew doesn't false-fire |
| `DROPPED_GRACE` | 3 | R-096-07 (commands applied before state advances, in arrival order); catalog #4 "no state change within N ticks" |

`OM_BUG_MOVE_RUBBERBAND = 1100` local enum in the integration test, comment "F5 moves it into conftest". Checked against decision 6 of the push brief: E-13 (movement-and-command) owns the 1100s `OM_BUG_*` range — 1100 is correct, not a guess.

## Red proof

Real run today:

```
tests/qa/t1/test_rts_detectors.py:51: in <module>
    from scripts.qa.rts_detectors import (
E   ModuleNotFoundError: No module named 'scripts.qa'
1 error in 0.10s
```

Collection error, expected — module not exist.

Stub-shim check (scratch dir, PYTHONPATH-injected namespace package, never touched repo `scripts/`, deleted after): stub returns one deliberately-wrong `Finding` per detector call and constants = 0, so import succeeds and every test runs its real body. Result: 13 failed, 1 skipped, 0 errors — every failure `AssertionError` (wrong uid/value/count), zero `ImportError`/`AttributeError`/`TypeError`. Confirms the test file itself is sound; only the missing/wrong impl fails it. Integration test skips correctly (`hasattr(dbg_lib, "om_tactical_trace_read")` false today — confirmed directly against the built `libouroboros_dbg.so`; `om_tactical_step` stub exists, trace reader does not).

Side note, not mine to touch: running the full `tests/qa/t1` dir hits an unrelated `NameError: name '_GENERATED_BINDERS' is not defined` in `tests/csim/conftest.py` (1174-line uncommitted diff there right now — another piece's live in-flight generated-bindings work, matches "F5" mentioned in the brief). Doesn't touch my file's own red-state proof since that used a private raw `ctypes.CDLL` load, not the `lib`/`dbg` fixtures. Flagging only, fenced file, not my job.

## Integration test caveat

`test_integration_scripted_move_is_silent_then_om_bug_move_rubberband_fires` calls hypothetical `om_tactical_unit_spawn` / `om_tactical_command_move` / `om_tactical_trace_enable` / `om_tactical_trace_read` — none exist yet (only `om_tactical_step` stub). Skipif gates on the one function the task named (`om_tactical_trace_read`); the other calls are best-effort names following the existing `om_trace_enable/len/read` pattern and will likely need a signature adjust once B10/B12/F5 land the real API. Flagged here, not fixed — sub-agent scope.
