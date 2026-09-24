extends SceneTree

# Piece C2-3 (docs/northstar/plans/push, P1 rung finding): res://autoload/
# c_bridge.gd's load_snapshot_live spawns pipe/ouroboros_pipe and talks the
# live C transport v1 wire protocol (docs/architecture.md "C transport v1"),
# unlike tests/test_c_bridge.gd which only ever exercises load_snapshot_file
# against tests/transport/fixtures/snapshot_seed1_tick10.json. Proves S-106/
# R-106-01 (drawn systems equal the regions, docs/bible/epics/
# E-16-client-camera-hud-and-world-view.md): a request below the 75-region
# feasibility floor for the default 15-faction generator (csrc/ouroboros_sim.h
# om_world_generate; empirically confirmed at tests/transport/
# test_pipe_shapes.py's n_regions=80 comment) must surface as a failure, not
# a silently-accepted empty snapshot. Loaded as a plain script and
# instantiated directly, exactly like test_c_bridge.gd.
#
# EXPECTED_LIVE_CHECKSUM_I64 is the int64 two's-complement bit pattern of the
# checksum scripts/specfactory/snapshot_fixture.py --generate computes for
# seed=1, 80 regions, tick 10, feature 6 (DRIFT) only -- the same invocation
# tests/transport/test_pipe_shapes.py's ctypes reference uses, and the same
# invocation that produced tests/transport/fixtures/snapshot_seed1_tick10.json
# (docs/architecture.md "C transport v1"). The raw uint64 is 9459460945690250679
# (> INT64_MAX); c_bridge.gd's own _decimal_to_i64 comment explains why the
# wire text is re-read as a decimal digit string instead of trusting
# JSON.parse_string on a number that large. Regenerate with:
#   scripts/specfactory/snapshot_fixture.py --seed 1 --regions 80 --ticks 10 \
#     --features 6 --generate --out /tmp/x.json
# if the sim's checksum algorithm or seed-1/80-region generation output ever
# changes (both are pinned by the determinism contract, CLAUDE.md, so this
# should not happen without a deliberate, documented change).

const BRIDGE_SCRIPT_PATH := "res://autoload/c_bridge.gd"
const PIPE_RES_PATH := "res://pipe/ouroboros_pipe"
const GOOD_SEED := 1
const GOOD_N_REGIONS := 80
const GOOD_FEATURES: Array = [6]
const BELOW_FLOOR_N_REGIONS := 60
const EXPECTED_N_REGIONS := 80
const EXPECTED_N_OWNED := 51
const EXPECTED_N_EDGES := 88
const EXPECTED_LIVE_CHECKSUM_I64 := -8987283128019300937

var _pass_count := 0
var _fail_count := 0
var _fail_msgs: Array[String] = []


func _initialize() -> void:
	_run_tests()
	print("\n=== C Bridge Live Test Results ===")
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
	var pipe_exe := ProjectSettings.globalize_path(PIPE_RES_PATH)
	_assert(FileAccess.file_exists(pipe_exe),
		"pipe/ouroboros_pipe not built at %s -- run `make pipe/ouroboros_pipe` first" % pipe_exe)
	if not FileAccess.file_exists(pipe_exe):
		return

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

	for m in ["load_snapshot_live", "regions", "owner_of", "checksum", "edges"]:
		_assert(bridge.has_method(m), "c_bridge missing method: " + m)
	if not (bridge.has_method("load_snapshot_live") and bridge.has_method("regions")
			and bridge.has_method("checksum") and bridge.has_method("edges")):
		return

	_check_good_live_load(bridge)
	_check_below_floor_live_load_fails(bridge)
	_check_snapshot_unchanged_after_failed_load(bridge)


