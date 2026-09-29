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
var _live_tests_completed := false


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
	_check_no_dead_delete_ui_T2g_4()
	_check_live_row_button_and_qa_state_shape_T2g_4(current_version)

	_root.queue_free()

	await _run_live_tests(current_version)
	_assert(_live_tests_completed, "the live-save checks did not run to the end (a script error aborted them, or c_bridge.gd lacks saves_dir / list_saves / load / DEFAULT_FEATURES)")

	# T2g-4 item 4: the live (qa_set_bridge-driven) render/click path must be
	# unaffected by the dead-code removal. This runs last, with no
	# `await process_frame` between the click below and the process quitting
	# in _initialize(), so SceneRouter's fade tween (real seconds of wall
	# time) never gets a frame to advance on and cannot try to actually swap
	# in scenes/galaxy/galaxy_view.tscn mid-test-run.
	await _check_load_click_routes_to_galaxy_T2g_4(current_version)


# Piece T2g-2 (docs/architecture.md "Save slots (T2g-2 rulings)"): c_bridge.gd
# is the real bridge behind the scene. The live mission/debrief/chronicle
# loads autosave the world to <saves_dir>/campaign_<seed>.omsave (R-111-01,
# never mid-mission: no autosave from the tactical load), list_saves()
# reads the sidecars through the pipe's list_saves command, and load(slot)
# answers the post-load snapshot or {} with last_error() set (R-111-03).
# The scene shows the live rows when no bridge was injected. Known gap when
# this was written: routing a loaded slot into the galaxy needs C2-4's
# persistent pipe session, so a card click loads through the bridge only.
func _run_live_tests(current_version: int) -> void:
	var CBridge = load("res://autoload/c_bridge.gd")
	var bridge = CBridge.new()
	for m in ["saves_dir", "list_saves", "load", "load_mission_live", "last_error"]:
		_assert(bridge.has_method(m), "c_bridge.gd missing method (piece T2g-2 not attached yet): " + m)
		if not bridge.has_method(m):
			return
	if not CBridge.get_script_constant_map().has("DEFAULT_FEATURES"):
		_assert(false, "c_bridge.gd missing constant DEFAULT_FEATURES")
		return

	var dir: String = bridge.saves_dir()
	_assert(dir.begins_with("/") and DirAccess.dir_exists_absolute(dir), "saves_dir() = %s is not an existing absolute directory" % dir)
	for f in ["campaign_1.omsave", "campaign_1.omsave.json", "campaign_bad.omsave", "campaign_bad.omsave.json"]:
		DirAccess.remove_absolute(dir.path_join(f))

	_assert(bridge.load_mission_live(1, CBridge.DEFAULT_N_REGIONS, CBridge.DEFAULT_FEATURES), "load_mission_live failed (last_error = %s)" % bridge.last_error())
	var rows: Array = bridge.list_saves()
	var row = _row_for(rows, "campaign_1")
	_assert(row != null, "no campaign_1 row after the live mission load's autosave (R-111-01); slots = %s" % str(rows.map(func(r): return r.get("slot"))))
	if row == null:
		return
	_assert(int(row.get("tick", -1)) == 0, "autosave row tick = %s, expected 0 (mission_start on a fresh world, C2-6 no longer pre-steps)" % row.get("tick"))
	_assert(int(row.get("version", -1)) == current_version, "autosave row version = %s, the scene's current_version is %s" % [row.get("version"), current_version])

	var snap: Dictionary = bridge.load("campaign_1")
	_assert(snap.get("type", "") == "snapshot" and (snap.get("regions", []) as Array).size() == CBridge.DEFAULT_N_REGIONS,
		"load(campaign_1) did not answer an 80-region snapshot (last_error = %s)" % bridge.last_error())
	_assert(int(snap.get("tick", -1)) == 0, "loaded snapshot tick = %s, expected 0" % snap.get("tick", -1))
	var snap2: Dictionary = bridge.load("campaign_1")
	_assert(snap2.get("checksum", 1) == snap.get("checksum", 2), "loading the same slot twice gave different checksums (R-111-02)")

	var tactical = CBridge.new()
	DirAccess.remove_absolute(dir.path_join("campaign_1.omsave"))
	DirAccess.remove_absolute(dir.path_join("campaign_1.omsave.json"))
	tactical.load_tactical_live(1, CBridge.DEFAULT_N_REGIONS, CBridge.DEFAULT_FEATURES)
	_assert(_row_for(tactical.list_saves(), "campaign_1") == null, "the tactical (mid-mission) load wrote an autosave (R-111-04)")
	bridge.load_mission_live(1, CBridge.DEFAULT_N_REGIONS, CBridge.DEFAULT_FEATURES)

	var bytes := FileAccess.get_file_as_bytes(dir.path_join("campaign_1.omsave"))
	_assert(bytes.size() > 8, "campaign_1.omsave missing or too short")
	if bytes.size() > 8:
		bytes[4] = 231
		bytes[5] = 3
		bytes[6] = 0
		bytes[7] = 0
		var bad_file := FileAccess.open(dir.path_join("campaign_bad.omsave"), FileAccess.WRITE)
		bad_file.store_buffer(bytes)
		bad_file.close()
		var sidecar = JSON.parse_string(FileAccess.get_file_as_string(dir.path_join("campaign_1.omsave.json")))
		sidecar["format_version"] = 999
		var bad_side := FileAccess.open(dir.path_join("campaign_bad.omsave.json"), FileAccess.WRITE)
		bad_side.store_string(JSON.stringify(sidecar))
		bad_side.close()
		var refused: Dictionary = bridge.load("campaign_bad")
		_assert(refused.is_empty(), "load of a version-999 save answered a frame instead of refusing (R-111-03)")
		_assert(bridge.last_error() in ["version mismatch", "corrupt"], "refused load last_error = '%s', expected 'version mismatch' or 'corrupt'" % bridge.last_error())

	var fresh: Node = (load(SCENE_PATH) as PackedScene).instantiate()
	get_root().add_child(fresh)
	await process_frame
	await process_frame
	var st: Dictionary = fresh.qa_state()
	var live_rows: Array = bridge.list_saves()
	_assert(int(st.get("slot_count", -1)) == live_rows.size() and live_rows.size() >= 2,
		"scene with no injected bridge shows %s slots, the live bridge lists %d" % [st.get("slot_count"), live_rows.size()])
	var good = _row_for(st.get("rows", []), "campaign_1")
	var bad = _row_for(st.get("rows", []), "campaign_bad")
	_assert(good != null and not bool(good.get("refused", true)), "live campaign_1 row missing or refused")
	_assert(bad != null and bool(bad.get("refused", false)) and str(bad.get("label_text", "")).contains("999") and str(bad.get("label_text", "")).contains(str(current_version)),
		"live campaign_bad row not refused with both versions in its label")
	if good != null:
		_assert(_find_label_with_text(fresh, str(good.get("label_text", ""))) != null, "no Label on screen shows the live row text '%s'" % good.get("label_text"))
	fresh.queue_free()
	await process_frame

	for f in ["campaign_1.omsave", "campaign_1.omsave.json", "campaign_bad.omsave", "campaign_bad.omsave.json"]:
		DirAccess.remove_absolute(dir.path_join(f))
	_live_tests_completed = true


