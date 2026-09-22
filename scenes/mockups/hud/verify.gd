extends SceneTree

const HUD_SCENE := "res://scenes/mockups/hud/hud_mockup.tscn"
const SEL_PATH := "res://scenes/mockups/hud/selection.gd"
const TOY_PATH := "res://scenes/mockups/hud/toy_units.gd"
const ROUTER_PATH := "res://scenes/mockups/hud/input_router.gd"
const CONTRACT_KEYS := ["seed", "hash", "tick", "clock_s", "selected", "groups", "focus_layer", "camera", "bounds", "units", "units_px", "commands", "objective", "timing_ms", "regen_count"]
const PLANTS := ["box-one-layer", "group-shared", "select-all-exists", "camera-unbounded", "clock-wallclock", "narrow-moves-focus"]

var _failures := 0
var _root: Node

func _initialize() -> void:
	_check_det1()
	_check_box2()
	_check_narrow3()
	_check_group4()
	_check_centre5()
	_check_noall6()
	_check_shift7()
	await _check_bound8()
	await _check_clock9()
	await _check_panel10()
	await _check_json11()

	if _failures > 0:
		print("VERIFY FAILED: %d check(s)" % _failures)
		quit(1)
		return
	print("VERIFY OK")
	quit(0)

func _fake_units() -> Dictionary:
	return {1: {"uid": 1, "faction": "player", "layer": 1, "pos": Vector2(10, 10), "hp": 100.0},
		2: {"uid": 2, "faction": "player", "layer": 2, "pos": Vector2(20, 20), "hp": 100.0},
		3: {"uid": 3, "faction": "player", "layer": 2, "pos": Vector2(30, 30), "hp": 100.0},
		4: {"uid": 4, "faction": "enemy", "layer": 1, "pos": Vector2(15, 15), "hp": 100.0}}

func _check_det1() -> void:
	var cls = _load_class(TOY_PATH)
	if cls == null or not cls.new().has_method("generate"):
		_assert(false, "DET-1: toy_units.gd missing generate()/step()"); return
	var a = cls.new(); a.generate(11); var b = cls.new(); b.generate(11); var c = cls.new(); c.generate(12)
	for i in range(300):
		a.step(); b.step(); c.step()
	_assert(a.compute_hash() == b.compute_hash() and a.compute_hash() != c.compute_hash(),
		"DET-1: hash_a=%s hash_b=%s hash_c=%s" % [a.compute_hash(), b.compute_hash(), c.compute_hash()])

func _check_box2() -> void:
	var cls = _load_class(SEL_PATH)
	if cls == null or not cls.new().has_method("box"):
		_assert(false, "BOX-2: selection.gd missing box()"); return
	var sel = cls.new()
	var units := _fake_units()
	var project := func(uid): return units[uid].pos
	sel.box(Rect2(-10, -10, 1000, 1000), project, units)
	_assert(sel.selected.size() == 3, "BOX-2: box selected %s, want 3 uids across both layers" % sel.selected)

func _check_narrow3() -> void:
	var cls = _load_class(SEL_PATH)
	if cls == null or not cls.new().has_method("narrow"):
		_assert(false, "NARROW-3: selection.gd missing narrow()"); return
	var sel = cls.new()
	sel.selected = [1, 2, 3]
	sel.focus_layer = 1
	sel.narrow(2, _fake_units())
	_assert(sel.selected == [2, 3] and sel.focus_layer == 1,
		"NARROW-3: selected=%s focus_layer=%d" % [sel.selected, sel.focus_layer])

func _check_group4() -> void:
	var cls = _load_class(SEL_PATH)
	if cls == null or not cls.new().has_method("bind"):
		_assert(false, "GROUP-4: selection.gd missing bind()"); return
	var sel = cls.new()
	var units := _fake_units()
	sel.selected = [1]; sel.bind(1, units)
	sel.selected = [1, 2]; sel.bind(2, units)
	var r: Dictionary = sel.recall(2, units, 0)
	_assert(not sel.groups.get(1, []).has(1) and sel.selected == [1, 2] and not r.centre_requested,
		"GROUP-4: groups=%s selected=%s" % [sel.groups, sel.selected])

func _check_centre5() -> void:
	var cls = _load_class(SEL_PATH)
	if cls == null or not cls.new().has_method("recall"):
		_assert(false, "CENTRE-5: selection.gd missing recall()"); return
	var sel = cls.new()
	var units := _fake_units()
	sel.selected = [1, 2]; sel.bind(3, units)
	var r1: Dictionary = sel.recall(3, units, 1000)
	var r2: Dictionary = sel.recall(3, units, 1300)
	var r3: Dictionary = sel.recall(3, units, 2000)
	_assert(not r1.centre_requested and r2.centre_requested and not r3.centre_requested,
		"CENTRE-5: r1=%s r2=%s r3=%s" % [r1.centre_requested, r2.centre_requested, r3.centre_requested])

