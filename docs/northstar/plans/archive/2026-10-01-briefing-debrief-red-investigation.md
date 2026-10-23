# Investigation: tests/test_briefing_debrief.gd two reds (2026-10-01)

Caveman-lite. Diagnosis only, no fix committed.

## Symptom

On origin/main, `test_briefing_debrief.gd` is 90 pass / 2 fail:
- `briefing with no setup() shows archetype 8, live frame says 3.0`
- `briefing with no setup() shows deadline_ticks 4436, live frame says 4441.0`

Three consecutive runs here gave identical numbers (8/4436 vs 3/4441). No run-to-run variance found in the file as it stands. See "Variance" below.

## Hypotheses

1. Test bridge and scene bridge open different worlds (seed, n_regions, features). REFUTED. Debug print in `c_bridge._ensure_mission` showed every session has args `[1, 80, [0..7]]`, snapshot tick 20. `live_seed()` is 1 with no `--seed` user arg, and the scene passes `bridge.DEFAULT_*`. Same world arguments.
2. Scene misreads the frame. REFUTED. `mission_briefing.gd` `load_frame` copies `archetype` and `deadline_ticks` straight into `_frame_*`; `qa_state()` returns them unchanged.
3. Unseeded RNG, wall clock or save-dir state. REFUTED for these numbers. Same seed and same command stream give the same frame: fresh bridges always answered 3 / 4441; the pipe is deterministic (the test's own "same seed twice" check passes).
4. The scene's `SimSession` bridge is not fresh: it was already used by earlier scene tests in the same process, and a second `mission_start` on a world that already ran `mission_end` answers a different mission. SUPPORTED.

## Evidence for 4

Instrumented `_ensure_mission` (print bridge id, args, tick, archetype, deadline) and `load_debrief_live` in a scratch edit. One `SimSession` bridge instance (the same object id) shows, in order:
- `mission_start` -> 3 / 4441 (briefing scene self-load in `_run_briefing_tests`)
- `load_debrief_live` with `mission_active=true` -> `mission_end`
- `mission_start` -> **8 / 4436** (next scene self-load on the same world; this is the briefing in `_run_live_tests`)
- later, the same bridge after another end: `mission_start` -> 1 / 5278

Each `mission_end` advances the world, so the next `mission_start` on it picks a different mission. The test's own local `CBridge.new()` is a brand-new world, so it answers 3 / 4441.

Confirmation by scratch edit: adding `SimSession.reset()` immediately before the live-test briefing instantiation gives 92 pass / 0 fail. Scratch edits reverted; not committed.

## Root cause

Order-dependent shared state, not a sim or scene fault. `_run_live_tests` compares the briefing (which uses the process-wide `SimSession.bridge()`, dirty from the earlier briefing and debrief scene tests, where the debrief scene self-loads and ends a mission on that same bridge) against a fresh private bridge. The test only calls `SimSession.reset()` later (after the live briefing, before the C4-4 Deploy block). The second red is the same cause, same frame.

## Which side is wrong

The test. The scene behaves as designed (shared session reuses the running world, per `sim_session.gd` header). Product behaviour that a second briefing after a debrief sees the next mission is correct. The test assumes a pristine session and never establishes it.

## Variance

The numbers in the report (4436/5272, 4441/4440) differ from here (4436/4441). A third mission (1 / 5278) appears on the same bridge after yet another mission_end, so the numbers depend on how many end/start cycles ran on the shared bridge before the assertion, which depends on the checkout's test and scene version. The pipe itself is deterministic. A different commit of the debrief/briefing scenes (extra or fewer `mission_end` calls) changes the count. I did not find any wall-clock or RNG input.

## Proposed fix

One line in `tests/test_briefing_debrief.gd` `_run_live_tests`: call `SimSession.reset()` before instantiating the live briefing (and the live debrief, same reasoning: the debrief's expected band comes from the fresh private bridge's mission_end, while the scene's bridge is reused). Verified green 92/0 for the briefing part.

Owner: `tests/test_briefing_debrief.gd` is listed under pieces C4 and G-legacytests; it is a fenced test, so only a ledger-classed test-defect edit by the Architect/test tier, never a builder. No scene or session file needs to change (`autoload/sim_session.gd` is owned by the galaxy piece, `scenes/mission_briefing/**` and `scenes/debrief/**` and `c_bridge.gd` by C4/C2; none touched).

## Classification

Test-defect (ledger row candidate): test relies on a pristine `SimSession` it never sets up. Not a product bug. Not a skip. No tolerance widened.
