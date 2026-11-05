# Wave 3 Wiring Spec — B2 + B3 + B5 (HISTORICAL)

**Status:** Locked 2026-05-26, shipped via PR #24 (2026-05-29). Document preserved as historical reference of what was built. The "Pre-Zip BLOCKER" + "Phase 1 ship plan" framing referenced below is dead per the 2026-05-30 cleanse — the substrate (B2 mission objectives clarity, B3 in-game tutorial, B5 release-mode wiring) shipped and remains live in the codebase.

## Context

Wave 3 closed three substrate gaps for the eventual Steam ship goal (long-term, no near-term deadline). Wave 2.5R/2.6M (cover-LOS sim substrate) merged via PR #23. Wave 3 = remaining wiring at the time of the 2026-05-26 decision:

- **B2 Mission objectives clarity** — sim-side briefing data + scene plain-language header
- **B3 In-game tutorial** — first-mission 5-beat overlay wiring + replay path
- **B5 Stage 13 packaging** — Windows PyInstaller spec + privacy modal + release-mode wiring

Wave 3 does NOT touch B4 (PAN_SPEED retune, 1-line post-playthrough) or B6 (tactical save, depends on pause menu surface). Steam launch tasks S#1-S#7 are post-Wave-3.

**Game framing — critical for subagent context:**

Game = pause-and-command tactical w/ generational chronicle. Player commands troops mid-mission (tactical layer) + watches civilization rise/fall via auto-advancing chronicle (world layer). Missions auto-trigger post-time-jump — NO manual mission selection from world map. NOT an RTS. NOT a 4X. Phase 1 reframe locked 2026-05-18 in `docs/bible/game_bible.md ## In Flux ### PIVOT 2026-05-18`.

---

## Design contract (LOCKED)

### B2 — Mission briefing plain-language header

**Sim side: NO WORK NEEDED.** `simulation/mission_briefing.py` already exposes plain-language imperatives via `OBJECTIVE_TEMPLATES_SHORT` for all 10 archetypes. `assemble_briefing()` already returns dict with key `objective: str` populated from `OBJECTIVE_TEMPLATES_SHORT` with slot substitution applied (line 63, 71). `simulation/pipe_transport.py:182-307` `_mission_setup_to_briefing()` already passes `objective` through into the dict emitted on sim_state messages. (Discovered 2026-05-26 during due-diligence audit — original spec assumed a new `short_objective` field was needed; verification showed existing infra was sufficient.)

**Godot side (`scenes/mission_briefing/mission_briefing.gd`):**
- New RichTextLabel header above MISSION OBJECTIVES section.
- Style: large + uppercase + era-active accent color via existing `_accent` member pattern (line 11: `_accent = ThemeConstants.get_era_accent(_data.get("era_id", "roman"))`). Apply via theme color override OR BBCode `[color=#<accent_hex>][b]<TEXT-UPPERCASE>[/b][/color]` using `_accent.to_html(false)` for hex string.
- Reads `objective` key from briefing dict (the existing field, no rename).
- If `objective` missing/empty → header hidden (graceful fallback, no scene error).

### B3 — Tutorial wiring

**Phase 1 scope:** simple 5-beat barebones first-mission tutorial in chronicle voice. NOT the multi-stage hallmark tutorial from `bible_monetization.md` component 8 (deferred post-launch).

**Bible alignment:** matches `docs/legacy/method_era1/priority_queue.md` Q#6 definition of done — "tutorial sequence covers movement, selection, control groups, mission objective, chronicle." Lore-tone, chronicle voice.

**Trigger model:**
- Tutorial fires ONCE on first-ever launch. Persistence via plain file `user://tutorial_completed` (string contents irrelevant; existence = completed).
- Onboarding completes → first mission starts → tutorial state machine listens for tactical signals → fires beats TUT_001 → TUT_005 in sequence.
- Beat advancement on click-anywhere OR ESC. No auto-timer.
- After TUT_005 dismissal → tutorial state machine writes `user://tutorial_completed` → never fires again automatically.
- Main menu "Replay Tutorial" button → deletes `user://tutorial_completed` + sets in-memory replay flag → next mission re-fires sequence.

