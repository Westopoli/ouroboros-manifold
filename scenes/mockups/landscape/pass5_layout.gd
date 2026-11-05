class_name Pass5Layout
extends RefCounted

# Pass 5 prototype (docs/northstar/plans/archive/specs/2026-10-03-land-mockup-pass5-spec.md): a layout node graph
# from simulation/layout_library leads, the generated terrain obeys it. Runs inside
# FieldMap.generate right after the pass-4 ramps. Prototype only; every number is a candidate.

const SP := FieldMap.SPACING
const DIR := "res://simulation/layout_library/"

const CAT_PAD := 1
const CAT_GRADED := 2
const CAT_BRIDGE := 3
const CAT_CORRIDOR := 4
const CAT_WALL := 5
const CAT_VANTAGE := 6

# Radius of the levelled pad per node kind (wu). Chokepoints have a corridor instead of a pad.
const PAD_WU := {"staging": 500.0, "objective": 600.0, "vantage": 350.0, "spawn_point": 450.0, "extraction": 350.0, "transit": 200.0, "flank_route": 200.0, "hazard_zone_anchor": 150.0, "reinforcement_structure": 250.0}
const PAD_SHOULDER_WU := 250.0
const CHOKE_LEN_WU := 1600.0
const WALL_H_WU := 900.0
const WALL_BAND_WU := 500.0
const WALL_SLOPE := 1.2
const VANTAGE_SEARCH_WU := 1500.0
const VANTAGE_GRADE_DEG := 14.0
const NODE_GRADE_DEG := 15.0
const NODE_RELAX_ITERATIONS := 0
const ROUTE_HALF_WU := 250.0
const ROUTE_SHOULDER_WU := 150.0
const ROUTE_GRADE_DEG := 18.0
const BLOCKED_COST := 5.0
const WATER_COST := 9.0
const CHOKE_FLANK_COST := 15.0
const ROUTE_ITERATIONS := 6
const MAX_ATTEMPTS := 3
const LIMIT_DEG := 30.0

static var _cache: Array = []


static func layouts() -> Array:
	if not _cache.is_empty():
		return _cache
	var files := Array(DirAccess.get_files_at(DIR)).filter(func(f): return f.begins_with("layout_") and f.ends_with(".json"))
	files.sort()
	for f in files:
		var d: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(DIR + f))
		var zones: Array = []
		for z in d.zones:
			zones.append({"id": z.zone_id, "type": z.node_type, "ratio": Vector2(z.position_ratio[0], z.position_ratio[1]), "props": z.properties})
		var edges: Array = []
		for e in d.edges:
			edges.append({"a": e.from_zone, "b": e.to_zone, "type": e.edge_type})
		_cache.append({"id": d.layout_id, "name": d.name, "zones": zones, "edges": edges})
	return _cache


# Node list, edge list and choke frames from the layout; no terrain edits.
static func prepare(fm: FieldMap) -> void:
	var lay: Dictionary = fm.p5_layout
	var n := fm.dim * fm.dim
	var info := {"nodes": [], "edges": lay.edges, "chokes": [], "applied": false, "react_ms": 0.0}
	var pos := {}
	for z in lay.zones:
		var p: Vector2 = z.ratio * fm.canvas
		pos[z.id] = p
		info.nodes.append({"id": z.id, "type": z.type, "pos": p, "orig": p, "props": z.props, "moved": false})
	for z in lay.zones:
		if z.type != "chokepoint":
			continue
		var nb: Array = []
		for e in lay.edges:
			if e.a == z.id:
				nb.append(pos[e.b])
			elif e.b == z.id:
				nb.append(pos[e.a])
		var axis := Vector2(0.0, -1.0)
		if nb.size() == 1:
			axis = (nb[0] - pos[z.id]).normalized()
		elif nb.size() >= 2:
			var best := -1.0
			for i in range(nb.size()):
				for j in range(i + 1, nb.size()):
					var d: float = nb[i].distance_to(nb[j])
					if d > best:
						best = d
						axis = (nb[j] - nb[i]).normalized()
		var hint: String = z.props.get("width_hint", "moderate")
		var w: float = fm.p5_narrow if hint == "narrow" else fm.p5_moderate
		info.chokes.append({"id": z.id, "hint": hint, "width": w, "axis": axis, "pos": pos[z.id], "t0": w * 0.5 + fm.p4_footprint * 0.5 - 40.0})
	info["changed"] = _zeros(n)
	info["bridge"] = _zeros(n)
	info["wall"] = _zeros(n)
	info["corridor"] = _zeros(n)
	fm.p5_info = info


