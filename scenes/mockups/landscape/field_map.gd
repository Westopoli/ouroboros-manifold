class_name FieldMap
extends RefCounted

const QaPlants := preload("res://scenes/mockups/_shared/qa_plants.gd")

const SPACING := 100.0
# Peaks 3000-5000wu per the brief. Elevation is stored continuous (world units, sea level
# 0) for placement and camera; only border tracing quantizes it.
const PEAK_HEIGHT_WU := 5000.0
# See also: tests/test_mockup_landscape_waterline.gd (Westley owns these three thresholds)
const DRAFT_LAKE_FILL_HEIGHT := 150.0
const DRAFT_RIVER_BAND := 150.0
const DRAFT_RIVER_MAX_GRADE := 20.0
const CITY_CORE_TARGET_ELEV_WU := 500.0
const CITY_REACH_WU := 4500.0

var canvas: float = 24000.0
var stability: float = 60.0
var dim: int = 0
var nodes: Array = []
# grid: flat Array of Dictionaries, index = gy * dim + gx, gx/gy in [0, dim-1].
# World position of a cell = Vector2(gx, gy) * SPACING.
# Each cell: {obstacle, cover, interference, water, population, wealth: float [0,1],
#             elevation: float world units (continuous, sea level 0, peaks ~PEAK_HEIGHT_WU),
#             slope: float [0,1] local steepness, zone: int 0..4, district: int 0..4}
var grid: Array = []
var borders: Array = []
var crossings: Array = []
# Each entry a PackedVector2Array of world-space points, highlands to the sea/a lake.
var rivers: Array = []

# Pass 4 (pass4_terrain.gd): landform shaping, minimum relief and benching are applied to the
# elevation right after _build_elevation; p4_info records what they did, p4 holds the analysis
# (set by pass4_ui.gd after generate).
var p4_landform: String = "seed"
var p4_min_relief: float = 2500.0
var p4_bench_override: float = -1.0
var p4_footprint: float = 300.0
var p4_ramps := true
var p4_detail_scale: float = 1.0
var p4_relief: float = 1.0
var p4_info: Dictionary = {}
var p4: Dictionary = {}
# Pass 5 (pass5_layout.gd): the chosen layout leads, the terrain obeys it. Null layout = off.
var p5_layout = null
var p5_react := true
var p5_narrow: float = 300.0
var p5_moderate: float = 600.0
var p5_info: Dictionary = {}
var p5_res: Dictionary = {}

var _rng := RandomNumberGenerator.new()


