class_name FieldMap
extends RefCounted

const SPACING := 100.0

var canvas: float = 16000.0
var stability: float = 60.0
var dim: int = 0
var nodes: Array = []
# grid: flat Array of Dictionaries, index = gy * dim + gx, gx/gy in [0, dim-1].
# World position of a cell = Vector2(gx, gy) * SPACING.
# Each cell: {obstacle, cover, elevation, interference, water, population, wealth: float [0,1],
#             zone: int 0/1/2, district: int 0..4}
var grid: Array = []
var borders: Array = []
var crossings: Array = []

var _rng := RandomNumberGenerator.new()

func generate(p_seed: int, p_canvas: float = 16000.0, p_stability: float = 60.0) -> void:
	canvas = p_canvas
	stability = clamp(p_stability, 0.0, 100.0)
	dim = int(canvas / SPACING) + 1
	_rng.seed = p_seed

	var noise_obstacle := _make_noise(p_seed + 0, 0.00035)
	var noise_cover := _make_noise(p_seed + 1, 0.00035)
	var noise_elevation := _make_noise(p_seed + 2, 0.00030)
	var noise_interference := _make_noise(p_seed + 3, 0.00040)
	var noise_zone_a := _make_noise(p_seed + 10, 0.00020)
	var noise_zone_b := _make_noise(p_seed + 11, 0.00022)
	var noise_zone_c := _make_noise(p_seed + 12, 0.00025)

	nodes = _build_nodes()
	var river_points := _build_river()

	var objective_pos: Vector2 = _find_node("objective")
	var vantage_pos: Vector2 = _find_node("vantage")
	var hazard_pos: Vector2 = _find_node("hazard_anchor")
	# Chokepoints are appended in base-list order: north approach, west approach, river bridge.
	var chokepoints: Array = _find_nodes("chokepoint")

	var obstacle_pos := PackedVector2Array()
	var obstacle_rad := PackedFloat32Array()
	var obstacle_int := PackedFloat32Array()
	for cp in chokepoints:
		obstacle_pos.append(cp)
		obstacle_rad.append(600.0)
		obstacle_int.append(0.85)
	obstacle_pos.append(hazard_pos)
	obstacle_rad.append(400.0)
	obstacle_int.append(0.40)

	var cover_pos := PackedVector2Array()
	var cover_rad := PackedFloat32Array()
	var cover_int := PackedFloat32Array()
	for cp in chokepoints:
		cover_pos.append(cp)
		cover_rad.append(550.0)
		cover_int.append(0.55)
	for st in _find_nodes("staging"):
		cover_pos.append(st)
		cover_rad.append(500.0)
		cover_int.append(0.30)

	var elevation_pos := PackedVector2Array([vantage_pos, vantage_pos])
	var elevation_rad := PackedFloat32Array([700.0, 3500.0])
	var elevation_int := PackedFloat32Array([0.90, 0.45])

	var interference_pos := PackedVector2Array([hazard_pos])
	var interference_rad := PackedFloat32Array([500.0])
	var interference_int := PackedFloat32Array([0.75])
	if chokepoints.size() > 2:
		interference_pos.append(chokepoints[2])
		interference_rad.append(400.0)
		interference_int.append(0.20)

	var harbor_pos: Vector2 = Vector2(0.42, 0.85) * canvas

	grid.resize(dim * dim)
	var elevation_flat := PackedFloat32Array()
	elevation_flat.resize(dim * dim)
	var water_flat := PackedFloat32Array()
	water_flat.resize(dim * dim)
	var district_flat := PackedFloat32Array()
	district_flat.resize(dim * dim)

	for gy in range(dim):
		for gx in range(dim):
			var idx := gy * dim + gx
			var wpos := Vector2(gx * SPACING, gy * SPACING)

			var water := _sample_water(wpos, river_points)

			var obstacle: float = clamp(_radial_sum_arrays(wpos, obstacle_pos, obstacle_rad, obstacle_int) + noise_obstacle.get_noise_2d(wpos.x, wpos.y) * 0.06, 0.0, 1.0)

			var cover_raw: float = _radial_sum_arrays(wpos, cover_pos, cover_rad, cover_int) + noise_cover.get_noise_2d(wpos.x, wpos.y) * 0.06
			# Higher stability raises cover (better-maintained defensive terrain).
			var cover: float = clamp(cover_raw * (1.0 + stability / 100.0 * 0.3), 0.0, 1.0)

			var interference_raw: float = _radial_sum_arrays(wpos, interference_pos, interference_rad, interference_int) + noise_interference.get_noise_2d(wpos.x, wpos.y) * 0.05
			# Higher stability lowers interference (fewer signal-denial hazards).
			var interference: float = clamp(interference_raw * (1.0 - stability / 100.0 * 0.5), 0.0, 1.0)

			var elevation_raw: float = clamp(_radial_sum_arrays(wpos, elevation_pos, elevation_rad, elevation_int) + 0.05 + noise_elevation.get_noise_2d(wpos.x, wpos.y) * 0.06, 0.0, 1.0)
			elevation_raw *= (1.0 - water * 0.9)
			var elevation: float = _terrace(clamp(elevation_raw, 0.0, 1.0))

			var za: float = noise_zone_a.get_noise_2d(wpos.x, wpos.y) * 0.5 + 0.5
			var zb: float = noise_zone_b.get_noise_2d(wpos.x, wpos.y) * 0.5 + 0.5
			var zc: float = noise_zone_c.get_noise_2d(wpos.x, wpos.y) * 0.5 + 0.5
			var zone := 0
			if zb >= za and zb >= zc:
				zone = 1
			elif zc >= za and zc >= zb:
				zone = 2

			var pop_radial: float = _radial_one(wpos, objective_pos, 5000.0, 1.0)
			var population: float = pop_radial * (1.0 - elevation * 0.5)
			if water > 0.5:
				population = 0.0
			population = clamp(population, 0.0, 1.0)

			var wealth: float = _radial_one(wpos, harbor_pos, 4000.0, 1.0) * (stability / 100.0)
			if water > 0.5:
				wealth = 0.0
			wealth = clamp(wealth, 0.0, 1.0)

			var district := 0
			if population >= 0.8:
				district = 4
			elif population >= 0.6:
				district = 3
			elif population >= 0.4:
				district = 2
			elif population >= 0.2:
				district = 1

			grid[idx] = {
				obstacle = obstacle,
				cover = cover,
				elevation = elevation,
				interference = interference,
				water = water,
				population = population,
				wealth = wealth,
				zone = zone,
				district = district,
			}
			elevation_flat[idx] = elevation
			water_flat[idx] = water
			district_flat[idx] = (1.0 if district >= 2 else 0.0)

	borders = []
	_append_borders(_march_squares(water_flat, dim, 0.5), "coast")
	for th in [0.125, 0.375, 0.625, 0.875]:
		_append_borders(_march_squares(elevation_flat, dim, th), "cliff")
	_append_borders(_march_squares(district_flat, dim, 0.5), "wall")

	crossings = []
	for bi in range(borders.size()):
		var border: Dictionary = borders[bi]
		var kind := ""
		match border.kind:
			"wall":
				kind = "gate"
			"coast":
				kind = "bridge"
			"cliff":
				kind = "pass"
		if kind == "":
			continue
		for cp in chokepoints:
			var res := _closest_point_on_polyline(cp, border.points)
			if res.distance <= 300.0:
				crossings.append({border_index = bi, point = res.point, kind = kind})

