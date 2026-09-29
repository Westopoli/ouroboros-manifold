extends SceneTree

# Piece G-uidatabus-1 (docs/northstar/plans/2026-09-28-gap-fix-and-migration-plan.md
# G1): autoload/ui_data_bus.gd's trigger_autosave() is supposed to route
# through SimSession (the live pipe session every scene shares,
# autoload/sim_session.gd) instead of the dead SimBridge autoload
# (autoload/sim_bridge.gd, the retired Python-era bridge). The wanted body:
#   func trigger_autosave(loop_phase: String) -> void:
#       SimSession.bridge()._autosave()
# c_bridge.gd's _autosave() (autoload/c_bridge.gd) already writes
# campaign_<seed>.omsave under saves_dir() and is already called
# automatically after mission_start/mission_end/jump; this only wires the
# UI-facing trigger to that same mechanism.
#
# Two checks:
#   1. Static: the source text of trigger_autosave()'s function body (the
#      slice between "func trigger_autosave" and the next "func ") must not
#      mention SimBridge anywhere. Red today: the current body branches on
#      SimBridge.USE_LIVE_SIM and calls SimBridge.send_command.
#   2. Live: open a real pipe session through SimSession.bridge(), call
#      UIDataBus.trigger_autosave(), and check a save file actually landed
#      under the bridge's saves_dir(). Red today: mock mode (SimBridge.
#      USE_LIVE_SIM false in a headless test run with no live sim wired up)
#      only prints and writes nothing.

const SOURCE_PATH := "res://autoload/ui_data_bus.gd"
const FUNC_NAME := "trigger_autosave"
const LIVE_SEED := 90210

var _pass_count := 0
var _fail_count := 0
var _fail_msgs: Array[String] = []
var _completed := false


func _initialize() -> void:
	await _run_tests()
	_assert(_completed, "the ui_data_bus checks did not run to the end (a script error aborted them)")
	print("\n=== UI Data Bus Test Results ===")
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


# Isolates the text of a single top-level function so an assertion about it
# cannot accidentally match a different function or a comment elsewhere in
# the file.
func _function_body(text: String, func_name: String) -> String:
	var header := "func " + func_name
	var start := text.find(header)
	if start == -1:
		return ""
	var body_start := text.find("\n", start) + 1
	var next_func := text.find("\nfunc ", body_start)
	if next_func == -1:
		next_func = text.length()
	return text.substr(body_start, next_func - body_start)


func _run_tests() -> void:
	_check_no_sim_bridge_reference_in_body()
	await _check_live_autosave_writes_a_save()
	_completed = true


func _check_no_sim_bridge_reference_in_body() -> void:
	var text := FileAccess.get_file_as_string(SOURCE_PATH)
	_assert(text != "", "could not read " + SOURCE_PATH)
	if text == "":
		return
	var body := _function_body(text, FUNC_NAME)
	_assert(body != "", "%s not found in %s" % [FUNC_NAME, SOURCE_PATH])
	if body == "":
		return
	_assert(not body.contains("SimBridge"),
		"trigger_autosave() body still references SimBridge (should go through SimSession instead):\n" + body)


func _check_live_autosave_writes_a_save() -> void:
	var SimSession := preload("res://autoload/sim_session.gd")
	var CBridge := load("res://autoload/c_bridge.gd")
	SimSession.reset()
	var bridge = SimSession.bridge()
	_assert(bridge.ensure_session(LIVE_SEED, CBridge.DEFAULT_N_REGIONS, CBridge.DEFAULT_FEATURES),
		"ensure_session(%d) failed: %s" % [LIVE_SEED, bridge.last_error()])

	var dir: String = bridge.saves_dir()
	var save_path := dir.path_join("campaign_%d.omsave" % LIVE_SEED)
	var sidecar_path := save_path + ".json"
	# Clean slate: a stale file here (a previous crashed run) would make the
	# assertion below pass for the wrong reason.
	DirAccess.remove_absolute(save_path)
	DirAccess.remove_absolute(sidecar_path)
	_assert(not FileAccess.file_exists(save_path), "stale save file present before the test ran: " + save_path)

	var ui_data_bus := get_root().get_node("UIDataBus")
	ui_data_bus.trigger_autosave("post_debrief")

	_assert(FileAccess.file_exists(save_path),
		"no save file at %s after UIDataBus.trigger_autosave (still on the dead SimBridge/mock path instead of SimSession.bridge()._autosave())" % save_path)

	# Teardown: leave no save file behind for the next run.
	DirAccess.remove_absolute(save_path)
	DirAccess.remove_absolute(sidecar_path)
	SimSession.reset()
