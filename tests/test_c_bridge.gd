extends SceneTree

# Piece T1/C2 (docs/northstar/plans/briefs/2026-09-22-manager-M3.md item 2/3):
# res://autoload/c_bridge.gd parses a C transport v1 snapshot message
# (docs/architecture.md "C transport v1") into regions()/owner_of()/checksum()/
# edges(), the shape tests/transport/test_pipe_shapes.py also checks against
# docs/northstar/spec_factory/transport/snapshot.schema.json. Loaded as a
# plain script and instantiated directly, not through the project autoload.

const BRIDGE_SCRIPT_PATH := "res://autoload/c_bridge.gd"
const FIXTURE_PATH := "res://tests/transport/fixtures/snapshot_seed1_tick10.json"
const FALLBACK_PATH := "user://test_c_bridge_fallback_snapshot.json"
const BAD_PATH := "user://test_c_bridge_bad_snapshot.json"
const FALLBACK_N_REGIONS := 60

var _pass_count := 0
var _fail_count := 0
var _fail_msgs: Array[String] = []


func _initialize() -> void:
	_run_tests()
	print("\n=== C Bridge Test Results ===")
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
	var script = load(BRIDGE_SCRIPT_PATH)
	_assert(script != null, "c_bridge script failed to load (missing or parse error): " + BRIDGE_SCRIPT_PATH)
	if script == null:
		return
	_assert(script is GDScript, "c_bridge resource is not a GDScript: " + BRIDGE_SCRIPT_PATH)
	if not (script is GDScript):
		return

	var bridge = (script as GDScript).new()
	_assert(bridge != null, "c_bridge failed to instantiate")
	if bridge == null:
		return

	for m in ["load_snapshot_file", "regions", "owner_of", "checksum", "edges"]:
		_assert(bridge.has_method(m), "c_bridge missing method: " + m)
	if not (bridge.has_method("load_snapshot_file") and bridge.has_method("regions")
			and bridge.has_method("owner_of") and bridge.has_method("checksum")
			and bridge.has_method("edges")):
		return

	var expected = _fixture_snapshot()
	_assert(expected != null, "could not obtain a snapshot (fixture missing and fallback write failed)")
	if expected == null:
		return

	var ok = bridge.load_snapshot_file(expected.path)
	_assert(bool(ok), "load_snapshot_file(%s) did not report success" % expected.path)

	var expected_n: int = expected.data.get("regions", []).size()
	var regions: Array = bridge.regions()
	_assert(regions.size() == expected_n,
		"regions().size() = %d, expected %d" % [regions.size(), expected_n])

	var expected_owner_0 = _region_owner(expected.data, 0)
	var actual_owner_0 = bridge.owner_of(0)
	_assert(actual_owner_0 == expected_owner_0,
		"owner_of(0) = %s, expected %s (from %s)" % [actual_owner_0, expected_owner_0, expected.path])

	var actual_checksum = bridge.checksum()
	var expected_checksum = int(expected.data.get("checksum", -1))
	_assert(actual_checksum == expected_checksum,
		"checksum() = %s, expected %s" % [actual_checksum, expected_checksum])

	var edges: Array = bridge.edges()
	var expected_edges: Array = expected.data.get("edges", [])
	_assert(edges.size() == expected_edges.size(),
		"edges().size() = %d, expected %d" % [edges.size(), expected_edges.size()])

	_check_missing_regions_rejected(bridge, expected.data)


# A snapshot missing the required "regions" key (docs/architecture.md "C
# transport v1"; snapshot.schema.json marks it required) must be rejected
# with an error return, never a crash or an unhandled exception.
func _check_missing_regions_rejected(bridge, good_snapshot: Dictionary) -> void:
	var bad: Dictionary = good_snapshot.duplicate(true)
	bad.erase("regions")
	_assert(not bad.has("regions"), "test setup bug: bad fixture still has 'regions'")
	var wrote := _write_json(BAD_PATH, bad)
	_assert(wrote, "could not write the malformed fixture to " + BAD_PATH)
	if not wrote:
		return

	var result = bridge.load_snapshot_file(BAD_PATH)
	var rejected: bool = (result == false) or (result is Dictionary and not bool(result.get("ok", true)))
	_assert(rejected,
		"load_snapshot_file on a snapshot missing 'regions' must return an error result (false, or {ok:false,...}), got: %s" % str(result))
	# Reaching this line at all (no engine crash, no unhandled script error
	# aborting the process) is itself the "not a crash" half of the assertion.
	_assert(true, "load_snapshot_file on the malformed snapshot returned control instead of crashing the process")


func _fixture_snapshot():
	if FileAccess.file_exists(FIXTURE_PATH):
		var data = _read_json(FIXTURE_PATH)
		if data != null:
			return {"path": FIXTURE_PATH, "data": data}
	var built := _build_minimal_snapshot()
	if not _write_json(FALLBACK_PATH, built):
		return null
	return {"path": FALLBACK_PATH, "data": built}


func _region_owner(snapshot: Dictionary, idx: int):
	for r in snapshot.get("regions", []):
		if int(r.get("i", -999)) == idx:
			return int(r.get("owner", -1))
	return null


# Minimal valid instance of docs/northstar/spec_factory/transport/snapshot.schema.json:
# 60 regions, an undirected edge list (a < b, om_edge_type in csrc/ouroboros_sim.h),
# no names/positions/prose (C5 rule, docs/architecture.md "C transport v1").
func _build_minimal_snapshot() -> Dictionary:
	var regions := []
	for i in range(FALLBACK_N_REGIONS):
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
	for i in range(FALLBACK_N_REGIONS - 1):
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
