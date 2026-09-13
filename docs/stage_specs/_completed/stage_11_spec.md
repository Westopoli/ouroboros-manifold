# Stage 11 — Galaxy View, Chronicle Scroll, and Seamless Transition

## Goal

Build the macro-loop visual structure: mission end → camera pulls back → galaxy view emerges → time jump executes with chronicle scroll printing alongside → camera pushes into next mission system → next mission begins. One continuous flow, no loading screens. This is the stage that makes the generational fantasy visible and playable.

## Bible References

Read the hub (`game_bible.md`) plus these spokes:

- `docs/bible_history/bible_2_00_world.md` → "Galaxy View — The Strategic Layer Between Missions" (including Faction territory, Connections, Military activity visualization, Ambient particle field, The pivot point), and "Seamless Transition — No Loading Screens" (including Chapter-boundary exits and Exit transition treatment).
- `docs/bible_history/bible_2_00_chronicle.md` → "Chronicle Scroll — Visual Presentation" (split-screen, Word fade-in, Master timeline, Chronicle–keyframe co-occurrence guarantee, Layout — expanding scroll, Entry interaction states).
- `docs/bible_history/bible_2_00_animation_strategy.md` → full document. Stage 11 reuses the sweep_line / divider primitives, blinking-cursor-as-heartbeat vocabulary, and smooth-fade-over-cuts rule.
- `docs/bible_history/bible_2_00_simulation.md` → "Time Jump Controller" (already implemented; this stage visualizes its output).

Do not read other spokes. Stage specs for Stages 6, 7, 7.5 are irrelevant here. Stage 8 and Stage 10 specs are consulted for protocol and UIDataBus patterns, see Integration Points.

## Context

Stages 1–4 proved the simulation. Stage 5 proved the chronicle distiller produces real narrative with real names. Stage 6 / 7 / 7.5 / 8 deliver the tactical engine and its renderer. Stage 9 proved the UI shell screens wrap around tactical gameplay with mock data; Stage 10 replaced that mock layer with a live WebSocket bridge to the Python sim. The `scenes/shared/galaxy/galaxy_structure.tscn` particle scene already exists from main-menu work, with a public API whose world-view methods are stubbed and ready to be filled in.

Stage 11's work is threefold:

1. **Implement the stubbed world-view API methods** on `galaxy_structure.gd` so the scene can render system nodes, faction territory with contoured borders, connections, military flashes, highlights, and scripted camera moves.
2. **Build the chronicle scroll panel** as a Godot UI scene that prints queued entries word-by-word with per-word fade-in, supports click-to-expand with strict pause semantics, and coexists with the galaxy in an expanding-scroll layout.
3. **Build the seamless transition sequencer** that orchestrates the six-phase flow (pull-back / galaxy emerges / time jump narration / settle / push-in / next mission), driven by keyframe snapshots and chronicle entries flowing through the UIDataBus.

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
├── time_jump_sequencer.tscn               - The six-phase orchestrator. Root scene for the galaxy view.
├── time_jump_sequencer.gd
├── galaxy_view_camera.gd                  - Camera choreography for pull-back, push-in, ambient orbit, viewport-resize framing.
└── territory_contour.gdshader             - Post-process shader producing the border contour between faction influence fields.

sim/world_view/
├── keyframe_selector.py                   - Consumes distiller output + ownership-change events, emits keyframe snapshots.
└── keyframe_message.py                    - Serialization of keyframe snapshots to JSON for transport.
```

### Modified files

```
scenes/shared/galaxy/
├── galaxy_structure.gd                    - Fill in stubbed world-view methods (system nodes, territory, connections, flashes, highlight, move_camera_to).
├── territory_bubbles.gdshader             - NEW: spherical influence bubble shader with additive blending.
└── galaxy_structure.tscn                  - Add SubViewport pass for territory bubbles + contour, add system-node multimesh, add connection-line renderer.

autoload/
└── ui_data_bus.gd                         - Add signals: time_jump_keyframe, chronicle_entry, time_jump_started, time_jump_ended. Add methods: proceed_to_next_mission(), exit_to_main_menu().

sim_bridge/                                 - Python side of UIDataBus transport (from Stage 10).
└── message_router.py                      - Route new message types ("keyframe", "chronicle_entry", "time_jump_start", "time_jump_end") to bus signals.

sim/
├── time_jump.py                           - Emit time_jump_start on entry, time_jump_end on exit. Drive keyframe_selector and distiller, enqueue keyframe + chronicle messages.
└── events.py                              - No behavioral change; keyframe_selector reads the event log this module already produces.

