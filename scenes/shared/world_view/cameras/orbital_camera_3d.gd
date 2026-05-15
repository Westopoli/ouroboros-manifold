extends Node3D

signal camera_move_completed
signal camera_mood_changed(mood: String)
# Stage 11g — additive click signals. _focus_on_region behavior is gated on
# FeatureFlags.ENABLE_INSPECTION_PANELS so existing flow is preserved with flag off.
signal region_clicked(region_id: String)
signal empty_space_clicked()

enum CameraMood { WIDE_ORBIT, RING_FOLLOW, APPROACH, DRIFT, PULLBACK, UNDERSIDE }

const MOOD_NAMES := {
	CameraMood.WIDE_ORBIT: "wide_orbit",
	CameraMood.RING_FOLLOW: "ring_follow",
	CameraMood.APPROACH: "approach",
	CameraMood.DRIFT: "drift",
	CameraMood.PULLBACK: "pullback",
	CameraMood.UNDERSIDE: "underside",
}

const MOOD_DURATIONS := {
	CameraMood.WIDE_ORBIT: Vector2(10.0, 18.0),
	CameraMood.RING_FOLLOW: Vector2(8.0, 14.0),
	CameraMood.APPROACH: Vector2(10.0, 16.0),
	CameraMood.DRIFT: Vector2(8.0, 14.0),
	CameraMood.PULLBACK: Vector2(10.0, 16.0),
	CameraMood.UNDERSIDE: Vector2(8.0, 12.0),
}

const BASE_ORBIT_SPEED := 0.012
const PAN_SPEED := 0.5
const ORBIT_SPEED := 0.01
const ZOOM_SPEED := 5.0
const ZOOM_MIN := 15.0
const ZOOM_MAX := 120.0
const FOCUS_DURATION := 1.5

var _camera: Camera3D
var _renderer: Node
var _zoom_controller: Node

var _auto_camera := false
var _current_mood: CameraMood = CameraMood.WIDE_ORBIT
var _mood_timer := 0.0
var _mood_duration := 30.0
var _mood_time := 0.0

var _base_azimuth := 0.0
var _offset_dist := 80.0
var _offset_elev := 0.6
var _offset_azimuth := 0.0
var _offset_target := Vector3.ZERO

var _mood_target_dist := 80.0
var _mood_target_elev := 0.6
var _mood_target_azimuth_speed := 0.02
var _mood_target_target := Vector3.ZERO

var _blend_from_dist := 80.0
var _blend_from_elev := 0.6
var _blend_from_target := Vector3.ZERO
var _blend_timer := 0.0
var _blend_duration := 6.0

var _mood_approach_start_dist := 80.0
var _mood_approach_end_dist := 15.0
var _mood_approach_start_elev := 0.5
var _mood_approach_end_elev := deg_to_rad(15.0)
var _mood_pullback_end_dist := 90.0
var _mood_pullback_end_elev := deg_to_rad(35.0)

var _dragging_pan := false
var _dragging_orbit := false
var _last_mouse_pos := Vector2.ZERO
var _drag_start_pos := Vector2.ZERO
var _auto_paused_by_input := false
var _move_tween: Tween


func setup(renderer: Node) -> void:
	_renderer = renderer
	_camera = Camera3D.new()
	_camera.position = Vector3(0, 45, 65)
	_camera.fov = 50.0
	_camera.current = true
	add_child(_camera)
	_camera.look_at(Vector3.ZERO)

	var zdc_script := load("res://scenes/shared/world_view/zoom_disclosure_controller.gd")
	_zoom_controller = Node.new()
	_zoom_controller.set_script(zdc_script)
	_zoom_controller.name = "ZoomDisclosureController"
	add_child(_zoom_controller)

	# Stage 11g Checkpoint L — pause ambient drift while any inspection holder
	# is active (region/faction panel, chronicle expansion). Resume restores
	# orbit from the current camera position (no auto-pan to overview).
	# See also: scenes/world/world_view_inspection_state.gd
	if FeatureFlags.ENABLE_INSPECTION_PAUSE and not InspectionState.pause_changed.is_connected(_on_inspection_pause_changed):
		InspectionState.pause_changed.connect(_on_inspection_pause_changed)


func _on_inspection_pause_changed(paused: bool) -> void:
	if paused:
		stop_ambient_motion()
	else:
		start_ambient_motion()


func teardown() -> void:
	_renderer = null


