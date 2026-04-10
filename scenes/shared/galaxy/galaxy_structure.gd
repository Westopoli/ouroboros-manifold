extends Node3D

signal structure_revealed
signal camera_mood_changed(mood: String)

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
	CameraMood.WIDE_ORBIT: Vector2(25.0, 40.0),
	CameraMood.RING_FOLLOW: Vector2(20.0, 35.0),
	CameraMood.APPROACH: Vector2(25.0, 35.0),
	CameraMood.DRIFT: Vector2(20.0, 30.0),
	CameraMood.PULLBACK: Vector2(20.0, 30.0),
	CameraMood.UNDERSIDE: Vector2(15.0, 25.0),
}

const TRANSITION_DURATION := 5.0

var _camera: Camera3D
var _central_point: MeshInstance3D
var _stream_pivot: Node3D
var _grid_mesh: MeshInstance3D

var _auto_camera := false
var _current_mood: CameraMood = CameraMood.WIDE_ORBIT
var _mood_timer := 0.0
var _mood_duration := 30.0
var _transitioning := false
var _transition_timer := 0.0
var _transition_from_pos := Vector3.ZERO
var _transition_from_target := Vector3.ZERO
var _transition_to_pos := Vector3.ZERO
var _transition_to_target := Vector3.ZERO

var _camera_pos := Vector3(0, 45, 65)
var _camera_target := Vector3.ZERO
var _target_pos := Vector3(0, 45, 65)

var _mood_time := 0.0
var _mood_azimuth := 0.0
var _mood_start_pos := Vector3.ZERO
var _mood_end_pos := Vector3.ZERO
var _pullback_signaled := false
var _mood_orbit_dist := 80.0
var _mood_orbit_elev := 0.6
var _mood_orbit_speed := 0.02
var _mood_ring_y := 3.5

func _ready() -> void:
	_build_camera()
	_build_central_point()
	_build_central_glow()
	var ring_defs := [
		# [name, count, r_min, r_max, s_min, s_max, thickness, quad, energy, gold_alpha, tilt_x, tilt_z]
		["Ring01", 250, 10.0, 11.0, 0.10, 0.12, 0.3, 0.15, 3.0, 0.85, 0.0, 0.0],
		["Ring02", 250, 14.0, 15.0, 0.085, 0.105, 0.3, 0.15, 3.0, 0.85, PI / 2.0, 0.0],
		["Ring03", 250, 18.0, 19.0, 0.07, 0.09, 0.3, 0.16, 2.8, 0.85, PI / 3.0, PI / 6.0],
		["Ring04", 250, 22.0, 23.0, 0.06, 0.08, 0.4, 0.17, 2.6, 0.85, 0.0, PI / 3.0],
		["Ring05", 250, 26.0, 27.0, 0.05, 0.07, 0.4, 0.17, 2.5, 0.80, PI / 4.0, PI / 2.0],
		["Ring06", 250, 30.0, 31.0, 0.045, 0.065, 0.4, 0.18, 2.5, 0.80, 2.0 * PI / 3.0, 0.0],
		["Ring07", 250, 33.0, 34.0, 0.04, 0.06, 0.5, 0.18, 2.3, 0.75, PI / 6.0, PI / 4.0],
		["Ring08", 250, 36.0, 37.0, 0.035, 0.055, 0.5, 0.19, 2.3, 0.75, PI / 2.0, PI / 3.0],
		["Ring09", 250, 39.0, 40.0, 0.03, 0.05, 0.5, 0.19, 2.0, 0.70, 5.0 * PI / 6.0, PI / 6.0],
		["Ring10", 250, 42.0, 43.0, 0.025, 0.045, 0.6, 0.20, 2.0, 0.70, PI / 3.0, 2.0 * PI / 3.0],
		["Ring11", 250, 45.0, 46.0, 0.02, 0.04, 0.6, 0.20, 1.8, 0.65, 0.0, PI / 2.0],
		["Ring12", 250, 48.0, 49.0, 0.02, 0.035, 0.6, 0.20, 1.8, 0.65, PI / 4.0, 5.0 * PI / 6.0],
	]
	for d in ring_defs:
		_build_ring(d[0], d[1], d[2], d[3], d[4], d[5], d[6], d[7], d[8],
			Color(1.0, 0.88, 0.5, d[9]), d[10], d[11])
	_build_radial_streams()
	_build_ambient_dust()
	_build_starfield()
	_build_grid_plane()
	_start_central_pulse()
	_start_stream_rotation()


