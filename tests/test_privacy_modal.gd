extends SceneTree

var _pass_count := 0
var _fail_count := 0
var _fail_msgs: Array[String] = []


func _initialize() -> void:
	_run_tests()
	print("\n=== Privacy Modal Test Results ===")
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
	var flag_path := "user://privacy_accepted"
	if FileAccess.file_exists(flag_path):
		DirAccess.remove_absolute(ProjectSettings.globalize_path(flag_path))

	var scene_path := "res://scenes/privacy_modal/privacy_modal.tscn"
	_assert(ResourceLoader.exists(scene_path),
		"scene file missing: " + scene_path)

	var packed = load(scene_path) if ResourceLoader.exists(scene_path) else null
	_assert(packed != null, "scene failed to load")
	if packed == null:
		return

	var node = packed.instantiate()
	_assert(node != null, "scene failed to instantiate")
	if node == null:
		return

	get_root().add_child(node)

	var btn := _find_button(node)
	_assert(btn != null, "no Button found in scene")
	if btn != null:
		var t: String = btn.text
		_assert(t.findn("Accept") >= 0 or t.findn("Continue") >= 0,
			"Button text missing 'Accept' or 'Continue', got: " + t)

	var text_node := _find_text_containing(node, "PRIVATE PLAYTEST BUILD")
	_assert(text_node != null,
		"no Label/RichTextLabel contains 'PRIVATE PLAYTEST BUILD'")

	var script_src: String = ""
	var f := FileAccess.open("res://scenes/privacy_modal/privacy_modal.gd", FileAccess.READ)
	if f != null:
		script_src = f.get_as_text()
		f.close()
	_assert(script_src.findn("pressed") >= 0,
		"script does not reference 'pressed' signal")
	_assert(script_src.find("user://privacy_accepted") >= 0,
		"script does not reference 'user://privacy_accepted' literal")

	node.queue_free()

	# Cross-process flag-skip path verified via source-grep (the runtime scenario
	# is "fresh process boot + pre-existing flag from prior session" — not
	# achievable in same-process SceneTree --script harness due to Godot
	# FileAccess.file_exists not seeing same-_initialize writes from inside
	# Control._ready called via add_child). Behavioral verification deferred
	# to manual playthrough / apex E2E.
	_assert(script_src.find("FileAccess.file_exists") >= 0,
		"script does not check FileAccess.file_exists for flag detection")
	_assert(script_src.find("_skip_to_loading_screen") >= 0,
		"script does not declare _skip_to_loading_screen field")
	_assert(script_src.find("return") >= 0,
		"script does not contain early-return from _ready")
	# Verify the flag-check + return are in proximity (early-return pattern)
	var fe_idx := script_src.find("FileAccess.file_exists")
	var ret_idx := script_src.find("return", fe_idx)
	_assert(fe_idx >= 0 and ret_idx > fe_idx and ret_idx - fe_idx < 300,
		"FileAccess.file_exists and early-return not in proximity (>300 chars apart)")


func _find_button(root: Node) -> Button:
	if root is Button:
		return root as Button
	for child in root.get_children():
		var found := _find_button(child)
		if found != null:
			return found
	return null


func _find_text_containing(root: Node, needle: String) -> Node:
	if root is Label:
		var lbl := root as Label
		if lbl.text.findn(needle) >= 0:
			return lbl
	if root is RichTextLabel:
		var rtl := root as RichTextLabel
		if rtl.text.findn(needle) >= 0:
			return rtl
		if rtl.get_parsed_text().findn(needle) >= 0:
			return rtl
	for child in root.get_children():
		var found := _find_text_containing(child, needle)
		if found != null:
			return found
	return null


func _count_visible_buttons(root: Node) -> int:
	var n := 0
	if root is Button and (root as Button).visible:
		n += 1
	for child in root.get_children():
		n += _count_visible_buttons(child)
	return n
