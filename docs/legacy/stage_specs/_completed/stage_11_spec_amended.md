# Stage 11 — World View, Chronicle Scroll, and Seamless Transition

## Goal

Build the macro-loop visual structure: mission end → camera pulls back → world view emerges → time jump executes with chronicle scroll printing alongside → camera pushes into next mission region → next mission begins. One continuous flow, no loading screens. This is the stage that makes the generational fantasy visible and playable.

## Bible References

Read the hub (`game_bible.md`) plus these spokes:

- `docs/bible_history/bible_2_00_world.md` → "Galaxy View — The Strategic Layer Between Missions" (including Faction territory, Connections, Military activity visualization, Ambient particle field, The pivot point), and "Seamless Transition — No Loading Screens" (including Chapter-boundary exits and Exit transition treatment).
- `docs/bible_history/bible_2_00_chronicle.md` → "Chronicle Scroll — Visual Presentation" (split-screen, Word fade-in, Master timeline, Chronicle–keyframe co-occurrence guarantee, Layout — expanding scroll, Entry interaction states).
- `docs/bible_history/bible_2_00_animation_strategy.md` → full document. Stage 11 reuses the sweep_line / divider primitives, blinking-cursor-as-heartbeat vocabulary, and smooth-fade-over-cuts rule.
- `docs/bible_history/bible_2_00_simulation.md` → "Time Jump Controller" (already implemented; this stage visualizes its output).

Also read these completed amendments (both landed before Stage 11):

- `amendment_world_view_architecture.md` — defines the shell + data + renderer + camera component architecture that this stage's sequencer targets. The shell API is the sequencer's only interface to the world view.
- `amendment_era_agnostic_rendering.md` — defines the `EraThemeResolver` and `EraConfig` system. Stage 11 reads `EraConfig.ACTIVE_ERA_ID` to pass to `shell.setup_era()`.

Do not read other spokes. Stage specs for Stages 6, 7, 7.5 are irrelevant here. Stage 8, Stage 8.5, and Stage 10 specs are consulted for protocol and UIDataBus patterns, see Integration Points.

## Context

Stages 1–4 proved the simulation. Stage 5 proved the chronicle distiller produces real narrative with real names. Stage 6 / 7 / 7.5 / 8 deliver the tactical engine and its renderer. Stage 8.5 landed the `EraThemeResolver` autoload and per-era JSON manifests for the tactical rendering layer. Stage 9 proved the UI shell screens wrap around tactical gameplay with mock data; Stage 10 replaced that mock layer with a live WebSocket bridge to the Python sim.

The world view component architecture was built during the `amendment_world_view_architecture.md` implementation:

- **`WorldViewShell`** (`scenes/shared/world_view/world_view_shell.tscn + .gd`) — the orchestrator. The sequencer talks to this and only this. It owns the data component, instances the per-era renderer and camera via `setup_era()`, and delegates all calls.
- **`WorldViewData`** (`scenes/shared/world_view/world_view_data.gd`) — shared data store. Pure data (regions, connections, territories, highlights). Emits signals on every mutation. No visuals.
- **`SettledReachRenderer`** (`scenes/shared/world_view/renderers/settled_reach_renderer.tscn + .gd`) — the first per-era renderer. Connects to WorldViewData signals and translates them into era-appropriate visuals.
- **`OrbitalCamera3D`** (`scenes/shared/world_view/cameras/orbital_camera_3d.tscn + .gd`) — the first camera component. Handles orbital motion, move-to-region, move-to-overview, and ambient motion.
- **`EraWorldViewConfig`** (`scenes/shared/world_view/era_world_view_config.tres`) — resource mapping era IDs to renderer + camera scene paths.

The main menu continues to instance `world_view_structure.tscn` directly for its decorative particle galaxy — that scene is separate from the world view shell and is unaffected by Stage 11.

Stage 11's work is threefold:

