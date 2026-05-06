# Launch Plan — Stage 13 ZIP

Coordinated multi-session push to ship the friends-ZIP build (Stage 13). Closes the remaining Stage 11 sub-goals, drains the launch_todo bug list, and packages everything per `docs/stage_specs/stage_13_spec.md`.

This doc is the brief. Each session picks a track, claims items in `docs/ai_status.md`, and works the checkpoints in order. Cross-track collisions are managed by the file-ownership table below — if a session needs to touch a file owned by a different track, claim it explicitly first.

## Status snapshot (2026-05-06)

- **Done:** Stages 1–12.5, Stage 11b/c/d (partial)/e.
- **Open Stage 11 sub-goals:** 11 C1 (line styling), 11 F (loop integration), 11 G (pause menu / exit path), 11 H (perf budget), 11d minimap viewport box, 11d enemy-clickability gate lift, 11f (deferred — playtest data).
- **Open launch_todo bugs:** unit rotation, squad-member impact origins, unit sizing, camera pan/zoom, combat balance, control-group swap.
- **Open launch_todo features:** ambient flyby ship removal, production building art, auto-assign unit-type hotkeys (1/2/3/4), shift-add selection, double-click-select-type, world view redesign (in flight per `ai_status.md`), chronicle output (in flight), library name regen, minimap viewport box, fog terrain darkening, command queueing, in-game tutorial, chronicle skip button.
- **Stage 13 spec:** ready, no implementation. Eight checkpoints A–H.

## The three tracks

### Track A — Sim & headless (Python, pytest-driven)

Owner: any session comfortable in `simulation/`.
Branch: `claude/survey-game-implementation-VE8jl` (or split per session).

Items:

1. **Rotation pipeline diagnostic test** — `simulation/test_facing_convergence.py` (added in this commit). Confirms `update_facing()` converges to the target bearing within tolerance over N ticks. Run it now (`cd simulation && python3 test_facing_convergence.py`) — **all 4 assertions pass**, so the sim-side rotation pipeline is correct.
2. **Snapshot facing propagation** — `simulation/test_facing_snapshot_propagation.py` (added in this commit). Confirms the snapshot serializer surfaces `facing_rad` in `full_snapshot()`, that `delta()` emits the change, and that `apply_delta()` round-trips it. **All 9 assertions pass.**

   Combined finding: **the rotation bug is renderer-side**, not sim. Track B should look at `scenes/tactical/unit_renderer.gd` — specifically how the squad mesh transforms consume `facing_rad` from the snapshot delta. Squads are renderer-only (`EraThemeResolver.get_squad_count`); the sim has one logical unit and is rotating it correctly. The most likely site is the squad mesh loop at `unit_renderer.gd:140-146`.
3. **Combat balance pass** — `simulation/sim_tuner.py` already exists with scenario harness + matplotlib graphing. Run a sweep against `config.UNIT_STATS`, read the curves directly. Per `bible_combat.md` engagement targets: minimum 45 s brawl, ~2 min tactical, 50v50 mirror 150–200 s.
4. **Stage 13 sim-side `--root` argparse** — added in this commit. `simulation/pipe_transport.py` `__main__` reads `--root` and `os.chdir`s before any file I/O. Verified by `tests/test_pipe_transport.py`-style smoke tests.
5. **Chronicle output polish** — already claimed in `ai_status.md` (rotation/chronicle session). Do not double-claim.
6. **Library name regen** — offline AI pipeline only. Out of friends-ZIP scope unless playtester feedback demands it; defer.

### Track B — Godot mechanics (testable, but visual confirm in the loop)

Owner: a session that can launch Godot.

Items, in order:

1. **Fix rotation in the renderer.** Track A confirmed the sim-side pipeline is correct (Track A items 1 & 2 both pass). The bug is in `scenes/tactical/unit_renderer.gd`. Squads are renderer-only — the sim has one logical unit and `EraThemeResolver.get_squad_count` controls the visible mesh count. Most likely the squad mesh transforms at `unit_renderer.gd:140-146` aren't picking up the per-tick `facing_rad` from the snapshot delta. Verify `facing_rad` is read from the apply_delta'd unit dict, then applied as a Y-axis (or up-axis) rotation on each squad mesh's `Transform3D.basis`.
2. **Squad impact origin.** Renderer-only fix. `scenes/tactical/visuals/projectile_renderer.gd` and `impact_feedback_manager.gd` currently spawn from / to the logical unit position. They need to spawn per squad mesh — either round-robin across squad indices or randomized per shot. Same `get_squad_count` API as the unit renderer.
3. **Control-group swap bug.** `scenes/tactical/input_router.gd` (recently touched in commit `8844c1d` — read the new logic first). Reproduce, then write a headless test scene that synthesizes input events and asserts selection state.
4. **Shift-add selection / double-click-select-type / enemy-clickable gate lift.** `input_router.gd`. Lift the `selection_eligible` gate for visible enemies (visibility comes from `scripts/tactical/visibility.gd`).
5. **Auto-assign unit-type hotkeys (1/2/3/4).** Same router. Auto, not manual.
6. **Command queueing + queue-state HUD indicator.** New mechanic — needs queue data structure on the unit, shift-modifier handling in router, optional queue rendering. Cheap-to-test queue logic; visual confirmation for the indicator.
7. **Camera pan/zoom tuning.** Pure feel. No automated test. Iterate with Westley.
8. **Unit sizing pass.** Pure feel. Iterate with Westley.

### Track C — Stage 11 closeout + Stage 13 packaging

Owner: a session that can launch Godot for the integration test.

Items, in order:

1. **11 G — pause menu + exit path.** Required for Stage 13 Checkpoint F's "quit mid-mission" test. New scene under `scenes/`, wires through `SceneRouter`. Small scope — Resume / Settings / Exit to Main Menu.
2. **11 F — full loop integration.** `pipe_transport.py` → `time_jump_emitter` → `time_jump_sequencer.gd`. Touches the sim entry and the Godot sequencer. Coordinate with Track A — `pipe_transport.py` is shared. **Before changing the tick delta JSON shape, post the proposed shape to `docs/architecture.md` per CLAUDE.md.**
3. **11 H — performance budget verification.** Run the busy time-jump scenario with the F3 debug overlay (build it as part of Stage 13 Checkpoint D first, see below). Capture FPS during peak narration. Pass: 60 FPS at medium zoom.
4. **11 C1 — connection line styling.** Solid (border) vs dashed (trade) in the world view renderer. `scenes/shared/world_view/renderers/shell_renderer.gd` (also touched in commit `8844c1d`).
5. **11d minimap viewport box.** Camera-frustum rectangle on the tactical minimap.
6. **Stage 13 Checkpoint A — PyInstaller sim bundle.** `build/pyinstaller_spec.py` and `build/build_zip.py` skeletons added in this commit. Iterate on hidden imports until the bundle starts. Bundle test: `sim/ouroboros_sim.exe --root <test_dir>` reaches `ready` message in <15 s, no Python install required.
7. **Stage 13 Checkpoint B — Godot export + sim launch integration.** Configure Godot export preset with the `release_build` feature tag. Modify `autoload/sim_bridge.gd` to resolve `SIM_EXECUTABLE_PATH` per `IS_RELEASE_BUILD`. Configure `project.godot` `use_custom_user_dir` and `custom_user_dir_name`.
8. **Stage 13 Checkpoint C — privacy modal.** New `scenes/privacy_modal/`. Disclosure text exact per spec, no rephrasing. Wire as main scene, transitions to existing `loading_screen.tscn`.
9. **Stage 13 Checkpoint D — debug overlay.** New `autoload/debug_overlay.gd`. F3 toggle. FPS, tick count, unit count, sim status. Off by default.
10. **Stage 13 Checkpoint E — build script polish.** Iterate `build/build_zip.py` until the full pipeline (PyInstaller → Godot export → assemble → ZIP) runs in one command.
11. **Stage 13 Checkpoint F — clean install verification.** 20-item checklist on a clean machine or VM. Westley runs this.
12. **Stage 13 Checkpoint G — version label** in `scenes/settings/settings.gd`.
13. **Stage 13 Checkpoint H — three full sessions, fresh build, different seeds.**

