class_name Pass6Cliffs
extends RefCounted

# Pass 6, fault 1: a cliff face stands only along the edge of ground a walker cannot enter, the
# blocked-ground mask of pass 4 (limit 30 degrees, footprint from the slider), not along every
# terrace contour. Small patches and short edges are dropped. Prototype only; candidates.
# See also: field_map.gd (call site), README "Pass 6" fault 1.

const LIMIT_DEG := 30.0
const MIN_EDGE_WU := 1200.0


static func blocked(fm: FieldMap) -> PackedFloat32Array:
	var n := fm.dim * fm.dim
	var h := PackedFloat32Array()
	h.resize(n)
	var land := PackedByteArray()
	land.resize(n)
	for i in range(n):
		h[i] = fm.grid[i].elevation
		land[i] = 1 if fm.grid[i].water < 0.5 else 0
	var tn := Pass4Terrain.slope_tan(h, land, fm.dim, fm.p4_footprint)
	var tl := tan(deg_to_rad(LIMIT_DEG))
	var out := PackedFloat32Array()
	out.resize(n)
	for i in range(n):
		out[i] = 1.0 if (land[i] == 1 and tn[i] > tl) else 0.0
	return out


static func polylines(fm: FieldMap) -> Array:
	var b := fm._blur(blocked(fm), fm.dim, 2)
	var out: Array = []
	for pl in fm._march_squares(b, fm.dim, 0.5):
		var len := 0.0
		for k in range(1, pl.size()):
			len += pl[k].distance_to(pl[k - 1])
		if pl.size() >= 2 and len >= MIN_EDGE_WU:
			out.append(pl)
	return out
