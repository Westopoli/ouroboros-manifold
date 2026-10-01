extends SceneTree

# B3 (plan 2026-09-30-mission-plays, R-078-05, R-079-02): the briefing's Refuse control.
# Since A5 the button exists disabled with the tooltip "Not wired yet". B3 wires it:
# enabled in recon, one press sends `mission_refuse` (docs/architecture.md "session
# commands"), the pipe answers the refusal debrief (band 5) and the briefing closes to
# the mission-end flow (SceneRouter "debrief", the same target the tactical view uses).
# Supersedes the A5 assertion in tests/test_briefing_controls.gd that Refuse is disabled
# (test-defect, ledger row in docs/northstar/plans/push_ledger_2026-09-22.md).
# Style mirrors tests/test_briefing_controls.gd and tests/test_briefing_deploy.gd.

const BRIEFING_SCENE_PATH := "res://scenes/mission_briefing/mission_briefing.tscn"
const DEBRIEF_SCENE_PATH := "res://scenes/debrief/debrief.tscn"
const CBridge := preload("res://autoload/c_bridge.gd")
const BAND_REFUSAL := 5

var _pass_count := 0
var _fail_count := 0
var _fail_msgs: Array[String] = []


func _initialize() -> void:
	await _run_tests()
	print("\n=== Briefing Refuse Test Results ===")
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
	await _test_refuse_enabled_in_recon()
	await _test_refuse_disabled_once_begun()
	await _test_debrief_names_the_refusal_band()
	# Last: the press routes to the debrief scene, and SceneRouter's fade (a real-time
	# tween) keeps running after it, so nothing else may follow in this process.
	await _test_refuse_press_ends_the_mission_and_frees_the_strategic_phase()


func _open_briefing(begin_first: bool = false) -> Node:
	var SimSession = load("res://autoload/sim_session.gd")
	SimSession.reset()
	var bridge = SimSession.bridge()
	if not bridge.load_mission_live(1, CBridge.DEFAULT_N_REGIONS, CBridge.DEFAULT_FEATURES):
		_assert(false, "setup: load_mission_live failed: %s" % bridge.last_error())
		return null
	if begin_first and not bridge.begin_mission_live(1, CBridge.DEFAULT_N_REGIONS, CBridge.DEFAULT_FEATURES):
		_assert(false, "setup: begin_mission_live failed: %s" % bridge.last_error())
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


func _find_named(node: Node, node_name: String):
	if node.name == node_name:
		return node
	for c in node.get_children():
		var found = _find_named(c, node_name)
		if found != null:
			return found
	return null


# R-079-02: Refuse is a live control in recon, no longer the A5 disabled placeholder.
func _test_refuse_enabled_in_recon() -> void:
	var scene := await _open_briefing()
	if scene == null:
		return
	var refuse = _find_named(scene, "Refuse")
	_assert(refuse != null, "B3/R-079-02: no node named Refuse in the briefing")
	if refuse != null:
		_assert(refuse is BaseButton, "B3: Refuse must be a button")
		_assert(refuse.is_visible_in_tree(), "B3/R-079-02: Refuse must be visible")
		_assert(not bool(refuse.get("disabled")), "B3/R-078-05: Refuse must be enabled in recon")
		_assert(String(refuse.get("tooltip_text")).strip_edges() != "Not wired yet",
			"B3: Refuse must drop the 'Not wired yet' tooltip once wired")
	await _close(scene)


# Control: mission_refuse is valid only in recon (docs/architecture.md), so a briefing
# opened over an already-begun mission keeps Refuse disabled, as Deploy does (C4-6).
func _test_refuse_disabled_once_begun() -> void:
	var scene := await _open_briefing(true)
	if scene == null:
		return
	var refuse = _find_named(scene, "Refuse")
	_assert(refuse != null, "B3 control: no node named Refuse in the briefing")
	if refuse != null:
		_assert(bool(refuse.get("disabled")),
			"B3: Refuse must be disabled when the mission is already begun (not in recon)")
	await _close(scene)