1. **Wire the world view shell to real simulation data** by building the keyframe pipeline that drives `WorldViewData` mutations (region adds/updates, territory changes, connection changes, flashes) through the shell's public API during time jump playback. Enhance the Settled Reach renderer with territory bubble shading and border contour rendering.
2. **Build the chronicle scroll panel** as a Godot UI scene that prints queued entries word-by-word with per-word fade-in, supports click-to-expand with strict pause semantics, and coexists with the world view in an expanding-scroll layout.
3. **Build the seamless transition sequencer** that orchestrates the six-phase flow (pull-back / world view emerges / time jump narration / settle / push-in / next mission), driven by keyframe snapshots and chronicle entries flowing through the UIDataBus.

The seam that makes this possible is Stage 10's UIDataBus. Stage 11 adds two new bus signals (`time_jump_keyframe` and `chronicle_entry`) whose implementations emit data received from the sim over the existing stdio-framed WebSocket transport. The sim side emits keyframe and chronicle messages as new JSON-framed message types riding Stage 8's protocol.

## What to Build

### New files

```
scenes/world/
├── chronicle_scroll_panel.tscn            - UI panel: queue, printer, entry list, expansion overlay.
├── chronicle_scroll_panel.gd
├── chronicle_entry.tscn                   - One entry row; owns its three states (printing / printed / expanded).
├── chronicle_entry.gd
├── chronicle_entry_expansion.tscn         - Overlay panel shown when an entry is expanded.
├── chronicle_entry_expansion.gd
├── time_jump_sequencer.tscn               - The six-phase orchestrator. Root scene for the world-view phase.
├── time_jump_sequencer.gd
└── territory_contour.gdshader             - Post-process shader for border contour between faction influence fields.

scenes/shared/world_view/renderers/
└── territory_bubbles.gdshader             - Spherical influence bubble shader with additive blending.

sim/world_view/
├── keyframe_selector.py                   - Consumes distiller output + ownership-change events, emits keyframe snapshots.
└── keyframe_message.py                    - Serialization of keyframe snapshots to JSON for transport.
```

### Modified files

```
scenes/shared/world_view/renderers/
└── settled_reach_renderer.gd              - Add territory bubble rendering (via territory_bubbles.gdshader),
                                             SubViewport pass for border contour (via territory_contour.gdshader),
                                             multimesh region nodes, connection lines, flash particles, highlight
                                             pulse. The renderer's signal handler stubs from the amendment are
                                             filled with production visuals.

scenes/shared/world_view/cameras/
└── orbital_camera_3d.gd                   - Add move_to_position(position, look_at, duration) for scripted
                                             pull-back/push-in choreography beyond the amendment's move_to_region
                                             and move_to_overview.

autoload/
└── ui_data_bus.gd                         - Add signals: time_jump_keyframe, chronicle_entry, time_jump_started,
                                             time_jump_ended. Add methods: proceed_to_next_mission(),
                                             exit_to_main_menu().

sim_bridge/
└── message_router.py                      - Route new message types ("keyframe", "chronicle_entry",
                                             "time_jump_start", "time_jump_end") to bus signals.

sim/
├── time_jump.py                           - Emit time_jump_start on entry, time_jump_end on exit. Drive
                                             keyframe_selector and distiller, enqueue keyframe + chronicle messages.
└── events.py                              - No behavioral change; keyframe_selector reads the event log.

scenes/main_menu/
└── main_menu.gd                           - Ensure sequencer/shell scene tree from a prior run is fully freed
                                             before main menu instances its own world_view_structure.tscn.

scenes/tactical/
└── pause_menu.gd                          - Wire "Exit to Main Menu" to UIDataBus.exit_to_main_menu() with
                                             fade-to-black treatment matching the post-narration Exit.

config/
└── world_view_config.py                   - NEW: all Stage 11 tuning values (see "Tuning values" section).
```

### Files explicitly NOT created

- No tutorial, no onboarding screen, no mission debrief. Those are Stage 12.
- No save-on-exit serialization. Exit cleanly terminates the run; Stage 12 wires save-on-exit.
- No subscription / entitlement changes. <!-- LEGACY 2026-05-09: subscription model scrapped entirely; see docs/bible_history/game_bible_1_23.md (formerly bible_monetization.md, folded into the hub 2026-05-31) "Current Monetization Model" section. Per-era ownership flags survive; subscription does not. -->

## Input/Output Shapes

### Keyframe message (sim → Godot, new message type over Stage 8 transport)

