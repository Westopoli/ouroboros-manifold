# Stage 8 — Godot Renderer, Command Interface, and Game State Persistence

## Goal

Prove that the tactical simulation can be played — not just simulated headless. Stage 8 stands up three systems simultaneously and proves they compose: (1) a Godot renderer that consumes tactical engine state over a WebSocket bridge and draws it at 60fps with linear interpolation between 20 Hz engine ticks; (2) a command interface (selection, control groups, movement, abilities, layer assignment) that issues the same command protocol the tactical engine already accepts from enemy macro scripts; (3) a **launch-grade save layer** covering three classes of state — simulation state (single current-state file per slot), tactical-engine state mid-mission for single-slot quit-and-resume, and onboarding preferences — with no rewind, no history, no fork.

Stage 8 is the stage where the game becomes **playable for the first time**. Stages 1–4 proved the simulation. Stage 5 proved the narrative pipeline. Stage 5.5 proved the mission generator. Stage 6 proved the tactical engine headless. Stage 7/7.5 proved procedural maps and enemy macro scripts. Stage 8 proves a human can sit down, receive a mission, study the terrain in a recon phase, command forces in real time, quit in the middle of a mission and resume later, and pick up the next chapter after a session break.

**Not in scope:** main-menu / new-game / load-game / save-slot-browser UI (Stage 9), mission briefing screen (Stage 9), era library / monetization UI (Stage 9), full chronicle scroll UI for time-jump montages between chapters and animated time-jump map (Beyond Stage 9 — Stage 8 ships ONLY the abbreviated 3–5 entry opening scroll as a minimal text list, no animation, no per-entry expand), mission debrief/outcome screen (Beyond Stage 9), tutorial (Beyond Stage 9), galaxy/system/planet view (Beyond Stage 9). **Rewind, fork-from-here, boundary-snapshot history, and multi-snapshot timeline browsing are all deferred to a post-launch rewind feature** (see hub §15 for the deferred design sketch). Stage 8 ships the **tactical scene** plus the **save layer** plus the **onboarding screen + abbreviated opening scroll** — nothing else.

**Architecture.** The Python tactical engine runs as a standalone WebSocket server. Godot is a pure client that subscribes to tick snapshots, renders them, interpolates between ticks for a 60fps presentation, and sends command packets back. No engine logic executes in Godot — it is a presentation layer that happens to also capture input. Persistence is a separate Python-side concern: the save writer serializes the current simulation state, any in-flight tactical state, and onboarding preferences to disk; the save loader reconstructs them on resume. No snapshot history, no pivot operations, no timeline concept.

## Bible Capture Pending

These bible edits landed during the Stage 8 write-up session; they do not block implementation but are listed here so an auditor can verify them:

1. **Hub "Beyond Stage 9" bullet** — removed the stale "onboarding screen" entry; the Stage 8 roadmap paragraph is now the only source of truth for onboarding scope.
2. **Hub Stage 8 roadmap paragraph** — "5-command vocabulary" replaced with "4-command vocabulary (`move`, `attack_move`, `attack_target`, `activate_ability`) plus the two layer commands." Persistence language rewritten from "rewind-capable" to "saves, not rewind — rewind is a post-launch feature."
3. **`docs/bible_history/bible_2_00_combat.md` L235 and L456** — "5-command protocol" / "same 5 commands" corrected to "4-command protocol" / "same 4 commands." The 5×3 compositional grid in the bible belongs to the **enemy macro behavior system**, not player commands.
4. **Hub §15 (Simulation State Journaling and Rollback)** — rewritten to remove rewind from Stage 8 scope. Stage 8 ships saves only; rewind is a post-launch feature with its own design sketch (pre-mission-selection snapshot boundary, 5-mission minimum gate, mission-generator re-run on rewind, linear-default + fork, chronicle erased on rewind).
5. **Onboarding rare-mark rule** — `game_bible.md:155` and `docs/bible_history/bible_2_00_missions.md:301` rewritten: the "up to two markable as rare" cap was removed. The rule is now "any subset may be marked rare, provided at least one archetype remains unmarked." The interaction is binary per archetype (rare or default); no sliders or gradation.
6. **`docs/bible_history/bible_2_00_combat.md` §"Mid-Mission HUD Layout"** — new section added between "Camera and Player View" and "Moving Battlefields." Captures the IGoP-inspired HUD layout adapted for Ouroboros. The hub Stage 8 paragraph's stale "up to 2 markable as rare" phrasing and stale "rewind-with-re-seed" mentions in "Beyond Stage 9" were fixed in the same pass.
7. **Hub Stage 8 paragraph — recon-phase enemy visibility** — corrected from "enemy positions based on intelligence quality" (stale; the bible never built an intelligence-quality system) to "enemy positions hidden," matching `docs/bible_history/bible_2_00_world.md` §"Recon Phase — Terrain Visibility, Enemy Hidden." Cross-reference added.

## Gating Open Design Questions — ALL RESOLVED

All Stage 8 design questions are now captured. The list below is preserved for audit; each entry is marked with its resolution. Implementation is unblocked on the design-question front.

- **S8-3 — Mid-mission UI information density.** RESOLVED (Q5): IGoP-inspired layout with Ouroboros substitutions. See `docs/bible_history/bible_2_00_combat.md` §"Mid-Mission HUD Layout." Reference screenshots at `docs/legacy/design_questions/igop_hud_reference_alpha.png` and `igop_hud_reference_beta.png`.

### Captured decisions the spec relies on (no change needed)

- **S8-1** (save scope — updated by Q3): three classes of state persist at launch: (1) current simulation state (single file, no history); (2) tactical mid-mission state for single-slot quit-and-resume; (3) onboarding preferences. Replays excluded. Rewind deferred post-launch.
- **S8-1e** (tactical mid-mission state scope — resolved by Q3): single-slot quit-and-resume. No multi-snapshot tactical state, no mid-mission rollback.
- **S8-1a, S8-1b, S8-1c, S8-1d** (deferred post-launch): all live under the post-launch rewind feature per Q3. Design notes preserved in the design doc for the eventual rewind design session.
- **Onboarding in Stage 8** (Q1): resolved Option A. Bible edited.
- **Player command count = 4** (Q2): resolved. Bible edited.
- **Onboarding interaction model** (Q4 / S8-2): binary per-archetype "mark as rare" — any subset allowed except all 10. Difficulty is a three-button Easy / Medium / Hard selector. Bible edited.
- **Mid-mission HUD layout** (Q5 / S8-3): IGoP-inspired clustered bottom bar, Ouroboros-specific reinforcement-structure panel replacing IGoP's build grid, layer selector above commander portrait. See `docs/bible_history/bible_2_00_combat.md` §"Mid-Mission HUD Layout." Bible edited.
- **S75-* / S7-*** resolutions as documented in the design doc.

## Bible References

- **`docs/bible_history/bible_2_00_combat.md`** — §Layer Assignment Hotkey (layer commands the renderer/input system must support), §Camera and Player View (free pan/zoom, minimap), §Command Vocabulary (command set for the command packet), §Unit Behavior AI / Abilities — Player-Activated Only (ability bar behavior: cooldown-only).
- **`docs/bible_history/bible_2_00_world.md`** — §Recon Phase (terrain visible, enemies hidden; free camera, no time pressure; mission clock starts on "Begin Mission"), §"The Vertical Dimension" / §§ on layer accessibility (what the renderer must display per layer).
- **`bible_monetization.md` (deleted 2026-05-31; see docs/bible_history/)** — §"Platform: PC-only" (keyboard+mouse-only command design — the renderer does not target controller input in this stage).
- **`game_bible.md` (hub)** — "The Cycle" step 2 (Recon Phase design), "Onboarding and First Chapter" (onboarding screen + opening time jump), §15 Simulation State Journaling and Rollback (persistence + rewind contract), §16 Space Era Vertical Layer Visualization (three-tier layer rendering approach the tactical renderer implements).

