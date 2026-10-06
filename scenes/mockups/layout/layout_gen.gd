extends RefCounted
# Layout prototype pass 1: generator. Pure data out (a Dictionary of arrays), no nodes.
# Method M4 (research/layout_engine/composition_methods.md): districts first, slots in the
# home districts, growth by rules in the contested and objective districts, five candidates,
# the best kept. All figures are drafts (Q-191-05). Spec: plans/2026-10-04-layout-prototype-pass1-spec.md.
# See also: layout_checks.gd (scores each candidate), layout_view.gd (draws the result).

const Checks := preload("res://scenes/mockups/layout/layout_checks.gd")
const KITS_PATH := "res://scenes/mockups/layout/layout_kits.json"
const ARCHETYPES := ["defensive_stand", "assault", "interception"]
const SYM_MODES := ["mirror", "rotate", "separate"]
const DIVISIONS := ["band", "ring", "patches"]
const GRID := 8
const CANDIDATES := 5
const FRONTAGE := 150.0  # wu of route width per unit abreast (draft)
const WAY_T := [-0.46, -0.30, -0.14, 0.0, 0.14, 0.30, 0.46]  # lane waypoints along the axis
const MARGIN := 0.04
# District codes in the 8x8 grid.
const HOME_A := 0
const HOME_B := 1
const NEAR_A := 2
const NEAR_B := 3
const CONTESTED := 4
const OBJ_DIST := 5
const WILD := 6

var kits: Dictionary
var rng := RandomNumberGenerator.new()
var rng_b := RandomNumberGenerator.new()  # second stream: side B grown separately
var nodes: Array
var edges: Array
var steps: Array
var cur_step := 0
var canvas := 32000.0
var axis := Vector2.RIGHT
var perp := Vector2.DOWN
var tspan := 1.0
var uspan := 1.0
var sym := "mirror"
var recipe: Dictionary
var districts: Array
var division := "band"
var lane_ids: Array  # per lane: node ids of waypoints 0..6
var name_count := {}
var theta_deg := 0


func _init() -> void:
	var f := FileAccess.open(KITS_PATH, FileAccess.READ)
	kits = JSON.parse_string(f.get_as_text())


# Make CANDIDATES maps for one (archetype, seed) and keep the best by checks.
# opts: sym (mirror|rotate|separate), growth (bool), recent (signatures of earlier maps).
func make(arch: String, seed_: int, opts := {}) -> Dictionary:
	var best := {}
	var best_score := -1.0
	var scores := []
	for k in CANDIDATES:
		var m := _build(arch, seed_, k, opts)
		Checks.run(m, kits, opts.get("recent", []))
		var s := Checks.score(m)
		scores.append(s)
		if s > best_score:
			best_score = s
			best = m
	best["candidate_scores"] = scores
	return best


func _build(arch: String, seed_: int, cand: int, opts: Dictionary) -> Dictionary:
	sym = opts.get("sym", "mirror")
	var growth: bool = opts.get("growth", true)
	recipe = kits["recipes"][arch]
	canvas = float(recipe["canvas"])
	var a_idx := ARCHETYPES.find(arch)
	rng.seed = seed_ * 1000003 + a_idx * 7919 + cand * 15485863 + 17
	rng_b.seed = seed_ * 998244353 + a_idx * 104729 + cand * 32452843 + 5
	nodes = []
	edges = []
	steps = []
	name_count = {}
	lane_ids = []
	cur_step = 0

	districts_route = []
	_districts()
	_step("districts", "Division: %s, axis %d degrees. Home, near ground, contested, objective." % [division, theta_deg])
	_step("home slots", "")
	var homes := _home_slots()
	steps[cur_step]["text"] = "Home ground and gate drawn for side A; side B %s." % ("mirrors it" if sym == "mirror" else ("is its rotated copy" if sym == "rotate" else "is grown separately with matched numbers"))
	_step("spine", "")
	_spine(homes)
	steps[cur_step]["text"] = "Route from home A through the objective ground to home B, in %d lane(s)." % lane_ids.size()
	_step("near prizes", "Each side gets one expansion site in its own ground, matched in width and distance.")
	_near_prizes()
	if growth:
		_grow()
	_tune()
	_step("match", "Route meander (1.0 to %.1f) tuned until walking distances match." % kits["tolerances"]["meander_max"])
	var m := {
		"arch": arch, "seed": seed_, "sym": sym, "growth": growth, "candidate": cand,
		"title": recipe["title"], "canvas": canvas, "division": division, "theta": theta_deg,
		"districts": districts, "nodes": nodes, "edges": edges, "steps": steps,
		"homes": homes, "lanes": lane_ids, "walk": kits["walk_speed"],
		"required": recipe["required"], "objective_side": recipe["objective_side"],
	}
	return m


