extends SceneTree

# Visible-game programme lane E1, K-e bridge decode (docs/northstar/plans/2026-10-07-visible-game-spec.md rev 6, lane E1,
# piece E1a; contract text docs/architecture.md "Visible-game economy fields"). Fenced: builders never edit this file.
# Pinned here (K-e's shapes, flagged for the contract text; the spec names the frame fields, not the bridge dicts):
#   * after mission_begin, in every era, the bridge sends ONE lots_dump ({"type":"cmd","name":"lots_dump"}, wants "lots")
#     and exposes lots() -> Array of {id, x, y, stage, building, owner} (ints, floats for x and y), ascending id; [] before
#     any dump. It is not asked again on tactical frames.
#   * a delta's lots_changed rows (same [id,x,y,stage,building,owner] row form) overlay lots() by id (new ids appended in
#     ascending order); lots() never loses a lot to a delta.
#   * K-e6: a full frame's `lots` (same row form) REPLACES the table (the dump's rows are not merged with it); a full frame
#     without a `lots` key leaves the table alone.
#   * _reconstruct_tactical's view carries: `lots` (the same list as lots()), `strongpoints` (Array of {id,x,y,owner,state}
#     from the last full frame, kept across deltas), `economy` (the frame's own {doctrine, resources} dict); the view has
#     no `lots_changed` key.
# "(control)" checks pass on main (structures decode unchanged). On main none of the rest exists: red.
#
# K-e6 (spec rev 11, lane E1 part d; R-193-01, R-193-02): a FULL tactical frame carries `lots`, the complete list in the
# lots_dump row form; _reconstruct_tactical's full branch REPLACES the table from it (not a merge), and the view's `lots` is
# that table; a full frame with no `lots` key leaves the table alone; the delta branch still folds lots_changed by id.
# The K-e6 checks are _run_ke6_tests at the end of this file.

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


func _full_frame(lots: Array = []) -> Dictionary:
	var fr := {
		"type": "tactical", "tick": 20, "full": true, "mission_over": false, "band": -1,
		"units": [], "structures": [STRUCT_A.duplicate()], "events": [], "profiles": [], "objectives": [], "map": {},
		"strongpoints": [SP_A.duplicate(), SP_B.duplicate()],
		"economy": {"doctrine": 1, "resources": {}},
	}
	if not lots.is_empty():
		fr["lots"] = lots  # K-e6; an empty `lots` is built by the K-e6 tests themselves
	return fr


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
	# (K-e6: a full frame WITHOUT a `lots` key leaves this table alone, so the fold below still starts from the dump's two rows)
	var v: Dictionary = f._reconstruct_tactical(_full_frame())
	v = f._reconstruct_tactical(_delta_frame())
	var after: Array = f.lots()
	_assert(after.size() == 3 and int(after[0]["id"]) == 2 and int(after[1]["id"]) == 5 and int(after[2]["id"]) == 9, "K-e: lots() after the delta is not ids 2, 5, 9: %s" % [after])
	_assert(int(_lot_by_id(after, 5).get("stage", -1)) == 4 and int(_lot_by_id(after, 2).get("stage", -1)) == 0, "K-e: lots_changed did not overlay by id")
	_assert((v.get("lots", []) as Array).size() == 3, "K-e: the view's `lots` is not the same 3-lot list")

	# not asked again on tactical frames
	_assert(f.load_tactical_live(1, 10, []), "control: load_tactical_live through the stub failed")
	_assert(f.count("lots_dump") == 1, "K-e: lots_dump re-requested on tactical frames (%d)" % f.count("lots_dump"))

	_run_place_tests(gs)
	_run_ke6_tests(gs)
	_completed = true


