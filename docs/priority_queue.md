# Priority Queue

Single source of truth for what's next. One item active at a time. See `docs/workflow.md` for how items flow through.

**Status values:** `queued` · `in-progress` · `confirming` · `blocked` · `done`
**Classification:** `BETA-BLOCKER` · `BETA-NICE` · `POST-BETA`

End goal: friends/Steam beta upload.

---

## ⚠ PIVOT 2026-05-18 — Phase 1 Ship Scope (FROZEN)

**This section supersedes everything below.** Plan file: `/Users/westley/.claude/plans/synchronous-stargazing-widget.md`. Bible amend: `docs/bible/game_bible.md ## In Flux ### PIVOT 2026-05-18`.

**Phase 1 ship scope = Pre-Zip BLOCKER gate (below) + Steam launch tasks (this section). EVERYTHING ELSE FROZEN.**

### Frozen until post-launch decision

- BETA-NICE queue (Q#8–Q#25) — all frozen.
- POST-BETA queue — all stays POST-BETA.
- Q#7 Stage 6 J RPS — ship-loose acceptable; combat feel is a known launch limitation.
- All Stage 11g Checkpoints beyond L (M, N, O, P, Q) — frozen.
- All lieutenant / multi-era / multiplayer / grand-strategy / branch system work — KILLED per bible pivot.

### Steam launch tasks (NEW — added 2026-05-18)

These run in parallel with Pre-Zip BLOCKERs and are required for shipping:

- [ ] **S#1 — Steam page draft** — short + long description, tag list, capsule plate. Tags: Strategy + Tactics + Story-Rich + Sci-fi + Indie. Banned: Real-Time-Strategy / RTS / Real-Time / Competitive / Esports. Capsule copy: "pause-and-command tactical with generational chronicle" framing; never use "RTS." Micro-research at draft moment: 1–2hr scan of CK3/Wildermyth/Battle Brothers/Old World capsule wording.
- [ ] **S#2 — Capsule plate art** — main capsule + small + header. Use existing Recraft-or-similar subscription. No paid spend.
- [ ] **S#3 — Screenshots (8–12)** — pause-frame composition, chronicle text overlays, faction map shots. From in-game; no extra art needed.
- [ ] **S#4 — Trailer (60–90s)** — self-edited (Westley has prior video experience). Pause-frame shots, chronicle text overlays, NO frantic-click footage. Micro-research at cut moment: 1hr watching 5–10 reference trailers in pause-tactical/narrative-strategy space.
- [ ] **S#5 — Steam Direct $100 fee + 30-day waiting clock start** — mandatory paid spend; only one. Start as soon as S#1 draft is ready.
- [ ] **S#6 — Next Fest entry** — pick fest in launch window (15min Steam.com check). Submit demo build.
- [ ] **S#7 — Community outreach posts** — r/grandstrategy, r/4Xgaming, r/IndieGaming, GameDiscoverCo public list. Follow community norms. Micro-research at posting moment: 1hr scan of subreddit posting rules.

### Phase 1 budget rules

- **Total work budget: 2–4 weeks from 2026-05-18.**
- **Marketing spend: $0 additional default.** Steam Direct $100 is the only mandatory cost.
- **Walk-away rule:** post-launch = no DLC roadmap, no community management beyond critical bugfix. Attention pivots elsewhere.
- **Reopen criteria:** revenue beats $25k lifetime ceiling within first 60 days AND Westley re-evaluates side-hustle vehicle stack.

### Q#6 Tutorial — locked as BLOCKER

Westley locked 2026-05-15. Sign-off question in old queue body is closed: tutorial IS a BLOCKER.

---

## Pre-Zip Beta Readiness Gate

**ZIP cannot ship to friends until every BLOCKER below is closed.** This section supersedes per-item BLOCKER tags in the queue body — read this first.

### BLOCKERS (must close pre-ZIP)

**Audit pass 2026-05-16:** Every row below was rescoped after combing the codebase. Many items advertised as "build from scratch" are actually wiring jobs on top of Stage 10 + 12 infra. Don't trust the row title — read the **Built / Wired / Missing** block.

- [ ] **Save/resume world-view v1** — currently no way to leave and come back to the same simulation; restarts every launch.
  - Built: `simulation/save_writer.write_sim_state`, `save_loader.load_sim_state`, `scenes/load_game/`, main menu CONTINUE, `AUTOSAVE_SLOT_ID="autosave"` in config, `UIDataBus.trigger_autosave(loop_phase)` sender.
  - Wired: nothing end-to-end. UIDataBus sends `{"type":"autosave"}` command; no sim-side handler receives it.
  - Missing: (a) `World/Region/Faction/stances/chronicle` → JSON-safe dict serializer, (b) reverse dict → entities deserializer, (c) sim-side command handler for `"autosave"` that calls serializer then `write_sim_state("autosave", state)`, (d) Godot boot path that loads `autosave` slot and skips `new_game` if present.
- [ ] **Save/resume tactical mid-mission state**
  - Built: `TacticalEngine.export_full_state()` + `restore_from_state()`, `write_tactical_state`, `load_tactical_state`, `consume_tactical_state`, `has_tactical_state`.
  - Wired: nothing end-to-end (no Godot caller).
  - Missing: in-mission pause-menu UI (Q#24 overlaps), autosave hook on abandon/quit, resume-on-mission-start branch that loads tactical.json + calls `restore_from_state`.
- [ ] **Mission map movement speed**
  - Built: `tactical.gd PAN_SPEED=1500`, `UIDataBus.edge_scroll_speed` setting (clamped 200–6000, persisted via ConfigFile), zoom-scaled pan.
  - Wired: setting flows into pan but no UI surface to change it.
  - Missing: either retune the default constant (1-line change after Westley plays a mission with different speeds) OR add a Settings slider. Pick one. Likely retune is enough for ZIP.
- [ ] **Mission objectives clarity (first-time-player)** — 11d gate-passed but in-mission UX still unclear.
  - Built: `scenes/tactical/hud.gd` objectives list w/ progress bars + 6 objective-type descriptions, `mission_marker.gd` in-world beacons.
  - Wired: HUD + beacons populated from snapshot deltas.
  - Missing: a pre-mission briefing screen that names the objective in plain language, OR a first-time tutorial tooltip on the HUD entry. Overlaps with **In-game tutorial** below — likely solved together.
- [ ] **In-game tutorial** — simple, barebones, lore-tone (chronicle voice). NOT a Discord call / README onboarding. Locked as BLOCKER 2026-05-15.
  - Built: `scenes/onboarding/onboarding.gd` (difficulty + archetype picker), `onboarding_store.py`. That's the entire prior surface.
  - Wired: onboarding runs once before first mission.
  - Missing: everything else — tutorial content (`simulation/library/tutorial/`), trigger logic on first mission, hint surface in mission scene. Only true "build from scratch" BLOCKER.
- [x] **Stage 11g Checkpoint L** — inspection pause wire-up. Q#1 below. *(confirmed 2026-05-15)*
- [x] **B4 in-game confirm** — selection upgrades manual checklist. Q#2 below. *(confirmed 2026-05-15)*
- [x] **B3 in-game retest** — control groups. Q#3 below. *(confirmed 2026-05-15)*
- [ ] **Stage 13 packaging**
  - Built: `build/pyinstaller_spec.spec` (mac), `build/build_zip.py` (full pipeline with `--version`/`--game-name`/`--godot-preset`/`--skip-*` args), `autoload/debug_overlay.gd` (F3-toggle FPS/tick/units, 79 lines fully implemented), main menu version label `v0.9.0`, `IS_RELEASE_BUILD` flag.
  - Wired: pipeline runs end-to-end on Mac.
  - Missing: (a) `DebugOverlay="*res://autoload/debug_overlay.gd"` line in `project.godot [autoload]` (one-line fix), (b) Windows PyInstaller spec (`build/pyinstaller_win.spec` scaffold), (c) privacy modal scene + main-menu trigger, (d) clean-install verify on a fresh Mac + Windows host. No drafting from scratch required.

**Dropped from gate (2026-05-16 audit):**
- ~~State-of-faction summary~~ — already built. `scenes/world/faction_info_panel.gd` shows status (Rising/Stable/Waning/Defeated), archetype, tech tier, region list. `scenes/debrief/debrief.gd` + `simulation/debrief_data.py` cover end-of-mission. Westley should play a session and confirm what's there is sufficient before reopening.

### Steam Direct timeline (post-friends-ZIP path, separate from gate)
- Steam Direct = **$100 app fee**.
- 30-day waiting period **starts at fee payment**, not at submission. Westley has not paid yet → Steam path cannot ship in <30 days regardless of build readiness.
- **Implication:** friends-beta ships as the Stage 13 ZIP (PyInstaller bundle). Steam Playtest is post-friends-beta.

### How to use this gate
- Before picking the next queue item, check this list. Pre-ZIP BLOCKERs come before anything else.
- An item with `[x]` in `launch_todo.md` does NOT imply "ships to friends OK" — we learned that the hard way with 11d Objectives. The gate above is authoritative.
- When a gate BLOCKER closes, check it off here AND add the queue-body Q# entry beneath.

---

## In-flight (close before new queue items start)

### Q#1 — Stage 11g Checkpoint L: pause coordinator wire-up          [status: done 2026-05-15] [BETA-BLOCKER]
Why: Inspection pause flag was off; region clicks didn't freeze chronicle/ambient camera.
Branch: `wn/feat-stage11g-l-pause`
Outcome: `orbital_camera_3d.gd` subscribed to `InspectionState.pause_changed` (calls `stop_ambient_motion()` on pause, `start_ambient_motion()` on resume). Flags flipped: `autoload/feature_flags.gd` `ENABLE_INSPECTION_PAUSE = true`, `simulation/config.py` matching. Verified in Godot: region click freezes chronicle + ambient drift; empty-space click resumes; Open-faction button opens faction view cleanly.
Followup: chronicle colored-mention clickability (panel-from-text) is Checkpoints N + O — separate item (task #11). The original test-deliverable step 3 ("double-hold a region") was confused phrasing for the multi-holder pause refcount; that behavior works (region_panel + expansion holders release independently) but is not user-visible until N+O lands.
Plan: `/Users/westley/.claude/plans/sunny-stargazing-spark.md`.

### Q#2 — B4 confirm: selection upgrades manual checklist          [status: done] [BETA-BLOCKER]
Why: Code landed (shift-click/drag adds, double-click selects type on-screen). Headless 5/5 pass. Needs Westley's eyes in actual gameplay.
Branch: n/a (merged; pure verification)
Test deliverable: Manual checklist (5 steps) preserved in archived track_b doc + queue history.
Definition of done: All 5 pass in-game. Mark done in `launch_todo.md`.
Depends on: nothing.

### Q#3 — B3 in-game retest: control groups          [status: done] [BETA-BLOCKER]
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

### Q#5 — Chronicle text improvement          [status: skipped — POST-BETA] [WAS BETA-NICE → POST-BETA]
Skipped 2026-05-15. Chronicle is "better" in current state and the design is changing substantially post-beta — refining further now would be churn against work that'll be redone. Any in-progress edits from the Opus session stay in tree until the post-beta redesign picks them up or discards them.

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
