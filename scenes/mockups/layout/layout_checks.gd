extends RefCounted
# Layout prototype pass 1: checks on a generated map, and its signature. Pure functions on data.
# See also: layout_gen.gd (calls run() on every candidate and keeps the best by score()).
# All thresholds are drafts (Q-191-05); Westley owns them.

const CHECK_IDS := ["connected", "matched", "equal", "bypass", "approaches", "choices", "objective", "distinct"]
const WALKABLE_SKIP := ["overlook"]


# Shortest walking distances from src over walkable edges (overlook edges are sight lines, not routes).
static func dists(m: Dictionary, src: int, skip := {}) -> Dictionary:
	var nodes: Array = m["nodes"]
	var edges: Array = m["edges"]
	var n := nodes.size()
	var dist := []
	var prev := []
	var prev_edge := []
	var done := []
	for i in n:
		dist.append(INF)
		prev.append(-1)
		prev_edge.append(-1)
		done.append(false)
	var adj := []
	for i in n:
		adj.append([])
	for e in edges:
		if e["kind"] in WALKABLE_SKIP or skip.has(e["id"]):
			continue
		adj[e["a"]].append(e["id"])
		adj[e["b"]].append(e["id"])
	dist[src] = 0.0
	for _i in n:
		var u := -1
		var best := INF
		for i in n:
			if not done[i] and dist[i] < best:
				best = dist[i]
				u = i
		if u < 0:
			break
		done[u] = true
		for ei in adj[u]:
			var e: Dictionary = edges[ei]
			var v: int = e["b"] if e["a"] == u else e["a"]
			var w: float = (nodes[e["a"]]["pos"] as Vector2).distance_to(nodes[e["b"]]["pos"]) * e["meander"]
			if dist[u] + w < dist[v]:
				dist[v] = dist[u] + w
				prev[v] = u
				prev_edge[v] = ei
	return {"dist": dist, "prev": prev, "prev_edge": prev_edge, "src": src}


static func path_edges(_m: Dictionary, g: Dictionary, target: int) -> Array:
	var out := []
	var cur := target
	while cur != g["src"] and g["prev"][cur] >= 0:
		out.append(g["prev_edge"][cur])
		cur = g["prev"][cur]
	out.reverse()
	return out


static func path_nodes(_m: Dictionary, g: Dictionary, target: int) -> Array:
	var out := [target]
	var cur := target
	while cur != g["src"] and g["prev"][cur] >= 0:
		cur = g["prev"][cur]
		out.append(cur)
	out.reverse()
	return out


# Places that need equal walking distance from both sides: significant resources, and the
# objective where nobody holds it (every stop of the moving route).
static func equal_targets(m: Dictionary) -> Array:
	var out := []
	for n in m["nodes"]:
		if (n["kind"] == "prize" and n.get("sig", false)) or (n["kind"] == "objective" and n.get("moving", false)):
			out.append(n["id"])
	return out


static func home_id(m: Dictionary, side: int) -> int:
	for n in m["nodes"]:
		if n["kind"] == "home" and n["side"] == side:
			return n["id"]
	return 0


static func objective_ids(m: Dictionary) -> Array:
	var out := []
	for n in m["nodes"]:
		if n["kind"] == "objective":
			out.append(n["id"])
	return out


static func loops(m: Dictionary) -> int:
	var v := 0
	var e := 0
	for n in m["nodes"]:
		v += 1
	for ed in m["edges"]:
		if not (ed["kind"] in WALKABLE_SKIP):
			e += 1
	return e - v + 1


