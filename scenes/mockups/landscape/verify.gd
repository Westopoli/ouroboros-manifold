extends SceneTree

const KITS_DIR := "res://scenes/mockups/landscape/kits/"
const DEFAULT_CANVAS := 24000.0
const SLOPE_THRESHOLD := 0.85
const CORE_WATER_DIST_WU := 400.0
const MOCKUP_SCENE := "res://scenes/mockups/landscape/landscape_mockup.tscn"
const CONTRACT_KEYS := ["seed", "hash", "canvas_wu", "stability", "kit", "band", "camera_height",
	"elevation_max_wu", "overlay", "city", "timing_ms", "regen_count", "piece_total", "objective_px"]
const PLANTS := ["seed-ignored", "overlay-screen-space", "stability-noop", "flat-terrain", "city-disc", "regen-stall"]

var _failures := 0
var _root: Node


func _initialize() -> void:
	var fm := FieldMap.new()
	fm.generate(11, DEFAULT_CANVAS, 60.0)

	_check_determinism(fm)
	_check_rivers(fm)
	_check_city_core_near_water(fm)
	_check_district_slope(fm)
	_check_chokepoint_kinds(fm)
	_check_kit_vocab(fm)

	await _check_contract()

	if _failures > 0:
		print("VERIFY FAILED: %d check(s)" % _failures)
		quit(1)
		return
	print("VERIFY OK")
	quit(0)


func _check_contract() -> void:
	var packed: PackedScene = load(MOCKUP_SCENE)
	if packed == null:
		_assert(false, "cannot load %s" % MOCKUP_SCENE)
		return
	_root = packed.instantiate()
	get_root().add_child(_root)
	await process_frame
	await process_frame

	if not (_root.has_method("qa_state") and _root.has_method("qa_plant")):
		_assert(false, "root missing qa_state/qa_plant contract")
		return

	var state0: Dictionary = _root.qa_state()
	_assert_contract_shape(state0)

	if _root.has_method("qa_seed") and _root.has_method("qa_set"):
		_check_contract_behavior(state0)
	else:
		_assert(false, "root missing qa_seed/qa_set contract methods")

	for id in PLANTS:
		_assert(_root.qa_plant(id), "qa_plant(%s) must return true" % id)
	_assert(not _root.qa_plant("nope"), "qa_plant('nope') must return false")


func _assert_contract_shape(state: Dictionary) -> void:
	var text := JSON.stringify(state)
	_assert(text != "", "qa_state() did not survive JSON.stringify")
	for key in CONTRACT_KEYS:
		_assert(state.has(key), "qa_state() missing key %s" % key)


func _check_contract_behavior(state0: Dictionary) -> void:
	var t0 := Time.get_ticks_msec()
	_root.qa_seed(11)
	var t1 := Time.get_ticks_msec()
	var hash_11_a = _root.qa_state().hash
	# plant: regen-stall
	_assert(t1 - t0 < 6000, "qa_seed(11) took %dms, expected < 6000ms" % (t1 - t0))

	_root.qa_seed(11)
	var hash_11_b = _root.qa_state().hash
	_assert(hash_11_a == hash_11_b, "qa_seed(11) twice must hash equal")

	# plant: seed-ignored
	_root.qa_seed(12)
	var hash_12 = _root.qa_state().hash
	_assert(hash_11_b != hash_12, "qa_seed(12) must hash differently from qa_seed(11)")

	# plant: flat-terrain
	_assert(state0.elevation_max_wu >= 3000.0, "elevation_max_wu %.1f below 3000" % state0.elevation_max_wu)

	# plant: city-disc
	_assert(state0.city.fraction_within_r_of_core < 0.7, "city fraction_within_r_of_core %.3f not below 0.7" % state0.city.fraction_within_r_of_core)

	# plant: overlay-screen-space
	_assert(state0.overlay.parent_class == "Node3D", "overlay parent_class is %s, expected Node3D" % state0.overlay.parent_class)
	_assert(String(state0.overlay.parent_path) == "World", "overlay parent_path is %s, expected World" % state0.overlay.parent_path)

	_root.qa_set("stability", 20.0)
	var hash_stab20 = _root.qa_state().hash
	_root.qa_set("stability", 90.0)
	var hash_stab90 = _root.qa_state().hash
	# plant: stability-noop
	_assert(hash_stab20 != hash_stab90, "stability 20 vs 90 must hash differently")


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
