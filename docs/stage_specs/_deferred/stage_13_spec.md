# Stage 13 — Friends-ZIP Build, Bundling, and Distribution Hygiene

## Goal

Produce a self-contained Windows ZIP that a friend can extract and double-click. The game launches, plays through the full generational loop (onboarding → mission → debrief → time jump → mission → ...), and quits cleanly — with no Python install, no terminal, no dev environment on the playtester's machine. Address the gap between "works on the developer's machine" and "works on a cold install."

## Bible References

Read the hub (`game_bible.md`) plus:

- `game_bible.md` → Stage 13 roadmap entry, Sacred Design Principle #3, `IS_RELEASE_BUILD` discipline (established Stage 9)

No spoke files required — this stage covers packaging and distribution, not game systems. Stage 9 spec is consulted for `IS_RELEASE_BUILD` semantics, `ThemeConstants`, `SceneRouter`, and security architecture. Stage 10 spec is consulted for sim process lifecycle (`OS.execute_with_pipe()`, `SIM_SCRIPT_PATH`, `pipe_transport.py`, crash log infrastructure). Stage 12 spec is consulted for bug report system (F12 capture).

Do not read `docs/bible_history/bible_2_00_combat.md`, `docs/bible_history/bible_2_00_simulation.md`, `docs/bible_history/bible_2_00_missions.md`, `docs/bible_history/bible_2_00_chronicle.md`, `docs/bible_history/bible_2_00_world.md`, `docs/bible_history/bible_2_00_antagonist.md`, `bible_monetization.md` (deleted 2026-05-31; see docs/bible_history/), `docs/bible_history/bible_2_00_ai_pipeline.md`, or `animation_strategy.md` — not relevant to Stage 13.

## Context

### What exists

- **Stages 1–5.5** — simulation backbone, chronicle distiller, coherence ledger, naming system, mission generator. All complete and stable.
- **Stage 6** — headless tactical engine with deterministic tick loop, outcome band classification, force retention scoring.
- **Stage 7 / 7.5** — map generation pipeline and enemy macro behavior scripts.
- **Stage 8** — Godot renderer, WebSocket bridge (superseded by Stage 10 stdio pipes), command interface, persistence layer (`save_writer.py`, `save_loader.py`, `TacticalEngine.export_full_state()` / `restore_from_state()`).
- **Stage 8.5** — `EraThemeResolver` autoload, per-era JSON manifests, 3D tactical rendering.
- **Stage 9** — UI shell with `UIDataBus` singleton, `SceneRouter`, `ThemeConstants` (including `IS_RELEASE_BUILD`), `InputSanitizer`, settings screen, all non-combat screens. Security architecture: pre-authored error messages, input sanitization, `IS_RELEASE_BUILD` logging discipline.
- **Stage 10** — live sim data over stdio pipes. Godot spawns Python sim via `OS.execute_with_pipe()`, `SIM_SCRIPT_PATH` config points to the sim entry script. `SimBridge` autoload owns process lifecycle. Crash log infrastructure writes to `logs/crash_report.txt`. `USE_LIVE_SIM` config flag switches between live and mock data sources.
- **Stage 11** — world view (via `WorldViewShell` + component architecture), chronicle scroll, seamless transition sequencer. Full macro-loop visual flow.
- **Stage 12** — onboarding (archetype descriptions, accordion), mission debrief (outcome band, objectives, ribbon graphs, impact preview), autosave at three loop boundaries (post-debrief, post-narration, mid-mission quit), bug report capture (F12 hotkey, rolling buffer, ZIP bundler, clipboard delivery).
- **Stage 12.5** — combat visual polish (unit facing, attack visuals, ability overlays, impact feedback, destruction sequences, ambient battle density, selection circle recolor, HUD animation refinement, edge-scroll speed setting).

### What Stage 13 adds

Stage 13 adds no new game systems. It packages everything from Stages 1–12.5 into a distributable artifact:

1. **Python sim bundling** — PyInstaller freezes the sim into a standalone Windows executable.
2. **Godot export** — Windows release export with `IS_RELEASE_BUILD = true`.
3. **Privacy modal** — first-launch acceptance gate before gameplay begins.
4. **Debug overlay** — lightweight FPS/tick/unit count overlay, off by default, toggled by F3.
5. **Build script** — automated pipeline producing the final ZIP.
6. **Pre-distribution checklist** — clean-install verification procedure.

