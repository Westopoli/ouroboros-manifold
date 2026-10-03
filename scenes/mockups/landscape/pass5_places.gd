class_name Pass5Places
extends RefCounted

# Pass 5 prototype: checks on the obeying terrain, equal-distance resources, and a separate score
# per kind of place. Everything here is a candidate number for Westley to judge.

const SP := FieldMap.SPACING
const KINDS := ["base", "economic", "resource", "expansion", "settlement"]
const BOX_CELLS := 5
const WATER_BOX_CELLS := 15
const BASE_RADIUS_WU := 2500.0
const ECON_PER_SIDE := 3
const EXP_PER_SIDE := 2
const SETTLE_COUNT := 3
const RESOURCE_COUNT := 2
const MIN_FROM_BASE_WU := 2500.0
const RES_SEP_WU := 4000.0
const ECON_NEAR_WU := 6000.0
const EXP_BAND_LO_WU := 3000.0
const EXP_BAND_HI_WU := 8000.0
const SETTLE_MIN_FROM_BASE_WU := 4500.0
const SEP_WU := {"economic": 1500.0, "expansion": 2500.0, "settlement": 3000.0}
const PLACE_COLOR := {"base": Color(0.2, 0.45, 1.0), "economic": Color(0.2, 0.9, 0.3), "resource": Color(1.0, 0.85, 0.1), "expansion": Color(0.2, 0.95, 0.95), "settlement": Color(1.0, 0.3, 0.95)}


