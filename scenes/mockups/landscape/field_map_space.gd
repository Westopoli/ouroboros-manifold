class_name SpaceFieldMap
extends FieldMap

# Five open-or-blocked layers cut from one block of hand-written value noise. No engine noise,
# no random calls: the C simulation can copy this file line for line.
# See also: docs/northstar/plans/2026-10-02-space-kit-mode-spec.md

const LAYERS := 5
const LAYER_HEIGHT_WU := 1000.0
const CLEAR_RADIUS_WU := 600.0
const MIN_POCKET_CELLS := 40
const TUNNEL_HALF_WIDTH_CELLS := 1
const CROSSING_MARK_MAX_CELLS := 50
const HASH_MASK := 0xFFFFFFFF
const LAYER_SEED_STEP := 7919
# lattice cells across (canvas, canvas, 5 layers), and the octave's weight.
const OCTAVE_LATTICES: Array[Vector3i] = [Vector3i(5, 5, 2), Vector3i(14, 14, 4)]
const OCTAVE_WEIGHTS: Array[float] = [0.65, 0.35]

var density: float = 35.0
# masks[k]: PackedByteArray of dim * dim, 1 open, 0 blocked, k = 0..4 (layer k + 1).
var masks: Array = []
# Each {points: PackedVector2Array, layer: int (1-based)}.
var tunnels: Array = []
# Per layer {blocked, open}, shares 0..1.
var layer_stats: Array = []
var pockets_filled := 0
var tunnels_cut := 0
var regions_unreachable_after := 0
# Percent of cells open on layer k and k + 1, k = 0..3.
var crossing_pct: Array = []


func generate(p_seed: int, p_canvas: float = 24000.0, p_density: float = 35.0) -> void:
	canvas = p_canvas
	density = clamp(p_density, 0.0, 90.0)
	dim = int(canvas / SPACING) + 1
	var n := dim * dim
	var independent: bool = QaPlants.is_active("space-independent-layers")

	var samples := PackedFloat64Array()
	samples.resize(LAYERS * n)
	for k in range(LAYERS):
		var layer_seed := p_seed + k * LAYER_SEED_STEP if independent else p_seed
		_sample_layer(samples, k, layer_seed, independent)

	var threshold := -1.0
	if density > 0.0:
		var sorted := samples.duplicate()
		sorted.sort()
		threshold = sorted[min(int(floor(density / 100.0 * sorted.size())), sorted.size() - 1)]
	var open := PackedByteArray()
	open.resize(LAYERS * n)
	for i in range(LAYERS * n):
		open[i] = 0 if samples[i] <= threshold else 1

	_build_nodes()
	for node in nodes:
		_clear_around(open, node.pos)

	pockets_filled = 0
	tunnels_cut = 0
	tunnels = []
	var objective_cell := _cell_of(nodes[0].pos)
	var labelled := _label_regions(open, objective_cell)
	if not QaPlants.is_active("space-no-carve"):
		_fill_and_carve(open, labelled, objective_cell)
		labelled = _label_regions(open, objective_cell)
	regions_unreachable_after = labelled.sizes.size() - 1

	masks = []
	layer_stats = []
	for k in range(LAYERS):
		var mask := open.slice(k * n, (k + 1) * n)
		masks.append(mask)
		var open_count := 0
		for i in range(n):
			open_count += mask[i]
		layer_stats.append({blocked = float(n - open_count) / n, open = float(open_count) / n})

	_build_grid(open)
	_build_crossings(open)
	_build_borders()
	rivers = []


func compute_hash() -> int:
	var parts: Array = []
	for n in nodes:
		parts.append(n.type)
		parts.append(int(round(n.pos.x)))
		parts.append(int(round(n.pos.y)))
	for mask in masks:
		parts.append(hash(mask))
	for t in tunnels:
		var pts: PackedVector2Array = t.points
		parts.append(t.layer)
		parts.append(pts.size())
		parts.append(int(round(pts[0].x)))
		parts.append(int(round(pts[0].y)))
	return hash(parts)


