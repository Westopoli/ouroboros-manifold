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
	_run_tests()
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

	if daemon is Node:
		(daemon as Node).free()