### Design decisions (resolved)

**Python bundling tool:** PyInstaller, one-dir mode. Produces `sim/ouroboros_sim.exe` plus `sim/_internal/`. Chosen over Nuitka (build complexity not worth marginal startup improvement for a friends build) and PyInstaller one-file mode (10–20s extraction delay before any progress messages is a dealbreaker).

**Privacy modal:** Acceptance gate. First-launch modal with "I Understand" button. Writes `user://privacy_accepted` flag so it shows once. No "Decline" button — closing the window is the opt-out. Appears before the loading screen starts the sim.

**Crash log strategy:** Godot's built-in log file (`godot.log`), enabled via project settings. Custom user directory configured to `data/` next to the executable (via `application/config/use_custom_user_dir` and `application/config/custom_user_dir_name`), so logs land at `data/logs/godot.log` inside the extracted ZIP folder — not buried in `AppData`. No custom Godot-side crash handler. Python-side crash log (`logs/crash_report.txt`) carries forward from Stage 10 unchanged.

**ZIP folder structure:** Flat with `sim/` subfolder.
```
OuroborosManifold/
├── OuroborosManifold.exe          ← double-click this
├── OuroborosManifold.pck          ← Godot resource pack
├── sim/                           ← PyInstaller output
│   ├── ouroboros_sim.exe
│   └── _internal/
├── data/                          ← created at runtime: logs, saves, settings
├── README.txt
└── feedback.txt
```

**Build pipeline:** Single Python build script that chains PyInstaller, Godot headless export, folder assembly, and ZIP creation. One command produces the final artifact. Godot export template configuration is a manual one-time prerequisite.

**Debug overlay:** Lightweight Label overlay showing FPS, tick count, active unit count, sim connection status. Off by default, toggled by F3. `IS_RELEASE_BUILD = true` still suppresses console `print()` — the overlay is a separate visual element. README mentions F3 under "Troubleshooting."

**Privacy modal visual treatment:** Minimal Terminal Meets Glass aesthetic. Dark `BASE` background, centered `tm_card`, disclosure text in Newsreader body style, "I Understand" button in standard `tm_button` style with gold accent. No scanline overlay, no animations, no galaxy background. Reuse existing Stage 9 theme components — do not build new visual systems for this screen.

**Privacy modal disclosure text:** Exact text, do not modify:
> **PRIVATE PLAYTEST BUILD**
>
> This build saves logs and crash reports to your machine. Nothing is sent anywhere. If you hit a bug, you can choose to send files to Westley — that's it.

**`IS_RELEASE_BUILD` toggle mechanism:** Godot feature tag, auto-detected at runtime. The Godot export preset defines a custom feature tag `release_build`. `ThemeConstants` reads `OS.has_feature("release_build")` — when running from the editor, the feature is absent (`false`); when running from the exported build with the tag set, it's `true`. Zero manual toggling between dev and release. The build script does not patch GDScript files. The export preset is the single source of truth for release mode.

**Sim working directory in release build:** The game root directory is passed to the sim as a `--root` command-line argument. Godot passes `["--root", OS.get_executable_path().get_base_dir()]` when spawning the sim process. The sim reads `--root` via `argparse` and uses it as the base for all relative path resolution (`logs/`, saved state, etc.). If `--root` is absent (dev mode, running from Python directly), the sim defaults to `os.getcwd()`. This keeps path resolution explicit and identical between dev and release — no PyInstaller-specific `sys._MEIPASS` detection, no `os.chdir()` calls.

## What to Build

### New files — Godot

