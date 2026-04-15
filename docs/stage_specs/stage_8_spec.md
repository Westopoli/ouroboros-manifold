# Stage 8 — Godot Renderer, Command Interface, and Game State Persistence

## Goal

Prove that the tactical simulation can be played — not just simulated headless. Stage 8 stands up three systems simultaneously and proves they compose: (1) a Godot renderer that consumes tactical engine state over a WebSocket bridge and draws it at 60fps with linear interpolation between 20 Hz engine ticks; (2) a command interface (selection, control groups, movement, abilities, layer assignment) that issues the same command protocol the tactical engine already accepts from enemy macro scripts; (3) a game-state persistence layer covering three classes of state — simulation state between missions/time jumps, tactical-engine state mid-mission for quit-and-resume, and onboarding preferences — with a rewind-with-re-seed primitive that lets the player roll the simulation back to a boundary snapshot and continue forward with fresh stochastic outcomes.

Stage 8 is the stage where the game becomes **playable for the first time**. Stages 1–4 proved the simulation. Stage 5 proved the narrative pipeline. Stage 5.5 proved the mission generator. Stage 6 proved the tactical engine headless. Stage 7/7.5 proved procedural maps and enemy macro scripts. Stage 8 proves a human can sit down, receive a mission, study the terrain in a recon phase, command forces in real time, and have their save survive a quit.

