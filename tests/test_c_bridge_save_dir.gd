extends SceneTree

# Piece C1-3: the save directory is redirectable. autoload/c_bridge.gd saves_dir()
# reads the OM_SAVE_DIR environment variable (an absolute path) and falls back to the
# game's user://saves; QA runs (tests/qa/desktop, scripts/qa_harness.sh) point it at a
# per-run temp directory so CI machines and a developer's desktop do not accumulate
# campaign_1 saves. Autosave (R-111-01) and list_saves both follow it.

var _pass_count := 0
var _fail_count := 0
var _fail_msgs: Array[String] = []
var _completed := false


func _initialize() -> void:
	_run_tests()
	_assert(_completed, "the save-dir checks did not run to the end (a script error aborted them)")
	print("\n=== C Bridge Save Dir Test Results ===")
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


func _run_tests() -> void:
	var CBridge = load("res://autoload/c_bridge.gd")
	var bridge = CBridge.new()

	OS.set_environment("OM_SAVE_DIR", "")
	var default_dir: String = bridge.saves_dir()
	_assert(default_dir == ProjectSettings.globalize_path("user://saves"),
		"with OM_SAVE_DIR unset saves_dir() = %s, expected the user://saves path (control)" % default_dir)

	var tmp := OS.get_user_data_dir().path_join("c1_3_test_saves_%d" % Time.get_ticks_usec())
	OS.set_environment("OM_SAVE_DIR", tmp)
	var redirected: String = bridge.saves_dir()
	_assert(redirected == tmp, "OM_SAVE_DIR=%s but saves_dir() = %s" % [tmp, redirected])
	_assert(DirAccess.dir_exists_absolute(tmp), "saves_dir() did not create the redirected directory")

	_assert(bridge.load_mission_live(1, CBridge.DEFAULT_N_REGIONS, CBridge.DEFAULT_FEATURES), "load_mission_live failed: %s" % bridge.last_error())
	_assert(FileAccess.file_exists(tmp.path_join("campaign_1.omsave")), "the autosave did not land in OM_SAVE_DIR")
	var rows: Array = bridge.list_saves()
	_assert(rows.size() == 1 and rows[0].get("slot") == "campaign_1", "list_saves() under OM_SAVE_DIR = %s, expected exactly campaign_1" % str(rows))
	_assert(not FileAccess.file_exists(default_dir.path_join("campaign_c1_3_marker.omsave")), "control: stray marker file in the default save dir")
	bridge.close_session()

	for f in DirAccess.get_files_at(tmp):
		DirAccess.remove_absolute(tmp.path_join(f))
	DirAccess.remove_absolute(tmp)
	OS.set_environment("OM_SAVE_DIR", "")
	_completed = true
