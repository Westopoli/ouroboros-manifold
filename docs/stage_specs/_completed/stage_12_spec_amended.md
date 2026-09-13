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
- **Stage 8.5** — `EraThemeResolver` autoload, per-era JSON manifests, 3D tactical rendering.
- **Stage 9** — UI shell with `UIDataBus` singleton, `SceneRouter`, `InputSanitizer`, save-slot browser (mock data), settings screen.
- **Stage 10** — live sim data over stdio pipe transport, crash log infrastructure (`logs/crash_report.txt`), error screen.
- **Stage 11** — world view (via `WorldViewShell` + component architecture from amendment), chronicle scroll, seamless transition sequencer. The sequencer orchestrates: `mission_ended` → pull-back → world view → narration → post-narration pause (Proceed/Exit) → push-in → next mission.

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
  pull-back → world view narration → post-narration AUTOSAVE [new] →
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

**`scenes/onboarding/onboarding.gd`** — additive only. Add one-line description labels beneath each archetype name. Add expand chevron per row with 2–3 sentence elaboration panel. Single-expand accordion behavior. Add guidance text at top.

**`scenes/tactical/tactical.gd`** — additive. On `mission_ended`, emit debrief data to `UIDataBus` before the sequencer receives the signal. Stage 11's sequencer listens for `debrief_completed` instead of `mission_ended` as its pull-back trigger.

**`autoload/ui_data_bus.gd`** — additive. New methods:
- `get_debrief_data() → Dictionary`
- `get_bug_report_path() → String`
- `trigger_autosave() → void`
- `get_mission_metrics() → Dictionary`

**`scenes/settings/settings.gd`** — additive. Add "Bug Reports" subsection showing log files path.

**`autoload/tactical_bridge.gd`** — additive. Expose command stream to `bug_report_manager.gd` via `command_sent(command: Dictionary)` signal.

**`scenes/tactical/hud.gd`** — additive. Persistent "F12 — Report Bug" label in bottom-left (fades to ~0.15 opacity after 30s, flashes on F12). "Report Bug" button in pause menu panel. Both trigger `BugReportManager.capture()`.

**`scenes/world/time_jump_sequencer.gd`** — modification. Change pull-back trigger from `mission_ended` to `debrief_completed`. Add autosave call at post-narration (before Proceed/Exit pause becomes interactive).

### Modified files — Python

**`config.py`** — new constants:

```python
# Debrief
METRICS_SAMPLE_INTERVAL_SEC = 1.0
IMPACT_PREVIEW_MAX_SENTENCES = 3

# Bug report
BUG_REPORT_BUFFER_SECONDS = 5
BUG_REPORT_BUFFER_CADENCE_SEC = 1.0
BUG_REPORT_COMMAND_BUFFER_SECONDS = 5
BUG_REPORT_OUTPUT_DIR = "logs/reports"
DISCORD_BUG_CHANNEL_URL = ""

# Autosave
AUTOSAVE_SLOT_ID = "autosave"
```

**`save_writer.py`** — no logic changes. Called at three boundary points.

**`save_loader.py`** — additive. Add `has_tactical_state(slot_id) → bool`.

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
      "tick": 0, "elapsed_sec": 0.0,
      "player_force_hp": 24000, "enemy_force_hp": 22000,
      "player_unit_count": 42, "enemy_unit_count": 38,
      "player_unit_counts_by_category": {"strike": 14, "line": 18, "siege": 10},
      "enemy_unit_counts_by_category": {"strike": 12, "line": 16, "siege": 10},
      "objective_progress": {"hold_zone_alpha": 0.0, "eliminate_force": 0.0},
      "structures_player": 2, "structures_enemy": 3, "structures_neutral": 1
    }
  ]
}
```

Held in memory by `MissionMetricsRecorder`. Not persisted to autosave. Included in bug-report ZIP.

### Bug report ZIP contents

```
bug_report_20260416_143022.zip
├── metadata.json
├── sim_state.json
├── tactical_snapshots/
│   ├── snapshot_tick_35940.json
│   ├── snapshot_tick_35960.json
│   ├── snapshot_tick_35980.json
│   ├── snapshot_tick_36000.json
│   └── snapshot_tick_36020.json
├── command_log.json
├── mission_metrics.json
├── onboarding.json
├── screenshot.png
└── crash_log.txt
```

### Bug report metadata

```json
{
  "schema_version": 1, "game_version": "0.12.0",
  "os": "Windows 10", "os_version": "10.0.19045", "python_version": "3.11.5",
  "timestamp": "2026-04-16T14:30:22Z",
  "chapter_number": 4, "current_phase": "tactical_mission",
  "mission_archetype": "defensive_stand", "mission_tick": 36020,
  "rng_seed": "0x8a3f...",
  "buffer_snapshots_count": 5, "command_log_entries": 23,
  "note": "Paste this file into Discord for Westley."
}
```

### Report loader CLI

```bash
python report_loader.py info bug_report_20260416_143022.zip
python report_loader.py load bug_report_20260416_143022.zip --snapshot 35960
python report_loader.py replay bug_report_20260416_143022.zip --snapshot 35960
python report_loader.py serve bug_report_20260416_143022.zip --snapshot 35960 --port 8765
```

### Autosave file layout (single slot, overwritten)

```
user://saves/autosave/
├── sim.json                   - Overwritten at post-debrief and post-narration boundaries
├── tactical.json              - Exists only while a mission is paused (mid-mission quit); consumed on resume
└── onboarding.json            - Written once at game start
```

### Impact preview templates

`impact_preview_templates.py` maps field delta direction and magnitude to prose fragments, assembles 2–3 sentences. Staff officer voice, not chronicle voice.

```python
FIELD_TEMPLATES = {
    "military": {
        ("up", "large"):    "Your victory significantly bolstered the region's military capabilities.",
        ("up", "moderate"): "Your defense stabilized the region's military position.",
        # ... etc
    },
}