func generate(p_seed: int, p_canvas: float = 24000.0, p_stability: float = 60.0) -> void:
	canvas = p_canvas
	stability = clamp(60.0 if QaPlants.is_active("stability-noop") else p_stability, 0.0, 100.0)
	dim = int(canvas / SPACING) + 1
	_rng.seed = p_seed

	# FastNoiseLite frequency is ~1/wavelength: N/canvas gives N cycles across the whole
	# map. This was previously backwards (continent at 60/canvas -- 60 cycles, ~400wu
	# features -- was finer than "detail" at 40/canvas), confirmed by an actual screenshot
	# reading as a field of tight spikes rather than a few broad landmasses; numbers below
	# are the corrected ordering (continent broadest, hills medium, detail finest).
	var noise_continent := _make_noise(p_seed + 0, 1.5 / canvas)
	var noise_hills := _make_noise(p_seed + 1, 8.0 / canvas)
	var noise_detail := _make_noise(p_seed + 2, 40.0 / canvas)
	var noise_boundary := _make_noise(p_seed + 3, 14.0 / canvas)
	var noise_moisture := _make_noise(p_seed + 4, 20.0 / canvas)
	var noise_obstacle := _make_noise(p_seed + 5, 0.00035)
	var noise_cover := _make_noise(p_seed + 6, 0.00035)
	var noise_interference := _make_noise(p_seed + 7, 0.00040)

	var elevation := _build_elevation(noise_continent, noise_hills, noise_detail)
	if not QaPlants.is_active("flat-terrain"):
		var t_shape := Time.get_ticks_usec()
		elevation = Pass4Terrain.shape(self, elevation, p_seed)
		p4_info["shape_ms"] = (Time.get_ticks_usec() - t_shape) / 1000.0
	var slope := _build_slope(elevation)
	var water_result := _build_water(elevation)
	var water: PackedFloat32Array = water_result.water
	rivers = water_result.rivers
	var zone := _build_zone(elevation, water, noise_boundary, noise_moisture)

	var core_gxy := _find_city_core(elevation, slope, water)
	var core_pos := Vector2(core_gxy.x, core_gxy.y) * SPACING
	var pop_result := _build_population_district(core_pos, elevation, slope, water)
	var population_raw: PackedFloat32Array = pop_result.population
	var district: PackedFloat32Array = pop_result.district

	grid.resize(dim * dim)
	for gy in range(dim):
		for gx in range(dim):
			var idx := gy * dim + gx
			grid[idx] = {
				elevation = elevation[idx],
				slope = slope[idx],
				water = water[idx],
				zone = zone[idx],
				district = int(district[idx]),
				population = population_raw[idx],
				obstacle = 0.0,
				cover = 0.0,
				interference = 0.0,
				wealth = 0.0,
			}

	if p4_ramps and not QaPlants.is_active("flat-terrain"):
		Pass4Terrain.cut_ramps(self, elevation, Vector2(core_gxy.x, core_gxy.y))
	if p5_layout != null:
		Pass5Layout.prepare(self)
		if p5_react:
			Pass5Layout.react(self, elevation)

	borders = []
	_append_borders(_march_squares(water, dim, 0.5), "coast")
	# Tracing cliff borders on raw continuous elevation picks up every ripple of the detail
	# noise octave as a "cliff" (12,000+ tiny segments, measured) -- the brief's own fix:
	# quantize to the five terraces for border tracing only, keep the mesh/placement height
	# continuous. Terracing flattens most of the terrain into wide flat bands so only real
	# level changes produce a contour.
	# Terracing alone still flickers across a threshold wherever the detail-noise octave's
	# high-frequency texture crosses it (13,000+ segments, measured) -- cliffs should read
	# macro terrain structure, not surface texture. A small box blur removes that
	# salt-and-pepper noise before tracing without touching the mesh/placement elevation.
	var terraced := _blur(_build_terrace_bands(elevation), dim, 2)
	for frac in [0.20, 0.42, 0.64, 0.86]:
		_append_borders(_march_squares(terraced, dim, frac), "cliff")
	var district_flat := PackedFloat32Array()
	district_flat.resize(dim * dim)
	for i in range(district.size()):
		district_flat[i] = 1.0 if district[i] >= 2.0 else 0.0
	_append_borders(_march_squares(district_flat, dim, 0.5), "wall")

	nodes = [{type = "objective", pos = core_pos}]
	var vantage_pos := _find_vantage(core_pos, elevation)
	nodes.append({type = "vantage", pos = vantage_pos})

	var wall_points := _points_of_kind("wall")
	var coast_points := _points_of_kind("coast")
	var cliff_points := _points_of_kind("cliff")

	var approach_dirs := _find_approach_directions(core_pos, wall_points)
	var gate_a := _nearest_point(wall_points, core_pos + approach_dirs[0] * CITY_REACH_WU * 0.6, core_pos)
	var gate_b := _nearest_point(wall_points, core_pos + approach_dirs[1] * CITY_REACH_WU * 0.6, core_pos)
	var bridge_pt := _nearest_point(coast_points, core_pos, core_pos)
	var pass_pt := _nearest_point(cliff_points, vantage_pos, core_pos)
	for p in [gate_a, gate_b, bridge_pt, pass_pt]:
		nodes.append({type = "chokepoint", pos = p})

	nodes.append({type = "flank_route", pos = core_pos + approach_dirs[0].rotated(0.6) * CITY_REACH_WU})
	nodes.append({type = "staging", pos = gate_a + approach_dirs[0] * 1200.0})
	nodes.append({type = "staging", pos = gate_b + approach_dirs[1] * 1200.0})
	nodes.append({type = "hazard_anchor", pos = _find_hazard_anchor(elevation, slope, water, core_pos)})
	var spawn_dir: Vector2 = -((approach_dirs[0] + approach_dirs[1]).normalized())
	if spawn_dir.length() < 0.1:
		spawn_dir = approach_dirs[0].rotated(PI * 0.5)
	nodes.append({type = "spawn_point", pos = core_pos + spawn_dir.rotated(0.3) * CITY_REACH_WU * 1.8})
	nodes.append({type = "spawn_point", pos = core_pos + spawn_dir.rotated(-0.3) * CITY_REACH_WU * 1.8})
	nodes.append({type = "extraction", pos = _find_extraction(core_pos, water)})
	for n in nodes:
		n.pos = n.pos.clamp(Vector2.ZERO, Vector2.ONE * canvas)

	var chokepoints: Array = _find_nodes("chokepoint")
	var hazard_pos: Vector2 = _find_node("hazard_anchor")

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

	var interference_pos := PackedVector2Array([hazard_pos])
	var interference_rad := PackedFloat32Array([500.0])
	var interference_int := PackedFloat32Array([0.75])
	if chokepoints.size() > 2:
		interference_pos.append(chokepoints[2])
		interference_rad.append(400.0)
		interference_int.append(0.20)

	var harbor_pos: Vector2 = _find_node("extraction")

	for gy in range(dim):
		for gx in range(dim):
			var idx := gy * dim + gx
			var wpos := Vector2(gx * SPACING, gy * SPACING)
			var cell: Dictionary = grid[idx]

			var obstacle: float = clamp(_radial_sum_arrays(wpos, obstacle_pos, obstacle_rad, obstacle_int) + noise_obstacle.get_noise_2d(wpos.x, wpos.y) * 0.06 + cell.slope * 0.5, 0.0, 1.0)

			var cover_raw: float = _radial_sum_arrays(wpos, cover_pos, cover_rad, cover_int) + noise_cover.get_noise_2d(wpos.x, wpos.y) * 0.06
			if cell.zone == 1 or cell.zone == 2:
				cover_raw += 0.2
			var cover: float = clamp(cover_raw + (stability / 100.0 - 0.5) * 0.6, 0.0, 1.0)

			var interference_raw: float = _radial_sum_arrays(wpos, interference_pos, interference_rad, interference_int) + noise_interference.get_noise_2d(wpos.x, wpos.y) * 0.05
			if cell.zone == 3:
				interference_raw += 0.2
			var interference: float = clamp(interference_raw * (1.0 - stability / 100.0 * 0.7), 0.0, 1.0)

			var wealth: float = _radial_one(wpos, harbor_pos, 4000.0, 1.0) * (stability / 100.0)
			if cell.water > 0.5:
				wealth = 0.0
			wealth = clamp(wealth, 0.0, 1.0)

			cell.obstacle = obstacle
			cell.cover = cover
			cell.interference = interference
			cell.wealth = wealth

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
	for r in rivers:
		var rp: PackedVector2Array = r
		if rp.size() > 0:
			parts.append(int(round(rp[0].x)))
			parts.append(int(round(rp[rp.size() - 1].y)))
	var gstep := 10
	var i2 := 0
	while i2 < grid.size():
		var cell: Dictionary = grid[i2]
		parts.append(int(round(cell.obstacle * 1000.0)))
		parts.append(int(round(cell.cover * 1000.0)))
		parts.append(int(round(cell.elevation * 10.0)))
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