func hash32(ix: int, iy: int, iz: int, p_seed: int) -> int:
	var h := (ix * 0x8da6b343) & HASH_MASK
	h ^= (iy * 0xd8163841) & HASH_MASK
	h ^= (iz * 0xcb1ab31f) & HASH_MASK
	h ^= p_seed & HASH_MASK
	h ^= h >> 13
	h = (h * 0x5bd1e995) & HASH_MASK
	h ^= h >> 15
	return h


# Samples layer k (0-based) into samples[k * dim * dim ...]. Trilinear value noise with
# smoothstep on every axis; the z blend is done once per lattice plane, which gives the same
# number as blending the eight corners per sample.
func _sample_layer(samples: PackedFloat64Array, k: int, layer_seed: int, independent: bool) -> void:
	var n := dim * dim
	for o in range(OCTAVE_LATTICES.size()):
		var lattice: Vector3i = OCTAVE_LATTICES[o]
		var weight: float = OCTAVE_WEIGHTS[o]
		var sx := lattice.x + 2
		var sy := lattice.y + 2

		var z := 0.5 if independent else (k + 0.5) / LAYERS * lattice.z
		var iz := int(floor(z))
		var tz := _smooth(z - iz)
		var plane := PackedFloat64Array()
		plane.resize(sx * sy)
		for iy in range(sy):
			for ix in range(sx):
				var v0 := hash32(ix, iy, iz, layer_seed) / 4294967296.0
				var v1 := hash32(ix, iy, iz + 1, layer_seed) / 4294967296.0
				plane[iy * sx + ix] = lerp(v0, v1, tz)

		var col_i := PackedInt32Array()
		var col_t := PackedFloat64Array()
		col_i.resize(dim)
		col_t.resize(dim)
		for gx in range(dim):
			var x := gx * SPACING / canvas * lattice.x
			var ix := int(floor(x))
			col_i[gx] = ix
			col_t[gx] = _smooth(x - ix)

		for gy in range(dim):
			var y := gy * SPACING / canvas * lattice.y
			var iy := int(floor(y))
			var ty := _smooth(y - iy)
			var row0 := iy * sx
			var row1 := row0 + sx
			var base := k * n + gy * dim
			for gx in range(dim):
				var ix := col_i[gx]
				var tx := col_t[gx]
				var top: float = lerp(plane[row0 + ix], plane[row0 + ix + 1], tx)
				var bottom: float = lerp(plane[row1 + ix], plane[row1 + ix + 1], tx)
				samples[base + gx] += weight * lerp(top, bottom, ty)


func _smooth(t: float) -> float:
	return t * t * (3.0 - 2.0 * t)


# The layout places the library keeps: objective, two spawns on the diagonal, a staging node
# 1,500 wu from each spawn toward the centre, and one vantage in the quarter farthest from both.
func _build_nodes() -> void:
	var centre := Vector2(canvas, canvas) * 0.5
	var spawns := [Vector2(canvas, canvas) * 0.15, Vector2(canvas, canvas) * 0.85]
	nodes = [{type = "objective", pos = centre}]
	for s in spawns:
		nodes.append({type = "spawn_point", pos = s})
	for s in spawns:
		nodes.append({type = "staging", pos = s + (centre - s).normalized() * 1500.0})
	var best_score := -INF
	var best := centre
	for q in [Vector2(0.25, 0.25), Vector2(0.75, 0.25), Vector2(0.25, 0.75), Vector2(0.75, 0.75)]:
		var pos: Vector2 = q * canvas
		var score: float = min(pos.distance_to(spawns[0]), pos.distance_to(spawns[1]))
		if score > best_score + 1.0:
			best_score = score
			best = pos
	nodes.append({type = "vantage", pos = best})
	for node in nodes:
		node.pos = node.pos.clamp(Vector2.ZERO, Vector2.ONE * canvas)


func _cell_of(pos: Vector2) -> Vector2i:
	return Vector2i(clampi(int(round(pos.x / SPACING)), 0, dim - 1), clampi(int(round(pos.y / SPACING)), 0, dim - 1))


