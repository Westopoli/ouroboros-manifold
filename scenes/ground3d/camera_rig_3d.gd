extends Node3D

## RTS camera rig for the 3D ground (visible-game lane C, C3). Ported from the landscape mockup's
## camera_rig.gd: world units are 1 wu per 3D unit, sim (x, y) maps to 3D (x, height, y). The rig publishes
## qa_camera() {x, y, scale} as the map band's equivalents (rulebook rows 3 and 31).

signal band_changed(band: String)

const PAN_SPEED_MIN := 1500.0
const ZOOM_STEP := 300.0
## W8: trackpad two-finger scroll, wu per pixel per wu of camera height. If the view moves the wrong way on the Mac, flip the sign here.
const PAN_GESTURE_WU_PER_PX := 0.0015
const ZOOM_MIN := 150.0
const ZOOM_MAX_MIN := 40000.0
const ZOOM_CANVAS_FACTOR := 1.2
const EDGE_SCROLL_ZONE := 60.0
const MICRO_MAX := 1200.0
const TACTICAL_MAX := 6000.0
const PITCH_LOW_DEG := 50.0
const PITCH_HIGH_DEG := 90.0
const GROUND_FOLLOW_TIME_CONSTANT := 0.2
const CELL_WU := 100.0
const CM_PER_WU := 100.0
const PICK_STEP_FRACTION := 0.01
const PICK_STEP_MIN := 1.0
const PICK_BISECT := 24

var _terrain: Dictionary = {}
var _canvas := Vector2(24000.0, 24000.0)
var _zoom_max := ZOOM_MAX_MIN
var _pan_speed := PAN_SPEED_MIN
var _height := 3000.0
var _pan_target := Vector2.ZERO
var _ground_y := 0.0
var _band := "tactical"
var _top_down := false
var _camera: Camera3D


func _ready() -> void:
	_camera = Camera3D.new()
	_camera.near = 1.0
	add_child(_camera)
	_camera.make_current()
	_apply_canvas()
	_pan_target = _canvas * 0.5
	_ground_y = height_at(_pan_target.x, _pan_target.y)
	_place()
	_update_band()


func _process(delta: float) -> void:
	_handle_pan(delta)
	var alpha := 1.0 - exp(-delta / GROUND_FOLLOW_TIME_CONSTANT)
	_ground_y = lerpf(_ground_y, height_at(_pan_target.x, _pan_target.y), alpha)
	_place()


func set_terrain(t: Dictionary) -> void:
	_terrain = t
	if not t.is_empty():
		_canvas = Vector2(float(t["cells_w"]), float(t["cells_h"])) * CELL_WU
	_apply_canvas()
	_pan_target = _pan_target.clamp(-_canvas * 0.15, _canvas * 1.15)
	_ground_y = height_at(_pan_target.x, _pan_target.y)
	_place()


func _apply_canvas() -> void:
	var side := maxf(_canvas.x, _canvas.y)
	_zoom_max = maxf(ZOOM_MAX_MIN, side * ZOOM_CANVAS_FACTOR)
	_pan_speed = maxf(PAN_SPEED_MIN, side / 16.0)
	if _camera != null:
		_camera.far = maxf(60000.0, side * 3.0)


func height_at(wx: float, wy: float) -> float:
	if _terrain.is_empty() or not _terrain.has("heights"):
		return 0.0
	var w := int(_terrain["cells_w"])
	var h := int(_terrain["cells_h"])
	var hs: PackedInt32Array = _terrain["heights"]
	var fx := clampf(wx / CELL_WU - 0.5, 0.0, w - 1.0)
	var fy := clampf(wy / CELL_WU - 0.5, 0.0, h - 1.0)
	var i0 := mini(int(floor(fx)), maxi(w - 2, 0))
	var j0 := mini(int(floor(fy)), maxi(h - 2, 0))
	var i1 := mini(i0 + 1, w - 1)
	var j1 := mini(j0 + 1, h - 1)
	var tx := fx - i0
	var ty := fy - j0
	var a := lerpf(hs[j0 * w + i0], hs[j0 * w + i1], tx)
	var b := lerpf(hs[j1 * w + i0], hs[j1 * w + i1], tx)
	return lerpf(a, b, ty) / CM_PER_WU