# Three octaves (continent/hills/detail) summed, then RE-NORMALIZED against this specific
# generation's own min/max so peaks land in the brief's 3000-5000wu window every seed,
# regardless of how the weighted noise sum happens to statistically distribute (a first
# attempt shaped the raw noise with a power curve before scaling and it silently crushed
# every peak to ~2100wu -- pow(x,1.4) on x in [0,1] shrinks values, it doesn't stretch them;
# caught by checking the actual min/max after generating, not by inspection). A south-edge
# bias guarantees a coast on at least one edge every seed; a mild power curve on the
# normalized [0,1] fraction (applied after normalization, in the direction that actually
# concentrates height near the top) gives peaks a pointed rather than plateaued profile.
func _build_elevation(noise_continent: FastNoiseLite, noise_hills: FastNoiseLite, noise_detail: FastNoiseLite) -> PackedFloat32Array:
	var raw := PackedFloat32Array()
	raw.resize(dim * dim)
	var min_raw := INF
	var max_raw := -INF
	# Only continent+hills feed the normalized macro shape. Detail was folded into the same
	# normalized signal in a first attempt and, once that signal was rescaled to reach
	# dramatic 3000-5000wu peaks, its amplitude scaled right along with it -- confirmed by
	# actually looking at a render: the terrain read as a field of giant jagged spikes, not
	# rolling texture, because a noise octave meant to be a small ripple was rescaled to
	# thousands of world units of amplitude. Detail is added below in fixed, absolute wu
	# instead, decoupled from peak height.
	for gy in range(dim):
		for gx in range(dim):
			var wpos := Vector2(gx * SPACING, gy * SPACING)
			var n := noise_continent.get_noise_2d(wpos.x, wpos.y) * 0.7 \
				+ noise_hills.get_noise_2d(wpos.x, wpos.y) * 0.3
			raw[gy * dim + gx] = n
			min_raw = min(min_raw, n)
			max_raw = max(max_raw, n)

	var peak_target: float = PEAK_HEIGHT_WU * _rng.randf_range(0.6, 1.0)
	var sea_depth_target: float = -PEAK_HEIGHT_WU * 0.3
	var detail_amplitude_wu := 80.0 * p4_detail_scale

	var out := PackedFloat32Array()
	out.resize(dim * dim)
	for gy in range(dim):
		for gx in range(dim):
			var idx := gy * dim + gx
			var n: float = raw[idx]
			var h := 0.0
			if n >= 0.0 and max_raw > 0.0:
				h = pow(n / max_raw, 1.3) * peak_target * p4_relief
			elif n < 0.0 and min_raw < 0.0:
				h = (n / min_raw) * sea_depth_target
			var wpos := Vector2(gx * SPACING, gy * SPACING)
			h += noise_detail.get_noise_2d(wpos.x, wpos.y) * detail_amplitude_wu
			var edge_bias: float = smoothstep(canvas * 0.72, canvas, wpos.y) * -(peak_target * 0.5 + 800.0)
			out[idx] = (h + edge_bias) * (0.05 if QaPlants.is_active("flat-terrain") else 1.0)
	return out


