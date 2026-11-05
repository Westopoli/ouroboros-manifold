extends SceneTree

# Wave 3 Pre-Zip Wiring Godot-side umbrella test.
# Encodes top-level acceptance criteria from `docs/legacy/test_specs/wave_3_pre_zip_wiring.md`
# that require Godot scene-tree / autoload instantiation to verify behaviorally.
# Initially RED. Goes GREEN only after all 7 leaves (B5-A, B5-B, B2-A, B3-A, B2-B, B3-B, B5-C) merge.
#
# DO NOT EDIT leaf-by-leaf. Parent-owned end-to-end gate.
# Runs headless via `scripts/run_godot_tests.sh tests/test_wave3_blockers_umbrella.gd`.

var _pass_count := 0
var _fail_count := 0
var _fail_msgs: Array[String] = []


func _initialize() -> void:
	_run_tests()
	print("\n=== Wave 3 Blockers Umbrella Results ===")
	print("PASS: %d  FAIL: %d" % [_pass_count, _fail_count])
	if _fail_count > 0:
		print("Failures:")
		for msg in _fail_msgs:
			print("  - " + msg)
		print("=== UMBRELLA RED ===\n")
		quit(1)
	else:
		print("=== UMBRELLA GREEN ===\n")
		quit(0)


func _assert(cond: bool, msg: String) -> void:
	if cond:
		_pass_count += 1
	else:
		_fail_count += 1
		_fail_msgs.append(msg)