func _find_label_with_text(node: Node, text: String):
	if node is Label and (node as Label).text == text:
		return node
	for c in node.get_children():
		var found = _find_label_with_text(c, text)
		if found != null:
			return found
	return null


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


# T2g-4 (docs/northstar/plans/2026-09-28-gap-fix-and-migration-plan.md, G1):
# load_game.gd carries a dead legacy save-card path (_refresh_slots,
# _add_slot_card, _format_playtime) and an unused delete-confirm overlay
# (_build_confirm_overlay, _show_delete_confirm) built into the scene tree
# on every load even though nothing calls it -- no E-16 rule covers deleting
# a save, so none of this should exist after the cleanup. Positive control:
# qa_state's own has_method check proves has_method() finds a method that IS
# still there, so a false result below means the method is genuinely gone,
# not a broken check.
func _check_no_dead_delete_ui_T2g_4() -> void:
	_assert(_root.has_method("qa_state"), "positive control failed: qa_state should still exist on the root")

	var overlay := _root.find_child("DeleteConfirmBtn", true, false)
	_assert(overlay == null,
		"T2g-4: found a node named 'DeleteConfirmBtn' in the scene tree (dead delete-confirm overlay should be gone): " + str(overlay))

	var glyph_btn := _find_button_with_exact_text(_root, "×")
	_assert(glyph_btn == null,
		"T2g-4: found a Button with the delete glyph '×' as its text (dead per-row delete button should be gone): " + str(glyph_btn))

	for m in ["_refresh_slots", "_add_slot_card", "_show_delete_confirm", "_build_confirm_overlay", "_format_playtime"]:
		_assert(not _root.has_method(m),
			"T2g-4: load_game.gd should no longer define dead method " + m)