func compute_hash() -> int:
	var parts: Array = []
	for n in nodes:
		parts.append(n.type)
		parts.append(int(round(n.pos.x)))
		parts.append(int(round(n.pos.y)))
	for b in borders:
		parts.append(b.kind)
		var pts: Array = b.points
		var step: int = max(1, int(pts.size() / 8))
		var i := 0
		while i < pts.size():
			parts.append(int(round(pts[i].x)))
			parts.append(int(round(pts[i].y)))
			i += step
	var gstep := 10
	var i2 := 0
	while i2 < grid.size():
		var cell: Dictionary = grid[i2]
		parts.append(int(round(cell.obstacle * 1000.0)))
		parts.append(int(round(cell.cover * 1000.0)))
		parts.append(int(round(cell.elevation * 1000.0)))
		parts.append(int(round(cell.interference * 1000.0)))
		parts.append(int(round(cell.water * 1000.0)))
		parts.append(int(round(cell.population * 1000.0)))
		parts.append(int(round(cell.wealth * 1000.0)))
		parts.append(cell.zone)
		parts.append(cell.district)
		i2 += gstep
	return hash(parts)

func _make_noise(seed_val: int, freq: float) -> FastNoiseLite:
	var n := FastNoiseLite.new()
	n.seed = seed_val
	n.noise_type = FastNoiseLite.TYPE_VALUE
	n.frequency = freq
	return n

