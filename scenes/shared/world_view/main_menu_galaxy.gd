extends Node3D

signal structure_revealed
signal camera_mood_changed(mood: String)
signal camera_move_completed

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

const TRANSITION_DURATION := 5.0

var _camera: Camera3D
var _central_point: MeshInstance3D
var _stream_pivot: Node3D
var _grid_mesh: MeshInstance3D

const BASE_ORBIT_SPEED := 0.012

var _auto_camera := false
var _current_mood: CameraMood = CameraMood.WIDE_ORBIT
var _mood_timer := 0.0
var _mood_duration := 30.0
var _mood_time := 0.0
var _pullback_signaled := false

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

# --- World view integration (active when setup() is called, null otherwise) ---
var _wv_data: Node
var _region_visuals: Dictionary = {}
var _highlight_tween: Tween
var _highlighted_node: MeshInstance3D

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

	var total_azimuth := _base_azimuth + _offset_azimuth
	_camera.global_position = _orbit_pos(total_azimuth, _offset_elev, _offset_dist)

	if _offset_target.distance_to(_camera.global_position) > 0.1:
		_camera.look_at(_offset_target)

	if not _pullback_signaled and _current_mood == CameraMood.PULLBACK and _offset_dist > 75.0:
		_pullback_signaled = true
		structure_revealed.emit()

	if _mood_timer <= 0.0:
		_switch_mood()


func _smooth_step(t: float) -> float:
	return t * t * (3.0 - 2.0 * t)


func _update_mood_targets() -> void:
	var progress := clampf(_mood_time / _mood_duration, 0.0, 1.0)

	match _current_mood:
		CameraMood.APPROACH:
			var ease_p := _smooth_step(progress)
			var target_dist := lerpf(_mood_approach_start_dist, _mood_approach_end_dist, ease_p)
			var target_elev := lerpf(_mood_approach_start_elev, _mood_approach_end_elev, ease_p)
			_mood_target_dist = target_dist
			_mood_target_elev = target_elev
			_blend_from_dist = target_dist
			_blend_from_elev = target_elev
		CameraMood.PULLBACK:
			var ease_p := _smooth_step(progress)
			var target_dist := lerpf(_mood_approach_start_dist, _mood_pullback_end_dist, ease_p)
			var target_elev := lerpf(_mood_approach_start_elev, _mood_pullback_end_elev, ease_p)
			_mood_target_dist = target_dist
			_mood_target_elev = target_elev
			_blend_from_dist = target_dist
			_blend_from_elev = target_elev
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
	_pullback_signaled = false

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
	shader_mat.shader = load("res://scenes/shared/world_view/ring_particles.gdshader")
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
	shader_mat.shader = load("res://scenes/shared/world_view/stream_particles.gdshader")
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
	shader_mat.shader = load("res://scenes/shared/world_view/dust_particles.gdshader")
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
	shader_mat.shader = load("res://scenes/shared/world_view/starfield_particles.gdshader")
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


# --- World View Integration ---

func setup(data: Node, _container: Node = null) -> void:
	_wv_data = data
	_wv_data.region_added.connect(_on_region_added)
	_wv_data.region_updated.connect(_on_region_updated)
	_wv_data.region_removed.connect(_on_region_removed)
	_wv_data.regions_cleared.connect(_on_regions_cleared)
	_wv_data.flash_region_requested.connect(_on_flash_region_requested)
	_wv_data.flash_conflict_requested.connect(_on_flash_conflict_requested)
	_wv_data.highlight_changed.connect(_on_highlight_changed)


func teardown() -> void:
	if _highlight_tween:
		_highlight_tween.kill()
		_highlight_tween = null
	_highlighted_node = null
	if _wv_data:
		_wv_data.region_added.disconnect(_on_region_added)
		_wv_data.region_updated.disconnect(_on_region_updated)
		_wv_data.region_removed.disconnect(_on_region_removed)
		_wv_data.regions_cleared.disconnect(_on_regions_cleared)
		_wv_data.flash_region_requested.disconnect(_on_flash_region_requested)
		_wv_data.flash_conflict_requested.disconnect(_on_flash_conflict_requested)
		_wv_data.highlight_changed.disconnect(_on_highlight_changed)
	for node in _region_visuals.values():
		node.queue_free()
	_region_visuals.clear()
	_wv_data = null


# --- Public API ---

func start_auto_camera() -> void:
	_auto_camera = true
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

func stop_auto_camera() -> void:
	_auto_camera = false

func move_camera_to(target_position: Vector3, look_at_target: Vector3, duration: float) -> void:
	_auto_camera = false
	var start_pos := _camera.global_position
	var start_target := _offset_target
	var tw := create_tween().set_ease(Tween.EASE_IN_OUT).set_trans(Tween.TRANS_CUBIC)
	tw.tween_method(func(t: float):
		_camera.global_position = start_pos.lerp(target_position, t)
		var current_target := start_target.lerp(look_at_target, t)
		if current_target.distance_to(_camera.global_position) > 0.1:
			_camera.look_at(current_target)
	, 0.0, 1.0, duration)
	tw.tween_callback(func(): camera_move_completed.emit())