Do NOT read `docs/bible_history/bible_2_00_chronicle.md`, `docs/bible_history/bible_2_00_antagonist.md`, `bible_monetization.md` (deleted 2026-05-31; see docs/bible_history/) (beyond the PC-only line), `docs/bible_history/bible_2_00_simulation.md` (beyond the field list the save writer serializes), or `docs/bible_history/bible_2_00_ai_pipeline.md` — not relevant to Stage 8.

## Cross-Stage References

- **Stages 1–4** — the save writer serializes `Region`, `Faction`, coherence-ledger, diplomacy, technology, and lifecycle state. The persistence layer reads these; it does not mutate them at runtime. Forward simulation uses the existing tick loop unchanged. Rewind is deferred post-launch; Stage 8 does not snapshot the sim for rollback.
- **Stage 5** — coherence-ledger entries belong to the serialized simulation state. Chronicle entries from a discarded timeline are erased on linear rewind (S8-1c capture).
- **Stage 5.5** — the mission generator's output (`MissionSetup`) is part of the per-mission tactical state. `MissionSetup` is serialized alongside the tactical engine's live state for quit-and-resume.
- **Stage 6** — the tactical engine runs as a **standalone server process** in Stage 8. The engine code does not change; Stage 8 wraps `TacticalEngine` in a WebSocket server loop and a snapshot/delta serializer. All determinism properties from Stage 6 hold.
- **Stage 7 / 7.5** — the renderer consumes `TacticalMap` + drifting-node positions via `current_spine_node_positions(tick)`. Behavior scripts continue to run inside the engine and their commands ride through the same command channel as the player's.
- **Stage 9** — the save-slot browser, main menu, era library, mission briefing, and settings screens. Stage 8 exposes the **persistence API** that Stage 9's `UIDataBus` will eventually call; in Stage 8 the only save-slot UI is a minimal debug panel (see "What to Build" below). Stage 9 replaces it with the polished browser.

## What to Build

### Architecture Overview

```
                    ┌───────────────────────────────────────┐
                    │           Python process              │
                    │                                       │
   disk (saves/) ◄──┤  save_writer.py   save_loader.py      │
                    │          ▲             │              │
                    │          │             ▼              │
                    │         ┌──────────────┐              │
                    │         │ simulation   │              │
                    │         │ (tick loop)  │              │
                    │         └──────┬───────┘              │
                    │                │ MissionSetup         │
                    │                ▼                      │
                    │         ┌──────────────┐              │
                    │         │TacticalEngine│◄──commands───┤
                    │         └──────┬───────┘              │
                    │                │ snapshots / deltas   │
                    │    ┌───────────▼────────────┐         │
                    │    │    socket_server.py    │◄───────┐│
                    │    │  (WebSocket, JSON)     │        ││
                    │    └───────────┬────────────┘        ││
                    └────────────────┼──────────────────────┘
                                     │ ws://localhost:PORT   │
                    ┌────────────────▼──────────────────────┴┐
                    │              Godot client               │
                    │                                         │
                    │   ws_client.gd ──► tactical_scene.tscn  │
                    │                      ├ unit_renderer    │
                    │                      ├ terrain_renderer │
                    │                      ├ hud (ability bar,│
                    │                      │   minimap, …)    │
                    │                      └ input_router     │
                    │                            │            │
                    │   onboarding_scene.tscn    │            │
                    │   recon_scene.tscn ────────┘            │
                    │                                         │
                    │   debug_save_panel.tscn (temporary)     │
                    └─────────────────────────────────────────┘
```

Three concurrent conceptual systems:

1. **Python side (new):** `socket_server.py` (WebSocket loop), snapshot/delta serializer, command packet ingest, `save_writer.py`, `save_loader.py`, `onboarding_store.py`. The existing `TacticalEngine` is wrapped; it is not modified beyond the thin accessors it already exposes. **No rewind manager** — rewind is deferred post-launch.
2. **Godot side (new):** tactical scene + renderer + input router, recon scene, onboarding scene, debug save panel. All scenes read from a `TacticalBridge` autoload (the client-side analogue of Stage 9's `UIDataBus`) that owns the WebSocket connection and publishes tick state to subscribers.
3. **Persistence side (cross-cutting):** save file format (one current-state file per class, no history), load/restore, onboarding preference storage. Rewind primitives are out of scope.

### Files to create — Python

**`socket_server.py`** — WebSocket server wrapping the tactical engine. Protected per `CLAUDE.md` ("Socket server is protected — requires explicit user confirmation before any changes"). First creation of this file counts as the protected action and requires Westley's explicit approval.
- `start_server(host, port, engine_factory)` — opens the listening socket, accepts one client at a time (single-player, no multi-client), spawns an engine via `engine_factory(mission_setup)` on client connection.
- Message framing: JSON, line-delimited; keys documented in "Input/Output Shapes" below.
- Server owns the tick clock: runs the engine at `TICK_HZ = 20`, publishes a snapshot on mission start and on reconnection, then delta packets every tick. Ingests command packets on each tick and hands them to the engine before `engine.step()`.
- Disconnect handling: engine **pauses** on client disconnect (does not tick). On reconnect within `RECONNECT_GRACE_SEC`, resume from the last tick. On timeout, drop the mission (Stage 8 does not support mission re-entry from a crashed client — that is crash recovery and is deferred).

**`snapshot_serializer.py`** — converts engine state into snapshot and delta dicts.
- `full_snapshot(engine) → dict` — all unit state, structure state, objective state, drifting node positions, fog-of-war per-faction mask digest, tick number, mission metadata. Emitted on mission start, on client reconnect, and every `SNAPSHOT_INTERVAL_SEC` (config; default 5.0).
- `delta(engine, prev_state) → dict` — unit additions/removals/position+HP changes, structure HP/ownership/production-timer changes, objective progress changes, command ACKs, sound/event hints. Emitted every tick.
- Snapshot and delta both carry `tick` for the client's interpolation buffer.

**`command_ingest.py`** — validates command packets from the client and converts them into the tactical engine's existing command types (`move`, `attack_move`, `attack_target`, `activate_ability`, plus whichever layer commands are chosen in conflict resolution #2). Drops malformed packets with a logged warning (gated behind a debug flag — no release-mode logging of client input).

**`save_writer.py`** — serializes the three launch classes of state. **No history, no snapshot stack, no rewind primitives.** Each class has a single current-state file per slot; writes overwrite the previous file.
- `write_sim_state(slot_id, sim_state) → None` — writes the current simulation state (regions, factions, coherence ledger, diplomacy, technology, lifecycle, chronicle entries). Called after a successful time-jump completes and after every mission resolution lands. Destination: `user://saves/<slot_id>/sim.json`. The file represents "where the playthrough is right now"; it is not a snapshot history.
- `write_tactical_state(slot_id, tactical_state) → None` — writes mid-mission tactical state for single-slot quit-and-resume (S8-1e resolution: one file, consumed on resume). Destination: `user://saves/<slot_id>/tactical.json`. Written on quit; deleted on successful resume.
- `write_onboarding(slot_id, prefs) → None` — writes onboarding preferences (difficulty + archetype weights + rare marks). "Permanent for the generational arc" per bible — overwritten only on new-cycle events (Exodus / Extinction).

**`save_loader.py`** — mirror of the writer.
- `list_slots() → list[SlotMetadata]` — enumerates save slots on disk. Metadata per slot: slot_id, chapter number, last-played timestamp, presence-of-tactical-state flag, onboarding summary (difficulty + count of rare marks).
- `load_sim_state(slot_id) → SimState` — loads the single current simulation state file.
- `load_tactical_state(slot_id) → TacticalState | None` — returns `None` if no in-flight mission is saved.
- `load_onboarding(slot_id) → OnboardingPrefs | None`.
- `consume_tactical_state(slot_id) → None` — deletes the tactical file after a successful resume transitions into the mission scene. Single-slot semantic: the file exists only while the mission is paused.

**`onboarding_store.py`** — dedicated read/write for the onboarding preference payload (difficulty setting + 10-archetype weight map + up-to-2 "rare" marks). Separate module because preferences outlive individual save operations (they survive Exodus / Extinction cycles) and have their own schema.

**Test files:** `test_socket_server.py`, `test_snapshot_serializer.py`, `test_command_ingest.py`, `test_save_writer.py`, `test_save_loader.py`, `test_onboarding_store.py`, `test_stage8_integration.py`.

### Files to create — Godot

**`autoload/tactical_bridge.gd`** — WebSocket client singleton. Owns the connection to `socket_server.py`. Exposes:
- `signal snapshot_received(snapshot: Dictionary)`
- `signal tick_delta_received(delta: Dictionary)`
- `signal connection_state_changed(state: int)`
- `send_command(command: Dictionary) → void`
- `connect_to_engine(host, port)`, `disconnect_from_engine()`

Maintains a small interpolation buffer (last 3 ticks) so the renderer can interpolate positions between 20 Hz engine ticks for 60fps smoothness.

**`scenes/onboarding/onboarding.tscn + .gd`** — the single onboarding screen per bible §"Onboarding and First Chapter." Per S8-2 resolution: a three-button Easy / Medium / Hard difficulty selector at top, followed by 10 mission-archetype rows each with a single "mark as rare" toggle, and a "Confirm" button at bottom. "Confirm" is disabled (with an inline explanation) until at least one archetype remains unmarked. On confirmation: writes the onboarding payload, triggers the opening time jump, hands off to `scenes/opening_scroll/` for the abbreviated 3–5 entry scroll, then transitions into the first recon scene. The three-button difficulty selector stores `"easy" | "medium" | "hard"` in the payload.

**`scenes/opening_scroll/opening_scroll.tscn + .gd`** — the abbreviated 3–5 entry chronicle scroll the player sees right after the opening time jump completes. Per bible §"Opening time jump" — minimal in-Stage-8 implementation: a vertical text list of 3–5 chronicle entries (all world entries — there is no previous mission so no consequence entries), pre-rendered using the Stage 5 chronicle distiller against the post-jump simulation state. **No animated map view, no per-entry expand interaction, no scroll animations** — those land with the full chronicle scroll UI in Beyond-Stage-9 work. Stage 8 is purely "render the entries the distiller produces, in order, and let the player click `Continue` to proceed to recon." This is the player's introduction to both the world and the chronicle voice; landing them in the first mission cold would undercut the bible's "weight of time" framing.

**`scenes/recon/recon.tscn + .gd`** — pre-mission free-camera view. Terrain visible, enemy positions hidden (per `docs/bible_history/bible_2_00_world.md` §Recon Phase). No time pressure. `Begin Mission` button transitions to `tactical.tscn` and signals the server to start the tick clock.

**`scenes/tactical/tactical.tscn + .gd`** — the big one. Top-down RTS camera with free pan/zoom (per `docs/bible_history/bible_2_00_combat.md` §Camera and Player View). Consumes snapshots and deltas from `TacticalBridge`, interpolates unit positions between ticks, renders the three-tier layer system (indicator rings, active-layer focus, dimmed inactive layers per hub §16), sends command packets on player input.

Children scenes:
- `unit_renderer.gd` — per-unit sprite + layer indicator ring + selection halo.
- `terrain_renderer.gd` — spine nodes, gradient-driven dressing (three tiers per §16), reinforcement structure markers with ownership color + HP bar + production timer.
- `hud.tscn + .gd` — the IGoP-inspired HUD per `docs/bible_history/bible_2_00_combat.md` §"Mid-Mission HUD Layout." Top-left info column (objectives + event ticker), top-center banner channel, top-right clock + menu, bottom-center command cluster (selection panel + minimap + reinforcement-structure panel), bottom-center-right control-group tabs, bottom-right commander portrait, right-edge layer selector. Ability bar is cooldown-only (per bible §Abilities — Player-Activated Only). Event ticker content at launch is hardcoded to the beat set (capture / loss / rout / objective threshold); no polished authored content in Stage 8.
- `input_router.gd` — keyboard + mouse → command packet. Handles box-select, click-select, right-click → `move` or `attack_move` (Shift modifier), `A`-then-click → `attack_move`, hotkey abilities, control groups (Ctrl+1..0 bind, 1..0 recall), tilde (`~`) all-army hotkey (auto-includes newly produced units per hub Stage 8 roadmap).

**`scenes/debug_save_panel/debug_save_panel.tscn + .gd`** — temporary UI for Stage 8 testing. Lists slots, shows per-slot metadata (chapter number, last played, tactical-state presence), buttons for "save now," "quit (write tactical state)," "resume (load tactical state)," and "new slot." No rewind, no fork, no timeline view — those are post-launch. Retired when Stage 9's polished save-slot browser ships. The panel calls `TacticalBridge` which calls the Python persistence API over the same WebSocket channel (reuses the socket; does not open a second port).

**`autoload/ws_input_sanitizer.gd`** — thin client-side validator that refuses to send malformed command packets (negative positions, unit IDs not in the last snapshot, etc.). Fails closed. Distinct from Stage 9's `InputSanitizer` which handles text fields — this one handles game commands.

**Test files / Godot:** `.gd` unit tests under `tests/` for `ws_client`, `tactical_bridge` protocol handling, and `input_router` command-packet construction. Godot's built-in `GutTestCase` harness.

### Files to modify — Python

**`tactical_engine.py`** — additive only. No logic changes.
- `pause()` / `resume()` methods toggling a `paused: bool` so `socket_server.py` can hold the tick clock during recon and on disconnect.
- `export_full_state() → dict` and `restore_from_state(state: dict)` — the tactical mid-mission serializer contract. Shape is the same `TacticalState` the `snapshot_serializer.full_snapshot` produces, extended with any internal engine fields (navmesh handle, RNG state, tick counter, pending command queue).
- No change to `step()`, no change to determinism.

**`mission_contracts.py`** — add a `generated_at: str` ISO-8601 field to `MissionSetup` so the save file can label boundary snapshots with a timestamp. Document the shape change in `docs/architecture.md` before code lands (per `CLAUDE.md` rule — `MissionSetup` is the mission-shape contract).

**`config.py`** — new constants (all Stage 8 tuning defaults):

```python
SOCKET_HOST = "127.0.0.1"
SOCKET_PORT = 8765
TICK_HZ = 20
SNAPSHOT_INTERVAL_SEC = 5.0
RECONNECT_GRACE_SEC = 30.0
INTERPOLATION_BUFFER_TICKS = 3

# Camera / input
CAMERA_ANGLE_DEGREES = 60.0  # fixed top-down RTS angle from horizontal
CAMERA_ZOOM_MIN = 0.5
CAMERA_ZOOM_MAX = 2.0
CAMERA_PAN_SPEED_WU_PER_SEC = 1500.0

# Control groups
CONTROL_GROUP_COUNT = 10  # 1..0 on keyboard (0 = group 10)

# Persistence
SAVE_ROOT = "user://saves"  # Godot-side; Python maps to OS path
# No snapshot history in Stage 8 — rewind is deferred post-launch.
```

### Files to modify — Godot

None in Stage 8 beyond Stage 7's renderer-friendly contracts (already in the `TacticalMap` shape). If Stage 9's Godot project exists at Stage 8 start, Stage 8 adds new autoloads and scenes but does not modify `ui_data_bus.gd`, `scene_router.gd`, or any Stage 9 scene. If Stage 9 has not started, Stage 8 creates a fresh Godot project at `godot/` and Stage 9 inherits it.

### Files NOT to modify

- **Protected engine files** (per `CLAUDE.md`): `tick.py`, `drift.py`, `faction.py`, `region.py`, `events.py`, `event_engine.py`, `intent_resolver.py`, `border_friction.py`, `technology.py`, `diplomacy.py`, `world.py`, `templates.py`, `theme_scifi.py`. None touched in Stage 8.
- **`socket_server.py`** — listed as protected in `CLAUDE.md`. **First creation** in Stage 8 is the protected action and requires Westley's explicit approval before Checkpoint A starts.
- **Stage 6 hand-authored test maps (`test_maps.py`)** — keep for regression; the socket server runs against them in Checkpoint B before procedurally generated Stage 7 maps come in.
- **Stage 9 UI scenes and autoloads** — if they exist when Stage 8 begins. Stage 8 is additive.

## Input/Output Shapes

All wire-format payloads are JSON, line-delimited (one JSON object per line over the WebSocket). MessagePack is a post-Stage-8 optimization if performance requires; Stage 8 defaults to JSON for debuggability.

### Server → client: full snapshot (on mission start + every `SNAPSHOT_INTERVAL_SEC` + on reconnect)

```json
{
  "type": "snapshot",
  "tick": 1200,
  "mission_id": "mission_0042",
  "map": {
    "canvas_size": [8000, 8000],
    "spine_nodes": [{"id": "chokepoint_n", "type": "chokepoint", "pos": [4000, 3200], "layer": 1}, "..."],
    "gradient_sources": [{"property": "obstacle_density", "pos": [4000, 3200], "radius": 600, "intensity": 0.7}, "..."],
    "drifting_nodes": [{"id": "obj_alpha", "path": "..."}]
  },
  "units": [
    {"uid": 17, "type": "vanguard", "pos": [4200.5, 3100.2], "layer": 1,
     "hp": 240, "max_hp": 300, "faction": 0,
     "facing_rad": 0.0, "ability_cd_sec": 4.2, "selection_eligible": true,
     "velocity": [0.0, 0.0]}
  ],
  "structures": [
    {"uid": 103, "pos": [4200, 3100], "layer": 1,
     "hp": 2400, "max_hp": 3000, "owner": "player",
     "capture_progress": 0.0, "production_timer_sec": 18.5,
     "production_target": "vanguard", "capture_radius": 300}
  ],
  "objectives": [
    {"id": "hold_zone_alpha", "type": "hold", "progress": 0.42, "status": "in_progress"}
  ],
  "fog_of_war": {
    "player_visible_unit_uids": [17, 18, 19, 88],
    "partial_visibility_uids": [88]
  },
  "tick_rate_hz": 20
}
```

### Server → client: tick delta (every tick)

**Dead-reckoning protocol (adopted pre-Checkpoint F for 200v200 scalability):** The original spec draft sent a position update for every moving unit every tick. At 200v200 this produced ~320 KB/s in the approach phase — fine on localhost but a parsing burden against the 16ms Godot frame budget. Dead-reckoning suppression was chosen over quantized encoding (insufficient compression) and MessagePack (Godot dependency + breaks JSON debuggability). Full design rationale in `docs/architecture.md` §"Stage 8 WebSocket tick delta shape."

A unit absent from `units_updated` and `units_removed` is on-course — the client extrapolates `pos += velocity * dt` using the last known `velocity`. `pos` + `velocity` appear together only on resyncs (prediction error > `DR_RESYNC_THRESHOLD` or velocity change > `DR_VEL_CHANGE_THRESHOLD`). Non-positional changes (`hp`, `layer`, `ability_cd_sec`) are emitted independently, without position.

```json
{
  "type": "delta",
  "tick": 1201,
  "units_updated": [
    {"uid": 17, "pos": [4205.1, 3101.0], "velocity": [102.0, 18.0], "hp": 238},
    {"uid": 22, "hp": 195}
  ],
  "units_added":   [{"uid": 91, "type": "vanguard", "pos": [4200, 3100], "layer": 1, "hp": 300, "max_hp": 300, "faction": 0, "velocity": [0.0, 0.0]}],
  "units_removed": [45],
  "structures_updated": [{"uid": 103, "capture_progress": 0.1}],
  "objectives_updated": [{"id": "hold_zone_alpha", "progress": 0.43}],
  "command_acks": [{"client_command_id": "c-7f2", "accepted": true}],
  "events": [{"kind": "unit_destroyed", "uid": 45, "at": [4210, 3105], "layer": 1}]
}
```

### Client → server: command packet

```json
{
  "type": "command",
  "client_command_id": "c-7f2",
  "client_tick_guess": 1201,
  "command": {
    "kind": "attack_move",
    "unit_uids": [17, 18, 19],
    "target": {"pos": [5100, 4200], "layer": 1}
  }
}
```

Command `kind` values — the canonical **4-command combat vocabulary** (`docs/bible_history/bible_2_00_combat.md` §Command Vocabulary) plus two layer commands on a separate channel (`docs/bible_history/bible_2_00_combat.md` §Layer Assignment Hotkey):

Combat channel (4):
- `move {unit_uids, target: {pos, layer}}`
- `attack_move {unit_uids, target: {pos, layer}}`
- `attack_target {unit_uids, target_uid}`
- `activate_ability {unit_uids, ability_id, optional target}`

Layer channel (2):
- `layer_hard_transfer {unit_uids, target_layer}` — immediate one-time transfer.
- `layer_preference_set {unit_uids, preferred_layer | null}` — persistent preference (null clears).

Session / client bookkeeping (not gameplay commands):
- `control_group_bind {group: 1..10, unit_uids}` and `control_group_recall {group: 1..10}` — published so reconnect can restore bindings.

### Persistence — current simulation state (single file per slot)

```json
{
  "schema_version": 1,
  "slot_id": "slot_a",
  "chapter_number": 12,
  "year": 312,
  "last_written_at": "2026-04-15T12:14:03Z",
  "rng_state": "0x8a3f...",
  "sim_state": {
    "regions": [],
    "factions": [],
    "coherence_ledger": {},
    "diplomacy": {},
    "technology": {},
    "lifecycle": {},
    "chronicle_entries": []
  }
}
```

One file per slot at `user://saves/<slot_id>/sim.json`. Overwritten each time the sim state reaches a new stable boundary (time-jump end, mission resolution landed). No history — the previous state is not retained. Rewind, if/when it ships post-launch, will introduce its own history format independently.

### Persistence — tactical mid-mission state (single-slot quit-and-resume)

Per S8-1e (resolved by Q3): one file per slot while a mission is paused; deleted on successful resume.

```json
{
  "schema_version": 1,
  "slot_id": "slot_a",
  "mission_id": "mission_0042",
  "tick": 1847,
  "rng_state": "...",
  "engine_state": { "full TacticalEngine.export_full_state() output": "..." },
  "mission_setup": { "MissionSetup dict": "..." }
}
```

On resume: `save_loader.load_tactical_state(slot)` rehydrates the engine via `engine.restore_from_state()`; the socket server starts the tick clock where it left off; the client reconnects and receives a fresh full snapshot. The tactical file is then consumed (deleted) so the next quit writes a clean new file.

### Persistence — onboarding preferences

```json
{
  "schema_version": 1,
  "difficulty": "medium",
  "rare_marks": ["counterinsurgency", "evacuation", "suppression"],
  "generational_cycle_id": 1
}
```

No per-archetype weight field — the interaction is binary per S8-2. Unmarked archetypes carry the default preference weight; archetypes in `rare_marks` carry the rare down-weight (0.1 per `docs/bible_history/bible_2_00_missions.md`). Validation at write time: `len(rare_marks) < 10` (at least one archetype must remain unmarked). Rewritten only at new-cycle events (Exodus / Extinction). Preferences live outside the simulation save file per the bible's "permanent for the generational arc" framing.

## Integration Points

- **Engine ↔ server.** `TacticalEngine` is wrapped by `socket_server.py`. Engine code never imports socket or network modules — the wrap is one-directional. Kill switch: `ENABLE_STAGE8_SOCKET = False` in `config.py` runs the engine headless via the existing Stage 6 / Stage 7 harnesses, exactly as today.
- **Engine ↔ persistence.** `save_writer.py` / `save_loader.py` call `TacticalEngine.export_full_state()` and `restore_from_state()`. They do not reach into engine internals — the contract is the same shape both directions.
- **Godot ↔ server.** Single WebSocket connection. `TacticalBridge` is the only module that speaks the wire protocol. All scenes subscribe to its signals.
- **Stage 9 handoff.** Stage 8's `debug_save_panel` is a throwaway UI. When Stage 9 ships, `UIDataBus` calls the same persistence API (`save_loader.list_slots()`, `save_writer.write_sim_state()`, etc.) from GDScript → Python over the same WebSocket channel. Stage 9 deletes the debug panel; the Python persistence modules are unchanged. The Stage 9 save-slot browser exposes load / delete / new-slot only — rewind and fork operations are not part of its Stage 8-era contract.
- **Post-launch rewind handoff.** When the rewind feature ships post-launch, it adds its own history writer on top of the Stage 8 save layer, its own retention policy, its own rewind / fork API, and its own Stage 9 UI additions. Stage 8 does not lay groundwork for this; the rewind feature designs its own serializer from scratch.
- **Kill switches.**
  - `ENABLE_STAGE8_SOCKET` — disables the server; engine remains usable headless.
  - `ENABLE_STAGE8_PERSISTENCE` — disables save writing; game runs mission-to-mission in memory like Stage 7.
  - Default: both OFF at Checkpoint A; flipped ON as each checkpoint is proven.

## Implementation Checkpoints

Each checkpoint is a hard stop per `dev_rules.md` § Mandatory Checkpoints. Run test, show output, wait for Westley approval. Do not batch. Do not continue without explicit approval. Stage 8 has more checkpoints than prior stages because three loosely-coupled subsystems (server, renderer, persistence) compose here and each needs its own proof pass.

### Checkpoint A — Socket Server Scaffold

**Protected-file gate.** `socket_server.py` is protected per `CLAUDE.md`. First creation of this file requires Westley's explicit verbal approval before any code lands. No code until that approval.

**Build:** `socket_server.py` bare skeleton — listens on `SOCKET_HOST:SOCKET_PORT`, accepts one client, echoes a single `{"type": "hello"}` packet on connection, disconnects cleanly. No engine wiring yet.

**Test:** `test_socket_server.py` — start server in background, open a client, read hello packet, close.

**Print:** Port, client address on connect, hello packet, disconnect reason.

**Verify:** Clean start / stop / reconnect. No zombie sockets. No port conflicts on rerun.

⛔ STOP.

### Checkpoint B — Snapshot + Delta Wire Format Against a Headless Engine

**Build:** `snapshot_serializer.py` with `full_snapshot(engine)` and `delta(engine, prev_state)`. `socket_server.py` wired to run a Stage 6 test map at 20 Hz, emitting one full snapshot on connect and deltas every tick.

**Test:** `test_snapshot_serializer.py` — run 100 ticks against a hand-authored test map, capture emitted JSON, verify full snapshot matches engine state and deltas replay back into an identical state.

**Print:** Snapshot size (bytes), delta size (bytes, min/avg/max over 100 ticks), per-tick serialization time, reconstruction check (PASS / FAIL).

**Verify:** Deltas shrink relative to full snapshots by an order of magnitude. Reconstruction holds. No serialization failures on any engine tick.

⛔ STOP.

### Checkpoint C — Command Ingest + Loopback Control

**Build:** `command_ingest.py`. Socket server ingests command packets from a test script playing the role of a client. Commands routed to the engine before `engine.step()`.

**Test:** `test_command_ingest.py` — send each of the four combat commands + both layer commands against a running engine, assert the engine's unit state reflects each command one tick later. Send malformed packets; assert they are dropped without crashing.

**Print:** Commands sent, commands accepted, commands dropped (with reason), engine state diff per command.

**Verify:** All six valid command kinds round-trip. Every malformed-packet category (unknown kind, bad uid, missing field) is dropped cleanly with a gated debug log line.

⛔ STOP.

### Checkpoint D — Save Writer / Loader (Sim State + Onboarding)

**Build:** `save_writer.py` + `save_loader.py` + `onboarding_store.py`. No Godot involvement; all tested headless.

**Test:** `test_save_writer.py` + `test_save_loader.py` + `test_onboarding_store.py` — write a simulated playthrough's sim state to `slot_a`, load it back, assert equality. Write onboarding prefs with boundary cases (0 rare marks, 9 rare marks, attempted 10 rare marks — the last must be rejected). Delete slot, verify disk is clean.

**Print:** File sizes, write / load times, round-trip equality check, rare-mark validation results.

**Verify:** Round-trip is byte-identical (after JSON re-serialization) for a 10-chapter simulated slot. Onboarding validator rejects all-10 rare-mark payload. Deletion leaves no leftover files.

⛔ STOP.

### Checkpoint E — Tactical Mid-Mission Quit-and-Resume

**Build:** `TacticalEngine.export_full_state()` + `restore_from_state()` accessors (additive, no logic change). `save_writer.write_tactical_state()` + `save_loader.load_tactical_state()` + `consume_tactical_state()`.

**Test:** `test_stage8_integration.py::test_quit_resume` — run a Stage 6 mission to tick 500, export tactical state, write to disk, load, restore into a fresh engine, step 100 more ticks, compare the result tick-for-tick against an unbroken run of the same mission to tick 600.

**Print:** Tick 500 unit count + checksum, tick 600 unit count + checksum (both branches), equality verdict. File path written, file path consumed (deleted).

**Verify:** Quit-and-resume is tick-identical to an unbroken run. Tactical file is consumed on load.

⛔ STOP.

### Checkpoint F — Godot Client Connection + Snapshot Ingestion

**Build:** Godot project scaffold (if not already present from a Stage 9 start). `autoload/tactical_bridge.gd` + `ws_client.gd`. A minimal `scenes/debug/debug_ws_test.tscn` that connects to the server and prints incoming snapshot metadata (tick number, unit count, structure count) to an on-screen label.

**Test:** Start the server with a test mission, start Godot, verify label updates every tick.

**Print:** On-screen: tick counter ticking at 20 Hz, unit count, structure count. Terminal (Godot side): connection state transitions.

**Verify:** Connection establishes within 1 second. Tick counter advances smoothly at 20 Hz. Disconnect / reconnect works without crashing either side.

⛔ STOP.

### Checkpoint G — Unit + Terrain Rendering (No HUD Yet)

**Build:** `scenes/tactical/tactical.tscn` with `unit_renderer.gd` + `terrain_renderer.gd`. Free-pan / free-zoom camera. Units drawn as simple placeholder sprites colored by faction. Terrain drawn from spine nodes + gradient heatmaps (debug visualization; not final art). Layer indicator rings beneath units per hub §16 tier 1.

**Test:** Load a Stage 7 generated map, run 500 ticks, record screen.

**Print:** Render frame time (p50, p95, p99), interpolation buffer depth over time, dropped-frame count.

**Verify:** 60fps sustained across the full 500 ticks. Unit positions visibly interpolate between engine ticks (smooth, not stepped). Camera pan / zoom responsive. All 5 layers visible via indicator rings.

⛔ STOP.

### Checkpoint H — Command Input System

**Build:** `input_router.gd`. Click-to-select, box-select, right-click → `move` (or `attack_move` with Shift), `A`-then-click → `attack_move`, `Ctrl+1..0` (or `Cmd+1..0` on macOS — macOS intercepts Ctrl+digit for Mission Control) bind control group, `1..0` recall, `~` all-army hotkey, `W`/`S`/`D`/`C`/`E` ability slots, `Q` / `Z` cycle active layer forward / backward (Westley's choice — replaces the originally specified `Tab` to avoid future conflict with focus-cycling UI), modifier-held `1..5` → layer-preference-set, `X` → layer-hard-transfer.

**Test:** Manual test matrix (one row per command × selection-size). `ws_input_sanitizer.gd` unit tests for malformed packet rejection.

**Print:** Per command row: selection size, command sent, server ACK, engine-state verification (the unit actually moved / attacked / received ability).

**Verify:** Every command in the matrix round-trips cleanly. Control groups persist across unit deaths (bindings auto-shrink when a bound unit dies). All-army hotkey auto-includes newly produced units per hub §Stage 8 entry.

⛔ STOP.

### Checkpoint I — HUD Panels (IGoP Layout)

**Build:** `hud.tscn` + child scenes per `docs/bible_history/bible_2_00_combat.md` §"Mid-Mission HUD Layout." All panels at Stage 8 scope (no polished authored ticker content, no enemy composition, right sidebar empty).

**Test:** Load a Stage 7 generated map with reinforcement structures, run a scripted mission where structures change ownership, objectives progress, forces route. Verify each HUD panel updates in response.

**Print:** Per panel: update cadence, frame time contribution, event-ticker entry list over the mission.

**Verify:** Layout matches reference screenshots. Ability bar shows cooldown rings only (no "ready" prompts). Reinforcement-structure panel lists only player-owned structures. Layer selector highlights active layer and responds to `Q`/`Z` cycle or click (see Checkpoint H note on the `Tab`→`Q`/`Z` swap). Event ticker shows hardcoded beats at the right moments (capture, loss, rout, threshold).

⛔ STOP.

### Checkpoint J — Onboarding Scene + Opening Time Jump + Opening Scroll

**Build:** `scenes/onboarding/onboarding.tscn` per S8-2 resolution. Three-button difficulty selector. 10-row rare-mark toggle list. Confirm button disabled until at least one archetype is unmarked (inline message). `scenes/opening_scroll/opening_scroll.tscn` for the abbreviated 3–5 entry text list. On confirm: write onboarding prefs, trigger opening time jump (20–50 years), invoke the Stage 5 chronicle distiller against the post-jump state to produce 3–5 world entries, render them in `opening_scroll`, then on `Continue` hand off to the recon scene for the first mission.

**Test:** Click through onboarding with adversarial inputs — 0 marks, 5 marks, 9 marks, 10 marks (blocked). Verify payload on disk matches selections. Verify opening time jump runs and produces a valid first mission. Verify the distiller produces 3–5 entries (not more, not fewer) and the scroll renders all of them in order. Verify `Continue` advances to recon.

**Print:** Payload as written to disk, time jump duration, distiller entry count, entry text rendered to scroll, first mission archetype chosen.

**Verify:** All-10-marked case blocked at the UI layer. Payload shape matches the Input/Output Shapes section. Opening time jump produces a valid post-jump sim state. Opening scroll shows 3–5 world-entry chronicle entries (all world-type — no consequence entries since there is no prior mission). Continue button advances to recon.

⛔ STOP.

### Checkpoint K — Recon Phase

**Build:** `scenes/recon/recon.tscn`. Free-camera view of the mission map per `docs/bible_history/bible_2_00_world.md` §Recon Phase. Terrain visible, enemy positions hidden. No time pressure (no mission clock yet). "Begin Mission" button transitions into `tactical.tscn` and tells the server to unpause the engine.

**Test:** Load a generated mission, enter recon, pan / zoom around, confirm enemy units are hidden. Hit Begin Mission, confirm transition to tactical scene and clock starts.

**Print:** Recon time elapsed, camera extents explored (optional), transition latency from Begin Mission to first tactical tick.

**Verify:** Terrain visible including spine nodes + gradient heatmaps (recon-level detail). Enemy units hidden. Mission clock is 0 during recon, starts on Begin Mission.

⛔ STOP.

### Checkpoint L — End-to-End Playable Loop

**Build:** Final wiring. `debug_save_panel.tscn` for save-slot management in lieu of Stage 9's browser.

**Test:** Play a full session. Onboarding → opening time jump → recon → mission → mission resolution → time jump → next recon → next mission → quit mid-mission → resume mid-mission → finish. Observe the whole loop.

**Print:** Session log: state transitions, save-write events, disk usage per slot, any errors.

**Verify:** Loop works end-to-end without crashes. Quit-and-resume restores the exact tactical state. Sim state carries across mission boundaries. Onboarding prefs persist across the session.

⛔ STOP.

### Checkpoint M — Performance + Stability (Final)

**Build:** No new code. Performance tuning + bug fixes only.

**Test:** 200v200 engagement on a Stage 7 generated large-canvas map. Record: renderer frame time, engine tick time, WebSocket round-trip, snapshot/delta sizes, total session memory. Play three full sessions (different seeds) checking for leaks, interpolation stalls, reconnect issues.

**Print:** Perf table: frame time p50/p95/p99, tick time, RTT, leak check over three sessions.

**Verify:** Renderer holds 60fps at 200v200 load (frame time p95 < 16ms). Engine tick time well under 50ms (one tick at 20 Hz). WebSocket RTT consistently under 5ms on localhost. No memory growth across three sessions. No protected-file edits (git diff clean against protected-file list).

⛔ STOP.

## Invariants

- **I1 — Tick rate fidelity.** Engine ticks at exactly `TICK_HZ` (20). Measured over a 60-second run, tick count is 1200 ± 5.
- **I2 — Renderer frame time.** Renderer p95 frame time < 16ms at 200v200 load on the Checkpoint M scenario.
- **I3 — Interpolation smoothness.** No visible unit-position stuttering during a 60-second capture. The interpolation buffer never exceeds `INTERPOLATION_BUFFER_TICKS` depth.
- **I4 — Determinism preserved.** Engine-side determinism from Stage 6 holds — the server wrapper does not introduce non-determinism. A fixed command stream + seed reproduces tick-for-tick.
- **I5 — Quit-and-resume round-trip.** Writing tactical state at tick N and restoring produces an engine that steps to tick N+K tick-identical to an unbroken run to tick N+K.
- **I6 — Save / load round-trip.** Sim-state file round-trips byte-identical (after canonical JSON re-serialization) for any valid sim state.
- **I7 — Onboarding validation.** `write_onboarding` rejects payloads with `len(rare_marks) == 10`; accepts all other valid subsets.
- **I8 — Client input sanitization.** `ws_input_sanitizer` refuses to send any packet with a unit uid not in the latest snapshot, a negative position, or an unknown command kind. 100% rejection on a corpus of adversarial inputs.
- **I9 — Protected files untouched.** `git diff` against the protected-file list (CLAUDE.md) is clean at Checkpoint M. `socket_server.py` is treated as protected from creation onward — no edits after its initial Checkpoint A landing without a fresh approval.
- **I10 — No rewind code.** `git grep` for rewind-related terms (rewind, fork_from, snapshot_history, timeline_branch) returns zero hits in implementation code. The post-launch rewind feature is a separate stage; Stage 8 must not lay groundwork.

Per CLAUDE.md: if an invariant fails, you may not widen thresholds or weaken tests. Escalate real bugs, or narrow scope (skip-cases never meant to be caught).

## Done Condition

- All 13 checkpoints (A–M) run, shown, approved by Westley.
- All 10 invariants (I1–I10) pass.
- A full session (onboarding → recon → mission → quit → resume → finish) runs cleanly on both Linux and Windows Godot builds.
- `tuning_output/stage8/` contains perf measurements from Checkpoint M.
- Bible capture items (§"Bible Capture Pending") all applied and verified in a pre-merge diff review.
- No protected engine file modified. `socket_server.py` is protected from its first edit forward.
- `docs/architecture.md` reflects the `MissionSetup.generated_at` field addition.
- IGoP HUD reference images present at `docs/legacy/design_questions/igop_hud_reference_alpha.png` and `igop_hud_reference_beta.png`.

## Files Created

(Filled in after implementation.)

## Notes for the Implementing Session

- **Socket server protection.** `socket_server.py` must get explicit verbal approval before Checkpoint A creates it. Once created, any subsequent edit requires another approval. Do not refactor it "while you're in there."
- **Three loosely-coupled systems, one stage.** Checkpoints split A–C (server), D–E (persistence), F–I (Godot client), J–K (onboarding + recon), L–M (integration + perf). The A–C and D–E groups can be parallelized by a single developer across sessions if useful; F and later depend on A–C.
- **Godot client is a presentation layer.** No gameplay logic in GDScript. If you find yourself reimplementing a tactical rule in Godot, stop — the rule belongs in the Python engine and the client should read the result via snapshot/delta.
- **Performance discipline.** Per dev_rules.md § Performance regression discipline, Checkpoint M has a hard frame-time budget. Do not ship a renderer that drops frames at 200v200.
- **IGoP reference.** The HUD layout and command-input philosophy both cite Immortal: Gates of Pyre. When in doubt about what a panel should look like or how a hotkey should behave, open the reference screenshots.
- **No rewind.** This is the second-most-important rule in this spec after the socket-server protection. Rewind is a post-launch feature. Do not add rewind hooks "we'll need later." Stage 8 ships saves, not rewind.

---

## Paused at This State — 2026-04-16

Stage 8 is paused partway through Checkpoint I. The tactical client renders, accepts commands, and round-trips through the socket server cleanly; Checkpoints A–H are signed off; Checkpoint I (HUD Panels) is plumbed but has gaps (see below). Pausing here to address a broader structural issue.

### Cause — Economic / Galaxy View Gap

The tactical layer works in isolation, but there is no surrounding economic / galaxy-level wrapper for missions to flow into or out of. Missions launch from a debug harness, resolve, and end in a void. The macro loop that gives tactical gameplay its *meaning* — galaxy view of factions and territory, time jumps feeding into mission briefings, mission outcomes feeding back into the simulation — does not yet exist in the client. That scaffolding lives in **Stage 9** (UI shell: main menu, era library, mission briefing), **Stage 10** (backend integration of the UI bus with the live sim), **Stage 11** (galaxy view + seamless transition), and **Stage 12** (loop edges: onboarding, debrief, save). Note Ouroboros has **no currency / no tech tree** by design (per `docs/bible_history/bible_2_00_combat.md` §Mid-Mission HUD Layout and `bible_monetization.md` (deleted 2026-05-31; see docs/bible_history/)); "economic view" here refers to the *galactic-scale* economy of faction territory, technology level, and field drift — not a resource-management UI.

Resuming Stage 8 ahead of resolving that gap is valid (Checkpoints J–M stand on their own), but the ordering was re-examined and further Stage 8 work was deferred. When resuming, either finish Stage 8 on its own terms or bring the Stage 9 / 11 scaffolding in first so Checkpoint J's onboarding → time jump → recon → mission flow has somewhere to *land*.

### Checkpoint Status at Pause

| Checkpoint | Status | Notes |
|---|---|---|
| A — Socket server scaffold | ✅ done | |
| B — Snapshot + delta wire format | ✅ done | |
| C — Command ingest + loopback | ✅ done | |
| D — Save writer / loader | ✅ done | |
| E — Tactical quit-and-resume | ✅ done | |
| F — Godot connection + snapshot ingest | ✅ done | |
| G — Unit + terrain rendering | ✅ done | Tier-1 layer indicator rings under units still TODO per hub §16. |
| H — Command input system | ✅ done | See divergences below. |
| I — HUD panels (IGoP layout) | ⚠️ partial | HUD built; event-emission gap on the sim side; hamburger menu is a placeholder. |
| J — Onboarding + opening time jump + opening scroll | ⏸ not started | |
| K — Recon phase | ⏸ not started | |
| L — End-to-end playable loop | ⏸ not started | Blocked by J, K, and the galaxy gap above. |
| M — Performance + stability | ⏸ not started | |

### Checkpoint I — Remaining Work

1. **Sim-side event emission.** `simulation/snapshot_serializer.py` currently emits one event kind: `unit_destroyed` (line 229). The four additional kinds required by the bible ticker list (`docs/bible_history/bible_2_00_combat.md` §Mid-Mission HUD Layout — "reinforcement structure captured / lost, force routed, objective threshold hit") are *not emitted anywhere*. HUD handlers in `scenes/tactical/hud.gd:72-89` are defensively coded for these kinds but will never fire until the sim emits them. Work needed:
   - `structure_captured` / `structure_lost` — diff `structure.owner_faction` between snapshots in the serializer; emit from the perspective of each diff.
   - `force_routed` — threshold on aggregate faction HP fraction or unit-count drop per tick; location TBD (`objectives.py` or a new `events/tactical_events.py`).
   - `objective_threshold` — emit when an `Objective.progress` crosses a threshold (25/50/75/100%).
2. **Hamburger menu button** at `hud.gd::_build_clock` (`☰`) is a visual placeholder with no `pressed.connect(...)`. Expected to route to a pause / settings overlay eventually — out of Checkpoint I scope, flagged for later.
3. **Layer indicator rings** under units (hub §16 Tier 1 — mechanical baseline). Belongs to Checkpoint G/H; not currently rendered. `unit_renderer.gd` would need a per-unit ring draw keyed on `unit["layer"]`.
4. **Right sidebar empty** — intentional per Checkpoint I build scope ("right sidebar empty"). No action needed.

### Divergences From Spec / Bible

Applied during implementation with Westley's approval. Spec lines already edited in place; listed here so a future session sees them in one view.

**Command input (Checkpoint H, spec line 468):**
- Ability keys: `W`/`S`/`D`/`C`/`E` (spec originally said `Q`/`W`/`E`/`R`/`T`).
- Layer cycle: `Q` forward / `Z` backward (spec originally said `Tab`). Westley's call to avoid conflict with Godot's focus-cycling on `Tab`.
- Layer hard transfer: `X`.
- Control-group bind: `Ctrl+1..0` **or `Cmd+1..0` on macOS**. macOS intercepts `Ctrl+digit` for Mission Control desktop switching, so Godot never sees it; accepting `meta_pressed` as an alternative modifier lets Mac users bind groups with `Cmd`. Code: `input_router.gd::_handle_digit`.
- Camera pan: edge-scroll (classic RTS), not WASD. Per `feedback_camera_controls` memory.

**HUD layout (Checkpoint I, diverges from `docs/bible_history/bible_2_00_combat.md` §Mid-Mission HUD Layout *text* in favor of matching the IGoP *reference screenshots*):**
- Minimap: **bottom-left at 1.5× base** (330×330). Bible text said "center or right-of-center." Westley's call after seeing the reference.
- Reinforcements panel: immediately right of the minimap. Bible text said "right of minimap" — matches.
- Selection panel: **bottom-center**. Bible text said "selected-unit portrait panel left-of-center."
- Commander portrait: **omitted** for now. Placeholder-only art, not needed for Stage 8 functional scope.
- Control-group strip: bottom-right, left of layer selector. Populates reactively as groups are bound.
- Layer selector: far right, 5 buttons for L0–L4, active layer highlighted.
- Ability display: single cooldown ring in the selection panel (see `hud.gd::_AbilityRing`). Bright-green outlined ring when ready, filled dark circle with seconds-remaining text while on cooldown. No "ready" prompts per bible "no ready notifications beyond the ring itself."

**Sim-side fixes applied during Stage 8 work (not strictly Stage 8 scope, but referenced in Stage 8 context):**
- `simulation/movement.py` — approach-state engagement-lock replaced with in-range guard. Fast units pursue fleeing targets instead of oscillating when the engagement lock drops for a tick. Plan reference: `/Users/westley/.claude/plans/lively-wandering-bear.md`. Known follow-up balance issue: `_ATTACK_MOVE_LEASH_SQ = 200.0 * 200.0` equals Raider attack range; Bastion (range 800) clears `auto_engage_target` before `resolve_damage` can use it. Out of scope here.
- Attack backswing added (combat polish).
- Selection-box visual artifact on mouse release fixed in `input_router.gd::_finish_selection` via `queue_redraw()`.
- Ctrl-C hang on `socket_server.py` shutdown is **known and accepted** (socket server becomes dead code after Stage 10 per `stage_10_spec.md` — stdio transport replaces it). Do not "fix" by refactoring the protected file.

### State to Preserve for Resumption

**How to run:**
1. `python3 simulation/run_debug_server.py` — starts socket server on `SOCKET_HOST:SOCKET_PORT`, loads a Stage 7 test map.
2. Open Godot project — tactical scene auto-connects via `TacticalBridge` autoload.

**Autoload map (important — two independent bridges):**
- `TacticalBridge` (`autoload/tactical_bridge.gd`) — WebSocket client to `simulation/socket_server.py`. **This is what the tactical HUD uses.** Exposes `units`, `structures`, `objectives`, `display_positions`, `current_tick`, `map_data`; signals `snapshot_received`, `tick_delta_received`, `connection_state_changed`.
- `SimBridge` (`autoload/sim_bridge.gd`) — stdio pipes to `simulation/pipe_transport.py`. **For Stage 9 strategic UI scenes**, auto-spawns a sim child process on project load. Unrelated to tactical. The `"SimBridge: spawned sim pid=..."` line in Godot output is from this and can be ignored during Stage 8 tactical work.

**Integration tests:** `simulation/test_stage8_integration.py` — 4/4 passing at pause. Run before resuming any Stage 8 work.

**Files created in Stage 8 (inventory for "Files Created" section above):**
- Sim side: `simulation/socket_server.py`, `simulation/snapshot_serializer.py`, `simulation/command_ingest.py`, `simulation/run_debug_server.py`, `simulation/pipe_transport.py`, save / load modules, test files.
- Godot side: `scenes/tactical/tactical.tscn` + `.gd`, `scenes/tactical/terrain_renderer.gd`, `scenes/tactical/unit_renderer.gd`, `scenes/tactical/input_router.gd`, `scenes/tactical/hud.tscn` + `.gd`. Autoloads: `autoload/tactical_bridge.gd`, `autoload/ws_client.gd`, `autoload/ws_input_sanitizer.gd`, `autoload/sim_bridge.gd`. (Other autoloads predate Stage 8.)
- Docs: IGoP HUD reference screenshots at `docs/legacy/design_questions/Immortal-Gates-of-Pyre-*.jpg` — permanent reference for layout decisions.

### Out-of-Stage-8 Items Surfaced During Implementation

Track separately; **do not fold back into Stage 8**:
- **Tactical art pass.** Settled Reach GLB assets exist at `docs/legacy/blender_stuff/the-settled-reach/` (at least `SetReachBastionT2.glb` imported). No stage spec currently covers importing era art into `tactical.tscn` — the scene is still Node2D with placeholder sprites per Checkpoint G. New design decision required: convert `tactical.tscn` to Node3D with an orthographic 60° camera (the `CAMERA_ANGLE_DEGREES = 60.0` constant anticipates this but is currently unused) vs. pre-render meshes to sprite sheets. Bible update + new stage spec needed if pursued.
- **Zoom-dependent camera tilt** (top-down at wide zoom → angled at close zoom). Not in any stage spec or bible section; hub §16 explicitly assumes *"the fixed top-down camera angle"*. If desired, belongs in `docs/bible_history/bible_2_00_combat.md` §Camera and Player View first.
- **Layer visualization Tier 2/3** (`game_bible.md` §16 — light and heavy environmental dressing). Tier 1 (indicator rings) is Checkpoint H territory. Tiers 2/3 are deferred with no current owner.

### When Resuming

Check this section first. Then:
1. Re-read `CLAUDE.md` (no shotgun fixes rule is especially important mid-implementation).
2. Confirm `test_stage8_integration.py` still passes.
3. Decide Checkpoint I disposition: close the sim-side event-emission gap, or explicitly defer with `# DEFERRED:` comments and move to Checkpoint J.
4. Before starting J, revisit the **Economic / Galaxy View Gap** framing above — if Stage 9 / 11 work landed in the interim, some Checkpoint J integration points (onboarding → time jump → recon handoff) may need to target the new scenes rather than the standalone harness.