func _build_nodes() -> Array:
	# Base position_ratio values (fraction of canvas, x,y in [0,1]) before jitter.
	# Coast runs along the south edge (y -> 1.0); hill/vantage sits north (y -> 0.0);
	# the river runs from near the hill down to the coast, bending past the objective.
	# objective         (0.50, 0.62)  city core on a rise inside the river bend
	# staging           (0.72, 0.55)  farmland side
	# staging           (0.78, 0.68)  farmland side
	# chokepoint        (0.50, 0.50)  wall meets the north land approach
	# chokepoint        (0.30, 0.62)  wall meets the west land approach
	# chokepoint        (0.52, 0.72)  river bridge chokepoint
	# flank_route       (0.75, 0.15)  route around the east shoulder of the hill
	# vantage           (0.50, 0.08)  hilltop
	# hazard_anchor     (0.75, 0.88)  marsh, southeast, off the river mouth
	# spawn_point       (0.25, 0.10)  far side from the objective, near the hill
	# spawn_point       (0.75, 0.10)  far side from the objective, near the hill
	# extraction        (0.30, 0.97)  coast, west of the river mouth
	# (no transit node in this hand-authored skeleton; transit remains a valid node type)
	var base: Array = [
		{type = "objective", ratio = Vector2(0.50, 0.62)},
		{type = "staging", ratio = Vector2(0.72, 0.55)},
		{type = "staging", ratio = Vector2(0.78, 0.68)},
		{type = "chokepoint", ratio = Vector2(0.50, 0.50)},
		{type = "chokepoint", ratio = Vector2(0.30, 0.62)},
		{type = "chokepoint", ratio = Vector2(0.52, 0.72)},
		{type = "flank_route", ratio = Vector2(0.75, 0.15)},
		{type = "vantage", ratio = Vector2(0.50, 0.08)},
		{type = "hazard_anchor", ratio = Vector2(0.75, 0.88)},
		{type = "spawn_point", ratio = Vector2(0.25, 0.10)},
		{type = "spawn_point", ratio = Vector2(0.75, 0.10)},
		{type = "extraction", ratio = Vector2(0.30, 0.97)},
	]
	var result: Array = []
	for entry in base:
		var jitter := Vector2(_rng.randf_range(-0.03, 0.03), _rng.randf_range(-0.03, 0.03))
		var ratio: Vector2 = (entry.ratio + jitter).clamp(Vector2.ZERO, Vector2.ONE)
		result.append({type = entry.type, pos = ratio * canvas})
	return result

func _build_river() -> PackedVector2Array:
	# River control points (position_ratio), from near the hill down to the coast,
	# bending past the objective's river bend:
	# (0.58,0.10) (0.62,0.25) (0.58,0.40) (0.50,0.50) (0.45,0.60) (0.52,0.68) (0.50,0.80) (0.46,0.92) (0.44,1.00)
	var base_ratios: Array = [
		Vector2(0.58, 0.10), Vector2(0.62, 0.25), Vector2(0.58, 0.40),
		Vector2(0.50, 0.50), Vector2(0.45, 0.60), Vector2(0.52, 0.68),
		Vector2(0.50, 0.80), Vector2(0.46, 0.92), Vector2(0.44, 1.00),
	]
	var points := PackedVector2Array()
	for r in base_ratios:
		var jitter := Vector2(_rng.randf_range(-0.02, 0.02), _rng.randf_range(-0.02, 0.02))
		var ratio: Vector2 = (r + jitter).clamp(Vector2.ZERO, Vector2.ONE)
		points.append(ratio * canvas)
	return points

