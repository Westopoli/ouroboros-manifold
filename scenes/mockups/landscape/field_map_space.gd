class_name SpaceFieldMap
extends FieldMap

# Five open-or-blocked layers, each a sheet of fractured plates (jittered-lattice Worley cells
# with narrow channels) from its own seed. No engine noise, no random calls: every random value is
# the hand-written hash below, so the C simulation can copy this file line for line.
# Pass 1's value-noise blobs stay reachable through the plant `space-noise-blobs`.
# See also: docs/northstar/plans/2026-10-02-space-kit-mode-spec.md

const LAYERS := 5
const LAYER_GAP_WU := 1400.0
const CLEAR_RADIUS_WU := 600.0
const MIN_POCKET_CELLS := 40
const TUNNEL_HALF_WIDTH_CELLS := 1
const CROSSING_MARK_MAX_CELLS := 50
const HASH_MASK := 0xFFFFFFFF
const LAYER_SEED_STEP := 7919
# lattice cells across (canvas, canvas, 5 layers), and the octave's weight.
const OCTAVE_LATTICES: Array[Vector3i] = [Vector3i(5, 5, 2), Vector3i(14, 14, 4)]
const OCTAVE_WEIGHTS: Array[float] = [0.65, 0.35]
# Pass 2 (plates). Hash channels: the iz argument of hash32 names what a value is for.
const PLATE_CELL_WU := 1600.0
const CHANNEL_WU := 160.0
const RUBBLE_CELL_WU := 400.0
const RUBBLE_CHANNEL_WU := 100.0
const RUBBLE_SHARE := 0.35
const SCALE_BASE := 0.6
const SCALE_SWING := 0.8
const DROP_SWING := 0.3
const MASS_CHANCE := 0.5
const MASS_RADIUS_WU := 2200.0
const ERODE_SHARE := 0.15
const H_JITTER_X := 0
const H_JITTER_Y := 1
const H_DROP := 2
const H_MASS_ON := 3
const H_MASS_PICK := 4
const H_ERODE := 5
const H_RUBBLE_X := 6
const H_RUBBLE_Y := 7
const H_RUBBLE_KEEP := 8
# kinds[k] values for a blocked cell.
const KIND_PLATE := 0
const KIND_MASS := 1
const KIND_RUBBLE := 2

var density: float = 35.0
var plate_cell_wu: float = PLATE_CELL_WU
var layer_gap_wu: float = LAYER_GAP_WU
# masks[k]: PackedByteArray of dim * dim, 1 open, 0 blocked, k = 0..4 (layer k + 1).
var masks: Array = []
# kinds[k]: KIND_* of each blocked cell (0 where open).
var kinds: Array = []
# Each {points: PackedVector2Array, layer: int (1-based)}. Pass 2: the closed bounding box of a
# plate dropped for reachability. Pass 1 (`space-noise-blobs`): a carved tunnel's polyline.
var tunnels: Array = []
# Per layer {blocked, open}, shares 0..1.
var layer_stats: Array = []
# Kept plates per layer after the clearing (the large mass counts as plates); empty in blob mode.
var plates_per_layer: Array = []
var plates_cleared := 0
var plates_cut := 0
var rubble_share := 0.0
var pockets_filled := 0
var tunnels_cut := 0
var regions_unreachable_after := 0
# Percent of cells open on layer k and k + 1, k = 0..3.
var crossing_pct: Array = []
# Per layer: plate id of every cell, and the number of plate id slots.
var _plate_ids: Array = []
var _plate_slots: Array = []