# K-e4 (docs/architecture.md, VG-CONTRACT-E4; spec lane E1 part b piece K-e4): send_place, place_result, strongpoints().
# Frames are fed through the queue and pump(), the path the reader thread uses; sends are captured by the stub's send_command.
func _run_place_tests(gs: GDScript) -> void:
	var f = gs.new()
	var seen: Array = []
	var has_sig: bool = f.has_signal("place_result")
	_assert(has_sig, "K-e4: c_bridge.gd has no signal place_result")
	_assert(f.has_method("send_place"), "K-e4: c_bridge.gd has no send_place(x, y, building)")
	_assert(f.has_method("strongpoints"), "K-e4: c_bridge.gd has no strongpoints()")
	if has_sig:
		f.connect("place_result", func(a, x, y, bl): seen.append([a, x, y, bl]))

	# strongpoints(): [] before any frame, then ascending id from the reconstructed view
	if f.has_method("strongpoints"):
		_assert((f.strongpoints() as Array).is_empty(), "K-e4: strongpoints() is not [] before any frame")
		f._reconstruct_tactical(_full_frame())
		var sps: Array = f.strongpoints()
		_assert(sps.size() == 2 and int(sps[0]["id"]) == 1 and int(sps[1]["id"]) == 2 and int(sps[0]["state"]) == 1,
			"K-e4: strongpoints() is not the view's 2 strongpoints ascending by id: %s" % [sps])
		f._reconstruct_tactical(_delta_frame())
		_assert((f.strongpoints() as Array).size() == 2, "K-e4: strongpoints() lost its rows across a delta")
	else:
		_assert(false, "K-e4: strongpoints() positive control cannot run without the method")

	# control: a move command still sends its frame and an ack for it emits no place_result
	f.sent.clear()
	_assert(f.send_unit_command({"kind": "move", "unit_ids": [1], "x": 10.0, "y": 20.0}), "control: send_unit_command(move) returned false")
	_assert(f.sent.size() == 1 and String(f.sent[0].get("verb", "")) == "move", "control: the move frame was not sent: %s" % [f.sent])
	f._queue.append({"type": "ack", "name": "command", "tick": 5})
	f.pump()
	_assert(seen.is_empty(), "K-e4: a move's ack emitted place_result: %s" % [seen])

	if not f.has_method("send_place"):
		_assert(false, "K-e4: the place checks cannot run without send_place")
		return

	# accepted: exact frame, true return, no result until the ack, then place_result(true, x, y, building)
	f.sent.clear()
	var ok: bool = f.send_place(1200.0, 800.0, 3)
	_assert(ok, "K-e4: send_place returned false")
	_assert(f.sent.size() == 1, "K-e4: send_place wrote %d frames, expected 1" % f.sent.size())
	if f.sent.size() == 1:
		var fr: Dictionary = f.sent[0]
		_assert(String(fr.get("type", "")) == "cmd" and String(fr.get("name", "")) == "command" and String(fr.get("verb", "")) == "place"
			and (fr.get("units", null) is Array) and (fr["units"] as Array).is_empty()
			and float(fr.get("x", -1.0)) == 1200.0 and float(fr.get("y", -1.0)) == 800.0 and int(fr.get("building", -1)) == 3,
			"K-e4: the place frame is not {cmd, command, verb place, units [], x 1200, y 800, building 3}: %s" % [fr])
	f.pump()
	_assert(seen.is_empty(), "K-e4: place_result emitted before any answer: %s" % [seen])
	f._queue.append({"type": "ack", "name": "command", "tick": 6})
	f.pump()
	_assert(seen.size() == 1 and bool(seen[0][0]) == true and float(seen[0][1]) == 1200.0 and float(seen[0][2]) == 800.0 and int(seen[0][3]) == 3,
		"K-e4: the ack did not emit place_result(true, 1200, 800, 3): %s" % [seen])
	f._queue.append({"type": "ack", "name": "command", "tick": 7})
	f.pump()
	_assert(seen.size() == 1, "K-e4: a later ack re-emitted place_result (no place pending): %s" % [seen])

	# refused: an error frame named command while pending
	f.sent.clear()
	seen.clear()
	_assert(f.send_place(5.0, 6.0, 0), "K-e4: second send_place returned false")
	f._queue.append({"type": "error", "name": "command", "reason": "command failed"})
	f.pump()
	_assert(seen.size() == 1 and bool(seen[0][0]) == false and float(seen[0][1]) == 5.0 and float(seen[0][2]) == 6.0 and int(seen[0][3]) == 0,
		"K-e4: the error did not emit place_result(false, 5, 6, 0): %s" % [seen])
	_assert(f.last_error() == "command failed", "K-e4: last_error() is not the refusal reason: '%s'" % f.last_error())

	# control: an error for another verb with no place pending emits nothing
	seen.clear()
	f._queue.append({"type": "error", "name": "command", "reason": "command failed"})
	f.pump()
	_assert(seen.is_empty(), "K-e4: an error with no place pending emitted place_result: %s" % [seen])


