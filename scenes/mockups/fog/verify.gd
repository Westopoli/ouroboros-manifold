extends SceneTree

const MOCKUP_SCENE := "res://scenes/mockups/fog/fog_mockup.tscn"
const FIXTURE_PATH := "res://scenes/mockups/fog/fixtures/map_seed11.json"
const SCENARIO_PATH := "res://scenes/mockups/fog/scenarios/patrol.json"
const DIM := 64
const CONTRACT_KEYS := ["seed", "hash", "phase", "tick", "memory", "visible_enemy_uids", "view_enemy_uids",
	"enemy_count_total", "cells", "circles", "enemies_px", "timing_ms", "regen_count"]
const PLANTS := ["fog-leak", "no-memory", "recon-shows-enemy", "radius-ignored", "los-ignored", "seed-ignored"]

var _failures := 0
var _root: Node

func _initialize() -> void:
	_check_det1()
	_check_vis2()
	_check_los3()
	_check_sym8()
	_check_mem6()
	_check_time10()
	_check_seed11()
	await _check_scene()
	if _failures > 0:
		print("VERIFY FAILED: %d check(s)" % _failures)
		quit(1)
		return
	print("VERIFY OK")
	quit(0)

func _assert(cond: bool, msg: String) -> void:
	if not cond:
		_failures += 1
		print("FAIL: %s" % msg)

func _mk_friendly(uid: int, pos: Vector2, sensor: float) -> Dictionary:
	return {"uid": uid, "pos": pos, "sensor_wu": sensor, "layer": 0, "waypoints": [], "wp_idx": 0, "speed": 0.0}

func _mk_enemy(uid: int, pos: Vector2) -> Dictionary:
	return {"uid": uid, "center": pos, "radius": 0.0, "angular_speed": 0.0, "phase_offset": 0.0, "pos": pos}

# plant: seed-ignored
func _check_det1() -> void:
	var hashes := []
	for sd in [11, 11, 12]:
		var t := FogTruth.new()
		t.load_fixture(FIXTURE_PATH)
		t.load_scenario(SCENARIO_PATH)
		t.generate(sd)
		t.phase = "mission"
		for i in range(300):
			t.step()
		hashes.append(t.compute_hash())
	_assert(hashes[0] == hashes[1] and hashes[0] != hashes[2], "DET-1 same seed equal, seed 12 differs")

# plant: radius-ignored
func _check_vis2() -> void:
	var t := FogTruth.new()
	t.friendlies = [_mk_friendly(1, Vector2.ZERO, 700.0)]
	var ok := true
	for c in [[650.0, true], [750.0, false]]:
		t.enemies = [_mk_enemy(900, Vector2(c[0], 0))]
		ok = ok and t.compute_visibility().visible_enemy_uids.has(900) == c[1]
	t.zones = [{"kind": "interference", "pos": Vector2.ZERO, "radius": 1000.0, "intensity": 0.5}]
	for c in [[350.0, true], [351.0, false]]:
		t.enemies = [_mk_enemy(900, Vector2(c[0], 0))]
		ok = ok and t.compute_visibility().visible_enemy_uids.has(900) == c[1]
	t.zones = []
	t.friendlies = [_mk_friendly(1, Vector2.ZERO, 300.0), _mk_friendly(2, Vector2(2000, 0), 300.0)]
	t.enemies = [_mk_enemy(910, Vector2(100, 0)), _mk_enemy(911, Vector2(2100, 0)), _mk_enemy(912, Vector2(5000, 0))]
	var u: Array = t.compute_visibility().visible_enemy_uids
	ok = ok and u.has(910) and u.has(911) and not u.has(912)
	_assert(ok, "VIS-2 sensor 700/interference 0.5/union numbers")

