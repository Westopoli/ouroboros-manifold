class_name SpaceFieldMap
extends FieldMap

# Five open-or-blocked layers, each a sheet of plates from its own seed: a jittered lattice of plate
# centres, each plate the cell of its centre against its eight neighbours (straight bisector edges)
# pulled in by half a channel, so the gap between two plates is one channel wide. Dropped plates are
# open water; rubble gathers on dropped plates next to kept ones. Every plate is a polygon; the cell
# masks are filled from the polygons, so play data and picture agree.
# No engine noise, no random calls: every random value is the hand-written hash below, so the C
# simulation can copy this file line for line.
# See also: docs/northstar/plans/2026-10-02-space-kit-mode-spec.md

const LAYERS := 5
const LAYER_GAP_WU := 1400.0
const CLEAR_RADIUS_WU := 600.0
const MIN_POCKET_CELLS := 40
const CROSSING_MARK_MIN_CELLS := 8
const CROSSING_MARK_MAX_CELLS := 50
const HASH_MASK := 0xFFFFFFFF
const LAYER_SEED_STEP := 7919
# lattice cells across (canvas, canvas, 5 layers), and the octave's weight.
const OCTAVE_LATTICES: Array[Vector3i] = [Vector3i(5, 5, 2), Vector3i(14, 14, 4)]
const OCTAVE_WEIGHTS: Array[float] = [0.65, 0.35]
const PLATE_CELL_WU := 1600.0
const CHANNEL_WU := 160.0
const JITTER_MAX := 0.45
const RUBBLE_CELL_WU := 400.0
const RUBBLE_CHANNEL_WU := 100.0
const RUBBLE_SHARE := 0.35
const DROP_SWING := 0.3
const MASS_CHANCE := 0.5
const MASS_RADIUS_WU := 2200.0
const ERODE_MAX := 0.12
# Hash channels: the iz argument of hash32 names what a value is for.
const H_JITTER_X := 0
const H_JITTER_Y := 1
const H_DROP := 2
const H_MASS_ON := 3
const H_MASS_PICK := 4
const H_ERODE := 5
const H_RUBBLE_X := 6
const H_RUBBLE_Y := 7
const H_RUBBLE_KEEP := 8
const H_RUBBLE_ERODE := 9
# kinds[k] values for a blocked cell, and the kind of a plate polygon.
const KIND_PLATE := 0
const KIND_MASS := 1
const KIND_RUBBLE := 2
const NEIGHBOURS: Array[Vector2i] = [
	Vector2i(-1, -1), Vector2i(0, -1), Vector2i(1, -1), Vector2i(-1, 0),
	Vector2i(1, 0), Vector2i(-1, 1), Vector2i(0, 1), Vector2i(1, 1),
]

var density: float = 35.0
var plate_cell_wu: float = PLATE_CELL_WU
var layer_gap_wu: float = LAYER_GAP_WU
# masks[k]: PackedByteArray of dim * dim, 1 open, 0 blocked, k = 0..4 (layer k + 1).
var masks: Array = []
# kinds[k]: KIND_* of each blocked cell (0 where open).
var kinds: Array = []
# plate_polys[k]: each {points: PackedVector2Array (counter-clockwise), kind: KIND_*, plate: int}.
# This is what is drawn; plates dropped for reachability are gone from it.
var plate_polys: Array = []
# fill_cells[k]: cells of layer k filled solid as small pockets (no polygon covers them).
var fill_cells: Array = []
# Each {points: PackedVector2Array, layer: int (1-based)}: the closed outline of a plate dropped
# for reachability.
var tunnels: Array = []
# Per layer {blocked, open}, shares 0..1.
var layer_stats: Array = []
# Kept plates per layer after the clearing (the large mass counts as plates), before rubble.
var plates_per_layer: Array = []
# Polygons drawn per layer: plates, mass and rubble.
var plate_polygon_count: Array = []
var plates_cleared := 0
var plates_cut := 0
var rubble_share := 0.0
var pockets_filled := 0
var tunnels_cut := 0
var regions_unreachable_after := 0
# Percent of cells open on layer k and k + 1, k = 0..3.
var crossing_pct: Array = []
# Per layer: {cx, cy, stride, wc, cell, polys, base, links}; see _build_plate_layer.
var _ctx: Array = []
# Cells (index over all layers) filled solid as pockets.
var _filled := PackedInt32Array()