# S-106/R-106-01 (each system drawn equals a region in the snapshot,
# docs/bible/epics/E-16-client-camera-hud-and-world-view.md): a feasible
# live request (80 regions, at/above the 75-region floor) must succeed and
# hand back the exact shape the C reference computes for seed 1, tick 10.
func _check_good_live_load(bridge) -> void:
	var ok = bridge.load_snapshot_live(GOOD_SEED, GOOD_N_REGIONS, GOOD_FEATURES)
	_assert(bool(ok),
		"S-106/R-106-01 (docs/architecture.md \"C transport v1\"): load_snapshot_live(%d, %d, %s) did not report success"
		% [GOOD_SEED, GOOD_N_REGIONS, str(GOOD_FEATURES)])
	if not bool(ok):
		return

	var regions: Array = bridge.regions()
	_assert(regions.size() == EXPECTED_N_REGIONS,
		"S-106/R-106-01: regions().size() = %d, expected %d (drawn systems must equal the regions)"
		% [regions.size(), EXPECTED_N_REGIONS])

	var owned := 0
	for r in regions:
		if int(r.get("owner", -1)) >= 0:
			owned += 1
	_assert(owned == EXPECTED_N_OWNED,
		"S-106/R-106-01: %d owned region(s), expected %d" % [owned, EXPECTED_N_OWNED])

	var edges: Array = bridge.edges()
	_assert(edges.size() == EXPECTED_N_EDGES,
		"S-106/R-106-01: edges().size() = %d, expected %d" % [edges.size(), EXPECTED_N_EDGES])

	var actual_checksum = bridge.checksum()
	_assert(actual_checksum == EXPECTED_LIVE_CHECKSUM_I64,
		"docs/architecture.md \"C transport v1\": checksum() = %s, expected %s (the C reference's value for seed=%d, %d regions, tick 10, feature 6)"
		% [actual_checksum, EXPECTED_LIVE_CHECKSUM_I64, GOOD_SEED, GOOD_N_REGIONS])


# The pipe answers set_seed with an error frame ("generation failed") when
# n_regions is below the feasibility floor, but c_bridge.gd's load_snapshot_live
# still sends "step" and "snapshot" afterward (om_pipe.c leaves W non-null on a
# failed set_seed, so "snapshot" comes back {"type":"snapshot","regions":[]}
# instead of an error) -- confirmed empirically against pipe/ouroboros_pipe
# while writing this test. load_snapshot_live must not treat that empty
# snapshot as success.
#
# last_error() does not exist on c_bridge.gd yet. This assertion documents
# the accessor the fix doer must add: a method named exactly `last_error`
# (no args) returning a String containing the pipe's error "reason" text
# ("generation failed") after a failed load_snapshot_live call.
func _check_below_floor_live_load_fails(bridge) -> void:
	var ok = bridge.load_snapshot_live(GOOD_SEED, BELOW_FLOOR_N_REGIONS, GOOD_FEATURES)
	_assert(not bool(ok),
		"S-106/R-106-01 (docs/architecture.md \"C transport v1\"): load_snapshot_live(%d, %d, %s) must return false -- %d regions is below the 75-region feasibility floor for the default 15-faction generator and the pipe answers set_seed with an error frame"
		% [GOOD_SEED, BELOW_FLOOR_N_REGIONS, str(GOOD_FEATURES), BELOW_FLOOR_N_REGIONS])

	_assert(bridge.has_method("last_error"),
		"c_bridge missing accessor: last_error() -- not implemented yet; the fix doer must add a no-arg method named exactly `last_error` returning a String, so a failed load_snapshot_live can surface the pipe's error \"reason\" (\"generation failed\") instead of nothing")
	if not bridge.has_method("last_error"):
		return

	var err := String(bridge.last_error())
	_assert(err.find("generation failed") != -1,
		"c_bridge.last_error() = %s, expected it to contain \"generation failed\" (the pipe's set_seed error reason, csrc/pipe/om_pipe.c)" % err)


# After a failed load_snapshot_live, the previously loaded snapshot (from
# _check_good_live_load, same bridge instance) must be unchanged -- a caller
# that only checks the return value and otherwise reads regions()/checksum()
# must never observe the empty, below-floor result.
func _check_snapshot_unchanged_after_failed_load(bridge) -> void:
	var regions: Array = bridge.regions()
	_assert(regions.size() == EXPECTED_N_REGIONS,
		"S-106/R-106-01: after a failed load_snapshot_live, regions().size() = %d, expected the previous good snapshot's %d (no snapshot is set on failure)"
		% [regions.size(), EXPECTED_N_REGIONS])

	var actual_checksum = bridge.checksum()
	_assert(actual_checksum == EXPECTED_LIVE_CHECKSUM_I64,
		"docs/architecture.md \"C transport v1\": after a failed load_snapshot_live, checksum() = %s, expected the previous good snapshot's %s unchanged"
		% [actual_checksum, EXPECTED_LIVE_CHECKSUM_I64])