# plant: los-ignored
func _check_los3() -> void:
	var t := FogTruth.new()
	t.friendlies = [_mk_friendly(1, Vector2.ZERO, 1000.0)]
	t.obstacles = [{"pos": Vector2(400, 0), "half_extents": Vector2(100, 300), "tall": true}]
	t.enemies = [_mk_enemy(950, Vector2(800, 0))]
	var blocked_ok: bool = not t.compute_visibility().visible_enemy_uids.has(950)
	t.obstacles = []
	var open_ok: bool = t.compute_visibility().visible_enemy_uids.has(950)
	_assert(blocked_ok and open_ok, "LOS-3 tall obstacle blocks sight")

# self-test, no plant
func _check_sym8() -> void:
	var t := FogTruth.new()
	var sees: bool = t.can_see(Vector2.ZERO, 700.0, Vector2(500, 0))
	var not_seen_back: bool = not t.can_see(Vector2(500, 0), 200.0, Vector2.ZERO)
	_assert(sees and not_seen_back, "SYM-8 asymmetric sensors")

# plant: no-memory
func _check_mem6() -> void:
	var g1 := FogCellGrid.new()
	g1.setup(10, 100.0)
	g1.memory = true
	var idx: int = g1.cell_index(Vector2(500, 500))
	g1.update([{"pos": Vector2(500, 500), "radius_eff": 150.0}])
	var was_visible: bool = g1.cells[idx] == FogCellGrid.VISIBLE
	g1.update([{"pos": Vector2(5000, 5000), "radius_eff": 50.0}])
	var became_explored: bool = g1.cells[idx] == FogCellGrid.EXPLORED
	g1.update([{"pos": Vector2(5000, 5000), "radius_eff": 50.0}])
	var stayed_explored: bool = g1.cells[idx] == FogCellGrid.EXPLORED
	var g2 := FogCellGrid.new()
	g2.setup(10, 100.0)
	g2.memory = false
	g2.update([{"pos": Vector2(500, 500), "radius_eff": 150.0}])
	g2.update([{"pos": Vector2(5000, 5000), "radius_eff": 50.0}])
	var went_never_seen: bool = g2.cells[idx] == FogCellGrid.NEVER_SEEN
	_assert(was_visible and became_explored and stayed_explored and went_never_seen, "MEM-6 memory-on/off transitions")

# self-test, no plant
func _check_time10() -> void:
	var t := FogTruth.new()
	for i in range(8):
		t.friendlies.append(_mk_friendly(i, Vector2(i * 700.0, 0.0), 700.0))
	for i in range(12):
		t.enemies.append(_mk_enemy(1000 + i, Vector2(i * 500.0, 1000.0)))
	var grid := FogCellGrid.new()
	grid.setup(DIM, 100.0)
	var total_us := 0
	var n := 30
	for i in range(n):
		var t0 := Time.get_ticks_usec()
		var vis: Dictionary = t.compute_visibility()
		grid.update(vis.circles)
		total_us += Time.get_ticks_usec() - t0
	var avg_ms: float = (float(total_us) / float(n)) / 1000.0
	_assert(avg_ms < 3.0, "TIME-10 tick_avg %.3fms under 3ms" % avg_ms)

# plant: seed-ignored
func _check_seed11() -> void:
	var t11 := FogTruth.new()
	t11.load_fixture(FIXTURE_PATH)
	t11.load_scenario(SCENARIO_PATH)
	t11.generate(11)
	var t12 := FogTruth.new()
	t12.load_fixture(FIXTURE_PATH)
	t12.load_scenario(SCENARIO_PATH)
	t12.generate(12)
	var far := 0
	for i in range(t11.obstacles.size()):
		if t11.obstacles[i].pos.distance_to(t12.obstacles[i].pos) > 200.0:
			far += 1
	_assert(far * 2 >= t11.obstacles.size(), "SEED-11 seeds 11/12 place >=half obstacles >200wu apart (%d/%d)" % [far, t11.obstacles.size()])

func _check_scene() -> void:
	var packed: PackedScene = load(MOCKUP_SCENE)
	if packed == null:
		_assert(false, "cannot load %s" % MOCKUP_SCENE)
		return
	_root = packed.instantiate()
	get_root().add_child(_root)
	await process_frame
	await process_frame
	_check_recon5()
	_root.qa_tick(1)
	_check_view4()
	_check_struct7()
	_check_spin12()
	_check_json9()

