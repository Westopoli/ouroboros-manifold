extends SceneTree

# VG-A piece A10. Proves S-136 / R-136-01 (a death bloom 0.5 s brighter than any hit; damage emitters; the wreck drifts
# along its last heading, decelerating; darkens over 3 to 5 s) and R-136-03 (wrecks fade out after 30 s, cap 150).
# section 2 events: kind 2 = kill(a unit, b killer or -1); the dead unit is absent from `units` in that frame.
# RED because res://scenes/tactical_c/fx/deaths.gd does not exist.
# Interface (test's choice): deaths.gd extends Node2D, child "Deaths" of "Fx".
#   set_frame(frame, local_faction, world_scale, camera)    advance(dt_s)
#   bloom_duration() -> float (0.5)    death_bloom_energy() -> float    hit_bloom_energy() -> float
#   wrecks() -> Array of {id}    wreck_position(id) -> Vector2 (world)    wreck_speed(id) -> float wu/s
#   wreck_darkness(id) -> float 0..1    wreck_emitters(id) -> int

const TITLE := "VG-A A10 deaths"
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


func _kill(deaths: Node, ids: Array) -> void:
	var alive := [_unit(1, 0, 0, 1500.0, 1500.0)]
	for i in ids:
		alive.append(_unit(i, 1, 0, 2400.0, 2400.0, 1, 100.0, {"facing": 0.0}))
	deaths.call("set_frame", _frame(alive), 0, SCALE, CAM)
	var evs := []
	for i in ids:
		evs.append([2, i, 1, 101])
	deaths.call("set_frame", _frame([_unit(1, 0, 0, 1500.0, 1500.0)], {"tick": 101, "events": evs}), 0, SCALE, CAM)


func _run_tests() -> void:
	var d = _mod("res://scenes/tactical_c/fx/deaths.gd", "A10: S-136 death bloom, wreck drift, darken, fade, cap")
	if d == null:
		return
	if not _need(d, ["set_frame", "advance", "bloom_duration", "death_bloom_energy", "hit_bloom_energy", "wrecks", "wreck_position",
			"wreck_speed", "wreck_darkness", "wreck_emitters"]):
		return
	_assert(is_equal_approx(float(d.call("bloom_duration")), 0.5), "A10: R-136-01 the death bloom lasts 0.5 s")
	_assert(float(d.call("death_bloom_energy")) > float(d.call("hit_bloom_energy")), "A10: R-136-01 the death bloom is brighter than any hit")
	_assert((d.call("wrecks") as Array).is_empty(), "A10 CONTROL: no kill, no wreck")
	_kill(d, [7])
	_assert((d.call("wrecks") as Array).size() == 1, "A10: a kill event leaves one wreck")
	_assert(int(d.call("wreck_emitters", 7)) >= 1, "A10: R-136-01 persistent damage emitters are active on the wreck")
	var p0: Vector2 = d.call("wreck_position", 7)
	_assert(p0.distance_to(Vector2(2400, 2400)) < 0.5, "A10: the wreck starts where the unit died")
	var v_early := float(d.call("wreck_speed", 7))
	d.call("advance", 2.0)
	var v_late := float(d.call("wreck_speed", 7))
	_assert(v_early > v_late and v_late >= 0.0, "A10: R-136-01 the wreck decelerates; speed %f then %f" % [v_early, v_late])
	_assert((d.call("wreck_position", 7) as Vector2).x > p0.x, "A10: the wreck drifts along its last heading (facing 0 = +x)")
	_assert(float(d.call("wreck_darkness", 7)) > 0.0 and float(d.call("wreck_darkness", 7)) < 1.0, "A10: at 2 s the wreck is darkening, not yet done (3 to 5 s)")
	d.call("advance", 3.1)
	_assert(float(d.call("wreck_darkness", 7)) > 0.999, "A10: R-136-01 darkening is complete by 5 s")
	d.call("advance", 24.0)
	_assert((d.call("wrecks") as Array).size() == 1, "A10: R-136-03 the wreck is still there at 29.1 s")
	d.call("advance", 1.5)
	_assert((d.call("wrecks") as Array).is_empty(), "A10: R-136-03 wrecks fade out after 30 s")
	# cap 150
	var ids := []
	for i in range(200):
		ids.append(100 + i)
	_kill(d, ids)
	_assert((d.call("wrecks") as Array).size() == 150, "A10: R-136-03 the wreck cap is 150; got %d" % (d.call("wrecks") as Array).size())
