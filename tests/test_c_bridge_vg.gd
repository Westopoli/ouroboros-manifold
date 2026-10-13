extends SceneTree

# Visible-game programme lane K, pieces K-a (autoload/c_bridge.gd decoders, set_layer and
# activate_ability wrappers, heights into terrain()), K-f (OM_PIPE override of the pipe path) and
# K-h (load_mission_live's fog_filter parameter, default off). Written against
# docs/northstar/plans/2026-10-07-visible-game-spec.md rev 4 section 2 and the rulebook rev 2.
# Fenced: builders never edit this file. Frames are fixture dictionaries; no live pipe is driven
# except the OM_PIPE case, which launches the real pipe through a wrapper script.
#
# Stories and rules: S-087 (fire/kill events), S-209 (structures), S-005 R-104-09 (layer order),
# S-086 R-096-05 (ability order), S-236 (heights), S-139 (K-f), S-089 R-089-03 and S-205 R-205-02 (K-h).
# Assumptions where section 2 is silent (reported, not guessed silently):
#   * the reconstructed view returned by _reconstruct_tactical carries `structures` (an Array of full
#     rows, ascending id), `events` (the frame's own list, not accumulated across frames), `profiles`
#     (kept from the last full frame) and `objectives`;
#   * set_layer and activate_ability go through send_unit_command(kind "set_layer" / "activate_ability",
#     keys unit_ids, layer / x, y) and send {"verb": kind, "units": ids, ...} like the existing kinds;
#   * the decoded heights are available as terrain()["heights"], an Array or PackedInt32Array of cm.

var _pass_count := 0
var _fail_count := 0
var _fail_msgs: Array[String] = []
var _completed := false

const STRUCT_A := {"id": 4, "type": 0, "owner": 1, "x": 3000.0, "y": 3000.0, "hp": 3000.0, "stage": 0, "cap": 0, "nst": 900, "next_type": 1, "period": 600}
const STRUCT_B := {"id": 7, "type": 0, "owner": 0, "x": 9000.0, "y": 9000.0, "hp": 3000.0, "stage": 0, "cap": 400, "nst": 1200, "next_type": 0, "period": 600}


func _initialize() -> void:
	_run_tests()
	_assert(_completed, "the VG bridge checks did not run to the end (a script error aborted them)")
	print("\n=== C Bridge VG Contract Test Results ===")
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


# A bridge whose pipe is replaced by recording stubs: send_command and _request record, _request
# answers `canned` (a Dictionary keyed by frame type), ensure_world and _autosave succeed.
func _stub_bridge() -> Object:
	var gs := GDScript.new()
	gs.source_code = "extends \"res://autoload/c_bridge.gd\"\n" \
		+ "var sent: Array = []\n" \
		+ "var canned: Dictionary = {}\n" \
		+ "func send_command(cmd: Dictionary) -> void:\n\tsent.append(cmd)\n" \
		+ "func _request(cmds: Array, want: Array) -> Dictionary:\n\tfor c in cmds:\n\t\tsent.append(c)\n\treturn canned\n" \
		+ "func ensure_world(seed: int, n_regions: int, features: Array) -> bool:\n\treturn true\n" \
		+ "func _autosave() -> bool:\n\treturn true\n"
	var err := gs.reload()
	_assert(err == OK, "the stub bridge script did not compile (%d)" % err)
	return gs.new()


func _by_id(rows: Array) -> Dictionary:
	var out := {}
	for r in rows:
		out[int(r["id"])] = r
	return out


func _unit(id: int, faction: int, state: int = 0) -> Dictionary:
	return {"id": id, "faction": faction, "type": 0, "tier": 0, "x": 100.0 * id, "y": 50.0, "hp": 100.0, "layer": 0, "facing": 0.0, "target": -1, "state": state}


func _full_frame() -> Dictionary:
	return {
		"type": "tactical", "tick": 20, "full": true, "mission_over": false, "band": -1,
		"units": [_unit(1, 0), _unit(2, 1)],
		"structures": [STRUCT_B.duplicate(), STRUCT_A.duplicate()],
		"events": [[0, 1, 2, 19]],
		"profiles": [{"type": 0, "max_hp": 250.0, "range": 200.0, "interval": 10, "sensor": 800.0, "ability": 0, "acd_max": 600, "aoe": 0.0}],
		"objectives": [{"i": 0, "progress": 0.1, "done": 0}],
		"map": {"canvas": 16000, "nodes": [], "cover": [{"x": 1.0, "y": 2.0, "r": 120.0, "h": 40.0, "class": 0}], "obstacles": [{"x": 5.0, "y": 6.0, "r": 200.0}]},
	}


