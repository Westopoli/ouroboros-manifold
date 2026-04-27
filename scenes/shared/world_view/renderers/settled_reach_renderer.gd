extends Node3D

const VORONOI_RESOLUTION := 2048
const MAX_SYSTEMS := 128

var _wv_data: Node
var _region_visuals: Dictionary = {}
var _connection_visuals: Dictionary = {}
var _highlight_tween: Tween
var _highlighted_node: MeshInstance3D
var _territory_viewport: SubViewport
var _territory_color_rect: ColorRect
var _territory_plane: MeshInstance3D
var _territory_registry: Dictionary = {}
var _system_data_image: Image
var _system_data_texture: ImageTexture
var _faction_colors_image: Image
var _faction_colors_texture: ImageTexture
var _faction_borders_image: Image
var _faction_borders_texture: ImageTexture
var _faction_color_to_index: Dictionary = {}
var _map_bounds: Rect2 = Rect2(-50, -50, 100, 100)

var _central_point: MeshInstance3D
var _stream_pivot: Node3D


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


func setup(data: Node, _container: Node = null) -> void:
	_wv_data = data
	_wv_data.region_added.connect(_on_region_added)
	_wv_data.region_updated.connect(_on_region_updated)
	_wv_data.region_removed.connect(_on_region_removed)
	_wv_data.regions_cleared.connect(_on_regions_cleared)
	_wv_data.territory_set.connect(_on_territory_set)
	_wv_data.territory_updated.connect(_on_territory_updated)
	_wv_data.territory_removed.connect(_on_territory_removed)
	_wv_data.connection_added.connect(_on_connection_added)
	_wv_data.connection_removed.connect(_on_connection_removed)
	_wv_data.flash_region_requested.connect(_on_flash_region_requested)
	_wv_data.flash_conflict_requested.connect(_on_flash_conflict_requested)
	_wv_data.highlight_changed.connect(_on_highlight_changed)
	_setup_territory_metaball()


func teardown() -> void:
	if _territory_plane:
		_territory_plane.queue_free()
		_territory_plane = null
	if _territory_viewport:
		_territory_viewport.queue_free()
		_territory_viewport = null
	_territory_color_rect = null
	_territory_registry.clear()
	_faction_color_to_index.clear()
	if _highlight_tween:
		_highlight_tween.kill()
		_highlight_tween = null
	_highlighted_node = null
	if _wv_data:
		_wv_data.region_added.disconnect(_on_region_added)
		_wv_data.region_updated.disconnect(_on_region_updated)
		_wv_data.region_removed.disconnect(_on_region_removed)
		_wv_data.regions_cleared.disconnect(_on_regions_cleared)
		_wv_data.territory_set.disconnect(_on_territory_set)
		_wv_data.territory_updated.disconnect(_on_territory_updated)
		_wv_data.territory_removed.disconnect(_on_territory_removed)
		_wv_data.connection_added.disconnect(_on_connection_added)
		_wv_data.connection_removed.disconnect(_on_connection_removed)
		_wv_data.flash_region_requested.disconnect(_on_flash_region_requested)
		_wv_data.flash_conflict_requested.disconnect(_on_flash_conflict_requested)
		_wv_data.highlight_changed.disconnect(_on_highlight_changed)
	for node in _region_visuals.values():
		node.queue_free()
	_region_visuals.clear()
	for node in _connection_visuals.values():
		node.queue_free()
	_connection_visuals.clear()
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
	var tw := create_tween().set_loops()
	tw.tween_property(_central_point, "scale", Vector3.ONE * 1.08, 3.927).set_ease(Tween.EASE_IN_OUT).set_trans(Tween.TRANS_SINE)
	tw.tween_property(_central_point, "scale", Vector3.ONE * 0.92, 3.927).set_ease(Tween.EASE_IN_OUT).set_trans(Tween.TRANS_SINE)


func _start_stream_rotation() -> void:
	var tw := create_tween().set_loops()
	tw.tween_property(_stream_pivot, "rotation:y", TAU, TAU / 0.01).set_ease(Tween.EASE_IN_OUT)
	tw.tween_callback(func(): _stream_pivot.rotation.y = 0.0)


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
	node.material_override = _make_emissive_material(Color.WHITE, 4.0)
	if node.get_child_count() > 0:
		var shell_node: MeshInstance3D = node.get_child(0)
		if shell_node is MeshInstance3D:
			var shell_sphere: SphereMesh = shell_node.mesh
			shell_sphere.radius = r["size"] * 0.65
			shell_sphere.height = r["size"] * 1.3
			shell_node.material_override.albedo_color = Color(r["color"].r, r["color"].g, r["color"].b, 0.15)
			shell_node.material_override.emission = r["color"]


