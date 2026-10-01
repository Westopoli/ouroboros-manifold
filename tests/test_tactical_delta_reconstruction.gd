extends SceneTree

# A7 client side (docs/architecture.md "Delta frame" and "Reconstruction";
# architect rulings round 2, section 3). The pipe writes full tactical frames
# (map + units[]) and delta frames (units_changed[] + units_removed[], no map).
# autoload/c_bridge.gd must keep an id -> unit dictionary: a full frame replaces
# it, a delta first deletes units_removed then overwrites with units_changed.
# The tactical frame the view reads (tactical_frame().get("units"/"map")) must
# always be the reconstructed full view, map kept from the last full frame.
# tactical_step_n(n) waits for ONE frame per call (n > 1 writes only the last).
#
# Ground truth is the server itself: a tactical_step with n = 0 and "full":true
# writes a full frame at the current tick without stepping.
#
# Positive controls: the mission has units in two factions, at least one unit
# dies over the run (so "a death removes the unit" reads a real removal), and a
# delta frame really carries no map (the frame from a raw n=1 step).
#
# Acceptance bar once the client is fixed, not edited here: tests/test_tactical_view.gd,
# test_tactical_hud.gd, test_tactical_attack_move.gd, test_tactical_camera.gd.

const STEP_TIMEOUT_NOTE := "tactical_step_n waits for one frame per call (A7), not n"

var _pass_count := 0
var _fail_count := 0
var _fail_msgs: Array[String] = []
var _completed := false


func _initialize() -> void:
	_run_tests()
	_assert(_completed, "the reconstruction checks did not run to the end (a script error aborted them)")
	print("\n=== Tactical Delta Reconstruction Test Results ===")
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


func _by_id(units: Array) -> Dictionary:
	var out := {}
	for u in units:
		out[int(u["id"])] = u
	return out


# The server's own full frame at the bridge's current tick.
func _server_full(bridge) -> Dictionary:
	var got: Dictionary = bridge._request([{"type": "cmd", "name": "tactical_step", "n": 0, "full": true}], ["tactical"])
	return got.get("tactical", {})


func _compare_to_server(bridge, label: String) -> void:
	var view: Dictionary = bridge.tactical_frame()
	var truth := _server_full(bridge)
	_assert(not truth.is_empty() and bool(truth.get("full", false)), "%s: the n=0 full:true request did not answer a full frame (last_error = %s)" % [label, bridge.last_error()])
	if truth.is_empty():
		return
	_assert(view.get("units", null) is Array, "%s: the stored tactical frame has no units array (a delta was stored as is)" % label)
	_assert(view.get("map", null) is Dictionary, "%s: the stored tactical frame has no map (maps ride only full frames; keep the last one)" % label)
	if not (view.get("units", null) is Array):
		return
	_assert(int(view.get("tick", -1)) == int(truth["tick"]), "%s: view tick %s != server tick %s" % [label, view.get("tick"), truth["tick"]])
	var got := _by_id(view["units"])
	var want := _by_id(truth["units"])
	_assert(got.size() == want.size(), "%s: view holds %d units, the server's full frame %d" % [label, got.size(), want.size()])
	var mismatches := 0
	for id in want:
		if not got.has(id) or got[id] != want[id]:
			mismatches += 1
	_assert(mismatches == 0, "%s: %d units differ (position, hp or presence) from the server's full frame" % [label, mismatches])
	for id in got:
		_assert(want.has(id), "%s: view keeps unit %d that the server's full frame no longer lists (a death did not remove it)" % [label, id])
		break
	_assert(view.get("map", {}) == truth.get("map", {}), "%s: view map differs from the server's full-frame map" % label)


