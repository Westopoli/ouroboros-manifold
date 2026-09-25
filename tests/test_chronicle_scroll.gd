extends SceneTree

# Piece C3 (docs/northstar/plans/briefs/2026-09-22-two-day-push.md wave-2 row
# C3; docs/northstar/plans/push/pieces.toml id C3, owns_glob
# scenes/world/chronicle_*, depends_on B8/T1): res://scenes/world/
# chronicle_scroll_panel.tscn's root gains a rebind entry point,
# load_frame(frame: Dictionary), that consumes a C transport v1 chronicle
# frame (docs/architecture.md "chronicle frame, mission frame, debrief
# frame") instead of the legacy {entry_id, base_form, expanded_form,
# mentions[]} shape queue_entry()/begin_time_jump() take today. The frame
# carries no prose (C5 rule): each entry's "fragment" is a
# simulation/library/chronicle/fragments.json id the panel resolves to text,
# falling back to "[fragment <id>]" when the id is absent (the fixture's
# fragment ids are all deliberately unassigned so every entry proves the
# fallback path). Full contract documented at docs/northstar/proving_ground/
# evidence/push_2026-09-22/c3_c4_tests_note.md. Bible:
# docs/bible/epics/E-09-chronicle.md R-065-01, R-068-02/07/08, R-069-01..06.

const SCENE_PATH := "res://scenes/world/chronicle_scroll_panel.tscn"
const FRAME_FIXTURE_PATH := "res://tests/fixtures/chronicle_frame_seed11.json"
const SNAPSHOT_FIXTURE_PATH := "res://tests/transport/fixtures/snapshot_seed1_tick10.json"
const FRAME_FALLBACK_PATH := "user://test_chronicle_scroll_fallback_frame.json"
const SNAPSHOT_FALLBACK_PATH := "user://test_chronicle_scroll_fallback_snapshot.json"
const N_REGIONS := 60
const PLANTS := ["entries-dropped", "refs-unresolved"]
const BAD_REGION_ID := 9999
const BAD_FACTION_ID := 99

var _pass_count := 0
var _fail_count := 0
var _fail_msgs: Array[String] = []
var _root: Node
var _snapshot: Dictionary
var _frame: Dictionary
var _live_tests_completed := false


func _initialize() -> void:
	await _run_tests()
	print("\n=== Chronicle Scroll Test Results ===")
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
	_snapshot = _load_snapshot()
	_assert(not _snapshot.is_empty(), "could not obtain a snapshot (fixture missing and fallback write failed)")
	_frame = _load_frame()
	_assert(not _frame.is_empty(), "could not obtain a chronicle frame (fixture missing and fallback write failed)")

	var packed = load(SCENE_PATH)
	_assert(packed != null, "cannot load %s" % SCENE_PATH)
	if packed == null or not (packed is PackedScene):
		return

	_root = (packed as PackedScene).instantiate()
	_assert(_root != null, "%s failed to instantiate" % SCENE_PATH)
	if _root == null:
		return
	get_root().add_child(_root)
	await process_frame
	await process_frame

	for m in ["set_snapshot", "load_frame", "qa_state", "qa_plant", "qa_click_entry", "qa_dismiss"]:
		_assert(_root.has_method(m), "chronicle_scroll_panel root missing method (piece C3 not attached yet): " + m)
	if not (_root.has_method("set_snapshot") and _root.has_method("load_frame")
			and _root.has_method("qa_state") and _root.has_method("qa_plant")
			and _root.has_method("qa_click_entry") and _root.has_method("qa_dismiss")):
		return

	_root.set_snapshot(_snapshot)
	_root.load_frame(_frame.duplicate(true))
	await process_frame

	_check_qa_state_json_safe()
	_check_entries_count_R065_01()
	_check_dropped_entries_zero_clean()
	_check_refs_resolve_R068_07()
	_check_prose_from_fragment_not_frame()
	_check_pace_R069_02()
	_check_hash_determinism_R068_08()
	_check_expanded_id_contract_R069_04()
	_check_plant_refs_unresolved()
	_check_plant_entries_dropped()
	_check_plant_nope_is_false()

	# C3-4: library resolution and server-field isolation.
	_check_library_fragment_resolves_C3_4()
	_check_poisoned_server_text_ignored_C3_4()

	# C3-6: fragment_ids array support (-1 structural line and real ids).
	_check_fragment_ids_all_minus_one_C3_6()
	_check_fragment_ids_real_C3_6()

	await _run_live_tests()
	_assert(_live_tests_completed, "the live-frame checks did not run to the end (a script error aborted them, or c_bridge.gd lacks load_chronicle_live / chronicle_frame / chronicle_snapshot / DEFAULT_FEATURES)")


