extends SceneTree

# VG-A piece A5. Proves S-007 (a tall obstacle hides units on more layers than a short one: cover is drawn by its
# class, obstacles and the map boundary are drawn). section 2 `map`: cover[{x,y,r,h,class}] class 0 small 1 medium 2 huge;
# obstacles[{x,y,r}]. Adopts push/tv-read's test_tactical_readability.gd interface for cover and obstacle polygons (fog moved to A4).
# RED because res://scenes/tactical_c/map_layer.gd does not exist.
# Interface (test's choice): map_layer.gd extends Node2D, child "MapLayer".
#   set_frame(frame, mission, local_faction, world_scale, camera)
#   cover_cells() -> Array of {class: int, polygon: PackedVector2Array (screen px), color: Color}
#   obstacle_polygons() -> Array of PackedVector2Array     boundary_polygon() -> PackedVector2Array (the canvas edge)
#   A frame with no "map" (space era): all empty.

const TITLE := "VG-A A5 map layer"
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


func _run_tests() -> void:
	var ml = _mod("res://scenes/tactical_c/map_layer.gd", "A5: S-007 cover by class, obstacles, boundary")
	if ml == null:
		return
	if not _need(ml, ["set_frame", "cover_cells", "obstacle_polygons", "boundary_polygon"]):
		return
	ml.call("set_frame", _map_frame(), {"type": "mission", "objectives": []}, 0, SCALE, CAM)
	var cells: Array = ml.call("cover_cells")
	_assert(cells.size() == 3, "A5: one cover cell per map.cover entry (3); got %d" % cells.size())
	if cells.size() == 3:
		var by_class := {}
		for c in cells:
			by_class[int(c["class"])] = c
		_assert(by_class.size() == 3 and by_class.has(0) and by_class.has(1) and by_class.has(2), "A5: the three classes 0, 1, 2 are each drawn")
		if by_class.size() == 3:
			_assert(by_class[0]["color"] != by_class[1]["color"] and by_class[1]["color"] != by_class[2]["color"] and by_class[0]["color"] != by_class[2]["color"],
				"A5: S-007 cover is coloured by class (small, medium, huge differ)")
			var w0 := _bbox(by_class[0]["polygon"]).size.x
			var w2 := _bbox(by_class[2]["polygon"]).size.x
			_assert(w2 > w0 * 3.0, "A5: a huge cover (r 600) is drawn much wider than a small one (r 100); got %f vs %f" % [w2, w0])
			var cc := _bbox(by_class[0]["polygon"]).get_center()
			_assert(cc.distance_to(_scr(Vector2(2000, 2000))) < 1.0, "A5: cover sits at its screen position")
	_assert((ml.call("obstacle_polygons") as Array).size() == 1, "A5: one obstacle polygon per map.obstacles entry")
	var b: PackedVector2Array = ml.call("boundary_polygon")
	_assert(b.size() >= 4, "A5: the map boundary is drawn")
	if b.size() >= 4:
		var r := _bbox(b)
		_assert(r.position.distance_to(_scr(Vector2(0, 0))) < 1.0 and r.end.distance_to(_scr(Vector2(4000, 4000))) < 1.0, "A5: the boundary is the canvas edge (0,0)-(4000,4000)")
	# CONTROL: no map, nothing drawn (space era)
	ml.call("set_frame", _frame([_unit(1, 0, 0, 1500.0, 1500.0)]), {}, 0, SCALE, CAM)
	_assert((ml.call("cover_cells") as Array).is_empty() and (ml.call("obstacle_polygons") as Array).is_empty() and (ml.call("boundary_polygon") as PackedVector2Array).is_empty(),
		"A5 CONTROL: a frame with no map draws no cover, obstacle or boundary")
