# Stage 12 — Loop Edges: Onboarding, Mission Debrief, Save Serialization, Bug Report Capture

## Goal

Close every open end of the game loop so the friends-ZIP build is a complete, playable, resumable experience with built-in tooling for testers to report bugs reproducibly. Four pillars: (1) onboarding screen with archetype descriptions; (2) mission debrief with 3D performance visualization and simulation impact preview; (3) autosave serialization at three loop boundaries plus mid-mission quit-and-resume; (4) a bug-report capture system that snapshots tactical state, command history, and mission metrics into a ZIP the tester pastes into Discord.

## Bible References

Read the hub (`game_bible.md`) plus these spokes:

- `docs/bible_history/bible_2_00_missions.md` → "Outcome Band Classification System" (two-component scoring, per-archetype thresholds), "Mission Outcome Resolver" (proportional lookup table, field deltas, mission-region-only scope). The debrief screen displays these.
- `docs/bible_history/bible_2_00_chronicle.md` → "Chronicle Template Authoring Framework" § consequence categories (`consequence_success`, `consequence_failure`, `consequence_mixed`, `consequence_ripple`), fragment structure, variable slot vocabulary. The debrief's simulation impact preview templates follow the same authoring contract.
- `docs/bible_history/bible_2_00_simulation.md` → "What the Simulation Provides to Missions" (sim stops during missions, digests outcome as consequence bundle), "Character Selector Data Contract" (the generational loop position diagram — debrief sits between mission and time jump).
- `docs/bible_history/bible_2_00_world.md` → "Seamless Transition — No Loading Screens" (the six-phase flow, chapter-boundary exit points, Exit transition treatment). The debrief inserts between phase 1 and phase 2.
- `game_bible.md` hub → "Onboarding and First Chapter" (single screen, difficulty + rare marks, opening time jump), "The Cycle" step 4 (mission resolution, outcome spectrum, commander fate).

Do not read `docs/bible_history/bible_2_00_antagonist.md`, `bible_monetization.md` (deleted 2026-05-31; see docs/bible_history/), `docs/bible_history/bible_2_00_ai_pipeline.md`, `animation_strategy.md`, or `docs/bible_history/bible_2_00_combat.md` — not relevant to Stage 12. Stage 8 spec is consulted for persistence API shapes. Stage 9 spec is consulted for UIDataBus contract and scene routing. Stage 10 spec is consulted for sim process lifecycle and crash log infrastructure. Stage 11 spec is consulted for the seamless transition sequencer API.

## Context

### What exists

- **Stages 1–5** — simulation backbone, chronicle distiller, coherence ledger, naming system. All complete and stable.
- **Stage 5.5** — mission generator produces `MissionSetup` records from simulation state.
- **Stage 6** — headless tactical engine with deterministic tick loop, outcome band classification, and force retention scoring.
- **Stage 7 / 7.5** — map generation pipeline and enemy macro behavior scripts.
- **Stage 8** — Godot renderer, WebSocket bridge, command interface, persistence layer. Key Stage 8 outputs this stage depends on:
  - `save_writer.py` / `save_loader.py` — writes and reads `sim.json`, `tactical.json`, `onboarding.json` per slot.
  - `TacticalEngine.export_full_state()` / `restore_from_state()` — mid-mission state round-trip.
  - `snapshot_serializer.py` — `full_snapshot(engine) → dict`.
  - `onboarding_store.py` — read/write onboarding preferences.
  - `scenes/onboarding/onboarding.tscn` — the existing onboarding screen (difficulty + rare marks, no descriptions).
  - `scenes/tactical/tactical.tscn` — the tactical scene with `mission_ended` signal.
- **Stage 9** — UI shell with `UIDataBus` singleton, `SceneRouter`, `InputSanitizer`, save-slot browser (mock data), settings screen.
- **Stage 10** — live sim data over stdio pipe transport, crash log infrastructure (`logs/crash_report.txt`), error screen.
- **Stage 11** — galaxy view, chronicle scroll, seamless transition sequencer. The sequencer orchestrates: `mission_ended` → pull-back → galaxy → narration → post-narration pause (Proceed/Exit) → push-in → next mission.

### What Stage 12 adds

Stage 12 inserts three new scenes into the existing loop and adds a cross-cutting bug-report system:

1. **Onboarding enhancement** — adds archetype descriptions and expand/collapse accordion to the Stage 8 onboarding screen.
2. **Mission debrief scene** — new scene inserted between `mission_ended` and the pull-back. Displays outcome band, objectives, force retention, 3D ribbon performance graphs, and a simulation impact preview.
3. **Autosave wiring** — connects Stage 8's `save_writer` to three loop boundaries (post-debrief, post-narration, mid-mission quit) with the resolved open-ended / single-slot / no-rewind semantics.
4. **Bug-report capture system** — rolling 5-second tactical state buffer, command log, F12 hotkey + pause menu trigger, ZIP bundler, clipboard + Discord delivery flow.

### Session-length decision (RESOLVED)

Open-ended run. Single autosave slot. No rewind, no manual save slots, no fork-from-here, no chronicle erase-on-rewind (no rewind exists). Restart is a hard reset that wipes the save. This was resolved in a prior chat session and confirmed at Stage 12 spec start.

### Generational loop position

```
onboarding → opening time jump → [loop start] →
  recon → mission → DEBRIEF [new] → AUTOSAVE [new] →
  pull-back → galaxy narration → post-narration AUTOSAVE [new] →
  Proceed/Exit pause → push-in → recon → ...
```

The debrief inserts between the tactical scene's `mission_ended` signal and the Stage 11 sequencer's pull-back phase. The sequencer's entry point shifts from `mission_ended` to `debrief_completed`.

## What to Build

### New files — Godot

