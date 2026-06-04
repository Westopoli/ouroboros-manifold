# Simulation Visualizer — Spec v1.2

## Goal

Build a developer tool that loads a recorded simulation dump and plays it back as a 2D animation with playback controls, camera controls, and per-unit inspection. Proves out by loading a real 6K close-spawn dump and letting Westley visually diagnose what movement is doing during slow ticks.

## Bible References

None. This is a dev tool, not a game system. The bible governs game design; this governs debugging infrastructure. No bible spokes need to be read before implementing.

## Context

Stage 6 movement is being rebuilt in layers (seek-only → separation → neighbor cap → overlap resolution → alignment/cohesion → attack-move + group speed). Each layer needs visual verification that units behave correctly under real combat loads. Reading numeric logs does not catch steering oscillation, density collapse, or targeting gaps — watching the sim does. This tool exists to make every subsequent movement layer auditable.

The visualizer is file-driven: simulation writes a JSONL dump during test runs, the viewer loads the dump later. No live attachment. This decouples the viewer from the sim's runtime and lets it evolve independently.

## What to Build

Two components, in strict order:

1. **`simulation/sim_logger.py`** — a helper class that writes per-tick JSONL dumps. Opt-in via `--dump <path>` CLI flag added to test scripts. Zero overhead when disabled; bounded by I/O when enabled.

2. **`tools/sim_viewer.py`** — a pygame application that loads a JSONL dump and animates it. Includes playback controls, camera controls, inspector panel, and a set of toggleable overlays.

A third component (a scenario harness that runs reproducible sim scenarios from YAML) is explicitly deferred to a later spec. Do not build it.

### Scope: Logger

The logger is a passive observer. It reads from `engine.store` after each tick completes and writes one JSONL line per tick. It must not call any RNG, must not mutate any simulation state, and must not allocate inside any hot path in a way that affects `subsystem_ms` measurements. Its own cost is logged separately as `logger_ms` in the timing breakdown.

Hook the logger into these test scripts (verify each exists first; skip and report any that were deleted):

- `simulation/test_checkpoint_6k.py`
- `simulation/test_checkpoint_6k_close_spawn.py`
- `simulation/test_checkpoint_6k_small_field.py`
- `simulation/test_checkpoint_6c.py`
- `simulation/test_checkpoint_6d.py`
- `simulation/test_6j_gradient.py`

### Scope: Viewer

Single pygame window. Three regions stacked vertically: map view (main area), playback controls strip, inspector panel strip.

**Map view:** world-space rendering with auto-fit letterboxing. Units drawn as filled circles (radius = `UNIT_COLLISION_RADIUS`), colored by faction, with an HP ring. Selected unit highlighted. Death effect: brief 1-tick flash, then removal.

**Camera controls:** mouse drag to pan, scroll wheel to zoom toward cursor, `R` to reset, `F` to focus selected unit.

**Playback controls:** play/pause (spacebar), step forward/back (arrows), jump to start/end (Home/End), speed cycle (`+`/`-` through 0.25x → 16x), click/drag tick scrubber.

**Inspector panel:** when a unit is clicked, shows `uid`, `type`, `faction`, `layer`, position, velocity, speed, hp, target, ability state. Updates live as playback advances.

**Overlays (toggleable, all default off):**

- `V` — velocity vectors (line from unit center, length proportional to speed)
- `T` — target lines (thin line from unit to its target)
- `D` — density heatmap (100 wu cells, color by unit count)
- `H` — HP bars above units instead of HP ring
- `G` — spatial hash grid overlay
- `B` — faction bounding boxes

### Technology

Pygame. Single dependency, installs cleanly on macOS/Linux/Windows, fast enough for 400 circles at 60fps without optimization. Rejected alternatives: matplotlib (too slow for interactive playback), HTML+JS (adds build pipeline), Godot (ties dev tool to game runtime).

## Input/Output Shapes

**Dump file format:** JSONL. One JSON object per line. Line 0 is the header; lines 1+ are tick records.

