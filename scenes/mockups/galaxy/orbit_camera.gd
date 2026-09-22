extends Node3D

const QaPlants := preload("res://scenes/mockups/_shared/qa_plants.gd")

signal empty_clicked

const DIST_MIN := 15.0
const DIST_MAX := 120.0
const ZOOM_STEP_FRACTION := 0.10
const PITCH_MIN_DEG := 20.0
const PITCH_MAX_DEG := 85.0
const PITCH_DEFAULT_DEG := 55.0
const DIST_DEFAULT := 50.0
const PAN_SPEED := 0.09
const ORBIT_YAW_SPEED := 0.01
const ORBIT_PITCH_SPEED := 0.1
const PICK_RADIUS_PX := 14.0
const FOCUS_DISTANCE := 20.0
const FOCUS_DURATION := 1.5

const BAND_SPLIT_LOW := 32.5
const BAND_SPLIT_HIGH := 70.0

var _galaxy_view: Node3D
var _target: Vector3 = Vector3.ZERO
var _distance: float = DIST_DEFAULT
var _yaw: float = 0.0
var _pitch_deg: float = PITCH_DEFAULT_DEG
var _focused_id: int = -1
var _hovered_id: int = -1

var _dragging_pan := false
var _dragging_orbit := false
var _press_pos: Vector2 = Vector2.ZERO
var _move_tween: Tween

@onready var _camera: Camera3D = $Camera3D


func _ready() -> void:
	_update_camera()


func set_galaxy_view(view: Node3D) -> void:
	_galaxy_view = view


func get_camera() -> Camera3D:
	return _camera


func _process(_delta: float) -> void:
	if not (_move_tween and _move_tween.is_valid() and _move_tween.is_running()):
		_update_camera()


func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventMouseButton:
		var mb := event as InputEventMouseButton
		var pos := _to_real_px(mb.position)
		if mb.button_index == MOUSE_BUTTON_LEFT:
			if mb.pressed:
				_dragging_pan = true
				_press_pos = pos
			else:
				_dragging_pan = false
				if _press_pos.distance_to(pos) < 4.0:
					_try_click(pos)
		elif mb.button_index == MOUSE_BUTTON_RIGHT:
			_dragging_orbit = mb.pressed
		elif mb.button_index == MOUSE_BUTTON_WHEEL_UP and mb.pressed:
			_zoom(1.0 - ZOOM_STEP_FRACTION)
		elif mb.button_index == MOUSE_BUTTON_WHEEL_DOWN and mb.pressed:
			_zoom(1.0 + ZOOM_STEP_FRACTION)
	elif event is InputEventMouseMotion:
		var mm := event as InputEventMouseMotion
		if _dragging_pan and mm.relative.length() > 0.01:
			_pan_by(mm.relative)
		elif _dragging_orbit:
			_orbit_by(mm.relative)
		_hovered_id = pick_at(_to_real_px(mm.position))


func _zoom(factor: float) -> void:
	_kill_tween()
	_distance = clampf(_distance * factor, DIST_MIN, DIST_MAX)


func _pan_by(rel: Vector2) -> void:
	_kill_tween()
	var basis := _camera.global_transform.basis
	var right := Vector3(basis.x.x, 0.0, basis.x.z).normalized()
	var fwd := Vector3(basis.z.x, 0.0, basis.z.z).normalized()
	var speed := PAN_SPEED * (_distance / DIST_DEFAULT)
	_target -= right * rel.x * speed
	_target += fwd * rel.y * speed


func _orbit_by(rel: Vector2) -> void:
	_kill_tween()
	_yaw -= rel.x * ORBIT_YAW_SPEED
	_pitch_deg = clampf(_pitch_deg + rel.y * ORBIT_PITCH_SPEED, PITCH_MIN_DEG, PITCH_MAX_DEG)


# This click ended a drag shorter than a few pixels is still treated as a click
# (qa_driver's own click verb never moves between press and release).
func _try_click(pos: Vector2) -> void:
	var id := pick_at(pos)
	if id == -1:
		empty_clicked.emit()
		return
	focus_system(id)