func generate(p_seed: int, p_canvas: float = 24000.0, p_density: float = 35.0) -> void:
	canvas = p_canvas
	density = clamp(p_density, 0.0, 90.0)
	dim = int(canvas / SPACING) + 1
	var n := dim * dim
	var open := PackedByteArray()
	open.resize(LAYERS * n)
	open.fill(1)
	var kind := PackedByteArray()
	kind.resize(LAYERS * n)
	_ctx = []
	_filled = PackedInt32Array()
	plates_per_layer = []
	plates_cleared = 0

	_build_nodes()
	for k in range(LAYERS):
		_build_plate_layer(open, kind, k, p_seed)

	pockets_filled = 0
	plates_cut = 0
	tunnels_cut = 0
	tunnels = []
	var objective_cell := _cell_of(nodes[0].pos)
	var labelled := _label_regions(open, objective_cell)
	if not QaPlants.is_active("space-no-carve"):
		_fill_and_drop_plates(open, kind, labelled, objective_cell)
		labelled = _label_regions(open, objective_cell)
	regions_unreachable_after = labelled.sizes.size() - 1

	masks = []
	kinds = []
	layer_stats = []
	plate_polys = []
	plate_polygon_count = []
	fill_cells = []
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
		plate_polys.append(_ctx[k].polys)
		plate_polygon_count.append(_ctx[k].polys.size())
		fill_cells.append(PackedInt32Array())
	rubble_share = float(rubble_cells) / max(blocked_cells, 1)
	for c in _filled:
		if open[c] == 0:
			var k := c / n
			fill_cells[k].append(c - k * n)

	_build_grid(open)
	_build_crossings(open)
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
	for count in plate_polygon_count:
		parts.append(count)
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


func _hash01(ix: int, iy: int, channel: int, layer_seed: int) -> float:
	return hash32(ix, iy, channel, layer_seed) / 4294967296.0


# Samples layer k (0-based) into samples[out_base ...]. Trilinear value noise with
# smoothstep on every axis; the z blend is done once per lattice plane, which gives the same
# number as blending the eight corners per sample. `independent` fixes z at 0.5 (a layer with its
# own seed); otherwise the layer's slice of one shared block is sampled.
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
# region id. The filled cells are kept in `_filled`: no polygon covers them, the placer draws them.
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
				_filled.append(i)
	return fill


func _key(i: int, j: int, stride: int) -> int:
	return (j + 2) * stride + (i + 2)


# A jittered square lattice of centres over the canvas, cell size `cell`, indices -2 .. wc + 1.
# The noise v (the layer's grid, sampled at the lattice cell's own middle) scales the jitter, up to
# JITTER_MAX of the cell: where v is low the plates are more regular. `v` holds v per key.
func _lattice(noise: PackedFloat64Array, cell: float, layer_seed: int, hx: int, hy: int) -> Dictionary:
	var wc := int(ceil(canvas / cell))
	var stride := wc + 4
	var cx := PackedFloat64Array()
	var cy := PackedFloat64Array()
	var v := PackedFloat64Array()
	cx.resize(stride * stride)
	cy.resize(stride * stride)
	v.resize(stride * stride)
	for j in range(-2, wc + 2):
		for i in range(-2, wc + 2):
			var key := _key(i, j, stride)
			var gx := clampi(int(round((i + 0.5) * cell / SPACING)), 0, dim - 1)
			var gy := clampi(int(round((j + 0.5) * cell / SPACING)), 0, dim - 1)
			var vv := noise[gy * dim + gx]
			var amp := JITTER_MAX * (0.5 + 0.5 * vv)
			v[key] = vv
			cx[key] = (i + 0.5 + (_hash01(i, j, hx, layer_seed) * 2.0 - 1.0) * amp) * cell
			cy[key] = (j + 0.5 + (_hash01(i, j, hy, layer_seed) * 2.0 - 1.0) * amp) * cell
	return {cx = cx, cy = cy, v = v, wc = wc, stride = stride, cell = cell}


