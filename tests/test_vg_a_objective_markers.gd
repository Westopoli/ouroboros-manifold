extends SceneTree

# VG-A piece A5b. Proves S-075 (one primary objective I can see progressing, up to three secondary ones): the world
# shows beacons at objective nodes, a hold/clear ring of the objective radius, and done/failed states.
# section 2 objectives[{i,progress,done}] done 0 open 1 complete 2 failed; mission frame objectives[{i,kind,node,primary,radius}].
# RED because res://scenes/tactical_c/objective_markers.gd does not exist.
# Interface (test's choice): objective_markers.gd extends Node2D, child "ObjectiveMarkers".
#   set_frame(frame, mission, local_faction, world_scale, camera)
#   beacons() -> Array of {objective: int, center: Vector2 screen, state: int (= done), color: Color}
#   rings() -> Array of {objective: int, center: Vector2, radius: float px (= radius * world_scale)}

const TITLE := "VG-A A5b objective markers"
var _pass_count := 0
var _fail_count := 0
var _fail_msgs: Array[String] = []

const VIEW := "res://scenes/tactical_c/tactical_view.tscn"
const SCALE := 0.25
const CAM := Vector2(2000, 2000)


func _initialize() -> void:
	await _run_tests()
	print("\n=== %s Results ===" % TITLE)
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


# Section 2 unit object: {id,faction,type,tier,x,y,hp,layer,facing,target,state,acd?,tl?,ld?,sight?}
func _unit(id: int, faction: int, type: int, x: float, y: float, layer: int = 1, hp: float = 100.0, extra: Dictionary = {}) -> Dictionary:
	var u := {"id": id, "faction": faction, "type": type, "tier": 0, "x": x, "y": y, "hp": hp,
		"layer": layer, "facing": 0.0, "target": -1, "state": 0}
	u.merge(extra, true)
	return u


# Section 2 profiles: [{type,max_hp,range,interval,sensor,ability,acd_max,aoe}], six types.
func _profiles() -> Array:
	var out := []
	for t in range(6):
		out.append({"type": t, "max_hp": 100.0, "range": 600.0, "interval": 10, "sensor": 800.0,
			"ability": t, "acd_max": 100, "aoe": 600.0 if t == 3 else 0.0})
	return out


# A tactical full frame; `hidden` ids are left out of faction 0's visible set.
func _frame(units: Array, extra: Dictionary = {}, hidden: Array = []) -> Dictionary:
	var vis0 := []
	var vis1 := []
	for u in units:
		if int(u["id"]) in hidden:
			continue
		vis0.append(int(u["id"]))
		if int(u["faction"]) == 1:
			vis1.append(int(u["id"]))
	var f := {"type": "tactical", "tick": 100, "player_faction": 0, "units": units,
		"visible": {"0": vis0, "1": vis1}, "profiles": _profiles(), "events": [], "structures": [],
		"objectives": []}
	f.merge(extra, true)
	return f


func _scr(w: Vector2) -> Vector2:
	return (w - CAM) * SCALE + Vector2(960, 540)


# Loads a piece's script and instantiates it under the root; null (and one red) when the file is missing.
func _mod(path: String, why: String) -> Node:
	var s = load(path)
	_assert(s != null, "%s does not exist (%s)" % [path, why])
	if s == null:
		return null
	var n = s.new()
	get_root().add_child(n)
	return n


func _need(m: Object, names: Array) -> bool:
	var ok := true
	for n in names:
		if not m.has_method(n):
			_assert(false, "%s lacks method %s" % [m.get_script().resource_path, n])
			ok = false
	return ok


# The live view, automatic stepping off (the pattern of tests/test_tactical_view.gd).
func _view() -> Node:
	var p = load(VIEW)
	var v: Node = p.instantiate()
	get_root().add_child(v)
	await process_frame
	v.set_process(false)
	await process_frame
	return v


# The section 2 inventory: qa_state()["inventory"] when present, else the qa_state itself.
func _inv(st: Dictionary) -> Dictionary:
	var i = st.get("inventory")
	return i if i is Dictionary else st


func _inv_has(inv: Dictionary, key: String) -> bool:
	if inv.has(key):
		return true
	var cur = inv
	for p in key.split("."):
		if cur is Dictionary and cur.has(p):
			cur = cur[p]
		else:
			return false
	return true