func _clear_around(open: PackedByteArray, pos: Vector2) -> void:
	var n := dim * dim
	var reach := int(ceil(CLEAR_RADIUS_WU / SPACING))
	var centre := _cell_of(pos)
	for gy in range(max(0, centre.y - reach), min(dim, centre.y + reach + 1)):
		for gx in range(max(0, centre.x - reach), min(dim, centre.x + reach + 1)):
			if (Vector2(gx, gy) * SPACING).distance_to(pos) <= CLEAR_RADIUS_WU:
				for k in range(LAYERS):
					open[k * n + gy * dim + gx] = 1


# Six-neighbour flood fill over open cells (four in-plane, one above, one below). Returns
# labels per cell (-1 blocked), the size of each region, and each region's cell nearest the
# objective in plane distance (first found wins a tie).
func _label_regions(open: PackedByteArray, objective_cell: Vector2i) -> Dictionary:
	var n := dim * dim
	var labels := PackedInt32Array()
	labels.resize(LAYERS * n)
	labels.fill(-1)
	var sizes: Array = []
	var nearest: Array = []
	var stack: Array = []
	for start in range(LAYERS * n):
		if open[start] == 0 or labels[start] != -1:
			continue
		var id := sizes.size()
		labels[start] = id
		stack.append(start)
		var size := 0
		var best := start
		var best_d := 1 << 60
		while not stack.is_empty():
			var c: int = stack.pop_back()
			size += 1
			var k := c / n
			var p := c - k * n
			var gy := p / dim
			var gx := p - gy * dim
			var d := (gx - objective_cell.x) * (gx - objective_cell.x) + (gy - objective_cell.y) * (gy - objective_cell.y)
			if d < best_d:
				best_d = d
				best = c
			if gx > 0 and open[c - 1] == 1 and labels[c - 1] == -1:
				labels[c - 1] = id
				stack.append(c - 1)
			if gx < dim - 1 and open[c + 1] == 1 and labels[c + 1] == -1:
				labels[c + 1] = id
				stack.append(c + 1)
			if gy > 0 and open[c - dim] == 1 and labels[c - dim] == -1:
				labels[c - dim] = id
				stack.append(c - dim)
			if gy < dim - 1 and open[c + dim] == 1 and labels[c + dim] == -1:
				labels[c + dim] = id
				stack.append(c + dim)
			if k > 0 and open[c - n] == 1 and labels[c - n] == -1:
				labels[c - n] = id
				stack.append(c - n)
			if k < LAYERS - 1 and open[c + n] == 1 and labels[c + n] == -1:
				labels[c + n] = id
				stack.append(c + n)
		sizes.append(size)
		nearest.append(best)
	var main := labels[objective_cell.y * dim + objective_cell.x]
	return {labels = labels, sizes = sizes, nearest = nearest, main = main}


