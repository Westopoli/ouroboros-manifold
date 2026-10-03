class_name SpaceFieldMap
extends FieldMap

# Five open-or-blocked layers, each a sheet of plates from its own seed: a jittered lattice of plate
# centres, each plate the cell of its centre against the surviving centres around it (straight
# bisector edges) pulled in by half a channel, so the gap between two plates is one channel wide.
# A size field removes some lattice centres (their area goes to the neighbours: a large floe) and
# splits others into four (small floes). Dropped plates are open water; rubble gathers on dropped
# plates next to kept ones. Every plate is a polygon; the cell masks are filled from the polygons,
# so play data and picture agree. Cells blocked on a layer and the one above are traced into walls
# so the two read as one solid body.
# Pass 5 adds the functional maps: what ordinary units can pass (the fine mask opened with a 300 wu
# block: anything narrower is solid) and what small craft can pass. The fine fracture above is kept
# whole; it is the small-craft map inside small-craft sections (batches of adjacent plates) and
# visual detail everywhere else. Reachability runs on the ordinary map: a cut-off region is joined to
# the main one by widening one channel (default) or by dropping the plates on the way (`join_mode`).
# No engine noise, no random calls: every random value is the hand-written hash below, so the C
# simulation can copy this file line for line.
# See also: docs/northstar/plans/2026-10-02-space-kit-mode-spec.md

const LAYERS := 5
const LAYER_GAP_WU := 1000.0
const CLEAR_RADIUS_WU := 600.0
const MIN_PASSAGE_WU := 300.0
# Placeholder until Q-166-05 (the small craft's size).
const SMALL_PASSAGE_WU := 100.0
const SMALL_SHARE_DEFAULT := 7.5
const BATCH_PLATES := 6
const SECTION_SEED_QUANTILE := 0.75
const MIN_POCKET_CELLS := 40
const JOIN_WIDEN := "widen"
const JOIN_DROP := "drop"
# Rounds of joining: every cut-off region is widened to the main region once per round.
const MAX_JOIN_ROUNDS := 8
const NO_MAIN_D2 := 1 << 28
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
const SIZE_SPREAD := 0.6
const SIZE_TAIL_SHARE := 0.25
const DENSITY_SWING := 0.8
const SIZE_SEED_OFFSET := 104729
const LATTICE_PAD := 3
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
const H_SPLIT_X := 10
const H_SPLIT_Y := 11
const H_SPLIT_DROP := 12
const H_SPLIT_ERODE := 13
const H_SECTION := 14
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
var size_spread: float = SIZE_SPREAD
var density_swing: float = DENSITY_SWING
var shared_density := true
# How a cut-off region is joined to the main one: JOIN_WIDEN or JOIN_DROP.
var join_mode: String = JOIN_WIDEN
# Percent of each layer's cells that are small-craft sections.
var small_share: float = SMALL_SHARE_DEFAULT
# Sections grow from the plates at the objective, staging and vantage nodes instead of the noise.
var sections_near_layout := false
# masks[k]: PackedByteArray of dim * dim, 1 open, 0 blocked, k = 0..4 (layer k + 1).
var masks: Array = []
# masks_ordinary[k]: the fine mask opened with a MIN_PASSAGE_WU block, 1 open. Reachability runs on
# this. small_masks[k]: what small craft can pass: the fine mask opened at SMALL_PASSAGE_WU (or the
# ordinary map, if more is open there) inside small-craft sections, the ordinary map outside.
var masks_ordinary: Array = []
var small_masks: Array = []
# section_cells[k]: per cell the 1-based index of the section batch it belongs to, 0 outside.
var section_cells: Array = []
# section_frames[k]: {a, b} segments outlining each section batch (marching squares on its cells).
var section_frames: Array = []
# Percent of layer k's cells in sections; percent of layer k's small-craft-open cells that ordinary
# units cannot reach.
var small_section_pct: Array = []
var small_only_pct: Array = []
# kinds[k]: KIND_* of each blocked cell (0 where open).
var kinds: Array = []
# plate_polys[k]: each {points: PackedVector2Array (counter-clockwise), kind: KIND_*, plate: site index}.
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
# Join by widening: channels opened, and the cells they turned from blocked to open.
var channels_widened := 0
var join_cells_opened := 0
var pockets_filled := 0
var tunnels_cut := 0
var regions_unreachable_after := 0
# Percent of cells open on layer k and k + 1, k = 0..3.
var crossing_pct: Array = []
# Cells blocked on layer k and k + 1, k = 0..3.
var filled_cells_per_pair: Array = []
# walls[k] (k = 0..3): the outline of the cells of each plate that are blocked on layer k and k + 1,
# {a: PackedVector2Array, b: PackedVector2Array, kind: PackedByteArray}; segment i runs a[i] to b[i]
# with the outward normal (d.y, -d.x) (x, y being the plane's two axes).
var walls: Array = []
# Per layer: {cx, cy, v, stride, wc, cell, site_pos, cell_sites, polys, base, links}; see
# _build_plate_layer. Plates are identified by their site index.
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
	# Per cell, which plate and kind covers it: plate site * 3 + kind, or -1 (open, or filled solid).
	var owner := PackedInt32Array()
	owner.resize(LAYERS * n)
	owner.fill(-1)
	var shared := PackedFloat64Array()
	if shared_density:
		shared.resize(n)
		_sample_layer(shared, 0, p_seed, true, 0)
	_ctx = []
	_filled = PackedInt32Array()
	plates_per_layer = []
	plates_cleared = 0

	_build_nodes()
	for k in range(LAYERS):
		_build_plate_layer(open, kind, owner, k, p_seed, shared)

	pockets_filled = 0
	plates_cut = 0
	tunnels_cut = 0
	channels_widened = 0
	join_cells_opened = 0
	tunnels = []
	var objective_cell := _cell_of(nodes[0].pos)
	var ordinary_cells := int(MIN_PASSAGE_WU / SPACING)
	var ordinary := _open_block(open, ordinary_cells)
	var labelled := _label_regions(ordinary, objective_cell)
	if not QaPlants.is_active("space-no-carve"):
		if join_mode == JOIN_DROP:
			_fill_and_drop_plates(open, kind, labelled)
		else:
			_fill_and_widen(open, kind, owner, labelled, objective_cell, ordinary_cells)
		ordinary = _open_block(open, ordinary_cells)
		labelled = _label_regions(ordinary, objective_cell)
	regions_unreachable_after = labelled.sizes.size() - (1 if labelled.main >= 0 else 0)

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

	_build_functional_maps(open, ordinary, labelled, p_seed)
	_build_grid(open)
	_build_crossings(open)
	_build_walls(open, owner)
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
	for mask in masks_ordinary:
		parts.append(hash(mask))
	for mask in small_masks:
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
	return (j + LATTICE_PAD) * stride + (i + LATTICE_PAD)


