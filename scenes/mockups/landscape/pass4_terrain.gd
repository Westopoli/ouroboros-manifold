class_name Pass4Terrain
extends RefCounted

# Pass 4 prototype (docs/northstar/plans/archive/specs/2026-10-03-land-mockup-pass4-spec.md): landforms, minimum
# relief, benching, then the numbers Westley judges (steepness, bands, walking reach, variety).
# Prototype only: not deterministic-checked, not budgeted, never loaded by the game.

const LANDFORM_MODES := ["seed", "mesa", "canyon", "islands", "none"]
const LANDFORM_NAMES := ["mesa", "canyon", "islands"]
const MIN_RELIEF_DEFAULT := 2500.0
const BENCH_STEP_WU := 300.0
const DRY_LEVEL_WU := 60.0
const LIMITS := [30.0, 32.5, 35.0]
const WALK_LIMITS := [30.0, 35.0]
const PEAK_WINDOW := 4
const SP := FieldMap.SPACING


# ---------------------------------------------------------------- generation

static func shape(fm: FieldMap, e: PackedFloat32Array, p_seed: int) -> PackedFloat32Array:
	var chosen: Array = []
	match fm.p4_landform:
		"seed":
			var pick := RandomNumberGenerator.new()
			pick.seed = p_seed + 101
			var first := pick.randi() % 3
			for i in range(3):
				if i == first or pick.randf() < 0.4:
					chosen.append(i)
		"mesa":
			chosen = [0]
		"canyon":
			chosen = [1]
		"islands":
			chosen = [2]
	var built: Array = []
	for i in chosen:
		var rng := RandomNumberGenerator.new()
		rng.seed = p_seed + 201 + i
		var ok := false
		match i:
			0:
				ok = _mesa(fm, e, rng)
			1:
				ok = _canyon(fm, e, rng)
			2:
				ok = _islands(fm, e, rng)
		if ok:
			built.append(LANDFORM_NAMES[i])
	var scale := _enforce_relief(fm, e)
	var share := _bench(fm, e, p_seed)
	fm.p4_info["landforms"] = built
	fm.p4_info["relief_scale"] = scale
	fm.p4_info["bench_share"] = share
	fm.p4_info["bench_from_seed"] = fm.p4_bench_override < 0.0
	return e


static func _idx(fm: FieldMap, p: Vector2) -> int:
	var gx := clampi(int(round(p.x / SP)), 0, fm.dim - 1)
	var gy := clampi(int(round(p.y / SP)), 0, fm.dim - 1)
	return gy * fm.dim + gx


static func _cell_box(fm: FieldMap, c: Vector2, r: float) -> Rect2i:
	var x0 := clampi(int(floor((c.x - r) / SP)), 0, fm.dim - 1)
	var x1 := clampi(int(ceil((c.x + r) / SP)), 0, fm.dim - 1)
	var y0 := clampi(int(floor((c.y - r) / SP)), 0, fm.dim - 1)
	var y1 := clampi(int(ceil((c.y + r) / SP)), 0, fm.dim - 1)
	return Rect2i(x0, y0, x1 - x0, y1 - y0)


# A flat-topped block lifted 900 wu over the ground it stands on, walls about 200 wu wide.
static func _mesa(fm: FieldMap, e: PackedFloat32Array, rng: RandomNumberGenerator) -> bool:
	var canvas := fm.canvas
	var r := canvas * rng.randf_range(0.05, 0.085)
	var margin := r * 1.6
	var c := Vector2.ZERO
	var base := 0.0
	var found := false
	for attempt in range(60):
		c = Vector2(rng.randf_range(margin, canvas - margin), rng.randf_range(margin, canvas - margin))
		base = e[_idx(fm, c)]
		if base > 400.0 * fm.p4_relief and base < 3000.0 * fm.p4_relief:
			found = true
			break
	if not found:
		return false
	var top := base + 900.0 * fm.p4_relief
	var edge := 200.0
	var p1 := rng.randf() * TAU
	var p2 := rng.randf() * TAU
	var box := _cell_box(fm, c, r * 1.3 + edge)
	for gy in range(box.position.y, box.end.y + 1):
		for gx in range(box.position.x, box.end.x + 1):
			var p := Vector2(gx, gy) * SP
			var d := p.distance_to(c)
			var a := (p - c).angle()
			var rr := r * (1.0 + 0.12 * sin(3.0 * a + p1) + 0.08 * sin(5.0 * a + p2))
			var t := smoothstep(0.0, 1.0, clampf((rr + edge - d) / edge, 0.0, 1.0))
			var i := gy * fm.dim + gx
			e[i] = lerpf(e[i], top, t)
	return true


