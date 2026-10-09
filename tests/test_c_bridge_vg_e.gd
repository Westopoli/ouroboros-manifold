extends SceneTree

# Visible-game programme lane E1, K-e bridge decode (docs/northstar/plans/2026-10-07-visible-game-spec.md rev 6, lane E1,
# piece E1a; contract text docs/architecture.md "Visible-game economy fields"). Fenced: builders never edit this file.
# Pinned here (K-e's shapes, flagged for the contract text; the spec names the frame fields, not the bridge dicts):
#   * after mission_begin, in every era, the bridge sends ONE lots_dump ({"type":"cmd","name":"lots_dump"}, wants "lots")
#     and exposes lots() -> Array of {id, x, y, stage, building, owner} (ints, floats for x and y), ascending id; [] before
#     any dump. It is not asked again on tactical frames.
#   * a delta's lots_changed rows (same [id,x,y,stage,building,owner] row form) overlay lots() by id (new ids appended in
#     ascending order); lots() never loses a lot to a delta.
#   * _reconstruct_tactical's view carries: `lots` (the same list as lots()), `strongpoints` (Array of {id,x,y,owner,state}
#     from the last full frame, kept across deltas), `economy` (the frame's own {doctrine, resources} dict); the view has
#     no `lots_changed` key.
# "(control)" checks pass on main (structures decode unchanged). On main none of the rest exists: red.

var _pass_count := 0
var _fail_count := 0
var _fail_msgs: Array[String] = []
var _completed := false

const STRUCT_A := {"id": 4, "type": 0, "owner": 1, "x": 3000.0, "y": 3000.0, "hp": 3000.0, "stage": 0, "cap": 0, "nst": 900, "next_type": 1, "period": 600}
const SP_A := {"id": 2, "x": 4000.0, "y": 5000.0, "owner": -1, "state": 0}
const SP_B := {"id": 1, "x": 6000.0, "y": 1000.0, "owner": 0, "state": 1}

const STUB_SRC := """
extends "res://autoload/c_bridge.gd"

var sent: Array = []
var lots_rows: Array = [[5, 100.0, 200.0, 3, 1, 0], [2, 50.5, 60.5, 0, 2, -1]]


func send_command(cmd: Dictionary) -> void:
	sent.append(cmd)


func _request(cmds: Array, want: Array) -> Dictionary:
	for c in cmds:
		sent.append(c)
	var out := {}
	for w in want:
		match String(w):
			"mission":
				out["mission"] = {"type": "mission", "units": []}
			"tactical":
				out["tactical"] = {"type": "tactical", "full": true, "tick": 0, "units": [], "structures": [], "map": {}, "strongpoints": [], "economy": {"doctrine": 3, "resources": {}}}
			"space_field":
				out["space_field"] = {"type": "space_field", "cells_w": 240, "cells_h": 240, "layers": 5, "masks": [], "polys": []}
			"terrain":
				out["terrain"] = {"type": "terrain", "cells_w": 4, "cells_h": 4, "bands": "00000000000000000000000000000000", "walkable": "00000000000000000000000000000000", "slopes": []}
			"lots":
				out["lots"] = {"type": "lots", "lots": lots_rows}
	return out


func ensure_world(seed: int, n_regions: int, features: Array) -> bool:
	return true


func _autosave() -> bool:
	return true


func count(name: String) -> int:
	var n := 0
	for c in sent:
		if String(c.get("name", "")) == name:
			n += 1
	return n
"""


func _initialize() -> void:
	_run_tests()
	_assert(_completed, "the K-e bridge checks did not run to the end (a script error aborted them)")
	print("\n=== C Bridge VG-E Test Results ===")
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


func _full_frame() -> Dictionary:
	return {
		"type": "tactical", "tick": 20, "full": true, "mission_over": false, "band": -1,
		"units": [], "structures": [STRUCT_A.duplicate()], "events": [], "profiles": [], "objectives": [], "map": {},
		"strongpoints": [SP_A.duplicate(), SP_B.duplicate()],
		"economy": {"doctrine": 1, "resources": {}},
	}


func _delta_frame() -> Dictionary:
	return {
		"type": "tactical", "tick": 21, "full": false, "mission_over": false, "band": -1,
		"units_changed": [], "units_removed": [], "structures_changed": [], "structures_removed": [], "events": [],
		"objectives": [],
		"lots_changed": [[5, 100.0, 200.0, 4, 1, 0], [9, 7.0, 8.0, 1, 3, 0]],
		"economy": {"doctrine": 2, "resources": {}},
	}


func _lot_by_id(rows: Array, id: int) -> Dictionary:
	for r in rows:
		if int(r.get("id", -1)) == id:
			return r
	return {}