# The noise grid at the cell nearest `pos`.
func _noise_at(noise: PackedFloat64Array, pos: Vector2) -> float:
	var gx := clampi(int(round(pos.x / SPACING)), 0, dim - 1)
	var gy := clampi(int(round(pos.y / SPACING)), 0, dim - 1)
	return noise[gy * dim + gx]


# A jittered square lattice of centres over the canvas, cell size `cell`, indices
# -LATTICE_PAD .. wc + LATTICE_PAD - 1. The noise (sampled at the lattice cell's own middle) scales
# the jitter, up to JITTER_MAX of the cell: where it is low the plates are more regular. `v` holds
# that noise per key.
func _lattice(noise: PackedFloat64Array, cell: float, layer_seed: int, hx: int, hy: int) -> Dictionary:
	var wc := int(ceil(canvas / cell))
	var stride := wc + 2 * LATTICE_PAD
	var cx := PackedFloat64Array()
	var cy := PackedFloat64Array()
	var v := PackedFloat64Array()
	cx.resize(stride * stride)
	cy.resize(stride * stride)
	v.resize(stride * stride)
	for j in range(-LATTICE_PAD, wc + LATTICE_PAD):
		for i in range(-LATTICE_PAD, wc + LATTICE_PAD):
			var key := _key(i, j, stride)
			var vv := _noise_at(noise, Vector2((i + 0.5) * cell, (j + 0.5) * cell))
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



# The cell of centre c: the square lo..hi cut by the perpendicular bisector against each of
# `others`, each cut pulled in by insets[idx] toward c. Counter-clockwise. The first `near` of
# `others` are always cut; the rest only while their cut can still reach the polygon (it only
# shrinks). `found` receives the index in `others` of every neighbour whose cut leaves an edge.
func _cell_polygon(c: Vector2, others: PackedVector2Array, near: int, lo: Vector2, hi: Vector2, insets: PackedFloat64Array, found: Array) -> PackedVector2Array:
	var poly := PackedVector2Array([lo, Vector2(hi.x, lo.y), hi, Vector2(lo.x, hi.y)])
	var cuts: Array = []
	var reach := INF
	for idx in range(others.size()):
		if idx == near:
			reach = 0.0
			for p in poly:
				reach = maxf(reach, p.distance_to(c))
		var q := others[idx]
		var nrm := (q - c).normalized()
		var d := nrm.dot((c + q) * 0.5) - insets[idx]
		if idx >= near and d - nrm.dot(c) >= reach:
			cuts.append(null)
			continue
		poly = _clip(poly, nrm, d)
		cuts.append([nrm, d])
	for idx in range(others.size()):
		if cuts[idx] == null:
			continue
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
					found.append(idx)
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


# The site (surviving plate centre) nearest `pos`, looking at the 5 by 5 lattice cells around it.
func _nearest_plate(ctx: Dictionary, pos: Vector2) -> int:
	var cell: float = ctx.cell
	var site_pos: PackedVector2Array = ctx.site_pos
	var bi := clampi(int(floor(pos.x / cell)), -1, ctx.wc)
	var bj := clampi(int(floor(pos.y / cell)), -1, ctx.wc)
	var best := -1
	var best_d := INF
	for j in range(bj - 2, bj + 3):
		for i in range(bi - 2, bi + 3):
			for s in ctx.cell_sites[_key(i, j, ctx.stride)]:
				var d := site_pos[s].distance_squared_to(pos)
				if d < best_d:
					best_d = d
					best = s
	return best


# Sets the cells inside a polygon blocked, row by row (even-odd crossings of each row).
func _fill_polygon(open: PackedByteArray, kind: PackedByteArray, owner: PackedInt32Array, base: int, poly: PackedVector2Array, kind_value: int, owner_value: int) -> void:
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
				owner[base + gy * dim + gx] = owner_value


