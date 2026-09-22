extends SceneTree

# Piece T2g (docs/northstar/plans/push/pieces.toml; docs/northstar/plans/briefs/
# 2026-09-22-two-day-push.md wave-2 row T2g, attach step 9): res://scenes/load_game/
# load_game.tscn is rebound from the legacy UIDataBus.get_save_slots() (Python
# saves) to the C bridge's save-slot contract (depends on attach/T2c, attach/T1).
# The scene already exists today (the Python-era slot screen); this file is red
# on missing methods (the rebind has not happened), not a parse error and not a
# missing scene.
#
# Contract this test requires of the root node (recorded verbatim in
# docs/northstar/proving_ground/evidence/push_2026-09-22/c5_t2g_tests_note.md):
#   qa_set_bridge(bridge) -> void     injects a save-slot source implementing
#                                     list_saves() -> Array and load(slot_id:
#                                     String) -> Dictionary (this test's
#                                     FakeBridge stands in for autoload/
#                                     c_bridge.gd, piece C2, not built yet
#                                     either -- the wiring shape is what's
#                                     tested, not the live pipe); replaces the
#                                     slot list immediately from bridge.list_saves()
#   qa_state() -> Dictionary          JSON-safe: slot_count, current_version,
#                                     has_save_button, rows [{slot, tick,
#                                     chapter, version, refused, label_text}]
#                                     -- one row per bridge.list_saves() entry,
#                                     `label_text` is whatever text the row
#                                     actually renders (checked for both
#                                     version numbers on a refusal, R-111-03)
#   qa_load_slot(slot_id: String) -> Dictionary   drives the same load action a
#                                     click on that slot's card would (stands
#                                     in for a synthetic mouse click on a
#                                     dynamically built card); calls the
#                                     injected bridge's load(slot_id) and
#                                     returns its result verbatim
#
# list_saves() contract (task brief, verbatim): an array of {slot, tick,
# chapter, version}; this test's fixtures add an extra "checksum" field for
# their own bookkeeping only (C transport v1's "a client ignores keys it does
# not know" rule, docs/architecture.md) so R-111-02 can compare "the slot's
# recorded checksum" against the post-load snapshot's checksum without a
# second, uncontracted accessor.

const SCENE_PATH := "res://scenes/load_game/load_game.tscn"
const CONTRACT_METHODS := ["qa_set_bridge", "qa_state", "qa_load_slot"]

var _pass_count := 0
var _fail_count := 0
var _fail_msgs: Array[String] = []
var _root: Node


class FakeBridge:
	extends RefCounted
	var slots: Array = []
	var load_calls: Array = []
	var load_results: Dictionary = {}

	func list_saves() -> Array:
		return slots

	func load(slot_id: String) -> Dictionary:
		load_calls.append(slot_id)
		return load_results.get(slot_id, {})


func _initialize() -> void:
	await _run_tests()
	print("\n=== Load Game Test Results ===")
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
	_assert(ResourceLoader.exists(SCENE_PATH), "scene file missing: " + SCENE_PATH)
	if not ResourceLoader.exists(SCENE_PATH):
		return

	var packed = load(SCENE_PATH)
	_assert(packed != null, "%s failed to load (parse error)" % SCENE_PATH)
	if packed == null or not (packed is PackedScene):
		return

	_root = (packed as PackedScene).instantiate()
	_assert(_root != null, "%s failed to instantiate" % SCENE_PATH)
	if _root == null:
		return
	get_root().add_child(_root)
	await process_frame
	await process_frame

	for m in CONTRACT_METHODS:
		_assert(_root.has_method(m), "load_game root missing method (T2g rebind not done): " + m)
	if not (_root.has_method("qa_set_bridge") and _root.has_method("qa_state") and _root.has_method("qa_load_slot")):
		_root.queue_free()
		return

	_check_qa_state_json_safe()
	_check_no_save_button_mid_mission_R111_04()
	var current_version := _check_current_version_present()
	_check_version_mismatch_refused_R111_03(current_version)
	_check_load_calls_bridge_and_checksum_matches_R111_02(current_version)
	_check_unlimited_slots_thirty_rows_R111_04(current_version)

	_root.queue_free()


func _check_qa_state_json_safe() -> void:
	var text := JSON.stringify(_root.qa_state())
	_assert(text != "", "qa_state() did not survive JSON.stringify")


