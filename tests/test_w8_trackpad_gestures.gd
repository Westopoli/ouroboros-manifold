extends SceneTree
# test-timeout: 20000

# W8 (docs/northstar/ROADMAP.md row W8, "no trackpad pan or zoom on the Mac"): a macOS trackpad sends InputEventPanGesture (two-finger
# scroll) and InputEventMagnifyGesture (pinch); scenes/galaxy/orbit_camera.gd and scenes/ground3d/camera_rig_3d.gd read mouse buttons and
# the wheel only, so on a Mac neither camera can be panned or zoomed with the trackpad. This file is the bug's spec (a bug, not a story:
# no S-### applies; the rules the cameras already keep are E-16 S-107 R-107-01 "scroll zooms along the forward axis" and S-236 R-236-01
# "one continuous camera from one unit up to the map view").
# Red today because the rigs ignore both gesture types (the events arrive, nothing moves); green when each rig handles them.
# Direction of the pan is NOT pinned (the sign cannot be checked on the Linux box; the fix names one constant to flip): the pan rows assert
# the camera moved along the gesture's axis and not along the other. Zoom direction is pinned: spread fingers (factor > 1) zoom in, matching
# wheel-up, so factor 2.0 halves the galaxy distance and lowers the ground camera, factor 0.5 doubles / raises it.
# Rigs built as the existing tests build them: ground as tests/test_vg_c3_camera_rig.gd:13-19, galaxy as tests/test_vg_b_b23.gd:128,203.
# Events go through the root Window and one frame (the b23 pattern). Headless-safe.
# CONTROLS (green today): the wheel still zooms both rigs, the pose set up for each row reads back, and an event that no rig handles
# (a gesture with delta zero / factor 1.0) moves nothing, so a red row means "gesture ignored", not "harness broken".

const GALAXY_SCENE := "res://scenes/galaxy/galaxy_view.tscn"
const FIXTURE_PATH := "res://tests/transport/fixtures/snapshot_seed1_tick10.json"
const GROUND_RIG := "res://scenes/ground3d/camera_rig_3d.gd"
const GROUND_FIXTURE := "res://tests/support/vg_c_fixture.gd"
const POS := Vector2(60.0, 60.0)  # clear of the galaxy view's MISSION button in the 64x64 headless window
const EPS := 0.001                # a float compare, not a game threshold
const START_DISTANCE := 40.0      # mid-range for orbit_camera DIST_MIN 7.5 .. DIST_MAX 120
const START_TARGET := Vector3(5.0, 0.0, 5.0)

var _pass_count := 0
var _fail_count := 0
var _fail_msgs: Array[String] = []


func _initialize() -> void:
	await _run_tests()
	print("\n=== W8 trackpad gestures ===")
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


func _frames(n: int) -> void:
	for _i in range(n):
		await process_frame


func _pan_gesture(delta: Vector2) -> void:
	var ev := InputEventPanGesture.new()
	ev.position = POS
	ev.delta = delta
	get_root().push_input(ev)
	await process_frame


func _magnify(factor: float) -> void:
	var ev := InputEventMagnifyGesture.new()
	ev.position = POS
	ev.factor = factor
	get_root().push_input(ev)
	await process_frame


func _wheel(index: int) -> void:
	for pressed in [true, false]:
		var ev := InputEventMouseButton.new()
		ev.button_index = index
		ev.pressed = pressed
		ev.position = POS
		ev.global_position = POS
		get_root().push_input(ev)
		await process_frame


func _run_tests() -> void:
	await _galaxy_rows()
	await _ground_rows()


# ---- galaxy: scenes/galaxy/orbit_camera.gd, reached as galaxy_view.tscn's "OrbitCamera" (test_vg_b_b23.gd:128,203) ----