func _delta_frame() -> Dictionary:
	var changed: Dictionary = STRUCT_A.duplicate()
	changed["owner"] = 0
	changed["cap"] = 1000
	return {
		"type": "tactical", "tick": 21, "full": false, "mission_over": false, "band": -1,
		"units_changed": [_unit(1, 0, 1)], "units_removed": [2],
		"structures_changed": [{"id": 4, "owner": 0, "cap": 1000}], "structures_removed": [7],
		"events": [[2, 2, 1, 21], [3, 4, 0, 21]],
		"objectives": [{"i": 0, "progress": 0.26, "done": 0}],
	}


func _run_tests() -> void:
	var CBridge = load("res://autoload/c_bridge.gd")

	# ---- K-a: decoders ----
	var b = CBridge.new()
	var full: Dictionary = b._reconstruct_tactical(_full_frame())
	_assert(full.get("structures", null) is Array and (full.get("structures", []) as Array).size() == 2,
		"S-209: the reconstructed full view has no `structures` array of both rows (keys: %s)" % [full.keys()])
	var srows: Array = full.get("structures", [])
	if srows.size() == 2:
		_assert(int(srows[0]["id"]) == 4 and int(srows[1]["id"]) == 7, "S-209: structures are not listed in ascending id")
	_assert(full.get("events", null) == [[0, 1, 2, 19]], "S-087: events were not passed through: %s" % [full.get("events")])
	_assert(full.get("profiles", null) is Array and (full.get("profiles", []) as Array).size() == 1, "S-086: profiles missing from the full view")
	var cover: Array = full.get("map", {}).get("cover", [])
	_assert(cover.size() == 1 and int(cover[0].get("class", -1)) == 0 and (full["map"].get("obstacles", []) as Array).size() == 1,
		"S-007: map cover `class` or obstacles lost in the view")

	var delta: Dictionary = b._reconstruct_tactical(_delta_frame())
	var sd := _by_id(delta.get("structures", []))
	_assert(sd.size() == 1 and sd.has(4), "S-209: after structures_changed/removed the view should hold only structure 4, holds %s" % [sd.keys()])
	if sd.has(4):
		_assert(int(sd[4]["owner"]) == 0 and int(sd[4]["cap"]) == 1000 and int(sd[4]["period"]) == 600 and float(sd[4]["x"]) == 3000.0,
			"S-209: a changed structure must overlay its changed fields on the kept row: %s" % [sd[4]])
	_assert(delta.get("events", null) == [[2, 2, 1, 21], [3, 4, 0, 21]],
		"S-087: a delta's events must be that frame's own list (never diffed, never accumulated): %s" % [delta.get("events")])
	_assert(delta.get("profiles", null) is Array and (delta.get("profiles", []) as Array).size() == 1, "S-086: profiles from the last full frame must survive the delta")
	_assert(not (delta.get("units_changed", null) is Array) and (delta.get("units", []) as Array).size() == 1, "control: units_removed did not drop unit 2")
	var u1: Dictionary = _by_id(delta.get("units", [])).get(1, {})
	_assert(int(u1.get("state", -1)) == 1, "S-087: unit state bit not carried into the view: %s" % [u1])
	var objs: Array = delta.get("objectives", [])
	_assert(objs.size() == 1 and objs[0].has("done"), "R-104-01: objectives lost `done`")
	# control: a second full frame replaces structures wholesale
	var again: Dictionary = b._reconstruct_tactical(_full_frame())
	_assert((again.get("structures", []) as Array).size() == 2, "control: a new full frame must restore both structures")

	# ---- K-a: layer and ability orders ----
	var s = _stub_bridge()
	_assert(s.send_unit_command({"kind": "set_layer", "unit_ids": [3, 4], "layer": 2}) == true, "S-005: send_unit_command refused kind set_layer")
	_assert(s.sent.size() == 1 and s.sent[0].get("verb", "") == "set_layer" and s.sent[0].get("units", []) == [3, 4] and int(s.sent[0].get("layer", -1)) == 2,
		"S-005: set_layer did not send {verb:set_layer, units:[3,4], layer:2}: %s" % [s.sent])
	var s2 = _stub_bridge()
	_assert(s2.send_unit_command({"kind": "activate_ability", "unit_ids": [5], "x": 10.0, "y": 20.0}) == true, "S-086: send_unit_command refused kind activate_ability")
	_assert(s2.sent.size() == 1 and s2.sent[0].get("verb", "") == "activate_ability" and s2.sent[0].get("units", []) == [5] and float(s2.sent[0].get("x", -1.0)) == 10.0,
		"S-086: activate_ability did not send {verb, units:[5], x:10, y:20}: %s" % [s2.sent])
	var s3 = _stub_bridge()
	_assert(s3.send_unit_command({"kind": "bogus", "unit_ids": [1]}) == false and s3.sent.is_empty(), "control: an unknown kind must still be refused unsent")
	_assert(s3.send_unit_command({"kind": "set_layer", "unit_ids": [], "layer": 1}) == false and s3.sent.is_empty(), "control: set_layer with no units must be refused unsent")

	# ---- K-a: heights into terrain() ----
	var h = _stub_bridge()
	# 2x2 cells, cm: 0, 100, -50, 25600 as little-endian int32 hex
	h.canned = {"terrain": {"type": "terrain", "cells_w": 2, "cells_h": 2, "bands": "00000000", "walkable": "01010101", "slopes": [],
		"heights": "00000000" + "64000000" + "ceffffff" + "00640000"}}
	_assert(h._fetch_terrain() == true, "control: _fetch_terrain failed on the fixture dump")
	var heights = h.terrain().get("heights", null)
	_assert(heights != null and heights.size() == 4, "S-236: terrain() has no 4-element `heights` (keys: %s)" % [h.terrain().keys()])
	if heights != null and heights.size() == 4:
		_assert([int(heights[0]), int(heights[1]), int(heights[2]), int(heights[3])] == [0, 100, -50, 25600],
			"S-236: heights decoded to %s, expected [0, 100, -50, 25600] (little-endian signed int32 cm)" % [heights])
	_assert(int(h.terrain().get("cells_w", 0)) == 2 and (h.terrain().get("bands", PackedByteArray()) as PackedByteArray).size() == 4, "control: existing terrain fields changed")

	# ---- K-f: OM_PIPE override ----
	var real_pipe := ProjectSettings.globalize_path("res://pipe/ouroboros_pipe")
	var kf = CBridge.new()
	OS.set_environment("OM_PIPE", "/nonexistent/vg_pipe_for_a_red_test")
	var opened: bool = kf.open_session(1, 0, [])
	_assert(opened == false, "S-139 (K-f): OM_PIPE pointing at a missing file must win over the default path (open_session returned true)")
	kf.close_session()
	var wrapper := OS.get_user_data_dir().path_join("vg_pipe_wrapper_%d.sh" % Time.get_ticks_usec())
	var f := FileAccess.open(wrapper, FileAccess.WRITE)
	if f != null:
		f.store_string("#!/bin/sh\ntouch \"%s.ran\"\nexec \"%s\" \"$@\"\n" % [wrapper, real_pipe])
		f.close()
		OS.execute("chmod", ["+x", wrapper])
		OS.set_environment("OM_PIPE", wrapper)
		var kf2 = CBridge.new()
		var opened2: bool = kf2.open_session(1, 0, [])
		OS.delay_msec(300)
		_assert(opened2 == true and FileAccess.file_exists(wrapper + ".ran"), "S-139 (K-f): OM_PIPE=<wrapper> was not the program launched (opened=%s)" % opened2)
		kf2.close_session()
		DirAccess.remove_absolute(wrapper)
		DirAccess.remove_absolute(wrapper + ".ran")
	else:
		_assert(false, "control: could not write the wrapper script in the user data dir")
	OS.set_environment("OM_PIPE", "")
	var kf3 = CBridge.new()
	_assert(kf3.open_session(1, 0, []) == true, "control: with OM_PIPE unset the default pipe must open (pipe/ouroboros_pipe built?)")
	kf3.close_session()

	# ---- K-h: fog_filter parameter ----
	var d = _stub_bridge()
	d.canned = {"mission": {"type": "mission"}}
	d.load_mission_live(1, 80, [0, 1])
	var start_d: Dictionary = _first_named(d.sent, "mission_start")
	_assert(not start_d.is_empty(), "control: load_mission_live sent no mission_start")
	_assert(not bool(start_d.get("fog_filter", false)), "R-089-03 (K-h): the default load_mission_live must not turn fog_filter on: %s" % [start_d])
	var on = _stub_bridge()
	on.canned = {"mission": {"type": "mission"}}
	var n_args := 0
	for m in on.get_method_list():
		if m["name"] == "load_mission_live":
			n_args = (m["args"] as Array).size()
	_assert(n_args >= 4, "R-089-03 (K-h): load_mission_live takes %d parameters, expected a fourth fog_filter parameter" % n_args)
	if n_args >= 4:
		on.load_mission_live(1, 80, [0, 1], true)
	var start_on: Dictionary = _first_named(on.sent, "mission_start")
	_assert(start_on.get("fog_filter", false) == true, "R-089-03, R-205-02 (K-h): load_mission_live(..., true) must send mission_start {fog_filter:true}: %s" % [start_on])
	_assert(n_args < 4 or int(start_on.get("faction", -1)) == 0, "control: mission_start lost its faction when the flag was added")

	_completed = true


func _first_named(cmds: Array, name: String) -> Dictionary:
	for c in cmds:
		if c is Dictionary and String(c.get("name", "")) == name:
			return c
	return {}
