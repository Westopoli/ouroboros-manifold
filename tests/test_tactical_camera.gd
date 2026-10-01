extends SceneTree

# Plan item A6, unit A6a (docs/northstar/plans/2026-09-30-mission-plays-plan.md,
# Wave A): the tactical camera of res://scenes/tactical_c/tactical_view.tscn.
# Rules proved: E-16 S-103 R-103-01 (free camera, no forced follow, pan and
# zoom), R-103-02 (the canvas bounds the camera at any zoom), and the plan's
# "camera frames the player's force at mission start" (QA run qa-20260929-2143:
# the only own unit sat at screen y=22, clipped by the top edge).
#
# Controls the QA profile already assumes (agora projects/ouroboros/qa.toml,
# scripts/qa_tactical.py): pan = the arrow keys (Up/Down/Left/Right), zoom =
# the mouse wheel (up = in, down = out). Edge scroll = the mouse resting on a
# viewport edge. Q-103-04 leaves the final key choice open: this file pins only
# what the QA profile sends today.
#
# Readouts used (all exist in qa_state() today): camera {x,y} (world units),
# units_px (screen px of the units the local faction can see), local_faction,
# canvas. Zoom is read through the screen distance between two units, so no
# new qa_state key is required.
#
# Detector positive controls: C1 (a camera pushed away from the force makes the
# in-viewport detector report "outside"), C2 (no input leaves the camera where
# it was: pan tests would otherwise pass on a drifting camera), C3 (the same
# wheel notch applied the other way moves the distance the other way).
#
# Not covered here: the "enemy visible" bullet of A6 (waits on A2).

const SCENE_PATH := "res://scenes/tactical_c/tactical_view.tscn"
const DESIGN_W := 1920.0
const DESIGN_H := 1080.0
const HOLD_FRAMES := 20
const WHEEL_NOTCHES_TO_CLAMP := 400

var _pass_count := 0
var _fail_count := 0
var _fail_msgs: Array[String] = []


func _initialize() -> void:
	await _run_tests()
	print("\n=== Tactical Camera Test Results ===")
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
	var packed = load(SCENE_PATH)
	_assert(packed is PackedScene, "cannot load " + SCENE_PATH)
	if not (packed is PackedScene):
		return
	await _test_framing_live_mission_start_R103_01()
	await _test_framing_fixture_corners_R103_01()
	await _test_keys_pan_R103_01()
	await _test_edge_scroll_pans_R103_01()
	await _test_wheel_zoom_bounded_R103_01_R103_02()


# -- helpers ---------------------------------------------------------------

func _mount(stop_stepping: bool) -> Node:
	var v: Node = (load(SCENE_PATH) as PackedScene).instantiate()
	get_root().add_child(v)
	await process_frame
	if stop_stepping:
		# Same reason as tests/test_tactical_view.gd: _process() steps the live
		# mission and would replace any frame this file loads.
		v.set_process(false)
	await process_frame
	return v


func _unmount(v: Node) -> void:
	v.queue_free()
	await process_frame


func _viewport_size() -> Vector2:
	# Under --headless get_root().size is not trustworthy (100x100); the view
	# computes everything in the 1920x1080 design space, so use that.
	var vp := Vector2(get_root().size)
	if vp.x < 200.0 or vp.y < 200.0:
		vp = Vector2(DESIGN_W, DESIGN_H)
	return vp


func _unit_half(v: Node) -> float:
	var consts: Dictionary = v.get_script().get_script_constant_map()
	return float(consts.get("UNIT_SIZE", 24.0)) * 0.5


func _local_ids(st: Dictionary) -> Array:
	var out: Array = []
	var lf := int(st.get("local_faction", 0))
	for id in st.get("units", {}):
		if int((st["units"][id] as Dictionary).get("faction", -1)) == lf:
			out.append(str(id))
	out.sort()
	return out


# Returns the ids of the local faction's units whose whole sprite (px +- half
# a unit) is NOT inside the viewport, or not drawn at all.
func _not_inside(v: Node) -> Array:
	var st: Dictionary = v.qa_state()
	var vp := _viewport_size()
	var half := _unit_half(v)
	var px: Dictionary = st.get("units_px", {})
	var bad: Array = []
	for id in _local_ids(st):
		if not px.has(id):
			bad.append(id)
			continue
		var p: Array = px[id]
		if p[0] - half < 0.0 or p[0] + half > vp.x or p[1] - half < 0.0 or p[1] + half > vp.y:
			bad.append(id)
	return bad