**Header line (line 0):**
```json
{
  "type": "header",
  "version": 1,
  "scenario": "checkpoint_6k_close_spawn",
  "map": {
    "width": 12000,
    "height": 12000,
    "name": "open_field_large"
  },
  "factions": {
    "0": {"name": "A", "color": "#3b82f6"},
    "1": {"name": "B", "color": "#ef4444"}
  },
  "tick_duration_seconds": 0.05,
  "config": {
    "UNIT_COLLISION_RADIUS": 15,
    "STEERING_SEPARATION_RADIUS": 40,
    "HARD_COLLISION_ENABLED": true,
    "COLLISION_RESOLUTION_ITERATIONS": 3
  }
}
```

**Tick line (line 1 onward):**
```json
{
  "type": "tick",
  "tick": 0,
  "units": [
    {
      "uid": 1,
      "faction": 0,
      "type": "Vanguard",
      "x": 3000.0,
      "y": 6000.0,
      "vx": 0.0,
      "vy": 0.0,
      "hp": 200,
      "max_hp": 200,
      "target_uid": -1,
      "ability_state": 0,
      "layer": 0
    }
  ],
  "deaths_this_tick": [],
  "subsystem_ms": {
    "movement": 24.5,
    "targeting": 7.2,
    "abilities": 9.5,
    "damage": 0.5,
    "fog": 0.3,
    "commands": 0.0,
    "logger": 0.4
  }
}
```

**Field semantics:**

| Field | Type | Notes |
|---|---|---|
| `uid` | int | Stable across the run |
| `faction` | int | 0 or 1 |
| `type` | string | "Vanguard", "Warden", etc. |
| `x`, `y` | float | World coordinates in wu |
| `vx`, `vy` | float | Current velocity in wu/s |
| `hp` | int | Current hit points |
| `max_hp` | int | Maximum hit points |
| `target_uid` | int | -1 if no target |
| `ability_state` | int | 0=inactive, 1=windup, 2=active, 3=telegraph |
| `layer` | int | Movement layer (ground, air) |

**Forward compatibility rule.** Movement, targeting, and combat systems will evolve across Stage 6 closeout and beyond. New per-unit fields (e.g. steering force components, neighbor counts, group membership) may be added to the tick line without bumping the format version, as long as existing fields retain their names and semantics. The viewer must tolerate unknown fields gracefully — unknown keys are ignored, missing optional keys fall back to sensible defaults (`vx`/`vy` default to 0, `target_uid` defaults to -1, `ability_state` defaults to 0). The format version is only bumped when an existing field's meaning or type changes, or when a required field is removed.

## Integration Points

**Logger integration with test scripts** is additive. The `--dump <path>` flag is opt-in; test scripts without the flag run exactly as before with zero logger overhead. The logger lives in `simulation/sim_logger.py` as a single helper module. Test scripts import it and instantiate one per run. Kill switch: omit the flag.

**Viewer integration** is nil. It is a standalone tool in `tools/sim_viewer.py` that reads files written to disk. It does not import anything from `simulation/` and does not need to be runnable in any CI pipeline. Kill switch: don't run it.

**Config dependencies.** The logger reads movement constants from `config.py` to write the header `config` block. Any constant that may affect how the viewer renders (collision radius, map dimensions, etc.) is included in the header so the viewer can adapt without re-reading config. The viewer itself has no dependency on `config.py`.

## Implementation Order and Checkpoints

Each step below is a mandatory checkpoint per dev_rules.md. **After completing each step, CC must run the prove-it test, show the output to Westley, STOP, and wait for approval.** Do not batch steps. Do not self-verify and continue.

### Step 1 — Logger module, standalone

**Build:** `simulation/sim_logger.py` only. The class, the file I/O, the header write, the tick write, and the close/flush. No test script integration yet.

**Prove it:** Write a tiny standalone script (`simulation/test_sim_logger.py`) that instantiates a `SimLogger`, writes a header plus three fake tick lines with hand-constructed unit data, closes it, then reads the file back and prints each line. Westley verifies the file contains four JSON lines, the header is correct, and the tick lines parse.

**STOP.** Wait for Westley to confirm the format looks right before touching any real test script.

