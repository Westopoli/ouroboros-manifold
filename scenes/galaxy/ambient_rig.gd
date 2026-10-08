extends Node3D

# R-106-05 ambient field (rings, inflow streams, dust, starfield, central glow), built from
# the prototype rig scenes/mockups/galaxy/legacy_ambient_rig.gd. A60: galaxy_quality 2 halves
# every emitter's amount (never deletes one); tiers 0 and 1 carry the full field. The
# shaders are the mockup's, read in place.

const TIER_FEWER := 2

var _tier := 0

var _central_point: MeshInstance3D
var _stream_pivot: Node3D
var _pulse_tween: Tween
var _rotation_tween: Tween


func _ready() -> void:
	_tier = int(UIDataBus.get_settings().get("galaxy_quality", 0))
	_build_central_point()
	_build_central_glow()
	var ring_defs := [
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
	# Tilted rings (tilt_x/tilt_z != 0) alias into a single bright vertical
	# column under the Compatibility renderer at Overview/Regional distance —
	# confirmed by isolation (rings alone reproduce it; zeroing tilt alone
	# removes it; screenshots in pass2/probe/ring_tilt/). Not a shader compile
	# failure, so the pass-2 relaxation clause applies per-parameter rather
	# than swapping the whole shader: Westley's Forward+ seat keeps the tilt,
	# the Compatibility QA render flattens the rings instead.
	var flat_qa := RenderingServer.get_current_rendering_method() == "gl_compatibility"
	for d in ring_defs:
		_build_ring(d[0], d[1], d[2], d[3], d[4], d[5], d[6], d[7], d[8],
			Color(1.0, 0.88, 0.5, d[9]), 0.0 if flat_qa else d[10], 0.0 if flat_qa else d[11])
	_build_radial_streams()
	_build_ambient_dust()
	_build_starfield()
	_build_grid_plane()
	_start_central_pulse()
	_start_stream_rotation()


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
	particles.amount = _amt(200)
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
	particles.visibility_aabb = AABB(Vector3(-200, -200, -200), Vector3(400, 400, 400))
	add_child(particles)


func _build_ring(ring_name: String, count: int, r_min: float, r_max: float,
		s_min: float, s_max: float, thickness: float, quad_size: float,
		energy: float, gold_override := Color(1.0, 0.88, 0.5, 0.85),
		p_tilt_x := 0.0, p_tilt_z := 0.0) -> void:
	var particles := GPUParticles3D.new()
	particles.name = ring_name
	particles.amount = _amt(count)
	particles.lifetime = 1000.0
	particles.explosiveness = 1.0
	particles.fixed_fps = 60
	particles.interpolate = true

	var shader_mat := ShaderMaterial.new()
	shader_mat.shader = load("res://scenes/mockups/galaxy/shaders/ring_particles.gdshader")
	shader_mat.set_shader_parameter("radius_min", r_min)
	shader_mat.set_shader_parameter("radius_max", r_max)
	shader_mat.set_shader_parameter("speed_min", s_min)
	shader_mat.set_shader_parameter("speed_max", s_max)
	shader_mat.set_shader_parameter("disc_thickness", thickness)
	shader_mat.set_shader_parameter("total_particles", _amt(count))
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
	particles.visibility_aabb = AABB(Vector3(-200, -200, -200), Vector3(400, 400, 400))
	add_child(particles)


func _build_radial_streams() -> void:
	_stream_pivot = Node3D.new()
	_stream_pivot.name = "StreamPivot"
	add_child(_stream_pivot)

	var particles := GPUParticles3D.new()
	particles.name = "RadialStreams"
	particles.amount = _amt(600)
	particles.lifetime = 1000.0
	particles.explosiveness = 1.0
	particles.fixed_fps = 60
	particles.interpolate = true

	var shader_mat := ShaderMaterial.new()
	shader_mat.shader = load("res://scenes/mockups/galaxy/shaders/stream_particles.gdshader")
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
	particles.visibility_aabb = AABB(Vector3(-200, -200, -200), Vector3(400, 400, 400))
	_stream_pivot.add_child(particles)


func _build_ambient_dust() -> void:
	var particles := GPUParticles3D.new()
	particles.name = "AmbientDust"
	particles.amount = _amt(400)
	particles.lifetime = 20.0
	particles.fixed_fps = 30
	particles.interpolate = true

	var shader_mat := ShaderMaterial.new()
	shader_mat.shader = load("res://scenes/mockups/galaxy/shaders/dust_particles.gdshader")
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
	particles.visibility_aabb = AABB(Vector3(-200, -200, -200), Vector3(400, 400, 400))
	add_child(particles)


func _build_starfield() -> void:
	var particles := GPUParticles3D.new()
	particles.name = "Starfield"
	particles.amount = _amt(2000)
	particles.lifetime = 1000.0
	particles.explosiveness = 1.0
	particles.fixed_fps = 0
	particles.interpolate = false

	var shader_mat := ShaderMaterial.new()
	shader_mat.shader = load("res://scenes/mockups/galaxy/shaders/starfield_particles.gdshader")
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
	particles.visibility_aabb = AABB(Vector3(-200, -200, -200), Vector3(400, 400, 400))
	add_child(particles)


func _build_grid_plane() -> void:
	var grid := MeshInstance3D.new()
	grid.name = "GridPlane"
	grid.position.y = -5.0

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

	grid.mesh = im
	grid.material_override = mat
	add_child(grid)


func _start_central_pulse() -> void:
	_pulse_tween = create_tween().set_loops()
	_pulse_tween.tween_property(_central_point, "scale", Vector3.ONE * 1.08, 3.927).set_ease(Tween.EASE_IN_OUT).set_trans(Tween.TRANS_SINE)
	_pulse_tween.tween_property(_central_point, "scale", Vector3.ONE * 0.92, 3.927).set_ease(Tween.EASE_IN_OUT).set_trans(Tween.TRANS_SINE)


func _start_stream_rotation() -> void:
	_rotation_tween = create_tween().set_loops()
	_rotation_tween.tween_property(_stream_pivot, "rotation:y", TAU, TAU / 0.01).set_ease(Tween.EASE_IN_OUT)
	_rotation_tween.tween_callback(func(): _stream_pivot.rotation.y = 0.0)


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


func _amt(n: int) -> int:
	return maxi(1, n / 2) if _tier == TIER_FEWER else n