func _unit(id: int, faction: int, x: float, y: float) -> Dictionary:
	return {"id": id, "faction": faction, "type": 0, "tier": 0, "x": x, "y": y,
		"hp": 100.0, "layer": 0, "facing": 0.0, "target": -1, "state": 0}


# A fresh frame whose player force (faction 0, six units 100 wu apart) is
# centred on (fx, fy); one enemy unit far from it. canvas differs from any live
# mission canvas so the view treats it as a new mission.
func _frame(canvas: float, fx: float, fy: float) -> Dictionary:
	var units: Array = []
	for i in range(6):
		units.append(_unit(i + 1, 0, fx + (i - 2.5) * 100.0, fy))
	units.append(_unit(100, 1, canvas - fx, canvas - fy))
	return {"type": "tactical", "tick": 0, "mission_over": false, "band": -1, "player_faction": 0,
		"map": {"canvas": canvas, "nodes": [], "cover": [], "obstacles": []},
		"units": units, "visible": {"0": [1, 2, 3, 4, 5, 6], "1": [100]}}


# Mouse events carry window coordinates; the viewport maps them to design
# space through the stretch transform (headless: a 64x64 window, scale 1/30).
func _win(p: Vector2) -> Vector2:
	return get_root().get_final_transform() * p


func _key(code: int, pressed: bool) -> void:
	var e := InputEventKey.new()
	e.keycode = code
	e.physical_keycode = code
	e.pressed = pressed
	Input.parse_input_event(e)


func _wheel(up: bool, at: Vector2) -> void:
	var e := InputEventMouseButton.new()
	e.button_index = MOUSE_BUTTON_WHEEL_UP if up else MOUSE_BUTTON_WHEEL_DOWN
	e.pressed = true
	e.position = _win(at)
	e.global_position = e.position
	e.factor = 1.0
	Input.parse_input_event(e)


func _mouse_to(p: Vector2) -> void:
	var e := InputEventMouseMotion.new()
	e.position = _win(p)
	e.global_position = e.position
	Input.parse_input_event(e)


func _frames(n: int) -> void:
	for i in range(n):
		await process_frame


func _cam(v: Node) -> Vector2:
	var c: Dictionary = v.qa_state().get("camera", {})
	return Vector2(float(c.get("x", 0.0)), float(c.get("y", 0.0)))


func _px_dist(v: Node, a: String, b: String) -> float:
	var px: Dictionary = v.qa_state().get("units_px", {})
	if not px.has(a) or not px.has(b):
		return -1.0
	return Vector2(px[a][0], px[a][1]).distance_to(Vector2(px[b][0], px[b][1]))


# -- A6a-1: framing --------------------------------------------------------

# R-103-01 / plan A6 bullet 1. Straight off the live mission the view mounts
# into (no fixture): the player's force must be on screen, every sprite whole.
func _test_framing_live_mission_start_R103_01() -> void:
	var v := await _mount(true)
	var st: Dictionary = v.qa_state()
	var locals := _local_ids(st)
	_assert(locals.size() > 0, "A6a-1 setup: the live mission frame carries no unit of the local faction (live load failed?)")
	if locals.size() > 0:
		var bad := _not_inside(v)
		_assert(bad.is_empty(),
			"A6a-1 R-103-01: at mission start %d of %d own units are not fully inside the %s viewport (first: %s at %s)"
			% [bad.size(), locals.size(), str(_viewport_size()), str(bad[0]) if bad.size() > 0 else "-",
				str(st.get("units_px", {}).get(bad[0])) if bad.size() > 0 else "-"])
	await _unmount(v)


# Same rule on two synthetic frames whose force hugs a canvas corner (the
# shape of the QA evidence), so a camera hard-coded to the canvas centre or to
# one corner cannot pass. The force is 60 wu from the edge: the unit centre is
# well inside the map but, centred camera at fit zoom, clipped on screen.
func _test_framing_fixture_corners_R103_01() -> void:
	var cases := [["top-edge", 0.5, 60.0, true], ["bottom-right-corner", 1.0, 60.0, false]]
	for c in cases:
		var v := await _mount(true)
		var live_canvas := float(v.qa_state().get("canvas", 0.0))
		var cv := 9000.0 if not is_equal_approx(live_canvas, 9000.0) else 9100.0
		var fx: float = cv * float(c[1]) if c[1] < 1.0 else cv - float(c[2])
		var fy: float = float(c[2]) if c[3] else cv - float(c[2])
		v.load_frame(_frame(cv, fx, fy))
		await process_frame
		var bad := _not_inside(v)
		_assert(bad.is_empty(),
			"A6a-1 R-103-01 [%s]: %d of 6 own units not fully inside the viewport after the frame loads (camera %s)"
			% [c[0], bad.size(), str(_cam(v))])

		# C1 positive control: push the camera to the opposite side of the map;
		# the detector must now report units outside, or it detects nothing.
		v.qa_pan(cv - fx, cv - fy)
		await process_frame
		_assert(_not_inside(v).size() > 0,
			"A6a-1 control C1 [%s]: with the camera panned to the far side the in-viewport detector still reports every own unit inside" % c[0])
		await _unmount(v)