scenes/main_menu/
└── main_menu.gd                           - After a run exits to main menu via fade-to-black, clear any held galaxy view state so the next run starts clean.

scenes/tactical/
└── pause_menu.gd                          - Wire the existing "Exit to Main Menu" pause-menu item to call UIDataBus.exit_to_main_menu() and run the same fade-to-black treatment as the post-narration Exit. This is the pre-pullback chapter-boundary exit path.

config/
└── world_view_config.py                   - NEW: all Stage 11 tuning values (see "Tuning values" section).
```

### Files explicitly NOT created

- No tutorial, no onboarding screen, no mission debrief. Those are Stage 12.
- No save-on-exit serialization. Exit cleanly terminates the run; Stage 12 wires save-on-exit.
- No subscription / entitlement changes.

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
    {
      "region_id": "r_07",
      "old_faction_id": "f_conqueror",
      "new_faction_id": "f_player"
    }
  ],
  "military_events": [
    {
      "kind": "attack",
      "attacker_region_id": "r_05",
      "defender_region_id": "r_07"
    },
    {
      "kind": "conquest",
      "attacker_region_id": "r_05",
      "defender_region_id": "r_07"
    }
  ],
  "connection_changes": [
    {
      "kind": "added",
      "from_region_id": "r_05",
      "to_region_id": "r_07",
      "connection_type": "border"
    }
  ],
  "regions_snapshot": [
    { "region_id": "r_05", "owner_faction_id": "f_player", "significance": 0.64 },
    { "region_id": "r_07", "owner_faction_id": "f_player", "significance": 0.41 }
  ]
}
```

`chronicle_entry_id` is present when this keyframe is paired to a chronicle entry (the co-occurrence guarantee case from `docs/bible_history/bible_2_00_chronicle.md`). It is `null` when the keyframe is an ownership-change-only keyframe (also covered by the guarantee — such keyframes animate silently).

`regions_snapshot` includes only regions whose `owner_faction_id` or `significance` changed between this keyframe and the previous one. The renderer carries forward unchanged regions from the prior keyframe.

### Chronicle entry message (sim → Godot, new message type)

Emitted for each distiller-produced entry. Ordered by `tick_range_start`. Paired with exactly one keyframe per the co-occurrence guarantee.

```json
{
  "type": "chronicle_entry",
  "time_jump_id": "tj_0003",
  "entry_id": "ce_0017",
  "tick_range_start": 14780,
  "tick_range_end": 14820,
  "base_form": "Within a decade of the Battle of the Nak Reach, Commander Vael Sorn retook the system for the Republic.",
  "expanded_form": "Within a decade of the Battle of the Nak Reach, Commander Vael Sorn retook the system for the Republic. The Conqueror's grip on the frontier had weakened after the loss of three border regions to administrative revolts; Sorn exploited the vacuum with a forced march and a single decisive engagement. The victory at the Nak Reach became the pivot point for the Republic's decade of recovery."
}
```

Both fields arrive pre-rendered from the distiller. The renderer treats them as opaque strings.

### Time-jump lifecycle messages

```json
{ "type": "time_jump_start", "time_jump_id": "tj_0003", "span_years": 27, "total_keyframes": 5, "total_entries": 4 }
{ "type": "time_jump_end", "time_jump_id": "tj_0003" }
```

`total_keyframes` and `total_entries` are advisory — used by the sequencer to set up the keyframe/entry queues before the first keyframe arrives.

### UIDataBus additions (Godot side)

```gdscript
# New signals on ui_data_bus.gd
signal time_jump_started(time_jump_id: String, span_years: int, total_keyframes: int, total_entries: int)
signal time_jump_keyframe(keyframe_data: Dictionary)   # Dictionary matches the keyframe JSON shape above.
signal chronicle_entry(entry_data: Dictionary)         # Dictionary matches the chronicle_entry JSON shape.
signal time_jump_ended(time_jump_id: String)

# New outgoing methods (Godot → sim)
func proceed_to_next_mission() -> void                 # Tells the sim to advance past the time jump boundary to the next mission.
func exit_to_main_menu() -> void                       # Tells the sim to terminate the run cleanly. No save. Sim teardown reuses Stage 10 lifecycle.
```

### Galaxy structure public API (previously stubbed, now implemented)

The method signatures already exist on `galaxy_structure.gd` from main-menu work. Their documented contracts from the stub comments are authoritative for behavior. Stage 11 fills in the bodies:

- `add_system_node(node_id, position, size, color)` — spawn a luminous point; size maps to bubble-radius and visual node size per bible.
- `remove_system_node(node_id)`, `update_system_node(node_id, size, color)`, `clear_system_nodes()` — maintain the node set.
- `set_territory(region_id, center, radius, color)` — emit a spherical influence bubble (additive blend, low opacity). Internal representation drives the contour shader.
- `update_territory(region_id, radius, color)` — interpolate to new values over the configured transition duration.
- `remove_territory(region_id)` — fade the bubble out over the configured duration.
- `add_connection(from_id, to_id, connection_type, color)`, `remove_connection(from_id, to_id)` — maintain connection lines.
- `flash_military_activity(region_id, intensity)` — position-based flash at the region's system node (used for revolts).
- `flash_conflict(from_id, to_id, intensity)` — flash at the midpoint between the two system nodes (used for attacks, conquests).
- `highlight_system(node_id)`, `clear_highlight()` — pulsed glow on the next-mission target.
- `move_camera_to(position, look_at, duration)` — scripted camera transition used for pull-back and push-in.
- `enable_manual_orbit()`, `disable_manual_orbit()`, `start_auto_camera()`, `stop_auto_camera()` — existing; reused during narration and post-narration ambient orbit.
- `set_opacity(alpha)`, `fade_in(duration)`, `fade_out(duration)` — existing; reused for the overall fade-to-black on Exit.

### Chronicle scroll panel API

```gdscript
# chronicle_scroll_panel.gd public methods
func begin_time_jump(total_entries: int) -> void       # Reset state, prepare for entries to arrive.
func queue_entry(entry_data: Dictionary) -> void       # Queue a chronicle entry. Does not start printing.
func start_printing(entry_id: String) -> void          # Begin word-by-word printing of a queued entry. Sequencer calls this when the master clock reaches the entry's tick range.
func end_time_jump() -> void                           # Signal that no more entries will arrive; hold the last printed entry.
func pause() -> void                                   # Pause word fade-in, halt the printing timer. Called by sequencer on expansion.
func resume() -> void                                  # Resume exactly where paused.

# Signals
signal entry_finished_printing(entry_id: String)       # Emitted when a printing entry completes.
signal entry_expansion_opened(entry_id: String)
signal entry_expansion_closed(entry_id: String)
signal all_entries_finished()                          # Emitted when the last queued entry finishes printing.
```

## Integration Points

### With Stage 10 (UIDataBus transport)

Stage 11 extends the UIDataBus rather than replacing it. New signals and methods listed in Input/Output Shapes. The transport layer (stdio-framed JSON, Python subprocess lifecycle, `message_router.py`) is unchanged — the new message types ride the existing framing. `message_router.py` gets four new route entries (`keyframe`, `chronicle_entry`, `time_jump_start`, `time_jump_end`) that fan out to the new bus signals.

### With Stage 8 (tactical renderer)

The pull-back phase starts from the tactical camera's final state at mission end. The tactical scene does not tear down when the mission ends; instead, it emits a `mission_ended` signal that the sequencer listens for. The sequencer captures the tactical camera's position and look-at, then calls `move_camera_to()` on the galaxy scene for the pull-back. The tactical scene can be freed once the pull-back has visibly cleared it from the viewport (configurable delay, default 500ms after pull-back begins).

### With Stage 5 (chronicle distiller)

The distiller runs inside the time-jump controller (already does). Stage 11's `keyframe_selector.py` consumes the distiller's output (`chronicle_entries` list) as its base set. Ownership-change events from `sim/events.py` are unioned in. The selector emits keyframe messages paired with the distiller's entries via `chronicle_entry_id`.

### Post-narration hold — sim state and renderer ambience

When the sim emits `time_jump_end`, two things happen in lockstep:

1. **Sim side.** The sim finishes the time jump, then immediately runs the mission generator to produce the next mission's briefing. The briefing is held in sim state — *not* emitted over the bus yet. The sim is now idle, waiting for either `proceed_to_next_mission()` or `exit_to_main_menu()`. On `proceed_to_next_mission()`, the held briefing is pushed through the bus and the sequencer hands off to the Stage 9 Mission Briefing screen. On `exit_to_main_menu()`, the held briefing is discarded as part of run teardown.
2. **Renderer side.** The sequencer receives `time_jump_end`, decelerates ambient orbit from `CAMERA_AMBIENT_ORBIT_SPEED_NARRATION` to `CAMERA_AMBIENT_ORBIT_SPEED_SETTLED`, calls `highlight_system(next_mission_region_id)` so the destination is visible before the player commits to Proceed, and shows the Proceed/Exit footer. The highlight clears when `move_camera_to` begins the push-in (on Proceed) or when the fade-to-black begins (on Exit).