func _on_region_removed(region_id: String) -> void:
	if region_id in _region_visuals:
		_region_visuals[region_id].queue_free()
		_region_visuals.erase(region_id)


func _on_regions_cleared() -> void:
	for node in _region_visuals.values():
		node.queue_free()
	_region_visuals.clear()
	_territory_registry.clear()
	_rebuild_territory_data()


# --- Territory ---

func _setup_territory_metaball() -> void:
	_system_data_image = Image.create(MAX_SYSTEMS, 1, false, Image.FORMAT_RGBAF)
	_system_data_texture = ImageTexture.create_from_image(_system_data_image)
	_faction_colors_image = Image.create(8, 1, false, Image.FORMAT_RGBAF)
	_faction_colors_texture = ImageTexture.create_from_image(_faction_colors_image)
	_faction_borders_image = Image.create(8, 1, false, Image.FORMAT_RGBAF)
	_faction_borders_texture = ImageTexture.create_from_image(_faction_borders_image)

	_territory_viewport = SubViewport.new()
	_territory_viewport.size = Vector2i(VORONOI_RESOLUTION, VORONOI_RESOLUTION)
	_territory_viewport.transparent_bg = true
	_territory_viewport.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	add_child(_territory_viewport)

	_territory_color_rect = ColorRect.new()
	_territory_color_rect.set_anchors_preset(Control.PRESET_FULL_RECT)
	var shader_mat := ShaderMaterial.new()
	shader_mat.shader = load("res://scenes/shared/world_view/renderers/territory_metaball.gdshader")
	shader_mat.set_shader_parameter("system_data", _system_data_texture)
	shader_mat.set_shader_parameter("faction_colors", _faction_colors_texture)
	shader_mat.set_shader_parameter("faction_borders", _faction_borders_texture)
	shader_mat.set_shader_parameter("system_count", 0)
	shader_mat.set_shader_parameter("influence_radius", 0.17)
	shader_mat.set_shader_parameter("threshold", 0.66)
	shader_mat.set_shader_parameter("tube_width", 0.04)
	shader_mat.set_shader_parameter("tube_alpha", 0.95)
	shader_mat.set_shader_parameter("fill_opacity", 0.55)
	shader_mat.set_shader_parameter("fill_fade_depth", 0.8)
	shader_mat.set_shader_parameter("gap_margin", 0.30)
	_territory_color_rect.material = shader_mat
	_territory_viewport.add_child(_territory_color_rect)

	_territory_plane = MeshInstance3D.new()
	var pm := PlaneMesh.new()
	pm.size = Vector2(100, 100)
	_territory_plane.mesh = pm
	var plane_mat := StandardMaterial3D.new()
	plane_mat.albedo_texture = _territory_viewport.get_texture()
	plane_mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	plane_mat.blend_mode = BaseMaterial3D.BLEND_MODE_MIX
	plane_mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	plane_mat.render_priority = -1
	plane_mat.no_depth_test = true
	plane_mat.cull_mode = BaseMaterial3D.CULL_DISABLED
	_territory_plane.material_override = plane_mat
	_territory_plane.visible = false
	add_child(_territory_plane)


func _rebuild_territory_data() -> void:
	if _territory_registry.is_empty():
		_territory_plane.visible = false
		return

	var min_pos := Vector2(INF, INF)
	var max_pos := Vector2(-INF, -INF)
	var max_radius := 1.0

	for entry in _territory_registry.values():
		var pos_2d := Vector2(entry["center"].x, entry["center"].z)
		min_pos = min_pos.min(pos_2d)
		max_pos = max_pos.max(pos_2d)
		max_radius = maxf(max_radius, entry["radius"])

	var margin := max_radius * 1.5
	min_pos -= Vector2(margin, margin)
	max_pos += Vector2(margin, margin)
	_map_bounds = Rect2(min_pos, max_pos - min_pos)

	var img := Image.create(MAX_SYSTEMS, 1, false, Image.FORMAT_RGBAF)
	var idx := 0
	for rid in _territory_registry:
		var entry: Dictionary = _territory_registry[rid]
		if idx >= MAX_SYSTEMS:
			break
		var pos_2d := Vector2(entry["center"].x, entry["center"].z)
		var norm_x := (pos_2d.x - min_pos.x) / _map_bounds.size.x
		var norm_y := (pos_2d.y - min_pos.y) / _map_bounds.size.y
		var faction_idx_norm: float = float(entry["faction_index"]) / 8.0
		var significance := clampf(entry["radius"] / max_radius, 0.0, 1.0)
		img.set_pixel(idx, 0, Color(norm_x, norm_y, faction_idx_norm, significance))
		idx += 1

	_system_data_image = img
	_system_data_texture.update(_system_data_image)

	var shader_mat: ShaderMaterial = _territory_color_rect.material
	shader_mat.set_shader_parameter("system_count", idx)
	shader_mat.set_shader_parameter("system_data", _system_data_texture)

	var pm: PlaneMesh = _territory_plane.mesh
	pm.size = Vector2(_map_bounds.size.x, _map_bounds.size.y)

	var avg_y := 0.0
	var count := 0
	for entry in _territory_registry.values():
		avg_y += entry["center"].y
		count += 1
	if count > 0:
		avg_y /= float(count)

	_territory_plane.position = Vector3(
		_map_bounds.position.x + _map_bounds.size.x * 0.5,
		avg_y,
		_map_bounds.position.y + _map_bounds.size.y * 0.5
	)
	_territory_plane.visible = true


