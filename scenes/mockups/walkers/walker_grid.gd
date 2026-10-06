extends RefCounted

# Prototype (disposable): walkability and band grid sampled from the land mockup's height field,
# plus least-time routes for walkers and flyers. No drawing. Read-only use of the landscape scripts.
# The cell is the land generator's own grid (FieldMap.SPACING, 100 wu at canvas 16000).
# The slope test is the land mockup's walk view: Pass4Terrain.analyse tan (footprint slope), limit 35 degrees.

const CANVAS_WU := 16000.0
const LIMIT_DEG := 35.0
# provisional (prototype draft, 2026-10-05)
const TRANSFER_S := 2.5
# provisional (prototype draft, 2026-10-05): the flyer speed used to weigh a transfer against a detour
const FLYER_PLAN_SPEED := 80.0
const INF_COST := 1.0e30
const LANDSCAPE := "res://scenes/mockups/landscape/"

var seed_value := 0
var dim := 0
var cell := 100.0
var height := PackedFloat32Array()
var band := PackedByteArray()
var walkable := PackedByteArray()
var land := PackedByteArray()
var main_cells := PackedInt32Array()
var _grade_limit := 0.0


func _init(p_seed: int = 11, p_canvas: float = CANVAS_WU) -> void:
	seed_value = p_seed
	var fm = load(LANDSCAPE + "field_map.gd").new()
	var p5 = load(LANDSCAPE + "pass5_layout.gd")
	var p4 = load(LANDSCAPE + "pass4_terrain.gd")
	var layouts: Array = p5.layouts()
	fm.p5_layout = layouts[p_seed % layouts.size()]
	fm.generate(p_seed, p_canvas, 60.0)
	var a: Dictionary = p4.analyse(fm)
	dim = fm.dim
	cell = fm.SPACING
	_grade_limit = tan(deg_to_rad(LIMIT_DEG))
	var n := dim * dim
	height = a.h
	band.resize(n)
	walkable.resize(n)
	land.resize(n)
	for i in range(n):
		land[i] = 1 if a.land[i] == 1 else 0
		band[i] = maxi(int(a.layer[i]), 1)
		walkable[i] = 1 if (a.land[i] == 1 and a.tan[i] <= _grade_limit) else 0
	_find_main()


# The largest 8-connected walkable region (walkers start there; smaller pockets are cut off).
func _find_main() -> void:
	var seen := PackedByteArray()
	seen.resize(dim * dim)
	for i in range(dim * dim):
		if walkable[i] == 0 or seen[i] == 1:
			continue
		var comp := PackedInt32Array([i])
		seen[i] = 1
		var k := 0
		while k < comp.size():
			var c := comp[k]
			k += 1
			for dy in range(-1, 2):
				for dx in range(-1, 2):
					var nx: int = c % dim + dx
					var ny: int = c / dim + dy
					if nx < 0 or ny < 0 or nx >= dim or ny >= dim:
						continue
					var nc := ny * dim + nx
					if walkable[nc] == 1 and seen[nc] == 0:
						seen[nc] = 1
						comp.append(nc)
		if comp.size() > main_cells.size():
			main_cells = comp


func cell_of(pos: Vector2) -> int:
	var gx := clampi(int(round(pos.x / cell)), 0, dim - 1)
	var gy := clampi(int(round(pos.y / cell)), 0, dim - 1)
	return gy * dim + gx


func cell_pos(i: int) -> Vector2:
	return Vector2(i % dim, i / dim) * cell


func band_at(pos: Vector2) -> int:
	return band[cell_of(pos)]


func walkable_at(pos: Vector2) -> bool:
	return walkable[cell_of(pos)] == 1


func height_at(pos: Vector2) -> float:
	return height[cell_of(pos)]


func walkable_share() -> float:
	var c := 0
	for v in walkable:
		c += v
	return float(c) / walkable.size()


