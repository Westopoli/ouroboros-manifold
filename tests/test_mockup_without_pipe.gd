extends SceneTree

# Guard: the prototype mockups must run on a machine with no sim binary (a Mac
# without pipe/ouroboros_pipe). Proves, with the binary absent:
#  (1) autoload/c_bridge.gd open_session() reports the failure (false + last_error)
#      and neither crashes nor quits the tree;
#  (2) autoload/sim_bridge.gd _spawn_sim() with an unspawnable target does not
#      crash or quit the tree (it emits sim_error spawn_failed);
#  (3) res://scenes/mockups/landscape/landscape_mockup.tscn instanced into the
#      tree runs 30 frames, the tree keeps running, the scene stays in the tree.
# Does not depend on the build: skipped with a line if the binary exists.

const PIPE_BIN := "res://pipe/ouroboros_pipe"
const MOCKUP := "res://scenes/mockups/landscape/landscape_mockup.tscn"

var _pass_count := 0
var _fail_count := 0
var _fail_msgs: Array[String] = []
var _sim_errors: Array = []


func _initialize() -> void:
	await _run_tests()
	print("\n=== Mockup Without Pipe Test Results ===")
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


func _on_sim_error(info: Dictionary) -> void:
	_sim_errors.append(info)


func _run_tests() -> void:
	if FileAccess.file_exists(ProjectSettings.globalize_path(PIPE_BIN)):
		print("SKIP: %s exists; this guard is for a machine without the pipe binary" % PIPE_BIN)
		return

	# (1) c_bridge: open_session with the binary absent
	var cb = load("res://autoload/c_bridge.gd").new()
	var ok = cb.open_session(1, 4, [])
	_assert(ok == false, "c_bridge.open_session returned true with no pipe binary")
	_assert(String(cb.last_error()) != "", "c_bridge.open_session left last_error() empty after a spawn failure")
	cb.close_session()

	# (2) sim_bridge: spawn with nothing to spawn. USE_LIVE_SIM is false so _ready
	# is a no-op; call _spawn_sim directly, as _ready would if it were on.
	var sb = load("res://autoload/sim_bridge.gd").new()
	sb.sim_error.connect(_on_sim_error)
	sb._spawn_sim(PackedStringArray())
	if not _sim_errors.is_empty():
		_assert(str(_sim_errors[0].get("kind", "")) == "spawn_failed", "sim_bridge spawn failure reported kind %s, not spawn_failed" % str(_sim_errors[0]))
	# the python fallback may really spawn (python3 on PATH); do not leave it running
	if int(sb._pid) > 0:
		OS.kill(int(sb._pid))
	sb.free()

	# (3) the landscape mockup in the tree for 30 frames
	var packed = load(MOCKUP)
	_assert(packed is PackedScene, "landscape mockup did not load as a PackedScene")
	if packed is PackedScene:
		var inst: Node = packed.instantiate()
		_assert(inst != null, "landscape mockup did not instantiate")
		if inst != null:
			root.add_child(inst)
			for i in 30:
				await process_frame
			_assert(inst.is_inside_tree(), "landscape mockup left the tree within 30 frames")
			_assert(is_instance_valid(inst), "landscape mockup was freed within 30 frames")
			inst.queue_free()
			await process_frame