# Quantized 0..1 terrace classification used only for cliff border tracing (see the call
# site's comment). Same gentle-bench-then-steep-cliff shape as the pre-pass-3 mockup's
# terracing, just no longer the mesh/placement height itself.
func _build_terrace_bands(elevation: PackedFloat32Array) -> PackedFloat32Array:
	var out := PackedFloat32Array()
	out.resize(elevation.size())
	var levels := 4.0
	var edge := 0.18
	var bench_slope := 0.15
	for i in range(elevation.size()):
		var raw: float = clamp(elevation[i] / PEAK_HEIGHT_WU, 0.0, 0.999999)
		var scaled: float = raw * (levels + 1.0)
		var level: float = floor(scaled)
		var frac: float = scaled - level
		var gentle: float = frac * bench_slope
		var cliff: float = smoothstep(1.0 - edge, 1.0, frac) * (1.0 - bench_slope)
		out[i] = clamp(level + gentle + cliff, 0.0, levels) / levels
	return out


func _blur(values: PackedFloat32Array, d: int, radius: int) -> PackedFloat32Array:
	var out := PackedFloat32Array()
	out.resize(values.size())
	for gy in range(d):
		for gx in range(d):
			var sum := 0.0
			var count := 0
			for oy in range(-radius, radius + 1):
				for ox in range(-radius, radius + 1):
					var nx := gx + ox
					var ny := gy + oy
					if nx < 0 or nx >= d or ny < 0 or ny >= d:
						continue
					sum += values[ny * d + nx]
					count += 1
			out[gy * d + gx] = sum / count
	return out


func _build_slope(elevation: PackedFloat32Array) -> PackedFloat32Array:
	var out := PackedFloat32Array()
	out.resize(dim * dim)
	# Normalized against a reference slope of one full terrace band per two grid cells;
	# steeper than that reads as fully "slope = 1" for gameplay/placement purposes.
	var reference: float = (PEAK_HEIGHT_WU * 0.25) / (SPACING * 2.0)
	for gy in range(dim):
		for gx in range(dim):
			var idx := gy * dim + gx
			var h := elevation[idx]
			var sum := 0.0
			var count := 0
			if gx > 0:
				sum += abs(h - elevation[idx - 1]); count += 1
			if gx < dim - 1:
				sum += abs(h - elevation[idx + 1]); count += 1
			if gy > 0:
				sum += abs(h - elevation[idx - dim]); count += 1
			if gy < dim - 1:
				sum += abs(h - elevation[idx + dim]); count += 1
			var avg: float = (sum / count) / SPACING if count > 0 else 0.0
			out[idx] = clamp(avg / reference, 0.0, 1.0)
	return out