```
scenes/privacy_modal/
├── privacy_modal.tscn              - Full-screen modal. Dark BASE background,
│                                     centered tm_card, disclosure text in
│                                     Newsreader body style, "I Understand"
│                                     tm_button with gold accent. No scanline,
│                                     no animations, no galaxy background.
│                                     Uses exact disclosure text from Design
│                                     Decisions section — do not rephrase.
└── privacy_modal.gd                - Checks for flag file on _ready(). If flag
                                      exists, immediately transitions to loading
                                      screen. If not, shows modal. On button press,
                                      writes flag and transitions.

autoload/
└── debug_overlay.gd                - F3-toggled overlay. Reads Engine.get_frames_
                                      per_second(), tick count from SimBridge, unit
                                      count from UIDataBus. Invisible by default.
                                      Renders as a Label in the top-right corner,
                                      monospace, semi-transparent background.
```

### New files — Python

```
(none — Stage 13 adds no new Python files)
```

### Modified files — Python

**`sim/pipe_transport.py` (or sim entry point)** — additive. Add `argparse` handling for `--root <path>`. If `--root` is provided, `os.chdir(root)` at startup before any file I/O (log file creation, state loading, etc.). If absent, no change to current behavior (`os.getcwd()` is used). This is the only sim-side change in Stage 13.

### New files — Build tooling

```
build/
├── build_zip.py                    - Build pipeline script. Runs PyInstaller on
│                                     the sim entry point, runs Godot headless
│                                     export, assembles folder structure, copies
│                                     README and feedback template, creates ZIP.
├── README.txt                      - Playtester-facing run instructions, F3/F12
│                                     hotkey reference, crash log locations,
│                                     feedback submission instructions.
├── feedback.txt                    - Template: name, date, what you played,
│                                     what worked, what didn't, crashes/bugs,
│                                     general impressions. Blank fields for
│                                     playtester to fill in and email back.
└── pyinstaller_spec.py             - PyInstaller .spec file for the sim bundle.
                                      Configures entry point, hidden imports,
                                      data files, output name.
```

### Modified files — Godot

**`project.godot`** — Two changes:
1. `application/config/use_custom_user_dir = true` and `application/config/custom_user_dir_name = "data"` — redirects `user://` to a `data/` folder next to the executable.
2. Main scene changed from `loading_screen.tscn` to `privacy_modal.tscn` (privacy modal handles the transition to loading screen).

**`autoload/sim_bridge.gd`** — `SIM_SCRIPT_PATH` replaced with `SIM_EXECUTABLE_PATH` logic that resolves differently based on `IS_RELEASE_BUILD`:
- When `false` (development): spawns `python sim/main.py` (or equivalent dev entry point) via `OS.execute_with_pipe()` as today. No `--root` argument (sim uses `os.getcwd()`).
- When `true` (release build): spawns `sim/ouroboros_sim.exe` (relative to executable directory) via `OS.execute_with_pipe()` with `["--root", game_root]`. No Python interpreter in the path.

**`autoload/theme_constants.gd`** — `IS_RELEASE_BUILD` changed from a hardcoded constant to `OS.has_feature("release_build")`. The Godot export preset defines the custom feature tag `release_build`. Running from the editor → feature absent → `false`. Running from export → feature present → `true`. No manual toggle, no build script file patching.

**`scenes/settings/settings.gd`** — additive. "Version" label at bottom of settings screen showing build version string (e.g., "Friends Build v0.13.0"). Helpful for identifying which build a playtester is running when they report issues.

## Integration Points

### Sim process launch path

`SimBridge._ready()` currently runs:
```gdscript
var result = OS.execute_with_pipe(python_path, [sim_script_path])
```

In the release build, this becomes:
```gdscript
var game_root = OS.get_executable_path().get_base_dir()
var sim_exe = game_root.path_join("sim/ouroboros_sim.exe")
var result = OS.execute_with_pipe(sim_exe, ["--root", game_root])
```

The `--root` argument tells the sim where to resolve all relative paths (`logs/`, saved state, etc.). In dev mode (running from Python directly), `--root` is absent and the sim defaults to `os.getcwd()`. The sim parses `--root` via `argparse` at startup before any file I/O.

The sim executable reads/writes the same length-prefixed JSON protocol over stdio. No protocol changes. The `pipe_transport.py` module is frozen inside the PyInstaller bundle — it doesn't know or care that it's running from a frozen executable.

### Privacy modal → loading screen flow