static func compute(fm: FieldMap, tol: float) -> Dictionary:
	var t0 := Time.get_ticks_usec()
	var info: Dictionary = fm.p5_info
	var dim := fm.dim
	var n := dim * dim
	var m := Pass5Layout.mask(fm)
	var pass_: PackedByteArray = m.walk
	var land: PackedByteArray = m.land
	var tn: PackedFloat32Array = m.tan
	var h: PackedFloat32Array = m.h
	var comp := Pass5Layout.label(pass_, dim)
	var by_id := {}
	for nd in info.nodes:
		by_id[nd.id] = nd
	var res := {"layout": fm.p5_layout.id, "name": fm.p5_layout.name, "react": info.applied, "tol": tol}

	# edges
	var broken: Array = []
	var flank_total := 0
	for e in info.edges:
		var ca := comp[_near_walk(fm, pass_, by_id[e.a].pos)]
		var cb := comp[_near_walk(fm, pass_, by_id[e.b].pos)]
		if ca == 0 or ca != cb:
			broken.append("%s-%s" % [e.a, e.b])
		if e.type == "flank":
			flank_total += 1
	res["edges_total"] = info.edges.size()
	res["edges_walkable"] = info.edges.size() - broken.size()
	res["edges_broken"] = broken

	# bases: staging for the player side, spawn for the enemy side
	var node_a: Dictionary = {}
	var node_b: Dictionary = {}
	for nd in info.nodes:
		if nd.type == "staging" and node_a.is_empty():
			node_a = nd
		if nd.type == "spawn_point" and node_b.is_empty():
			node_b = nd
	var tl := tan(deg_to_rad(Pass5Layout.LIMIT_DEG))
	var flat := PackedFloat32Array()
	flat.resize(n)
	var passf := PackedFloat32Array()
	passf.resize(n)
	var waterf := PackedFloat32Array()
	waterf.resize(n)
	var tanc := PackedFloat32Array()
	tanc.resize(n)
	for i in range(n):
		tanc[i] = minf(tn[i] / tl, 1.0)
		passf[i] = float(pass_[i])
		waterf[i] = 1.0 - land[i]
	var tan_mean := _box_mean(tanc, dim, BOX_CELLS)
	var open := _box_mean(passf, dim, BOX_CELLS)
	var wfrac := _box_mean(waterf, dim, WATER_BOX_CELLS)
	for i in range(n):
		flat[i] = 1.0 - tan_mean[i]
	var lo := INF
	var hi := -INF
	for i in range(n):
		if pass_[i] == 1:
			lo = minf(lo, h[i])
			hi = maxf(hi, h[i])
	var scores := {}
	var placed: Array = []
	var cell_a := _pick_base(fm, pass_, flat, open, node_a, scores, "base")
	var cell_b := _pick_base(fm, pass_, flat, open, node_b, scores, "base")
	res["base_a_cell"] = cell_a
	res["base_b_cell"] = cell_b
	var d_a := PackedFloat32Array()
	var d_b := PackedFloat32Array()
	if cell_a >= 0:
		d_a = Pass5Layout.walk_dist(fm, pass_, cell_a)
		placed.append(_place("base", 0, cell_a, dim, scores["base"][cell_a]))
	if cell_b >= 0:
		d_b = Pass5Layout.walk_dist(fm, pass_, cell_b)
		placed.append(_place("base", 1, cell_b, dim, scores["base"][cell_b]))
	if d_a.is_empty():
		d_a.resize(n)
		d_a.fill(-1.0)
	if d_b.is_empty():
		d_b.resize(n)
		d_b.fill(-1.0)
	var pos_a: Vector2 = Vector2(cell_a % dim, cell_a / dim) * SP if cell_a >= 0 else Vector2.ZERO
	var pos_b: Vector2 = Vector2(cell_b % dim, cell_b / dim) * SP if cell_b >= 0 else Vector2.ZERO
	var bases_route: bool = cell_a >= 0 and cell_b >= 0 and d_a[cell_b] >= 0.0
	res["bases_route"] = bases_route
	res["bases_walk_wu"] = d_a[cell_b] if bases_route else -1.0
	res["bases_straight_wu"] = pos_a.distance_to(pos_b)

	# vantages
	var vant: Array = []
	for nd in info.nodes:
		if nd.type != "vantage":
			continue
		var c := _near_walk(fm, pass_, nd.pos)
		var ok: bool = comp[c] != 0 and cell_a >= 0 and comp[c] == comp[cell_a]
		var ring := _ring_mean_height(fm, pass_, h, nd.pos, 3000.0)
		vant.append({"id": nd.id, "reachable": ok, "height_wu": h[_cell(fm, nd.pos)], "above_local_mean_wu": h[_cell(fm, nd.pos)] - ring, "moved": nd.moved})
	res["vantages"] = vant
	res["vantages_reachable"] = vant.filter(func(v): return v.reachable).size()

	# chokes
	var chokes: Array = []
	var bypass_ok := 0
	for ck in info.chokes:
		var perp := Vector2(-ck.axis.y, ck.axis.x)
		var run := _measure_run(fm, pass_, ck.pos, perp)
		var sides := _sides_blocked(fm, pass_, ck.pos, perp, run)
		chokes.append({"id": ck.id, "hint": ck.hint, "target_wu": ck.width, "measured_wu": run.width, "sides_blocked": sides})
	res["chokes"] = chokes
	# a flank route bypasses its choke when a walking route exists between its endpoints that never uses a choke corridor
	var flank_ok := 0
	for e in info.edges:
		if e.type != "flank":
			continue
		var pa := _cell(fm, by_id[e.a].pos)
		var pb := _cell(fm, by_id[e.b].pos)
		var avoid := pass_.duplicate()
		for i in range(n):
			if info.corridor[i] == 1:
				avoid[i] = 0
		var mm := {"walk": avoid, "land": land, "h": h}
		var path := Pass5Layout.astar(fm, mm, info, pa, pb, true, false)
		if not path.is_empty():
			flank_ok += 1
	res["flank_total"] = flank_total
	res["flank_bypass_ok"] = flank_ok

	# the equal-distance resources, then the other kinds
	var rel_ok := func(a: float, b: float) -> bool:
		return a >= 0.0 and b >= 0.0 and absf(a - b) / maxf((a + b) * 0.5, 1.0) <= tol
	var elev_rank := PackedFloat32Array()
	elev_rank.resize(n)
	for i in range(n):
		elev_rank[i] = clampf((h[i] - lo) / maxf(hi - lo, 1.0), 0.0, 1.0)
	var res_score := PackedFloat32Array()
	res_score.resize(n)
	var fair_cells := 0
	for i in range(n):
		if pass_[i] == 0 or d_a[i] < MIN_FROM_BASE_WU or d_b[i] < MIN_FROM_BASE_WU:
			continue
		if rel_ok.call(d_a[i], d_b[i]):
			res_score[i] = 0.4 * flat[i] + 0.3 * open[i] + 0.3 * elev_rank[i] + 0.0001
			fair_cells += 1
	scores["resource"] = res_score
	res["fair_cells"] = fair_cells
	var resources: Array = []
	var res_unmet := 0
	for k in range(RESOURCE_COUNT):
		var c := _pick(res_score, dim, RES_SEP_WU, placed, ["resource"])
		var unmet := false
		if c < 0:
			c = _best_balanced(pass_, d_a, d_b, dim, placed)
			unmet = true
			res_unmet += 1
		if c >= 0:
			var p := _place("resource", 2, c, dim, res_score[c])
			p["unmet"] = unmet
			resources.append(p)
			placed.append(p)
	res["resources_unmet"] = res_unmet

	var econ := PackedFloat32Array()
	econ.resize(n)
	var expn := PackedFloat32Array()
	expn.resize(n)
	var settle := PackedFloat32Array()
	settle.resize(n)
	for i in range(n):
		if pass_[i] == 0:
			continue
		var da: float = d_a[i]
		var db: float = d_b[i]
		if da < 0.0 or db < 0.0:
			continue
		var near := minf(da, db)
		var wn := clampf(wfrac[i] / 0.15, 0.0, 1.0)
		if near >= 1200.0:
			econ[i] = 0.3 * flat[i] + 0.3 * wn + 0.2 * open[i] + 0.2 * (1.0 - clampf(near / ECON_NEAR_WU, 0.0, 1.0))
		var own := minf(da, db)
		var other := maxf(da, db)
		if own >= EXP_BAND_LO_WU and own <= EXP_BAND_HI_WU and own < other * 0.85:
			var band := 1.0 - clampf(absf(own - 5000.0) / 3000.0, 0.0, 1.0)
			expn[i] = 0.35 * flat[i] + 0.25 * open[i] + 0.4 * band
		if near >= SETTLE_MIN_FROM_BASE_WU:
			var mid := 1.0 - clampf(absf(da - db) / maxf(da + db, 1.0) / 0.4, 0.0, 1.0)
			settle[i] = 0.3 * flat[i] + 0.2 * wn + 0.3 * mid + 0.2 * open[i]
	scores["economic"] = econ
	scores["expansion"] = expn
	scores["settlement"] = settle
	var scale := fm.canvas / 24000.0
	var counts := {"economic": maxi(1, int(round(ECON_PER_SIDE * scale))), "expansion": maxi(1, int(round(EXP_PER_SIDE * scale))), "settlement": maxi(1, int(round(SETTLE_COUNT * scale)))}
	res["counts_per_side"] = counts
	res["scale"] = scale
	for kind in ["economic", "expansion"]:
		for side in [0, 1]:
			var arr: PackedFloat32Array = scores[kind].duplicate()
			var dn: PackedFloat32Array = d_a if side == 0 else d_b
			var dm: PackedFloat32Array = d_b if side == 0 else d_a
			for i in range(n):
				if arr[i] > 0.0 and not (dn[i] <= dm[i]):
					arr[i] = 0.0
			for k in range(counts[kind]):
				var c := _pick(arr, dim, SEP_WU[kind], placed, [])
				if c >= 0:
					placed.append(_place(kind, side, c, dim, arr[c]))
	for k in range(counts["settlement"]):
		var c := _pick(scores["settlement"], dim, SEP_WU["settlement"], placed, [])
		if c >= 0:
			placed.append(_place("settlement", 2, c, dim, scores["settlement"][c]))
	res["places"] = placed

	# distance rows: objective and each resource
	var rows: Array = []
	var obj_node: Dictionary = {}
	for nd in info.nodes:
		if nd.type == "objective":
			obj_node = nd
			break
	var targets: Array = []
	if not obj_node.is_empty():
		targets.append({"name": "objective", "pos": obj_node.pos})
	for k in range(resources.size()):
		targets.append({"name": "resource %d" % (k + 1), "pos": resources[k].pos})
	var rows_ok := true
	for t in targets:
		var c := _near_walk(fm, pass_, t.pos)
		var wa: float = d_a[c] if pass_[c] == 1 else -1.0
		var wb: float = d_b[c] if pass_[c] == 1 else -1.0
		var sa: float = pos_a.distance_to(t.pos)
		var sb: float = pos_b.distance_to(t.pos)
		var diff := absf(wa - wb) / maxf((wa + wb) * 0.5, 1.0) if wa >= 0.0 and wb >= 0.0 else -1.0
		var ok: bool = diff >= 0.0 and diff <= tol
		if not ok:
			rows_ok = false
		rows.append({"name": t.name, "walk_a": wa, "walk_b": wb, "walk_diff": diff, "straight_a": sa, "straight_b": sb, "straight_diff": absf(sa - sb) / maxf((sa + sb) * 0.5, 1.0), "within_tol": ok})
	res["distance_rows"] = rows
	res["equal_distance_ok"] = rows_ok and not rows.is_empty()
	res["scores"] = scores
	res["comp"] = comp
	res["walk"] = pass_
	res["tan"] = tn
	res["land"] = land
	res["places_ms"] = (Time.get_ticks_usec() - t0) / 1000.0
	return res


