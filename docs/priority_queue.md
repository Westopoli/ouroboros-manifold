# Priority Queue

Single source of truth for what's next. One item active at a time. See `docs/workflow.md` for how items flow through.

**Status values:** `queued` · `in-progress` · `confirming` · `blocked` · `done`
**Classification:** `BETA-BLOCKER` · `BETA-NICE` · `POST-BETA`

End goal: friends/Steam beta upload.

> ⚠️ **Awaiting Westley sign-off on top-5 ranking before Phase 3 starts.** Classifications below are first-pass — items flagged 🟡 need a call. See "Sign-off questions" at bottom.

---

## In-flight (close before new queue items start)

### Q#1 — Stage 11g Checkpoint L: pause coordinator wire-up          [status: in-progress] [BETA-BLOCKER]
Why: Inspection pause flag still off. Without it, region clicks don't actually freeze the chronicle/tweens — system half-built.
Branch: `wn/feat-stage11g-l-pause`
Test deliverable:
- Scene: main game, world view.
- Steps:
  1. Click a region → chronicle prints stop, tweens freeze.
  2. Click empty space → resume.
  3. Double-hold a region → expansion view + region panel.
  4. Open faction button from region panel → faction view opens cleanly.
- Expected: pause/resume visible; no missed frames; no ambient camera drift during pause.
- Fail-look-for: chronicle continues during pause; camera keeps drifting; double-hold broken.
Definition of done: `orbital_camera_3d.gd` subscribed to `InspectionState.pause_changed`; `ENABLE_INSPECTION_PAUSE = true`; verification passes; PR merged.
Depends on: nothing.
Plan: `/Users/westley/.claude/plans/sunny-stargazing-spark.md`.

### Q#2 — B4 confirm: selection upgrades manual checklist          [status: confirming] [BETA-BLOCKER]
Why: Code landed (shift-click/drag adds, double-click selects type on-screen). Headless 5/5 pass. Needs Westley's eyes in actual gameplay.
Branch: n/a (merged; pure verification)
Test deliverable: Manual checklist (5 steps) preserved in archived track_b doc + queue history.
Definition of done: All 5 pass in-game. Mark done in `launch_todo.md`.
Depends on: nothing.

### Q#3 — B3 in-game retest: control groups          [status: confirming] [BETA-BLOCKER]
Why: Headless 12/12. Untested in actual gameplay. Bug was digit-1..4 hijack — needs proof of fix during a real mission.
Branch: n/a (merged)
Test deliverable:
  1. Start mission with ≥3 unit types.
  2. Select units, Ctrl+1 → group 1 bound.
  3. Select different units, Ctrl+2 → group 2; verify uids no longer in group 1.
  4. Press 1 → group 1 recalls.
  5. Press 2 → group 2 recalls.
Definition of done: Westley confirms in mission. Mark done in `launch_todo.md`.
Depends on: nothing.

### Q#4 — Track A2 diagnostic: 50v50 mirror duration miss          [status: done — parked POST-BETA] [WAS BETA-BLOCKER → POST-BETA]
Diagnosed 2026-05-15. Original 432.7s WARN was **~90% test-fixture contamination** — single attack-move to behind-enemy spawn + fog/vision meant columns walked past each other, never re-engaged. Fixed in `simulation/test_j_duration.py`: convergent attack-move on map center, spawn closer to center, asymmetric composition support (`types_b` was never used). Diagnostics added (per-seed survivors + winner).

Post-fixture: deterministic 131s mean, low variance, B always wins ~25v0. Real residual signals:
- 50v50 mirror = 131s vs bible 150–200s (~13% short).
- L5 Strike-mirror = 42s vs 45s min.
- L5 Line/Siege mirror = 1000s stall (edge case — real missions use mixed comp).

**Parked POST-BETA because bible v3.00 RE-OPEN FLAG (`bible_combat.md:383`) already plans a per-branch retcon — Branch 1 (Settled Reach / sci-fi) targets 30–45s engagements, HP drops. Tuning now to hit a target the bible plans to discard is wasted work.** Friends-ZIP ships with current values per bible directive.

Fixture fix lands as a permanent improvement — test now measures real combat duration, not pathing contamination.

Memory: `project_a2_duration_test_fixture.md`.

### Q#5 — Chronicle text improvement: capture or re-queue          [status: blocked] [BETA-NICE] 🟡
Why: 6-step Opus session was running before reorg. State unknown.
Branch: TBD
Test deliverable: TBD once state captured.
Definition of done: Merged + `launch_todo.md` updated, or formally re-queued as fresh item.
Depends on: Westley confirms what (if anything) survived from Opus session.

---

## BETA-BLOCKER queue (ranked, post-Phase-3)

### Q#6 — Tutorial / first-time-player explanation 🟡
Why: Friends won't know what to do without lore-flavored guidance. Beta feedback worthless if testers bounce on confusion.
Test deliverable: launch fresh save → tutorial flow → tester reaches first mission with understanding of controls + objectives.
Definition of done: tutorial sequence covers movement, selection, control groups, mission objective, chronicle.
Depends on: Q#1 (pause coordinator) for any inspection-tied tutorial beats.
**Sign-off question:** Is this a BLOCKER, or do you plan to onboard friends manually (Discord call, written README)? If manual → drop to BETA-NICE.