One keyframe message is emitted per keyframe. Ordered by `tick`. Message type discriminator is `"keyframe"`.

```json
{
  "type": "keyframe",
  "time_jump_id": "tj_0003",
  "keyframe_index": 2,
  "tick": 14820,
  "tick_range_start": 14780,
  "tick_range_end": 14820,
  "chronicle_entry_id": "ce_0017",
  "ownership_changes": [
    { "region_id": "r_07", "old_faction_id": "f_conqueror", "new_faction_id": "f_player" }
  ],
  "military_events": [
    { "kind": "attack", "attacker_region_id": "r_05", "defender_region_id": "r_07" },
    { "kind": "conquest", "attacker_region_id": "r_05", "defender_region_id": "r_07" }
  ],
  "connection_changes": [
    { "kind": "added", "from_region_id": "r_05", "to_region_id": "r_07", "connection_type": "border" }
  ],
  "regions_snapshot": [
    { "region_id": "r_05", "owner_faction_id": "f_player", "significance": 0.64 },
    { "region_id": "r_07", "owner_faction_id": "f_player", "significance": 0.41 }
  ]
}
```

`chronicle_entry_id` is present when this keyframe is paired to a chronicle entry (the co-occurrence guarantee). It is `null` when the keyframe is ownership-change-only (animates silently).

`regions_snapshot` includes only regions whose `owner_faction_id` or `significance` changed since the prior keyframe. Unchanged regions carry forward.

### Chronicle entry message (sim → Godot, new message type)

```json
{
  "type": "chronicle_entry",
  "time_jump_id": "tj_0003",
  "entry_id": "ce_0017",
  "tick_range_start": 14780,
  "tick_range_end": 14820,
  "base_form": "Within a decade of the Battle of the Nak Reach, Commander Vael Sorn retook the system for the Republic.",
  "expanded_form": "Within a decade of the Battle of the Nak Reach, Commander Vael Sorn retook the system for the Republic. The Conqueror's grip on the frontier had weakened..."
}
```

Both fields arrive pre-rendered from the distiller. The renderer treats them as opaque strings.

### Time-jump lifecycle messages

```json
{ "type": "time_jump_start", "time_jump_id": "tj_0003", "span_years": 27, "total_keyframes": 5, "total_entries": 4 }
{ "type": "time_jump_end", "time_jump_id": "tj_0003" }
```

### UIDataBus additions (Godot side)

```gdscript
signal time_jump_started(time_jump_id: String, span_years: int, total_keyframes: int, total_entries: int)
signal time_jump_keyframe(keyframe_data: Dictionary)
signal chronicle_entry(entry_data: Dictionary)
signal time_jump_ended(time_jump_id: String)

func proceed_to_next_mission() -> void
func exit_to_main_menu() -> void
```

### World view shell API (from amendment — exercised by sequencer)

The sequencer calls the shell's public API per `amendment_world_view_architecture.md`:

- `setup_era(era_id)` — called once with `EraConfig.ACTIVE_ERA_ID`.
- `add_region_node(id, position, size, color, faction_id)`, `update_region_node(id, size, color)`, `clear_region_nodes()`
- `set_territory(region_id, center, radius, color)`, `update_territory(region_id, radius, color)`, `remove_territory(region_id)`
- `add_connection(from_id, to_id, connection_type, color)`, `remove_connection(from_id, to_id)`
- `flash_military_activity(region_id, intensity)`, `flash_conflict(from_id, to_id, intensity)`
- `highlight_region(region_id)`, `clear_highlight()`
- `move_camera_to_region(region_id, duration)`, `move_camera_to_overview(duration)`
- `start_auto_camera()`, `stop_auto_camera()`
- `set_opacity(alpha)`

### Chronicle scroll panel API

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

## Integration Points

### With Stage 10 (UIDataBus transport)

Stage 11 extends the UIDataBus rather than replacing it. The transport layer (stdio-framed JSON, Python subprocess lifecycle, `message_router.py`) is unchanged — new message types ride the existing framing. `message_router.py` gets four new route entries.

### With Stage 8 (tactical renderer)