static func _place(kind: String, side: int, c: int, dim: int, score: float) -> Dictionary:
	return {"kind": kind, "side": side, "cell": c, "pos": Vector2(c % dim, c / dim) * SP, "score": score}


static func _cell(fm: FieldMap, p: Vector2) -> int:
	return clampi(int(round(p.y / SP)), 0, fm.dim - 1) * fm.dim + clampi(int(round(p.x / SP)), 0, fm.dim - 1)


# The cell itself if walkable, else the nearest walkable cell within 4 cells, else the cell.
static func _near_walk(fm: FieldMap, pass_: PackedByteArray, p: Vector2) -> int:
	var c := _cell(fm, p)
	if pass_[c] == 1:
		return c
	var dim := fm.dim
	for r in range(1, 5):
		for oy in range(-r, r + 1):
			for ox in range(-r, r + 1):
				var gx: int = c % dim + ox
				var gy: int = c / dim + oy
				if gx >= 0 and gy >= 0 and gx < dim and gy < dim and pass_[gy * dim + gx] == 1:
					return gy * dim + gx
	return c


static func _pick_base(fm: FieldMap, pass_: PackedByteArray, flat: PackedFloat32Array, open: PackedFloat32Array, nd: Dictionary, scores: Dictionary, key: String) -> int:
	if nd.is_empty():
		return -1
	if not scores.has(key):
		var z := PackedFloat32Array()
		z.resize(fm.dim * fm.dim)
		scores[key] = z
	var s: PackedFloat32Array = scores[key]
	var box := Pass4Terrain._cell_box(fm, nd.pos, BASE_RADIUS_WU)
	var best := -1
	var best_s := 0.0
	for gy in range(box.position.y, box.end.y + 1):
		for gx in range(box.position.x, box.end.x + 1):
			var i := gy * fm.dim + gx
			var d := (Vector2(gx, gy) * SP).distance_to(nd.pos)
			if pass_[i] == 0 or d > BASE_RADIUS_WU:
				continue
			var v := 0.4 * flat[i] + 0.3 * open[i] + 0.3 * (1.0 - d / BASE_RADIUS_WU) + 0.0001
			s[i] = v
			if v > best_s:
				best_s = v
				best = i
	scores[key] = s
	return best


