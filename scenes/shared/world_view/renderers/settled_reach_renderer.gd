extends Node

const BORDER_SEGMENTS := 48
const CONTOUR_RESOLUTION := 256
const CONTOUR_THRESHOLD := 0.08
const CONTOUR_BRIGHTNESS := 1.4
const CONTOUR_LINE_THICKNESS := 1.5
const CONTOUR_COLOR := Color(0.788, 0.659, 0.298, 1.0)

var _data: Node
var _container: Node
var _region_visuals: Dictionary = {}
var _territory_visuals: Dictionary = {}
var _connection_visuals: Dictionary = {}
var _highlight_tween: Tween
var _highlighted_node: MeshInstance3D
var _contour_viewport: SubViewport
var _contour_camera: Camera3D
var _contour_container: Node3D
var _contour_quad: MeshInstance3D
var _contour_disks: Dictionary = {}
var _contour_gradient: GradientTexture2D


func setup(data: Node, container: Node) -> void:
	_data = data
	_container = container
	_data.region_added.connect(_on_region_added)
	_data.region_updated.connect(_on_region_updated)
	_data.region_removed.connect(_on_region_removed)
	_data.regions_cleared.connect(_on_regions_cleared)
	_data.territory_set.connect(_on_territory_set)
	_data.territory_updated.connect(_on_territory_updated)
	_data.territory_removed.connect(_on_territory_removed)
	_data.connection_added.connect(_on_connection_added)
	_data.connection_removed.connect(_on_connection_removed)
	_data.flash_region_requested.connect(_on_flash_region_requested)
	_data.flash_conflict_requested.connect(_on_flash_conflict_requested)
	_data.highlight_changed.connect(_on_highlight_changed)
	_setup_contour()


func teardown() -> void:
	for disk in _contour_disks.values():
		disk.queue_free()
	_contour_disks.clear()
	if _contour_quad:
		_contour_quad.queue_free()
		_contour_quad = null
	if _contour_viewport:
		_contour_viewport.queue_free()
		_contour_viewport = null
	_contour_camera = null
	_contour_container = null
	if _highlight_tween:
		_highlight_tween.kill()
		_highlight_tween = null
	_highlighted_node = null
	if _data:
		_data.region_added.disconnect(_on_region_added)
		_data.region_updated.disconnect(_on_region_updated)
		_data.region_removed.disconnect(_on_region_removed)
		_data.regions_cleared.disconnect(_on_regions_cleared)
		_data.territory_set.disconnect(_on_territory_set)
		_data.territory_updated.disconnect(_on_territory_updated)
		_data.territory_removed.disconnect(_on_territory_removed)
		_data.connection_added.disconnect(_on_connection_added)
		_data.connection_removed.disconnect(_on_connection_removed)
		_data.flash_region_requested.disconnect(_on_flash_region_requested)
		_data.flash_conflict_requested.disconnect(_on_flash_conflict_requested)
		_data.highlight_changed.disconnect(_on_highlight_changed)
	_region_visuals.clear()
	_territory_visuals.clear()
	_connection_visuals.clear()
	_data = null
	_container = null