# Pockets under MIN_POCKET_CELLS are filled solid; larger ones get a tunnel on their own layer
# toward the objective's cell, cut as a Bresenham line TUNNEL_HALF_WIDTH_CELLS wide, ending at
# the first main-region cell it touches. The objective column is open on every layer (the
# clear radius), so every line ends.
func _fill_and_carve(open: PackedByteArray, labelled: Dictionary, objective_cell: Vector2i) -> void:
	var n := dim * dim
	var labels: PackedInt32Array = labelled.labels
	var sizes: Array = labelled.sizes
	var main: int = labelled.main
	var fill := PackedByteArray()
	fill.resize(sizes.size())
	for id in range(sizes.size()):
		if id != main and sizes[id] < MIN_POCKET_CELLS:
			fill[id] = 1
			pockets_filled += 1
	# Filled before any tunnel is cut, so a tunnel through a small pocket is not filled back in.
	if pockets_filled > 0:
		for i in range(LAYERS * n):
			if labels[i] >= 0 and fill[labels[i]] == 1:
				open[i] = 0
	for id in range(sizes.size()):
		if id == main or fill[id] == 1:
			continue
		var c: int = labelled.nearest[id]
		var k := c / n
		var p := c - k * n
		var x0 := p % dim
		var y0 := p / dim
		var dx: int = abs(objective_cell.x - x0)
		var dy: int = -abs(objective_cell.y - y0)
		var sx := 1 if x0 < objective_cell.x else -1
		var sy := 1 if y0 < objective_cell.y else -1
		var err := dx + dy
		var points := PackedVector2Array()
		while true:
			points.append(Vector2(x0, y0) * SPACING)
			var reached := false
			for oy in range(-TUNNEL_HALF_WIDTH_CELLS, TUNNEL_HALF_WIDTH_CELLS + 1):
				for ox in range(-TUNNEL_HALF_WIDTH_CELLS, TUNNEL_HALF_WIDTH_CELLS + 1):
					var nx := x0 + ox
					var ny := y0 + oy
					if nx < 0 or nx >= dim or ny < 0 or ny >= dim:
						continue
					var ci := k * n + ny * dim + nx
					if labels[ci] == main:
						reached = true
					open[ci] = 1
			if reached or (x0 == objective_cell.x and y0 == objective_cell.y):
				break
			var e2 := 2 * err
			if e2 >= dy:
				err += dy
				x0 += sx
			if e2 <= dx:
				err += dx
				y0 += sy
		tunnels.append({points = points, layer = k + 1})
		tunnels_cut += 1


func _build_grid(open: PackedByteArray) -> void:
	var n := dim * dim
	grid.resize(n)
	for i in range(n):
		var blocked := 0
		for k in range(LAYERS):
			blocked += 1 - open[k * n + i]
		grid[i] = {
			elevation = 0.0,
			slope = 0.0,
			water = 0.0,
			zone = 0,
			district = 0,
			population = 0.0,
			obstacle = float(blocked) / LAYERS,
			cover = 0.0,
			interference = 0.0,
			wealth = 0.0,
		}


# A crossing cell is open on layers k and k + 1. In-plane clusters of such cells that are small
# enough to be scarce get one mark at their centroid; bigger ones are obviously crossable.
func _build_crossings(open: PackedByteArray) -> void:
	var n := dim * dim
	crossings = []
	crossing_pct = []
	for k in range(LAYERS - 1):
		var both := PackedByteArray()
		both.resize(n)
		var count := 0
		for i in range(n):
			var v: int = open[k * n + i] & open[(k + 1) * n + i]
			both[i] = v
			count += v
		crossing_pct.append(100.0 * count / n)
		var seen := PackedByteArray()
		seen.resize(n)
		var stack: Array = []
		for start in range(n):
			if both[start] == 0 or seen[start] == 1:
				continue
			seen[start] = 1
			stack.append(start)
			var size := 0
			var sum := Vector2.ZERO
			while not stack.is_empty():
				var c: int = stack.pop_back()
				var gy := c / dim
				var gx := c - gy * dim
				size += 1
				sum += Vector2(gx, gy)
				if gx > 0 and both[c - 1] == 1 and seen[c - 1] == 0:
					seen[c - 1] = 1
					stack.append(c - 1)
				if gx < dim - 1 and both[c + 1] == 1 and seen[c + 1] == 0:
					seen[c + 1] = 1
					stack.append(c + 1)
				if gy > 0 and both[c - dim] == 1 and seen[c - dim] == 0:
					seen[c - dim] = 1
					stack.append(c - dim)
				if gy < dim - 1 and both[c + dim] == 1 and seen[c + dim] == 0:
					seen[c + dim] = 1
					stack.append(c + dim)
			if size <= CROSSING_MARK_MAX_CELLS:
				crossings.append({point = sum / size * SPACING, kind = "shaft", layer_from = k + 1, layer_to = k + 2})


func _build_borders() -> void:
	borders = []
	for k in range(LAYERS):
		var mask: PackedByteArray = masks[k]
		var values := PackedFloat32Array()
		values.resize(mask.size())
		for i in range(mask.size()):
			values[i] = mask[i]
		for pl in _march_squares(values, dim, 0.5):
			if pl.size() >= 2:
				borders.append({kind = "asteroid", layer = k + 1, points = pl})