# A winding cut 600 wu wide and up to 1500 wu deep, started on high land and run across it.
static func _canyon(fm: FieldMap, e: PackedFloat32Array, rng: RandomNumberGenerator) -> bool:
	var canvas := fm.canvas
	var half := 300.0
	var shoulder := 150.0
	var depth := 1500.0 * fm.p4_relief
	var carve := PackedFloat32Array()
	carve.resize(e.size())
	var dim := fm.dim
	var cut := 0
	for attempt in range(30):
		carve.fill(0.0)
		var pos := Vector2(rng.randf_range(0.1, 0.9), rng.randf_range(0.1, 0.9)) * canvas
		if e[_idx(fm, pos)] < 1200.0 * fm.p4_relief:
			continue
		var heading := rng.randf() * TAU
		var phase := rng.randf() * TAU
		var steps := int(canvas * 0.4 / SP)
		for s in range(steps):
			pos += Vector2.from_angle(heading + 0.7 * sin(s * 0.06 + phase)) * SP
			var box := _cell_box(fm, pos, half + shoulder)
			for gy in range(box.position.y, box.end.y + 1):
				for gx in range(box.position.x, box.end.x + 1):
					var d := (Vector2(gx, gy) * SP).distance_to(pos)
					var v := smoothstep(half + shoulder, half, d)
					var i := gy * dim + gx
					carve[i] = maxf(carve[i], v)
		cut = 0
		for i in range(e.size()):
			if carve[i] > 0.5 and e[i] > 600.0 * fm.p4_relief:
				cut += 1
		if cut >= 250:
			break
	if cut < 250:
		return false
	for i in range(e.size()):
		if carve[i] > 0.0 and e[i] > 120.0:
			e[i] = lerpf(e[i], maxf(e[i] - depth, 120.0), carve[i])
	return true


# Five to seven cones rising from the sea along a wandering line, 1500 to 2300 wu apart.
static func _islands(fm: FieldMap, e: PackedFloat32Array, rng: RandomNumberGenerator) -> bool:
	var canvas := fm.canvas
	var pos := Vector2.ZERO
	var found := false
	for attempt in range(80):
		pos = Vector2(rng.randf_range(0.1, 0.9), rng.randf_range(0.1, 0.9)) * canvas
		if e[_idx(fm, pos)] < -300.0:
			found = true
			break
	if not found:
		return false
	var heading := rng.randf() * TAU
	var placed := 0
	for k in range(rng.randi_range(5, 7)):
		heading += rng.randf_range(-0.6, 0.6)
		pos += Vector2.from_angle(heading) * rng.randf_range(1500.0, 2300.0)
		pos = pos.clamp(Vector2.ONE * 800.0, Vector2.ONE * (canvas - 800.0))
		var r := canvas * rng.randf_range(0.02, 0.037)
		var peak := rng.randf_range(300.0, 900.0) * fm.p4_relief
		if e[_idx(fm, pos)] > -50.0:
			continue
		var box := _cell_box(fm, pos, r)
		for gy in range(box.position.y, box.end.y + 1):
			for gx in range(box.position.x, box.end.x + 1):
				var d := (Vector2(gx, gy) * SP).distance_to(pos)
				if d >= r:
					continue
				var cone := -200.0 + (peak + 200.0) * pow(1.0 - d / r, 0.8)
				var i := gy * fm.dim + gx
				e[i] = maxf(e[i], cone)
		placed += 1
	return placed > 0


# Guarantee: highest ground minus lowest dry ground is at least p4_min_relief. Short maps have
# their dry ground stretched upward; sea floor is left alone.
static func _enforce_relief(fm: FieldMap, e: PackedFloat32Array) -> float:
	var hi := -INF
	for v in e:
		hi = maxf(hi, v)
	var need := fm.p4_min_relief + DRY_LEVEL_WU
	if hi >= need or hi <= 0.0:
		return 1.0
	var k := need / hi
	for i in range(e.size()):
		if e[i] > 0.0:
			e[i] *= k
	return k


