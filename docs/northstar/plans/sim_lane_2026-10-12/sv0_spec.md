# SV-0: optional `retention` on `mission_end` (debug pipe only)

Source: simviewer plan (`docs/northstar/plans/2026-10-12-simviewer-plan.md`, SV-0) as amended by Westley 2026-10-13 ("go ahead with (c)"): no core change, no header change; the pipe sets unit HP so the sim measures the retention itself. Pre-flight facts read at origin/main 3125ee77.

## Facts (read, not assumed)
- `om_mission_end` (`csrc/mission.c:1514`) measures retention in `om_mission_end_retention` from the player's force units' HP over max HP, weighted by `om_unit_power`; `om_mission_compute_retention` clamps to [0,1].
- `om_unit_set_hp(w, unit_id, hp)` is public (`ouroboros_sim.h:2148`); `om_unit_profile_max_hp(w, type)` (:2138), `om_unit_get_unit_type` (:2122), `om_unit_count` (:2112), `om_unit_get_faction`, `om_player_faction` are public. `handle_assign_commander` (`csrc/pipe/om_pipe.c:1427`) already iterates player units by id 1..`om_unit_count`.
- `objective_complete` is a debug-build verb: `handle_objective_complete` (`om_pipe.c:1730`) answers `error` reason `debug build required` in the release pipe. The viewer therefore drives `pipe/ouroboros_pipe_dbg`.

## Behaviour
1. `mission_end` takes an optional number `retention`. Absent: byte-identical output and state to today (R-077-01 measured retention).
2. Present, debug build (`OM_DEBUG_INJECT`): value outside 0..1 or not a number answers `{"type":"error","name":"mission_end","reason":"bad retention"}` and changes nothing (the mission stays running). Otherwise, before `om_mission_end`, every alive unit of the player faction gets `om_unit_set_hp(w, id, retention * om_unit_profile_max_hp(w, type))`; then the normal path runs. The debrief's `retention` equals the given value (tolerance 1e-9) and its `band` is the sim's own classification of 0.75 x objective score + 0.25 x that retention.
3. Present, release build: `error` reason `debug build required`, nothing changes (same convention as `objective_complete`).
4. Tooling artefact, documented: the HP write also sets commander fate (killed at 0 HP, wounded below 30%, R-077-03). Documented in `docs/architecture.md` beside `mission_end`; the game client never sends the field.

## Pieces
- Test writer (Engineer, Sonnet 5.5): `tests/transport/test_pipe_mission_end_retention.py`, fenced.
- Builder (Doer, Sonnet 5.5): `csrc/pipe/om_pipe.c` (`handle_mission_end` only) and the `mission_end` paragraph in `docs/architecture.md`.
- Then a second Fable audit of the architecture.md paragraph before SV-1 builds.

## Tests (required)
Seed 16, 80 regions, features 0-7 (as `test_pipe_debrief_region_delta.py`), `objective_complete` objective 0 completion 1.0:
- T1 retention 0.0 answers debrief `retention` 0.0 and a band lower than the run without the field (positive control: without it, retention is 1.0).
- T2 retention 0.5: debrief retention 0.5 (1e-9).
- T3 absent: debrief frames equal a run recorded without the field (byte-identical to base).
- T4 retention -0.1, 1.1, and "x": `error` `bad retention`, then a following `mission_end` without the field still answers a debrief (nothing was changed).
- T5 release pipe `pipe/ouroboros_pipe` with `retention` present: `error` `debug build required`.
- T6 band sweep: for each retention in {0.0, 0.25, 0.5, 0.75, 1.0}, the debrief band is non-decreasing in retention (a pipe-level monotonicity check, no threshold values asserted).
Red reason on base: the field is ignored, debrief retention stays 1.0 (T1, T2) and the release pipe answers a debrief (T5).
