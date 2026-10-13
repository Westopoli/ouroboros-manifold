extends Node3D

# Copied from scenes/shared/world_view/renderers/constellation_renderer.gd
# (2026-09-22) for the pass-2 galaxy mockup, changed only for the shader's
# res:// path (scenes/galaxy/shaders/, a copy — see galaxy_adapter.gd)
# and the zoom controller lookup (direct injection via setup(), since this
# mockup's tree shape differs from the live scene's sibling-search pattern).

const GalaxyGen := preload("res://scenes/galaxy/galaxy_gen.gd")

const TUBE_SIDES := 8
const CURVE_SEGMENTS := 16
const ARC_HEIGHT_FRACTION := 0.15
const FILAMENT_WIDTH_BORDER := 0.0375   # prototype legacy_constellation_renderer.gd:12, 0.075 x CIV_SCALE 0.5 (B23)
const FILAMENT_WIDTH_TRADE := 0.0175   # prototype legacy_constellation_renderer.gd:13, 0.035 x CIV_SCALE 0.5 (B23)

var _wv_data: Node
var _zoom_controller: Node
var _filament_visuals: Dictionary = {}
var _filament_shader: Shader

var _alpha_overview := 0.3
var _alpha_regional := 1.0
var _alpha_local := 1.0


func setup(data: Node, zoom_controller: Node) -> void:
	_wv_data = data
	_zoom_controller = zoom_controller
	_filament_shader = load("res://scenes/galaxy/shaders/constellation_filament.gdshader")
	_wv_data.connection_added.connect(_on_connection_added)
	_wv_data.connection_removed.connect(_on_connection_removed)
	_wv_data.regions_cleared.connect(_on_regions_cleared)


func get_filament_visuals() -> Dictionary:
	return _filament_visuals


func teardown() -> void:
	if _wv_data:
		if _wv_data.connection_added.is_connected(_on_connection_added):
			_wv_data.connection_added.disconnect(_on_connection_added)
		if _wv_data.connection_removed.is_connected(_on_connection_removed):
			_wv_data.connection_removed.disconnect(_on_connection_removed)
		if _wv_data.regions_cleared.is_connected(_on_regions_cleared):
			_wv_data.regions_cleared.disconnect(_on_regions_cleared)
	for node in _filament_visuals.values():
		node.queue_free()
	_filament_visuals.clear()
	_wv_data = null
	_zoom_controller = null


func _process(_delta: float) -> void:
	if not _zoom_controller or _filament_visuals.is_empty():
		return
	var band: String = _zoom_controller.current_band
	var blend: float = _zoom_controller.blend_factor
	var blend_dir: String = _zoom_controller.blend_direction

	var target_alpha := _alpha_regional
	match band:
		"overview":
			if blend_dir == "down":
				target_alpha = lerpf(_alpha_overview, _alpha_regional, blend)
			else:
				target_alpha = _alpha_overview
		"regional":
			if blend_dir == "down":
				target_alpha = lerpf(_alpha_regional, _alpha_local, blend)
			else:
				target_alpha = _alpha_regional
		"local":
			target_alpha = _alpha_local

	for key in _filament_visuals:
		var node: MeshInstance3D = _filament_visuals[key]
		var mat: ShaderMaterial = node.material_override
		if mat:
			mat.set_shader_parameter("alpha_multiplier", target_alpha)


func _on_connection_added(from_id: String, to_id: String) -> void:
	var key := _connection_key(from_id, to_id)
	if key in _filament_visuals:
		_filament_visuals[key].queue_free()
		_filament_visuals.erase(key)

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
	var is_trade := conn_type == "trade"
	var base_width: float = FILAMENT_WIDTH_TRADE if is_trade else FILAMENT_WIDTH_BORDER

	var curve_points := _compute_bezier_arc(from_pos, to_pos)
	var mesh := _build_tube_mesh(curve_points, base_width)

	var mesh_inst := MeshInstance3D.new()
	mesh_inst.set_meta("edge", {"a_id": from_id, "b_id": to_id})
	mesh_inst.mesh = mesh
	var mat := ShaderMaterial.new()
	mat.shader = _filament_shader
	mat.set_shader_parameter("filament_color", color)
	mat.set_shader_parameter("emission_energy", 2.0 if is_trade else 3.0)
	mat.set_shader_parameter("shimmer_speed", 0.3)
	mat.set_shader_parameter("shimmer_strength", 0.4)
	mat.set_shader_parameter("alpha_multiplier", 1.0)
	mat.set_shader_parameter("is_trade", is_trade)
	mesh_inst.material_override = mat
	mesh_inst.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF

	add_child(mesh_inst)
	_filament_visuals[key] = mesh_inst