func _process(delta: float) -> void:
	if not _auto_camera:
		return

	if _transitioning:
		_transition_timer += delta
		var t := clampf(_transition_timer / TRANSITION_DURATION, 0.0, 1.0)
		var ease_t := _smooth_step(t)
		_camera_pos = _transition_from_pos.lerp(_transition_to_pos, ease_t)
		_camera_target = _transition_from_target.lerp(_transition_to_target, ease_t)
		if t >= 1.0:
			_transitioning = false
			_mood_time = 0.0
			_enter_mood(_current_mood)
	else:
		_mood_timer -= delta
		_mood_time += delta
		_update_mood(delta)
		if _mood_timer <= 0.0:
			_transition_to_next_mood()

	_camera.global_position = _camera_pos
	if _camera_target.distance_to(_camera.global_position) > 0.1:
		_camera.look_at(_camera_target)


func _smooth_step(t: float) -> float:
	return t * t * (3.0 - 2.0 * t)


func _enter_mood(mood: CameraMood) -> void:
	_mood_time = 0.0
	_pullback_signaled = false
	var dur_range: Vector2 = MOOD_DURATIONS[mood]
	_mood_duration = randf_range(dur_range.x, dur_range.y)
	_mood_timer = _mood_duration

	# Derive azimuth from current camera position to avoid jumps
	var current_azimuth := atan2(_camera_pos.z, _camera_pos.x)
	var current_dist := Vector2(_camera_pos.x, _camera_pos.z).length()

	match mood:
		CameraMood.WIDE_ORBIT:
			_mood_orbit_dist = maxf(current_dist, 70.0)
			_mood_orbit_elev = randf_range(deg_to_rad(25.0), deg_to_rad(45.0))
			_mood_orbit_speed = randf_range(0.015, 0.025)
			_mood_azimuth = current_azimuth
		CameraMood.RING_FOLLOW:
			_mood_azimuth = current_azimuth
			_mood_ring_y = _camera_pos.y
		CameraMood.APPROACH:
			_mood_start_pos = _camera_pos
			_mood_end_pos = _orbit_pos(current_azimuth + 0.3, deg_to_rad(15.0), 15.0)
		CameraMood.DRIFT:
			_mood_start_pos = _camera_pos
			var drift_dir := Vector3(randf_range(-1.0, 1.0), 0.0, randf_range(-1.0, 1.0)).normalized()
			_mood_end_pos = _mood_start_pos + drift_dir * 20.0
		CameraMood.PULLBACK:
			_mood_start_pos = _camera_pos
			_mood_end_pos = _orbit_pos(current_azimuth + 0.4, deg_to_rad(35.0), randf_range(80.0, 100.0))
		CameraMood.UNDERSIDE:
			_target_pos = _camera_pos


func _update_mood(delta: float) -> void:
	var progress := clampf(_mood_time / _mood_duration, 0.0, 1.0)

	match _current_mood:
		CameraMood.WIDE_ORBIT:
			_mood_azimuth += _mood_orbit_speed * delta
			_camera_pos = _orbit_pos(_mood_azimuth, _mood_orbit_elev, _mood_orbit_dist)
			_camera_target = Vector3.ZERO

		CameraMood.RING_FOLLOW:
			_mood_azimuth += 0.11 * delta
			_camera_pos = Vector3(cos(_mood_azimuth) * 27.5, _mood_ring_y, sin(_mood_azimuth) * 27.5)
			_camera_target = Vector3.ZERO

		CameraMood.APPROACH:
			var ease_p := _smooth_step(progress)
			_camera_pos = _mood_start_pos.lerp(_mood_end_pos, ease_p)
			_camera_target = Vector3.ZERO

		CameraMood.DRIFT:
			_camera_pos = _mood_start_pos.lerp(_mood_end_pos, progress)
			var target_drift := Vector3(sin(_mood_time * 0.1) * 3.0, 0.0, cos(_mood_time * 0.1) * 3.0)
			_camera_target = target_drift

		CameraMood.PULLBACK:
			var ease_p := _smooth_step(progress)
			_camera_pos = _mood_start_pos.lerp(_mood_end_pos, ease_p)
			_camera_target = Vector3.ZERO
			if not _pullback_signaled and _camera_pos.length() > 75.0:
				_pullback_signaled = true
				structure_revealed.emit()

		CameraMood.UNDERSIDE:
			var sway := sin(_mood_time * 0.2) * 5.0
			_camera_pos = _target_pos + Vector3(sway, 0.0, cos(_mood_time * 0.15) * 3.0)
			_camera_target = Vector3(0.0, 5.0, 0.0)