**Ambient liveliness during the hold.** The galaxy is not completely static during the post-narration hold. The settled ambient orbit is the base motion. On top of that, the sequencer cycles **low-key ambient animations** to keep the view feeling alive without distracting from the moment: faint pulse on the highlighted destination system (using the existing blinking-cursor heartbeat timing from the animation strategy), occasional very-low-intensity flickers on random non-contested systems (suggesting ongoing life — simulated by particle-burst primitives at 10–20% of military-flash intensity, frequency ~1 every 3–5 seconds), and slow parallax drift on the ambient particle field already driven by the galaxy scene's existing shaders. Nothing new, nothing loud — existing primitives composed at low intensities.

Ambient animation configuration is tuning values (see `AMBIENT_LIVELINESS_*` in `world_view_config.py`).

### With the main menu

Exit from a run fades the screen to black and loads the main menu scene. The main menu's `_ready()` already handles a clean start. `main_menu.gd` gets one small addition: if it detects residual galaxy-view state from a prior run (e.g., a `GalaxyStructure` node still holding system nodes), it calls `clear_system_nodes()` and resets opacity before its own fade-in.

### Kill switches

- `config.WORLD_VIEW_ENABLED` — if false, mission end transitions directly to the next mission briefing with no galaxy view, no chronicle scroll, no camera choreography. A "GENERATION +27 YEARS" text card appears briefly and fades. This is the kill-switch-architecture compliance path; it lets Stage 12 work proceed if Stage 11 is unstable.
- `config.CHRONICLE_SCROLL_ENABLED` — if false, galaxy view runs without the scroll panel. Keyframes animate, no text prints. Used for visual tuning of the galaxy side in isolation.
- `config.KEYFRAME_STREAM_ENABLED` — if false on the sim side, the sim emits a single placeholder keyframe per time jump (current state only). Used for testing the renderer with trivial input.

## Checkpoints

Each checkpoint is a STOP point per `dev_rules.md`. Output is shown to Westley, approved, and only then does the next checkpoint begin.

### Checkpoint A — Keyframe selector (sim-side, headless)

Build `sim/world_view/keyframe_selector.py` and `keyframe_message.py`. Write a headless test that runs a time jump end-to-end against a scripted simulation state with seeded events and verifies:

- Every chronicle entry from the distiller produces a keyframe with matching `chronicle_entry_id` and matching `tick_range_start` / `tick_range_end`.
- Every ownership change in the event log produces a keyframe (either paired to an entry if the distiller also picked it, or standalone with `chronicle_entry_id: null`).
- Keyframes are ordered by `tick`.
- Emitted JSON passes a round-trip parse.

Prove-it output: a printed table of keyframes showing tick, paired entry id (or "---"), ownership changes count, military events count.

### Checkpoint B — Transport round-trip

Wire the four new message types through `message_router.py`. Send scripted messages from the sim harness, verify Godot-side bus signals fire with the expected payloads. Fill in `ui_data_bus.gd` signal declarations and router entries.

Prove-it output: a Godot console log showing each signal firing in order with the payload summary (keyframe index, entry id, tick range).

### Checkpoint C — Galaxy structure world-view API fill-in

Implement the stubbed methods on `galaxy_structure.gd` in this order:

1. `add_system_node`, `remove_system_node`, `update_system_node`, `clear_system_nodes` — simplest; multimesh-rendered glowing points. Use existing particle color by default, override per faction color for owned systems.
2. `add_connection`, `remove_connection` — Line3D or ImmediateMesh lines between nodes. Border = solid, trade = thinner/dashed (MeshInstance3D with a dashed shader or short segment strip).
3. `set_territory`, `update_territory`, `remove_territory` — spherical influence bubbles. Use the new `territory_bubbles.gdshader` with additive blending, low opacity, faction color. Bubble radius scales with `radius` parameter per bible.
4. Border contour — new SubViewport pass sampling the bubble sum texture; contour shader (`territory_contour.gdshader`) draws a bright line at the equipotential threshold between two faction intensities. Approach: render per-faction influence fields to separate channels of a summed texture, compute max and second-max per pixel, draw contour where `max - second_max` falls within the threshold band.
5. `flash_military_activity`, `flash_conflict` — particle bursts at position or midpoint. Reuse the animation-strategy ember/bloom primitives where possible.
6. `highlight_system`, `clear_highlight` — pulsed glow on a single node. Reuses the main menu's blinking-cursor heartbeat timing.
7. `move_camera_to` — Tween-driven camera interpolation with configurable easing.

