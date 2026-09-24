extends SceneTree

# Piece C4 (docs/northstar/plans/briefs/2026-09-22-two-day-push.md wave-2 row
# C4; docs/northstar/plans/push/pieces.toml id C4, owns_glob
# scenes/mission_briefing/**+scenes/debrief/**, depends_on B9/T1):
# res://scenes/mission_briefing/mission_briefing.tscn and
# res://scenes/debrief/debrief.tscn each gain a rebind entry point,
# load_frame(frame: Dictionary), that consumes a C transport v1 mission/
# debrief frame (docs/architecture.md "chronicle frame, mission frame,
# debrief frame") instead of the legacy UIDataBus.get_mission_briefing()/
# setup({"debrief":...}) name-and-prose dicts these scenes use today. The
# frame carries no names (C5 rule): an objective's "node" is a tactical map
# index, and its on-screen marker name must come from a client-side layout
# table, never be echoed straight from the frame. Full contract documented
# at docs/northstar/proving_ground/evidence/push_2026-09-22/
# c3_c4_tests_note.md. Bible: docs/bible/epics/E-10-missions.md
# R-079-01..04, R-077-01/02, R-076 (deadline, as referenced by R-079).

const BRIEFING_SCENE_PATH := "res://scenes/mission_briefing/mission_briefing.tscn"
const DEBRIEF_SCENE_PATH := "res://scenes/debrief/debrief.tscn"
const MISSION_FIXTURE_PATH := "res://tests/fixtures/mission_frame_seed11.json"
const DEBRIEF_FIXTURE_PATH := "res://tests/fixtures/debrief_frame_seed11.json"
const MISSION_FALLBACK_PATH := "user://test_briefing_debrief_fallback_mission.json"
const DEBRIEF_FALLBACK_PATH := "user://test_briefing_debrief_fallback_debrief.json"

const BRIEFING_PLANTS := ["marker-from-frame"]
const DEBRIEF_PLANTS := ["band-off-by-one"]

# R-077-02's five-band spectrum, worst to best, by the debrief frame's int
# "band" (docs/architecture.md's example uses band:2). This is the contract
# C4 must implement the int->string mapping against, not a guess by the test.
const BAND_NAMES := ["total_failure", "partial_failure", "partial_success", "strong_success", "total_success"]

var _pass_count := 0
var _fail_count := 0
var _fail_msgs: Array[String] = []
var _mission: Dictionary
var _debrief: Dictionary
var _live_tests_completed := false


func _initialize() -> void:
	await _run_tests()
	print("\n=== Briefing/Debrief Test Results ===")
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
	_mission = _load_mission()
	_assert(not _mission.is_empty(), "could not obtain a mission frame (fixture missing and fallback write failed)")
	_debrief = _load_debrief()
	_assert(not _debrief.is_empty(), "could not obtain a debrief frame (fixture missing and fallback write failed)")

	await _run_briefing_tests()
	await _run_debrief_tests()
	await _run_live_tests()
	_assert(_live_tests_completed, "the live-frame checks did not run to the end (a script error aborted them, or c_bridge.gd lacks load_mission_live / load_debrief_live / mission_frame / debrief_frame / DEFAULT_FEATURES)")


func _run_briefing_tests() -> void:
	var packed = load(BRIEFING_SCENE_PATH)
	_assert(packed != null, "cannot load %s" % BRIEFING_SCENE_PATH)
	if packed == null or not (packed is PackedScene):
		return

	var root: Node = (packed as PackedScene).instantiate()
	_assert(root != null, "%s failed to instantiate" % BRIEFING_SCENE_PATH)
	if root == null:
		return
	get_root().add_child(root)
	await process_frame
	await process_frame

	for m in ["load_frame", "qa_state", "qa_plant"]:
		_assert(root.has_method(m), "mission_briefing root missing method (piece C4 not attached yet): " + m)
	if not (root.has_method("load_frame") and root.has_method("qa_state") and root.has_method("qa_plant")):
		root.queue_free()
		return

	root.load_frame(_mission.duplicate(true))
	await process_frame

	_check_briefing_json_safe(root)
	_check_archetype_and_deadline_R076_R079(root)
	_check_objective_count_R079(root)
	_check_marker_name_from_table_not_frame(root)
	_check_plant_marker_from_frame(root)
	_check_plant_nope_is_false(root, BRIEFING_PLANTS, "briefing")

	root.queue_free()
	await process_frame