func _galaxy_rows() -> void:
	var f := FileAccess.open(FIXTURE_PATH, FileAccess.READ)
	var snap = JSON.parse_string(f.get_as_text()) if f != null else null
	_assert(snap is Dictionary, "CONTROL W8 galaxy: fixture snapshot_seed1_tick10.json readable")
	if not (snap is Dictionary):
		return
	var view: Node = (load(GALAXY_SCENE) as PackedScene).instantiate()
	view.driven = true
	get_root().add_child(view)
	await _frames(2)
	view.set_snapshot(snap)
	await _frames(2)
	var rig: Node = view.get_node_or_null("OrbitCamera")
	_assert(rig != null, "CONTROL W8 galaxy: galaxy_view.tscn has an OrbitCamera node")
	if rig == null:
		return

	# controls: the pose reads back, a null gesture moves nothing, the wheel still zooms
	rig.set_view(START_DISTANCE, START_TARGET)
	_assert(absf(rig.get_distance() - START_DISTANCE) < EPS and rig.get_target().distance_to(START_TARGET) < EPS,
		"CONTROL W8 galaxy: set_view(40, (5,0,5)) reads back as %s / %s" % [rig.get_distance(), rig.get_target()])
	await _pan_gesture(Vector2.ZERO)
	await _magnify(1.0)
	_assert(absf(rig.get_distance() - START_DISTANCE) < EPS and rig.get_target().distance_to(START_TARGET) < EPS,
		"CONTROL W8 galaxy: a zero pan and a factor 1.0 pinch must move nothing, got %s / %s" % [rig.get_distance(), rig.get_target()])
	await _wheel(MOUSE_BUTTON_WHEEL_UP)
	_assert(rig.get_distance() < START_DISTANCE - EPS, "CONTROL W8 galaxy: wheel up must still zoom in (regression), distance %s" % rig.get_distance())

	# pan: a horizontal gesture moves the target; a vertical one moves it too; neither is a no-op
	rig.set_view(START_DISTANCE, START_TARGET)
	await _pan_gesture(Vector2(40.0, 0.0))
	var moved: float = rig.get_target().distance_to(START_TARGET)
	_assert(moved > EPS, "W8 galaxy: InputEventPanGesture delta (40, 0) must change get_target(), moved %s" % moved)
	rig.set_view(START_DISTANCE, START_TARGET)
	await _pan_gesture(Vector2(0.0, 40.0))
	moved = rig.get_target().distance_to(START_TARGET)
	_assert(moved > EPS, "W8 galaxy: InputEventPanGesture delta (0, 40) must change get_target(), moved %s" % moved)
	rig.set_view(START_DISTANCE, START_TARGET)
	await _pan_gesture(Vector2(40.0, 0.0))
	var a: Vector3 = rig.get_target() - START_TARGET
	rig.set_view(START_DISTANCE, START_TARGET)
	await _pan_gesture(Vector2(-40.0, 0.0))
	var b: Vector3 = rig.get_target() - START_TARGET
	_assert(a.length() > EPS and a.dot(b) < 0.0,
		"W8 galaxy: opposite pan gestures must move the target in opposite directions, got %s and %s" % [a, b])
	rig.set_view(START_DISTANCE, START_TARGET)
	await _pan_gesture(Vector2(40.0, 0.0))
	var near: float = (rig.get_target() - START_TARGET).length()
	rig.set_view(START_DISTANCE * 2.0, START_TARGET)
	await _pan_gesture(Vector2(40.0, 0.0))
	var far: float = (rig.get_target() - START_TARGET).length()
	_assert(near > EPS and far > near * 1.5,
		"W8 galaxy: the same gesture moves further when farther out (constant on-screen speed), near %s far %s" % [near, far])

	# pinch: factor 2.0 halves the distance, 0.5 doubles it; the target stays put
	rig.set_view(START_DISTANCE, START_TARGET)
	await _magnify(2.0)
	_assert(absf(rig.get_distance() - START_DISTANCE * 0.5) < 0.01,
		"W8 galaxy: InputEventMagnifyGesture factor 2.0 must halve get_distance() (40 -> 20), got %s" % rig.get_distance())
	_assert(rig.get_target().distance_to(START_TARGET) < EPS, "W8 galaxy: a pinch must not move the target, got %s" % rig.get_target())
	rig.set_view(START_DISTANCE, START_TARGET)
	await _magnify(0.5)
	_assert(absf(rig.get_distance() - START_DISTANCE * 2.0) < 0.01,
		"W8 galaxy: InputEventMagnifyGesture factor 0.5 must double get_distance() (40 -> 80), got %s" % rig.get_distance())
	view.queue_free()
	await _frames(1)