### Step 2 — Hook logger into one test script + perf budget check

**Build:** Add the `--dump <path>` flag to `simulation/test_checkpoint_6k_close_spawn.py` only. Instantiate the logger when the flag is present, call `log_tick` inside the existing tick loop, call `close` at the end. Do not touch any other test script yet.

**Prove it:** Three runs, all captured and displayed:

1. Baseline: `python3 simulation/test_checkpoint_6k_close_spawn.py` (no flag). Capture mean and p95 tick time.
2. With dump: `python3 simulation/test_checkpoint_6k_close_spawn.py --dump /tmp/6k_close.jsonl`. Capture mean and p95 tick time, file size, first three lines via `head -3`, last line via `tail -1`, total line count via `wc -l`.
3. Disabled re-check: `python3 simulation/test_checkpoint_6k_close_spawn.py` again. Capture mean and p95 tick time. Must match run 1 within noise.

Print all three number sets side by side in the checkpoint output. Per dev_rules performance regression discipline, the logger-enabled run must not exceed the baseline mean tick time by more than 5%, and the disabled re-check must be bit-for-bit equivalent to the baseline (only one `if logger is not None:` check per tick is permissible overhead). A >5% enabled-mode regression or any measurable disabled-mode regression is a budget failure — CC must optimize and re-run before moving on.

**STOP.** Westley confirms all three numbers and the dump well-formedness before CC proceeds.

### Step 3 — Minimal viewer: load and render static

**Build:** `tools/sim_viewer.py`. Loads the JSONL file, parses header, parses all tick lines into memory (defer streaming; assume file fits). Opens a pygame window. Renders tick 0 only — no playback, no controls, no inspector. Units drawn as faction-colored filled circles. Auto-fit camera to map bounds.

**Prove it:** Run `python3 tools/sim_viewer.py /tmp/6k_close.jsonl`. Window opens, shows unit positions at tick 0. Print to terminal: unit count per faction, map dimensions from header, and a confirmation that the window opened. Westley verifies unit counts match what the test spawned and positions look roughly right.

**STOP.** Westley confirms the static render before CC adds playback.

### Step 4 — Playback controls

**Build:** Add play/pause (spacebar), step forward (right arrow), step back (left arrow), jump to start (Home), jump to end (End), speed cycle (`+`/`-`), tick scrubber (click and drag). Display current tick, total ticks, current speed, current `subsystem_ms` totals next to the controls.

**Prove it:** Run the viewer on the same dump. Press space — playback starts. Press `+` — speed increases. Press right arrow while paused — one tick advance. Drag the scrubber — jump to arbitrary tick. Westley watches the approach phase and confirms units visually move toward each other.

**STOP.** Westley confirms playback works before CC adds camera controls.

### Step 5 — Camera controls

**Build:** Mouse drag to pan, scroll wheel to zoom toward cursor, `R` to reset camera, `F` to focus on selected unit (wire the key; behavior activates in step 6 when selection exists).

**Prove it:** Run the viewer. Drag to pan. Scroll to zoom in and out. Press `R` to reset. Westley confirms camera feels right.

**STOP.** Westley confirms camera before CC adds the inspector.

### Step 6 — Inspector panel and unit selection

**Build:** Click a unit in the map view to select it. Selected unit gets a yellow highlight ring. Inspector panel shows the selected unit's full state (uid, type, faction, layer, pos, vel, speed, hp, target, ability). Inspector updates live as playback advances. `F` key focuses camera on selected unit. Click empty space to deselect.

**Prove it:** Run the viewer. Click a unit. Inspector populates. Press space. Inspector updates each tick. Press `F`. Camera centers on selected unit. Click empty space. Inspector clears. Westley verifies a specific unit's state evolution across ticks.

**STOP.** Westley confirms the inspector before CC adds overlays.

### Step 7 — Overlays V, T, D

**Build:** The three high-value overlays. `V` (velocity vectors), `T` (target lines), `D` (density heatmap at 100 wu cells). Each toggled by its key. Default off.