# K-e6 (VG-CONTRACT-E6; R-193-01, R-193-02): full frames carry `lots` and replace the table; deltas still fold.
func _run_ke6_tests(gs: GDScript) -> void:
	# control (green on the K-e5 tree): after the dump (lots 2 and 5), a delta alone still folds lots_changed by id
	var c = gs.new()
	c._session_pid = 2147483000
	c._session_args = [1, 10, []]
	_assert(c.load_mission_live(1, 10, []) and c.begin_mission_live(1, 10, []), "control: begin_mission_live through the stub failed")
	c._reconstruct_tactical(_delta_frame())
	var cl: Array = c.lots()
	_assert(cl.size() == 3 and int(cl[0]["id"]) == 2 and int(cl[1]["id"]) == 5 and int(cl[2]["id"]) == 9 and int(_lot_by_id(cl, 5).get("stage", -1)) == 4,
		"control: a delta no longer folds lots_changed into the dump's table (ids 2, 5, 9, lot 5 stage 4): %s" % [cl])

	# control (green on the K-e5 tree and after): a full frame WITHOUT the `lots` key leaves the dump's table alone
	var k = gs.new()
	k._session_pid = 2147483000
	k._session_args = [1, 10, []]
	_assert(k.load_mission_live(1, 10, []) and k.begin_mission_live(1, 10, []), "control: begin_mission_live through the stub failed")
	var kv: Dictionary = k._reconstruct_tactical(_full_frame())
	var kids: Array = []
	for l in k.lots():
		kids.append(int(l["id"]))
	_assert(kids == [2, 5] and (kv.get("lots", []) as Array).size() == 2, "control: a full frame without `lots` changed the table (ids 2, 5 expected): %s" % [kids])

	# a full frame with three rows replaces the two-row table: ids 2 and 5 are gone, ids 3, 7, 8 are in, ascending
	var f = gs.new()
	f._session_pid = 2147483000
	f._session_args = [1, 10, []]
	_assert(f.load_mission_live(1, 10, []) and f.begin_mission_live(1, 10, []), "control: begin_mission_live through the stub failed")
	_assert((f.lots() as Array).size() == 2, "control: the dump's table should hold 2 rows before the full frame")
	var rows := [[3, 30.0, 31.0, 1, 0, -1], [7, 70.0, 71.0, 2, 4, 0], [8, 80.0, 81.0, 5, 2, 1]]
	var v: Dictionary = f._reconstruct_tactical(_full_frame(rows))
	var lots: Array = f.lots()
	var ids: Array = []
	for l in lots:
		ids.append(int(l["id"]))
	_assert(ids == [3, 7, 8], "K-e6 R-193-01: a full frame with `lots` rows 3, 7, 8 must replace the table (ids 2, 5 gone), got ids %s" % [ids])
	var l7: Dictionary = _lot_by_id(lots, 7)
	_assert(int(l7.get("stage", -1)) == 2 and int(l7.get("building", -1)) == 4 and int(l7.get("owner", -2)) == 0 and float(l7.get("x", 0.0)) == 70.0 and float(l7.get("y", 0.0)) == 71.0,
		"K-e6 R-193-01: the decoded lot 7 differs from row [7,70,71,2,4,0]: %s" % [l7])
	var vl: Variant = v.get("lots", null)
	var vids: Array = []
	if vl is Array:
		for l in vl:
			vids.append(int(l["id"]))
	_assert(vids == [3, 7, 8], "K-e6 R-193-02: the full view's `lots` is not the frame's rows 3, 7, 8, got ids %s" % [vids])
	var tl: Variant = f.tactical_frame().get("lots", null)
	_assert(tl is Array and (tl as Array).size() == 3, "K-e6 R-193-02: tactical_frame()[\"lots\"] is not the replaced 3-row table: %s" % [tl])
	_assert(not v.has("lots_changed"), "K-e6: the full view should carry no lots_changed")

	# a delta after that full frame folds into the replaced table (lot 7 changes, lot 11 appears)
	var d: Dictionary = _delta_frame()
	d["lots_changed"] = [[7, 70.0, 71.0, 3, 4, 0], [11, 5.0, 6.0, 0, 1, 0]]
	f._reconstruct_tactical(d)
	var after: Array = f.lots()
	var aids: Array = []
	for l in after:
		aids.append(int(l["id"]))
	_assert(aids == [3, 7, 8, 11] and int(_lot_by_id(after, 7).get("stage", -1)) == 3, "K-e6: the delta after the full frame did not fold into ids 3, 7, 8, 11 (lot 7 stage 3): %s" % [aids])

	# the next full frame replaces again, down to none: `lots` [] empties the table
	var empty: Dictionary = _full_frame()
	empty["lots"] = []
	f._reconstruct_tactical(empty)
	_assert((f.lots() as Array).is_empty(), "K-e6 R-193-01: a full frame with `lots` [] must empty the table, got %d rows" % (f.lots() as Array).size())
