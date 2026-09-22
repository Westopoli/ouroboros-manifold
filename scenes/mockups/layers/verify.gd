extends SceneTree

const FIXTURE_PATH := "res://scenes/mockups/layers/fixtures/map_seed11.json"
const MOCKUP_SCENE := "res://scenes/mockups/layers/layers_mockup.tscn"
const PLANTS := ["instant-transfer", "blocked-ignored", "cross-layer-full-range",
	"ring-colour-same", "no-dimming", "wrong-height"]

var _failures := 0
var _root: Node

func _initialize() -> void:
	_check_dur2()
	_check_block3()
	_check_same4()
	_check_vis5()
	_check_det1()
	await _check_contract()

	if _failures > 0:
		print("VERIFY FAILED: %d check(s)" % _failures)
		quit(1)
		return
	print("VERIFY OK")
	quit(0)

func _make_raw_sim() -> ToySim:
	var s := ToySim.new()
	s.load_fixture(FIXTURE_PATH)
	return s

func _make_sim(seed_n: int = 11) -> ToySim:
	var s := _make_raw_sim()
	s.generate(seed_n)
	return s

func _check_dur2() -> void:
	var sim := _make_sim()
	sim.transfer(1, 2)
	sim.transfer(2, 2)
	sim.step(19)
	# plant: instant-transfer
	_assert(sim.units[1].layer == 1, "fast unit completed before its 20-tick duration")
	sim.step(1)
	_assert(sim.units[1].layer == 2, "fast unit did not complete at exactly tick 20")
	_assert(sim.units[2].layer == 1, "slow unit completed alongside the fast one")
	sim.step(80)
	_assert(sim.units[2].layer == 2, "slow unit did not complete at exactly tick 100")

func _check_block3() -> void:
	var sim := _make_sim()
	var u: Dictionary = sim.units[1]
	u.pos = sim.blocked_center
	sim.transfer(1, 2)
	# plant: blocked-ignored
	_assert(u.pending, "transfer onto a blocked cell did not go pending")
	_assert(u.layer == 1, "layer changed while a transfer is pending")
	sim.step(30)
	_assert(u.pending and u.layer == 1, "a pending transfer resolved without the unit reaching an open cell")
	var open_pos: Vector2 = sim.blocked_center + Vector2(sim.blocked_radius + 200.0, 0.0)
	sim.move(1, open_pos.x, open_pos.y)
	var dist: float = u.pos.distance_to(open_pos)
	var step_dist: float = ToySim.MOVE_SPEED_WU_S / ToySim.TICK_HZ
	sim.step(int(ceil(dist / step_dist)) + ToySim.TRANSITION_TICKS["fast"] + 2)
	_assert(not u.pending and u.layer == 2, "transfer did not start and complete once the unit reached an open cell")

func _check_same4() -> void:
	var sim := _make_sim()
	sim.transfer(1, 1)
	_assert(sim.units[1].transition == null and not sim.units[1].pending and sim.units[1].layer == 1,
		"a same-layer transfer produced a transition, a pending state, or a layer change")

func _check_vis5() -> void:
	var sim := _make_sim()
	sim.units[1].pos = Vector2.ZERO
	sim.units[2].pos = Vector2.ZERO
	sim.units[101].pos = Vector2(0, 5000)
	sim.units[102].pos = Vector2(350, 0)
	sim.units[102].layer = 2
	sim.units[103].pos = Vector2(450, 0)
	sim.units[103].layer = 2
	var fast_seen: Array = sim.visible_by(1)
	# plant: cross-layer-full-range
	_assert(fast_seen.has(102), "fast unit did not see the layer-2 enemy at 350wu")
	_assert(not fast_seen.has(103), "fast unit saw the layer-2 enemy at 450wu, beyond its 400wu cross-layer radius")
	_assert(not fast_seen.has(101), "fast unit saw the far layer-1 enemy under the obstacle")
	var slow_seen: Array = sim.visible_by(2)
	_assert(not slow_seen.has(102) and not slow_seen.has(103), "slow unit saw a layer-2 enemy beyond its 150wu radius")

func _run_stream(sim: ToySim) -> Dictionary:
	sim.transfer(1, 2)
	var starts: Array = []
	var ends: Array = []
	for i in range(200):
		var was: bool = sim.units[1].transition != null
		sim.step(1)
		var now: bool = sim.units[1].transition != null
		if now and not was:
			starts.append(sim.tick)
		if was and not now:
			ends.append(sim.tick)
	return {"hash": sim.compute_hash(), "starts": starts, "ends": ends}