func _on_connection_removed(from_id: String, to_id: String) -> void:
	var key := _connection_key(from_id, to_id)
	if key in _filament_visuals:
		_filament_visuals[key].queue_free()
		_filament_visuals.erase(key)


func _on_regions_cleared() -> void:
	for node in _filament_visuals.values():
		node.queue_free()
	_filament_visuals.clear()


func _compute_bezier_arc(from_pos: Vector3, to_pos: Vector3) -> PackedVector3Array:
	var mid := (from_pos + to_pos) * 0.5
	var dist := from_pos.distance_to(to_pos)
	var arc_height := dist * ARC_HEIGHT_FRACTION

	var dir := (to_pos - from_pos).normalized()
	var up := Vector3.UP
	if absf(dir.dot(up)) > 0.95:
		up = Vector3.RIGHT
	var perp := dir.cross(up).normalized()

	# prototype legacy_constellation_renderer.gd:149 divides by CIV_SCALE (B23, W3)
	var hash_val := (from_pos.x * 73.0 + from_pos.z * 137.0 + to_pos.x * 97.0 + to_pos.z * 53.0) / GalaxyGen.CIV_SCALE
	var perp_offset := sin(hash_val) * arc_height * 0.5

	var cp1 := from_pos.lerp(mid, 0.5) + Vector3(0, arc_height, 0) + perp * perp_offset
	var cp2 := mid.lerp(to_pos, 0.5) + Vector3(0, arc_height, 0) + perp * perp_offset

	var points := PackedVector3Array()
	for i in range(CURVE_SEGMENTS + 1):
		var t := float(i) / float(CURVE_SEGMENTS)
		points.append(_cubic_bezier(from_pos, cp1, cp2, to_pos, t))
	return points


func _cubic_bezier(p0: Vector3, p1: Vector3, p2: Vector3, p3: Vector3, t: float) -> Vector3:
	var it := 1.0 - t
	return it * it * it * p0 + 3.0 * it * it * t * p1 + 3.0 * it * t * t * p2 + t * t * t * p3


func _build_tube_mesh(curve: PackedVector3Array, radius: float) -> ArrayMesh:
	var mesh := ArrayMesh.new()
	var verts := PackedVector3Array()
	var uvs := PackedVector2Array()
	var indices := PackedInt32Array()

	var total_length := 0.0
	var segment_lengths := PackedFloat32Array()
	segment_lengths.append(0.0)
	for i in range(1, curve.size()):
		var seg_len := curve[i - 1].distance_to(curve[i])
		total_length += seg_len
		segment_lengths.append(total_length)

	if total_length < 0.001 * GalaxyGen.CIV_SCALE:   # prototype :181 (B23, W3)
		return mesh

	for i in range(curve.size()):
		var pos := curve[i]
		var tangent: Vector3
		if i == 0:
			tangent = (curve[1] - curve[0]).normalized()
		elif i == curve.size() - 1:
			tangent = (curve[i] - curve[i - 1]).normalized()
		else:
			tangent = (curve[i + 1] - curve[i - 1]).normalized()

		var up := Vector3.UP
		if absf(tangent.dot(up)) > 0.95:
			up = Vector3.RIGHT
		var right := tangent.cross(up).normalized()
		var actual_up := right.cross(tangent).normalized()

		var u_along := segment_lengths[i] / total_length

		for j in range(TUBE_SIDES + 1):
			var angle := float(j) / float(TUBE_SIDES) * TAU
			var offset := right * cos(angle) * radius + actual_up * sin(angle) * radius
			verts.append(pos + offset)
			uvs.append(Vector2(u_along, float(j) / float(TUBE_SIDES)))

	var ring_count := curve.size()
	var verts_per_ring := TUBE_SIDES + 1
	for i in range(ring_count - 1):
		for j in range(TUBE_SIDES):
			var curr := i * verts_per_ring + j
			var next := curr + verts_per_ring
			indices.append(curr)
			indices.append(next)
			indices.append(curr + 1)
			indices.append(curr + 1)
			indices.append(next)
			indices.append(next + 1)

	var arrays := []
	arrays.resize(Mesh.ARRAY_MAX)
	arrays[Mesh.ARRAY_VERTEX] = verts
	arrays[Mesh.ARRAY_TEX_UV] = uvs
	arrays[Mesh.ARRAY_INDEX] = indices
	mesh.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arrays)
	return mesh


func _connection_key(from_id: String, to_id: String) -> String:
	if from_id < to_id:
		return from_id + "::" + to_id
	return to_id + "::" + from_id