func _check_noall6() -> void:
	var sel_cls = _load_class(SEL_PATH)
	var router_cls = _load_class(ROUTER_PATH)
	if sel_cls == null or router_cls == null:
		_assert(false, "NOALL-6: selection.gd or input_router.gd missing"); return
	var router := Node.new(); router.set_script(router_cls)
	var all_cmds: Array = sel_cls.new().commands()
	if router.has_method("mapped_commands"):
		all_cmds += router.mapped_commands()
	var bad: Array = all_cmds.filter(func(c): return String(c).findn("select_all") != -1)
	_assert(bad.is_empty(), "NOALL-6: found select-all-like command(s) %s" % bad)

func _check_shift7() -> void:
	var cls = _load_class(SEL_PATH)
	if cls == null or not cls.new().has_method("shift_click"):
		_assert(false, "SHIFT-7: selection.gd missing shift_click()"); return
	var sel = cls.new()
	var units := _fake_units()
	sel.selected = [1]
	sel.shift_click(2, units)
	var added: bool = sel.selected.has(2)
	sel.shift_click(1, units)
	var removed: bool = not sel.selected.has(1)
	_assert(added and removed, "SHIFT-7: added=%s removed=%s selected=%s" % [added, removed, sel.selected])

func _check_bound8() -> void:
	var root = await _instantiate_root()
	if root == null or not root.has_method("qa_camera"):
		_assert(false, "BOUND-8: cannot instantiate or missing qa_camera"); return
	root.qa_seed(11); root.qa_camera(3000.0, 999999.0, -999999.0)
	var s: Dictionary = root.qa_state()
	var b: Dictionary = s.bounds; var cam: Dictionary = s.camera
	var inside: bool = cam.x >= b.min_x and cam.x <= b.max_x and cam.z >= b.min_z and cam.z <= b.max_z
	var rig: Node = root.get_node_or_null("CameraRig")
	var cam3d: Camera3D = rig.get_camera() if rig and rig.has_method("get_camera") else null
	var pitch_ok: bool = cam3d != null and is_equal_approx(rad_to_deg(-cam3d.rotation.x), 90.0)
	root.qa_set("focus_layer", 2)
	var cam2: Dictionary = root.qa_state().camera
	_assert(inside and pitch_ok and cam2 == cam, "BOUND-8: cam=%s bounds=%s pitch_ok=%s cam2=%s" % [cam, b, pitch_ok, cam2])

func _check_clock9() -> void:
	var root = await _instantiate_root()
	if root == null or not root.has_method("qa_tick"):
		_assert(false, "CLOCK-9: cannot instantiate or missing qa_tick"); return
	root.qa_seed(11); root.qa_tick(1200)
	var c1: float = root.qa_state().get("clock_s", -1.0)
	OS.delay_msec(500)
	var c2: float = root.qa_state().get("clock_s", -2.0)
	_assert(is_equal_approx(c1, 60.0) and is_equal_approx(c1, c2), "CLOCK-9: c1=%.3f c2=%.3f" % [c1, c2])

func _check_panel10() -> void:
	var root = await _instantiate_root()
	if root == null or not root.has_method("qa_select"):
		_assert(false, "PANEL-10: cannot instantiate or missing qa_select"); return
	root.qa_seed(11); root.qa_select([1, 2, 3])
	var controls: Array = []
	_collect_controls(root, controls)
	var overlay: Node = root.get_node_or_null("HUD/BoxOverlay")
	var overlay_ok: bool = overlay != null and overlay.mouse_filter == Control.MOUSE_FILTER_IGNORE
	var focus_ok := true
	for c in controls:
		focus_ok = focus_ok and c.focus_mode == Control.FOCUS_NONE
	_assert(controls.size() > 0 and focus_ok and overlay_ok,
		"PANEL-10: controls=%d focus_ok=%s overlay_ok=%s" % [controls.size(), focus_ok, overlay_ok])

func _check_json11() -> void:
	var root = await _instantiate_root()
	if root == null or not root.has_method("qa_state"):
		_assert(false, "JSON-11: cannot instantiate or missing qa_state"); return
	root.qa_seed(11)
	var state: Dictionary = root.qa_state()
	var text := JSON.stringify(state)
	var keys_ok := true
	for k in CONTRACT_KEYS:
		keys_ok = keys_ok and state.has(k)
	var plants_ok: bool = root.has_method("qa_plant") and not root.qa_plant("nope")
	for id in PLANTS:
		plants_ok = plants_ok and root.qa_plant(id)
	_assert(text != "" and typeof(JSON.parse_string(text)) == TYPE_DICTIONARY and keys_ok and plants_ok,
		"JSON-11: text_ok=%s keys_ok=%s plants_ok=%s" % [text != "", keys_ok, plants_ok])

func _instantiate_root():
	if not FileAccess.file_exists(HUD_SCENE): return null
	if _root != null: return _root
	var packed: PackedScene = load(HUD_SCENE)
	if packed == null: return null
	_root = packed.instantiate()
	get_root().add_child(_root)
	await process_frame; await process_frame
	return _root

func _collect_controls(node: Node, out: Array) -> void:
	for child in node.get_children():
		if child is Control:
			out.append(child)
		_collect_controls(child, out)

func _load_class(path: String):
	if not FileAccess.file_exists(path): return null
	return load(path)

func _assert(condition: bool, message: String) -> void:
	if not condition:
		_failures += 1
		print("FAIL: %s" % message)