# Benched ground: terraces of BENCH_STEP_WU with short risers, over a noise-shaped share of the land.
# Ground under 150 wu is left alone: terracing it would pull coast land under the water line.
# Benches keep a 15 percent tilt: dead-flat benches read as basins to the lake finder and flood.
static func _bench(fm: FieldMap, e: PackedFloat32Array, p_seed: int) -> float:
	var share: float
	if fm.p4_bench_override >= 0.0:
		share = clampf(fm.p4_bench_override / 100.0, 0.0, 1.0)
	else:
		var rng := RandomNumberGenerator.new()
		rng.seed = p_seed * 7 + 13
		share = rng.randf_range(0.15, 0.65)
	var land: Array = []
	for i in range(e.size()):
		if e[i] > 0.0:
			land.append(i)
	if land.is_empty() or share <= 0.0:
		return 0.0
	var noise := fm._make_noise(p_seed + 9, 6.0 / fm.canvas)
	var dim := fm.dim
	var vals := PackedFloat32Array()
	vals.resize(land.size())
	for k in range(land.size()):
		var i: int = land[k]
		vals[k] = noise.get_noise_2d((i % dim) * SP, (i / dim) * SP)
	var sorted := vals.duplicate()
	sorted.sort()
	var thr: float = sorted[int(share * (sorted.size() - 1))]
	var benched := 0
	for k in range(land.size()):
		var i: int = land[k]
		var w := 1.0 if share >= 1.0 else smoothstep(thr + 0.06, thr, vals[k])
		w *= smoothstep(150.0, 450.0, e[i])
		var t := e[i] / BENCH_STEP_WU
		var f := floorf(t)
		var terr := (f + 0.15 * (t - f) + 0.85 * smoothstep(0.7, 1.0, t - f)) * BENCH_STEP_WU
		e[i] = lerpf(e[i], terr, w)
		if w > 0.5:
			benched += 1
	return float(benched) / float(land.size())


# ---------------------------------------------------------------- blocked-ground mask

# Slope over a footprint: tan of the steepest height difference across a window `width` wu wide
# (four directions, centred on the cell). Sea level floors the heights so a beach is not a cliff.
# This one array is the only thing that blocks ground: the steep view, the X cursor, the walk
# flood and the ramp cutter all read it.
static func slope_tan(h: PackedFloat32Array, land: PackedByteArray, dim: int, width: float) -> PackedFloat32Array:
	var out := PackedFloat32Array()
	out.resize(dim * dim)
	_slope_rect(h, land, dim, width, out, 0, 0, dim - 1, dim - 1)
	return out


static func _slope_rect(h: PackedFloat32Array, land: PackedByteArray, dim: int, width: float, out: PackedFloat32Array, x0: int, y0: int, x1: int, y1: int) -> void:
	var r := width * 0.5 / SP
	var rd := r * 0.70710678
	var ox := [r, 0.0, rd, rd]
	var oy := [0.0, r, rd, -rd]
	for gy in range(maxi(y0, 0), mini(y1, dim - 1) + 1):
		for gx in range(maxi(x0, 0), mini(x1, dim - 1) + 1):
			var i := gy * dim + gx
			if land[i] == 0:
				out[i] = 0.0
				continue
			var m := 0.0
			for k in range(4):
				var d := absf(_hs(h, dim, gx + ox[k], gy + oy[k]) - _hs(h, dim, gx - ox[k], gy - oy[k]))
				if d > m:
					m = d
			out[i] = m / width


static func _hs(h: PackedFloat32Array, dim: int, fx: float, fy: float) -> float:
	fx = clampf(fx, 0.0, dim - 1.001)
	fy = clampf(fy, 0.0, dim - 1.001)
	var gx := int(fx)
	var gy := int(fy)
	var tx := fx - gx
	var ty := fy - gy
	var i := gy * dim + gx
	var a := maxf(h[i], 0.0)
	var b := maxf(h[i + 1], 0.0)
	var c := maxf(h[i + dim], 0.0)
	var d := maxf(h[i + dim + 1], 0.0)
	return lerpf(lerpf(a, b, tx), lerpf(c, d, tx), ty)


