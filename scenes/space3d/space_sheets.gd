class_name SpaceSheets
extends Node3D

# VG-D-VIEW unit 1 (docs/northstar/plans/2026-10-13-d-view-spec.md "Field", "Vision tube"): the five stacked sheets of a space mission, drawn from
# the field the sim sends (SimSession.bridge().space_field(): masks and plate polys). Engine layer L (0-based) sits at y = L * LAYER_GAP_WU. The
# slab shape is scenes/mockups/landscape/placer.gd _add_slab :424-443 re-written here (a fan from the centroid at the thickness, a skirt down to
# the sheet), per poly as _place_sheets :238-336 does; that file and FieldMap are not loaded. Every slab and cell square shares ONE
# ShaderMaterial (shaders/sheet_tube.gdshader), so the tube costs one set of uniform updates per set_tube call.

const SHADER := preload("res://scenes/space3d/shaders/sheet_tube.gdshader")
const LAYER_VIEW := preload("res://scenes/tactical_c/layer_view.gd")
const KIT_PATH := "res://scenes/mockups/landscape/kits/space.json"
const LAYERS := LAYER_VIEW.LAYER_COUNT  # five engine layers 0..4
# DRAFT-space-layer-gap, Q-246-01 (a); the same 1,000 as SpaceView.LAYER_GAP_WU and field_map_space.gd:22.
const LAYER_GAP_WU := 1000.0
# DRAFT-sheet-dim: kit-mode spec section 4, "darkened by 55 percent" on every sheet but the focus sheet.
const SHEET_DIM := 0.55
# DRAFT-cell-thickness (d-view spec "Layer indicators" bullet and Numbers). d-view spec rev 1, gap 10 null action said 60 (the plate
# thickness); the spec paragraph says 30 and is taken. Architect may veto on the shot.
const CELL_THICKNESS_WU := 30.0
# Cells follow the sim: 240 x 240 cells of 100 wu, mask index cy * 240 + cx, centre ((cx + 0.5) * 100, (cy + 0.5) * 100) (csrc/space_raster.c).
const SIDE := 240
const CELL_WU := 100.0
const KIND_MASS := 1
const KIND_RUBBLE := 2
# Fade cut-off between sheets: a sheet is above the focus sheet when its y is greater than focus_y + 0.5 * gap
# (d-view spec rev 1, gap 10 null action, Architect may veto on the shot).
const FADE_HALF_GAP := 0.5

var _mat := ShaderMaterial.new()
var _plate_h := 0.0
var _rubble_h := 0.0
var _kit_sheet := PackedColorArray()
var _kit_mass := Color.BLACK
var _focus := 0
var _counts: Array = []
var _tube_on := false
var _tube_focus_y := 0.0


func _init() -> void:
	_mat.shader = SHADER
	_mat.set_shader_parameter("layer_gap", LAYER_GAP_WU)
	_mat.set_shader_parameter("layer_colours", PackedColorArray(LAYER_VIEW.LAYER_COLOURS))
	var f := FileAccess.open(KIT_PATH, FileAccess.READ)
	var kit = JSON.parse_string(f.get_as_text()) if f != null else null
	if not kit is Dictionary:
		push_error("SpaceSheets: cannot read %s" % KIT_PATH)
		return
	_plate_h = float(kit["plate"]["thickness"])
	_rubble_h = float(kit["rubble"]["thickness"])
	for hex in kit["layers"]:
		_kit_sheet.append(Color.html(str(hex)))
	_kit_mass = Color.html(str(kit["mass"]))
	_push_colours()


func sheet_y(layer: int) -> float:
	return layer * LAYER_GAP_WU


# The colour in use: the kit colour on the focus sheet, darkened SHEET_DIM on every other.
func sheet_colour(layer: int) -> Color:
	return _kit_sheet[layer] if layer == _focus else _kit_sheet[layer].darkened(SHEET_DIM)


func set_focus_layer(n: int) -> void:
	_focus = n
	_push_colours()