# Greedy winner: the highest score at least `sep` wu from everything already placed.
static func _pick(score: PackedFloat32Array, dim: int, sep: float, placed: Array, same_kind: Array) -> int:
	var best := -1
	var best_s := 0.0
	for i in range(score.size()):
		if score[i] <= best_s:
			continue
		var p := Vector2(i % dim, i / dim) * SP
		var ok := true
		for q in placed:
			var need := sep
			if q.kind == "base":
				need = maxf(sep, 1200.0)
			if p.distance_to(q.pos) < need:
				ok = false
				break
		if ok:
			best_s = score[i]
			best = i
	return best


static func _best_balanced(pass_: PackedByteArray, d_a: PackedFloat32Array, d_b: PackedFloat32Array, dim: int, placed: Array) -> int:
	var best := -1
	var best_r := INF
	for i in range(pass_.size()):
		if pass_[i] == 0 or d_a[i] < MIN_FROM_BASE_WU or d_b[i] < MIN_FROM_BASE_WU:
			continue
		var r := absf(d_a[i] - d_b[i]) / maxf((d_a[i] + d_b[i]) * 0.5, 1.0)
		if r >= best_r:
			continue
		var p := Vector2(i % dim, i / dim) * SP
		var ok := true
		for q in placed:
			if q.kind == "resource" and p.distance_to(q.pos) < RES_SEP_WU:
				ok = false
				break
		if ok:
			best_r = r
			best = i
	return best


