# AI Status Board

Shared coordination file for parallel Claude Code sessions working on the launch push. Up to **four concurrent sessions** are expected:

- **Stage 11g (C2)** — world view / chronicle / faction palette work
- **Track A** — sim balance, headless tuning (`docs/launch_tracks/track_a_sim_and_balance.md`)
- **Track B** — tactical mechanics & combat polish (`docs/launch_tracks/track_b_tactical_mechanics.md`)
- **Track C** — Stage 13 friends-ZIP packaging (`docs/launch_tracks/track_c_stage_13_packaging.md`)

A fifth seat — the **overlord** (Opus, summoned by Westley on demand) — mediates cross-track conflicts and escalations. It is not always running.

---

## Rules

1. **Read before pull.** First action in any session: `git pull`, then read this file end-to-end before claiming work or editing any file. The state here changes between every commit from any of the four sessions.

2. **Claim before edit.** Every code change requires a claim under "Active Claims." Commit and push the claim *before* editing code. The claim is the lock — if it isn't on `origin`, you don't hold it.

3. **One active claim per session.** Finish, release (move to "Completed"), then claim the next item. Don't hold claims you aren't actively working — others may be waiting on the file.

4. **Touch only your scope.** Each track doc has a "Scope (out)" table. Honor it. If a fix seems to require a file outside your scope, escalate; do not edit.

5. **Don't edit other sessions' lines.** You may edit only:
   - Your own claim line under Active Claims.
   - Append-only sections (Cross-Track Signals, Escalations, Completed).
   Never modify or delete another session's claim, signal, or escalation. If a signal directed at you is resolved, *you* mark it `[resolved YYYY-MM-DD]` inline — don't delete it.

6. **Status values for your own claim:**
   - `claimed` — actively working
   - `ready-for-confirm` — code done, waiting on Westley to verify visually or run checklist
   - `blocked` — cannot proceed; blocker note required
   - When done: move the line to "Completed" with date and one-line summary.

7. **Cross-Track Signals are append-only.** Format below. Anyone may post; only the addressee marks resolved. Never edit or delete another session's signal.

8. **Escalations are append-only and stop work.** When you escalate, you stop on that claim. Do not retry, do not pivot to "fix it differently," do not pick up another claim in the same area until Westley or the overlord responds. Escalation is the end of your turn.

9. **Shared-file protocol.** These files are touched by more than one track:
   - `project.godot` — `[autoload]` is C2's, `[application]` is Track C's. Different blocks merge cleanly, but post a Cross-Track Signal *before* editing the file so others know to pull.
   - `docs/launch_todo.md` — append-only completion edits; small surface, but post a signal before editing if your edit is more than a one-liner.
   - `simulation/pipe_transport.py` — flagged by both A and C. Coordinate via signal before any edit.
   - `build/pyinstaller_spec.py` — Track C owns; Track A appends to `hiddenimports` reactively only when C signals.
   - This file (`ai_status.md`) — claim and signal edits only; structural changes go through the overlord/Westley.