func _run_tests() -> void:
	var CBridge = load("res://autoload/c_bridge.gd")
	var bridge = CBridge.new()
	var ok: bool = bridge.load_tactical_live(1, CBridge.DEFAULT_N_REGIONS, CBridge.DEFAULT_FEATURES)
	_assert(ok, "load_tactical_live returned false (last_error = %s)" % bridge.last_error())
	var first: Dictionary = bridge.tactical_frame()
	# First red line on A7-pipe: load_tactical_live stores the delta its tactical_step n=1 answered.
	_assert(first.get("units", null) is Array and (first.get("units", []) as Array).size() > 0, "load_tactical_live: the stored tactical frame has no units (the stored frame is a delta)")
	_assert(first.get("map", null) is Dictionary and (first.get("map", {}) as Dictionary).has("nodes"), "load_tactical_live: the stored tactical frame has no map")
	if not (first.get("units", null) is Array):
		_finish(bridge)
		return
	var factions := {}
	for u in first["units"]:
		factions[int(u["faction"])] = true
	_assert(factions.size() >= 2, "control: the mission has units of one faction only")
	var start_ids := _by_id(first["units"])
	var tick0 := int(first.get("tick", -1))
	_compare_to_server(bridge, "after load_tactical_live (tick %d)" % tick0)

	# Control: a raw single step answers a delta with no map and no units.
	var raw: Dictionary = bridge._request([{"type": "cmd", "name": "tactical_step", "n": 1}], ["tactical"]).get("tactical", {})
	_assert(raw.get("full", true) == false and not raw.has("map") and not raw.has("units"), "control: a raw n=1 tactical_step frame is not a delta: %s" % [raw.keys()])
	# That raw step moved the world one tick past what the bridge has stored; resync the stored view by stepping through the bridge.

	# n > 1 writes one frame: the call must return true with the tick advanced by n.
	var before := int(bridge.tactical_frame().get("tick", -1))
	var stepped: bool = bridge.tactical_step_n(5)
	_assert(stepped, "tactical_step_n(5) returned false (%s; last_error = %s)" % [STEP_TIMEOUT_NOTE, bridge.last_error()])
	if not stepped:
		_finish(bridge)
		return
	_assert(int(bridge.tactical_frame().get("tick", -1)) == before + 6, "tactical_step_n(5): tick %s, expected %d (the earlier raw step plus 5)" % [bridge.tactical_frame().get("tick"), before + 6])
	_compare_to_server(bridge, "after tactical_step_n(5)")

	# Deltas and the every-20th-step full frame interleave: 45 single steps cross two multiples of 20.
	for i in 45:
		if not bridge.tactical_step_n(1):
			_assert(false, "tactical_step_n(1) failed at step %d (%s)" % [i, bridge.last_error()])
			_finish(bridge)
			return
	_compare_to_server(bridge, "after 45 single steps")

	# Drive the player's units at the enemy so that a unit dies (seed 1 never fights
	# unprompted); each 40-step call crosses two full-frame boundaries, the frames
	# between them are deltas.
	var mine: Array = []
	var ex := 0.0
	var ey := 0.0
	var foes := 0
	for u in first["units"]:
		if int(u["faction"]) == 0:
			mine.append(int(u["id"]))
		else:
			ex += float(u["x"])
			ey += float(u["y"])
			foes += 1
	_assert(bridge.send_unit_command({"kind": "attack_move", "unit_ids": mine, "x": ex / foes, "y": ey / foes}), "attack_move command was refused")
	var died := false
	var seen := start_ids.duplicate()
	var dead_id := -1
	for i in 80:
		if not bridge.tactical_step_n(40):
			_assert(false, "tactical_step_n(40) failed (%s)" % bridge.last_error())
			break
		var now := _by_id(bridge.tactical_frame().get("units", []))
		for id in seen:
			if not now.has(id):
				died = true
				dead_id = id
		if died:
			break
		seen.merge(now)
	_assert(died, "control: no unit died within the stepped run, the death check below proves nothing")
	_compare_to_server(bridge, "after a unit died")
	_assert(not _by_id(bridge.tactical_frame().get("units", [])).has(dead_id), "unit %d died but is still in the view" % dead_id)
	_finish(bridge)


func _finish(bridge) -> void:
	bridge.close_session()
	_completed = true
