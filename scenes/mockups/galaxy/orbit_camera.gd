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
# Widened from 20.0 (pass-1 review: "reads as flying into a planet" — see
# docs/northstar/research/mockups/galaxy/README.md, BAND-X). 28.0 stays
# inside Local (< BAND_SPLIT_LOW 32.5) but keeps enough of the disc in frame
# for neighbouring systems and their filaments to still read (paired with
# galaxy_view.gd's lower LOCAL_FAR_WU-driven desaturation cutoff and capped
# local_boost).
const FOCUS_DISTANCE := 28.0
const FOCUS_DURATION := 1.5

const BAND_SPLIT_LOW := 32.5
const BAND_SPLIT_HIGH := 70.0

# Ported from scenes/shared/world_view/cameras/orbital_camera_3d.gd's idle
# auto-orbit (2026-09-22): six moods drifting distance/pitch/yaw-speed/target
# instead of that file's separate azimuth/elevation state, since pass 1's
# _yaw/_pitch_deg/_distance/_target is the same spherical parametrization
# (elevation == pitch, azimuth == yaw). Values re-clamped to this file's own
# PITCH_MIN_DEG/PITCH_MAX_DEG (20-85) and DIST_MIN/MAX (15-120, identical
# range to the legacy ZOOM_MIN/MAX so no rescaling needed there); RING_FOLLOW
# and UNDERSIDE wanted 5deg and negative (below-horizon) pitch the legacy
# camera allowed and this one does not — both clamp to PITCH_MIN_DEG instead
# of reaching lower, so UNDERSIDE reads as "shallow sweep", not literally
# below the disc. Auto-orbit is for idle ambiance only: any interaction
# (drag, zoom, click-focus, qa_camera/qa_set) turns it off for the rest of
# the run, never back on — QA scripts call qa_camera as one of their first
# actions, so every screenshot after that is deterministic.
enum CameraMood { WIDE_ORBIT, RING_FOLLOW, APPROACH, DRIFT, PULLBACK, UNDERSIDE }

const MOOD_DURATIONS := {
	CameraMood.WIDE_ORBIT: Vector2(10.0, 18.0),
	CameraMood.RING_FOLLOW: Vector2(8.0, 14.0),
	CameraMood.APPROACH: Vector2(10.0, 16.0),
	CameraMood.DRIFT: Vector2(8.0, 14.0),
	CameraMood.PULLBACK: Vector2(10.0, 16.0),
	CameraMood.UNDERSIDE: Vector2(8.0, 12.0),
}

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

var _auto_camera := true
var _current_mood: CameraMood = CameraMood.WIDE_ORBIT
var _mood_time := 0.0
var _mood_duration := 14.0
var _mood_timer := 5.0
var _mood_target_dist := DIST_DEFAULT
var _mood_target_pitch := PITCH_DEFAULT_DEG
var _mood_target_yaw_speed := 0.012
var _mood_target_offset := Vector3.ZERO
var _blend_from_dist := DIST_DEFAULT
var _blend_from_pitch := PITCH_DEFAULT_DEG
var _blend_from_offset := Vector3.ZERO
var _blend_timer := 6.0
var _blend_duration := 6.0
var _approach_start_dist := DIST_DEFAULT
var _approach_end_dist := 30.0
var _approach_start_pitch := PITCH_DEFAULT_DEG
var _approach_end_pitch := 24.0
var _pullback_end_dist := 90.0
var _pullback_end_pitch := 40.0

@onready var _camera: Camera3D = $Camera3D
var _zoom_controller: Node


func _ready() -> void:
	_zoom_controller = Node.new()
	_zoom_controller.set_script(load("res://scenes/mockups/galaxy/legacy_zoom_disclosure_controller.gd"))
	_zoom_controller.name = "ZoomDisclosureController"
	add_child(_zoom_controller)
	_update_camera()


func get_zoom_controller() -> Node:
	return _zoom_controller


func set_galaxy_view(view: Node3D) -> void:
	_galaxy_view = view


func get_camera() -> Camera3D:
	return _camera


func _process(delta: float) -> void:
	if _move_tween and _move_tween.is_valid() and _move_tween.is_running():
		_zoom_controller.update_from_distance(_distance)
		return
	if _auto_camera:
		_advance_auto_camera(delta)
	_update_camera()
	_zoom_controller.update_from_distance(_distance)


func _advance_auto_camera(delta: float) -> void:
	_mood_time += delta
	_mood_timer -= delta
	_blend_timer += delta
	_update_mood_targets()
	var ease_t := _smooth_step(clampf(_blend_timer / _blend_duration, 0.0, 1.0))
	_distance = clampf(lerpf(_blend_from_dist, _mood_target_dist, ease_t), DIST_MIN, DIST_MAX)
	_pitch_deg = clampf(lerpf(_blend_from_pitch, _mood_target_pitch, ease_t), PITCH_MIN_DEG, PITCH_MAX_DEG)
	_target = _blend_from_offset.lerp(_mood_target_offset, ease_t)
	_yaw += _mood_target_yaw_speed * delta
	if _mood_timer <= 0.0:
		_switch_mood()


