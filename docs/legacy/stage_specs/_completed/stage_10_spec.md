# Stage 10 — Backend Integration

## Goal

Replace Stage 9's `UIDataBus` mock layer with a live connection to the Python simulation, running as a child process communicating over stdio pipes.

## Bible References

- `game_bible.md` — Stage 10 roadmap entry, Sacred Design Principle #3, "The Cycle" section
- `docs/bible_history/bible_2_00_combat.md` — Tactical engine tick rate (20 ticks/sec), command vocabulary (move, attack_move, attack_target, activate_ability), snapshot/delta state model
- `bible_monetization.md` (deleted 2026-05-31; see docs/bible_history/) — Entitlement model (Stage 10 hardcodes "Settled Reach owned"), trial/subscription structure (not implemented, context only) <!-- LEGACY 2026-05-09: trial/subscription model scrapped; see bible_monetization.md "Current Monetization Model" section. Hardcoded "Settled Reach owned" entitlement remains valid as a per-era ownership flag. -->

- `animation_strategy.md` — Loading screen animation vocabulary (shader atmospheres, glyph bloom, blinking cursor)

## Context

**Builds on:**

- **Stage 8** — Defined the sim/renderer protocol: message schema (snapshot messages, delta messages, command messages), tick rate (20/sec), hybrid state sync (full snapshot on mission start + periodic snapshots every N seconds, deltas between). Stage 8 used a raw TCP `socket_server.py` as the transport — Stage 10 replaces that transport with stdio pipes while preserving the message schema.
- **Stage 9** — Built all non-combat UI screens against a `UIDataBus` singleton serving mock data. Every screen calls `UIDataBus` methods and connects to `UIDataBus` signals. Stage 10 preserves this API and swaps the data source behind it.

**Key architectural decisions (resolved in design brainstorming):**

