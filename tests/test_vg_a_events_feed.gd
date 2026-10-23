extends SceneTree
# Rule pins: R-104-01@1aaaa3, R-104-02@03d7aa, R-104-03@9dae08, R-127-04@db7974

# VG-A piece A8. Proves S-104 / R-104-01 (a quiet ticker of four beats and nothing else at launch), R-104-02
# (a banner appears and clears within 5 s; spec: 4 s), R-104-03 (elapsed mission time mm:ss, 20 ticks/s), R-127-04
# (structure captured / lost from a structures_changed owner change). Objective threshold beats at 25/50/75/100 %
# (spec section 7). Force routed has no sim source yet: not tested. The TickerBeats signal (E1m) waits on E1m's name.
# RED because res://scenes/tactical_c/hud/events_feed.gd does not exist.
# Interface (test's choice): events_feed.gd extends Control, child "Events" of "Hud".
#   feed(frame_or_delta, local_faction)   a full frame (structures, objectives) or a delta (structures_changed, objectives)
#   lines() -> Array of {kind: "captured"|"lost"|"objective", text}   banner() -> String   advance(dt_s)   clock_text(tick) -> String

const TITLE := "VG-A A8 events feed"
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


func _kinds(lines: Array) -> Array:
	var k := []
	for l in lines:
		k.append(String(l["kind"]))
	return k


func _run_tests() -> void:
	var ef = _mod("res://scenes/tactical_c/hud/events_feed.gd", "A8: S-104 the four beats, banner 4 s, clock")
	if ef == null:
		return
	if not _need(ef, ["feed", "lines", "banner", "advance", "clock_text"]):
		return
	var full := _frame([_unit(1, 0, 0, 1000.0, 1000.0)], {"structures": [
		{"id": 5, "type": 0, "owner": 1, "x": 2000.0, "y": 2000.0, "hp": 500.0, "stage": 0, "cap": 0, "nst": 150, "next_type": 0, "period": 100},
		{"id": 6, "type": 0, "owner": 0, "x": 1500.0, "y": 1500.0, "hp": 500.0, "stage": 0, "cap": 0, "nst": 150, "next_type": 0, "period": 100}],
		"objectives": [{"i": 0, "progress": 0.1, "done": 0}]})
	ef.call("feed", full, 0)
	_assert((ef.call("lines") as Array).is_empty(), "A8 CONTROL: a first frame is not a beat")
	ef.call("feed", {"type": "tactical_delta", "tick": 101, "objectives": [{"i": 0, "progress": 0.2, "done": 0}]}, 0)
	_assert((ef.call("lines") as Array).is_empty(), "A8: progress 0.1 -> 0.2 crosses no threshold, no beat")
	ef.call("feed", {"type": "tactical_delta", "tick": 102, "objectives": [{"i": 0, "progress": 0.3, "done": 0}]}, 0)
	_assert(_kinds(ef.call("lines")) == ["objective"], "A8: progress crossing 25%% is one objective beat; got " + str(_kinds(ef.call("lines"))))
	ef.call("feed", {"type": "tactical_delta", "tick": 103, "events": [[0, 1, 2, 103], [2, 7, 1, 103]], "structures_changed": [{"id": 6, "owner": 1}]}, 0)
	_assert(_kinds(ef.call("lines")) == ["objective", "lost"], "A8: R-127-04 a structure of ours changing owner is 'lost'; fire and kill events add nothing; got " + str(_kinds(ef.call("lines"))))
	ef.call("feed", {"type": "tactical_delta", "tick": 104, "structures_changed": [{"id": 5, "owner": 0}]}, 0)
	_assert(_kinds(ef.call("lines")) == ["objective", "lost", "captured"], "A8: R-127-04 a structure changing to us is 'captured'; got " + str(_kinds(ef.call("lines"))))
	# R-104-02 banner clears
	_assert(String(ef.call("banner")) != "", "A8: R-104-02 a structure beat raises a banner")
	ef.call("advance", 3.9)
	_assert(String(ef.call("banner")) != "", "A8: the banner is still up at 3.9 s")
	ef.call("advance", 0.2)
	_assert(String(ef.call("banner")) == "", "A8: the banner clears after 4 s (R-104-02: within 5 s)")
	# R-104-03 clock
	_assert(ef.call("clock_text", 1200) == "01:00" and ef.call("clock_text", 0) == "00:00" and ef.call("clock_text", 1219) == "01:00", "A8: R-104-03 the clock reads elapsed mm:ss at 20 ticks per second")