# Breadth-first over dry ground; a cell is entered when its footprint slope is within the limit.
static func flood(tan_arr: PackedFloat32Array, land: PackedByteArray, dim: int, start: int, limit_tan: float) -> PackedByteArray:
	var out := PackedByteArray()
	out.resize(tan_arr.size())
	var queue := PackedInt32Array()
	queue.append(start)
	out[start] = 1
	var head := 0
	var dx := [-1, 1, 0, 0, -1, 1, -1, 1]
	var dy := [0, 0, -1, 1, -1, -1, 1, 1]
	while head < queue.size():
		var i := queue[head]
		head += 1
		var gx := i % dim
		var gy := i / dim
		for k in range(8):
			var nx: int = gx + dx[k]
			var ny: int = gy + dy[k]
			if nx < 0 or ny < 0 or nx >= dim or ny >= dim:
				continue
			var j := ny * dim + nx
			if out[j] == 0 and land[j] == 1 and tan_arr[j] <= limit_tan:
				out[j] = 1
				queue.append(j)
	return out


# ---------------------------------------------------------------- ramps

const RAMP_GRADE_DEG := 28.0
const RAMP_HALF_WU := 250.0
const RAMP_SHOULDER_WU := 150.0
const RAMP_PAD_WU := 400.0


# Q-189-01: on a ground era a walking route reaches every band. For each layer that has land on the
# core's landmass but nothing the flood reaches, grade a ramp (28 degrees, 500 wu wide) from the
# nearest reachable ground that lets it climb at that grade, up to the layer floor.
# Run once at limit 30 (the harsher of the two limits), so it also holds at 35.
static func cut_ramps(fm: FieldMap, elev: PackedFloat32Array, core_v: Vector2) -> void:
	var dim := fm.dim
	var n := dim * dim
	var h := PackedFloat32Array()
	h.resize(n)
	var land := PackedByteArray()
	land.resize(n)
	for i in range(n):
		h[i] = fm.grid[i].elevation
		land[i] = 1 if fm.grid[i].water < 0.5 else 0
	var core := int(core_v.y) * dim + int(core_v.x)
	var ramp_cells := PackedByteArray()
	ramp_cells.resize(n)
	var ramps := 0
	fm.p4_info["ramps"] = 0
	fm.p4_info["ramp_cells"] = ramp_cells
	fm.p4_info["ramp_bands"] = []
	if land[core] == 0:
		return
	var width := fm.p4_footprint
	var t30 := tan(deg_to_rad(30.0))
	var grade := tan(deg_to_rad(RAMP_GRADE_DEG))
	var tn := slope_tan(h, land, dim, width)
	var main := _landmass(land, dim, core)
	var skipped := {}
	var bands_done: Array = []
	var lo := INF
	var hi := -INF
	for i in range(n):
		if land[i] == 1:
			lo = minf(lo, h[i])
			hi = maxf(hi, h[i])
	var step := maxf((hi - lo) / 5.0, 1.0)
	fm.p4_info["band_lo"] = lo
	fm.p4_info["band_step"] = step
	for iter in range(8):
		var reach := flood(tn, land, dim, core, t30)
		var reached_band := [false, false, false, false, false]
		var has_land := [false, false, false, false, false]
		for i in range(n):
			if main[i] == 1:
				var b := clampi(int(floor((h[i] - lo) / step)), 0, 4)
				has_land[b] = true
				if reach[i] == 1:
					reached_band[b] = true
		var target := -1
		for b in range(5):
			if has_land[b] and not reached_band[b] and not skipped.has(b):
				target = b
				break
		if target < 0:
			break
		var floor_h := lo + step * target + 10.0
		var path := _ramp_path(h, main, reach, dim, target, lo, step, floor_h, grade)
		if path.is_empty():
			skipped[target] = true
			continue
		_stamp_ramp(fm, elev, h, land, reach, ramp_cells, dim, path, floor_h)
		ramps += 1
		bands_done.append(target + 1)
		_slope_rect(h, land, dim, width, tn, 0, 0, dim - 1, dim - 1)
	fm.p4_info["ramps"] = ramps
	fm.p4_info["ramp_bands"] = bands_done