func _find_node(t: String) -> Vector2:
	for n in nodes:
		if n.type == t:
			return n.pos
	return Vector2.ZERO

func _find_nodes(t: String) -> Array:
	var result: Array = []
	for n in nodes:
		if n.type == t:
			result.append(n.pos)
	return result

func _radial_contribution(pos: Vector2, source: Dictionary) -> float:
	var d: float = pos.distance_to(source.pos)
	var t: float = clamp(1.0 - d / source.radius, 0.0, 1.0)
	return source.intensity * smoothstep(0.0, 1.0, t)

func _radial_sum_arrays(pos: Vector2, positions: PackedVector2Array, radii: PackedFloat32Array, intensities: PackedFloat32Array) -> float:
	var total := 0.0
	for i in range(positions.size()):
		var d: float = pos.distance_to(positions[i])
		var t: float = clamp(1.0 - d / radii[i], 0.0, 1.0)
		total += intensities[i] * smoothstep(0.0, 1.0, t)
	return total

func _radial_one(pos: Vector2, source_pos: Vector2, radius: float, intensity: float) -> float:
	return _radial_contribution(pos, {pos = source_pos, radius = radius, intensity = intensity})

# Water convention: signed distance field, negative = water. water[cell] in [0,1] is a
# smoothed step of that SDF: 0.0 = fully dry, 1.0 = deep water, 0.5 = the shoreline
# (the isoline the coast border is traced from).
func _sample_water(pos: Vector2, river_points: PackedVector2Array) -> float:
	var coast_line_y: float = 0.90 * canvas
	var coast_sdf: float = coast_line_y - pos.y
	var river_sdf: float = _distance_to_polyline(pos, river_points) - 180.0
	var sdf: float = min(coast_sdf, river_sdf)
	var transition := 300.0
	return clamp(smoothstep(-transition, transition, -sdf), 0.0, 1.0)

func _distance_to_polyline(p: Vector2, points: PackedVector2Array) -> float:
	var best := INF
	for i in range(points.size() - 1):
		var d := _dist_to_segment(p, points[i], points[i + 1])
		if d < best:
			best = d
	return best

func _dist_to_segment(p: Vector2, a: Vector2, b: Vector2) -> float:
	var ab := b - a
	var len_sq := ab.length_squared()
	var t := 0.0
	if len_sq > 0.0:
		t = clamp((p - a).dot(ab) / len_sq, 0.0, 1.0)
	return p.distance_to(a + ab * t)

func _closest_point_on_polyline(p: Vector2, points: Array) -> Dictionary:
	var best_d := INF
	var best_p := Vector2.ZERO
	for i in range(points.size() - 1):
		var res := _closest_on_segment(p, points[i], points[i + 1])
		if res.distance < best_d:
			best_d = res.distance
			best_p = res.point
	return {distance = best_d, point = best_p}

func _closest_on_segment(p: Vector2, a: Vector2, b: Vector2) -> Dictionary:
	var ab := b - a
	var len_sq := ab.length_squared()
	var t := 0.0
	if len_sq > 0.0:
		t = clamp((p - a).dot(ab) / len_sq, 0.0, 1.0)
	var proj := a + ab * t
	return {distance = p.distance_to(proj), point = proj}

