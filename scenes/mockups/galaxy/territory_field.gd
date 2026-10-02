extends Node

# Owns the territory field grid: the highest net field among factions, that
# faction's seam term and its id, for every cell of a 96-cell cube. Input is the
# list of systems (position, significance, owner); output is the field texture
# (RG16F: R = net, G = seam term), the id texture (R8) and the palette. Knows
# nothing about cameras or drawing. Any change marks it dirty; _process refills
# the whole grid once per frame (refill() is also callable, synchronously).
#
# The grid is filled by the graphics card: shaders/field_bake.gdshader runs the
# field maths once per cell into a sheet of z-slices, the sheets are read back
# and cut into the two 3D textures. Under the dummy renderer the sheets read
# back empty and the textures stay zero (the headless verify only needs this
# node not to fail).
# See also: tests/test_field.gd (the contract this implements), tests/field_reference.gd.

const GRID_CELLS := 96
const GRID_SIZE := 2.0 * (GalaxyGen.BALL_RADIUS + GalaxyGen.INFLUENCE_RADIUS)
const GRID_MIN := Vector3(-GRID_SIZE * 0.5, -GRID_SIZE * 0.5, -GRID_SIZE * 0.5)
const MAX_SYSTEMS := 1024
const MAX_FACTIONS := 16
const GAP_STRENGTH := 0.5   # legacy_shell_renderer.gd's gap_strength (the shader default 0.8 was never used)
const SHEET_COLS := 16

var field_texture: ImageTexture3D
var id_texture: ImageTexture3D
var palette := PackedVector3Array()
var fill_count := 0
var last_refill_ms := 0.0

var _pos := PackedVector3Array()
var _sig := PackedFloat32Array()
var _own := PackedInt32Array()
var _dirty := false
var _field_vp: SubViewport
var _id_vp: SubViewport
var _field_mat: ShaderMaterial
var _id_mat: ShaderMaterial
var _tex_a: ImageTexture
var _tex_o: ImageTexture


func _init() -> void:
	palette.resize(MAX_FACTIONS)
	palette.fill(Vector3.ONE)


func _ready() -> void:
	var rows := ceili(float(GRID_CELLS) / float(SHEET_COLS))
	var sheet := Vector2i(SHEET_COLS * GRID_CELLS, rows * GRID_CELLS)
	var shader: Shader = load("res://scenes/mockups/galaxy/shaders/field_bake.gdshader")
	_field_vp = _make_sheet_viewport(sheet, true)
	_id_vp = _make_sheet_viewport(sheet, false)
	_field_mat = _add_sheet_rect(_field_vp, sheet, shader, 0)
	_id_mat = _add_sheet_rect(_id_vp, sheet, shader, 1)


func _make_sheet_viewport(size: Vector2i, hdr: bool) -> SubViewport:
	var vp := SubViewport.new()
	vp.size = size
	vp.disable_3d = true
	vp.use_hdr_2d = hdr
	vp.transparent_bg = true
	vp.msaa_2d = Viewport.MSAA_DISABLED
	vp.render_target_update_mode = SubViewport.UPDATE_DISABLED
	add_child(vp)
	return vp


func _add_sheet_rect(vp: SubViewport, size: Vector2i, shader: Shader, mode: int) -> ShaderMaterial:
	var rect := ColorRect.new()
	rect.size = Vector2(size)
	var mat := ShaderMaterial.new()
	mat.shader = shader
	mat.set_shader_parameter("mode", mode)
	mat.set_shader_parameter("N", GRID_CELLS)
	mat.set_shader_parameter("cols", SHEET_COLS)
	mat.set_shader_parameter("gmin", GRID_MIN)
	mat.set_shader_parameter("cell", GRID_SIZE / float(GRID_CELLS))
	mat.set_shader_parameter("R", GalaxyGen.INFLUENCE_RADIUS)
	mat.set_shader_parameter("gap_strength", GAP_STRENGTH)
	rect.material = mat
	vp.add_child(rect)
	return mat


func set_systems(systems: Array) -> void:
	_pos.clear()
	_sig.clear()
	_own.clear()
	for s in systems:
		_pos.append(s.pos)
		_sig.append(float(s.significance))
		_own.append(int(s.owner))
	_dirty = true


func add_system(pos: Vector3, significance: float, owner: int) -> int:
	_pos.append(pos)
	_sig.append(significance)
	_own.append(owner)
	_dirty = true
	return _pos.size() - 1


