# AI Status Board (stub)

**This file is no longer the coordination source of truth.** As of 2026-05-15 there is one terminal in flight (Westley's). The multi-terminal coordination need that justified this board is gone.

**Where things live now:**
- **Pre-Zip BLOCKERs + queue:** `docs/priority_queue.md` (top section is the gate)
- **Bug/feature inventory:** `docs/launch_todo.md`
- **Workflow rules:** `docs/workflow.md`
- **Project rules:** `CLAUDE.md`

This file is retained only for the **historical escalations log** below (append-only record of past blockers and how they resolved) and the **completed log** of multi-track-era work, so future archaeology has a single landing page.

---

## Escalations to Westley (historical, append-only)

Format: `- YYYY-MM-DD: <blocker> — tried: <what> — hypothesis: <best guess> — files touched: <list>`

- 2026-05-08 [track-a]: A1 duration target unreachable via scale tuning. `BUDGET_TO_POWER_SCALE` / `MILITARY_TO_POWER_SCALE` landed at 300/2000 (mission unit counts in 30–100 band), but `test_j_duration.py` L7 (50v50 mirror) reports mean = 432.7s vs bible target 150–200s. L7 calls `store.spawn()` directly, bypassing the scale path — duration is governed by per-unit stats / power_rating math downstream. — tried: 5-point sweep [1.0×–4.0×] across archetype/region/budget grid; reverted-config regression — hypothesis: A1 scope ends at unit counts; duration mismatch is A2 territory or downstream bug — files touched: `simulation/config.py:706-707`, new `simulation/test_a1_force_scale_sweep.py`. **Resolved 2026-05-15:** diagnosed as 90% test-fixture contamination; fixture fixed; residual real signal parked POST-BETA per bible v3.00 retcon plan. See `docs/priority_queue.md` Q#4.

- 2026-05-08 [track-a]: Pre-existing test failures observed during A1 regression sweep — not introduced by A1, confirmed by reverting config and re-running. Failures:
  - `test_stage8_integration.py` — `numpy.int32` not JSON-serializable in `engine_state.death_log[0].uid`.
  - `test_checkpoint_h.py` — `chronicle_assembler.py:264` reads `region.name`, MockRegion only defines `fields` / `composites`.
  - `test_stage7_checkpoint_k.py` — Raider spawn position drift `(2011.6, 2020.4)` vs `(2000, 2000)`.
  - `test_4b_selector.py` — lineage recency penalty insufficient to flip selection.
  - `test_stage7_checkpoint_m.py`, `test_6j_{matrix,mixed,tuning}.py`, `test_siege_hp_sweep.py` — timeouts at 180s wall.
  - `test_game_loop.py`, `test_stage7_5_checkpoint_i.py` — flaky under parallel CPU load; pass serial. — hypothesis: 9 pre-existing real bugs, 2 parallel-runner flakies — files touched: none (read-only verification).

---

## Completed log (multi-track era, 2026-05-08 → 2026-05-15)

- 2026-05-15 [reorg] Phase 1+2+2.5 — Coordination consolidation, ranked queue, Pre-Zip Beta Readiness Gate. Multi-track A/B/C model retired. `docs/ai_status.md` collapsed to this stub.
- 2026-05-15 [Q#4] Track A2 diagnostic — 50v50 mirror duration miss resolved as test-fixture contamination, not balance. Fixture fixed in `simulation/test_j_duration.py` (convergent center attack-move; spawn closer to center; asymmetric composition support). Residual 131s vs 150–200s bible target parked POST-BETA per bible v3.00 RE-OPEN FLAG (Branch 1 Settled Reach retcon plans 30–45s engagements). Memory: `project_a2_duration_test_fixture.md`.
- 2026-05-09 [track-c] Stage 13 — Friends-ZIP packaging: stopped per Westley. Game not yet ready to share. Spec docs remain valid. Drafted files in tree: `build/pyinstaller_spec.spec`, `build/build_zip.py`, `autoload/debug_overlay.gd` (not yet registered as autoload). macOS PyInstaller pass complete; Windows pass deferred. Full state at stop documented in archived track_c spec.
- 2026-05-08 [track-b] B3 — Control groups swapping bug: code landed, **untested in-game** (logged in `docs/bible/game_bible.md` Operational TODOs). Root cause: digit-1..4 hijack in `_handle_digit` blocking recall. Fix: removed hijack (`1..0` always recalls), exclusive membership in `_bind_group`, deleted orphaned `_select_by_category()` + `_CATEGORY_TYPES`. Headless test `tests/test_input_router_control_groups.tscn` 12/12 pass.
- 2026-05-08 [track-a] A1 — Force allocation scale tuning: closed with caveat per Westley. `BUDGET_TO_POWER_SCALE` / `MILITARY_TO_POWER_SCALE` at 300/2000 (`simulation/config.py:706-707`). Mission unit counts in 30–100 band. Diagnostic harness `simulation/test_a1_force_scale_sweep.py` left in place.
- 2026-05-08 [track-b] B2 — Squad-member impact origins: confirmed by Westley. Added public `UnitRenderer.get_squad_world_position(uid, squad_idx=-1)`; `attack_visual_manager.gd` projectile/beam/volley positions and `impact_feedback_manager.gd` burst position now sample a random squad mesh on the firer/target.
- 2026-05-08 [track-b] B1 — Unit rotation: closed as already-working. Sim-side facing tests pass clean (5/5 + 9/9). Westley confirmed rotation visible in playthrough.

---

## Standing notes (carried from old board)

- **SIM_UNITS_PER_SIDE changed from 1 → 10** in `autoload/sim_bridge.gd:35` by rotation session. Revert to desired value when rotation work is closed.
- **Chronicle text improvement plan** (Opus session, state unknown) — purely Python-side text pipeline changes; does NOT touch Godot files. Files: `simulation/events.py`, `simulation/chronicle_assembler.py`, `simulation/chronicle_distiller.py`, `simulation/library/chronicle/fragments.json`. Parked POST-BETA per Q#5.