**Tutorial state machine:**
- Lives as autoload singleton (`autoload/tutorial_state_machine.gd`). Survives scene transitions.
- Listens to signals: `mission_load`, `first_unit_visible`, `first_unit_selected`, `first_mission_loaded`, `first_mission_complete`.
- Maps signals → beat IDs per beats.json `trigger_event` field (replacing current `trigger_event_TBD` placeholder).
- Beat dispatch: instantiates `tutorial_overlay.tscn` (if not already in tree) → calls `show_beat(beat_id)` → on `beat_dismissed` signal advances to next.

**Existing surfaces reused:**
- `simulation/library/tutorial/beats.json` — 5 beats already authored (TUT_001-005, chronicle voice).
- `scenes/tutorial/tutorial_overlay.gd` — `show_beat()` + `hide_beat()` + anchor resolution already implemented.

### B5 — Packaging + release-mode wiring

**Windows PyInstaller spec:** `legacy/build/pyinstaller_win.spec` (NEW) — mirror Mac spec structure. Same `simulation/pipe_transport.py` entry, same 76 hidden_imports, same data files. COLLECT name: `ouroboros_sim` (binary suffix `.exe` on Windows handled by PyInstaller).

**Privacy modal:** `scenes/privacy_modal/privacy_modal.tscn` + `.gd` (NEW). Scene shows text below verbatim. Single "Accept & Continue" button → writes `user://privacy_accepted` → SceneRouter.go_to("loading_screen") (existing).

```
PRIVATE PLAYTEST BUILD

This build saves logs and crash reports to your machine.
Nothing is sent anywhere. If you hit a bug, you can choose
to send files to Westley — that's it.
```

If `user://privacy_accepted` exists on _ready() → immediately route to loading_screen (skip modal).

**Custom user dir:** `project.godot` config — `application/config/use_custom_user_dir = true`, `application/config/custom_user_dir_name = "data"`. Side-effect: logs + saves go to `<game_root>/data/` not `~/.local/share/godot/...`.

**Release-mode detection:** `autoload/theme_constants.gd:4` — replace hardcoded `const IS_RELEASE_BUILD: bool = false` with `const IS_RELEASE_BUILD: bool = OS.has_feature("release_build")`. Preset config = Westley's last-mile call before friends-ZIP cut (not in this wave).

**sim_bridge release-mode branch:** `autoload/sim_bridge.gd._spawn_sim()` — when `IS_RELEASE_BUILD`, exec `<game_root>/sim/ouroboros_sim.exe` (Win) or `<game_root>/sim/ouroboros_sim` (Mac) with `--root <game_root>` arg. Dev mode unchanged.

**DebugOverlay autoload:** `project.godot [autoload]` section — add `DebugOverlay="*res://autoload/debug_overlay.gd"`. F3-toggle already implemented in `autoload/debug_overlay.gd`.

**Main scene chain:** `project.godot` — main scene = `scenes/privacy_modal/privacy_modal.tscn`. Privacy modal → loading_screen → main_menu chain.

---

## Files in scope

### Sub-wave 3.1 (parallel, 2 leaves — first to dispatch)

| Leaf | impl_files | test_files |
|---|---|---|
| **B5-A** Windows spec + DebugOverlay autoload | `legacy/build/pyinstaller_win.spec` (NEW), `project.godot` (1-line autoload add) | `simulation/test_b5_pyinstaller_specs.py` |
| **B5-B** Privacy modal scene | `scenes/privacy_modal/privacy_modal.tscn` (NEW), `scenes/privacy_modal/privacy_modal.gd` (NEW) | `tests/test_privacy_modal.gd` |

(B2-A dropped 2026-05-26 — `OBJECTIVE_TEMPLATES_SHORT` already populates `briefing.objective` for all 10 archetypes; no sim-side work required.)

### Sub-wave 3.2 (parallel, 2 leaves — after 3.1 merges)

| Leaf | impl_files | test_files |
|---|---|---|
| **B3-A** Tutorial trigger schema + replay flag | `simulation/library/tutorial/beats.json` | `simulation/test_b3_tutorial_beats_schema.py` |
| **B2-B** Briefing scene header + mission_id flow | `scenes/mission_briefing/mission_briefing.gd`, `autoload/scene_router.gd` | `tests/test_b2_briefing_scene.gd` |