# ---------- districts ----------

func _districts() -> void:
	theta_deg = rng.randi_range(0, 11) * 15
	var th := deg_to_rad(theta_deg)
	axis = Vector2(cos(th), sin(th))
	perp = Vector2(-sin(th), cos(th))
	division = DIVISIONS[rng.randi() % 3]
	tspan = 0.0
	uspan = 0.0
	for cy in GRID:
		for cx in GRID:
			var rel := _cell_center(cx, cy) - Vector2(canvas, canvas) * 0.5
			tspan = maxf(tspan, absf(rel.dot(axis)))
			uspan = maxf(uspan, absf(rel.dot(perp)))
	districts = []
	for cy in GRID:
		for cx in GRID:
			var rel := _cell_center(cx, cy) - Vector2(canvas, canvas) * 0.5
			districts.append(_classify(rel.dot(axis) / tspan, rel.dot(perp) / uspan))
	# Objective district: the cells holding the objective ground.
	for p in _objective_points():
		var c := _cell_of(p)
		districts[c.y * GRID + c.x] = OBJ_DIST


func _classify(t: float, u: float) -> int:
	if t < -0.62:
		return HOME_A if absf(u) < 0.55 else WILD
	if t > 0.62:
		return HOME_B if absf(u) < 0.55 else WILD
	if absf(u) > 0.85:
		return WILD
	if t < -0.3:
		return NEAR_A
	if t > 0.3:
		return NEAR_B
	match division:
		"band":
			return CONTESTED
		"ring":
			return CONTESTED if Vector2(t * 1.6, u).length() > 0.35 else WILD
		_:
			return CONTESTED if absf(u) > 0.3 else WILD


func _objective_points() -> Array:
	var pts := []
	if recipe["objective"] == "route":
		for u in [-0.7, -0.25, 0.25, 0.7]:
			pts.append(_pos(0.0, u))
	else:
		var s: int = recipe["objective_side"]
		pts.append(_pos(-0.30 if s == 0 else 0.30, 0.0))
	return pts


func _cell_center(cx: int, cy: int) -> Vector2:
	return Vector2(cx + 0.5, cy + 0.5) * canvas / GRID


func _cell_of(p: Vector2) -> Vector2i:
	return Vector2i(clampi(int(p.x / canvas * GRID), 0, GRID - 1), clampi(int(p.y / canvas * GRID), 0, GRID - 1))


func _district_at(p: Vector2) -> int:
	var c := _cell_of(p)
	return districts[c.y * GRID + c.x]


# Normalised (t along the axis, u across) to canvas position.
func _pos(t: float, u: float) -> Vector2:
	var p := Vector2(canvas, canvas) * 0.5 + axis * t * tspan + perp * u * uspan
	var lo := canvas * MARGIN
	return Vector2(clampf(p.x, lo, canvas - lo), clampf(p.y, lo, canvas - lo))


func _inside(p: Vector2) -> bool:
	var lo := canvas * MARGIN
	return p.x >= lo and p.y >= lo and p.x <= canvas - lo and p.y <= canvas - lo


# ---------- graph helpers ----------

func _step(rule: String, text: String) -> void:
	steps.append({"rule": rule, "text": text})
	cur_step = steps.size() - 1


func _uniq_name(skin: String) -> String:
	var n: int = name_count.get(skin, 0)
	name_count[skin] = n + 1
	return skin if n == 0 else "%s %s" % [skin, char(65 + n)]


func _vrange(r: Array, r2 := rng) -> float:
	return r2.randf_range(float(r[0]), float(r[1]))


func _variant(kind: String, r2 := rng, avoid := "") -> Dictionary:
	var vs: Array = kits["kinds"][kind]["variants"]
	var pool := vs.filter(func(v): return v["id"] != avoid)
	return pool[r2.randi() % pool.size()]