static func _zeros(n: int) -> PackedByteArray:
	var a := PackedByteArray()
	a.resize(n)
	return a


static func _cell(fm: FieldMap, p: Vector2) -> int:
	return clampi(int(round(p.y / SP)), 0, fm.dim - 1) * fm.dim + clampi(int(round(p.x / SP)), 0, fm.dim - 1)


static func _put(fm: FieldMap, elev: PackedFloat32Array, i: int, h: float) -> void:
	elev[i] = h
	fm.grid[i].elevation = h
	if h >= 60.0 and fm.grid[i].water >= 0.5:
		fm.grid[i].water = 0.0


# ---------------------------------------------------------------- reaction

static func react(fm: FieldMap, elev: PackedFloat32Array) -> void:
	var t0 := Time.get_ticks_usec()
	var info: Dictionary = fm.p5_info
	var dim := fm.dim
	var by_id := {}
	for nd in info.nodes:
		by_id[nd.id] = nd
	# vantages: the highest dry ground near the node, or the node's own spot if that is higher
	for nd in info.nodes:
		if nd.type != "vantage":
			continue
		var c := _cell(fm, nd.pos)
		var best := c
		var best_h: float = fm.grid[c].elevation if fm.grid[c].water < 0.5 else -INF
		var refs: Array = []
		for e in info.edges:
			if e.a == nd.id or e.b == nd.id:
				var other: Dictionary = by_id[e.b if e.a == nd.id else e.a]
				refs.append({"pos": other.pos, "h": maxf(fm.grid[_cell(fm, other.pos)].elevation, 0.0)})
		var box := Pass4Terrain._cell_box(fm, nd.pos, VANTAGE_SEARCH_WU)
		for gy in range(box.position.y, box.end.y + 1):
			for gx in range(box.position.x, box.end.x + 1):
				var i := gy * dim + gx
				var cp := Vector2(gx, gy) * SP
				if fm.grid[i].water >= 0.5 or cp.distance_to(nd.pos) > VANTAGE_SEARCH_WU or fm.grid[i].elevation <= best_h:
					continue
				var climbable := true
				for r in refs:
					if fm.grid[i].elevation - r.h > tan(deg_to_rad(VANTAGE_GRADE_DEG)) * cp.distance_to(r.pos):
						climbable = false
				if climbable:
					best = i
					best_h = fm.grid[i].elevation
		if best != c:
			nd.pos = Vector2(best % dim, best / dim) * SP
			nd.moved = true
	# node heights: start at the ground under each node, then relax so every edge can be walked at
	# NODE_GRADE_DEG over 1.2 times its straight length (vantages move least)
	var hn := {}
	var mob := {}
	for nd in info.nodes:
		hn[nd.id] = maxf(fm.grid[_cell(fm, nd.pos)].elevation, 100.0)
		mob[nd.id] = 0.25 if nd.type == "vantage" else 1.0
	for it in range(NODE_RELAX_ITERATIONS):
		for e in info.edges:
			var lim: float = tan(deg_to_rad(NODE_GRADE_DEG)) * 1.2 * by_id[e.a].pos.distance_to(by_id[e.b].pos)
			var diff: float = hn[e.a] - hn[e.b]
			if absf(diff) > lim:
				var ex: float = absf(diff) - lim
				var tot: float = mob[e.a] + mob[e.b]
				var da: float = ex * mob[e.a] / tot * (-1.0 if diff > 0.0 else 1.0)
				var db: float = ex * mob[e.b] / tot * (1.0 if diff > 0.0 else -1.0)
				hn[e.a] += da
				hn[e.b] += db
	info["node_h"] = hn
	# pads
	for nd in info.nodes:
		if not PAD_WU.has(nd.type):
			continue
		_pad(fm, elev, info, nd.pos, PAD_WU[nd.type], hn[nd.id], CAT_VANTAGE if nd.type == "vantage" else CAT_PAD)
	# chokes
	for ck in info.chokes:
		_choke(fm, elev, info, ck, hn[ck.id])
	# walking routes
	var cuts := 0
	var iters := 0
	var attempts := {}
	for iter in range(ROUTE_ITERATIONS):
		var m := mask(fm)
		var comp := label(m.walk, dim)
		var cut_this := 0
		for e in info.edges:
			var ca := _cell(fm, by_id[e.a].pos)
			var cb := _cell(fm, by_id[e.b].pos)
			if m.walk[ca] == 1 and comp[ca] == comp[cb]:
				continue
			var key: String = e.a + ">" + e.b
			if attempts.get(key, 0) >= MAX_ATTEMPTS:
				continue
			attempts[key] = attempts.get(key, 0) + 1
			var path := astar(fm, m, info, ca, cb, false, e.type == "flank")
			if path.is_empty():
				continue
			_stamp(fm, elev, info, m, path, ROUTE_HALF_WU + 100.0 * iter)
			cuts += 1
			cut_this += 1
			m = mask(fm)
			comp = label(m.walk, dim)
		if cut_this == 0:
			break
		iters += 1
	info.applied = true
	info["cuts"] = cuts
	info["route_iterations"] = iters
	info.react_ms = (Time.get_ticks_usec() - t0) / 1000.0