func _run_debrief_tests() -> void:
	var packed = load(DEBRIEF_SCENE_PATH)
	_assert(packed != null, "cannot load %s" % DEBRIEF_SCENE_PATH)
	if packed == null or not (packed is PackedScene):
		return

	var root: Node = (packed as PackedScene).instantiate()
	_assert(root != null, "%s failed to instantiate" % DEBRIEF_SCENE_PATH)
	if root == null:
		return
	get_root().add_child(root)
	await process_frame
	await process_frame

	for m in ["load_frame", "qa_state", "qa_plant"]:
		_assert(root.has_method(m), "debrief root missing method (piece C4 not attached yet): " + m)
	if not (root.has_method("load_frame") and root.has_method("qa_state") and root.has_method("qa_plant")):
		root.queue_free()
		return

	root.load_frame(_debrief.duplicate(true))
	await process_frame

	_check_debrief_json_safe(root)
	_check_band_R077(root)
	_check_percentages(root)
	_check_region_delta_four_numbers(root)
	_check_plant_band_off_by_one(root)
	_check_plant_nope_is_false(root, DEBRIEF_PLANTS, "debrief")

	root.queue_free()
	await process_frame


# Piece C4-3 (docs/architecture.md "session commands (v1.1)"): with no
# setup() params the briefing and debrief scenes read the frame the live pipe
# answers to mission_start / mission_end (c_bridge.gd load_mission_live /
# load_debrief_live), not tests/fixtures/*_frame_seed11.json. The fixtures
# carry 3 objectives (archetype 2) and band 2; the live seed-1 world answers
# a different mission and a different band, so a scene that still shows the
# fixture cannot pass.
func _run_live_tests() -> void:
	var CBridge = load("res://autoload/c_bridge.gd")
	var bridge = CBridge.new()
	for m in ["load_mission_live", "load_debrief_live", "mission_frame", "debrief_frame", "last_error"]:
		_assert(bridge.has_method(m), "c_bridge.gd missing method (piece C4-3 not attached yet): " + m)
		if not bridge.has_method(m):
			return
	_assert(CBridge.get_script_constant_map().has("DEFAULT_FEATURES"), "c_bridge.gd missing constant DEFAULT_FEATURES")
	if not CBridge.get_script_constant_map().has("DEFAULT_FEATURES"):
		return
	var live_ok: bool = bridge.load_mission_live(1, CBridge.DEFAULT_N_REGIONS, CBridge.DEFAULT_FEATURES)
	_assert(live_ok, "load_mission_live(1, %d, DEFAULT_FEATURES) returned false (last_error = %s)" % [CBridge.DEFAULT_N_REGIONS, bridge.last_error()])
	var live_mission: Dictionary = bridge.mission_frame()
	_assert(live_mission.get("type", "") == "mission", "live mission frame type = %s, expected mission" % live_mission.get("type", ""))
	_assert((live_mission.get("objectives", []) as Array).size() >= 1, "live mission frame has no objectives")

	var again = CBridge.new()
	again.load_mission_live(1, CBridge.DEFAULT_N_REGIONS, CBridge.DEFAULT_FEATURES)
	_assert(again.mission_frame() == live_mission, "same seed answered two different mission frames (determinism)")

	var bad = CBridge.new()
	var bad_ok: bool = bad.load_mission_live(1, 30, CBridge.DEFAULT_FEATURES)
	_assert(not bad_ok, "load_mission_live at 30 regions (below the feasibility floor) returned true")
	_assert(bad.last_error() != "", "a failed live mission load left last_error empty (silent failure)")
	_assert(bad.mission_frame().is_empty(), "a failed live mission load still exposed a mission frame")

	var live_debrief_ok: bool = bridge.load_debrief_live(1, CBridge.DEFAULT_N_REGIONS, CBridge.DEFAULT_FEATURES)
	_assert(live_debrief_ok, "load_debrief_live returned false (last_error = %s)" % bridge.last_error())
	var live_debrief: Dictionary = bridge.debrief_frame()
	_assert(live_debrief.get("type", "") == "debrief", "live debrief frame type = %s, expected debrief" % live_debrief.get("type", ""))

	_assert(int(live_mission.get("archetype", -1)) != int(_mission.get("archetype")) or (live_mission.get("objectives", []) as Array).size() != (_mission.get("objectives", []) as Array).size(),
		"live mission frame equals the fixture; the live check below cannot tell them apart (fixture control)")
	_assert(int(live_debrief.get("band", -1)) != int(_debrief.get("band")),
		"live debrief band equals the fixture band; the live check below cannot tell them apart (fixture control)")

	var briefing: Node = (load(BRIEFING_SCENE_PATH) as PackedScene).instantiate()
	get_root().add_child(briefing)
	await process_frame
	await process_frame
	if briefing.has_method("qa_state"):
		var b: Dictionary = briefing.qa_state()
		_assert(int(b.get("archetype", -1)) == int(live_mission.get("archetype", -2)),
			"briefing with no setup() shows archetype %s, live frame says %s" % [b.get("archetype"), live_mission.get("archetype")])
		_assert(int(b.get("deadline_ticks", -1)) == int(live_mission.get("deadline_ticks", -2)),
			"briefing with no setup() shows deadline_ticks %s, live frame says %s" % [b.get("deadline_ticks"), live_mission.get("deadline_ticks")])
		_assert((b.get("objectives", []) as Array).size() == (live_mission.get("objectives", []) as Array).size(),
			"briefing with no setup() shows %d objectives, live frame has %d" % [(b.get("objectives", []) as Array).size(), (live_mission.get("objectives", []) as Array).size()])
	else:
		_assert(false, "mission_briefing root has no qa_state()")
	briefing.queue_free()
	await process_frame

	var debrief: Node = (load(DEBRIEF_SCENE_PATH) as PackedScene).instantiate()
	get_root().add_child(debrief)
	await process_frame
	await process_frame
	if debrief.has_method("qa_state"):
		var d: Dictionary = debrief.qa_state()
		var expected_band: String = BAND_NAMES[int(live_debrief.get("band", 0))]
		_assert(str(d.get("band", "")) == expected_band,
			"debrief with no setup() shows band %s, live frame says %s" % [d.get("band"), expected_band])
		_assert(is_equal_approx(float(d.get("brought_home_pct", -1.0)), float(live_debrief.get("brought_home", 0.0)) * 100.0),
			"debrief with no setup() shows brought_home_pct %s, live frame says %s" % [d.get("brought_home_pct"), float(live_debrief.get("brought_home", 0.0)) * 100.0])
	else:
		_assert(false, "debrief root has no qa_state()")
	debrief.queue_free()
	await process_frame
	_live_tests_completed = true