The pull-back phase starts from the tactical camera's final state at mission end. The tactical scene emits `mission_ended`; the sequencer captures the tactical camera's position and begins pull-back choreography through the world view shell's camera. The tactical scene is freed after a configurable delay (500ms default).

### With Stage 5 (chronicle distiller)

The distiller runs inside the time-jump controller (already does). `keyframe_selector.py` consumes the distiller's output as its base set. Ownership-change events from `sim/events.py` are unioned in.

### With the world view amendment architecture

The sequencer instances `world_view_shell.tscn` and calls `setup_era(EraConfig.ACTIVE_ERA_ID)`. All visual operations go through the shell — the sequencer never touches the renderer or camera directly. The shell delegates to WorldViewData (which emits signals), and the Settled Reach renderer responds to those signals. Camera is driven through the shell's delegated methods.

Territory bubbles and border contour rendering are enhancements to the Settled Reach renderer — they extend the renderer's signal handlers (which were stubs or minimal implementations from the amendment) with production visuals. The contour SubViewport is managed by the renderer, not the shell.

### Post-narration hold — sim state and renderer ambience

When the sim emits `time_jump_end`:

1. **Sim side.** The sim runs the mission generator to produce the next briefing, holds it in state (not emitted yet), waits for `proceed_to_next_mission()` or `exit_to_main_menu()`.
2. **Renderer side.** Sequencer decelerates orbit, calls `highlight_region(next_mission_region_id)`, shows Proceed/Exit footer. Kicks off ambient-liveliness cycle: heartbeat pulse on highlighted region, low-intensity flickers on other regions (~1 every 3–5s at 10–20% flash intensity).

### With the main menu

Exit fades to black and loads the main menu. The world view shell and main menu's decorative galaxy are separate scenes — no shared state. `main_menu.gd` ensures any sequencer scene tree from a prior run is freed before instancing its own `world_view_structure.tscn`.

### Kill switches

- `config.WORLD_VIEW_ENABLED` — if false, mission end → text card "GENERATION +N YEARS" → next briefing. No world view, no scroll, no choreography.
- `config.CHRONICLE_SCROLL_ENABLED` — if false, world view runs without scroll. Keyframes animate, no text.
- `config.KEYFRAME_STREAM_ENABLED` — if false (sim side), sim emits single placeholder keyframe.

## Engineering Decisions and Defaults

### Keyframe / chronicle pipeline integration

In `time_jump.py`: run distiller → run keyframe_selector → union ownership-change keyframes. Deduplication: if an ownership-change falls inside a distiller entry's tick range, the keyframe absorbs it (no duplicate).

### Connection edge type rendering

Three sim edge types collapse to two visuals: `border` and `both` → solid faction-color lines; `trade` → thinner dashed. The renderer maps `"both"` to the border visual.

### World view scene architecture

**The main menu and the world view are NOT the same scene.** Main menu instances `world_view_structure.tscn` directly (standalone decorative galaxy). Sequencer instances `world_view_shell.tscn` and calls `setup_era()`. They share no state and no nodes.

### Border contour implementation

Post-process shader in a SubViewport managed by the Settled Reach renderer. Per-faction influence fields rendered additively to separate channels; contour shader draws where `max - second_max` falls within threshold band. One pass, handles enclaves naturally.

### Scroll panel slide animation

Reuse `docs/bible_history/bible_2_00_animation_strategy.md`'s sweep_line. Slide-in: 400ms ease-out-cubic from screen right, world view viewport resizes simultaneously. Slide-out on Proceed: mirror. No slide on Exit — fade to black.

### Camera choreography

- Pull-back: 2.5s ease-in-out-cubic, tactical camera → world view ambient orbit start. Tactical scene freed 500ms in.
- World view emerges: 1.0s opacity ramp overlapping pull-back tail.
- Narration orbit: 0.03 rad/sec via `start_auto_camera()`.
- Post-narration settle: decelerate to 0.01 rad/sec.
- Push-in: 3.0s ease-in-out-cubic, current → target region → tactical start.

All durations are tuning values in `world_view_config.py`.

### Exit behavior

Plain exit, no confirmation modal. Fade-to-black 600ms, main menu loads. Save-on-exit wiring is Stage 12.

### Exit path availability