### Sub-wave 3.3 (parallel, 2 leaves — after 3.2 merges)

| Leaf | impl_files | test_files |
|---|---|---|
| **B3-B** Tutorial state machine + main menu replay | `autoload/tutorial_state_machine.gd` (NEW), `scenes/main_menu/main_menu.gd`, `scenes/tactical/tactical.gd` | `tests/test_b3_tutorial_integration.gd` |
| **B5-C** Release-mode wire-up | `project.godot` (main scene + custom user dir), `autoload/theme_constants.gd`, `autoload/sim_bridge.gd` | `tests/test_b5_release_mode.gd` |

**Cross-leaf file collision:** `project.godot` touched by B5-A (autoload section) + B5-C (main scene + custom user dir section). Serialized to different sub-waves. B5-A merges first, B5-C reads B5-A's autoload entry as starting state.

---

## Type contract

Leaf agents MAY import / reference ONLY these symbols. New symbols introduced require contract proposal (`.swarm/proposals/leaf-NN.md`).

### Python symbols (`simulation/`)

- `mission_briefing.assemble_briefing(archetype: str, slots: dict) -> dict` — existing
- `mission_briefing.SITUATION_TEMPLATES: dict[str, str]` — existing
- `mission_briefing.OBJECTIVE_TEMPLATES_SHORT: dict[str, str]` — existing; 10-archetype plain-language imperatives
- `mission_briefing.OBJECTIVE_TEMPLATES_DETAIL: dict[str, str]` — existing
- `pipe_transport._mission_setup_to_briefing(setup, sim_env, cmdr_selection) -> dict` — existing
- Existing dict key on briefing return value: `objective: str` (populated from OBJECTIVE_TEMPLATES_SHORT); B2 Godot side reads this.

### GDScript class names

- `UIDataBus` (autoload) — existing
- `SimBridgeDataSource` (autoload) — existing
- `SceneRouter` (autoload) — existing
- `ThemeConstants` (autoload) — existing
- `TacticalBridge` (autoload) — existing
- `DebugOverlay` (autoload) — registered by B5-A
- `TutorialStateMachine` (autoload) — created by B3-B
- `TutorialOverlay` (scene script class) — existing at `scenes/tutorial/tutorial_overlay.gd`

### project.godot config keys (touched)

- `application/run/main_scene` — set by B5-C
- `application/config/use_custom_user_dir` — set by B5-C
- `application/config/custom_user_dir_name` — set by B5-C
- `autoload/DebugOverlay` — set by B5-A
- `autoload/TutorialStateMachine` — set by B3-B

### Signal names (new)

- `TutorialStateMachine.beat_fired(beat_id: String)` — emitted when beat shown
- `TutorialStateMachine.tutorial_completed` — emitted on TUT_005 dismissal
- `TutorialOverlay.beat_dismissed(beat_id: String)` — already exists, leaf does not redefine

### Trigger event names (beats.json `trigger_event` field, locked)

- `mission_load` — TUT_001 (Space to pause)
- `first_unit_visible` — TUT_002 (selection)
- `first_unit_selected` — TUT_003 (movement)
- `first_mission_loaded` — TUT_004 (objectives panel)
- `first_mission_complete` — TUT_005 (chronicle)

### Persistence files (user://)

- `user://privacy_accepted` — written by B5-B
- `user://tutorial_completed` — written by B3-B (TutorialStateMachine)

---

## Acceptance criteria

### B5-A (Windows PyInstaller spec + DebugOverlay autoload)
1. `legacy/build/pyinstaller_win.spec` exists, parses as valid PyInstaller spec, has same Analysis/PYZ/EXE/COLLECT structure as Mac spec.
2. `project.godot [autoload]` block contains line `DebugOverlay="*res://autoload/debug_overlay.gd"`.
3. Test `simulation/test_b5_pyinstaller_specs.py`: both `legacy/build/pyinstaller_spec.spec` and `legacy/build/pyinstaller_win.spec` parse; specs declare same hidden_imports + data files; binary name `ouroboros_sim`.

