extends Node3D

const INFLUENCE_RADIUS := 5.0
const BOX_MARGIN := 8.0
const ISO_THRESHOLD := 0.6
const SHELL_RES_DIVISOR := 2

var _wv_data: Node
var _zoom_controller: Node
var _shell_shader: Shader
var _faction_meshes: Dictionary = {}
var _faction_systems: Dictionary = {}
var _faction_labels: Dictionary = {}

var _sub_viewport: SubViewport
var _sub_camera: Camera3D
var _shell_container: Node3D
var _canvas_layer: CanvasLayer
var _overlay: TextureRect

var _opacity_overview := 0.50
var _opacity_regional := 0.12
var _opacity_local := 0.05

var _diag_timer := 0.0


func setup(data: Node, zoom_controller: Node) -> void:
	_wv_data = data
	_zoom_controller = zoom_controller
	_shell_shader = load("res://scenes/shared/world_view/renderers/shell_metaball.gdshader")
	_wv_data.territory_set.connect(_on_territory_changed)
	_wv_data.territory_updated.connect(_on_territory_changed)
	_wv_data.territory_removed.connect(_on_territory_removed)
	_wv_data.regions_cleared.connect(_on_regions_cleared)
	_setup_low_res_viewport()


func _setup_low_res_viewport() -> void:
	_sub_viewport = SubViewport.new()
	_sub_viewport.transparent_bg = true
	_sub_viewport.own_world_3d = true
	var main_size := get_viewport().get_visible_rect().size
	_sub_viewport.size = Vector2i(int(main_size.x) / SHELL_RES_DIVISOR, int(main_size.y) / SHELL_RES_DIVISOR)
	_sub_viewport.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	_sub_viewport.msaa_3d = Viewport.MSAA_DISABLED
	add_child(_sub_viewport)

	_sub_camera = Camera3D.new()
	_sub_camera.current = true
	_sub_camera.fov = 50.0
	_sub_viewport.add_child(_sub_camera)

	_shell_container = Node3D.new()
	_sub_viewport.add_child(_shell_container)

	_canvas_layer = CanvasLayer.new()
	_canvas_layer.layer = -1
	add_child(_canvas_layer)

	_overlay = TextureRect.new()
	_overlay.texture = _sub_viewport.get_texture()
	_overlay.set_anchors_preset(Control.PRESET_FULL_RECT)
	_overlay.stretch_mode = TextureRect.STRETCH_SCALE
	_overlay.texture_filter = CanvasItem.TEXTURE_FILTER_LINEAR
	_overlay.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_canvas_layer.add_child(_overlay)


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
	for mesh in _faction_meshes.values():
		mesh.queue_free()
	_faction_meshes.clear()
	for label in _faction_labels.values():
		label.queue_free()
	_faction_labels.clear()
	_faction_systems.clear()
	if _overlay:
		_overlay.queue_free()
	if _canvas_layer:
		_canvas_layer.queue_free()
	if _sub_viewport:
		_sub_viewport.queue_free()
	_sub_viewport = null
	_sub_camera = null
	_shell_container = null
	_canvas_layer = null
	_overlay = null
	_wv_data = null
	_zoom_controller = null