# plant: recon-shows-enemy
func _check_recon5() -> void:
	var s0: Dictionary = _root.qa_state()
	var recon_ok: bool = s0.cells.never_seen == 0 and s0.cells.explored == 0 and s0.cells.visible == DIM * DIM and s0.view_enemy_uids.is_empty()
	var hud: Node = _root.get_node("HUD"); hud._update_readout()
	var readout_ok: bool = int(String(hud._readout_label.text).split(" ")[2]) == 0
	_root.qa_tick(20)
	var s1: Dictionary = _root.qa_state()
	var still_recon: bool = s1.hash == s0.hash and s1.tick == 0
	_root.qa_set("phase", "mission")
	var s2: Dictionary = _root.qa_state()
	var begin_ok: bool = s2.cells.never_seen > 3000 and s2.phase == "mission"
	hud._update_readout()
	readout_ok = readout_ok and int(String(hud._readout_label.text).split(" ")[2]) == s2.view_enemy_uids.size()
	var nodes: Array = _root.get_node("World/FogView/MapNodes").get_children()
	var labels_ok := true
	for n in nodes:
		if n is Label3D:
			labels_ok = labels_ok and not String(n.text).is_empty()
	_assert(recon_ok and still_recon and begin_ok and nodes.size() > 0 and readout_ok and labels_ok, "RECON-5 recon/begin, HUD readout from view set, node labels")

# plant: fog-leak
func _check_view4() -> void:
	var s: Dictionary = _root.qa_state()
	var fog_view: Node = _root.get_node("World/FogView")
	var count_ok: bool = s.view_enemy_uids.size() == 3 and fog_view.get_enemy_count() == 3
	var set_ok: bool = s.view_enemy_uids.has(101) and s.view_enemy_uids.has(102) and s.view_enemy_uids.has(103)
	var none_leaked: bool = not s.view_enemy_uids.has(104) and not s.view_enemy_uids.has(108)
	_assert(count_ok and set_ok and none_leaked, "VIEW-4 view holds only the 3 visible of 8 enemies")

# self-test, no plant (uses fog-leak-free state from VIEW-4/RECON-5 above)
func _check_struct7() -> void:
	_root.qa_move(1, 5600, 1700)
	_root.qa_tick(40)
	var s1: Dictionary = _root.qa_state()
	var visited: bool = s1.structures.get("1", "") == "visible"
	_root.qa_move(1, 100, 100)
	_root.qa_tick(80)
	var s2: Dictionary = _root.qa_state()
	var explored: bool = s2.structures.get("1", "") == "explored"
	var never: bool = s2.structures.get("2", "") == "never_seen"
	var fog_view: Node = _root.get_node("World/FogView")
	var not_drawn: bool = not fog_view.get_enemy_uids().has(101) and not fog_view.get_enemy_uids().has(102)
	_assert(visited and explored and never and not_drawn, "STRUCT-7 structure explored/never-seen states")

# self-test, no plant
func _check_spin12() -> void:
	var hud: Node = _root.get_node("HUD")
	var before: Dictionary = _root.qa_state()
	hud._seed_spinbox.value = 42.0
	var after: Dictionary = _root.qa_state()
	_assert(after.seed == 42 and after.regen_count == before.regen_count + 1, "SPIN-12 seed spinbox value_changed regenerates")

func _check_json9() -> void:
	var s: Dictionary = _root.qa_state()
	var keys_ok: bool = JSON.stringify(s) != ""
	for k in CONTRACT_KEYS:
		keys_ok = keys_ok and s.has(k)
	var plants_ok := true
	for id in PLANTS:
		plants_ok = plants_ok and _root.qa_plant(id)
	var nope_ok: bool = not _root.qa_plant("nope")
	_assert(keys_ok and plants_ok and nope_ok, "JSON-9 qa_state round trip and qa_plant contract")