```
scenes/debrief/
├── debrief.tscn                        - Full-screen debrief scene.
├── debrief.gd                          - Outcome display, graph orchestration, impact preview, Continue/Exit.
├── ribbon_graph.tscn                   - 3D ribbon visualization subscene.
├── ribbon_graph.gd                     - Builds ribbon meshes from metric arrays, camera orbit, flash particles.
└── impact_preview.gd                   - Templated prose from outcome resolver field deltas.

scenes/bug_report/
├── bug_report_popup.tscn               - Post-capture popup: "Paste into Discord", path fallback, dismiss.
├── bug_report_popup.gd
└── bug_report_settings_entry.tscn      - Settings screen subsection showing log path for old reports.

autoload/
├── bug_report_manager.gd              - Rolling buffer, command log, F12 handler, ZIP bundler, clipboard.
└── mission_metrics_recorder.gd        - Per-second sampling of tactical state for debrief graphs.

tests/
├── test_bug_report_manager.gd
└── test_mission_metrics_recorder.gd
```

### New files — Python

```
sim/
├── bug_report_bundler.py               - Assembles the report ZIP from snapshots, commands, metrics, metadata.
├── report_loader.py                    - CLI tool: ingests a report ZIP, reconstructs engine state, optional command replay.
├── impact_preview_templates.py         - Templated prose for simulation impact preview (field delta → sentences).
└── debrief_data.py                     - Assembles debrief payload: outcome band, objective breakdown, retention, deltas.

tests/
├── test_bug_report_bundler.py
├── test_report_loader.py
├── test_impact_preview_templates.py
└── test_debrief_data.py
```

### Modified files — Godot

**`scenes/onboarding/onboarding.gd`** — additive only. Add one-line description labels beneath each archetype name. Add expand chevron per row with 2–3 sentence elaboration panel. Single-expand accordion behavior (expanding one collapses the previous). Add guidance text at top: "You can mark up to 2 mission types as rare. If you're not sure, leave them all unmarked — you'll experience every type." No changes to difficulty selector or confirm button logic.

**`scenes/tactical/tactical.gd`** — additive. On `mission_ended`, emit debrief data to `UIDataBus` before the sequencer receives the signal. Stage 11's sequencer listens for `debrief_completed` instead of `mission_ended` as its pull-back trigger.

**`autoload/ui_data_bus.gd`** — additive. New methods:
- `get_debrief_data() → Dictionary` — returns outcome band, objective breakdown, force retention, field deltas, mission metrics arrays.
- `get_bug_report_path() → String` — returns the log files directory path for the settings screen.
- `trigger_autosave() → void` — writes sim state via the persistence API.
- `get_mission_metrics() → Dictionary` — returns the per-second metric arrays from the current mission.

**`scenes/settings/settings.gd`** — additive. Add "Bug Reports" subsection showing the log files path for finding old reports.

**`autoload/tactical_bridge.gd`** — additive. Expose the command stream to `bug_report_manager.gd` via a signal (`command_sent(command: Dictionary)`).

**`scenes/tactical/hud.gd`** — additive. Two additions: (1) A **persistent "F12 — Report Bug" label** in the bottom-left corner of the tactical HUD, rendered in small font at low opacity. The label fades to near-invisible (opacity ~0.15) after 30 seconds of unpaused gameplay, but remains if the player looks for it. On F12 press, the label briefly flashes full opacity as confirmation. The label is visible during active play, during recon, and on the debrief screen — anywhere the bug report system is active. (2) A "Report Bug" button in the pause menu panel. Both trigger `BugReportManager.capture()`.

**`scenes/world/time_jump_sequencer.gd`** — modification. Change the pull-back trigger from `mission_ended` to `debrief_completed`. Add autosave call at post-narration (before Proceed/Exit pause becomes interactive).

### Modified files — Python

**`config.py`** — new constants:

```python
# Debrief
METRICS_SAMPLE_INTERVAL_SEC = 1.0       # Per-second sampling for debrief graphs
IMPACT_PREVIEW_MAX_SENTENCES = 3        # Simulation impact preview length

# Bug report
BUG_REPORT_BUFFER_SECONDS = 5           # Rolling ring buffer duration
BUG_REPORT_BUFFER_CADENCE_SEC = 1.0     # One snapshot per second in the buffer
BUG_REPORT_COMMAND_BUFFER_SECONDS = 5   # Command log retention window
BUG_REPORT_OUTPUT_DIR = "logs/reports"   # Secondary save location (also goes to Downloads)
DISCORD_BUG_CHANNEL_URL = ""            # Set before ZIP build; empty = hide Discord button

# Autosave
AUTOSAVE_SLOT_ID = "autosave"           # Single slot, overwritten each time
```

**`save_writer.py`** — no logic changes. Called by the Godot autosave wiring at the three boundary points. The existing `write_sim_state(slot_id, sim_state)` and `write_tactical_state(slot_id, tactical_state)` are sufficient.

**`save_loader.py`** — additive. Add `has_tactical_state(slot_id) → bool` convenience method for the load-routing logic (checks if `tactical.json` exists for the slot).

## Input/Output Shapes

### Debrief payload (Python → Godot via UIDataBus)

```json
{
  "outcome_band": "strong_success",
  "outcome_band_prose": "A hard-fought defense that held the line.",
  "final_score": 0.78,
  "objective_score": 0.82,
  "force_retention": 0.68,
  "objectives": [
    {"id": "hold_zone_alpha", "type": "hold_zone", "weight": 0.6, "completion": 0.95, "label": "Hold the northern approach"},
    {"id": "eliminate_force", "type": "eliminate_force", "weight": 0.4, "completion": 0.62, "label": "Destroy the assault force"}
  ],
  "field_deltas": {
    "military": {"raw": 6.4, "direction": "up", "magnitude": "moderate", "prose": "Military position strengthened"},
    "tension": {"raw": -4.2, "direction": "down", "magnitude": "small", "prose": "Regional tensions eased"},
    "economy": {"raw": -3.8, "direction": "down", "magnitude": "small", "prose": "Minor economic disruption"},
    "population": {"raw": 0.0, "direction": "stable", "magnitude": "none", "prose": "Population unaffected"}
  },
  "impact_preview": "Your defense stabilized the region's military position. The eased tensions may discourage further aggression along this border — but the economic disruption could attract opportunists if the region doesn't recover quickly.",
  "commander_fate": "survived",
  "mission_duration_ticks": 36000,
  "mission_duration_seconds": 1800
}
```