# Piece C3-3 (docs/architecture.md "session commands (v1.1)"): with no
# load_frame() call the panel reads the frame the live pipe answers to
# jump (c_bridge.gd load_chronicle_live: fresh world, 10 steps, a 50-tick
# jump), plus the snapshot that follows it for ref resolution, not the
# tests/fixtures and tests/transport/fixtures files. The live world's frame
# differs from the fixture (its jump ticks and entry list), so a panel that
# still shows the fixture cannot pass the hash comparison. Known sim-side
# gap when this was written: the live frame's entries list arrives empty
# (chronicle refs and fragment ids owed by the sim), so the panel is only
# asserted to show exactly what the live frame carries, whatever that is.
func _run_live_tests() -> void:
	var CBridge = load("res://autoload/c_bridge.gd")
	var bridge = CBridge.new()
	for m in ["load_chronicle_live", "chronicle_frame", "chronicle_snapshot", "last_error"]:
		_assert(bridge.has_method(m), "c_bridge.gd missing method (piece C3-3 not attached yet): " + m)
		if not bridge.has_method(m):
			return
	if not CBridge.get_script_constant_map().has("DEFAULT_FEATURES"):
		_assert(false, "c_bridge.gd missing constant DEFAULT_FEATURES")
		return

	var ok: bool = bridge.load_chronicle_live(1, CBridge.DEFAULT_N_REGIONS, CBridge.DEFAULT_FEATURES)
	_assert(ok, "load_chronicle_live(1, %d, DEFAULT_FEATURES) returned false (last_error = %s)" % [CBridge.DEFAULT_N_REGIONS, bridge.last_error()])
	var live_frame: Dictionary = bridge.chronicle_frame()
	var live_snapshot: Dictionary = bridge.chronicle_snapshot()
	_assert(live_frame.get("type", "") == "chronicle", "live chronicle frame type = %s, expected chronicle" % live_frame.get("type", ""))
	var jump: Dictionary = live_frame.get("jump", {})
	_assert(int(jump.get("to_tick", 0)) - int(jump.get("from_tick", 0)) == 50, "live jump spans %s ticks, expected 50" % (int(jump.get("to_tick", 0)) - int(jump.get("from_tick", 0))))
	_assert(live_frame.get("entries", null) is Array, "live chronicle frame has no entries array")
	_assert(live_snapshot.get("type", "") == "snapshot" and (live_snapshot.get("regions", []) as Array).size() == CBridge.DEFAULT_N_REGIONS,
		"the snapshot after the jump is missing or has the wrong region count")

	var again = CBridge.new()
	again.load_chronicle_live(1, CBridge.DEFAULT_N_REGIONS, CBridge.DEFAULT_FEATURES)
	_assert(again.chronicle_frame() == live_frame, "same seed answered two different chronicle frames (determinism)")

	var bad = CBridge.new()
	_assert(not bad.load_chronicle_live(1, 30, CBridge.DEFAULT_FEATURES), "load_chronicle_live at 30 regions (below the feasibility floor) returned true")
	_assert(bad.last_error() != "", "a failed live chronicle load left last_error empty (silent failure)")
	_assert(bad.chronicle_frame().is_empty(), "a failed live chronicle load still exposed a chronicle frame")

	_assert(hash(live_frame) != hash(_frame), "live chronicle frame equals the fixture; the live check below cannot tell them apart (fixture control)")

	# The scenes share one process-wide session (autoload/sim_session.gd, C2-6):
	# start the scene under test on a fresh world, the one the private bridge
	# above answered from.
	load("res://autoload/sim_session.gd").reset()
	var fresh: Node = (load(SCENE_PATH) as PackedScene).instantiate()
	get_root().add_child(fresh)
	await process_frame
	await process_frame
	var st: Dictionary = fresh.qa_state()
	_assert(int(st.get("hash", 0)) == hash(live_frame),
		"panel with no load_frame() call shows frame hash %s, live frame hash is %s (still showing the fixture?)" % [st.get("hash"), hash(live_frame)])
	_assert((st.get("entries", []) as Array).size() + int(st.get("dropped_entries", 0)) == (live_frame.get("entries", []) as Array).size(),
		"panel shows %d entries + %d dropped, live frame carries %d" % [(st.get("entries", []) as Array).size(), int(st.get("dropped_entries", 0)), (live_frame.get("entries", []) as Array).size()])
	fresh.queue_free()
	await process_frame
	_live_tests_completed = true


