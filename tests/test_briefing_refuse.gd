extends SceneTree

# B3 (plan 2026-09-30-mission-plays, R-078-05, R-079-02): the briefing's Refuse control.
# Since A5 the button exists disabled with the tooltip "Not wired yet". B3 wires it:
# enabled in recon, one press sends `mission_refuse` (docs/architecture.md "session
# commands"), the pipe answers the refusal debrief (band 5) and the briefing closes to
# the mission-end flow (SceneRouter "debrief", the same target the tactical view uses).
# Supersedes the A5 assertion in tests/test_briefing_controls.gd that Refuse is disabled
# (test-defect, ledger row in docs/northstar/plans/push_ledger_2026-09-22.md).
# A39 (docs/northstar/plans/2026-10-01-architect-rulings-2.md): the bridge keeps the latest
# debrief frame when it arrives (after mission_end and after mission_refuse; debrief_frame()),
# the debrief scene shows that frame and never starts a mission itself, no held frame (or a
# band it has no name for) shows the shared error panel, never a clamped name. Refuse routes
# to 'debrief'.
# Style mirrors tests/test_briefing_controls.gd and tests/test_briefing_deploy.gd.

const BRIEFING_SCENE_PATH := "res://scenes/mission_briefing/mission_briefing.tscn"
const DEBRIEF_SCENE_PATH := "res://scenes/debrief/debrief.tscn"
const CBridge := preload("res://autoload/c_bridge.gd")
const BAND_REFUSAL := 5
const PLAYED_BANDS := ["total_failure", "partial_failure", "partial_success", "strong_success", "total_success"]
const MISSION_STARTERS := ["mission_start", "mission_begin", "mission_end", "mission_refuse"]


# A real c_bridge.gd that records the name of every command it sends.
class CountBridge:
	extends "res://autoload/c_bridge.gd"
	var sent: Array = []

	func send_command(cmd: Dictionary) -> void:
		sent.append(str(cmd.get("name", "")))
		super.send_command(cmd)

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
	await _test_debrief_unknown_band_shows_error_panel()
	await _test_bridge_holds_no_debrief_frame_before_any()
	await _test_debrief_with_no_held_frame_shows_error_panel_and_starts_nothing()
	await _test_refusal_frame_is_held_and_debrief_shows_it()
	await _test_played_mission_end_frame_is_held_and_debrief_shows_it()
	# Last: the press routes to the debrief scene, and SceneRouter's fade (a real-time
	# tween) keeps running after it, so nothing else may follow in this process.
	await _test_refuse_press_ends_the_mission_and_frees_the_strategic_phase()


func _open_briefing(begin_first: bool = false) -> Node:
	var SimSession = load("res://autoload/sim_session.gd")
	SimSession.reset()
	SimSession._bridge = CountBridge.new()
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
	_assert(bridge.sent.has("mission_refuse"), "B3: pressing Refuse must send mission_refuse, sent %s" % str(bridge.sent))
	_assert(bridge.last_error() == "", "B3: pressing Refuse must not leave a pipe error, got '%s'" % bridge.last_error())
	_assert(not bridge.mission_active(), "B3/R-078-05: the refused mission is over (mission_active() false)")
	_assert(not bridge.mission_begun(), "B3/R-078-05: no force is deployed (mission_begun() false)")
	var debrief: Dictionary = bridge.debrief_frame()
	_assert(int(debrief.get("band", -1)) == BAND_REFUSAL,
		"B3/R-078-05: bridge.debrief_frame() must hold the refusal debrief (band 5), got %s" % JSON.stringify(debrief))
	_assert(not debrief.has("commander_fate"), "B3: a refusal debrief carries no commander_fate: %s" % JSON.stringify(debrief))
	var shown = await _mount_debrief()
	_assert(String((shown.qa_state() as Dictionary).get("band", "")) == "refusal",
		"A39: the debrief after Refuse must show band 'refusal'")
	_assert(not bool((shown.qa_state() as Dictionary).get("error_panel", true)),
		"A39: the debrief after Refuse must not show the error panel")
	shown.queue_free()
	var jumped: bool = bridge.load_chronicle_live(1, CBridge.DEFAULT_N_REGIONS, CBridge.DEFAULT_FEATURES)
	_assert(jumped, "B3: after Refuse the next jump must be accepted (phase back to strategic): %s" % bridge.last_error())
	await _close(scene)


