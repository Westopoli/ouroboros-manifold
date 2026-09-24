extends SceneTree

# Piece C1-2 (docs/northstar/plans/push/pieces.toml C1): the main menu's CONTINUE
# is enabled by the live save list (SimSession.bridge().list_saves(), the pipe's
# sidecar-backed slot list), not the legacy UIDataBus.get_save_slots(). A bridge
# can be injected (qa_set_bridge, like scenes/load_game) so the two cases are
# testable without touching the player's real saves; the live default is proven
# by tests/qa/desktop/test_continue_flow.py.
#
# Contract required of res://scenes/main_menu/main_menu.tscn's root:
#   qa_set_bridge(bridge) -> void   bridge has list_saves() -> Array; re-evaluates CONTINUE
#   qa_state() -> Dictionary        JSON-safe: continue_enabled (bool), slot_count (int)
# and of the CONTINUE menu item: a control named "Continue" (NewGame's sibling naming),
# dimmed and ignoring the mouse when there are no saves. The dim lives on the item's
# Label child: the entrance animation tweens every menu item's own modulate to 1.0 and
# would erase a dim set there.

const SCENE_PATH := "res://scenes/main_menu/main_menu.tscn"

var _pass_count := 0
var _fail_count := 0
var _fail_msgs: Array[String] = []
var _completed := false


class FakeBridge:
	extends RefCounted
	var slots: Array = []

	func list_saves() -> Array:
		return slots


func _initialize() -> void:
	await _run_tests()
	_assert(_completed, "the main-menu checks did not run to the end (a script error aborted them)")
	print("\n=== Main Menu Continue Test Results ===")
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


func _find_named(node: Node, node_name: String):
	if node.name == node_name:
		return node
	for c in node.get_children():
		var found = _find_named(c, node_name)
		if found != null:
			return found
	return null


func _label_alpha(item: Node) -> float:
	for c in item.get_children():
		if c is Label:
			return (c as Label).modulate.a
	return -1.0


func _run_tests() -> void:
	var scene: Node = (load(SCENE_PATH) as PackedScene).instantiate()
	get_root().add_child(scene)
	await process_frame
	await process_frame
	for m in ["qa_set_bridge", "qa_state"]:
		_assert(scene.has_method(m), "main_menu root missing method (piece C1-2 not attached yet): " + m)
		if not scene.has_method(m):
			scene.queue_free()
			return

	var fake := FakeBridge.new()
	scene.qa_set_bridge(fake)
	var none: Dictionary = scene.qa_state()
	_assert(JSON.stringify(none) != "", "qa_state() did not survive JSON.stringify")
	_assert(int(none.get("slot_count", -1)) == 0 and not bool(none.get("continue_enabled", true)),
		"with no saves: slot_count %s continue_enabled %s, expected 0 / false" % [none.get("slot_count"), none.get("continue_enabled")])
	var item = _find_named(scene, "Continue")
	_assert(item != null, "no control named Continue in the main menu")
	if item != null:
		_assert(_label_alpha(item) < 1.0 and (item as Control).mouse_filter == Control.MOUSE_FILTER_IGNORE,
			"with no saves the Continue item should be dimmed and ignore the mouse (label alpha %s, filter %s)" % [_label_alpha(item), (item as Control).mouse_filter])

	fake.slots = [{"slot": "campaign_1", "tick": 10, "chapter": 0, "version": 1}]
	scene.qa_set_bridge(fake)
	var some: Dictionary = scene.qa_state()
	_assert(int(some.get("slot_count", -1)) == 1 and bool(some.get("continue_enabled", false)),
		"with one save: slot_count %s continue_enabled %s, expected 1 / true" % [some.get("slot_count"), some.get("continue_enabled")])
	if item != null:
		_assert((item as Control).mouse_filter != Control.MOUSE_FILTER_IGNORE and is_equal_approx(_label_alpha(item), 1.0),
			"with a save the Continue item should be enabled (label alpha %s, filter %s)" % [_label_alpha(item), (item as Control).mouse_filter])

	scene.queue_free()
	await process_frame
	_completed = true