func _check_qa_state_json_safe() -> void:
	var text := JSON.stringify(_root.qa_state())
	_assert(text != "", "qa_state() did not survive JSON.stringify")


func _check_entries_count_R065_01() -> void:
	var state: Dictionary = _root.qa_state()
	var entries: Array = state.get("entries", [])
	_assert(entries.size() == 6,
		"R-065-01: qa_state().entries has %d entries, expected 6 from the fixture" % entries.size())


func _check_dropped_entries_zero_clean() -> void:
	var state: Dictionary = _root.qa_state()
	_assert(int(state.get("dropped_entries", -1)) == 0,
		"clean fixture should drop nothing: dropped_entries = %s, expected 0" % state.get("dropped_entries"))


# R-068-07 as cited by the brief for this piece: every ref in a finished
# entry must name a region/faction that actually exists (grounded, per the
# epic's purpose paragraph), checked against the same snapshot the galaxy
# view/c_bridge use (tests/transport/fixtures/snapshot_seed1_tick10.json).
func _check_refs_resolve_R068_07() -> void:
	var state: Dictionary = _root.qa_state()
	_assert(int(state.get("unresolved_refs", -1)) == 0,
		"R-068-07: clean fixture refs all name real regions/factions from the snapshot, unresolved_refs = %s" % state.get("unresolved_refs"))

	var owners: Dictionary = state.get("owners", {})
	var expected_regions := _distinct_region_refs(_frame)
	_assert(owners.size() == expected_regions.size(),
		"owners has %d entries, expected one per referenced region (%d)" % [owners.size(), expected_regions.size()])

	var mismatches := 0
	for rid in expected_regions:
		var expected_owner := _region_owner(_snapshot, rid)
		var actual = owners.get(rid, owners.get(str(rid), null))
		if actual == null or int(actual) != expected_owner:
			mismatches += 1
	_assert(mismatches == 0,
		"R-068-07: %d referenced region(s) have owners[i] != the snapshot fixture's owner" % mismatches)


func _check_prose_from_fragment_not_frame() -> void:
	var frame_entries: Array = _frame.get("entries", [])
	for e in frame_entries:
		_assert(not (e.has("text") or e.has("base_form") or e.has("prose") or e.has("expanded_form")),
			"test fixture bug: chronicle frame entries must carry no prose (C5 rule), found a text-like key on entry %s" % e.get("id"))
	var fragment_by_id := {}
	for e in frame_entries:
		fragment_by_id[int(e.get("id"))] = int(e.get("fragment"))

	var state: Dictionary = _root.qa_state()
	var entries: Array = state.get("entries", [])
	var placeholder_count := 0
	for entry in entries:
		var eid := int(entry.get("entry_id", -1))
		_assert(fragment_by_id.has(eid), "qa_state() entry_id %d does not match any fixture entry id" % eid)
		var expected_fragment: int = fragment_by_id.get(eid, -1)
		var fid := int(entry.get("fragment_id", -2))
		_assert(fid == expected_fragment,
			"entry %d: fragment_id = %d, expected %d (the frame's own fragment id; the panel looks prose up, it does not carry it)" % [eid, fid, expected_fragment])
		var text: String = str(entry.get("text", ""))
		_assert(text != "", "entry %d has no rendered text" % eid)
		if text == "[fragment %d]" % fid:
			placeholder_count += 1
	_assert(placeholder_count == entries.size(),
		"every fixture fragment id (910201..910206) is deliberately absent from simulation/library/chronicle/fragments.json; expected all %d entries to render the '[fragment <id>]' placeholder (docs/architecture.md's own example), got %d" % [entries.size(), placeholder_count])