# Layer k (0-based) as a sheet of plates, written into open / kind / owner at k * dim * dim.
# Sites are the plate centres: the lattice centres, minus those the size field removes (a large
# floe), plus four in place of those it splits (small floes). Each plate is kept or dropped by its
# own hash against the density, shifted by the density noise v at the plate (some areas packed,
# some open); one large mass may be grown; the layout places drop the plates around them; rubble
# fills dropped plates that touch a kept one.
func _build_plate_layer(open: PackedByteArray, kind: PackedByteArray, owner: PackedInt32Array, k: int, p_seed: int, shared: PackedFloat64Array) -> void:
	var n := dim * dim
	var coherent: bool = QaPlants.is_active("space-coherent-layers")
	var ls := p_seed if coherent else p_seed + k * LAYER_SEED_STEP
	# The density noise v: one field for every layer when shared, else the layer's own.
	var noise := shared
	if not shared_density or coherent:
		noise = PackedFloat64Array()
		noise.resize(n)
		_sample_layer(noise, k, ls, not coherent, 0)
	# The size field u is always the layer's own.
	var size_noise := PackedFloat64Array()
	size_noise.resize(n)
	_sample_layer(size_noise, k, ls + SIZE_SEED_OFFSET, not coherent, 0)

	var ctx := _lattice(noise, plate_cell_wu, ls, H_JITTER_X, H_JITTER_Y)
	var wc: int = ctx.wc
	var stride: int = ctx.stride
	var cx: PackedFloat64Array = ctx.cx
	var cy: PackedFloat64Array = ctx.cy
	var cell: float = ctx.cell

	# The lowest and highest SIZE_TAIL_SHARE * spread of the lattice's u values (cut points read from
	# the sorted values, so the share does not depend on the noise's range) are removed (low) or
	# split into four (high). Two removed centres never touch, so every point has a surviving
	# centre among its 5 by 5 lattice cells.
	var us := PackedFloat64Array()
	us.resize(stride * stride)
	for j in range(-LATTICE_PAD, wc + LATTICE_PAD):
		for i in range(-LATTICE_PAD, wc + LATTICE_PAD):
			us[_key(i, j, stride)] = _noise_at(size_noise, Vector2((i + 0.5) * cell, (j + 0.5) * cell))
	var sorted_us := us.duplicate()
	sorted_us.sort()
	var tail := int(floor(SIZE_TAIL_SHARE * size_spread * sorted_us.size()))
	var low_cut: float = sorted_us[tail] if tail > 0 else -1.0
	var high_cut: float = sorted_us[sorted_us.size() - 1 - tail] if tail > 0 else 2.0
	var removed := PackedByteArray()
	removed.resize(stride * stride)
	var cell_sites: Array = []
	for _c in range(stride * stride):
		cell_sites.append([])
	# Each {pos, ix, iy (hash coordinates), drop, erode (hash channels), li, lj (lattice cell),
	# plated (lattice cell -1 .. wc: has a polygon), inside (lattice cell on the canvas)}.
	var sites: Array = []
	for j in range(-LATTICE_PAD, wc + LATTICE_PAD):
		for i in range(-LATTICE_PAD, wc + LATTICE_PAD):
			var key := _key(i, j, stride)
			var u := us[key]
			var split := false
			if tail > 0:
				if u > high_cut:
					split = true
				elif u < low_cut:
					var free := true
					for o in NEIGHBOURS:
						var qi: int = i + o.x
						var qj: int = j + o.y
						if qi >= -LATTICE_PAD and qi < wc + LATTICE_PAD and qj >= -LATTICE_PAD and qj < wc + LATTICE_PAD and removed[_key(qi, qj, stride)] == 1:
							free = false
							break
					if free:
						removed[key] = 1
						continue
			var plated := i >= -1 and i <= wc and j >= -1 and j <= wc
			var inside := i >= 0 and i < wc and j >= 0 and j < wc
			if not split:
				cell_sites[key].append(sites.size())
				sites.append({pos = Vector2(cx[key], cy[key]), ix = i, iy = j, drop = H_DROP, erode = H_ERODE, li = i, lj = j, plated = plated, inside = inside})
				continue
			var amp: float = JITTER_MAX * (0.5 + 0.5 * ctx.v[key])
			for b in range(2):
				for a in range(2):
					var sx: float = (i + 0.25 + 0.5 * a + (_hash01(i * 2 + a, j * 2 + b, H_SPLIT_X, ls) * 2.0 - 1.0) * amp * 0.5) * cell
					var sy: float = (j + 0.25 + 0.5 * b + (_hash01(i * 2 + a, j * 2 + b, H_SPLIT_Y, ls) * 2.0 - 1.0) * amp * 0.5) * cell
					cell_sites[key].append(sites.size())
					sites.append({pos = Vector2(sx, sy), ix = i * 2 + a, iy = j * 2 + b, drop = H_SPLIT_DROP, erode = H_SPLIT_ERODE, li = i, lj = j, plated = plated, inside = inside})
	var count := sites.size()
	var site_pos := PackedVector2Array()
	site_pos.resize(count)
	for s in range(count):
		site_pos[s] = sites[s].pos
	ctx.site_pos = site_pos
	ctx.cell_sites = cell_sites

	# Every plated site's cell polygon and the plates it shares a channel with.
	var plated_ids: Array = []
	var inside_ids: Array = []
	var base := {}
	var links := {}
	var nbrs := {}
	for s in range(count):
		var site: Dictionary = sites[s]
		if not site.plated:
			continue
		plated_ids.append(s)
		if site.inside:
			inside_ids.append(s)
		var ids: Array = []
		var others := PackedVector2Array()
		var near := 0
		for ring in range(2):
			for dj in range(-2, 3):
				for di in range(-2, 3):
					if (maxi(absi(di), absi(dj)) <= 1) != (ring == 0):
						continue
					for q in cell_sites[_key(site.li + di, site.lj + dj, stride)]:
						if q != s:
							ids.append(q)
							others.append(site_pos[q])
			if ring == 0:
				near = ids.size()
		var insets := PackedFloat64Array()
		insets.resize(ids.size())
		insets.fill(CHANNEL_WU * 0.5)
		var found: Array = []
		base[s] = _cell_polygon(site.pos, others, near, Vector2((site.li - 2) * cell, (site.lj - 2) * cell), Vector2((site.li + 3) * cell, (site.lj + 3) * cell), insets, found)
		var linked: Array = []
		for idx in found:
			if sites[ids[idx]].plated:
				linked.append(ids[idx])
		links[s] = linked
		nbrs[s] = {ids = ids, others = others, near = near}

	var kept := PackedByteArray()
	var mass := PackedByteArray()
	var cleared := PackedByteArray()
	kept.resize(count)
	mass.resize(count)
	cleared.resize(count)
	# The channels and the eroded corners take part of a plate's area, so the share of plates kept is
	# the blocked percent divided by the share of a plate that stays solid.
	var solid := (1.0 - CHANNEL_WU / cell) * (1.0 - CHANNEL_WU / cell) * (1.0 - ERODE_MAX * 0.5) * (1.0 - ERODE_MAX * 0.5)
	for s in plated_ids:
		var keep_share: float = density / 100.0 / solid + (_noise_at(noise, site_pos[s]) - 0.5) * density_swing if density > 0.0 else -1.0
		var roll := _hash01(sites[s].ix, sites[s].iy, sites[s].drop, ls)
		if shared_density and not coherent:
			# The same roll on every layer for plates whose centroids fall in one coarse cell.
			var centroid := Vector2.ZERO
			for pt in base[s]:
				centroid += pt
			centroid /= base[s].size()
			roll = _hash01(int(floor(centroid.x / plate_cell_wu)), int(floor(centroid.y / plate_cell_wu)), H_DROP, p_seed)
		kept[s] = 1 if roll <= keep_share else 0

	if _hash01(0, 0, H_MASS_ON, ls) < MASS_CHANCE:
		var pick: int = inside_ids[int(_hash01(0, 0, H_MASS_PICK, ls) * inside_ids.size())]
		var pick_centre: Vector2 = site_pos[pick]
		for s in plated_ids:
			if site_pos[s].distance_to(pick_centre) <= MASS_RADIUS_WU:
				mass[s] = 1
				kept[s] = 1

	# The layout places: the plate holding each node and every plate whose centre is near it.
	for node in nodes:
		var home := _nearest_plate(ctx, node.pos)
		for s in plated_ids:
			if cleared[s] == 0 and (s == home or site_pos[s].distance_to(node.pos) <= CLEAR_RADIUS_WU):
				cleared[s] = 1
				if kept[s] == 1:
					plates_cleared += 1
				kept[s] = 0
				mass[s] = 0

	var polys: Array = []
	for s in plated_ids:
		if kept[s] == 0:
			continue
		var site: Dictionary = sites[s]
		var poly: PackedVector2Array = base[s]
		if mass[s] == 1:
			# The channels between two plates of the mass are closed.
			var nb: Dictionary = nbrs[s]
			var insets := PackedFloat64Array()
			for q in nb.ids:
				insets.append(0.0 if mass[q] == 1 else CHANNEL_WU * 0.5)
			poly = _clip_canvas(_cell_polygon(site.pos, nb.others, nb.near, Vector2((site.li - 2) * cell, (site.lj - 2) * cell), Vector2((site.li + 3) * cell, (site.lj + 3) * cell), insets, []))
		else:
			poly = _clip_canvas(poly)
			if poly.size() >= 3:
				poly = _erode(poly, site.ix, site.iy, ls, site.erode)
		if poly.size() < 3:
			continue
		var kind_value := KIND_MASS if mass[s] == 1 else KIND_PLATE
		polys.append({points = poly, kind = kind_value, plate = s})
		_fill_polygon(open, kind, owner, k * n, poly, kind_value, s * 3 + kind_value)
	plates_per_layer.append(polys.size())

	# Rubble: only on dropped plates that share a channel with a kept plate, on a finer lattice;
	# the share follows the noise at the fragment, so it gathers at the edges of packed areas.
	var near_kept := PackedByteArray()
	near_kept.resize(count)
	for s in plated_ids:
		if kept[s] == 0 and cleared[s] == 0:
			for q in links[s]:
				if kept[q] == 1:
					near_kept[s] = 1
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
			if parent < 0 or near_kept[parent] == 0:
				continue
			var around := PackedVector2Array()
			for o in NEIGHBOURS:
				var q := _key(i + o.x, j + o.y, rub.stride)
				around.append(Vector2(rub.cx[q], rub.cy[q]))
			var poly := _cell_polygon(centre, around, 8, Vector2((i - 1) * RUBBLE_CELL_WU, (j - 1) * RUBBLE_CELL_WU), Vector2((i + 2) * RUBBLE_CELL_WU, (j + 2) * RUBBLE_CELL_WU), rubble_insets, [])
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
			_fill_polygon(open, kind, owner, k * n, poly, KIND_RUBBLE, parent * 3 + KIND_RUBBLE)

	ctx.polys = polys
	ctx.base = base
	ctx.links = links
	ctx.noise = noise
	ctx.ls = ls
	_ctx.append(ctx)