func enable_manual_orbit() -> void:
	pass # Deferred: see docs/legacy/stage_specs/main_menu_galaxy_spec.md (Stage B/C — manual orbit)

func disable_manual_orbit() -> void:
	pass # Deferred: see docs/legacy/stage_specs/main_menu_galaxy_spec.md (Stage B/C — manual orbit)

func get_camera_position() -> Vector3:
	return _camera.global_position

func get_camera_target() -> Vector3:
	return _offset_target

func set_opacity(_alpha: float) -> void:
	pass

func set_particle_color(_color: Color) -> void:
	pass # Deferred: see docs/legacy/stage_specs/main_menu_galaxy_spec.md (Stage D — particle color)

func fade_in(_duration: float) -> void:
	pass # Fade applied on the SubViewportContainer by the consumer

func fade_out(_duration: float) -> void:
	pass # Fade applied on the SubViewportContainer by the consumer

# --- Camera interface aliases (for shell compatibility) ---

func move_to_region(region_id: String, duration: float) -> void:
	var pos := region_id_to_world_position(region_id)
	var cam_pos := pos + _orbit_pos(_base_azimuth + PI, deg_to_rad(25.0), 30.0)
	move_camera_to(cam_pos, pos, duration)


func move_to_overview(duration: float) -> void:
	var center := Vector3.ZERO
	if _wv_data and not _wv_data.regions.is_empty():
		var bounds := get_world_bounds()
		center = Vector3(bounds.get_center().x, 0.0, bounds.get_center().y)
	var cam_pos := center + _orbit_pos(_base_azimuth, deg_to_rad(50.0), 80.0)
	move_camera_to(cam_pos, center, duration)


func move_to_position(pos: Vector3, look_at_target: Vector3, duration: float) -> void:
	move_camera_to(pos, look_at_target, duration)


func start_ambient_motion() -> void:
	start_auto_camera()


func stop_ambient_motion() -> void:
	stop_auto_camera()


func get_current_position() -> Vector3:
	return get_camera_position()


func get_current_target() -> Vector3:
	return get_camera_target()


# --- World View Signal Handlers ---

func get_world_bounds() -> Rect2:
	if _region_visuals.is_empty():
		return Rect2(-50, -50, 100, 100)
	var min_x := INF
	var min_z := INF
	var max_x := -INF
	var max_z := -INF
	for id in _wv_data.regions:
		var pos: Vector3 = _wv_data.regions[id]["position"]
		min_x = minf(min_x, pos.x)
		max_x = maxf(max_x, pos.x)
		min_z = minf(min_z, pos.z)
		max_z = maxf(max_z, pos.z)
	var margin := 15.0
	return Rect2(min_x - margin, min_z - margin, max_x - min_x + margin * 2, max_z - min_z + margin * 2)


func region_id_to_world_position(region_id: String) -> Vector3:
	if _wv_data:
		var r: Dictionary = _wv_data.get_region(region_id)
		if not r.is_empty():
			return r["position"]
	return Vector3.ZERO


func _on_region_added(region_id: String) -> void:
	var r: Dictionary = _wv_data.get_region(region_id)
	var node := MeshInstance3D.new()
	var sphere := SphereMesh.new()
	sphere.radius = r["size"] * 0.5
	sphere.height = r["size"]
	sphere.radial_segments = 16
	sphere.rings = 8
	node.mesh = sphere
	node.material_override = _make_emissive_material(Color.WHITE, 4.0)
	node.position = r["position"]
	add_child(node)
	_region_visuals[region_id] = node

	var shell := MeshInstance3D.new()
	var shell_sphere := SphereMesh.new()
	shell_sphere.radius = r["size"] * 0.65
	shell_sphere.height = r["size"] * 1.3
	shell_sphere.radial_segments = 24
	shell_sphere.rings = 12
	shell.mesh = shell_sphere
	var shell_mat := StandardMaterial3D.new()
	shell_mat.albedo_color = Color(r["color"].r, r["color"].g, r["color"].b, 0.15)
	shell_mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	shell_mat.cull_mode = BaseMaterial3D.CULL_FRONT
	shell_mat.emission_enabled = true
	shell_mat.emission = r["color"]
	shell_mat.emission_energy_multiplier = 2.0
	shell_mat.rim_enabled = true
	shell_mat.rim = 1.0
	shell_mat.rim_tint = 0.0
	shell_mat.render_priority = -1
	shell.material_override = shell_mat
	node.add_child(shell)


func _on_region_updated(region_id: String) -> void:
	if region_id not in _region_visuals:
		return
	var r: Dictionary = _wv_data.get_region(region_id)
	var node: MeshInstance3D = _region_visuals[region_id]
	var sphere: SphereMesh = node.mesh
	sphere.radius = r["size"] * 0.5
	sphere.height = r["size"]
	node.material_override = _make_emissive_material(Color.WHITE, 4.0)
	if node.get_child_count() > 0:
		var shell: MeshInstance3D = node.get_child(0)
		var shell_sphere: SphereMesh = shell.mesh
		shell_sphere.radius = r["size"] * 0.65
		shell_sphere.height = r["size"] * 1.3
		shell.material_override.albedo_color = Color(r["color"].r, r["color"].g, r["color"].b, 0.15)
		shell.material_override.emission = r["color"]


