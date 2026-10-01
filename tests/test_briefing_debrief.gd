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
const DEBRIEF_NONZERO_DELTA_PATH := "res://tests/fixtures/debrief_frame_nonzero_delta.json"
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
	await _run_live_debrief_tests()
	await _run_region_delta_text_tests()
	_check_debrief_no_simbridge_reference()
	await _run_debrief_on_continue_pin()


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

	# Earlier scene tests ran mission_start/mission_end on the shared session;
	# the live frames above come from fresh private bridges, so start clean.
	load("res://autoload/sim_session.gd").reset()
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

	# Piece C4-4 (docs/architecture.md "session commands (v1.1)", E-12 S-092):
	# a started mission is in recon (clock not started) until the player
	# presses Begin, the briefing's DEPLOY FORCES button (control name
	# Deploy), which sends mission_begin over the shared session and answers
	# the first tactical frame. begin_mission_live is idempotent; the
	# scene's begin_mission() reports whether the mission is begun.
	for m in ["begin_mission_live", "mission_begun"]:
		_assert(bridge.has_method(m), "c_bridge.gd missing method (piece C4-4 not attached yet): " + m)
		if not bridge.has_method(m):
			return
	var recon = CBridge.new()
	_assert(recon.load_mission_live(1, CBridge.DEFAULT_N_REGIONS, CBridge.DEFAULT_FEATURES), "load_mission_live failed for the recon check: %s" % recon.last_error())
	_assert(not recon.mission_begun(), "a freshly started mission is already begun (it must be in recon until Begin)")
	_assert(recon.begin_mission_live(1, CBridge.DEFAULT_N_REGIONS, CBridge.DEFAULT_FEATURES), "begin_mission_live failed: %s" % recon.last_error())
	_assert(recon.mission_begun(), "mission_begun() is false after begin_mission_live")
	_assert(recon.tactical_frame().get("type", "") == "tactical", "begin_mission_live did not keep the tactical frame it was answered with")
	_assert(recon.begin_mission_live(1, CBridge.DEFAULT_N_REGIONS, CBridge.DEFAULT_FEATURES), "a second begin_mission_live was not idempotent: %s" % recon.last_error())
	recon.close_session()

	var SimSession = load("res://autoload/sim_session.gd")
	SimSession.reset()
	var scene: Node = (load(BRIEFING_SCENE_PATH) as PackedScene).instantiate()
	get_root().add_child(scene)
	await process_frame
	await process_frame
	_assert(scene.has_method("begin_mission"), "mission_briefing root has no begin_mission()")
	if scene.has_method("begin_mission"):
		var shared = SimSession.bridge()
		_assert(shared.mission_active() and not shared.mission_begun(), "the briefing scene should leave the mission in recon before Begin")
		_assert(scene.begin_mission(), "begin_mission() returned false (last_error = %s)" % shared.last_error())
		_assert(shared.mission_begun(), "the shared mission is not begun after the briefing's begin_mission()")
		_assert(shared.tactical_frame().get("type", "") == "tactical", "no tactical frame after the briefing's begin_mission()")
	var deploy = _find_named(scene, "Deploy")
	_assert(deploy != null, "positive control: no control named Deploy in the briefing (the flow spine clicks it)")
	scene.queue_free()
	await process_frame
	SimSession.reset()
	_live_tests_completed = true


func _find_named(node: Node, node_name: String):
	if node.name == node_name:
		return node
	for c in node.get_children():
		var found = _find_named(c, node_name)
		if found != null:
			return found
	return null


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


# Piece C4-8 (R-077-02): region_delta_text in qa_state() carries all four
# rendered strings (+3, -2.5, "no change" for zero). Two frames tested:
# nonzero fixture (all four have values with sign) and an all-zero frame
# (all four render "no change", never blank, never "+0").
func _run_region_delta_text_tests() -> void:
	var packed = load(DEBRIEF_SCENE_PATH)
	if packed == null or not (packed is PackedScene):
		_assert(false, "C4-8: cannot load debrief scene")
		return

	# --- nonzero fixture ---
	var nonzero: Dictionary = {}
	if FileAccess.file_exists(DEBRIEF_NONZERO_DELTA_PATH):
		nonzero = _read_json(DEBRIEF_NONZERO_DELTA_PATH)
	if nonzero.is_empty():
		nonzero = {
			"type": "debrief", "band": 3, "achieved": 0.75, "brought_home": 0.5,
			"region_delta": {"military": 3.0, "economy": -2.5, "tension": 1.0, "population": -4.0},
		}
	var r1: Node = (packed as PackedScene).instantiate()
	get_root().add_child(r1)
	await process_frame
	await process_frame
	r1.load_frame(nonzero.duplicate(true))
	await process_frame
	_check_region_delta_text_nonzero(r1, nonzero.get("region_delta", {}))
	r1.queue_free()
	await process_frame

	# --- all-zero frame ---
	var zero_frame: Dictionary = {
		"type": "debrief", "band": 2, "achieved": 0.5, "brought_home": 0.5,
		"region_delta": {"military": 0.0, "economy": 0.0, "tension": 0.0, "population": 0.0},
	}
	var r2: Node = (packed as PackedScene).instantiate()
	get_root().add_child(r2)
	await process_frame
	await process_frame
	r2.load_frame(zero_frame)
	await process_frame
	_check_region_delta_text_zero(r2)
	r2.queue_free()
	await process_frame