### Mission metrics arrays (sampled per second during mission)

```json
{
  "sample_interval_sec": 1.0,
  "samples": [
    {
      "tick": 0,
      "elapsed_sec": 0.0,
      "player_force_hp": 24000,
      "enemy_force_hp": 22000,
      "player_unit_count": 42,
      "enemy_unit_count": 38,
      "player_unit_counts_by_category": {"strike": 14, "line": 18, "siege": 10},
      "enemy_unit_counts_by_category": {"strike": 12, "line": 16, "siege": 10},
      "objective_progress": {"hold_zone_alpha": 0.0, "eliminate_force": 0.0},
      "structures_player": 2,
      "structures_enemy": 3,
      "structures_neutral": 1
    }
  ]
}
```

These arrays are held in memory by `MissionMetricsRecorder` during the mission. Not persisted to the autosave (presentation data, not game state). Included in the bug-report ZIP.

### Bug report ZIP contents

```
bug_report_20260416_143022.zip
├── metadata.json              - OS, game version, chapter, current phase, timestamp, RNG seed, Discord note
├── sim_state.json             - Current simulation state (same format as autosave sim.json)
├── tactical_snapshots/        - Ring buffer contents (if mid-mission)
│   ├── snapshot_tick_35940.json
│   ├── snapshot_tick_35960.json
│   ├── snapshot_tick_35980.json
│   ├── snapshot_tick_36000.json
│   └── snapshot_tick_36020.json
├── command_log.json           - All player commands from the 5-second window, tick-stamped
├── mission_metrics.json       - Full per-second metric arrays for debrief graphs
├── onboarding.json            - Difficulty + rare marks
├── screenshot.png             - Frame capture at the instant F12 was pressed
└── crash_log.txt              - Copy of logs/crash_report.txt if it exists (may be empty)
```

### Bug report metadata

```json
{
  "schema_version": 1,
  "game_version": "0.12.0",
  "os": "Windows 10",
  "os_version": "10.0.19045",
  "python_version": "3.11.5",
  "timestamp": "2026-04-16T14:30:22Z",
  "chapter_number": 4,
  "current_phase": "tactical_mission",
  "mission_archetype": "defensive_stand",
  "mission_tick": 36020,
  "rng_seed": "0x8a3f...",
  "buffer_snapshots_count": 5,
  "command_log_entries": 23,
  "note": "Paste this file into Discord for Westley."
}
```

### Report loader CLI

```bash
# List snapshots in a report
python report_loader.py info bug_report_20260416_143022.zip

# Load a specific snapshot and start the engine from that tick
python report_loader.py load bug_report_20260416_143022.zip --snapshot 35960

# Load and replay the command log from a snapshot (watch the bug unfold)
python report_loader.py replay bug_report_20260416_143022.zip --snapshot 35960

# Load into a live server (connect Godot client to see it rendered)
python report_loader.py serve bug_report_20260416_143022.zip --snapshot 35960 --port 8765
```

### Autosave file layout (single slot, overwritten)

```
user://saves/autosave/
├── sim.json                   - Overwritten at post-debrief and post-narration boundaries
├── tactical.json              - Exists only while a mission is paused (mid-mission quit); consumed on resume
└── onboarding.json            - Written once at game start; overwritten only on new cycle (Exodus/Extinction)
```

### Impact preview templates

The `impact_preview_templates.py` module maps field delta direction and magnitude to prose fragments, then assembles 2–3 sentences. This is not the chronicle voice — it reads like a staff officer's assessment.

```python
FIELD_TEMPLATES = {
    "military": {
        ("up", "large"):    "Your victory significantly bolstered the region's military capabilities.",
        ("up", "moderate"): "Your defense stabilized the region's military position.",
        ("up", "small"):    "The region's military recovered slightly.",
        ("down", "large"):  "The region's military was devastated by the engagement.",
        ("down", "moderate"): "Military strength in the region took a notable hit.",
        ("down", "small"):  "Minor military losses were sustained.",
        ("stable", "none"): None,  # Omit from preview
    },
    # ... tension, economy, population follow the same pattern
}

FORWARD_LOOK_TEMPLATES = {
    # Keyed by (dominant_delta_field, dominant_direction, secondary_condition)
    ("military", "up", "tension_down"):
        "This may discourage further aggression along this border.",
    ("military", "up", "economy_down"):
        "But the economic disruption could attract opportunists if the region doesn't recover quickly.",
    ("military", "down", "tension_up"):
        "The weakened garrison and rising unrest could invite further attacks — or internal fractures.",
    ("economy", "down", "military_stable"):
        "The economic damage may compound over time if the region's trade routes aren't restored.",
    # ... ~20 forward-look templates total, covering common delta combinations
}
```

Magnitude thresholds (what counts as "large" vs "moderate" vs "small") are config values derived from the archetype's consequence table ranges. A +15% military delta is "large" for Defensive Stand because that's its total-success value; the same +15% might be "moderate" for Multi-Front Defense where total success yields +10%.

## Integration Points