```
Game launch
    │
    ▼
privacy_modal.tscn (_ready)
    │
    ├── Flag file exists → SceneRouter.go_to("loading_screen")
    │
    └── Flag file missing → Show modal
            │
            └── "I Understand" pressed → write flag → SceneRouter.go_to("loading_screen")
                    │
                    ▼
            loading_screen.tscn (Stage 10 — spawns sim, shows progress)
                    │
                    ▼
            main_menu.tscn
```

### Config flags

| Flag | Value in release build | Effect |
|------|----------------------|--------|
| `IS_RELEASE_BUILD` | `true` | Suppresses all `print()` output. Error messages pre-authored only. |
| `USE_LIVE_SIM` | `true` | UIDataBus delegates to SimBridgeDataSource, not MockDataSource. |
| `ENTITLEMENT_SETTLED_REACH` | `true` | All era-access checks pass for Settled Reach. |

### Kill switch

`IS_RELEASE_BUILD = false` reverts the build to development mode: sim launched from Python script, debug output enabled, privacy modal still appears (flag file check is independent of build mode).

## Checkpoints

### Checkpoint A — PyInstaller Sim Bundle

**Build:** `build/pyinstaller_spec.py` and the PyInstaller invocation section of `legacy/build/build_zip.py`. Freeze the Python sim into `sim/ouroboros_sim.exe` + `sim/_internal/`.

**Test:** Run `sim/ouroboros_sim.exe --root <some_test_dir>` directly from the command line (not through Godot). Verify it starts, writes progress messages to stdout in length-prefixed JSON format, reaches the `ready` message, and creates `logs/` inside `<some_test_dir>` (not inside `sim/`). Then send a simple command via stdin and verify a response. Run on a machine without Python installed if possible (or rename/hide the Python installation temporarily). Also test without `--root` — verify it falls back to cwd.

**Print:** Startup time (seconds from process launch to `ready` message). Bundle size (total `sim/` folder). First progress message and ready message content.

**Verify:** Sim starts without Python installed. Progress messages arrive in correct format. Ready message arrives within 15 seconds. Bundle size < 200MB.

⛔ STOP.

### Checkpoint B — Godot Export + Sim Launch Integration

**Build:** Godot Windows release export configuration. Modify `sim_bridge.gd` to resolve `SIM_EXECUTABLE_PATH` for release builds. Configure `project.godot` custom user directory.

**Test:** Export the Godot project. Place the exported `.exe` + `.pck` alongside the `sim/` folder from Checkpoint A. Run the `.exe`. Verify: loading screen appears, sim process spawns, progress messages display, sim reaches ready, main menu loads with live data.

**Print:** Loading screen → ready transition time. Sim process PID (verify it launched). `data/logs/` directory creation (verify custom user dir works). Godot log file location.

**Verify:** Game launches from exported `.exe`. Sim spawns from `sim/ouroboros_sim.exe`. Loading screen shows progress. Main menu reaches live data. `data/` folder created next to executable. Godot log at `data/logs/godot.log`.

⛔ STOP.

### Checkpoint C — Privacy Modal

**Build:** `scenes/privacy_modal/privacy_modal.tscn` + `.gd`. Wire as main scene in `project.godot`.

**Test:** (1) First launch — no flag file exists. Verify modal appears with disclosure text and "I Understand" button. Click button. Verify flag file written to `data/privacy_accepted` (or `user://privacy_accepted`). Verify transition to loading screen. (2) Second launch — flag file exists. Verify modal is skipped, loading screen appears immediately. (3) Delete flag file manually. Verify modal reappears on next launch.

**Print:** Flag file path and contents. Modal → loading screen transition timing.

**Verify:** Modal blocks on first launch. Flag persists. Modal skips on subsequent launches. Deleting flag restores modal.

⛔ STOP.

### Checkpoint D — Debug Overlay

**Build:** `autoload/debug_overlay.gd`. Register as autoload.

**Test:** Launch game. Verify overlay is invisible by default. Press F3. Verify overlay appears showing FPS, tick count (0 or N/A before mission), unit count (0 or N/A), sim status (connected/disconnected). Start a mission. Verify tick count and unit count update in real time. Press F3 again. Verify overlay hides. Verify F3 does not conflict with any existing hotkey.

**Print:** Screenshot of overlay during mission (showing live values). F3 toggle behavior.