# -- A6a-2: pan ------------------------------------------------------------

# R-103-01: keys pan the camera freely; no forced follow. Runs on the live
# view with processing on, so held-key panning in _process() is exercised.
func _test_keys_pan_R103_01() -> void:
	var v := await _mount(false)
	var canvas := float(v.qa_state().get("canvas", 0.0))
	_assert(canvas > 0.0, "A6a-2 setup: no canvas in the live frame")
	if canvas <= 0.0:
		await _unmount(v)
		return
	var mid := canvas * 0.5
	# Park the pointer mid-screen: a pointer resting on an edge is an edge scroll.
	_mouse_to(get_root().get_visible_rect().size * 0.5)
	await _frames(2)

	# C2 control: idle frames never move the camera (no auto-follow, R-103-01).
	v.qa_pan(mid, mid)
	await _frames(HOLD_FRAMES)
	_assert(_cam(v).is_equal_approx(Vector2(mid, mid)),
		"A6a-2 control C2 R-103-01: camera drifted from (%s,%s) to %s with no input (forced follow or drift)" % [mid, mid, str(_cam(v))])

	var cases := [["Up", KEY_UP, Vector2(0, -1)], ["Down", KEY_DOWN, Vector2(0, 1)],
		["Left", KEY_LEFT, Vector2(-1, 0)], ["Right", KEY_RIGHT, Vector2(1, 0)]]
	for c in cases:
		v.qa_pan(mid, mid)
		await process_frame
		var before := _cam(v)
		_key(int(c[1]), true)
		await _frames(HOLD_FRAMES)
		_key(int(c[1]), false)
		await process_frame
		var d := _cam(v) - before
		var dir: Vector2 = c[2]
		_assert(d.dot(dir) > 0.0,
			"A6a-2 R-103-01: holding %s moved the camera by %s, expected motion along %s" % [c[0], str(d), str(dir)])
		_assert(absf(d.dot(Vector2(dir.y, dir.x))) < 0.001,
			"A6a-2 R-103-01: holding %s also moved the camera across the axis (delta %s)" % [c[0], str(d)])

	# R-103-02: holding a key forever against the edge never leaves the canvas.
	v.qa_pan(1.0, 1.0)
	await process_frame
	_key(KEY_LEFT, true)
	_key(KEY_UP, true)
	await _frames(HOLD_FRAMES * 3)
	_key(KEY_LEFT, false)
	_key(KEY_UP, false)
	await process_frame
	var c0 := _cam(v)
	_assert(c0.x >= 0.0 and c0.y >= 0.0 and c0.x <= canvas and c0.y <= canvas,
		"A6a-2 R-103-02: camera %s left the 0..%s canvas after panning against the edge" % [str(c0), str(canvas)])
	await _unmount(v)


# R-103-01 "edge-scrolls": the mouse resting on a viewport edge pans toward
# that edge; resting mid-screen does not.
func _test_edge_scroll_pans_R103_01() -> void:
	var v := await _mount(false)
	var canvas := float(v.qa_state().get("canvas", 0.0))
	_assert(canvas > 0.0, "A6a-2 setup: no canvas in the live frame")
	if canvas <= 0.0:
		await _unmount(v)
		return
	var mid := canvas * 0.5
	# The visible rect (1920x1920 under headless expand-stretch, 1920x1080 on a
	# real window) is where the screen edges are; every edge is hit on both.
	var vp := get_root().get_visible_rect().size
	var cases := [["left", Vector2(0.0, vp.y * 0.5), Vector2(-1, 0)], ["right", Vector2(vp.x - 1.0, vp.y * 0.5), Vector2(1, 0)],
		["top", Vector2(vp.x * 0.5, 0.0), Vector2(0, -1)], ["bottom", Vector2(vp.x * 0.5, vp.y - 1.0), Vector2(0, 1)]]
	for c in cases:
		v.qa_pan(mid, mid)
		_mouse_to(vp * 0.5)
		await _frames(2)
		var before := _cam(v)
		_mouse_to(c[1])
		await _frames(HOLD_FRAMES)
		var d := _cam(v) - before
		_mouse_to(vp * 0.5)
		await process_frame
		_assert(d.dot(c[2]) > 0.0,
			"A6a-2 R-103-01: mouse resting on the %s edge moved the camera by %s, expected motion toward that edge" % [c[0], str(d)])
		# The pointer back mid-screen: the camera stops.
		var settled := _cam(v)
		await _frames(HOLD_FRAMES)
		_assert(_cam(v).is_equal_approx(settled),
			"A6a-2 R-103-01: camera kept moving (%s -> %s) after the pointer left the %s edge" % [str(settled), str(_cam(v)), c[0]])
	await _unmount(v)


