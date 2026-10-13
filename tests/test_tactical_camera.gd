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
#
# VG-A18 (2026-10-12), the camera at mission start (spec 2026-10-07-visible-game-spec.md
# Rev 12d, paragraph "A18, the camera at mission start"; ledger FINDING-camera-start-framing).
# Rules the new cases prove, word for word:
#   R-103-01 (docs/bible/epics/E-16-client-camera-hud-and-world-view.md:32): "Given a mission, When the player
#     pans, zooms, or edge-scrolls, Then the camera moves freely with no forced follow; the classic view has one
#     auto-anchor home the player returns to by key, and the designed views of R-103-05 and R-103-06 are the only
#     camera modes."
#   R-103-02 (E-16:33): "Given any zoom level, When the viewport is read, Then the mission canvas edges bound the
#     camera; it never leaves the map."
#   R-246-07 (docs/bible/epics/E-17, :397): "each faction's army spawns in a cleared pocket at its home base (the
#     faction's anchor, where its first economy area and structures stand)"
#   Westley 2026-10-12 on the camera at mission start: "yes, of your base" (spec A18: the opening view is "of your base").
# The bible has NO rule that names the margin or the home key: R-103-01 says only "one auto-anchor home the player
# returns to by key". The margin and the key come from the Architect's gap rulings of 2026-10-12, which are used here:
#   G2: the margin is 10% of the viewport per side (DRAFT-a18-margin), zoom clamp ZOOM_MAX / ZOOM_STEP, R-103-02 binds
#       the camera centre (not the view rectangle). Read as 10% of the viewport dimension along each axis:
#       192 px on the left and right edges, 108 px on the top and bottom edges of the 1920 x 1080 design space.
#   G3: the player's spawn point is the kind-7 map node nearest the centroid of the own units.
#   G4: the home key is KEY_HOME (DRAFT-a18-home-key); Home restores the stored opening camera and zoom.
#   G5: the 2D path only (these fixtures are space-era frames); the 3D rig fit is FU-A18-3d, not tested here.
#   G6: no existing assertion of this file changes; only the groups below are added.
#   G7 / G8 (not ruled, the null actions stand): the framed set is the local faction's own units only (no visible
#       enemy, no sight term) plus the spawn point plus the own lots; an empty set keeps today's zoom 1.0 and canvas centre.
# The framed set P: own units, the spawn point, every frame["lots"] row whose owner == the local faction (owner -1 is
# neutral and not in P). The box B is the bounding box of P; the zoom is the one at which B, inset by the margin on
# each side, fills the viewport (clamped 1.0 .. ZOOM_MAX / ZOOM_STEP); the camera centre is the centre of B, clamped to
# 0..canvas. A world point is on screen when 0 <= sx < 1920 and 0 <= sy < 1080 (the daemon verb "project"); an own unit
# is inside when its px +- UNIT_SIZE / 2 is (_not_inside, unchanged).
# New groups (controls first): C-A, C-B, C-D controls; MARGIN (R-103-01 + G2), SPAWN (R-246-07 + G3), OWN LOTS
# (R-246-07 + R-103-01), OWN UNITS ONLY (G7), HOME KEY (R-103-01 + G4), CANVAS BOUND (R-103-02), EMPTY SET (G8).

const SCENE_PATH := "res://scenes/tactical_c/tactical_view.tscn"
const DESIGN_W := 1920.0
const DESIGN_H := 1080.0
const HOLD_FRAMES := 20
const WHEEL_NOTCHES_TO_CLAMP := 400
# spec Rev 12d A18, DRAFT-a18-margin (untagged in the spec): the margin around the framed box is 10% of the viewport on
# each side (Architect gap ruling G2, 2026-10-12): x edges at 0.1 * 1920 = 192 px, y edges at 0.1 * 1080 = 108 px.
const MARGIN_SHARE := 0.1
# One display pixel: the allowed slack when comparing a screen position or a camera or scale difference with a number
# the rulings give. It comes from the float of the screen formula (sx = (wx - cam.x) * scale + SCREEN_W / 2, double
# arithmetic: the real error is far below it); no tolerance wider than this is used.
const ONE_PX := 1.0
const SPAWN_KIND := 7  # the map node kind of a player spawn (the live mission frame: nodes of kind 7 at (11950, 150) and (11950, 23850))
const ZOOM_CEIL := 40.0 / 1.25  # ZOOM_MAX / ZOOM_STEP of tactical_view.gd:26-27 (G8 clamp)

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
	await _test_a18_controls()
	await _test_a18_margin_R103_01()
	await _test_a18_spawn_R246_07()
	await _test_a18_own_lots_R246_07()
	await _test_a18_own_units_only_G7()
	await _test_a18_home_key_R103_01()
	await _test_a18_canvas_bound_R103_02()
	await _test_a18_empty_set_G8()


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


