class_name Pass6Shape
extends RefCounted

# Pass 6 prototype: the layout shapes the terrain while it is generated (the layout leads, the
# terrain obeys). Runs inside FieldMap.generate after the pass-4 shaping and before water, slope
# and zones are built. Pass 5's cutter stays behind it as the fallback, not the method.
# Prototype only; every number is a candidate for Westley to set.
#
# Method, in order:
#  1. each layout node gets a height by its kind (relative to the map's relief), relaxed so every
#     edge can be walked at GRADE_DEG over 1.2 times its straight length;
#  2. each edge becomes a meandering centreline whose height runs between its two node heights;
#  3. a land belt is raised around the graph so the nodes stand on land with mountains of the
#     seed's own shape beside the routes;
#  4. a vantage gets a summit cone;
#  5. a valley is carved along every centreline: flat floor of the measured walking width,
#     walls rising beside it; a chokepoint narrows the floor to the layout's width and lifts
#     its sides.

const HEIGHT_FRAC := {"staging": 0.10, "spawn_point": 0.13, "extraction": 0.08, "reinforcement_structure": 0.17, "transit": 0.20, "flank_route": 0.22, "hazard_zone_anchor": 0.24, "chokepoint": 0.27, "objective": 0.30, "vantage": 0.70}
const NODE_MIN_H := 150.0
const GRADE_DEG := 13.0
const PATH_SLACK := 1.2
const VALLEY_WU := 700.0
const SHOULDER_WU := 1300.0
const BELT_IN_WU := 2200.0
const BELT_OUT_WU := 5500.0
const BELT_PEAK_FRAC := 0.75
const MEANDER_FRAC := 0.10
const MEANDER_MAX_WU := 900.0
const CHOKE_TAPER_WU := 1100.0
const CHOKE_WALL_LIFT_WU := 900.0
const CHOKE_WALL_REACH_WU := 1500.0
const CONE_R_WU := 1800.0
const CONE_DEG := 40.0
const SAMPLE_STEP_WU := 150.0
const FLOOR_NOISE_WU := 20.0

# floor mask kept for the dewater step: 1 on a valley or pad floor
static var _floor: PackedByteArray = PackedByteArray()


