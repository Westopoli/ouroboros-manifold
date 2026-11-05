# Stage 11 Amendment — Remaining Work

> **Supersedes:** `stage_11_spec_amended.md` (now legacy reference)
> **Date:** 2026-04-20
> **Context:** The world view architecture amendment landed (2026-04-16) and delivered most of what the original spec's Checkpoint C described. Checkpoints A and B groundwork were completed on 2026-04-20. This amendment captures only the remaining work with correct file paths and codebase state.

---

## What's Already Done

### Checkpoint A — Keyframe selector (COMPLETE)

- `simulation/world_view/keyframe_selector.py` — `select_keyframes()` consuming `run_time_jump()` output
- `simulation/world_view/keyframe_message.py` — transport JSON serialization
- `simulation/world_view/time_jump_emitter.py` — `build_time_jump_messages()` (ordered: start → entry/keyframe pairs → end)
- `simulation/test_checkpoint_11a.py` — headless test, passing
- `simulation/test_checkpoint_11b.py` — headless test, passing
- `KEYFRAME_MAX_PER_TIME_JUMP = 12` in `simulation/config.py`

### Checkpoint B — Transport plumbing (COMPLETE)

- `autoload/ui_data_bus.gd` — 4 signals (`time_jump_started`, `time_jump_keyframe`, `chronicle_entry`, `time_jump_ended`) + `proceed_to_next_mission()` / `exit_to_main_menu()`
- `autoload/sim_bridge.gd:_dispatch()` — routes `time_jump_start`, `time_jump_end`, `keyframe`, `chronicle_entry` message types to UIDataBus signals
- `simulation/config.py` — all Stage 11 tuning values (kill switches, scroll cadence, world view visuals, camera choreography, ambient liveliness, exit timing)

### World view component architecture (COMPLETE — from amendment)

All of these exist with working implementations, not stubs:

- `scenes/shared/world_view/world_view_shell.gd + .tscn` — orchestrator with full delegation API
- `scenes/shared/world_view/world_view_data.gd` — signal-based data store (regions, connections, territories, highlights)
- `scenes/shared/world_view/renderers/settled_reach_renderer.gd + .tscn` — emissive sphere region nodes with halos, territory bubbles with border circles, connection lines, flash tweens (region + conflict), highlight pulsing
- `scenes/shared/world_view/cameras/orbital_camera_3d.gd + .tscn` — `move_to_region()`, `move_to_overview()`, `start_ambient_motion()`, `stop_ambient_motion()`
- `scenes/shared/world_view/era_world_view_config.gd + .tres` — era-to-renderer/camera mapping

---

## What's Left to Build

### Checkpoint C — Renderer & Camera Enhancements

The amendment delivered functional visuals. Three items remain:

**C1 — Border vs trade connection distinction** (minor)
- File: `scenes/shared/world_view/renderers/settled_reach_renderer.gd`
- Current: all connections render identically (solid lines)
- Needed: `border`/`both` → solid faction-color lines; `trade` → thinner dashed lines
- The renderer already reads `connection_type` from WorldViewData — just needs visual branching in `_on_connection_added()`

**C2 — Border contour SubViewport pass** (new)
- Files: `scenes/shared/world_view/renderers/settled_reach_renderer.gd` (manages SubViewport), new `scenes/shared/world_view/renderers/territory_contour.gdshader`
- Per-faction influence fields rendered additively to separate channels; contour shader draws where `max - second_max` falls within threshold band
- Config: `WORLD_VIEW_CONTOUR_THRESHOLD`, `WORLD_VIEW_CONTOUR_BRIGHTNESS`, `WORLD_VIEW_CONTOUR_LINE_THICKNESS_PX`
- This is the most complex remaining visual item. Can be deferred if it blocks progress — the territory bubbles with border circles already provide faction boundary visibility.

**C3 — Camera `move_to_position()`** (required for sequencer)
- File: `scenes/shared/world_view/cameras/orbital_camera_3d.gd`
- Add: `move_to_position(position: Vector3, look_at: Vector3, duration: float) -> void`
- The sequencer needs this for scripted pull-back/push-in choreography beyond `move_to_region` and `move_to_overview`
- Implementation: same tween pattern as existing `_animate_to()`, but with explicit position + look_at instead of orbit parameters

**Prove-it:** Test harness exercising connection type distinction, contour rendering (if built), and camera position targeting against a mock world state. Visual verification by Westley.

⛔ STOP.

### Checkpoint D — Chronicle Scroll Panel (new scene)

Standalone UI scene, tested outside sequencer.

