# Priority Queue

Single source of truth for what's next. One item active at a time. See `docs/workflow.md` for how items flow through.

**Status values:** `queued` · `in-progress` · `confirming` · `blocked` · `done`
**Classification:** `BETA-BLOCKER` · `BETA-NICE` · `POST-BETA`

End goal: friends/Steam beta upload.

---

## In-flight (close before new queue items start)

### Q#1 — Stage 11g Checkpoint L: pause coordinator wire-up          [status: in-progress] [BETA-BLOCKER]
Why: Pause flag still off. Without it, inspection clicks don't actually freeze the chronicle/tweens — system half-built.
Branch: `wn/feat-stage11g-l-pause` (when picked up)
Test deliverable:
- Scene: launch main game, enter world view.
- Steps:
  1. Click a region → chronicle prints stop, tweens freeze.
  2. Click empty space → resume.
  3. Double-hold a region → expansion view + region panel.
  4. Open faction button from region panel → faction view opens cleanly.
- Expected: pause/resume visible; no missed frames; no lingering ambient camera motion during pause.
- Fail-look-for: chronicle text continues during pause; ambient camera keeps drifting; double-hold fails to open expansion.
Definition of done: `orbital_camera_3d.gd` subscribed to `InspectionState.pause_changed`; `ENABLE_INSPECTION_PAUSE = true`; 4-step verification passes; PR merged.
Depends on: nothing — sub-steps already landed (`InspectionState`, panel host, sequencer, chronicle scroll, settled-reach renderer all subscribed).
Plan: `/Users/westley/.claude/plans/sunny-stargazing-spark.md`.

### Q#2 — B4 confirm: selection upgrades manual checklist          [status: confirming] [BETA-BLOCKER]
Why: Code landed (shift-click/drag adds; double-click selects type on-screen). Headless 5/5 pass. Needs Westley's eyes in actual gameplay before close.
Branch: n/a (already merged; pure verification)
Test deliverable: Manual checklist already in archived track_b doc:
  1. Click empty area → selection clears.
  2. Click unit A, shift-click unit B → both selected.
  3. Box-drag over 5 units (no shift) → those 5 selected, prior selection gone.
  4. Box-drag over different group with shift → original 5 + new units, no dupes.
  5. Double-click raider → all on-screen friendly raiders selected; pan some off-screen, double-click again → only on-screen ones.
Definition of done: Westley confirms all 5 in-game. Then mark done in `launch_todo.md`.
Depends on: nothing.

### Q#3 — B3 in-game retest: control groups          [status: confirming] [BETA-BLOCKER]
Why: Headless test 12/12. Untested in actual gameplay. Bug was digit-1..4 hijack blocking recall — needs proof it works during a real mission.
Branch: n/a (already merged)
Test deliverable:
  1. Start a mission with at least 3 unit types.
  2. Select units, press Ctrl+1 → group 1 bound.
  3. Select different units, press Ctrl+2 → group 2 bound; verify those uids no longer in group 1.
  4. Press 1 → group 1 recalls (camera/select).
  5. Press 2 → group 2 recalls.
Definition of done: Westley confirms in mission. Mark done in `launch_todo.md`.
Depends on: nothing.

### Q#4 — Track A2 diagnostic: 50v50 mirror duration miss          [status: queued] [BETA-BLOCKER → may BLOCK-POST-BETA]
Why: `test_j_duration.py` L7 reports 432.7s vs bible target 150–200s. A1 scale tuning is physically independent of this. Need ONE session to confirm cause.
Branch: `wn/bug-a2-duration-diagnostic`
Test deliverable:
  - Re-run `python3 simulation/test_j_duration.py`.
  - Examine `/tmp/j_duration_50v50.jsonl`.
  - Name the offending unit type / mechanic.
Definition of done: Diagnosis written into queue or escalated. **If cause lands in `force_allocator.py` / `power_rating.py` / `damage.py` (protected engine files), park as BLOCKED-POST-BETA and stop.** If it's a `UNIT_STATS` knob, propose to Westley before changing.
Depends on: nothing.

### Q#5 — Chronicle text improvement: capture or re-queue          [status: blocked] [BETA-NICE]
Why: 6-step Opus session was running before reorg. State unknown. Either capture work product or re-queue the plan.
Branch: TBD
Test deliverable: TBD once state captured.
Definition of done: Either merged + `launch_todo.md` updated, or formally re-queued as a fresh item with its own number.
Depends on: Westley confirms what (if anything) survived.

---

## Queue (BETA-BLOCKER, pending Phase 2 inventory)

*Phase 2 of the reorg plan populates this section. Seed items below from `docs/launch_todo.md` open bugs — to be ranked once full inventory sweep is done.*

- Unit rotation bug (still listed open in `launch_todo.md` — sync drift; need to verify B1 close)
- Impact origins (listed open; B2 done — sync drift)
- Unit sizing
- Camera pan/zoom
- Unit balance (separate from Q#4; broader combat feel)
- Fog darkening
- Command queue (B5 from archived track-b)
- Production assets
- Flyby ships
- Color legend
- Pan/drag invert
- Center button
- Tutorial
- Chronicle skip
- Hotkeys 1-4 rework (note: full hotkey scheme rework pending — don't lock in new mappings)

---

## Out of scope until beta feedback

- **Stage 6 Checkpoint J (RPS FAILs L1/L4):** BETA-BLOCKER tag but explicitly out of scope for current loop. Own multi-session arc. Governed by Testing Rigor Directive — re-audit every L1–L4 fixture for uncontrolled variables BEFORE re-running balance assertions.
- **Track C / Stage 13 packaging:** Stopped 2026-05-09. Drafted files (`build/pyinstaller_spec.spec`, `build/build_zip.py`, `autoload/debug_overlay.gd`) in tree but not wired. macOS PyInstaller pass done; Windows pass deferred. Resume after BETA-BLOCKER queue empty.

---

## Pre-existing test failures (logged, not actively claimed)

- `test_stage8_integration.py` — numpy int32 not JSON-serializable in `death_log`
- `test_checkpoint_h.py` — `chronicle_assembler.py:264` reads `region.name`, MockRegion missing it
- `test_stage7_checkpoint_k.py` — Raider spawn position drift
- `test_4b_selector.py` — lineage recency penalty insufficient
- `test_stage7_checkpoint_m.py`, `test_6j_{matrix,mixed,tuning}.py`, `test_siege_hp_sweep.py` — 180s timeouts
- `test_game_loop.py`, `test_stage7_5_checkpoint_i.py` — flaky under parallel; pass serial