static func _landmass(land: PackedByteArray, dim: int, start: int) -> PackedByteArray:
	var out := PackedByteArray()
	out.resize(land.size())
	var queue := PackedInt32Array()
	queue.append(start)
	out[start] = 1
	var head := 0
	while head < queue.size():
		var i := queue[head]
		head += 1
		for oy in range(-1, 2):
			for ox in range(-1, 2):
				var nx: int = i % dim + ox
				var ny: int = i / dim + oy
				if nx < 0 or ny < 0 or nx >= dim or ny >= dim:
					continue
				var j := ny * dim + nx
				if out[j] == 0 and land[j] == 1:
					out[j] = 1
					queue.append(j)
	return out


# Multi-source BFS outward from the reached ground over the core's landmass; the first cell of the
# target layer far enough from its start to climb to the layer floor at the ramp grade ends the
# path (after a 400 wu level pad at the end, so the end cell's footprint is flat). Returned start first.
static func _ramp_path(h: PackedFloat32Array, main: PackedByteArray, reach: PackedByteArray, dim: int, band: int, lo: float, step: float, floor_h: float, grade: float) -> PackedInt32Array:
	var n := h.size()
	var dist := PackedFloat32Array()
	dist.resize(n)
	dist.fill(-1.0)
	var start_h := PackedFloat32Array()
	start_h.resize(n)
	var parent := PackedInt32Array()
	parent.resize(n)
	parent.fill(-1)
	var queue := PackedInt32Array()
	for i in range(n):
		if reach[i] == 1:
			dist[i] = 0.0
			start_h[i] = h[i]
			queue.append(i)
	var head := 0
	while head < queue.size():
		var i := queue[head]
		head += 1
		if reach[i] == 0 and clampi(int(floor((h[i] - lo) / step)), 0, 4) == band and (floor_h - start_h[i]) <= grade * (dist[i] - RAMP_PAD_WU):
			var path := PackedInt32Array()
			var c := i
			while c != -1:
				path.append(c)
				c = parent[c]
			path.reverse()
			return path
		for oy in range(-1, 2):
			for ox in range(-1, 2):
				if ox == 0 and oy == 0:
					continue
				var nx: int = i % dim + ox
				var ny: int = i / dim + oy
				if nx < 0 or ny < 0 or nx >= dim or ny >= dim:
					continue
				var j := ny * dim + nx
				if dist[j] < 0.0 and main[j] == 1:
					dist[j] = dist[i] + (SP if ox == 0 or oy == 0 else SP * 1.41421356)
					start_h[j] = start_h[i]
					parent[j] = i
					queue.append(j)
	return PackedInt32Array()


static func _stamp_ramp(fm: FieldMap, elev: PackedFloat32Array, h: PackedFloat32Array, land: PackedByteArray, reach: PackedByteArray, ramp_cells: PackedByteArray, dim: int, path: PackedInt32Array, floor_h: float) -> void:
	var total := 0.0
	var arc: Array = [0.0]
	for k in range(1, path.size()):
		var a := Vector2(path[k - 1] % dim, path[k - 1] / dim)
		var b := Vector2(path[k] % dim, path[k] / dim)
		total += a.distance_to(b) * SP
		arc.append(total)
	var h0: float = h[path[0]]
	var best_v := {}
	var best_h := {}
	var reach_cells := ceili((RAMP_HALF_WU + RAMP_SHOULDER_WU) / SP)
	for k in range(path.size()):
		var p: float = h0 + (floor_h - h0) * minf(arc[k] / maxf(total - RAMP_PAD_WU, 1.0), 1.0)
		var cx: int = path[k] % dim
		var cy: int = path[k] / dim
		for gy in range(maxi(cy - reach_cells, 0), mini(cy + reach_cells, dim - 1) + 1):
			for gx in range(maxi(cx - reach_cells, 0), mini(cx + reach_cells, dim - 1) + 1):
				var i := gy * dim + gx
				if land[i] == 0 or reach[i] == 1:
					continue
				var d := Vector2(gx - cx, gy - cy).length() * SP
				var v := smoothstep(RAMP_HALF_WU + RAMP_SHOULDER_WU, RAMP_HALF_WU, d)
				if v > best_v.get(i, 0.0):
					best_v[i] = v
					best_h[i] = p
	for i in best_v:
		var v: float = best_v[i]
		var nh := lerpf(h[i], best_h[i], v)
		h[i] = nh
		elev[i] = nh
		fm.grid[i].elevation = nh
		if v >= 0.5:
			ramp_cells[i] = 1


