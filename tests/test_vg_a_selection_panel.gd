extends SceneTree

# VG-A piece A7. Proves S-105 (click, box-select, bind groups, never an all-army button), R-104-04 (summed HP, one
# ability slot per unit type with a cooldown ring), R-104-07 (groups 1 through 0 show type and count), R-105-02
# (Ctrl+digit binds exclusively, digit recalls, twice centres the camera), R-105-04 (no select-all), double-click
# selects the same type. section 2: profiles[{max_hp,acd_max}], unit acd = the tick the ability is ready.
# RED because res://scenes/tactical_c/hud/selection_panel.gd does not exist.
# Interface (test's choice): selection_panel.gd extends Control, child "Selection" of "Hud".
#   set_frame(frame)     set_selection(ids)     summary() -> Array of {type, count}
#   hp_fraction() -> float (sum hp / sum max_hp)    ability_slots() -> Array of {type, cooldown: float 0 ready .. 1 just used}
#   bind_group(n, ids)   group(n) -> Array (n 1..10, the digit 0 is group 10)   group_tabs() -> Array of {n, type, count}
#   press_digit(n, t_ms) -> {selection: Array, centre: Vector2 | null}   centre is the group's world centroid on a second press
#   select_same_type(id) -> Array    double-click: every own visible unit of that type

const TITLE := "VG-A A7 selection panel"
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
	var sp = _mod("res://scenes/tactical_c/hud/selection_panel.gd", "A7: S-105 selection summary, ability ring, groups")
	if sp == null:
		return
	if not _need(sp, ["set_frame", "set_selection", "summary", "hp_fraction", "ability_slots", "bind_group", "group", "group_tabs", "press_digit", "select_same_type"]):
		return
	var units := [
		_unit(1, 0, 0, 1000.0, 1000.0, 1, 100.0),
		_unit(2, 0, 0, 1200.0, 1000.0, 1, 50.0),
		_unit(3, 0, 2, 1000.0, 1400.0, 1, 50.0, {"acd": 175}),
		_unit(4, 1, 0, 2400.0, 2400.0)]
	sp.call("set_frame", _frame(units))
	sp.call("set_selection", [1, 2, 3])
	var sm: Array = sp.call("summary")
	var by := {}
	for s in sm:
		by[int(s["type"])] = int(s["count"])
	_assert(by.get(0, 0) == 2 and by.get(2, 0) == 1 and sm.size() == 2, "A7: R-104-04 the summary is type x count; got " + str(sm))
	_assert(absf(float(sp.call("hp_fraction")) - 200.0 / 300.0) < 0.001, "A7: R-104-04 summed HP = sum hp / sum profile max_hp")
	sp.call("set_selection", [3])
	var slots: Array = sp.call("ability_slots")
	_assert(slots.size() == 1 and absf(float(slots[0]["cooldown"]) - 0.75) < 0.001, "A7: the ability ring shows (acd - tick) / acd_max = 0.75; got " + str(slots))
	sp.call("set_selection", [2])
	_assert(absf(float((sp.call("ability_slots") as Array)[0]["cooldown"])) < 0.001, "A7 CONTROL: a unit with no acd reads ready (cooldown 0)")
	# groups: exclusive membership
	sp.call("bind_group", 1, [1, 2])
	sp.call("bind_group", 2, [2, 3])
	_assert(sp.call("group", 1) == [1] and (sp.call("group", 2) as Array).size() == 2, "A7: R-105-02 binding a unit to a second group takes it out of the first")
	sp.call("bind_group", 10, [3])
	_assert(sp.call("group", 10) == [3] and sp.call("group", 2) == [2], "A7: R-105-02 the digit 0 is group 10 and is exclusive too")
	var tabs: Array = sp.call("group_tabs")
	var seen := {}
	for t in tabs:
		seen[int(t["n"])] = t
	_assert(seen.has(1) and seen.has(2) and seen.has(10) and not seen.has(3), "A7: R-104-07 only the bound groups have tabs")
	if seen.has(1):
		_assert(int(seen[1]["count"]) == 1 and int(seen[1]["type"]) == 0, "A7: R-104-07 a tab shows its unit type and count")
	# recall and double press
	var one: Dictionary = sp.call("press_digit", 1, 0)
	_assert(one["selection"] == [1] and one["centre"] == null, "A7: R-105-02 one press recalls the group and does not move the camera")
	var two: Dictionary = sp.call("press_digit", 1, 100)
	_assert(two["centre"] is Vector2 and (two["centre"] as Vector2).distance_to(Vector2(1000, 1000)) < 0.5, "A7: R-105-02 pressing twice centres the camera on the group")
	# double-click selects the same type
	var same: Array = sp.call("select_same_type", 1)
	same.sort()
	_assert(same == [1, 2], "A7: double-click selects every visible own unit of that type (not the enemy of that type); got " + str(same))
	# R-105-04 control: there is no select-all anywhere
	_assert(not sp.has_method("select_all") and not sp.has_method("select_all_army"), "A7 CONTROL: R-105-04 the panel has no select-all")