func _process(delta: float) -> void:
	if not _camera:
		return

	# Don't fight with active move tweens — they drive camera position directly
	if _move_tween and _move_tween.is_valid() and _move_tween.is_running():
		if _zoom_controller:
			_zoom_controller.update_from_distance(_offset_dist)
		return

	if _auto_camera:
		_base_azimuth += BASE_ORBIT_SPEED * delta
		_mood_time += delta
		_mood_timer -= delta
		_blend_timer += delta
		_update_mood_targets()

		var blend_t := clampf(_blend_timer / _blend_duration, 0.0, 1.0)
		var ease_t := _smooth_step(blend_t)
		_offset_dist = lerpf(_blend_from_dist, _mood_target_dist, ease_t)
		_offset_elev = lerpf(_blend_from_elev, _mood_target_elev, ease_t)
		_offset_azimuth += _mood_target_azimuth_speed * delta
		_offset_target = _blend_from_target.lerp(_mood_target_target, ease_t)

		if _mood_timer <= 0.0:
			_switch_mood()

	_offset_dist = clampf(_offset_dist, ZOOM_MIN, ZOOM_MAX)
	var total_azimuth := _base_azimuth + _offset_azimuth
	_camera.global_position = _offset_target + _orbit_pos(total_azimuth, _offset_elev, _offset_dist)
	if _offset_target.distance_to(_camera.global_position) > 0.1:
		_camera.look_at(_offset_target)

	if _zoom_controller:
		_zoom_controller.update_from_distance(_offset_dist)



func _input(event: InputEvent) -> void:
	if not _camera:
		return

	if event is InputEventMouseButton:
		match event.button_index:
			MOUSE_BUTTON_LEFT:
				if event.pressed:
					_dragging_orbit = true
					_last_mouse_pos = event.position
					_drag_start_pos = event.position
					_pause_auto_if_needed()
				else:
					_dragging_orbit = false
					if not _dragging_pan:
						_resume_auto_if_paused()
					if _drag_start_pos.distance_to(event.position) < 4.0:
						_try_click_focus(event.position)
			MOUSE_BUTTON_RIGHT:
				if event.pressed:
					_dragging_pan = true
					_last_mouse_pos = event.position
					_pause_auto_if_needed()
				else:
					_dragging_pan = false
					if not _dragging_orbit:
						_resume_auto_if_paused()
			MOUSE_BUTTON_WHEEL_UP:
				_offset_dist -= ZOOM_SPEED
				_offset_dist = clampf(_offset_dist, ZOOM_MIN, ZOOM_MAX)
			MOUSE_BUTTON_WHEEL_DOWN:
				_offset_dist += ZOOM_SPEED
				_offset_dist = clampf(_offset_dist, ZOOM_MIN, ZOOM_MAX)

	elif event is InputEventPanGesture:
		_offset_dist += event.delta.y * 2.0
		_offset_dist = clampf(_offset_dist, ZOOM_MIN, ZOOM_MAX)

	elif event is InputEventMouseMotion:
		var motion: InputEventMouseMotion = event
		if _dragging_orbit:
			var delta_mouse: Vector2 = motion.position - _last_mouse_pos
			_last_mouse_pos = motion.position
			_offset_azimuth -= delta_mouse.x * ORBIT_SPEED
			_offset_elev += delta_mouse.y * ORBIT_SPEED
			_offset_elev = clampf(_offset_elev, deg_to_rad(-80.0), deg_to_rad(80.0))
		elif _dragging_pan:
			var delta_mouse: Vector2 = motion.position - _last_mouse_pos
			_last_mouse_pos = motion.position
			var right := _camera.global_transform.basis.x
			_offset_target -= right * delta_mouse.x * PAN_SPEED * 0.1
			_offset_target += Vector3.UP * delta_mouse.y * PAN_SPEED * 0.1


func _pause_auto_if_needed() -> void:
	if _auto_camera:
		_auto_camera = false
		_auto_paused_by_input = true


func _resume_auto_if_paused() -> void:
	if _auto_paused_by_input:
		_auto_camera = true
		_auto_paused_by_input = false


func _try_click_focus(screen_pos: Vector2) -> void:
	var space := get_world_3d()
	if not space:
		return
	var state := space.direct_space_state
	if not state:
		return
	var from := _camera.project_ray_origin(screen_pos)
	var dir := _camera.project_ray_normal(screen_pos)
	var query := PhysicsRayQueryParameters3D.create(from, from + dir * 500.0)
	var result := state.intersect_ray(query)
	if result.is_empty():
		empty_space_clicked.emit()
		return
	var collider: Node = result["collider"]
	var node: Node = collider.get_parent()
	if node and node.has_meta("region_id"):
		var region_id: String = node.get_meta("region_id")
		region_clicked.emit(region_id)
		# Preserve today's auto-focus behavior when inspection panels aren't wired up.
		# When ENABLE_INSPECTION_PANELS is true, the sequencer drives camera moves via
		# the region_clicked signal — see scenes/world/time_jump_sequencer.gd.
		if not FeatureFlags.ENABLE_INSPECTION_PANELS:
			_focus_on_region(region_id)
	else:
		empty_space_clicked.emit()


