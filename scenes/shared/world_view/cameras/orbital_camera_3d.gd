extends Node

signal camera_move_completed()
signal ambient_motion_started()

const ORBIT_SPEED := 0.15
const OVERVIEW_DISTANCE := 80.0
const OVERVIEW_ELEVATION := deg_to_rad(50.0)
const REGION_DISTANCE := 30.0
const REGION_ELEVATION := deg_to_rad(25.0)

var _renderer: Node
var _viewport: SubViewport
var _camera: Camera3D

var _target := Vector3.ZERO
var _azimuth := 0.0
var _elevation := OVERVIEW_ELEVATION
var _distance := OVERVIEW_DISTANCE
var _ambient := false
var _move_tween: Tween


func setup(renderer: Node, viewport: SubViewport) -> void:
	_renderer = renderer
	_viewport = viewport
	_camera = Camera3D.new()
	_camera.fov = 50.0
	_camera.current = true
	_viewport.add_child(_camera)
	_apply_orbit()


func teardown() -> void:
	_ambient = false
	if _move_tween:
		_move_tween.kill()
		_move_tween = null
	if _camera and is_instance_valid(_camera):
		_camera.queue_free()
	_camera = null
	_renderer = null
	_viewport = null


func _process(delta: float) -> void:
	if not _ambient or not _camera or not is_instance_valid(_camera):
		return
	_azimuth += ORBIT_SPEED * delta
	_apply_orbit()


func move_to_region(region_id: String, duration: float) -> void:
	_ambient = false
	if not _renderer:
		camera_move_completed.emit()
		return

	var region_pos: Vector3 = _renderer.region_id_to_world_position(region_id)
	_animate_to(region_pos, REGION_DISTANCE, REGION_ELEVATION, duration)


func move_to_overview(duration: float) -> void:
	_ambient = false
	var center := Vector3.ZERO
	if _renderer:
		var bounds: Rect2 = _renderer.get_world_bounds()
		center = Vector3(bounds.get_center().x, 0, bounds.get_center().y)
	_animate_to(center, OVERVIEW_DISTANCE, OVERVIEW_ELEVATION, duration)


func move_to_position(pos: Vector3, look_at_target: Vector3, duration: float) -> void:
	_ambient = false
	if not _camera or not is_instance_valid(_camera):
		camera_move_completed.emit()
		return

	var start_pos := _camera.global_position
	var start_target := _target

	if _move_tween:
		_move_tween.kill()

	_move_tween = create_tween().set_ease(Tween.EASE_IN_OUT).set_trans(Tween.TRANS_CUBIC)
	_move_tween.tween_method(func(t: float):
		_camera.global_position = start_pos.lerp(pos, t)
		var current_look := start_target.lerp(look_at_target, t)
		_camera.look_at(current_look)
	, 0.0, 1.0, duration)
	_move_tween.tween_callback(func():
		_target = look_at_target
		camera_move_completed.emit()
	)


func start_ambient_motion() -> void:
	_ambient = true
	ambient_motion_started.emit()


func stop_ambient_motion() -> void:
	_ambient = false


func get_current_position() -> Vector3:
	if _camera and is_instance_valid(_camera):
		return _camera.global_position
	return Vector3.ZERO


func get_current_target() -> Vector3:
	return _target


func _apply_orbit() -> void:
	if not _camera or not is_instance_valid(_camera):
		return
	var y := sin(_elevation) * _distance
	var horiz := cos(_elevation) * _distance
	var pos := _target + Vector3(cos(_azimuth) * horiz, y, sin(_azimuth) * horiz)
	_camera.global_position = pos
	if pos.distance_to(_target) > 0.1:
		_camera.look_at(_target)


func _animate_to(new_target: Vector3, new_distance: float, new_elevation: float, duration: float) -> void:
	if _move_tween:
		_move_tween.kill()

	var start_target := _target
	var start_distance := _distance
	var start_elevation := _elevation

	_move_tween = create_tween().set_ease(Tween.EASE_IN_OUT).set_trans(Tween.TRANS_CUBIC)
	_move_tween.tween_method(func(t: float):
		_target = start_target.lerp(new_target, t)
		_distance = lerpf(start_distance, new_distance, t)
		_elevation = lerpf(start_elevation, new_elevation, t)
		_apply_orbit()
	, 0.0, 1.0, duration)
	_move_tween.tween_callback(func():
		camera_move_completed.emit()
	)