func generate(p_seed: int, p_canvas: float = 24000.0, p_density: float = 35.0) -> void:
	canvas = p_canvas
	density = clamp(p_density, 0.0, 90.0)
	dim = int(canvas / SPACING) + 1
	var n := dim * dim
	var blobs: bool = QaPlants.is_active("space-noise-blobs")
	var open := PackedByteArray()
	open.resize(LAYERS * n)
	var kind := PackedByteArray()
	kind.resize(LAYERS * n)
	_plate_ids = []
	_plate_slots = []
	plates_per_layer = []
	plates_cleared = 0

	_build_nodes()
	if blobs:
		_fill_blobs(open, p_seed)
		for node in nodes:
			_clear_around(open, node.pos)
	else:
		for k in range(LAYERS):
			_build_plate_layer(open, kind, k, p_seed)

	pockets_filled = 0
	plates_cut = 0
	tunnels_cut = 0
	tunnels = []
	var objective_cell := _cell_of(nodes[0].pos)
	var labelled := _label_regions(open, objective_cell)
	if not QaPlants.is_active("space-no-carve"):
		if blobs:
			_fill_and_carve(open, labelled, objective_cell)
		else:
			_fill_and_drop_plates(open, labelled, objective_cell)
		labelled = _label_regions(open, objective_cell)
	regions_unreachable_after = labelled.sizes.size() - 1

	masks = []
	kinds = []
	layer_stats = []
	var rubble_cells := 0
	var blocked_cells := 0
	for k in range(LAYERS):
		var mask := open.slice(k * n, (k + 1) * n)
		var kk := kind.slice(k * n, (k + 1) * n)
		var open_count := 0
		for i in range(n):
			if mask[i] == 1:
				open_count += 1
				kk[i] = KIND_PLATE
			elif kk[i] == KIND_RUBBLE:
				rubble_cells += 1
		blocked_cells += n - open_count
		masks.append(mask)
		kinds.append(kk)
		layer_stats.append({blocked = float(n - open_count) / n, open = float(open_count) / n})
	rubble_share = float(rubble_cells) / max(blocked_cells, 1)

	_build_grid(open)
	_build_crossings(open)
	if blobs:
		_build_borders()
	else:
		# Plates are drawn as tiles; an outline overlay of five stacked layers would only clutter.
		borders = []
	rivers = []


func compute_hash() -> int:
	var parts: Array = []
	for n in nodes:
		parts.append(n.type)
		parts.append(int(round(n.pos.x)))
		parts.append(int(round(n.pos.y)))
	for mask in masks:
		parts.append(hash(mask))
	for kk in kinds:
		parts.append(hash(kk))
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


# Pass 1 generator (`space-noise-blobs`): one block of three-dimensional value noise, thresholded
# at the density quantile over all five layers.
func _fill_blobs(open: PackedByteArray, p_seed: int) -> void:
	var n := dim * dim
	var independent: bool = QaPlants.is_active("space-independent-layers")
	var samples := PackedFloat64Array()
	samples.resize(LAYERS * n)
	for k in range(LAYERS):
		var layer_seed := p_seed + k * LAYER_SEED_STEP if independent else p_seed
		_sample_layer(samples, k, layer_seed, independent, k * n)

	var threshold := -1.0
	if density > 0.0:
		var sorted := samples.duplicate()
		sorted.sort()
		threshold = sorted[min(int(floor(density / 100.0 * sorted.size())), sorted.size() - 1)]
	for i in range(LAYERS * n):
		open[i] = 0 if samples[i] <= threshold else 1


# Samples layer k (0-based) into samples[out_base ...]. Trilinear value noise with
# smoothstep on every axis; the z blend is done once per lattice plane, which gives the same
# number as blending the eight corners per sample.
func _sample_layer(samples: PackedFloat64Array, k: int, layer_seed: int, independent: bool, out_base: int) -> void:
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
			var base := out_base + gy * dim
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


# Regions other than the main one under MIN_POCKET_CELLS are filled solid. Returns 1 per filled
# region id.
func _fill_pockets(open: PackedByteArray, labelled: Dictionary) -> PackedByteArray:
	var labels: PackedInt32Array = labelled.labels
	var sizes: Array = labelled.sizes
	var main: int = labelled.main
	var fill := PackedByteArray()
	fill.resize(sizes.size())
	for id in range(sizes.size()):
		if id != main and sizes[id] < MIN_POCKET_CELLS:
			fill[id] = 1
			pockets_filled += 1
	if pockets_filled > 0:
		for i in range(labels.size()):
			if labels[i] >= 0 and fill[labels[i]] == 1:
				open[i] = 0
	return fill


# Pass 1: larger pockets get a tunnel on their own layer toward the objective's cell, cut as a
# Bresenham line TUNNEL_HALF_WIDTH_CELLS wide, ending at the first main-region cell it touches. The
# objective column is open on every layer (the clear radius), so every line ends. Pockets are
# filled before any tunnel is cut, so a tunnel through a small pocket is not filled back in.
func _fill_and_carve(open: PackedByteArray, labelled: Dictionary, objective_cell: Vector2i) -> void:
	var n := dim * dim
	var labels: PackedInt32Array = labelled.labels
	var sizes: Array = labelled.sizes
	var main: int = labelled.main
	var fill := _fill_pockets(open, labelled)
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


