extends SceneTree

# Piece C5-G1 (docs/northstar/plans/2026-09-28-gap-fix-and-migration-plan.md
# "G-G1 camera"; mission-plays plan item C5): the live galaxy camera
# (scenes/galaxy/orbit_camera.gd, node OrbitCamera of galaxy_view.tscn) takes
# real mouse input and gains focus_region(i).
#   R-107-01  left-drag pans; scroll zooms along the forward axis; right-drag
#             orbits; clicking a system centers on it and zooms to Local.
#   R-107-02  outside a time jump the camera is fully the player's (no idle
#             drift of its own).
#   A48-2     the galaxy pans by left-drag only; R-103-09 (constant pan speed
#             on screen) and the pan-speed slider do not apply to it. The
#             former pan_screen_speed check is dropped (test-defect, ledger).
#             A56 SUSPENDS the vertical-grab direction (check vertical_grab removed):
#             the prototype's drag direction wins until Westley has compared it
#             (scenes/mockups/galaxy/orbit_camera.gd:256-264). See
#             docs/northstar/proving_ground/evidence/push_2026-10-01/c5_prototype_vs_rules.md.
#   A48-1     the camera has an autonomous flag (OrbitCamera.set_autonomous(bool),
#             is_autonomous(); qa_state()["camera_autonomous"]), set by the menu
#             backdrop and the jump sequencer; any player input cancels it.
#             Only the camera's own half is tested here; the menu and sequencer
#             do not drive the live camera on this base.
# Events go in through the root Window the way a real mouse does, in real
# window pixels (the unit qa_state().systems_px is in). Needs a real window
# (headless pins it to 64x64, below the 14 px pick radius), so it runs under
# Xvfb from tests/qa/desktop/test_galaxy_camera.py, which parses the RESULT
# lines this prints, one per named check.
# Positive control: the drag, zoom and orbit checks below measure real
# movement from a baseline in the same run, so a camera that ignores input
# fails them; the no-drift check is the one guard that is green on a camera
# that never moves.

const SCENE_PATH := "res://scenes/galaxy/galaxy_view.tscn"
const FIXTURE_PATH := "res://tests/transport/fixtures/snapshot_seed1_tick10.json"
const DRAG_PX := 100.0
const SETTLE_SEC := 4.0

var _pass_count := 0
var _fail_count := 0
var _fail_msgs: Array[String] = []
var _view: Node
var _rig: Node
var _ids: Array = []
var _check_name := ""
var _failed: Dictionary = {}
const CHECKS := ["no_idle_drift", "wheel_zoom", "drag_pan", "autonomous_flag", "autonomous_cancelled_by_input", "right_drag_orbit", "click_focus", "focus_region"]


func _initialize() -> void:
	await _run_tests()
	for name in CHECKS:
		print("RESULT " + JSON.stringify({"check": name, "ok": not _failed.has(name) and not _failed.has(""), "msg": _failed.get(name, _failed.get("", ""))}))
	print("\n=== Galaxy Camera Test Results ===")
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
		if not _failed.has(_check_name):
			_failed[_check_name] = msg


func _run_tests() -> void:
	var packed = load(SCENE_PATH)
	_assert(packed != null, "cannot load " + SCENE_PATH)
	if packed == null:
		return
	_view = (packed as PackedScene).instantiate()
	get_root().add_child(_view)
	await process_frame
	await process_frame
	var snap = JSON.parse_string(FileAccess.get_file_as_string(FIXTURE_PATH))
	_assert(snap is Dictionary, "snapshot fixture unreadable")
	if not (snap is Dictionary):
		return
	_view.set_snapshot(snap)
	await process_frame
	_rig = _view.get_node_or_null("OrbitCamera")
	_assert(_rig != null, "galaxy_view has no OrbitCamera node")
	if _rig == null:
		return
	_ids = _view.qa_state()["systems_px"].keys()
	_ids.sort()
	_assert(_ids.size() >= 10, "fixture gave fewer than 10 systems")

	_check_name = "no_idle_drift"
	await _check_no_idle_drift_R107_02()
	_check_name = "wheel_zoom"
	await _check_wheel_zoom_R107_01()
	_check_name = "drag_pan"
	await _check_drag_pan_R107_01()
	_check_name = "autonomous_flag"
	await _check_autonomous_flag_A48_1()
	_check_name = "autonomous_cancelled_by_input"
	await _check_input_cancels_autonomy_A48_1()
	_check_name = "right_drag_orbit"
	await _check_right_drag_orbits_R107_01()
	_check_name = "click_focus"
	await _check_click_focuses_local_R107_01()
	_check_name = "focus_region"
	await _check_focus_region_R107_01()