func _add_node(kind: String, variant: String, pos: Vector2, side: int, extra := {}) -> int:
	var n := {"id": nodes.size(), "kind": kind, "variant": variant, "pos": pos, "side": side,
		"district": _district_at(pos), "step": cur_step, "name": "", "choice": "", "nums": {}}
	n.merge(extra, true)
	nodes.append(n)
	return n["id"]


func _add_edge(a: int, b: int, kind: String, width: float, extra := {}) -> int:
	var e := {"id": edges.size(), "a": a, "b": b, "kind": kind, "width": width, "meander": 1.0,
		"step": cur_step, "choke": false, "hidden": false, "open": false}
	e.merge(extra, true)
	edges.append(e)
	return e["id"]


func edge_len(e: Dictionary) -> float:
	return (nodes[e["a"]]["pos"] as Vector2).distance_to(nodes[e["b"]]["pos"]) * e["meander"]


func _fmt(text: String, vals: Dictionary) -> String:
	for k in vals:
		text = text.replace("{%s}" % k, str(vals[k]))
	return text


func _in(x: float, r: Array) -> bool:
	return x >= float(r[0]) and x <= float(r[1])


func _fire(width: float) -> int:
	return maxi(1, int(width / FRONTAGE))


# ---------- home slots ----------

func _home_slots() -> Dictionary:
	var hv_a := _variant("home")
	var gv_a := _variant("gate")
	var wall_a := int(_vrange(hv_a["numbers"]["wall"]))
	var rad_a := _vrange(hv_a["numbers"]["radius"])
	var w_a := _vrange(gv_a["numbers"]["width"])
	var total := w_a * int(gv_a["mouths"])
	var hv_b := hv_a
	var gv_b := gv_a
	var wall_b := wall_a
	var rad_b := rad_a
	var w_b := w_a
	if sym == "separate":
		# Grown separately: a different variant with the same numbers, where one can carry them.
		var homes_ok: Array = kits["kinds"]["home"]["variants"].filter(func(v): return v["id"] != hv_a["id"] and _in(rad_a, v["numbers"]["radius"]) and _in(wall_a, v["numbers"]["wall"]))
		var gates_ok: Array = kits["kinds"]["gate"]["variants"].filter(func(v): return v["id"] != gv_a["id"] and _in(total / int(v["mouths"]), v["numbers"]["width"]))
		if not homes_ok.is_empty():
			hv_b = homes_ok[rng_b.randi() % homes_ok.size()]
		if not gates_ok.is_empty():
			gv_b = gates_ok[rng_b.randi() % gates_ok.size()]
			w_b = total / int(gv_b["mouths"])
	var out := {"a": {}, "b": {}}
	for s in 2:
		var hv: Dictionary = hv_a if s == 0 else hv_b
		var gv: Dictionary = gv_a if s == 0 else gv_b
		var wall: int = wall_a if s == 0 else wall_b
		var rad: float = rad_a if s == 0 else rad_b
		var w: float = w_a if s == 0 else w_b
		var sign_t := -1.0 if s == 0 else 1.0
		var home := _add_node("home", hv["id"], _pos(sign_t * 0.8, 0.0), s, {
			"name": _uniq_name(hv["skins"][rng.randi() % hv["skins"].size()]),
			"choice": _fmt(hv["choice"], {"wall": wall}), "nums": {"radius": int(rad), "wall": wall}})
		var gates := []
		for g in int(gv["mouths"]):
			var du: float = 0.0 if int(gv["mouths"]) == 1 else (-0.12 if g == 0 else 0.12)
			var gid := _add_node("gate", gv["id"], _pos(sign_t * 0.62, du), s, {
				"name": _uniq_name(gv["skins"][rng.randi() % gv["skins"].size()]),
				"choice": _fmt(gv["choice"], {"width": int(w)}), "nums": {"width": int(w)}})
			_add_edge(home, gid, "route", w, {"choke": int(w) < 700, "closed": int(w) < 700})
			gates.append(gid)
		if gv.get("overlook", false):
			nodes[gates[0]]["overlooked"] = true
		out["a" if s == 0 else "b"] = {"home": home, "gates": gates, "gate_variant": gv["id"],
			"home_variant": hv["id"], "wall": wall, "radius": rad, "width": w}
	return out


# ---------- spine ----------