func _inv_val(inv: Dictionary, key: String) -> Variant:
	if inv.has(key):
		return inv[key]
	var cur = inv
	for p in key.split("."):
		if cur is Dictionary and cur.has(p):
			cur = cur[p]
		else:
			return null
	return cur


# A count however the inventory spells it: number, bool, list or dict.
func _count(v: Variant) -> int:
	if v is bool:
		return 1 if v else 0
	if v is Array or v is Dictionary:
		return v.size()
	if v is int or v is float:
		return int(v)
	return 0


func _bbox(poly: PackedVector2Array) -> Rect2:
	var r := Rect2(poly[0], Vector2.ZERO)
	for p in poly:
		r = r.expand(p)
	return r


func _map_frame() -> Dictionary:
	return _frame([_unit(1, 0, 0, 1500.0, 1500.0)], {"map": {"canvas": 4000.0,
		"nodes": [{"i": 0, "kind": 0, "x": 1000.0, "y": 1000.0}, {"i": 1, "kind": 1, "x": 3000.0, "y": 2800.0}],
		"cover": [{"x": 2000.0, "y": 2000.0, "r": 100.0, "h": 30.0, "class": 0},
			{"x": 2600.0, "y": 1200.0, "r": 300.0, "h": 60.0, "class": 1},
			{"x": 1200.0, "y": 3000.0, "r": 600.0, "h": 90.0, "class": 2}],
		"obstacles": [{"x": 2500.0, "y": 1500.0, "r": 100.0}]}})


func _mission() -> Dictionary:
	return {"type": "mission", "objectives": [
		{"i": 0, "kind": 1, "node": 0, "primary": true, "radius": 300.0},
		{"i": 1, "kind": 2, "node": 1, "primary": false, "radius": 200.0}]}


func _with_done(d0: int, d1: int) -> Dictionary:
	var f := _map_frame()
	f["objectives"] = [{"i": 0, "progress": 0.4, "done": d0}, {"i": 1, "progress": 1.0 if d1 == 1 else 0.2, "done": d1}]
	return f


func _color_of(om: Node, d0: int, d1: int, obj: int) -> Variant:
	om.call("set_frame", _with_done(d0, d1), _mission(), 0, SCALE, CAM)
	for b in om.call("beacons"):
		if int(b["objective"]) == obj:
			return b["color"]
	return null


func _run_tests() -> void:
	var om = _mod("res://scenes/tactical_c/objective_markers.gd", "A5b: S-075 beacons, done/failed, hold/clear rings")
	if om == null:
		return
	if not _need(om, ["set_frame", "beacons", "rings"]):
		return
	om.call("set_frame", _with_done(0, 0), _mission(), 0, SCALE, CAM)
	var bs: Array = om.call("beacons")
	_assert(bs.size() == 2, "A5b: one beacon per objective (2); got %d" % bs.size())
	for b in bs:
		var node_world := Vector2(1000, 1000) if int(b["objective"]) == 0 else Vector2(3000, 2800)
		_assert((b["center"] as Vector2).distance_to(_scr(node_world)) < 0.5, "A5b: beacon %d sits on its map node" % int(b["objective"]))
		_assert(int(b["state"]) == 0, "A5b CONTROL: an open objective reads state 0")
	for r in om.call("rings"):
		var want := (300.0 if int(r["objective"]) == 0 else 200.0) * SCALE
		_assert(absf(float(r["radius"]) - want) < 0.5, "A5b: hold/clear ring %d has the objective radius in px (%f); got %f" % [int(r["objective"]), want, float(r["radius"])])
	var open_c = _color_of(om, 0, 0, 1)
	var done_c = _color_of(om, 0, 1, 1)
	var fail_c = _color_of(om, 0, 2, 1)
	_assert(open_c != null and open_c != done_c and done_c != fail_c and open_c != fail_c, "A5b: S-075 open, complete and failed beacons read differently")
	om.call("set_frame", _with_done(0, 1), _mission(), 0, SCALE, CAM)
	var st := {}
	for b in om.call("beacons"):
		st[int(b["objective"])] = int(b["state"])
	_assert(st.get(1, -1) == 1 and st.get(0, -1) == 0, "A5b: a complete objective reads state 1 and leaves the other open")