func _check_briefing_json_safe(root: Node) -> void:
	var text := JSON.stringify(root.qa_state())
	_assert(text != "", "briefing qa_state() did not survive JSON.stringify")


# R-076 (the clock) as referenced by R-079 (the briefing shows it): qa_state()
# carries the raw deadline in ticks as data (qa_state() is canonical from
# data, never from HUD labels); the on-screen wording is a separate,
# unfenced concern.
func _check_archetype_and_deadline_R076_R079(root: Node) -> void:
	var state: Dictionary = root.qa_state()
	_assert(int(state.get("archetype", -1)) == int(_mission.get("archetype")),
		"archetype = %s, expected %s (from the frame, not invented)" % [state.get("archetype"), _mission.get("archetype")])
	_assert(int(state.get("deadline_ticks", -1)) == int(_mission.get("deadline_ticks")),
		"R-076/R-079: deadline_ticks = %s, expected %s" % [state.get("deadline_ticks"), _mission.get("deadline_ticks")])


# R-079-01..04: exactly one primary and (here) two secondary objectives; the
# exactly-one-primary shape itself is E-10 S-075's R-075-01, cross-referenced
# here because R-079's briefing renders whatever S-075 built.
func _check_objective_count_R079(root: Node) -> void:
	var state: Dictionary = root.qa_state()
	var objectives: Array = state.get("objectives", [])
	_assert(objectives.size() == 3,
		"R-079-01..04: objectives has %d entries, expected 3 (1 primary + 2 secondary)" % objectives.size())
	var primary_count := 0
	for o in objectives:
		if bool(o.get("primary", false)):
			primary_count += 1
	_assert(primary_count == 1,
		"R-075-01/R-079: exactly one objective must be primary, found %d" % primary_count)