# One press: mission_refuse is sent, the briefing routes on, the sim's refusal debrief (band 5) is kept for the
# next scene, the session leaves the mission phase, and the strategic phase is free again
# (a jump is refused with "mission running" while a mission still runs, so a successful
# jump proves the pipe really received mission_refuse).
func _test_refuse_press_ends_the_mission_and_frees_the_strategic_phase() -> void:
	var scene := await _open_briefing()
	if scene == null:
		return
	var SimSession = load("res://autoload/sim_session.gd")
	var bridge = SimSession.bridge()
	var refuse = _find_named(scene, "Refuse")
	_assert(refuse != null, "B3: no node named Refuse in the briefing")
	if refuse == null:
		await _close(scene)
		return
	_assert(bridge.mission_active() and not bridge.mission_begun(), "control: mission in recon before Refuse")
	if bool(refuse.get("disabled")):
		_assert(false, "B3: Refuse is disabled in recon, cannot press it")
		await _close(scene)
		return
	var router := get_root().get_node("SceneRouter")
	# The legacy SimBridge autoload fails to start under --headless and routes to
	# error_screen at boot; SceneRouter.go_to() ignores calls while that fade runs, so
	# wait it out (up to 5 s) before pressing.
	var waited := 0
	while bool(router.get("_transitioning")) and waited < 300:
		await process_frame
		waited += 1
	_assert(not bool(router.get("_transitioning")), "setup: SceneRouter still transitioning after 300 frames")
	var before := str(router.get("_current_scene_name"))
	refuse.emit_signal("pressed")
	await process_frame
	# The briefing closes: go_to() sets _current_scene_name synchronously (see the C4-9
	# pin in tests/test_briefing_debrief.gd); "debrief" is the mission-end flow's first
	# scene, the same target the tactical view routes to.
	var after := str(router.get("_current_scene_name"))
	_assert(after == "debrief", "B3: Refuse must route the briefing to 'debrief' (was '%s', now '%s')" % [before, after])
	_assert(bridge.last_error() == "", "B3: pressing Refuse must not leave a pipe error, got '%s'" % bridge.last_error())
	_assert(not bridge.mission_active(), "B3/R-078-05: the refused mission is over (mission_active() false)")
	_assert(not bridge.mission_begun(), "B3/R-078-05: no force is deployed (mission_begun() false)")
	var debrief: Dictionary = bridge.debrief_frame()
	_assert(int(debrief.get("band", -1)) == BAND_REFUSAL,
		"B3/R-078-05: bridge.debrief_frame() must hold the refusal debrief (band 5), got %s" % JSON.stringify(debrief))
	_assert(not debrief.has("commander_fate"), "B3: a refusal debrief carries no commander_fate: %s" % JSON.stringify(debrief))
	var jumped: bool = bridge.load_chronicle_live(1, CBridge.DEFAULT_N_REGIONS, CBridge.DEFAULT_FEATURES)
	_assert(jumped, "B3: after Refuse the next jump must be accepted (phase back to strategic): %s" % bridge.last_error())
	await _close(scene)


# R-078-05: the debrief shows the refusal band by name; it is not clamped to a success band
# (debrief.gd BAND_NAMES stops at total_success today).
func _test_debrief_names_the_refusal_band() -> void:
	var packed = load(DEBRIEF_SCENE_PATH)
	_assert(packed != null, "cannot load %s" % DEBRIEF_SCENE_PATH)
	if packed == null:
		return
	var root: Node = (packed as PackedScene).instantiate()
	get_root().add_child(root)
	await process_frame
	_assert(root.has_method("load_frame") and root.has_method("qa_state"), "debrief missing load_frame/qa_state")
	if root.has_method("load_frame") and root.has_method("qa_state"):
		root.load_frame({"band": BAND_REFUSAL, "achieved": 0.0, "brought_home": 0.0,
			"region_delta": {"military": 0.0, "economy": 0.0, "tension": 6.0, "population": 0.0}})
		var state: Dictionary = root.qa_state()
		_assert(String(state.get("band", "")) == "refusal",
			"B3/R-078-05: a band-5 debrief frame must show band 'refusal', got '%s'" % str(state.get("band", "")))
	root.queue_free()
	await process_frame
	load("res://autoload/sim_session.gd").reset()