Two places, satisfying the bible's symmetric chapter-boundary exit:

- **Post-narration:** Proceed/Exit footer on scroll panel.
- **In-mission:** Existing pause menu "Exit to Main Menu" wired to same `exit_to_main_menu()` and fade treatment.

No exit during the pull-back transition (2.5s cinematic beat).

## Tuning Values (defaults; live in `config/world_view_config.py`)

```python
# Keyframe selection (sim side)
KEYFRAME_SIGNIFICANCE_THRESHOLD = 0.55
KEYFRAME_MAX_PER_TIME_JUMP = 12

# Chronicle scroll
SCROLL_PER_WORD_CADENCE_SEC = 0.08
SCROLL_PER_WORD_FADE_DURATION_SEC = 0.20
SCROLL_ENTRY_MIN_DISPLAY_DURATION_SEC = 3.0
SCROLL_PANEL_SLIDE_IN_DURATION_SEC = 0.40
SCROLL_PANEL_SLIDE_OUT_DURATION_SEC = 0.40
SCROLL_PANEL_WIDTH_FRACTION = 0.38

# World view
WORLD_VIEW_TERRITORY_BUBBLE_OPACITY = 0.25
WORLD_VIEW_TERRITORY_BUBBLE_RADIUS_SCALE = 1.6
WORLD_VIEW_CONTOUR_THRESHOLD = 0.08
WORLD_VIEW_CONTOUR_BRIGHTNESS = 1.4
WORLD_VIEW_CONTOUR_LINE_THICKNESS_PX = 1.5
WORLD_VIEW_FLASH_DURATION_SEC = 0.35
WORLD_VIEW_FLASH_INTENSITY = 0.7
WORLD_VIEW_TERRITORY_TRANSITION_DURATION_SEC = 1.0

# Camera choreography
CAMERA_PULL_BACK_DURATION_SEC = 2.5
CAMERA_WORLD_VIEW_FADE_IN_DURATION_SEC = 1.0
CAMERA_AMBIENT_ORBIT_SPEED_NARRATION = 0.03
CAMERA_AMBIENT_ORBIT_SPEED_SETTLED = 0.01
CAMERA_PUSH_IN_DURATION_SEC = 3.0
TACTICAL_SCENE_FREE_DELAY_MS = 500

# Ambient liveliness during post-narration hold
AMBIENT_LIVELINESS_FLICKER_MIN_INTERVAL_SEC = 3.0
AMBIENT_LIVELINESS_FLICKER_MAX_INTERVAL_SEC = 5.0
AMBIENT_LIVELINESS_FLICKER_INTENSITY_FRACTION = 0.15
AMBIENT_LIVELINESS_HIGHLIGHT_PULSE_PERIOD_SEC = 1.5

# Exit
EXIT_FADE_TO_BLACK_DURATION_SEC = 0.6
```

## Checkpoints

Each checkpoint is a STOP point per `dev_rules.md`.

### Checkpoint A — Keyframe selector (sim-side, headless)

Build `sim/world_view/keyframe_selector.py` and `keyframe_message.py`. Headless test against scripted simulation state verifying: every distiller entry → keyframe with matching IDs and tick ranges; every ownership change → keyframe; ordered by tick; JSON round-trips.

Prove-it: printed keyframe table (tick, entry id or "---", ownership count, military count).

### Checkpoint B — Transport round-trip

Wire four message types through `message_router.py`. Scripted sim messages → Godot bus signals fire with expected payloads.

Prove-it: Godot console log showing each signal in order with payload summary.

### Checkpoint C — World view renderer enhancement

The shell, data component, renderer, and camera exist from the amendment. This checkpoint enhances the Settled Reach renderer with production visuals and adds the sequencer's camera position targeting.

Build in order (sub-checkpoints C1–C7, each a STOP):