func _spine(homes: Dictionary) -> void:
	var lanes := 1 if division == "band" else 2
	var jit := _jitter_table(lanes)
	for l in lanes:
		var via_u := (rng.randf_range(-0.12, 0.12) if lanes == 1 else (0.55 if l == 0 else -0.55) * rng.randf_range(0.9, 1.1))
		# The road bends: even about the middle under mirror, odd under rotate, random phase when separate.
		var bow_amp := rng.randf_range(0.1, 0.3) if lanes == 1 else rng.randf_range(0.04, 0.12)
		var bow_k := float(rng.randi_range(1, 2))
		var bow_phase := rng_b.randf_range(0.0, TAU)
		var ids := []
		for i in WAY_T.size():
			var t: float = WAY_T[i]
			var prof := 1.0 - pow(absf(t) / 0.62, 2.0)
			var j: Vector2 = jit[l][i]
			var arg := bow_k * PI * t / 0.62
			var bow := cos(arg) if sym == "mirror" else (sin(arg) if sym == "rotate" else sin(arg + bow_phase))
			var p := _pos(t + j.x, via_u * prof + j.y + bow_amp * bow * prof)
			var nid := _add_node("waypoint", "", p, -1)
			ids.append(nid)
		lane_ids.append(ids)
		var ga: Array = homes["a"]["gates"]
		var gb: Array = homes["b"]["gates"]
		var g_a: int = ga[min(l, ga.size() - 1)]
		var g_b: int = gb[min(l, gb.size() - 1)]
		var prev := g_a
		for i in ids.size():
			_add_edge(prev, ids[i], "route", rng.randf_range(800.0, 1500.0), {"lane": l})
			prev = ids[i]
		_add_edge(prev, g_b, "route", rng.randf_range(800.0, 1500.0), {"lane": l})
	for s in 2:
		var gates: Array = homes["a" if s == 0 else "b"]["gates"]
		for g in gates:
			var linked := false
			for e in edges:
				if e["a"] == g or e["b"] == g:
					if e["kind"] == "route" and e.has("lane"):
						linked = true
			if not linked:
				_add_edge(g, lane_ids[0][0 if s == 0 else WAY_T.size() - 1], "route", rng.randf_range(800.0, 1500.0), {"lane": 0})
	if division == "ring":
		_add_edge(lane_ids[0][3], lane_ids[1][3], "link", rng.randf_range(700.0, 1000.0), {"lane": -1})
	_objective()


# Waypoint jitter in the (t, u) frame; side B derives from A by the sides switch.
func _jitter_table(lanes: int) -> Array:
	var tab := []
	for l in lanes:
		var row := []
		for i in WAY_T.size():
			row.append(Vector2.ZERO)
		for i in 4:
			row[i] = Vector2(rng.randf_range(-0.04, 0.04), rng.randf_range(-0.06, 0.06))
		for i in range(4, WAY_T.size()):
			var src: Vector2 = row[WAY_T.size() - 1 - i]
			match sym:
				"mirror":
					row[i] = Vector2(-src.x, src.y)
				"rotate":
					row[i] = Vector2(-src.x, -src.y)
				_:
					row[i] = Vector2(rng_b.randf_range(-0.04, 0.04), rng_b.randf_range(-0.06, 0.06))
		tab.append(row)
	return tab


func _objective() -> void:
	var okit: Dictionary
	if recipe["objective"] == "route":
		okit = _variant_by_id("objective", "walkway")
		var ids := []
		var us := [-0.7, -0.25, 0.25, 0.7]
		for i in us.size():
			var p := _pos(rng.randf_range(-0.05, 0.05), us[i] + rng.randf_range(-0.04, 0.04))
			var nid := _add_node("objective", "walkway", p, -1, {"name": "", "route_stop": i, "moving": true})
			ids.append(nid)
		nodes[ids[0]]["name"] = _uniq_name(okit["skins"][0])
		nodes[ids[0]]["choice"] = okit["choice"]
		nodes[ids[0]]["nums"] = {"stops": us.size()}
		for i in us.size() - 1:
			_add_edge(ids[i], ids[i + 1], "objroute", _vrange(okit["numbers"]["width"]))
		for i in ids.size():
			var best := -1
			var bd := 1e12
			for l in lane_ids.size():
				var w: int = lane_ids[l][3]
				var d: float = (nodes[w]["pos"] as Vector2).distance_to(nodes[ids[i]]["pos"])
				if d < bd:
					bd = d
					best = w
			var dup := false
			for e in edges:
				if (e["a"] == ids[i] and e["b"] == best) or (e["b"] == ids[i] and e["a"] == best):
					dup = true
			if not dup:
				_add_edge(ids[i], best, "link", rng.randf_range(600.0, 900.0))
		districts_route = ids
	else:
		var s: int = recipe["objective_side"]
		var idx := 1 if s == 0 else 5
		okit = _variant("objective")
		while okit.get("moving", false):
			okit = _variant("objective")
		var nid: int = lane_ids[0][idx]
		var n: Dictionary = nodes[nid]
		n["kind"] = "objective"
		n["variant"] = okit["id"]
		n["side"] = -1
		n["district"] = OBJ_DIST
		n["name"] = _uniq_name(okit["skins"][rng.randi() % okit["skins"].size()])
		n["holder"] = s
		n["choice"] = okit["choice"]
		n["nums"] = {"width": int(_vrange(okit["numbers"]["width"]))}
		districts_route = [nid]


