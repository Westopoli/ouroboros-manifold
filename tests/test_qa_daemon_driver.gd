extends SceneTree

# G2 (visible-game spec section 5, scout 7 "Driver additions"): autoload/qa_daemon.gd
# gains (1) key modifiers on input key / key_down / key_up, (2) a hover readback,
# (3) a per-run screenshot directory argument, (4) process_mode ALWAYS.
# Wire shapes proved here (the scout names the idea, not the spelling; a builder
# that picks another spelling must go through the Architect, not edit this test):
#   ["input","key","c",["ctrl","shift","alt"]]   optional trailing modifier list; same for key_down/key_up
#   tree()["hover"] = path of the visible Control under the pointer, "" when none
#   ["screenshot", name, out_dir]                 optional dir, forwarded to the driver after name
#   daemon.process_mode == PROCESS_MODE_ALWAYS    set in _ready, active or not
# Runs in --script SceneTree mode; the daemon gets a real qa_driver.gd (no --qa-port
# needed: the test seats it as the daemon's _driver, as _ready would) so the
# modifier and hover checks see real InputEvents arriving at a recorder node.
# Proves S-001-era harness need: story plays (preflight 7, section on drivers).
# test-timeout: 1800

const DaemonScript := preload("res://autoload/qa_daemon.gd")
const DriverScript := preload("res://scenes/mockups/_shared/qa_driver.gd")

class Recorder extends Node:
	var keys: Array = []
	func _input(e: InputEvent) -> void:
		if e is InputEventKey:
			keys.append({
				"code": e.keycode, "pressed": e.pressed,
				"ctrl": e.ctrl_pressed, "shift": e.shift_pressed, "alt": e.alt_pressed,
			})

class StubDriver extends Node:
	var shots: Array = []
	func _do_screenshot(name = "", a = "", b = "") -> void:
		shots.append([name, a, b])

var _pass_count := 0
var _fail_count := 0
var _fail_msgs: Array[String] = []


func _initialize() -> void:
	await _run_tests()
	print("\n=== QA Daemon Driver (G2) Test Results ===")
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


func _make_daemon(with_real_driver: bool) -> Node:
	var d: Node = DaemonScript.new()
	root.add_child(d)
	if with_real_driver:
		var drv: Node = DriverScript.new()
		d.add_child(drv)
		d._driver = drv
	return d


func _run_tests() -> void:
	await _check_process_mode()
	await _check_modifiers()
	await _check_hover()
	await _check_screenshot_dir()


func _check_process_mode() -> void:
	var d := _make_daemon(false)
	await process_frame
	_assert(d.process_mode == Node.PROCESS_MODE_ALWAYS,
		"G2: qa_daemon process_mode is %d, want PROCESS_MODE_ALWAYS (a paused tree would stop its polling)" % d.process_mode)
	var verdict = await d._dispatch("pause", [true])
	_assert(verdict is Dictionary and verdict.get("ok", false), "pause verb did not answer ok")
	_assert(d.can_process(), "G2: daemon cannot process while the tree is paused (pause hang)")
	await d._dispatch("pause", [false])
	_assert(not paused, "pause false did not unpause the tree")
	d.queue_free()


