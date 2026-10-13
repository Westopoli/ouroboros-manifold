extends Node3D

# Territory shells: one full-screen quad in a half-resolution SubViewport draws every faction's
# bubble from the baked field (territory_field.gd, shaders/shell_field.gdshader; pieces B1/B2),
# shown through one premultiplied-alpha overlay. R-106-03: opacity by zoom band.
# See also: scenes/galaxy/legacy_shell_renderer.gd (superseded one box per faction).
# The field script and shader load by path at setup; until B1/B2 land the quad carries an empty
# ShaderMaterial and the shell is structure only.

const FIELD_PATH := "res://scenes/galaxy/territory_field.gd"
const SHADER_PATH := "res://scenes/galaxy/shaders/shell_field.gdshader"
const SHELL_RES_DIVISOR := 2
const UnknownLabel := preload("res://scenes/galaxy/unknown_label.gd")
const ShellLabels := preload("res://scenes/galaxy/shell_labels.gd")

# Quality hook: 1 = full resolution, 2 = shipped default (half), 4 = quarter.
var res_divisor := SHELL_RES_DIVISOR
# Set by galaxy_quality.gd (A54): 1 forces stand-in shells (tiers 1 and 2). -1 (tier 0, or unset) follows the rendering method.
var stand_in_mode := -1
var known_faction_ids: Array = []

var _wv_data: Node
var _labels: RefCounted   # faction labels, and the flat stand-in under the Compatibility renderer
var _zoom_controller: Node
var _field: Node
var _field_script: Script
var _sub_viewport: SubViewport
var _sub_camera: Camera3D
var _canvas_layer: CanvasLayer
var _overlay: TextureRect
var _quad_mat: ShaderMaterial
var _bound_field_tex: Texture3D
var _faction_systems: Dictionary = {}     # colour key -> {region_id: true}

var _opacity_overview := 0.50
var _opacity_regional := 0.12
var _opacity_local := 0.05


func setup(data: Node, zoom_controller: Node) -> void:
	_wv_data = data
	_zoom_controller = zoom_controller
	var use_stand_in := RenderingServer.get_current_rendering_method() == "gl_compatibility" if stand_in_mode < 0 else stand_in_mode == 1
	_labels = ShellLabels.new(self, use_stand_in)
	if not _labels.stand_in:
		if ResourceLoader.exists(FIELD_PATH):
			_field_script = load(FIELD_PATH)
			_field = _field_script.new()
			_field.name = "TerritoryField"
			add_child(_field)
			_field.bind_world_view(_wv_data)
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
	_follow_main_camera()

	var quad := MeshInstance3D.new()
	var mesh := QuadMesh.new()
	mesh.size = Vector2(2, 2)
	quad.mesh = mesh
	quad.extra_cull_margin = 16384.0
	quad.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	_quad_mat = ShaderMaterial.new()
	if ResourceLoader.exists(SHADER_PATH):
		_quad_mat.shader = load(SHADER_PATH)
	if _field_script:
		var k: Dictionary = _field_script.get_script_constant_map()
		_quad_mat.set_shader_parameter("gmin", k["GRID_MIN"])
		_quad_mat.set_shader_parameter("gsize", k["GRID_SIZE"])
		_quad_mat.set_shader_parameter("grid_n", float(k["GRID_CELLS"]))
	_quad_mat.set_shader_parameter("shell_opacity", _opacity_regional)
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
	if not is_inside_tree():
		return Vector2i.ONE
	var main_size := get_viewport().get_visible_rect().size
	return Vector2i(maxi(int(main_size.x) / res_divisor, 1), maxi(int(main_size.y) / res_divisor, 1))


func _follow_main_camera() -> void:
	if not is_inside_tree():
		return
	var main_cam := get_viewport().get_camera_3d()
	if main_cam and _sub_camera:
		_sub_camera.global_transform = main_cam.global_transform
		_sub_camera.fov = main_cam.fov
		_sub_camera.near = main_cam.near
		_sub_camera.far = main_cam.far


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
	_labels = null
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
	if _sub_viewport:
		_follow_main_camera()
		var target_size := _target_size()
		if _sub_viewport.size != target_size:
			_sub_viewport.size = target_size

	var band: String = _zoom_controller.current_band
	var blend: float = _zoom_controller.blend_factor
	var blend_dir: String = _zoom_controller.blend_direction
	var target_opacity := _opacity_regional
	match band:
		"overview":
			if blend_dir == "down":
				target_opacity = lerpf(_opacity_overview, _opacity_regional, blend)
			else:
				target_opacity = _opacity_overview
		"regional":
			if blend_dir == "down":
				target_opacity = lerpf(_opacity_regional, _opacity_local, blend)
		"local":
			target_opacity = _opacity_local
	var label_alpha := 0.0
	if band == "overview":
		label_alpha = 1.0 - blend if blend_dir == "down" else 1.0
	_labels.apply(target_opacity, label_alpha)
	if _quad_mat:
		_quad_mat.set_shader_parameter("shell_opacity", target_opacity)
	if _field:
		_bind_field_textures()


# The field creates its textures on the first fill; bind them once they exist.
func _bind_field_textures() -> void:
	if _field.field_texture == null:
		return
	if _field.field_texture != _bound_field_tex:
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
	for fk in _faction_systems.keys():
		if fk != color_key and region_id in _faction_systems[fk]:
			_faction_systems[fk].erase(region_id)
			if _faction_systems[fk].is_empty():
				_faction_systems.erase(fk)
			break
	if color_key not in _faction_systems:
		_faction_systems[color_key] = {}
	_faction_systems[color_key][region_id] = true
	_refresh_labels()


func _on_territory_removed(region_id: String) -> void:
	for fk in _faction_systems.keys():
		if region_id in _faction_systems[fk]:
			_faction_systems[fk].erase(region_id)
			if _faction_systems[fk].is_empty():
				_faction_systems.erase(fk)
			break
	_refresh_labels()


func _refresh_labels() -> void:
	_labels.refresh(_faction_systems, _wv_data, known_faction_ids)


func _on_regions_cleared() -> void:
	_clear_state()


func _clear_state() -> void:
	_faction_systems.clear()
	if _labels:
		_labels.clear()


func _color_key(color: Color) -> String:
	return "%02x%02x%02x" % [int(color.r * 255), int(color.g * 255), int(color.b * 255)]
