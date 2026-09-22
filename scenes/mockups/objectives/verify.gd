extends SceneTree

const DIR := "res://scenes/mockups/objectives/"
const MOCKUP_SCENE := DIR + "objectives_mockup.tscn"
const ARCHETYPE_NAMES := ["defensive_stand", "siege_breaking", "reconquest", "assault", "suppression",
	"multi_front_defense", "interception", "rear_guard", "containment", "counterinsurgency"]
const ARCHETYPE_KINDS := {
	"defensive_stand": "hold_zone", "siege_breaking": "destroy_targets", "reconquest": "hold_zone",
	"assault": "destroy_targets", "suppression": "eliminate_force", "multi_front_defense": "hold_zone",
	"interception": "destroy_targets", "rear_guard": "escort_to_extraction", "containment": "hold_zone",
	"counterinsurgency": "eliminate_force"}
const CONTRACT_KEYS := ["seed", "hash", "fixture", "archetype", "objective", "satisfiable",
	"route_len_wu", "time_limit_ticks", "skipped", "marker", "tick", "timing_ms", "regen_count"]
const OBJ_KEYS := ["id", "type", "progress", "status", "is_primary", "location"]
const PLANTS := ["objective-on-spawn", "marker-unnamed", "progress-static", "kind-mapping-random", "seed-ignored", "route-ignored"]
const LABEL_MIN_PIXEL_SIZE := 0.5

var _failures := 0


func _initialize() -> void:
	_check_det_1(); _check_seed_2(); _check_kind_3(); _check_place_4(); _check_sat_5(); _check_route_6()
	await _check_name_7()
	_check_prog_8(); _check_shape_9()
	await _check_label_12()
	await _check_json_10()
	await _check_time_11()
	if _failures > 0:
		print("VERIFY FAILED: %d check(s)" % _failures)
		quit(1)
		return
	print("VERIFY OK")
	quit(0)

func _places(fixture_seed: int):
	var script = load(DIR + "places.gd")
	if script == null:
		return null
	var p = script.new()
	p.load_path(DIR + "fixtures/nodes_seed%d.json" % fixture_seed)
	return p

func _mgen():
	return load(DIR + "mission_gen.gd")

func _assert(cond: bool, msg: String) -> bool:
	if not cond:
		_failures += 1
		print("FAIL: %s" % msg)
	return cond

# plant: seed-ignored (seed 12 then equals seed 11 in SEED-2)
func _check_det_1() -> void:
	var mg = _mgen(); var p = _places(11)
	if not _assert(mg != null and p != null, "DET-1 deps missing"):
		return
	var m1 = mg.build("defensive_stand", p, 11)
	var m2 = mg.build("defensive_stand", p, 11)
	_assert(mg.mission_hash(m1) == mg.mission_hash(m2), "DET-1 same seed/archetype/fixture must hash equal")

# plant: seed-ignored
func _check_seed_2() -> void:
	var mg = _mgen(); var p = _places(11)
	if not _assert(mg != null and p != null, "SEED-2 deps missing"):
		return
	var diff := 0
	for a in ARCHETYPE_NAMES:
		if mg.mission_hash(mg.build(a, p, 11)) != mg.mission_hash(mg.build(a, p, 12)):
			diff += 1
	_assert(diff >= 6, "SEED-2 only %d/10 archetypes differ by seed, need >= 6" % diff)

# plant: kind-mapping-random
func _check_kind_3() -> void:
	var mg = _mgen(); var p = _places(11)
	if not _assert(mg != null and p != null, "KIND-3 deps missing"):
		return
	var bad: Array = []
	for a in ARCHETYPE_NAMES:
		if mg.build(a, p, 11).kind != ARCHETYPE_KINDS[a]:
			bad.append(a)
	_assert(bad.is_empty(), "KIND-3 kind mismatch for %s" % [bad])