static func apply(fm: FieldMap, e: PackedFloat32Array, p_seed: int) -> void:
	var t0 := Time.get_ticks_usec()
	var lay: Dictionary = fm.p5_layout
	var dim := fm.dim
	var n := dim * dim
	var hi := 0.0
	for v in e:
		hi = maxf(hi, v)
	var relief := maxf(hi, 1000.0)
	var by_id := {}
	var nodes: Array = []
	for z in lay.zones:
		var nd := {"id": z.id, "type": z.type, "pos": z.ratio * fm.canvas, "props": z.props}
		by_id[z.id] = nd
		nodes.append(nd)
	# 1. node heights, relaxed along the edges
	var hn := {}
	var mob := {}
	for nd in nodes:
		hn[nd.id] = maxf(HEIGHT_FRAC.get(nd.type, 0.2) * relief, NODE_MIN_H)
		mob[nd.id] = 2.0 if nd.type == "vantage" else 1.0
	var tg := tan(deg_to_rad(GRADE_DEG)) * PATH_SLACK
	for it in range(80):
		var moved := false
		for ed in lay.edges:
			var lim: float = tg * by_id[ed.a].pos.distance_to(by_id[ed.b].pos)
			var diff: float = hn[ed.a] - hn[ed.b]
			if absf(diff) > lim + 1.0:
				var ex: float = absf(diff) - lim
				var tot: float = mob[ed.a] + mob[ed.b]
				var s := -1.0 if diff > 0.0 else 1.0
				hn[ed.a] = maxf(hn[ed.a] + s * ex * mob[ed.a] / tot, NODE_MIN_H)
				hn[ed.b] = maxf(hn[ed.b] - s * ex * mob[ed.b] / tot, NODE_MIN_H)
				moved = true
		if not moved:
			break
	# 2. centreline samples: node pads and meandering edges
	var s_pos := PackedVector2Array()
	var s_h := PackedFloat32Array()
	var s_hw := PackedFloat32Array()
	var half_valley := VALLEY_WU * 0.5 + fm.p4_footprint * 0.5 - 40.0
	var chokes: Array = []
	for nd in nodes:
		if nd.type == "chokepoint":
			var w: float = fm.p5_narrow if nd.props.get("width_hint", "moderate") == "narrow" else fm.p5_moderate
			chokes.append({"pos": nd.pos, "hw": w * 0.5 + fm.p4_footprint * 0.5 - 40.0})
	for nd in nodes:
		var pad: float = Pass5Layout.PAD_WU.get(nd.type, 200.0)
		var hw := maxf(pad + fm.p4_footprint * 0.5 - 40.0, half_valley)
		if nd.type == "chokepoint":
			hw = _choke_hw(chokes, nd.pos, half_valley)
		s_pos.append(nd.pos)
		s_h.append(hn[nd.id])
		s_hw.append(hw)
	var ei := 0
	for ed in lay.edges:
		var a: Vector2 = by_id[ed.a].pos
		var b: Vector2 = by_id[ed.b].pos
		var len := a.distance_to(b)
		var steps := maxi(int(len / SAMPLE_STEP_WU), 2)
		var perp := (b - a).orthogonal().normalized()
		var noise: FastNoiseLite = fm._make_noise(p_seed + 700 + ei, 1.0 / maxf(len * 0.45, 1500.0))
		var amp := minf(len * MEANDER_FRAC, MEANDER_MAX_WU) * (1.6 if ed.type == "flank" else 1.0)
		var pts := PackedVector2Array()
		for k in range(steps + 1):
			var t := float(k) / float(steps)
			var off := noise.get_noise_1d(t * len) * 2.0 * amp * sqrt(sin(PI * t))
			pts.append(a.lerp(b, t) + perp * off)
		var arc := PackedFloat32Array()
		arc.append(0.0)
		for k in range(1, pts.size()):
			arc.append(arc[k - 1] + pts[k].distance_to(pts[k - 1]))
		var total: float = arc[arc.size() - 1]
		for k in range(1, pts.size() - 1):
			s_pos.append(pts[k])
			s_h.append(lerpf(hn[ed.a], hn[ed.b], arc[k] / total))
			s_hw.append(_choke_hw(chokes, pts[k], half_valley))
		ei += 1
	# 3. land belt, 4. vantage cones
	var dg := _distance_to_samples(fm, s_pos, s_hw)
	var near_d: PackedFloat32Array = dg.dist
	var near_s: PackedInt32Array = dg.src
	var n_hills := fm._make_noise(p_seed + 60, 5.0 / fm.canvas)
	var n_fine := fm._make_noise(p_seed + 61, 1.0 / 500.0)
	var e1 := e.duplicate()
	for gy in range(dim):
		for gx in range(dim):
			var i := gy * dim + gx
			var c := smoothstep(BELT_OUT_WU, BELT_IN_WU, near_d[i])
			if c <= 0.0:
				continue
			var wp := Vector2(gx, gy) * FieldMap.SPACING
			var f := clampf(n_hills.get_noise_2d(wp.x, wp.y) * 0.8 + 0.5, 0.0, 1.0)
			var floor_h := NODE_MIN_H + relief * BELT_PEAK_FRAC * pow(f, 1.2)
			e1[i] = lerpf(e[i], maxf(e[i], floor_h), c)
	for nd in nodes:
		if nd.type == "vantage":
			var box := Pass4Terrain._cell_box(fm, nd.pos, CONE_R_WU)
			for gy in range(box.position.y, box.end.y + 1):
				for gx in range(box.position.x, box.end.x + 1):
					var d := (Vector2(gx, gy) * FieldMap.SPACING).distance_to(nd.pos)
					if d > CONE_R_WU:
						continue
					var i := gy * dim + gx
					e1[i] = maxf(e1[i], hn[nd.id] - tan(deg_to_rad(CONE_DEG)) * maxf(d - 300.0, 0.0))
	# choke walls: lift the ground beside a chokepoint so its sides are blocked
	for ck in chokes:
		var box := Pass4Terrain._cell_box(fm, ck.pos, CHOKE_WALL_REACH_WU)
		for gy in range(box.position.y, box.end.y + 1):
			for gx in range(box.position.x, box.end.x + 1):
				var d := (Vector2(gx, gy) * FieldMap.SPACING).distance_to(ck.pos)
				e1[gy * dim + gx] += CHOKE_WALL_LIFT_WU * smoothstep(CHOKE_WALL_REACH_WU, CHOKE_WALL_REACH_WU * 0.5, d)
	# 5. carve the valleys
	_floor = PackedByteArray()
	_floor.resize(n)
	var floor_cells := 0
	for i in range(n):
		var s: int = near_s[i]
		if s < 0:
			e[i] = e1[i]
			continue
		var rel: float = near_d[i] - s_hw[s]
		var w := 1.0 - smoothstep(0.0, SHOULDER_WU, maxf(rel, 0.0))
		var wp := Vector2(i % dim, i / dim) * FieldMap.SPACING
		var target: float = s_h[s] + n_fine.get_noise_2d(wp.x, wp.y) * FLOOR_NOISE_WU
		e[i] = lerpf(e1[i], target, w)
		if rel <= 0.0:
			_floor[i] = 1
			floor_cells += 1
	fm.p6_info = {"applied": true, "ms": (Time.get_ticks_usec() - t0) / 1000.0, "relief": relief, "node_h": hn, "floor_cells": floor_cells, "samples": s_pos.size(), "half_valley_wu": half_valley}