# -- VG-A18: the camera at mission start ------------------------------------

# A fixture frame (space era, 2D). own: Array of Vector2 (faction 0, ids 1..n, all visible to faction 0); enemies:
# Array of Vector2 (faction 1, ids 100..; `enemy_seen` puts them in the local faction's visible list); nodes: map
# nodes; lots: lot rows; sight: a "sight" field on every own unit (0.0 = absent, as the other fixtures). tick 0 and a
# canvas that differs from the live one make the view treat it as a new mission, as _frame() does.
func _frame_ex(canvas: float, own: Array, enemies: Array, nodes: Array, lots: Array, enemy_seen := false, sight := 0.0) -> Dictionary:
	var units: Array = []
	var seen: Array = []
	for i in range(own.size()):
		var u := _unit(i + 1, 0, own[i].x, own[i].y)
		if sight > 0.0:
			u["sight"] = sight
		units.append(u)
		seen.append(i + 1)
	var foes: Array = []
	for i in range(enemies.size()):
		units.append(_unit(100 + i, 1, enemies[i].x, enemies[i].y))
		foes.append(100 + i)
		if enemy_seen:
			seen.append(100 + i)
	return {"type": "tactical", "tick": 0, "mission_over": false, "band": -1, "player_faction": 0,
		"map": {"canvas": canvas, "nodes": nodes, "cover": [], "obstacles": []},
		"units": units, "visible": {"0": seen, "1": foes}, "lots": lots}


func _map_node(i: int, kind: int, x: float, y: float) -> Dictionary:
	return {"i": i, "kind": kind, "x": x, "y": y}


# A lot row as c_bridge.gd _lot_row builds it: {id, x, y, stage, building, owner}.
func _lot(id: int, x: float, y: float, owner: int) -> Dictionary:
	return {"id": id, "x": x, "y": y, "stage": 2, "building": 0, "owner": owner}


# A fixture canvas that differs from the live mission's canvas (24000 at the dump of 2026-10-13).
func _fixture_canvas(v: Node) -> float:
	var live_canvas := float(v.qa_state().get("canvas", 0.0))
	return 9000.0 if not is_equal_approx(live_canvas, 9000.0) else 9100.0


# The 2D screen formula of tactical_view.gd _to_screen (assumption b), read from the qa_state camera and scale.
func _screen_of(v: Node, wx: float, wy: float) -> Vector2:
	var st: Dictionary = v.qa_state()
	var c: Dictionary = st["camera"]
	var s := float(st["scale"])
	return Vector2((wx - float(c["x"])) * s + DESIGN_W * 0.5, (wy - float(c["y"])) * s + DESIGN_H * 0.5)


# A world point is on screen when 0 <= sx < 1920 and 0 <= sy < 1080 (the daemon verb "project").
func _on_screen(p: Vector2) -> bool:
	return p.x >= 0.0 and p.x < DESIGN_W and p.y >= 0.0 and p.y < DESIGN_H


func _scale(v: Node) -> float:
	return float(v.qa_state().get("scale", 0.0))