# Keeps the part of a convex polygon with n . p <= d.
func _clip(poly: PackedVector2Array, nrm: Vector2, d: float) -> PackedVector2Array:
	var out := PackedVector2Array()
	var count := poly.size()
	for i in range(count):
		var a := poly[i]
		var b := poly[(i + 1) % count]
		var sa := nrm.dot(a) - d
		var sb := nrm.dot(b) - d
		if sa <= 0.0:
			out.append(a)
		if (sa < 0.0 and sb > 0.0) or (sa > 0.0 and sb < 0.0):
			out.append(a + (b - a) * (sa / (sa - sb)))
	return out


func _clip_canvas(poly: PackedVector2Array) -> PackedVector2Array:
	poly = _clip(poly, Vector2(-1.0, 0.0), 0.0)
	poly = _clip(poly, Vector2(1.0, 0.0), canvas)
	poly = _clip(poly, Vector2(0.0, -1.0), 0.0)
	return _clip(poly, Vector2(0.0, 1.0), canvas)


# The cell of centre (i, j): the lattice square widened by one cell, cut by the perpendicular
# bisector against each of the eight neighbours, each cut pulled in by insets[idx] toward the
# centre. Counter-clockwise. `found` receives the (i, j) of every neighbour whose cut leaves an edge.
func _cell_polygon(cx: PackedFloat64Array, cy: PackedFloat64Array, stride: int, i: int, j: int, cell: float, insets: PackedFloat64Array, found: Array) -> PackedVector2Array:
	var key := _key(i, j, stride)
	var c := Vector2(cx[key], cy[key])
	var poly := PackedVector2Array([
		Vector2((i - 1) * cell, (j - 1) * cell), Vector2((i + 2) * cell, (j - 1) * cell),
		Vector2((i + 2) * cell, (j + 2) * cell), Vector2((i - 1) * cell, (j + 2) * cell),
	])
	var cuts: Array = []
	for idx in range(8):
		var o: Vector2i = NEIGHBOURS[idx]
		var q := _key(i + o.x, j + o.y, stride)
		var qc := Vector2(cx[q], cy[q])
		var nrm := (qc - c).normalized()
		var d := nrm.dot((c + qc) * 0.5) - insets[idx]
		poly = _clip(poly, nrm, d)
		cuts.append([nrm, d])
	for idx in range(8):
		var nrm: Vector2 = cuts[idx][0]
		var d: float = cuts[idx][1]
		var first := Vector2.ZERO
		var seen := false
		for p in poly:
			if absf(nrm.dot(p) - d) < 0.01:
				if not seen:
					first = p
					seen = true
				elif p.distance_to(first) > 1.0:
					found.append(Vector2i(i + NEIGHBOURS[idx].x, j + NEIGHBOURS[idx].y))
					break
	return poly


# Moves each vertex toward the centroid by a hashed share (up to ERODE_MAX) of its distance, so
# edges stay straight and corners vary. Vertices on the canvas boundary stay.
func _erode(poly: PackedVector2Array, i: int, j: int, layer_seed: int, channel: int) -> PackedVector2Array:
	var centroid := Vector2.ZERO
	for p in poly:
		centroid += p
	centroid /= poly.size()
	var out := PackedVector2Array()
	for vi in range(poly.size()):
		var p := poly[vi]
		if p.x < 0.01 or p.y < 0.01 or p.x > canvas - 0.01 or p.y > canvas - 0.01:
			out.append(p)
		else:
			out.append(p + (centroid - p) * (_hash01(i, j * 64 + vi, channel, layer_seed) * ERODE_MAX))
	return out


# The key of the plate whose centre is nearest `pos` (3 by 3 lattice cells around it).
func _nearest_plate(ctx: Dictionary, pos: Vector2) -> int:
	var cx: PackedFloat64Array = ctx.cx
	var cy: PackedFloat64Array = ctx.cy
	var bi := clampi(int(floor(pos.x / ctx.cell)), -1, ctx.wc)
	var bj := clampi(int(floor(pos.y / ctx.cell)), -1, ctx.wc)
	var best := -1
	var best_d := INF
	for j in range(bj - 1, bj + 2):
		for i in range(bi - 1, bi + 2):
			var key := _key(i, j, ctx.stride)
			var dx := cx[key] - pos.x
			var dy := cy[key] - pos.y
			var d := dx * dx + dy * dy
			if d < best_d:
				best_d = d
				best = key
	return best


