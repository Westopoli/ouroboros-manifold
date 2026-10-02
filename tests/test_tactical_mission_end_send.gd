extends SceneTree

# C5-N (A43, docs/northstar/plans/2026-10-01-architect-rulings-2.md, Addendum 21): the
# tactical view ends the mission. At both routing sites (the End Mission button and a
# frame reporting mission_over) it sends `mission_end` through the bridge, waits for the
# debrief frame, then routes to 'debrief'. No frame means the error panel in place and no
# route, never an empty debrief. The debrief (A39) shows the held frame and starts nothing
# itself, so the view's send must be the ONLY mission_end of the mission.
# Rules: R-075-07 (mission termination), R-077-02 (debrief band), docs/architecture.md
# "session commands" (mission_end answers the debrief frame).
#
# Scenarios (each mounts the real tactical_view.tscn over a live mission):
#   S1 End Mission press, healthy pipe (positive control: no error panel, and nothing sent
#      or routed before the press)
#   S2 a tactical frame with mission_over true
#   S3 a bridge that swallows mission_end: the error panel shows, the route is not taken
# Style mirrors tests/test_briefing_refuse.gd.

const SCENE_PATH := "res://scenes/tactical_c/tactical_view.tscn"
const CBridge := preload("res://autoload/c_bridge.gd")
const PLAYED_BANDS := ["total_failure", "partial_failure", "partial_success", "strong_success", "total_success"]
const WAIT_MSEC := 15000


# A real c_bridge.gd that records the name of every command it sends and can drop some.
class CountBridge:
	extends "res://autoload/c_bridge.gd"
	var sent: Array = []
	var swallow: Array = []

	func send_command(cmd: Dictionary) -> void:
		var cmd_name := str(cmd.get("name", ""))
		sent.append(cmd_name)
		if swallow.has(cmd_name):
			return
		super.send_command(cmd)

var _pass_count := 0
var _fail_count := 0
var _fail_msgs: Array[String] = []
var _route_seen_held: Variant = null


func _initialize() -> void:
	await _run_tests()
	print("\n=== Tactical mission_end send Test Results ===")
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
	await _test_end_mission_press_sends_one_mission_end_and_debrief_shows_played_frame()
	await _test_mission_over_frame_sends_one_mission_end()
	await _test_no_debrief_frame_shows_error_panel_and_does_not_route()


func _router() -> Node:
	return get_root().get_node("SceneRouter")


# SceneRouter.go_to() ignores calls while a fade runs (the legacy SimBridge autoload also
# routes to error_screen at boot under --headless); wait it out.
func _settle_router() -> void:
	var deadline := Time.get_ticks_msec() + 5000
	while bool(_router().get("_transitioning")) and Time.get_ticks_msec() < deadline:
		await process_frame
	_assert(not bool(_router().get("_transitioning")), "setup: SceneRouter still transitioning after 5 s")


# Fresh session over a CountBridge, tactical view mounted on the live mission.
func _mount_view(swallow: Array = []) -> Array:
	await _settle_router()
	# The router keeps the last target name from an earlier scenario; clear it so a
	# stale 'debrief' cannot read as this scenario's route.
	_router().set("_current_scene_name", "tactical_c")
	var SimSession = load("res://autoload/sim_session.gd")
	SimSession.reset()
	var bridge := CountBridge.new()
	bridge.swallow = swallow
	SimSession._bridge = bridge
	var packed = load(SCENE_PATH)
	_assert(packed is PackedScene, "cannot load " + SCENE_PATH)
	var view: Node = (packed as PackedScene).instantiate()
	get_root().add_child(view)
	await process_frame
	await process_frame
	_assert(bridge.mission_begun(), "setup: the tactical view did not leave a begun live mission: %s" % bridge.last_error())
	return [view, bridge]


# Waits until the router targets 'debrief' or the view shows its error panel (up to
# WAIT_MSEC). Records whether a debrief frame was already held the first frame the route
# was seen, "route only after the frame is held".
func _wait_route_or_error(view: Node, bridge) -> void:
	_route_seen_held = null
	var deadline := Time.get_ticks_msec() + WAIT_MSEC
	while Time.get_ticks_msec() < deadline:
		if str(_router().get("_current_scene_name")) == "debrief":
			_route_seen_held = not bridge.debrief_frame().is_empty()
			return
		if bool(view.qa_state().get("error_panel", false)):
			return
		await process_frame


func _teardown(view: Node) -> void:
	await _settle_router()
	if is_instance_valid(view):
		view.queue_free()
	var current = current_scene
	if current != null and is_instance_valid(current):
		current.queue_free()
	await process_frame
	load("res://autoload/sim_session.gd").reset()


func _count(sent: Array, cmd_name: String) -> int:
	var n := 0
	for s in sent:
		if s == cmd_name:
			n += 1
	return n