# Controls: the predicate for a lot is trustworthy and the harness reaches the view.
func _test_a18_controls() -> void:
	var v := await _mount(true)
	var cv := _fixture_canvas(v)
	var p := Vector2(3000.0, 4200.0)
	v.load_frame(_frame_ex(cv, [p], [], [], [_lot(1, p.x, p.y, 0)]))
	await process_frame
	var st: Dictionary = v.qa_state()
	var era := get_root().get_node_or_null("/root/EraConfig")
	var era_kind: String = era.kind() if era != null else "missing"
	_assert(era_kind == "space", "A18 setup: EraConfig.kind() is %s; these fixtures are space-era (2D path, G5)" % era_kind)
	# C-A: a lot at the same world point as an own unit lands on the unit's px by the 2D formula (and by the view's own
	# _to_screen, which the daemon verb "project" calls), so the on-screen predicate of a lot can be trusted.
	var unit_px: Array = st["units_px"].get("1", [])
	_assert(unit_px.size() == 2, "A18 control C-A: unit 1 is not drawn on the control fixture (units_px %s)" % str(st["units_px"]))
	if unit_px.size() == 2:
		var lot_px := _screen_of(v, p.x, p.y)
		_assert(lot_px.distance_to(Vector2(unit_px[0], unit_px[1])) <= ONE_PX,
			"A18 control C-A: the screen formula puts the lot at %s but units_px puts the unit at the same world point at %s" % [str(lot_px), str(unit_px)])
		var proj: Array = v._to_screen(p.x, p.y)
		_assert(Vector2(proj[0], proj[1]).distance_to(lot_px) <= ONE_PX,
			"A18 control C-A: the view's _to_screen (the verb project) gives %s, the formula %s" % [str(proj), str(lot_px)])
	# C-B: the predicate reports a point 5000 wu away as NOT on screen (this fixture's scale is the zoom ceiling, 3.84 px/wu).
	var cam := _cam(v)
	_assert(_scale(v) * 5000.0 > DESIGN_W,
		"A18 control C-B setup: scale %s puts 5000 wu inside the viewport width, the point could never be off screen" % _scale(v))
	_assert(not _on_screen(_screen_of(v, cam.x + 5000.0, cam.y)),
		"A18 control C-B: a point 5000 wu to the right of the camera is reported on screen at %s" % str(_screen_of(v, cam.x + 5000.0, cam.y)))
	_assert(not _on_screen(_screen_of(v, cam.x, cam.y - 5000.0)),
		"A18 control C-B: a point 5000 wu above the camera is reported on screen at %s" % str(_screen_of(v, cam.x, cam.y - 5000.0)))
	_assert(_on_screen(_screen_of(v, cam.x, cam.y)), "A18 control C-B: the camera centre itself is reported off screen")
	await _unmount(v)
	# C-D: an injected key press reaches the view's _unhandled_input (KEY_A arms the attack-move mode), so a Home key
	# that does nothing is the feature missing and not the injection broken.
	var v2 := await _mount(true)
	_assert(not bool(v2.get("_attack_move_mode")), "A18 control C-D setup: attack-move mode is already armed")
	_key(KEY_A, true)
	await process_frame
	_key(KEY_A, false)
	await process_frame
	_assert(bool(v2.get("_attack_move_mode")), "A18 control C-D: an injected KEY_A press did not reach the view (the key injection is broken)")
	await _unmount(v2)


