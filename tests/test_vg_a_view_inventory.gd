extends SceneTree

# VG-A piece A12. Proves the element inventory of docs/northstar/plans/2026-10-07-visible-game-spec.md section 2 on the
# real view: tactical_view.tscn instantiates A1..A15 under the node names UnitVisuals, UnitSquads, MapLayer, ObjectiveMarkers,
# FogLayer, LayerView, StructuresLayer, Hud/{Objectives,Selection,Comb,Events,Reinforcements,Strip,Clock},
# Fx/{Shots,Deaths,Abilities,Ambient}, LoadingOverlay; and qa_state() carries the inventory keys fog_layer, objective_markers,
# cover_cells, obstacles, structures, shots_in_flight, wrecks, squads, abilities_fx, ambient, loading_overlay,
# hud.{clock,objectives,selection,events,strip,comb,reinforcements}. Row 11 of the rulebook: the old keys stay (SUP).
# Inventory placement is read tolerantly: qa_state()["inventory"][key] or qa_state()[key]; "hud.clock" flat or nested.
# RED because the view has none of these nodes or keys (main draws one square per unit).

const TITLE := "VG-A A12 view inventory"
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


const NODES := ["UnitVisuals", "UnitSquads", "MapLayer", "ObjectiveMarkers", "FogLayer", "LayerView", "StructuresLayer", "LoadingOverlay"]
const HUD := ["Objectives", "Selection", "Comb", "Events", "Reinforcements", "Strip", "Clock"]
const FX := ["Shots", "Deaths", "Abilities", "Ambient"]
const KEYS := ["fog_layer", "objective_markers", "cover_cells", "obstacles", "structures", "shots_in_flight", "wrecks", "squads",
	"abilities_fx", "ambient", "loading_overlay", "hud.clock", "hud.objectives", "hud.selection", "hud.events", "hud.strip",
	"hud.comb", "hud.reinforcements"]


func _run_tests() -> void:
	var v: Node = await _view()
	var st: Dictionary = v.call("qa_state")
	# CONTROL (rulebook row 11): the keys main already has stay
	for k in ["scene", "tick", "plants", "unit_count", "units", "units_px", "selected", "camera"]:
		_assert(st.has(k), "A12 CONTROL: qa_state keeps %s (rulebook row 11, SUP)" % k)
	for n in NODES:
		_assert(v.find_child(n, true, false) != null, "A12: node %s is missing from the view (section 2 node names)" % n)
	var hud := v.find_child("Hud", true, false)
	_assert(hud != null, "A12: node Hud is missing")
	for n in HUD:
		_assert(hud != null and hud.find_child(n, true, false) != null, "A12: node Hud/%s is missing" % n)
	var fx := v.find_child("Fx", true, false)
	_assert(fx != null, "A12: node Fx is missing")
	for n in FX:
		_assert(fx != null and fx.find_child(n, true, false) != null, "A12: node Fx/%s is missing" % n)
	var inv := _inv(st)
	for k in KEYS:
		_assert(_inv_has(inv, k), "A12: qa_state inventory lacks %s" % k)
	# values on a fixture frame: 2 own units with sight, 3 structures, 3 cover, 1 obstacle
	var f := _frame([_unit(1, 0, 0, 1500.0, 1500.0, 1, 100.0, {"sight": 800}), _unit(2, 0, 0, 1800.0, 1600.0, 1, 100.0, {"sight": 400}), _unit(3, 1, 0, 2400.0, 2400.0)], {
		"structures": [{"id": 1, "type": 0, "owner": 0, "x": 1500.0, "y": 1500.0, "hp": 800.0, "stage": 0, "cap": 0, "nst": 150, "next_type": 1, "period": 100},
			{"id": 2, "type": 0, "owner": 1, "x": 2400.0, "y": 2400.0, "hp": 800.0, "stage": 0, "cap": 0, "nst": 160, "next_type": 2, "period": 200}],
		"map": {"canvas": 4000.0, "nodes": [],
			"cover": [{"x": 2000.0, "y": 2000.0, "r": 100.0, "h": 30.0, "class": 0}, {"x": 2600.0, "y": 1200.0, "r": 300.0, "h": 60.0, "class": 1},
				{"x": 1200.0, "y": 3000.0, "r": 600.0, "h": 90.0, "class": 2}],
			"obstacles": [{"x": 2500.0, "y": 1500.0, "r": 100.0}]}})
	v.call("load_frame", f)
	await process_frame
	inv = _inv(v.call("qa_state"))
	_assert(_count(_inv_val(inv, "fog_layer")) == 2, "A12: fog_layer counts the 2 sight discs; got " + str(_inv_val(inv, "fog_layer")))
	_assert(_count(_inv_val(inv, "structures")) == 2, "A12: structures counts the frame's 2; got " + str(_inv_val(inv, "structures")))
	_assert(_count(_inv_val(inv, "cover_cells")) == 3, "A12: cover_cells counts the frame's 3; got " + str(_inv_val(inv, "cover_cells")))
	_assert(_count(_inv_val(inv, "obstacles")) == 1, "A12: obstacles counts the frame's 1; got " + str(_inv_val(inv, "obstacles")))
	_assert(_count(_inv_val(inv, "hud.reinforcements")) == 1, "A12: hud.reinforcements counts the 1 owned structure; got " + str(_inv_val(inv, "hud.reinforcements")))
	_assert(_count(_inv_val(inv, "wrecks")) == 0 and _count(_inv_val(inv, "shots_in_flight")) == 0, "A12 CONTROL: a quiet frame has no wrecks and no shots")
	_assert(_count(_inv_val(inv, "loading_overlay")) == 0, "A12: the loading overlay is gone once a frame is loaded")