func _setup_contour() -> void:
	var grad := Gradient.new()
	grad.offsets = [0.0, 0.7, 1.0]
	grad.colors = [Color.WHITE, Color.WHITE, Color(1, 1, 1, 0)]
	_contour_gradient = GradientTexture2D.new()
	_contour_gradient.width = 256
	_contour_gradient.fill = GradientTexture2D.FILL_RADIAL
	_contour_gradient.fill_from = Vector2(0.5, 0.5)
	_contour_gradient.fill_to = Vector2(1.0, 0.5)
	_contour_gradient.gradient = grad

	_contour_viewport = SubViewport.new()
	_contour_viewport.size = Vector2i(CONTOUR_RESOLUTION, CONTOUR_RESOLUTION)
	_contour_viewport.transparent_bg = true
	_contour_viewport.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	_contour_viewport.own_world_3d = true
	add_child(_contour_viewport)

	_contour_camera = Camera3D.new()
	_contour_camera.projection = Camera3D.PROJECTION_ORTHOGONAL
	_contour_camera.size = 100.0
	_contour_camera.position = Vector3(0, 100, 0)
	_contour_camera.rotation.x = -PI / 2.0
	_contour_camera.near = 0.1
	_contour_camera.far = 200.0
	_contour_viewport.add_child(_contour_camera)

	_contour_container = Node3D.new()
	_contour_viewport.add_child(_contour_container)

	_contour_quad = MeshInstance3D.new()
	var qm := QuadMesh.new()
	qm.size = Vector2(130, 130)
	_contour_quad.mesh = qm
	_contour_quad.position = Vector3(0, 0.01, 0)
	_contour_quad.rotation.x = -PI / 2.0
	var shader_mat := ShaderMaterial.new()
	shader_mat.shader = load("res://scenes/shared/world_view/renderers/territory_contour.gdshader")
	shader_mat.set_shader_parameter("faction_map", _contour_viewport.get_texture())
	shader_mat.set_shader_parameter("contour_threshold", CONTOUR_THRESHOLD)
	shader_mat.set_shader_parameter("line_thickness", CONTOUR_LINE_THICKNESS)
	shader_mat.set_shader_parameter("brightness", CONTOUR_BRIGHTNESS)
	shader_mat.set_shader_parameter("contour_color", CONTOUR_COLOR)
	_contour_quad.material_override = shader_mat
	_container.add_child(_contour_quad)


func _update_contour_bounds() -> void:
	if not _contour_camera or not _contour_quad:
		return
	var bounds := get_world_bounds()
	var center_x := bounds.position.x + bounds.size.x * 0.5
	var center_z := bounds.position.y + bounds.size.y * 0.5
	var extent := maxf(bounds.size.x, bounds.size.y) + 10.0
	_contour_camera.size = extent
	_contour_camera.position = Vector3(center_x, 100.0, center_z)
	_contour_quad.position = Vector3(center_x, 0.01, center_z)
	var qm: QuadMesh = _contour_quad.mesh
	qm.size = Vector2(extent, extent)


func _add_contour_disk(region_id: String) -> void:
	if not _contour_container:
		return
	var t: Dictionary = _data.get_territory(region_id)
	if t.is_empty():
		return
	_remove_contour_disk(region_id)
	var disk := MeshInstance3D.new()
	var qm := QuadMesh.new()
	qm.size = Vector2(t["radius"] * 2.0, t["radius"] * 2.0)
	disk.mesh = qm
	disk.position = Vector3(t["center"].x, 0.0, t["center"].z)
	disk.rotation.x = -PI / 2.0
	var mat := StandardMaterial3D.new()
	mat.albedo_color = t["color"]
	mat.albedo_texture = _contour_gradient
	mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	mat.no_depth_test = true
	disk.material_override = mat
	_contour_container.add_child(disk)
	_contour_disks[region_id] = disk


func _remove_contour_disk(region_id: String) -> void:
	if region_id in _contour_disks:
		_contour_disks[region_id].queue_free()
		_contour_disks.erase(region_id)


func get_world_bounds() -> Rect2:
	if _region_visuals.is_empty():
		return Rect2(-50, -50, 100, 100)
	var min_x := INF
	var min_z := INF
	var max_x := -INF
	var max_z := -INF
	for id in _data.regions:
		var pos: Vector3 = _data.regions[id]["position"]
		min_x = minf(min_x, pos.x)
		max_x = maxf(max_x, pos.x)
		min_z = minf(min_z, pos.z)
		max_z = maxf(max_z, pos.z)
	var margin := 15.0
	return Rect2(min_x - margin, min_z - margin, max_x - min_x + margin * 2, max_z - min_z + margin * 2)


func region_id_to_world_position(region_id: String) -> Vector3:
	if _data:
		var r: Dictionary = _data.get_region(region_id)
		if not r.is_empty():
			return r["position"]
	return Vector3.ZERO


