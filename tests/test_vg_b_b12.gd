extends SceneTree

# VG lane B piece B12 (docs/northstar/plans/2026-10-07-visible-game-spec.md
# rev 4, lane B): the autonomous camera the A48-1 stack tests expect.
# A48 item 1: the camera has an autonomous flag; the main-menu backdrop sets
# it (R-110-01: six moods, 5 s transitions); the jump sequencer sets it for the
# replay and clears it after (R-107-02); any player input overrides it; the
# view is told, it polls nothing. Outside that the camera never drifts
# (stack probe check no_idle_drift, R-107-02).
#
# Interface fixed by this test (the brief left it open; reported to the
# Architect): res://scenes/galaxy/auto_camera.gd, extends Node, no scene.
#   const MOOD_COUNT := 6           # R-110-01
#   const TRANSITION_SEC := 5.0     # R-110-01
#   begin_from(distance: float, target: Vector3, yaw: float) -> void
#   set_autonomous(on: bool) -> void      # told by menu / sequencer
#   is_autonomous() -> bool               # false after _init
#   notify_player_input() -> void         # clears the flag
#   advance(delta: float) -> void         # no-op unless autonomous
#   get_distance() -> float, get_target() -> Vector3, get_yaw() -> float
#   get_mood_index() -> int               # 0..MOOD_COUNT-1
# The orbit rig reads get_* each frame and calls notify_player_input() on
# input; that wiring is a later piece, not tested here.

const PATH := "res://scenes/galaxy/auto_camera.gd"

var _pass := 0
var _fail := 0
var _msgs: Array[String] = []


func _initialize() -> void:
	_run()
	print("\n=== VG B12 auto camera ===")
	print("PASS: %d  FAIL: %d" % [_pass, _fail])
	for m in _msgs:
		print("  - " + m)
	print("=== RED ===\n" if _fail > 0 else "=== GREEN ===\n")
	quit(1 if _fail > 0 else 0)


func _assert(c: bool, m: String) -> void:
	if c:
		_pass += 1
	else:
		_fail += 1
		_msgs.append(m)


func _make() -> Node:
	var s = load(PATH)
	if s == null:
		return null
	var n: Node = s.new()
	n.begin_from(50.0, Vector3(1, 0, 2), 0.3)
	return n


func _snap(n: Node) -> Array:
	return [n.get_distance(), n.get_target(), n.get_yaw()]


func _run() -> void:
	var script = load(PATH)
	_assert(script != null, "cannot load %s (piece B12 auto_camera.gd missing)" % PATH)
	if script == null:
		return
	_assert(script.MOOD_COUNT == 6, "R-110-01: MOOD_COUNT must be 6")
	_assert(is_equal_approx(script.TRANSITION_SEC, 5.0), "R-110-01: TRANSITION_SEC must be 5.0")

	var cam := _make()
	_assert(not cam.is_autonomous(), "A48-1: the flag starts off")
	var s0 := _snap(cam)
	for i in 600:
		cam.advance(1.0 / 30.0)
	_assert(_snap(cam) == s0, "R-107-02: camera drifted with the flag off")

	cam.set_autonomous(true)
	_assert(cam.is_autonomous(), "A48-1: set_autonomous(true) not reflected")
	var moved := false
	var moods := {}
	for i in 3600:
		cam.advance(1.0 / 30.0)
		moods[cam.get_mood_index()] = true
		if _snap(cam) != s0:
			moved = true
	_assert(moved, "R-110-01: autonomous camera never moved in 120 s")
	_assert(moods.size() >= 2, "R-110-01: autonomous camera cycled only %d mood in 120 s" % moods.size())
	for k in moods:
		_assert(k >= 0 and k < script.MOOD_COUNT, "mood index %d outside 0..5" % k)

	cam.notify_player_input()
	_assert(not cam.is_autonomous(), "R-107-02: player input must clear the flag")
	var s1 := _snap(cam)
	for i in 300:
		cam.advance(1.0 / 30.0)
	_assert(_snap(cam) == s1, "R-107-02: camera moved after player input overrode it")

	cam.set_autonomous(true)
	_assert(cam.is_autonomous(), "A48-1: the sequencer can set the flag again after an override")
	cam.set_autonomous(false)
	var s2 := _snap(cam)
	cam.advance(1.0)
	_assert(_snap(cam) == s2, "A48-1: set_autonomous(false) must stop the motion")

	# Determinism: same start and same steps give the same pose.
	var a := _make()
	var b := _make()
	a.set_autonomous(true)
	b.set_autonomous(true)
	for i in 1800:
		a.advance(1.0 / 30.0)
		b.advance(1.0 / 30.0)
	_assert(_snap(a) == _snap(b) and a.get_mood_index() == b.get_mood_index(),
		"determinism: two cameras with equal input diverged (random or clock input)")
	a.free()
	b.free()
	cam.free()