# -- A6a-3: wheel zoom -----------------------------------------------------

# R-103-01 (zoom) and R-103-02: wheel up zooms in, wheel down zooms out, both
# stop at a bound, and the camera never leaves the canvas at any zoom. Zoom is
# read as the screen distance between two own units on a fixture frame (the
# live force stands on one pixel, so it cannot show zoom).
func _test_wheel_zoom_bounded_R103_01_R103_02() -> void:
	var v := await _mount(true)
	var live_canvas := float(v.qa_state().get("canvas", 0.0))
	var canvas := 9000.0 if not is_equal_approx(live_canvas, 9000.0) else 9100.0
	v.load_frame(_frame(canvas, canvas * 0.5, canvas * 0.5))
	await process_frame
	var centre := _viewport_size() * 0.5
	var d0 := _px_dist(v, "1", "6")
	_assert(d0 > 0.0, "A6a-3 setup: units 1 and 6 are not both drawn on the fixture frame")

	_wheel(true, centre)
	await _frames(2)
	var d_in := _px_dist(v, "1", "6")
	_assert(d_in > d0, "A6a-3 R-103-01: one wheel-up notch left unit spacing at %s px (was %s); expected zoom in" % [d_in, d0])

	# C3 control: the opposite notch moves the other way, so "changed" is not
	# just any jitter.
	_wheel(false, centre)
	_wheel(false, centre)
	await _frames(2)
	var d_out := _px_dist(v, "1", "6")
	_assert(d_out < d_in, "A6a-3 control C3 R-103-01: wheel-down did not shrink unit spacing (%s px after, %s px before)" % [d_out, d_in])

	# Bounded in: hammering the wheel reaches a ceiling (the 2nd batch changes
	# nothing). Bounded out: same on the floor, and the spacing stays > 0.
	for i in range(WHEEL_NOTCHES_TO_CLAMP):
		_wheel(true, centre)
	await _frames(2)
	var in_a := _px_dist(v, "1", "6")
	for i in range(WHEEL_NOTCHES_TO_CLAMP):
		_wheel(true, centre)
	await _frames(2)
	var in_b := _px_dist(v, "1", "6")
	_assert(in_a > d0 and absf(in_a - in_b) <= 0.001 * maxf(in_a, 1.0),
		"A6a-3 R-103-01: zoom-in has no bound (spacing %s px after %d notches, %s px after %d more)" % [in_a, WHEEL_NOTCHES_TO_CLAMP, in_b, WHEEL_NOTCHES_TO_CLAMP])
	var cam_in := _cam(v)
	_assert(cam_in.x >= 0.0 and cam_in.y >= 0.0 and cam_in.x <= canvas and cam_in.y <= canvas,
		"A6a-3 R-103-02: camera %s outside the 0..%s canvas at max zoom-in" % [str(cam_in), str(canvas)])

	for i in range(WHEEL_NOTCHES_TO_CLAMP * 2):
		_wheel(false, centre)
	await _frames(2)
	var out_a := _px_dist(v, "1", "6")
	for i in range(WHEEL_NOTCHES_TO_CLAMP):
		_wheel(false, centre)
	await _frames(2)
	var out_b := _px_dist(v, "1", "6")
	_assert(out_a > 0.0 and out_a < in_b and absf(out_a - out_b) <= 0.001 * maxf(out_a, 1.0),
		"A6a-3 R-103-01: zoom-out has no bound or collapsed (spacing %s px, then %s px; zoomed-in was %s)" % [out_a, out_b, in_b])
	var cam_out := _cam(v)
	_assert(cam_out.x >= 0.0 and cam_out.y >= 0.0 and cam_out.x <= canvas and cam_out.y <= canvas,
		"A6a-3 R-103-02: camera %s outside the 0..%s canvas at max zoom-out" % [str(cam_out), str(canvas)])
	await _unmount(v)