func _check_modifiers() -> void:
	var rec := Recorder.new()
	root.add_child(rec)
	var d := _make_daemon(true)
	await process_frame

	# Control: no modifier list leaves every modifier off (also proves the recorder sees events).
	await d._dispatch("input", ["key", "C"])
	_assert(rec.keys.size() >= 2, "control: plain key produced %d key events, want 2 (recorder blind)" % rec.keys.size())
	var plain_clean := true
	for k in rec.keys:
		if k["ctrl"] or k["shift"] or k["alt"]:
			plain_clean = false
	_assert(plain_clean, "control: plain key carried a modifier")

	rec.keys.clear()
	var r = await d._dispatch("input", ["key", "C", ["ctrl"]])
	_assert(r is Dictionary and r.get("ok", false), "key with modifier list was rejected: %s" % str(r))
	_assert(rec.keys.size() >= 2 and rec.keys.all(func(k): return k["ctrl"] and not k["shift"] and not k["alt"]),
		"G2: key with [ctrl] did not set ctrl (and only ctrl) on press and release (got %s)" % str(rec.keys))

	rec.keys.clear()
	await d._dispatch("input", ["key", "C", ["ctrl", "shift", "alt"]])
	_assert(rec.keys.size() >= 2 and rec.keys.all(func(k): return k["ctrl"] and k["shift"] and k["alt"]),
		"G2: key with [ctrl,shift,alt] did not set all three (got %s)" % str(rec.keys))

	rec.keys.clear()
	await d._dispatch("input", ["key_down", "1", ["shift"]])
	_assert(rec.keys.size() == 1 and rec.keys[0]["pressed"] and rec.keys[0]["shift"] and not rec.keys[0]["ctrl"],
		"G2: key_down with [shift] wrong (got %s)" % str(rec.keys))
	rec.keys.clear()
	await d._dispatch("input", ["key_up", "1", ["shift"]])
	_assert(rec.keys.size() == 1 and not rec.keys[0]["pressed"] and rec.keys[0]["shift"],
		"G2: key_up with [shift] wrong (got %s)" % str(rec.keys))

	d.queue_free()
	rec.queue_free()


func _check_hover() -> void:
	var scene := Control.new()
	scene.name = "G2Scene"
	scene.size = Vector2(400, 300)
	var btn := Button.new()
	btn.name = "G2Btn"
	btn.text = "hover me"
	btn.position = Vector2(100, 100)
	btn.size = Vector2(120, 40)
	scene.add_child(btn)
	root.add_child(scene)
	current_scene = scene
	var d := _make_daemon(true)
	await process_frame
	await process_frame

	var t0: Dictionary = d.tree()
	_assert(t0.has("hover"), "G2: tree() has no 'hover' key")
	_assert(t0.get("hover", null) is String, "G2: tree()['hover'] is not a String")

	await d._dispatch("input", ["move", 160.0, 120.0])
	await process_frame
	var t1: Dictionary = d.tree()
	_assert(t1.get("hover", "<missing>") == String(btn.get_path()),
		"G2: pointer over the button, hover = %s, want %s" % [str(t1.get("hover", "<missing>")), String(btn.get_path())])

	# Control: pointer off every Control reads back "" (a hover that is always the button fails here).
	await d._dispatch("input", ["move", 390.0, 290.0])
	await process_frame
	var t2: Dictionary = d.tree()
	_assert(t2.get("hover", "<missing>") == "" or t2.get("hover", "<missing>") == String(scene.get_path()),
		"G2: pointer off the button, hover = %s, want '' (or the bare scene root)" % str(t2.get("hover", "<missing>")))
	_assert(t2.get("hover", "<missing>") != String(btn.get_path()), "G2: hover stuck on the button after the pointer left")

	d.queue_free()
	current_scene = null
	scene.queue_free()


func _check_screenshot_dir() -> void:
	var d := _make_daemon(false)
	var stub := StubDriver.new()
	d.add_child(stub)
	d._driver = stub
	await process_frame
	var r = await d._dispatch("screenshot", ["shot_a", "user://qa/run_42"])
	_assert(r is Dictionary and r.get("ok", false), "screenshot with a dir arg was rejected: %s" % str(r))
	_assert(stub.shots.size() == 1, "screenshot reached the driver %d times, want 1" % stub.shots.size())
	if stub.shots.size() == 1:
		_assert(stub.shots[0][0] == "shot_a", "driver got name %s, want shot_a" % str(stub.shots[0][0]))
		_assert(stub.shots[0].has("user://qa/run_42"),
			"G2: the per-run dir was not forwarded to the driver (got %s)" % str(stub.shots[0]))
	# Control: no dir arg still works and forwards no dir.
	stub.shots.clear()
	await d._dispatch("screenshot", ["shot_b"])
	_assert(stub.shots.size() == 1 and stub.shots[0][0] == "shot_b" and not stub.shots[0].has("user://qa/run_42"),
		"control: screenshot without dir broke (got %s)" % str(stub.shots))
	d.queue_free()