func _process(delta: float) -> void:
	if not _zoom_controller:
		return

	# Sync SubViewport camera with main camera
	var main_cam := get_viewport().get_camera_3d()
	if main_cam and _sub_camera:
		_sub_camera.global_transform = main_cam.global_transform
		_sub_camera.fov = main_cam.fov
		_sub_camera.near = main_cam.near
		_sub_camera.far = main_cam.far

	# Resize SubViewport if window changed
	if _sub_viewport:
		var main_size := get_viewport().get_visible_rect().size
		var target_size := Vector2i(maxi(int(main_size.x) / SHELL_RES_DIVISOR, 1), maxi(int(main_size.y) / SHELL_RES_DIVISOR, 1))
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

	for faction_id in _faction_meshes:
		var mesh: MeshInstance3D = _faction_meshes[faction_id]
		var mat: ShaderMaterial = mesh.material_override
		if mat:
			mat.set_shader_parameter("shell_opacity", target_opacity)

	for faction_id in _faction_labels:
		var label: Label3D = _faction_labels[faction_id]
		label.modulate.a = label_alpha

	_diag_timer += delta
	if _diag_timer >= 2.0:
		_diag_timer = 0.0
		var diag_cam := get_viewport().get_camera_3d()
		var cam_match := "no_main_cam"
		if diag_cam and _sub_camera:
			var pos_diff := diag_cam.global_position.distance_to(_sub_camera.global_position)
			cam_match = "pos_diff=%.3f fov=%.1f/%.1f" % [pos_diff, diag_cam.fov, _sub_camera.fov]
		var sv_size := _sub_viewport.size if _sub_viewport else Vector2i.ZERO
		var main_size := get_viewport().get_visible_rect().size
		var overlay_size := _overlay.size if _overlay else Vector2.ZERO
		var overlay_vis := _overlay.visible if _overlay else false
		var shell_children := _shell_container.get_child_count() if _shell_container else 0
		print("[SHELL_DIAG] band=%s opacity=%.3f cam=%s sv_size=%s main_size=%s overlay_size=%s overlay_vis=%s shell_children=%d canvas_layer=%d" % [
			band, target_opacity, cam_match, sv_size, main_size, overlay_size, overlay_vis, shell_children, _canvas_layer.layer if _canvas_layer else -99])


func _on_territory_changed(region_id: String) -> void:
	var t: Dictionary = _wv_data.get_territory(region_id)
	if t.is_empty():
		return
	var color_key := _color_key(t["color"])

	var changed_faction := false
	for fk in _faction_systems:
		if fk != color_key and region_id in _faction_systems[fk]:
			_faction_systems[fk].erase(region_id)
			if _faction_systems[fk].is_empty():
				_remove_faction_shell(fk)
			changed_faction = true
			break

	if color_key not in _faction_systems:
		_faction_systems[color_key] = {}
	_faction_systems[color_key][region_id] = {
		"center": t["center"],
		"radius": t["radius"],
		"color": t["color"],
	}

	if changed_faction:
		_rebuild_all_shells()
	else:
		_rebuild_faction_shell(color_key)


func _on_territory_removed(region_id: String) -> void:
	for fk in _faction_systems:
		if region_id in _faction_systems[fk]:
			_faction_systems[fk].erase(region_id)
			if _faction_systems[fk].is_empty():
				_remove_faction_shell(fk)
			else:
				_rebuild_faction_shell(fk)
			return


func _on_regions_cleared() -> void:
	for mesh in _faction_meshes.values():
		mesh.queue_free()
	_faction_meshes.clear()
	for label in _faction_labels.values():
		label.queue_free()
	_faction_labels.clear()
	_faction_systems.clear()


