extends SceneTree

# VG-A piece A1 (docs/northstar/plans/2026-10-07-visible-game-spec.md rev 4, lane A table).
# Proves S-104 / R-104-10 (every unit: thin HP bar above, layer-colour ring beneath, selection ring
# when selected), S-132 / R-132-01 (six type shapes), R-089-03 (a hidden enemy: no node, no HP bar).
# RED because res://scenes/tactical_c/unit_visuals.gd does not exist (main draws one square per unit).
# Interface (test's choice, extends push/tv-read's test_tactical_readability.gd; the builder matches it):
#   unit_visuals.gd  extends Node2D, child "UnitVisuals" of the view
#     set_frame(frame, local_faction, world_scale, camera)   one node per unit the local faction sees
#     unit_node(id) -> Node2D | null     position = screen px      unit_polygon(id) -> PackedVector2Array
#     unit_color(id) -> Color            faction colour            unit_facing(id) -> float (radians)
#     hp_bar(id) -> Node2D | null        local position.y < 0       hp_fraction(id) -> float (hp / profile max_hp)
#     layer_ring(id) -> Node2D | null    local position.y > 0       layer_ring_color(id) -> Color
#     set_selected(ids) / selection_ring(id) -> Node2D | null
# Positive controls: marked CONTROL below. Scale per type comes from the manifest (no number given): not asserted.

const TITLE := "VG-A A1 unit visuals"
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
	var uv = _mod("res://scenes/tactical_c/unit_visuals.gd", "A1: S-104 R-104-10, six shapes, bars and rings")
	if uv == null:
		return
	if not _need(uv, ["set_frame", "unit_node", "unit_polygon", "unit_color", "unit_facing", "hp_bar", "hp_fraction",
			"layer_ring", "layer_ring_color", "set_selected", "selection_ring"]):
		return
	var units := []
	for t in range(6):
		units.append(_unit(10 + t, 0, t, 1000.0 + 200.0 * t, 1500.0, 1, 100.0, {"facing": 0.5}))
	units.append(_unit(20, 1, 0, 2400.0, 2400.0))
	units.append(_unit(21, 1, 0, 3000.0, 3000.0))
	units.append(_unit(22, 0, 0, 1500.0, 1800.0, 3, 50.0, {"facing": 1.25}))
	uv.call("set_frame", _frame(units, {}, [21]), 0, SCALE, CAM)
	# R-132-01: six types, six distinct polygons
	var polys := []
	for t in range(6):
		var p: PackedVector2Array = uv.call("unit_polygon", 10 + t)
		_assert(p.size() >= 3, "A1: type %d has no polygon shape (R-132-01)" % t)
		polys.append(p)
	for i in range(6):
		for j in range(i + 1, 6):
			_assert(polys[i] != polys[j], "A1: types %d and %d share one shape (R-132-01 six shapes)" % [i, j])
	# position, facing, faction colour
	var n10: Node2D = uv.call("unit_node", 10)
	_assert(n10 != null and n10.position.distance_to(_scr(Vector2(1000, 1500))) < 0.5, "A1: the node sits at the unit's screen position")
	_assert(absf(float(uv.call("unit_facing", 22)) - 1.25) < 0.01, "A1: the shape faces unit.facing (S-100)")
	_assert(uv.call("unit_color", 10) != uv.call("unit_color", 20), "A1: own and enemy units differ in faction colour")
	_assert(uv.call("unit_color", 10) == uv.call("unit_color", 11), "A1: same faction, same colour whatever the type")
	# R-104-10 chrome: HP bar above, layer ring beneath
	var hb: Node2D = uv.call("hp_bar", 10)
	var lr: Node2D = uv.call("layer_ring", 10)
	_assert(hb != null and hb.position.y < 0.0, "A1: R-104-10 a thin HP bar sits above the unit (local y < 0)")
	_assert(lr != null and lr.position.y > 0.0, "A1: R-104-10 a layer-colour ring sits beneath the unit (local y > 0)")
	_assert(uv.call("layer_ring_color", 10) != uv.call("layer_ring_color", 22), "A1: layer 1 and layer 3 rings differ in colour")
	_assert(absf(float(uv.call("hp_fraction", 22)) - 0.5) < 0.001, "A1: HP bar fraction = hp / profiles max_hp (50/100)")
	# CONTROL: a visible enemy is drawn, a hidden one gets no node and no HP bar (R-089-03)
	_assert(uv.call("unit_node", 20) != null, "A1 CONTROL: the visible enemy is drawn")
	_assert(uv.call("unit_node", 21) == null and uv.call("hp_bar", 21) == null, "A1 R-089-03: a hidden enemy has no node and no HP bar")
	# selection ring
	uv.call("set_selected", [10, 11])
	_assert(uv.call("selection_ring", 10) != null and uv.call("selection_ring", 11) != null, "A1: R-104-10 selected units carry a selection ring")
	_assert(uv.call("selection_ring", 12) == null, "A1 CONTROL: an unselected unit has no selection ring")
	uv.call("set_selected", [11])
	_assert(uv.call("selection_ring", 10) == null, "A1 CONTROL: deselecting removes the ring")