# MARGIN. R-103-01 (the camera frames the player's base at mission start) with the G2 ruling "10% of the viewport per
# side (DRAFT-a18-margin)": the box of own units stands exactly 192 px (x) or 108 px (y) from the viewport edges on the
# limiting axis. Red today: the camera sits flush (A19 leaves 48 px, V2) and the sight term would shift it further.
func _test_a18_margin_R103_01() -> void:
	var cases := [
		# [name, own box lo, own box hi, expected inset of the limiting axis in px, limiting axis]
		["wider than tall", Vector2(3000.0, 4000.0), Vector2(4800.0, 4400.0), MARGIN_SHARE * DESIGN_W, 0],
		["taller than wide", Vector2(4000.0, 3000.0), Vector2(4400.0, 4800.0), MARGIN_SHARE * DESIGN_H, 1]]
	for c in cases:
		var v := await _mount(true)
		var cv := _fixture_canvas(v)
		var lo: Vector2 = c[1]
		var hi: Vector2 = c[2]
		var mid := (lo + hi) * 0.5
		# Four corners and two mid points of the box; the spawn node stands inside the box so it does not move it.
		var own := [lo, hi, Vector2(lo.x, hi.y), Vector2(hi.x, lo.y), Vector2(mid.x, lo.y), Vector2(mid.x, hi.y)]
		v.load_frame(_frame_ex(cv, own, [], [_map_node(0, SPAWN_KIND, mid.x, mid.y)], []))
		await process_frame
		var a: int = c[4]
		var inset: float = c[3]
		var p_lo := _screen_of(v, lo.x, lo.y)
		var p_hi := _screen_of(v, hi.x, hi.y)
		var extent: float = DESIGN_W if a == 0 else DESIGN_H
		_assert(absf(p_lo[a] - inset) <= ONE_PX,
			"A18 MARGIN G2 R-103-01 [%s]: the box low edge is at %s px on axis %d, expected the margin %s px (10%% of the viewport)" % [c[0], p_lo[a], a, inset])
		_assert(absf(p_hi[a] - (extent - inset)) <= ONE_PX,
			"A18 MARGIN G2 R-103-01 [%s]: the box high edge is at %s px on axis %d, expected %s px (the viewport edge less 10%%)" % [c[0], p_hi[a], a, extent - inset])
		# The other axis is centred on the box (the camera centre is the centre of B).
		var b := 1 - a
		var cam := _cam(v)
		_assert(absf((p_lo[b] + p_hi[b]) * 0.5 - (DESIGN_W if b == 0 else DESIGN_H) * 0.5) <= ONE_PX and cam.distance_to(mid) * _scale(v) <= ONE_PX,
			"A18 MARGIN G2 [%s]: the camera %s is not the centre of the box %s" % [c[0], str(cam), str(mid)])
		_assert(_not_inside(v).is_empty(), "A18 MARGIN R-103-01 [%s]: own units not fully inside the viewport: %s" % [c[0], str(_not_inside(v))])
		await _unmount(v)


# SPAWN. R-246-07 (the army spawns at its home base) and G3 (the player's spawn point is the kind-7 node nearest the own
# centroid): a spawn node placed away from the units is on screen after load_frame, the farther kind-7 node and a kind-0
# node are not framed (the scale equals a twin frame that carries only the spawn node). Red today: map nodes are not read.
func _test_a18_spawn_R246_07() -> void:
	var v := await _mount(true)
	var cv := _fixture_canvas(v)
	var own := [Vector2(2000.0, 4500.0), Vector2(2400.0, 4500.0), Vector2(2000.0, 4600.0), Vector2(2400.0, 4600.0)]
	var spawn := Vector2(2200.0, 800.0)  # 3700 wu from the own centroid (2200, 4550): the nearest kind-7 node
	var far_kind7 := _map_node(2, SPAWN_KIND, 6800.0, 4550.0)  # 4600 wu from the centroid
	var kind0 := _map_node(0, 0, 8500.0, 8500.0)
	v.load_frame(_frame_ex(cv, own, [], [kind0, _map_node(1, SPAWN_KIND, spawn.x, spawn.y), far_kind7], []))
	await process_frame
	var p := _screen_of(v, spawn.x, spawn.y)
	_assert(_on_screen(p), "A18 SPAWN R-246-07 G3: the spawn node (%s, %s) is off screen at %s after load_frame (camera %s, scale %s)" % [spawn.x, spawn.y, str(p), str(_cam(v)), _scale(v)])
	_assert(_not_inside(v).is_empty(), "A18 SPAWN R-246-07: own units not fully inside the viewport: %s" % str(_not_inside(v)))
	var scale_full := _scale(v)
	var cam_full := _cam(v)
	# Twin: only the spawn node. The farther kind-7 node and the kind-0 node must not change the framing.
	v.load_frame(_frame_ex(cv, own, [], [_map_node(1, SPAWN_KIND, spawn.x, spawn.y)], []))
	await process_frame
	_assert(is_equal_approx(_scale(v), scale_full) and _cam(v).is_equal_approx(cam_full),
		"A18 SPAWN G3: with a farther kind-7 node and a kind-0 node the framing is scale %s camera %s; without them scale %s camera %s (only the nearest kind-7 node is the spawn point)" % [scale_full, str(cam_full), _scale(v), str(_cam(v))])
	await _unmount(v)


