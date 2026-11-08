extends "res://tests/support/vg_c_case.gd"
# Rule pins: none (prototype fix: no S- or R- id). Westley 2026-11-08: "water needs to be based on height, not picked".
# Evidence: docs/northstar/plans/decision_pack_2026-10-18/followups/02_terrain_obeys_legend.md section 4 (the stripes).
# Run: scripts/run_godot_tests.sh tests/test_mockup_landscape_waterline.gd   (headless, no display needed)
# Style from the older lakefill test (git show 7218f105:tests/test_mockup_landscape_lakefill.gd); thresholds are not reused.
#
# Piece: scenes/mockups/landscape/field_map.gd, _build_water. Contract the builder implements:
#   1. Lakes: breadth-first, UNCAPPED fill to the waterline elevation[seed] + FieldMap.DRAFT_LAKE_FILL_HEIGHT (150).
#   2. Rivers: water is stamped only on cells with elevation <= nearest path point elevation + FieldMap.DRAFT_RIVER_BAND (150);
#      path points steeper than FieldMap.DRAFT_RIVER_MAX_GRADE (20 deg) are not stamped (a dry mountain stream).
#
# FIXTURE CHOICES (the contract gives no definitions; each is a fixture choice, not a threshold):
#   - Data read: FieldMap.new(); generate(seed, canvas); a cell is WATER when grid[i].water >= 0.5 (the coast trace's 0.5);
#     elevation is grid[i].elevation (the shipped, post-ramp elevation the player sees).
#   - River corridor: every cell whose centre is within RIVER_CORRIDOR_WU of a point of fm.rivers (path vertices).
#   - Sea water: water cell with elevation <= 0 (the sea ramp is smoothstep(60,-60), water >= 0.5 exactly when elevation <= 0).
#   - Lake water: a water cell outside the corridor and not sea.
#   - Perched pair: a lake water cell with a 4-neighbour dry cell lower by more than PERCHED_DROP_WU.
#   - Flips per row: both directions (water to land and land to water) between x and x-1 over the box, divided by rows
#     (the probe's metric: x runs box.x+1 .. box.end.x-1).
#   - Nearest path point (river rule): nearest point over all of fm.rivers by distance; its elevation is the grid elevation of
#     the cell at round(point / SPACING).

const FIELD_MAP := "res://scenes/mockups/landscape/field_map.gd"

# Westley owns every threshold below. The numbers are drafts from the brief; a value nobody gave is marked DRAFT.
const DRAFT_RIVER_CORRIDOR_WU := 250.0  # Westley owns this threshold (DRAFT-river-corridor)
const DRAFT_LAKE_FILL_HEIGHT := 150.0  # Westley owns this threshold (DRAFT-lake-fill-height)
const DRAFT_RIVER_BAND := 150.0  # Westley owns this threshold (DRAFT-river-band)
const DRAFT_RIVER_MAX_GRADE := 20.0  # Westley owns this threshold (DRAFT-river-max-grade, degrees)
const PERCHED_DROP_WU := 20.0  # Westley owns this threshold (a water cell this much above a dry neighbour is perched)
const MAX_PERCHED_PAIRS := 0  # Westley owns this threshold
const MAX_FLIPS_PER_ROW := 2.0  # Westley owns this threshold
const CONTROL_MIN_PERCHED := 100  # Westley owns this threshold (positive control: the old loop must score above this on seed 3)
const OLD_LOOP_CAP := 1500  # the old loop's cell cap, copied into the reference function
const HEIGHT_EPS := 0.01  # float slack for the river-rule comparison

const CANVAS := 16000.0
const BIG_CANVAS := 24000.0
const CASES := [[1, CANVAS], [2, CANVAS], [3, CANVAS], [4, CANVAS], [5, CANVAS], [1, BIG_CANVAS]]
# Flip boxes (probe boxes): seed -> Rect2i(x, y, w, h) in cells, canvas 16,000.
const FLIP_BOXES := {1: Rect2i(118, 0, 42, 80), 3: Rect2i(65, 0, 45, 60)}