func _check_pace_R069_02() -> void:
	var state: Dictionary = _root.qa_state()
	var pace: Dictionary = state.get("pace", {})
	_assert(is_equal_approx(float(pace.get("word_interval_s", -1.0)), 0.08),
		"R-069-02: pace.word_interval_s = %s, expected 0.08" % pace.get("word_interval_s"))
	_assert(is_equal_approx(float(pace.get("fade_s", -1.0)), 0.20),
		"R-069-02: pace.fade_s = %s, expected 0.20" % pace.get("fade_s"))


func _check_hash_determinism_R068_08() -> void:
	var h1 = _root.qa_state().get("hash")
	_root.load_frame(_frame.duplicate(true))
	var h2 = _root.qa_state().get("hash")
	_assert(h1 != null and h1 == h2,
		"R-068-08: load_frame() twice on the same frame must give an equal, non-null hash (got %s then %s)" % [h1, h2])


func _check_expanded_id_contract_R069_04() -> void:
	var before = _root.qa_state().get("expanded_id")
	_assert(before == null or str(before) == "" or int(before) == -1,
		"clean: expanded_id should be empty before any click (positive control), got %s" % before)

	var target_id := int(_frame["entries"][0]["id"])
	_root.qa_click_entry(target_id)
	var opened = _root.qa_state().get("expanded_id")
	_assert(int(opened) == target_id,
		"R-069-04: qa_click_entry(%d) should set expanded_id to %d, got %s" % [target_id, target_id, opened])

	_root.qa_dismiss()
	var after = _root.qa_state().get("expanded_id")
	_assert(after == null or str(after) == "" or int(after) == -1,
		"R-069-04: qa_dismiss() should clear expanded_id, got %s" % after)


func _bad_ref_frame() -> Dictionary:
	var f: Dictionary = _frame.duplicate(true)
	var entries: Array = f["entries"].duplicate(true)
	var e0: Dictionary = entries[0].duplicate(true)
	var refs: Dictionary = e0["refs"].duplicate(true)
	var regions: Array = refs["regions"].duplicate(true)
	regions.append(BAD_REGION_ID)
	refs["regions"] = regions
	e0["refs"] = refs
	entries[0] = e0
	f["entries"] = entries
	return f


func _check_plant_refs_unresolved() -> void:
	var bad := _bad_ref_frame()
	_root.load_frame(bad)
	var clean_unresolved := int(_root.qa_state().get("unresolved_refs", -1))
	_assert(clean_unresolved > 0,
		"clean: a frame with a nonexistent region id (%d) should raise unresolved_refs above 0 (positive control), got %d" % [BAD_REGION_ID, clean_unresolved])

	_assert(_root.qa_plant("refs-unresolved"), "qa_plant(refs-unresolved) must return true")
	_root.load_frame(bad)
	var planted_unresolved := int(_root.qa_state().get("unresolved_refs", -1))
	_assert(planted_unresolved == 0,
		"PLANT refs-unresolved: unresolved_refs should read 0 with ref validation disabled, got %d" % planted_unresolved)

	_root.load_frame(_frame.duplicate(true))


func _bad_entry_frame() -> Dictionary:
	var f: Dictionary = _frame.duplicate(true)
	var entries: Array = f["entries"].duplicate(true)
	entries.append({
		"id": 299,
		"start_tick": 148,
		"end_tick": 150,
		"category": 19,
		"cluster_type": 3,
		"refs": {"regions": [BAD_REGION_ID], "factions": [BAD_FACTION_ID]},
		"fragment": 910299,
		"significance": 0.3,
	})
	f["entries"] = entries
	return f