# OWN LOTS. R-246-07 (home base: where the faction's first economy area and structures stand) and Westley "yes, of your
# base": two own lots placed away from the units are on screen; an enemy lot and a neutral lot (owner -1) far on the
# opposite side are not in the box (scale and camera equal a twin without those two rows). Red today: lots are not read.
func _test_a18_own_lots_R246_07() -> void:
	var v := await _mount(true)
	var cv := _fixture_canvas(v)
	var own := [Vector2(2000.0, 4500.0), Vector2(2400.0, 4500.0), Vector2(2000.0, 4600.0), Vector2(2400.0, 4600.0)]
	var mine_a := _lot(10, 3800.0, 3000.0, 0)
	var mine_b := _lot(11, 1500.0, 5600.0, 0)
	var foe := _lot(12, 8200.0, 8200.0, 1)
	var neutral := _lot(13, 8400.0, 8000.0, -1)
	v.load_frame(_frame_ex(cv, own, [], [], [mine_a, mine_b, foe, neutral]))
	await process_frame
	for l in [mine_a, mine_b]:
		var p := _screen_of(v, l["x"], l["y"])
		_assert(_on_screen(p), "A18 OWN LOTS R-246-07: own lot %d at (%s, %s) is off screen at %s after load_frame (camera %s, scale %s)" % [l["id"], l["x"], l["y"], str(p), str(_cam(v)), _scale(v)])
	_assert(_not_inside(v).is_empty(), "A18 OWN LOTS R-246-07: own units not fully inside the viewport: %s" % str(_not_inside(v)))
	var scale_all := _scale(v)
	var cam_all := _cam(v)
	v.load_frame(_frame_ex(cv, own, [], [], [mine_a, mine_b]))
	await process_frame
	_assert(is_equal_approx(_scale(v), scale_all) and _cam(v).is_equal_approx(cam_all),
		"A18 OWN LOTS: with an enemy lot and a neutral lot the framing is scale %s camera %s; without them scale %s camera %s (only owner == local faction lots are framed)" % [scale_all, str(cam_all), _scale(v), str(_cam(v))])
	await _unmount(v)


# OWN UNITS ONLY (G7, not ruled: the null action stands). A visible enemy unit far away and a sight field on the own
# units change nothing: the framing equals a twin without them. Red today: the framing includes visible units and a sight term.
func _test_a18_own_units_only_G7() -> void:
	var v := await _mount(true)
	var cv := _fixture_canvas(v)
	var own := [Vector2(3000.0, 4000.0), Vector2(4800.0, 4400.0), Vector2(3900.0, 4200.0)]
	var nodes := [_map_node(0, SPAWN_KIND, 3900.0, 4200.0)]
	v.load_frame(_frame_ex(cv, own, [Vector2(7500.0, 7500.0)], nodes, [], true, 300.0))
	await process_frame
	var scale_busy := _scale(v)
	var cam_busy := _cam(v)
	v.load_frame(_frame_ex(cv, own, [], nodes, []))
	await process_frame
	_assert(is_equal_approx(_scale(v), scale_busy) and _cam(v).is_equal_approx(cam_busy),
		"A18 OWN UNITS ONLY G7: with a visible enemy unit and a sight field the framing is scale %s camera %s; the own units alone give scale %s camera %s" % [scale_busy, str(cam_busy), _scale(v), str(_cam(v))])
	await _unmount(v)