func _transition_to_next_mood() -> void:
	var available: Array[int] = []
	for mood_val in CameraMood.values():
		if mood_val != _current_mood:
			available.append(mood_val)

	var next_mood: CameraMood = available[randi() % available.size()] as CameraMood

	_transition_from_pos = _camera_pos
	_transition_from_target = _camera_target
	_current_mood = next_mood

	match next_mood:
		CameraMood.WIDE_ORBIT:
			var dist := randf_range(70.0, 90.0)
			var elev := randf_range(deg_to_rad(25.0), deg_to_rad(45.0))
			_mood_azimuth = randf() * TAU
			_transition_to_pos = _orbit_pos(_mood_azimuth, elev, dist)
			_transition_to_target = Vector3.ZERO
		CameraMood.RING_FOLLOW:
			_mood_azimuth = randf() * TAU
			_transition_to_pos = Vector3(cos(_mood_azimuth) * 27.5, 3.5, sin(_mood_azimuth) * 27.5)
			_transition_to_target = Vector3.ZERO
		CameraMood.APPROACH:
			var start_dist := randf_range(70.0, 85.0)
			var start_elev := randf_range(deg_to_rad(20.0), deg_to_rad(40.0))
			_mood_azimuth = randf() * TAU
			_mood_start_pos = _orbit_pos(_mood_azimuth, start_elev, start_dist)
			_mood_end_pos = _orbit_pos(_mood_azimuth + 0.3, deg_to_rad(15.0), 15.0)
			_transition_to_pos = _mood_start_pos
			_transition_to_target = Vector3.ZERO
		CameraMood.DRIFT:
			var dist := randf_range(30.0, 50.0)
			var angle := randf() * TAU
			_mood_start_pos = Vector3(cos(angle) * dist, randf_range(5.0, 20.0), sin(angle) * dist)
			var drift_dir := Vector3(randf_range(-1.0, 1.0), 0.0, randf_range(-1.0, 1.0)).normalized()
			_mood_end_pos = _mood_start_pos + drift_dir * 20.0
			_transition_to_pos = _mood_start_pos
			_transition_to_target = Vector3.ZERO
		CameraMood.PULLBACK:
			var angle := randf() * TAU
			_mood_start_pos = _orbit_pos(angle, deg_to_rad(15.0), randf_range(15.0, 20.0))
			_mood_end_pos = _orbit_pos(angle + 0.4, deg_to_rad(35.0), randf_range(80.0, 100.0))
			_transition_to_pos = _mood_start_pos
			_transition_to_target = Vector3.ZERO
		CameraMood.UNDERSIDE:
			var dist := randf_range(30.0, 50.0)
			var angle := randf() * TAU
			_target_pos = Vector3(cos(angle) * dist * 0.5, randf_range(-20.0, -35.0), sin(angle) * dist * 0.5)
			_transition_to_pos = _target_pos
			_transition_to_target = Vector3(0.0, 5.0, 0.0)

	_transitioning = true
	_transition_timer = 0.0
	camera_mood_changed.emit(MOOD_NAMES[next_mood])


func _orbit_pos(azimuth: float, elevation: float, distance: float) -> Vector3:
	var y := sin(elevation) * distance
	var horiz := cos(elevation) * distance
	return Vector3(cos(azimuth) * horiz, y, sin(azimuth) * horiz)


func _build_camera() -> void:
	_camera = Camera3D.new()
	_camera.position = Vector3(0, 45, 65)
	_camera.fov = 50.0
	_camera.current = true
	add_child(_camera)
	_camera.look_at(Vector3.ZERO)


