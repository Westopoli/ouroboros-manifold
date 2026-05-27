extends SceneTree

var _pass_count := 0
var _fail_count := 0
var _fail_msgs: Array[String] = []


func _initialize() -> void:
	_run_tests()
	print("\n=== B5 Release Mode Test Results ===")
	print("PASS: %d  FAIL: %d" % [_pass_count, _fail_count])
	if _fail_count > 0:
		print("Failures:")
		for msg in _fail_msgs:
			print("  - " + msg)
		print("=== RED ===\n")
		quit(1)
	else:
		print("=== GREEN ===\n")
		quit(0)


func _assert(cond: bool, msg: String) -> void:
	if cond:
		_pass_count += 1
	else:
		_fail_count += 1
		_fail_msgs.append(msg)


func _read_file(path: String) -> String:
	var abs := ProjectSettings.globalize_path(path) if path.begins_with("res://") else path
	var f := FileAccess.open(abs, FileAccess.READ)
	if f == null:
		return ""
	var txt := f.get_as_text()
	f.close()
	return txt


func _run_tests() -> void:
	var main_scene = ProjectSettings.get_setting("application/run/main_scene")
	_assert(str(main_scene) == "res://scenes/privacy_modal/privacy_modal.tscn",
		"main_scene mismatch, got: " + str(main_scene))

	var use_custom = ProjectSettings.get_setting("application/config/use_custom_user_dir")
	_assert(bool(use_custom) == true,
		"use_custom_user_dir should be true, got: " + str(use_custom))

	var dir_name = ProjectSettings.get_setting("application/config/custom_user_dir_name")
	_assert(str(dir_name) == "data",
		"custom_user_dir_name should be 'data', got: " + str(dir_name))

	# Autoload-presence check via project.godot grep (SceneTree --script harness
	# does not load autoloads — verified via leaf-02/05/06 MERGE_ASSUMPTIONS).
	# Behavioral autoload-accessible verification deferred to apex E2E + manual playthrough.
	var pg_src := _read_file("res://project.godot")
	_assert(pg_src.find("ThemeConstants=\"*res://autoload/theme_constants.gd\"") >= 0,
		"ThemeConstants autoload registration missing from project.godot")

	var tc_src := _read_file("res://autoload/theme_constants.gd")
	_assert(tc_src.find("OS.has_feature(\"release_build\")") >= 0,
		"theme_constants.gd missing OS.has_feature(\"release_build\")")

	var sb_src := _read_file("res://autoload/sim_bridge.gd")
	_assert(sb_src.find("IS_RELEASE_BUILD") >= 0 or sb_src.find("release_build") >= 0,
		"sim_bridge.gd missing IS_RELEASE_BUILD / release_build reference")
	_assert(sb_src.find("--root") >= 0,
		"sim_bridge.gd missing --root literal")
	_assert(sb_src.find("OS.has_feature(\"windows\")") >= 0 or sb_src.find(".exe") >= 0,
		"sim_bridge.gd missing windows platform detection")
	_assert(sb_src.find("OS.get_executable_path()") >= 0,
		"sim_bridge.gd missing OS.get_executable_path() for game_root resolution")
	_assert(sb_src.find("ouroboros_sim") >= 0,
		"sim_bridge.gd missing ouroboros_sim binary reference")