func _hash01(ix: int, iy: int, channel: int, layer_seed: int) -> float:
	return hash32(ix, iy, channel, layer_seed) / 4294967296.0


# Pass 2: layer k (0-based) as a sheet of plates, written into open / kind at k * dim * dim.
# Plates are Worley cells of a jittered lattice laid in a warped space whose cell size follows the
# two-octave noise (small plates where it is low), so the field has packed and open areas.
# A cell is open water within CHANNEL_WU of a plate boundary. Each plate is kept or dropped by
# its own hash against the density; dropped plates carry rubble; one large mass may be grown;
# the layout places drop the plates around them; kept edges are eroded.
func _build_plate_layer(open: PackedByteArray, kind: PackedByteArray, k: int, p_seed: int) -> void:
	var n := dim * dim
	var base := k * n
	var coherent: bool = QaPlants.is_active("space-coherent-layers")
	var ls := p_seed if coherent else p_seed + k * LAYER_SEED_STEP
	var v := PackedFloat64Array()
	v.resize(n)
	_sample_layer(v, k, ls, not coherent, 0)

	# Warped lattice coordinates: one lattice unit is one plate, whatever the local plate size.
	var ux := PackedFloat64Array()
	var uy := PackedFloat64Array()
	ux.resize(n)
	uy.resize(n)
	var umax_x := 0.0
	var umax_y := 0.0
	for gy in range(dim):
		var acc := 0.0
		for gx in range(dim):
			var i := gy * dim + gx
			ux[i] = acc
			acc += SPACING / (plate_cell_wu * (SCALE_BASE + SCALE_SWING * v[i]))
		umax_x = max(umax_x, ux[gy * dim + dim - 1])
	for gx in range(dim):
		var acc := 0.0
		for gy in range(dim):
			var i := gy * dim + gx
			uy[i] = acc
			acc += SPACING / (plate_cell_wu * (SCALE_BASE + SCALE_SWING * v[i]))
		umax_y = max(umax_y, uy[(dim - 1) * dim + gx])
	# Lattice index ix runs from -1; slot lx = ix + 1.
	var wx := int(floor(umax_x)) + 3
	var wy := int(floor(umax_y)) + 3
	var slots := wx * wy
	var centre_x := PackedFloat64Array()
	var centre_y := PackedFloat64Array()
	centre_x.resize(slots)
	centre_y.resize(slots)
	for ly in range(wy):
		for lx in range(wx):
			centre_x[ly * wx + lx] = (lx - 1) + _hash01(lx - 1, ly - 1, H_JITTER_X, ls)
			centre_y[ly * wx + lx] = (ly - 1) + _hash01(lx - 1, ly - 1, H_JITTER_Y, ls)

	var pid := PackedInt32Array()
	var pid2 := PackedInt32Array()
	var channel := PackedByteArray()
	pid.resize(n)
	pid2.resize(n)
	channel.resize(n)
	var count := PackedInt32Array()
	var sum_x := PackedFloat64Array()
	var sum_y := PackedFloat64Array()
	var sum_v := PackedFloat64Array()
	count.resize(slots)
	sum_x.resize(slots)
	sum_y.resize(slots)
	sum_v.resize(slots)
	for gy in range(dim):
		for gx in range(dim):
			var i := gy * dim + gx
			var px := ux[i]
			var py := uy[i]
			var bx := int(floor(px))
			var by := int(floor(py))
			var d1 := INF
			var d2 := INF
			var id1 := 0
			var id2 := 0
			for ly in range(by, by + 3):
				for lx in range(bx, bx + 3):
					var j := ly * wx + lx
					var dx := centre_x[j] - px
					var dy := centre_y[j] - py
					var d := dx * dx + dy * dy
					if d < d1:
						d2 = d1
						id2 = id1
						d1 = d
						id1 = j
					elif d < d2:
						d2 = d
						id2 = j
			pid[i] = id1
			pid2[i] = id2
			var width_wu := (sqrt(d2) - sqrt(d1)) * plate_cell_wu * (SCALE_BASE + SCALE_SWING * v[i])
			channel[i] = 1 if width_wu < CHANNEL_WU else 0
			count[id1] += 1
			sum_x[id1] += gx * SPACING
			sum_y[id1] += gy * SPACING
			sum_v[id1] += v[i]

	var existing: Array = []
	var centroid := PackedVector2Array()
	centroid.resize(slots)
	var kept := PackedByteArray()
	var mass := PackedByteArray()
	var cleared := PackedByteArray()
	kept.resize(slots)
	mass.resize(slots)
	cleared.resize(slots)
	for p in range(slots):
		if count[p] == 0:
			continue
		existing.append(p)
		centroid[p] = Vector2(sum_x[p], sum_y[p]) / count[p]
		var keep_share := density / 100.0 + (sum_v[p] / count[p] - 0.5) * DROP_SWING if density > 0.0 else -1.0
		kept[p] = 1 if _hash01(p % wx - 1, p / wx - 1, H_DROP, ls) <= keep_share else 0

	if _hash01(0, 0, H_MASS_ON, ls) < MASS_CHANCE:
		var pick: int = existing[int(_hash01(0, 0, H_MASS_PICK, ls) * existing.size())]
		for p in existing:
			if centroid[p].distance_to(centroid[pick]) <= MASS_RADIUS_WU:
				mass[p] = 1
				kept[p] = 1

	# The layout places: the plate holding each node and every plate whose centre is near it.
	for node in nodes:
		var cell := _cell_of(node.pos)
		var home := pid[cell.y * dim + cell.x]
		for p in existing:
			if cleared[p] == 0 and (p == home or centroid[p].distance_to(node.pos) <= CLEAR_RADIUS_WU):
				cleared[p] = 1
				if kept[p] == 1:
					plates_cleared += 1
				kept[p] = 0
				mass[p] = 0
	var kept_count := 0
	for p in existing:
		kept_count += kept[p]
	plates_per_layer.append(kept_count)

	# Rubble: a second, finer lattice in world units.
	var rw := int(canvas / RUBBLE_CELL_WU) + 4
	var rubble_x := PackedFloat64Array()
	var rubble_y := PackedFloat64Array()
	var rubble_kept := PackedByteArray()
	rubble_x.resize(rw * rw)
	rubble_y.resize(rw * rw)
	rubble_kept.resize(rw * rw)
	for ly in range(rw):
		for lx in range(rw):
			rubble_x[ly * rw + lx] = ((lx - 1) + _hash01(lx - 1, ly - 1, H_RUBBLE_X, ls)) * RUBBLE_CELL_WU
			rubble_y[ly * rw + lx] = ((ly - 1) + _hash01(lx - 1, ly - 1, H_RUBBLE_Y, ls)) * RUBBLE_CELL_WU
			rubble_kept[ly * rw + lx] = 1 if _hash01(lx - 1, ly - 1, H_RUBBLE_KEEP, ls) < RUBBLE_SHARE else 0

	for gy in range(dim):
		for gx in range(dim):
			var i := gy * dim + gx
			var p := pid[i]
			var blocked_kind := -1
			if channel[i] == 1:
				if mass[p] == 1 and mass[pid2[i]] == 1:
					blocked_kind = KIND_MASS
			elif kept[p] == 1:
				blocked_kind = KIND_MASS if mass[p] == 1 else KIND_PLATE
			elif cleared[p] == 0 and _in_rubble(gx * SPACING, gy * SPACING, rubble_x, rubble_y, rubble_kept, rw):
				blocked_kind = KIND_RUBBLE
			if blocked_kind < 0:
				open[base + i] = 1
			else:
				kind[base + i] = blocked_kind

	# Erode: a blocked cell next to open space is removed by its own hash, so edges are broken.
	var before := open.slice(base, base + n)
	for gy in range(dim):
		for gx in range(dim):
			var i := gy * dim + gx
			if before[i] == 1:
				continue
			var edge: bool = (gx > 0 and before[i - 1] == 1) or (gx < dim - 1 and before[i + 1] == 1) \
				or (gy > 0 and before[i - dim] == 1) or (gy < dim - 1 and before[i + dim] == 1)
			if edge and _hash01(gx, gy, H_ERODE, ls) < ERODE_SHARE:
				open[base + i] = 1
	_plate_ids.append(pid)
	_plate_slots.append(slots)


