extends Node

# Autonomous galaxy camera (A48-1, R-110-01, R-107-02): six moods, each
# reached by a 5 s eased transition. Moves only while told it is autonomous;
# player input clears the flag. Deterministic: pose is a function of the
# start pose and the summed delta.

const MOOD_COUNT := 6
const TRANSITION_SEC := 5.0
const HOLD_SEC := 5.0  # named draft: dwell time per mood, not pinned by R-110-01

# Per mood: distance scale, target offset (x, z) as a fraction of the start
# distance, yaw offset in radians.
const MOODS := [
	[1.0, Vector2(0.0, 0.0), 0.0],
	[0.6, Vector2(0.3, 0.1), 0.8],
	[1.4, Vector2(-0.2, 0.3), 1.6],
	[0.8, Vector2(-0.3, -0.2), 2.4],
	[1.2, Vector2(0.2, -0.3), 3.2],
	[0.5, Vector2(0.0, 0.2), 4.0],
]

var _autonomous := false
var _t := 0.0
var _base_distance := 50.0
var _base_target := Vector3.ZERO
var _base_yaw := 0.0
var _distance := 50.0
var _target := Vector3.ZERO
var _yaw := 0.0
var _mood := 0
var _from := 0


func begin_from(distance: float, target: Vector3, yaw: float) -> void:
	_base_distance = distance
	_base_target = target
	_base_yaw = yaw
	_distance = distance
	_target = target
	_yaw = yaw
	_t = 0.0
	_mood = 0
	_from = 0


func set_autonomous(on: bool) -> void:
	_autonomous = on


func is_autonomous() -> bool:
	return _autonomous


func notify_player_input() -> void:
	_autonomous = false


func advance(delta: float) -> void:
	if not _autonomous:
		return
	_t += delta
	var period := TRANSITION_SEC + HOLD_SEC
	var step := int(_t / period)
	var phase := _t - float(step) * period
	_from = step % MOOD_COUNT
	_mood = (step + 1) % MOOD_COUNT
	var k := smoothstep(0.0, TRANSITION_SEC, phase)
	var a := _pose(_from)
	var b := _pose(_mood)
	_distance = lerpf(a[0], b[0], k)
	_target = (a[1] as Vector3).lerp(b[1], k)
	_yaw = lerpf(a[2], b[2], k)
	if k < 1.0:
		_mood = _from if k < 0.5 else _mood


func _pose(i: int) -> Array:
	var m: Array = MOODS[i]
	var off: Vector2 = m[1]
	return [
		_base_distance * float(m[0]),
		_base_target + Vector3(off.x, 0.0, off.y) * _base_distance,
		_base_yaw + float(m[2]),
	]


func get_distance() -> float:
	return _distance


func get_target() -> Vector3:
	return _target


func get_yaw() -> float:
	return _yaw


func get_mood_index() -> int:
	return _mood