# Sets the cells inside a polygon blocked, row by row (even-odd crossings of each row).
func _fill_polygon(open: PackedByteArray, kind: PackedByteArray, base: int, poly: PackedVector2Array, kind_value: int) -> void:
	var low_y := INF
	var high_y := -INF
	for p in poly:
		low_y = min(low_y, p.y)
		high_y = max(high_y, p.y)
	var count := poly.size()
	for gy in range(maxi(0, int(ceil(low_y / SPACING))), mini(dim - 1, int(floor(high_y / SPACING))) + 1):
		var y: float = min(gy * SPACING, canvas - 0.001)
		var xs := PackedFloat64Array()
		for e in range(count):
			var a := poly[e]
			var b := poly[(e + 1) % count]
			if (a.y <= y and b.y > y) or (b.y <= y and a.y > y):
				xs.append(a.x + (y - a.y) / (b.y - a.y) * (b.x - a.x))
		xs.sort()
		for pair in range(0, xs.size() - 1, 2):
			for gx in range(maxi(0, int(ceil(xs[pair] / SPACING))), mini(dim - 1, int(floor(xs[pair + 1] / SPACING))) + 1):
				open[base + gy * dim + gx] = 0
				kind[base + gy * dim + gx] = kind_value


# Layer k (0-based) as a sheet of plates, written into open / kind at k * dim * dim.
# Each plate is kept or dropped by its own hash against the density, shifted by the noise v at the
# plate (some areas packed, some open); one large mass may be grown; the layout places drop the
# plates around them; rubble fills dropped plates that touch a kept one.
func _build_plate_layer(open: PackedByteArray, kind: PackedByteArray, k: int, p_seed: int) -> void:
	var n := dim * dim
	var coherent: bool = QaPlants.is_active("space-coherent-layers")
	var ls := p_seed if coherent else p_seed + k * LAYER_SEED_STEP
	var noise := PackedFloat64Array()
	noise.resize(n)
	_sample_layer(noise, k, ls, not coherent, 0)

	var ctx := _lattice(noise, plate_cell_wu, ls, H_JITTER_X, H_JITTER_Y)
	var wc: int = ctx.wc
	var stride: int = ctx.stride
	var cx: PackedFloat64Array = ctx.cx
	var cy: PackedFloat64Array = ctx.cy
	var cell: float = ctx.cell

	# Plates exist for lattice indices -1 .. wc: their cells reach into the canvas.
	var keys: Array = []
	var inside: Array = []
	var base := {}
	var links := {}
	var half := PackedFloat64Array()
	half.resize(8)
	half.fill(CHANNEL_WU * 0.5)
	for j in range(-1, wc + 1):
		for i in range(-1, wc + 1):
			var key := _key(i, j, stride)
			var found: Array = []
			base[key] = _cell_polygon(cx, cy, stride, i, j, cell, half, found)
			var neighbours: Array = []
			for o in found:
				if o.x >= -1 and o.x <= wc and o.y >= -1 and o.y <= wc:
					neighbours.append(_key(o.x, o.y, stride))
			links[key] = neighbours
			keys.append(key)
			if i >= 0 and i < wc and j >= 0 and j < wc:
				inside.append(key)

	# The channels and the eroded corners take about a quarter of a plate's area, so the share of
	# plates kept is the blocked percent divided by the share of a plate that stays solid.
	var solid := (1.0 - CHANNEL_WU / cell) * (1.0 - CHANNEL_WU / cell) * (1.0 - ERODE_MAX * 0.5) * (1.0 - ERODE_MAX * 0.5)
	var kept := PackedByteArray()
	var mass := PackedByteArray()
	var cleared := PackedByteArray()
	kept.resize(stride * stride)
	mass.resize(stride * stride)
	cleared.resize(stride * stride)
	for key in keys:
		var i: int = key % stride - 2
		var j: int = key / stride - 2
		var keep_share: float = density / 100.0 / solid + (ctx.v[key] - 0.5) * DROP_SWING if density > 0.0 else -1.0
		kept[key] = 1 if _hash01(i, j, H_DROP, ls) <= keep_share else 0

	if _hash01(0, 0, H_MASS_ON, ls) < MASS_CHANCE:
		var pick: int = inside[int(_hash01(0, 0, H_MASS_PICK, ls) * inside.size())]
		var pick_centre := Vector2(cx[pick], cy[pick])
		for key in keys:
			if Vector2(cx[key], cy[key]).distance_to(pick_centre) <= MASS_RADIUS_WU:
				mass[key] = 1
				kept[key] = 1

	# The layout places: the plate holding each node and every plate whose centre is near it.
	for node in nodes:
		var home := _nearest_plate(ctx, node.pos)
		for key in keys:
			if cleared[key] == 0 and (key == home or Vector2(cx[key], cy[key]).distance_to(node.pos) <= CLEAR_RADIUS_WU):
				cleared[key] = 1
				if kept[key] == 1:
					plates_cleared += 1
				kept[key] = 0
				mass[key] = 0

	var polys: Array = []
	for key in keys:
		if kept[key] == 0:
			continue
		var i: int = key % stride - 2
		var j: int = key / stride - 2
		var poly: PackedVector2Array = base[key]
		if mass[key] == 1:
			# The channels between two plates of the mass are closed.
			var insets := PackedFloat64Array()
			for o in NEIGHBOURS:
				insets.append(0.0 if mass[_key(i + o.x, j + o.y, stride)] == 1 else CHANNEL_WU * 0.5)
			poly = _clip_canvas(_cell_polygon(cx, cy, stride, i, j, cell, insets, []))
		else:
			poly = _clip_canvas(poly)
			if poly.size() >= 3:
				poly = _erode(poly, i, j, ls, H_ERODE)
		if poly.size() < 3:
			continue
		var kind_value := KIND_MASS if mass[key] == 1 else KIND_PLATE
		polys.append({points = poly, kind = kind_value, plate = key})
		_fill_polygon(open, kind, k * n, poly, kind_value)
	plates_per_layer.append(polys.size())

	# Rubble: only on dropped plates that share a channel with a kept plate, on a finer lattice;
	# the share follows the noise at the fragment, so it gathers at the edges of packed areas.
	var near_kept := PackedByteArray()
	near_kept.resize(stride * stride)
	for key in keys:
		if kept[key] == 0 and cleared[key] == 0:
			for q in links[key]:
				if kept[q] == 1:
					near_kept[key] = 1
					break
	var rub := _lattice(noise, RUBBLE_CELL_WU, ls, H_RUBBLE_X, H_RUBBLE_Y)
	var rubble_insets := PackedFloat64Array()
	rubble_insets.resize(8)
	rubble_insets.fill(RUBBLE_CHANNEL_WU * 0.5)
	for j in range(-1, rub.wc + 1):
		for i in range(-1, rub.wc + 1):
			var rk := _key(i, j, rub.stride)
			if _hash01(i, j, H_RUBBLE_KEEP, ls) >= RUBBLE_SHARE * rub.v[rk]:
				continue
			var centre := Vector2(rub.cx[rk], rub.cy[rk])
			if centre.x < -RUBBLE_CELL_WU * 0.5 or centre.y < -RUBBLE_CELL_WU * 0.5 or centre.x > canvas + RUBBLE_CELL_WU * 0.5 or centre.y > canvas + RUBBLE_CELL_WU * 0.5:
				continue
			var parent := _nearest_plate(ctx, centre)
			if near_kept[parent] == 0:
				continue
			var poly := _cell_polygon(rub.cx, rub.cy, rub.stride, i, j, RUBBLE_CELL_WU, rubble_insets, [])
			var outline: PackedVector2Array = base[parent]
			for e in range(outline.size()):
				var edge := outline[(e + 1) % outline.size()] - outline[e]
				if edge.length() > 0.01:
					var outward := Vector2(edge.y, -edge.x).normalized()
					poly = _clip(poly, outward, outward.dot(outline[e]))
			poly = _clip_canvas(poly)
			if poly.size() < 3:
				continue
			poly = _erode(poly, i, j, ls, H_RUBBLE_ERODE)
			polys.append({points = poly, kind = KIND_RUBBLE, plate = parent})
			_fill_polygon(open, kind, k * n, poly, KIND_RUBBLE)

	ctx.polys = polys
	ctx.base = base
	ctx.links = links
	_ctx.append(ctx)


