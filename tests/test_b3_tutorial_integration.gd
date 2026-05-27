extends SceneTree

const TSM_PATH := "res://autoload/tutorial_state_machine.gd"
const MAIN_MENU_PATH := "res://scenes/main_menu/main_menu.gd"
const TACTICAL_PATH := "res://scenes/tactical/tactical.gd"
const PROJECT_GODOT_PATH := "res://project.godot"
const BEATS_PATH := "res://simulation/library/tutorial/beats.json"

var failures: Array[String] = []


func _read(path: String) -> String:
	if not FileAccess.file_exists(path):
		return ""
	var f := FileAccess.open(path, FileAccess.READ)
	if f == null:
		return ""
	var s := f.get_as_text()
	f.close()
	return s


func _expect(cond: bool, msg: String) -> void:
	if not cond:
		failures.append(msg)


func _initialize() -> void:
	var tsm_src := _read(TSM_PATH)
	_expect(tsm_src != "", "tutorial_state_machine.gd source not readable")

	for trigger in ["mission_load", "first_unit_visible", "first_unit_selected", "first_mission_loaded", "first_mission_complete"]:
		_expect(tsm_src.find(trigger) != -1, "tsm missing trigger event reference: %s" % trigger)

	_expect(tsm_src.find("_completed") != -1, "tsm missing _completed field")
	_expect(tsm_src.find("user://tutorial_completed") != -1, "tsm missing user://tutorial_completed flag path literal")
	_expect(tsm_src.find("func reset_for_replay") != -1, "tsm missing reset_for_replay() method")
	_expect(tsm_src.find("signal beat_fired") != -1, "tsm missing beat_fired signal")
	_expect(tsm_src.find("signal tutorial_completed") != -1, "tsm missing tutorial_completed signal")
	_expect(tsm_src.find("FileAccess.file_exists") != -1, "tsm missing flag file check")
	_expect(tsm_src.find("show_beat") != -1, "tsm not invoking overlay show_beat")

	var menu_src := _read(MAIN_MENU_PATH)
	_expect(menu_src != "", "main_menu.gd source not readable")
	_expect(menu_src.find("Button.new()") != -1, "main_menu missing Button instantiation")
	var menu_lower := menu_src.to_lower()
	_expect(menu_lower.find("tutorial") != -1, "main_menu missing tutorial-related Button text")
	_expect(menu_src.find("reset_for_replay") != -1, "main_menu missing reset_for_replay call wiring")
	_expect(menu_src.find("version.text = \"v0.9.0\"") != -1, "main_menu version label displaced")

	var tactical_src := _read(TACTICAL_PATH)
	_expect(tactical_src != "", "tactical.gd source not readable")
	_expect(tactical_src.find("first_unit_visible") != -1, "tactical.gd missing first_unit_visible reference")
	_expect(tactical_src.find("first_unit_selected") != -1, "tactical.gd missing first_unit_selected reference")
	_expect(tactical_src.find("TutorialStateMachine") != -1, "tactical.gd not routing to TutorialStateMachine")

	var pg_src := _read(PROJECT_GODOT_PATH)
	_expect(pg_src != "", "project.godot source not readable")
	_expect(pg_src.find("TutorialStateMachine=\"*res://autoload/tutorial_state_machine.gd\"") != -1, "project.godot missing TutorialStateMachine autoload entry")
	_expect(pg_src.find("DebugOverlay=\"*res://autoload/debug_overlay.gd\"") != -1, "project.godot lost leaf-01 DebugOverlay autoload entry")

	var beats_src := _read(BEATS_PATH)
	_expect(beats_src != "", "beats.json source not readable")
	_expect(beats_src.find("trigger_event_TBD") == -1, "beats.json still has _TBD placeholder (leaf-04 precondition not met)")

	var tsm_node := get_root().get_node_or_null("TutorialStateMachine")
	_expect(tsm_node != null, "TutorialStateMachine autoload not reachable via /root (project.godot autoload entry may not be active in this harness)")
	if tsm_node != null:
		_expect(tsm_node.has_method("reset_for_replay"), "TutorialStateMachine missing reset_for_replay() at runtime")
		_expect(tsm_node.has_signal("beat_fired"), "TutorialStateMachine missing beat_fired signal at runtime")
		_expect(tsm_node.has_signal("tutorial_completed"), "TutorialStateMachine missing tutorial_completed signal at runtime")

	if failures.is_empty():
		print("test_b3_tutorial_integration: PASS")
		quit(0)
	else:
		print("test_b3_tutorial_integration: FAIL")
		for f in failures:
			print("  - %s" % f)
		quit(1)