# HOME KEY. R-103-01 "the classic view has one auto-anchor home the player returns to by key" with G4: KEY_HOME restores
# the stored opening camera and zoom. Red today: no key is bound.
func _test_a18_home_key_R103_01() -> void:
	var v := await _mount(true)
	var cv := _fixture_canvas(v)
	var lo := Vector2(3000.0, 4000.0)
	var hi := Vector2(4800.0, 4400.0)
	var mid := (lo + hi) * 0.5
	v.load_frame(_frame_ex(cv, [lo, hi], [], [_map_node(0, SPAWN_KIND, mid.x, mid.y)], []))
	await process_frame
	var cam0 := _cam(v)
	var scale0 := _scale(v)
	# Move away: pan with qa_pan and zoom with the wheel (a control: the camera and the scale really did move).
	v.qa_pan(cam0.x + 2500.0, cam0.y - 1500.0)
	var centre := _viewport_size() * 0.5
	for i in range(3):
		_wheel(true, centre)
	await _frames(2)
	_assert((_cam(v) - cam0).length() * scale0 > ONE_PX and absf(_scale(v) - scale0) * (hi.x - lo.x) > ONE_PX,
		"A18 HOME KEY control: the pan and the wheel left camera %s (opening %s) and scale %s (opening %s)" % [str(_cam(v)), str(cam0), _scale(v), scale0])
	_key(KEY_HOME, true)
	await process_frame
	_key(KEY_HOME, false)
	await _frames(2)
	var cam1 := _cam(v)
	var scale1 := _scale(v)
	_assert((cam1 - cam0).length() * scale0 <= ONE_PX,
		"A18 HOME KEY R-103-01 G4: after KEY_HOME the camera is %s, the opening camera was %s" % [str(cam1), str(cam0)])
	_assert(absf(scale1 - scale0) * (hi.x - lo.x) <= ONE_PX,
		"A18 HOME KEY R-103-01 G4: after KEY_HOME the scale is %s, the opening scale was %s" % [scale1, scale0])
	await _unmount(v)


# CANVAS BOUND. R-103-02: the camera centre stays inside 0..canvas at the opening zoom, and the own units stand on
# screen, for a box at the canvas corner (the view rectangle reaches past the canvas edge; the ruling G2 binds the
# centre, not the rectangle, so own units must still be on screen). Green or red today: see the report.
func _test_a18_canvas_bound_R103_02() -> void:
	var v := await _mount(true)
	var cv := _fixture_canvas(v)
	var own := [Vector2(20.0, 20.0), Vector2(1520.0, 20.0), Vector2(20.0, 420.0), Vector2(1520.0, 420.0)]
	v.load_frame(_frame_ex(cv, own, [], [], []))
	await process_frame
	var cam := _cam(v)
	_assert(cam.x >= 0.0 and cam.y >= 0.0 and cam.x <= cv and cam.y <= cv,
		"A18 CANVAS BOUND R-103-02: camera %s outside 0..%s at the opening zoom" % [str(cam), cv])
	_assert(_not_inside(v).is_empty(),
		"A18 CANVAS BOUND R-103-02: %d of 4 own units at the canvas corner are not fully inside the viewport (camera %s, scale %s)" % [_not_inside(v).size(), str(cam), _scale(v)])
	await _unmount(v)


# EMPTY SET (G8, not ruled: the null action stands). No unit of the local faction, no spawn node, no own lot: today's
# result stays, zoom 1.0 (scale == 1080 / canvas) and the canvas centre. A pin, green today.
func _test_a18_empty_set_G8() -> void:
	var v := await _mount(true)
	var cv := _fixture_canvas(v)
	var frame := _frame_ex(cv, [], [Vector2(2000.0, 2000.0)], [], [_lot(20, 3000.0, 3000.0, 1)])
	v.load_frame(frame)
	await process_frame
	_assert(absf(_scale(v) - DESIGN_H / cv) <= 1e-9 * (DESIGN_H / cv),
		"A18 EMPTY SET G8: scale %s with no own unit, expected zoom 1.0 (scale %s)" % [_scale(v), DESIGN_H / cv])
	_assert(_cam(v).is_equal_approx(Vector2(cv * 0.5, cv * 0.5)),
		"A18 EMPTY SET G8: camera %s with no own unit, expected the canvas centre %s" % [str(_cam(v)), str(Vector2(cv * 0.5, cv * 0.5))])
	await _unmount(v)