static func run(m: Dictionary, kits: Dictionary, recent: Array) -> void:
	var tol: float = kits["tolerances"]["equal_distance"]
	var bmin: float = kits["tolerances"]["bypass_min"]
	var nodes: Array = m["nodes"]
	var edges: Array = m["edges"]
	var ha := home_id(m, 0)
	var hb := home_id(m, 1)
	var ga := dists(m, ha)
	var gb := dists(m, hb)
	var walk: float = m["walk"]
	var checks := []

	var lost := 0
	for i in nodes.size():
		if ga["dist"][i] == INF:
			lost += 1
	checks.append({"id": "connected", "label": "Connected", "ok": lost == 0,
		"line": "All %d places reach each other." % nodes.size() if lost == 0 else "%d of %d places cannot be reached." % [lost, nodes.size()]})

	var ca: Dictionary = m["homes"]["a"]
	var cb: Dictionary = m["homes"]["b"]
	var fa: float = ca["width"] * ca["gates"].size()
	var fb: float = cb["width"] * cb["gates"].size()
	var ok_m: bool = absf(fa - fb) / maxf(fa, fb) <= 0.05 and absf(ca["radius"] - cb["radius"]) / maxf(ca["radius"], cb["radius"]) <= 0.05 and ca["wall"] == cb["wall"]
	checks.append({"id": "matched", "label": "Sides matched", "ok": ok_m,
		"line": "Home ground %d wu and gate frontage %d wu on both sides." % [int(ca["radius"]), int(fa)] if ok_m else "Home or gate numbers differ: frontage %d vs %d wu, radius %d vs %d wu." % [int(fa), int(fb), int(ca["radius"]), int(cb["radius"])]})

	var targets := equal_targets(m)
	var bad := []
	var worst := 0.0
	for t in targets:
		var da: float = ga["dist"][t]
		var db: float = gb["dist"][t]
		var rel := absf(da - db) / maxf(maxf(da, db), 1.0)
		worst = maxf(worst, rel)
		if rel > tol:
			bad.append(nodes[t]["name"] if nodes[t]["name"] != "" else "stop %d" % nodes[t].get("route_stop", 0))
	checks.append({"id": "equal", "label": "Equal distance", "ok": bad.is_empty() and not targets.is_empty(),
		"line": ("%d place(s) within %d%% (worst %.1f%%, %d s from each side)." % [targets.size(), int(tol * 100.0), worst * 100.0, int(_avg_dist(targets, ga) / walk)]) if bad.is_empty() and not targets.is_empty()
			else ("Nothing to equalise: no significant resource on this map." if targets.is_empty() else "Over %d%%: %s." % [int(tol * 100.0), ", ".join(bad)])})

	var xs := 0
	var short := []
	var min_ratio := INF
	for n in nodes:
		if n["kind"] != "crossing":
			continue
		xs += 1
		var chokes := []
		for e in edges:
			if e["choke"] and (e["a"] == n["id"] or e["b"] == n["id"]) and e["kind"] == "route":
				chokes.append(e)
		if chokes.size() < 2:
			short.append(n["name"])
			continue
		var u: int = chokes[0]["a"] if chokes[0]["b"] == n["id"] else chokes[0]["b"]
		var v: int = chokes[1]["a"] if chokes[1]["b"] == n["id"] else chokes[1]["b"]
		var through := _elen(nodes, chokes[0]) + _elen(nodes, chokes[1])
		var g := dists(m, u, {chokes[0]["id"]: true, chokes[1]["id"]: true})
		var round_len: float = g["dist"][v]
		var ratio := round_len / maxf(through, 1.0)
		min_ratio = minf(min_ratio, ratio)
		if ratio < bmin:
			short.append("%s %.1fx" % [n["name"], ratio])
	checks.append({"id": "bypass", "label": "Way round", "ok": short.is_empty() and xs > 0,
		"line": ("%d crossing(s), way round at least %.1fx the way through." % [xs, min_ratio]) if short.is_empty() and xs > 0
			else ("No crossing on this map." if xs == 0 else "Way round under %.1fx: %s." % [bmin, ", ".join(short)])})

	var objs := objective_ids(m)
	var appr := 0
	var hidden_n := 0
	if not objs.is_empty():
		for e in edges:
			if (e["a"] == objs[0] or e["b"] == objs[0]) and not (e["kind"] in WALKABLE_SKIP):
				appr += 1
				if e["hidden"]:
					hidden_n += 1
	checks.append({"id": "approaches", "label": "Approaches", "ok": appr >= 2,
		"line": "%d approaches to the objective, %d hidden." % [appr, hidden_n] if appr >= 2 else "Only %d approach to the objective." % appr})

	var have := {}
	for n in nodes:
		if n["kind"] == "prize" and not n.get("sig", false):
			continue
		have[n["kind"]] = true
	var missing := []
	for k in m["required"]:
		if not have.has(k):
			missing.append(k)
	checks.append({"id": "choices", "label": "Choices present", "ok": missing.is_empty(),
		"line": "Every choice the recipe asks for is on the map: %s." % ", ".join(m["required"]) if missing.is_empty() else "Missing: %s." % ", ".join(missing)})

	var ok_o := false
	var line_o := ""
	if objs.is_empty():
		line_o = "No objective."
	elif nodes[objs[0]].get("moving", false):
		ok_o = objs.size() >= 3
		line_o = "The objective walks a route of %d stops." % objs.size() if ok_o else "Route too short to walk."
	else:
		var h: int = nodes[objs[0]]["holder"]
		var d_def: float = (ga if h == 0 else gb)["dist"][objs[0]]
		var d_oth: float = (gb if h == 0 else ga)["dist"][objs[0]]
		ok_o = d_def <= 0.6 * d_oth
		line_o = "Objective sits beside the defender: %d s from them, %d s from the attacker." % [int(d_def / walk), int(d_oth / walk)] if ok_o else "Objective is not beside the defender (%d s vs %d s)." % [int(d_def / walk), int(d_oth / walk)]
	checks.append({"id": "objective", "label": "Objective", "ok": ok_o, "line": line_o})

	m["checks"] = checks
	m["loops"] = loops(m)
	m["signature"] = signature(m)
	var dmin := INF
	for s in recent:
		dmin = minf(dmin, sig_distance(m["signature"], s))
	m["sig_min_distance"] = dmin
	var ok_d: bool = recent.is_empty() or dmin >= 1.0
	checks.append({"id": "distinct", "label": "Distinct", "ok": ok_d,
		"line": "No earlier map to compare with." if recent.is_empty() else ("Signature distance to the nearest earlier map: %.1f." % dmin)})