func _build_central_point() -> void:
	_central_point = MeshInstance3D.new()
	var sphere := SphereMesh.new()
	sphere.radius = 1.5
	sphere.height = 3.0
	sphere.radial_segments = 32
	sphere.rings = 16
	_central_point.mesh = sphere

	var mat := StandardMaterial3D.new()
	mat.albedo_color = Color(1.0, 0.95, 0.75, 1.0)
	mat.emission_enabled = true
	mat.emission = Color(1.0, 0.90, 0.55)
	mat.emission_energy_multiplier = 2.5
	mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	_central_point.material_override = mat
	add_child(_central_point)

	# Soft halo behind central glow — billboard quad with radial gradient
	var halo := MeshInstance3D.new()
	var halo_quad := QuadMesh.new()
	halo_quad.size = Vector2(20.0, 20.0)
	halo.mesh = halo_quad

	var grad := GradientTexture2D.new()
	var g := Gradient.new()
	g.set_color(0, Color(1.0, 0.92, 0.6, 1.0))
	g.set_color(1, Color(1.0, 0.92, 0.6, 0.0))
	grad.gradient = g
	grad.fill = GradientTexture2D.FILL_RADIAL
	grad.fill_from = Vector2(0.5, 0.5)
	grad.fill_to = Vector2(0.5, 0.0)
	grad.width = 256
	grad.height = 256

	var halo_mat := StandardMaterial3D.new()
	halo_mat.albedo_color = Color(1.0, 0.92, 0.6, 0.5)
	halo_mat.albedo_texture = grad
	halo_mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	halo_mat.blend_mode = BaseMaterial3D.BLEND_MODE_ADD
	halo_mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	halo_mat.billboard_mode = BaseMaterial3D.BILLBOARD_ENABLED
	halo_mat.no_depth_test = true
	halo.material_override = halo_mat
	add_child(halo)


func _build_central_glow() -> void:
	var particles := GPUParticles3D.new()
	particles.amount = 200
	particles.lifetime = 6.0
	particles.fixed_fps = 60
	particles.interpolate = true

	var proc_mat := ParticleProcessMaterial.new()
	proc_mat.emission_shape = ParticleProcessMaterial.EMISSION_SHAPE_SPHERE
	proc_mat.emission_sphere_radius = 3.0
	proc_mat.initial_velocity_min = 0.3
	proc_mat.initial_velocity_max = 1.0
	proc_mat.damping_min = 2.0
	proc_mat.damping_max = 4.0
	proc_mat.gravity = Vector3.ZERO
	proc_mat.color = Color(1.0, 0.92, 0.6, 0.6)
	particles.process_material = proc_mat

	particles.draw_pass_1 = _make_particle_quad(0.3)
	particles.material_override = _make_additive_material(
		Color(1.0, 0.92, 0.6, 0.6),
		Color(1.0, 0.90, 0.55),
		3.0
	)
	add_child(particles)


func _build_ring(ring_name: String, count: int, r_min: float, r_max: float,
		s_min: float, s_max: float, thickness: float, quad_size: float,
		energy: float, gold_override := Color(1.0, 0.88, 0.5, 0.85),
		p_tilt_x := 0.0, p_tilt_z := 0.0) -> void:
	var particles := GPUParticles3D.new()
	particles.name = ring_name
	particles.amount = count
	particles.lifetime = 1000.0
	particles.explosiveness = 1.0
	particles.fixed_fps = 60
	particles.interpolate = true

	var shader_mat := ShaderMaterial.new()
	shader_mat.shader = load("res://scenes/shared/galaxy/ring_particles.gdshader")
	shader_mat.set_shader_parameter("radius_min", r_min)
	shader_mat.set_shader_parameter("radius_max", r_max)
	shader_mat.set_shader_parameter("speed_min", s_min)
	shader_mat.set_shader_parameter("speed_max", s_max)
	shader_mat.set_shader_parameter("disc_thickness", thickness)
	shader_mat.set_shader_parameter("total_particles", count)
	shader_mat.set_shader_parameter("blue_fraction", 0.15)
	shader_mat.set_shader_parameter("gold_color", gold_override)
	shader_mat.set_shader_parameter("blue_color", Color(0.7, 0.8, 1.0, 0.7))
	shader_mat.set_shader_parameter("tilt_x", p_tilt_x)
	shader_mat.set_shader_parameter("tilt_z", p_tilt_z)
	particles.process_material = shader_mat

	particles.draw_pass_1 = _make_particle_quad(quad_size)
	particles.material_override = _make_additive_material(
		Color(1.0, 0.88, 0.5, 0.85),
		Color(1.0, 0.88, 0.5),
		energy
	)
	add_child(particles)