func _px(id: int) -> Vector2:
	var p = _view.qa_state()["systems_px"][id]
	return Vector2(p[0], p[1])


func _distance() -> float:
	return float(_view.qa_state()["distance"])


func _centre() -> Vector2:
	return Vector2(get_root().size) / 2.0


func _frames(n: int) -> void:
	for _i in range(n):
		await process_frame


func _button(index: int, pressed: bool, at: Vector2) -> void:
	var ev := InputEventMouseButton.new()
	ev.button_index = index
	ev.pressed = pressed
	ev.position = at
	ev.global_position = at
	if pressed:
		ev.button_mask = 1 << (index - 1)
	get_root().push_input(ev)
	await process_frame


func _motion(at: Vector2, rel: Vector2, mask: int) -> void:
	var ev := InputEventMouseMotion.new()
	ev.position = at
	ev.global_position = at
	ev.relative = rel
	ev.button_mask = mask
	get_root().push_input(ev)
	await process_frame


func _drag(button: int, from: Vector2, delta: Vector2) -> void:
	var mask := 1 << (button - 1)
	await _button(button, true, from)
	var steps := 5
	for s in range(steps):
		await _motion(from + delta * float(s + 1) / float(steps), delta / float(steps), mask)
	await _button(button, false, from + delta)
	await _frames(2)


func _wheel(index: int) -> void:
	await _button(index, true, _centre())
	await _button(index, false, _centre())
	await _frames(2)


func _isolated_system() -> int:
	# A system whose nearest neighbour is further than twice the pick radius,
	# so a click on it cannot land on another one.
	var state: Dictionary = _view.qa_state()
	var radius := float(state["pick_radius_px"])
	for id in _ids:
		var p := _px(id)
		var ok := true
		for other in _ids:
			if other != id and _px(other).distance_to(p) < radius * 2.5:
				ok = false
				break
		if ok and p.x > 50.0 and p.y > 50.0 and p.x < get_root().size.x - 50.0 and p.y < get_root().size.y - 50.0:
			return id
	return -1


func _settle_on(id: int) -> void:
	var deadline := Time.get_ticks_msec() + int(SETTLE_SEC * 1000.0)
	while Time.get_ticks_msec() < deadline:
		await process_frame
		if _view.qa_state()["band"] == "Local" and _px(id).distance_to(_centre()) < get_root().size.x * 0.03:
			return


func _check_no_idle_drift_R107_02() -> void:
	_view.qa_camera(60.0, int(_ids[0]))   # TD-VG-B-14: was 120 (B23 prototype scale, every distance halved)
	await _frames(3)
	var d0 := _distance()
	var p0 := _px(int(_ids[1]))
	await create_timer(1.5).timeout
	_assert(is_equal_approx(_distance(), d0), "R-107-02: camera distance drifted by itself outside a jump (%s -> %s)" % [d0, _distance()])
	_assert(_px(int(_ids[1])).distance_to(p0) < 0.5, "R-107-02: camera moved by itself outside a jump (px %s -> %s)" % [p0, _px(int(_ids[1]))])


