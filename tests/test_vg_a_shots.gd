extends SceneTree

# VG-A piece A9. Proves S-134 (shots travel, hits bloom, nothing twitches) / R-134-05 (six per-type shot categories,
# the Interceptor a missile volley) and the spec rule: a fire event is drawn only when its shooter or its target is
# visible, from the visible end. section 2 events[kind,a,b,tick] kind 0 = fire(a shooter, b target).
# RED because res://scenes/tactical_c/fx/shots.gd does not exist.
# Interface (test's choice): shots.gd extends Node2D, child "Shots" of "Fx".
#   set_frame(frame, local_faction, world_scale, camera)    shot_category(type) -> int
#   shots() -> Array of {category: int, volley: int, from: Vector2, to: Vector2 (screen), origin_visible: bool}
#   blooms() -> Array of {center: Vector2 screen}           impact bloom where a unit's hp dropped between two frames

const TITLE := "VG-A A9 shots"
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


func _units(hp3: float) -> Array:
	return [_unit(1, 0, 1, 1500.0, 1500.0), _unit(2, 0, 0, 1700.0, 1500.0), _unit(3, 1, 0, 2400.0, 2400.0, 1, hp3),
		_unit(4, 1, 0, 3000.0, 3000.0), _unit(5, 1, 0, 3200.0, 3000.0)]


func _run_tests() -> void:
	var sh = _mod("res://scenes/tactical_c/fx/shots.gd", "A9: S-134 per-type shots, volleys, fog rule, impact bloom")
	if sh == null:
		return
	if not _need(sh, ["set_frame", "shot_category", "shots", "blooms"]):
		return
	var cats := {}
	for t in range(6):
		cats[int(sh.call("shot_category", t))] = true
	_assert(cats.size() == 6, "A9: R-134-05 six unit types, six shot categories; got %d" % cats.size())
	# fire events: 1 -> 3 (both visible), 4 -> 2 (shooter hidden, target visible), 4 -> 5 (both hidden)
	var f := _frame(_units(100.0), {"events": [[0, 1, 3, 100], [0, 4, 2, 100], [0, 4, 5, 100]]}, [4, 5])
	sh.call("set_frame", f, 0, SCALE, CAM)
	var s: Array = sh.call("shots")
	_assert(s.size() == 2, "A9: both-hidden fire is not drawn; the two others are (2 shots); got %d" % s.size())
	var hidden_origin := 0
	var interceptor_volley := 0
	for x in s:
		if not bool(x["origin_visible"]):
			hidden_origin += 1
			_assert((x["to"] as Vector2).distance_to(_scr(Vector2(1700, 1500))) < 0.5 or (x["from"] as Vector2).distance_to(_scr(Vector2(1700, 1500))) < 0.5,
				"A9: a shot with a hidden shooter is drawn at the visible end (the target)")
		else:
			interceptor_volley = int(x["volley"])
			_assert(int(x["category"]) == int(sh.call("shot_category", 1)), "A9: the shot takes its shooter's category")
	_assert(hidden_origin == 1, "A9: exactly one shot has a hidden origin")
	_assert(interceptor_volley >= 2, "A9: R-134-05 the Interceptor fires a missile volley (more than one projectile); got %d" % interceptor_volley)
	# impact bloom from an hp drop between two frames
	sh.call("set_frame", _frame(_units(100.0), {"tick": 101}), 0, SCALE, CAM)
	_assert((sh.call("blooms") as Array).is_empty(), "A9 CONTROL: no hp drop, no bloom")
	sh.call("set_frame", _frame(_units(80.0), {"tick": 102}), 0, SCALE, CAM)
	var b: Array = sh.call("blooms")
	_assert(b.size() == 1 and (b[0]["center"] as Vector2).distance_to(_scr(Vector2(2400, 2400))) < 0.5, "A9: S-134 an hp drop blooms at the unit that was hit")
