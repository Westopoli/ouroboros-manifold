extends RefCounted

## [DRAFT-e1k-streets] Hidden route mesh for the settlement layer: one ribbon from each stage 2+ lot to its nearest
## stage 2+ neighbour within 3 cells. The mockup's _build_routes (settlement_mockup.gd:283-319) reads a path network
## the sim does not carry; E2 carries it, and this file is replaced by it then.
## Values verbatim from the mockup (GAP 4 ruling, Architect 2026-10-13): half-width 1 unit (M:297), lift 0.15 unit
## (M:292-301), y = max ground height of the 3x3 cells around each sampled cell (M:292-299).
## The terrain dict carries no water mask, so the mockup's water clamp to >= 0 (M:298) is not applied.
## See also: scenes/settlement/settlement_layer.gd, spec Rev 12d (docs/northstar/plans/2026-10-07-visible-game-spec.md).

const CELL_WU := 100.0
const MIN_STAGE := 2
const LINK_CELLS := 3.0
const HALF_WIDTH_WU := 100.0 # M:297, one unit
const LIFT_WU := 15.0 # M:300, 0.15 unit


static func ribbons(lots: Array, t: Dictionary) -> ArrayMesh:
	var cand: Array = []
	for lot in lots:
		if int(lot["stage"]) >= MIN_STAGE:
			cand.append(lot)
	cand.sort_custom(func(a, b): return int(a["id"]) < int(b["id"]))
	var max_d2 := (LINK_CELLS * CELL_WU) * (LINK_CELLS * CELL_WU)
	var done := {}
	var verts := PackedVector3Array()
	var idxs := PackedInt32Array()
	for a in cand:
		var best = null
		var best_d2 := INF
		for b in cand:
			if int(b["id"]) == int(a["id"]):
				continue
			var dx := float(b["x"]) - float(a["x"])
			var dy := float(b["y"]) - float(a["y"])
			var d2 := dx * dx + dy * dy
			if d2 <= max_d2 and d2 < best_d2: # ascending ids, strict <: a tie keeps the lower id
				best = b
				best_d2 = d2
		if best == null:
			continue
		var lo := mini(int(a["id"]), int(best["id"]))
		var hi := maxi(int(a["id"]), int(best["id"]))
		var key := lo * 4294967296 + hi
		if done.has(key):
			continue
		done[key] = true
		_ribbon(t, a, best, verts, idxs)
	var mesh := ArrayMesh.new()
	if verts.size() > 0:
		var arr := []
		arr.resize(Mesh.ARRAY_MAX)
		arr[Mesh.ARRAY_VERTEX] = verts
		arr[Mesh.ARRAY_INDEX] = idxs
		mesh.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arr)
	return mesh


static func _ribbon(t: Dictionary, a: Dictionary, b: Dictionary, verts: PackedVector3Array, idxs: PackedInt32Array) -> void:
	var ax := float(a["x"])
	var ay := float(a["y"])
	var bx := float(b["x"])
	var by := float(b["y"])
	var n := maxi(int(ceil(maxf(absf(bx - ax), absf(by - ay)) / CELL_WU - 1e-6)), 1)
	var pts: Array = []
	for k in n + 1:
		var f := float(k) / float(n)
		var px := lerpf(ax, bx, f)
		var py := lerpf(ay, by, f)
		pts.append(Vector3(px, _top_at(t, px, py) + LIFT_WU, py))
	for k in n:
		var p: Vector3 = pts[k]
		var q: Vector3 = pts[k + 1]
		var dir := Vector3(q.x - p.x, 0.0, q.z - p.z)
		if dir.length() < 1e-6:
			continue
		var side := Vector3(-dir.z, 0.0, dir.x).normalized() * HALF_WIDTH_WU
		var base := verts.size()
		verts.append_array([p - side, p + side, q - side, q + side])
		idxs.append_array([base, base + 1, base + 2, base + 1, base + 3, base + 2])


static func _top_at(t: Dictionary, wx: float, wy: float) -> float:
	var w := int(t.get("cells_w", 0))
	var h := int(t.get("cells_h", 0))
	var hs: PackedInt32Array = t.get("heights", PackedInt32Array())
	if w < 1 or h < 1 or hs.size() < w * h:
		return 0.0
	var cx := int(floor(wx / CELL_WU))
	var cy := int(floor(wy / CELL_WU))
	var top := -1e9
	for oy in range(-1, 2):
		for ox in range(-1, 2):
			var nx := clampi(cx + ox, 0, w - 1)
			var ny := clampi(cy + oy, 0, h - 1)
			top = maxf(top, float(hs[ny * w + nx]) / 100.0)
	return top