# R-078-05: the debrief shows the refusal band by name; it is not clamped to a success band
# (debrief.gd BAND_NAMES stops at total_success today); A39(a): band 5 is named 'refusal'.
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


func _mount_debrief() -> Node:
	var packed = load(DEBRIEF_SCENE_PATH)
	var root: Node = (packed as PackedScene).instantiate()
	get_root().add_child(root)
	await process_frame
	await process_frame
	return root


# Pumps the bridge until cond.call() holds (up to 5 s).
func _pump_until(bridge, cond: Callable) -> bool:
	var deadline := Time.get_ticks_msec() + 5000
	while not cond.call() and Time.get_ticks_msec() < deadline:
		if bridge.pump() == 0:
			OS.delay_msec(5)
	return cond.call()


func _started_a_mission(sent: Array, from_index: int) -> Array:
	var hits: Array = []
	for i in range(from_index, sent.size()):
		if MISSION_STARTERS.has(sent[i]):
			hits.append(sent[i])
	return hits


# A39(a): an unknown band (not one of the five played bands or refusal) is an error, not a
# clamped name: the shared error panel shows and qa_state()["band"] is no band name.
func _test_debrief_unknown_band_shows_error_panel() -> void:
	for bad_band in [9, -1]:
		var root: Node = await _mount_debrief_with_frame(
			{"band": bad_band, "achieved": 0.0, "brought_home": 0.0, "region_delta": {}})
		if root == null:
			return
		var state: Dictionary = root.qa_state()
		_assert(bool(state.get("error_panel", false)),
			"A39(a): unknown band %d must show the error panel (qa_state error_panel), state %s" % [bad_band, JSON.stringify(state)])
		_assert(not PLAYED_BANDS.has(String(state.get("band", ""))) and String(state.get("band", "")) != "refusal",
			"A39(a): unknown band %d must not be shown as a clamped band name, got '%s'" % [bad_band, str(state.get("band", ""))])
		root.queue_free()
		await process_frame
	load("res://autoload/sim_session.gd").reset()


# Mounts the debrief over a bridge that holds no frame, then rebinds it with load_frame().
func _mount_debrief_with_frame(frame: Dictionary) -> Node:
	var SimSession = load("res://autoload/sim_session.gd")
	SimSession.reset()
	SimSession._bridge = CountBridge.new()
	var root: Node = await _mount_debrief()
	if not (root.has_method("load_frame") and root.has_method("qa_state")):
		_assert(false, "debrief missing load_frame/qa_state")
		return null
	root.load_frame(frame)
	return root


# A39(b): before any mission_end or mission_refuse the bridge holds no debrief frame.
func _test_bridge_holds_no_debrief_frame_before_any() -> void:
	var SimSession = load("res://autoload/sim_session.gd")
	SimSession.reset()
	_assert(SimSession.bridge().debrief_frame().is_empty(), "A39(b): a fresh bridge must hold no debrief frame")
	var bridge = CountBridge.new()
	SimSession._bridge = bridge
	if bridge.load_mission_live(1, CBridge.DEFAULT_N_REGIONS, CBridge.DEFAULT_FEATURES):
		_assert(bridge.debrief_frame().is_empty(),
			"A39(b): a started mission that has not ended holds no debrief frame, got %s" % JSON.stringify(bridge.debrief_frame()))
	else:
		_assert(false, "setup: load_mission_live failed: %s" % bridge.last_error())
	SimSession.reset()


# A39(b): no frame held means the error panel, and the debrief sends no mission command of
# its own (load_debrief_live's start-then-end leaves the live path).
func _test_debrief_with_no_held_frame_shows_error_panel_and_starts_nothing() -> void:
	var SimSession = load("res://autoload/sim_session.gd")
	SimSession.reset()
	var bridge = CountBridge.new()
	SimSession._bridge = bridge
	var root: Node = await _mount_debrief()
	var state: Dictionary = root.qa_state() if root.has_method("qa_state") else {}
	_assert(bool(state.get("error_panel", false)),
		"A39(b): a debrief reached with no held frame must show the error panel, state %s" % JSON.stringify(state))
	_assert(_started_a_mission(bridge.sent, 0).is_empty(),
		"A39(b): the debrief must not start or end a mission itself, it sent %s" % str(bridge.sent))
	root.queue_free()
	await process_frame
	SimSession.reset()