# Pass 2 reachability. Pockets are filled solid; every other cut-off region is joined to the main
# one by dropping plates: from the plate under the region's nearest cell, breadth-first over the
# layer's plate adjacency (plates that share a channel) to the objective's plate, and every plate
# on the path becomes open water.
func _fill_and_drop_plates(open: PackedByteArray, kind: PackedByteArray, labelled: Dictionary, objective_cell: Vector2i) -> void:
	var n := dim * dim
	var sizes: Array = labelled.sizes
	var main: int = labelled.main
	var fill := _fill_pockets(open, labelled)
	for id in range(sizes.size()):
		if id == main or fill[id] == 1:
			continue
		var c: int = labelled.nearest[id]
		var k := c / n
		var ctx: Dictionary = _ctx[k]
		var gy := (c - k * n) / dim
		var gx := (c - k * n) - gy * dim
		var from := _nearest_plate(ctx, Vector2(gx, gy) * SPACING)
		var to := _nearest_plate(ctx, nodes[0].pos)
		_drop_plates(open, kind, k, _plate_path(ctx.links, from, to))


# Plate keys from `from` to `to` inclusive (empty if not connected).
func _plate_path(links: Dictionary, from: int, to: int) -> PackedInt32Array:
	var path := PackedInt32Array()
	if not links.has(from) or not links.has(to):
		return path
	var parent := {from: -1}
	var queue: Array = [from]
	var head := 0
	while head < queue.size() and not parent.has(to):
		var cur: int = queue[head]
		head += 1
		for q in links[cur]:
			if not parent.has(q):
				parent[q] = cur
				queue.append(q)
	if not parent.has(to):
		return path
	var p := to
	while p != -1:
		path.append(p)
		p = parent[p]
	return path


