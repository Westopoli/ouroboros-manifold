extends Node

# Owns the territory field grid: the highest net field among factions, that
# faction's seam term and its id, for every cell of a 96-cell cube. Input is the
# galaxy world view's territories (centre, radius = significance, colour; the
# colour is the faction identity); output is the field texture
# (RG16F: R = net, G = seam term), the id texture (R8) and the palette. Knows
# nothing about cameras or drawing. Any change marks it dirty; _process refills
# the whole grid once per frame (refill() is also callable, synchronously).
#
# The grid is filled by the graphics card: shaders/field_bake.gdshader runs the
# field maths once per cell into a sheet of z-slices (a second tiny pass copies
# the id channel into an 8-bit sheet), the sheets are read back and cut into the
# two 3D textures. Under the dummy renderer the sheets read
# back empty and the textures stay zero (the headless verify only needs this
# node not to fail).
# Ported from the mockup scenes/mockups/galaxy/territory_field.gd (origin/push/galaxy-field).
# See also: tests/test_vg_b_b1.gd (the contract this implements).

const GRID_CELLS := 96
# The cube holds the layout ball plus one influence radius on each side: 2 * (R_BALL + INFLUENCE_RADIUS),
# the prototype's rule (territory_field.gd:19-20 on origin/push/galaxy-field); 2 * (50 + 14) = 128.
# INFLUENCE_RADIUS 14 is the prototype's galaxy_gen.gd:17 value, 28 x CIV_SCALE 0.5 (B23, spec rev 12b).
# GRID_CELLS stays the texture size, so a cell is 1.33 wu. R_BALL lives in galaxy_gen.gd; the values here are written out.
const GRID_SIZE := 128.0
const INFLUENCE_RADIUS := 14.0
const GRID_MIN := Vector3(-64.0, -64.0, -64.0)
const MAX_SYSTEMS := 1024
const MAX_FACTIONS := 16
const GAP_STRENGTH := 0.5   # legacy_shell_renderer.gd's gap_strength (the shader default 0.8 was never used)

var field_texture: ImageTexture3D
var id_texture: ImageTexture3D
var palette := PackedVector3Array()
var fill_count := 0
var last_refill_ms := 0.0

var _pos := PackedVector3Array()
var _sig := PackedFloat32Array()
var _own := PackedInt32Array()
var _dirty := false
var _wv: Node
var _faction_of := {}
var _color_ids := {}
var _field_vp: SubViewport
var _id_vp: SubViewport
var _field_mat: ShaderMaterial
var _id_mat: ShaderMaterial
var _tex_a: ImageTexture
var _tex_o: ImageTexture
var _tex_ranges: ImageTexture


func _init() -> void:
	palette.resize(MAX_FACTIONS)
	palette.fill(Vector3.ONE)


func _ready() -> void:
	var sheet := Vector2i(GRID_CELLS, GRID_CELLS * GRID_CELLS)
	var shader: Shader = load("res://scenes/galaxy/shaders/field_bake.gdshader")
	_field_vp = _make_sheet_viewport(sheet, true)
	_id_vp = _make_sheet_viewport(sheet, false)
	_field_mat = _add_sheet_rect(_field_vp, sheet, shader, 0)
	_id_mat = _add_sheet_rect(_id_vp, sheet, shader, 1)
	_id_mat.set_shader_parameter("field_sheet", _field_vp.get_texture())


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
	mat.set_shader_parameter("gmin", GRID_MIN)
	mat.set_shader_parameter("cell", GRID_SIZE / float(GRID_CELLS))
	mat.set_shader_parameter("R", INFLUENCE_RADIUS)
	mat.set_shader_parameter("gap_strength", GAP_STRENGTH)
	rect.material = mat
	vp.add_child(rect)
	return mat


func bind_world_view(wv: Node) -> void:
	_wv = wv
	_faction_of.clear()
	_color_ids.clear()
	palette.fill(Vector3.ONE)
	for id in wv.territories:
		_assign(id)
	wv.territory_set.connect(_on_territory_changed)
	wv.territory_updated.connect(_on_territory_changed)
	wv.territory_removed.connect(_on_territory_removed)
	_dirty = true


func faction_id_of(region_id: String) -> int:
	return _faction_of.get(region_id, -1)


func _assign(region_id: String) -> void:
	var c: Color = _wv.territories[region_id]["color"]
	var key := Vector3(c.r, c.g, c.b)
	if not _color_ids.has(key):
		var id := _color_ids.size()
		if id >= MAX_FACTIONS:
			_faction_of.erase(region_id)
			return
		_color_ids[key] = id
		palette[id] = key
	_faction_of[region_id] = _color_ids[key]


func _on_territory_changed(region_id: String) -> void:
	if _wv.territories.has(region_id):
		_assign(region_id)
	_dirty = true


