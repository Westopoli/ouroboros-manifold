class_name Pass6Cliffs
extends RefCounted

# Pass 6: the blocked-ground mask used to shade impassable ground (ground.gd). Cliff face pieces are
# gone (Westley, pass 6 review). Blocked = dry cell whose footprint slope is over 30 degrees.
# See also: ground.gd (the shading), README "Pass 6".

const LIMIT_DEG := 30.0


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