func _on_region_added(region_id: String) -> void:
	var r: Dictionary = _data.get_region(region_id)
	var node := MeshInstance3D.new()
	var sphere := SphereMesh.new()
	sphere.radius = r["size"] * 0.5
	sphere.height = r["size"]
	sphere.radial_segments = 16
	sphere.rings = 8
	node.mesh = sphere
	node.material_override = _make_emissive_material(r["color"], 2.5)
	node.position = r["position"]
	_container.add_child(node)
	_region_visuals[region_id] = node

	var halo := MeshInstance3D.new()
	var quad := QuadMesh.new()
	quad.size = Vector2(r["size"] * 3.0, r["size"] * 3.0)
	halo.mesh = quad
	var halo_mat := StandardMaterial3D.new()
	halo_mat.albedo_color = Color(r["color"].r, r["color"].g, r["color"].b, 0.25)
	halo_mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	halo_mat.blend_mode = BaseMaterial3D.BLEND_MODE_ADD
	halo_mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	halo_mat.billboard_mode = BaseMaterial3D.BILLBOARD_ENABLED
	halo_mat.no_depth_test = true
	halo.material_override = halo_mat
	node.add_child(halo)


func _on_region_updated(region_id: String) -> void:
	if region_id not in _region_visuals:
		return
	var r: Dictionary = _data.get_region(region_id)
	var node: MeshInstance3D = _region_visuals[region_id]
	var sphere: SphereMesh = node.mesh
	sphere.radius = r["size"] * 0.5
	sphere.height = r["size"]
	node.material_override = _make_emissive_material(r["color"], 2.5)
	if node.get_child_count() > 0:
		var halo: MeshInstance3D = node.get_child(0)
		var quad: QuadMesh = halo.mesh
		quad.size = Vector2(r["size"] * 3.0, r["size"] * 3.0)
		halo.material_override.albedo_color = Color(r["color"].r, r["color"].g, r["color"].b, 0.25)


func _on_region_removed(region_id: String) -> void:
	if region_id in _region_visuals:
		_region_visuals[region_id].queue_free()
		_region_visuals.erase(region_id)


func _on_regions_cleared() -> void:
	for node in _region_visuals.values():
		node.queue_free()
	_region_visuals.clear()
	for disk in _contour_disks.values():
		disk.queue_free()
	_contour_disks.clear()


func _on_territory_set(region_id: String) -> void:
	var t: Dictionary = _data.get_territory(region_id)

	var group := Node3D.new()
	group.position = t["center"]
	_container.add_child(group)

	var bubble := MeshInstance3D.new()
	var sphere := SphereMesh.new()
	sphere.radius = t["radius"]
	sphere.height = t["radius"] * 2.0
	sphere.radial_segments = 24
	sphere.rings = 12
	bubble.mesh = sphere
	var mat := StandardMaterial3D.new()
	mat.albedo_color = Color(t["color"].r, t["color"].g, t["color"].b, 0.08)
	mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	mat.cull_mode = BaseMaterial3D.CULL_DISABLED
	mat.no_depth_test = true
	bubble.material_override = mat
	group.add_child(bubble)

	var border_mat := _make_border_material(t["color"])

	var border := MeshInstance3D.new()
	border.mesh = _make_circle_mesh(t["radius"])
	border.material_override = border_mat
	group.add_child(border)

	var border_v := MeshInstance3D.new()
	border_v.mesh = _make_circle_mesh(t["radius"])
	border_v.material_override = border_mat
	border_v.rotation.y = PI / 2.0
	group.add_child(border_v)

	var border_h := MeshInstance3D.new()
	border_h.mesh = _make_circle_mesh(t["radius"])
	border_h.material_override = border_mat
	border_h.rotation.x = PI / 2.0
	group.add_child(border_h)

	_territory_visuals[region_id] = group
	_add_contour_disk(region_id)
	_update_contour_bounds()


func _on_territory_updated(region_id: String) -> void:
	if region_id in _territory_visuals:
		_territory_visuals[region_id].queue_free()
		_territory_visuals.erase(region_id)
	_on_territory_set(region_id)


func _on_territory_removed(region_id: String) -> void:
	if region_id in _territory_visuals:
		_territory_visuals[region_id].queue_free()
		_territory_visuals.erase(region_id)
	_remove_contour_disk(region_id)
	_update_contour_bounds()


