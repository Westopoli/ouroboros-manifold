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