# Sea from elevation<0, a handful of bounded-flood lakes in local basins above sea level, and
# 2-4 rivers traced downhill by steepest descent from high sources to the sea or a lake.
# Lake detection is a cheap local-minimum + bounded flood, not a real watershed transform --
# adequate for a mockup canvas, documented as a simplification in the report.
func _build_water(elevation: PackedFloat32Array) -> Dictionary:
	var water := PackedFloat32Array()
	water.resize(dim * dim)
	for i in range(water.size()):
		water[i] = smoothstep(60.0, -60.0, elevation[i])

	var lake_seeds := _find_lake_seeds(elevation)
	for seed_idx in lake_seeds:
		_flood_lake(elevation, water, seed_idx)

	var rivers_out: Array = []
	var sources := _find_river_sources(elevation)
	for src in sources:
		var path := _trace_river(elevation, water, src)
		if path.size() >= 2:
			rivers_out.append(path)
			_stamp_river(elevation, water, path)
	return {water = water, rivers = rivers_out}


func _find_lake_seeds(elevation: PackedFloat32Array) -> Array:
	var seeds: Array = []
	var step := 6
	for gy in range(step, dim - step, step):
		for gx in range(step, dim - step, step):
			var idx := gy * dim + gx
			var h := elevation[idx]
			if h <= 0.0 or h > PEAK_HEIGHT_WU * 0.18:
				continue
			var is_min := true
			for oy in range(-1, 2):
				for ox in range(-1, 2):
					if ox == 0 and oy == 0:
						continue
					var nidx := (gy + oy) * dim + (gx + ox)
					if elevation[nidx] < h:
						is_min = false
						break
				if not is_min:
					break
			if is_min:
				seeds.append(idx)
	return seeds


func _flood_lake(elevation: PackedFloat32Array, water: PackedFloat32Array, seed_idx: int) -> void:
	# Replaces a depth-first walk capped at 1,500 cells: the cap cut lakes off at arbitrary cells
	# and made the every-second-column stripes (FINDING-landscape-lakefill-stripes).
	var fill_level: float = elevation[seed_idx] + DRAFT_LAKE_FILL_HEIGHT
	var visited := {}
	var queue: Array = [seed_idx]
	var head := 0
	visited[seed_idx] = true
	var lake_offsets: Array[Vector2i] = [Vector2i(-1, 0), Vector2i(1, 0), Vector2i(0, -1), Vector2i(0, 1)]
	while head < queue.size():
		var idx: int = queue[head]
		head += 1
		if elevation[idx] > fill_level:
			continue
		water[idx] = max(water[idx], 1.0)
		var gy := idx / dim
		var gx := idx % dim
		for offset in lake_offsets:
			var nx: int = gx + offset.x
			var ny: int = gy + offset.y
			if nx < 0 or nx >= dim or ny < 0 or ny >= dim:
				continue
			var nidx := ny * dim + nx
			if not visited.has(nidx) and elevation[nidx] <= fill_level:
				visited[nidx] = true
				queue.append(nidx)


func _find_river_sources(elevation: PackedFloat32Array) -> Array:
	var candidates: Array = []
	var step := 8
	for gy in range(step, dim - step, step):
		for gx in range(step, dim - step, step):
			var idx := gy * dim + gx
			if elevation[idx] > PEAK_HEIGHT_WU * 0.55:
				candidates.append(idx)
	candidates.sort_custom(func(a, b): return elevation[a] > elevation[b])
	var sources: Array = []
	var min_dist: float = canvas * 0.18
	var count: int = 2 + _rng.randi_range(0, 2)
	for idx in candidates:
		if sources.size() >= count:
			break
		var gy: int = idx / dim
		var gx: int = idx % dim
		var pos := Vector2(gx, gy) * SPACING
		var far_enough := true
		for s in sources:
			if pos.distance_to(Vector2(s % dim, s / dim) * SPACING) < min_dist:
				far_enough = false
				break
		if far_enough:
			sources.append(idx)
	return sources


func _trace_river(elevation: PackedFloat32Array, water: PackedFloat32Array, start_idx: int) -> PackedVector2Array:
	var path := PackedVector2Array()
	var gx := start_idx % dim
	var gy := start_idx / dim
	path.append(Vector2(gx, gy) * SPACING)
	var max_steps: int = dim * 3
	for _step in range(max_steps):
		var idx := gy * dim + gx
		if water[idx] > 0.5:
			return path
		var step_result := _river_step(elevation, gx, gy)
		if step_result.x == gx and step_result.y == gy:
			break
		gx = step_result.x
		gy = step_result.y
		path.append(Vector2(gx, gy) * SPACING)
	# Steepest descent on noisy terrain can stall in a shallow local dip well short of real
	# water (a proper watershed/depression-fill is out of scope for this mockup); guarantee
	# the "every river ends at sea or a lake" invariant by extending the last point straight
	# to the nearest actual water cell rather than leaving the river stranded inland.
	var nearest := _nearest_water_cell(water, gx, gy)
	if nearest != Vector2i(gx, gy):
		path.append(Vector2(nearest.x, nearest.y) * SPACING)
	return path