func _update_mood_targets() -> void:
	var progress := clampf(_mood_time / _mood_duration, 0.0, 1.0)
	match _current_mood:
		CameraMood.APPROACH:
			var ease_p := _smooth_step(progress)
			_mood_target_dist = lerpf(_approach_start_dist, _approach_end_dist, ease_p)
			_mood_target_pitch = lerpf(_approach_start_pitch, _approach_end_pitch, ease_p)
			_blend_from_dist = _mood_target_dist
			_blend_from_pitch = _mood_target_pitch
		CameraMood.PULLBACK:
			var ease_p2 := _smooth_step(progress)
			_mood_target_dist = lerpf(_approach_start_dist, _pullback_end_dist, ease_p2)
			_mood_target_pitch = lerpf(_approach_start_pitch, _pullback_end_pitch, ease_p2)
			_blend_from_dist = _mood_target_dist
			_blend_from_pitch = _mood_target_pitch
		CameraMood.DRIFT:
			_mood_target_offset = Vector3(sin(_mood_time * 0.1) * 3.0, 0.0, cos(_mood_time * 0.1) * 3.0)


func _switch_mood() -> void:
	var available: Array[int] = []
	for m in CameraMood.values():
		if m != _current_mood:
			available.append(m)
	_current_mood = available[randi() % available.size()] as CameraMood
	_mood_time = 0.0
	_blend_from_dist = _distance
	_blend_from_pitch = _pitch_deg
	_blend_from_offset = _target
	_blend_timer = 0.0

	var dur: Vector2 = MOOD_DURATIONS[_current_mood]
	_mood_duration = randf_range(dur.x, dur.y)
	_mood_timer = _mood_duration

	match _current_mood:
		CameraMood.WIDE_ORBIT:
			_mood_target_dist = randf_range(70.0, 95.0)
			_mood_target_pitch = randf_range(25.0, 45.0)
			_mood_target_yaw_speed = randf_range(0.008, 0.014)
			_mood_target_offset = Vector3.ZERO
			_blend_duration = 6.0
		CameraMood.RING_FOLLOW:
			_mood_target_dist = 30.0
			_mood_target_pitch = PITCH_MIN_DEG
			_mood_target_yaw_speed = 0.05
			_mood_target_offset = Vector3.ZERO
			_blend_duration = 5.0
		CameraMood.APPROACH:
			_approach_start_dist = _distance
			_approach_end_dist = 30.0
			_approach_start_pitch = _pitch_deg
			_approach_end_pitch = 24.0
			_mood_target_yaw_speed = 0.006
			_mood_target_offset = Vector3.ZERO
			_blend_duration = 4.0
		CameraMood.DRIFT:
			_mood_target_dist = randf_range(35.0, 55.0)
			_mood_target_pitch = randf_range(25.0, 40.0)
			_mood_target_yaw_speed = 0.003
			_mood_target_offset = Vector3.ZERO
			_blend_duration = 5.0
		CameraMood.PULLBACK:
			_approach_start_dist = _distance
			_pullback_end_dist = randf_range(85.0, 105.0)
			_approach_start_pitch = _pitch_deg
			_pullback_end_pitch = 40.0
			_mood_target_yaw_speed = 0.006
			_mood_target_offset = Vector3.ZERO
			_blend_duration = 4.0
		CameraMood.UNDERSIDE:
			_mood_target_dist = randf_range(35.0, 55.0)
			_mood_target_pitch = PITCH_MIN_DEG
			_mood_target_yaw_speed = 0.003
			_mood_target_offset = Vector3(0.0, 0.0, 4.0)
			_blend_duration = 6.0


func _smooth_step(t: float) -> float:
	return t * t * (3.0 - 2.0 * t)


func _stop_auto_camera() -> void:
	_auto_camera = false


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
	_stop_auto_camera()
	_distance = clampf(_distance * factor, DIST_MIN, DIST_MAX)


func _pan_by(rel: Vector2) -> void:
	_kill_tween()
	_stop_auto_camera()
	var basis := _camera.global_transform.basis
	var right := Vector3(basis.x.x, 0.0, basis.x.z).normalized()
	var fwd := Vector3(basis.z.x, 0.0, basis.z.z).normalized()
	var speed := PAN_SPEED * (_distance / DIST_DEFAULT)
	_target -= right * rel.x * speed
	_target += fwd * rel.y * speed


func _orbit_by(rel: Vector2) -> void:
	_kill_tween()
	_stop_auto_camera()
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
	_stop_auto_camera()
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
	_stop_auto_camera()
	if target_system_id >= 0 and _galaxy_view != null and _galaxy_view.get_galaxy() != null:
		var g: Galaxy = _galaxy_view.get_galaxy()
		if target_system_id < g.systems.size():
			_target = g.systems[target_system_id].pos
			_focused_id = target_system_id
	_distance = clampf(distance, DIST_MIN, DIST_MAX)
	_update_camera()
	_zoom_controller.update_from_distance(_distance)


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