# Time per unit of speed for one step between neighbouring cells a to b (walker).
func _step_cost(a: int, b: int, option: String) -> float:
	var d := cell_pos(a).distance_to(cell_pos(b))
	var dh := height[b] - height[a]
	var along := sqrt(d * d + dh * dh)
	if option == "a":
		return along
	var f := clampf(absf(dh) / d / _grade_limit, 0.0, 1.0)
	if dh > 0.0:
		return along / (1.0 - 0.5 * f)
	if dh < 0.0 and option == "c":
		return along / (1.0 + 0.25 * f)
	return along


func nearest_walkable(pos: Vector2) -> int:
	var c := cell_of(pos)
	if walkable[c] == 1:
		return c
	var best := -1
	var best_d := INF
	for i in range(dim * dim):
		if walkable[i] == 1:
			var d := cell_pos(i).distance_squared_to(pos)
			if d < best_d:
				best_d = d
				best = i
	return best


func route_walker(from: Vector2, to: Vector2, slope_option: String = "a") -> Dictionary:
	var start := nearest_walkable(from)
	var r := _search(start, 0, to, 0, slope_option, false)
	return _finish(r)


# layer 1..5. Transfers are timed (TRANSFER_S) and listed in the result under "transfers".
func route_flyer(from: Vector2, to: Vector2, layer: int, climb_when_blocked: bool = false, speed: float = FLYER_PLAN_SPEED) -> Dictionary:
	var ok := true
	var steps := int(from.distance_to(to) / (cell * 0.5)) + 1
	for s in range(steps + 1):
		if band_at(from.lerp(to, float(s) / steps)) > layer:
			ok = false
			break
	if ok:
		return _finish({"points": PackedVector2Array([from, to]), "reached": true, "end": to, "transfers": []})
	var r := _search(cell_of(from), layer, to, 1, "a", climb_when_blocked, speed)
	r.points[0] = from
	return _finish(r)


func _finish(r: Dictionary) -> Dictionary:
	var pts: PackedVector2Array = r.points
	var length := 0.0
	for i in range(1, pts.size()):
		length += pts[i - 1].distance_to(pts[i])
	var transfers: Array = r.get("transfers", [])
	var cost: float = r.get("cost", length)
	var crossings: Array = []
	var prev := band_at(pts[0])
	for i in range(1, pts.size()):
		var seg := pts[i - 1].distance_to(pts[i])
		var k := maxi(int(seg / (cell * 0.25)), 1)
		for s in range(1, k + 1):
			var p := pts[i - 1].lerp(pts[i], float(s) / k)
			var b := band_at(p)
			if b != prev:
				crossings.append({"pos": p, "from_band": prev, "to_band": b})
				prev = b
	return {
		"points": pts, "length": length, "cost": cost, "transfers": transfers,
		"crossings": crossings, "bands_crossed": crossings.size(),
		"reached": r.reached, "end": r.end,
		"seconds_at": func(speed: float) -> float: return cost / speed + TRANSFER_S * transfers.size(),
	}