# plant: objective-on-spawn
func _check_place_4() -> void:
	var mg = _mgen(); var p = _places(11)
	if not _assert(mg != null and p != null, "PLACE-4 deps missing"):
		return
	var bad: Array = []
	for a in ARCHETYPE_NAMES:
		if not _place_ok(mg.build(a, p, 11), p):
			bad.append(a)
	_assert(bad.is_empty(), "PLACE-4 bad placement for %s" % [bad])

func _place_ok(m: Dictionary, p) -> bool:
	var pos := Vector2(m.objective.location.x, m.objective.location.y)
	var kinds := {"hold_zone": "objective", "escort_to_extraction": "extraction", "survive_duration": "staging"}
	if kinds.has(m.kind):
		return _at_any(pos, p.nodes_of(kinds[m.kind]))
	if m.kind == "destroy_targets":
		return _at_any(pos, p.nodes_of("chokepoint") + p.nodes_of("hazard_anchor"))
	if m.kind == "eliminate_force":
		return pos.distance_to(p.enemy_spawn().pos) <= 500.0
	return false

func _at_any(pos: Vector2, arr: Array) -> bool:
	for n in arr:
		if pos.distance_to(n) < 1.0:
			return true
	return false

# plant: objective-on-spawn
func _check_sat_5() -> void:
	var mg = _mgen()
	if not _assert(mg != null, "SAT-5 deps missing"):
		return
	var bad: Array = []
	for fx in [11, 12, 13]:
		var p = _places(fx)
		for a in ARCHETYPE_NAMES:
			var m = mg.build(a, p, 11)
			var d: float = Vector2(m.objective.location.x, m.objective.location.y).distance_to(p.player_spawn().pos)
			if not m.satisfiable or d < 2000.0:
				bad.append("%s@%d" % [a, fx])
	_assert(bad.is_empty(), "SAT-5 unsatisfiable or too close: %s" % [bad])

# plant: route-ignored
func _check_route_6() -> void:
	var pscript = load(DIR + "places.gd"); var mg = _mgen()
	if not _assert(pscript != null and mg != null, "ROUTE-6 deps missing"):
		return
	var p1 = pscript.new()
	p1.load_dict({"canvas": 3000.0, "seed": 11, "nodes": [{"type": "spawn_point", "pos": [0, 1500]}, {"type": "hazard_anchor", "pos": [1500, 1500]}]})
	var a := Vector2(0, 1500); var b := Vector2(3000, 1500)
	var straight := a.distance_to(b)
	var routed: float = p1.route_length(a, b)
	if not _assert(routed > straight + 1.0, "ROUTE-6 route %f does not exceed straight line %f" % [routed, straight]):
		return
	var p2 = pscript.new()
	p2.load_dict(_walled_fixture())
	var m = mg.build("defensive_stand", p2, 11)
	_assert(not m.satisfiable and m.skipped.size() > 0, "ROUTE-6 walled objective must be unsatisfiable with a skip")

func _walled_fixture() -> Dictionary:
	var nodes := [{"type": "objective", "pos": [3000, 3000]}, {"type": "spawn_point", "pos": [100, 100]}, {"type": "spawn_point", "pos": [5900, 5900]}]
	for i in range(26):
		var pos := Vector2(3000, 3000) + Vector2(cos(TAU * i / 26.0), sin(TAU * i / 26.0)) * 400.0
		nodes.append({"type": "hazard_anchor", "pos": [pos.x, pos.y]})
	return {"canvas": 6000.0, "seed": 11, "nodes": nodes}

# plant: marker-unnamed
func _check_name_7() -> void:
	var packed = load(MOCKUP_SCENE)
	if not _assert(packed != null, "NAME-7 cannot load scene"):
		return
	var root = packed.instantiate()
	get_root().add_child(root)
	await process_frame; await process_frame
	var marker := _find_marker(root)
	if not _assert(marker != null, "NAME-7 no Marker node found"):
		root.queue_free()
		return
	var labels := _find_label3ds(marker)
	if _assert(labels.size() == 1, "NAME-7 marker label count %d, expected 1" % labels.size()):
		var st: Dictionary = root.qa_state()
		_assert(labels[0].text != "" and labels[0].text == String(st.marker.name), "NAME-7 label text mismatch: '%s' vs '%s'" % [labels[0].text, st.marker.name])
	root.queue_free()