func _check_region_delta_text_nonzero(root: Node, expected_delta: Dictionary) -> void:
	var state: Dictionary = root.qa_state()
	var rdt: Dictionary = state.get("region_delta_text", {})
	_assert(rdt.size() == 4,
		"C4-8 region_delta_text nonzero: expected 4 keys, got %d" % rdt.size())
	# military: 3.0 -> "+3"
	_assert(str(rdt.get("military", "")) == "+3",
		"C4-8 region_delta_text nonzero: military = '%s', expected '+3'" % str(rdt.get("military", "")))
	# economy: -2.5 -> "-2.5"
	_assert(str(rdt.get("economy", "")) == "-2.5",
		"C4-8 region_delta_text nonzero: economy = '%s', expected '-2.5'" % str(rdt.get("economy", "")))
	# tension: 1.0 -> "+1"
	_assert(str(rdt.get("tension", "")) == "+1",
		"C4-8 region_delta_text nonzero: tension = '%s', expected '+1'" % str(rdt.get("tension", "")))
	# population: -4.0 -> "-4"
	_assert(str(rdt.get("population", "")) == "-4",
		"C4-8 region_delta_text nonzero: population = '%s', expected '-4'" % str(rdt.get("population", "")))


func _check_region_delta_text_zero(root: Node) -> void:
	var state: Dictionary = root.qa_state()
	var rdt: Dictionary = state.get("region_delta_text", {})
	_assert(rdt.size() == 4,
		"C4-8 region_delta_text zero: expected 4 keys, got %d" % rdt.size())
	for k in ["military", "economy", "tension", "population"]:
		_assert(str(rdt.get(k, "")) == "no change",
			"C4-8 region_delta_text zero: %s = '%s', expected 'no change'" % [k, str(rdt.get(k, ""))])


# Piece C6-1 (S-077 R-077-01/02): live debrief frame band, achieved,
# brought_home, and region_delta.military shown by the scene equal the
# pipe's answer; once load_frame() sets _frame, the _params["debrief"]
# legacy path is not consulted (debrief.gd _debrief() priority order).
func _run_live_debrief_tests() -> void:
	var CBridge = load("res://autoload/c_bridge.gd")
	var probe = CBridge.new()
	if not probe.load_debrief_live(1, CBridge.DEFAULT_N_REGIONS, CBridge.DEFAULT_FEATURES):
		_assert(false, "C6-1 probe: load_debrief_live(1) failed -- %s" % probe.last_error())
		probe.close_session()
		return
	var live: Dictionary = probe.debrief_frame()
	probe.close_session()

	# no-setup path: achieved_pct and region_delta.military match live frame.
	var SimSession = load("res://autoload/sim_session.gd")
	SimSession.reset()
	var d1: Node = (load(DEBRIEF_SCENE_PATH) as PackedScene).instantiate()
	get_root().add_child(d1)
	await process_frame
	await process_frame
	if d1.has_method("qa_state"):
		var s1: Dictionary = d1.qa_state()
		_assert(is_equal_approx(float(s1.get("achieved_pct", -1.0)), float(live.get("achieved", 0.0)) * 100.0),
			"C6-1 no-setup achieved_pct = %s, live frame has %s" % [s1.get("achieved_pct"), float(live.get("achieved", 0.0)) * 100.0])
		var s1_delta: Dictionary = s1.get("region_delta", {})
		var live_delta: Dictionary = live.get("region_delta", {})
		_assert(is_equal_approx(float(s1_delta.get("military", -999.0)), float(live_delta.get("military", -998.0))),
			"C6-1 no-setup region_delta.military = %s, live frame has %s" % [s1_delta.get("military"), live_delta.get("military")])
	else:
		_assert(false, "C6-1 no-setup: debrief missing qa_state()")
	d1.queue_free()
	await process_frame
	SimSession.reset()

	# live frame wins over _params["debrief"] once load_frame() is called.
	# alt fixture carries conspicuously wrong values so any contamination is obvious.
	var alt := {
		"type": "debrief", "band": 4, "achieved": 0.11, "brought_home": 0.22,
		"region_delta": {"military": 99.0, "economy": 99.0, "tension": 99.0, "population": 99.0},
	}
	SimSession.reset()
	var d2: Node = (load(DEBRIEF_SCENE_PATH) as PackedScene).instantiate()
	get_root().add_child(d2)
	await process_frame
	await process_frame
	if not (d2.has_method("setup") and d2.has_method("load_frame") and d2.has_method("qa_state")):
		_assert(false, "C6-1 legacy-wins: debrief missing setup/load_frame/qa_state")
		d2.queue_free()
		return
	d2.setup({"debrief": alt})
	await process_frame
	d2.load_frame(live.duplicate(true))
	await process_frame
	var s2: Dictionary = d2.qa_state()
	var expected_band: String = BAND_NAMES[clampi(int(live.get("band", 0)), 0, BAND_NAMES.size() - 1)]
	_assert(str(s2.get("band", "")) == expected_band,
		"C6-1 S-077/R-077-02: live frame wins over _params[debrief] -- band=%s expected %s" % [s2.get("band"), expected_band])
	_assert(is_equal_approx(float(s2.get("achieved_pct", -1.0)), float(live.get("achieved", 0.0)) * 100.0),
		"C6-1: live frame wins -- achieved_pct=%s expected %s" % [s2.get("achieved_pct"), float(live.get("achieved", 0.0)) * 100.0])
	_assert(is_equal_approx(float(s2.get("brought_home_pct", -1.0)), float(live.get("brought_home", 0.0)) * 100.0),
		"C6-1: live frame wins -- brought_home_pct=%s expected %s" % [s2.get("brought_home_pct"), float(live.get("brought_home", 0.0)) * 100.0])
	var live_delta2: Dictionary = live.get("region_delta", {})
	var s2_delta: Dictionary = s2.get("region_delta", {})
	_assert(is_equal_approx(float(s2_delta.get("military", -999.0)), float(live_delta2.get("military", -998.0))),
		"C6-1: live frame wins -- region_delta.military=%s expected %s" % [s2_delta.get("military"), live_delta2.get("military")])
	d2.queue_free()
	await process_frame
	SimSession.reset()