### Q#7 — Stage 6 Checkpoint J (RPS FAILs L1/L4) [multi-session arc] 🟡
Why: L1 = Strike vs Siege 0% wins. L4 = soft RPS gradient broken. Combat identity for the game.
Branch: `wn/bug-stage6j-rps` (multi-session)
Test deliverable: re-audit every L1–L4 fixture for uncontrolled variables (per Testing Rigor Directive) BEFORE re-running balance assertions. Then individual checkpoint deliverables.
Definition of done: L1–L4 pass; Stage 6 J + K + L closeable.
Depends on: Westley clears Track A2 diagnostic + Stage 11g L (concurrent test-suite churn).
**Sign-off question:** Is RPS playable-enough for friends-beta (Strike never beats Siege would be a brutal first impression) or can it ship loose since "balance feedback" is exactly what beta tests?

---

## BETA-NICE queue

### Q#8 — Stage 11g Checkpoint M: faction palette integration
Why: Faction hues stable across time jumps + vivid/pale by size. Current per-jump even-hue is functional, just less polished.
Test deliverable: 2 consecutive jumps → factions keep hues. Toggle flag → reverts.
Definition of done: `ENABLE_FACTION_PALETTE = true`; all consumers read from `FactionPalette.get_display_color`.

### Q#9 — Stage 11g Checkpoint N+O: chronicle mentions (sim + Godot)
Why: Click faction/region names in chronicle text → camera/panel navigates. Cool feature; not required for core loop.
Test deliverable: click faction name → panel opens, camera pans. Click region name → same.
Definition of done: `ENABLE_CHRONICLE_MENTIONS = true`; both sides wired.

### Q#10 — Fix unit sizing
Test deliverable: pick 3 unit types, eyeball scale vs squad-member meshes + minimap markers.

### Q#11 — Fix main camera pan/zoom feel
Test deliverable: edge-scroll + scroll-wheel zoom in mission scene.

### Q#12 — Fog of war terrain darkening (SC2-style)
Test deliverable: outside vision range → darkened overlay; inside → transparent.

### Q#13 — Color legend for world view
Test deliverable: world view shows faction-color legend; matches `FactionPalette`.

### Q#14 — Pan/drag invert option in settings
Test deliverable: settings toggle flips drag direction.

### Q#15 — "Center view / zoom out" button on world view
Test deliverable: button click → camera reset to default vantage.

### Q#16 — Skip button for chronicle entries (per-entry + skip-all)
Test deliverable: per-entry skip jumps to next; skip-all jumps past sequence.

### Q#17 — Command queuing (shift-queue orders)
Test deliverable: shift-right-click 3 waypoints → unit executes in sequence.

### Q#18 — Map view redesign (Settled Reach v2)
Test deliverable: TBD once design spec exists.

### Q#19 — Regenerate library names (AI-quality pass)
Test deliverable: spot-check 20 generated region/faction names for tone consistency.

### Q#20 — Remove static flyby ship animations (placeholder removal)
Test deliverable: main menu / world view → no flyby placeholders.

### Q#21 — Create production building assets
Test deliverable: reinforcement structures have real art.

### Q#22 — Smooth territory transitions (shader-uniform animation)
Test deliverable: territory color shifts blend instead of pop. (Stage 11 known limitation.)

### Q#23 — Border vs trade connection visual distinction (solid vs dashed)
Test deliverable: borders solid, trade routes dashed.

### Q#24 — Pause menu (in-mission exit path)
Test deliverable: in-mission ESC → menu with resume / settings / exit. Currently untested.

### Q#25 — Performance budget profiling
Test deliverable: 50v50 mission → frame time + sim tick metrics captured.

---

## POST-BETA / explicitly deferred

- **Stage 11g Checkpoint P** — Bible amendments. Docs-only; do after M/N/O ship.
- **Stage 11g Checkpoint Q** — Stage gate sign-off. Depends on L+M+N+O+P.
- **Stage 11f** — Fairness redesign. Blocked on playtest data corpus (i.e. needs the beta).
- **Hotkeys 1-4 auto-assign** — full hotkey scheme rework pending; don't lock in new mappings.
- **Track C / Stage 13 packaging** — Stopped 2026-05-09. Drafted files in tree (`build/pyinstaller_spec.spec`, `build/build_zip.py`, `autoload/debug_overlay.gd` not yet registered). macOS pass done; Windows pass deferred.
- **In-game tutorial** if classified NICE — see Q#6 sign-off question.

---

## Pre-existing test failures (logged, not actively claimed)

Triage POST-BETA unless something escalates them:

- `test_stage8_integration.py` — numpy int32 not JSON-serializable in `death_log`
- `test_checkpoint_h.py` — `chronicle_assembler.py:264` reads `region.name`, MockRegion missing it
- `test_stage7_checkpoint_k.py` — Raider spawn position drift
- `test_4b_selector.py` — lineage recency penalty insufficient
- `test_stage7_checkpoint_m.py`, `test_6j_{matrix,mixed,tuning}.py`, `test_siege_hp_sweep.py` — 180s timeouts
- `test_game_loop.py`, `test_stage7_5_checkpoint_i.py` — flaky under parallel; pass serial

---

## Sign-off questions (need Westley before Phase 3 starts)

1. **Q#4 (A2 diagnostic):** OK with park-POST-BETA if cause is in protected engine files?
2. **Q#5 (Chronicle text):** any state to capture from the Opus session, or re-queue from scratch?
3. **Q#6 (Tutorial):** BLOCKER or NICE? Manual onboarding (Discord/README) acceptable for first beta?
4. **Q#7 (Stage 6 J RPS):** BLOCKER or ship loose (since "tell us combat feel" is exactly the beta question)?
5. **Top-5 order:** proposed Q#1 → Q#2 → Q#3 → Q#4 → Q#6 (or Q#7). Confirm or reorder.