func _handle_pan(delta: float) -> void:
	var dir := Vector2.ZERO
	if Input.is_action_pressed("ui_left") or Input.is_key_pressed(KEY_A):
		dir.x -= 1.0
	if Input.is_action_pressed("ui_right") or Input.is_key_pressed(KEY_D):
		dir.x += 1.0
	if Input.is_action_pressed("ui_up") or Input.is_key_pressed(KEY_W):
		dir.y -= 1.0
	if Input.is_action_pressed("ui_down") or Input.is_key_pressed(KEY_S):
		dir.y += 1.0
	var mouse := get_viewport().get_mouse_position()
	var vp := get_viewport().get_visible_rect().size
	if mouse.x < EDGE_SCROLL_ZONE:
		dir.x -= 1.0
	if mouse.x > vp.x - EDGE_SCROLL_ZONE:
		dir.x += 1.0
	if mouse.y < EDGE_SCROLL_ZONE:
		dir.y -= 1.0
	if mouse.y > vp.y - EDGE_SCROLL_ZONE:
		dir.y += 1.0
	if dir != Vector2.ZERO:
		pan(dir.normalized() * _pan_speed * delta)


func pan(wu: Vector2) -> void:
	_pan_target = (_pan_target + wu).clamp(-_canvas * 0.15, _canvas * 1.15)
	_place()


func pan_to(wu: Vector2) -> void:
	_pan_target = wu.clamp(-_canvas * 0.15, _canvas * 1.15)
	_ground_y = height_at(_pan_target.x, _pan_target.y)
	_place()


func _input(event: InputEvent) -> void:
	if event is InputEventMouseButton and event.pressed:
		if event.button_index == MOUSE_BUTTON_WHEEL_UP:
			zoom_by(-1)
		elif event.button_index == MOUSE_BUTTON_WHEEL_DOWN:
			zoom_by(1)
	elif event is InputEventPanGesture:
		pan(event.delta * _height * PAN_GESTURE_WU_PER_PX)
	elif event is InputEventMagnifyGesture:
		zoom_scale(event.factor)


func _wheel_step() -> float:
	return ZOOM_STEP if maxf(_canvas.x, _canvas.y) <= ZOOM_MAX_MIN else maxf(ZOOM_STEP, _height * 0.08)


## steps > 0 zooms out (camera rises), steps < 0 zooms in.
func zoom_by(steps: int) -> void:
	_height = clampf(_height + steps * _wheel_step(), ZOOM_MIN, _zoom_max)
	_update_band()
	_place()


## factor > 1 (fingers spread) zooms in, like wheel up.
func zoom_scale(factor: float) -> void:
	_height = clampf(_height / factor, ZOOM_MIN, _zoom_max)
	_update_band()
	_place()


func set_top_down(on: bool) -> void:
	_top_down = on
	_place()


func is_top_down() -> bool:
	return _top_down


func _update_band() -> void:
	var b := "map"
	if _height < MICRO_MAX:
		b = "micro"
	elif _height < TACTICAL_MAX:
		b = "tactical"
	if b != _band:
		_band = b
		band_changed.emit(_band)


func band() -> String:
	return _band


func camera_height() -> float:
	return _height


func get_camera() -> Camera3D:
	return _camera


func _pitch_degrees() -> float:
	if _top_down:
		return PITCH_HIGH_DEG
	return lerpf(PITCH_LOW_DEG, PITCH_HIGH_DEG, smoothstep(TACTICAL_MAX, _zoom_max, _height))


func _place() -> void:
	if _camera == null:
		return
	position = Vector3(_pan_target.x, _ground_y, _pan_target.y)
	var pitch := deg_to_rad(_pitch_degrees())
	var dist := _height / sin(pitch)
	_camera.position = Vector3(0.0, _height, cos(pitch) * dist)
	_camera.rotation = Vector3(-pitch, 0.0, 0.0)


func project_to_screen(wu: Vector2) -> Vector2:
	return _camera.unproject_position(Vector3(wu.x, height_at(wu.x, wu.y), wu.y))


func pick_ground(px: Vector2) -> Vector2:
	var o := _camera.project_ray_origin(px)
	var d := _camera.project_ray_normal(px)
	var t_max := _camera.far
	var t_prev := 0.0
	var t := 0.0
	while t < t_max:
		var p := o + d * t
		if p.y <= height_at(p.x, p.z):
			var lo := t_prev
			var hi := t
			for i in PICK_BISECT:
				var mid := (lo + hi) * 0.5
				var q := o + d * mid
				if q.y <= height_at(q.x, q.z):
					hi = mid
				else:
					lo = mid
			var r := o + d * hi
			return Vector2(r.x, r.z)
		t_prev = t
		t += maxf(PICK_STEP_MIN, t * PICK_STEP_FRACTION)
	return _pan_target


## Pixels per wu at the pan target, the map band's equivalent of the 2D camera scale.
func qa_camera() -> Dictionary:
	var dist := _height / sin(deg_to_rad(_pitch_degrees()))
	var vp_h := get_viewport().get_visible_rect().size.y
	var s := vp_h / (2.0 * dist * tan(deg_to_rad(_camera.fov) * 0.5))
	return {"x": _pan_target.x, "y": _pan_target.y, "scale": s}