## File ownership (avoid collisions)

| File / area | Track | Notes |
|---|---|---|
| `simulation/pipe_transport.py` | A & C share | Track A owns the `__main__` `--root` bits; Track C owns `time_jump_emitter` wiring. Coordinate via ai_status. |
| `simulation/config.py` | A | Balance pass lives here. |
| `simulation/facing.py`, `damage.py`, `tactical_engine.py` | protected — ask Westley before changes. |
| `simulation/socket_server.py` | protected — explicit ask, always. |
| `simulation/snapshot_serializer.py` | A | Rotation/snapshot test reads it; balance work doesn't change shape. Tick-delta shape changes go to `docs/architecture.md` first. |
| `scenes/tactical/unit_renderer.gd` | B | Squad rotation, sizing, facing. |
| `scenes/tactical/visuals/projectile_renderer.gd`, `impact_feedback_manager.gd` | B | Squad-aware impact origins. |
| `scenes/tactical/input_router.gd` | B | All input/selection work. Recently touched on main; read it before editing. |
| `scenes/tactical/hud.gd`, `hud.tscn` | B | HUD additions (queue indicator, etc). |
| `autoload/sim_bridge.gd` | C | `SIM_EXECUTABLE_PATH`, release-build branch. |
| `autoload/theme_constants.gd` | C | `IS_RELEASE_BUILD` → `OS.has_feature("release_build")`. |
| `autoload/debug_overlay.gd` (new) | C | Stage 13 D. |
| `scenes/world/time_jump_sequencer.gd` | C | 11 F. Recently touched on main. |
| `scenes/shared/world_view/**` | C | 11 C1 line styling. Recently touched on main. |
| `scenes/privacy_modal/**` (new) | C | Stage 13 C. |
| `project.godot` | C | Custom user dir, main scene, export feature tag. |
| `build/**` (new) | C | All Stage 13 build tooling. |
| `docs/launch_todo.md` | shared | Mark items as you complete them with the date. |
| `docs/ai_status.md` | shared | Claim before starting an item. |
| `docs/architecture.md` | gated | Tick-delta shape changes go here *before* implementation. |
| `docs/bible/**` | gated | Append-only; bible edits need Westley sign-off. |

## Test strategy by item

| Item | Headless test? | Visual confirm needed? |
|---|---|---|
| Unit rotation (sim) | yes — `tests/test_facing_convergence.py` | no |
| Unit rotation (renderer) | partial — facing_rad in snapshot test | yes |
| Squad impact origins | no — renderer only | yes |
| Unit sizing | no | yes |
| Camera pan/zoom | no | yes |
| Combat balance | yes — `sim_tuner.py` graph + invariants | yes (final feel pass) |
| Control-group swap | yes — input-router fixture | spot check |
| Shift-add / double-click | yes — input-router fixture | spot check |
| Enemy clickable gate lift | yes — selection-eligible assertion | spot check |
| Auto unit-type hotkeys | yes — input-router fixture | spot check |
| Command queueing logic | yes — queue-state assertions | yes (queue indicator) |
| 11 C1 line styling | no | yes |
| 11 F loop integration | partial — sim emit + sequencer state machine | yes (the whole loop) |
| 11 G pause menu | partial — scene wiring | yes |
| 11 H perf | yes — F3 overlay capture | review |
| 11d minimap viewport box | no | yes |
| Stage 13 A PyInstaller | yes — bundle starts, --root works | no |
| Stage 13 B Godot export | yes — exported `.exe` runs | yes (loads to main menu) |
| Stage 13 C privacy modal | partial — flag-file persistence | yes |
| Stage 13 D debug overlay | partial — autoload registers | yes |
| Stage 13 E build script | yes — single-command ZIP build | review ZIP contents |
| Stage 13 F clean install | no — manual checklist | full 20-item run |
| Stage 13 G version label | no | yes |
| Stage 13 H stability | no — three-session run | yes |