# T2g-4 item 4: the live path (qa_set_bridge -> _render_bridge_rows, the
# real production code, not the dead legacy cards) must render exactly one
# row per slot with a "LOAD" button, and qa_state()'s shape/values the
# dead-code removal is not supposed to touch must stay exactly as they are
# today.
func _check_live_row_button_and_qa_state_shape_T2g_4(current_version: int) -> void:
	if current_version < 0:
		return
	# Earlier fixture checks in this pass called qa_set_bridge() back to back
	# with no `await process_frame` between them, so their own queue_free()'d
	# rows (different slot ids: slot_ok/slot_bad/slot_x/slot_0.../slot_29)
	# can still be children of the list here (deferred, not yet actually
	# freed). Harmless for this check since each row's LOAD button is named
	# "Load_<slot id>" and this batch's ids (slot_a/b/c) are disjoint from
	# every earlier batch's, but it rules out a plain "count every LOAD-text
	# button in the whole tree" assertion, which would double-count those
	# leftovers. The per-slot exact-name lookups below are unaffected.
	var bridge := FakeBridge.new()
	bridge.slots = [
		{"slot": "slot_a", "tick": 10, "chapter": 1, "version": current_version},
		{"slot": "slot_b", "tick": 20, "chapter": 2, "version": current_version},
		{"slot": "slot_c", "tick": 30, "chapter": 3, "version": current_version},
	]
	_root.qa_set_bridge(bridge)

	for slot in bridge.slots:
		var matches := _root.find_children("Load_" + str(slot["slot"]), "", true, false)
		_assert(matches.size() == 1,
			"T2g-4: expected exactly one LOAD button named 'Load_%s', found %d" % [slot["slot"], matches.size()])
		if matches.size() >= 1:
			_assert(matches[0] is Button and (matches[0] as Button).text == "LOAD",
				"T2g-4: node named 'Load_%s' is not a Button with text 'LOAD'" % slot["slot"])

	var state: Dictionary = _root.qa_state()
	var expected_keys := ["scene", "tick", "slot_count", "current_version", "has_save_button", "rows", "plants"]
	for k in expected_keys:
		_assert(state.has(k), "T2g-4: qa_state() is missing key '%s' (shape changed)" % k)
	_assert(state.keys().size() == expected_keys.size(),
		"T2g-4: qa_state() has %d keys, expected exactly %d (%s), got %s" % [state.keys().size(), expected_keys.size(), str(expected_keys), str(state.keys())])
	_assert(str(state.get("scene", "")) == "load_game", "T2g-4: qa_state().scene changed, got '%s'" % state.get("scene"))
	_assert(int(state.get("tick", 0)) == -1, "T2g-4: qa_state().tick changed, got %s" % state.get("tick"))
	_assert(bool(state.get("has_save_button", true)) == false, "T2g-4: qa_state().has_save_button changed, got %s" % state.get("has_save_button"))
	_assert((state.get("plants", null) as Array) == [], "T2g-4: qa_state().plants changed, got %s" % [state.get("plants")])
	_assert(int(state.get("slot_count", -1)) == bridge.slots.size(), "T2g-4: qa_state().slot_count = %s, expected %d" % [state.get("slot_count"), bridge.slots.size()])


# T2g-4 item 4, continued: a click on a LOAD row must still call through to
# the injected bridge and still route to the galaxy exactly as before. Must
# run last in _run_tests() with no further `await process_frame` -- see the
# comment at the call site.
func _check_load_click_routes_to_galaxy_T2g_4(current_version: int) -> void:
	if current_version < 0:
		return
	var scene: Node = (load(SCENE_PATH) as PackedScene).instantiate()
	get_root().add_child(scene)
	await process_frame
	await process_frame

	var bridge := FakeBridge.new()
	bridge.slots = [{"slot": "slot_click", "tick": 5, "chapter": 1, "version": current_version}]
	bridge.load_results["slot_click"] = {"type": "snapshot", "tick": 5, "checksum": 7, "regions": [], "factions": [], "edges": []}
	scene.qa_set_bridge(bridge)

	var load_btn: Node = scene.find_child("Load_slot_click", true, false)
	_assert(load_btn != null and load_btn is Button, "T2g-4: no LOAD button found for slot_click to click")
	if load_btn == null:
		scene.queue_free()
		return

	# SceneRouter is a project autoload; this test script is itself the
	# SceneTree's main --script entry, loaded before autoload globals are
	# registered as compile-time identifiers, so it is reached by node path
	# instead of the bare "SceneRouter" identifier (which fails to compile
	# here even though it resolves fine from a normally-loaded scene script
	# like load_game.gd or scene_router.gd itself).
	var scene_router: Node = get_root().get_node("SceneRouter")
	scene_router.set("_current_scene_name", "not_galaxy_yet_T2g_4_sentinel")
	(load_btn as Button).pressed.emit()

	_assert(bridge.load_calls == ["slot_click"],
		"T2g-4: clicking LOAD should call the bridge's load exactly once with 'slot_click', calls were %s" % str(bridge.load_calls))
	var routed_name: String = str(scene_router.get("_current_scene_name"))
	_assert(routed_name == "galaxy",
		"T2g-4: clicking LOAD on a successful slot should route to the galaxy (SceneRouter._current_scene_name = '%s')" % routed_name)


func _find_button_with_exact_text(root: Node, text: String) -> Node:
	if root is BaseButton:
		var raw = (root as BaseButton).get("text")
		if raw != null and str(raw) == text:
			return root
	for child in root.get_children():
		var found := _find_button_with_exact_text(child, text)
		if found != null:
			return found
	return null


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
