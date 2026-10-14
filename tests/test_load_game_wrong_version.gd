extends SceneTree

# B5 (docs/northstar/plans/2026-10-01-architect-rulings-2.md section 2): the save layout
# changed, OM_SAVE_FORMAT_VERSION is 5 (B6 lifecycle fields, ruling 1.8), and save.c rejects every other version. The
# load-game screen must show a rejected save as unreadable and not crash.
#
# Fixtures are real: a live autosave written through the pipe, then a copy whose version
# word (bytes 4..7 of the .omsave, little endian) and sidecar "format_version" are patched
# to 3, the pre-bump layout. tests/test_load_game.gd has a version-999 case; this file adds
# the one that matters after the bump (an old, well-formed save) and the check that a save
# written now is current (sidecar and scene both say 5, so fresh saves are not refused).

const SCENE_PATH := "res://scenes/load_game/load_game.tscn"
const EXPECTED_VERSION := 11

var _pass_count := 0
var _fail_count := 0
var _fail_msgs: Array[String] = []
var _completed := false


func _initialize() -> void:
	await _run()
	_assert(_completed, "the checks did not run to the end (a script error aborted them, or c_bridge.gd lacks saves_dir / list_saves / load / ensure_session)")
	print("\n=== Load Game Wrong-Version Test Results ===")
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


func _row_for(rows: Array, slot_id: String):
	for r in rows:
		if typeof(r) == TYPE_DICTIONARY and str(r.get("slot", "")) == slot_id:
			return r
	return null


func _write_bytes(path: String, bytes: PackedByteArray) -> void:
	var f := FileAccess.open(path, FileAccess.WRITE)
	f.store_buffer(bytes)
	f.close()


func _write_text(path: String, text: String) -> void:
	var f := FileAccess.open(path, FileAccess.WRITE)
	f.store_string(text)
	f.close()


func _run() -> void:
	var CBridge = load("res://autoload/c_bridge.gd")
	var bridge = CBridge.new()
	for m in ["saves_dir", "list_saves", "load", "load_mission_live", "last_error", "ensure_session"]:
		_assert(bridge.has_method(m), "c_bridge.gd missing method: " + m)
		if not bridge.has_method(m):
			return
	var dir: String = bridge.saves_dir()
	_assert(dir.begins_with("/") and DirAccess.dir_exists_absolute(dir), "saves_dir() = %s is not an existing absolute directory" % dir)
	var files := ["campaign_1.omsave", "campaign_1.omsave.json", "campaign_old.omsave", "campaign_old.omsave.json"]
	for f in files:
		DirAccess.remove_absolute(dir.path_join(f))

	_assert(bridge.ensure_session(1, CBridge.DEFAULT_N_REGIONS, CBridge.DEFAULT_FEATURES, false), "ensure_session(1) failed: %s" % bridge.last_error())
	_assert(bridge.load_mission_live(1, CBridge.DEFAULT_N_REGIONS, CBridge.DEFAULT_FEATURES), "load_mission_live failed (last_error = %s)" % bridge.last_error())

	var bytes := FileAccess.get_file_as_bytes(dir.path_join("campaign_1.omsave"))
	_assert(bytes.size() > 8, "campaign_1.omsave missing or too short")
	if bytes.size() <= 8:
		return
	var sidecar = JSON.parse_string(FileAccess.get_file_as_string(dir.path_join("campaign_1.omsave.json")))
	_assert(typeof(sidecar) == TYPE_DICTIONARY, "campaign_1.omsave.json did not parse as a JSON object")
	if typeof(sidecar) != TYPE_DICTIONARY:
		return

	# (1) A save written now carries 5, in the file and in its sidecar.
	var file_version := int(bytes[4]) | (int(bytes[5]) << 8) | (int(bytes[6]) << 16) | (int(bytes[7]) << 24)
	_assert(file_version == EXPECTED_VERSION, "a save written now has version word %d in its header, expected %d" % [file_version, EXPECTED_VERSION])
	_assert(int(sidecar.get("format_version", -1)) == EXPECTED_VERSION,
		"a save written now has sidecar format_version %s, expected %d (csrc/pipe/om_pipe.c writes a constant)" % [sidecar.get("format_version"), EXPECTED_VERSION])

	# (2) The screen's current version is 5 and a fresh save is readable, not refused.
	var packed := load(SCENE_PATH) as PackedScene
	var fresh: Node = packed.instantiate()
	get_root().add_child(fresh)
	await process_frame
	await process_frame
	var st0: Dictionary = fresh.qa_state()
	_assert(int(st0.get("current_version", -1)) == EXPECTED_VERSION,
		"load-game current_version = %s, expected %d (scenes/load_game/load_game.gd CURRENT_SAVE_VERSION)" % [st0.get("current_version"), EXPECTED_VERSION])
	var good0 = _row_for(st0.get("rows", []), "campaign_1")
	_assert(good0 != null and not bool(good0.get("refused", true)), "a save written now shows as refused on the load-game screen: %s" % str(good0))
	fresh.queue_free()
	await process_frame

	# (3) A well-formed version-3 save is refused by the loader and shown as unreadable.
	var old := bytes.duplicate()
	old[4] = 3
	old[5] = 0
	old[6] = 0
	old[7] = 0
	_write_bytes(dir.path_join("campaign_old.omsave"), old)
	var old_side: Dictionary = sidecar.duplicate()
	old_side["format_version"] = 3
	_write_text(dir.path_join("campaign_old.omsave.json"), JSON.stringify(old_side))

	var refused: Dictionary = bridge.load("campaign_old")
	_assert(refused.is_empty(), "load of a version-3 save answered a frame instead of refusing (R-111-03)")
	_assert(bridge.last_error() in ["version mismatch", "corrupt"], "refused load last_error = '%s', expected 'version mismatch' or 'corrupt'" % bridge.last_error())

	var screen: Node = packed.instantiate()
	get_root().add_child(screen)
	await process_frame
	await process_frame
	var st: Dictionary = screen.qa_state()
	var old_row = _row_for(st.get("rows", []), "campaign_old")
	var good = _row_for(st.get("rows", []), "campaign_1")
	_assert(old_row != null, "the version-3 save has no row on the load-game screen; slots = %s" % str((st.get("rows", []) as Array).map(func(r): return r.get("slot"))))
	if old_row != null:
		_assert(bool(old_row.get("refused", false)), "the version-3 save row is not marked refused")
		var label := str(old_row.get("label_text", ""))
		_assert(label.contains("3") and label.contains(str(EXPECTED_VERSION)) and label.to_lower().contains("incompatible"),
			"the version-3 row label should name both versions and say incompatible, got '%s'" % label)
	# Positive control: the same screen shows the current save as loadable, so the refusal above is the version.
	_assert(good != null and not bool(good.get("refused", true)), "control: the current-version save row is missing or refused on the same screen")
	# Not a crash: the screen answers again after the click path on the refused row.
	if screen.has_method("qa_load_slot"):
		var res = screen.qa_load_slot("campaign_old")
		_assert(typeof(res) == TYPE_DICTIONARY and (res as Dictionary).is_empty(), "qa_load_slot on the version-3 row answered a frame (type %s)" % str((res as Dictionary).get("type", "?")) if typeof(res) == TYPE_DICTIONARY else "returned a non-dictionary")
	_assert(typeof(screen.qa_state()) == TYPE_DICTIONARY, "qa_state() stopped answering after loading the refused slot")
	screen.queue_free()
	await process_frame

	for f in files:
		DirAccess.remove_absolute(dir.path_join(f))
	_completed = true