# True where (x, y) lies in a kept rubble fragment: the fragment's own cell wins the nearest-centre
# test and the point is at least RUBBLE_CHANNEL_WU clear of the next cell.
func _in_rubble(x: float, y: float, rubble_x: PackedFloat64Array, rubble_y: PackedFloat64Array, rubble_kept: PackedByteArray, rw: int) -> bool:
	var bx := int(floor(x / RUBBLE_CELL_WU))
	var by := int(floor(y / RUBBLE_CELL_WU))
	var d1 := INF
	var d2 := INF
	var id1 := 0
	for ly in range(by, by + 3):
		for lx in range(bx, bx + 3):
			var j := ly * rw + lx
			var dx := rubble_x[j] - x
			var dy := rubble_y[j] - y
			var d := dx * dx + dy * dy
			if d < d1:
				d2 = d1
				d1 = d
				id1 = j
			elif d < d2:
				d2 = d
	return rubble_kept[id1] == 1 and sqrt(d2) - sqrt(d1) >= RUBBLE_CHANNEL_WU


# Pass 2 reachability. Pockets are filled solid as in pass 1; every other cut-off region is joined
# to the main one by dropping plates: from the region's nearest cell, breadth-first over the layer's
# plate adjacency (plates that share a channel) to the objective's plate, and every plate on the
# path becomes open water. A dropped plate that held anything is recorded in `tunnels` as its
# bounding box.
func _fill_and_drop_plates(open: PackedByteArray, labelled: Dictionary, objective_cell: Vector2i) -> void:
	var n := dim * dim
	var sizes: Array = labelled.sizes
	var main: int = labelled.main
	var fill := _fill_pockets(open, labelled)
	var adjacency: Array = []
	adjacency.resize(LAYERS)
	for id in range(sizes.size()):
		if id == main or fill[id] == 1:
			continue
		var c: int = labelled.nearest[id]
		var k := c / n
		if adjacency[k] == null:
			adjacency[k] = _plate_adjacency(k)
		var pid: PackedInt32Array = _plate_ids[k]
		var path := _plate_path(adjacency[k], _plate_slots[k], pid[c - k * n], pid[objective_cell.y * dim + objective_cell.x])
		_drop_plates(open, k, path)


