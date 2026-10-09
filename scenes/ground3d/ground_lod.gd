class_name GroundLod
extends RefCounted

# Distance level of detail for the ground mesh (S-236 R-236-01: continuous detail from one unit to the map view).
# Level l samples every 2^l-th cell and always keeps the last row and column, so every level covers level 0's footprint.
# See also: ground_mesh.gd, which builds the full-detail mesh with the same vertex placement and colours.

const CELL_WU := 100.0
const GroundBands := preload("res://scenes/ground3d/ground_bands.gd")
# Draft, not Westley's number: camera height (wu) at which level 0 hands over to level 1; each level doubles it.
const SWITCH_BASE_WU := 1500.0
const BLEND_BAND := 0.25

var _terrain: Dictionary = {}
var _levels: Array = []


func set_terrain(t: Dictionary) -> void:
	_terrain = t
	_levels.clear()
	var span := maxi(int(t["cells_w"]), int(t["cells_h"]))
	var stride := 1
	while stride == 1 or stride < span:
		_levels.append(_build(stride))
		stride *= 2


func level_count() -> int:
	return _levels.size()


func switch_height(level: int) -> float:
	return SWITCH_BASE_WU * pow(2.0, level)


func level_for(camera_height: float) -> int:
	var l := 0
	while l < _levels.size() - 1 and camera_height >= switch_height(l):
		l += 1
	return l


func blend_for(camera_height: float) -> float:
	var l := level_for(camera_height)
	if l >= _levels.size() - 1:
		return 0.0
	var sw := switch_height(l)
	return clampf((camera_height - sw * (1.0 - BLEND_BAND)) / (sw * BLEND_BAND), 0.0, 1.0)


func mesh_for(level: int) -> MeshInstance3D:
	return _levels[level]["mi"]


func surface_at(level: int, wx: float, wy: float) -> float:
	var lv: Dictionary = _levels[level]
	var xs: Array = lv["xs"]
	var ys: Array = lv["ys"]
	var fx := _frac(xs, wx / CELL_WU - 0.5)
	var fy := _frac(ys, wy / CELL_WU - 0.5)
	var h00 := _h(xs[fx.x], ys[fy.x])
	var h10 := _h(xs[fx.y], ys[fy.x])
	var h01 := _h(xs[fx.x], ys[fy.y])
	var h11 := _h(xs[fx.y], ys[fy.y])
	return lerpf(lerpf(h00, h10, fx.z), lerpf(h01, h11, fx.z), fy.z)


# Returns (lower index, upper index, t) into the sampled index list for a cell coordinate.
func _frac(idx: Array, c: float) -> Vector3:
	c = clampf(c, float(idx[0]), float(idx[-1]))
	for n in idx.size() - 1:
		if c <= float(idx[n + 1]):
			var span := float(idx[n + 1] - idx[n])
			return Vector3(n, n + 1, (c - idx[n]) / span)
	return Vector3(idx.size() - 1, idx.size() - 1, 0.0)


func _h(i: int, j: int) -> float:
	return _terrain["heights"][j * int(_terrain["cells_w"]) + i] / 100.0


func _indices(n: int, stride: int) -> Array:
	var out: Array = []
	var i := 0
	while i < n - 1:
		out.append(i)
		i += stride
	out.append(n - 1)
	return out


func _build(stride: int) -> Dictionary:
	var w: int = _terrain["cells_w"]
	var h: int = _terrain["cells_h"]
	var bands: PackedByteArray = _terrain["bands"]
	var walk: PackedByteArray = _terrain["walkable"]
	var xs := _indices(w, stride)
	var ys := _indices(h, stride)
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	for b in ys.size() - 1:
		for a in xs.size() - 1:
			var c00 := Vector2i(xs[a], ys[b])
			var c10 := Vector2i(xs[a + 1], ys[b])
			var c01 := Vector2i(xs[a], ys[b + 1])
			var c11 := Vector2i(xs[a + 1], ys[b + 1])
			for c in [c00, c10, c11, c00, c11, c01]:
				var k: int = c.y * w + c.x
				st.set_color(GroundBands.colour(bands[k], walk[k] != 0))
				st.add_vertex(Vector3((c.x + 0.5) * CELL_WU, _terrain["heights"][k] / 100.0, (c.y + 0.5) * CELL_WU))
	st.generate_normals()
	var mi := MeshInstance3D.new()
	mi.mesh = st.commit()
	var mat := StandardMaterial3D.new()
	mat.vertex_color_use_as_albedo = true
	mat.vertex_color_is_srgb = true
	mat.roughness = 0.9
	mi.material_override = mat
	return {"mi": mi, "xs": xs, "ys": ys}
