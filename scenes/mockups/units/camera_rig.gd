extends Node3D

const PAN_SPEED := 1500.0
const ZOOM_STEP := 300.0
const ZOOM_MIN := 500.0
const ZOOM_MAX := 12000.0
const EDGE_SCROLL_ZONE := 60.0

@export var canvas_size: float = 8000.0

var _height: float = 2500.0
var _pan_target: Vector3 = Vector3.ZERO
var _mouse_canvas: Vector2 = Vector2.ZERO

@onready var _camera: Camera3D = $Camera3D
@onready var _hud_panel: Control = get_node("../HUD/VBoxContainer")


func _ready() -> void:
	_pan_target = Vector3(canvas_size * 0.5, 0.0, canvas_size * 0.5)
	position = _pan_target
	_mouse_canvas = get_viewport().get_mouse_position()
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

	# _mouse_canvas (tracked from InputEventMouseMotion, canvas-space) converted to
	# real window pixels via get_final_transform(), compared against the real window
	# size from DisplayServer -- both sides the same space (see the objectives mockup
	# pass-2 brief for the sibling bug this mirrors).
	if get_viewport().gui_get_hovered_control() == null and not _hud_panel_rect().has_point(_mouse_canvas):
		var mouse := get_viewport().get_final_transform() * _mouse_canvas
		var win := DisplayServer.window_get_size()
		if mouse.x < EDGE_SCROLL_ZONE:
			dir.x -= 1.0
		if mouse.x > win.x - EDGE_SCROLL_ZONE:
			dir.x += 1.0
		if mouse.y < EDGE_SCROLL_ZONE:
			dir.z -= 1.0
		if mouse.y > win.y - EDGE_SCROLL_ZONE:
			dir.z += 1.0

	if dir != Vector3.ZERO:
		_pan_target += dir.normalized() * PAN_SPEED * delta
		_clamp_pan_target()
		position.x = _pan_target.x
		position.z = _pan_target.z


func _hud_panel_rect() -> Rect2:
	return _hud_panel.get_global_rect()


func _clamp_pan_target() -> void:
	var margin := canvas_size * 0.15
	_pan_target.x = clampf(_pan_target.x, -margin, canvas_size + margin)
	_pan_target.z = clampf(_pan_target.z, -margin, canvas_size + margin)


func _input(event: InputEvent) -> void:
	if event is InputEventMouseMotion:
		_mouse_canvas = (event as InputEventMouseMotion).position
	if event is InputEventMouseButton:
		var mb := event as InputEventMouseButton
		if mb.pressed:
			if mb.button_index == MOUSE_BUTTON_WHEEL_UP:
				_zoom_by(ZOOM_STEP)
			elif mb.button_index == MOUSE_BUTTON_WHEEL_DOWN:
				_zoom_by(-ZOOM_STEP)


func _zoom_by(amount: float) -> void:
	_height = clampf(_height - amount, ZOOM_MIN, ZOOM_MAX)
	_update_camera()


func _update_camera() -> void:
	_camera.position = Vector3(0.0, _height, 0.0)
	_camera.rotation = Vector3(-PI / 2.0, 0.0, 0.0)


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
	position = _pan_target
	_update_camera()


func get_pan_target() -> Vector2:
	return Vector2(_pan_target.x, _pan_target.z)