var districts_route := []  # objective node ids (one, or the stops of the moving route)


func _variant_by_id(kind: String, id: String) -> Dictionary:
	for v in kits["kinds"][kind]["variants"]:
		if v["id"] == id:
			return v
	return {}


# ---------- near-ground prizes (slots) ----------

func _near_prizes() -> void:
	var pv_a := _variant("prize")
	var off_sign := 1.0 if rng.randf() < 0.5 else -1.0
	var spur := _vrange(pv_a["numbers"]["spur"])
	var width := _vrange(pv_a["numbers"]["width"])
	for s in 2:
		var pv: Dictionary = pv_a
		if s == 1 and sym == "separate":
			pv = _variant("prize", rng_b, pv_a["id"])
			width = clampf(width, pv["numbers"]["width"][0], pv["numbers"]["width"][1])
			spur = clampf(spur, pv["numbers"]["spur"][0], pv["numbers"]["spur"][1])
		var idx := 0 if s == 0 else 6
		var wp: int = lane_ids[0][idx]
		var sg := off_sign if (s == 0 or sym == "mirror" or sym == "separate") else -off_sign
		_spur(wp, pv, width, spur, sg, s, false)
		nodes[wp]["piece"] = true


# Hang a prize off a route node. Returns the prize node id.
func _spur(wp: int, pv: Dictionary, width: float, spur: float, sg: float, side: int, sig: bool) -> int:
	var base: Vector2 = nodes[wp]["pos"]
	var p := base + perp * sg * spur
	if not _inside(p):
		sg = -sg
		p = base + perp * sg * spur
	p = Vector2(clampf(p.x, canvas * MARGIN, canvas * (1.0 - MARGIN)), clampf(p.y, canvas * MARGIN, canvas * (1.0 - MARGIN)))
	var pid := _add_node("prize", pv["id"], p, side, {
		"name": _uniq_name(pv["skins"][rng.randi() % pv["skins"].size()]), "sig": sig,
		"choice": _fmt(pv["choice"], {"spur": int(spur / kits["walk_speed"])}),
		"nums": {"width": int(width), "spur_wu": int(spur)}})
	_add_edge(wp, pid, "spur", width, {"closed": true})
	if pv.get("backdoor", false):
		var li := _lane_pos(wp)
		if li.x >= 0:
			var j: int = clampi(li.y + (2 if li.y < 3 else -2), 0, WAY_T.size() - 1)
			_add_edge(pid, lane_ids[li.x][j], "backdoor", width * 0.7, {"closed": true, "hidden": true})
			nodes[pid]["nums"]["back_door"] = true
	return pid


func _lane_pos(nid: int) -> Vector2i:
	for l in lane_ids.size():
		var i: int = lane_ids[l].find(nid)
		if i >= 0:
			return Vector2i(l, i)
	return Vector2i(-1, -1)


# ---------- growth rules ----------

func _grow() -> void:
	var todo := []
	var budget: Dictionary = recipe["budget"]
	for kind in ["crossing", "heights", "prize", "commons", "hidden"]:
		for i in int(budget.get(kind, 0)):
			todo.append(kind)
	# Fisher-Yates on the main stream: the order of rules is part of the signature.
	for i in range(todo.size() - 1, 0, -1):
		var j := rng.randi() % (i + 1)
		var tmp = todo[i]
		todo[i] = todo[j]
		todo[j] = tmp
	for kind in todo:
		var ok := false
		match kind:
			"crossing":
				ok = _rule_crossing()
			"heights":
				ok = _rule_heights()
			"prize":
				ok = _rule_prize()
			"commons":
				ok = _rule_commons()
			"hidden":
				ok = _rule_hidden()
		if not ok:
			_step("skipped " + kind, "No room for a %s here; the map goes without." % kind)


