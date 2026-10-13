extends SceneTree

# VG-A piece A1b. Proves S-132 / R-132-03 (a Strike unit is 3 to 5 small models moving as one).
# RED because res://scenes/tactical_c/unit_squads.gd does not exist.
# Interface (test's choice): unit_squads.gd extends Node2D, child "UnitSquads".
#   set_frame(frame, local_faction, world_scale, camera)
#   squad_models(id) -> Array of Vector2 (local offsets, px); empty for an unmarked type or a hidden unit
# Which types are marked comes from the manifest (not given): the test asks which of the six answer non-empty.

const TITLE := "VG-A A1b unit squads"
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


func _models(sq: Node, frame: Dictionary, id: int) -> Array:
	sq.call("set_frame", frame, 0, SCALE, CAM)
	return sq.call("squad_models", id)


func _run_tests() -> void:
	var sq = _mod("res://scenes/tactical_c/unit_squads.gd", "A1b: S-132 R-132-03, 3 to 5 models per marked type")
	if sq == null:
		return
	if not _need(sq, ["set_frame", "squad_models"]):
		return
	var units := []
	for t in range(6):
		units.append(_unit(10 + t, 0, t, 1000.0 + 200.0 * t, 1500.0))
	units.append(_unit(30, 1, 0, 2400.0, 2400.0))
	units.append(_unit(31, 1, 0, 3000.0, 3000.0))
	var f := _frame(units, {}, [31])
	var marked := 0
	for t in range(6):
		var m: Array = _models(sq, f, 10 + t)
		if m.is_empty():
			continue
		marked += 1
		_assert(m.size() >= 3 and m.size() <= 5, "A1b: R-132-03 type %d squad has %d models, expected 3 to 5" % [t, m.size()])
		var distinct := {}
		for o in m:
			distinct[o] = true
		_assert(distinct.size() == m.size(), "A1b: type %d squad models stand at distinct offsets" % t)
		_assert(m == _models(sq, f, 10 + t), "A1b: the same frame gives the same offsets (no random jitter)")
		# moving as one: the unit moves, the offsets stay
		var moved := _frame(units.duplicate(true), {}, [31])
		moved["units"][t]["x"] = float(moved["units"][t]["x"]) + 300.0
		_assert(m == _models(sq, moved, 10 + t), "A1b: R-132-03 the models keep their offsets when the unit moves")
	_assert(marked >= 1, "A1b: at least one of the six types is marked as a squad type (R-132-03)")
	# CONTROL: a hidden enemy draws no models (R-089-03)
	_assert(_models(sq, f, 31).is_empty(), "A1b CONTROL: a hidden enemy has no squad models")