func _check_plant_entries_dropped() -> void:
	var bad := _bad_entry_frame()
	_root.load_frame(bad)
	var clean_state: Dictionary = _root.qa_state()
	_assert(int(clean_state.get("dropped_entries", -1)) == 1,
		"clean: an entry whose every ref is nonexistent should be dropped rather than shown broken (positive control), dropped_entries = %s" % clean_state.get("dropped_entries"))
	_assert(clean_state.get("entries", []).size() == 6,
		"clean: the wholly-unresolvable 7th entry should not appear in entries[], got %d" % clean_state.get("entries", []).size())

	_assert(_root.qa_plant("entries-dropped"), "qa_plant(entries-dropped) must return true")
	_root.load_frame(bad)
	var planted_state: Dictionary = _root.qa_state()
	_assert(int(planted_state.get("dropped_entries", -1)) == 0,
		"PLANT entries-dropped: dropped_entries should read 0 with dropping disabled, got %s" % planted_state.get("dropped_entries"))
	_assert(planted_state.get("entries", []).size() == 7,
		"PLANT entries-dropped: the unresolvable entry should now appear (7 total), got %d" % planted_state.get("entries", []).size())

	_root.load_frame(_frame.duplicate(true))


func _check_plant_nope_is_false() -> void:
	_assert(not _root.qa_plant("nope"), "qa_plant('nope') must return false")
	for id in PLANTS:
		_assert(_root.qa_plant(id), "qa_plant(%s) must return true" % id)


func _distinct_region_refs(frame: Dictionary) -> Array:
	var seen := []
	for e in frame.get("entries", []):
		for rid in e.get("refs", {}).get("regions", []):
			var r := int(rid)
			if not seen.has(r):
				seen.append(r)
	return seen


func _region_owner(snapshot: Dictionary, idx: int) -> int:
	for r in snapshot.get("regions", []):
		if int(r.get("i", -999)) == idx:
			return int(r.get("owner", -1))
	return -999


func _load_snapshot() -> Dictionary:
	if FileAccess.file_exists(SNAPSHOT_FIXTURE_PATH):
		var data = _read_json(SNAPSHOT_FIXTURE_PATH)
		if data != null:
			return data
	var built := _build_minimal_snapshot()
	_write_json(SNAPSHOT_FALLBACK_PATH, built)
	return built


# Minimal valid instance of docs/northstar/spec_factory/transport/snapshot.schema.json,
# same shape as tests/test_c_bridge.gd's fallback (kept independent per-file: fenced
# tests do not share a non-fenced helper module).
func _build_minimal_snapshot() -> Dictionary:
	var regions := []
	for i in range(N_REGIONS):
		regions.append({
			"i": i,
			"owner": (i % 3) - 1,
			"tier": 1,
			"military": 10.0,
			"economy": 10.0,
			"tension": 10.0,
			"population": 10.0,
			"stability": 10.0,
			"capacity": 10.0,
		})
	var edges := []
	for i in range(N_REGIONS - 1):
		edges.append({"a": i, "b": i + 1, "t": i % 2})
	var factions := []
	for f in range(3):
		factions.append({"id": f, "archetype": 0, "budget": 100.0, "tech": 1.0, "stance": [1, 1, 1]})
	return {
		"type": "snapshot",
		"tick": 10,
		"checksum": 424242,
		"regions": regions,
		"factions": factions,
		"edges": edges,
	}


func _load_frame() -> Dictionary:
	if FileAccess.file_exists(FRAME_FIXTURE_PATH):
		var data = _read_json(FRAME_FIXTURE_PATH)
		if data != null:
			return data
	var built := _build_minimal_chronicle_frame()
	_write_json(FRAME_FALLBACK_PATH, built)
	return built