Prove-it output: a test harness scene (`tests/test_galaxy_world_view.tscn`) that scripts each method in sequence against a mock world state — adds three factions with territories, draws connections, runs flashes, moves the camera — and visually displays the result. Westley reviews by running the harness and eyeballing the output.

Break into sub-checkpoints C1 through C7 mirroring the list above. Each sub-checkpoint is its own STOP.

### Checkpoint D — Chronicle scroll panel (standalone)

Build the scroll panel as a standalone UI scene tested outside the sequencer. Harness (`tests/test_chronicle_scroll.tscn`) feeds mock entries, exercises word-by-word fade-in with tunable per-word duration, exercises click-to-expand with pause/resume verification, exercises the three states (printing / printed / expanded) with the blinking cursor on printed entries.

Prove-it output: Westley runs the harness, verifies printing cadence, fade quality, expansion panel behavior, and state transitions visually.

### Checkpoint E — Time jump sequencer (integrated)

Build `time_jump_sequencer.gd` and wire it to the bus signals. The sequencer:

1. On `time_jump_started`, sets up the galaxy view with the starting world state, transitions the scroll panel in (slide-in animation), resizes the galaxy viewport to ~60% width.
2. On each `time_jump_keyframe`, advances the galaxy animation to that keyframe's world state (ownership interpolation, territory updates, connection updates, flashes).
3. On each `chronicle_entry`, queues the entry in the scroll panel. Starts printing when the galaxy animation reaches the entry's `tick_range_start`.
4. On `time_jump_ended`, decelerates the galaxy to settled ambient orbit, calls `highlight_system(next_mission_region_id)`, kicks off the ambient-liveliness cycle (low-intensity random flickers on non-highlighted systems), holds the last entry printed, shows the Proceed / Exit footer.
5. On Proceed, slides the scroll panel out, resizes the galaxy viewport back to full, executes the push-in via `move_camera_to`, then emits `ready_for_next_mission`.
6. On Exit, calls `exit_to_main_menu()`, runs a fade-to-black, loads the main menu.

Prove-it output: a scripted fake time jump runs end-to-end with three keyframes and two entries. Westley reviews the full sequence visually.

### Checkpoint F — Full loop integration

Wire Stage 11 to the live Stage 8 / Stage 10 pipeline. End-to-end test:

1. Start a new game.
2. Complete a real mission.
3. Observe pull-back from tactical into galaxy view.
4. Watch the time jump render with real keyframes and real chronicle entries from the distiller.
5. Expand an entry mid-narration, verify everything pauses.
6. Dismiss expansion, verify resume.
7. Press Proceed, observe push-in to next mission system.
8. Verify the next mission briefing appears.

Prove-it output: Westley plays through one full mission → time jump → next mission cycle and signs off.

### Checkpoint G — Exit path verification

Separate checkpoint because it was not covered in F. After a time jump narration completes, press Exit on the scroll panel footer. Verify: fade-to-black runs, main menu loads, no residual galaxy state, starting a new run from main menu works cleanly. Then verify the in-mission exit path: during a tactical mission, open the pause menu, select Exit to Main Menu. Verify the same fade-to-black treatment runs and the same clean main-menu restart works.

Prove-it output: Westley exits from both paths (in-mission pause menu, post-narration footer) and confirms clean termination and clean restart.

### Checkpoint H — Performance budget

Per `dev_rules.md` performance-regression discipline. Measure per-frame cost of the integrated galaxy view during a busy time jump (10 keyframes, 10 entries, 8 factions, 40 systems, 60 connections, 3 simultaneous military flashes):

- Frame time budget: 60 FPS sustained at 1920×1080 on a representative machine.
- SubViewport pass cost for bubbles + contour: measured and under 4ms.
- Chronicle scroll per-word animation cost: under 0.5ms per frame during active printing.

Fail criteria: any budget exceeded. Budget anchoring: the 60 FPS frame-time ceiling is the canonical target; the SubViewport and scroll sub-budgets are subdivisions of the remaining frame budget after the main-menu galaxy's measured baseline is accounted for. **Before running the busy-time-jump measurement, first re-measure the main-menu galaxy at the same resolution and record its frame cost as the baseline `B_ms`.** The SubViewport pass budget of 4ms is the additional budget Stage 11's territory/contour rendering is allowed to spend on top of `B_ms`. The scroll 0.5ms ceiling is a standalone UI-thread budget, not affected by the galaxy baseline.