static func _pad(fm: FieldMap, elev: PackedFloat32Array, info: Dictionary, centre: Vector2, r: float, target: float, cat: int) -> void:
	var dim := fm.dim
	var box := Pass4Terrain._cell_box(fm, centre, r + PAD_SHOULDER_WU)
	for gy in range(box.position.y, box.end.y + 1):
		for gx in range(box.position.x, box.end.x + 1):
			var d := (Vector2(gx, gy) * SP).distance_to(centre)
			var v := smoothstep(r + PAD_SHOULDER_WU, r, d)
			if v <= 0.0:
				continue
			var i := gy * dim + gx
			_put(fm, elev, i, lerpf(elev[i], target, v))
			if v >= 0.5:
				info.changed[i] = cat


static func _choke(fm: FieldMap, elev: PackedFloat32Array, info: Dictionary, ck: Dictionary, hb: float) -> void:
	var dim := fm.dim
	var axis: Vector2 = ck.axis
	var perp := Vector2(-axis.y, axis.x)
	var t0: float = ck.t0
	var reach := maxf(CHOKE_LEN_WU * 0.5 + 400.0, t0 + WALL_BAND_WU + 300.0)
	var box := Pass4Terrain._cell_box(fm, ck.pos, reach * 1.45)
	for gy in range(box.position.y, box.end.y + 1):
		for gx in range(box.position.x, box.end.x + 1):
			var rel: Vector2 = Vector2(gx, gy) * SP - ck.pos
			var as_ := absf(rel.dot(axis))
			var at := absf(rel.dot(perp))
			var ws := smoothstep(CHOKE_LEN_WU * 0.5 + 400.0, CHOKE_LEN_WU * 0.5, as_)
			var wt := smoothstep(t0 + WALL_BAND_WU + 300.0, t0 + WALL_BAND_WU, at)
			var w := ws * wt
			if w <= 0.0:
				continue
			var i := gy * dim + gx
			var h: float = elev[i]
			if at <= t0:
				_put(fm, elev, i, lerpf(h, hb, ws))
				if ws >= 0.5:
					info.changed[i] = CAT_CORRIDOR
					info.corridor[i] = 1
			else:
				var wall := WALL_H_WU * smoothstep(t0, t0 + 120.0, at) + WALL_SLOPE * clampf(at - t0 - 120.0, 0.0, WALL_BAND_WU - 120.0)
				var tgt := maxf(hb + wall, h)
				if tgt > h + 1.0:
					_put(fm, elev, i, lerpf(h, tgt, w))
					if wall >= 100.0 and w >= 0.5:
						info.changed[i] = CAT_WALL
						info.wall[i] = 1