### B5-B (Privacy modal scene)
1. `scenes/privacy_modal/privacy_modal.tscn` exists; loads in Godot without parse error.
2. Scene shows the 4-paragraph text verbatim.
3. Single "Accept & Continue" button → writes `user://privacy_accepted` → calls `SceneRouter.go_to("loading_screen")`.
4. `_ready()` checks `FileAccess.file_exists("user://privacy_accepted")` → if true, immediately routes to loading_screen without showing modal.
5. Test `tests/test_b3_privacy_modal.gd` (headless): scene instantiates, button click writes flag, flag-exists path skips modal.

### B2-A (DROPPED 2026-05-26)
Sim-side `OBJECTIVE_TEMPLATES_SHORT` already populates `briefing.objective` for all 10 archetypes. No leaf needed.

### B3-A (Tutorial trigger schema + beats.json wiring)
1. Each beat in `simulation/library/tutorial/beats.json` has `trigger_event` field (replacing `trigger_event_TBD`) matching trigger names locked in Type contract.
2. JSON schema validation: id (string), trigger_event (string from allowlist), headline (string), body (string), pointed_anchor (string), accent_hint (string).
3. Test `simulation/test_b3_tutorial_beats_schema.py`: loads beats.json, validates each beat has all 6 fields, trigger_event matches one of 5 locked names.

### B2-B (Briefing scene header)
1. `scenes/mission_briefing/mission_briefing.gd` adds RichTextLabel node `short_objective_header` above MISSION OBJECTIVES section (line 202 reference).
2. Header style: era-active accent color via existing `_accent` member (line 11 pattern: `ThemeConstants.get_era_accent(_data.get("era_id", "roman"))`). Apply via theme color override OR BBCode `[color=#<_accent.to_html(false)>][b]<TEXT-UPPERCASE>[/b][/color]` with font size ≥1.5× body text.
3. Reads `objective` key from briefing dict (existing field, populated sim-side from `OBJECTIVE_TEMPLATES_SHORT`). If field missing/empty → header `visible = false`.
4. `autoload/scene_router.gd` mission_briefing route accepts `mission_id` param + passes through to scene's `setup(params)`. (Already supports `params: Dictionary = {}` per line 35 — verify no further change needed.)
5. Test `tests/test_b2_briefing_scene.gd` (headless): instantiate scene w/ mock briefing dict (objective set), verify header label has correct text + style; second pass w/ missing objective → header hidden.

### B3-B (Tutorial state machine + main menu replay)
1. `autoload/tutorial_state_machine.gd` exists, registered in project.godot autoload.
2. `_ready()` checks `FileAccess.file_exists("user://tutorial_completed")` → sets `_completed = true` if so.
3. On signals matching locked trigger events → if `_completed == false`, instantiates TutorialOverlay (if absent), calls `show_beat(beat_id)`.
4. On `beat_dismissed(TUT_005)` → writes `user://tutorial_completed`, sets `_completed = true`, emits `tutorial_completed`.
5. `scenes/main_menu/main_menu.gd` adds "Replay Tutorial" button → on press: deletes `user://tutorial_completed` via DirAccess + calls `TutorialStateMachine.reset_for_replay()`.
6. `scenes/tactical/tactical.gd` emits `first_unit_visible` after first sim_state populates units; emits `first_unit_selected` after first unit selection input.
7. Test `tests/test_b3_tutorial_integration.gd` (headless): fresh state (no flag file) → fire `mission_load` signal → overlay shows TUT_001 → dismiss → TUT_002 etc → after TUT_005 dismissal flag file exists; re-fire `mission_load` → no overlay; replay path resets flag → overlay re-fires.

### B5-C (Release-mode wire-up)
1. `project.godot` main scene set to `scenes/privacy_modal/privacy_modal.tscn`.
2. `project.godot` has `application/config/use_custom_user_dir=true` + `application/config/custom_user_dir_name="data"`.
3. `autoload/theme_constants.gd:4` — `const IS_RELEASE_BUILD: bool = OS.has_feature("release_build")`.
4. `autoload/sim_bridge.gd._spawn_sim()` — branch on `ThemeConstants.IS_RELEASE_BUILD`: if true, exec `<game_root>/sim/ouroboros_sim` (`.exe` on Windows) with `--root <game_root>`; else existing dev path unchanged.
5. Test `tests/test_b5_release_mode.gd` (headless): theme_constants reads OS.has_feature correctly under test harness; sim_bridge release-mode branch composes correct argv structure (mock OS.execute_with_pipe).