# ---- ground: scenes/ground3d/camera_rig_3d.gd, built as test_vg_c3_camera_rig.gd:13-19 ----

func _ground_rows() -> void:
	var rs = load(GROUND_RIG) if ResourceLoader.exists(GROUND_RIG) else null
	_assert(rs is GDScript, "CONTROL W8 ground: camera_rig_3d.gd loads")
	var fx = load(GROUND_FIXTURE)
	if not (rs is GDScript) or not (fx is GDScript):
		return
	var rig = rs.new()
	get_root().add_child(rig)
	await process_frame
	# The headless window is 64x64, so the rig's edge-scroll zone (60 px) covers all of it and _process would drift the pan target every
	# frame; the input handlers are what is under test, so frame processing is off for this rig (push_input still reaches _input).
	rig.set_process(false)
	rig.set_terrain(fx.terrain())
	rig.pan_to(Vector2(400.0, 300.0))
	await process_frame
	var h0: float = rig.camera_height()

	# controls: the pose reads back, null gestures move nothing, the wheel still zooms
	_assert(absf(float(rig.qa_camera()["x"]) - 400.0) < 0.5 and absf(float(rig.qa_camera()["y"]) - 300.0) < 0.5,
		"CONTROL W8 ground: pan_to(400, 300) reads back, got %s" % rig.qa_camera())
	await _pan_gesture(Vector2.ZERO)
	await _magnify(1.0)
	_assert(absf(float(rig.qa_camera()["x"]) - 400.0) < 0.5 and absf(rig.camera_height() - h0) < EPS,
		"CONTROL W8 ground: a zero pan and a factor 1.0 pinch must move nothing, got %s height %s" % [rig.qa_camera(), rig.camera_height()])
	await _wheel(MOUSE_BUTTON_WHEEL_UP)
	_assert(rig.camera_height() < h0 - EPS, "CONTROL W8 ground: wheel up must still lower the camera (regression), height %s -> %s" % [h0, rig.camera_height()])

	# pan
	rig.pan_to(Vector2(400.0, 300.0))
	await _pan_gesture(Vector2(40.0, 0.0))
	var x1: float = float(rig.qa_camera()["x"])
	_assert(absf(x1 - 400.0) > 0.5, "W8 ground: InputEventPanGesture delta (40, 0) must change the camera x, got %s" % x1)
	_assert(absf(float(rig.qa_camera()["y"]) - 300.0) < 0.5, "W8 ground: a horizontal gesture must not change the camera y, got %s" % rig.qa_camera())
	rig.pan_to(Vector2(400.0, 300.0))
	await _pan_gesture(Vector2(-40.0, 0.0))
	var x2: float = float(rig.qa_camera()["x"])
	_assert((x1 - 400.0) * (x2 - 400.0) < 0.0,
		"W8 ground: opposite pan gestures must move the camera x in opposite directions, got %s and %s" % [x1, x2])
	rig.pan_to(Vector2(400.0, 300.0))
	await _pan_gesture(Vector2(0.0, 40.0))
	_assert(absf(float(rig.qa_camera()["y"]) - 300.0) > 0.5, "W8 ground: InputEventPanGesture delta (0, 40) must change the camera y, got %s" % rig.qa_camera())

	# pinch: factor 2.0 lowers the camera, 0.5 raises it; the pan target stays put
	rig.pan_to(Vector2(400.0, 300.0))
	var h1: float = rig.camera_height()
	await _magnify(2.0)
	var h2: float = rig.camera_height()
	_assert(h2 < h1 - EPS, "W8 ground: InputEventMagnifyGesture factor 2.0 must lower camera_height(), %s -> %s" % [h1, h2])
	_assert(absf(float(rig.qa_camera()["x"]) - 400.0) < 0.5 and absf(float(rig.qa_camera()["y"]) - 300.0) < 0.5,
		"W8 ground: a pinch must not move the pan target, got %s" % rig.qa_camera())
	await _magnify(0.5)
	_assert(rig.camera_height() > h2 + EPS, "W8 ground: InputEventMagnifyGesture factor 0.5 must raise camera_height(), %s -> %s" % [h2, rig.camera_height()])
	rig.queue_free()
	await process_frame
