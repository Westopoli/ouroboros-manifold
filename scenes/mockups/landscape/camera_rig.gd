extends Node3D

## Standalone RTS camera rig for the landscape mockup: WASD/edge-scroll pan,
## wheel zoom across three height bands, pitch eases toward top-down in the
## map band. No autoload or scene dependencies — self-contained.

signal band_changed(band: String)

const PAN_SPEED_MIN := 1500.0
const ZOOM_STEP := 300.0
# Old tactical.gd floors zoom at 150; the band table's micro band officially
# starts at 300, but we keep the lower 150 floor to preserve tactical.gd's
# close-in zoom feel rather than inventing a new restriction for this mockup.
const ZOOM_MIN := 150.0
const ZOOM_MAX_MIN := 40000.0
const EDGE_SCROLL_ZONE := 60.0

const MICRO_MAX := 1200.0
const TACTICAL_MAX := 6000.0
const MAP_MAX_MIN := 40000.0

const PITCH_LOW_DEG := 50.0
const PITCH_HIGH_DEG := 90.0

# Pan speed, zoom ceiling and camera range grow with the canvas so a 128,000 wu map can be crossed
# and seen whole (pass 6: canvas up to 128,000 wu).
@export var canvas_size: float = 24000.0:
	set(v):
		canvas_size = v
		_zoom_max = maxf(ZOOM_MAX_MIN, v * 1.2)
		_map_max = maxf(MAP_MAX_MIN, v * 1.2)
		_pan_speed = maxf(PAN_SPEED_MIN, v / 16.0)
		if is_node_ready():
			_camera.far = maxf(60000.0, v * 3.0)
var _zoom_max := ZOOM_MAX_MIN
var _map_max := MAP_MAX_MIN
var _pan_speed := PAN_SPEED_MIN

const GROUND_FOLLOW_TIME_CONSTANT := 0.2

# "height" = distance from the camera to the ground-plane point it looks at (above the
# terrain under the rig, not literal world Y -- see _update_ground_follow), same role as
# tactical.gd's zoom_dist. Pitch changes across bands, so a raw camera Y would decouple
# wheel-zoom input from a consistent camera distance.
var _height: float = 3000.0
var _pan_target: Vector3 = Vector3.ZERO
var _current_band: String = "tactical"
var _ground_y: float = 0.0
var _top_down := false

# Set by the owner (hud.gd) after every regenerate. The rig samples this to keep a
# constant height above the terrain under it (Halo Wars: scrolling onto a mountain
# doesn't require a zoom change) rather than a fixed world Y.
var field_map: FieldMap

@onready var _camera: Camera3D = $Camera3D


func _ready() -> void:
	_pan_target = Vector3(canvas_size * 0.5, 0.0, canvas_size * 0.5)
	position = _pan_target
	_update_band()
	_update_camera()


func _process(delta: float) -> void:
	_handle_pan(delta)
	_update_ground_follow(delta)
	_update_camera()


# Smoothed over ~200ms so a ridge crossed while panning doesn't jolt the camera; the zoom
# amount (_height) stays exactly what the wheel set regardless of terrain underneath.
func _update_ground_follow(delta: float) -> void:
	var target_y := _sample_ground_elevation(_pan_target.x, _pan_target.z)
	var alpha: float = 1.0 - exp(-delta / GROUND_FOLLOW_TIME_CONSTANT)
	_ground_y = lerp(_ground_y, target_y, alpha)
	position.y = _ground_y


func _sample_ground_elevation(x: float, z: float) -> float:
	if field_map == null:
		return 0.0
	var dim: int = field_map.dim
	var gx: int = clampi(int(round(x / FieldMap.SPACING)), 0, dim - 1)
	var gy: int = clampi(int(round(z / FieldMap.SPACING)), 0, dim - 1)
	return field_map.grid[gy * dim + gx].elevation


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
		_pan_target += dir.normalized() * _pan_speed * delta
		_clamp_pan_target()
		position.x = _pan_target.x
		position.z = _pan_target.z


func _clamp_pan_target() -> void:
	var margin := canvas_size * 0.15
	_pan_target.x = clampf(_pan_target.x, -margin, canvas_size + margin)
	_pan_target.z = clampf(_pan_target.z, -margin, canvas_size + margin)


func _input(event: InputEvent) -> void:
	if event is InputEventMouseButton:
		var mb := event as InputEventMouseButton
		if mb.pressed:
			if mb.button_index == MOUSE_BUTTON_WHEEL_UP:
				_zoom_by(_wheel_step())
			elif mb.button_index == MOUSE_BUTTON_WHEEL_DOWN:
				_zoom_by(-_wheel_step())
	elif event is InputEventPanGesture:
		var pg := event as InputEventPanGesture
		_zoom_by(-pg.delta.y * 15.0)


func _wheel_step() -> float:
	return ZOOM_STEP if canvas_size <= 40000.0 else maxf(ZOOM_STEP, _height * 0.08)


func _zoom_by(amount: float) -> void:
	_height = clampf(_height - amount, ZOOM_MIN, _zoom_max)
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
	if _top_down:
		return PITCH_HIGH_DEG
	return lerp(PITCH_LOW_DEG, PITCH_HIGH_DEG, smoothstep(TACTICAL_MAX, _map_max, _height))


func _update_camera() -> void:
	var pitch := deg_to_rad(_pitch_degrees())
	var dist := _height / sin(pitch)
	_camera.position = Vector3(0.0, _height, cos(pitch) * dist)
	# look_at(rig_origin, Vector3.UP) degenerates at pitch=90 (max zoom, looking straight
	# down): the view direction and the UP reference become parallel, so look_at's basis
	# flips unpredictably ("map inverts itself" at max zoom). Setting rotation directly from
	# the known pitch has no such case since it never depends on an external up reference.
	_camera.rotation = Vector3(-pitch, 0.0, 0.0)


func get_current_band() -> String:
	return _current_band


# Straight down at the current height, any band; off restores the band's own pitch.
func set_top_down(on: bool) -> void:
	_top_down = on
	_update_camera()


func is_top_down() -> bool:
	return _top_down


func get_height() -> float:
	return _height


func get_camera() -> Camera3D:
	return _camera


# For the screenshot driver: jump straight to a height/look-at point instead of
# animating there via input, so a batch of shots can be taken deterministically.
func set_height(h: float) -> void:
	_height = clampf(h, ZOOM_MIN, _zoom_max)
	_update_band()
	_update_camera()


func pan_to(world_pos: Vector3) -> void:
	_pan_target = Vector3(world_pos.x, 0.0, world_pos.z)
	_clamp_pan_target()
	# Snap the ground follow instantly here (no 200ms smoothing) since this is the
	# deterministic screenshot-driver jump, not an interactive pan.
	_ground_y = _sample_ground_elevation(_pan_target.x, _pan_target.z)
	position = Vector3(_pan_target.x, _ground_y, _pan_target.z)
	_update_camera()