func _register_faction_color(color: Color) -> int:
	if color in _faction_color_to_index:
		return _faction_color_to_index[color]
	var idx: int = _faction_color_to_index.size() + 1
	if idx > 8:
		return 1
	_faction_color_to_index[color] = idx
	_faction_colors_image.set_pixel(idx - 1, 0, Color(color.r * 0.9, color.g * 0.9, color.b * 0.9, 1.0))
	_faction_colors_texture.update(_faction_colors_image)
	_faction_borders_image.set_pixel(idx - 1, 0, Color(
		minf(color.r * 1.3, 1.0),
		minf(color.g * 1.3, 1.0),
		minf(color.b * 1.3, 1.0),
		1.0
	))
	_faction_borders_texture.update(_faction_borders_image)
	var shader_mat: ShaderMaterial = _territory_color_rect.material
	shader_mat.set_shader_parameter("faction_colors", _faction_colors_texture)
	shader_mat.set_shader_parameter("faction_borders", _faction_borders_texture)
	return idx


func _on_territory_set(region_id: String) -> void:
	var t: Dictionary = _wv_data.get_territory(region_id)
	var faction_idx := _register_faction_color(t["color"])
	_territory_registry[region_id] = {
		"center": t["center"],
		"radius": t["radius"],
		"color": t["color"],
		"faction_index": faction_idx,
	}
	_rebuild_territory_data()


func _on_territory_updated(region_id: String) -> void:
	var t: Dictionary = _wv_data.get_territory(region_id)
	var faction_idx := _register_faction_color(t["color"])
	_territory_registry[region_id] = {
		"center": t["center"],
		"radius": t["radius"],
		"color": t["color"],
		"faction_index": faction_idx,
	}
	_rebuild_territory_data()


func _on_territory_removed(region_id: String) -> void:
	_territory_registry.erase(region_id)
	_rebuild_territory_data()


# --- Connections ---

func _on_connection_added(from_id: String, to_id: String) -> void:
	var key := _connection_key(from_id, to_id)
	if key in _connection_visuals:
		_connection_visuals[key].queue_free()
		_connection_visuals.erase(key)

	var from_r: Dictionary = _wv_data.get_region(from_id)
	var to_r: Dictionary = _wv_data.get_region(to_id)
	if from_r.is_empty() or to_r.is_empty():
		return

	var conn: Dictionary = _wv_data.get_connection(from_id, to_id)
	if conn.is_empty():
		return

	var from_pos: Vector3 = from_r["position"]
	var to_pos: Vector3 = to_r["position"]
	var conn_type: String = conn.get("connection_type", "border")
	var color: Color = conn.get("color", Color.WHITE)

	var mesh_inst := MeshInstance3D.new()
	var im := ImmediateMesh.new()
	im.surface_begin(Mesh.PRIMITIVE_LINES)
	im.surface_add_vertex(from_pos)
	im.surface_add_vertex(to_pos)
	im.surface_end()
	mesh_inst.mesh = im

	var mat := StandardMaterial3D.new()
	mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	mat.emission_enabled = true
	mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA

	if conn_type == "trade":
		mat.albedo_color = Color(color.r, color.g, color.b, 0.15)
		mat.emission = color
		mat.emission_energy_multiplier = 1.0
	else:
		mat.albedo_color = Color(color.r, color.g, color.b, 0.4)
		mat.emission = color
		mat.emission_energy_multiplier = 2.0

	mesh_inst.material_override = mat
	add_child(mesh_inst)
	_connection_visuals[key] = mesh_inst


func _on_connection_removed(from_id: String, to_id: String) -> void:
	var key := _connection_key(from_id, to_id)
	if key in _connection_visuals:
		_connection_visuals[key].queue_free()
		_connection_visuals.erase(key)


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


func _connection_key(from_id: String, to_id: String) -> String:
	if from_id < to_id:
		return from_id + "::" + to_id
	return to_id + "::" + from_id