**Prove it:** Run the viewer. Toggle `V` — velocity vectors appear on moving units. Toggle `T` — target lines appear between units and their targets. Toggle `D` — density heatmap overlays the map. Westley confirms each overlay is readable and correct.

**STOP.** Westley confirms. CC may implement the remaining overlays (`H`, `G`, `B`) as a single follow-up if Westley requests them, but the v1.2 done condition does not require them.

### Step 8 — Hook logger into remaining test scripts

**Build:** Add the `--dump <path>` flag to the remaining test scripts from the list in "Scope: Logger." Verify each file exists before editing; skip and report any that were deleted. This is a mechanical repeat of step 2 across multiple files. No per-file perf budget re-check is required — the step 2 budget already proved the logger is cheap.

**Prove it:** For each instrumented test: run with `--dump /tmp/<scriptname>.jsonl`, confirm the test still passes, print file size and line count. Westley signs off once all instrumented tests produce valid dumps.

**STOP.** This is the final implementation checkpoint. Done condition check happens next.

## Done Condition

Westley runs `python3 simulation/test_checkpoint_6k_close_spawn.py --dump /tmp/6k_close.jsonl` then `python3 tools/sim_viewer.py /tmp/6k_close.jsonl`. He watches the approach phase and the combat phase, scrubs to arbitrary ticks, clicks units to inspect, and toggles at least the `V`, `T`, and `D` overlays. The bug question he is trying to answer — *what is movement actually doing during slow ticks* — becomes visually investigable within a few minutes of playback.

Westley explicitly says "yes, this works" before the visualizer is considered done and the Layer 0 movement spec begins.

## Performance Budget

Per dev_rules.md performance regression discipline: every algorithm replacement or instrumentation addition must verify cost, not just correctness. The visualizer's logger component is an instrumentation addition that sits inside the hot tick loop of every instrumented test, so it is subject to this rule.

**Budget rules:**

1. **Baseline captured before step 2.** Pre-logger mean and p95 tick time on `test_checkpoint_6k_close_spawn.py` is the reference.
2. **Enabled-mode ceiling: 5% of mean tick time.** `logger_ms` is reported in the `subsystem_ms` block and must not exceed 5% of the mean tick cost. A run with `--dump` active must not exceed the baseline mean by more than 5%.
3. **Disabled-mode ceiling: zero measurable regression.** A run without `--dump` must be bit-for-bit equivalent in cost to the pre-instrumentation baseline. Only one `if logger is not None:` branch per tick is permissible.
4. **Both ceilings printed at the step 2 checkpoint.** Westley reviews the three numbers (baseline, enabled, disabled re-check) in terminal output and signs off on the budget before CC proceeds.
5. **Budget failure blocks the step.** A violation forces CC to optimize (cheaper JSON serialization, buffered writes, reduced per-unit field count) and re-run before the step 2 checkpoint closes.

The viewer has no performance budget — it is not on any critical path and runs on Westley's desktop only.

## Out of Scope for v1.2

- Recording from a live sim (file-only)
- Side-by-side comparison of two dumps
- Per-unit timeline plots in the inspector
- Editing scenarios from the viewer
- Network replay
- Compression of dump files
- Anti-aliased rendering, shaders, polish
- Showing terrain, navmesh, or fog of war (units only)
- Scenario harness (component 3 from earlier drafts — explicitly deferred)
- Overlays H, G, B (step 7 ships V, T, D only; the rest are optional follow-ups)

These may be added in later specs once v1.2 is in daily use and the next pain point is clear.

## Files Created

Filled in after implementation. Expected:

- `simulation/sim_logger.py`
- `simulation/test_sim_logger.py`
- `tools/sim_viewer.py`
- edits to `simulation/test_checkpoint_6k_close_spawn.py`
- edits to `simulation/test_checkpoint_6k.py`
- edits to `simulation/test_checkpoint_6k_small_field.py`
- edits to `simulation/test_checkpoint_6c.py`
- edits to `simulation/test_checkpoint_6d.py`
- edits to `simulation/test_6j_gradient.py` (if it still exists)

Any file not on this list should not be created by this work.
