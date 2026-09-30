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
# Piece G-uidatabus-2 (same plan doc): _ready() and proceed_to_next_mission()
# each carry one more bare SimBridge identifier reference that G-projectgodot-1
# will strand once the SimBridge autoload is deleted (a bare autoload
# identifier anywhere in a .gd file, even in an unreached branch, fails the
# whole file to parse once that autoload is gone -- GDScript resolves
# autoload names at parse time). _ready()'s "if SimBridge.USE_LIVE_SIM: ...
# else: load mock_data_source.gd" branch is to become an unconditional load
# of sim_bridge_data_source.gd (the live source is what players see today and
# stays live), and proceed_to_next_mission()'s "SimBridge.send_command(...)"
# is to become a pure "SceneRouter.go_to('mission_briefing')" scene
# transition (mission_briefing.gd's own _ready() already self-loads the live
# mission via SimSession).
#
# Four checks:
#   1. Static: the source text of trigger_autosave()'s function body (the
#      slice between "func trigger_autosave" and the next "func ") must not
#      mention SimBridge anywhere. Red today: the current body branches on
#      SimBridge.USE_LIVE_SIM and calls SimBridge.send_command.
#   2. Live: open a real pipe session through SimSession.bridge(), call
#      UIDataBus.trigger_autosave(), and check a save file actually landed
#      under the bridge's saves_dir(). Red today: mock mode (SimBridge.
#      USE_LIVE_SIM false in a headless test run with no live sim wired up)
#      only prints and writes nothing.
#   3. _ready(): static check that its function body no longer mentions
#      SimBridge or mock_data_source (G-uidatabus-2). Red today: the body
#      still branches on SimBridge.USE_LIVE_SIM and loads mock_data_source.gd
#      in its else arm. Paired with a same-shape pin (non-red today, since
#      SimBridge.USE_LIVE_SIM already defaults to true in this codebase) that
#      the resulting _source is the live sim_bridge_data_source.gd script,
#      not mock_data_source.gd -- this is what "unconditionally live"
#      actually has to keep being true once the branch is deleted.
#   4. proceed_to_next_mission(): static check that its function body no
#      longer mentions SimBridge (G-uidatabus-2), plus a live check that
#      calling it routes through SceneRouter.go_to("mission_briefing") and
#      not through a SimBridge command. Red today: the body only calls
#      SimBridge.send_command and never touches SceneRouter, so
#      SceneRouter's routing target does not move to "mission_briefing".

const SOURCE_PATH := "res://autoload/ui_data_bus.gd"
const FUNC_NAME := "trigger_autosave"
const READY_FUNC_NAME := "_ready"
const PROCEED_FUNC_NAME := "proceed_to_next_mission"
const LIVE_SOURCE_SCRIPT_PATH := "res://autoload/sim_bridge_data_source.gd"
const MOCK_SOURCE_SCRIPT_PATH := "res://autoload/mock_data_source.gd"
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
	# Autoload _ready() calls (UIDataBus, SimBridge, SceneRouter, ...) are
	# deferred to the first idle frame, not run synchronously before
	# _initialize(). The live checks below (assertions 3b and 4b) read state
	# those _ready() calls set up, so wait one frame before touching any
	# autoload instance state.
	await process_frame
	_check_no_sim_bridge_reference_in_body()
	await _check_live_autosave_writes_a_save()
	_check_ready_body_no_forbidden_references()
	_check_ready_source_is_always_live()
	_check_proceed_no_sim_bridge_reference_in_body()
	await _check_proceed_routes_via_scene_router()
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


