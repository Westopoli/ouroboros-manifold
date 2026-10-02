extends Node3D

# Territory shells for the galaxy mockup: one full-screen pass over the baked
# field grid (territory_field.gd, shaders/shell_field.gdshader) draws every
# faction's bubble. Replaces legacy_shell_renderer.gd (one raymarched box per
# faction, a loop over every system at every step). Keeps its public surface:
# setup / teardown / get_faction_shell_count; adds get_shell_viewport,
# res_divisor, get_territory_field, set_debug_mode (see tests/gpu_checks.gd).
#
# Faction identity is the territory colour (as before); each colour gets a field
# id (0..15) in order of first appearance, kept until the regions are cleared.
# Under the Compatibility renderer (the software QA render) there is no field:
# one flat translucent billboard per faction stands in, as before.

const INFLUENCE_RADIUS := GalaxyGen.INFLUENCE_RADIUS
const BOX_MARGIN := GalaxyGen.INFLUENCE_RADIUS * 1.15
const SHELL_RES_DIVISOR := 2
# A flat stand-in quad has none of the shader's rim/seam alpha boost (up to 2.5x),
# so its base opacity is raised to stay visible at the same _opacity_* values.
const STAND_IN_OPACITY_MULTIPLIER := 1.8

const TerritoryField := preload("res://scenes/mockups/galaxy/territory_field.gd")

# Quality hook: 1 = full resolution, 2 = shipped default (half), 4 = quarter.
var res_divisor := SHELL_RES_DIVISOR

var _wv_data: Node
var _zoom_controller: Node
var _stand_in := false
var _field: Node
var _sub_viewport: SubViewport
var _sub_camera: Camera3D
var _canvas_layer: CanvasLayer
var _overlay: TextureRect
var _quad_mat: ShaderMaterial
var _bound_field_tex: Texture3D
var _faction_systems: Dictionary = {}     # colour key -> {region_id: {center, radius, color}}
var _faction_labels: Dictionary = {}
var _faction_meshes: Dictionary = {}      # stand-in only
var _faction_field_id: Dictionary = {}    # colour key -> field id
var _field_index: Dictionary = {}         # region_id -> index in the field's system list

var _opacity_overview := 0.50
var _opacity_regional := 0.12
var _opacity_local := 0.05


func setup(data: Node, zoom_controller: Node) -> void:
	_wv_data = data
	_zoom_controller = zoom_controller
	_stand_in = RenderingServer.get_current_rendering_method() == "gl_compatibility"
	if not _stand_in:
		_field = TerritoryField.new()
		_field.name = "TerritoryField"
		add_child(_field)
		_setup_low_res_viewport()
	_wv_data.territory_set.connect(_on_territory_changed)
	_wv_data.territory_updated.connect(_on_territory_changed)
	_wv_data.territory_removed.connect(_on_territory_removed)
	_wv_data.regions_cleared.connect(_on_regions_cleared)


func _setup_low_res_viewport() -> void:
	_sub_viewport = SubViewport.new()
	_sub_viewport.transparent_bg = true
	_sub_viewport.own_world_3d = true
	_sub_viewport.size = _target_size()
	_sub_viewport.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	_sub_viewport.msaa_3d = Viewport.MSAA_DISABLED
	add_child(_sub_viewport)

	_sub_camera = Camera3D.new()
	_sub_camera.current = true
	_sub_viewport.add_child(_sub_camera)

	var quad := MeshInstance3D.new()
	var mesh := QuadMesh.new()
	mesh.size = Vector2(2, 2)
	quad.mesh = mesh
	quad.extra_cull_margin = 16384.0
	quad.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	_quad_mat = ShaderMaterial.new()
	_quad_mat.shader = load("res://scenes/mockups/galaxy/shaders/shell_field.gdshader")
	_quad_mat.set_shader_parameter("gmin", TerritoryField.GRID_MIN)
	_quad_mat.set_shader_parameter("gsize", TerritoryField.GRID_SIZE)
	_quad_mat.set_shader_parameter("grid_n", float(TerritoryField.GRID_CELLS))
	quad.material_override = _quad_mat
	_sub_viewport.add_child(quad)

	_canvas_layer = CanvasLayer.new()
	_canvas_layer.layer = -1
	add_child(_canvas_layer)

	_overlay = TextureRect.new()
	_overlay.texture = _sub_viewport.get_texture()
	_overlay.set_anchors_preset(Control.PRESET_FULL_RECT)
	_overlay.stretch_mode = TextureRect.STRETCH_SCALE
	_overlay.texture_filter = CanvasItem.TEXTURE_FILTER_LINEAR
	_overlay.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var overlay_mat := CanvasItemMaterial.new()
	overlay_mat.blend_mode = CanvasItemMaterial.BLEND_MODE_PREMULT_ALPHA
	_overlay.material = overlay_mat
	_canvas_layer.add_child(_overlay)