# R-111-04: there is no save of any kind during a mission; this screen (the
# campaign continue/load list) never offers a save action at all. Positive
# control: the same tree-walk that would find a "SAVE" button does find the
# BACK button that already exists today, proving the search mechanism works.
func _check_no_save_button_mid_mission_R111_04() -> void:
	var state: Dictionary = _root.qa_state()
	_assert(state.has("has_save_button"), "qa_state() missing key 'has_save_button'")
	_assert(bool(state.get("has_save_button", true)) == false,
		"R-111-04: has_save_button should be false, this screen never offers a manual save")

	var back_btn := _find_button_containing(_root, "back")
	_assert(back_btn != null, "positive control failed: no BACK button found by the tree-walk (search mechanism itself is broken)")

	var save_btn := _find_button_containing(_root, "save")
	_assert(save_btn == null,
		"R-111-04: found a button whose text contains 'save' in the campaign list: " + str(save_btn))


func _check_current_version_present() -> int:
	var state: Dictionary = _root.qa_state()
	_assert(state.has("current_version"), "qa_state() missing key 'current_version'")
	var v := int(state.get("current_version", -1))
	_assert(v >= 0, "current_version should be a non-negative int, got %s" % v)
	return v


func _check_version_mismatch_refused_R111_03(current_version: int) -> void:
	if current_version < 0:
		return
	var mismatched_version := current_version + 1
	var bridge := FakeBridge.new()
	bridge.slots = [
		{"slot": "slot_ok", "tick": 500, "chapter": 3, "version": current_version},
		{"slot": "slot_bad", "tick": 700, "chapter": 4, "version": mismatched_version},
	]
	_root.qa_set_bridge(bridge)

	var state: Dictionary = _root.qa_state()
	var rows: Array = state.get("rows", [])
	_assert(rows.size() == 2, "expected 2 rows after qa_set_bridge with 2 slots, got %d" % rows.size())

	var ok_row = _row_for(rows, "slot_ok")
	var bad_row = _row_for(rows, "slot_bad")
	_assert(ok_row != null, "no row rendered for slot_ok")
	_assert(bad_row != null, "no row rendered for slot_bad")
	if ok_row == null or bad_row == null:
		return

	_assert(bool(ok_row.get("refused", true)) == false,
		"slot_ok's version matches the build; it should not render as refused")
	_assert(bool(bad_row.get("refused", false)) == true,
		"R-111-03: slot_bad's version does not match the build; it should render as refused")

	var label: String = str(bad_row.get("label_text", ""))
	_assert(label.contains(str(current_version)) and label.contains(str(mismatched_version)),
		"R-111-03: the refused slot's label should name both versions (%d and %d), got '%s'" % [current_version, mismatched_version, label])


func _check_load_calls_bridge_and_checksum_matches_R111_02(current_version: int) -> void:
	if current_version < 0:
		return
	var recorded_checksum := 918273645
	var bridge := FakeBridge.new()
	bridge.slots = [
		{"slot": "slot_x", "tick": 42, "chapter": 2, "version": current_version, "checksum": recorded_checksum},
	]
	bridge.load_results["slot_x"] = {"type": "snapshot", "tick": 42, "checksum": recorded_checksum, "regions": [], "factions": [], "edges": []}
	_root.qa_set_bridge(bridge)

	var result: Dictionary = _root.qa_load_slot("slot_x")
	_assert(bridge.load_calls == ["slot_x"],
		"R-111-02: loading slot_x should call the bridge's load exactly once with 'slot_x', calls were %s" % str(bridge.load_calls))
	_assert(int(result.get("checksum", -1)) == recorded_checksum,
		"R-111-02: the post-load snapshot's checksum (%s) should equal the slot's recorded checksum (%d)" % [result.get("checksum"), recorded_checksum])


func _check_unlimited_slots_thirty_rows_R111_04(current_version: int) -> void:
	if current_version < 0:
		return
	var bridge := FakeBridge.new()
	var slots := []
	for i in range(30):
		slots.append({"slot": "slot_%d" % i, "tick": i * 10, "chapter": (i % 5) + 1, "version": current_version})
	bridge.slots = slots
	_root.qa_set_bridge(bridge)

	var state: Dictionary = _root.qa_state()
	_assert(int(state.get("slot_count", -1)) == 30,
		"R-111-04: no fixed slot limit; slot_count should be 30, got %s" % state.get("slot_count"))
	_assert(state.get("rows", []).size() == 30,
		"R-111-04: 30 fixture slots should render 30 rows, got %d" % state.get("rows", []).size())


func _row_for(rows: Array, slot_id: String):
	for r in rows:
		if typeof(r) == TYPE_DICTIONARY and str(r.get("slot", "")) == slot_id:
			return r
	return null


func _find_button_containing(root: Node, needle: String) -> Node:
	if root is BaseButton:
		var b := root as BaseButton
		var raw = b.get("text")
		var t: String = str(raw) if raw != null else ""
		if b.visible and t.findn(needle) >= 0:
			return b
	for child in root.get_children():
		var found := _find_button_containing(child, needle)
		if found != null:
			return found
	return null