# ---------------------------------------------------------------- walking mask and search

# Walkable at limit 30: dry, footprint slope within the limit, or a bridge cell.
static func mask(fm: FieldMap) -> Dictionary:
	var dim := fm.dim
	var n := dim * dim
	var h := PackedFloat32Array()
	h.resize(n)
	var land := PackedByteArray()
	land.resize(n)
	for i in range(n):
		h[i] = fm.grid[i].elevation
		land[i] = 1 if fm.grid[i].water < 0.5 else 0
	var tn := Pass4Terrain.slope_tan(h, land, dim, fm.p4_footprint)
	var tl := tan(deg_to_rad(LIMIT_DEG))
	var pass_ := PackedByteArray()
	pass_.resize(n)
	var bridge: PackedByteArray = fm.p5_info.bridge
	for i in range(n):
		if (land[i] == 1 and tn[i] <= tl) or bridge[i] == 1:
			pass_[i] = 1
	return {"walk": pass_, "land": land, "tan": tn, "h": h}


# 8-neighbour connected components over the walkable cells (label 0 = not walkable).
static func label(pass_: PackedByteArray, dim: int) -> PackedInt32Array:
	var out := PackedInt32Array()
	out.resize(pass_.size())
	var next := 1
	var queue := PackedInt32Array()
	for s in range(pass_.size()):
		if pass_[s] == 0 or out[s] != 0:
			continue
		out[s] = next
		queue.clear()
		queue.append(s)
		var head := 0
		while head < queue.size():
			var i := queue[head]
			head += 1
			var gx := i % dim
			var gy := i / dim
			for oy in range(-1, 2):
				for ox in range(-1, 2):
					var nx := gx + ox
					var ny := gy + oy
					if nx < 0 or ny < 0 or nx >= dim or ny >= dim:
						continue
					var j := ny * dim + nx
					if pass_[j] == 1 and out[j] == 0:
						out[j] = next
						queue.append(j)
		next += 1
	return out