func focus_system(id: int) -> void:
	if _galaxy_view == null or _galaxy_view.get_galaxy() == null:
		return
	var g: Galaxy = _galaxy_view.get_galaxy()
	if id < 0 or id >= g.systems.size():
		return
	_focused_id = id
	_kill_tween()
	var start_target := _target
	var start_dist := _distance
	var end_pos: Vector3 = g.systems[id].pos
	_move_tween = create_tween().set_ease(Tween.EASE_OUT).set_trans(Tween.TRANS_CUBIC)
	_move_tween.tween_method(_apply_focus_tween.bind(start_target, start_dist, end_pos), 0.0, 1.0, FOCUS_DURATION)


func _apply_focus_tween(t: float, start_target: Vector3, start_dist: float, end_pos: Vector3) -> void:
	_target = start_target.lerp(end_pos, t)
	_distance = lerpf(start_dist, FOCUS_DISTANCE, t)
	_update_camera()


func qa_camera(distance: float, target_system_id: int) -> void:
	_kill_tween()
	if target_system_id >= 0 and _galaxy_view != null and _galaxy_view.get_galaxy() != null:
		var g: Galaxy = _galaxy_view.get_galaxy()
		if target_system_id < g.systems.size():
			_target = g.systems[target_system_id].pos
			_focused_id = target_system_id
	_distance = clampf(distance, DIST_MIN, DIST_MAX)
	_update_camera()


func _kill_tween() -> void:
	if _move_tween and _move_tween.is_valid():
		_move_tween.kill()
	_move_tween = null


func _update_camera() -> void:
	var pitch := deg_to_rad(_pitch_deg)
	var offset := Vector3(cos(_yaw) * cos(pitch), sin(pitch), sin(_yaw) * cos(pitch)) * _distance
	_camera.position = _target + offset
	_camera.look_at(_target, Vector3.UP)


func get_band() -> String:
	if QaPlants.is_active("bands-frozen"):
		return "Regional"
	if _distance >= BAND_SPLIT_HIGH:
		return "Overview"
	if _distance >= BAND_SPLIT_LOW:
		return "Regional"
	return "Local"


func get_distance() -> float:
	return _distance


func get_focused() -> int:
	return _focused_id


func get_hovered() -> int:
	return _hovered_id


func _effective_pick_radius() -> float:
	return -1.0 if QaPlants.is_active("pick-radius-zero") else PICK_RADIUS_PX


# get_viewport().get_visible_rect().size read from this Node3D is the project's
# configured base resolution (1920x1080), not the real window pixel size, under
# canvas_items/expand stretch (see _shared/README.md); unproject_position() and
# every InputEvent position _unhandled_input receives are in that same base-
# resolution space, so rescale to DisplayServer's real pixel size to match what
# qa_driver's click/move verbs send and what qa_state() reports.
func _canvas_to_real_scale() -> Vector2:
	var inflated: Vector2 = get_viewport().get_visible_rect().size
	var real: Vector2 = DisplayServer.window_get_size()
	if inflated.x <= 0.0 or inflated.y <= 0.0:
		return Vector2.ONE
	return Vector2(real.x / inflated.x, real.y / inflated.y)


func _to_real_px(canvas_pos: Vector2) -> Vector2:
	var scale := _canvas_to_real_scale()
	return Vector2(canvas_pos.x * scale.x, canvas_pos.y * scale.y)


func project(system_id: int) -> Vector2:
	if _galaxy_view == null or _galaxy_view.get_galaxy() == null:
		return Vector2(-1, -1)
	var g: Galaxy = _galaxy_view.get_galaxy()
	if system_id < 0 or system_id >= g.systems.size():
		return Vector2(-1, -1)
	var raw: Vector2 = _camera.unproject_position(g.systems[system_id].pos)
	return _to_real_px(raw)


func pick_at(px: Vector2) -> int:
	if _galaxy_view == null or _galaxy_view.get_galaxy() == null:
		return -1
	var g: Galaxy = _galaxy_view.get_galaxy()
	var radius := _effective_pick_radius()
	var best := -1
	var best_d := INF
	for sys in g.systems:
		var p := project(sys.id)
		var d := p.distance_to(px)
		if d <= radius and d < best_d:
			best_d = d
			best = sys.id
	return best