func _find_marker(node: Node) -> Node:
	for c in node.get_children():
		if c is Marker:
			return c
		var found := _find_marker(c)
		if found != null:
			return found
	return null

func _find_label3ds(node: Node) -> Array:
	var out: Array = []
	for c in node.get_children():
		if c is Label3D:
			out.append(c)
		out.append_array(_find_label3ds(c))
	return out

# plant: progress-static
func _check_prog_8() -> void:
	var mg = _mgen(); var p = _places(11)
	if not _assert(mg != null and p != null, "PROG-8 deps missing"):
		return
	var m = mg.build("defensive_stand", p, 11)
	mg.tick(m, 200)
	var p200 = m.progress
	mg.tick(m, 100)
	var paused_ok := is_equal_approx(m.progress, p200)
	mg.tick(m, 300)
	if not _assert(paused_ok and m.progress > 0.0 and m.progress < 1.0, "PROG-8 tick(600)=%f paused_ok=%s" % [m.progress, paused_ok]):
		return
	while m.status != "complete" and m.tick < 3000:
		mg.tick(m, 100)
	_assert(m.status == "complete", "PROG-8 never completed tick=%d progress=%f" % [m.tick, m.progress])

# plant: none
func _check_shape_9() -> void:
	var mg = _mgen(); var p = _places(11)
	if not _assert(mg != null and p != null, "SHAPE-9 deps missing"):
		return
	var keys: Array = mg.build("defensive_stand", p, 11).objective.keys()
	keys.sort()
	var want: Array = OBJ_KEYS.duplicate()
	want.sort()
	_assert(keys == want, "SHAPE-9 objective keys %s != %s" % [keys, want])

# plant: none
func _check_json_10() -> void:
	var packed = load(MOCKUP_SCENE)
	if not _assert(packed != null, "JSON-10 cannot load scene"):
		return
	var root = packed.instantiate()
	get_root().add_child(root)
	await process_frame; await process_frame
	var st: Dictionary = root.qa_state()
	var missing: Array = []
	for k in CONTRACT_KEYS:
		if not st.has(k):
			missing.append(k)
	if _assert(JSON.stringify(st) != "" and missing.is_empty(), "JSON-10 stringify empty or missing keys %s" % [missing]):
		var bad: Array = []
		for id in PLANTS:
			if not root.qa_plant(id):
				bad.append(id)
		_assert(bad.is_empty() and not root.qa_plant("nope"), "JSON-10 qa_plant bad ids %s" % [bad])
	root.queue_free()

# plant: none
func _check_time_11() -> void:
	var packed = load(MOCKUP_SCENE)
	if not _assert(packed != null, "TIME-11 cannot load scene"):
		return
	var root = packed.instantiate()
	get_root().add_child(root)
	await process_frame; await process_frame
	root.qa_seed(11)
	var st: Dictionary = root.qa_state()
	_assert(float(st.timing_ms.gen) < 200.0, "TIME-11 gen %f ms" % float(st.timing_ms.gen))
	root.queue_free()

# plant: marker-unnamed
func _check_label_12() -> void:
	var packed = load(MOCKUP_SCENE)
	if not _assert(packed != null, "LABEL-12 cannot load scene"):
		return
	var root = packed.instantiate()
	get_root().add_child(root)
	await process_frame; await process_frame
	var labels := _find_label3ds(root)
	var bad: Array = []
	for l in labels:
		if l.pixel_size < LABEL_MIN_PIXEL_SIZE or l.text == "":
			bad.append("%s(px=%.3f,text='%s')" % [l.name, l.pixel_size, l.text])
	_assert(not labels.is_empty() and bad.is_empty(), "LABEL-12 bad Label3D nodes %s" % [bad])
	root.queue_free()
