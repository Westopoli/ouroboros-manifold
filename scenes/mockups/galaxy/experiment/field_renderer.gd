extends Node3D
# Throwaway experiment: one SubViewport + full-screen quad marching the baked field.
# Composited like legacy_shell_renderer.gd (CanvasLayer -1, premult overlay).

const TMPL := "res://scenes/mockups/galaxy/experiment/field_march.tmpl"

var sub_viewport: SubViewport
var _cam: Camera3D
var _quad: MeshInstance3D
var overlay: TextureRect
var _layer: CanvasLayer
var _mat: ShaderMaterial
var _zoom: Node
var divisor := 2
var _tmpl := ""
var _quads: Array[MeshInstance3D] = []
var reps := 1

func setup(zoom_controller: Node) -> void:
	_zoom = zoom_controller
	_tmpl = FileAccess.get_file_as_string(TMPL)
	sub_viewport = SubViewport.new()
	sub_viewport.transparent_bg = true
	sub_viewport.own_world_3d = true
	sub_viewport.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	sub_viewport.msaa_3d = Viewport.MSAA_DISABLED
	add_child(sub_viewport)
	_cam = Camera3D.new()
	_cam.current = true
	sub_viewport.add_child(_cam)
	var q := QuadMesh.new()
	q.size = Vector2(2, 2)
	_quad = MeshInstance3D.new()
	_quad.mesh = q
	_quad.extra_cull_margin = 16384.0
	_quad.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	_mat = ShaderMaterial.new()
	_quad.material_override = _mat
	sub_viewport.add_child(_quad)
	_quads.append(_quad)
	_layer = CanvasLayer.new()
	_layer.layer = -1
	add_child(_layer)
	overlay = TextureRect.new()
	overlay.texture = sub_viewport.get_texture()
	overlay.set_anchors_preset(Control.PRESET_FULL_RECT)
	overlay.stretch_mode = TextureRect.STRETCH_SCALE
	overlay.texture_filter = CanvasItem.TEXTURE_FILTER_LINEAR
	overlay.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var om := CanvasItemMaterial.new()
	om.blend_mode = CanvasItemMaterial.BLEND_MODE_PREMULT_ALPHA
	overlay.material = om
	_layer.add_child(overlay)
	RenderingServer.viewport_set_measure_render_time(sub_viewport.get_viewport_rid(), true)

func set_enabled(on: bool) -> void:
	overlay.visible = on
	sub_viewport.render_target_update_mode = SubViewport.UPDATE_ALWAYS if on else SubViewport.UPDATE_DISABLED

# v: steps, cross, skip(bool), refine(int), divisor
func apply_variant(v: Dictionary) -> void:
	var code := _tmpl.replace("%STEPS%", str(int(v.get("steps", 64)))) \
		.replace("%CROSS%", str(int(v.get("cross", 4)))) \
		.replace("%SKIP%", "true" if v.get("skip", true) else "false") \
		.replace("%REFINE%", str(int(v.get("refine", 2))))
	var sh := Shader.new()
	sh.code = code
	_mat.shader = sh
	divisor = int(v.get("divisor", 2))
	var main_size := get_viewport().get_visible_rect().size
	sub_viewport.size = Vector2i(maxi(int(main_size.x) / divisor, 1), maxi(int(main_size.y) / divisor, 1))
	_params_dirty = true
	# timing amplification: reps identical full-screen passes per frame keep the GPU
	# saturated (clocks up); the probe divides the viewport time by reps.
	reps = int(v.get("reps", 1))
	while _quads.size() < reps:
		var q2 := MeshInstance3D.new()
		q2.mesh = _quad.mesh
		q2.extra_cull_margin = 16384.0
		q2.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		q2.material_override = _mat
		sub_viewport.add_child(q2)
		_quads.append(q2)
	for i in _quads.size():
		_quads[i].visible = i < reps

var _params_dirty := true
var _volume: Texture3D
var _skip: Texture3D
var _gmin := Vector3.ZERO
var _gsize := 1.0
var _n := 96

func set_volume(vol: Texture3D, skip: Texture3D, gmin: Vector3, gsize: float, n: int, palette: PackedVector3Array) -> void:
	_mat.set_shader_parameter("field", vol)
	_mat.set_shader_parameter("skip_tex", skip)
	_mat.set_shader_parameter("gmin", gmin)
	_mat.set_shader_parameter("gsize", gsize)
	_mat.set_shader_parameter("grid_n", float(n))
	var pal: Array = []
	for i in 16:
		pal.append(palette[i] if i < palette.size() else Vector3.ONE)
	_mat.set_shader_parameter("palette", pal)

func set_reps(n: int) -> void:
	reps = n
	for i in _quads.size():
		_quads[i].visible = i < reps

func _process(_d: float) -> void:
	var main_cam := get_viewport().get_camera_3d()
	if main_cam and _cam:
		_cam.global_transform = main_cam.global_transform
		_cam.fov = main_cam.fov
		_cam.near = main_cam.near
		_cam.far = main_cam.far
	if _zoom == null:
		return
	var band: String = _zoom.current_band
	var blend: float = _zoom.blend_factor
	var bd: String = _zoom.blend_direction
	var o_over := 0.50
	var o_reg := 0.12
	var o_loc := 0.05
	var target := o_reg
	match band:
		"overview":
			target = lerpf(o_over, o_reg, blend) if bd == "down" else o_over
		"regional":
			target = lerpf(o_reg, o_loc, blend) if bd == "down" else o_reg
		"local":
			target = o_loc
	_mat.set_shader_parameter("shell_opacity", target)