var _fm_script: GDScript = null


func _run() -> void:
	_fm_script = load(FIELD_MAP) as GDScript
	_check(_fm_script != null, "missing script: " + FIELD_MAP)
	if _fm_script == null:
		return
	_consts_exist()
	_control_old_loop()
	for c in CASES:
		_case(int(c[0]), float(c[1]))
	_determinism(1)
	_determinism(3)


func _gen(p_seed: int, p_canvas: float):
	var fm = _fm_script.new()
	fm.generate(p_seed, p_canvas)
	return fm


func _water_mask(fm) -> PackedByteArray:
	var n: int = fm.dim * fm.dim
	var w := PackedByteArray()
	w.resize(n)
	for i in range(n):
		w[i] = 1 if float(fm.grid[i].water) >= 0.5 else 0
	return w


func _elev(fm) -> PackedFloat32Array:
	var n: int = fm.dim * fm.dim
	var e := PackedFloat32Array()
	e.resize(n)
	for i in range(n):
		e[i] = fm.grid[i].elevation
	return e


# 1 for each cell whose centre lies within DRAFT_RIVER_CORRIDOR_WU of a point of fm.rivers.
func _corridor(fm) -> PackedByteArray:
	var d: int = fm.dim
	var sp: float = _fm_script.SPACING
	var m := PackedByteArray()
	m.resize(d * d)
	var reach := int(ceil(DRAFT_RIVER_CORRIDOR_WU / sp))
	for r in fm.rivers:
		for p in (r as PackedVector2Array):
			var cx := int(round(p.x / sp))
			var cy := int(round(p.y / sp))
			for gy in range(maxi(cy - reach, 0), mini(cy + reach, d - 1) + 1):
				for gx in range(maxi(cx - reach, 0), mini(cx + reach, d - 1) + 1):
					if Vector2(gx * sp, gy * sp).distance_to(p) <= DRAFT_RIVER_CORRIDOR_WU:
						m[gy * d + gx] = 1
	return m


# Perched pairs among lake water cells; `skip` (may be empty) marks cells excluded (river corridor).
func _perched_pairs(d: int, elev: PackedFloat32Array, water: PackedByteArray, skip: PackedByteArray) -> int:
	var n := 0
	for i in range(d * d):
		if water[i] == 0 or elev[i] <= 0.0:
			continue  # dry, or sea
		if skip.size() > 0 and skip[i] == 1:
			continue
		var gx := i % d
		var gy := i / d
		for o in [Vector2i(-1, 0), Vector2i(1, 0), Vector2i(0, -1), Vector2i(0, 1)]:
			var nx: int = gx + o.x
			var ny: int = gy + o.y
			if nx < 0 or nx >= d or ny < 0 or ny >= d:
				continue
			var ni := ny * d + nx
			if water[ni] == 0 and elev[i] - elev[ni] > PERCHED_DROP_WU:
				n += 1
	return n


func _flips_per_row(d: int, water: PackedByteArray, box: Rect2i) -> float:
	var flips := 0
	for y in range(box.position.y, box.end.y):
		for x in range(box.position.x + 1, box.end.x):
			if water[y * d + x] != water[y * d + x - 1]:
				flips += 1
	return float(flips) / float(box.size.y)