Prove-it output: Godot profiler screenshot and numerical table showing baseline `B_ms`, busy-time-jump frame time, SubViewport delta, and scroll animation cost.

## Engineering Decisions and Defaults

These are decisions the spec makes upfront with reasoning, so CC does not have to guess:

### Keyframe / chronicle pipeline integration (Q9 / Option A)

In `time_jump.py`, the order is: run distiller → run keyframe_selector passing distiller output → union in ownership-change keyframes from the event log → emit. Deduplication rule: if an ownership-change event falls inside a distiller-produced entry's tick range, the keyframe for that entry absorbs the ownership change (no duplicate keyframe). Otherwise, the ownership change produces its own keyframe with `chronicle_entry_id: null`.

### Connection edge type rendering

The sim's three edge types (`border`, `trade`, `both` per `docs/bible_history/bible_2_00_world.md`) collapse to two visual treatments in the galaxy view: `border` and `both` both render as solid faction-color lines; `trade` renders as a thinner dashed line. The border-vs-both distinction (economic propagation) is not player-readable at galaxy scale and is deliberately not visualized. `add_connection` accepts all three type values; internally it maps `"both"` to the border visual.

### Galaxy scene architecture

Stage 11 does not create a new galaxy scene. The existing `scenes/shared/galaxy/galaxy_structure.tscn` is instanced by `time_jump_sequencer.tscn`, which is the root scene for the world-view phase. The main menu and the sequencer both instance the same shared scene, honoring the original reuse intent. The difference is configuration: main menu sets opacity 0.7 and starts auto-camera; the sequencer sets opacity 1.0 and drives the camera via `move_camera_to` during transitions and `start_auto_camera` during ambient orbit.

### Border contour implementation

Marching-cubes on a discretized influence field is expensive per frame and overkill for our density. The default approach is a **post-process shader** sampling a per-faction influence sum texture. Each faction's bubbles render additively to a dedicated channel of the texture; the contour shader samples neighboring pixels, computes local max and second-max, and draws the contour where the difference falls within a threshold band. This produces contours where faction influences meet regardless of topology, handles enclaves naturally, and runs in one SubViewport pass.

### Scroll panel slide animation

Reuse `docs/bible_history/bible_2_00_animation_strategy.md`'s sweep_line primitive. Slide-in: panel enters from screen right with a 400ms ease-out-cubic tween, galaxy viewport resizes simultaneously. Slide-out on Proceed: mirror of slide-in, 400ms ease-in-cubic. No sliding on Exit — the whole screen fades to black.

### Camera choreography

- Pull-back: 2.5s, ease-in-out-cubic, tactical camera position → galaxy ambient-orbit start position. Tactical scene freed 500ms into the pull-back.
- Galaxy-emerges transition: 1.0s opacity ramp from 0 to 1 on the galaxy scene, overlapping the tail of the pull-back.
- Narration ambient orbit: 0.03 rad/sec around the pivot point, driven by `start_auto_camera()`.
- Post-narration settle: decelerate to 0.01 rad/sec (slower ambient).
- Push-in: 3.0s, ease-in-out-cubic, current camera position → target system's close-up position → tactical camera start position.

All durations are tuning values in `config/world_view_config.py`.

### Exit behavior for Stage 11

Plain exit, no confirmation modal. The game ships only to Westley through Stage 12. Exit: fade-to-black 600ms, main menu loads. Save-on-exit wiring is Stage 12.

### Exit path availability — where the Exit button appears

Stage 11 surfaces Exit in two places, which together satisfy the bible's "symmetric exit offer at chapter boundaries":

- **Post-narration (primary chapter-boundary exit).** The Proceed/Exit footer on the scroll panel, displayed during the post-narration hold (after `time_jump_ended`). This is the explicit chapter-boundary exit the bible names.
- **In-mission (pre-pullback equivalent).** The existing Stage 8 tactical pause menu's "Exit to Main Menu" item. This already exists as a given-for-any-RTS affordance. Stage 11 wires this pause-menu exit to route through the same `exit_to_main_menu()` bus method and fade-to-black treatment as the post-narration Exit, so the visual and lifecycle behavior is identical regardless of which exit path the player takes.

There is **no Exit affordance during the pull-back camera transition itself.** The pull-back is a cinematic beat (2.5s) and adding a mid-transition UI element would undermine it. The player either exits from inside the mission (pause menu) or waits for the post-narration hold (Proceed/Exit footer). Covering both ends of a chapter boundary with pre-existing or spec-introduced UI means no additional UI affordance is needed for the pre-pullback moment.