func _push_colours() -> void:
	var sheet := PackedColorArray()
	var mass := PackedColorArray()
	for k in range(LAYERS):
		sheet.append(sheet_colour(k))
		mass.append(_kit_mass if k == _focus else _kit_mass.darkened(SHEET_DIM))
	_mat.set_shader_parameter("sheet_colours", sheet)
	_mat.set_shader_parameter("mass_colours", mass)


func set_tube(active: bool, center: Vector2, radius: float, focus_y: float) -> void:
	_tube_on = active
	_tube_focus_y = focus_y
	_mat.set_shader_parameter("tube_on", active)
	_mat.set_shader_parameter("tube_center", center)
	_mat.set_shader_parameter("tube_radius", radius)
	_mat.set_shader_parameter("focus_y", focus_y)


# The sheets above the focus layer while the tube is active; empty when it is not.
func faded_layers() -> Array:
	var out := []
	if _tube_on:
		for k in range(LAYERS):
			if sheet_y(k) > _tube_focus_y + FADE_HALF_GAP * LAYER_GAP_WU:
				out.append(k)
	return out


# Array of 5 {layer, y, blocked_cells, slabs, cell_squares}: blocked_cells is the mask popcount (covered or not), slabs the poly count of the
# layer, cell_squares the blocked cells no poly covers.
func counts() -> Array:
	return _counts.duplicate(true)


func build(field: Dictionary) -> void:
	for c in get_children():
		remove_child(c)
		c.queue_free()
	_counts = []
	var box := BoxMesh.new()
	box.size = Vector3(CELL_WU, CELL_THICKNESS_WU, CELL_WU)
	for k in range(LAYERS):
		var mask: PackedByteArray = field["masks"][k]
		var covered := PackedByteArray()
		covered.resize(SIDE * SIDE)
		var sheet := {"verts": PackedVector3Array(), "norms": PackedVector3Array()}
		var mass := {"verts": PackedVector3Array(), "norms": PackedVector3Array()}
		var slabs := 0
		for poly in field["polys"]:
			if int(poly["layer"]) != k:
				continue
			var pts: PackedVector2Array = poly["points"]
			var kind := int(poly["kind"])
			_add_slab(mass if kind == KIND_MASS else sheet, pts, _rubble_h if kind == KIND_RUBBLE else _plate_h)
			_cover(covered, pts)
			slabs += 1
		var blocked := 0
		var open_at := PackedInt32Array()
		for i in range(SIDE * SIDE):
			if (int(mask[i >> 3]) >> (i & 7)) & 1 == 1:
				blocked += 1
				if covered[i] == 0:
					open_at.append(i)
		_counts.append({"layer": k, "y": sheet_y(k), "blocked_cells": blocked, "slabs": slabs, "cell_squares": open_at.size()})
		_add_mesh_node("Sheet_L%d" % k, sheet, false, k)
		_add_mesh_node("Mass_L%d" % k, mass, true, k)
		_add_cells("Cells_L%d" % k, open_at, box, k)


func _add_mesh_node(node_name: String, data: Dictionary, is_mass: bool, layer: int) -> void:
	if (data["verts"] as PackedVector3Array).is_empty():
		return
	var arrays := []
	arrays.resize(Mesh.ARRAY_MAX)
	arrays[Mesh.ARRAY_VERTEX] = data["verts"]
	arrays[Mesh.ARRAY_NORMAL] = data["norms"]
	if is_mass:
		# The shader reads COLOR.r < 0.5 as a mass slab; a mesh without a COLOR array reads white.
		var cols := PackedColorArray()
		cols.resize((data["verts"] as PackedVector3Array).size())
		cols.fill(Color(0.0, 0.0, 0.0, 1.0))
		arrays[Mesh.ARRAY_COLOR] = cols
	var mesh := ArrayMesh.new()
	mesh.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arrays)
	var mi := MeshInstance3D.new()
	mi.name = node_name
	mi.mesh = mesh
	mi.material_override = _mat
	mi.position = Vector3(0.0, sheet_y(layer), 0.0)
	add_child(mi)