# ---------------------------------------------------------------- analysis

static func analyse(fm: FieldMap) -> Dictionary:
	var t0 := Time.get_ticks_usec()
	var dim := fm.dim
	var n := dim * dim
	var h := PackedFloat32Array()
	h.resize(n)
	var land := PackedByteArray()
	land.resize(n)
	var lo := INF
	var hi := -INF
	var land_count := 0
	for i in range(n):
		var cell: Dictionary = fm.grid[i]
		h[i] = cell.elevation
		if cell.water < 0.5:
			land[i] = 1
			land_count += 1
			lo = minf(lo, h[i])
			hi = maxf(hi, h[i])
	if land_count == 0:
		return {}
	var relief := hi - lo
	var step := maxf(relief / 5.0, 1.0)
	if fm.p4_info.has("band_lo"):
		lo = fm.p4_info.band_lo
		step = fm.p4_info.band_step
	var layer := PackedByteArray()
	layer.resize(n)
	var layer_count := [0, 0, 0, 0, 0]
	var joint := {}
	for i in range(n):
		if land[i] == 1:
			var l := clampi(int(floor((h[i] - lo) / step)), 0, 4)
			layer[i] = l + 1
			layer_count[l] += 1
			var key: int = l * 5 + int(fm.grid[i].zone)
			joint[key] = joint.get(key, 0) + 1
	var edges: Array = []
	var shares: Array = []
	for l in range(5):
		edges.append(lo + step * l)
		shares.append(100.0 * layer_count[l] / land_count)
	var variety := 0.0
	for key in joint:
		var p: float = float(joint[key]) / land_count
		variety -= p * log(p) / log(2.0)

	var tn := slope_tan(h, land, dim, fm.p4_footprint)
	var steep := {}
	for lim in LIMITS:
		steep[str(lim)] = steep_share(tn, land, land_count, lim)

	var peaks: Array = []
	var w := PEAK_WINDOW
	for gy in range(w, dim - w):
		for gx in range(w, dim - w):
			var idx := gy * dim + gx
			if layer[idx] < 4:
				continue
			var hv := h[idx]
			var is_peak := true
			for oy in range(-w, w + 1):
				for ox in range(-w, w + 1):
					if ox == 0 and oy == 0:
						continue
					var j := idx + oy * dim + ox
					if h[j] > hv or (h[j] == hv and j < idx):
						is_peak = false
						break
				if not is_peak:
					break
			if is_peak:
				peaks.append(idx)

	var core := _core_cell(fm, land)
	var reach := {}
	var walk := {}
	for lim in WALK_LIMITS:
		var r := flood(tn, land, dim, core, tan(deg_to_rad(lim)))
		reach[str(lim)] = r
		var reached := 0
		var layers_hit := [false, false, false, false, false]
		for i in range(n):
			if r[i] == 1:
				reached += 1
				layers_hit[layer[i] - 1] = true
		var peaks_hit := 0
		for pi in peaks:
			if r[pi] == 1:
				peaks_hit += 1
		walk[str(lim)] = {
			"reach_pct": 100.0 * reached / land_count,
			"layers_reachable": layers_hit.count(true),
			"peaks": peaks.size(),
			"peaks_reachable": peaks_hit,
			"peaks_reachable_pct": 100.0 * peaks_hit / maxf(peaks.size(), 1),
		}
	var ramp_cells: PackedByteArray = fm.p4_info.get("ramp_cells", PackedByteArray())
	if ramp_cells.size() != n:
		ramp_cells = PackedByteArray()
		ramp_cells.resize(n)
	var metrics := {
		"lowest_wu": lo,
		"highest_wu": hi,
		"relief_wu": relief,
		"band_floor_wu": edges,
		"step_wu": step,
		"layer_share_pct": shares,
		"steep_pct": steep,
		"walk": walk,
		"variety_bits": variety,
		"variety_max_bits": log(25.0) / log(2.0),
		"land_pct": 100.0 * land_count / n,
		"landforms": fm.p4_info.get("landforms", []),
		"bench_share_pct": 100.0 * fm.p4_info.get("bench_share", 0.0),
		"bench_from_seed": fm.p4_info.get("bench_from_seed", true),
		"min_relief_wu": fm.p4_min_relief,
		"relief_scale": fm.p4_info.get("relief_scale", 1.0),
		"shape_ms": fm.p4_info.get("shape_ms", 0.0),
		"footprint_wu": fm.p4_footprint,
		"detail_scale": fm.p4_detail_scale,
		"relief_mult": fm.p4_relief,
		"ramps_on": fm.p4_ramps,
		"ramps": fm.p4_info.get("ramps", 0),
		"ramp_cells": ramp_cells.count(1),
		"ramp_bands": fm.p4_info.get("ramp_bands", []),
		"core_cell": core,
		"core_landmass_pct": 100.0 * _landmass(land, dim, core).count(1) / land_count,
	}
	metrics["analyse_ms"] = (Time.get_ticks_usec() - t0) / 1000.0
	return {"metrics": metrics, "h": h, "land": land, "layer": layer, "tan": tn, "reach": reach, "peaks": peaks, "lo": lo, "step": step, "ramp_cells": ramp_cells, "land_count": land_count}


