extends SceneTree

# Prototype selftest for walker_grid.gd (disposable). Run:
#   scripts/run_godot_tests.sh scenes/mockups/walkers/walkers_selftest.gd

const Grid := preload("res://scenes/mockups/walkers/walker_grid.gd")
const SEEDS := [11, 12, 13]
const PAIRS := 8

var _pass := 0
var _fail := 0
var _calls := 0
var _usec := 0
var _worst_usec := 0


func _initialize() -> void:
	for sd in SEEDS:
		_seed_checks(sd)
	print("\nPASS: %d  FAIL: %d" % [_pass, _fail])
	print("route calls: %d  mean %.1f ms  worst %.1f ms" % [_calls, _usec / 1000.0 / maxi(_calls, 1), _worst_usec / 1000.0])
	print("=== GREEN ===" if _fail == 0 else "=== RED ===")
	quit(0 if _fail == 0 else 1)


func _check(ok: bool, msg: String) -> void:
	if ok:
		_pass += 1
	else:
		_fail += 1
		print("FAIL: " + msg)


func _walk(g, a: Vector2, b: Vector2, opt: String) -> Dictionary:
	var t := Time.get_ticks_usec()
	var r: Dictionary = g.route_walker(a, b, opt)
	var d := Time.get_ticks_usec() - t
	_calls += 1
	_usec += d
	_worst_usec = maxi(_worst_usec, d)
	return r


func _fly(g, a: Vector2, b: Vector2, layer: int, climb: bool) -> Dictionary:
	var t := Time.get_ticks_usec()
	var r: Dictionary = g.route_flyer(a, b, layer, climb)
	var d := Time.get_ticks_usec() - t
	_calls += 1
	_usec += d
	_worst_usec = maxi(_worst_usec, d)
	return r


func _cells(g, pred: Callable) -> Array:
	var out: Array = []
	for i in range(g.dim * g.dim):
		if pred.call(i):
			out.append(i)
	return out