func update_system(index: int, pos: Vector3, significance: float, owner: int) -> void:
	if _pos[index] != pos or not is_equal_approx(_sig[index], significance) or _own[index] != owner:
		_pos[index] = pos
		_sig[index] = significance
		_own[index] = owner
		_dirty = true


func set_system_owner(index: int, owner: int) -> void:
	if _own[index] != owner:
		_own[index] = owner
		_dirty = true


func set_palette_color(faction_id: int, color: Color) -> void:
	if faction_id >= 0 and faction_id < MAX_FACTIONS:
		palette[faction_id] = Vector3(color.r, color.g, color.b)


func is_dirty() -> bool:
	return _dirty


func _process(_delta: float) -> void:
	if _dirty:
		refill()


func refill() -> void:
	var t0 := Time.get_ticks_usec()
	_upload_systems()
	for vp in [_field_vp, _id_vp]:
		vp.render_target_update_mode = SubViewport.UPDATE_DISABLED
		vp.render_target_update_mode = SubViewport.UPDATE_ONCE
	RenderingServer.force_draw(false, 0.0)
	var field_sheet := _field_vp.get_texture().get_image()
	var id_sheet := _id_vp.get_texture().get_image()
	var ok: bool = field_sheet != null and not field_sheet.is_empty() and id_sheet != null and not id_sheet.is_empty()
	var field_slices: Array[Image] = []
	var id_slices: Array[Image] = []
	for z in GRID_CELLS:
		var rect := Rect2i((z % SHEET_COLS) * GRID_CELLS, (z / SHEET_COLS) * GRID_CELLS, GRID_CELLS, GRID_CELLS)
		var f: Image
		var i: Image
		if ok:
			f = field_sheet.get_region(rect)
			f.convert(Image.FORMAT_RGH)
			i = id_sheet.get_region(rect)
			i.convert(Image.FORMAT_R8)
		else:
			f = Image.create(GRID_CELLS, GRID_CELLS, false, Image.FORMAT_RGH)
			i = Image.create(GRID_CELLS, GRID_CELLS, false, Image.FORMAT_R8)
		field_slices.append(f)
		id_slices.append(i)
	if field_texture == null:
		field_texture = ImageTexture3D.new()
		field_texture.create(Image.FORMAT_RGH, GRID_CELLS, GRID_CELLS, GRID_CELLS, false, field_slices)
		id_texture = ImageTexture3D.new()
		id_texture.create(Image.FORMAT_R8, GRID_CELLS, GRID_CELLS, GRID_CELLS, false, id_slices)
	else:
		field_texture.update(field_slices)
		id_texture.update(id_slices)
	_dirty = false
	fill_count += 1
	last_refill_ms = (Time.get_ticks_usec() - t0) / 1000.0


func _upload_systems() -> void:
	var n := mini(_pos.size(), MAX_SYSTEMS)
	var img_a := Image.create(MAX_SYSTEMS, 1, false, Image.FORMAT_RGBAF)
	var img_o := Image.create(MAX_SYSTEMS, 1, false, Image.FORMAT_RF)
	var max_sig := PackedFloat32Array()
	max_sig.resize(MAX_FACTIONS)
	var n_fac := 0
	var used := 0
	for i in n:
		if _own[i] < 0 or _own[i] >= MAX_FACTIONS:
			continue
		var p := _pos[i]
		img_a.set_pixel(used, 0, Color(p.x, p.y, p.z, _sig[i]))
		img_o.set_pixel(used, 0, Color(float(_own[i]), 0.0, 0.0, 1.0))
		max_sig[_own[i]] = maxf(max_sig[_own[i]], _sig[i])
		n_fac = maxi(n_fac, _own[i] + 1)
		used += 1
	if _tex_a == null:
		_tex_a = ImageTexture.create_from_image(img_a)
		_tex_o = ImageTexture.create_from_image(img_o)
	else:
		_tex_a.update(img_a)
		_tex_o.update(img_o)
	for mat in [_field_mat, _id_mat]:
		mat.set_shader_parameter("sys_a", _tex_a)
		mat.set_shader_parameter("sys_o", _tex_o)
		mat.set_shader_parameter("n_sys", used)
		mat.set_shader_parameter("n_fac", n_fac)
		mat.set_shader_parameter("max_sig", max_sig)