static func steep_share(tn: PackedFloat32Array, land: PackedByteArray, land_count: int, limit_deg: float) -> float:
	var tl := tan(deg_to_rad(limit_deg))
	var cnt := 0
	for i in range(tn.size()):
		if land[i] == 1 and tn[i] > tl:
			cnt += 1
	return 100.0 * cnt / maxf(land_count, 1)


# Share too steep at 30, 32.5, 35 for several footprints (no ramps involved: pure terrain heights).
static func footprint_table(fm: FieldMap, widths: Array) -> Dictionary:
	var a: Dictionary = fm.p4
	var out := {}
	for wd in widths:
		var tn := slope_tan(a.h, a.land, fm.dim, wd)
		var row := {}
		for lim in LIMITS:
			row[str(lim)] = steep_share(tn, a.land, a.land_count, lim)
		out[str(int(wd))] = row
	return out


static func _core_cell(fm: FieldMap, land: PackedByteArray) -> int:
	for nd in fm.nodes:
		if nd.type == "objective":
			var i := _idx(fm, nd.pos)
			if land[i] == 1:
				return i
			for r in range(1, 12):
				for oy in range(-r, r + 1):
					for ox in range(-r, r + 1):
						var gx := i % fm.dim + ox
						var gy := i / fm.dim + oy
						if gx >= 0 and gy >= 0 and gx < fm.dim and gy < fm.dim and land[gy * fm.dim + gx] == 1:
							return gy * fm.dim + gx
			return i
	return 0


# ---------------------------------------------------------------- views

const WATER := Color(0.1, 0.22, 0.45)
const GROUND := Color(0.56, 0.62, 0.5)
const RED := Color(0.9, 0.08, 0.08)
const ORANGE := Color(1.0, 0.55, 0.05)
const BAND_COLORS := [Color(0.25, 0.62, 0.3), Color(0.68, 0.82, 0.3), Color(0.96, 0.86, 0.3), Color(0.8, 0.48, 0.22), Color(0.96, 0.96, 0.96)]
const WALK_OK := Color(0.4, 0.74, 0.38)
const WALK_NO := Color(0.78, 0.25, 0.8)
const PEAK_OK := Color(0.1, 0.95, 0.95)
const PEAK_NO := Color(0.03, 0.03, 0.03)
const RAMP := Color(1.0, 0.88, 0.05)


# Colour per cell (grid point) for a view: steep30, steep35, band, walk. Red means blocked at the
# limit: exactly the cells the walk flood cannot enter.
static func cell_colors(fm: FieldMap, view: String, limit: float) -> PackedColorArray:
	var a: Dictionary = fm.p4
	var dim := fm.dim
	var n := dim * dim
	var out := PackedColorArray()
	out.resize(n)
	var h: PackedFloat32Array = a.h
	var land: PackedByteArray = a.land
	var tn: PackedFloat32Array = a.tan
	var tl := tan(deg_to_rad(limit))
	var t30 := tan(deg_to_rad(30.0))
	var reach: PackedByteArray = a.reach[str(limit)]
	var ramp: PackedByteArray = a.ramp_cells
	var lo: float = a.lo
	var step: float = a.step
	for i in range(n):
		if land[i] == 0:
			out[i] = WATER
			continue
		var c := GROUND
		match view:
			"steep30", "steep35":
				if tn[i] > tl:
					c = RED
				elif limit > 30.0 and tn[i] > t30:
					c = ORANGE
			"band":
				c = BAND_COLORS[clampi(int(floor((h[i] - lo) / step)), 0, 4)]
			"walk":
				if reach[i] == 1:
					c = RAMP if ramp[i] == 1 else WALK_OK
				else:
					c = WALK_NO
		out[i] = c
	if view == "walk":
		var core: int = a.metrics.core_cell
		_blob(out, dim, core, 2, Color.WHITE)
		for pi in a.peaks:
			_blob(out, dim, pi, 1, PEAK_OK if reach[pi] == 1 else PEAK_NO)
	return out


