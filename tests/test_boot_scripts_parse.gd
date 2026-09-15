extends SceneTree

# S-BOOT-01: every autoload script parses and instantiates, and the boot
# scene (privacy_modal) loads, so the legacy client can reach the editor
# and screenshots. See autoload/tactical_bridge.gd — WsClient removal.

var _pass_count := 0
var _fail_count := 0
var _fail_msgs: Array[String] = []


func _initialize() -> void:
	_run_tests()
	print("\n=== Boot Scripts Parse Test Results ===")
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


func _autoload_script_paths() -> Array[String]:
	var paths: Array[String] = []
	var f := FileAccess.open("res://project.godot", FileAccess.READ)
	_assert(f != null, "could not open res://project.godot")
	if f == null:
		return paths

	var in_autoload := false
	while not f.eof_reached():
		var line := f.get_line()
		var trimmed := line.strip_edges()
		if trimmed == "[autoload]":
			in_autoload = true
			continue
		if in_autoload and trimmed.begins_with("[") and trimmed != "[autoload]":
			break
		if not in_autoload:
			continue
		if trimmed.is_empty():
			continue
		var eq := trimmed.find("=")
		if eq < 0:
			continue
		var value := trimmed.substr(eq + 1).strip_edges()
		value = value.trim_prefix("\"").trim_suffix("\"")
		value = value.trim_prefix("*")
		if value.begins_with("res://"):
			paths.append(value)
	f.close()
	return paths


func _run_tests() -> void:
	var paths := _autoload_script_paths()
	_assert(paths.size() > 0, "no autoload script paths parsed from project.godot")

	for path in paths:
		var script = load(path)
		_assert(script != null, "autoload script failed to load (parse error): " + path)
		if script == null:
			continue
		_assert(script is Script, "autoload resource is not a Script: " + path)
		if script is Script:
			_assert((script as Script).can_instantiate(),
				"autoload script cannot be instantiated (broken parse): " + path)

	var scene_path := "res://scenes/privacy_modal/privacy_modal.tscn"
	_assert(ResourceLoader.exists(scene_path), "boot scene missing: " + scene_path)
	if ResourceLoader.exists(scene_path):
		var packed = load(scene_path)
		_assert(packed != null, "boot scene failed to load: " + scene_path)
		if packed != null:
			var node = packed.instantiate()
			_assert(node != null, "boot scene failed to instantiate: " + scene_path)
			if node != null:
				node.queue_free()