# Immediate 8-neighbors first; if none are lower (a shallow pit), widen the search radius
# so the path can hop over small local dips instead of stalling on them.
func _river_step(elevation: PackedFloat32Array, gx: int, gy: int) -> Vector2i:
	var idx := gy * dim + gx
	for radius in [1, 2, 3, 4]:
		var best_h: float = elevation[idx]
		var best := Vector2i(gx, gy)
		for oy in range(-radius, radius + 1):
			for ox in range(-radius, radius + 1):
				if ox == 0 and oy == 0:
					continue
				var nx := gx + ox
				var ny := gy + oy
				if nx < 0 or nx >= dim or ny < 0 or ny >= dim:
					continue
				var nh: float = elevation[ny * dim + nx]
				if nh < best_h:
					best_h = nh
					best = Vector2i(nx, ny)
		if best != Vector2i(gx, gy):
			return best
	return Vector2i(gx, gy)


func _nearest_water_cell(water: PackedFloat32Array, gx: int, gy: int) -> Vector2i:
	var best_d := INF
	var best := Vector2i(gx, gy)
	for idx in range(water.size()):
		if water[idx] <= 0.5:
			continue
		var wx := idx % dim
		var wy := idx / dim
		var d: float = Vector2(wx - gx, wy - gy).length()
		if d < best_d:
			best_d = d
			best = Vector2i(wx, wy)
	return best


func _stamp_river(elevation: PackedFloat32Array, water: PackedFloat32Array, path: PackedVector2Array) -> void:
	for i in range(path.size()):
		var t: float = float(i) / float(max(1, path.size() - 1))
		var width: float = lerp(50.0, 220.0, t)
		var p: Vector2 = path[i]
		var reach: int = int(ceil(width / SPACING)) + 1
		var gx := int(round(p.x / SPACING))
		var gy := int(round(p.y / SPACING))
		var pidx := clampi(gy, 0, dim - 1) * dim + clampi(gx, 0, dim - 1)
		if _local_grade_deg(elevation, pidx) > DRAFT_RIVER_MAX_GRADE:
			continue
		var ceiling: float = elevation[pidx] + DRAFT_RIVER_BAND
		for oy in range(-reach, reach + 1):
			for ox in range(-reach, reach + 1):
				var nx := gx + ox
				var ny := gy + oy
				if nx < 0 or nx >= dim or ny < 0 or ny >= dim:
					continue
				var cell_pos := Vector2(nx, ny) * SPACING
				var d := cell_pos.distance_to(p)
				var idx := ny * dim + nx
				if elevation[idx] > ceiling:
					continue
				water[idx] = max(water[idx], smoothstep(width, width * 0.4, d))


# Local grade in degrees: atan of the largest drop from the cell to any of its 8 neighbours,
# divided by the neighbour distance in wu (SPACING, or SPACING * sqrt(2) on a diagonal).
func _local_grade_deg(elevation: PackedFloat32Array, idx: int) -> float:
	var gx := idx % dim
	var gy := idx / dim
	var best := 0.0
	for oy in range(-1, 2):
		for ox in range(-1, 2):
			if ox == 0 and oy == 0:
				continue
			var nx := gx + ox
			var ny := gy + oy
			if nx < 0 or nx >= dim or ny < 0 or ny >= dim:
				continue
			var run: float = SPACING * (1.41421356 if ox != 0 and oy != 0 else 1.0)
			best = max(best, (elevation[idx] - elevation[ny * dim + nx]) / run)
	return rad_to_deg(atan(best))


