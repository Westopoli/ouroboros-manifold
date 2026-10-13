extends SceneTree

# VG-A piece A13 (reinforcements panel). Proves R-104-06 / R-126-05: one row per owned structure with the production
# timer bar, the next unit icon and structure HP; neutral and enemy structures do not appear.
# section 2 structures: nst = the next spawn tick, period = ticks between spawns, next_type the next unit type.
# RED because res://scenes/tactical_c/hud/reinforcements.gd does not exist.
# Interface (test's choice): reinforcements.gd extends Control, child "Reinforcements" of "Hud".
#   set_frame(frame, local_faction)    apply_delta(delta, tick)
#   rows() -> Array of {id, next_type: int, timer: float 0..1 (elapsed share of the period), hp: float}

const TITLE := "VG-A A13 reinforcements"
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


func _structs() -> Array:
	return [
		{"id": 1, "type": 0, "owner": 0, "x": 1500.0, "y": 1500.0, "hp": 800.0, "stage": 0, "cap": 0, "nst": 150, "next_type": 1, "period": 100},
		{"id": 2, "type": 0, "owner": 1, "x": 2400.0, "y": 2400.0, "hp": 800.0, "stage": 0, "cap": 400, "nst": 160, "next_type": 2, "period": 200},
		{"id": 3, "type": 0, "owner": -1, "x": 1800.0, "y": 1900.0, "hp": 800.0, "stage": 0, "cap": 0, "nst": 0, "next_type": -1, "period": 0}]


func _run_tests() -> void:
	var rp = _mod("res://scenes/tactical_c/hud/reinforcements.gd", "A13: R-104-06 reinforcement rows")
	if rp == null:
		return
	if not _need(rp, ["set_frame", "apply_delta", "rows"]):
		return
	rp.call("set_frame", _frame([_unit(9, 0, 0, 1000.0, 1000.0)], {"structures": _structs(), "tick": 100}), 0)
	var rows: Array = rp.call("rows")
	_assert(rows.size() == 1, "A13: R-104-06 only owned structures get a row (1 of 3); got %d" % rows.size())
	if rows.size() == 1:
		_assert(int(rows[0]["id"]) == 1 and int(rows[0]["next_type"]) == 1, "A13: the row shows the next unit type")
		_assert(absf(float(rows[0]["timer"]) - 0.5) < 0.001, "A13: timer = 1 - (nst - tick) / period = 0.5 at tick 100; got %f" % float(rows[0]["timer"]))
		_assert(float(rows[0]["hp"]) > 0.0, "A13: the row shows structure HP")
	rp.call("apply_delta", {"structures_changed": [{"id": 2, "owner": 0}]}, 110)
	_assert((rp.call("rows") as Array).size() == 2, "A13: a captured structure gains a row")
	rp.call("apply_delta", {"structures_changed": [{"id": 1, "owner": 1}]}, 111)
	_assert((rp.call("rows") as Array).size() == 1, "A13: a lost structure loses its row")
