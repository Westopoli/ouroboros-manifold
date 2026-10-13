extends SceneTree

# VG-A piece A7b. Proves R-105-07 (the Comb): holding a bound group's digit blooms the layer strip into one bar per
# layer the group occupies, sized by unit count; dragging across bars and releasing selects those layers' units;
# releasing the digit collapses the strip. A single-layer group has no comb.
# RED because res://scenes/tactical_c/hud/comb.gd does not exist.
# Interface (test's choice): comb.gd extends Control, child "Comb" of "Hud".
#   open(group_ids, frame) -> bool (false for a single-layer group)    is_open() -> bool
#   bars() -> Array of {layer, count} ascending by layer, empty when closed
#   drag(from_layer, to_layer) -> Array of unit ids on every layer from..to (inclusive)    release() -> void

const TITLE := "VG-A A7b comb"
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
	var c = _mod("res://scenes/tactical_c/hud/comb.gd", "A7b: R-105-07 the Comb")
	if c == null:
		return
	if not _need(c, ["open", "is_open", "bars", "drag", "release"]):
		return
	var units := [_unit(1, 0, 0, 1000.0, 1000.0, 1), _unit(2, 0, 0, 1100.0, 1000.0, 1), _unit(3, 0, 0, 1200.0, 1000.0, 2),
		_unit(4, 0, 0, 1300.0, 1000.0, 3), _unit(5, 0, 0, 1400.0, 1000.0, 3), _unit(6, 0, 0, 1500.0, 1000.0, 3)]
	var f := _frame(units)
	_assert(c.call("open", [1, 2, 3, 4, 5, 6], f), "A7b: a group spanning layers opens the comb")
	var bars: Array = c.call("bars")
	var counts := []
	for b in bars:
		counts.append([int(b["layer"]), int(b["count"])])
	_assert(counts == [[1, 2], [2, 1], [3, 3]], "A7b: R-105-07 one bar per occupied layer, sized by unit count; got " + str(counts))
	var dragged: Array = c.call("drag", 1, 2)
	dragged.sort()
	_assert(dragged == [1, 2, 3], "A7b: dragging across bars 1 and 2 selects those layers' units; got " + str(dragged))
	var one: Array = c.call("drag", 3, 3)
	one.sort()
	_assert(one == [4, 5, 6], "A7b: dragging one bar selects that layer only")
	c.call("release")
	_assert(not c.call("is_open") and (c.call("bars") as Array).is_empty(), "A7b: releasing the digit collapses the strip")
	# CONTROL: a single-layer group has no comb
	_assert(not c.call("open", [1, 2], f), "A7b CONTROL: a group on one layer does not bloom")