func _lane_edges_in_mid() -> Array:
	var out := []
	for e in edges:
		if e["kind"] != "route" or not e.has("lane") or e.get("used", false):
			continue
		var a: Dictionary = nodes[e["a"]]
		var b: Dictionary = nodes[e["b"]]
		if a["kind"] == "gate" or b["kind"] == "gate":
			continue
		var mid := ((a["pos"] as Vector2) + (b["pos"] as Vector2)) * 0.5
		var dm := _district_at(mid)
		if dm == CONTESTED or dm == OBJ_DIST or a["district"] in [CONTESTED, OBJ_DIST] or b["district"] in [CONTESTED, OBJ_DIST]:
			out.append(e)
	return out


func _pick(arr: Array):
	if arr.is_empty():
		return null
	return arr[rng.randi() % arr.size()]


func _rule_crossing() -> bool:
	var cands := _lane_edges_in_mid().filter(func(e): return edge_len(e) >= 2000.0)
	var e = _pick(cands)
	if e == null:
		return false
	var kv := _variant("crossing")
	var u: int = e["a"]
	var v: int = e["b"]
	var pu: Vector2 = nodes[u]["pos"]
	var pv: Vector2 = nodes[v]["pos"]
	var L := pu.distance_to(pv)
	var w := _vrange(kv["numbers"]["width"])
	var ratio := _vrange(kv["numbers"]["bypass"])
	var dline := (pv - pu).normalized()
	var nrm := Vector2(-dline.y, dline.x)
	var d := L * sqrt(maxf(pow((ratio - 0.6) / 2.0, 2.0) - 0.04, 0.01))
	var sg := 1.0 if rng.randf() < 0.5 else -1.0
	var b1 := pu + dline * 0.2 * L + nrm * sg * d
	var b2 := pu + dline * 0.8 * L + nrm * sg * d
	if not (_inside(b1) and _inside(b2)):
		sg = -sg
		b1 = pu + dline * 0.2 * L + nrm * sg * d
		b2 = pu + dline * 0.8 * L + nrm * sg * d
	b1 = Vector2(clampf(b1.x, canvas * MARGIN, canvas * (1 - MARGIN)), clampf(b1.y, canvas * MARGIN, canvas * (1 - MARGIN)))
	b2 = Vector2(clampf(b2.x, canvas * MARGIN, canvas * (1 - MARGIN)), clampf(b2.y, canvas * MARGIN, canvas * (1 - MARGIN)))
	_step("crossing", "")
	var mid := (pu + pv) * 0.5
	var m := _add_node("crossing", kv["id"], mid, -1, {"name": _uniq_name(kv["skins"][rng.randi() % kv["skins"].size()]), "choke_width": int(w)})
	var lane: int = e["lane"]
	# The old edge becomes two choke edges meeting at the crossing node.
	e["b"] = m
	e["choke"] = true
	e["closed"] = true
	e["width"] = w
	e["used"] = true
	e["fx_step"] = cur_step
	var e2 := _add_edge(m, v, "route", w, {"lane": lane, "choke": true, "closed": true, "used": true, "fx_step": cur_step, "step": e["step"]})
	var wl := rng.randf_range(700.0, 1100.0)
	var n1 := _add_node("waypoint", "", b1, -1, {"loop": true})
	var n2 := _add_node("waypoint", "", b2, -1, {"loop": true})
	_add_edge(u, n1, "loop", wl)
	var mid_edge := _add_edge(n1, n2, "loop", wl)
	_add_edge(n2, v, "loop", wl)
	var through := edge_len(e) + edge_len(edges[e2])
	var round_len := 0.0
	for k in [edges.size() - 3, edges.size() - 2, edges.size() - 1]:
		round_len += edge_len(edges[k])
	var extra := int(maxf(round_len - through, 0.0) / kits["walk_speed"])
	if kv.get("twin", false):
		var em: Dictionary = edges[mid_edge]
		em["choke"] = true
		em["closed"] = true
		em["hidden"] = true
		em["width"] = _vrange(kv["numbers"]["width"])
	nodes[m]["choice"] = _fmt(kv["choice"], {"fire": _fire(w), "extra": extra})
	nodes[m]["nums"] = {"width": int(w), "bypass": snappedf(round_len / maxf(through, 1.0), 0.1), "extra_s": extra}
	nodes[m]["loop_nodes"] = [n1, n2]
	steps[cur_step]["text"] = "Crossing: %s on the %s route; %d wu choke, way round %.1fx." % [nodes[m]["name"], "short", int(w), round_len / maxf(through, 1.0)]
	_stamp(cur_step, [m, n1, n2], [mid_edge, edges.size() - 3, edges.size() - 1])
	return true


