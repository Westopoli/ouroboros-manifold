# leaf-06 assumptions

## A1: Bash test runner blocked

`bash scripts/run_godot_tests.sh tests/test_b3_tutorial_integration.gd` denied by harness perms (same operational gap as leaf-02/leaf-05). RED→GREEN proof unrunnable in this session. Parent re-runs at merge gate. Static-equivalence sub:

- Staged test uses source-grep verification of impl wiring per leaf-02/leaf-05 MERGE_ASSUMPTIONS guidance (SceneTree --script harness defers `_ready()` post-`_initialize`, behavioral cross-frame assertions race).
- One runtime probe retained: `get_root().get_node_or_null("TutorialStateMachine")` to confirm autoload registration loads under the harness. If autoload not loaded by `--script` SceneTree (similar to leaf-02 SceneRouter pattern), this assertion may need to be downgraded to source-grep of `project.godot` at merge gate. Pre-emptive note: this is allowed to be flaky; parent decides.

## A2: beats.json dict-shape adopted from leaf-04

Iteration via `for beat_id in _beats: var beat = _beats[beat_id]` per leaf-04.ASSUMPTIONS A1. Mapping built via `trigger_event` field on each beat dict, NOT positional list index. Verified beats.json has 5 dict entries (TUT_001..TUT_005) with trigger_event populated (no _TBD placeholders).

## A3: first_unit_selected signal source — polling fallback

No `selection_changed` signal exists on `scenes/tactical/input_router.gd`. Selection state held in `selected_uids: Array[int]` member, mutated by `_click_select`/`_box_select`/`_double_click_select`/`_select_all_army`. Two routes considered:

1. Patch input_router.gd to emit `selection_changed` signal. REJECTED: input_router.gd not in leaf-06 impl_files allowlist (would expand scope beyond brief).
2. Poll `$InputRouter.selected_uids.size() > 0` from tactical.gd `_process()` with `_emitted_first_unit_selected` member flag. ADOPTED: minimal-diff, stays inside impl_files contract.

Polling cost: one `get_node_or_null("InputRouter")` + one `Array.size()` per frame until flag flips, then guard short-circuits. Negligible.

## A4: first_unit_visible emission site

Per brief instruction, fire from inside `_on_first_snapshot` after `TacticalBridge.units.size() > 0` check. Existing `CONNECT_ONE_SHOT` ensures `_on_first_snapshot` runs once; member flag `_emitted_first_unit_visible` adds belt-and-suspenders against re-entry.

## A5: tutorial overlay instantiation as autoload child

`TutorialStateMachine._ensure_overlay()` calls `get_tree().get_root().add_child(_overlay)` to put overlay under /root (above all scenes, persists across scene transitions). Alternative — add to current scene — REJECTED because tutorial spans main_menu→loading→briefing→tactical→debrief lifecycle and the autoload must outlive any single scene. Side effect: overlay z-order is on top of whichever scene is active. Acceptable per spec intent (tutorial cards modal-style).

## A6: handle_trigger() as public API, not signal hookup

Spec brief says "Listen for these signals". Two routes considered:

1. Define a global signal bus, have emitters call `Bus.first_unit_visible.emit()`, have TSM listen. REJECTED: no existing signal-bus pattern in codebase; would create new infrastructure outside scope.
2. Public method `handle_trigger(trigger_event: String)` on TSM, callers invoke directly. ADOPTED: minimal, no new infrastructure, matches the brief's "listen for these signals (per locked allowlist)" intent since the trigger names ARE the contract.

Future signal-bus refactor can swap method calls for signal emissions without changing TSM contract.

## A7: reset_for_replay() deletes via DirAccess.remove_absolute(globalize_path)

Per brief instruction. `globalize_path("user://tutorial_completed")` resolves to the platform-specific user-data path (e.g. macOS `~/Library/Application Support/Godot/app_userdata/Ouroboros/tutorial_completed`). Sibling leaf-07 will add `config/use_custom_user_dir=true` + `custom_user_dir_name="data"` later, redirecting user:// to `<game_root>/data/`. `globalize_path` honors this transparently — no leaf-06 change needed when leaf-07 lands.

## A8: project.godot stage minimal-touch

Staged project.godot is byte-identical to repo HEAD except for one inserted line in `[autoload]` section: `TutorialStateMachine="*res://autoload/tutorial_state_machine.gd"` appended after `DebugOverlay` (leaf-01 entry). No changes to `[application]`, `[display]`, `[physics]`, `[rendering]`, or other autoload entries. Leaf-07 will add `[application]` keys; merger combines.

## A9: Main menu Button placement

Replay Tutorial button added as direct child of menu Control (sibling of `version` label), positioned via `PRESET_BOTTOM_LEFT` with negative offsets to sit in bottom-left corner. Does not enter the `content` VBoxContainer (would push existing items + interfere with entrance animation stagger). Standalone child, no interference with NEW GAME / CONTINUE / version layout.
