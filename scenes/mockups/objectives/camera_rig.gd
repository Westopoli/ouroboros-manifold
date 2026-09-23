extends Node3D

const PAN_SPEED := 1500.0
const ZOOM_STEP := 300.0
const ZOOM_MIN := 800.0
const ZOOM_MAX := 20000.0
const EDGE_SCROLL_ZONE := 60.0

@export var canvas_size: float = 24000.0

var _height: float = 3000.0
var _pan_target: Vector3 = Vector3.ZERO
var _mouse_pos: Vector2 = Vector2.ZERO

@onready var _camera: Camera3D = $Camera3D


func _ready() -> void:
	_pan_target = Vector3(canvas_size * 0.5, 0.0, canvas_size * 0.5)
	position = _pan_target
	_mouse_pos = get_viewport().get_visible_rect().size * 0.5
	_update_camera()


func _process(delta: float) -> void:
	_handle_pan(delta)


func _handle_pan(delta: float) -> void:
	var dir := Vector3.ZERO
	if Input.is_key_pressed(KEY_A):
		dir.x -= 1.0
	if Input.is_key_pressed(KEY_D):
		dir.x += 1.0
	if Input.is_key_pressed(KEY_W):
		dir.z -= 1.0
	if Input.is_key_pressed(KEY_S):
		dir.z += 1.0

	dir += _edge_scroll_dir(_mouse_pos, get_viewport().get_visible_rect().size)

	if dir != Vector3.ZERO:
		_pan_target += dir.normalized() * PAN_SPEED * delta
		_clamp_pan_target()
		position.x = _pan_target.x
		position.z = _pan_target.z


func _edge_scroll_dir(mouse: Vector2, bounds: Vector2) -> Vector3:
	var dir := Vector3.ZERO
	if mouse.x < EDGE_SCROLL_ZONE:
		dir.x -= 1.0
	if mouse.x > bounds.x - EDGE_SCROLL_ZONE:
		dir.x += 1.0
	if mouse.y < EDGE_SCROLL_ZONE:
		dir.z -= 1.0
	if mouse.y > bounds.y - EDGE_SCROLL_ZONE:
		dir.z += 1.0
	return dir


func _clamp_pan_target() -> void:
	var margin := canvas_size * 0.15
	_pan_target.x = clampf(_pan_target.x, -margin, canvas_size + margin)
	_pan_target.z = clampf(_pan_target.z, -margin, canvas_size + margin)


func _input(event: InputEvent) -> void:
	if event is InputEventMouseMotion:
		_mouse_pos = event.position
	if event is InputEventMouseButton and event.pressed:
		if event.button_index == MOUSE_BUTTON_WHEEL_UP:
			_zoom_by(ZOOM_STEP)
		elif event.button_index == MOUSE_BUTTON_WHEEL_DOWN:
			_zoom_by(-ZOOM_STEP)


func _zoom_by(amount: float) -> void:
	_height = clampf(_height - amount, ZOOM_MIN, ZOOM_MAX)
	_update_camera()


func _update_camera() -> void:
	_camera.position = Vector3(0.0, _height, 0.0)
	_camera.rotation = Vector3(-PI * 0.5, 0.0, 0.0)


func get_camera() -> Camera3D:
	return _camera


func get_height() -> float:
	return _height


func set_height(h: float) -> void:
	_height = clampf(h, ZOOM_MIN, ZOOM_MAX)
	_update_camera()


func pan_to(world_pos: Vector3) -> void:
	_pan_target = Vector3(world_pos.x, 0.0, world_pos.z)
	_clamp_pan_target()
	position = Vector3(_pan_target.x, 0.0, _pan_target.z)


func qa_camera(height: float, x: float, z: float) -> void:
	pan_to(Vector3(x, 0.0, z))
	set_height(height)