func _case(p_seed: int, p_canvas: float) -> void:
	var fm = _gen(p_seed, p_canvas)
	var d: int = fm.dim
	var tag := "seed %d canvas %d" % [p_seed, int(p_canvas)]
	var water := _water_mask(fm)
	var elev := _elev(fm)
	var corridor := _corridor(fm)
	_check(fm.rivers.size() > 0, "%s: premise: the map has no river, the corridor and river-rule checks prove nothing" % tag)

	# (a) lake perched pairs
	var perched := _perched_pairs(d, elev, water, corridor)
	print("%s: lake perched pairs outside the river corridor: %d" % [tag, perched])
	_check(perched <= MAX_PERCHED_PAIRS, "%s: lake: %d water cells sit more than %s wu above a dry 4-neighbour outside the river corridor (limit %d): the lake is not filled to a height" % [tag, perched, PERCHED_DROP_WU, MAX_PERCHED_PAIRS])

	# (b) stripes: flips per row in the probe box
	if p_canvas == CANVAS and FLIP_BOXES.has(p_seed):
		var fpr := _flips_per_row(d, water, FLIP_BOXES[p_seed])
		print("%s: flips per row in box %s: %.2f" % [tag, FLIP_BOXES[p_seed], fpr])
		_check(fpr <= MAX_FLIPS_PER_ROW, "%s: stripes: %.2f water/land flips per row in box %s (limit %s)" % [tag, fpr, FLIP_BOXES[p_seed], MAX_FLIPS_PER_ROW])

	# (c) river rule: no corridor water cell higher than its nearest path point + band
	var pts: Array = []  # [Vector2 world, float elevation]
	var sp: float = _fm_script.SPACING
	for r in fm.rivers:
		for p in (r as PackedVector2Array):
			var px := clampi(int(round(p.x / sp)), 0, d - 1)
			var py := clampi(int(round(p.y / sp)), 0, d - 1)
			pts.append([p, elev[py * d + px]])
	var worst := -1e9
	var worst_cell := -1
	var bad := 0
	for i in range(d * d):
		if water[i] == 0 or corridor[i] == 0:
			continue
		var cp := Vector2(i % d, i / d) * sp
		var best_dist := INF
		var best_h := 0.0
		for pe in pts:
			var dd: float = cp.distance_to(pe[0])
			if dd < best_dist:
				best_dist = dd
				best_h = pe[1]
		var over: float = elev[i] - (best_h + DRAFT_RIVER_BAND)
		if over > HEIGHT_EPS:
			bad += 1
		if over > worst:
			worst = over
			worst_cell = i
	print("%s: river-rule violations: %d (worst %.1f wu over, cell %d)" % [tag, bad, worst, worst_cell])
	_check(bad == 0, "%s: river rule: %d corridor water cells lie more than %s wu above the nearest river path point (worst %.1f wu over, cell %d)" % [tag, bad, DRAFT_RIVER_BAND, worst, worst_cell])

	# (g) sea unchanged: every cell below sea level is water
	var below := 0
	var below_wet := 0
	for i in range(d * d):
		if elev[i] < 0.0:
			below += 1
			if water[i] == 1:
				below_wet += 1
	_check(below > 0, "%s: premise: no cell below sea level" % tag)
	_check(below_wet == below, "%s: sea: %d of %d cells below sea level are water" % [tag, below_wet, below])


# (d) two generates of one seed give the identical water array.
func _determinism(p_seed: int) -> void:
	var a = _gen(p_seed, CANVAS)
	var b = _gen(p_seed, CANVAS)
	var ha := _water_hash(a)
	var hb := _water_hash(b)
	print("seed %d: water hash %d / %d" % [p_seed, ha, hb])
	_check(ha == hb, "seed %d: determinism: two generates give different water arrays (%d vs %d)" % [p_seed, ha, hb])


func _water_hash(fm) -> int:
	var buf := PackedFloat32Array()
	buf.resize(fm.dim * fm.dim)
	for i in range(fm.dim * fm.dim):
		buf[i] = fm.grid[i].water
	return hash(buf.to_byte_array())


# (e) named consts exist with the stated defaults.
func _consts_exist() -> void:
	var consts: Dictionary = _fm_script.get_script_constant_map()
	var want := {"DRAFT_LAKE_FILL_HEIGHT": DRAFT_LAKE_FILL_HEIGHT, "DRAFT_RIVER_BAND": DRAFT_RIVER_BAND, "DRAFT_RIVER_MAX_GRADE": DRAFT_RIVER_MAX_GRADE}
	for k in want:
		_check(consts.has(k), "consts: FieldMap.%s does not exist" % k)
		if consts.has(k):
			_check(is_equal_approx(float(consts[k]), float(want[k])), "consts: FieldMap.%s is %s, expected %s" % [k, consts[k], want[k]])