**New files:**
- `scenes/world/chronicle_scroll_panel.tscn + .gd` — queue, printer, entry list
- `scenes/world/chronicle_entry.tscn + .gd` — one row; three states (printing / printed / expanded)
- `scenes/world/chronicle_entry_expansion.tscn + .gd` — overlay for expanded entry

**Panel API:**
```gdscript
func begin_time_jump(total_entries: int) -> void
func queue_entry(entry_data: Dictionary) -> void
func start_printing(entry_id: String) -> void
func end_time_jump() -> void
func pause() -> void
func resume() -> void

signal entry_finished_printing(entry_id: String)
signal entry_expansion_opened(entry_id: String)
signal entry_expansion_closed(entry_id: String)
signal all_entries_finished()
```

**Behavior:**
- Word-by-word fade-in at `SCROLL_PER_WORD_CADENCE_SEC` with `SCROLL_PER_WORD_FADE_DURATION_SEC`
- Click-to-expand shows `expanded_form` text, pauses sequencer, blinking cursor stops
- Dismiss resumes sequencer and printing
- Single-expand accordion (opening one closes others)
- Slide-in: 400ms ease-out-cubic from screen right per `docs/bible_history/bible_2_00_animation_strategy.md` sweep_line

**Prove-it:** Harness feeds mock entries, exercises word-by-word fade-in, click-to-expand with pause/resume, state transitions. Westley reviews.

⛔ STOP.

### Checkpoint E — Time Jump Sequencer (new scene — the main orchestrator)

**New files:**
- `scenes/world/time_jump_sequencer.tscn + .gd`

**Open question — mission end signal:** The tactical scene (`scenes/tactical/tactical.gd`) currently has no `mission_ended` signal. The sequencer needs a trigger to start the pull-back phase. Options:
1. Add a `mission_ended` signal to `tactical.gd` (fired when the engine reports mission complete)
2. Route through UIDataBus (sim emits a `mission_complete` message type)
3. Add to `sim_bridge.gd` dispatch

This must be resolved before implementing the sequencer. The sim side needs to detect "mission over" and emit it through the transport.

**Open question — pause menu exit:** The original spec references `scenes/tactical/pause_menu.gd` for wiring "Exit to Main Menu." No pause menu file exists. Either it needs to be created or the exit path wired through whatever in-mission UI exists. Confirm with Westley.

**Six-phase flow:**
1. `mission_ended` received → instance WorldViewShell, `setup_era(EraConfig.ACTIVE_ERA_ID)`, populate initial world state from sim data
2. Pull-back: 2.5s ease-in-out-cubic, tactical camera → world view. Tactical scene freed 500ms in. World view opacity ramp 1.0s overlapping.
3. Slide chronicle scroll panel in. Start auto camera (orbit at 0.03 rad/sec).
4. On each `time_jump_keyframe` → advance world view (territory changes, flashes, connection changes via shell API). On each `chronicle_entry` → queue and print in scroll panel.
5. On `time_jump_ended` → decelerate orbit to 0.01 rad/sec, highlight destination region, show Proceed/Exit footer. Ambient liveliness flickers.
6. Proceed → clear highlight, slide scroll out, push-in 3.0s to target region → emit signal for next mission load. Exit → `UIDataBus.exit_to_main_menu()`, fade-to-black 600ms.

**Sim-side wiring:** `simulation/pipe_transport.py` currently only runs the tactical tick loop. When a time jump is triggered, the transport needs to call `time_jump_emitter.build_time_jump_messages()` and send those messages. This wiring doesn't exist yet.

**Prove-it:** Scripted fake time jump (3 keyframes, 2 entries) runs end-to-end in Godot. Westley reviews the full six-phase flow.

⛔ STOP.

### Checkpoint F — Full Loop Integration

Wire sequencer to live Stage 10 pipeline. New game → complete mission → pull-back → world view with real keyframes and chronicle entries → expand mid-narration (pause) → dismiss (resume) → Proceed → push-in → next briefing.

**Prove-it:** Westley plays one full mission → time jump → next mission cycle.

⛔ STOP.

### Checkpoint G — Exit Path Verification

Two exit paths:
1. **Post-narration:** Proceed/Exit footer on scroll panel → fade-to-black → main menu → clean restart
2. **In-mission:** (depends on pause menu resolution from Checkpoint E) → same fade treatment → clean restart

No exit during pull-back transition.

**Prove-it:** Westley exits from both paths, confirms clean termination and restart.

⛔ STOP.

### Checkpoint H — Performance Budget

60 FPS at 1920×1080 during busy time jump (10 keyframes, 10 entries, 8 factions, 40 regions, 60 connections, 3 simultaneous flashes). SubViewport pass (if border contour built) ≤ 4ms above baseline. Scroll ≤ 0.5ms.

