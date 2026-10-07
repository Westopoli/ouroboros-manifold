extends SceneTree

# Guard G3 (docs/northstar/plans/2026-10-07-visible-game-spec.md rev 4, section 2;
# programme Guard 1; preflight 7-story-plays.md section 4): autoload/qa_daemon.gd
# state()["inventory"] reports the current scene's nodes by name (class, visible,
# count) and the text of HUD Labels, reusing _collect_tree. Shape fixed by this test:
#   inventory["nodes_by_name"][name] = {"class": String, "visible": bool, "count": int}
#   inventory["hud_texts"][name]     = String   (every Label / Control with text, visible or not)
# Proves the G3 guard, S-### none (harness piece). Positive control: a name
# absent from the scene must be absent from the inventory.

var _pass_count := 0
var _fail_count := 0
var _fail_msgs: Array[String] = []


func _initialize() -> void:
	await _run_tests()
	print("\n=== QA Daemon Inventory Test Results ===")
	print("PASS: %d  FAIL: %d" % [_pass_count, _fail_count])
	if _fail_count > 0:
		for msg in _fail_msgs:
			print("  - " + msg)
		print("=== RED ===\n")
		quit(1)
	else:
		print("=== GREEN ===\n")
		quit(0)


func _assert(cond: bool, msg: String) -> void:
	if cond:
		_pass_count += 1
	else:
		_fail_count += 1
		_fail_msgs.append(msg)


func _label(name: String, text: String, vis := true) -> Label:
	var l := Label.new()
	l.name = name
	l.text = text
	l.visible = vis
	return l


func _run_tests() -> void:
	var script = load("res://autoload/qa_daemon.gd")
	var d = (script as Script).new()
	var scene := Node2D.new()
	scene.name = "FakeTactical"
	var hud := Control.new()
	hud.name = "Hud"
	hud.add_child(_label("Clock", "T+0042"))
	hud.add_child(_label("Objectives", "Hold the ridge"))
	hud.add_child(_label("Reinforcements", "secret", false))
	scene.add_child(hud)
	# TD-VG-GUARD-1: Godot 4.6.3 auto-renames same-named siblings, so count 3 by name
	# needs three distinct parents. Siblings case: two "Pair" siblings, second auto-renamed.
	for pn in ["FxA", "FxB", "FxC"]:
		var fx := Node2D.new()
		fx.name = pn
		var s := Node2D.new()
		s.name = "Shots"
		fx.add_child(s)
		scene.add_child(fx)
	var sib := Node2D.new()
	sib.name = "Sibs"
	for i in 2:
		var p := Node2D.new()
		p.name = "Pair"
		sib.add_child(p)
	scene.add_child(sib)
	var g3 := Node3D.new()
	g3.name = "Ground3D"
	scene.add_child(g3)
	var fog := Node2D.new()
	fog.name = "FogLayer"
	fog.visible = false
	scene.add_child(fog)

	get_root().add_child(d)
	get_root().add_child(scene)
	await process_frame
	current_scene = scene

	var st: Dictionary = d.state()
	_assert(st.has("scene") and st.has("tick"), "existing state keys scene/tick lost")
	_assert(st.has("inventory"), "state() has no 'inventory' key (G3 feature missing)")
	if st.has("inventory") and st["inventory"] is Dictionary:
		var inv: Dictionary = st["inventory"]
		_assert(inv.has("nodes_by_name") and inv["nodes_by_name"] is Dictionary, "inventory has no nodes_by_name dictionary")
		_assert(inv.has("hud_texts") and inv["hud_texts"] is Dictionary, "inventory has no hud_texts dictionary")
		var n: Dictionary = inv.get("nodes_by_name", {})
		var h: Dictionary = inv.get("hud_texts", {})
		_check_entry(n, "Hud", "Control", true, 1)
		_check_entry(n, "Clock", "Label", true, 1)
		_check_entry(n, "Ground3D", "Node3D", true, 1)
		_check_entry(n, "Shots", "Node2D", true, 3)
		_check_entry(n, "Pair", "Node2D", true, 1)
		_assert(n.has("Pair") or n.has("@Node2D@2"), "auto-renamed sibling absent")
		_check_entry(n, "FogLayer", "Node2D", false, 1)
		_check_entry(n, "Reinforcements", "Label", false, 1)
		_assert(not n.has("NoSuchNode"), "positive control: absent name NoSuchNode appeared in inventory")
		_assert(not n.has("FakeTactical"), "the scene root itself is listed; only its descendants are")
		_assert(h.get("Clock", null) == "T+0042", "hud_texts Clock != 'T+0042': %s" % str(h.get("Clock", null)))
		_assert(h.get("Objectives", null) == "Hold the ridge", "hud_texts Objectives wrong: %s" % str(h.get("Objectives", null)))
		_assert(not h.has("Ground3D"), "hud_texts lists a node with no text")
		var again: Dictionary = d.state()
		_assert(again.get("inventory", null) == inv, "inventory not deterministic across two calls")

	# Reuse of _collect_tree: tree() output is unchanged by G3 (visible Controls only).
	var t: Dictionary = d.tree()
	var paths: Array = []
	for c in t["controls"]:
		paths.append(c["path"])
	_assert(paths.any(func(p): return String(p).ends_with("Hud/Clock")), "tree() lost the visible Clock control")
	_assert(not paths.any(func(p): return String(p).ends_with("Reinforcements")), "tree() lists a hidden control")

	current_scene = null
	scene.free()
	d.free()


func _check_entry(n: Dictionary, name: String, cls: String, vis: bool, count: int) -> void:
	_assert(n.has(name), "inventory missing node '%s'" % name)
	if not n.has(name):
		return
	var e: Dictionary = n[name]
	_assert(e.get("class", "") == cls, "%s class %s != %s" % [name, e.get("class", ""), cls])
	_assert(e.get("visible", null) == vis, "%s visible %s != %s" % [name, e.get("visible", null), vis])
	_assert(int(e.get("count", -1)) == count, "%s count %s != %d" % [name, e.get("count", -1), count])