# A39(b) + R-078-05: mission_refuse's debrief frame is held by the bridge and the debrief
# shows it, without sending any mission command.
func _test_refusal_frame_is_held_and_debrief_shows_it() -> void:
	var SimSession = load("res://autoload/sim_session.gd")
	SimSession.reset()
	var bridge = CountBridge.new()
	SimSession._bridge = bridge
	if not bridge.load_mission_live(1, CBridge.DEFAULT_N_REGIONS, CBridge.DEFAULT_FEATURES):
		_assert(false, "setup: load_mission_live failed: %s" % bridge.last_error())
		return
	bridge.send_command({"type": "cmd", "name": "mission_refuse"})
	_assert(_pump_until(bridge, func(): return not bridge.mission_active()), "setup: mission_refuse was not answered in 5 s")
	var held: Dictionary = bridge.debrief_frame()
	_assert(int(held.get("band", -1)) == BAND_REFUSAL,
		"A39(b): after mission_refuse debrief_frame() must hold the band-5 frame, got %s" % JSON.stringify(held))
	_assert(not held.has("commander_fate"), "A39(b): the refusal frame has no commander_fate: %s" % JSON.stringify(held))
	var mark: int = bridge.sent.size()
	var root: Node = await _mount_debrief()
	var state: Dictionary = root.qa_state()
	_assert(String(state.get("band", "")) == "refusal",
		"A39(b): the debrief must show the held refusal frame (band 'refusal'), got %s" % JSON.stringify(state))
	_assert(not bool(state.get("error_panel", true)), "A39(b): a held frame must not show the error panel")
	_assert(_started_a_mission(bridge.sent, mark).is_empty(),
		"A39(b): the debrief must send no mission command, it sent %s" % str(bridge.sent.slice(mark)))
	root.queue_free()
	await process_frame
	SimSession.reset()


# A39(b): a played mission's mission_end frame is held the same way and shown by the debrief.
func _test_played_mission_end_frame_is_held_and_debrief_shows_it() -> void:
	var SimSession = load("res://autoload/sim_session.gd")
	SimSession.reset()
	var bridge = CountBridge.new()
	SimSession._bridge = bridge
	if not bridge.load_mission_live(1, CBridge.DEFAULT_N_REGIONS, CBridge.DEFAULT_FEATURES) \
			or not bridge.begin_mission_live(1, CBridge.DEFAULT_N_REGIONS, CBridge.DEFAULT_FEATURES):
		_assert(false, "setup: mission start/begin failed: %s" % bridge.last_error())
		return
	bridge.send_command({"type": "cmd", "name": "mission_end"})
	_assert(_pump_until(bridge, func(): return not bridge.mission_active()), "setup: mission_end was not answered in 5 s")
	var held: Dictionary = bridge.debrief_frame()
	var band := int(held.get("band", -1))
	_assert(band >= 0 and band < PLAYED_BANDS.size() and held.has("commander_fate"),
		"A39(b): after a played mission_end debrief_frame() must hold its frame (band 0-4, commander_fate), got %s" % JSON.stringify(held))
	var mark: int = bridge.sent.size()
	var root: Node = await _mount_debrief()
	var state: Dictionary = root.qa_state()
	_assert(band >= 0 and band < PLAYED_BANDS.size() and String(state.get("band", "")) == PLAYED_BANDS[band],
		"A39(b): the debrief must show the held band '%s', got %s" % [PLAYED_BANDS[band] if band >= 0 and band < PLAYED_BANDS.size() else "?", JSON.stringify(state)])
	_assert(not bool(state.get("error_panel", true)), "A39(b): a held frame must not show the error panel")
	_assert(_started_a_mission(bridge.sent, mark).is_empty(),
		"A39(b): the debrief must send no mission command, it sent %s" % str(bridge.sent.slice(mark)))
	root.queue_free()
	await process_frame
	SimSession.reset()