# Zones (still zone_a..e in code; a kit names them) come from perturbed continuous elevation
# plus a cheap moisture proxy (distance to the nearest river sample or the south coast edge,
# not a true distance transform) so bands read as noise-separated regions, not elevation rings.
func _build_zone(elevation: PackedFloat32Array, water: PackedFloat32Array, noise_boundary: FastNoiseLite, noise_moisture: FastNoiseLite) -> PackedInt32Array:
	var out := PackedInt32Array()
	out.resize(dim * dim)
	for gy in range(dim):
		for gx in range(dim):
			var idx := gy * dim + gx
			var wpos := Vector2(gx * SPACING, gy * SPACING)
			var moisture_sea: float = 1.0 - clamp((canvas - wpos.y) / 7000.0, 0.0, 1.0)
			var moisture_river := 0.0
			for r in rivers:
				var rp: PackedVector2Array = r
				var d := _distance_to_polyline(wpos, rp)
				moisture_river = max(moisture_river, 1.0 - clamp(d / 1600.0, 0.0, 1.0))
			var moisture: float = clamp(max(moisture_sea, moisture_river) + noise_moisture.get_noise_2d(wpos.x, wpos.y) * 0.12, 0.0, 1.0)
			var latitude: float = wpos.y / canvas

			var perturbed: float = elevation[idx] + noise_boundary.get_noise_2d(wpos.x, wpos.y) * PEAK_HEIGHT_WU * 0.12 - (1.0 - latitude) * PEAK_HEIGHT_WU * 0.15

			var zone := 1
			if moisture > 0.55 and perturbed < PEAK_HEIGHT_WU * 0.12:
				zone = 0
			elif perturbed < PEAK_HEIGHT_WU * 0.30:
				zone = 1
			elif perturbed < PEAK_HEIGHT_WU * 0.55:
				zone = 2
			elif perturbed < PEAK_HEIGHT_WU * 0.80:
				zone = 3
			else:
				zone = 4
			out[idx] = zone
	return out


# Score every cell: near water but dry, flat, a habitable elevation, not hugging the edge.
# The city core is the argmax; a tiny per-seed jitter breaks exact ties deterministically.
func _find_city_core(elevation: PackedFloat32Array, slope: PackedFloat32Array, water: PackedFloat32Array) -> Vector2i:
	var best_score := -INF
	var best := Vector2i(dim / 2, dim / 2)
	var margin: int = int(dim * 0.12)
	# Picking a single representative point tolerates a coarse stride; a full per-cell scan
	# measured as a real contributor to a ~1.2s field_map generation at a 24000wu canvas.
	for gy in range(margin, dim - margin, 2):
		for gx in range(margin, dim - margin, 2):
			var idx := gy * dim + gx
			if water[idx] > 0.4:
				continue
			var water_score := 0.0
			for offset in [Vector2i(-4, 0), Vector2i(4, 0), Vector2i(0, -4), Vector2i(0, 4)]:
				var nx: int = clampi(gx + offset.x, 0, dim - 1)
				var ny: int = clampi(gy + offset.y, 0, dim - 1)
				water_score = max(water_score, water[ny * dim + nx])
			var flat_score: float = 1.0 - slope[idx]
			var elev_diff: float = abs(elevation[idx] - CITY_CORE_TARGET_ELEV_WU)
			var elev_score: float = clamp(1.0 - elev_diff / (PEAK_HEIGHT_WU * 0.4), 0.0, 1.0)
			var edge_dist: float = min(min(gx, dim - 1 - gx), min(gy, dim - 1 - gy)) / float(dim)
			var edge_score: float = clamp(edge_dist / 0.2, 0.0, 1.0)
			var score: float = water_score * 1.4 + flat_score * 1.0 + elev_score * 1.0 + edge_score * 0.6 + _rng.randf() * 0.01
			if score > best_score:
				best_score = score
				best = Vector2i(gx, gy)
	return best


# Population is radial falloff from the core, reshaped by slope (steep ground never
# populates) and water proximity (a bonus, so the city hugs a river or coast instead of
# spreading as a uniform ring) -- a cheap stand-in for a real cost-flood-fill that still
# directly answers "cities follow rivers/valleys, never a plain circle".
func _build_population_district(core_pos: Vector2, elevation: PackedFloat32Array, slope: PackedFloat32Array, water: PackedFloat32Array) -> Dictionary:
	var population := PackedFloat32Array()
	population.resize(dim * dim)
	var district := PackedFloat32Array()
	district.resize(dim * dim)
	for gy in range(dim):
		for gx in range(dim):
			var idx := gy * dim + gx
			var wpos := Vector2(gx * SPACING, gy * SPACING)
			var dist := wpos.distance_to(core_pos)
			var radial: float = clamp(1.0 - dist / CITY_REACH_WU, 0.0, 1.0)
			var slope_penalty: float = 1.0 - clamp(slope[idx] * 2.0, 0.0, 1.0)
			var water_bonus: float = 1.0 + clamp(water[idx] * 3.0, 0.0, 1.0) * 0.6 if water[idx] < 0.5 else 0.0
			var pop: float = radial if QaPlants.is_active("city-disc") else radial * slope_penalty * water_bonus
			if water[idx] > 0.5 and not QaPlants.is_active("city-disc"):
				pop = 0.0
			pop = clamp(pop, 0.0, 1.0)
			population[idx] = pop
			var d := 0
			if pop >= 0.8:
				d = 4
			elif pop >= 0.6:
				d = 3
			elif pop >= 0.4:
				d = 2
			elif pop >= 0.2:
				d = 1
			district[idx] = d
	return {population = population, district = district}