func _target_size() -> Vector2i:
	var main_size := get_viewport().get_visible_rect().size
	return Vector2i(maxi(int(main_size.x) / res_divisor, 1), maxi(int(main_size.y) / res_divisor, 1))


func teardown() -> void:
	if _wv_data:
		if _wv_data.territory_set.is_connected(_on_territory_changed):
			_wv_data.territory_set.disconnect(_on_territory_changed)
		if _wv_data.territory_updated.is_connected(_on_territory_changed):
			_wv_data.territory_updated.disconnect(_on_territory_changed)
		if _wv_data.territory_removed.is_connected(_on_territory_removed):
			_wv_data.territory_removed.disconnect(_on_territory_removed)
		if _wv_data.regions_cleared.is_connected(_on_regions_cleared):
			_wv_data.regions_cleared.disconnect(_on_regions_cleared)
	_clear_state()
	for node in [_overlay, _canvas_layer, _sub_viewport, _field]:
		if node:
			node.queue_free()
	_field = null
	_sub_viewport = null
	_sub_camera = null
	_canvas_layer = null
	_overlay = null
	_quad_mat = null
	_bound_field_tex = null
	_wv_data = null
	_zoom_controller = null


func get_faction_shell_count() -> int:
	return _faction_systems.size()


func get_shell_viewport() -> SubViewport:
	return _sub_viewport


func get_territory_field() -> Node:
	return _field


func set_debug_mode(mode: int) -> void:
	if _quad_mat:
		_quad_mat.set_shader_parameter("debug_mode", mode)


func _process(_delta: float) -> void:
	if not _zoom_controller:
		return

	var main_cam := get_viewport().get_camera_3d()
	if main_cam and _sub_camera:
		_sub_camera.global_transform = main_cam.global_transform
		_sub_camera.fov = main_cam.fov
		_sub_camera.near = main_cam.near
		_sub_camera.far = main_cam.far

	if _sub_viewport:
		var target_size := _target_size()
		if _sub_viewport.size != target_size:
			_sub_viewport.size = target_size

	var band: String = _zoom_controller.current_band
	var blend: float = _zoom_controller.blend_factor
	var blend_dir: String = _zoom_controller.blend_direction

	var target_opacity := _opacity_regional
	var label_alpha := 0.0
	match band:
		"overview":
			if blend_dir == "down":
				target_opacity = lerpf(_opacity_overview, _opacity_regional, blend)
				label_alpha = lerpf(1.0, 0.0, blend)
			else:
				target_opacity = _opacity_overview
				label_alpha = 1.0
		"regional":
			if blend_dir == "down":
				target_opacity = lerpf(_opacity_regional, _opacity_local, blend)
			else:
				target_opacity = _opacity_regional
			label_alpha = 0.0
		"local":
			target_opacity = _opacity_local
			label_alpha = 0.0

	if _quad_mat:
		_quad_mat.set_shader_parameter("shell_opacity", target_opacity)
		_bind_field_textures()
	for faction_id in _faction_meshes:
		var mesh: MeshInstance3D = _faction_meshes[faction_id]
		var std_mat := mesh.material_override as StandardMaterial3D
		if std_mat:
			std_mat.albedo_color.a = target_opacity * STAND_IN_OPACITY_MULTIPLIER

	for faction_id in _faction_labels:
		var label: Label3D = _faction_labels[faction_id]
		label.modulate.a = label_alpha


# The field creates its textures on the first fill; bind them once they exist.
func _bind_field_textures() -> void:
	if _field.field_texture == null or _field.field_texture == _bound_field_tex:
		return
	_bound_field_tex = _field.field_texture
	_quad_mat.set_shader_parameter("field", _field.field_texture)
	_quad_mat.set_shader_parameter("id_tex", _field.id_texture)
	var pal: Array = []
	for c in _field.palette:
		pal.append(c)
	_quad_mat.set_shader_parameter("palette", pal)


func _on_territory_changed(region_id: String) -> void:
	var t: Dictionary = _wv_data.get_territory(region_id)
	if t.is_empty():
		return
	var color_key := _color_key(t["color"])

	var previous_key := ""
	for fk in _faction_systems:
		if fk != color_key and region_id in _faction_systems[fk]:
			previous_key = fk
			break
	if previous_key != "":
		_faction_systems[previous_key].erase(region_id)
		if _faction_systems[previous_key].is_empty():
			_remove_faction(previous_key)
		else:
			_update_faction(previous_key)

	if color_key not in _faction_systems:
		_faction_systems[color_key] = {}
	_faction_systems[color_key][region_id] = {"center": t["center"], "radius": t["radius"], "color": t["color"]}
	_update_faction(color_key)
	_feed_field(region_id, color_key, t)


