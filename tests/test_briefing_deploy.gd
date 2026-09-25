extends SceneTree

# C4-6 (QA-004/005/006): Deploy button guard and refused-begin error display.
# Proves: Deploy is disabled when not in recon; enabled when in recon; a
# refused begin_mission() surfaces last_error() in a visible node (DeployError).
# Style mirrors tests/test_briefing_debrief.gd.

const BRIEFING_SCENE_PATH := "res://scenes/mission_briefing/mission_briefing.tscn"
const CBridge := preload("res://autoload/c_bridge.gd")

var _pass_count := 0
var _fail_count := 0
var _fail_msgs: Array[String] = []


func _initialize() -> void:
	await _run_tests()
	print("\n=== Briefing Deploy Test Results ===")
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
	await _test_deploy_disabled_when_not_in_recon()
	await _test_deploy_enabled_when_in_recon()
	await _test_deploy_error_shown_on_refused_begin()


# R-QA-004/005: Deploy is disabled when the mission is already begun (not in recon).
# Uses begin_mission_live() first so mission_begun() == true before the scene loads.
func _test_deploy_disabled_when_not_in_recon() -> void:
	var SimSession = load("res://autoload/sim_session.gd")
	SimSession.reset()
	var bridge = SimSession.bridge()
	if not bridge.load_mission_live(1, CBridge.DEFAULT_N_REGIONS, CBridge.DEFAULT_FEATURES):
		_assert(false, "deploy_disabled_setup: load_mission_live failed: %s" % bridge.last_error())
		SimSession.reset()
		return
	if not bridge.begin_mission_live(1, CBridge.DEFAULT_N_REGIONS, CBridge.DEFAULT_FEATURES):
		_assert(false, "deploy_disabled_setup: begin_mission_live failed: %s" % bridge.last_error())
		SimSession.reset()
		return
	_assert(bridge.mission_begun(), "control: mission_begun() must be true after begin_mission_live")

	var packed = load(BRIEFING_SCENE_PATH)
	_assert(packed != null, "cannot load %s" % BRIEFING_SCENE_PATH)
	if packed == null:
		SimSession.reset()
		return
	var scene: Node = (packed as PackedScene).instantiate()
	get_root().add_child(scene)
	await process_frame
	await process_frame

	_assert(scene.has_method("qa_state"), "mission_briefing missing qa_state()")
	if scene.has_method("qa_state"):
		var state: Dictionary = scene.qa_state()
		_assert(not bool(state.get("deploy_enabled", true)),
			"C4-6: Deploy must be disabled when mission already begun (not in recon); qa_state = %s" % JSON.stringify(state))

	scene.queue_free()
	await process_frame
	SimSession.reset()


# R-QA-004/005: Deploy is enabled when the session has an active mission in recon
# (mission_active() == true, mission_begun() == false).
func _test_deploy_enabled_when_in_recon() -> void:
	var SimSession = load("res://autoload/sim_session.gd")
	SimSession.reset()
	var bridge = SimSession.bridge()
	if not bridge.load_mission_live(1, CBridge.DEFAULT_N_REGIONS, CBridge.DEFAULT_FEATURES):
		_assert(false, "deploy_enabled_setup: load_mission_live failed: %s" % bridge.last_error())
		SimSession.reset()
		return
	_assert(bridge.mission_active(), "control: mission_active() must be true after load_mission_live")
	_assert(not bridge.mission_begun(), "control: mission_begun() must be false after load_mission_live (recon state)")

	var packed = load(BRIEFING_SCENE_PATH)
	_assert(packed != null, "cannot load %s" % BRIEFING_SCENE_PATH)
	if packed == null:
		SimSession.reset()
		return
	var scene: Node = (packed as PackedScene).instantiate()
	get_root().add_child(scene)
	await process_frame
	await process_frame

	_assert(scene.has_method("qa_state"), "mission_briefing missing qa_state()")
	if scene.has_method("qa_state"):
		var state: Dictionary = scene.qa_state()
		_assert(bool(state.get("deploy_enabled", false)),
			"C4-6: Deploy must be enabled when mission is in recon state; qa_state = %s" % JSON.stringify(state))

	scene.queue_free()
	await process_frame
	SimSession.reset()


# R-QA-006: When begin_mission() is refused, last_error() text appears in a
# visible node named DeployError in the scene (not only in the console).
func _test_deploy_error_shown_on_refused_begin() -> void:
	var SimSession = load("res://autoload/sim_session.gd")
	SimSession.reset()
	var bridge = SimSession.bridge()
	if not bridge.load_mission_live(1, CBridge.DEFAULT_N_REGIONS, CBridge.DEFAULT_FEATURES):
		_assert(false, "deploy_error_setup: load_mission_live failed: %s" % bridge.last_error())
		SimSession.reset()
		return

	var packed = load(BRIEFING_SCENE_PATH)
	_assert(packed != null, "cannot load %s" % BRIEFING_SCENE_PATH)
	if packed == null:
		SimSession.reset()
		return
	var scene: Node = (packed as PackedScene).instantiate()
	get_root().add_child(scene)
	await process_frame
	await process_frame

	_assert(scene.has_method("qa_plant"), "mission_briefing missing qa_plant()")
	_assert(scene.has_method("begin_mission"), "mission_briefing missing begin_mission()")
	if scene.has_method("qa_plant") and scene.has_method("begin_mission"):
		_assert(scene.qa_plant("begin-refused"), "qa_plant('begin-refused') returned false (not implemented yet)")
		var result: bool = scene.begin_mission()
		_assert(not result, "C4-6: begin_mission() must return false when 'begin-refused' is planted")
		var error_node = _find_named(scene, "DeployError")
		_assert(error_node != null,
			"C4-6: no node named DeployError in mission_briefing after refused begin; error must be visible on screen, not only printed")
		if error_node != null:
			var text: String = String(error_node.get("text"))
			_assert(text != "",
				"C4-6: DeployError node has empty text after refused begin; last_error() must be shown on screen")

	scene.queue_free()
	await process_frame
	SimSession.reset()


func _find_named(node: Node, node_name: String):
	if node.name == node_name:
		return node
	for c in node.get_children():
		var found = _find_named(c, node_name)
		if found != null:
			return found
	return null