func _stamp(step: int, node_ids: Array, edge_ids: Array) -> void:
	for n in node_ids:
		nodes[n]["step"] = step
	for e in edge_ids:
		edges[e]["step"] = step


func _rule_heights() -> bool:
	var e = _pick(_lane_edges_in_mid().filter(func(x): return edge_len(x) >= 1800.0))
	if e == null:
		return false
	var hv := _variant("heights")
	var u: int = e["a"]
	var v: int = e["b"]
	var pu: Vector2 = nodes[u]["pos"]
	var pv: Vector2 = nodes[v]["pos"]
	var mid := (pu + pv) * 0.5
	var nrm := (pv - pu).orthogonal().normalized()
	var off := rng.randf_range(1500.0, 2300.0)
	var sg := 1.0 if rng.randf() < 0.5 else -1.0
	if not _inside(mid + nrm * sg * off):
		sg = -sg
	var hp := mid + nrm * sg * off
	var band := int(_vrange(hv["numbers"]["band"]) + 0.5)
	var cw := _vrange(hv["numbers"]["climb"])
	_step("heights", "")
	var h := _add_node("heights", hv["id"], hp, -1, {"name": _uniq_name(hv["skins"][rng.randi() % hv["skins"].size()]), "band": band, "strongpoint": hv.get("strongpoint", false)})
	var c1 := _add_edge(u, h, "climb", cw, {"closed": true})
	var c2 := _add_edge(v, h, "climb", cw, {"closed": true, "meander": rng.randf_range(1.25, 1.6)})
	var ov := _add_edge(h, u, "overlook", 0.0, {"target": mid})
	var extra := int(absf(edge_len(edges[c2]) - edge_len(edges[c1])) / kits["walk_speed"])
	nodes[h]["choice"] = _fmt(hv["choice"], {"band": band, "extra": extra})
	nodes[h]["nums"] = {"band": band, "climb": int(cw), "second_way_s": extra}
	steps[cur_step]["text"] = "Heights: %s, %d band(s), overlooks the road with two ways up." % [nodes[h]["name"], band]
	_stamp(cur_step, [h], [c1, c2, ov])
	return true


func _rule_prize() -> bool:
	# A significant resource must be equally far from both sides, so the pair hangs off the
	# centre waypoint of a lane, one each side of the road.
	var pv := _variant("prize")
	var width := _vrange(pv["numbers"]["width"])
	var spur := _vrange(pv["numbers"]["spur"])
	var cands := []
	for l in lane_ids.size():
		var nid: int = lane_ids[l][3]
		if nodes[nid]["kind"] == "waypoint" and not nodes[nid].get("piece", false):
			cands.append(nid)
	var wc = _pick(cands)
	if wc == null:
		return false
	var sg := 1.0 if rng.randf() < 0.5 else -1.0
	_step("prize pair", "")
	var pv_b: Dictionary = pv
	if sym == "separate":
		pv_b = _variant("prize", rng_b, pv["id"])
	var wb := clampf(width, pv_b["numbers"]["width"][0], pv_b["numbers"]["width"][1])
	var sb := clampf(spur, pv_b["numbers"]["spur"][0], pv_b["numbers"]["spur"][1])
	var pa := _spur(wc, pv, width, spur, sg, -1, true)
	var pb := _spur(wc, pv_b, wb, sb, -sg, -1, true)
	nodes[wc]["piece"] = true
	nodes[pa]["pair"] = pb
	nodes[pb]["pair"] = pa
	steps[cur_step]["text"] = "Prize pair: %s and %s, either side of the road at its middle, equally far from both homes." % [nodes[pa]["name"], nodes[pb]["name"]]
	var es := []
	for e in edges:
		if e["step"] == cur_step:
			es.append(e["id"])
	_stamp(cur_step, [pa, pb], es)
	return true


