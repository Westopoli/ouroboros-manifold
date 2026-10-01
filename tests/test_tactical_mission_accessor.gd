extends SceneTree

# A6 follow-up C5-N (docs/northstar/plans/2026-10-01-architect-rulings.md "A6 follow-ups" 3):
# autoload/c_bridge.gd has a public mission() -> Dictionary, the running mission's
# frame; the tactical HUD reads it instead of reaching into the private
# _session_mission. Proves R-103-02 (HUD objective line) is fed through the accessor.
const CBridge := preload("res://autoload/c_bridge.gd")
const VIEW_SOURCE := "res://scenes/tactical_c/tactical_view.gd"

var _pass_count := 0
var _fail_count := 0
var _fail_msgs: Array[String] = []


func _initialize() -> void:
	_run_tests()
	print("\n=== Mission Accessor Test Results ===")
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
	var SimSession = load("res://autoload/sim_session.gd")
	SimSession.reset()
	var bridge = SimSession.bridge()
	_assert(bridge.has_method("mission"), "c_bridge.gd has no public mission() accessor")
	if bridge.has_method("mission"):
		_assert(bridge.load_mission_live(1, CBridge.DEFAULT_N_REGIONS, CBridge.DEFAULT_FEATURES),
			"setup: load_mission_live failed: %s" % bridge.last_error())
		var m: Dictionary = bridge.mission()
		_assert(not m.is_empty(), "mission() is empty on a live mission")
		_assert(m.get("objectives", null) is Array and not (m["objectives"] as Array).is_empty(),
			"mission() on a live mission carries no objectives")
		_assert(m == bridge.get("_session_mission"), "mission() differs from the running mission's frame")
		bridge.close_session()
	var src := FileAccess.get_file_as_string(VIEW_SOURCE)
	_assert(src != "", "cannot read " + VIEW_SOURCE)
	_assert(src.find("_session_mission") == -1,
		"tactical_view.gd still reaches into the private _session_mission instead of bridge.mission()")