func _check_det1() -> void:
	var a := _run_stream(_make_sim())
	var b := _run_stream(_make_sim())
	_assert(a.hash == b.hash, "same seed and command stream gave different hashes across two runs")
	_assert(a.starts == b.starts and a.ends == b.ends, "transition start/end ticks differ across two runs")

	var g1 := _make_raw_sim()
	g1.debug_use_global_rng = true
	g1.generate(11)
	var g2 := _make_raw_sim()
	g2.debug_use_global_rng = true
	g2.generate(11)
	_assert(g1.units[1].pos != g2.units[1].pos,
		"self-test: a global-RNG variant produced identical jitter twice; this check would not catch non-determinism")

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

	_check_height6()
	_check_ring7()
	_check_dim8()
	_check_focus9()
	_check_json10()

func _check_height6() -> void:
	_root.qa_seed(11)
	_root.qa_transfer(1, 2)
	_root.qa_tick(10)
	var lv: LayerView = _root.get_layer_view()
	var off: float = LayerView.UNIT_HALF_EXTENT
	var y_mid: float = lv.get_unit_body(1).position.y
	# plant: wrong-height
	_assert(y_mid > off + 0.5 and y_mid < LayerView.LAYER_HEIGHT + off - 0.5, "mid-transition y is not strictly between the two layer heights")
	_root.qa_tick(15)
	var y_after: float = lv.get_unit_body(1).position.y
	_assert(is_equal_approx(y_after, LayerView.LAYER_HEIGHT + off), "completed-transfer y does not equal layer_height_wu")

func _check_ring7() -> void:
	_root.qa_seed(11)
	_root.qa_transfer(1, 2)
	var lv: LayerView = _root.get_layer_view()
	_root.qa_tick(19)
	var before: Color = lv.get_unit_ring(1).material_override.albedo_color
	_assert(_close(before, LayerView.LAYER_COLORS[0]), "ring colour changed before the completion tick")
	_root.qa_tick(1)
	var after: Color = lv.get_unit_ring(1).material_override.albedo_color
	# plant: ring-colour-same
	_assert(_close(after, LayerView.LAYER_COLORS[1]) and not _close(after, before), "ring colour did not flip on the completion tick")

func _check_dim8() -> void:
	_root.qa_seed(11)
	_root.qa_transfer(1, 2)
	_root.qa_tick(25)
	var lv: LayerView = _root.get_layer_view()
	_root.qa_set("focus_layer", 1)
	# plant: no-dimming
	_assert(is_equal_approx(lv.get_unit_body(1).material_override.albedo_color.a, 0.4), "layer-2 unit is not dimmed with focus on layer 1")
	_assert(is_equal_approx(lv.get_unit_body(2).material_override.albedo_color.a, 1.0), "layer-1 unit is dimmed with focus on layer 1")
	_root.qa_set("focus_layer", 2)
	_assert(is_equal_approx(lv.get_unit_body(1).material_override.albedo_color.a, 1.0), "layer-2 unit is dimmed with focus on layer 2")
	_assert(is_equal_approx(lv.get_unit_body(2).material_override.albedo_color.a, 0.4), "layer-1 unit is not dimmed with focus on layer 2")

func _check_focus9() -> void:
	_root.qa_set("focus_layer", 1)
	_root.cycle_focus_layer()
	_assert(_root.get_focus_layer() == 2 and _root.get_hud().get_highlighted_layer() == 2, "Tab did not move focus (and the strip) from 1 to 2")
	_root.cycle_focus_layer()
	_assert(_root.get_focus_layer() == 1 and _root.get_hud().get_highlighted_layer() == 1, "Tab did not move focus (and the strip) from 2 back to 1")

func _check_json10() -> void:
	var state: Dictionary = _root.qa_state()
	_assert(JSON.stringify(state) != "", "qa_state() did not survive JSON.stringify")
	for key in ["seed", "hash", "tick", "focus_layer", "layer_height_wu", "units", "units_px",
		"visible_enemy_uids", "rings", "timing_ms", "regen_count"]:
		_assert(state.has(key), "qa_state() missing key %s" % key)
	_assert(not _root.qa_plant("nope"), "qa_plant('nope') must return false")
	for id in PLANTS:
		_assert(_root.qa_plant(id), "qa_plant(%s) must return true" % id)

func _close(a: Color, b: Color) -> bool:
	return absf(a.r - b.r) < 0.01 and absf(a.g - b.g) < 0.01 and absf(a.b - b.b) < 0.01

func _assert(condition: bool, message: String) -> void:
	if not condition:
		_failures += 1
		print("FAIL: %s" % message)
