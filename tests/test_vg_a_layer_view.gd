extends SceneTree

# VG-A piece A3. Proves S-002 (visible half) / R-104-09 (the right sidebar holds the layer strip),
# R-105-03 (Tab cycles focus to the next layer), S-005 (own-layer sensor rings), 0.4 dimming of inactive layers
# (spec A3), rise/drop from tl and ld (section 2). Narrowing (R-105-06) and set_layer wait on Q-232-01: not tested.
# RED because res://scenes/tactical_c/layer_view.gd does not exist.
# Interface (test's choice): layer_view.gd extends Node2D, child "LayerView".
#   set_frame(frame, local_faction, world_scale, camera)     set_focus_layer(n) / focus_layer() -> int
#   cycle_focus()                    Tab: next layer present in the strip, wrapping
#   strip_layers() -> Array of int   ascending, every layer a unit occupies
#   dim_alpha(layer) -> float        1.0 on the focus layer, 0.4 elsewhere
#   transit(id) -> String            "rise" (tl above layer), "drop" (tl below), "" when no tl
#   sensor_ring(id) -> Dictionary | null   {center: Vector2 screen, radius: float px}, own units with `sight` only

const TITLE := "VG-A A3 layer view"
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
	var lv = _mod("res://scenes/tactical_c/layer_view.gd", "A3: S-002 strip, rings, dimming, Tab focus")
	if lv == null:
		return
	if not _need(lv, ["set_frame", "set_focus_layer", "focus_layer", "cycle_focus", "strip_layers", "dim_alpha", "transit", "sensor_ring"]):
		return
	var units := [
		_unit(1, 0, 0, 1500.0, 1500.0, 1, 100.0, {"sight": 800}),
		_unit(2, 0, 1, 1800.0, 1600.0, 2),
		_unit(3, 0, 2, 1900.0, 1700.0, 3),
		_unit(4, 0, 0, 1600.0, 1400.0, 1, 100.0, {"state": 4, "tl": 2, "ld": 130}),
		_unit(5, 0, 0, 1700.0, 1400.0, 3, 100.0, {"state": 4, "tl": 2, "ld": 130}),
		_unit(6, 1, 0, 2400.0, 2400.0, 1, 100.0, {"sight": 900})]
	lv.call("set_frame", _frame(units), 0, SCALE, CAM)
	_assert(lv.call("strip_layers") == [1, 2, 3], "A3: R-104-09 the strip lists the layers in play; got " + str(lv.call("strip_layers")))
	lv.call("set_focus_layer", 2)
	_assert(is_equal_approx(float(lv.call("dim_alpha", 2)), 1.0), "A3: the focused layer is not dimmed")
	_assert(is_equal_approx(float(lv.call("dim_alpha", 1)), 0.4) and is_equal_approx(float(lv.call("dim_alpha", 3)), 0.4), "A3: inactive layers dim to 0.4")
	# R-105-03 Tab
	lv.call("set_focus_layer", 1)
	lv.call("cycle_focus")
	_assert(int(lv.call("focus_layer")) == 2, "A3: R-105-03 Tab moves focus 1 -> 2")
	lv.call("cycle_focus")
	lv.call("cycle_focus")
	_assert(int(lv.call("focus_layer")) == 1, "A3: R-105-03 Tab wraps 3 -> 1")
	# rise / drop
	_assert(lv.call("transit", 4) == "rise" and lv.call("transit", 5) == "drop", "A3: tl above the layer reads rise, below reads drop")
	_assert(lv.call("transit", 1) == "", "A3 CONTROL: a unit with no tl is not in transit")
	# sensor rings: own units with sight only, radius = sight * scale
	var ring = lv.call("sensor_ring", 1)
	_assert(ring != null and absf(float(ring["radius"]) - 800.0 * SCALE) < 0.5, "A3: own sensor ring radius = sight * world_scale (200 px)")
	_assert(lv.call("sensor_ring", 2) == null, "A3 CONTROL: an own unit without sight gets no ring")
	_assert(lv.call("sensor_ring", 6) == null, "A3: sight is own faction only; an enemy gets no ring")
