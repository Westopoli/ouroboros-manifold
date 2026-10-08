extends SceneTree

# VG-A piece A2. Proves S-101 / R-101 (units are seen turning and settling) and S-100 (turn rather than snap):
# the client draws between two sim frames, never snapping.
# RED because res://scenes/tactical_c/unit_motion.gd does not exist.
# Interface (test's choice): unit_motion.gd extends Node.
#   push_frame(frame)               the newest sim frame; the previous one becomes the interpolation start
#   position_at(id, alpha) -> Vector2    world position, alpha 0 = previous frame, 1 = newest
#   facing_at(id, alpha) -> float        radians, shortest arc
#   has_unit(id) -> bool

const TITLE := "VG-A A2 unit motion"
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


func _run_tests() -> void:
	var mo = _mod("res://scenes/tactical_c/unit_motion.gd", "A2: S-101 interpolation buffer, no snapping")
	if mo == null:
		return
	if not _need(mo, ["push_frame", "position_at", "facing_at", "has_unit"]):
		return
	mo.call("push_frame", _frame([_unit(1, 0, 0, 1000.0, 1000.0, 1, 100.0, {"facing": 6.2}), _unit(2, 0, 0, 500.0, 500.0)]))
	mo.call("push_frame", _frame([_unit(1, 0, 0, 1100.0, 1040.0, 1, 100.0, {"facing": 0.1}), _unit(3, 1, 0, 2000.0, 2000.0)], {"tick": 101}))
	var a0: Vector2 = mo.call("position_at", 1, 0.0)
	var a1: Vector2 = mo.call("position_at", 1, 1.0)
	var am: Vector2 = mo.call("position_at", 1, 0.5)
	# CONTROL: the ends equal the two frames
	_assert(a0.distance_to(Vector2(1000, 1000)) < 0.01 and a1.distance_to(Vector2(1100, 1040)) < 0.01, "A2 CONTROL: alpha 0 and 1 equal the two sim frames")
	_assert(am.distance_to(Vector2(1050, 1020)) < 0.5, "A2: S-101 alpha 0.5 sits halfway, not snapped to either end; got " + str(am))
	var q: Vector2 = mo.call("position_at", 1, 0.25)
	_assert(q.x > a0.x and q.x < am.x, "A2: positions advance monotonically with alpha")
	# S-100: turn through the short way (6.2 -> 0.1 is a 0.18 rad turn, not a spin back through 3 rad)
	var fm: float = mo.call("facing_at", 1, 0.5)
	var want := 6.2 + angle_difference(6.2, 0.1) * 0.5
	_assert(absf(angle_difference(fm, want)) < 0.05, "A2: S-100 facing interpolates along the shortest arc; got %f" % fm)
	# a unit new in the frame appears where it is (no slide in from the origin); a removed one is gone
	_assert(mo.call("has_unit", 3) and (mo.call("position_at", 3, 0.5) as Vector2).distance_to(Vector2(2000, 2000)) < 0.01, "A2: a new unit appears at its own position, not interpolated from the origin")
	_assert(not mo.call("has_unit", 2), "A2: a unit absent from the newest frame is dropped")
