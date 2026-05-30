# leaf-07 assumptions

## A1: bash test runner blocked
`bash scripts/run_godot_tests.sh` denied by harness perms (same as leaf-02/05/06). RED→GREEN proof not runnable in this session. Static-equivalence sub:
- Staged test source-greps impl files for required tokens (release_build, --root, ouroboros_sim, OS.has_feature("windows"), OS.get_executable_path, IS_RELEASE_BUILD).
- Staged impl files contain all required tokens (verified via Grep tool).
- ProjectSettings assertions independent of --script SceneTree _ready deferral quirk per leaf-02/05 MERGE_ASSUMPTIONS guidance (ProjectSettings parsed at engine init).
- Parent re-runs at merge gate.

## A2: game_root resolution
Used `OS.get_executable_path().get_base_dir()` per brief U-8. Returns directory containing Godot game binary in packaged build. In dev mode this branch is gated behind `IS_RELEASE_BUILD == false`, so dev path unaffected.

## A3: Windows binary suffix detection
Used `OS.has_feature("windows")` ternary on `bin_name`. Mac/Linux fall through to bare `ouroboros_sim`. PyInstaller `.exe` suffix matches build/pyinstaller_win.spec convention (leaf-01).

## A4: --root arg position
Appended `--root <game_root>` at end of release-mode args (after --save-root). pipe_transport.py line 1283 parses via `sys.argv.index("--root") + 1`, position-agnostic. Confirmed.

## A5: python3 fallback only in dev
Original code had `python` fallback after `python3` fail. Preserved only for dev path. Release path has single exec target (compiled binary); no python fallback applies.

## A6: project.godot sibling-wave merge state
Real `project.godot` already has DebugOverlay (leaf-01, wave 1, merged) AND TutorialStateMachine (leaf-06, wave 3, merged into HEAD before this session). Staged project.godot preserves ALL existing autoload entries verbatim. Only `[application]` section modified — `run/main_scene` swapped to privacy_modal.tscn; `config/use_custom_user_dir=true` + `config/custom_user_dir_name="data"` inserted after main_scene. `[display]`, `[physics]`, `[rendering]` untouched.

## A7: source-grep test pattern over behavioral assertions
Per leaf-02 + leaf-05 + leaf-06 MERGE_ASSUMPTIONS, --script SceneTree harness defers _ready and has cross-tick FileAccess quirks. Test uses ProjectSettings.get_setting (parsed at engine init, no deferral issue) + FileAccess.get_as_text source-grep on impl files (single-frame, no add_child/await). One autoload node lookup retained (`get_root().get_node_or_null("ThemeConstants")`) — flagged as flaky per leaf-06 A2; downgradable to source-grep at merge gate if harness doesn't load autoload.

## A8: function signature preservation
`_spawn_sim(extra_args: PackedStringArray = PackedStringArray()) -> void:` unchanged at line 116. Only function body modified. `restart_with_load` + `restart` + `_ready` callers unaffected (they pass PackedStringArray as before).

## A9: ENTITLEMENT_SETTLED_REACH + USE_LIVE_SIM + SIM_SCRIPT_PATH + SIM_UNITS_PER_SIDE consts preserved
All sim_bridge.gd const declarations + signals + member vars + every other method (_reader_loop, _read_framed, _dispatch, _route_to_error_screen, send_command, _kill_sim, restart, _notification) byte-identical to repo HEAD. Only `_spawn_sim` body changed.

## A10: traceability comment added
sim_bridge.gd `_spawn_sim` release-mode branch has comment block citing theme_constants.gd IS_RELEASE_BUILD source-of-truth + pipe_transport.py line 1283 `--root` parsing. Per CLAUDE.md traceability rule.