func _seed_checks(sd: int) -> void:
	var t0 := Time.get_ticks_usec()
	var g = Grid.new(sd)
	print("seed %d: grid %dx%d cells of %d wu, built in %.0f ms, walkable %.1f%%" % [sd, g.dim, g.dim, int(g.cell), (Time.get_ticks_usec() - t0) / 1000.0, g.walkable_share() * 100.0])
	var walk: Array = Array(g.main_cells)
	var share: float = 100.0 * walk.size() / (g.dim * g.dim)
	print("  main walkable region %.1f%% of cells" % share)
	var steep: Array = _cells(g, func(i): return g.walkable[i] == 0 and g.height[i] > 0.0)
	var rng := RandomNumberGenerator.new()
	rng.seed = sd

	# routes stay on walkable cells, for every option
	var pairs: Array = []
	for k in range(PAIRS):
		pairs.append([walk[rng.randi() % walk.size()], walk[rng.randi() % walk.size()]])
	var bad := 0
	for pr in pairs:
		for opt in ["a", "b", "c"]:
			var r := _walk(g, g.cell_pos(pr[0]), g.cell_pos(pr[1]), opt)
			for p in r.points:
				if not g.walkable_at(p):
					bad += 1
	_check(bad == 0, "seed %d: %d route points in non-walkable cells" % [sd, bad])

	# target inside steep ground: ends at a reachable cell, reached = false
	if steep.is_empty():
		_check(false, "seed %d: no steep cell to aim at" % sd)
	else:
		var tgt: Vector2 = g.cell_pos(steep[steep.size() / 2])
		var r := _walk(g, g.cell_pos(walk[0]), tgt, "a")
		_check(not r.reached and g.walkable_at(r.end), "seed %d: steep target reached=%s end walkable=%s" % [sd, r.reached, g.walkable_at(r.end)])
		print("  steep target %s: ends at %s, %.0f wu from it" % [tgt, r.end, r.end.distance_to(tgt)])

	# option b vs a: longer when the route gains height, same when it stays level
	var gain_ok := false
	var level_ok := false
	var level_found := false
	for k in range(60):
		var a: int = walk[rng.randi() % walk.size()]
		var b: int = walk[rng.randi() % walk.size()]
		var ra := _walk(g, g.cell_pos(a), g.cell_pos(b), "a")
		if ra.points.size() < 2:
			continue
		var maxstep := 0.0
		for i in range(1, ra.points.size()):
			maxstep = maxf(maxstep, absf(g.height_at(ra.points[i]) - g.height_at(ra.points[i - 1])))
		var rb := _walk(g, g.cell_pos(a), g.cell_pos(b), "b")
		var ta: float = ra.seconds_at.call(80.0)
		var tb: float = rb.seconds_at.call(80.0)
		if not gain_ok and g.height[b] - g.height[a] > 100.0:
			gain_ok = true
			_check(tb > ta, "seed %d: gain route b %.2f not > a %.2f" % [sd, tb, ta])
			print("  gain route %.0f wu up: a %.1f s, b %.1f s, c %.1f s at speed 80" % [g.height[b] - g.height[a], ta, tb, _walk(g, g.cell_pos(a), g.cell_pos(b), "c").seconds_at.call(80.0)])
		if not level_found and maxstep < 0.01 and ra.points.size() > 3:
			level_found = true
			level_ok = absf(tb - ta) < 1e-3
			_check(level_ok, "seed %d: level route b %.4f vs a %.4f" % [sd, tb, ta])
	# a level route may be missing from random pairs: search neighbours of flat cells
	if not level_found:
		for i in walk:
			if i + 3 < g.dim * g.dim and (i % g.dim) < g.dim - 4 and g.walkable[i + 3] == 1 and absf(g.height[i] - g.height[i + 3]) < 0.01 and absf(g.height[i] - g.height[i + 1]) < 0.01 and absf(g.height[i] - g.height[i + 2]) < 0.01:
				var ra := _walk(g, g.cell_pos(i), g.cell_pos(i + 3), "a")
				var rb := _walk(g, g.cell_pos(i), g.cell_pos(i + 3), "b")
				var ok: bool = ra.length == rb.length and absf(ra.cost - rb.cost) < 1e-3 and ra.points.size() == 4
				level_found = true
				_check(ok, "seed %d: level 3-cell route a %.3f b %.3f" % [sd, ra.cost, rb.cost])
				break
	_check(gain_ok, "seed %d: no height-gaining route found" % sd)
	_check(level_found, "seed %d: no level route found" % sd)

	# flyer on layer 1 to a band 3 place
	var low: Array = _cells(g, func(i): return g.band[i] == 1 and g.height[i] > 0.0)
	var high: Array = _cells(g, func(i): return g.band[i] == 3)
	if low.is_empty() or high.is_empty():
		_check(false, "seed %d: no band 1 or band 3 cell (low %d, high %d)" % [sd, low.size(), high.size()])
	else:
		var from: Vector2 = g.cell_pos(low[low.size() / 3])
		var to: Vector2 = g.cell_pos(high[high.size() / 2])
		var no_climb := _fly(g, from, to, 1, false)
		var climb := _fly(g, from, to, 1, true)
		_check(not no_climb.reached, "seed %d: layer 1 flyer arrived at a band 3 place without climbing" % sd)
		_check(climb.reached and climb.transfers.size() >= 2 and climb.end.distance_to(to) < g.cell, "seed %d: climbing flyer reached=%s transfers=%d" % [sd, climb.reached, climb.transfers.size()])
		print("  flyer layer 1 to band 3: no-climb ends %.0f wu short; climb %d transfers, %.0f s at speed 80" % [no_climb.end.distance_to(to), climb.transfers.size(), climb.seconds_at.call(80.0)])

	# determinism
	var d1 := _walk(g, g.cell_pos(pairs[0][0]), g.cell_pos(pairs[0][1]), "b")
	var d2 := _walk(g, g.cell_pos(pairs[0][0]), g.cell_pos(pairs[0][1]), "b")
	_check(d1.points == d2.points and d1.cost == d2.cost and d1.length == d2.length, "seed %d: walker routing not deterministic" % sd)
	var f1 := _fly(g, Vector2(500, 500), Vector2(15000, 14000), 2, true)
	var f2 := _fly(g, Vector2(500, 500), Vector2(15000, 14000), 2, true)
	_check(f1.points == f2.points and f1.length == f2.length, "seed %d: flyer routing not deterministic" % sd)

	# corner to corner
	var cc := _walk(g, g.cell_pos(_nearest_in(g, walk, Vector2(0, 0))), g.cell_pos(_nearest_in(g, walk, Vector2(16000, 16000))), "a")
	print("  corner to corner (walker, option a): reached %s, %.0f wu along ground, %d bands crossed; seconds at 40 / 80 / 150: %.0f / %.0f / %.0f" % [cc.reached, cc.length, cc.bands_crossed, cc.seconds_at.call(40.0), cc.seconds_at.call(80.0), cc.seconds_at.call(150.0)])


func _nearest_in(g, cells: Array, p: Vector2) -> int:
	var best: int = cells[0]
	for i in cells:
		if g.cell_pos(i).distance_squared_to(p) < g.cell_pos(best).distance_squared_to(p):
			best = i
	return best
