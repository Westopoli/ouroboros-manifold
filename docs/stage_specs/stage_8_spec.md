# Stage 8 — Godot Renderer, Command Interface, and Game State Persistence

## Goal

Prove that the tactical simulation can be played — not just simulated headless. Stage 8 stands up three systems simultaneously and proves they compose: (1) a Godot renderer that consumes tactical engine state over a WebSocket bridge and draws it at 60fps with linear interpolation between 20 Hz engine ticks; (2) a command interface (selection, control groups, movement, abilities, layer assignment) that issues the same command protocol the tactical engine already accepts from enemy macro scripts; (3) a **launch-grade save layer** covering three classes of state — simulation state (single current-state file per slot), tactical-engine state mid-mission for single-slot quit-and-resume, and onboarding preferences — with no rewind, no history, no fork.

Stage 8 is the stage where the game becomes **playable for the first time**. Stages 1–4 proved the simulation. Stage 5 proved the narrative pipeline. Stage 5.5 proved the mission generator. Stage 6 proved the tactical engine headless. Stage 7/7.5 proved procedural maps and enemy macro scripts. Stage 8 proves a human can sit down, receive a mission, study the terrain in a recon phase, command forces in real time, quit in the middle of a mission and resume later, and pick up the next chapter after a session break.

**Not in scope:** main-menu / new-game / load-game / save-slot-browser UI (Stage 9), mission briefing screen (Stage 9), era library / monetization UI (Stage 9), chronicle scroll UI and animated time-jump map (Beyond Stage 9), mission debrief/outcome screen (Beyond Stage 9), tutorial (Beyond Stage 9), galaxy/system/planet view (Beyond Stage 9). **Rewind, fork-from-here, boundary-snapshot history, and multi-snapshot timeline browsing are all deferred to a post-launch rewind feature** (see hub §15 for the deferred design sketch). Stage 8 ships the **tactical scene** plus the **save layer** plus the **onboarding screen** — nothing else.

**Architecture.** The Python tactical engine runs as a standalone WebSocket server. Godot is a pure client that subscribes to tick snapshots, renders them, interpolates between ticks for a 60fps presentation, and sends command packets back. No engine logic executes in Godot — it is a presentation layer that happens to also capture input. Persistence is a separate Python-side concern: the save writer serializes the current simulation state, any in-flight tactical state, and onboarding preferences to disk; the save loader reconstructs them on resume. No snapshot history, no pivot operations, no timeline concept.

## Bible Capture Pending

These bible edits landed during the Stage 8 write-up session; they do not block implementation but are listed here so an auditor can verify them:

1. **Hub "Beyond Stage 9" bullet** — removed the stale "onboarding screen" entry; the Stage 8 roadmap paragraph is now the only source of truth for onboarding scope.
2. **Hub Stage 8 roadmap paragraph** — "5-command vocabulary" replaced with "4-command vocabulary (`move`, `attack_move`, `attack_target`, `activate_ability`) plus the two layer commands." Persistence language rewritten from "rewind-capable" to "saves, not rewind — rewind is a post-launch feature."
3. **`bible_combat.md` L235 and L456** — "5-command protocol" / "same 5 commands" corrected to "4-command protocol" / "same 4 commands." The 5×3 compositional grid in the bible belongs to the **enemy macro behavior system**, not player commands.
4. **Hub §15 (Simulation State Journaling and Rollback)** — rewritten to remove rewind from Stage 8 scope. Stage 8 ships saves only; rewind is a post-launch feature with its own design sketch (pre-mission-selection snapshot boundary, 5-mission minimum gate, mission-generator re-run on rewind, linear-default + fork, chronicle erased on rewind).
5. **Onboarding rare-mark rule** — `game_bible.md:155` and `bible_missions.md:301` rewritten: the "up to two markable as rare" cap was removed. The rule is now "any subset may be marked rare, provided at least one archetype remains unmarked." The interaction is binary per archetype (rare or default); no sliders or gradation.

## Gating Open Design Questions — READ BEFORE IMPLEMENTATION

> **This section must reach zero entries before implementation begins.** Each open item is a design decision (per `design_rules.md` classification — not an engineering default, not a tuning value) and must be resolved in a Claude.ai brainstorming session, captured into the bible/spec, and deleted from this list.

Per `docs/design_questions/stage_7_8_design.md`, these are still [OPEN]:

- **S8-3 — Mid-mission UI information density.** Minimap details, selection info panel, objective tracker, reinforcement-structure status display, enemy composition hints. The ability bar's cooldown-only behavior is specified in the bible; the rest of the HUD is not. Affects what the tactical HUD scene must contain.

### Captured decisions the spec relies on (no change needed)