func _run_tests() -> void:
	var CBridge = load("res://autoload/c_bridge.gd")
	var b = CBridge.new()

	# control: structures decode unchanged
	var full: Dictionary = b._reconstruct_tactical(_full_frame())
	_assert(full.get("structures", null) is Array and (full["structures"] as Array).size() == 1 and int(full["structures"][0]["id"]) == 4,
		"control: the full view lost its structures")

	# strongpoints and economy ride the full view
	var sp: Variant = full.get("strongpoints", null)
	_assert(sp is Array and (sp as Array).size() == 2, "K-e: the full view has no `strongpoints` Array of 2 rows (keys: %s)" % [full.keys()])
	if sp is Array and (sp as Array).size() == 2:
		_assert(int(sp[0]["id"]) == 1 and int(sp[1]["id"]) == 2 and int(sp[0]["state"]) == 1 and int(sp[1]["owner"]) == -1,
			"K-e: strongpoints are not ascending id with their fields kept: %s" % [sp])
	var eco: Variant = full.get("economy", null)
	_assert(eco is Dictionary and int((eco as Dictionary).get("doctrine", -1)) == 1 and (eco as Dictionary).get("resources", null) is Dictionary,
		"K-e: the view `economy` is not the frame's {doctrine, resources}: %s" % [eco])
	_assert(not full.has("lots_changed"), "K-e: the full view should carry no lots_changed")

	# a delta keeps strongpoints from the last full frame, takes its own economy, folds lots_changed
	var d1: Dictionary = b._reconstruct_tactical(_delta_frame())
	_assert(d1.get("strongpoints", null) is Array and (d1["strongpoints"] as Array).size() == 2, "K-e: strongpoints from the last full frame did not survive the delta")
	_assert(int(d1.get("economy", {}).get("doctrine", -1)) == 2, "K-e: a delta's own economy.doctrine (2) was not used: %s" % [d1.get("economy")])
	_assert(not d1.has("lots_changed"), "K-e: the view still carries lots_changed")
	_assert(d1.get("lots", null) is Array, "K-e: the delta view has no `lots` Array")

	# live path through the stub
	var gs := GDScript.new()
	gs.source_code = STUB_SRC
	_assert(gs.reload() == OK, "the stub bridge script did not compile (control)")
	var f = gs.new()
	f._session_pid = 2147483000
	f._session_args = [1, 10, []]
	_assert(f.has_method("lots"), "K-e: c_bridge.gd has no lots()")
	if not f.has_method("lots"):
		_completed = true
		return
	_assert((f.lots() as Array).is_empty(), "K-e: lots() is not [] before any dump")
	_assert(f.load_mission_live(1, 10, []), "control: load_mission_live through the stub failed")
	_assert(f.count("lots_dump") == 0, "K-e: lots_dump sent before mission_begin")
	_assert(f.begin_mission_live(1, 10, []), "control: begin_mission_live through the stub failed: %s" % f.last_error())
	_assert(f.count("lots_dump") == 1, "K-e: %d lots_dump sent after mission_begin, expected exactly 1" % f.count("lots_dump"))
	var lots: Array = f.lots()
	_assert(lots.size() == 2 and int(lots[0]["id"]) == 2 and int(lots[1]["id"]) == 5, "K-e: lots() not the dump's 2 rows in ascending id: %s" % [lots])
	var l5: Dictionary = _lot_by_id(lots, 5)
	_assert(int(l5.get("stage", -1)) == 3 and int(l5.get("building", -1)) == 1 and int(l5.get("owner", -2)) == 0 and float(l5.get("x", 0.0)) == 100.0 and float(l5.get("y", 0.0)) == 200.0,
		"K-e: the decoded lot 5 differs from row [5,100,200,3,1,0]: %s" % [l5])
	var l2: Dictionary = _lot_by_id(lots, 2)
	_assert(int(l2.get("stage", -1)) == 0 and int(l2.get("owner", 0)) == -1 and float(l2.get("x", 0.0)) == 50.5, "K-e: the decoded lot 2 differs from its row: %s" % [l2])

	# a delta folds in: lot 5 changes stage, lot 9 appears, lot 2 stays
	var v: Dictionary = f._reconstruct_tactical(_full_frame())
	v = f._reconstruct_tactical(_delta_frame())
	var after: Array = f.lots()
	_assert(after.size() == 3 and int(after[0]["id"]) == 2 and int(after[1]["id"]) == 5 and int(after[2]["id"]) == 9, "K-e: lots() after the delta is not ids 2, 5, 9: %s" % [after])
	_assert(int(_lot_by_id(after, 5).get("stage", -1)) == 4 and int(_lot_by_id(after, 2).get("stage", -1)) == 0, "K-e: lots_changed did not overlay by id")
	_assert((v.get("lots", []) as Array).size() == 3, "K-e: the view's `lots` is not the same 3-lot list")

	# not asked again on tactical frames
	_assert(f.load_tactical_live(1, 10, []), "control: load_tactical_live through the stub failed")
	_assert(f.count("lots_dump") == 1, "K-e: lots_dump re-requested on tactical frames (%d)" % f.count("lots_dump"))
	_completed = true