func _on_territory_removed(region_id: String) -> void:
	for fk in _faction_systems:
		if region_id in _faction_systems[fk]:
			_faction_systems[fk].erase(region_id)
			if _faction_systems[fk].is_empty():
				_remove_faction(fk)
			else:
				_update_faction(fk)
			break
	if _field and _field_index.has(region_id):
		_field.set_system_owner(_field_index[region_id], -1)


func _on_regions_cleared() -> void:
	_clear_state()


func _clear_state() -> void:
	for mesh in _faction_meshes.values():
		mesh.queue_free()
	_faction_meshes.clear()
	for label in _faction_labels.values():
		label.queue_free()
	_faction_labels.clear()
	_faction_systems.clear()
	_faction_field_id.clear()
	_field_index.clear()
	if _field:
		_field.set_systems([])


func _feed_field(region_id: String, color_key: String, t: Dictionary) -> void:
	if _field == null:
		return
	if color_key not in _faction_field_id:
		if _faction_field_id.size() >= TerritoryField.MAX_FACTIONS:
			push_warning("shell_renderer: more than %d factions, the extra one gets no shell" % TerritoryField.MAX_FACTIONS)
			return
		_faction_field_id[color_key] = _faction_field_id.size()
		_field.set_palette_color(_faction_field_id[color_key], t["color"])
		_bound_field_tex = null   # rebind to push the palette
	var fid: int = _faction_field_id[color_key]
	if _field_index.has(region_id):
		_field.update_system(_field_index[region_id], t["center"], t["radius"], fid)
	else:
		_field_index[region_id] = _field.add_system(t["center"], t["radius"], fid)


# Label (and, in the stand-in, the billboard) of one faction from its systems.
func _update_faction(faction_id: String) -> void:
	var systems: Dictionary = _faction_systems[faction_id]
	var min_pos := Vector3(INF, INF, INF)
	var max_pos := Vector3(-INF, -INF, -INF)
	var centroid := Vector3.ZERO
	var color := Color.WHITE
	for entry in systems.values():
		var pos: Vector3 = entry["center"]
		min_pos = min_pos.min(pos)
		max_pos = max_pos.max(pos)
		centroid += pos
		color = entry["color"]
	centroid /= float(systems.size())

	if _stand_in:
		var box_min := min_pos - Vector3.ONE * BOX_MARGIN
		var box_max := max_pos + Vector3.ONE * BOX_MARGIN
		var mesh_inst: MeshInstance3D
		if faction_id in _faction_meshes:
			mesh_inst = _faction_meshes[faction_id]
		else:
			mesh_inst = MeshInstance3D.new()
			mesh_inst.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
			mesh_inst.transparency = 0.5
			add_child(mesh_inst)
			_faction_meshes[faction_id] = mesh_inst
		var sphere := SphereMesh.new()
		sphere.radius = 1.0
		sphere.height = 2.0
		sphere.radial_segments = 16
		sphere.rings = 10
		mesh_inst.mesh = sphere
		mesh_inst.position = (box_min + box_max) * 0.5
		mesh_inst.scale = (box_max - box_min) * 0.5
		var std_mat := StandardMaterial3D.new()
		std_mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
		std_mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
		std_mat.blend_mode = BaseMaterial3D.BLEND_MODE_ADD
		std_mat.cull_mode = BaseMaterial3D.CULL_DISABLED
		std_mat.albedo_color = Color(color.r, color.g, color.b, _opacity_regional * STAND_IN_OPACITY_MULTIPLIER)
		std_mat.render_priority = -2
		mesh_inst.material_override = std_mat

	var label: Label3D
	if faction_id in _faction_labels:
		label = _faction_labels[faction_id]
	else:
		label = Label3D.new()
		label.billboard = BaseMaterial3D.BILLBOARD_ENABLED
		label.no_depth_test = true
		label.font_size = 24
		label.pixel_size = 0.01 * GalaxyGen.CIV_SCALE
		label.outline_size = 4
		label.modulate = Color(1, 1, 1, 0)
		add_child(label)
		_faction_labels[faction_id] = label

	var label_text: String = faction_id
	for rid in systems:
		var rdata: Dictionary = _wv_data.get_region(rid)
		if not rdata.is_empty():
			label_text = rdata.get("faction_id", faction_id)
			break
	label.text = label_text.replace("_", " ").capitalize()
	label.position = centroid + Vector3(0, 3.0 * GalaxyGen.CIV_SCALE, 0)
	label.outline_modulate = Color(color.r * 0.3, color.g * 0.3, color.b * 0.3, 1.0)


func _color_key(color: Color) -> String:
	return "%02x%02x%02x" % [int(color.r * 255), int(color.g * 255), int(color.b * 255)]


func _remove_faction(faction_id: String) -> void:
	if faction_id in _faction_meshes:
		_faction_meshes[faction_id].queue_free()
		_faction_meshes.erase(faction_id)
	if faction_id in _faction_labels:
		_faction_labels[faction_id].queue_free()
		_faction_labels.erase(faction_id)
	_faction_systems.erase(faction_id)