# Fallback mirrors tests/fixtures/chronicle_frame_seed11.json verbatim so a
# missing/unreadable fixture file degrades to the same 6-entry shape instead
# of a second unrelated failure mode.
func _build_minimal_chronicle_frame() -> Dictionary:
	return {
		"type": "chronicle",
		"jump": {"from_tick": 100, "to_tick": 150},
		"entries": [
			{"id": 201, "start_tick": 102, "end_tick": 109, "category": 0, "cluster_type": 0,
				"refs": {"regions": [3], "factions": [0]}, "fragment": 910201, "significance": 0.92},
			{"id": 202, "start_tick": 111, "end_tick": 116, "category": 5, "cluster_type": 1,
				"refs": {"regions": [4], "factions": [0]}, "fragment": 910202, "significance": 0.71},
			{"id": 203, "start_tick": 119, "end_tick": 131, "category": 10, "cluster_type": 2,
				"refs": {"regions": [12, 13], "factions": [1]}, "fragment": 910203, "significance": 0.83},
			{"id": 204, "start_tick": 133, "end_tick": 137, "category": 16, "cluster_type": 3,
				"refs": {"regions": [24], "factions": [2, 0]}, "fragment": 910204, "significance": 0.68},
			{"id": 205, "start_tick": 139, "end_tick": 143, "category": 16, "cluster_type": 3,
				"refs": {"regions": [25], "factions": [2, 0]}, "fragment": 910205, "significance": 0.62},
			{"id": 206, "start_tick": 145, "end_tick": 149, "category": 17, "cluster_type": 3,
				"refs": {"regions": [13], "factions": [1]}, "fragment": 910206, "significance": 0.51},
		],
	}


func _read_json(path: String):
	var f := FileAccess.open(path, FileAccess.READ)
	if f == null:
		return null
	var text := f.get_as_text()
	f.close()
	return JSON.parse_string(text)


func _write_json(path: String, data: Dictionary) -> bool:
	var f := FileAccess.open(path, FileAccess.WRITE)
	if f == null:
		return false
	f.store_string(JSON.stringify(data))
	f.close()
	return true


# --- C3-4: library resolution and server-field isolation -------------------

# Fragment id 0 (LT_O_001) with region_id=3 must resolve to named prose:
#   {region_name} -> "the Iron Vale"   (CHRON_REGION_NAMES[3 % 16])
#   {lineage_name} -> "Ashworth"       (CHRON_LINEAGE_SURNAMES[3 % 8])
# The raw slot strings must not appear in the result.
func _check_library_fragment_resolves_C3_4() -> void:
	var lib_frame := {
		"type": "chronicle",
		"jump": {"from_tick": 0, "to_tick": 50},
		"entries": [
			{"id": 1, "start_tick": 1, "end_tick": 10, "category": 2, "cluster_type": 0,
				"refs": {"regions": [3], "factions": [0]}, "fragment": 0,
				"significance": 0.9},
		],
	}
	_root.set_snapshot(_snapshot)
	_root.load_frame(lib_frame)
	var state: Dictionary = _root.qa_state()
	var entries: Array = state.get("entries", [])
	_assert(entries.size() == 1,
		"C3-4 library: expected 1 entry from lib_frame, got %d" % entries.size())
	if entries.size() > 0:
		var text: String = str(entries[0].get("text", ""))
		_assert("{region_name}" not in text,
			"C3-4: raw slot {region_name} must not appear in resolved text: %s" % text)
		_assert("the Iron Vale" in text,
			"C3-4: region_id=3 must yield 'the Iron Vale' in text (CHRON_REGION_NAMES[3 %% 16]), got: %s" % text)
		_assert("Ashworth" in text,
			"C3-4: region_id=3 must yield lineage 'Ashworth' in text (CHRON_LINEAGE_SURNAMES[3 %% 8]), got: %s" % text)
		_assert("[fragment 0]" not in text,
			"C3-4: fragment id 0 must resolve to library text, not the fallback placeholder: %s" % text)
	_root.load_frame(_frame.duplicate(true))