# Assertion 3a (G-uidatabus-2): _ready()'s function body must not mention
# SimBridge (the USE_LIVE_SIM branch condition) or mock_data_source (its
# else-arm load target) once the branch is removed. Red today: the current
# body is
#   if SimBridge.USE_LIVE_SIM:
#       _source = load("res://autoload/sim_bridge_data_source.gd").new()
#   else:
#       _source = load("res://autoload/mock_data_source.gd").new()
func _check_ready_body_no_forbidden_references() -> void:
	var text := FileAccess.get_file_as_string(SOURCE_PATH)
	_assert(text != "", "could not read " + SOURCE_PATH)
	if text == "":
		return
	var body := _function_body(text, READY_FUNC_NAME)
	_assert(body != "", "%s not found in %s" % [READY_FUNC_NAME, SOURCE_PATH])
	if body == "":
		return
	_assert(not body.contains("SimBridge"),
		"_ready() body still references SimBridge (should unconditionally load the live data source, not branch on SimBridge.USE_LIVE_SIM):\n" + body)
	_assert(not body.contains("mock_data_source"),
		"_ready() body still references mock_data_source.gd (should unconditionally load sim_bridge_data_source.gd):\n" + body)


# Assertion 3b (pin, non-red): once the branch above is gone, _ready() must
# still end up with the live source. Not red today -- SimBridge.USE_LIVE_SIM
# (autoload/sim_bridge.gd) already defaults to true in this codebase, so the
# current branch already resolves to sim_bridge_data_source.gd -- but this
# guards the actual contract ("always live, regardless of any
# USE_LIVE_SIM-style flag") rather than just the absence of the old branch
# text, and must keep passing after the fix lands.
func _check_ready_source_is_always_live() -> void:
	var ui_data_bus := get_root().get_node_or_null("UIDataBus")
	_assert(ui_data_bus != null, "could not find the UIDataBus autoload node in the tree")
	if ui_data_bus == null:
		return
	var source = ui_data_bus.get("_source")
	_assert(source != null, "UIDataBus._source is null after _ready() ran")
	if source == null:
		return
	var source_script: Script = source.get_script()
	_assert(source_script != null, "UIDataBus._source has no attached script")
	if source_script == null:
		return
	_assert(source_script.resource_path == LIVE_SOURCE_SCRIPT_PATH,
		"UIDataBus._source is %s, expected the live %s (not %s)" % [source_script.resource_path, LIVE_SOURCE_SCRIPT_PATH, MOCK_SOURCE_SCRIPT_PATH])


# Assertion 4a (G-uidatabus-2): proceed_to_next_mission()'s function body
# must not mention SimBridge once it becomes a pure scene transition. Red
# today: the current body is
#   SimBridge.send_command({"type": "command", "cmd": "proceed_to_next_mission"})
func _check_proceed_no_sim_bridge_reference_in_body() -> void:
	var text := FileAccess.get_file_as_string(SOURCE_PATH)
	_assert(text != "", "could not read " + SOURCE_PATH)
	if text == "":
		return
	var body := _function_body(text, PROCEED_FUNC_NAME)
	_assert(body != "", "%s not found in %s" % [PROCEED_FUNC_NAME, SOURCE_PATH])
	if body == "":
		return
	_assert(not body.contains("SimBridge"),
		"proceed_to_next_mission() body still references SimBridge (should be SceneRouter.go_to('mission_briefing') instead):\n" + body)


# Assertion 4b (G-uidatabus-2): calling proceed_to_next_mission() must route
# through SceneRouter.go_to("mission_briefing") (observed the same way
# tests/test_error_screen.gd and tests/test_briefing_debrief.gd observe
# routing: SceneRouter.go_to() sets _current_scene_name synchronously before
# its fade tween runs, so it is safe to read right after the call). Red
# today: the current body only calls SimBridge.send_command and never touches
# SceneRouter, so _current_scene_name never becomes "mission_briefing".
func _check_proceed_routes_via_scene_router() -> void:
	var ui_data_bus := get_root().get_node_or_null("UIDataBus")
	_assert(ui_data_bus != null, "could not find the UIDataBus autoload node in the tree")
	var scene_router := get_root().get_node_or_null("SceneRouter")
	_assert(scene_router != null, "could not find the SceneRouter autoload node in the tree")
	if ui_data_bus == null or scene_router == null:
		return

	ui_data_bus.proceed_to_next_mission()
	await process_frame

	_assert(str(scene_router.get("_current_scene_name")) == "mission_briefing",
		"proceed_to_next_mission() left SceneRouter at '%s', expected 'mission_briefing' (still on the dead SimBridge.send_command path instead of SceneRouter.go_to)" % scene_router.get("_current_scene_name"))