func _primary_objective(state: Dictionary) -> Dictionary:
	for o in state.get("objectives", []):
		if bool(o.get("primary", false)):
			return o
	return {}


func _mutated_mission_frame(mission: Dictionary) -> Dictionary:
	var m: Dictionary = mission.duplicate(true)
	m["archetype"] = int(mission.get("archetype", 0)) + 1
	m["region"] = int(mission.get("region", 0)) + 1
	m["deadline_ticks"] = int(mission.get("deadline_ticks", 0)) + 50
	return m


# "the primary objective's marker name comes from the client layout table
# (not the frame)": load two frames that share the primary objective's node
# id but differ in every other field; the marker name must not move (a
# table lookup keyed on node alone), and it must not just be the raw node
# number restated (the naive, wrong implementation this rebind must avoid).
func _check_marker_name_from_table_not_frame(root: Node) -> void:
	var node := int(_mission["objectives"][0]["node"])

	root.load_frame(_mission.duplicate(true))
	var primary1 := _primary_objective(root.qa_state())
	var name1 := str(primary1.get("marker_name", ""))
	_assert(name1 != "", "primary objective has no marker_name")
	_assert(name1 != str(node) and name1 != ("Node %d" % node),
		"clean: marker_name should not just restate the frame's raw node id %d (positive control), got %s" % [node, name1])

	root.load_frame(_mutated_mission_frame(_mission))
	var primary2 := _primary_objective(root.qa_state())
	var name2 := str(primary2.get("marker_name", ""))
	_assert(name1 == name2,
		"marker_name for node %d changed from %s to %s when only region/archetype/deadline changed; it must be a function of the node id alone (client layout table), not the surrounding frame" % [node, name1, name2])

	root.load_frame(_mission.duplicate(true))


# PLANT marker-from-frame (fault site this piece must expose): when active,
# the primary objective's marker_name becomes the literal "Node %d" % node
# instead of the table lookup — the exact regression the check above guards
# against.
func _check_plant_marker_from_frame(root: Node) -> void:
	var node := int(_mission["objectives"][0]["node"])
	_assert(root.qa_plant("marker-from-frame"), "qa_plant(marker-from-frame) must return true")
	root.load_frame(_mission.duplicate(true))
	var primary := _primary_objective(root.qa_state())
	var name := str(primary.get("marker_name", ""))
	_assert(name == ("Node %d" % node),
		"PLANT marker-from-frame: marker_name should read 'Node %d', got %s" % [node, name])
	root.load_frame(_mission.duplicate(true))


func _check_debrief_json_safe(root: Node) -> void:
	var text := JSON.stringify(root.qa_state())
	_assert(text != "", "debrief qa_state() did not survive JSON.stringify")


# R-077-01/02: the frame already carries the sim-resolved band int (the
# threshold math is B9/csrc/mission.c's job, proven by tests/csim); C4's job
# is only the int->display-string mapping, checked here against BAND_NAMES.
func _check_band_R077(root: Node) -> void:
	var state: Dictionary = root.qa_state()
	var expected: String = BAND_NAMES[int(_debrief.get("band"))]
	_assert(str(state.get("band", "")) == expected,
		"R-077-01/02: band = %s, expected %s (band int %s)" % [state.get("band"), expected, _debrief.get("band")])


func _check_percentages(root: Node) -> void:
	var state: Dictionary = root.qa_state()
	var expected_achieved := float(_debrief.get("achieved")) * 100.0
	var expected_brought_home := float(_debrief.get("brought_home")) * 100.0
	_assert(is_equal_approx(float(state.get("achieved_pct", -1.0)), expected_achieved),
		"achieved_pct = %s, expected %s (achieved %s shown as a percentage)" % [state.get("achieved_pct"), expected_achieved, _debrief.get("achieved")])
	_assert(is_equal_approx(float(state.get("brought_home_pct", -1.0)), expected_brought_home),
		"brought_home_pct = %s, expected %s (brought_home %s shown as a percentage)" % [state.get("brought_home_pct"), expected_brought_home, _debrief.get("brought_home")])