func _check_wheel_zoom_R107_01() -> void:
	_view.qa_camera(50.0, int(_ids[0]))   # TD-VG-B-14: was 100 (B23 prototype scale, every distance halved)
	await _frames(3)
	var d0 := _distance()
	await _wheel(MOUSE_BUTTON_WHEEL_UP)
	var d1 := _distance()
	_assert(d1 < d0, "R-107-01: wheel up did not zoom in (distance %s -> %s)" % [d0, d1])
	await _wheel(MOUSE_BUTTON_WHEEL_DOWN)
	await _wheel(MOUSE_BUTTON_WHEEL_DOWN)
	var d2 := _distance()
	_assert(d2 > d1, "R-107-01: wheel down did not zoom out (distance %s -> %s)" % [d1, d2])
	_assert(_px(int(_ids[0])).distance_to(_centre()) < get_root().size.x * 0.01, "R-107-01: zoom moved the focused system off the view centre; scroll zooms along the forward axis")


func _check_drag_pan_R107_01() -> void:
	var focus := int(_ids[0])
	_view.qa_camera(40.0, focus)   # TD-VG-B-14: was 80 (B23 prototype scale, every distance halved)
	await _frames(3)
	var d0 := _distance()
	var p0 := _px(focus)
	await _drag(MOUSE_BUTTON_LEFT, _centre() + Vector2(0, 200), Vector2(DRAG_PX, 0))
	var p1 := _px(focus)
	_assert(is_equal_approx(_distance(), d0), "R-107-01: a left-drag changed the camera distance")
	_assert(p1.x > p0.x + 10.0, "R-107-01: left-drag right did not move the map right (x %s -> %s)" % [p0.x, p1.x])
	await _drag(MOUSE_BUTTON_LEFT, _centre() + Vector2(0, 200), Vector2(0, DRAG_PX))
	_assert(absf(_px(focus).y - p1.y) > 10.0, "R-107-01: a vertical left-drag did not pan the map")


# A48-1: the flag exists, is off by default, and is observable. Idle with no flag
# still does not drift (no_idle_drift above).
func _check_autonomous_flag_A48_1() -> void:
	_assert(_rig.has_method("set_autonomous") and _rig.has_method("is_autonomous"), "A48-1: OrbitCamera has no set_autonomous(bool) / is_autonomous()")
	if not (_rig.has_method("set_autonomous") and _rig.has_method("is_autonomous")):
		return
	_view.qa_camera(50.0, int(_ids[0]))   # TD-VG-B-14: was 100 (B23 prototype scale, every distance halved)
	await _frames(3)
	_assert(_view.qa_state().get("camera_autonomous", null) == false, "A48-1: qa_state camera_autonomous should be false by default (got %s)" % [_view.qa_state().get("camera_autonomous", null)])
	_assert(not _rig.is_autonomous(), "A48-1: is_autonomous() true by default")
	_rig.set_autonomous(true)
	await _frames(2)
	_assert(_rig.is_autonomous() and _view.qa_state().get("camera_autonomous", null) == true, "A48-1: set_autonomous(true) not reported (camera %s, qa_state %s)" % [_rig.is_autonomous(), _view.qa_state().get("camera_autonomous", null)])
	_rig.set_autonomous(false)
	await _frames(2)
	_assert(not _rig.is_autonomous() and _view.qa_state().get("camera_autonomous", null) == false, "A48-1: set_autonomous(false) not reported")