func _build_radial_streams() -> void:
	_stream_pivot = Node3D.new()
	_stream_pivot.name = "StreamPivot"
	add_child(_stream_pivot)

	var particles := GPUParticles3D.new()
	particles.name = "RadialStreams"
	particles.amount = 600
	particles.lifetime = 1000.0
	particles.explosiveness = 1.0
	particles.fixed_fps = 60
	particles.interpolate = true

	var shader_mat := ShaderMaterial.new()
	shader_mat.shader = load("res://scenes/shared/galaxy/stream_particles.gdshader")
	shader_mat.set_shader_parameter("outer_radius", 45.0)
	shader_mat.set_shader_parameter("inner_radius", 5.0)
	shader_mat.set_shader_parameter("flow_speed", 0.03)
	shader_mat.set_shader_parameter("stream_width", 1.5)
	shader_mat.set_shader_parameter("y_scatter", 1.5)
	shader_mat.set_shader_parameter("num_streams", 6)
	shader_mat.set_shader_parameter("stream_color", Color(1.0, 0.92, 0.65, 0.7))
	particles.process_material = shader_mat

	particles.draw_pass_1 = _make_particle_quad(0.12)
	particles.material_override = _make_additive_material(
		Color(1.0, 0.92, 0.65, 0.7),
		Color(1.0, 0.90, 0.55),
		2.5
	)
	_stream_pivot.add_child(particles)


func _build_ambient_dust() -> void:
	var particles := GPUParticles3D.new()
	particles.name = "AmbientDust"
	particles.amount = 400
	particles.lifetime = 20.0
	particles.fixed_fps = 30
	particles.interpolate = true

	var shader_mat := ShaderMaterial.new()
	shader_mat.shader = load("res://scenes/shared/galaxy/dust_particles.gdshader")
	shader_mat.set_shader_parameter("sphere_radius", 60.0)
	shader_mat.set_shader_parameter("drift_speed", 0.3)
	shader_mat.set_shader_parameter("blue_fraction", 0.5)
	shader_mat.set_shader_parameter("gold_color", Color(1.0, 0.88, 0.5, 0.3))
	shader_mat.set_shader_parameter("blue_color", Color(0.6, 0.7, 1.0, 0.2))
	particles.process_material = shader_mat

	particles.draw_pass_1 = _make_particle_quad(0.1)
	particles.material_override = _make_additive_material(
		Color(1.0, 0.88, 0.5, 0.3),
		Color(1.0, 0.88, 0.5),
		1.5
	)
	add_child(particles)


func _build_starfield() -> void:
	var particles := GPUParticles3D.new()
	particles.name = "Starfield"
	particles.amount = 2000
	particles.lifetime = 1000.0
	particles.explosiveness = 1.0
	particles.fixed_fps = 0
	particles.interpolate = false

	var shader_mat := ShaderMaterial.new()
	shader_mat.shader = load("res://scenes/shared/galaxy/starfield_particles.gdshader")
	shader_mat.set_shader_parameter("sphere_radius", 55.0)
	shader_mat.set_shader_parameter("blue_fraction", 0.4)
	shader_mat.set_shader_parameter("gold_color", Color(1.0, 0.92, 0.7, 0.4))
	shader_mat.set_shader_parameter("blue_color", Color(0.7, 0.8, 1.0, 0.25))
	particles.process_material = shader_mat

	particles.draw_pass_1 = _make_particle_quad(0.2)
	particles.material_override = _make_additive_material(
		Color(1.0, 0.95, 0.8, 0.7),
		Color(1.0, 0.95, 0.8),
		2.5
	)
	add_child(particles)


func _build_grid_plane() -> void:
	_grid_mesh = MeshInstance3D.new()
	_grid_mesh.name = "GridPlane"
	_grid_mesh.position.y = -5.0

	var im := ImmediateMesh.new()
	var mat := StandardMaterial3D.new()
	mat.albedo_color = Color(0.8, 0.75, 0.55, 0.04)
	mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	mat.no_depth_test = true

	var ring_radii := [10.0, 20.0, 30.0, 40.0, 50.0]
	var segments := 64

	for radius in ring_radii:
		im.surface_begin(Mesh.PRIMITIVE_LINE_STRIP)
		for i in range(segments + 1):
			var angle := float(i) / float(segments) * TAU
			im.surface_add_vertex(Vector3(cos(angle) * radius, 0.0, sin(angle) * radius))
		im.surface_end()

	var radial_count := 12
	var max_radius := 50.0
	for i in range(radial_count):
		var angle := float(i) / float(radial_count) * TAU
		im.surface_begin(Mesh.PRIMITIVE_LINES)
		im.surface_add_vertex(Vector3.ZERO)
		im.surface_add_vertex(Vector3(cos(angle) * max_radius, 0.0, sin(angle) * max_radius))
		im.surface_end()

	_grid_mesh.mesh = im
	_grid_mesh.material_override = mat
	add_child(_grid_mesh)