# A* over the grid. walk_only: only walkable cells (cost 1). Otherwise blocked ground costs 5,
# water 9 (a bridge), wall cells are closed, and a choke corridor costs 15 for a flank route.
static func astar(fm: FieldMap, m: Dictionary, info: Dictionary, src: int, dst: int, walk_only: bool, flank: bool) -> PackedInt32Array:
	var dim := fm.dim
	var n := dim * dim
	var g := PackedFloat32Array()
	g.resize(n)
	g.fill(INF)
	var parent := PackedInt32Array()
	parent.resize(n)
	parent.fill(-1)
	var hk := PackedFloat32Array()
	var hv := PackedInt32Array()
	var dx := dst % dim
	var dy := dst / dim
	g[src] = 0.0
	_push(hk, hv, 0.0, src)
	var pass_: PackedByteArray = m.walk
	var land: PackedByteArray = m.land
	var wall: PackedByteArray = info.wall
	var corr: PackedByteArray = info.corridor
	var hh: PackedFloat32Array = m.h
	var closed := PackedByteArray()
	closed.resize(n)
	while hv.size() > 0:
		var i := _pop(hk, hv)
		if i == dst:
			var path := PackedInt32Array()
			var c := i
			while c != -1:
				path.append(c)
				c = parent[c]
			path.reverse()
			return path
		if closed[i] == 1:
			continue
		closed[i] = 1
		var gx := i % dim
		var gy := i / dim
		for oy in range(-1, 2):
			for ox in range(-1, 2):
				if ox == 0 and oy == 0:
					continue
				var nx := gx + ox
				var ny := gy + oy
				if nx < 0 or ny < 0 or nx >= dim or ny >= dim:
					continue
				var j := ny * dim + nx
				var cost := 1.0
				if pass_[j] == 0:
					if walk_only or wall[j] == 1:
						continue
					cost = (BLOCKED_COST if land[j] == 1 else WATER_COST) + 8.0 * absf(hh[j] - hh[i]) / SP
				elif flank and corr[j] == 1:
					cost = CHOKE_FLANK_COST
				var ng: float = g[i] + cost * (SP if ox == 0 or oy == 0 else SP * 1.41421356)
				if ng < g[j]:
					g[j] = ng
					parent[j] = i
					var ddx := absf(nx - dx)
					var ddy := absf(ny - dy)
					_push(hk, hv, ng + SP * (maxf(ddx, ddy) + 0.41421356 * minf(ddx, ddy)), j)
	return PackedInt32Array()


static func _push(hk: PackedFloat32Array, hv: PackedInt32Array, k: float, v: int) -> void:
	hk.append(k)
	hv.append(v)
	var c := hk.size() - 1
	while c > 0:
		var p := (c - 1) >> 1
		if hk[p] <= hk[c]:
			break
		var tk := hk[p]
		hk[p] = hk[c]
		hk[c] = tk
		var tv := hv[p]
		hv[p] = hv[c]
		hv[c] = tv
		c = p


static func _pop(hk: PackedFloat32Array, hv: PackedInt32Array) -> int:
	var top := hv[0]
	var last := hk.size() - 1
	hk[0] = hk[last]
	hv[0] = hv[last]
	hk.resize(last)
	hv.resize(last)
	var c := 0
	while true:
		var l := 2 * c + 1
		var r := l + 1
		var s := c
		if l < last and hk[l] < hk[s]:
			s = l
		if r < last and hk[r] < hk[s]:
			s = r
		if s == c:
			break
		var tk := hk[s]
		hk[s] = hk[c]
		hk[c] = tk
		var tv := hv[s]
		hv[s] = hv[c]
		hv[c] = tv
		c = s
	return top


# Dijkstra from one cell over walkable cells: walking distance in wu (-1 = not reachable).
static func walk_dist(fm: FieldMap, pass_: PackedByteArray, src: int) -> PackedFloat32Array:
	var dim := fm.dim
	var n := dim * dim
	var g := PackedFloat32Array()
	g.resize(n)
	g.fill(-1.0)
	if pass_[src] == 0:
		return g
	var hk := PackedFloat32Array()
	var hv := PackedInt32Array()
	var done := PackedByteArray()
	done.resize(n)
	g[src] = 0.0
	_push(hk, hv, 0.0, src)
	while hv.size() > 0:
		var i := _pop(hk, hv)
		if done[i] == 1:
			continue
		done[i] = 1
		var gx := i % dim
		var gy := i / dim
		for oy in range(-1, 2):
			for ox in range(-1, 2):
				if ox == 0 and oy == 0:
					continue
				var nx := gx + ox
				var ny := gy + oy
				if nx < 0 or ny < 0 or nx >= dim or ny >= dim:
					continue
				var j := ny * dim + nx
				if pass_[j] == 0:
					continue
				var ng: float = g[i] + (SP if ox == 0 or oy == 0 else SP * 1.41421356)
				if g[j] < 0.0 or ng < g[j]:
					g[j] = ng
					_push(hk, hv, ng, j)
	return g