---

## Out of scope

- Region-click-to-mission UI (not a game feature — missions auto-advance via `proceed_to_next_mission()`).
- B4 PAN_SPEED retune (1-line constant, post-Westley-playthrough).
- B6 tactical mid-mission save (depends on B3 pause menu surface; separate wave).
- Multi-stage hallmark-era tutorial (bible_monetization.md component 8 — deferred post-launch).
- Steam launch tasks S#1-S#7 (separate batch).
- Visual polish 2.5D layering pass.
- Tutorial content authoring beyond existing 5 beats (TUT_001-005 already in beats.json).
- Export preset configuration (`export_presets.cfg`) — Westley's last-mile call.

---

## Subagent framing prefix (REQUIRED on every Wave 3 leaf brief)

> Game = pause-and-command tactical w/ generational chronicle. Player commands troops mid-mission (tactical layer) + watches civilization rise/fall via auto-advancing chronicle (world layer). Missions auto-trigger post-time-jump — no manual mission selection from world map. NOT an RTS. NOT a 4X. Phase 1 reframe doc: `/Users/westley/.claude/plans/synchronous-stargazing-widget.md` + `docs/bible/game_bible.md ## In Flux ### PIVOT 2026-05-18`.

---

## Umbrella test

`simulation/test_wave3_blockers_umbrella.py` (Python side) — RED before any leaf, GREEN after all 7 leaves merge. Encodes parent-owned end-to-end gate. Assertions:

1. B5-A: `legacy/build/pyinstaller_win.spec` exists + parses; project.godot DebugOverlay autoload line present.
2. B5-B: privacy_modal scene file exists; gd script defines `_on_accept_pressed` handler that calls FileAccess.
3. B2-A: import `simulation.mission_briefing` → assert all 10 templates have `short_objective`; assert `assemble_briefing` return contains the key.
4. B3-A: load beats.json → assert 5 beats, all have `trigger_event` field from locked allowlist.
5. B2-B: grep `scenes/mission_briefing/mission_briefing.gd` for `short_objective_header` node + BBCode style.
6. B3-B: grep `autoload/tutorial_state_machine.gd` for signal handlers matching all 5 trigger events.
7. B5-C: parse project.godot — assert main_scene=privacy_modal, custom_user_dir=true, custom_user_dir_name="data"; grep theme_constants.gd for `OS.has_feature("release_build")`.

`tests/test_wave3_blockers_umbrella.gd` (Godot headless) — companion umbrella, exercises scene loading paths:
1. Privacy modal scene instantiates without error.
2. Mission briefing scene instantiates with mock short_objective → header visible.
3. Tutorial overlay scene loads first beat via TutorialStateMachine.
4. Main menu scene shows Replay Tutorial button.

Source-grep assertions in Python umbrella per `cover_asteroid_los_spec.md` precedent — leaf agents can't fake them without actually wiring code.

---

## Execution order

1. Author `simulation/test_wave3_blockers_umbrella.py` + `tests/test_wave3_blockers_umbrella.gd`. Confirm RED.
2. Initialize `.swarm/wave-3.SWEEP.md` (placeholder until first per-leaf ASSUMPTIONS land) + `.swarm/wave-3.snapshot.json`.
3. `/swarm` reads this spec → emits Sub-wave 3.1 briefs (B5-A, B5-B, B2-A).
4. `/swarm-review` audits 3.1 briefs.
5. Westley approves → dispatch 3.1 leaves in parallel (hardened anti-bypass + framing prefix).
6. `/swarm-merge` per leaf as they return GREEN.
7. After 3.1 merged: emit 3.2 briefs (B3-A, B2-B) → review → approve → dispatch → merge.
8. After 3.2 merged: emit 3.3 briefs (B3-B, B5-C) → review → approve → dispatch → merge.
9. Run umbrella → GREEN.
10. Apex E2E pass.
11. Westley manual playthrough sign-off.
12. Cut friends-ZIP.