func _rebuild_faction_shell(faction_id: String) -> void:
	var systems: Dictionary = _faction_systems[faction_id]
	if systems.is_empty():
		_remove_faction_shell(faction_id)
		return
	var min_pos := Vector3(INF, INF, INF)
	var max_pos := Vector3(-INF, -INF, -INF)
	var centroid := Vector3.ZERO
	var color := Color.WHITE
	var max_sig := 0.0

	for entry in systems.values():
		var pos: Vector3 = entry["center"]
		min_pos.x = minf(min_pos.x, pos.x)
		min_pos.y = minf(min_pos.y, pos.y)
		min_pos.z = minf(min_pos.z, pos.z)
		max_pos.x = maxf(max_pos.x, pos.x)
		max_pos.y = maxf(max_pos.y, pos.y)
		max_pos.z = maxf(max_pos.z, pos.z)
		centroid += pos
		color = entry["color"]
		max_sig = maxf(max_sig, entry["radius"])

	centroid /= float(systems.size())

	min_pos -= Vector3.ONE * BOX_MARGIN
	max_pos += Vector3.ONE * BOX_MARGIN
	var box_center := (min_pos + max_pos) * 0.5
	var box_size := max_pos - min_pos

	var img := Image.create(64, 1, false, Image.FORMAT_RGBAF)
	var idx := 0
	for entry in systems.values():
		if idx >= 64:
			break
		var pos: Vector3 = entry["center"]
		var sig := clampf(entry["radius"] / maxf(max_sig, 0.01), 0.0, 1.0)
		img.set_pixel(idx, 0, Color(pos.x, pos.y, pos.z, sig))
		idx += 1
	var tex := ImageTexture.create_from_image(img)

	var rival_img := Image.create(256, 1, false, Image.FORMAT_RGBAF)
	var rival_idx := 0
	for other_fk in _faction_systems:
		if other_fk == faction_id:
			continue
		for rival_entry in _faction_systems[other_fk].values():
			if rival_idx >= 256:
				break
			var rpos: Vector3 = rival_entry["center"]
			var rsig := clampf(rival_entry["radius"] / maxf(max_sig, 0.01), 0.0, 1.0)
			rival_img.set_pixel(rival_idx, 0, Color(rpos.x, rpos.y, rpos.z, rsig))
			rival_idx += 1
		if rival_idx >= 256:
			break
	var rival_tex := ImageTexture.create_from_image(rival_img)

	var mesh_inst: MeshInstance3D
	if faction_id in _faction_meshes:
		mesh_inst = _faction_meshes[faction_id]
	else:
		mesh_inst = MeshInstance3D.new()
		mesh_inst.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		mesh_inst.transparency = 0.5
		_shell_container.add_child(mesh_inst)
		_faction_meshes[faction_id] = mesh_inst

	var box := BoxMesh.new()
	box.size = box_size
	mesh_inst.mesh = box
	mesh_inst.position = box_center

	var mat := ShaderMaterial.new()
	mat.shader = _shell_shader
	mat.set_shader_parameter("system_positions", tex)
	mat.set_shader_parameter("system_count", idx)
	mat.set_shader_parameter("rival_positions", rival_tex)
	mat.set_shader_parameter("rival_count", rival_idx)
	mat.set_shader_parameter("shell_color", Vector3(color.r, color.g, color.b))
	mat.set_shader_parameter("influence_radius", INFLUENCE_RADIUS)
	mat.set_shader_parameter("iso_threshold", ISO_THRESHOLD)
	mat.set_shader_parameter("shell_opacity", _opacity_regional)
	mat.set_shader_parameter("gap_strength", 0.5)
	mat.set_shader_parameter("box_min_world", min_pos)
	mat.set_shader_parameter("box_max_world", max_pos)
	mat.render_priority = -2
	mesh_inst.material_override = mat

	# Faction label — stays in main scene at full resolution
	var label: Label3D
	if faction_id in _faction_labels:
		label = _faction_labels[faction_id]
	else:
		label = Label3D.new()
		label.billboard = BaseMaterial3D.BILLBOARD_ENABLED
		label.no_depth_test = true
		label.font_size = 24
		label.outline_size = 4
		label.modulate = Color(1, 1, 1, 0)
		add_child(label)
		_faction_labels[faction_id] = label

	var label_text := faction_id
	for rid in systems:
		var rdata: Dictionary = _wv_data.get_region(rid)
		if not rdata.is_empty():
			label_text = rdata.get("faction_id", faction_id)
			break
	label.text = label_text.replace("_", " ").capitalize()
	label.position = centroid + Vector3(0, 3.0, 0)
	label.outline_modulate = Color(color.r * 0.3, color.g * 0.3, color.b * 0.3, 1.0)


func _rebuild_all_shells() -> void:
	for fk in _faction_systems:
		if not _faction_systems[fk].is_empty():
			_rebuild_faction_shell(fk)


func _color_key(color: Color) -> String:
	return "%02x%02x%02x" % [int(color.r * 255), int(color.g * 255), int(color.b * 255)]


func _remove_faction_shell(faction_id: String) -> void:
	if faction_id in _faction_meshes:
		_faction_meshes[faction_id].queue_free()
		_faction_meshes.erase(faction_id)
	if faction_id in _faction_labels:
		_faction_labels[faction_id].queue_free()
		_faction_labels.erase(faction_id)
	_faction_systems.erase(faction_id)