# Mean of a field over a (2r+1) box at every cell, from a summed-area table.
static func _box_mean(a: PackedFloat32Array, dim: int, r: int) -> PackedFloat32Array:
	var w := dim + 1
	var sat := PackedFloat64Array()
	sat.resize(w * w)
	for gy in range(dim):
		var row := 0.0
		for gx in range(dim):
			row += a[gy * dim + gx]
			sat[(gy + 1) * w + gx + 1] = sat[gy * w + gx + 1] + row
	var out := PackedFloat32Array()
	out.resize(dim * dim)
	for gy in range(dim):
		var y0 := maxi(gy - r, 0)
		var y1 := mini(gy + r, dim - 1)
		for gx in range(dim):
			var x0 := maxi(gx - r, 0)
			var x1 := mini(gx + r, dim - 1)
			var s := sat[(y1 + 1) * w + x1 + 1] - sat[y0 * w + x1 + 1] - sat[(y1 + 1) * w + x0] + sat[y0 * w + x0]
			out[gy * dim + gx] = s / float((y1 - y0 + 1) * (x1 - x0 + 1))
	return out


static func _ring_mean_height(fm: FieldMap, pass_: PackedByteArray, h: PackedFloat32Array, centre: Vector2, r: float) -> float:
	var box := Pass4Terrain._cell_box(fm, centre, r)
	var s := 0.0
	var cnt := 0
	for gy in range(box.position.y, box.end.y + 1):
		for gx in range(box.position.x, box.end.x + 1):
			var i := gy * fm.dim + gx
			if fm.grid[i].water < 0.5 and (Vector2(gx, gy) * SP).distance_to(centre) <= r:
				s += h[i]
				cnt += 1
	return s / maxf(cnt, 1)


# Length of the walkable run through the choke centre, sampled every 20 wu along the perpendicular.
static func _measure_run(fm: FieldMap, pass_: PackedByteArray, centre: Vector2, perp: Vector2) -> Dictionary:
	var step := 20.0
	var reach := 1500.0
	var start := 0.0
	var found := false
	for k in range(0, 31):
		for sgn in [1.0, -1.0]:
			var t: float = sgn * k * step
			if pass_[_cell(fm, centre + perp * t)] == 1:
				start = t
				found = true
				break
		if found:
			break
	if not found:
		return {"width": 0.0, "lo": 0.0, "hi": 0.0}
	var hi := start
	while hi < reach and pass_[_cell(fm, centre + perp * (hi + step))] == 1:
		hi += step
	var lo := start
	while lo > -reach and pass_[_cell(fm, centre + perp * (lo - step))] == 1:
		lo -= step
	return {"width": hi - lo + step, "lo": lo, "hi": hi}


# Both ends of the run meet cells that are not walkable (blocked ground or water).
static func _sides_blocked(fm: FieldMap, pass_: PackedByteArray, centre: Vector2, perp: Vector2, run: Dictionary) -> bool:
	if run.width <= 0.0:
		return false
	return pass_[_cell(fm, centre + perp * (run.hi + 150.0))] == 0 and pass_[_cell(fm, centre + perp * (run.lo - 150.0))] == 0