- **Stage 11 sequencer.** The debrief inserts before the pull-back. `time_jump_sequencer.gd` changes its trigger from `mission_ended` to `debrief_completed`. The debrief scene emits `debrief_completed` when the player presses Continue. The sequencer's pull-back phase begins from there. This is the only modification to a Stage 11 file.
- **Stage 8 persistence.** The autosave wiring calls the existing `save_writer.write_sim_state()` and `save_writer.write_tactical_state()` at the three boundary points. No changes to the writer or loader logic — only new call sites.
- **Stage 10 crash log.** The bug-report ZIP copies `logs/crash_report.txt` if it exists. No changes to Stage 10's crash handler.
- **Stage 9 UIDataBus.** New methods added (see Modified Files above). Existing methods unchanged.
- **Stage 9 settings screen.** One new subsection added for bug report log path.
- **Stage 9 scene router.** New scene registered: `debrief`. Existing scenes unchanged.
- **Kill switches.**
  - `ENABLE_STAGE12_DEBRIEF = true` — if false, `mission_ended` goes directly to the sequencer's pull-back (Stage 11 behavior). Default ON.
  - `ENABLE_STAGE12_AUTOSAVE = true` — if false, game runs in memory like Stage 11. Default ON.
  - `ENABLE_STAGE12_BUG_REPORT = true` — if false, F12 does nothing, pause menu entry hidden. Default ON.

## Implementation Checkpoints

### Checkpoint A — Onboarding Enhancement

**Build:** Modify `scenes/onboarding/onboarding.gd` to add one-line descriptions beneath each archetype name, an expand chevron per row, a 2–3 sentence elaboration panel per archetype, single-expand accordion behavior, and guidance text at top.

**Archetype descriptions (one-line):**

| Archetype | One-liner |
|-----------|-----------|
| Defensive Stand | Hold your position against an incoming assault. |
| Siege Breaking | Break an enemy stranglehold on a besieged region. |
| Reconquest | Retake a recently conquered region before the occupier digs in. |
| Assault | Lead an offensive to conquer enemy territory. |
| Suppression | Crush a newly formed breakaway faction before it consolidates. |
| Multi-Front Defense | Survive simultaneous attacks from multiple directions. |
| Interception | Intercept an enemy force in the field before it reaches its target. |
| Evacuation | Save what you can from a region that's already lost. |
| Containment | Draw a line and hold it against an expanding hostile faction. |
| Counterinsurgency | Hunt down insurgent forces in your own territory without destroying it. |

**Expanded descriptions** (2–3 sentences each) cover the tactical feel, expected unit composition, and map character. Written once, stored as static strings in the onboarding script.

**Test:** Click through onboarding with adversarial inputs — verify all 10 descriptions render, accordion collapses correctly, expand chevrons animate, guidance text is visible, and all Stage 8 Checkpoint J invariants still hold (rare-mark validation, payload shape, opening time jump, distiller output).

**Print:** Screenshot of onboarding screen with one archetype expanded. Payload as written to disk.

**Verify:** Descriptions readable at default resolution. Accordion behavior correct (only one expanded at a time). Guidance text visible. Stage 8 onboarding invariants unchanged.

⛔ STOP.

### Checkpoint B — Mission Metrics Recorder

**Build:** `autoload/mission_metrics_recorder.gd`. Samples tactical engine state every `METRICS_SAMPLE_INTERVAL_SEC` (1.0s) during active missions. Records: player/enemy force HP, unit counts (total and by category), objective progress per objective, structure ownership counts. Stores arrays in memory. Exposes `get_metrics() → Dictionary` matching the mission metrics shape above. Starts recording on mission start, stops on `mission_ended`, holds data until the debrief scene reads it.

**Test:** Run a scripted 120-second mission against a Stage 7 generated map. Verify the recorder produces 120 samples (±1). Verify sample values match engine state at each sample tick (spot-check 5 random samples against engine queries).

**Print:** Sample count, first/last sample, min/max/mean of player_force_hp across samples, memory footprint of the metrics arrays.

**Verify:** Sample count matches mission duration. Spot-checked values are exact. Memory footprint under 500KB for a 30-minute mission (~1800 samples).

⛔ STOP.

### Checkpoint C — Debrief Data Assembly (Python)

