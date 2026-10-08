extends SceneTree

# VG-A piece A11. Proves S-234's unblocked half and R-103-01/02 (free pan, canvas edges bound the camera at any zoom),
# R-103-04 (never bound to a layer), spec A11 (edge-scroll within 60 px, zoom to the map band, initial framing).
# RED because res://scenes/tactical_c/camera.gd does not exist.
# Interface (test's choice): camera.gd extends Node.
#   setup(canvas: float, viewport: Vector2)     frame_units(world_positions: Array)  initial framing, own units all in view
#   pan(delta_world: Vector2)    edge_scroll(mouse: Vector2, dt_s: float)    zoom_to(z: float)    zoom_min() -> float
#   view_rect() -> Rect2 (world units visible)   centre() -> Vector2 (world)

const TITLE := "VG-A A11 camera"
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
	var c = _mod("res://scenes/tactical_c/camera.gd", "A11: pan, 60 px edge scroll, zoom to the map band, initial framing")
	if c == null:
		return
	if not _need(c, ["setup", "frame_units", "pan", "edge_scroll", "zoom_to", "zoom_min", "view_rect", "centre"]):
		return
	var canvas := 4000.0
	c.call("setup", canvas, Vector2(1920, 1080))
	# zoom to the map band: zooming all the way out shows the map and no more
	c.call("zoom_to", 0.0001)
	var r: Rect2 = c.call("view_rect")
	_assert(r.size.x <= canvas + 0.5 and r.size.y <= canvas + 0.5, "A11: R-103-02 the widest zoom never shows more than the canvas; got " + str(r.size))
	_assert(float(c.call("zoom_min")) > 0.0, "A11: zoom_min is the map band's widest zoom")
	var z2 := float(c.call("zoom_min")) * 2.0
	c.call("zoom_to", z2)
	# bounds on pan
	c.call("pan", Vector2(-1.0e6, -1.0e6))
	r = c.call("view_rect")
	_assert(r.position.x >= -0.5 and r.position.y >= -0.5, "A11: R-103-02 panning far up-left stops at the canvas edge; got " + str(r.position))
	c.call("pan", Vector2(1.0e6, 1.0e6))
	r = c.call("view_rect")
	_assert(r.end.x <= canvas + 0.5 and r.end.y <= canvas + 0.5, "A11: R-103-02 panning far down-right stops at the canvas edge; got " + str(r.end))
	# edge scroll within 60 px
	c.call("pan", Vector2(-1.0e6, -1.0e6))
	c.call("pan", Vector2(1500.0, 1500.0))
	var base: Vector2 = c.call("centre")
	c.call("edge_scroll", Vector2(960, 540), 1.0)
	_assert((c.call("centre") as Vector2).distance_to(base) < 0.01, "A11 CONTROL: the pointer mid-screen does not scroll")
	c.call("edge_scroll", Vector2(61, 540), 1.0)
	_assert((c.call("centre") as Vector2).distance_to(base) < 0.01, "A11: 61 px from the edge is outside the 60 px edge zone")
	c.call("edge_scroll", Vector2(30, 540), 1.0)
	var left: Vector2 = c.call("centre")
	_assert(left.x < base.x - 0.01, "A11: 30 px from the left edge scrolls left")
	c.call("edge_scroll", Vector2(1900, 540), 1.0)
	_assert((c.call("centre") as Vector2).x > left.x + 0.01, "A11: 20 px from the right edge scrolls right")
	# initial framing: every own unit starts inside the view
	c.call("zoom_to", z2)
	var own := [Vector2(800, 800), Vector2(950, 870), Vector2(1100, 820)]
	c.call("frame_units", own)
	r = c.call("view_rect")
	for p in own:
		_assert(r.has_point(p), "A11: initial framing holds own unit %s inside the view %s" % [str(p), str(r)])
	_assert(r.position.x >= -0.5 and r.end.x <= canvas + 0.5, "A11: the initial framing respects the canvas bound")