**Verify:** Off by default. Toggles on F3. Shows accurate live data during missions. No hotkey conflict. Renders correctly at 1920×1080 and 1280×720.

⛔ STOP.

### Checkpoint E — Build Script + ZIP Assembly

**Build:** `legacy/build/build_zip.py`, `legacy/build/README.txt`, `legacy/build/feedback.txt`, `build/pyinstaller_spec.py`. The full automated pipeline.

**Test:** Run `python legacy/build/build_zip.py` from the project root. Verify it: (1) runs PyInstaller and produces `sim/` folder, (2) runs Godot headless export and produces `.exe` + `.pck`, (3) assembles the folder structure per the spec, (4) copies README and feedback template, (5) creates the final ZIP. Inspect the ZIP contents.

**Print:** Build script console output (each step with timing). ZIP file listing (`zipinfo` or equivalent). Total ZIP size.

**Verify:** ZIP contains exactly the specified folder structure. No dev-only files (no `.import/`, no `.godot/`, no `__pycache__/`, no `.git/`). README and feedback.txt present. ZIP size reasonable (< 500MB — flag if larger).

⛔ STOP.

### Checkpoint F — Clean Install Verification

**Build:** No new code. Run the pre-distribution checklist.

**Test:** Extract the ZIP on a second machine (or a clean VM) with no development environment. Run through the full checklist:

1. Double-click `OuroborosManifold.exe`. Game launches.
2. Privacy modal appears. Click "I Understand."
3. Loading screen with progress. Sim starts.
4. Main menu loads.
5. Start new game. Onboarding screen. Select options. Confirm.
6. Opening time jump. Chronicle scroll prints.
7. First mission. Combat works (units move, attack, take damage, die with visual effects).
8. F12 bug report — verify ZIP created in `data/logs/reports/`.
9. F3 debug overlay — verify it toggles and shows live data.
10. Complete mission. Debrief screen.
11. Continue. Pull-back → world view → narration → Proceed.
12. Second mission begins.
13. Quit mid-mission. Close game.
14. Relaunch. Continue. Verify resume at saved point.
15. Complete mission. Continue through narration.
16. Exit to main menu. Verify clean exit.
17. Check `data/logs/godot.log` exists and contains no absolute dev paths.
18. Check `data/logs/sim_stderr.log` exists.
19. Check save file (in `data/`) contains no absolute dev paths.
20. Verify no console window appears (sim runs headless, no visible terminal).

**Print:** Checklist results (pass/fail per item). Any warnings or anomalies.

**Verify:** All 20 checklist items pass. Full game loop works on a clean machine. No leaked dev paths in any file. No visible sim process window.

⛔ STOP.

### Checkpoint G — Version Label + Settings

**Build:** Version label in settings screen.

**Test:** Open settings. Verify version string visible at bottom. Verify it reads "Friends Build v0.13.0" (or whatever version string is configured).

**Print:** Screenshot of settings screen with version label.

**Verify:** Version label present. Readable. Correct value.

⛔ STOP.

### Checkpoint H — Final Build + Stability

**Build:** No new code. Final ZIP build via the build script, fresh from clean state.

**Test:** Three full sessions on the clean-install machine (different seeds), 2+ chapters each. Cover: onboarding variations, multiple mission types, mid-mission quit/resume, F12 reports, F3 overlay during combat, debrief, narration, Exit to main menu, re-Continue.

**Print:** Session summaries. Any crashes or anomalies. ZIP size. Startup time. Frame time during combat at medium zoom (from F3 overlay).

**Verify:** Zero crashes across 3 sessions. Full loop clean each time. Startup time < 15 seconds (process launch to main menu). Combat at 60fps (medium zoom). All playtester-facing files (README, feedback.txt) are accurate and complete.

⛔ STOP.

## Invariants

