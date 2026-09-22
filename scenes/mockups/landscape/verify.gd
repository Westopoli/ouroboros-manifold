extends SceneTree

const KITS_DIR := "res://scenes/mockups/landscape/kits/"
const DEFAULT_CANVAS := 24000.0
const SLOPE_THRESHOLD := 0.85
const CORE_WATER_DIST_WU := 400.0

var _failures := 0


func _init() -> void:
	var fm := FieldMap.new()
	fm.generate(11, DEFAULT_CANVAS, 60.0)

	_check_determinism(fm)
	_check_rivers(fm)
	_check_city_core_near_water(fm)
	_check_district_slope(fm)
	_check_chokepoint_kinds(fm)
	_check_kit_vocab(fm)

	if _failures > 0:
		print("VERIFY FAILED: %d check(s)" % _failures)
		quit(1)
		return
	print("VERIFY OK")
	quit(0)


func _check_determinism(fm: FieldMap) -> void:
	var b := FieldMap.new()
	b.generate(11, DEFAULT_CANVAS, 60.0)
	_assert(fm.compute_hash() == b.compute_hash(), "seed 11 generated twice must hash equal")

	var c := FieldMap.new()
	c.generate(12, DEFAULT_CANVAS, 60.0)
	_assert(fm.compute_hash() != c.compute_hash(), "seed 12 must hash differently from seed 11")

	# Pass 3: a different seed must change the whole derived layout (terrain-first), not
	# only dressing -- check the actual node positions differ, not just the hash.
	var moved := false
	for i in range(min(fm.nodes.size(), c.nodes.size())):
		if fm.nodes[i].pos.distance_to(c.nodes[i].pos) > 50.0:
			moved = true
			break
	_assert(moved, "seed 12 must move at least one spine node, not just re-jitter dressing")


func _check_rivers(fm: FieldMap) -> void:
	_assert(fm.rivers.size() > 0, "at least one river must be traced")
	for r in fm.rivers:
		var rp: PackedVector2Array = r
		if rp.size() < 2:
			_assert(false, "a river polyline has fewer than 2 points")
			continue
		var last_elev := _elevation_at(fm, rp[0])
		var climbed := false
		for i in range(1, rp.size()):
			var e := _elevation_at(fm, rp[i])
			if e > last_elev + 5.0:
				climbed = true
			last_elev = e
		_assert(not climbed, "a river polyline climbs uphill at some point")
		var end_water := _water_at(fm, rp[rp.size() - 1])
		_assert(end_water > 0.5, "a river polyline does not end in water (sea or a lake)")


func _check_city_core_near_water(fm: FieldMap) -> void:
	var core: Vector2 = Vector2.ZERO
	for n in fm.nodes:
		if n.type == "objective":
			core = n.pos
	var dim: int = fm.dim
	var best_d := INF
	for gy in range(dim):
		for gx in range(dim):
			if fm.grid[gy * dim + gx].water > 0.5:
				var d: float = core.distance_to(Vector2(gx, gy) * FieldMap.SPACING)
				best_d = min(best_d, d)
	_assert(best_d <= CORE_WATER_DIST_WU + 300.0, "city core is %.0fwu from water, expected within ~%.0fwu" % [best_d, CORE_WATER_DIST_WU])


func _check_district_slope(fm: FieldMap) -> void:
	var worst := 0.0
	for cell in fm.grid:
		if cell.district >= 1 and cell.slope > worst:
			worst = cell.slope
	_assert(worst <= SLOPE_THRESHOLD, "a district cell has slope %.2f, above the %.2f threshold" % [worst, SLOPE_THRESHOLD])


func _check_chokepoint_kinds(fm: FieldMap) -> void:
	var kinds := {}
	for c in fm.crossings:
		kinds[c.kind] = true
	_assert(kinds.has("bridge"), "no chokepoint crossing is a river/coast bridge")
	_assert(kinds.has("pass"), "no chokepoint crossing is a cliff pass")
	_assert(kinds.has("gate"), "no chokepoint crossing is a wall gate")


func _elevation_at(fm: FieldMap, p: Vector2) -> float:
	var dim: int = fm.dim
	var gx: int = clampi(int(round(p.x / FieldMap.SPACING)), 0, dim - 1)
	var gy: int = clampi(int(round(p.y / FieldMap.SPACING)), 0, dim - 1)
	return fm.grid[gy * dim + gx].elevation


func _water_at(fm: FieldMap, p: Vector2) -> float:
	var dim: int = fm.dim
	var gx: int = clampi(int(round(p.x / FieldMap.SPACING)), 0, dim - 1)
	var gy: int = clampi(int(round(p.y / FieldMap.SPACING)), 0, dim - 1)
	return fm.grid[gy * dim + gx].water


func _check_kit_vocab(fm: FieldMap) -> void:
	var dir := DirAccess.open(KITS_DIR)
	if dir == null:
		_assert(false, "cannot open kits dir %s" % KITS_DIR)
		return

	dir.list_dir_begin()
	var file_name := dir.get_next()
	while file_name != "":
		if not dir.current_is_dir() and file_name.ends_with(".json"):
			_check_one_kit(KITS_DIR + file_name, fm)
		file_name = dir.get_next()
	dir.list_dir_end()


func _check_one_kit(path: String, fm: FieldMap) -> void:
	var kit := Placer.load_kit(path)
	_assert(not kit.is_empty(), "%s failed to parse" % path)
	if kit.is_empty():
		return

	var mesh_names := _collect_mesh_names(kit)
	var bad: Array = []
	for m in mesh_names:
		if m != "none" and not Placer.is_known_mesh_name(m):
			bad.append(m)
	_assert(bad.is_empty(), "%s references unknown mesh name(s): %s" % [path, bad])

	var world := Node3D.new()
	get_root().add_child(world)
	var placer := Placer.new()
	var result := placer.place(fm, kit, world)
	print("%s: %d pieces (%s)" % [kit.get("name", path), result.total, result.by_type])
	world.queue_free()


func _collect_mesh_names(kit: Dictionary) -> Array:
	var names: Array = []
	for rule in kit.get("terrain", []):
		names.append(rule.get("mesh", "none"))
	for rule in kit.get("city", []):
		names.append(rule.get("mesh", "none"))
	for border_kind in kit.get("borders", {}).keys():
		var border: Dictionary = kit.borders[border_kind]
		names.append(border.get("mesh", "none"))
		for crossing_kind in border.get("crossing", {}).keys():
			names.append(border.crossing[crossing_kind].get("mesh", "none"))
	for node_type in kit.get("nodes", {}).keys():
		names.append(kit.nodes[node_type].get("mesh", "none"))
	if kit.has("backdrop"):
		names.append(kit.backdrop.get("mesh", "none"))
	return names


func _assert(condition: bool, message: String) -> void:
	if not condition:
		_failures += 1
		print("FAIL: %s" % message)