# Reachability. Pockets are filled solid; the other regions are joined into the main one by dropping
# plates. Each region, in order, is joined to the nearest region it is not yet joined to: from the
# plate under its nearest cell, breadth-first over the layer's plate adjacency (plates that share a
# channel) to a plate whose centre cell lies in such a region, and every plate on the path becomes
# open water. (Pass 2 walked every region to the objective's plate; on the ordinary map, where every
# narrow channel is solid and the main region starts as the one pool around the objective, that cut
# so many plates that density 70 came out near 50 percent blocked.)
func _fill_and_drop_plates(open: PackedByteArray, kind: PackedByteArray, labelled: Dictionary) -> void:
	var n := dim * dim
	var sizes: Array = labelled.sizes
	var main: int = labelled.main
	var fill := _fill_pockets(open, labelled)
	var labels: PackedInt32Array = labelled.labels
	# plate_region[k]: plate -> id of the region holding its centre cell (unfilled regions only).
	var plate_region: Array = []
	for k in range(LAYERS):
		var regions := {}
		var ctx: Dictionary = _ctx[k]
		for p in ctx.base:
			var at: Vector2 = ctx.site_pos[p]
			var id := labels[k * n + clampi(int(round(at.y / SPACING)), 0, dim - 1) * dim + clampi(int(round(at.x / SPACING)), 0, dim - 1)]
			if id >= 0 and fill[id] == 0:
				regions[p] = id
		plate_region.append(regions)
	var joined := PackedInt32Array()
	joined.resize(sizes.size())
	for id in range(sizes.size()):
		joined[id] = id
	for id in range(sizes.size()):
		if id == main or fill[id] == 1:
			continue
		var c: int = labelled.nearest[id]
		var k := c / n
		var ctx: Dictionary = _ctx[k]
		var gy := (c - k * n) / dim
		var gx := (c - k * n) - gy * dim
		var from := _nearest_plate(ctx, Vector2(gx, gy) * SPACING)
		var path := _plate_path(ctx.links, from, plate_region[k], joined, id)
		if path.is_empty():
			continue
		_drop_plates(open, kind, k, path)
		var root := _root(joined, id)
		for p in path:
			if plate_region[k].has(p):
				joined[_root(joined, plate_region[k][p])] = root