# A* over (cell, layer) states. kind 0 walker: cost is time at speed 1. kind 1 flyer: cost is wu,
# a transfer costs TRANSFER_S * speed. Ties break by lower state index.
func _search(start: int, layer: int, to: Vector2, kind: int, option: String, climb: bool, speed: float = 1.0) -> Dictionary:
	var n := dim * dim
	var layers := 5 if (kind == 1 and climb) else 1
	var g := PackedFloat64Array()
	g.resize(n * layers)
	g.fill(INF_COST)
	var parent := PackedInt32Array()
	parent.resize(n * layers)
	parent.fill(-1)
	var done := PackedByteArray()
	done.resize(n * layers)
	var goal := cell_of(to)
	var s0 := (layer - 1) * n + start if layers > 1 else start
	var base_layer := layer if layers > 1 else 0
	var hk := PackedFloat64Array()
	var hi := PackedInt32Array()
	g[s0] = 0.0
	_push(hk, hi, _h(start, to, kind, option), s0)
	var found := -1
	while hk.size() > 0:
		var top := _pop(hk, hi)
		var s := top
		if done[s] == 1:
			continue
		done[s] = 1
		var c := s % n
		var l := s / n
		if c == goal:
			found = s
			break
		var gx := c % dim
		var gy := c / dim
		var lay := (l + 1) if layers > 1 else layer
		for dy in range(-1, 2):
			for dx in range(-1, 2):
				if dx == 0 and dy == 0:
					continue
				var nx := gx + dx
				var ny := gy + dy
				if nx < 0 or ny < 0 or nx >= dim or ny >= dim:
					continue
				var nc := ny * dim + nx
				if kind == 0:
					if walkable[nc] == 0:
						continue
				elif band[nc] > lay:
					continue
				var w := _step_cost(c, nc, option) if kind == 0 else cell * (1.4142135 if (dx != 0 and dy != 0) else 1.0)
				var ns := l * n + nc
				if g[s] + w < g[ns]:
					g[ns] = g[s] + w
					parent[ns] = s
					_push(hk, hi, g[ns] + _h(nc, to, kind, option), ns)
		if layers > 1 and l < 4:
			var ns := (l + 1) * n + c
			var w := TRANSFER_S * speed
			if g[s] + w < g[ns]:
				g[ns] = g[s] + w
				parent[ns] = s
				_push(hk, hi, g[ns] + _h(c, to, kind, option), ns)
	var reached := found >= 0
	if not reached:
		var best_d := INF
		for s in range(n * layers):
			if g[s] < INF_COST:
				var d := cell_pos(s % n).distance_squared_to(to)
				if d < best_d - 0.001:
					best_d = d
					found = s
	var chain: Array = []
	var s := found
	while s >= 0:
		chain.append(s)
		s = parent[s]
	chain.reverse()
	var pts := PackedVector2Array()
	var transfers: Array = []
	for i in range(chain.size()):
		var p := cell_pos(chain[i] % n)
		if i > 0 and chain[i] / n != chain[i - 1] / n:
			transfers.append({"pos": p, "from_layer": chain[i - 1] / n + 1, "to_layer": chain[i] / n + 1})
		pts.append(p)
	var end_pos := pts[pts.size() - 1]
	return {"points": pts, "reached": reached, "end": end_pos, "transfers": transfers, "cost": g[found] - TRANSFER_S * speed * transfers.size() if kind == 1 else g[found]}


func _h(c: int, to: Vector2, kind: int, option: String) -> float:
	var d := cell_pos(c).distance_to(to)
	if kind == 1:
		return d
	return d / (1.25 if option == "c" else 1.0)


func _push(hk: PackedFloat64Array, hi: PackedInt32Array, key: float, idx: int) -> void:
	hk.append(key)
	hi.append(idx)
	var i := hk.size() - 1
	while i > 0:
		var p := (i - 1) / 2
		if hk[p] < hk[i] or (hk[p] == hk[i] and hi[p] < hi[i]):
			break
		var tk := hk[p]; hk[p] = hk[i]; hk[i] = tk
		var ti := hi[p]; hi[p] = hi[i]; hi[i] = ti
		i = p


func _pop(hk: PackedFloat64Array, hi: PackedInt32Array) -> int:
	var top := hi[0]
	var last := hk.size() - 1
	hk[0] = hk[last]
	hi[0] = hi[last]
	hk.resize(last)
	hi.resize(last)
	var i := 0
	while true:
		var l := i * 2 + 1
		var r := l + 1
		var m := i
		if l < last and (hk[l] < hk[m] or (hk[l] == hk[m] and hi[l] < hi[m])):
			m = l
		if r < last and (hk[r] < hk[m] or (hk[r] == hk[m] and hi[r] < hi[m])):
			m = r
		if m == i:
			break
		var tk := hk[m]; hk[m] = hk[i]; hk[i] = tk
		var ti := hi[m]; hi[m] = hi[i]; hi[i] = ti
		i = m
	return top