1. **Process lifecycle:** Godot spawns the Python sim as a child process via `OS.create_process()` on game launch, kills it via `OS.kill()` on quit. Single click to launch, single process from the player's perspective (the sim runs headless in the background with no visible window).
2. **IPC mechanism:** Stdio pipes, not WebSocket. The sim reads commands from stdin, writes state to stdout. No network port, no firewall popup, no port conflicts. The WebSocket protocol from Stage 8 is replaced; `socket_server.py` is dead code after this stage.
3. **Message format:** Length-prefixed JSON. Each message is a 4-byte big-endian length header followed by a UTF-8 JSON string. The message *schema* (types, fields, snapshot/delta structure) carries forward from Stage 8 unchanged — only the transport changes.
4. **Startup handshake:** The sim writes incremental `{"type": "progress", ...}` messages during initialization, then a final `{"type": "ready", ...}` message. Godot shows a loading screen with progress bar and rotating flavor text until the ready message arrives. Timeout after a configurable duration (default 30 seconds) triggers an error screen.
5. **Crash recovery:** If the sim process dies, Godot detects the broken pipe, transitions to an error screen showing a pre-authored message and the relative path to the crash log file (`logs/crash_report.txt`). No auto-restart, no state recovery. The crash log contains the Python traceback, sim version, and OS/Python version. It does NOT contain: save file contents, simulation state, absolute file paths, environment variables, or machine-identifying information (hostname, username, MAC address).
6. **Entitlement:** A single boolean config flag `ENTITLEMENT_SETTLED_REACH = true`. All era-access checks read this flag. No entitlement data structure, no ownership categories, no key system stubs.
7. **UIDataBus architecture:** `UIDataBus` stays as the public API. It delegates to either `MockDataSource` (Stage 9's existing mock data) or `SimBridgeDataSource` (the live pipe reader). A config flag `USE_LIVE_SIM` switches between them. Screens never change.
8. **Stderr:** The sim redirects its own stderr to `logs/sim_stderr.log` on startup. Godot ignores the stderr pipe. The crash log is a separate file written by the sim's exception handler.
9. **Shutdown:** Godot kills the sim process via `OS.kill()` on quit. No graceful shutdown command — Stage 10 has no save system, so there's nothing to flush. A shutdown command will be added in Stage 12 when save serialization lands.

## What to Build

### File 1: `sim_bridge.gd` — Pipe Reader and Writer

**Purpose:** Autoload singleton that owns the sim child process and the stdio pipe communication. This is the `SimBridgeDataSource` that `UIDataBus` delegates to when `USE_LIVE_SIM = true`.

**Scope:**

- On `_ready()`: spawns the sim process via `OS.create_process()`, stores the pipe handles and PID.
- In `_process()`: polls the stdout pipe for incoming messages. Reads 4-byte length headers, accumulates bytes until a complete message is available, parses the JSON, and dispatches by message type.
- Dispatches messages via signals: `progress_updated(step, pct)`, `state_updated(snapshot_or_delta)`, `sim_ready(metadata)`, `sim_error(info)`.
- Provides `send_command(cmd_dict)` method: serializes the dict to length-prefixed JSON and writes it to the sim's stdin pipe.
- Monitors process liveness: checks `OS.is_process_running(pid)` each frame. If the process dies unexpectedly, emits `sim_error` with crash context.
- On `_notification(NOTIFICATION_WM_CLOSE_REQUEST)` and tree exit: kills the sim process via `OS.kill(pid)`.
- Exposes the same data-access API as `MockDataSource` (method signatures matching what `UIDataBus` expects), reading from the most recent parsed state.

### File 2: `sim_bridge_data_source.gd` — Data Source Interface Implementation

**Purpose:** Implements the data source interface that `UIDataBus` delegates to. Wraps `SimBridge`'s raw state into the same data shapes that `MockDataSource` returns, so screens see identical structures regardless of source.

**Scope:**

- Implements every method that `UIDataBus` currently delegates to `MockDataSource`: `get_mission_briefing()`, `get_era_data()`, `get_save_slots()`, `get_commander_info()`, etc. (exact method list derived from Stage 9's `UIDataBus` API).
- Each method reads from `SimBridge`'s most recent parsed state and transforms it into the return shape screens expect.
- For data the sim doesn't provide yet (e.g., save slot metadata — Stage 12), returns sensible defaults or empty structures.

### File 3: `mock_data_source.gd` — Extracted Mock Data Source

**Purpose:** Stage 9's existing mock data, extracted from `UIDataBus` into a standalone class implementing the same data source interface.

**Scope:**

- Contains all the hardcoded mock data currently inline in `UIDataBus`.
- Implements the same interface as `sim_bridge_data_source.gd`.
- Used when `USE_LIVE_SIM = false`.

### File 4: Modified `ui_data_bus.gd` — Delegation Layer

**Purpose:** Modify the existing `UIDataBus` to delegate to whichever data source is active based on config.

**Scope:**

- On `_ready()`: reads `config.USE_LIVE_SIM`. If true, instantiates `SimBridgeDataSource` (which internally connects to `SimBridge`). If false, instantiates `MockDataSource`.
- All existing public methods delegate to the active data source.
- All existing signals are re-emitted from the active data source's signals.
- No screen-facing API changes. Every screen that currently works against `UIDataBus` continues to work unchanged.

### File 5: `loading_screen.tscn` / `loading_screen.gd` — Loading Screen

**Purpose:** Displayed on game launch while the sim initializes. Shows progress, flavor text, and transitions to the main menu when the sim reports ready.

**Scope:**

- **Background:** The main menu galaxy shader (reuse `scenes/shared/galaxy/galaxy_structure.tscn` or the main menu background shader) playing at reduced intensity / dimmed.
- **Progress display:** A progress bar or progress indicator in monospace (JetBrains Mono), showing the current initialization step name and percentage. Uses the blinking cursor from the animation strategy. Example: `LOADING CONFIG ████████░░ 80% █` (blinking cursor after the percentage).
- **Flavor text:** Below the progress bar, a rotating text snippet drawn from `data/loading_tips.json`. Displayed in serif (Newsreader), secondary text color, italic. Rotates on each progress step change, or on a timer (every 3–5 seconds) if a step takes long. Fade transition between snippets.
- **Timeout:** If no `ready` message arrives within `config.SIM_STARTUP_TIMEOUT_SEC` (default 30), transitions to the error screen.
- **Ready transition:** On receiving the `sim_ready` signal, the loading screen fades out and transitions to the main menu scene.
- **Error transition:** On receiving `sim_error` or on timeout, transitions to the error screen.
- **Aesthetic:** Follows the bible's UI aesthetic — dark background, monospace for data, serif for narrative flavor text, gold brand accent for the progress bar, subtle scanlines overlay.

### File 6: `error_screen.tscn` / `error_screen.gd` — Error Screen

**Purpose:** Displayed when the sim crashes or fails to start.

**Scope:**

- **Message:** Pre-authored text only. "The simulation encountered an error and had to stop." No internal error details on screen. No absolute file paths.
- **Crash log pointer:** "A crash report has been saved to `logs/crash_report.txt` in your game folder. If you'd like to help, send this file to Westley." Displayed in monospace, tertiary text color.
- **Actions:** Two buttons — "Restart" (kills any lingering sim process, respawns, returns to loading screen) and "Quit" (kills sim process, exits game).
- **Security:** The screen displays only pre-authored strings. No exception text, no stack traces, no dynamic content from the sim. The crash log file is the only place diagnostic data lives. The crash log file itself follows the security rules: Python traceback with relative paths only, sim version, OS version, Python version. No save data, no absolute paths, no env vars, no machine-identifying info.

### File 7: `data/loading_tips.json` — Flavor Text Pool

**Purpose:** Array of strings displayed on the loading screen. Authored by Westley.

**Scope:**

- A JSON array of strings: `["tip one", "tip two", ...]`.
- Loaded by the loading screen scene on startup.
- If the file is missing or empty, the loading screen still works — it just shows progress without flavor text.
- Example placeholder content for initial implementation (Westley replaces with real content):
  ```json
  [
    "The simulation doesn't care about you. That's what makes it interesting.",
    "Every tick, every faction evaluates every neighbor.",
    "Somewhere in the galaxy, a faction just made a terrible decision.",
    "Your predecessor's mistakes are now your problem."
  ]
  ```

### File 8: Sim-side pipe protocol (`pipe_transport.py` or modification to existing sim entry point)

**Purpose:** Replace the sim's TCP `socket_server.py` transport with stdio pipe I/O.

**Scope:**

- The sim reads commands from stdin as length-prefixed JSON (4-byte big-endian header + UTF-8 JSON body).
- The sim writes state updates (progress, ready, snapshots, deltas) to stdout in the same length-prefixed JSON format.
- On startup, the sim writes progress messages: `{"type": "progress", "step": "<step_name>", "pct": <0.0-1.0>}` for each initialization phase. Step names are human-readable (e.g., "loading_config", "initializing_simulation", "building_world").
- After initialization completes, the sim writes: `{"type": "ready", "version": "<sim_version>"}`.
- The sim redirects its own stderr to `logs/sim_stderr.log` at startup (relative to the sim's working directory, which is the game install folder).
- The sim installs a top-level exception handler that writes crash data to `logs/crash_report.txt` on unhandled exceptions: Python traceback (with absolute paths stripped to relative), sim version string, `platform.system()`, `platform.release()`, `sys.version`. No other data.
- `socket_server.py` is marked as dead code. It is not deleted (git history), but no code path references it after this stage.
- **Stdout discipline:** The sim MUST NOT write anything to stdout except length-prefixed protocol messages. All `print()` calls, logging output, and library warnings must be redirected to stderr (which goes to the log file). A stray `print()` will corrupt the pipe protocol and crash the connection. The sim should set `sys.stdout` to a wrapper that enforces the length-prefix framing, and redirect Python's default print target to stderr at startup.

### File 9: Config additions

**Purpose:** New config values for Stage 10.

**Scope (added to existing config):**

- `USE_LIVE_SIM: bool = true` — switches UIDataBus between live and mock data source.
- `SIM_EXECUTABLE_PATH: String = "sim/ouroboros_sim"` — relative path to the sim executable (or Python script during development). Platform suffix appended at runtime (`.exe` on Windows).
- `SIM_STARTUP_TIMEOUT_SEC: float = 30.0` — how long the loading screen waits for the ready message before showing the error screen.
- `ENTITLEMENT_SETTLED_REACH: bool = true` — hardcoded entitlement flag. All era-access checks read this. Replaced by real entitlement system Beyond Stage 13.
- `IS_RELEASE_BUILD: bool = false` — already exists from Stage 9. Stage 10 uses it to gate whether the crash log includes the full traceback (non-release) or a sanitized version (release). For the friends-ZIP build, this is `true`.
- `CRASH_LOG_PATH: String = "logs/crash_report.txt"` — relative path for crash log output.
- `STDERR_LOG_PATH: String = "logs/sim_stderr.log"` — relative path for sim stderr capture.

## Input/Output Shapes

### Pipe Protocol Messages (sim → Godot)

```json
// Progress (during startup)
{
  "type": "progress",
  "step": "initializing_simulation",
  "pct": 0.4
}

// Ready (startup complete)
{
  "type": "ready",
  "version": "0.10.0"
}

// Full snapshot (mission start + periodic)
{
  "type": "snapshot",
  "tick": 14200,
  "units": [
    {
      "id": "u_001",
      "type": "vanguard",
      "pos": [120.5, 340.2],
      "layer": 1,
      "hp": 1200,
      "hp_max": 1200,
      "state": "idle",
      "target": null,
      "faction": "player"
    }
  ],
  "objectives": [ ... ],
  "reinforcement_structures": [ ... ],
  "fog_state": { ... }
}

// Delta update (between snapshots)
{
  "type": "delta",
  "tick": 14201,
  "changes": [
    {"id": "u_001", "pos": [121.0, 339.8], "hp": 1150, "state": "engaged"},
    {"id": "u_007", "state": "dead"}
  ]
}

// Simulation state for non-combat screens (era data, world state, etc.)
{
  "type": "sim_state",
  "world": { ... },
  "mission_briefing": { ... },
  "commander": { ... },
  "era": "settled_reach"
}
```

### Pipe Protocol Messages (Godot → sim)

```json
// Player command
{
  "type": "command",
  "tick": 14201,
  "cmd": "attack_move",
  "unit_ids": ["u_001", "u_002"],
  "target": [500.0, 200.0],
  "layer": 1
}

// Request full state (for non-combat screens)
{
  "type": "request_state",
  "scope": "mission_briefing"
}

// Ability activation
{
  "type": "command",
  "tick": 14205,
  "cmd": "activate_ability",
  "unit_ids": ["u_003"],
  "ability": "rally"
}
```

### Data Source Interface (UIDataBus delegation)

```
# Methods (return types match Stage 9's existing mock shapes)
get_mission_briefing() -> Dictionary
get_era_data() -> Dictionary
get_save_slots() -> Array[Dictionary]
get_commander_info() -> Dictionary
get_force_composition() -> Dictionary
get_region_state() -> Dictionary
get_entitlement_state() -> Dictionary   # reads ENTITLEMENT_SETTLED_REACH flag
is_era_accessible(era_id: String) -> bool

# Signals
state_updated(new_state: Dictionary)
era_data_changed()
mission_briefing_ready(briefing: Dictionary)
```

## Integration Points

**Replaces:** `UIDataBus`'s internal mock data with a delegation pattern (mock or live source based on config).

**New autoloads:** `SimBridge` (pipe owner, always loaded when `USE_LIVE_SIM = true`).

**Modified autoloads:** `UIDataBus` (adds delegation, preserves public API).

**Kill switch:** `config.USE_LIVE_SIM = false` reverts the entire stage to Stage 9's mock behavior. No sim process is spawned, no pipes are opened, `UIDataBus` serves mock data exactly as before. This is the primary kill switch.

**Scene flow change:** Game launch now goes Loading Screen → (sim ready) → Main Menu, instead of directly to Main Menu. When `USE_LIVE_SIM = false`, the loading screen is skipped and the game goes directly to Main Menu as before.

**Dead code:** `socket_server.py` (Stage 8's TCP transport) is no longer referenced by any code path. It remains in the repo for git history but is effectively dead.

## Checkpoints

### Checkpoint A — Sim-Side Pipe Transport

**Build:** Implement `pipe_transport.py` (or modify the sim's entry point). The sim reads stdin, writes stdout, both length-prefixed JSON. Stderr redirects to file. Progress messages on startup, ready message on completion. Crash handler writes crash log.

**Prove it:** Run the sim standalone from a terminal. Verify:
1. Progress messages appear on stdout as properly framed length-prefixed JSON (not raw text).
2. Ready message appears after progress completes.
3. `logs/sim_stderr.log` exists and captures any stderr output.
4. Force a crash (e.g., raise an exception after ready). Verify `logs/crash_report.txt` is written with traceback (relative paths only), sim version, OS info. Verify no absolute paths, no env vars, no username in the crash log.
5. Verify that a `print("debug")` call in sim code does NOT appear as raw text on stdout (it should go to stderr log or be caught by the stdout wrapper).

**STOP. Show output. Wait for Westley.**

### Checkpoint B — Godot-Side Pipe Reader (SimBridge)

**Build:** Implement `sim_bridge.gd` as an autoload. It spawns the sim process via `OS.create_process()`, reads the pipe in `_process()`, parses length-prefixed JSON messages, and emits signals.

**Prove it:** Launch the game with `USE_LIVE_SIM = true`. Verify:
1. The sim process spawns (visible in Task Manager as a separate background process, no console window).
2. `SimBridge` receives and parses the progress messages (print them to Godot console).
3. `SimBridge` receives the ready message.
4. `SimBridge.send_command()` successfully writes a test command to the sim's stdin (sim logs receipt to stderr log file).
5. Killing the sim process externally (via Task Manager) causes `SimBridge` to detect the dead process and emit `sim_error`.
6. Quitting the Godot game kills the sim process (no orphan in Task Manager after game closes).

**STOP. Show output. Wait for Westley.**

### Checkpoint C — Loading Screen

**Build:** Implement `loading_screen.tscn` / `loading_screen.gd`. Connects to `SimBridge` signals. Shows progress bar, step name, and flavor text from `data/loading_tips.json`. Transitions to main menu on ready, error screen on failure/timeout.

**Prove it:** Launch the game. Verify:
1. Loading screen appears with the galaxy background (or appropriate shader).
2. Progress bar advances as the sim initializes, step names update.
3. Flavor text rotates between progress steps.
4. On sim ready, loading screen fades out and main menu appears.
5. Set `SIM_STARTUP_TIMEOUT_SEC = 2` and delay sim startup artificially. Verify timeout triggers error screen.
6. Kill the sim during loading. Verify error screen appears with crash log path.

**STOP. Show output. Wait for Westley.**

### Checkpoint D — Error Screen

**Build:** Implement `error_screen.tscn` / `error_screen.gd`. Pre-authored error message, crash log path, Restart and Quit buttons.

**Prove it:** Trigger the error screen (kill sim during loading or force a crash). Verify:
1. Error message is the pre-authored text, not a dynamic error string.
2. Crash log path shown is relative (`logs/crash_report.txt`), not absolute.
3. "Restart" button kills lingering process, respawns sim, returns to loading screen, and successfully reaches main menu.
4. "Quit" button kills sim process and exits the game cleanly (no orphan process).
5. Verify the crash log file on disk contains: traceback with relative paths, sim version, OS/Python version. Verify it does NOT contain: absolute paths, env vars, hostname, username.

**STOP. Show output. Wait for Westley.**

### Checkpoint E — UIDataBus Delegation

**Build:** Extract `MockDataSource` from `UIDataBus`. Implement `SimBridgeDataSource`. Modify `UIDataBus` to delegate based on `USE_LIVE_SIM` config flag.

**Prove it:**
1. Set `USE_LIVE_SIM = false`. Launch game. Verify all Stage 9 screens work exactly as before (mock data, no sim process spawned, loading screen skipped).
2. Set `USE_LIVE_SIM = true`. Launch game. Verify all Stage 9 screens receive data from the live sim. At minimum: Main Menu loads, Era Library shows Settled Reach as owned and Roman as free (based on `ENTITLEMENT_SETTLED_REACH` flag), Mission Briefing populates with real sim data.
3. Toggle `USE_LIVE_SIM` between runs to confirm clean switching.
4. Verify no Stage 9 screen code was modified (only `UIDataBus` internals changed).

**STOP. Show output. Wait for Westley.**

### Checkpoint F — End-to-End Integration

**Build:** Full flow test: game launch → loading screen → main menu → start new game → mission briefing shows real sim data → begin mission → tactical engine receives commands and sends state updates → Godot renders units moving.

**Prove it:** Play through the full loop:
1. Launch game. Loading screen with progress and flavor text.
2. Main menu appears after sim ready.
3. Start new game. Era selection shows Settled Reach owned, Roman free.
4. Mission briefing populates from real simulation state (region name, enemy faction, force composition — all from the sim, not mocks).
5. Begin mission. Units appear. Issue a move command. Verify units respond (the sim processes the command and sends delta updates, Godot renders the movement).
6. Close the game. Verify sim process is killed (no orphan).
7. Repeat with `USE_LIVE_SIM = false` — verify the game still launches into mock mode cleanly.

**STOP. Show output. Wait for Westley.**

## Done Condition

The game launches, shows a loading screen with progress and flavor text while the sim initializes, transitions to the main menu with real sim data, allows starting a mission with real simulation state, and responds to player commands during tactical gameplay — all over stdio pipes with no network port. The `USE_LIVE_SIM = false` kill switch restores full Stage 9 mock behavior. The error screen handles sim crashes with a secure, pre-authored message and a crash log file containing diagnostic data with no sensitive information. The player experiences a single executable launch with no visible backend process window.

## Files Created

- `simulation/pipe_transport.py` — stdio pipe transport, crash handler, stderr redirect, sim_state/mission_briefing emission
- `autoload/sim_bridge.gd` — process spawner, reader/writer threads, length-prefix JSON protocol, error routing
- `autoload/sim_bridge_data_source.gd` — live data source; delegates to SimBridge state
- `autoload/mock_data_source.gd` — extracted from UIDataBus; used when USE_LIVE_SIM=false
- `scenes/loading_screen/loading_screen.tscn` + `loading_screen.gd`
- `scenes/error_screen/error_screen.tscn` + `error_screen.gd`
- `data/loading_tips.json`

## Files Modified

- `autoload/ui_data_bus.gd` — stripped of inline mock data; now delegates to `_source` (MockDataSource or SimBridgeDataSource)
- `autoload/scene_router.gd` — added `"loading_screen"`, `"error_screen"`, `"tactical"` to SCENES dict; initial `_current_scene_name` set to `"loading_screen"`; `go_back()` now guards `_transitioning` before popping stack (race-condition fix)
- `project.godot` — main scene changed from `main_menu.tscn` to `loading_screen.tscn`
- `scenes/mission_briefing/mission_briefing.gd` — DEPLOY FORCES button now calls `SceneRouter.go_to("tactical")` instead of showing stub modal

---

## ⏸ PAUSED — 2026-04-16

**Cause:** Economic/Galaxy view gap. The tactical pipeline (stdio transport) is complete, but the macro simulation data layer — world state, faction names, region names, chapter/generation tracking — is not yet connected to the Godot UI pipeline. This creates a gap where the mission briefing can only populate from tactical engine unit data rather than full macro sim state. Implementing the remaining Checkpoint F item requires Stage 8 (WebSocket tactical scene) to be signed off first, as both implementations share `tactical.gd` and `input_router.gd` in the same working directory with no branch protection.

**What is complete:**
- Checkpoints A–F are all passed and signed off by Westley.
- Loading screen, error screen, UIDataBus delegation, sim process lifecycle all fully functional.
- Mission briefing populates from real engine data (unit types, counts, force parity, tick counter).
- DEPLOY FORCES navigates to the tactical scene.
- `USE_LIVE_SIM=false` kill switch restores full mock behavior cleanly.

**One deferred item (Checkpoint F, item 5):**

Wire the tactical transport from WebSocket (Stage 8) to stdio pipe (Stage 10). Two targeted file changes:

1. **`scenes/tactical/tactical.gd` `_ready()`** — remove `TacticalBridge.connect_to_engine("127.0.0.1", 8765)`. Add `SimBridge.state_updated.connect(TacticalBridge._on_message)` so the existing state machine (dead-reckoning, snapshot/delta apply) is fed from the stdio pipe instead.

2. **`scenes/tactical/input_router.gd` `_send()`** — replace `TacticalBridge.send_command(cmd)` with `SimBridge.send_command({"type": "command", "command": cmd})`.

`socket_server.py`, `WsClient`, and `TacticalBridge.connect_to_engine()` are left intact (not deleted) per spec — they become dead code paths rather than removed files.

**Divergences from spec:**

| Spec said | What was built | Reason |
|-----------|----------------|--------|
| `OS.create_process()` for spawning sim | `OS.execute_with_pipe()` | Godot 4.6 API — `execute_with_pipe` returns the stdio pipe handle directly; `create_process` does not expose pipes |
| `SIM_EXECUTABLE_PATH` config constant | `SIM_SCRIPT_PATH` in `sim_bridge.gd` | Named to reflect that it points to a Python script during development, not a compiled executable |
| Mission briefing populated from "real simulation state" (implies world/faction/region data) | Populated from tactical engine unit snapshot only (unit types, counts, parity, tick) | Macro sim data (region names, faction names, chapter/generation) is not yet connected to the tactical pipeline — Economic/Galaxy view gap |
| Recon phase between mission briefing and tactical scene | DEPLOY goes directly to `tactical.tscn` | Recon scene is Stage 8 scope; Stage 10 only wires the navigation entry point |
| `_pending_error_screen` pattern not in spec | Added to `sim_bridge.gd` | SceneRouter transition guard blocks `go_to("error_screen")` if called mid-transition; retry-in-`_process` pattern needed to guarantee error screen reaches the player |
| `go_back()` stack pop pattern | Added `_transitioning` guard before pop | Race condition: pressing back during fade-out consumed a stack entry without navigating; fix ensures pop only happens when navigation will succeed |

**Performance note (Stage 8.5 H.5):** `delta_baseline()` was added to `snapshot_serializer.py` during the interpolation buffer work. Both `pipe_transport.py` and `socket_server.py` now use `delta_baseline(engine)` instead of `full_snapshot(engine)` for the per-tick prev_state cache. This eliminates a 60ms/tick fog-of-war recomputation that was throttling the sim to ~11Hz at 200v200. The full snapshot is still sent to the client on the 5-second interval — only the internal delta-comparison cache was changed.

**To resume:** Wait for Stage 8 sign-off. Make the two targeted changes to `tactical.gd` and `input_router.gd` listed above. Run Checkpoint F prove-it item 5 (units appear, issue move command, verify units respond via stdio). Mark Stage 10 done.