# Reachability by widening. Pockets are filled solid; then, round after round, every region of
# MIN_POCKET_CELLS or more that the main region does not reach is joined to it: the pair of cells
# (one in the region, one in the main region, on the same layer) nearest in the plane is found, and the
# straight line between them is opened with the 3 by 3 block (MIN_PASSAGE_WU / 2 each side of it). The
# fine mask opens, the plates lose the same area (see _cut_polygons), so mask and picture agree.
func _fill_and_widen(open: PackedByteArray, kind: PackedByteArray, owner: PackedInt32Array, labelled: Dictionary, objective_cell: Vector2i, ordinary_cells: int) -> void:
	var n := dim * dim
	_fill_pockets(open, labelled)
	for _round in range(MAX_JOIN_ROUNDS):
		labelled = _label_regions(_open_block(open, ordinary_cells), objective_cell)
		var main: int = labelled.main
		if main < 0:
			return
		var labels: PackedInt32Array = labelled.labels
		var sizes: Array = labelled.sizes
		var cut := {}
		for id in range(sizes.size()):
			if id != main and sizes[id] >= MIN_POCKET_CELLS:
				cut[id] = []
		if cut.is_empty():
			return
		var main_count := PackedInt32Array()
		main_count.resize(LAYERS)
		for c in range(LAYERS * n):
			var id := labels[c]
			if id == main:
				main_count[c / n] += 1
			elif cut.has(id):
				cut[id].append(c)
		var near: Array = []
		near.resize(LAYERS)
		for id in cut:
			_widen_channel(open, kind, owner, labels, main, main_count, near, cut[id], ordinary_cells / 2)


# Opens one channel from the region `cells` (indices over all layers) to the main region.
func _widen_channel(open: PackedByteArray, kind: PackedByteArray, owner: PackedInt32Array, labels: PackedInt32Array, main: int, main_count: PackedInt32Array, near: Array, cells: Array, radius: int) -> void:
	var n := dim * dim
	var best := NO_MAIN_D2
	var best_k := -1
	var from := Vector2i.ZERO
	var to := Vector2i.ZERO
	for c in cells:
		var k: int = c / n
		if main_count[k] == 0:
			continue
		var p: int = c - k * n
		var gy := p / dim
		var gx := p - gy * dim
		var id := labels[c]
		if not ((gx > 0 and labels[c - 1] != id) or (gx < dim - 1 and labels[c + 1] != id) or (gy > 0 and labels[c - dim] != id) or (gy < dim - 1 and labels[c + dim] != id)):
			continue
		if near[k] == null:
			near[k] = _main_nearest(labels, main, k)
		var d2: int = near[k].d2[p]
		if d2 < best:
			best = d2
			best_k = k
			from = Vector2i(gx, gy)
			var src: int = near[k].src[p]
			to = Vector2i(src - (src / dim) * dim, src / dim)
	if best_k < 0:
		return
	var channel := PackedByteArray()
	channel.resize(n)
	var low := Vector2i(maxi(mini(from.x, to.x) - 2 * radius, 0), maxi(mini(from.y, to.y) - 2 * radius, 0))
	var high := Vector2i(mini(maxi(from.x, to.x) + 2 * radius, dim - 1), mini(maxi(from.y, to.y) + 2 * radius, dim - 1))
	# Bresenham from `from` to `to`; every cell within `radius` of a line cell is opened.
	var dx := absi(to.x - from.x)
	var dy := -absi(to.y - from.y)
	var sx := 1 if from.x < to.x else -1
	var sy := 1 if from.y < to.y else -1
	var err := dx + dy
	var x := from.x
	var y := from.y
	while true:
		# At the canvas edge the block slides inward, so it is still a whole block (the ordinary map's
		# opening needs one) and the channel is not left open only on the edge row.
		var block_x := clampi(x - radius, 0, dim - 1 - 2 * radius)
		var block_y := clampi(y - radius, 0, dim - 1 - 2 * radius)
		for cy in range(block_y, block_y + 2 * radius + 1):
			for cx in range(block_x, block_x + 2 * radius + 1):
				channel[cy * dim + cx] = 1
				var c := best_k * n + cy * dim + cx
				if open[c] == 0:
					open[c] = 1
					kind[c] = KIND_PLATE
					owner[c] = -1
					join_cells_opened += 1
		if x == to.x and y == to.y:
			break
		var e2 := 2 * err
		if e2 >= dy:
			err += dy
			x += sx
		if e2 <= dx:
			err += dx
			y += sy
	channels_widened += 1
	_cut_polygons(best_k, channel, low, high)


# For every cell of layer k, the cell of the main region nearest to it in the plane (Euclidean, exact:
# a column pass, then the lower envelope of parabolas along each row): {d2: squared distance in cells,
# src: the nearest main cell's index within the layer}. Cells with no main cell on the layer get d2 of
# at least NO_MAIN_D2.
func _main_nearest(labels: PackedInt32Array, main: int, k: int) -> Dictionary:
	var n := dim * dim
	var base := k * n
	var row_of := PackedInt32Array()
	row_of.resize(n)
	for gx in range(dim):
		var last := -1
		for gy in range(dim):
			if labels[base + gy * dim + gx] == main:
				last = gy
			row_of[gy * dim + gx] = last
		var next := -1
		for gy in range(dim - 1, -1, -1):
			if labels[base + gy * dim + gx] == main:
				next = gy
			var above := row_of[gy * dim + gx]
			if next >= 0 and (above < 0 or next - gy < gy - above):
				row_of[gy * dim + gx] = next
	var d2 := PackedInt32Array()
	d2.resize(n)
	var src := PackedInt32Array()
	src.resize(n)
	var f := PackedFloat64Array()
	f.resize(dim)
	var v := PackedInt32Array()
	v.resize(dim)
	var z := PackedFloat64Array()
	z.resize(dim + 1)
	for gy in range(dim):
		for gx in range(dim):
			var r := row_of[gy * dim + gx]
			f[gx] = float((gy - r) * (gy - r)) if r >= 0 else float(NO_MAIN_D2)
		var top := 0
		v[0] = 0
		z[0] = -INF
		z[1] = INF
		for q in range(1, dim):
			var s := ((f[q] + q * q) - (f[v[top]] + v[top] * v[top])) / float(2 * q - 2 * v[top])
			while s <= z[top]:
				top -= 1
				s = ((f[q] + q * q) - (f[v[top]] + v[top] * v[top])) / float(2 * q - 2 * v[top])
			top += 1
			v[top] = q
			z[top] = s
			z[top + 1] = INF
		top = 0
		for gx in range(dim):
			while z[top + 1] < gx:
				top += 1
			d2[gy * dim + gx] = int((gx - v[top]) * (gx - v[top]) + f[v[top]])
			src[gy * dim + gx] = row_of[gy * dim + v[top]] * dim + v[top]
	return {d2 = d2, src = src}