This adds one wiring requirement to Stage 8's pause menu — see the Modified files list's note on `scenes/tactical/pause_menu.gd`.

## Tuning Values (defaults; live in `config/world_view_config.py`)

```python
# Keyframe selection (sim side)
KEYFRAME_SIGNIFICANCE_THRESHOLD = 0.55           # Inherits from distiller's threshold by default.
KEYFRAME_MAX_PER_TIME_JUMP = 12                  # Cap to prevent visual overload.

# Chronicle scroll
SCROLL_PER_WORD_CADENCE_SEC = 0.08               # Time between word arrivals.
SCROLL_PER_WORD_FADE_DURATION_SEC = 0.20         # Per-word fade-in duration (Q8).
SCROLL_ENTRY_MIN_DISPLAY_DURATION_SEC = 3.0      # Minimum time an entry remains visible after finishing.
SCROLL_PANEL_SLIDE_IN_DURATION_SEC = 0.40
SCROLL_PANEL_SLIDE_OUT_DURATION_SEC = 0.40
SCROLL_PANEL_WIDTH_FRACTION = 0.38               # Panel occupies 38% of screen; galaxy gets 62%.

# Galaxy view
GALAXY_TERRITORY_BUBBLE_OPACITY = 0.25
GALAXY_TERRITORY_BUBBLE_RADIUS_SCALE = 1.6       # Multiplier on system significance for bubble radius.
GALAXY_CONTOUR_THRESHOLD = 0.08                  # Influence-difference band width where contour draws.
GALAXY_CONTOUR_BRIGHTNESS = 1.4                  # Contour line brightness (brand-gold-adjacent color).
GALAXY_CONTOUR_LINE_THICKNESS_PX = 1.5
GALAXY_FLASH_DURATION_SEC = 0.35
GALAXY_FLASH_INTENSITY = 0.7
GALAXY_TERRITORY_TRANSITION_DURATION_SEC = 1.0   # Time for a bubble to interpolate on ownership change.

# Camera choreography
CAMERA_PULL_BACK_DURATION_SEC = 2.5
CAMERA_GALAXY_FADE_IN_DURATION_SEC = 1.0
CAMERA_AMBIENT_ORBIT_SPEED_NARRATION = 0.03
CAMERA_AMBIENT_ORBIT_SPEED_SETTLED = 0.01
CAMERA_PUSH_IN_DURATION_SEC = 3.0
TACTICAL_SCENE_FREE_DELAY_MS = 500               # Delay before freeing tactical scene after pull-back begins.

# Ambient liveliness during post-narration hold
AMBIENT_LIVELINESS_FLICKER_MIN_INTERVAL_SEC = 3.0
AMBIENT_LIVELINESS_FLICKER_MAX_INTERVAL_SEC = 5.0
AMBIENT_LIVELINESS_FLICKER_INTENSITY_FRACTION = 0.15   # Fraction of GALAXY_FLASH_INTENSITY for ambient flickers.
AMBIENT_LIVELINESS_HIGHLIGHT_PULSE_PERIOD_SEC = 1.5    # Period of the destination-highlight pulse (matches blinking-cursor heartbeat vocabulary).

# Exit
EXIT_FADE_TO_BLACK_DURATION_SEC = 0.6
```

## Done Condition

Westley starts a new game. He completes a real mission via the tactical engine. At mission end, the camera pulls back smoothly — no loading screen, no scene-cut. The galaxy view emerges with the Settled Reach rendered: system nodes visible, faction territories colored with contoured borders, connections drawn. A chronicle scroll panel slides in from the right and the galaxy resizes to ~62% width. Chronicle entries print word-by-word with each word fading in smoothly, synchronized to keyframes — as an entry describes a region falling to an invader, Westley sees the territory shift on the map. He clicks an entry mid-narration; everything pauses. He dismisses the expansion; everything resumes exactly where it paused. The last entry finishes, the galaxy settles into slow ambient orbit, the next mission's destination system pulses with a subtle highlight, faint flickers animate on unrelated distant systems, and the scroll panel footer shows Proceed and Exit. He clicks Proceed; the highlight clears, the scroll slides out, the galaxy resumes full screen, the camera pushes into the next mission's target system, and the next mission's briefing appears.

He quits back to main menu, starts a new run. In the new run, at a time jump, he clicks Exit instead. The screen fades to black, the main menu loads, and starting another new run works cleanly.

Performance holds 60 FPS at 1920×1080 across a busy time jump.

Westley signs off before Stage 12 begins.

## Implementation Variations

Deviations from spec as built, signed off by Westley during checkpoint reviews.