**Prove-it:** Profiler screenshot, numerical table.

⛔ STOP.

---

## Checkpoint E Implementation Plan

Recorded here so it survives context boundaries.

**New files:**
- `scenes/world/time_jump_sequencer.gd + .tscn` — 6-phase orchestrator (setup → pull-back → narration → streaming → ended → exit)
- `scenes/tactical/pause_menu.gd + .tscn` — ESC overlay (Resume / Exit to Main Menu)
- `scenes/debug/test_time_jump_sequencer.gd + .tscn` — auto-scripted fake time jump test

**Modifications:**
- `autoload/ui_data_bus.gd` — add `mission_completed(mission_result: Dictionary)` signal
- `autoload/sim_bridge.gd` — add `mission_complete` dispatch to `_dispatch()`
- `autoload/scene_router.gd` — register `time_jump_sequencer` scene

**Six phases:** (1) Create SubViewportContainer + SubViewport + WorldViewShell, populate from params. (2) Pull-back 2.5s, world view fade 0→1 over 1.0s. (3) Slide chronicle panel in, start auto camera orbit. (4) On `time_jump_keyframe` → apply territory changes/flashes. On `chronicle_entry` → queue + print. (5) On `time_jump_ended` → slow orbit, highlight destination, show Proceed/Exit footer. (6) Proceed → slide scroll out, push-in 3.0s → mission_briefing. Exit → main menu.

**Sim-side wiring deferred to F:** `pipe_transport.py` only has a TacticalEngine, not the full strategic World. Wiring `run_time_jump()` requires the strategic→tactical bridge. E tests Godot side with fake UIDataBus signals; F connects to live sim.

**Pause menu:** dark overlay, ESC toggle, Resume + Exit buttons. One-line addition to `tactical.gd:_ready()`.

**Test harness:** auto-emits time_jump_started → 3 keyframes + 2 entries → time_jump_ended on timers. Manual pause/resume/skip buttons.

---

## Polish Items (deferred)

- **Player camera override during time jump.** Bible says player can click-drag to override auto-orbit. `orbital_camera_3d.gd` has no mouse input handling. Not blocking — core sequencer flow works without it.

## Era-Specific Renderer Note

The Settled Reach world view is visually derived from the main menu's particle galaxy. The world view = ambient particle galaxy backdrop + region node locations + faction border visualization overlaid. Other space-themed eras may reuse/modify this renderer; non-space eras (Roman, etc.) will have completely different renderers. The current renderer's region nodes + territory bubbles + border contour are the functional overlay — don't over-engineer beyond this.

## Kill Switches (in `simulation/config.py`, already added)

- `WORLD_VIEW_ENABLED` — if false, skip world view entirely (text card fallback)
- `CHRONICLE_SCROLL_ENABLED` — if false, world view runs without scroll
- `KEYFRAME_STREAM_ENABLED` — if false, sim emits single placeholder keyframe

---

## Key File Reference

| Purpose | Path |
|---------|------|
| World view shell | `scenes/shared/world_view/world_view_shell.gd` |
| World view data | `scenes/shared/world_view/world_view_data.gd` |
| Settled Reach renderer | `scenes/shared/world_view/renderers/settled_reach_renderer.gd` |
| Orbital camera | `scenes/shared/world_view/cameras/orbital_camera_3d.gd` |
| Era config | `autoload/era_config.gd` (`ACTIVE_ERA_ID`) |
| Era theme resolver | `autoload/era_theme_resolver.gd` |
| UIDataBus | `autoload/ui_data_bus.gd` |
| SimBridge dispatch | `autoload/sim_bridge.gd` (`:_dispatch()`) |
| Scene router | `autoload/scene_router.gd` |
| Tactical scene | `scenes/tactical/tactical.gd` |
| Time jump (sim) | `simulation/time_jump.py` (`run_time_jump()`) |
| Keyframe selector | `simulation/world_view/keyframe_selector.py` |
| Keyframe messages | `simulation/world_view/keyframe_message.py` |
| Time jump emitter | `simulation/world_view/time_jump_emitter.py` |
| Pipe transport | `simulation/pipe_transport.py` |
| Config (all tuning) | `simulation/config.py` |

---

## Stage 12 Handoff Note

Stage 12 inserts a mission debrief between `mission_ended` and the sequencer's pull-back. When Stage 12 is built, the sequencer's trigger changes from `mission_ended` to `debrief_completed`. Build the sequencer with `mission_ended` for now — Stage 12 swaps it.
