extends Node3D

# Orbit-style camera rig for the galaxy view (R-107-01, R-107-02, R-103-09):
# left-drag pans on the ground plane at a constant on-screen speed, wheel
# zooms along the forward axis, right-drag orbits the target, a click on a
# system centres it and zooms to Local. The camera moves only on input or an
# eased focus; it never drifts on its own.

const DIST_MIN := 10.0
const DIST_MAX := 220.0
const PITCH_DEG := 55.0
const LOCAL_DISTANCE := 25.0
const ZOOM_STEP := 0.9
const ORBIT_RAD_PER_PX := 0.005
const CLICK_SLOP_PX := 4.0
const GalaxyView := preload("res://scenes/galaxy/galaxy_view.gd")
const FOCUS_SEC := 0.6

var _target: Vector3 = Vector3.ZERO
var _distance: float = 50.0
var _yaw: float = 0.0
var _mouse := Vector2(-1.0, -1.0)
var _dragged := 0.0
var _tween: Tween
var _autonomous := false

@onready var _camera: Camera3D = $Camera3D


func _ready() -> void:
	_update_camera()


func set_view(distance: float, target: Vector3) -> void:
	_distance = clampf(distance, DIST_MIN, DIST_MAX)
	_target = target
	_update_camera()


func set_autonomous(on: bool) -> void:
	_autonomous = on


func is_autonomous() -> bool:
	return _autonomous


func get_target() -> Vector3:
	return _target


func get_distance() -> float:
	return _distance


func get_camera() -> Camera3D:
	return _camera


func focus_region(i: int) -> void:
	var positions: Dictionary = _positions()
	if not positions.has(i):
		return
	_stop_focus()
	_tween = create_tween().set_parallel(true).set_trans(Tween.TRANS_CUBIC).set_ease(Tween.EASE_OUT)
	_tween.tween_method(_set_target, _target, positions[i], FOCUS_SEC)
	_tween.tween_method(_set_distance, _distance, LOCAL_DISTANCE, FOCUS_SEC)


func get_hovered() -> int:
	return _system_at(_mouse)


func project(pos: Vector3) -> Vector2:
	var raw: Vector2 = _camera.unproject_position(pos)
	var vp := get_viewport()
	if vp is SubViewport and vp.get_parent() is SubViewportContainer:
		var box: SubViewportContainer = vp.get_parent()
		var sub := Vector2(vp.size)
		var stretch := box.size / sub if box.stretch and sub.x > 0.0 and sub.y > 0.0 else Vector2.ONE
		raw = box.get_global_rect().position + raw * stretch
		return raw * _canvas_to_real_scale(get_tree().root.get_visible_rect().size)
	return raw * _canvas_to_real_scale(vp.get_visible_rect().size)


func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventMouseMotion:
		_mouse = event.position
		if event.button_mask != 0:
			_autonomous = false
		if event.button_mask & MOUSE_BUTTON_MASK_LEFT:
			_dragged += event.relative.length()
			_pan(event.relative)
		elif event.button_mask & MOUSE_BUTTON_MASK_RIGHT:
			_yaw -= event.relative.x * ORBIT_RAD_PER_PX
			_update_camera()
	elif event is InputEventMouseButton:
		_mouse = event.position
		if event.pressed:
			_autonomous = false
			_stop_focus()
			if event.button_index == MOUSE_BUTTON_LEFT:
				_dragged = 0.0
			elif event.button_index == MOUSE_BUTTON_WHEEL_UP:
				set_view(_distance * ZOOM_STEP, _target)
			elif event.button_index == MOUSE_BUTTON_WHEEL_DOWN:
				set_view(_distance / ZOOM_STEP, _target)
		elif event.button_index == MOUSE_BUTTON_LEFT and _dragged < CLICK_SLOP_PX:
			var hit := _system_at(event.position)
			if hit != -1:
				focus_region(hit)


func _pan(rel: Vector2) -> void:
	_stop_focus()
	var height := maxf(get_viewport().get_visible_rect().size.y, 1.0)
	var per_px := 2.0 * _distance * tan(deg_to_rad(_camera.fov) * 0.5) / height
	var fwd := -_camera.global_transform.basis.z
	fwd.y = 0.0
	fwd = fwd.normalized()
	var right := _camera.global_transform.basis.x
	right.y = 0.0
	right = right.normalized()
	_target += (-right * rel.x + fwd * rel.y / sin(deg_to_rad(PITCH_DEG))) * per_px
	_update_camera()


func _system_at(at: Vector2) -> int:
	var best := -1
	var best_d := GalaxyView.PICK_RADIUS_PX
	var positions: Dictionary = _positions()
	for i in positions:
		if _camera.is_position_behind(positions[i]):
			continue
		var d := _camera.unproject_position(positions[i]).distance_to(at)
		if d <= best_d:
			best_d = d
			best = i
	return best


func _positions() -> Dictionary:
	var owner_view := get_parent()
	return owner_view.get_positions() if owner_view != null and owner_view.has_method("get_positions") else {}


func _stop_focus() -> void:
	if _tween != null and _tween.is_valid():
		_tween.kill()


func _set_target(t: Vector3) -> void:
	_target = t
	_update_camera()


func _set_distance(d: float) -> void:
	_distance = d
	_update_camera()


# The viewport's visible rect under canvas_items/expand stretch is the base
# resolution (1920x1080), not the window's real pixel size, which is what
# qa_state().systems_px is measured in; rescale to the window.
func _canvas_to_real_scale(inflated: Vector2) -> Vector2:
	var real: Vector2 = get_window().size
	if inflated.x <= 0.0 or inflated.y <= 0.0 or real.x <= 0.0 or real.y <= 0.0:
		return Vector2.ONE
	return Vector2(real.x / inflated.x, real.y / inflated.y)


func _update_camera() -> void:
	var pitch := deg_to_rad(PITCH_DEG)
	var offset := Vector3(cos(_yaw) * cos(pitch), sin(pitch), sin(_yaw) * cos(pitch)) * _distance
	_camera.position = _target + offset
	_camera.look_at(_target, Vector3.UP)
