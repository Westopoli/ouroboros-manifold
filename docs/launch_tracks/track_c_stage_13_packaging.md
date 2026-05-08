# Track C — Stage 13 Friends-ZIP Packaging

**Owner:** one Claude Code session.
**Branch:** `claude/survey-game-implementation-VE8jl` (or split per session, by ai_status.md claim).
**Reads first (in order):** `CLAUDE.md`, this file, `docs/stage_specs/stage_13_spec.md` (the canonical spec — this track is the implementer of that spec), `docs/ai_status.md`.

This track packages the existing game (Stages 1 → 12.5 + Stage 11 closeout) into a self-contained Windows ZIP per Stage 13. Almost everything is wrapping; very little is new game code. Every Stage 13 checkpoint ends with `⛔ STOP`. Honor every one — pause and wait for Westley before the next.

## Goal

Produce `OuroborosManifold-v0.13.0.zip` — a self-contained Windows distributable that a friend can extract and double-click, plays through the full generational loop, and quits cleanly. No Python install, no terminal, no dev environment on the playtester's machine.

## Scope (in)

- `build/**` — packaging tooling. Skeletons already in tree from the launch_plan starter commit (`pyinstaller_spec.py`, `build_zip.py`, `README.txt`, `feedback.txt`). Iterate.
- `scenes/privacy_modal/` (new) — first-launch privacy disclosure modal.
- `autoload/debug_overlay.gd` (new) — F3-toggled FPS/tick/unit overlay.
- `autoload/sim_bridge.gd` — `SIM_EXECUTABLE_PATH` resolution per `IS_RELEASE_BUILD`.
- `autoload/theme_constants.gd` — `IS_RELEASE_BUILD` becomes `OS.has_feature("release_build")` instead of a hardcoded constant.
- `project.godot` — `[application]` block only: `use_custom_user_dir=true`, `custom_user_dir_name="data"`, main scene change to `privacy_modal.tscn`. **Do NOT touch the `[autoload]` block** (C2 owns it, having added `FactionPalette` for Stage 11g).
- `scenes/settings/settings.gd` — version label addition (Stage 13 Checkpoint G).

## Scope (out — do NOT touch)

| Off-limits | Why |
|---|---|
| `scenes/tactical/**`, `scripts/tactical/**` | Track B. Do not edit even if a Stage 13 checkpoint seems to need it — escalate instead. |
| `simulation/**` (except `pipe_transport.py` `__main__` block, already done in starter commit) | Track A or protected. The `--root` argparse already landed; no further sim changes are part of Stage 13. If hidden_imports need additions to PyInstaller spec, that is `build/pyinstaller_spec.py` not sim code. |
| `scenes/world/**`, `scenes/shared/world_view/**` | C2 (Stage 11g) is editing extensively. |
| `project.godot [autoload]` | C2 owns this block. Coordinate via ai_status.md if you absolutely need to add an autoload. |
| `autoload/faction_palette.gd` | C2's. |

## Items in priority order

The Stage 13 spec defines 8 checkpoints A → H. Below is the ordered work plan for this track, with two items held until C2's Stage 11g lands.

### C1. Stage 13 Checkpoint A — PyInstaller sim bundle

**Build:** iterate `build/pyinstaller_spec.py` (already in tree). Run PyInstaller until the bundle starts on a Windows host without a Python install.

**Test:** `sim/ouroboros_sim.exe --root <test_dir>` directly from the command line — verify it starts, writes length-prefixed JSON progress messages, reaches `ready` within 15 s, creates `<test_dir>/logs/` (not inside `sim/`), accepts a command via stdin and responds.

**Print:** startup time, bundle size, first progress message, ready message.

**Verify:** sim starts without Python installed. Bundle < 200 MB. Ready within 15 s.

**Note:** if the build environment doesn't have a Windows host, document the spec changes you would make, run the closest available equivalent (e.g., a Linux PyInstaller bundle to validate hidden_imports list), and stop for Westley to do the Windows iteration. Do not block on environment — ship the spec progress and escalate.

⛔ STOP. Wait for Westley.

### C2. Stage 13 Checkpoint D — debug overlay

**Build:** new `autoload/debug_overlay.gd`. Register as autoload in `project.godot [autoload]` only after coordinating with C2 via `ai_status.md` (C2 added `FactionPalette` in that block recently).

**Behavior:** F3-toggled overlay showing FPS (`Engine.get_frames_per_second()`), tick count (from `SimBridge`), unit count (from `UIDataBus`), sim status (connected/disconnected). Off by default. Top-right corner, monospace, semi-transparent background.

**Test:** launch game. Verify invisible by default. Press F3, verify shows. Start a mission, verify tick/unit counts update live. Press F3 again, verify hides. Verify F3 conflicts with no other hotkey.

**Verify:** off by default. Toggles on F3. No conflict. Renders correctly at 1920×1080 and 1280×720.

⛔ STOP. Wait for Westley.

### C3. Stage 13 Checkpoint B — Godot export + sim launch integration

**Build:**
- Configure Godot Windows release export preset. The preset must include the custom feature tag `release_build`.
- Modify `autoload/theme_constants.gd`: `IS_RELEASE_BUILD` becomes `OS.has_feature("release_build")` (read at runtime, not a hardcoded constant).
- Modify `autoload/sim_bridge.gd`: when `IS_RELEASE_BUILD` is true, resolve the sim path to `sim/ouroboros_sim.exe` relative to the executable directory and spawn with `["--root", game_root]` instead of `[python, sim_script_path]`. When false, behavior is unchanged.
- Modify `project.godot [application]`: `use_custom_user_dir=true`, `custom_user_dir_name="data"`. Do **not** touch `[autoload]`.