static func _blob(out: PackedColorArray, dim: int, idx: int, r: int, c: Color) -> void:
	var cx := idx % dim
	var cy := idx / dim
	for gy in range(cy - r, cy + r + 1):
		for gx in range(cx - r, cx + r + 1):
			if gx >= 0 and gy >= 0 and gx < dim and gy < dim:
				out[gy * dim + gx] = c


# One flat square per cell, centred on the grid point, so a painted cell is exactly a mask cell.
static func build_overlay(fm: FieldMap, colors: PackedColorArray) -> MeshInstance3D:
	var dim := fm.dim
	var h: PackedFloat32Array = fm.p4.h
	var verts := PackedVector3Array()
	var cols := PackedColorArray()
	verts.resize(dim * dim * 6)
	cols.resize(dim * dim * 6)
	var light := Vector3(-0.5, 0.8, -0.3).normalized()
	var o := 0
	for gy in range(dim):
		for gx in range(dim):
			var h00 := _corner(h, dim, gx, gy)
			var h10 := _corner(h, dim, gx + 1, gy)
			var h01 := _corner(h, dim, gx, gy + 1)
			var h11 := _corner(h, dim, gx + 1, gy + 1)
			var x0 := (gx - 0.5) * SP
			var z0 := (gy - 0.5) * SP
			var c := colors[gy * dim + gx]
			var nrm := Vector3(-(h10 + h11 - h00 - h01) / (2.0 * SP), 1.0, -(h01 + h11 - h00 - h10) / (2.0 * SP)).normalized()
			var lam := maxf(0.0, nrm.dot(light))
			var shade := 0.9 + 0.1 * lam if (c == RED or c == ORANGE or c == RAMP) else 0.62 + 0.38 * lam
			var cc := Color(c.r * shade, c.g * shade, c.b * shade)
			var p00 := Vector3(x0, h00, z0)
			var p10 := Vector3(x0 + SP, h10, z0)
			var p11 := Vector3(x0 + SP, h11, z0 + SP)
			var p01 := Vector3(x0, h01, z0 + SP)
			verts[o] = p00
			verts[o + 1] = p10
			verts[o + 2] = p11
			verts[o + 3] = p00
			verts[o + 4] = p11
			verts[o + 5] = p01
			for k in range(6):
				cols[o + k] = cc
			o += 6
	var arrays := []
	arrays.resize(Mesh.ARRAY_MAX)
	arrays[Mesh.ARRAY_VERTEX] = verts
	arrays[Mesh.ARRAY_COLOR] = cols
	var mesh := ArrayMesh.new()
	mesh.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arrays)
	var mi := MeshInstance3D.new()
	mi.name = "P4Overlay"
	mi.mesh = mesh
	var mat := StandardMaterial3D.new()
	mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	mat.vertex_color_use_as_albedo = true
	mat.cull_mode = BaseMaterial3D.CULL_DISABLED
	mi.material_override = mat
	return mi


# Height of the dual-grid corner at (gx - 0.5, gy - 0.5): mean of the four cells around it.
static func _corner(h: PackedFloat32Array, dim: int, gx: int, gy: int) -> float:
	var x0 := clampi(gx - 1, 0, dim - 1)
	var x1 := clampi(gx, 0, dim - 1)
	var y0 := clampi(gy - 1, 0, dim - 1)
	var y1 := clampi(gy, 0, dim - 1)
	return (h[y0 * dim + x0] + h[y0 * dim + x1] + h[y1 * dim + x0] + h[y1 * dim + x1]) * 0.25