1. **C1 — Region nodes.** Multimesh-rendered luminous points in the renderer's `_on_region_added()` handler. Faction color for owned regions.
2. **C2 — Connections.** Line3D or ImmediateMesh lines in `_on_connection_added()`. Border = solid faction-color, trade = thinner dashed.
3. **C3 — Territory bubbles.** `territory_bubbles.gdshader` in `_on_territory_set()` / `_on_territory_updated()` / `_on_territory_removed()`. Additive blend, low opacity, faction color. Radius scales with significance.
4. **C4 — Border contour.** SubViewport pass + `territory_contour.gdshader`. Per-faction influence → summed texture → contour at equipotential threshold.
5. **C5 — Flashes.** Particle bursts in `_on_flash_region_requested()` and `_on_flash_conflict_requested()`. Reuse animation-strategy ember/bloom.
6. **C6 — Highlight.** SKIPPED per Westley's request. Basic scale pulse retained, no heartbeat.
7. **C7 — Camera position targeting.** Add `move_to_position(position, look_at, duration)` to `orbital_camera_3d.gd`.

Prove-it: test harness (`tests/test_world_view.tscn`) scripts all operations against a mock world state (3 factions, territories, connections, flashes, camera moves). Westley eyeballs.

### Checkpoint D — Chronicle scroll panel (standalone)

Standalone UI scene tested outside sequencer. Harness feeds mock entries, exercises word-by-word fade-in, click-to-expand with pause/resume, three states (printing / printed / expanded), blinking cursor.

Prove-it: Westley runs harness, verifies printing cadence, fade, expansion, state transitions.

### Checkpoint E — Time jump sequencer (integrated)

Build `time_jump_sequencer.gd` wired to bus signals. The sequencer: (1) on `time_jump_started` → instance shell, `setup_era()`, populate initial world state, slide scroll in, resize viewport; (2) on keyframes → advance world view animation; (3) on entries → queue and print; (4) on `time_jump_ended` → settle orbit, highlight destination, show Proceed/Exit; (5) Proceed → clear highlight, slide scroll out, push-in; (6) Exit → `exit_to_main_menu()`, fade-to-black.

Prove-it: scripted fake time jump (3 keyframes, 2 entries) runs end-to-end. Westley reviews.

### Checkpoint F — Full loop integration

Wire to live Stage 8 / Stage 10 pipeline. New game → complete mission → pull-back → world view with real keyframes and entries → expand mid-narration (pause) → dismiss (resume) → Proceed → push-in → next briefing.

Prove-it: Westley plays one full mission → time jump → next mission cycle.

### Checkpoint G — Exit path verification

Post-narration Exit: fade-to-black, main menu, clean restart. In-mission Exit: pause menu → same treatment → clean restart.

Prove-it: Westley exits from both paths, confirms clean termination and restart.

### Checkpoint H — Performance budget

60 FPS at 1920×1080 during busy time jump (10 keyframes, 10 entries, 8 factions, 40 regions, 60 connections, 3 simultaneous flashes). SubViewport pass ≤ 4ms above baseline. Scroll ≤ 0.5ms. Measure main-menu baseline `B_ms` first.

Prove-it: profiler screenshot, numerical table (B_ms, busy frame time, SubViewport delta, scroll cost).

## Done Condition

Westley starts a new game. Completes a mission. Camera pulls back smoothly — no loading screen. World view emerges with the Settled Reach rendered: region nodes visible, faction territories colored with contoured borders, connections drawn. Chronicle scroll slides in, entries print word-by-word synchronized to keyframes. Click-to-expand pauses everything; dismiss resumes. Last entry finishes, world view settles, destination region pulses, ambient flickers, Proceed/Exit footer. Proceed → scroll slides out, push-in, next briefing. Exit → fade-to-black, clean main menu, clean restart. 60 FPS at 1920×1080.

Westley signs off before Stage 12 begins.

## Progress (2026-04-20)

### Checkpoint A — COMPLETE (headless, no visual testing needed)

Files created:
- `simulation/world_view/__init__.py`
- `simulation/world_view/keyframe_selector.py` — `select_keyframes()` consuming `run_time_jump()` output
- `simulation/world_view/keyframe_message.py` — transport JSON serialization
- `simulation/test_checkpoint_11a.py` — headless test, all checks pass

Config added: `KEYFRAME_MAX_PER_TIME_JUMP = 12` in `simulation/config.py`

### Checkpoint B — GROUNDWORK COMPLETE (transport plumbing; visual verification deferred)

