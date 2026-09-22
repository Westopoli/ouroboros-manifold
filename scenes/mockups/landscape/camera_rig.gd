extends Node3D

## Standalone RTS camera rig for the landscape mockup: WASD/edge-scroll pan,
## wheel zoom across three height bands, pitch eases toward top-down in the
## map band. No autoload or scene dependencies — self-contained.

signal band_changed(band: String)

const PAN_SPEED := 1500.0
const ZOOM_STEP := 300.0
# Old tactical.gd floors zoom at 150; the band table's micro band officially
# starts at 300, but we keep the lower 150 floor to preserve tactical.gd's
# close-in zoom feel rather than inventing a new restriction for this mockup.
const ZOOM_MIN := 150.0
const ZOOM_MAX := 40000.0
const EDGE_SCROLL_ZONE := 60.0

const MICRO_MAX := 1200.0
const TACTICAL_MAX := 6000.0
const MAP_MAX := 40000.0

const PITCH_LOW_DEG := 50.0
const PITCH_HIGH_DEG := 90.0

@export var canvas_size: float = 16000.0

# "height" = distance from the camera to the ground-plane point it looks at
# (same role as tactical.gd's zoom_dist), not literal world-space Y. Pitch
# changes across bands, so a literal world Y would decouple wheel-zoom input
# from a consistent camera distance.
var _height: float = 3000.0
var _pan_target: Vector3 = Vector3.ZERO
var _current_band: String = "tactical"

@onready var _camera: Camera3D = $Camera3D


func _ready() -> void:
	_pan_target = Vector3(canvas_size * 0.5, 0.0, canvas_size * 0.5)
	position = _pan_target
	_update_band()
	_update_camera()


func _process(delta: float) -> void:
	_handle_pan(delta)
	_update_camera()


func _handle_pan(delta: float) -> void:
	var dir := Vector3.ZERO
	if Input.is_action_pressed("ui_left") or Input.is_key_pressed(KEY_A):
		dir.x -= 1.0
	if Input.is_action_pressed("ui_right") or Input.is_key_pressed(KEY_D):
		dir.x += 1.0
	if Input.is_action_pressed("ui_up") or Input.is_key_pressed(KEY_W):
		dir.z -= 1.0
	if Input.is_action_pressed("ui_down") or Input.is_key_pressed(KEY_S):
		dir.z += 1.0

	var mouse := get_viewport().get_mouse_position()
	var vp := get_viewport().get_visible_rect().size
	if mouse.x < EDGE_SCROLL_ZONE:
		dir.x -= 1.0
	if mouse.x > vp.x - EDGE_SCROLL_ZONE:
		dir.x += 1.0
	if mouse.y < EDGE_SCROLL_ZONE:
		dir.z -= 1.0
	if mouse.y > vp.y - EDGE_SCROLL_ZONE:
		dir.z += 1.0

	if dir != Vector3.ZERO:
		_pan_target += dir.normalized() * PAN_SPEED * delta
		_clamp_pan_target()
		position = _pan_target


func _clamp_pan_target() -> void:
	var margin := canvas_size * 0.15
	_pan_target.x = clampf(_pan_target.x, -margin, canvas_size + margin)
	_pan_target.z = clampf(_pan_target.z, -margin, canvas_size + margin)


func _input(event: InputEvent) -> void:
	if event is InputEventMouseButton:
		var mb := event as InputEventMouseButton
		if mb.pressed:
			if mb.button_index == MOUSE_BUTTON_WHEEL_UP:
				_zoom_by(ZOOM_STEP)
			elif mb.button_index == MOUSE_BUTTON_WHEEL_DOWN:
				_zoom_by(-ZOOM_STEP)
	elif event is InputEventPanGesture:
		var pg := event as InputEventPanGesture
		_zoom_by(-pg.delta.y * 15.0)


func _zoom_by(amount: float) -> void:
	_height = clampf(_height - amount, ZOOM_MIN, ZOOM_MAX)
	_update_band()
	_update_camera()


func _update_band() -> void:
	var band := "map"
	if _height < MICRO_MAX:
		band = "micro"
	elif _height < TACTICAL_MAX:
		band = "tactical"
	if band != _current_band:
		_current_band = band
		band_changed.emit(_current_band)


func _pitch_degrees() -> float:
	return lerp(PITCH_LOW_DEG, PITCH_HIGH_DEG, smoothstep(TACTICAL_MAX, MAP_MAX, _height))


func _update_camera() -> void:
	var pitch := deg_to_rad(_pitch_degrees())
	var dist := _height / sin(pitch)
	_camera.position = Vector3(0.0, _height, cos(pitch) * dist)
	_camera.look_at(global_position, Vector3.UP)


func get_current_band() -> String:
	return _current_band


func get_height() -> float:
	return _height


# For the screenshot driver: jump straight to a height/look-at point instead of
# animating there via input, so a batch of shots can be taken deterministically.
func set_height(h: float) -> void:
	_height = clampf(h, ZOOM_MIN, ZOOM_MAX)
	_update_band()
	_update_camera()


func pan_to(world_pos: Vector3) -> void:
	_pan_target = Vector3(world_pos.x, 0.0, world_pos.z)
	_clamp_pan_target()
	position = _pan_target
	_update_camera()