**Test:** export. Place exported `.exe` + `.pck` alongside the `sim/` folder from C1. Run. Verify loading screen appears, sim spawns, progress displays, sim reaches ready, main menu loads with live data. Verify `data/logs/` is created next to the executable.

⛔ STOP. Wait for Westley.

### C4. Stage 13 Checkpoint C — privacy modal

**Build:** new `scenes/privacy_modal/privacy_modal.tscn` + `.gd`. Wire as main scene in `project.godot [application]`.

**Disclosure text — exact, do not modify:**
> **PRIVATE PLAYTEST BUILD**
>
> This build saves logs and crash reports to your machine. Nothing is sent anywhere. If you hit a bug, you can choose to send files to Westley — that's it.

**Visual treatment:** minimal — dark `BASE` background, centered `tm_card`, Newsreader body style, "I Understand" button in standard `tm_button` with gold accent. No scanline overlay, no animations, no galaxy background. Reuse Stage 9 theme components.

**Behavior:** check for `user://privacy_accepted` flag on `_ready`. If present, immediately go to `loading_screen.tscn`. If not, show modal. On button press, write flag, then go to loading screen.

**Test:** first launch — modal appears. Click button. Verify flag file written and transition to loading screen. Second launch — modal skipped. Delete flag file manually — modal reappears.

⛔ STOP. Wait for Westley.

### C5. Stage 13 Checkpoint E — build script polish

**Build:** iterate `build/build_zip.py` until it runs the full pipeline in one command:
```
python build/build_zip.py
```
Steps: PyInstaller → Godot headless export → assemble folder per Stage 13 spec layout → copy README and feedback.txt → ZIP.

**Test:** run from project root. Verify ZIP contents match the spec's folder structure exactly. No dev-only files (`.import/`, `.godot/`, `__pycache__/`, `.git/`).

**Verify:** ZIP < 500 MB (flag if larger). README and feedback.txt present.

⛔ STOP. Wait for Westley.

### C6. Stage 13 Checkpoint G — version label

**Build:** add a Label at the bottom of `scenes/settings/settings.gd` showing build version (e.g., "Friends Build v0.13.0"). Source from a `VERSION` constant in `theme_constants.gd` or a `version.cfg` — pick one and document.

**Test:** open settings. Version visible. Correct value.

⛔ STOP. Wait for Westley.

### C7. Stage 13 Checkpoint F — clean install verification

**No new code.** Westley runs the 20-item checklist from `stage_13_spec.md` Checkpoint F on a clean machine or VM.

This track's job is to make sure all prior checkpoints landed cleanly and that any blockers Westley hits during the checklist are diagnosed and fixed.

⛔ STOP. Wait for Westley.

### C8. Stage 13 Checkpoint H — final stability

**No new code.** Three full sessions on the clean-install machine, different seeds, 2+ chapters each. Westley runs.

⛔ STOP.

### Held items (waiting on C2's Stage 11g to land)

These are *not* Stage 13, but they're on the launch path and listed here so the track owner doesn't accidentally pick them up too early:

- **11G — pause menu (Resume / Settings / Exit to Main Menu).** New scene. Required for Stage 13 Checkpoint F's quit-mid-mission test. Touches `SceneRouter`. Hold until C2 finishes Stage 11g Checkpoint L (inspection-state pause integration). Different surface from C2's pause, but co-located in the world view / sequencer code path.
- **11C1 — connection line styling (border vs trade, solid vs dashed).** Touches `scenes/shared/world_view/renderers/shell_renderer.gd`. Hold until C2 finishes Stage 11g Checkpoint M (faction palette integration touches the same file extensively).

When unblocked, these slot in after C6 / before C7.

## Workflow

1. `git pull` before starting any checkpoint.
2. Claim the checkpoint in `docs/ai_status.md` before editing.
3. Build the code, run the checkpoint's "Test" section as written.
4. Print whatever the checkpoint's "Print" section asks for.
5. Verify against the checkpoint's "Verify" section.
6. ⛔ STOP. Wait for Westley before the next checkpoint.

## Guardrails

- **`⛔ STOP` gates are absolute.** Never chain checkpoints. Never self-verify and continue.
- **Stage 13 invariants I1–I12** (in `stage_13_spec.md`) — keep them in mind. The most easily violated:
  - I3 — sim process invisible (no console window)
  - I5 — debug output suppressed under `IS_RELEASE_BUILD = true`
  - I6 — no leaked dev paths (`/home/`, `C:\Users\`, project paths) in saves, logs, or `.pck`
  - I9 — kill switch functional (`IS_RELEASE_BUILD = false` restores dev mode cleanly)
- **No game logic in Stage 13.** If you find yourself writing combat/sim/scene logic, stop — it belongs in an earlier stage. This track only packages.
- **`project.godot [autoload]` — coordinate via ai_status.md.** C2 owns this block right now.
- **No blind git reverts.**

## Definition of done

- All 8 Stage 13 checkpoints (A → H) approved by Westley.
- All 12 Stage 13 invariants pass.
- ZIP delivered to playtest group.
- `docs/launch_todo.md` and `docs/launch_plan.md` reflect Stage 13 closure.
