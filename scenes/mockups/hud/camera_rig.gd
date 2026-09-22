extends Node3D

const QaPlants := preload("res://scenes/mockups/_shared/qa_plants.gd")

const PAN_SPEED := 1500.0
const ZOOM_STEP := 300.0
const HEIGHT_MIN := 150.0
const HEIGHT_MAX := 12000.0
const EDGE_SCROLL_ZONE := 60.0
const CANVAS_SIZE := 6000.0

var _height: float = 3000.0
var _pan: Vector3 = Vector3(CANVAS_SIZE * 0.5, 0.0, CANVAS_SIZE * 0.5)

@onready var _camera: Camera3D = $Camera3D


func _ready() -> void:
	_update_camera()


func _process(delta: float) -> void:
	var dir := Vector3.ZERO
	if Input.is_key_pressed(KEY_A): dir.x -= 1.0
	if Input.is_key_pressed(KEY_D): dir.x += 1.0
	if Input.is_key_pressed(KEY_W): dir.z -= 1.0
	if Input.is_key_pressed(KEY_S): dir.z += 1.0

	var mouse := get_viewport().get_mouse_position()
	var vp := DisplayServer.window_get_size()
	if mouse.x < EDGE_SCROLL_ZONE: dir.x -= 1.0
	if mouse.x > vp.x - EDGE_SCROLL_ZONE: dir.x += 1.0
	if mouse.y < EDGE_SCROLL_ZONE: dir.z -= 1.0
	if mouse.y > vp.y - EDGE_SCROLL_ZONE: dir.z += 1.0

	if dir != Vector3.ZERO:
		_pan += dir.normalized() * PAN_SPEED * delta
		_clamp_pan()
		_update_camera()


func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventMouseButton and event.pressed:
		if event.button_index == MOUSE_BUTTON_WHEEL_UP:
			_zoom_by(ZOOM_STEP)
		elif event.button_index == MOUSE_BUTTON_WHEEL_DOWN:
			_zoom_by(-ZOOM_STEP)


func _zoom_by(amount: float) -> void:
	set_height(_height - amount)


func get_ground_half_extent() -> Vector2:
	var fov_rad := deg_to_rad(_camera.fov if _camera != null else 55.0)
	var half_z := _height * tan(fov_rad * 0.5)
	var aspect := 16.0 / 9.0
	var vp := DisplayServer.window_get_size()
	if vp.y > 0:
		aspect = float(vp.x) / float(vp.y)
	return Vector2(half_z * aspect, half_z)


func _clamp_axis(v: float, half_extent: float) -> float:
	var lo := half_extent
	var hi := CANVAS_SIZE - half_extent
	if lo <= hi:
		return clampf(v, lo, hi)
	return CANVAS_SIZE * 0.5


func _clamp_pan() -> void:
	if QaPlants.is_active("camera-unbounded"):
		return
	var extent := get_ground_half_extent()
	_pan.x = _clamp_axis(_pan.x, extent.x)
	_pan.z = _clamp_axis(_pan.z, extent.y)


func _update_camera() -> void:
	_camera.position = Vector3(_pan.x, _height, _pan.z)
	_camera.rotation = Vector3(-PI / 2.0, 0.0, 0.0)


func centre_on(pos: Vector2) -> void:
	_pan = Vector3(pos.x, 0.0, pos.y)
	_clamp_pan()
	_update_camera()


func set_height(h: float) -> void:
	_height = clampf(h, HEIGHT_MIN, HEIGHT_MAX)
	_clamp_pan()
	_update_camera()


func get_height() -> float:
	return _height


func get_pan() -> Vector2:
	return Vector2(_pan.x, _pan.z)


func get_camera() -> Camera3D:
	return _camera


func get_bounds() -> Dictionary:
	return {"min_x": 0.0, "max_x": CANVAS_SIZE, "min_z": 0.0, "max_z": CANVAS_SIZE}