# Piece C4-9 (docs/northstar/plans/2026-09-28-gap-fix-and-migration-plan.md
# G1): scenes/debrief/debrief.gd's _on_continue() drops its dead
# "if SimBridge.USE_LIVE_SIM: SimBridge.send_command({...continue_from_debrief...})"
# block (SimBridge is being retired, see G1). Source-grep guard mirrors the
# established pattern (tests/test_b2_briefing_scene.gd's router_script_src
# find() checks): once G1 lands, the script's raw source must not mention
# SimBridge anywhere.
func _check_debrief_no_simbridge_reference() -> void:
	var f := FileAccess.open("res://scenes/debrief/debrief.gd", FileAccess.READ)
	var src := ""
	if f != null:
		src = f.get_as_text()
		f.close()
	_assert(src != "", "C4-9: could not read scenes/debrief/debrief.gd source")
	_assert(src.find("SimBridge") < 0,
		"C4-9 (G1): scenes/debrief/debrief.gd still references SimBridge; _on_continue() must drop the dead continue_from_debrief send")


# Piece C4-9 pin: _on_continue()'s three surviving effects --
# UIDataBus.trigger_autosave("post_debrief"), debrief_completed.emit(), and
# SceneRouter.go_to("chronicle") -- must fire in the same order before and
# after the SimBridge block is dropped. autoload/ui_data_bus.gd's
# trigger_autosave() has no signal or log seam to observe directly (it either
# sends over SimBridge in live mode or just prints in mock mode), so this pin
# asserts what is safely observable: the call does not error, debrief_completed
# fires, and SceneRouter's routing target reaches "chronicle" (go_to() sets
# _current_scene_name synchronously before its fade tween runs, see
# autoload/scene_router.gd go_to()). This must pass unchanged both before and
# after the G1 edit -- it is a pin on unrelated behavior, not a red check.
func _run_debrief_on_continue_pin() -> void:
	var packed = load(DEBRIEF_SCENE_PATH)
	if packed == null or not (packed is PackedScene):
		_assert(false, "C4-9 pin: cannot load debrief scene")
		return
	var root: Node = (packed as PackedScene).instantiate()
	get_root().add_child(root)
	await process_frame
	await process_frame
	if not root.has_method("_on_continue"):
		_assert(false, "C4-9 pin: debrief root has no _on_continue()")
		root.queue_free()
		return

	var completed := [false]
	root.debrief_completed.connect(func(): completed[0] = true)

	root._on_continue()
	await process_frame

	var scene_router := get_root().get_node("SceneRouter")
	_assert(completed[0] == true, "C4-9 pin: _on_continue() must still emit debrief_completed")
	_assert(str(scene_router.get("_current_scene_name")) == "chronicle",
		"C4-9 pin: _on_continue() must still route to chronicle, SceneRouter._current_scene_name = %s" % str(scene_router.get("_current_scene_name")))

	root.queue_free()
	await process_frame