# Elevation terracing: quantized into 5 levels (0..4). Each level is a bench with a gentle
# continuous slope (bench_slope) across most of its span, then a steep smoothstep cliff
# ramp in the last `edge` fraction of the span up into the next level, so the transition
# is continuous but reads as a cliff rather than a hard floor() step.
func _terrace(raw: float) -> float:
	var levels := 4.0
	var edge := 0.18
	var bench_slope := 0.15
	var scaled: float = clamp(raw, 0.0, 0.999999) * (levels + 1.0)
	var level: float = floor(scaled)
	var frac: float = scaled - level
	var gentle: float = frac * bench_slope
	var cliff: float = smoothstep(1.0 - edge, 1.0, frac) * (1.0 - bench_slope)
	var terraced: float = clamp(level + gentle + cliff, 0.0, levels)
	return terraced / levels

func _edge_t(va: float, vb: float, threshold: float) -> float:
	if is_equal_approx(va, vb):
		return 0.5
	return clamp((threshold - va) / (vb - va), 0.0, 1.0)

func _march_squares(values: PackedFloat32Array, d: int, threshold: float) -> Array:
	var segments: Array = []
	for gy in range(d - 1):
		for gx in range(d - 1):
			var v00: float = values[gy * d + gx]
			var v10: float = values[gy * d + gx + 1]
			var v11: float = values[(gy + 1) * d + gx + 1]
			var v01: float = values[(gy + 1) * d + gx]
			var case_index := 0
			if v00 >= threshold:
				case_index |= 1
			if v10 >= threshold:
				case_index |= 2
			if v11 >= threshold:
				case_index |= 4
			if v01 >= threshold:
				case_index |= 8
			if case_index == 0 or case_index == 15:
				continue
			var p00 := Vector2(gx, gy) * SPACING
			var p10 := Vector2(gx + 1, gy) * SPACING
			var p11 := Vector2(gx + 1, gy + 1) * SPACING
			var p01 := Vector2(gx, gy + 1) * SPACING
			var bottom: Vector2 = p00.lerp(p10, _edge_t(v00, v10, threshold))
			var right: Vector2 = p10.lerp(p11, _edge_t(v10, v11, threshold))
			var top: Vector2 = p01.lerp(p11, _edge_t(v01, v11, threshold))
			var left: Vector2 = p00.lerp(p01, _edge_t(v00, v01, threshold))
			match case_index:
				1, 14:
					segments.append([left, bottom])
				2, 13:
					segments.append([bottom, right])
				3, 12:
					segments.append([left, right])
				4, 11:
					segments.append([right, top])
				6, 9:
					segments.append([bottom, top])
				7, 8:
					segments.append([left, top])
				5:
					var avg: float = (v00 + v10 + v11 + v01) * 0.25
					if avg >= threshold:
						segments.append([left, top])
						segments.append([bottom, right])
					else:
						segments.append([left, bottom])
						segments.append([right, top])
				10:
					var avg2: float = (v00 + v10 + v11 + v01) * 0.25
					if avg2 >= threshold:
						segments.append([left, bottom])
						segments.append([right, top])
					else:
						segments.append([left, top])
						segments.append([bottom, right])
	return _stitch_segments(segments)

func _stitch_segments(segments: Array) -> Array:
	var key_of := func(p: Vector2) -> String:
		return "%d_%d" % [int(round(p.x * 10.0)), int(round(p.y * 10.0))]
	var endpoint_map := {}
	for i in range(segments.size()):
		for end in [0, 1]:
			var k: String = key_of.call(segments[i][end])
			if not endpoint_map.has(k):
				endpoint_map[k] = []
			endpoint_map[k].append([i, end])
	var used := {}
	var polylines: Array = []
	for i in range(segments.size()):
		if used.has(i):
			continue
		used[i] = true
		var chain: Array = [segments[i][0], segments[i][1]]
		var extended := true
		while extended:
			extended = false
			var tail_key: String = key_of.call(chain[chain.size() - 1])
			for entry in endpoint_map.get(tail_key, []):
				var si: int = entry[0]
				if used.has(si):
					continue
				var other_end: int = 1 - entry[1]
				chain.append(segments[si][other_end])
				used[si] = true
				extended = true
				break
		polylines.append(chain)
	return polylines

func _append_borders(polylines: Array, kind: String) -> void:
	for pl in polylines:
		if pl.size() >= 2:
			borders.append({kind = kind, points = pl})