## Order of operations (revised)

1. **Now:** Track A drops the rotation tests + Stage 13 `--root` + build skeletons (this commit).
2. **Concurrent:** Track B picks up rotation diagnosis using the new tests; Track C starts Stage 13 Checkpoint A (PyInstaller) + Checkpoint D (debug overlay) — neither depends on bug fixes.
3. **Then:** Track C does 11 G (pause menu) and 11 F (loop integration). Architecture-doc gate on tick-delta shape applies.
4. **Then:** Track B works through the input/selection items.
5. **Then:** Track A balance pass (sim_tuner sweeps).
6. **Then:** Track C Stage 13 B, C, E.
7. **Visual confirmation pass with Westley:** camera, sizing, 11 C1, minimap viewport, fog terrain darkening, ambient ship removal, command indicators, queue indicator.
8. **Then:** Stage 13 F → H.

## Guardrails

- **Protected engine files** (require Westley approval): `tick.py`, `drift.py`, `faction.py`, `region.py`, `events.py`, `event_engine.py`, `intent_resolver.py`, `border_friction.py`, `technology.py`, `diplomacy.py`, `world.py`, `templates.py`, `theme_scifi.py`. Note: `tactical_engine.py`, `facing.py`, `damage.py` are not on this list but treat them as protected — ask before editing logic.
- **Socket server protected:** `simulation/socket_server.py` — explicit ask before any change.
- **Tick delta shape:** any change to the JSON shape goes to `docs/architecture.md` *before* implementation.
- **Invariants:** never widen thresholds, extend windows, or loosen tolerances without Westley's approval. Scope-narrowing OK; loosening, never. Never weaken a test to make the implementation pass.
- **No blind reverts:** never `git checkout`, `git restore`, or `git stash` files without confirming git is up to date with Westley first. Two parallel sessions are likely writing files concurrently.
- **One fix at a time:** when multiple bugs surface, fix one, confirm, then move on. Batched fixes break bisection.
- **No shotgun debugging:** form a hypothesis, add logging, get user output, then fix. One confirmed diagnosis beats ten guesses.
- **Stage 13 STOP gates:** every checkpoint ends with `⛔ STOP`. Honor it. Wait for Westley before the next.

## Cross-session coordination

- Claim items in `docs/ai_status.md` before starting. Use the existing format.
- If you need to touch a file owned by another track, post a heads-up in `ai_status.md`'s Cross-Session Notes section before editing.
- Pull from origin frequently. Two parallel local Claude sessions are also writing files.
- Visual-confirm items: do not mark "done" until Westley has confirmed. Mark them "ready for confirm" in `ai_status.md`.

## What's in this commit (delivered alongside this doc)

- `docs/launch_plan.md` — this file.
- `simulation/pipe_transport.py` — `--root` argparse and `os.chdir` at sim entry. Stage 13 Checkpoint A prerequisite.
- `build/pyinstaller_spec.py` — skeleton .spec file. Hidden imports list will iterate during Checkpoint A.
- `build/build_zip.py` — skeleton build pipeline. Linear, no error recovery beyond printing what failed.
- `build/README.txt` — playtester-facing run instructions skeleton. Westley to author final prose.
- `build/feedback.txt` — playtester feedback template skeleton.
- `simulation/test_facing_convergence.py` — sim-layer rotation convergence test (passes).
- `simulation/test_facing_snapshot_propagation.py` — snapshot-serializer facing propagation test (passes).

These are starter material. None of the build tooling has been run end-to-end (no Godot export templates configured here, no Windows host); local sessions will iterate.