# One 100 x 100 prism per blocked cell no poly covers, centred on the cell centre and standing on the sheet (instance y = half the thickness);
# the instance buffer is the 3 x 4 transform, row by row.
func _add_cells(node_name: String, cells: PackedInt32Array, box: Mesh, layer: int) -> void:
	if cells.is_empty():
		return
	var buf := PackedFloat32Array()
	buf.resize(cells.size() * 12)
	for n in range(cells.size()):
		var gy := cells[n] / SIDE
		var gx := cells[n] - gy * SIDE
		var o := n * 12
		buf[o] = 1.0
		buf[o + 3] = (gx + 0.5) * CELL_WU
		buf[o + 5] = 1.0
		buf[o + 7] = CELL_THICKNESS_WU * 0.5
		buf[o + 10] = 1.0
		buf[o + 11] = (gy + 0.5) * CELL_WU
	var mm := MultiMesh.new()
	mm.transform_format = MultiMesh.TRANSFORM_3D
	mm.mesh = box
	mm.instance_count = cells.size()
	mm.buffer = buf
	var mmi := MultiMeshInstance3D.new()
	mmi.name = node_name
	mmi.multimesh = mm
	mmi.material_override = _mat
	mmi.position = Vector3(0.0, sheet_y(layer), 0.0)
	add_child(mmi)


# placer.gd _add_slab :424-443: the top face at `height` as a fan from the centroid, and a skirt down to y = 0 (the sheet) on every edge.
func _add_slab(into: Dictionary, points: PackedVector2Array, height: float) -> void:
	var verts: PackedVector3Array = into["verts"]
	var norms: PackedVector3Array = into["norms"]
	var centroid := Vector2.ZERO
	for p in points:
		centroid += p
	centroid /= points.size()
	var centre_top := Vector3(centroid.x, height, centroid.y)
	for i in range(points.size()):
		var a := points[i]
		var b := points[(i + 1) % points.size()]
		var a_top := Vector3(a.x, height, a.y)
		var b_top := Vector3(b.x, height, b.y)
		verts.append_array(PackedVector3Array([centre_top, a_top, b_top]))
		norms.append_array(PackedVector3Array([Vector3.UP, Vector3.UP, Vector3.UP]))
		var outward := Vector3(b.y - a.y, 0.0, a.x - b.x).normalized()
		verts.append_array(PackedVector3Array([a_top, Vector3(b.x, 0.0, b.y), b_top, a_top, Vector3(a.x, 0.0, a.y), Vector3(b.x, 0.0, b.y)]))
		norms.append_array(PackedVector3Array([outward, outward, outward, outward, outward, outward]))
	into["verts"] = verts
	into["norms"] = norms


# Marks every cell whose centre a poly covers, by the sim's rule (csrc/space_raster.c:44-76 sr_fill_polygon, "even-odd scanline at each cell row
# centre"): the cell centre is ((gx + 0.5) * 100, (gy + 0.5) * 100); an edge crosses the row when (ay <= y && by > y) || (by <= y && ay > y); a
# cell is inside when xs[p] <= x <= xs[p + 1] (inclusive).
func _cover(covered: PackedByteArray, pts: PackedVector2Array) -> void:
	var low_y := INF
	var high_y := -INF
	for p in pts:
		low_y = minf(low_y, p.y)
		high_y = maxf(high_y, p.y)
	var n := pts.size()
	for gy in range(maxi(int(low_y / CELL_WU) - 1, 0), mini(int(high_y / CELL_WU) + 1, SIDE - 1) + 1):
		var y := (gy + 0.5) * CELL_WU
		var xs: Array = []
		for e in range(n):
			var a := pts[e]
			var b := pts[(e + 1) % n]
			if (a.y <= y and b.y > y) or (b.y <= y and a.y > y):
				xs.append(a.x + (y - a.y) / (b.y - a.y) * (b.x - a.x))
		xs.sort()
		var p := 0
		while p + 1 < xs.size():
			# The direct inclusive test decides; the margin of one cell only bounds the scan.
			for gx in range(maxi(int(floor(float(xs[p]) / CELL_WU - 0.5)) - 1, 0), mini(int(ceil(float(xs[p + 1]) / CELL_WU - 0.5)) + 1, SIDE - 1) + 1):
				var x := (gx + 0.5) * CELL_WU
				if x >= float(xs[p]) and x <= float(xs[p + 1]):
					covered[gy * SIDE + gx] = 1
			p += 2