func _focus_on_region(region_id: String) -> void:
	if not _renderer:
		return
	var pos: Vector3 = _renderer.region_id_to_world_position(region_id)
	if pos == Vector3.ZERO:
		return
	_auto_camera = false
	_auto_paused_by_input = false
	# Approach from the current viewing angle — don't swing to the opposite side
	var from_target := _camera.global_position - pos
	var approach_az := atan2(from_target.z, from_target.x)
	var cam_pos := pos + _orbit_pos(approach_az, deg_to_rad(25.0), 22.0)
	move_to_position(cam_pos, pos, FOCUS_DURATION)


# --- Public API ---

func move_to_region(region_id: String, duration: float) -> void:
	if not _renderer:
		return
	var pos: Vector3 = _renderer.region_id_to_world_position(region_id)
	var from_target := _camera.global_position - pos
	var approach_az := atan2(from_target.z, from_target.x)
	var cam_pos := pos + _orbit_pos(approach_az, deg_to_rad(25.0), 30.0)
	move_to_position(cam_pos, pos, duration)


func move_to_overview(duration: float) -> void:
	var center := Vector3.ZERO
	if _renderer and _renderer.has_method("get_world_bounds"):
		var bounds: Rect2 = _renderer.get_world_bounds()
		center = Vector3(bounds.get_center().x, 0.0, bounds.get_center().y)
	var cam_pos := center + _orbit_pos(_base_azimuth, deg_to_rad(50.0), 80.0)
	move_to_position(cam_pos, center, duration)


func move_to_position(pos: Vector3, look_at_target: Vector3, duration: float) -> void:
	if _move_tween and _move_tween.is_valid():
		_move_tween.kill()
	_auto_camera = false
	_auto_paused_by_input = false
	var start_pos := _camera.global_position
	var start_target := _offset_target
	_move_tween = create_tween().set_ease(Tween.EASE_IN_OUT).set_trans(Tween.TRANS_CUBIC)
	_move_tween.tween_method(func(t: float):
		_camera.global_position = start_pos.lerp(pos, t)
		_offset_target = start_target.lerp(look_at_target, t)
		_offset_dist = _camera.global_position.distance_to(_offset_target)
		if _offset_target.distance_to(_camera.global_position) > 0.1:
			_camera.look_at(_offset_target)
	, 0.0, 1.0, duration)
	_move_tween.tween_callback(func():
		# Sync orbit state from final position so _process can take over smoothly
		var delta_pos := _camera.global_position - _offset_target
		_base_azimuth = atan2(delta_pos.z, delta_pos.x)
		_offset_azimuth = 0.0
		_offset_elev = asin(clampf(delta_pos.y / maxf(_offset_dist, 0.1), -1.0, 1.0))
		camera_move_completed.emit()
	)


func start_ambient_motion() -> void:
	_auto_camera = true
	_auto_paused_by_input = false
	var start_pos := _camera.global_position
	_base_azimuth = atan2(start_pos.z, start_pos.x)
	var dist_3d := start_pos.length()
	_offset_dist = maxf(dist_3d, 70.0)
	_offset_elev = asin(clampf(start_pos.y / maxf(dist_3d, 0.1), -1.0, 1.0))
	_offset_azimuth = 0.0
	_offset_target = Vector3.ZERO
	_mood_target_dist = _offset_dist
	_mood_target_elev = _offset_elev
	_mood_target_azimuth_speed = randf_range(0.015, 0.025)
	_mood_target_target = Vector3.ZERO
	_blend_from_dist = _offset_dist
	_blend_from_elev = _offset_elev
	_blend_from_target = Vector3.ZERO
	_blend_timer = 0.0
	_blend_duration = 6.0
	_current_mood = CameraMood.WIDE_ORBIT
	_mood_time = 0.0
	_mood_duration = 30.0
	_mood_timer = 5.0
	camera_mood_changed.emit(MOOD_NAMES[_current_mood])


func stop_ambient_motion() -> void:
	_auto_camera = false
	_auto_paused_by_input = false


func get_current_position() -> Vector3:
	if _camera:
		return _camera.global_position
	return Vector3.ZERO