static func _elen(nodes: Array, e: Dictionary) -> float:
	return (nodes[e["a"]]["pos"] as Vector2).distance_to(nodes[e["b"]]["pos"]) * e["meander"]


static func _avg_dist(targets: Array, g: Dictionary) -> float:
	var s := 0.0
	for t in targets:
		s += g["dist"][t]
	return s / maxf(targets.size(), 1)


static func score(m: Dictionary) -> float:
	var passes := 0
	for c in m["checks"]:
		if c["ok"]:
			passes += 1
	var d: float = m.get("sig_min_distance", INF)
	return passes * 100.0 + (minf(d, 5.0) * 5.0 if d != INF else 0.0)


static func pass_count(m: Dictionary) -> int:
	var p := 0
	for c in m["checks"]:
		if c["ok"]:
			p += 1
	return p


# Signature: division pattern, loop count, and the order of piece kinds along each side's route to the objective.
static func signature(m: Dictionary) -> Dictionary:
	var nodes: Array = m["nodes"]
	var objs := objective_ids(m)
	var routes := []
	for s in 2:
		var g := dists(m, home_id(m, s))
		var seq := ""
		if not objs.is_empty():
			var pn := path_nodes(m, g, objs[0])
			var on_path := {}
			for p in pn:
				on_path[p] = true
			for p in pn:
				seq += _letter(nodes[p]["kind"])
				var near := ""
				for e in m["edges"]:
					if e["a"] != p and e["b"] != p:
						continue
					var q: int = e["b"] if e["a"] == p else e["a"]
					if not on_path.has(q) and nodes[q]["kind"] in ["prize", "heights", "hidden"]:
						near += _letter(nodes[q]["kind"])
				var chars := near.split("")
				chars.sort()
				seq += "".join(chars)
		routes.append(_squash(seq))
	return {"division": m["division"], "loops": loops(m), "route_a": routes[0], "route_b": routes[1]}


static func _letter(kind: String) -> String:
	match kind:
		"home": return "H"
		"gate": return "G"
		"crossing": return "X"
		"commons": return "C"
		"prize": return "P"
		"heights": return "U"
		"hidden": return "D"
		"objective": return "O"
	return ""


static func _squash(s: String) -> String:
	var out := ""
	for ch in s:
		if out.is_empty() or out[out.length() - 1] != ch:
			out += ch
	return out


static func _lev(a: String, b: String) -> float:
	if a == b:
		return 0.0
	var prev := []
	for j in b.length() + 1:
		prev.append(j)
	for i in range(1, a.length() + 1):
		var cur := [i]
		for j in range(1, b.length() + 1):
			cur.append(mini(mini(cur[j - 1] + 1, prev[j] + 1), prev[j - 1] + (0 if a[i - 1] == b[j - 1] else 1)))
		prev = cur
	return float(prev[b.length()]) / float(maxi(a.length(), b.length()))


# 0 means the same map to the eye; a few means clearly different.
static func sig_distance(a: Dictionary, b: Dictionary) -> float:
	var d := 0.0 if a["division"] == b["division"] else 1.0
	d += minf(absf(a["loops"] - b["loops"]), 3.0) * 0.5
	d += _lev(a["route_a"], b["route_a"]) * 1.5
	d += _lev(a["route_b"], b["route_b"]) * 1.5
	return d