# Cuts the opened channel (`channel`: 1 per cell, inside the cell box low..high) out of layer k's plate
# polygons by clipping, not by re-deriving the polygons from the mask, so the plates keep their straight
# edges: the channel is the union of the cell squares, taken as one rectangle per run of equal rows, and
# each polygon minus a rectangle is up to four convex pieces (each an ordinary polygon of the layer).
func _cut_polygons(k: int, channel: PackedByteArray, low: Vector2i, high: Vector2i) -> void:
	var half := SPACING * 0.5
	var rects: Array = []
	var above := {}
	for gy in range(low.y, high.y + 1):
		var now := {}
		var gx := low.x
		while gx <= high.x:
			if channel[gy * dim + gx] == 0:
				gx += 1
				continue
			var start := gx
			while gx <= high.x and channel[gy * dim + gx] == 1:
				gx += 1
			var key := start * 4096 + gx
			var at: int
			if above.has(key):
				at = above[key]
				var taller: Rect2 = rects[at]
				taller.size.y += SPACING
				rects[at] = taller
			else:
				at = rects.size()
				rects.append(Rect2(Vector2(start * SPACING - half, gy * SPACING - half), Vector2((gx - start) * SPACING, SPACING)))
			now[key] = at
		above = now
	var box := Rect2(Vector2(low.x * SPACING - half, low.y * SPACING - half), Vector2((high.x - low.x + 1) * SPACING, (high.y - low.y + 1) * SPACING))
	var ctx: Dictionary = _ctx[k]
	var out: Array = []
	for pl in ctx.polys:
		var pieces: Array = [pl.points]
		if _bounds(pl.points).intersects(box):
			for rect in rects:
				var next: Array = []
				for piece in pieces:
					if _bounds(piece).intersects(rect):
						next.append_array(_subtract_rect(piece, rect))
					else:
						next.append(piece)
				pieces = next
		for piece in pieces:
			out.append({points = piece, kind = pl.kind, plate = pl.plate})
	ctx.polys = out


func _bounds(poly: PackedVector2Array) -> Rect2:
	var low := Vector2(INF, INF)
	var high := Vector2(-INF, -INF)
	for p in poly:
		low = Vector2(minf(low.x, p.x), minf(low.y, p.y))
		high = Vector2(maxf(high.x, p.x), maxf(high.y, p.y))
	return Rect2(low, high - low)


# A convex polygon minus an axis-aligned rectangle: the parts left of, right of, below and above it,
# each clipped to what the earlier parts left (so they do not overlap). Parts under one square wu are
# dropped.
func _subtract_rect(poly: PackedVector2Array, rect: Rect2) -> Array:
	var x0 := rect.position.x
	var y0 := rect.position.y
	var x1 := rect.end.x
	var y1 := rect.end.y
	var parts: Array = []
	parts.append(_clip(poly, Vector2(1.0, 0.0), x0))
	var rest := _clip(poly, Vector2(-1.0, 0.0), -x0)
	parts.append(_clip(rest, Vector2(-1.0, 0.0), -x1))
	rest = _clip(rest, Vector2(1.0, 0.0), x1)
	parts.append(_clip(rest, Vector2(0.0, 1.0), y0))
	rest = _clip(rest, Vector2(0.0, -1.0), -y0)
	parts.append(_clip(rest, Vector2(0.0, -1.0), -y1))
	var out: Array = []
	for part in parts:
		var clean := PackedVector2Array()
		for p in part:
			if clean.is_empty() or p.distance_to(clean[clean.size() - 1]) > 0.01:
				clean.append(p)
		if clean.size() > 1 and clean[0].distance_to(clean[clean.size() - 1]) <= 0.01:
			clean.remove_at(clean.size() - 1)
		var area := 0.0
		for i in range(clean.size()):
			area += clean[i].cross(clean[(i + 1) % clean.size()])
		if clean.size() >= 3 and absf(area) * 0.5 >= 1.0:
			out.append(clean)
	return out


func _root(joined: PackedInt32Array, id: int) -> int:
	while joined[id] != id:
		id = joined[id]
	return id


# Plate keys from `from` to the nearest plate (in hops) that lies in a region joined to a different
# root than `own`, inclusive; empty if none is connected.
func _plate_path(links: Dictionary, from: int, plate_region: Dictionary, joined: PackedInt32Array, own: int) -> PackedInt32Array:
	var path := PackedInt32Array()
	if not links.has(from):
		return path
	var own_root := _root(joined, own)
	var parent := {from: -1}
	var queue: Array = [from]
	var head := 0
	var found := -1
	while head < queue.size() and found < 0:
		var cur: int = queue[head]
		head += 1
		if plate_region.has(cur) and _root(joined, plate_region[cur]) != own_root:
			found = cur
			break
		for q in links[cur]:
			if not parent.has(q):
				parent[q] = cur
				queue.append(q)
	if found < 0:
		return path
	var p := found
	while p != -1:
		path.append(p)
		p = parent[p]
	return path