func _find_vantage(core_pos: Vector2, elevation: PackedFloat32Array) -> Vector2:
	var best_h := -INF
	var best := core_pos + Vector2(0, -CITY_REACH_WU)
	for gy in range(0, dim, 2):
		for gx in range(0, dim, 2):
			var wpos := Vector2(gx * SPACING, gy * SPACING)
			var d := wpos.distance_to(core_pos)
			if d < CITY_REACH_WU * 0.5 or d > CITY_REACH_WU * 2.2:
				continue
			var h: float = elevation[gy * dim + gx]
			if h > best_h:
				best_h = h
				best = wpos
	return best


func _find_hazard_anchor(elevation: PackedFloat32Array, slope: PackedFloat32Array, water: PackedFloat32Array, core_pos: Vector2) -> Vector2:
	var best_score := -INF
	var best := core_pos + Vector2(CITY_REACH_WU, CITY_REACH_WU)
	for gy in range(0, dim, 2):
		for gx in range(0, dim, 2):
			var idx := gy * dim + gx
			var wpos := Vector2(gx * SPACING, gy * SPACING)
			var d := wpos.distance_to(core_pos)
			if d < CITY_REACH_WU * 0.7:
				continue
			var marsh_score: float = (1.0 - slope[idx]) * (1.0 if elevation[idx] > -60.0 and elevation[idx] < 200.0 else 0.0) * (1.0 - water[idx])
			var highland_score: float = clamp(elevation[idx] / PEAK_HEIGHT_WU, 0.0, 1.0) * 0.5
			var score: float = max(marsh_score, highland_score)
			if score > best_score:
				best_score = score
				best = wpos
	return best


func _find_extraction(core_pos: Vector2, water: PackedFloat32Array) -> Vector2:
	var best_d := INF
	var best := core_pos + Vector2(0, CITY_REACH_WU * 2.0)
	for gy in range(0, dim, 2):
		for gx in range(0, dim, 2):
			var idx := gy * dim + gx
			if water[idx] < 0.4 or water[idx] > 0.9:
				continue
			var wpos := Vector2(gx * SPACING, gy * SPACING)
			var d := wpos.distance_to(core_pos)
			if d < best_d:
				best_d = d
				best = wpos
	return best


func _points_of_kind(kind: String) -> Array:
	var pts: Array = []
	for b in borders:
		if b.kind == kind:
			for p in b.points:
				pts.append(p)
	return pts


func _nearest_point(points: Array, target: Vector2, fallback: Vector2) -> Vector2:
	if points.is_empty():
		return fallback
	var best: Vector2 = points[0]
	var best_d: float = target.distance_to(best)
	for p in points:
		var d: float = target.distance_to(p)
		if d < best_d:
			best_d = d
			best = p
	return best


# Two outward approach directions from the core: the wall points closest to the core define
# the local wall normal at two roughly opposite sides, used to place gates and staging.
func _find_approach_directions(core_pos: Vector2, wall_points: Array) -> Array:
	if wall_points.size() < 2:
		return [Vector2(1, 0), Vector2(-1, 0)]
	var sorted_pts: Array = wall_points.duplicate()
	sorted_pts.sort_custom(func(a, b): return core_pos.distance_to(a) < core_pos.distance_to(b))
	var dir_a: Vector2 = (sorted_pts[0] - core_pos).normalized()
	var dir_b := dir_a
	for p in sorted_pts:
		var d: Vector2 = (p - core_pos).normalized()
		if d.dot(dir_a) < 0.2:
			dir_b = d
			break
	if dir_b.is_equal_approx(dir_a):
		dir_b = -dir_a
	return [dir_a, dir_b]


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