# A48-1 / R-107-02: any player input overrides autonomy. Each input kind starts
# from a flag that is verified on first (positive control), so a flag that is
# never set cannot pass.
func _check_input_cancels_autonomy_A48_1() -> void:
	if not (_rig.has_method("set_autonomous") and _rig.has_method("is_autonomous")):
		_assert(false, "A48-1: OrbitCamera has no set_autonomous(bool) / is_autonomous()")
		return
	var inputs := ["wheel", "left_drag", "right_drag"]
	for kind in inputs:
		_view.qa_camera(50.0, int(_ids[0]))   # TD-VG-B-14: was 100 (B23 prototype scale, every distance halved)
		await _frames(3)
		_rig.set_autonomous(true)
		await _frames(2)
		_assert(_rig.is_autonomous(), "A48-1 (control): flag not set before the %s input" % kind)
		match kind:
			"wheel":
				await _wheel(MOUSE_BUTTON_WHEEL_UP)
			"left_drag":
				await _drag(MOUSE_BUTTON_LEFT, _centre() + Vector2(0, 200), Vector2(DRAG_PX, 0))
			"right_drag":
				await _drag(MOUSE_BUTTON_RIGHT, _centre() + Vector2(0, 200), Vector2(DRAG_PX, 0))
		_assert(not _rig.is_autonomous(), "A48-1: %s input did not cancel the autonomous flag" % kind)
		_assert(_view.qa_state().get("camera_autonomous", null) == false, "A48-1: qa_state camera_autonomous still true after %s input" % kind)


func _check_right_drag_orbits_R107_01() -> void:
	var focus := int(_ids[0])
	var other := int(_ids[_ids.size() - 1])
	_view.qa_camera(30.0, focus)   # TD-VG-B-14: was 60 (B23 prototype scale, every distance halved)
	await _frames(3)
	var d0 := _distance()
	var f0 := _px(focus)
	var o0 := _px(other)
	await _drag(MOUSE_BUTTON_RIGHT, _centre() + Vector2(0, 200), Vector2(DRAG_PX, 0))
	_assert(_px(other).distance_to(o0) > 5.0, "R-107-01: right-drag did not orbit (another system stayed at %s)" % [o0])
	_assert(_px(focus).distance_to(f0) < 2.0, "R-107-01: orbit moved the focus point (%s -> %s); it turns about it" % [f0, _px(focus)])
	_assert(is_equal_approx(_distance(), d0), "R-107-01: orbit changed the camera distance")


func _check_click_focuses_local_R107_01() -> void:
	_view.qa_camera(60.0, -1)   # TD-VG-B-14: was 120 (B23 prototype scale, every distance halved)
	await _frames(3)
	var id := _isolated_system()
	_assert(id != -1, "no isolated on-screen system at distance 60 to click")
	if id == -1:
		return
	var at := _px(id)
	await _button(MOUSE_BUTTON_LEFT, true, at)
	await _button(MOUSE_BUTTON_LEFT, false, at)
	await _settle_on(id)
	_assert(_view.qa_state()["band"] == "Local", "R-107-01: clicking system %d did not zoom to Local (band %s, distance %s)" % [id, _view.qa_state()["band"], _distance()])
	_assert(_px(id).distance_to(_centre()) < get_root().size.x * 0.03, "R-107-01: clicking system %d did not centre it (px %s, centre %s)" % [id, _px(id), _centre()])


func _check_focus_region_R107_01() -> void:
	_assert(_rig.has_method("focus_region"), "G-G1: OrbitCamera has no focus_region(i)")
	if not _rig.has_method("focus_region"):
		return
	_view.qa_camera(70.0, -1)   # TD-VG-B-14: was 140 (B23 prototype scale, every distance halved)
	await _frames(3)
	var id := int(_ids[_ids.size() / 2])
	_rig.focus_region(id)
	await _settle_on(id)
	_assert(_view.qa_state()["band"] == "Local", "G-G1: focus_region(%d) did not zoom to Local (band %s)" % [id, _view.qa_state()["band"]])
	_assert(_px(id).distance_to(_centre()) < get_root().size.x * 0.03, "G-G1: focus_region(%d) did not centre it (px %s, centre %s)" % [id, _px(id), _centre()])
	_rig.focus_region(99999)
	await _frames(3)
	_assert(_view.qa_state()["system_count"] > 0, "G-G1: focus_region on an unknown id broke the view")