# Opens every cell nearest to a plate on the path and removes its polygons. A plate that held
# anything is recorded in `tunnels` as its outline.
func _drop_plates(open: PackedByteArray, kind: PackedByteArray, k: int, path: PackedInt32Array) -> void:
	var n := dim * dim
	var ctx: Dictionary = _ctx[k]
	for p in path:
		var held := false
		var kept_polys: Array = []
		for pl in ctx.polys:
			if pl.plate == p:
				held = true
			else:
				kept_polys.append(pl)
		ctx.polys = kept_polys
		var outline: PackedVector2Array = ctx.base[p]
		var low := Vector2(INF, INF)
		var high := Vector2(-INF, -INF)
		for pt in outline:
			low = Vector2(min(low.x, pt.x), min(low.y, pt.y))
			high = Vector2(max(high.x, pt.x), max(high.y, pt.y))
		for gy in range(maxi(0, int(floor(low.y / SPACING)) - 1), mini(dim - 1, int(ceil(high.y / SPACING)) + 1) + 1):
			for gx in range(maxi(0, int(floor(low.x / SPACING)) - 1), mini(dim - 1, int(ceil(high.x / SPACING)) + 1) + 1):
				if _nearest_plate(ctx, Vector2(gx, gy) * SPACING) == p:
					var c := k * n + gy * dim + gx
					if open[c] == 0:
						held = true
						open[c] = 1
						kind[c] = KIND_PLATE
		if held:
			var points := outline.duplicate()
			points.append(outline[0])
			tunnels.append({points = points, layer = k + 1})
			plates_cut += 1
			tunnels_cut += 1


# Opens `src` (LAYERS * dim * dim, 1 open) in plane with a square block of `size` cells, 1 or 3 (the
# widths MIN_PASSAGE_WU and SMALL_PASSAGE_WU give on the 100 wu grid): a cell stays open only if a
# block of open cells inside the canvas covers it. A block of one cell, the grid's own element for a
# disc as wide as a cell, is the mask itself.
func _open_block(src: PackedByteArray, size: int) -> PackedByteArray:
	if size <= 1:
		return src.duplicate()
	var n := dim * dim
	var last := dim - 1
	# Erosion: rows, then columns.
	var rows := PackedByteArray()
	rows.resize(src.size())
	for start in range(0, src.size(), dim):
		for i in range(start + 1, start + last):
			rows[i] = src[i - 1] & src[i] & src[i + 1]
	var eroded := PackedByteArray()
	eroded.resize(src.size())
	for k in range(LAYERS):
		for i in range(k * n + dim, (k + 1) * n - dim):
			eroded[i] = rows[i - dim] & rows[i] & rows[i + dim]
	# Dilation: rows, then columns.
	for start in range(0, src.size(), dim):
		rows[start] = eroded[start] | eroded[start + 1]
		rows[start + last] = eroded[start + last - 1] | eroded[start + last]
		for i in range(start + 1, start + last):
			rows[i] = eroded[i - 1] | eroded[i] | eroded[i + 1]
	var out := PackedByteArray()
	out.resize(src.size())
	for k in range(LAYERS):
		var base := k * n
		for i in range(base, base + dim):
			out[i] = rows[i] | rows[i + dim]
		for i in range(base + n - dim, base + n):
			out[i] = rows[i - dim] | rows[i]
		for i in range(base + dim, base + n - dim):
			out[i] = rows[i - dim] | rows[i] | rows[i + dim]
	return out


# The ordinary and small-craft maps, the sections and their numbers, from the final fine mask
# `open`, its ordinary opening and that map's final region labelling.
func _build_functional_maps(open: PackedByteArray, ordinary: PackedByteArray, labelled: Dictionary, p_seed: int) -> void:
	var n := dim * dim
	var small_open := _open_block(open, int(SMALL_PASSAGE_WU / SPACING))
	masks_ordinary = []
	small_masks = []
	section_cells = []
	section_frames = []
	small_section_pct = []
	small_only_pct = []
	var labels: PackedInt32Array = labelled.labels
	for k in range(LAYERS):
		var cells := _build_sections(k)
		var in_section := 0
		var mask_ord := ordinary.slice(k * n, (k + 1) * n)
		var mask_small := mask_ord.duplicate()
		var small_count := 0
		var small_only := 0
		for i in range(n):
			if cells[i] != 0:
				in_section += 1
				mask_small[i] = small_open[k * n + i] | mask_ord[i]
			if mask_small[i] == 1:
				small_count += 1
				if labels[k * n + i] != labelled.main:
					small_only += 1
		masks_ordinary.append(mask_ord)
		small_masks.append(mask_small)
		section_cells.append(cells)
		section_frames.append(_trace_sections(cells))
		small_section_pct.append(100.0 * in_section / n)
		small_only_pct.append(100.0 * small_only / max(small_count, 1))


# Section cells of layer k (0-based): batches of BATCH_PLATES adjacent plates, a cell belonging to
# the plate nearest it. Seeds are, by default, plates where the density noise is in its top
# quartile, taken in hash order, one batch after another; with `sections_near_layout`, the plates at
# the objective, staging and vantage nodes, grown in turns so every place gets a share. Growing
# stops as soon as the sections hold `small_share` percent of the layer's cells.
func _build_sections(k: int) -> PackedByteArray:
	var n := dim * dim
	var cells := PackedByteArray()
	cells.resize(n)
	var target := int(round(small_share / 100.0 * n))
	if target <= 0:
		return cells
	var ctx: Dictionary = _ctx[k]
	var site_pos: PackedVector2Array = ctx.site_pos
	var on_canvas: Array = []
	for p in ctx.base:
		if site_pos[p].x >= 0.0 and site_pos[p].y >= 0.0 and site_pos[p].x <= canvas and site_pos[p].y <= canvas:
			on_canvas.append(p)
	var taken := {}
	var batches: Array = []
	var covered := 0
	if sections_near_layout:
		for node in nodes:
			if node.type == "objective" or node.type == "staging" or node.type == "vantage":
				var seed_plate := _nearest_plate(ctx, node.pos)
				if not taken.has(seed_plate):
					taken[seed_plate] = true
					batches.append([seed_plate])
					covered += _mark_plate(ctx, seed_plate, cells, batches.size())
		for _round in range(BATCH_PLATES - 1):
			for b in range(batches.size()):
				if covered >= target or batches[b].size() >= BATCH_PLATES:
					continue
				var next := _next_plate(ctx, batches[b], taken, on_canvas)
				if next >= 0:
					taken[next] = true
					batches[b].append(next)
					covered += _mark_plate(ctx, next, cells, b + 1)
		return cells
	var noise_at_plate: Array = []
	for p in on_canvas:
		noise_at_plate.append(_noise_at(ctx.noise, site_pos[p]))
	var sorted_noise := noise_at_plate.duplicate()
	sorted_noise.sort()
	var cut: float = sorted_noise[int(SECTION_SEED_QUANTILE * sorted_noise.size())]
	var seeds: Array = []
	for i in range(on_canvas.size()):
		if noise_at_plate[i] >= cut:
			seeds.append([_hash01(on_canvas[i], k, H_SECTION, ctx.ls), on_canvas[i]])
	seeds.sort()
	for entry in seeds:
		if covered >= target:
			break
		var seed_plate: int = entry[1]
		if taken.has(seed_plate):
			continue
		taken[seed_plate] = true
		var batch: Array = [seed_plate]
		batches.append(batch)
		covered += _mark_plate(ctx, seed_plate, cells, batches.size())
		while batch.size() < BATCH_PLATES and covered < target:
			var next := _next_plate(ctx, batch, taken, on_canvas)
			if next < 0:
				break
			taken[next] = true
			batch.append(next)
			covered += _mark_plate(ctx, next, cells, batches.size())
	return cells