func _start_central_pulse() -> void:
	var tw := create_tween().set_loops()
	tw.tween_property(_central_point, "scale", Vector3.ONE * 1.08, 3.927).set_ease(Tween.EASE_IN_OUT).set_trans(Tween.TRANS_SINE)
	tw.tween_property(_central_point, "scale", Vector3.ONE * 0.92, 3.927).set_ease(Tween.EASE_IN_OUT).set_trans(Tween.TRANS_SINE)


func _start_stream_rotation() -> void:
	var tw := create_tween().set_loops()
	tw.tween_property(_stream_pivot, "rotation:y", TAU, TAU / 0.01).set_ease(Tween.EASE_IN_OUT)
	tw.tween_callback(func(): _stream_pivot.rotation.y = 0.0)


func _make_particle_quad(size: float) -> QuadMesh:
	var quad := QuadMesh.new()
	quad.size = Vector2(size, size)
	return quad


func _make_additive_material(albedo: Color, emission: Color, energy: float) -> StandardMaterial3D:
	var mat := StandardMaterial3D.new()
	mat.albedo_color = albedo
	mat.emission_enabled = true
	mat.emission = emission
	mat.emission_energy_multiplier = energy
	mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	mat.blend_mode = BaseMaterial3D.BLEND_MODE_ADD
	mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	mat.billboard_mode = BaseMaterial3D.BILLBOARD_ENABLED
	return mat


# --- Public API ---

func start_auto_camera() -> void:
	_auto_camera = true
	_camera_pos = _camera.global_position
	_camera_target = Vector3.ZERO
	_current_mood = CameraMood.WIDE_ORBIT
	_enter_mood(_current_mood)
	camera_mood_changed.emit(MOOD_NAMES[_current_mood])

func stop_auto_camera() -> void:
	_auto_camera = false

func move_camera_to(target_position: Vector3, look_at_target: Vector3, duration: float) -> void:
	_auto_camera = false
	_transitioning = true
	_transition_timer = 0.0
	_transition_from_pos = _camera_pos
	_transition_from_target = _camera_target
	_transition_to_pos = target_position
	_transition_to_target = look_at_target
	# Re-enable _process for the transition
	_auto_camera = true
	var tw := create_tween()
	tw.tween_interval(duration)
	tw.tween_callback(func(): _auto_camera = false)

func enable_manual_orbit() -> void:
	pass # TODO: World view stage

func disable_manual_orbit() -> void:
	pass # TODO: World view stage

func get_camera_position() -> Vector3:
	return _camera.global_position

func get_camera_target() -> Vector3:
	return _camera_target

func set_opacity(_alpha: float) -> void:
	pass

func set_particle_color(_color: Color) -> void:
	pass # TODO: Stage D

func fade_in(_duration: float) -> void:
	pass # Fade applied on the SubViewportContainer by the consumer

func fade_out(_duration: float) -> void:
	pass # Fade applied on the SubViewportContainer by the consumer

# --- World View Integration (STUBBED) ---

func add_system_node(_node_id: String, _pos: Vector3, _size: float, _color: Color) -> void:
	pass # TODO: World view stage

func remove_system_node(_node_id: String) -> void:
	pass # TODO: World view stage

func update_system_node(_node_id: String, _size: float, _color: Color) -> void:
	pass # TODO: World view stage

func clear_system_nodes() -> void:
	pass # TODO: World view stage

func set_territory(_region_id: String, _center: Vector3, _radius: float, _color: Color) -> void:
	pass # TODO: World view stage

func update_territory(_region_id: String, _radius: float, _color: Color) -> void:
	pass # TODO: World view stage

func remove_territory(_region_id: String) -> void:
	pass # TODO: World view stage

func add_connection(_from_id: String, _to_id: String, _connection_type: String, _color: Color) -> void:
	pass # TODO: World view stage

func remove_connection(_from_id: String, _to_id: String) -> void:
	pass # TODO: World view stage

func flash_military_activity(_region_id: String, _intensity: float) -> void:
	pass # TODO: World view stage

func flash_conflict(_from_id: String, _to_id: String, _intensity: float) -> void:
	pass # TODO: World view stage

func highlight_system(_node_id: String) -> void:
	pass # TODO: World view stage

func clear_highlight() -> void:
	pass # TODO: World view stage
