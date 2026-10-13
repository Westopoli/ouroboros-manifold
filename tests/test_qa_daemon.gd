extends SceneTree

# F6 (two-day push, item 5): the daemon seam for C7. res://autoload/qa_daemon.gd
# does not exist yet -- C7 creates it, plus the project.godot [autoload] line
# (M0-owned; C7/M3 cannot touch project.godot per the manager ownership table,
# so M0 adds that one line when C7 attaches). This test loads the daemon
# script directly and calls state() on an instance, the same way
# test_boot_scripts_parse.gd loads every autoload script directly -- `--script`
# SceneTree mode does not run Godot's normal autoload bootstrap, so a real
# check here can never rely on get_node("/root/QADaemon"); it must be red for
# the same reason regardless of whether the project.godot line exists.

var _pass_count := 0
var _fail_count := 0
var _fail_msgs: Array[String] = []


func _initialize() -> void:
	await _run_tests()
	print("\n=== QA Daemon Test Results ===")
	print("PASS: %d  FAIL: %d" % [_pass_count, _fail_count])
	if _fail_count > 0:
		print("Failures:")
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


func _run_tests() -> void:
	var daemon_path := "res://autoload/qa_daemon.gd"
	_assert(ResourceLoader.exists(daemon_path), "qa daemon script missing: " + daemon_path)
	if not ResourceLoader.exists(daemon_path):
		return

	var script = load(daemon_path)
	_assert(script != null, "qa daemon script failed to load (parse error): " + daemon_path)
	if script == null:
		return
	_assert(script is Script, "qa daemon resource is not a Script: " + daemon_path)
	if not (script is Script):
		return
	_assert((script as Script).can_instantiate(),
		"qa daemon script cannot be instantiated (broken parse): " + daemon_path)
	if not (script as Script).can_instantiate():
		return

	var daemon = (script as Script).new()
	_assert(daemon != null, "qa daemon failed to instantiate")
	if daemon == null:
		return

	_assert(daemon.has_method("state"), "qa daemon has no state() method")
	if not daemon.has_method("state"):
		if daemon is Node:
			(daemon as Node).free()
		return

	var result = daemon.state()
	_assert(result is Dictionary, "qa daemon state() did not return a Dictionary")
	if result is Dictionary:
		var d: Dictionary = result
		_assert(d.has("scene"), "qa daemon state() missing key 'scene'")
		_assert(d.has("tick"), "qa daemon state() missing key 'tick'")

	await _check_step_reaches_the_scene_qa_step(script)
	await _check_project_verb(script)

	if daemon is Node:
		(daemon as Node).free()


# Piece C7-3: the daemon's step verb also calls the current scene's
# qa_step(n) when it has one (the way plant reaches qa_plant), so a desktop
# test can advance a scene that owns a live sim session (C2-4). A scene
# without qa_step is left alone and the daemon's own counter still moves.
func _check_step_reaches_the_scene_qa_step(script) -> void:
	var gs := GDScript.new()
	gs.source_code = "extends Node\nvar got := -1\nfunc qa_step(n: int) -> void:\n\tgot = n\n"
	_assert(gs.reload() == OK, "step test stub script failed to compile")
	var stub := Node.new()
	stub.set_script(gs)
	var plain := Node.new()
	var d = (script as Script).new()
	get_root().add_child(d)
	get_root().add_child(stub)
	get_root().add_child(plain)
	await process_frame

	current_scene = stub
	var r: Dictionary = d._dispatch("step", [7])
	_assert(bool(r.get("ok", false)) and int(r["result"].get("tick", -1)) == 7, "step verb did not answer ok with tick 7: %s" % str(r))
	_assert(int(stub.get("got")) == 7, "step verb did not reach the scene's qa_step (got %s, expected 7)" % stub.get("got"))

	current_scene = plain
	var r2: Dictionary = d._dispatch("step", [3])
	_assert(bool(r2.get("ok", false)) and int(r2["result"].get("tick", -1)) == 10, "step verb on a scene without qa_step failed: %s" % str(r2))
	_assert(int(stub.get("got")) == 7, "step verb reached a scene that is no longer current")

	current_scene = null
	for n in [d, stub, plain]:
		n.free()


