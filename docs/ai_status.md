# AI Status Board

Single-terminal coordination snapshot. Tracks A/B/C parallel-session model retired 2026-05-15 — see `docs/launch_tracks/_archive/`. Queue and per-item details live in `docs/priority_queue.md`. Full workflow doc: `docs/workflow.md`.

---

## Current Item

*(One row only. Empty between items.)*

- **None active** — Phase 1 reorg in progress (this commit). Top of queue picks up after Phase 1 closes.

---

## Queue (titles only — full detail in `docs/priority_queue.md`)

In-flight items to close BEFORE new queue work begins:

1. **Stage 11g Checkpoint L** — wire `orbital_camera_3d` to `InspectionState.pause_changed`, flip `ENABLE_INSPECTION_PAUSE` → true, run 4-step verification. Plan: `/Users/westley/.claude/plans/sunny-stargazing-spark.md`.
2. **B4 confirm** — Westley's 5-step manual checklist (shift-click, drag-add, double-click type select).
3. **B3 in-game retest** — control groups in actual gameplay (headless 12/12 already).
4. **Track A2 diagnostic** — 50v50 mirror duration 432s vs 150–200s target. One session to confirm cause is in `force_allocator.py` / `power_rating.py` / `damage.py`. If yes → BLOCKED-POST-BETA.
5. **Chronicle text improvement** — capture mid-flight Opus session state or re-queue 6-step plan.

Then Phase 2 inventory sort populates the rest of the BETA-BLOCKER queue.

Out of scope until beta feedback comes in:
- Stage 6 Checkpoint J (RPS FAILs L1/L4) — multi-session arc, governed by Testing Rigor Directive.
- Track C / Stage 13 packaging — stopped 2026-05-09, game not ready to share.

---

## Escalations to Westley (append-only)

Format: `- YYYY-MM-DD: <blocker> — tried: <what> — hypothesis: <best guess> — files touched: <list>`
After escalating, stop work on this claim.

- 2026-05-08 [track-a]: A1 duration target unreachable via scale tuning. `BUDGET_TO_POWER_SCALE` / `MILITARY_TO_POWER_SCALE` landed at 300/2000 (mission unit counts in 30–100 band), but `test_j_duration.py` L7 (50v50 mirror) reports mean = 432.7s vs bible target 150–200s. L7 calls `store.spawn()` directly, bypassing the scale path — duration is governed by per-unit stats / power_rating math downstream. Per track-a STOP rules, suspected bug in `force_allocator.py` / `power_rating.py` is outside A1 scope. **Question:** is 150–200s reachable via scale tuning (no — confirmed) or is the bug downstream? — tried: 5-point sweep [1.0×–4.0×] across archetype/region/budget grid; reverted-config regression — hypothesis: A1 scope ends at unit counts; duration mismatch is A2 territory or downstream bug — files touched: `simulation/config.py:706-707`, new `simulation/test_a1_force_scale_sweep.py`. **Reframed as queue item Q4 (Track A2 diagnostic).**

- 2026-05-08 [track-a]: Pre-existing test failures observed during A1 regression sweep — not introduced by A1, confirmed by reverting config and re-running. Failures:
  - `test_stage8_integration.py` — `numpy.int32` not JSON-serializable in `engine_state.death_log[0].uid`.
  - `test_checkpoint_h.py` — `chronicle_assembler.py:264` reads `region.name`, MockRegion only defines `fields` / `composites`.
  - `test_stage7_checkpoint_k.py` — Raider spawn position drift `(2011.6, 2020.4)` vs `(2000, 2000)`.
  - `test_4b_selector.py` — lineage recency penalty insufficient to flip selection.
  - `test_stage7_checkpoint_m.py`, `test_6j_{matrix,mixed,tuning}.py`, `test_siege_hp_sweep.py` — timeouts at 180s wall.
  - `test_game_loop.py`, `test_stage7_5_checkpoint_i.py` — flaky under parallel CPU load; pass serial. — hypothesis: 9 pre-existing real bugs, 2 parallel-runner flakies — files touched: none (read-only verification).

---

## Completed log

- 2026-05-09 [track-c] Stage 13 — Friends-ZIP packaging: stopped per Westley. Game not yet ready to share. Spec docs remain valid. Drafted files in tree: `build/pyinstaller_spec.spec`, `build/build_zip.py`, `autoload/debug_overlay.gd` (not yet registered as autoload). macOS PyInstaller pass complete; Windows pass deferred. Full state at stop documented in archived track_c spec.
- 2026-05-08 [track-b] B3 — Control groups swapping bug: code landed, **untested in-game** (logged in `docs/bible/game_bible.md` Operational TODOs). Root cause: digit-1..4 hijack in `_handle_digit` blocking recall. Fix: removed hijack (`1..0` always recalls), exclusive membership in `_bind_group`, deleted orphaned `_select_by_category()` + `_CATEGORY_TYPES`. Headless test `tests/test_input_router_control_groups.tscn` 12/12 pass.
- 2026-05-08 [track-a] A1 — Force allocation scale tuning: closed with caveat per Westley. `BUDGET_TO_POWER_SCALE` / `MILITARY_TO_POWER_SCALE` at 300/2000 (`simulation/config.py:706-707`). Mission unit counts in 30–100 band. **Caveat:** scale tuning is physically independent of 50v50 mirror duration (L7 spawns via `store.spawn()`); 432s vs 150–200s bible target miss is a separate combat-balance issue (now Q4 in queue). Diagnostic harness `simulation/test_a1_force_scale_sweep.py` left in place.
- 2026-05-08 [track-b] B2 — Squad-member impact origins: confirmed by Westley. Added public `UnitRenderer.get_squad_world_position(uid, squad_idx=-1)`; `attack_visual_manager.gd` projectile/beam/volley positions and `impact_feedback_manager.gd` burst position now sample a random squad mesh on the firer/target. Bloom emission glow left unit-centered. Burst impact y now follows the squad's layer height. Isolated harness scene at `scenes/debug/test_squad_impact_origins.tscn`.
- 2026-05-08 [track-b] B1 — Unit rotation: closed as already-working. Sim-side facing tests pass clean (5/5 + 9/9). Westley confirmed rotation visible in playthrough.

---

## Standing Notes (informational, not a queue)

- **SIM_UNITS_PER_SIDE changed from 1 → 10** in `autoload/sim_bridge.gd:35` by rotation session. Revert to desired value when rotation work is closed.
- **Chronicle text improvement plan** (Opus session, state unknown) — purely Python-side text pipeline changes; does NOT touch Godot files. Files: `simulation/events.py` (adding `chronicle_prose` field), `simulation/chronicle_assembler.py` (region grounding, word-echo prevention, faction-attributed deltas), `simulation/chronicle_distiller.py` (overlap dedup), `simulation/library/chronicle/fragments.json` (fragment trimming). World view session does not modify `ScrollEntry` shape.