10. **Branch discipline.** Each track owns its own branch (named in your session's brief). Push frequently. Merges to the shared launch branch happen at Westley's call, not autonomously. Never `git checkout/restore/stash` without confirming the working tree state with Westley first.

11. **Escalation triggers (broader than the track docs' STOP lists).** Escalate immediately on any of:
    - A test fails after a change you made.
    - A test that previously passed now fails (even if you didn't change related code — `git pull` may have).
    - The track doc's "STOP-and-escalate" conditions trigger.
    - Output looks "off" but you're not sure why.
    - You'd need to widen an invariant, loosen a tolerance, or skip a test case the test was meant to catch.
    - You'd need to edit a file outside your scope.
    - Two checkpoints in the track doc seem to conflict.
    - Anything not explicitly covered by your track doc.

12. **The overlord is not always watching.** Westley relays escalations to the overlord when needed. Don't wait silently — when you escalate, **post the escalation here AND tell Westley in chat**. Then stop.

---

## Active Claims

- [ ] Improve chronicle text output — **claimed by: Opus session (rotation/chronicle)** — `claimed` — implementing 6-step plan: prose event names, region grounding, faction-attributed deltas, word-echo prevention, overlap dedup, fragment trimming. *(Track A's A5 should defer until this is released.)*

- [ ] Stage 11.5 / 11g — World View 3D Territory Visualization — **claimed by: Opus session (world view) [aka C2]** — `claimed` — actively iterating checkpoints. Tracks B and C must respect C2's scope (see track docs).

- [ ] Track B / B4 — Selection upgrades (input_router.gd) — **claimed by: Track B (tactical)** — `ready-for-confirm` — implemented (a) shift-click / shift-drag adds to selection; (b) left-button double-click selects all friendly visible-on-screen units of the clicked unit's type. Item (c) auto-category hotkeys dropped per Westley (hotkey scheme reworked later). New headless test `tests/test_input_router_selection.tscn` drives real `_click_select` / `_box_select` against a SubViewport-hosted Camera3D — 5/5 pass; B3 test still 12/12.
  - **Files edited:** `scenes/tactical/input_router.gd` (added `_box_additive` member, `_pick_unit_at` helper, `_double_click_select`; threaded `additive` through `_finish_selection` / `_click_select` / `_box_select`).
  - **New files:** `tests/test_input_router_selection.gd` + `.tscn`.
  - **Manual confirm checklist:**
    1. Click an empty area → selection clears (regression check).
    2. Click unit A, shift-click unit B → both selected.
    3. Box-drag over 5 units (no shift) → those 5 selected, prior selection gone.
    4. Box-drag over a different group with shift held → original 5 + new units, no duplicates.
    5. Double-click a raider → all on-screen friendly raiders selected. Pan camera so some raiders go off-screen, double-click again → only on-screen ones selected. Double-click an enemy unit → no-op (not selection_eligible).

---

## Cross-Track Signals (append-only)

Format: `- YYYY-MM-DD [from-track] → [to-track]: message`
Resolution: addressee appends ` [resolved YYYY-MM-DD]` inline; never delete.

- 2026-05-08 [track-c] → [c2]: Stage 13 Checkpoint D needs `autoload/debug_overlay.gd` registered in `project.godot [autoload]` (the block C2 owns). File is drafted at `autoload/debug_overlay.gd`; off by default; F3-toggled FPS/Tick/Units/Sim status overlay; read-only, satisfies invariant I10. Track C is **not** editing `project.godot` — please add the line `DebugOverlay="*res://autoload/debug_overlay.gd"` at the end of `[autoload]` (after `FeatureFlags`) when you next push the autoload block, and reply-resolve here. Track C is stopping at C2 per spec STOP gate until then. [withdrawn 2026-05-09 — Track C stopped per Westley; Stage 13 deferred until game ready to share]
- 2026-05-08 [track-c] → [all]: Stage 13 spec text (`docs/stage_specs/stage_13_spec.md`, Checkpoint D) says debug overlay reads tick from `SimBridge` and units from `UIDataBus`. In actual code, `current_tick` and `units` live on `TacticalBridge` (mirrors `autoload/bug_report_manager.gd:38, :94` and `autoload/mission_metrics_recorder.gd:95`). Overlay reads from TacticalBridge. Flagging so future spec-compliance audits don't read this as a violation. No code change requested. [withdrawn 2026-05-09 — Track C stopped]

---

## Escalations to Overlord / Westley (append-only)

Format: `- YYYY-MM-DD [track]: <blocker> — tried: <what> — hypothesis: <best guess> — files touched: <list>`
After escalating, stop work on this claim.

- 2026-05-08 [track-a]: A1 duration target unreachable via scale tuning. Sweep over `BUDGET_TO_POWER_SCALE` / `MILITARY_TO_POWER_SCALE` chose **300 / 2000** (2× baseline of 150 / 1000) — puts mission unit counts in the requested 30–100 band across archetypes (defensive_stand, assault, reconquest, siege_breaking, counterinsurgency) and region states (mil/pop 30/50/80, capacity 0.3/0.5/0.8, budget 100/300/500). Edge: siege_breaking on a weak region drops to 27 player units (3 below band), BUDGET path can exceed 100 at high budgets. Diagnostic: `simulation/test_a1_force_scale_sweep.py`. **The blocker:** `test_j_duration.py` L7 (50v50 mirror) reports mean = 432.7 s vs bible target 150–200 s (`bible_combat.md`). The scale constants don't drive that test (L7 calls `store.spawn()` directly), so no value of `BUDGET_TO_POWER_SCALE` / `MILITARY_TO_POWER_SCALE` can close the gap — duration is governed by per-unit stats / power_rating math downstream. Per track doc, "bible targets unattainable with any reasonable scale value (suggests the bug is in force_allocator.py or power_rating.py, not the scale)" is an explicit STOP trigger. **Question:** is the 150–200 s target reachable via scale tuning (no — confirmed), or is the bug downstream in `force_allocator.py` / `power_rating.py` and outside A1 scope? — tried: 5-point sweep [1.0×, 1.5×, 2.0×, 3.0×, 4.0×] across archetype/region/budget grid; full `simulation/test_*.py` regression at 300/2000; reverted-config regression to confirm pre-existing failures (separate escalation below) — hypothesis: A1 scope ends at unit counts; duration mismatch is A2 territory or a downstream bug (force_allocator power math, power_rating multipliers, or tactical engine pacing) — files touched: `simulation/config.py:706-707` (scales 150→300, 1000→2000), new `simulation/test_a1_force_scale_sweep.py` (diagnostic harness only).
- 2026-05-08 [track-a]: Pre-existing test failures observed during A1 regression sweep — **not introduced by A1**, confirmed by reverting `config.py` to 150/1000 and re-running. Logging here so they don't disappear. Not Track A's to fix unless Westley reassigns. Failures (running `python3 simulation/test_*.py` individually):
  - `test_stage8_integration.py` — `numpy.int32` not JSON-serializable in `engine_state.death_log[0].uid`.
  - `test_checkpoint_h.py` — `chronicle_assembler.py:264` reads `region.name` but the test's MockRegion only defines `fields` / `composites`.
  - `test_stage7_checkpoint_k.py` — Raider spawn position drift (got `(2011.6, 2020.4)`, expected `(2000, 2000)`).
  - `test_4b_selector.py` — lineage recency penalty insufficient to flip selection.
  - `test_stage7_checkpoint_m.py` — fails ~155 s in (didn't capture exact assert; can re-run if useful).
  - `test_6j_matrix.py`, `test_6j_mixed.py`, `test_6j_tuning.py` — timeout at 180 s wall (likely just slow, not failures, but blocking the parallel sweep).
  - `test_siege_hp_sweep.py` — timeout at 180 s wall.
  - `test_game_loop.py` — flaky under parallel CPU load (4 workers); passes serial.
  - `test_stage7_5_checkpoint_i.py` — determinism check non-deterministically fails (~1 in 3 under parallel load); passes serial. Possibly a real determinism issue surfacing under load, possibly just a race in the harness — flagging.
  — tried: reverted config and re-ran all 11 to confirm they fail on baseline too; `test_game_loop` and `test_stage7_5_checkpoint_i` pass when run serially — hypothesis: 9 are pre-existing real bugs/breakages independent of A1; 2 are parallel-runner flakies — files touched: none for these (read-only verification only). Stopping per rule 8 / 11.

- 2026-05-08 [track-c]: C1 needs a Windows host for the PyInstaller `.exe` build — this machine is darwin (macOS) and PyInstaller cannot cross-compile to a Windows binary. Per track doc note for Checkpoint A, the plan is: (a) draft `build/pyinstaller_spec.py` with the entry point and an initial `hiddenimports` list, (b) optionally run a Linux PyInstaller pass to validate that import list against the frozen sim, (c) stop and let Westley iterate the actual `ouroboros_sim.exe` build on a Windows machine. Confirming this plan before writing the spec. — tried: nothing yet (escalating before code per rule 12 / track doc "DO NOT TRY TO SOLVE PROBLEMS YOURSELF") — hypothesis: Westley owns the Windows iteration loop; Track C produces the spec + the rest of the host-agnostic build pipeline (`build_zip.py`, `README.txt`, `feedback.txt`) — files touched: none yet. [withdrawn 2026-05-09 — Track C stopped per Westley; Stage 13 deferred until game ready to share]

---

## Standing Notes (informational, not a queue)

- **SIM_UNITS_PER_SIDE changed from 1 → 10** in `autoload/sim_bridge.gd:35` by rotation session. Needed 10v10 to properly test facing. Affects unit counts in briefing data. Revert to desired value when rotation work is closed if needed.

- **Chronicle text improvement plan** (rotation/chronicle session) — purely Python-side text pipeline changes. Does NOT touch Godot files, scroll UI, or world view rendering. Files being modified:
  - `simulation/events.py` — adding `chronicle_prose` string field to each TEMPLATES entry (no behavioral changes)
  - `simulation/chronicle_assembler.py` — region grounding, word-echo prevention, faction-attributed deltas
  - `simulation/chronicle_distiller.py` — cross-entry overlap dedup
  - `simulation/library/chronicle/fragments.json` — trimming verbose fragments
  - World view session does not modify the `ScrollEntry` dataclass shape.

---

## Completed

- 2026-05-08 [track-b] B1 — Unit rotation: closed as already-working. Sim-side facing tests (`simulation/test_facing_convergence.py`, `simulation/test_facing_snapshot_propagation.py`) pass clean (5/5 + 9/9). Westley confirmed rotation is visible in playthrough. Prior `Opus session (rotation/visuals)` claim was stale and is removed; closing per Westley's permission.
- 2026-05-08 [track-b] B2 — Squad-member impact origins: confirmed by Westley. Added public `UnitRenderer.get_squad_world_position(uid, squad_idx=-1)` accessor; `attack_visual_manager.gd` projectile/beam/volley positions and `impact_feedback_manager.gd` burst position now sample a random squad mesh on the firer/target instead of the unit's logical center. Bloom emission glow left unit-centered (unit-wide damage flash, not a localized impact). Burst impact y now follows the squad's layer height (was hardcoded 0). Sim-side facing tests stayed green. Isolated harness scene at `scenes/debug/test_squad_impact_origins.tscn`.
- 2026-05-08 [track-a] A1 — Force allocation scale tuning: closed with caveat per Westley. `BUDGET_TO_POWER_SCALE` / `MILITARY_TO_POWER_SCALE` landed at **300 / 2000** in `simulation/config.py:706-707` (2× baseline). Mission unit counts now in 30–100 band across archetype/region/budget grid; force_allocator + mission generator path tests green. **Caveat (separate from A1):** scale tuning is physically independent of the 50v50 mirror duration metric — `test_j_duration.py` L7 spawns via `store.spawn()`, bypassing the mission pipeline — so the 432 s vs 150–200 s bible target miss is a real combat-balance issue but not solvable here. Logged on `launch_todo.md` "Fix unit balance" line for separate triage. A2 (per-unit balance) not picked up per Westley — combat balance is his call on staffing. Diagnostic harness `simulation/test_a1_force_scale_sweep.py` left in place. A1 escalation in Escalations section stays for record. Pre-existing failures escalation also stays for Westley triage.
- 2026-05-08 [track-b] B3 — Control groups swapping bug: code landed, **untested in-game** (logged in `docs/bible/game_bible.md` Operational TODOs alongside the Windows PyInstaller checkpoint). Root cause: digit-1..4 hijack in `_handle_digit` blocking recall. Fix: removed hijack (`1..0` always recalls), exclusive membership in `_bind_group` (option B — newly-bound uids stripped from other groups), deleted orphaned `_select_by_category()` + `_CATEGORY_TYPES`. Headless test `tests/test_input_router_control_groups.tscn` 12/12 pass. Manual checklist in the bible TODO entry.
- 2026-05-09 [track-c] Stage 13 — Friends-ZIP packaging: stopped per Westley. Game not yet ready to be shared; Stage 13 deferred. Track C session terminated. Spec docs (`docs/launch_tracks/track_c_stage_13_packaging.md`, `docs/stage_specs/stage_13_spec.md`) remain valid for future resumption. Drafted `autoload/debug_overlay.gd` and any starter `build/**` files left in tree as-is for reuse. Track C escalation (macOS host) and signals to C2/all withdrawn inline.
  - **Implementation state at stop (for future resumption):**
    - **C1 — PyInstaller sim bundle (Stage 13 Checkpoint A):** macOS pass complete; Windows pass deferred.
      - `build/pyinstaller_spec.py` renamed to `build/pyinstaller_spec.spec` (PyInstaller treats `.py` as an entry script — that was a starter-commit bug). `build/build_zip.py:38` updated to point to the new filename.
      - `hiddenimports` in the spec extended with: `command_ingest`, `mission_contracts`, `map_gen_contracts`, `debrief_data`, `power_rating`, `unit`, `world`, `faction`, `events`, `time_jump`, `world_view`, `world_view.time_jump_emitter`. Validated on darwin/arm64 via `/tmp/sim_smoke.py` — bundle 32 MB, cold ready 5.60s, warm 0.25s, length-prefixed JSON protocol intact, `ready_for_tactical` → `snapshot` roundtrip works, `--root <tmpdir>` writes `logs/sim_stderr.log` next to the chosen root (not inside the bundle), `console=False` produced the `runw` Darwin bootloader (Windows equivalent at build time).
      - PyInstaller installed in `simulation/.venv` (Python 3.14.3, PyInstaller 6.20.0). No third-party deps added — numpy 2.4.4 was already in the venv.
      - **Windows iteration logged as Operational TODO** in `docs/bible/game_bible.md` (commit `a41eeb67234ddd6cf40110c7be8ad40476c317b2`, 2026-05-08 18:33 EDT). Whoever picks Stage 13 back up should run `simulation/.venv/bin/python -m PyInstaller --noconfirm build/pyinstaller_spec.spec` on a Windows host and iterate `hiddenimports` against any `ModuleNotFoundError` from the frozen sim.
      - **Suggested but not done:** add `build/_pyi_dist/`, `build/_pyi_work/`, and `build/_godot_out/` to `.gitignore`.
    - **C2 — Debug overlay (Stage 13 Checkpoint D):** code landed, **not registered as autoload, not in-game tested.**
      - File: `autoload/debug_overlay.gd` — `extends CanvasLayer` (layer 200), F3-toggle in `_unhandled_input`, off by default, top-right ColorRect panel + Label that auto-resizes to label content. Reads `Engine.get_frames_per_second()`, `TacticalBridge.current_tick`, `TacticalBridge.units.size()`, and tracks connection state via `TacticalBridge.connection_state_changed`. Read-only — invariant I10 satisfied. Bible-audited (era-agnostic vocabulary; off-by-default doesn't break "commander, not god"; no sim mutation).
      - **Spec/reality mismatch worth knowing:** `docs/stage_specs/stage_13_spec.md` Checkpoint D says tick comes from `SimBridge` and units from `UIDataBus`. In actual code those fields live on `TacticalBridge` (mirrored by `autoload/bug_report_manager.gd:38, :94` and `autoload/mission_metrics_recorder.gd:95`). Overlay reads from TacticalBridge. Future spec audit should not flag this as drift.
      - **To finish this checkpoint when Stage 13 resumes:** add `DebugOverlay="*res://autoload/debug_overlay.gd"` at the end of `[autoload]` in `project.godot` (after `FeatureFlags`). Block is C2-owned, so coordinate via signal first. Then run the spec test: launch game → verify invisible by default → press F3 in main menu (FPS live, Tick `0`/`N/A`, Units `0`, Sim `disconnected`) → start a mission → verify Tick/Units update live and Sim shows `connected` → press F3 to hide → check renders at 1920×1080 and 1280×720.
    - **C3–C8 not started:** privacy modal, Godot export + sim launch integration, full build script, README/feedback, version label, clean-install verification, final stability — none touched. Spec entries remain authoritative for resumption.
    - **Files in tree but not wired up:** `build/pyinstaller_spec.spec`, `build/build_zip.py`, `autoload/debug_overlay.gd`. Safe to leave; none alter runtime behavior until referenced from `project.godot` or invoked explicitly.