# A frame entry carrying server-side base_text / expanded_text must not
# affect what the panel renders; the panel resolves fragment id from the
# library and ignores all prose fields on the frame entry.
func _check_poisoned_server_text_ignored_C3_4() -> void:
	var poisoned_frame := {
		"type": "chronicle",
		"jump": {"from_tick": 0, "to_tick": 50},
		"entries": [
			{"id": 1, "start_tick": 1, "end_tick": 10, "category": 2, "cluster_type": 0,
				"refs": {"regions": [3], "factions": [0]}, "fragment": 0,
				"base_text": "POISONED_BASE", "expanded_text": "POISONED_EXPANDED",
				"significance": 0.9},
		],
	}
	_root.set_snapshot(_snapshot)
	_root.load_frame(poisoned_frame)
	var state: Dictionary = _root.qa_state()
	var entries: Array = state.get("entries", [])
	_assert(entries.size() == 1,
		"C3-4 poisoned: expected 1 entry, got %d" % entries.size())
	if entries.size() > 0:
		var text: String = str(entries[0].get("text", ""))
		_assert("POISONED_BASE" not in text,
			"C3-4: base_text='POISONED_BASE' from frame must not appear in rendered text (R-068-02: no prose from server): %s" % text)
		_assert("POISONED_EXPANDED" not in text,
			"C3-4: expanded_text='POISONED_EXPANDED' from frame must not appear in rendered text: %s" % text)
	_root.load_frame(_frame.duplicate(true))


# --- C3-6: fragment_ids array support -----------------------------------------

# Entry with fragment_ids [-1,-1,-1]: must render structural line (category,
# resolved region name, tick range). No fragment prose, no {/}/[ tokens.
func _check_fragment_ids_all_minus_one_C3_6() -> void:
	var minus_frame := {
		"type": "chronicle",
		"jump": {"from_tick": 0, "to_tick": 50},
		"entries": [
			{"id": 901, "start_tick": 50, "end_tick": 60, "category": 3, "cluster_type": 1,
				"refs": {"regions": [5], "factions": [0]},
				"fragment": -1, "fragment_ids": [-1, -1, -1], "significance": 0.5},
		],
	}
	_root.set_snapshot(_snapshot)
	_root.load_frame(minus_frame)
	var state: Dictionary = _root.qa_state()
	var entries: Array = state.get("entries", [])
	_assert(entries.size() == 1,
		"C3-6 all-minus-one: expected 1 entry, got %d" % entries.size())
	if entries.size() > 0:
		var text: String = str(entries[0].get("text", ""))
		_assert(text != "",
			"C3-6 all-minus-one: structural line must not be empty")
		_assert("{" not in text,
			"C3-6 all-minus-one: no { in structural line (unfilled placeholder): %s" % text)
		_assert("}" not in text,
			"C3-6 all-minus-one: no } in structural line (unfilled placeholder): %s" % text)
		_assert("[" not in text,
			"C3-6 all-minus-one: no [ in structural line (placeholder token): %s" % text)
	_root.load_frame(_frame.duplicate(true))


# Entry with fragment_ids [0,-1,-1] and region_id=3: must resolve prose from
# library id 0 with names filled; qa_state entry must carry fragment_ids[3].
func _check_fragment_ids_real_C3_6() -> void:
	var fids_frame := {
		"type": "chronicle",
		"jump": {"from_tick": 0, "to_tick": 50},
		"entries": [
			{"id": 902, "start_tick": 1, "end_tick": 10, "category": 2, "cluster_type": 0,
				"refs": {"regions": [3], "factions": [0]},
				"fragment": 0, "fragment_ids": [0, -1, -1], "significance": 0.9},
		],
	}
	_root.set_snapshot(_snapshot)
	_root.load_frame(fids_frame)
	var state: Dictionary = _root.qa_state()
	var entries: Array = state.get("entries", [])
	_assert(entries.size() == 1,
		"C3-6 fragment_ids real: expected 1 entry, got %d" % entries.size())
	if entries.size() > 0:
		var fids = entries[0].get("fragment_ids", null)
		_assert(fids != null and fids is Array and (fids as Array).size() == 3,
			"C3-6: qa_state entry must carry fragment_ids Array[3], got %s" % str(fids))
		var text: String = str(entries[0].get("text", ""))
		_assert("the Iron Vale" in text,
			"C3-6: fragment_ids[0]=0 region_id=3 must yield 'the Iron Vale' in text, got: %s" % text)
		_assert("{region_name}" not in text,
			"C3-6: raw slot {region_name} must not appear in resolved text: %s" % text)
	_root.load_frame(_frame.duplicate(true))