**Build:** `sim/debrief_data.py`. Consumes the outcome band classification output (from Stage 6's `objectives.py`), the mission region's current sim state, and the archetype's consequence table. Produces the debrief payload matching the Input/Output Shape above. `sim/impact_preview_templates.py` assembles the 2–3 sentence impact preview from field delta directions and magnitudes.

**Test:** `test_debrief_data.py` — feed 5 different outcome bands across 3 archetypes (Defensive Stand, Assault, Evacuation). Verify: outcome_band_prose matches the archetype's band label, field_deltas match the consequence table, impact_preview is 2–3 grammatical sentences using the correct templates, commander_fate is correctly derived.

**Print:** For each test case: archetype, outcome band, field deltas, impact preview text.

**Verify:** All 15 combinations produce valid payloads. Impact preview never exceeds 3 sentences. No template produces empty or None text for non-zero deltas. Stable fields correctly omitted from preview.

⛔ STOP.

### Checkpoint D — Debrief Scene (Outcome + Objectives + Retention + Impact Preview)

**Build:** `scenes/debrief/debrief.tscn` and `debrief.gd`. Full-screen scene displaying: outcome band (prose phrase prominently, numeric score smaller), objective breakdown (per-objective completion bars with labels and weights), force retention ratio (percentage + visual), and impact preview text (2–3 sentences). Two buttons: "Continue" (emits `debrief_completed`) and "Exit to Main Menu" (fade to black, load main menu per `docs/bible_history/bible_2_00_world.md` Exit transition treatment). Style follows Stage 9's "Terminal Meets Glass" aesthetic.

**No ribbon graphs yet** — those land in Checkpoint E. This checkpoint proves the data flows from engine → Python debrief assembly → UIDataBus → Godot debrief scene.

**Test:** Complete a mission, verify debrief scene appears with correct data. Test all 5 outcome bands (use debug overrides to force each band). Verify Continue triggers the pull-back. Verify Exit fades to black and loads main menu.

**Print:** Screenshot of debrief screen for each outcome band. Transition timing from Continue to pull-back start.

**Verify:** Data matches engine output. All 5 bands display correctly. Continue → pull-back seamless. Exit → black → main menu clean.

⛔ STOP.

### Checkpoint E — Ribbon Performance Graphs (3D Visualization)

**Build:** `scenes/debrief/ribbon_graph.tscn` and `ribbon_graph.gd`. A 3D subscene embedded in the debrief screen. Consumes the mission metrics arrays from Checkpoint B. Renders each tracked metric as a luminous ribbon suspended in 3D space — the X axis is mission time, the Y axis is metric value, ribbons are offset in Z to avoid overlap. Player faction ribbons in brand gold (`#c9a84c`), enemy faction ribbons in their faction color. Key battle moments (engagements, structure captures, objective completions) marked with flash particles reusing the galaxy view's particle system. Camera slowly orbits (reusing galaxy camera infrastructure from `scenes/shared/galaxy/galaxy_structure.tscn`).

**Ribbon meshes** are built from the metric arrays using Godot's `ImmediateMesh` or `SurfaceTool` — one quad strip per metric, extruded along the time axis with height driven by the metric value. Ribbons glow using an emissive material with bloom.

**Metrics graphed (4 ribbons):**
1. Player total force HP (gold) vs Enemy total force HP (faction color)
2. Player structure control count (gold) vs Enemy structure control count (faction color)

Two ribbon pairs, each showing the player/enemy contrast over time. Objective progress is shown as markers on the time axis rather than a separate ribbon (progress is 0–1 while HP is 0–30000+; they don't share a Y scale).

**Test:** Run a scripted mission with known battle events (two engagements at known ticks, one structure capture). Verify ribbons render with correct shapes — HP ribbons dip at engagement moments, structure ribbon steps at capture. Verify flash particles appear at the correct time positions. Verify camera orbit is smooth.

**Print:** Screenshot of ribbon graph from three camera angles. Frame time during orbit (p50, p95).

**Verify:** Ribbon shapes match the metric data. Flash particles at correct positions. Camera orbit holds 60fps. Ribbons visually distinguishable (gold vs faction color, adequate Z separation).

**Future enhancement note:** The holographic briefing table visualization (Option C from design brainstorming) is a candidate for the commercial release. It reframes the same data as a translucent tactical display with unit silhouette markers, fitting the "commander reviewing a battle" fantasy. Its main advantage over ribbons is that the visualization format (surface plot + markers) is era-agnostic while the visual dressing (holographic translucency vs parchment vs CRT) becomes the era-specific skin — solving the Sacred Principle #3 concern naturally. Not in Stage 12 scope; noted here so a future stage knows the design intent exists.

⛔ STOP.

### Checkpoint F — Bug Report Rolling Buffer + Command Log

**Build:** `autoload/bug_report_manager.gd`. During active missions, maintains:
1. A **ring buffer** of 5 tactical state snapshots, one captured per second, using `TacticalEngine.export_full_state()` via the bridge. The oldest snapshot is evicted when a new one arrives. Buffer only runs during missions (between missions, the sim boundary state is sufficient).
2. A **command log** that records every command packet the player sends (received via `TacticalBridge.command_sent` signal), timestamped by engine tick. Log is also a rolling buffer trimmed to the same 5-second window.

Both buffers are in-memory only. They are consumed when a bug report is triggered and are not persisted to the autosave.

**Test:** Run a 30-second mission, issue 15+ commands. At tick 600 (second 30), read the buffer. Verify: exactly 5 snapshots in the ring buffer covering ticks ~580–600 (±1 tick). Command log contains only commands from the same 5-second window. Older commands and snapshots have been evicted.

**Print:** Buffer snapshot tick numbers, command log tick range, memory footprint of the buffer.

**Verify:** Ring buffer is exactly 5 entries. Command log entries all fall within the 5-second window. Memory footprint under 1MB for a 200v200 engagement.

⛔ STOP.

### Checkpoint G — Bug Report ZIP Bundler + Delivery

**Build:** `sim/bug_report_bundler.py` (Python side — assembles ZIP contents) and the Godot-side delivery flow in `bug_report_manager.gd`:

1. On F12 press (or pause menu "Report Bug" click):
   - Capture a screenshot of the current frame.
   - Freeze the ring buffer and command log contents.
   - Collect: sim state (current `sim.json`), ring buffer snapshots, command log, mission metrics arrays, onboarding prefs, crash log (if exists), metadata (OS, game version, chapter, phase, tick, RNG seed).
   - Bundle into a ZIP via `bug_report_bundler.py`.
   - Save ZIP to **two locations**: OS Downloads folder (`~/Downloads/` or platform equivalent) and `logs/reports/` in the game directory.
   - **Copy the ZIP file to the system clipboard** (Windows: `CF_HDROP` file copy via `ctypes` so Ctrl+V pastes the file into Discord; Mac/Linux: copy the file path string to clipboard).
   - Show `bug_report_popup.tscn`: "Bug report captured! Paste into Discord with Ctrl+V." Below in small text: "Also saved to: [logs/reports/filename.zip]". Dismiss button.

2. Settings screen integration: `bug_report_settings_entry.tscn` shows the `logs/reports/` path in the settings screen under a "Bug Reports" heading.

**Test:**
1. Mid-mission: press F12. Verify ZIP appears in Downloads and `logs/reports/`. Verify clipboard contains the file (Windows: open Discord, Ctrl+V — file attaches. Other platforms: Ctrl+V pastes the path).
2. Verify ZIP contents match the schema: metadata.json, sim_state.json, tactical_snapshots/ with 5 files, command_log.json, mission_metrics.json, onboarding.json, screenshot.png, crash_log.txt.
3. Between missions (on the debrief screen): press F12. Verify ZIP contains sim state but no tactical snapshots or command log (no mission in flight).
4. Verify popup appears and dismisses cleanly. Verify settings screen shows the reports path.
5. Verify the persistent "F12 — Report Bug" HUD label is visible at mission start, fades to near-invisible after 30 seconds of gameplay, and flashes full opacity briefly when F12 is pressed.

**Print:** ZIP file path (both locations), ZIP file size, clipboard contents description, popup screenshot.

**Verify:** ZIP in both locations. Clipboard works on Windows (file paste into Discord). ZIP contents match schema. Popup displays and dismisses. Settings entry visible.

⛔ STOP.

### Checkpoint H — Report Loader CLI

**Build:** `sim/report_loader.py`. A command-line tool for Westley's machine that ingests a bug-report ZIP and reconstructs the game state.

Four modes:
- `info` — prints metadata, lists snapshots with tick numbers, lists command count.
- `load` — loads a chosen snapshot into a `TacticalEngine` instance, prints the engine state summary (unit counts, objective progress, tick number).
- `replay` — loads a snapshot and replays the command log from that tick forward, printing tick-by-tick state changes. Stops at the end of the command log.
- `serve` — loads a snapshot, starts the WebSocket server (reusing Stage 8's `socket_server.py`), and optionally replays commands. Westley connects Godot to see the bug rendered visually.

**Test:** Generate a bug report from Checkpoint G. Run all four modes against it. Verify `info` prints correct metadata. Verify `load` produces an engine state matching the snapshot. Verify `replay` produces the same sequence of state changes the tester experienced. Verify `serve` allows a Godot client to connect and render the scene.

**Print:** Output of `info`, `load` (unit count + objectives), `replay` (first and last tick state), `serve` (connection established + first snapshot sent).

**Verify:** Round-trip fidelity — `load` state matches the snapshot exactly. `replay` produces deterministic output (same commands + same RNG state = same results). `serve` renders a scene that matches the screenshot in the ZIP.

⛔ STOP.

### Checkpoint I — Autosave Wiring

**Build:** Wire Stage 8's `save_writer` to three boundary points in the game loop:

1. **Post-debrief** — when the player presses Continue on the debrief screen, before `debrief_completed` signal fires: call `save_writer.write_sim_state(AUTOSAVE_SLOT_ID, sim_state)`. The sim state at this point includes mission consequences (the outcome resolver has already applied field deltas).
2. **Post-narration** — when the time jump finishes and the post-narration pause becomes interactive (before Proceed/Exit): call `save_writer.write_sim_state(AUTOSAVE_SLOT_ID, sim_state)`. The sim state at this point includes all time-jump effects.
3. **Mid-mission quit** — when the player chooses "Quit to Main Menu" from the pause menu during a mission: call `save_writer.write_tactical_state(AUTOSAVE_SLOT_ID, tactical_state)` (which also writes `sim_state`). This is the Stage 8 quit-and-resume mechanism wired into the real game loop.

**Load routing on game start:** When the player selects "Continue" from the main menu:
- Check `save_loader.has_tactical_state(AUTOSAVE_SLOT_ID)`.
- If true: load tactical state, connect to engine, resume mission at the saved tick.
- If false: load sim state, determine where in the loop the save was taken (post-debrief = pre-time-jump; post-narration = pre-push-in), and route to the appropriate point.

**Distinguishing post-debrief vs post-narration saves:** Add a `loop_phase` field to the sim state metadata: `"post_debrief"` or `"post_narration"`. The load router reads this field.

**Hard reset:** "New Game" from the main menu (or a future "Restart" option) calls `save_writer.delete_slot(AUTOSAVE_SLOT_ID)` and routes to onboarding. This is the "restart is a hard reset that wipes the save" semantic.

**Test:**
1. Play through: onboarding → mission → debrief → Continue. Verify `sim.json` exists with `loop_phase: "post_debrief"`. Quit. Relaunch. Continue. Verify game resumes into the pull-back/time-jump sequence.
2. Play through the time jump to post-narration pause. Verify `sim.json` overwritten with `loop_phase: "post_narration"`. Quit. Relaunch. Continue. Verify game resumes at the post-narration pause (Proceed/Exit).
3. Start a mission, play 60 seconds, quit via pause menu. Verify `tactical.json` exists. Relaunch. Continue. Verify game resumes mid-mission at the saved tick. Complete the mission. Verify `tactical.json` consumed (deleted).
4. From any state, choose New Game. Verify autosave slot wiped. Verify onboarding screen appears.

**Print:** File paths written at each boundary, file sizes, `loop_phase` values, resume routing decisions.

**Verify:** All three save points write correct files. Resume routing is correct for all three cases. Mid-mission resume is tick-identical to Stage 8's Checkpoint E invariant (I5). Hard reset wipes the slot completely.

⛔ STOP.

### Checkpoint J — End-to-End Loop Verification

**Build:** No new code. Integration test of the full loop with all Stage 12 systems active.

**Test:** Play a complete session:
1. New Game → onboarding (set difficulty, mark 1 archetype as rare, expand 2 archetypes to read descriptions) → opening time jump → first recon → first mission.
2. Mid-mission: press F12. Verify bug report ZIP generated.
3. Complete mission → debrief screen (verify outcome band, objectives, ribbon graphs, impact preview) → Continue.
4. Pull-back → galaxy narration → post-narration pause → Proceed.
5. Second recon → second mission → quit mid-mission via pause menu.
6. Relaunch → Continue → resume mid-mission → complete mission → debrief → Continue.
7. Pull-back → galaxy narration → post-narration → Exit to Main Menu.
8. Continue → resume at post-narration (verifying the last autosave).
9. New Game → verify onboarding (previous save wiped).

Also: run `report_loader.py replay` against the bug report from step 2. Verify it reconstructs the tester's mid-mission state.

**Print:** Session log: each state transition, each autosave write, each resume route, bug report ZIP path, report loader output.

**Verify:** Full loop completes without crashes. All autosave boundaries write and resume correctly. Bug report captures and replays correctly. Debrief data is accurate. Onboarding descriptions display correctly. Hard reset works.

⛔ STOP.

### Checkpoint K — Performance + Stability (Final)

**Build:** No new code. Performance tuning + bug fixes only.

**Test:** Three full sessions (different seeds). Each session: onboarding → 3+ chapters → multiple F12 captures → mid-mission quit/resume at least once. Measure:
- Debrief scene frame time (ribbon graph rendering).
- Bug report ZIP generation time (F12 to popup).
- Autosave write time at each boundary.
- Rolling buffer memory footprint during 200v200 engagements.
- Total disk usage after 5+ chapters of autosaves + bug reports.

**Print:** Perf table: debrief frame time p50/p95, ZIP generation time, autosave write time, buffer memory, disk usage.

**Verify:**
- Debrief ribbon graph holds 60fps (frame time p95 < 16ms).
- F12 → popup latency under 2 seconds (including screenshot capture and ZIP compression).
- Autosave write time under 500ms at each boundary.
- Rolling buffer memory under 2MB during 200v200.
- No memory growth across three sessions.

⛔ STOP.

## Invariants

- **I1 — Autosave round-trip.** `write_sim_state` at any boundary followed by `load_sim_state` produces an identical sim state (byte-identical after canonical JSON re-serialization).
- **I2 — Mid-mission resume fidelity.** Writing tactical state at tick N and restoring produces an engine that steps to tick N+K tick-identical to an unbroken run (inherits Stage 8 I5).
- **I3 — Bug report reproducibility.** Loading any ring-buffer snapshot from a bug report ZIP and replaying the associated command log produces the same engine state sequence the tester experienced (verified by comparing final-tick checksums).
- **I4 — Ring buffer bounds.** The ring buffer never exceeds `BUG_REPORT_BUFFER_SECONDS` snapshots. The command log never contains entries outside the buffer's tick window.
- **I5 — Debrief data accuracy.** The debrief payload's `outcome_band`, `objective_score`, and `force_retention` match the tactical engine's outcome band classification output exactly (no rounding, no approximation).
- **I6 — Impact preview grammar.** The impact preview is always 1–3 complete, grammatical English sentences. No template produces empty output for non-zero field deltas.
- **I7 — Autosave cadence.** Exactly 2 sim-state writes per complete chapter cycle (post-debrief + post-narration). Exactly 1 tactical-state write per mid-mission quit. No additional writes.
- **I8 — Clipboard delivery (Windows).** On Windows, the bug report ZIP is copyable from clipboard into a Discord message via Ctrl+V. Verified by paste test.
- **I9 — No rewind code.** `git grep` for rewind-related terms (rewind, fork_from, snapshot_history, timeline_branch) returns zero hits in Stage 12 implementation code. Inherits Stage 8 I10.
- **I10 — Kill switch isolation.** Each of the three kill switches (`ENABLE_STAGE12_DEBRIEF`, `ENABLE_STAGE12_AUTOSAVE`, `ENABLE_STAGE12_BUG_REPORT`) can be independently set to false without crashing the game or breaking the loop. The loop degrades gracefully to Stage 11 behavior when all three are off.

## Done Condition

- All 11 checkpoints (A–K) run, shown, approved by Westley.
- All 10 invariants (I1–I10) pass.
- A full session (onboarding → 3+ chapters → bug report capture → mid-mission quit/resume → hard reset) runs cleanly.
- `report_loader.py` successfully replays a bug report captured during the session.
- `tuning_output/stage12/` contains perf measurements from Checkpoint K.
- No Stage 11 files modified beyond `time_jump_sequencer.gd` (pull-back trigger change).
- No Stage 8 persistence logic modified — only new call sites.
- Settings screen shows bug report log path.

## Implementation Status

**Checkpoints A–I: COMPLETE.** Checkpoints J (end-to-end verification) and K (performance) are blocked on Stage 11 sequencer completion — the full loop playthrough requires the pull-back → galaxy → narration → post-narration flow that Stage 11 provides.

### Variations from spec

1. **`impact_preview.gd` not created as a separate file.** Impact preview logic lives in `debrief.gd` inline (it just displays the pre-assembled prose from the Python-side `impact_preview_templates.py`). No Godot-side computation needed — the debrief scene is a pure renderer as intended.

2. **Ribbon graph does not reuse galaxy camera infrastructure.** The galaxy scene (`scenes/shared/galaxy/galaxy_structure.tscn`) was not available or suitable for the SubViewport embedding. Ribbon graph has its own lightweight orbit camera and emissive materials. Visual polish (chart-style orientation, backface culling fix) deferred — the orbit + glow ribbons work but Westley wants to revisit the look later.

3. **No flash particles on ribbon graphs.** The spec called for "flash particles reusing the galaxy view's particle system" at key battle moments. Not implemented — the ribbon graph renders metric ribbons only. Markers for engagements/captures can be added in a future pass.

4. **Clipboard copies the actual file on macOS (not just the path).** Spec said "Mac/Linux: copy the file path string to clipboard." Implementation uses an AppleScript temp file executed via `osascript` to copy the file itself, so Cmd+V pastes the ZIP directly into Discord. Windows uses `Set-Clipboard -Path`. Linux falls back to path string.

5. **ZIP assembly happens on the Godot side, not Python side.** The spec listed `bug_report_bundler.py` as the primary assembler. In practice, all capture data (ring buffer, command log, screenshot, metrics) lives in Godot memory, so the ZIP is built using Godot's `ZIPPacker` in `bug_report_manager.gd`. The Python `bug_report_bundler.py` exists as a utility for `report_loader.py` and standalone use.

6. **`bug_report_settings_entry.tscn` not created.** The settings screen integration (showing the log path) was not built. `UIDataBus.get_bug_report_path()` exists and returns the globalized path — the settings UI entry can be added when the settings screen is next touched.

7. **Godot-side test files not created** (`test_bug_report_manager.gd`, `test_mission_metrics_recorder.gd`). Both systems were verified via manual testing with debug prints during development. Python-side `test_debrief_data.py` exists and passes (15/15 combinations).

8. **`report_loader.py serve` mode is a placeholder.** Prints state summary but does not start a WebSocket server. Full engine reconstruction from Godot-side snapshots requires mapping back to `TacticalEngine.restore_from_state()` format, which the Godot-side ring buffer doesn't capture. The `info`, `load`, and `replay` modes work against real bug report ZIPs.

9. **Autosave wiring is partial.** Post-debrief trigger wired (`debrief.gd` → `UIDataBus.trigger_autosave("post_debrief")`). Post-narration and mid-mission quit triggers require Stage 11's `time_jump_sequencer.gd` and pause menu, respectively. Integration points are clean — `UIDataBus.trigger_autosave(loop_phase)` sends the command via SimBridge.

10. **Kill switches defined in `config.py` but not wired as runtime guards.** The three `ENABLE_STAGE12_*` flags exist. Godot-side guard checks (skip debrief, skip autosave, disable F12) will be wired during Checkpoint J when the full loop is testable.

## Files Created

### Godot

| File | Purpose |
|------|---------|
| `scenes/debrief/debrief.tscn` | Debrief scene root (Control + script) |
| `scenes/debrief/debrief.gd` | Full debrief screen: outcome band, objectives, retention, impact preview, ribbon graph, Continue/Exit |
| `scenes/debrief/ribbon_graph.tscn` | 3D ribbon visualization subscene (Node3D + script) |
| `scenes/debrief/ribbon_graph.gd` | Builds ribbon meshes from metric arrays, orbit camera, emissive materials |
| `scenes/bug_report/bug_report_popup.tscn` | Post-capture popup (CanvasLayer + script) |
| `scenes/bug_report/bug_report_popup.gd` | "File copied to clipboard" popup with dismiss |
| `scenes/onboarding/onboarding.tscn` | Onboarding scene root (Control + script) |
| `scenes/onboarding/onboarding.gd` | Difficulty selection, archetype accordion with rare toggle, era filtering |
| `autoload/bug_report_manager.gd` | Ring buffer, command log, F12 capture, ZIP bundler, clipboard, popup |
| `autoload/mission_metrics_recorder.gd` | Per-second tactical state sampling during missions |

### Python

| File | Purpose |
|------|---------|
| `simulation/debrief_data.py` | Assembles debrief payload from mission result + consequence tables |
| `simulation/impact_preview_templates.py` | Field delta → prose templates, forward-look templates |
| `simulation/bug_report_bundler.py` | ZIP assembly utility (used by report_loader.py) |
| `simulation/report_loader.py` | CLI tool: info/load/replay/serve modes for bug report ZIPs |
| `simulation/test_debrief_data.py` | 15 test combinations (5 bands × 3 archetypes), all pass |

### Modified

| File | Change |
|------|--------|
| `autoload/scene_router.gd` | Added `"onboarding"` and `"debrief"` to SCENES dict |
| `autoload/tactical_bridge.gd` | Added `command_sent` signal, emitted from `send_command()` |
| `autoload/ui_data_bus.gd` | Added `get_mission_metrics()`, `get_bug_report_path()`, `trigger_autosave()` |
| `scenes/new_game/new_game.gd` | `_on_begin()` routes to `"onboarding"` instead of `"mission_briefing"` |
| `scenes/tactical/tactical.gd` | Added MissionMetricsRecorder + BugReportManager start/stop, F5 debug debrief |
| `scenes/tactical/input_router.gd` | Added `BugReportManager.log_command(cmd)` in `_send()` |
| `scenes/tactical/hud.gd` | Added persistent "F12 — Report Bug" label with 30s fade |
| `simulation/config.py` | Added Stage 12 constants, bug report config, autosave slot ID, kill switches |
| `simulation/save_loader.py` | Added `has_tactical_state()` convenience method |
| `project.godot` | Registered `MissionMetricsRecorder` and `BugReportManager` autoloads |

## Notes for the Implementing Session

- **Debrief is a presentation layer.** All debrief data is assembled on the Python side (`debrief_data.py`). The Godot scene is a pure renderer. If you find yourself computing outcome bands or field deltas in GDScript, stop — the computation belongs in Python and the result flows through UIDataBus.
- **Ribbon graph reuses galaxy infrastructure.** The orbital camera rig and particle system from `scenes/shared/galaxy/galaxy_structure.tscn` are the starting point. Don't build a new camera system. Don't build a new particle system. Instantiate what exists.
- **Bug report manager is an autoload.** It runs at all times during missions (to maintain the rolling buffer). It must have zero performance impact when not capturing — the ring buffer write is one `export_full_state()` call per second, which is the same operation the WebSocket snapshot system already performs.
- **Clipboard is platform-dependent.** The `CF_HDROP` file copy for Windows is the primary path (your testers are likely on Windows). Mac/Linux get path-string-to-clipboard as a fallback. Don't spend significant time on cross-platform clipboard parity — get Windows right.
- **The report loader is a developer tool, not a user-facing feature.** It does not need a GUI, polish, or error handling beyond basic "file not found" / "invalid ZIP" messages. It runs on your machine only.
- **Impact preview templates are hand-authored, not AI-generated.** There are ~20 forward-look templates covering common delta combinations. This is a small enough set to write by hand and validate by eye. Don't involve the library builder pipeline — it's overkill for this volume.
- **Autosave slot ID is hardcoded.** There is exactly one slot (`"autosave"`). The Stage 9 save-slot browser shows this one slot or "No saved campaigns" if it doesn't exist. No slot creation, no slot naming, no multi-slot management. This is the simplest possible persistence for the friends-ZIP.