func _rule_commons() -> bool:
	var cands := []
	for l in lane_ids.size():
		for i in range(1, 6):
			var nid: int = lane_ids[l][i]
			var n: Dictionary = nodes[nid]
			if n["kind"] == "waypoint" and not n.get("piece", false) and n["district"] in [CONTESTED, OBJ_DIST]:
				cands.append(nid)
	var nid = _pick(cands)
	if nid == null:
		return false
	var cv := _variant("commons")
	var w := _vrange(cv["numbers"]["width"])
	_step("commons", "")
	var n: Dictionary = nodes[nid]
	n["kind"] = "commons"
	n["variant"] = cv["id"]
	n["name"] = _uniq_name(cv["skins"][rng.randi() % cv["skins"].size()])
	n["choice"] = _fmt(cv["choice"], {"width": int(w)})
	n["nums"] = {"width": int(w)}
	n["piece"] = true
	for e in edges:
		if (e["a"] == nid or e["b"] == nid) and e["kind"] == "route":
			e["width"] = w
			e["open"] = true
			e["fx_step"] = cur_step
	steps[cur_step]["text"] = "Commons: %s, %d wu of open ground on the road." % [n["name"], int(w)]
	return true


func _rule_hidden() -> bool:
	var o: int = districts_route[0]
	var li := _lane_pos(o)
	if li.x < 0:
		return false
	var s: int = recipe["objective_side"]
	var toward := 1 if s == 0 else -1
	var j: int = clampi(li.y + 2 * toward, 0, WAY_T.size() - 1)
	var other: int = lane_ids[li.x][j]
	var hv := _variant("hidden")
	var w := _vrange(hv["numbers"]["width"])
	var po: Vector2 = nodes[o]["pos"]
	var pj: Vector2 = nodes[other]["pos"]
	var mid := (po + pj) * 0.5
	var nrm := (pj - po).orthogonal().normalized()
	var sg := 1.0 if rng.randf() < 0.5 else -1.0
	var off := rng.randf_range(1400.0, 2200.0)
	if not _inside(mid + nrm * sg * off):
		sg = -sg
	_step("hidden approach", "")
	var h := _add_node("hidden", hv["id"], mid + nrm * sg * off, -1, {"name": _uniq_name(hv["skins"][rng.randi() % hv["skins"].size()]),
		"choice": _fmt(hv["choice"], {"width": int(w)}), "nums": {"width": int(w)}})
	var e1 := _add_edge(h, o, "hidden", w, {"closed": true, "hidden": true})
	var e2 := _add_edge(h, other, "hidden", w, {"closed": true, "hidden": true})
	steps[cur_step]["text"] = "Hidden approach: %s gives the objective a second way in, %d wu wide, out of sight of the road." % [nodes[h]["name"], int(w)]
	_stamp(cur_step, [h], [e1, e2])
	return true


# ---------- tuning: meander until walking distances match ----------

func _tune() -> void:
	var tol: float = kits["tolerances"]["equal_distance"]
	var cap: float = kits["tolerances"]["meander_max"]
	for round_i in 24:
		var changed := false
		for t in Checks.equal_targets({"nodes": nodes}):
			var ga := Checks.dists({"nodes": nodes, "edges": edges}, _home_id(0))
			var gb := Checks.dists({"nodes": nodes, "edges": edges}, _home_id(1))
			var da: float = ga["dist"][t]
			var db: float = gb["dist"][t]
			if absf(da - db) / maxf(da, db) <= tol * 0.5:
				continue
			var short_g: Dictionary = ga if da < db else gb
			var delta := absf(da - db)
			var path := Checks.path_edges({"nodes": nodes, "edges": edges}, short_g, t)
			var editable := []
			var total := 0.0
			for ei in path:
				var e: Dictionary = edges[ei]
				if e["kind"] in ["route", "loop", "link"] and e["meander"] < cap - 0.001:
					editable.append(ei)
					total += edge_len(e)
			if editable.is_empty() or total <= 0.0:
				continue
			var f := 1.0 + delta / total
			for ei in editable:
				edges[ei]["meander"] = minf(cap, edges[ei]["meander"] * f)
			changed = true
		if not changed:
			break


func _home_id(side: int) -> int:
	for n in nodes:
		if n["kind"] == "home" and n["side"] == side:
			return n["id"]
	return 0