FORWARD_LOOK_TEMPLATES = {
    ("military", "up", "tension_down"):
        "This may discourage further aggression along this border.",
    # ... ~20 forward-look templates total
}
```

Magnitude thresholds are config values derived from the archetype's consequence table ranges.

## Integration Points

- **Stage 11 sequencer.** The debrief inserts before the pull-back. `time_jump_sequencer.gd` changes its trigger from `mission_ended` to `debrief_completed`. This is the only modification to a Stage 11 file.
- **Stage 8 persistence.** Autosave calls existing `save_writer.write_sim_state()` and `save_writer.write_tactical_state()` at three boundaries. No writer/loader logic changes.
- **Stage 10 crash log.** Bug-report ZIP copies `logs/crash_report.txt` if it exists. No changes to Stage 10.
- **Stage 9 UIDataBus.** New methods added. Existing methods unchanged.
- **Stage 9 settings screen.** One new subsection for bug report log path.
- **Stage 9 scene router.** New scene registered: `debrief`. Existing scenes unchanged.
- **Kill switches:**
  - `ENABLE_STAGE12_DEBRIEF = true` — if false, `mission_ended` goes directly to sequencer's pull-back (Stage 11 behavior).
  - `ENABLE_STAGE12_AUTOSAVE = true` — if false, game runs in memory like Stage 11.
  - `ENABLE_STAGE12_BUG_REPORT = true` — if false, F12 does nothing, pause menu entry hidden.

## Implementation Checkpoints

### Checkpoint A — Onboarding Enhancement

**Build:** Modify `scenes/onboarding/onboarding.gd`. Add one-line descriptions, expand chevron, 2–3 sentence elaboration panel, single-expand accordion, guidance text.

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

**Test:** Adversarial inputs. Verify all 10 descriptions render, accordion collapses, Stage 8 invariants hold.

**Print:** Screenshot with one archetype expanded. Payload as written to disk.

**Verify:** Descriptions readable. Accordion correct. Stage 8 onboarding invariants unchanged.

⛔ STOP.

### Checkpoint B — Mission Metrics Recorder

**Build:** `autoload/mission_metrics_recorder.gd`. Samples every 1.0s during missions. Records player/enemy force HP, unit counts (total + by category), objective progress, structure ownership. Holds in memory.

**Test:** 120-second scripted mission. Verify ~120 samples. Spot-check 5 against engine state.

**Print:** Sample count, first/last sample, min/max/mean player_force_hp, memory footprint.

**Verify:** Count matches duration. Values exact. Memory < 500KB for 30-min mission.

⛔ STOP.

### Checkpoint C — Debrief Data Assembly (Python)

**Build:** `sim/debrief_data.py` and `sim/impact_preview_templates.py`.

**Test:** `test_debrief_data.py` — 5 outcome bands × 3 archetypes. Verify payload shape, field deltas, impact preview grammar.

**Print:** For each: archetype, band, deltas, preview text.

**Verify:** 15 valid payloads. Preview ≤ 3 sentences. No empty text for non-zero deltas.

⛔ STOP.

### Checkpoint D — Debrief Scene (Outcome + Objectives + Retention + Impact Preview)

**Build:** `scenes/debrief/debrief.tscn` and `debrief.gd`. Outcome band, objectives, retention, impact preview. Continue/Exit buttons. Terminal Meets Glass aesthetic.

**No ribbon graphs yet** — those are Checkpoint E.

**Test:** Complete a mission, verify debrief with correct data. Test all 5 bands. Verify Continue → pull-back. Verify Exit → black → main menu.

**Print:** Screenshot per band. Transition timing.

**Verify:** Data matches engine. All 5 bands display. Continue → pull-back seamless. Exit clean.

⛔ STOP.

### Checkpoint E — Ribbon Performance Graphs (3D Visualization)

**Build:** `scenes/debrief/ribbon_graph.tscn` and `ribbon_graph.gd`. 3D subscene in debrief. Ribbons from metric arrays: X = time, Y = value, Z offset. Player gold, enemy faction color. Flash particles at battle moments. Camera slowly orbits using the world view's `OrbitalCamera3D` component (`scenes/shared/world_view/cameras/orbital_camera_3d.tscn`).

**Metrics graphed (4 ribbons):**
1. Player total force HP (gold) vs Enemy total force HP (faction color)
2. Player structure count (gold) vs Enemy structure count (faction color)

Objective progress as markers on time axis.

**Test:** Scripted mission with known events. Verify ribbon shapes, flash positions, camera orbit.

**Print:** Screenshot from 3 angles. Frame time p50/p95.

**Verify:** Shapes match data. Flashes correct. 60fps orbit. Ribbons distinguishable.

**Future enhancement note:** The holographic briefing table visualization (Option C from design brainstorming) is a candidate for commercial release. It reframes the same data as a translucent tactical display — the format (surface plot + markers) is era-agnostic while visual dressing (holographic vs parchment vs CRT) becomes the era-specific skin, solving Sacred Principle #3 naturally. Not in Stage 12 scope; noted for future reference.

⛔ STOP.

### Checkpoint F — Bug Report Rolling Buffer + Command Log

**Build:** `autoload/bug_report_manager.gd`. Ring buffer of 5 tactical snapshots (1/sec). Command log (same 5-second window). In-memory only.

**Test:** 30-second mission, 15+ commands. At tick 600, verify exactly 5 snapshots covering ~580–600. Command log within window.

**Print:** Snapshot ticks, command log range, memory.

**Verify:** Ring buffer = 5. Commands in window. Memory < 1MB at 200v200.

⛔ STOP.

### Checkpoint G — Bug Report ZIP Bundler + Delivery

**Build:** `sim/bug_report_bundler.py` + Godot delivery in `bug_report_manager.gd`. F12 or pause menu → screenshot, freeze buffers, collect state, ZIP, save to Downloads + `logs/reports/`, clipboard copy, popup.

**Test:** Mid-mission F12 → ZIP in both locations, clipboard works (Windows Ctrl+V into Discord). Verify ZIP schema. Between-missions F12 → no tactical snapshots. HUD label visible/fading/flashing.

**Print:** ZIP paths, size, clipboard description, popup screenshot.

**Verify:** ZIP in both locations. Clipboard on Windows. Schema correct. Popup dismisses. Settings entry visible.

⛔ STOP.

### Checkpoint H — Report Loader CLI

**Build:** `sim/report_loader.py`. Four modes: `info`, `load`, `replay`, `serve`.

**Test:** All four modes against Checkpoint G's ZIP. Verify metadata, state reconstruction, deterministic replay, serve + Godot connect.

**Print:** Output of each mode.

**Verify:** Round-trip fidelity. Replay deterministic. Serve renders matching scene.

⛔ STOP.

### Checkpoint I — Autosave Wiring

**Build:** Wire `save_writer` to three boundaries:
1. **Post-debrief** — before `debrief_completed` fires.
2. **Post-narration** — before Proceed/Exit becomes interactive.
3. **Mid-mission quit** — pause menu quit writes tactical + sim state.

**Load routing:** Check `has_tactical_state()` → if true, resume mission; if false, read `loop_phase` field (`"post_debrief"` or `"post_narration"`) and route accordingly. Hard reset: `save_writer.delete_slot()` → onboarding.

**Test:** (1) Mission → debrief → Continue → verify `sim.json` with `loop_phase: "post_debrief"` → quit → relaunch → Continue → resumes into pull-back. (2) Through to post-narration → verify overwritten `sim.json` with `loop_phase: "post_narration"` → quit → relaunch → resumes at Proceed/Exit. (3) Mid-mission quit → verify `tactical.json` → relaunch → resume at saved tick → complete → verify `tactical.json` consumed. (4) New Game → verify slot wiped → onboarding.

**Print:** File paths, sizes, `loop_phase` values, routing decisions.

**Verify:** All three boundaries write correct files. Routing correct. Mid-mission tick-identical (inherits Stage 8 I5). Hard reset wipes.

⛔ STOP.

### Checkpoint J — End-to-End Loop Verification

**Build:** No new code. Integration test of full loop.

**Test:** Full session: New Game → onboarding → opening time jump → first mission → mid-mission F12 → complete → debrief → Continue → pull-back → narration → Proceed → second mission → quit mid-mission → relaunch → Continue → resume → complete → debrief → Continue → narration → Exit → Continue from save → New Game → verify wipe.

Also: `report_loader.py replay` against the F12 report.

**Print:** Session log of state transitions, saves, resumes, bug report path, loader output.

**Verify:** Full loop clean. All saves/resumes correct. Bug report captures/replays. Debrief accurate. Onboarding correct. Hard reset works.

⛔ STOP.

### Checkpoint K — Performance + Stability (Final)

**Build:** No new code. Performance tuning + bug fixes.

**Test:** Three full sessions (different seeds), 3+ chapters each, multiple F12s, mid-mission quit/resume. Measure: debrief frame time, ZIP generation time, autosave write time, buffer memory, disk usage.

**Print:** Perf table: debrief p50/p95, ZIP time, autosave time, buffer memory, disk usage.

**Verify:** Debrief ribbon 60fps (p95 < 16ms). F12 → popup < 2s. Autosave < 500ms. Buffer < 2MB at 200v200. No memory growth across sessions.

⛔ STOP.

## Invariants

- **I1 — Autosave round-trip.** `write_sim_state` → `load_sim_state` produces byte-identical state (canonical JSON).
- **I2 — Mid-mission resume fidelity.** Write at tick N, restore, step to N+K = tick-identical to unbroken run (inherits Stage 8 I5).
- **I3 — Bug report reproducibility.** Load snapshot + replay command log → same final-tick checksums.
- **I4 — Ring buffer bounds.** Never exceeds `BUG_REPORT_BUFFER_SECONDS` snapshots. Command log within window.
- **I5 — Debrief data accuracy.** Payload's `outcome_band`, `objective_score`, `force_retention` match engine output exactly.
- **I6 — Impact preview grammar.** Always 1–3 complete sentences. No empty output for non-zero deltas.
- **I7 — Autosave cadence.** Exactly 2 sim writes per chapter (post-debrief + post-narration). Exactly 1 tactical write per mid-mission quit.
- **I8 — Clipboard delivery (Windows).** ZIP copyable via Ctrl+V into Discord.
- **I9 — No rewind code.** `git grep` for rewind/fork terms returns zero in Stage 12 code.
- **I10 — Kill switch isolation.** Each of three switches independently false → no crash, graceful degradation to Stage 11 behavior.

## Done Condition

- All 11 checkpoints (A–K) approved.
- All 10 invariants pass.
- Full session (onboarding → 3+ chapters → bug report → mid-mission quit/resume → hard reset) runs cleanly.
- `report_loader.py` replays a captured report.
- `tuning_output/stage12/` contains Checkpoint K measurements.
- No Stage 11 files modified beyond `time_jump_sequencer.gd` (pull-back trigger change).
- No Stage 8 persistence logic modified — only new call sites.
- Settings screen shows bug report log path.

## Files Created

(Filled in after implementation.)

## Notes for the Implementing Session

- **Debrief is a presentation layer.** All debrief data is assembled in Python (`debrief_data.py`). The Godot scene is a pure renderer. If you find yourself computing outcome bands in GDScript, stop — it belongs in Python.
- **Ribbon graph reuses world view camera.** The orbital camera component at `scenes/shared/world_view/cameras/orbital_camera_3d.tscn` is the starting point for the ribbon graph's camera orbit. Don't build a new camera system.
- **Bug report manager is an autoload.** Runs at all times during missions. Zero perf impact when not capturing — the ring buffer write is one `export_full_state()` per second (same as the snapshot system).
- **Clipboard is platform-dependent.** `CF_HDROP` for Windows is primary. Mac/Linux get path-string-to-clipboard. Don't over-invest in cross-platform clipboard parity.
- **The report loader is a developer tool.** No GUI, no polish beyond basic error messages.
- **Impact preview templates are hand-authored.** ~20 total. Don't involve the library builder pipeline.
- **Autosave slot ID is hardcoded.** One slot (`"autosave"`). The Stage 9 save-slot browser shows this one slot or "No saved campaigns."
