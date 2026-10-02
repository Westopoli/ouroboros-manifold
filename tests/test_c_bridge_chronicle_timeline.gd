extends SceneTree

# G-C3 client unit 1 (docs/northstar/plans/2026-10-01-architect-rulings-2.md
# A48 item 13, A59, A65): autoload/c_bridge.gd hands the client the chronicle
# frame's optional "ownership" and "keyframes" fields, and never hands out a
# timeline that belongs to a world that is gone.
#   * chronicle_frame() already returns the whole frame; the first block is a
#     guard that the live frame carries both fields in the documented shape
#     (docs/architecture.md "chronicle frame"): stride 2, n_regions == the
#     world's regions, jump_ticks/2 + 1 snapshots (26 for the 50-tick jump),
#     every owner an int in -1..n_factions-1, from_tick == jump.from_tick;
#     keyframes ascending, no duplicates, inside [from_tick, to_tick].
#   * A59: timelines are memory-only. After load(slot) the bridge shows no
#     chronicle frame at all (so no "ownership", no "keyframes": the client
#     shows the scroll over the final state, no replay). Today load() leaves
#     the pre-load frame in place, which is the red check.
# Positive control: the same bridge, before the load, DID carry both fields.

const CBridgeScript := "res://autoload/c_bridge.gd"

var _pass_count := 0
var _fail_count := 0
var _fail_msgs: Array[String] = []


func _initialize() -> void:
	_run_tests()
	print("\n=== C Bridge Chronicle Timeline Results ===")
	print("PASS: %d  FAIL: %d" % [_pass_count, _fail_count])
	for msg in _fail_msgs:
		print("  - " + msg)
	print("=== %s ===\n" % ("RED" if _fail_count > 0 else "GREEN"))
	quit(1 if _fail_count > 0 else 0)


func _assert(cond: bool, msg: String) -> void:
	if cond:
		_pass_count += 1
	else:
		_fail_count += 1
		_fail_msgs.append(msg)


func _run_tests() -> void:
	var tmp := ProjectSettings.globalize_path("user://test_c_bridge_chronicle_timeline_saves")
	DirAccess.make_dir_recursive_absolute(tmp)
	OS.set_environment("OM_SAVE_DIR", tmp)
	var CBridge = load(CBridgeScript)
	var bridge = CBridge.new()
	var ok: bool = bridge.load_chronicle_live(1, CBridge.DEFAULT_N_REGIONS, CBridge.DEFAULT_FEATURES)
	_assert(ok, "load_chronicle_live failed: %s" % bridge.last_error())
	if not ok:
		OS.set_environment("OM_SAVE_DIR", "")
		return
	var frame: Dictionary = bridge.chronicle_frame()
	_check_live_fields(frame, bridge, CBridge.DEFAULT_N_REGIONS)

	# A59 after a load. campaign_1 was written by the autosave above.
	var snap: Dictionary = bridge.load("campaign_1")
	_assert(not snap.is_empty(), "load(campaign_1) returned no snapshot: %s" % bridge.last_error())
	var after: Dictionary = bridge.chronicle_frame()
	_assert(not after.has("ownership"), "A59: after load() chronicle_frame() still carries the pre-load \"ownership\" timeline")
	_assert(not after.has("keyframes"), "A59: after load() chronicle_frame() still carries the pre-load \"keyframes\"")
	_assert(after.is_empty(), "A59: after load() chronicle_frame() is not empty (a load produces no chronicle frame)")

	bridge.close_session()
	OS.set_environment("OM_SAVE_DIR", "")
	for f in DirAccess.get_files_at(tmp):
		DirAccess.remove_absolute(tmp.path_join(f))


func _check_live_fields(frame: Dictionary, bridge, n_regions: int) -> void:
	_assert(frame.has("ownership") and frame["ownership"] is Dictionary, "live chronicle frame has no \"ownership\" object (positive control for the post-load check)")
	_assert(frame.has("keyframes") and frame["keyframes"] is Array, "live chronicle frame has no \"keyframes\" array (positive control for the post-load check)")
	if not (frame.get("ownership") is Dictionary and frame.get("keyframes") is Array):
		return
	var own: Dictionary = frame["ownership"]
	var jump: Dictionary = frame.get("jump", {})
	var from_tick := int(jump.get("from_tick", -1))
	var to_tick := int(jump.get("to_tick", -1))
	_assert(int(own.get("stride", 0)) == 2, "ownership.stride = %s, expected 2" % str(own.get("stride")))
	_assert(int(own.get("from_tick", -2)) == from_tick, "ownership.from_tick %s != jump.from_tick %d" % [str(own.get("from_tick")), from_tick])
	_assert(int(own.get("n_regions", 0)) == n_regions, "ownership.n_regions = %s, expected %d" % [str(own.get("n_regions")), n_regions])
	var snaps: Array = own.get("snapshots", [])
	_assert(snaps.size() == (to_tick - from_tick) / 2 + 1, "ownership.snapshots has %d entries, expected %d" % [snaps.size(), (to_tick - from_tick) / 2 + 1])
	var n_factions: int = (bridge.snapshot().get("factions", []) as Array).size()
	var shape_ok := true
	var range_ok := true
	for s in snaps:
		if not (s is Array) or (s as Array).size() != n_regions:
			shape_ok = false
			continue
		for v in s:
			if not (v is float or v is int) or int(v) < -1 or int(v) >= maxi(n_factions, 1):
				range_ok = false
	_assert(shape_ok, "a snapshot is not an array of n_regions owners")
	_assert(range_ok, "a snapshot owner is outside -1..n_factions-1 (n_factions = %d)" % n_factions)
	var kfs: Array = frame["keyframes"]
	var sorted_ok := true
	var inside_ok := true
	for i in range(kfs.size()):
		if i > 0 and int(kfs[i]) <= int(kfs[i - 1]):
			sorted_ok = false
		if int(kfs[i]) < from_tick or int(kfs[i]) > to_tick:
			inside_ok = false
	_assert(sorted_ok, "keyframes are not strictly ascending: %s" % str(kfs))
	_assert(inside_ok, "a keyframe lies outside [from_tick, to_tick]: %s" % str(kfs))