func _run_tests() -> void:
	# ---------------------------------------------------------------------
	# B5-B — Privacy modal scene loads + has accept button + privacy text
	# ---------------------------------------------------------------------
	var privacy_scene_path := "res://scenes/privacy_modal/privacy_modal.tscn"
	var privacy_scene = load(privacy_scene_path) if ResourceLoader.exists(privacy_scene_path) else null
	_assert(privacy_scene != null,
		"B5-B not landed: privacy_modal.tscn missing or fails to load")

	if privacy_scene != null:
		var privacy_node = privacy_scene.instantiate()
		_assert(privacy_node != null,
			"B5-B: privacy_modal scene failed to instantiate")
		if privacy_node != null:
			get_root().add_child(privacy_node)
			var has_accept_btn := _find_button_by_text(privacy_node, "Accept") != null \
				or _find_button_by_text(privacy_node, "Continue") != null
			_assert(has_accept_btn,
				"B5-B: privacy_modal scene missing Accept/Continue button")
			var has_privacy_text := _find_text_containing(privacy_node, "PRIVATE PLAYTEST BUILD") != null
			_assert(has_privacy_text,
				"B5-B: privacy_modal scene missing 'PRIVATE PLAYTEST BUILD' text")
			privacy_node.queue_free()

	# ---------------------------------------------------------------------
	# B3-B — TutorialStateMachine autoload available + has API
	# ---------------------------------------------------------------------
	var tsm = get_root().get_node_or_null("TutorialStateMachine")
	_assert(tsm != null,
		"B3-B not landed: TutorialStateMachine autoload not registered or accessible")

	if tsm != null:
		_assert(tsm.has_method("reset_for_replay"),
			"B3-B: TutorialStateMachine missing reset_for_replay() method")
		_assert(tsm.has_signal("beat_fired"),
			"B3-B: TutorialStateMachine missing beat_fired signal")
		_assert(tsm.has_signal("tutorial_completed"),
			"B3-B: TutorialStateMachine missing tutorial_completed signal")

	# ---------------------------------------------------------------------
	# B5-A — DebugOverlay autoload registered
	# ---------------------------------------------------------------------
	var dbg = get_root().get_node_or_null("DebugOverlay")
	_assert(dbg != null,
		"B5-A not landed: DebugOverlay autoload not registered (project.godot missing entry)")

	# ---------------------------------------------------------------------
	# B2-B — Mission briefing scene exposes short_objective_header
	# ---------------------------------------------------------------------
	var briefing_scene_path := "res://scenes/mission_briefing/mission_briefing.tscn"
	var briefing_scene = load(briefing_scene_path) if ResourceLoader.exists(briefing_scene_path) else null
	_assert(briefing_scene != null,
		"B2-B: mission_briefing.tscn fails to load (existing scene)")

	if briefing_scene != null:
		var briefing_node = briefing_scene.instantiate()
		if briefing_node != null:
			get_root().add_child(briefing_node)
			var header = briefing_node.find_child("short_objective_header", true, false)
			_assert(header != null,
				"B2-B not landed: briefing scene missing short_objective_header node")
			briefing_node.queue_free()

	# ---------------------------------------------------------------------
	# B3-B — Main menu has Replay Tutorial button
	# ---------------------------------------------------------------------
	var menu_scene_path := "res://scenes/main_menu/main_menu.tscn"
	var menu_scene = load(menu_scene_path) if ResourceLoader.exists(menu_scene_path) else null
	if menu_scene != null:
		var menu_node = menu_scene.instantiate()
		if menu_node != null:
			get_root().add_child(menu_node)
			var replay_btn = _find_button_by_text(menu_node, "Replay Tutorial")
			if replay_btn == null:
				replay_btn = _find_button_by_text(menu_node, "Tutorial")
			_assert(replay_btn != null,
				"B3-B not landed: main_menu scene missing Replay Tutorial button")
			menu_node.queue_free()

	# ---------------------------------------------------------------------
	# B5-C — Project config: main scene + custom user dir + release flag
	# ---------------------------------------------------------------------
	var main_scene_setting: String = ProjectSettings.get_setting("application/run/main_scene", "")
	_assert(main_scene_setting == "res://scenes/privacy_modal/privacy_modal.tscn",
		"B5-C not landed: project main_scene must be privacy_modal.tscn, got " + main_scene_setting)

	var use_custom_dir: bool = ProjectSettings.get_setting("application/config/use_custom_user_dir", false)
	_assert(use_custom_dir,
		"B5-C not landed: application/config/use_custom_user_dir must be true")

	var custom_dir_name: String = ProjectSettings.get_setting("application/config/custom_user_dir_name", "")
	_assert(custom_dir_name == "data",
		"B5-C not landed: application/config/custom_user_dir_name must be 'data', got " + custom_dir_name)

	var theme_const = get_root().get_node_or_null("ThemeConstants")
	_assert(theme_const != null,
		"B5-C: ThemeConstants autoload not accessible (regression check)")

	# ---------------------------------------------------------------------
	# Cross-leaf infra: user:// persistence sanity
	# ---------------------------------------------------------------------
	var test_path := "user://_wave3_umbrella_sentinel.tmp"
	var f := FileAccess.open(test_path, FileAccess.WRITE)
	_assert(f != null,
		"infra: cannot write to user:// — environment broken")
	if f != null:
		f.store_string("sentinel")
		f.close()
		_assert(FileAccess.file_exists(test_path),
			"infra: user:// write succeeded but file_exists returns false")
		DirAccess.remove_absolute(ProjectSettings.globalize_path(test_path))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


func _find_button_by_text(root: Node, needle: String) -> Node:
	if root is Button:
		var btn := root as Button
		if btn.text.findn(needle) >= 0:
			return btn
	for child in root.get_children():
		var found := _find_button_by_text(child, needle)
		if found != null:
			return found
	return null


func _find_text_containing(root: Node, needle: String) -> Node:
	if root is Label:
		var lbl := root as Label
		if lbl.text.findn(needle) >= 0:
			return lbl
	if root is RichTextLabel:
		var rtl := root as RichTextLabel
		if rtl.text.findn(needle) >= 0:
			return rtl
		if rtl.get_parsed_text().findn(needle) >= 0:
			return rtl
	for child in root.get_children():
		var found := _find_text_containing(child, needle)
		if found != null:
			return found
	return null