- **S8-1** (save scope — updated by Q3): three classes of state persist at launch: (1) current simulation state (single file, no history); (2) tactical mid-mission state for single-slot quit-and-resume; (3) onboarding preferences. Replays excluded. Rewind deferred post-launch.
- **S8-1e** (tactical mid-mission state scope — resolved by Q3): single-slot quit-and-resume. No multi-snapshot tactical state, no mid-mission rollback.
- **S8-1a, S8-1b, S8-1c, S8-1d** (deferred post-launch): all live under the post-launch rewind feature per Q3. Design notes preserved in the design doc for the eventual rewind design session.
- **Onboarding in Stage 8** (Q1): resolved Option A. Bible edited.
- **Player command count = 4** (Q2): resolved. Bible edited.
- **Onboarding interaction model** (Q4 / S8-2): binary per-archetype "mark as rare" — any subset allowed except all 10. Difficulty is a three-button Easy / Medium / Hard selector. Bible edited.
- **S75-* / S7-*** resolutions as documented in the design doc.

## Bible References

- **`bible_combat.md`** — §Layer Assignment Hotkey (layer commands the renderer/input system must support), §Camera and Player View (free pan/zoom, minimap), §Command Vocabulary (command set for the command packet), §Unit Behavior AI / Abilities — Player-Activated Only (ability bar behavior: cooldown-only).
- **`bible_world.md`** — §Recon Phase (terrain visible, enemies hidden; free camera, no time pressure; mission clock starts on "Begin Mission"), §"The Vertical Dimension" / §§ on layer accessibility (what the renderer must display per layer).
- **`bible_monetization.md`** — §"Platform: PC-only" (keyboard+mouse-only command design — the renderer does not target controller input in this stage).
- **`game_bible.md` (hub)** — "The Cycle" step 2 (Recon Phase design), "Onboarding and First Chapter" (onboarding screen + opening time jump), §15 Simulation State Journaling and Rollback (persistence + rewind contract), §16 Space Era Vertical Layer Visualization (three-tier layer rendering approach the tactical renderer implements).

Do NOT read `bible_chronicle.md`, `bible_antagonist.md`, `bible_monetization.md` (beyond the PC-only line), `bible_simulation.md` (beyond the field list the save writer serializes), or `bible_ai_pipeline.md` — not relevant to Stage 8.

## Cross-Stage References

- **Stages 1–4** — the save writer serializes `Region`, `Faction`, coherence-ledger, diplomacy, technology, and lifecycle state. The persistence layer reads these; it does not mutate them at runtime. On rewind, the simulation is restored from a snapshot and advanced forward with a fresh RNG seed — the forward simulation uses the existing tick loop unchanged.
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

**`scenes/onboarding/onboarding.tscn + .gd`** — the single onboarding screen per bible §"Onboarding and First Chapter." Per S8-2 resolution: a three-button Easy / Medium / Hard difficulty selector at top, followed by 10 mission-archetype rows each with a single "mark as rare" toggle, and a "Confirm" button at bottom. "Confirm" is disabled (with an inline explanation) until at least one archetype remains unmarked. On confirmation: writes the onboarding payload, triggers the opening time jump, then transitions into the first recon scene. The three-button difficulty selector stores `"easy" | "medium" | "hard"` in the payload.

**`scenes/recon/recon.tscn + .gd`** — pre-mission free-camera view. Terrain visible, enemy positions hidden (per `bible_world.md` §Recon Phase). No time pressure. `Begin Mission` button transitions to `tactical.tscn` and signals the server to start the tick clock.

**`scenes/tactical/tactical.tscn + .gd`** — the big one. Top-down RTS camera with free pan/zoom (per `bible_combat.md` §Camera and Player View). Consumes snapshots and deltas from `TacticalBridge`, interpolates unit positions between ticks, renders the three-tier layer system (indicator rings, active-layer focus, dimmed inactive layers per hub §16), sends command packets on player input.

Children scenes:
- `unit_renderer.gd` — per-unit sprite + layer indicator ring + selection halo.
- `terrain_renderer.gd` — spine nodes, gradient-driven dressing (three tiers per §16), reinforcement structure markers with ownership color + HP bar + production timer.
- `hud.tscn + .gd` — minimap (bottom-right), selection info panel, objective tracker, ability bar (cooldown-only per bible), reinforcement structure status list, **mid-mission HUD is GATED on S8-3**; Stage 8 ships minimap + selection info + ability bar + objective tracker; the density questions (enemy composition hints, reinforcement detail level) are placeholders.
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
     "hp": 240, "max_hp": 300, "faction": "player",
     "facing_rad": 1.57, "ability_cd_sec": 4.2, "selection_eligible": true}
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

```json
{
  "type": "delta",
  "tick": 1201,
  "units_updated": [{"uid": 17, "pos": [4205.1, 3101.0], "hp": 238}],
  "units_added":   [{"uid": 91, "type": "vanguard", "pos": [4200, 3100], "layer": 1, "hp": 300, "max_hp": 300, "faction": "player"}],
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

Command `kind` values — the canonical **4-command combat vocabulary** (`bible_combat.md` §Command Vocabulary) plus two layer commands on a separate channel (`bible_combat.md` §Layer Assignment Hotkey):

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

No per-archetype weight field — the interaction is binary per S8-2. Unmarked archetypes carry the default preference weight; archetypes in `rare_marks` carry the rare down-weight (0.1 per `bible_missions.md`). Validation at write time: `len(rare_marks) < 10` (at least one archetype must remain unmarked). Rewritten only at new-cycle events (Exodus / Extinction). Preferences live outside the simulation save file per the bible's "permanent for the generational arc" framing.

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