func _on_region_removed(region_id: String) -> void:
	if region_id in _region_visuals:
		_region_visuals[region_id].queue_free()
		_region_visuals.erase(region_id)


func _on_regions_cleared() -> void:
	for node in _region_visuals.values():
		node.queue_free()
	_region_visuals.clear()


func _on_flash_region_requested(region_id: String, intensity: float) -> void:
	if region_id not in _region_visuals:
		return
	var node: MeshInstance3D = _region_visuals[region_id]
	var pos: Vector3 = node.global_position
	var r: Dictionary = _wv_data.get_region(region_id)
	var color: Color = r.get("color", Color.WHITE)
	var base_energy := 2.5
	var tw := create_tween()
	for _rep in range(5):
		tw.tween_property(node.material_override, "emission_energy_multiplier", base_energy + intensity * 14.0, 0.15)
		tw.tween_property(node.material_override, "emission_energy_multiplier", base_energy, 0.85).set_ease(Tween.EASE_OUT)
	var count := randi_range(3, 3 + int(intensity * 7.0))
	for i in count:
		var delay := randf() * 0.20
		var offset := Vector3(randf_range(-3.0, 3.0), randf_range(-3.0, 3.0), randf_range(-3.0, 3.0))
		_spawn_flash_spark(pos + offset, color, intensity, delay)


func _on_flash_conflict_requested(from_id: String, to_id: String, intensity: float) -> void:
	var from_r: Dictionary = _wv_data.get_region(from_id)
	var to_r: Dictionary = _wv_data.get_region(to_id)
	if from_r.is_empty() or to_r.is_empty():
		return
	var from_pos: Vector3 = from_r["position"]
	var to_pos: Vector3 = to_r["position"]
	var color := Color(1.0, 0.4, 0.1)
	var count := randi_range(4, 4 + int(intensity * 8.0))
	for i in count:
		var t := randf()
		var base_pos := from_pos.lerp(to_pos, t)
		var scatter := Vector3(randf_range(-2.0, 2.0), randf_range(-2.0, 2.0), randf_range(-2.0, 2.0))
		var delay := randf() * 0.25
		_spawn_flash_spark(base_pos + scatter, color, intensity, delay)


func _spawn_flash_spark(pos: Vector3, _color: Color, intensity: float, delay: float) -> void:
	var spark := MeshInstance3D.new()
	spark.mesh = SphereMesh.new()
	spark.mesh.radius = randf_range(0.15, 0.4) * (0.5 + intensity * 0.5)
	spark.mesh.height = spark.mesh.radius * 2.0
	spark.mesh.radial_segments = 4
	spark.mesh.rings = 2
	var mat := StandardMaterial3D.new()
	mat.albedo_color = Color(1.0, 1.0, 1.0, 0.0)
	mat.emission_enabled = true
	mat.emission = Color.WHITE
	mat.emission_energy_multiplier = 30.0
	mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	mat.billboard_mode = BaseMaterial3D.BILLBOARD_ENABLED
	spark.material_override = mat
	spark.position = pos
	spark.visible = false
	add_child(spark)
	var lifespan := randf_range(0.06, 0.16)
	var tw := create_tween()
	tw.tween_callback(func():
		spark.visible = true
		mat.albedo_color.a = 1.0
	).set_delay(delay)
	tw.tween_property(mat, "albedo_color:a", 0.0, lifespan).set_ease(Tween.EASE_OUT)
	tw.parallel().tween_property(mat, "emission_energy_multiplier", 0.0, lifespan).set_ease(Tween.EASE_OUT)
	tw.tween_callback(func(): spark.queue_free())


func _on_highlight_changed(region_id: String) -> void:
	if _highlight_tween:
		_highlight_tween.kill()
		_highlight_tween = null
	if _highlighted_node:
		_highlighted_node.scale = Vector3.ONE
		_highlighted_node = null

	if region_id.is_empty() or region_id not in _region_visuals:
		return

	_highlighted_node = _region_visuals[region_id]
	_highlight_tween = create_tween().set_loops()
	_highlight_tween.tween_property(_highlighted_node, "scale", Vector3.ONE * 1.4, 0.6) \
		.set_ease(Tween.EASE_IN_OUT).set_trans(Tween.TRANS_SINE)
	_highlight_tween.tween_property(_highlighted_node, "scale", Vector3.ONE, 0.6) \
		.set_ease(Tween.EASE_IN_OUT).set_trans(Tween.TRANS_SINE)


func _make_emissive_material(color: Color, energy: float) -> StandardMaterial3D:
	var mat := StandardMaterial3D.new()
	mat.albedo_color = color
	mat.emission_enabled = true
	mat.emission = color
	mat.emission_energy_multiplier = energy
	mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	return mat