# The first untaken plate on the canvas that shares a channel with a member of the batch.
func _next_plate(ctx: Dictionary, batch: Array, taken: Dictionary, on_canvas: Array) -> int:
	for m in batch:
		for q in ctx.links[m]:
			if not taken.has(q) and on_canvas.has(q):
				return q
	return -1


# Marks the cells nearest to plate p with `id` and returns how many were unmarked before.
func _mark_plate(ctx: Dictionary, p: int, cells: PackedByteArray, id: int) -> int:
	var low := Vector2(INF, INF)
	var high := Vector2(-INF, -INF)
	for pt in ctx.base[p]:
		low = Vector2(min(low.x, pt.x), min(low.y, pt.y))
		high = Vector2(max(high.x, pt.x), max(high.y, pt.y))
	var added := 0
	for gy in range(maxi(0, int(floor(low.y / SPACING)) - 1), mini(dim - 1, int(ceil(high.y / SPACING)) + 1) + 1):
		for gx in range(maxi(0, int(floor(low.x / SPACING)) - 1), mini(dim - 1, int(ceil(high.x / SPACING)) + 1) + 1):
			if cells[gy * dim + gx] == 0 and _nearest_plate(ctx, Vector2(gx, gy) * SPACING) == p:
				cells[gy * dim + gx] = id
				added += 1
	return added


# The outline of every section batch of one layer.
func _trace_sections(cells: PackedByteArray) -> Dictionary:
	var by_batch := {}
	for i in range(cells.size()):
		if cells[i] != 0:
			if not by_batch.has(cells[i]):
				by_batch[cells[i]] = []
			by_batch[cells[i]].append(i)
	var wa := PackedVector2Array()
	var wb := PackedVector2Array()
	var wk := PackedByteArray()
	for id in by_batch:
		_trace_walls(by_batch[id], KIND_PLATE, wa, wb, wk)
	return {a = wa, b = wb}


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


# Cells blocked on layer k and k + 1 are traced, per plate (and kind), into wall segments from the
# outline of the plate's such cells, so the two layers can be drawn as one solid body there.
func _build_walls(open: PackedByteArray, owner: PackedInt32Array) -> void:
	var n := dim * dim
	walls = []
	filled_cells_per_pair = []
	for k in range(LAYERS - 1):
		var groups := {}
		var both := 0
		for i in range(n):
			if open[k * n + i] == 0 and open[(k + 1) * n + i] == 0:
				both += 1
				var key: int = owner[k * n + i]
				if not groups.has(key):
					groups[key] = []
				groups[key].append(i)
		filled_cells_per_pair.append(both)
		var wa := PackedVector2Array()
		var wb := PackedVector2Array()
		var wk := PackedByteArray()
		for key in groups:
			_trace_walls(groups[key], KIND_PLATE if key < 0 else key % 3, wa, wb, wk)
		walls.append({a = wa, b = wb, kind = wk})


# The outline of a set of cells by marching squares on a padded local grid; each segment is
# oriented so its outward normal (d.y, -d.x) points to the empty side.
func _trace_walls(cells: Array, kind_value: int, wa: PackedVector2Array, wb: PackedVector2Array, wk: PackedByteArray) -> void:
	var low := Vector2i(dim, dim)
	var high := Vector2i(-1, -1)
	for c in cells:
		var gy: int = c / dim
		var gx: int = c - gy * dim
		low = Vector2i(mini(low.x, gx), mini(low.y, gy))
		high = Vector2i(maxi(high.x, gx), maxi(high.y, gy))
	var origin := low - Vector2i.ONE
	var s := maxi(high.x - low.x, high.y - low.y) + 3
	var local := PackedFloat32Array()
	local.resize(s * s)
	for c in cells:
		var gy: int = c / dim
		local[(gy - origin.y) * s + (c - gy * dim - origin.x)] = 1.0
	var shift := Vector2(origin) * SPACING
	var eps := SPACING * 0.1
	for chain in _march_squares(local, s, 0.5):
		for e in range(chain.size() - 1):
			var a: Vector2 = chain[e] + shift
			var b: Vector2 = chain[e + 1] + shift
			var d := b - a
			if d.length() < 0.01:
				continue
			var nrm := Vector2(d.y, -d.x).normalized()
			var mid := (a + b) * 0.5
			if _local_value(local, s, origin, mid + nrm * eps) > _local_value(local, s, origin, mid - nrm * eps):
				var swap := a
				a = b
				b = swap
			wa.append(a)
			wb.append(b)
			wk.append(kind_value)


func _local_value(local: PackedFloat32Array, s: int, origin: Vector2i, pos: Vector2) -> float:
	var x := clampf(pos.x / SPACING - origin.x, 0.0, s - 1.001)
	var y := clampf(pos.y / SPACING - origin.y, 0.0, s - 1.001)
	var ix := int(x)
	var iy := int(y)
	var tx := x - ix
	var ty := y - iy
	return lerpf(lerpf(local[iy * s + ix], local[iy * s + ix + 1], tx), lerpf(local[(iy + 1) * s + ix], local[(iy + 1) * s + ix + 1], tx), ty)