### Checkpoint F — Full loop integration

- **No continuous pull-back from tactical camera.** Spec calls for a seamless camera pull-back from the tactical view into the galaxy. Actual: mission end → SceneRouter transitions to debrief scene → debrief Continue → SceneRouter transitions to time_jump scene. Scene cuts are masked by SceneRouter's fade transitions, not a continuous camera move.
- **No push-in to next mission.** Spec calls for camera pushing into the next mission's target system after Proceed. Actual: Proceed fades to black and loads the tactical scene via SceneRouter.
- **No border contour shader.** `territory_contour.gdshader` not implemented. Territory is visualized with influence bubbles only, no equipotential contour lines between factions.
- **Connection lines implemented (C2 backfill).** `add_connection`/`remove_connection` renders ImmediateMesh lines between adjacent regions. Border/both edges: alpha 0.4, emission 2.0. Trade edges: alpha 0.15, emission 1.0. Per-keyframe `connections_snapshot` built in `keyframe_selector.py` from `world.adjacency` and `world.edge_types`.
- **No `config/world_view_config.py`.** Tuning values are inline in the relevant GDScript files rather than centralized in a Python config module.
- **Camera timing differs from spec defaults.** Spec: pull-back 2.5s, push-in 3.0s. Actual: overview move 4.0s, no push-in. Scroll slide-in 1.0s (spec: 0.4s). Viewport resize 1.2s (spec: not specified separately).
- **Faction name coloring in chronicle text.** Not in spec. Added: faction display names in chronicle entries are colored to match their territory color on the galaxy view.
- **Same mission repeats.** No mission generator exists yet. `_make_engine()` always produces the same hardcoded tactical setup. The game loop cycles correctly (tactical → debrief → time jump → proceed → tactical) but the mission content is identical each cycle.
- **Debrief is an intermediary scene.** Spec describes a six-phase continuous flow. Actual flow inserts the Stage 12 debrief scene between mission end and time jump as a discrete step with its own Continue button.
- **Continuous ownership timeline (not in spec).** Territory colors update every 2 ticks (configurable via `config.OWNERSHIP_TIMELINE_STRIDE`) instead of only at the 12 discrete keyframe boundaries. Produces 25 ownership snapshots per 50-tick time jump. Sent in the `time_jump_start` message, played back independently of keyframe/chronicle pacing in `_advance_timeline()`. When the timeline is active, keyframes skip color updates on existing regions — the timeline is the sole driver of territory colors. Keyframes still handle adding new regions, connections, and military flashes.
- **Staggered military flashes on ownership change.** When an ownership timeline tick changes a region's faction, a flash fires with a random delay spread across the tick interval (up to 80% of interval). Prevents all flashes from firing simultaneously. Flash animation is a 5× repeating spike (0.15s up, 0.85s decay = 1.0s per cycle, 5.0s total burst).
- **Evenly-spaced faction colors.** Spec doesn't specify how faction colors are assigned. Implementation uses evenly-spaced HSV hues (`hue = float(i) / faction_count`) sorted by faction ID for deterministic, visually distinct colors regardless of faction ID hash values.
- **1v1 fast-test mode.** `SimBridge.SIM_UNITS_PER_SIDE` const (default 1) and `--units` CLI arg allow spawning minimal units close together for rapid iteration. When units ≤ 5, uses weakest unit type on a small 2000×2000 map.

### Checkpoint G — Exit path verification

- **Post-narration Exit works.** Fade-to-black → main menu → clean restart confirmed.
- **In-mission Exit works.** Pause menu Exit to Main Menu → same treatment confirmed.
- **No pause menu wiring change needed.** The existing pause menu exit path already routes through `UIDataBus.exit_to_main_menu()`.

### Checkpoint H — Performance budget

- **60 FPS sustained.** Visually confirmed at 1920×1080 during a busy time jump (12 keyframes, 10 chronicle entries, 4 factions, 14 regions, 25 ownership timeline snapshots with staggered military flashes). No frame drops observed.
- **No separate SubViewport/scroll sub-budget measurements.** Spec calls for isolated SubViewport pass cost (< 4ms) and scroll animation cost (< 0.5ms). Godot's built-in debugger profiler does not surface per-pass GPU timing. Visual confirmation of sustained 60 FPS covers the aggregate budget.
- **No profiler screenshot.** Spec calls for a Godot profiler screenshot and numerical table. Profiler sub-tabs did not display FPS data in the user's Godot 4.6.1 configuration. Visual confirmation substituted.

## Files Created

*Filled in after implementation.*