func get_current_target() -> Vector3:
	return _offset_target


func get_zoom_controller() -> Node:
	return _zoom_controller


# --- Mood system ---

func _smooth_step(t: float) -> float:
	return t * t * (3.0 - 2.0 * t)


func _update_mood_targets() -> void:
	var progress := clampf(_mood_time / _mood_duration, 0.0, 1.0)
	match _current_mood:
		CameraMood.APPROACH:
			var ease_p := _smooth_step(progress)
			_mood_target_dist = lerpf(_mood_approach_start_dist, _mood_approach_end_dist, ease_p)
			_mood_target_elev = lerpf(_mood_approach_start_elev, _mood_approach_end_elev, ease_p)
			_blend_from_dist = _mood_target_dist
			_blend_from_elev = _mood_target_elev
		CameraMood.PULLBACK:
			var ease_p := _smooth_step(progress)
			_mood_target_dist = lerpf(_mood_approach_start_dist, _mood_pullback_end_dist, ease_p)
			_mood_target_elev = lerpf(_mood_approach_start_elev, _mood_pullback_end_elev, ease_p)
			_blend_from_dist = _mood_target_dist
			_blend_from_elev = _mood_target_elev
		CameraMood.DRIFT:
			_mood_target_target = Vector3(sin(_mood_time * 0.1) * 3.0, 0.0, cos(_mood_time * 0.1) * 3.0)


func _switch_mood() -> void:
	var available: Array[int] = []
	for mood_val in CameraMood.values():
		if mood_val != _current_mood:
			available.append(mood_val)
	var next_mood: CameraMood = available[randi() % available.size()] as CameraMood
	_current_mood = next_mood
	_mood_time = 0.0

	_blend_from_dist = _offset_dist
	_blend_from_elev = _offset_elev
	_blend_from_target = _offset_target
	_blend_timer = 0.0

	var dur_range: Vector2 = MOOD_DURATIONS[next_mood]
	_mood_duration = randf_range(dur_range.x, dur_range.y)
	_mood_timer = _mood_duration

	match next_mood:
		CameraMood.WIDE_ORBIT:
			_mood_target_dist = randf_range(70.0, 90.0)
			_mood_target_elev = randf_range(deg_to_rad(25.0), deg_to_rad(45.0))
			_mood_target_azimuth_speed = randf_range(0.015, 0.025)
			_mood_target_target = Vector3.ZERO
			_blend_duration = 6.0
		CameraMood.RING_FOLLOW:
			_mood_target_dist = 27.5
			_mood_target_elev = deg_to_rad(5.0)
			_mood_target_azimuth_speed = 0.10
			_mood_target_target = Vector3.ZERO
			_blend_duration = 5.0
		CameraMood.APPROACH:
			_mood_approach_start_dist = _offset_dist
			_mood_approach_start_elev = _offset_elev
			_mood_approach_end_dist = 15.0
			_mood_approach_end_elev = deg_to_rad(15.0)
			_mood_target_azimuth_speed = 0.01
			_mood_target_target = Vector3.ZERO
			_blend_duration = 4.0
		CameraMood.DRIFT:
			_mood_target_dist = randf_range(30.0, 50.0)
			_mood_target_elev = randf_range(deg_to_rad(10.0), deg_to_rad(25.0))
			_mood_target_azimuth_speed = 0.005
			_mood_target_target = Vector3(0.0, 0.0, 3.0)
			_blend_duration = 5.0
		CameraMood.PULLBACK:
			_mood_approach_start_dist = _offset_dist
			_mood_approach_start_elev = _offset_elev
			_mood_pullback_end_dist = randf_range(80.0, 100.0)
			_mood_pullback_end_elev = deg_to_rad(35.0)
			_mood_target_azimuth_speed = 0.01
			_mood_target_target = Vector3.ZERO
			_blend_duration = 4.0
		CameraMood.UNDERSIDE:
			_mood_target_dist = randf_range(30.0, 50.0)
			_mood_target_elev = randf_range(deg_to_rad(-30.0), deg_to_rad(-45.0))
			_mood_target_azimuth_speed = 0.005
			_mood_target_target = Vector3(0.0, 5.0, 0.0)
			_blend_duration = 6.0

	camera_mood_changed.emit(MOOD_NAMES[next_mood])


func _orbit_pos(azimuth: float, elevation: float, distance: float) -> Vector3:
	var y := sin(elevation) * distance
	var horiz := cos(elevation) * distance
	return Vector3(cos(azimuth) * horiz, y, sin(azimuth) * horiz)