static func _choke_hw(chokes: Array, p: Vector2, half_valley: float) -> float:
	var hw := half_valley
	for ck in chokes:
		hw = minf(hw, lerpf(ck.hw, half_valley, smoothstep(0.0, CHOKE_TAPER_WU, p.distance_to(ck.pos))))
	return hw


# Chamfer distance transform from the sample cells, carrying the nearest sample's index.
static func _distance_to_samples(fm: FieldMap, s_pos: PackedVector2Array, s_hw: PackedFloat32Array) -> Dictionary:
	var dim := fm.dim
	var n := dim * dim
	var dist := PackedFloat32Array()
	dist.resize(n)
	dist.fill(INF)
	var src := PackedInt32Array()
	src.resize(n)
	src.fill(-1)
	for k in range(s_pos.size()):
		var c := clampi(int(round(s_pos[k].y / FieldMap.SPACING)), 0, dim - 1) * dim + clampi(int(round(s_pos[k].x / FieldMap.SPACING)), 0, dim - 1)
		if dist[c] > 0.0 or s_hw[k] < s_hw[src[c]]:
			dist[c] = 0.0
			src[c] = k
	var diag := FieldMap.SPACING * 1.41421356
	for rep in range(2):
		for gy in range(dim):
			for gx in range(dim):
				var i := gy * dim + gx
				if gx > 0:
					_relax(dist, src, i, i - 1, FieldMap.SPACING)
				if gy > 0:
					_relax(dist, src, i, i - dim, FieldMap.SPACING)
					if gx > 0:
						_relax(dist, src, i, i - dim - 1, diag)
					if gx < dim - 1:
						_relax(dist, src, i, i - dim + 1, diag)
		for gy in range(dim - 1, -1, -1):
			for gx in range(dim - 1, -1, -1):
				var i := gy * dim + gx
				if gx < dim - 1:
					_relax(dist, src, i, i + 1, FieldMap.SPACING)
				if gy < dim - 1:
					_relax(dist, src, i, i + dim, FieldMap.SPACING)
					if gx > 0:
						_relax(dist, src, i, i + dim - 1, diag)
					if gx < dim - 1:
						_relax(dist, src, i, i + dim + 1, diag)
	return {"dist": dist, "src": src}


static func _relax(dist: PackedFloat32Array, src: PackedInt32Array, i: int, j: int, w: float) -> void:
	if dist[j] + w < dist[i]:
		dist[i] = dist[j] + w
		src[i] = src[j]


# Valley and pad floors are dry: a lake or a river stamped on one is removed (a ford).
static func clear_water(fm: FieldMap, e: PackedFloat32Array, water: PackedFloat32Array) -> void:
	for i in range(_floor.size()):
		if _floor[i] == 1 and e[i] >= 60.0:
			water[i] = 0.0
