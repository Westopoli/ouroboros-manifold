extends SceneTree
# Rule pins: R-089-03@c09d1f, R-089-04@edc267

# VG-A piece A4. Proves S-005 / S-091 / S-092, R-089-04 (visibility recomputed every tick, nothing remembered),
# R-089-03 (what is outside sight is dimmed and not drawn).
# RED because res://scenes/tactical_c/fog_layer.gd does not exist.
# Interface (test's choice): fog_layer.gd extends Node2D, child "FogLayer".
#   set_frame(frame, local_faction, world_scale, camera)
#   sight_discs() -> Array of {points: PackedVector2Array} (TD-VG-A-sightdisc: was {center, radius}), one per own unit carrying `sight`
#   outside_alpha() -> float, 0 < a < 1     the dim outside every disc

const TITLE := "VG-A A4 fog layer"
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


# TD-VG-A-sightdisc: area centroid of a disc's polygon (a disc without `points` reads as Vector2(INF, INF) and fails the checks).
func _centroid(disc: Dictionary) -> Vector2:
	var p: PackedVector2Array = disc.get("points", PackedVector2Array())
	if p.size() < 3:
		return Vector2(INF, INF)
	var a := 0.0
	var c := Vector2.ZERO
	for k in p.size():
		var u := p[k]
		var v := p[(k + 1) % p.size()]
		var cr := u.x * v.y - v.x * u.y
		a += cr
		c += (u + v) * cr
	return c / (3.0 * a)


func _far(disc: Dictionary) -> float:
	var c := _centroid(disc)
	var f := -1.0
	for q in disc.get("points", PackedVector2Array()):
		f = maxf(f, q.distance_to(c))
	return f


func _bbox(poly: PackedVector2Array) -> Rect2:
	var r := Rect2(poly[0], Vector2.ZERO)
	for p in poly:
		r = r.expand(p)
	return r


func _run_tests() -> void:
	var fg = _mod("res://scenes/tactical_c/fog_layer.gd", "A4: sight discs from unit.sight, outside dimmed")
	if fg == null:
		return
	if not _need(fg, ["set_frame", "sight_discs", "outside_alpha"]):
		return
	var units := [
		_unit(1, 0, 0, 1500.0, 1500.0, 1, 100.0, {"sight": 800}),
		_unit(2, 0, 0, 1800.0, 1600.0, 1, 100.0, {"sight": 400}),
		_unit(3, 0, 0, 1900.0, 1700.0),
		_unit(4, 1, 0, 2400.0, 2400.0, 1, 100.0, {"sight": 900})]
	fg.call("set_frame", _frame(units), 0, SCALE, CAM)
	var d: Array = fg.call("sight_discs")
	_assert(d.size() == 2, "A4: S-091 one disc per own unit with sight (2), none for a unit without sight or an enemy; got %d" % d.size())
	if d.size() == 2:
		# TD-VG-A-sightdisc: a disc is {points: PackedVector2Array}; its radius is the farthest point from the polygon's centroid.
		var radii := [_far(d[0]), _far(d[1])]
		radii.sort()
		_assert(absf(radii[0] - 100.0) < 0.5 and absf(radii[1] - 200.0) < 0.5, "A4: radius = sight * world_scale; a unit that sees farther has a larger disc; got " + str(radii))
		var near := false
		for x in d:
			if _centroid(x).distance_to(_scr(Vector2(1500, 1500))) < 0.5:
				near = true
		_assert(near, "A4 CONTROL: a disc is centred on the unit's screen position")
	_assert(float(fg.call("outside_alpha")) > 0.0 and float(fg.call("outside_alpha")) < 1.0, "A4: S-092 the outside is dimmed, not black and not clear")
	# R-089-04: nothing remembered. The unit leaves; no disc stays where it was.
	var moved := units.duplicate(true)
	moved[0]["x"] = 3200.0
	fg.call("set_frame", _frame(moved), 0, SCALE, CAM)
	var stale := false
	for x in fg.call("sight_discs"):
		if _centroid(x).distance_to(_scr(Vector2(1500, 1500))) < 0.5:
			stale = true
	_assert(not stale, "A4: R-089-04 no disc remains at a position the unit has left")
	_assert((fg.call("sight_discs") as Array).size() == 2, "A4: the moved unit still has its disc, at the new position")