func _check_region_delta_four_numbers(root: Node) -> void:
	var state: Dictionary = root.qa_state()
	var delta: Dictionary = state.get("region_delta", {})
	var expected: Dictionary = _debrief.get("region_delta", {})
	_assert(delta.size() == 4,
		"region_delta has %d keys, expected exactly 4 (military, economy, tension, population)" % delta.size())
	var mismatches := 0
	for k in ["military", "economy", "tension", "population"]:
		if not delta.has(k) or not is_equal_approx(float(delta.get(k, 999.0)), float(expected.get(k, -999.0))):
			mismatches += 1
	_assert(mismatches == 0,
		"%d of region_delta's 4 fields do not match the frame's region_delta" % mismatches)


# PLANT band-off-by-one (fault site this piece must expose): when active,
# the int->string mapping shifts by one index (clamped to the last band),
# so band 2 (partial_success) reads as band 3 (strong_success).
func _check_plant_band_off_by_one(root: Node) -> void:
	var clean_expected: String = BAND_NAMES[int(_debrief.get("band"))]
	var clean_state: Dictionary = root.qa_state()
	_assert(str(clean_state.get("band", "")) == clean_expected,
		"clean: band should read %s before the plant (positive control), got %s" % [clean_expected, clean_state.get("band")])

	_assert(root.qa_plant("band-off-by-one"), "qa_plant(band-off-by-one) must return true")
	root.load_frame(_debrief.duplicate(true))
	var shifted_index: int = mini(int(_debrief.get("band")) + 1, BAND_NAMES.size() - 1)
	var planted_expected: String = BAND_NAMES[shifted_index]
	var planted_state: Dictionary = root.qa_state()
	_assert(str(planted_state.get("band", "")) == planted_expected,
		"PLANT band-off-by-one: band should read %s (shifted one band worse->better), got %s" % [planted_expected, planted_state.get("band")])

	root.load_frame(_debrief.duplicate(true))


func _check_plant_nope_is_false(root: Node, plants: Array, label: String) -> void:
	_assert(not root.qa_plant("nope"), "%s: qa_plant('nope') must return false" % label)
	for id in plants:
		_assert(root.qa_plant(id), "%s: qa_plant(%s) must return true" % [label, id])


func _load_mission() -> Dictionary:
	if FileAccess.file_exists(MISSION_FIXTURE_PATH):
		var data = _read_json(MISSION_FIXTURE_PATH)
		if data != null:
			return data
	var built := _build_minimal_mission()
	_write_json(MISSION_FALLBACK_PATH, built)
	return built


# Fallback mirrors tests/fixtures/mission_frame_seed11.json verbatim.
func _build_minimal_mission() -> Dictionary:
	return {
		"type": "mission",
		"archetype": 2,
		"region": 7,
		"deadline_ticks": 380,
		"objectives": [
			{"i": 0, "kind": 1, "node": 3, "primary": true, "radius": 300.0, "progress": 0.0},
			{"i": 1, "kind": 2, "node": 7, "primary": false, "radius": 150.0, "progress": 0.0},
			{"i": 2, "kind": 0, "node": 12, "primary": false, "radius": 220.0, "progress": 0.0},
		],
		"force": {"types": [2, 2, 1, 0, 0, 0], "tiers": [2, 2, 1, 0, 0, 0]},
	}


func _load_debrief() -> Dictionary:
	if FileAccess.file_exists(DEBRIEF_FIXTURE_PATH):
		var data = _read_json(DEBRIEF_FIXTURE_PATH)
		if data != null:
			return data
	var built := _build_minimal_debrief()
	_write_json(DEBRIEF_FALLBACK_PATH, built)
	return built


# Fallback mirrors tests/fixtures/debrief_frame_seed11.json verbatim.
func _build_minimal_debrief() -> Dictionary:
	return {
		"type": "debrief",
		"band": 2,
		"achieved": 0.8,
		"brought_home": 0.6,
		"region_delta": {"military": -4.0, "economy": 2.0, "tension": -3.0, "population": 0.0},
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