# (f) POSITIVE CONTROL, green on main: the OLD lake loop (depth-first, 1,500-cell cap, copied verbatim from _flood_lake) over the
# real seed 3 elevation scores above CONTROL_MIN_PERCHED perched pairs, so detector (a) can fail. The same detector scores
# 0 on an uncapped breadth-first fill, so it can also pass.
func _control_old_loop() -> void:
	var fm = _gen(3, CANVAS)
	var d: int = fm.dim
	var elev := _elev(fm)
	var seeds: Array = fm._find_lake_seeds(elev)
	_check(seeds.size() > 0, "control: premise: seed 3 has no lake seeds")
	for mode in ["old", "fixed"]:
		var w := PackedFloat32Array()
		w.resize(d * d)
		for i in range(d * d):
			w[i] = smoothstep(60.0, -60.0, elev[i])
		for s in seeds:
			if mode == "old":
				_old_flood(d, elev, w, s)
			else:
				_bfs_flood(d, elev, w, s)
		var mask := PackedByteArray()
		mask.resize(d * d)
		for i in range(d * d):
			mask[i] = 1 if w[i] >= 0.5 else 0
		var n := _perched_pairs(d, elev, mask, PackedByteArray())
		print("control seed 3 %s lake loop: perched pairs %d" % [mode, n])
		if mode == "old":
			_check(n > CONTROL_MIN_PERCHED, "CONTROL: the old depth-first capped loop scores only %d perched pairs on seed 3 (want > %d): the detector cannot see the fault" % [n, CONTROL_MIN_PERCHED])
		else:
			_check(n == 0, "CONTROL: an uncapped breadth-first fill scores %d perched pairs on seed 3 (want 0): the detector flags a correct fill" % n)


# Reference copy of the old _flood_lake (field_map.gd): depth-first (pop_back), capped at OLD_LOOP_CAP visits.
func _old_flood(d: int, elev: PackedFloat32Array, water: PackedFloat32Array, seed_idx: int) -> void:
	var fill_level: float = elev[seed_idx] + DRAFT_LAKE_FILL_HEIGHT
	var visited := {seed_idx: true}
	var queue: Array = [seed_idx]
	var visits := 0
	while not queue.is_empty() and visits < OLD_LOOP_CAP:
		var idx: int = queue.pop_back()
		visits += 1
		if elev[idx] > fill_level:
			continue
		water[idx] = max(water[idx], 1.0)
		_push_neighbours(d, elev, fill_level, visited, queue, idx)


# Reference breadth-first, uncapped fill (the contract's lake rule).
func _bfs_flood(d: int, elev: PackedFloat32Array, water: PackedFloat32Array, seed_idx: int) -> void:
	var fill_level: float = elev[seed_idx] + DRAFT_LAKE_FILL_HEIGHT
	var visited := {seed_idx: true}
	var queue: Array = [seed_idx]
	var head := 0
	while head < queue.size():
		var idx: int = queue[head]
		head += 1
		if elev[idx] > fill_level:
			continue
		water[idx] = max(water[idx], 1.0)
		_push_neighbours(d, elev, fill_level, visited, queue, idx)


func _push_neighbours(d: int, elev: PackedFloat32Array, fill_level: float, visited: Dictionary, queue: Array, idx: int) -> void:
	var gx := idx % d
	var gy := idx / d
	for o in [Vector2i(-1, 0), Vector2i(1, 0), Vector2i(0, -1), Vector2i(0, 1)]:
		var nx: int = gx + o.x
		var ny: int = gy + o.y
		if nx < 0 or nx >= d or ny < 0 or ny >= d:
			continue
		var ni := ny * d + nx
		if not visited.has(ni) and elev[ni] <= fill_level:
			visited[ni] = true
			queue.append(ni)