Files modified:
- `autoload/ui_data_bus.gd` — 4 signals (`time_jump_started`, `time_jump_keyframe`, `chronicle_entry`, `time_jump_ended`) + `proceed_to_next_mission()` / `exit_to_main_menu()`
- `autoload/sim_bridge.gd` — routing for `time_jump_start`, `time_jump_end`, `keyframe`, `chronicle_entry` in `_dispatch()`
- `simulation/config.py` — all Stage 11 tuning values (kill switches, scroll, world view, camera, ambient, exit)

Files created:
- `simulation/world_view/time_jump_emitter.py` — `build_time_jump_messages()` (ordered emission: start → entry/keyframe pairs → end)
- `simulation/test_checkpoint_11b.py` — headless test, all checks pass

**Remaining for full B verification:** Run Godot with a scripted sim emitting these messages; confirm signals fire with correct payloads in console. Blocked on map/world-view scene not being testable yet.

### Checkpoint C — COMPLETE (renderer enhancement)

C1 (region nodes), C2 (connections — no-op by design), C3/C4 (territory metaball shader replacing Voronoi/contour), C5 (flashes — random white spark bursts), C6 (highlight — SKIPPED per Westley), C7 (camera position targeting — already existed). Tested via `scenes/debug/test_world_view.tscn`.

### Checkpoint D — COMPLETE (chronicle scroll panel)

All files built and tested via `scenes/debug/test_chronicle_scroll.tscn`:
- `scenes/world/chronicle_scroll_panel.gd` — full API with slide_in/slide_out
- `scenes/world/chronicle_entry.gd` — word-by-word fade, 3 states, blinking cursor, click-to-expand
- `scenes/world/chronicle_entry_expansion.gd` — overlay with dismiss

**Tuning note:** Word fade duration is intentionally 3–8s (slow materialization effect), not the 0.20s in config tuning values. The config value `SCROLL_PER_WORD_FADE_DURATION_SEC` is not used — the entry uses its own longer fade for a ghostly slow-reveal feel.

### Checkpoint E — COMPLETE (time jump sequencer)

Files created:
- `scenes/world/time_jump_sequencer.gd` + `.tscn` — six-phase orchestrator (INIT → NARRATION → SETTLING → PROCEEDING/EXITING)
- `scenes/debug/test_time_jump.gd` + `.tscn` — test harness with scripted 3-keyframe, 2-entry fake time jump

Wired to UIDataBus signals. World view resizes to left 62% when scroll slides in. Proceed fades to black → main menu (fallback when no live sim). Exit fades to black → main menu. Tested with scripted data.

**Known limitations (expected, addressed in F):** Regions appear on first keyframe, not on time_jump_start. Territory transitions are instant (no smooth animation — attempted batched timeline with debounced shell rebuilds, staggered flashes, and cross-fade but the metaball raymarching shader rebuilds the entire mesh per faction on every change, causing visible pops regardless of batching strategy; needs a fundamentally different approach such as animating shader uniforms directly). Proceed sends `proceed_to_next_mission` only when live sim is running.

### Checkpoints F–H — COMPLETE (with known gaps)

Stage 11 signed off. The core loop works: new game → mission → pull-back → world view with real keyframes/chronicle entries → proceed → next mission. Known gaps carried forward to `launch_todo.md`:

- **Smooth territory transitions** — not implemented. Metaball shader rebuilds entire faction mesh on every change; needs shader-uniform animation approach. Territory updates work but snap instantly.
- **Border vs trade connection visual distinction** — connections render but all look the same (no solid vs dashed).
- **Border contour SubViewport shader pass** — deferred; territory bubbles provide adequate visibility.
- **Pause menu** — does not exist. In-mission exit path untested. Post-narration exit works.
- **Performance budget** — not formally measured (60 FPS target at 1920×1080 during busy time jump). Shell renderer moved to half-res SubViewport which improved performance but no profiler numbers captured.

## Files Created

- `simulation/world_view/__init__.py`
- `simulation/world_view/keyframe_selector.py`
- `simulation/world_view/keyframe_message.py`
- `simulation/world_view/time_jump_emitter.py`
- `simulation/test_checkpoint_11a.py`
- `simulation/test_checkpoint_11b.py`
