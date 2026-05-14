extends Node3D

var _wv_data: Node
var _region_visuals: Dictionary = {}
var _constellation: Node3D
var _shell: Node3D
var _highlight_tween: Tween
var _highlighted_node: MeshInstance3D

var _central_point: MeshInstance3D
var _stream_pivot: Node3D

# Stage 11g — looping ambient tweens, paused via InspectionState.
# See also: scenes/world/world_view_inspection_state.gd
var _pulse_tween: Tween
var _rotation_tween: Tween


func _ready() -> void:
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
	for d in ring_defs:
		_build_ring(d[0], d[1], d[2], d[3], d[4], d[5], d[6], d[7], d[8],
			Color(1.0, 0.88, 0.5, d[9]), d[10], d[11])
	_build_radial_streams()
	_build_ambient_dust()
	_build_starfield()
	_build_grid_plane()
	_start_central_pulse()
	_start_stream_rotation()
	if FeatureFlags.ENABLE_INSPECTION_PAUSE:
		InspectionState.pause_changed.connect(set_paused)


func setup(data: Node, _container: Node = null) -> void:
	_wv_data = data
	_wv_data.region_added.connect(_on_region_added)
	_wv_data.region_updated.connect(_on_region_updated)
	_wv_data.region_removed.connect(_on_region_removed)
	_wv_data.regions_cleared.connect(_on_regions_cleared)
	_wv_data.flash_region_requested.connect(_on_flash_region_requested)
	_wv_data.flash_conflict_requested.connect(_on_flash_conflict_requested)
	_wv_data.highlight_changed.connect(_on_highlight_changed)
	_setup_constellation()
	_setup_shell()


func teardown() -> void:
	if _highlight_tween:
		_highlight_tween.kill()
		_highlight_tween = null
	_highlighted_node = null
	if _constellation:
		_constellation.teardown()
		_constellation.queue_free()
		_constellation = null
	if _shell:
		_shell.teardown()
		_shell.queue_free()
		_shell = null
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


# --- Galaxy building ---

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
	particles.visibility_aabb = AABB(Vector3(-200, -200, -200), Vector3(400, 400, 400))
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
	particles.visibility_aabb = AABB(Vector3(-200, -200, -200), Vector3(400, 400, 400))
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
	particles.visibility_aabb = AABB(Vector3(-200, -200, -200), Vector3(400, 400, 400))
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
	particles.visibility_aabb = AABB(Vector3(-200, -200, -200), Vector3(400, 400, 400))
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


# --- Stage 11g — pause coordinator hookup ---

func set_paused(paused: bool) -> void:
	if _pulse_tween != null and _pulse_tween.is_valid():
		if paused: _pulse_tween.pause()
		else:      _pulse_tween.play()
	if _rotation_tween != null and _rotation_tween.is_valid():
		if paused: _rotation_tween.pause()
		else:      _rotation_tween.play()
	if _highlight_tween != null and _highlight_tween.is_valid():
		if paused: _highlight_tween.pause()
		else:      _highlight_tween.play()


# --- Region signal handlers ---

func _on_region_added(region_id: String) -> void:
	var r: Dictionary = _wv_data.get_region(region_id)
	var node := MeshInstance3D.new()
	node.set_meta("region_id", region_id)
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

	# Collision shape for click-to-focus raycasting
	var body := StaticBody3D.new()
	var col := CollisionShape3D.new()
	var col_sphere := SphereShape3D.new()
	col_sphere.radius = r["size"] * 0.65
	col.shape = col_sphere
	body.add_child(col)
	node.add_child(body)


func _on_region_updated(region_id: String) -> void:
	if region_id not in _region_visuals:
		return
	var r: Dictionary = _wv_data.get_region(region_id)
	var node: MeshInstance3D = _region_visuals[region_id]
	var sphere: SphereMesh = node.mesh
	sphere.radius = r["size"] * 0.5
	sphere.height = r["size"]


func _on_region_removed(region_id: String) -> void:
	if region_id in _region_visuals:
		_region_visuals[region_id].queue_free()
		_region_visuals.erase(region_id)


func _on_regions_cleared() -> void:
	for node in _region_visuals.values():
		node.queue_free()
	_region_visuals.clear()


# --- Constellation ---

func _setup_constellation() -> void:
	var script := load("res://scenes/shared/world_view/renderers/constellation_renderer.gd")
	_constellation = Node3D.new()
	_constellation.set_script(script)
	_constellation.name = "ConstellationRenderer"
	add_child(_constellation)
	# Find zoom controller from camera sibling — set up after camera calls setup()
	var zoom_ctrl: Node = null
	await get_tree().process_frame
	for sibling in get_parent().get_children():
		if sibling.has_method("get_zoom_controller"):
			zoom_ctrl = sibling.get_zoom_controller()
			break
	_constellation.setup(_wv_data, zoom_ctrl)


# --- Shell ---

func _setup_shell() -> void:
	var script := load("res://scenes/shared/world_view/renderers/shell_renderer.gd")
	_shell = Node3D.new()
	_shell.set_script(script)
	_shell.name = "ShellRenderer"
	add_child(_shell)
	var zoom_ctrl: Node = null
	await get_tree().process_frame
	for sibling in get_parent().get_children():
		if sibling.has_method("get_zoom_controller"):
			zoom_ctrl = sibling.get_zoom_controller()
			break
	_shell.setup(_wv_data, zoom_ctrl)


# --- Flashes ---

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


# --- Highlight ---

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


# --- Public queries ---

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
	var margin_val := 15.0
	return Rect2(min_x - margin_val, min_z - margin_val, max_x - min_x + margin_val * 2, max_z - min_z + margin_val * 2)


func region_id_to_world_position(region_id: String) -> Vector3:
	if _wv_data:
		var r: Dictionary = _wv_data.get_region(region_id)
		if not r.is_empty():
			return r["position"]
	return Vector3.ZERO


# --- Utility ---

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


func _make_emissive_material(color: Color, energy: float) -> StandardMaterial3D:
	var mat := StandardMaterial3D.new()
	mat.albedo_color = color
	mat.emission_enabled = true
	mat.emission = color
	mat.emission_energy_multiplier = energy
	mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	return mat