# Grade the ground along a route: heights follow a smoothed profile limited to the route grade,
# stamped over a strip with soft shoulders; water on the route becomes a bridge.
static func _stamp(fm: FieldMap, elev: PackedFloat32Array, info: Dictionary, m0: Dictionary, path: PackedInt32Array, half: float) -> void:
	var dim := fm.dim
	var m := path.size()
	var hs := PackedFloat32Array()
	hs.resize(m)
	for k in range(m):
		hs[k] = maxf(fm.grid[path[k]].elevation, 0.0)
	var pin := PackedByteArray()
	pin.resize(m)
	for k in range(m):
		pin[k] = 1 if (k == 0 or k == m - 1) else 0
	var prof := hs.duplicate()
	var last := -1
	for k in range(m):
		if pin[k] == 0:
			continue
		if last < 0:
			for q in range(k):
				prof[q] = hs[k]
		else:
			for q in range(last + 1, k):
				prof[q] = lerpf(hs[last], hs[k], float(q - last) / float(k - last))
		last = k
	if last < 0:
		for q in range(m):
			prof[q] = lerpf(hs[0], hs[m - 1], float(q) / float(maxi(m - 1, 1)))
	else:
		for q in range(last + 1, m):
			prof[q] = hs[last]
	var md := tan(deg_to_rad(ROUTE_GRADE_DEG)) * SP
	for k in range(1, m):
		if pin[k] == 0:
			prof[k] = clampf(prof[k], prof[k - 1] - md, prof[k - 1] + md)
	for k in range(m - 2, -1, -1):
		if pin[k] == 0:
			prof[k] = clampf(prof[k], prof[k + 1] - md, prof[k + 1] + md)
	# ends too far apart in height for the grade: meet in the middle, both pads give way
	if absf(hs[m - 1] - hs[0]) > md * (m - 1):
		var mid := (hs[0] + hs[m - 1]) * 0.5
		var sgn := 1.0 if hs[m - 1] > hs[0] else -1.0
		for k in range(m):
			prof[k] = maxf(mid + sgn * md * (k - (m - 1) * 0.5), 0.0)
	var best_d := {}
	var best_h := {}
	var rc := ceili((half + ROUTE_SHOULDER_WU) / SP)
	for k in range(m):
		var cx: int = path[k] % dim
		var cy: int = path[k] / dim
		if fm.grid[path[k]].water >= 0.5:
			for oy in range(-1, 2):
				for ox in range(-1, 2):
					var q := (clampi(cy + oy, 0, dim - 1)) * dim + clampi(cx + ox, 0, dim - 1)
					if fm.grid[q].water >= 0.5:
						info.bridge[q] = 1
						info.changed[q] = CAT_BRIDGE
			continue
		for gy in range(maxi(cy - rc, 0), mini(cy + rc, dim - 1) + 1):
			for gx in range(maxi(cx - rc, 0), mini(cx + rc, dim - 1) + 1):
				var i := gy * dim + gx
				if info.wall[i] == 1:
					continue
				var d := Vector2(gx - cx, gy - cy).length() * SP
				if d < best_d.get(i, INF) and d < half + ROUTE_SHOULDER_WU:
					best_d[i] = d
					best_h[i] = prof[k]
	for i in best_d:
		var v := smoothstep(half + ROUTE_SHOULDER_WU, half, best_d[i])
		if fm.grid[i].water >= 0.5:
			elev[i] = lerpf(elev[i], best_h[i], v)
			fm.grid[i].elevation = elev[i]
			continue
		_put(fm, elev, i, lerpf(elev[i], best_h[i], v))
		if v >= 0.5 and info.changed[i] != CAT_CORRIDOR and info.changed[i] != CAT_PAD and info.changed[i] != CAT_VANTAGE:
			info.changed[i] = CAT_GRADED