func _on_territory_removed(region_id: String) -> void:
	_faction_of.erase(region_id)
	_dirty = true


func is_dirty() -> bool:
	return _dirty


func _process(_delta: float) -> void:
	if _dirty and _wv != null:
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
	var field_bytes := PackedByteArray()
	var id_bytes := PackedByteArray()
	if ok:
		field_sheet.convert(Image.FORMAT_RGH)
		id_sheet.convert(Image.FORMAT_R8)
		field_bytes = field_sheet.get_data()
		id_bytes = id_sheet.get_data()
	var field_stride := GRID_CELLS * GRID_CELLS * 4
	var id_stride := GRID_CELLS * GRID_CELLS
	for z in GRID_CELLS:
		if ok:
			field_slices.append(Image.create_from_data(GRID_CELLS, GRID_CELLS, false, Image.FORMAT_RGH, field_bytes.slice(z * field_stride, (z + 1) * field_stride)))
			id_slices.append(Image.create_from_data(GRID_CELLS, GRID_CELLS, false, Image.FORMAT_R8, id_bytes.slice(z * id_stride, (z + 1) * id_stride)))
		else:
			field_slices.append(Image.create(GRID_CELLS, GRID_CELLS, false, Image.FORMAT_RGH))
			id_slices.append(Image.create(GRID_CELLS, GRID_CELLS, false, Image.FORMAT_R8))
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
	# Owned systems, bucketed by z (counting sort), so a slice scans only the slab of
	# systems that can reach it.
	var cell := GRID_SIZE / float(GRID_CELLS)
	var reach := INFLUENCE_RADIUS
	_pos.clear()
	_sig.clear()
	_own.clear()
	for id in _wv.territories:
		if _faction_of.has(id) and _pos.size() < MAX_SYSTEMS:
			var t: Dictionary = _wv.territories[id]
			_pos.append(t["center"])
			_sig.append(float(t["radius"]))
			_own.append(_faction_of[id])
	var n := _pos.size()
	var bucket := PackedInt32Array()
	bucket.resize(n)
	var start := PackedInt32Array()
	start.resize(GRID_CELLS + 2)
	var max_sig := PackedFloat32Array()
	max_sig.resize(MAX_FACTIONS)
	var n_fac := 0
	var used := 0
	for i in n:
		if _own[i] < 0 or _own[i] >= MAX_FACTIONS:
			bucket[i] = -1
			continue
		bucket[i] = clampi(int((_pos[i].z - GRID_MIN.z) / cell), 0, GRID_CELLS - 1)
		start[bucket[i] + 1] += 1
		max_sig[_own[i]] = maxf(max_sig[_own[i]], _sig[i])
		n_fac = maxi(n_fac, _own[i] + 1)
		used += 1
	for b in GRID_CELLS + 1:
		start[b + 1] += start[b]
	var fill := start.duplicate()
	var img_a := Image.create(MAX_SYSTEMS, 1, false, Image.FORMAT_RGBAF)
	var img_o := Image.create(MAX_SYSTEMS, 1, false, Image.FORMAT_RF)
	for i in n:
		if bucket[i] < 0:
			continue
		var slot := fill[bucket[i]]
		fill[bucket[i]] += 1
		var p := _pos[i]
		img_a.set_pixel(slot, 0, Color(p.x, p.y, p.z, _sig[i]))
		img_o.set_pixel(slot, 0, Color(float(_own[i]), 0.0, 0.0, 1.0))
	var img_r := Image.create(GRID_CELLS, 1, false, Image.FORMAT_RGF)
	for k in GRID_CELLS:
		var zc := GRID_MIN.z + (k + 0.5) * cell
		var b_lo := clampi(int((zc - reach - GRID_MIN.z) / cell), 0, GRID_CELLS - 1)
		var b_hi := clampi(int((zc + reach - GRID_MIN.z) / cell), 0, GRID_CELLS - 1)
		img_r.set_pixel(k, 0, Color(float(start[b_lo]), float(start[b_hi + 1]), 0.0, 1.0))
	if _tex_a == null:
		_tex_a = ImageTexture.create_from_image(img_a)
		_tex_o = ImageTexture.create_from_image(img_o)
		_tex_ranges = ImageTexture.create_from_image(img_r)
	else:
		_tex_a.update(img_a)
		_tex_o.update(img_o)
		_tex_ranges.update(img_r)
	_field_mat.set_shader_parameter("sys_a", _tex_a)
	_field_mat.set_shader_parameter("sys_o", _tex_o)
	_field_mat.set_shader_parameter("ranges", _tex_ranges)
	_field_mat.set_shader_parameter("n_fac", n_fac)
	_field_mat.set_shader_parameter("max_sig", max_sig)