# Piece G-project (Architect 2026-10-09): the test-only daemon verb "project" x y (world coordinates) answers
# {"ok": true, "result": {"x", "y", "on_screen"}}, the screen pixel the open tactical view draws that world point at
# (2D view: inverse of TacticalView._to_world; ground 3D view: the rig camera's unproject_position), on_screen true
# inside the 1920x1080 viewport; with no tactical view open {"ok": false, "error": "project: no tactical view"}.
# RED now because the verb is missing: _dispatch answers "unknown verb project".
func _check_project_verb(script) -> void:
	var d = (script as Script).new()
	get_root().add_child(d)
	await process_frame

	# G-project test 1: no tactical view -> the error.
	var plain := Node.new()
	get_root().add_child(plain)
	current_scene = plain
	var r0: Dictionary = await d._dispatch("project", [10.0, 10.0])
	_assert(not bool(r0.get("ok", true)) and String(r0.get("error", "")) == "project: no tactical view",
		"G-project: project with no tactical view must answer the 'project: no tactical view' error (verb missing); got %s" % str(r0))
	current_scene = null
	plain.free()

	# G-project test 2: 2D view; project(unit world pos) == units_px within 1 px; far point is off screen.
	var fx = load("res://tests/support/vg_c_fixture.gd")
	var view: Node = load("res://scenes/tactical_c/tactical_view.tscn").instantiate()
	get_root().add_child(view)
	await process_frame
	view.set_process(false)
	var fr: Dictionary = fx.frame()
	fr["player_faction"] = 0
	fr["visible"] = {"0": [1, 2, 3, 4]}
	# TD-VG-A-15: the fixture has no map.canvas, so load_frame never framed it and the
	# units projected against the camera the view already held (A18 opening frame, zoom 32,
	# unit 1 off screen). A canvas makes the view frame the fixture's own box. Was: no canvas.
	fr["map"]["canvas"] = 1000.0
	view.load_frame(fr)
	await process_frame
	current_scene = view
	var upx: Dictionary = view.qa_state().get("units_px", {})
	_assert(upx.size() > 0, "G-project: the 2D view lists no units_px for the fixture frame (test setup)")
	var checked := 0
	for u in fx.frame()["units"]:
		var p = upx.get(str(u["id"]), upx.get(u["id"]))
		if p == null:
			continue
		var want := Vector2(float(p[0]), float(p[1])) if p is Array else Vector2(p)
		var r: Dictionary = await d._dispatch("project", [float(u["x"]), float(u["y"])])
		var res: Dictionary = r.get("result", {})
		var got := Vector2(float(res.get("x", -1.0e9)), float(res.get("y", -1.0e9)))
		_assert(bool(r.get("ok", false)) and got.distance_to(want) <= 1.0,
			"G-project: 2D project of unit %d = %s, units_px says %s (verb missing); reply %s" % [u["id"], got, want, str(r)])
		checked += 1
	_assert(checked > 0, "G-project: no fixture unit had a units_px entry to compare")
	# Positive control: a point one screen-width (1920 px) away in world units is off screen.
	var scale_w: float = float(view.get("_world_scale"))
	var u0: Dictionary = fx.frame()["units"][0]
	var far: Dictionary = await d._dispatch("project", [float(u0["x"]) + 1920.0 / maxf(scale_w, 0.0001), float(u0["y"])])
	_assert(bool(far.get("ok", false)) and not bool(far.get("result", {}).get("on_screen", true)),
		"G-project control: a point one screen-width away must be on_screen=false (verb missing); got %s" % str(far))
	var near: Dictionary = await d._dispatch("project", [float(u0["x"]), float(u0["y"])])
	_assert(bool(near.get("ok", false)) and bool(near.get("result", {}).get("on_screen", false)),
		"G-project control: the unit's own point must be on_screen=true (verb missing); got %s" % str(near))
	current_scene = null
	view.free()

	# G-project test 3: ground 3D view. SKIPPED: the ground view needs the /root/EraConfig autoload
	# (TacticalView._ground_era) and SimSession.bridge().mission(), neither exists under a --script SceneTree
	# (no autoload bootstrap), so Ground3DHost is never created by the view here. The builder verifies it live:
	# rig.project_to_screen(Vector2) (scenes/ground3d camera rig) must equal the verb's x,y within 1 px.
	print("SKIP G-project test 3 (ground3d): needs EraConfig/SimSession autoloads, absent in --script mode")

	d.free()