**Not in scope:** main-menu / new-game / load-game / save-slot-browser UI (Stage 9), mission briefing screen (Stage 9), era library / monetization UI (Stage 9), chronicle scroll UI and animated time-jump map (Beyond Stage 9), mission debrief/outcome screen (Beyond Stage 9), tutorial (Beyond Stage 9), galaxy/system/planet view (Beyond Stage 9), crash recovery, multi-branch tree UI, cloud saves (deferred per open question #15). Stage 8 ships the **tactical scene** plus the **persistence primitive** plus the **onboarding screen** — nothing else.

**Architecture.** The Python tactical engine runs as a standalone WebSocket server. Godot is a pure client that subscribes to tick snapshots, renders them, interpolates between ticks for a 60fps presentation, and sends command packets back. No engine logic executes in Godot — it is a presentation layer that happens to also capture input. Persistence is a separate Python-side concern: the save writer serializes simulation state and tactical state to disk; the save loader reconstructs them; rewind is "load snapshot N, discard snapshots >N in this slot (linear), resume simulation from N with fresh seed."

## Design-Doc Conflicts and Gating Open Questions — READ FIRST

> **This section is flagged per the user's request.** Implementation cannot start until the gating questions are resolved in a Claude.ai brainstorming session and the spec is updated.

### Bible-internal conflicts (flag to Westley for resolution)

1. **Onboarding scope.** `game_bible.md` §"Implementation Stage Roadmap" entry for Stage 8 (lines ~524) lists "Onboarding screen: single screen with difficulty setting and mission preference weights … See 'Onboarding and First Chapter' for the full design." The same hub's "Beyond Stage 9" bullet (line ~528) lists "onboarding screen" among deferred items. The Stage 8 entry is the more recent v2.09 text. **Proposed resolution:** delete "onboarding screen" from the "Beyond Stage 9" bullet (it is already in Stage 8). Flag for Westley approval before the Stage 8 spec goes live.

2. **Command-vocabulary count.** `bible_combat.md` §Command Vocabulary enumerates **four** commands (`move`, `attack_move`, `attack_target`, `activate_ability`). Other bible passages — `bible_combat.md` line 235 ("5-command protocol"), line 456 ("the same 5 commands the player does"), hub line 524 ("Ability hotkeys mapped to the 5-command vocabulary") — refer to **five** commands. The layer-assignment hotkey system (`bible_combat.md` §"Layer Assignment Hotkey") introduces two more commands (hard layer transfer, layer preference assignment) which are the likely source of the discrepancy, but the count is inconsistent across the text. **Proposed resolution:** Westley picks one:
   - **(A)** Canonical count is **5** = the four combat commands + a single "layer assignment" command (both hard transfer and preference flow through one command object with a flag). Edit `bible_combat.md` §Command Vocabulary to list all five.
   - **(B)** Canonical count is **4** for the combat vocabulary; layer commands are a separate channel. Edit L235, L456, and the Stage 8 hub entry to say "4-command combat vocabulary plus layer commands" or similar.
   - **Stage 8 cannot ship a command protocol until one is picked.** The Stage 8 WebSocket command packet shape depends on this decision.

### Gating open design questions (unanswered — block spec finalization)

Per `docs/design_questions/stage_7_8_design.md`, these are still [OPEN] and classified as **design decisions** (not engineering defaults, not tuning):

3. **S8-1d — Snapshot retention policy.** Unlimited / last-N ring buffer / keep-major-prune-intermediate / manual prune. Determines how far back the player can meaningfully rewind and shapes the save-file format. Stage 8 cannot ship a save-writer without this decision — the serializer either writes an unbounded list, a fixed-size circular buffer, or a tagged-keep/tagged-prune structure, and these are not freely interchangeable.
4. **S8-1e — Tactical mid-mission state scope.** Single-slot quit-and-resume (write on quit, load on resume, consume once) vs rewind-extends-into-missions (multiple tactical snapshots, rewind to earlier mid-mission tick). Within-mission rewind is significantly more complex (unit nav state, ability cooldowns, fog memory, ongoing effects) and changes what `TacticalEngine` must be able to round-trip to disk. Stage 8 cannot ship the tactical-state persister until this scope is fixed.
5. **S8-2 — Onboarding preference weight UI.** Sliders per archetype / star ratings / like-this + rare checkboxes / drag-to-rank. The onboarding screen itself is in Stage 8 scope, but the interaction model is unanswered. Affects the onboarding scene's structure and the data shape of the preference payload.
6. **S8-3 — Mid-mission UI information density.** Minimap details, selection info panel, objective tracker, reinforcement-structure status display, enemy composition hints. The ability bar's cooldown-only behavior is specified in the bible; the rest of the HUD is not. Affects what the tactical HUD scene must contain.

**Recommendation to Westley:** resolve questions 1, 3, 4 before Stage 8 implementation begins (they shape contracts). Questions 2, 5, 6 can be pinned with engineering defaults in this spec pending your approval, but they are flagged as design decisions so a default-plus-review is not the same as an answer.

### Captured decisions the spec relies on (no change needed)

- **S8-1** (save scope): sim + tactical mid-mission + onboarding; replays excluded; sim rewind-with-re-seed in scope. Captured in hub §15.
- **S8-1a** (cadence): boundary-only — every time-jump boundary + every mission start/end. Captured in hub §15.
- **S8-1b** (branching): linear default + explicit "fork from here." Captured in hub §15.
- **S8-1c** (chronicle on rewind): **erase** on linear rewind; fork-from-here is the preservation mechanism. Captured in hub §15.
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
                    │    ┌─────┴─────────────────────┐      │
                    │    │      rewind_manager.py    │      │
                    │    │  (snapshot pivot + fork)  │      │
                    │    └───────────┬───────────────┘      │
                    │                │                      │
                    │         ┌──────▼──────┐               │
                    │         │ simulation  │               │
                    │         │ (tick loop) │               │
                    │         └──────┬──────┘               │
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

1. **Python side (new):** `socket_server.py` (WebSocket loop), snapshot/delta serializer, command packet ingest, `save_writer.py`, `save_loader.py`, `rewind_manager.py`, `onboarding_store.py`. The existing `TacticalEngine` is wrapped; it is not modified beyond the thin accessors it already exposes.
2. **Godot side (new):** tactical scene + renderer + input router, recon scene, onboarding scene, debug save panel. All scenes read from a `TacticalBridge` autoload (the client-side analogue of Stage 9's `UIDataBus`) that owns the WebSocket connection and publishes tick state to subscribers.
3. **Persistence side (cross-cutting):** save file format, boundary-snapshot capture, load/restore, rewind (linear), fork-from-here, onboarding preference storage.

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

**`save_writer.py`** — serializes all three classes of state.
- `write_sim_snapshot(slot_id, label, sim_state) → snapshot_id` — writes a boundary snapshot. `label` is a human-readable tag ("chapter_3 — mission start", "time_jump 312→358"). Destination: `user://saves/<slot_id>/sim/<snapshot_id>.json` (Godot-side path; Python maps to the OS-equivalent directory).
- `write_tactical_state(slot_id, tactical_state)` — writes mid-mission tactical state for quit-and-resume. Single file per slot (S8-1e default pending: "single-slot quit-and-resume" — see open question).
- `write_onboarding(slot_id, prefs) → None` — writes onboarding preferences (difficulty + archetype weights + rare marks). "Permanent for the generational arc" per bible — overwritten only on new-cycle events (Exodus / Extinction).

**`save_loader.py`** — mirror of the writer.
- `list_slots() → list[SlotMetadata]` — enumerates save slots on disk.
- `load_sim_snapshot(slot_id, snapshot_id) → SimState`
- `load_tactical_state(slot_id) → TacticalState | None`
- `load_onboarding(slot_id) → OnboardingPrefs | None`

**`rewind_manager.py`** — implements linear rewind + fork-from-here per S8-1b.
- `rewind(slot_id, snapshot_id)` — linear: discards snapshots with `tick > snapshot.tick` in this slot, restores `snapshot_id`, wipes chronicle entries from the discarded window (S8-1c), seeds the simulation RNG with a fresh seed drawn from the system entropy source, resumes simulation.
- `fork(slot_id, snapshot_id, new_slot_id, label)` — duplicates the slot at `snapshot_id` into `new_slot_id`; the original is unchanged (the caller typically rewinds the original next). Forked slots appear as sibling slots to the Stage 9 save-slot browser; in Stage 8 they appear in the debug save panel.
- Retention policy (S8-1d) is GATED — the manager's pruning behavior is a stub until the question is resolved. Stage 8 ships the rewind primitive itself; the pruning hook is a `TODO: S8-1d` line in the module.

**`onboarding_store.py`** — dedicated read/write for the onboarding preference payload (difficulty setting + 10-archetype weight map + up-to-2 "rare" marks). Separate from the simulation save file because preferences outlive individual rewinds.

**Test files:** `test_socket_server.py`, `test_snapshot_serializer.py`, `test_command_ingest.py`, `test_save_writer.py`, `test_save_loader.py`, `test_rewind_manager.py`, `test_onboarding_store.py`, `test_stage8_integration.py`.

### Files to create — Godot

**`autoload/tactical_bridge.gd`** — WebSocket client singleton. Owns the connection to `socket_server.py`. Exposes:
- `signal snapshot_received(snapshot: Dictionary)`
- `signal tick_delta_received(delta: Dictionary)`
- `signal connection_state_changed(state: int)`
- `send_command(command: Dictionary) → void`
- `connect_to_engine(host, port)`, `disconnect_from_engine()`

Maintains a small interpolation buffer (last 3 ticks) so the renderer can interpolate positions between 20 Hz engine ticks for 60fps smoothness.

**`scenes/onboarding/onboarding.tscn + .gd`** — the single onboarding screen per bible §"Onboarding and First Chapter." **GATED on S8-2** (interaction model). Scaffolding lands early but the weight-UI implementation waits on the answer.

**`scenes/recon/recon.tscn + .gd`** — pre-mission free-camera view. Terrain visible, enemy positions hidden (per `bible_world.md` §Recon Phase). No time pressure. `Begin Mission` button transitions to `tactical.tscn` and signals the server to start the tick clock.

**`scenes/tactical/tactical.tscn + .gd`** — the big one. Top-down RTS camera with free pan/zoom (per `bible_combat.md` §Camera and Player View). Consumes snapshots and deltas from `TacticalBridge`, interpolates unit positions between ticks, renders the three-tier layer system (indicator rings, active-layer focus, dimmed inactive layers per hub §16), sends command packets on player input.

Children scenes:
- `unit_renderer.gd` — per-unit sprite + layer indicator ring + selection halo.
- `terrain_renderer.gd` — spine nodes, gradient-driven dressing (three tiers per §16), reinforcement structure markers with ownership color + HP bar + production timer.
- `hud.tscn + .gd` — minimap (bottom-right), selection info panel, objective tracker, ability bar (cooldown-only per bible), reinforcement structure status list, **mid-mission HUD is GATED on S8-3**; Stage 8 ships minimap + selection info + ability bar + objective tracker; the density questions (enemy composition hints, reinforcement detail level) are placeholders.
- `input_router.gd` — keyboard + mouse → command packet. Handles box-select, click-select, right-click → `move` or `attack_move` (Shift modifier), `A`-then-click → `attack_move`, hotkey abilities, control groups (Ctrl+1..0 bind, 1..0 recall), tilde (`~`) all-army hotkey (auto-includes newly produced units per hub Stage 8 roadmap).

**`scenes/debug_save_panel/debug_save_panel.tscn + .gd`** — temporary UI for Stage 8 testing. Lists slots, shows boundary snapshots per slot, buttons for "rewind to here," "fork from here," "quit (write tactical state)," "resume (load tactical state)." Retired when Stage 9's polished save-slot browser ships. The panel calls `TacticalBridge` which calls the Python persistence API over the same WebSocket channel (reuses the socket; does not open a second port).

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
# S8-1d retention policy: GATED. Stub constant, do not rely on:
SAVE_RETENTION_POLICY = "unlimited"  # TODO: S8-1d
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

Command `kind` values (pending conflict resolution #2 — command vocabulary count):

- `move`, `attack_move`, `attack_target`, `activate_ability` — the four combat commands from `bible_combat.md` §Command Vocabulary.
- `layer_hard_transfer {unit_uids, target_layer}` — immediate transfer.
- `layer_preference_set {unit_uids, preferred_layer | null}` — persistent preference (null clears).
- `control_group_bind {group: 1..10, unit_uids}` and `control_group_recall {group: 1..10}` — client-side operations that also publish so reconnect can restore bindings.

If Westley resolves conflict #2 as **(A) canonical 5**, collapse `layer_hard_transfer` and `layer_preference_set` into a single `layer_assign {unit_uids, target_layer, mode: "hard" | "preference"}` packet.

### Persistence — boundary sim snapshot (on time-jump end + mission start + mission end)

```json
{
  "schema_version": 1,
  "snapshot_id": "snap_00042",
  "slot_id": "slot_a",
  "label": "Chapter 3 — Mission 12 start",
  "boundary_kind": "mission_start",
  "tick": 3120,
  "year": 312,
  "created_at": "2026-04-15T12:14:03Z",
  "parent_snapshot_id": "snap_00041",
  "rng_seed": "0x8a3f...",
  "sim_state": {
    "regions": [],
    "factions": [],
    "coherence_ledger": {},
    "diplomacy": {},
    "technology": {},
    "lifecycle": {},
    "chronicle_entries": []
  },
  "onboarding_ref": "slot_a/onboarding.json"
}
```

On linear rewind: all snapshots in `slot_a` with `tick > target.tick` are deleted, including their chronicle entries. On fork: `slot_b` is initialized by copying `slot_a`'s snapshots up to and including `snapshot_id`; the two slots then evolve independently.

### Persistence — tactical mid-mission state (quit-and-resume)

**GATED on S8-1e.** Default shape assuming single-slot quit-and-resume:

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

On resume: `save_loader.load_tactical_state(slot)` rehydrates the engine via `engine.restore_from_state()`; the socket server starts the tick clock where it left off; client reconnects and receives a fresh full snapshot.

### Persistence — onboarding preferences

```json
{
  "schema_version": 1,
  "difficulty": "medium",
  "archetype_weights": {
    "defensive_stand": 1.0, "assault": 1.0, "multi_front_defense": 1.0,
    "counterinsurgency": 1.0, "siege_breaking": 1.0, "reconquest": 1.0,
    "suppression": 1.0, "interception": 1.0, "evacuation": 1.0, "containment": 1.0
  },
  "rare_marks": ["counterinsurgency", "evacuation"],
  "generational_cycle_id": 1
}
```

Rewritten only at new-cycle events (Exodus / Extinction). Rewind does not touch onboarding prefs — they live outside the rewindable simulation state per the bible ("permanent for the generational arc").

## Integration Points

- **Engine ↔ server.** `TacticalEngine` is wrapped by `socket_server.py`. Engine code never imports socket or network modules — the wrap is one-directional. Kill switch: `ENABLE_STAGE8_SOCKET = False` in `config.py` runs the engine headless via the existing Stage 6 / Stage 7 harnesses, exactly as today.
- **Engine ↔ persistence.** `save_writer.py` / `save_loader.py` call `TacticalEngine.export_full_state()` and `restore_from_state()`. They do not reach into engine internals — the contract is the same shape both directions.
- **Godot ↔ server.** Single WebSocket connection. `TacticalBridge` is the only module that speaks the wire protocol. All scenes subscribe to its signals.
- **Stage 9 handoff.** Stage 8's `debug_save_panel` is a throwaway UI. When Stage 9 ships, `UIDataBus` calls the same persistence API (`save_loader.list_slots()`, `rewind_manager.rewind()`, etc.) from GDScript → Python over the same WebSocket channel. Stage 9 deletes the debug panel; the Python persistence modules are unchanged.
- **Kill switches.**
  - `ENABLE_STAGE8_SOCKET` — disables the server; engine remains usable headless.
  - `ENABLE_STAGE8_PERSISTENCE` — disables save writing; game runs mission-to-mission in memory like Stage 7.
  - `ENABLE_STAGE8_REWIND` — disables rewind and fork (persistence still writes). Defensive flag in case rewind has issues late in the stage.
  - Default: all OFF at Checkpoint A; flipped ON as each checkpoint is proven.