func _plate_adjacency(k: int) -> Array:
	var pid: PackedInt32Array = _plate_ids[k]
	var adjacency: Array = []
	for p in range(_plate_slots[k]):
		adjacency.append([])
	for gy in range(dim):
		for gx in range(dim):
			var i := gy * dim + gx
			if gx < dim - 1:
				_link(adjacency, pid[i], pid[i + 1])
			if gy < dim - 1:
				_link(adjacency, pid[i], pid[i + dim])
	return adjacency


func _link(adjacency: Array, a: int, b: int) -> void:
	if a != b and not adjacency[a].has(b):
		adjacency[a].append(b)
		adjacency[b].append(a)


# Plate ids from `from` to `to` inclusive (empty if not connected).
func _plate_path(adjacency: Array, slots: int, from: int, to: int) -> PackedInt32Array:
	var parent := PackedInt32Array()
	parent.resize(slots)
	parent.fill(-2)
	parent[from] = -1
	var queue: Array = [from]
	var head := 0
	while head < queue.size() and parent[to] == -2:
		var cur: int = queue[head]
		head += 1
		for q in adjacency[cur]:
			if parent[q] == -2:
				parent[q] = cur
				queue.append(q)
	var path := PackedInt32Array()
	if parent[to] == -2:
		return path
	var p := to
	while p != -1:
		path.append(p)
		p = parent[p]
	return path


func _drop_plates(open: PackedByteArray, k: int, path: PackedInt32Array) -> void:
	var n := dim * dim
	var pid: PackedInt32Array = _plate_ids[k]
	var index := PackedInt32Array()
	index.resize(_plate_slots[k])
	index.fill(-1)
	for j in range(path.size()):
		index[path[j]] = j
	var low: Array = []
	var high: Array = []
	var held := PackedByteArray()
	held.resize(path.size())
	for j in range(path.size()):
		low.append(Vector2(INF, INF))
		high.append(Vector2(-INF, -INF))
	for i in range(n):
		var j := index[pid[i]]
		if j < 0:
			continue
		var gy := i / dim
		var cell := Vector2(i - gy * dim, gy)
		low[j] = Vector2(min(low[j].x, cell.x), min(low[j].y, cell.y))
		high[j] = Vector2(max(high[j].x, cell.x), max(high[j].y, cell.y))
		if open[k * n + i] == 0:
			held[j] = 1
			open[k * n + i] = 1
	for j in range(path.size()):
		if held[j] == 0:
			continue
		var a: Vector2 = (low[j] - Vector2(0.5, 0.5)) * SPACING
		var b: Vector2 = (high[j] + Vector2(0.5, 0.5)) * SPACING
		tunnels.append({points = PackedVector2Array([a, Vector2(b.x, a.y), b, Vector2(a.x, b.y), a]), layer = k + 1})
		plates_cut += 1
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