- **I1 — No Python required.** The ZIP runs on a Windows machine with no Python installation.
- **I2 — Single click launch.** Double-clicking `OuroborosManifold.exe` starts the game. No additional steps.
- **I3 — Sim process invisible.** No console window, no terminal, no visible subprocess. The player sees one application.
- **I4 — Privacy gate.** First launch shows privacy modal before any gameplay. Subsequent launches skip it.
- **I5 — Debug output suppressed.** With `IS_RELEASE_BUILD = true`, no `print()` output reaches the Godot console or any player-visible log. Godot's internal log (`godot.log`) is exempt — it's a diagnostic file, not player-facing output.
- **I6 — No leaked dev paths.** `grep -r` across all files in the extracted ZIP (saves, logs, config, `.pck`) returns zero absolute paths from the build machine (no `/home/`, no `C:\Users\`, no project-specific paths).
- **I7 — Crash log isolation.** Python crash log (`logs/crash_report.txt`) contains relative paths only, sim version, OS version, Python version. No save data, no absolute paths, no env vars, no machine-identifying info. (Inherited from Stage 10.)
- **I8 — Sim protocol unchanged.** The frozen sim executable uses identical length-prefixed JSON protocol as the development sim. Zero protocol changes between dev and release.
- **I9 — Kill switch functional.** `IS_RELEASE_BUILD = false` + `USE_LIVE_SIM = false` restores full development behavior (Python script launch, mock data, debug output).
- **I10 — Debug overlay isolation.** F3 overlay has zero effect on game state, simulation, or frame timing (beyond the Label render cost). Toggling it mid-mission does not affect determinism.
- **I11 — Autosave round-trip in release build.** Save written by the release build is loadable by the release build. (Inherited from Stage 12 I1, verified in the release context.)
- **I12 — Sim path resolution via `--root`.** When `--root` is passed, all sim file I/O (logs, crash reports, state) resolves relative to the provided root, not relative to the sim executable's location. When `--root` is absent, sim uses `os.getcwd()`.

## Done Condition

- All 8 checkpoints (A–H) approved.
- All 12 invariants pass.
- Full game loop (onboarding → 2+ chapters with combat → debrief → narration → quit/resume → exit) runs cleanly on a clean-install machine.
- ZIP produced by the build script in a single command.
- README and feedback template are complete and accurate.
- Privacy modal appears on first launch, skips on subsequent.
- F3 overlay shows live data during missions.
- F12 bug report produces a ZIP in `data/logs/reports/`.
- No leaked dev paths in any file.
- No visible sim process window.
- ZIP delivered to playtest group.

## Files Created

(Filled in after implementation.)

## Notes for the Implementing Session

- **This is a packaging stage, not a systems stage.** Almost all the game code already exists. Stage 13 wraps it for distribution. If you find yourself writing game logic, stop — it belongs in an earlier stage.
- **PyInstaller hidden imports.** The sim likely uses packages that PyInstaller can't auto-detect (e.g., packages loaded dynamically, or C extensions). The `pyinstaller_spec.py` file needs a `hiddenimports` list. Build, test, see what's missing, add to the list. This is an iterative process — expect 2–3 rounds.
- **Godot export templates must be installed first.** The build script assumes Godot export templates for the target platform are already installed in the editor. This is a manual one-time setup step — the spec does not automate it. Document the exact Godot version and export template version required.
- **`OS.execute_with_pipe()` on Windows with `.exe`.** Verify that the process spawns without a visible console window. Godot's `OS.execute_with_pipe()` may need `OS.PROCESS_FLAG_OPEN_CONSOLE = false` or the PyInstaller spec may need `console=False` in the `.spec` file. Test this explicitly in Checkpoint B.
- **Custom user directory and `user://` paths.** Setting `use_custom_user_dir` changes where `user://` resolves. Every existing system that writes to `user://` (settings, saves, privacy flag) will now write to `data/` next to the executable. Verify this doesn't break anything — particularly the save system's path expectations from Stage 12.
- **README content is authored by Westley.** The build script copies a `README.txt` from `build/`. The spec provides the structure; Westley writes the actual prose before distribution.
- **The build script is a developer tool.** No GUI, no error recovery beyond printing what failed. If PyInstaller fails, it prints the error and exits. If Godot export fails, same. The script is linear — step 1, step 2, step 3, zip.
- **Version string.** The settings screen version label and any version references in logs should read from a single source — a `VERSION` constant in `ThemeConstants` or a `version.cfg` file. The build script can auto-increment or stamp this. Decide during implementation, not in spec — this is an engineering decision.