func _on_connection_added(from_id: String, to_id: String) -> void:
	var from_r: Dictionary = _data.get_region(from_id)
	var to_r: Dictionary = _data.get_region(to_id)
	var conn: Dictionary = _data.get_connection(from_id, to_id)
	if from_r.is_empty() or to_r.is_empty():
		return

	var node := MeshInstance3D.new()
	var im := ImmediateMesh.new()
	var conn_type: String = conn.get("connection_type", "border")
	var is_trade: bool = conn_type == "trade"
	im.surface_begin(Mesh.PRIMITIVE_LINES)
	if is_trade:
		var start: Vector3 = from_r["position"]
		var end: Vector3 = to_r["position"]
		var seg_count := 9
		for i in range(seg_count):
			var t0 := float(i) / float(seg_count)
			var t1 := (float(i) + 0.6) / float(seg_count)
			im.surface_add_vertex(start.lerp(end, t0))
			im.surface_add_vertex(start.lerp(end, t1))
	else:
		im.surface_add_vertex(from_r["position"])
		im.surface_add_vertex(to_r["position"])
	im.surface_end()
	node.mesh = im
	var mat := StandardMaterial3D.new()
	var base_color: Color = conn["color"]
	if is_trade:
		base_color.a = 0.4
	mat.albedo_color = base_color
	mat.emission_enabled = true
	mat.emission = conn["color"]
	mat.emission_energy_multiplier = 1.0 if not is_trade else 0.5
	mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	node.material_override = mat
	_container.add_child(node)

	var key := _connection_key(from_id, to_id)
	_connection_visuals[key] = node


func _on_connection_removed(from_id: String, to_id: String) -> void:
	var key := _connection_key(from_id, to_id)
	if key in _connection_visuals:
		_connection_visuals[key].queue_free()
		_connection_visuals.erase(key)


func _on_flash_region_requested(region_id: String, intensity: float) -> void:
	if region_id not in _region_visuals:
		return
	var node: MeshInstance3D = _region_visuals[region_id]
	var mat: StandardMaterial3D = node.material_override
	var base_energy := 2.5
	var tw := _container.create_tween()
	tw.tween_property(mat, "emission_energy_multiplier", base_energy + intensity * 12.0, 0.1)
	tw.tween_property(mat, "emission_energy_multiplier", base_energy, 0.5).set_ease(Tween.EASE_OUT)


func _on_flash_conflict_requested(from_id: String, to_id: String, intensity: float) -> void:
	var from_r: Dictionary = _data.get_region(from_id)
	var to_r: Dictionary = _data.get_region(to_id)
	if from_r.is_empty() or to_r.is_empty():
		return

	var node := MeshInstance3D.new()
	var im := ImmediateMesh.new()
	im.surface_begin(Mesh.PRIMITIVE_LINES)
	im.surface_add_vertex(from_r["position"])
	im.surface_add_vertex(to_r["position"])
	im.surface_end()
	node.mesh = im
	var mat := StandardMaterial3D.new()
	mat.albedo_color = Color(1.0, 0.4, 0.1, intensity)
	mat.emission_enabled = true
	mat.emission = Color(1.0, 0.4, 0.1)
	mat.emission_energy_multiplier = intensity * 10.0
	mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	node.material_override = mat
	_container.add_child(node)

	var tw := _container.create_tween()
	tw.tween_property(mat, "albedo_color:a", 0.0, 0.6).set_ease(Tween.EASE_OUT)
	tw.parallel().tween_property(mat, "emission_energy_multiplier", 0.0, 0.6).set_ease(Tween.EASE_OUT)
	tw.tween_callback(func(): node.queue_free())


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
	_highlight_tween = _container.create_tween().set_loops()
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


func _make_circle_mesh(radius: float) -> ImmediateMesh:
	var im := ImmediateMesh.new()
	im.surface_begin(Mesh.PRIMITIVE_LINE_STRIP)
	for i in range(BORDER_SEGMENTS + 1):
		var angle := float(i) / float(BORDER_SEGMENTS) * TAU
		im.surface_add_vertex(Vector3(cos(angle) * radius, 0.0, sin(angle) * radius))
	im.surface_end()
	return im


func _make_border_material(color: Color) -> StandardMaterial3D:
	var mat := StandardMaterial3D.new()
	mat.albedo_color = Color(color.r, color.g, color.b, 0.3)
	mat.emission_enabled = true
	mat.emission = color
	mat.emission_energy_multiplier = 1.5
	mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	mat.no_depth_test = true
	return mat


func _connection_key(from_id: String, to_id: String) -> String:
	if from_id < to_id:
		return from_id + "::" + to_id
	return to_id + "::" + from_id