# A43 + A39(b): End Mission sends exactly one mission_end, the route follows the held
# frame, the debrief then shows the played mission's frame. Includes the healthy-pipe
# positive control (no error panel anywhere).
func _test_end_mission_press_sends_one_mission_end_and_debrief_shows_played_frame() -> void:
	var mounted := await _mount_view()
	var view: Node = mounted[0]
	var bridge = mounted[1]
	var button = view.get_node_or_null("CanvasLayer/EndMission")
	_assert(button != null, "A43: no CanvasLayer/EndMission button on the tactical view")
	if button == null:
		await _teardown(view)
		return
	_assert(_count(bridge.sent, "mission_end") == 0,
		"A43 control: no mission_end may be sent before End Mission is pressed, sent %s" % str(bridge.sent))
	_assert(str(_router().get("_current_scene_name")) != "debrief", "A43 control: the view routed to debrief before End Mission")
	_assert(bridge.debrief_frame().is_empty(), "A43 control: no debrief frame before the mission ends")
	button.emit_signal("pressed")
	await _wait_route_or_error(view, bridge)
	_assert(str(_router().get("_current_scene_name")) == "debrief",
		"A43: End Mission must route to 'debrief' once the frame arrives (router '%s', error_panel %s, sent %s, error '%s')" % [
			str(_router().get("_current_scene_name")), str(view.qa_state().get("error_panel", false)), str(bridge.sent), bridge.last_error()])
	_assert(_route_seen_held == true,
		"A43: the route to 'debrief' must come only after the debrief frame is held (bridge.debrief_frame().band set), held at route: %s" % str(_route_seen_held))
	_assert(not bool(view.qa_state().get("error_panel", false)), "A43 control: a healthy pipe must not show the error panel")
	for i in 10:
		await process_frame
	_assert(_count(bridge.sent, "mission_end") == 1,
		"A43: End Mission must send EXACTLY ONE mission_end, sent %s" % str(bridge.sent))
	var held: Dictionary = bridge.debrief_frame()
	var band := int(held.get("band", -1))
	_assert(band >= 0 and band < PLAYED_BANDS.size() and held.has("commander_fate"),
		"A43: the held frame must be the played mission's (band 0-4, commander_fate), got %s" % JSON.stringify(held))
	# The router's own swap mounts the debrief scene; it must show the played frame.
	await _settle_router()
	var shown = current_scene
	_assert(shown != null and shown.has_method("qa_state"), "A43: the routed scene is not a debrief with qa_state()")
	if shown != null and shown.has_method("qa_state"):
		var state: Dictionary = shown.qa_state()
		_assert(band >= 0 and band < PLAYED_BANDS.size() and String(state.get("band", "")) == PLAYED_BANDS[band],
			"A43/A39: the debrief must show the played frame's band '%s', got %s" % [PLAYED_BANDS[band] if band >= 0 and band < PLAYED_BANDS.size() else "?", JSON.stringify(state)])
		_assert(not bool(state.get("error_panel", true)), "A43/A39: the debrief of a played mission must not show the error panel")
		_assert(_count(bridge.sent, "mission_end") == 1,
			"A43/A39: mounting the debrief must not end the mission again, sent %s" % str(bridge.sent))
	await _teardown(view)


# A43: the sim reporting the mission over (a tactical frame with mission_over true) is the
# second routing site; it sends exactly one mission_end too.
func _test_mission_over_frame_sends_one_mission_end() -> void:
	var mounted := await _mount_view()
	var view: Node = mounted[0]
	var bridge = mounted[1]
	_assert(_count(bridge.sent, "mission_end") == 0, "A43 control: no mission_end before the mission is over, sent %s" % str(bridge.sent))
	var over: Dictionary = bridge.tactical_frame().duplicate(true)
	_assert(not over.is_empty(), "setup: the bridge holds no tactical frame")
	over["mission_over"] = true
	view.load_frame(over)
	await _wait_route_or_error(view, bridge)
	_assert(str(_router().get("_current_scene_name")) == "debrief",
		"A43: a mission_over frame must route to 'debrief' once the frame arrives (router '%s', error_panel %s, sent %s)" % [
			str(_router().get("_current_scene_name")), str(view.qa_state().get("error_panel", false)), str(bridge.sent)])
	_assert(_route_seen_held == true,
		"A43: the mission_over route must come only after the debrief frame is held, held at route: %s" % str(_route_seen_held))
	for i in 10:
		await process_frame
	_assert(_count(bridge.sent, "mission_end") == 1,
		"A43: a mission_over frame must send EXACTLY ONE mission_end, sent %s" % str(bridge.sent))
	var band := int(bridge.debrief_frame().get("band", -1))
	_assert(band >= 0 and band < PLAYED_BANDS.size(),
		"A43: the held frame must be a played band 0-4, got %s" % JSON.stringify(bridge.debrief_frame()))
	await _teardown(view)


# A43: if the debrief frame does not arrive the view shows the error panel in place and does
# NOT route to an empty debrief. Both sites.
func _test_no_debrief_frame_shows_error_panel_and_does_not_route() -> void:
	for site in ["button", "mission_over"]:
		var mounted := await _mount_view(["mission_end"])
		var view: Node = mounted[0]
		var bridge = mounted[1]
		if site == "button":
			var button = view.get_node_or_null("CanvasLayer/EndMission")
			_assert(button != null, "A43: no CanvasLayer/EndMission button on the tactical view")
			if button == null:
				await _teardown(view)
				continue
			button.emit_signal("pressed")
		else:
			var over: Dictionary = bridge.tactical_frame().duplicate(true)
			over["mission_over"] = true
			view.load_frame(over)
		await _wait_route_or_error(view, bridge)
		_assert(_count(bridge.sent, "mission_end") >= 1,
			"A43 (%s): the view must have sent mission_end, sent %s" % [site, str(bridge.sent)])
		_assert(bool(view.qa_state().get("error_panel", false)),
			"A43 (%s): no debrief frame must show the error panel in place (qa_state error_panel), router '%s'" % [
				site, str(_router().get("_current_scene_name"))])
		for i in 10:
			await process_frame
		_assert(str(_router().get("_current_scene_name")) != "debrief",
			"A43 (%s): with no debrief frame the view must not route to an empty debrief" % site)
		_assert(bridge.debrief_frame().is_empty(), "A43 (%s): the swallowed mission_end holds no frame" % site)
		await _teardown(view)