# Opens every cell nearest to a plate on the path and removes its polygons. A plate that held
# anything is recorded in `tunnels` as its outline.
func _drop_plates(open: PackedByteArray, kind: PackedByteArray, k: int, path: PackedInt32Array) -> void:
	var n := dim * dim
	var ctx: Dictionary = _ctx[k]
	var cell: float = ctx.cell
	for p in path:
		var held := false
		var kept_polys: Array = []
		for pl in ctx.polys:
			if pl.plate == p:
				held = true
			else:
				kept_polys.append(pl)
		ctx.polys = kept_polys
		var i: int = p % ctx.stride - 2
		var j: int = p / ctx.stride - 2
		for gy in range(maxi(0, int(floor((j - 1) * cell / SPACING))), mini(dim - 1, int(ceil((j + 2) * cell / SPACING))) + 1):
			for gx in range(maxi(0, int(floor((i - 1) * cell / SPACING))), mini(dim - 1, int(ceil((i + 2) * cell / SPACING))) + 1):
				if _nearest_plate(ctx, Vector2(gx, gy) * SPACING) == p:
					var c := k * n + gy * dim + gx
					if open[c] == 0:
						held = true
						open[c] = 1
						kind[c] = KIND_PLATE
		if held:
			var outline: PackedVector2Array = ctx.base[p]
			var points := outline.duplicate()
			points.append(outline[0])
			tunnels.append({points = points, layer = k + 1})
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


# A crossing cell is open on layers k and k + 1. In-plane clusters of such cells between
# CROSSING_MARK_MIN_CELLS and CROSSING_MARK_MAX_CELLS get one mark at their centroid; bigger ones
# are obviously crossable, smaller ones are noise.
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
			if size >= CROSSING_MARK_MIN_CELLS and size <= CROSSING_MARK_MAX_CELLS:
				crossings.append({point = sum / size * SPACING, kind = "shaft", layer_from = k + 1, layer_to = k + 2})
