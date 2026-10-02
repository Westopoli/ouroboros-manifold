extends SceneTree

# A5 (plan 2026-09-30-mission-plays): the briefing's controls are Accept and Refuse.
# Proves R-079-02 / S-079: no "Review Chronicle" control, no "after backend
# integration" placeholder modal; Deploy (Accept) reachable in one click; Refuse
# present and enabled in recon (B3 wired it; A39(d) replaced the A5 disabled assertions).
# Style mirrors tests/test_briefing_deploy.gd.

const BRIEFING_SCENE_PATH := "res://scenes/mission_briefing/mission_briefing.tscn"
const BRIEFING_SCRIPT_PATH := "res://scenes/mission_briefing/mission_briefing.gd"
const CBridge := preload("res://autoload/c_bridge.gd")

var _pass_count := 0
var _fail_count := 0
var _fail_msgs: Array[String] = []


func _initialize() -> void:
	await _run_tests()
	print("\n=== Briefing Controls Test Results ===")
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
	await _test_no_chronicle_control_or_placeholder_modal()
	await _test_deploy_reachable()
	await _test_refuse_present_and_enabled()


func _open_briefing() -> Node:
	var SimSession = load("res://autoload/sim_session.gd")
	SimSession.reset()
	var bridge = SimSession.bridge()
	if not bridge.load_mission_live(1, CBridge.DEFAULT_N_REGIONS, CBridge.DEFAULT_FEATURES):
		_assert(false, "setup: load_mission_live failed: %s" % bridge.last_error())
		return null
	var packed = load(BRIEFING_SCENE_PATH)
	_assert(packed != null, "cannot load %s" % BRIEFING_SCENE_PATH)
	if packed == null:
		return null
	var scene: Node = (packed as PackedScene).instantiate()
	get_root().add_child(scene)
	await process_frame
	await process_frame
	return scene


func _close(scene: Node) -> void:
	if scene != null:
		scene.queue_free()
		await process_frame
	load("res://autoload/sim_session.gd").reset()


# R-079-02 / S-079: the chronicle is reached from the debrief and galaxy, not here.
func _test_no_chronicle_control_or_placeholder_modal() -> void:
	var scene := await _open_briefing()
	if scene == null:
		return
	var offenders: Array[String] = []
	_collect_text_offenders(scene, offenders)
	_assert(offenders.is_empty(),
		"A5/R-079-02: briefing must have no Review Chronicle control and no 'backend integration' text; found %s" % str(offenders))
	var src := FileAccess.get_file_as_string(BRIEFING_SCRIPT_PATH)
	_assert(src.to_lower().find("backend integration") == -1,
		"A5/R-079-02: mission_briefing.gd still contains the 'after backend integration' placeholder modal text")
	await _close(scene)


func _collect_text_offenders(node: Node, out: Array[String]) -> void:
	if node is Control and "text" in node:
		var t := String(node.get("text")).to_lower()
		if t.find("chronicle") != -1 or t.find("backend integration") != -1:
			out.append("%s:'%s'" % [node.name, t])
	for c in node.get_children():
		_collect_text_offenders(c, out)


# S-079 / R-079-02: Accept (the node named Deploy) is visible, enabled in recon,
# and one press begins the mission.
func _test_deploy_reachable() -> void:
	var scene := await _open_briefing()
	if scene == null:
		return
	var deploy = _find_named(scene, "Deploy")
	_assert(deploy != null, "A5/R-079-02: no node named Deploy (Accept) in the briefing")
	if deploy != null:
		_assert(deploy is BaseButton, "A5: Deploy must be a button")
		_assert(deploy.is_visible_in_tree(), "A5/S-079: Deploy must be visible")
		_assert(not bool(deploy.get("disabled")), "A5/S-079: Deploy must be enabled in recon")
		_assert(deploy.has_signal("pressed"), "A5: Deploy must emit pressed")
		var SimSession = load("res://autoload/sim_session.gd")
		_assert(not SimSession.bridge().mission_begun(), "control: mission not begun before Deploy press")
		deploy.emit_signal("pressed")
		await process_frame
		_assert(SimSession.bridge().mission_begun(),
			"A5/S-079: one press of Deploy must begin the mission (mission_begun() true); error=%s" % SimSession.bridge().last_error())
	await _close(scene)


# R-079-02: Refuse exists and is enabled in recon (B3 wired it; A39(d) retired the A5 disabled-with-tooltip assertions).
func _test_refuse_present_and_enabled() -> void:
	var scene := await _open_briefing()
	if scene == null:
		return
	var refuse = _find_named(scene, "Refuse")
	_assert(refuse != null, "A5/R-079-02: no node named Refuse in the briefing")
	if refuse != null:
		_assert(refuse is BaseButton, "A5: Refuse must be a button")
		_assert(refuse.is_visible_in_tree(), "A5/R-079-02: Refuse must be visible")
		_assert(not bool(refuse.get("disabled")), "B3/R-078-05: Refuse must be enabled in recon")
	await _close(scene)


func _find_named(node: Node, node_name: String):
	if node.name == node_name:
		return node
	for c in node.get_children():
		var found = _find_named(c, node_name)
		if found != null:
			return found
	return null
