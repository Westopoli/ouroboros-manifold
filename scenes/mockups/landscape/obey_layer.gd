extends Node

# Terrain-obeys mockup, pass 1 (docs/northstar/plans/2026-10-15-terrain-obeys-mockup-spec.md).
# Requests from the seed, terrain edits, the route check and the shot driver. Drawing is obey_overlay.gd.
# See also: tests/test_mockup_obey.gd (the contract), landscape_mockup.gd obey_report().
#
# Where the edits go: the spec wants them after the landform stages (Pass4Terrain.shape,
# Pass6Shape.apply) and before the band fit (Pass4Terrain.cut_ramps stores band_lo/band_step, then
# Pass4Terrain.analyse). FieldMap.generate has no hook there and field_map.gd is not this piece's file, so
# _sync() runs right after hud.gd finished a regenerate: it edits the grid elevation, runs cut_ramps again
# (which refits the bands over the edited field), then analyse (steep mask, slopes), then rebuilds the ground.

const OverlayScript := preload("res://scenes/mockups/landscape/obey_overlay.gd")
const WALK_LIMIT_DEG := 35.0
const CANVAS_CYCLE: Array = [8000.0, 16000.0]
const SHOT_CANVASES: Array = [16000, 8000]
const SHOT_SEEDS: Array = [1, 2, 3]
const POINTS: Array = ["base_b", "objective", "site_0", "site_1"]
const SEED_ANGLE := 470
const SEED_ROLLS := 480
const RING_CLEARANCE_WU := 450.0
# a pad's ring zone: the ring (to pad + 300) plus the slope footprint's reach (150) and one sample cell
const ZONE_WU := 600.0

# [name, default, nudge step]; every number a named draft, shown in the panel, moved by [ ] when selected.
const DRAFTS: Array = [
	["base-inset", 2400.0, 100.0],
	["resource-clearance", 2400.0, 100.0],
	["route-small-width", 180.0, 20.0],
	["route-big-width", 600.0, 50.0],
	["vantage-offset", 1500.0, 100.0],
	["base-pad", 1200.0, 100.0],
	["objective-pad", 600.0, 50.0],
	["site-pad", 400.0, 50.0],
	["choke-wall", 900.0, 100.0],
	["wall-rise", 400.0, 50.0],
	["vantage-rise", 300.0, 50.0],
	["route-max-count", 4.0, 1.0],
	["obey-budget", 250.0, 50.0],
	["choke-length", 600.0, 100.0],
	["wall-gap", 125.0, 20.0],
	["wall-face", 100.0, 20.0],
	["ramp-grade", 28.0, 1.0],
	["ramp-reach", 2400.0, 200.0],
	["vantage-radius", 250.0, 50.0],
	["objective-offset", 1500.0, 100.0],
	["pad-scale-floor", 0.6, 0.1],
	["carve-cost", 6.0, 1.0],
	["carve-shoulder", 150.0, 50.0],
	["obey-budget-2", 500.0, 50.0],
	["site-line-clearance", 900.0, 100.0],
]

var draft: Dictionary = {}
var selected := 0
var req: Dictionary = {}
var res: Dictionary = {}
var fm: FieldMap
var overlay: Control

var _hud
var _camera_rig: Node3D
var _fm_done: FieldMap
var _visual_stale := false
var _started := false
var carved := PackedInt32Array()
var carved_routes := 0
var carve_ms := 0.0
var _pin := PackedByteArray()
var _blocked := PackedByteArray()
var _zone := PackedByteArray()
var _carved_set := PackedByteArray()


func _ready() -> void:
	for d in DRAFTS:
		draft[d[0]] = d[1]
	# This node sits before the HUD in the scene, so this runs before the HUD's _ready: the first generate
	# is at this mockup's own canvas and seed instead of the HUD's defaults (24,000 wu, seed 11), and
	# the keys below (V, C) are read before the HUD's own use of them.
	_hud = get_node("../HUD")
	_camera_rig = get_node("../CameraRig")
	_hud._canvas = CANVAS_CYCLE[1]
	get_node("../HUD/VBoxContainer/SeedSpinBox").value = 1
	var canvas_layer := CanvasLayer.new()
	canvas_layer.layer = 5
	add_child(canvas_layer)
	overlay = OverlayScript.new()
	overlay.layer = self
	overlay.set_anchors_preset(Control.PRESET_FULL_RECT)
	overlay.mouse_filter = Control.MOUSE_FILTER_IGNORE
	canvas_layer.add_child(overlay)
	_start.call_deferred()


func _start() -> void:
	var args := OS.get_cmdline_user_args()
	var shot := args.find("--shot")
	if shot >= 0 and shot + 1 < args.size():
		await _run_shots(args[shot + 1])
	_started = true


func _process(_delta: float) -> void:
	if _started:
		_sync()
		_rebuild_visual()


func _input(event: InputEvent) -> void:
	if not (event is InputEventKey and event.pressed and not event.echo):
		return
	var handled := true
	match event.keycode:
		KEY_V:
			overlay.visible = not overlay.visible
		KEY_F1, KEY_F2, KEY_F3:
			_hud.qa_seed(event.keycode - KEY_F1 + 1)
		KEY_C:
			var at: int = CANVAS_CYCLE.find(float(_hud.get_canvas_wu()))
			_hud.qa_set_canvas(CANVAS_CYCLE[(at + 1) % CANVAS_CYCLE.size()])
		KEY_COMMA:
			selected = (selected + DRAFTS.size() - 1) % DRAFTS.size()
			overlay.set_panel(result_text(), draft_text())
		KEY_PERIOD:
			selected = (selected + 1) % DRAFTS.size()
			overlay.set_panel(result_text(), draft_text())
		KEY_BRACKETLEFT, KEY_BRACKETRIGHT:
			var d: Array = DRAFTS[selected]
			var sign := 1.0 if event.keycode == KEY_BRACKETRIGHT else -1.0
			draft[d[0]] = maxf(float(draft[d[0]]) + sign * d[2], d[2])
			_hud.qa_regenerate()
		_:
			handled = false
	if handled:
		get_viewport().set_input_as_handled()


# ---------------------------------------------------------------- report

func obey_report() -> Dictionary:
	_sync()
	return res.get("report", {})


func request_positions() -> Dictionary:
	_sync()
	var out := {}
	for p in req.pads:
		out[p.name] = p.pos
	return out


func request_pads() -> Dictionary:
	_sync()
	var out := {}
	for p in req.pads:
		out[p.name] = p.r
	return out


func carved_cell_list() -> PackedInt32Array:
	_sync()
	return carved


# ---------------------------------------------------------------- sync with the hud's regenerate

func _sync() -> void:
	var current: FieldMap = _hud.get_field_map()
	if current == null or current == _fm_done or _hud.get_kit_name() == "space":
		return
	_fm_done = current
	fm = current
	req = build_requests(_hud.get_seed(), fm.canvas)
	var t0 := Time.get_ticks_usec()
	_apply_edits()
	carve_ms = (Time.get_ticks_usec() - t0) / 1000.0
	_refit_and_rebuild()
	res = _check()
	res.report["check_ms"] += carve_ms
	overlay.set_panel(result_text(), draft_text())
	overlay.queue_redraw()


func _d(name: String) -> float:
	return draft[name]


# ---------------------------------------------------------------- 1. requests from the seed (no terrain read)

func build_requests(p_seed: int, canvas: float) -> Dictionary:
	var ra := RandomNumberGenerator.new()
	ra.seed = p_seed + SEED_ANGLE
	var angle := ra.randf() * TAU
	var dir := Vector2(cos(angle), sin(angle))
	var centre := Vector2(canvas, canvas) * 0.5
	var to_edge := canvas * 0.5 / maxf(absf(dir.x), absf(dir.y))
	var sc := maxf(canvas / 16000.0, _d("pad-scale-floor"))
	var t := maxf(to_edge - _d("base-inset") * sc, 0.0)
	var base_a := centre - dir * t
	var base_b := centre + dir * t
	var rb := RandomNumberGenerator.new()
	rb.seed = p_seed + SEED_ROLLS
	var frac := lerpf(0.35, 0.65, rb.randf())
	var width := lerpf(_d("route-small-width"), _d("route-big-width"), rb.randf())
	var side := 1.0 if rb.randf() < 0.5 else -1.0
	var route_count := 2 + int(floor(rb.randf() * 3.0))
	var obj_side := 1.0 if rb.randf() < 0.5 else -1.0
	var perp := dir.orthogonal()
	var rc := _d("resource-clearance") * sc
	# the nearer site must sit at least DRAFT-site-line-clearance off the base line (scaled down, it would land on
	# the line and the choke); the objective moves out instead. The half wu is float margin so the test's own
	# cross product reads >= the draft.
	var off := _d("objective-offset")
	if absf(off - rc) < _d("site-line-clearance"):
		off = rc + _d("site-line-clearance")
	var objective := centre + perp * obj_side * (off + 0.5)
	var pads: Array = [
		{"name": "base_a", "pos": base_a, "r": _d("base-pad") * sc},
		{"name": "base_b", "pos": base_b, "r": _d("base-pad") * sc},
		{"name": "objective", "pos": objective, "r": _d("objective-pad") * sc},
		{"name": "site_0", "pos": objective + perp * rc, "r": _d("site-pad") * sc},
		{"name": "site_1", "pos": objective - perp * rc, "r": _d("site-pad") * sc},
	]
	_separate_pads(pads)
	var span := _d("choke-wall") * sc
	var asked_frac := frac
	var clen := _d("choke-length") * sc
	frac = _clear_choke_frac(frac, base_a, base_b, width, span, clen, pads)
	var choke := base_a.lerp(base_b, frac)
	side = _vantage_side(side, choke, perp, pads)
	return {
		"seed": p_seed, "canvas": canvas, "scale": sc, "span": span, "dir": dir, "perp": perp, "angle": angle,
		"choke": choke, "choke_frac": frac, "choke_frac_asked": asked_frac, "choke_w": width, "choke_len": clen,
		"vantage": choke + perp * side * _d("vantage-offset"), "vantage_side": side,
		"route_count": route_count,
		"pads": pads,
	}


# Pads that overlap are shrunk until their centres are at least the radii sum apart (Q: pads must not overlap).
func _separate_pads(pads: Array) -> void:
	for it in range(8):
		var moved := false
		for i in range(pads.size()):
			for j in range(i + 1, pads.size()):
				var d: float = pads[i].pos.distance_to(pads[j].pos)
				var sum: float = pads[i].r + pads[j].r
				if d < sum:
					var f := d / sum * 0.98
					pads[i].r *= f
					pads[j].r *= f
					moved = true
		if not moved:
			break


# The choke's wall block must not cut a pad: slide the choke along the base line, inside [0.35, 0.65], to the
# nearest spot whose block (corridor plus both wall spans) clears every pad by its ring and a footprint window.
# No such spot: the spot with the most room; the check then shows what is left.
func _clear_choke_frac(frac: float, a: Vector2, b: Vector2, width: float, span: float, clen: float, pads: Array) -> float:
	var length := a.distance_to(b)
	var axis := (b - a).normalized()
	var half := Vector2(clen * 0.5, width * 0.5 + span)
	var best := frac
	var best_score := -INF
	var step := 50.0 / length
	var k := 0.0
	while frac - k >= 0.3499 or frac + k <= 0.6501:
		for f in ([frac] if k == 0.0 else [frac - k, frac + k]):
			if f < 0.35 - 0.0001 or f > 0.65 + 0.0001:
				continue
			var box := {"pos": a.lerp(b, f), "axis": axis, "half": half}
			var score := INF
			for p in pads:
				score = minf(score, _sdf(box, p.pos) - p.r)
			if score >= RING_CLEARANCE_WU:
				return f
			if score > best_score + 0.001:
				best_score = score
				best = f
		k += step
	return best


# The vantage keeps the seeded side unless its mound would reach a pad's ring; then the other side.
func _vantage_side(side: float, choke: Vector2, perp: Vector2, pads: Array) -> float:
	var ramp_len := _d("vantage-rise") / tan(deg_to_rad(_d("ramp-grade")))
	for sd in [side, -side]:
		var v: Vector2 = choke + perp * sd * _d("vantage-offset")
		var clear := true
		for p in pads:
			if v.distance_to(p.pos) < p.r + _d("vantage-radius") + ramp_len + RING_CLEARANCE_WU:
				clear = false
		if clear:
			return sd
	return side


# ---------------------------------------------------------------- 2. terrain obeys

func _cell_of(p: Vector2) -> Vector2i:
	var s := FieldMap.SPACING
	return Vector2i(clampi(int(round(p.x / s)), 0, fm.dim - 1), clampi(int(round(p.y / s)), 0, fm.dim - 1))


func _median(h: PackedFloat32Array, centre: Vector2, radius: float) -> float:
	var vals := PackedFloat32Array()
	var s := FieldMap.SPACING
	var c0 := _cell_of(centre - Vector2.ONE * radius)
	var c1 := _cell_of(centre + Vector2.ONE * radius)
	for gy in range(c0.y, c1.y + 1):
		for gx in range(c0.x, c1.x + 1):
			if (Vector2(gx, gy) * s).distance_to(centre) <= radius:
				vals.append(h[gy * fm.dim + gx])
	vals.sort()
	return vals[vals.size() / 2]


# Signed distance outside a feature: a disc ("r") or a box ("axis" along its length, "half" = Vector2).
func _sdf(f: Dictionary, p: Vector2) -> float:
	if f.has("r"):
		return p.distance_to(f.pos) - f.r
	var q: Vector2 = p - f.pos
	var l: Vector2 = Vector2(q.dot(f.axis), q.dot(f.axis.orthogonal()))
	var o: Vector2 = Vector2(absf(l.x), absf(l.y)) - f.half
	return Vector2(maxf(o.x, 0.0), maxf(o.y, 0.0)).length() + minf(maxf(o.x, o.y), 0.0)


# A plateau at height h where sdf <= 0, joined to the ground by a cone that never exceeds the ramp grade
# (the ground is clamped into the cone), out to ramp-reach; within fix wu of the plateau the grade is also
# enforced between neighbours (8 directions, true distance), so the pad ring is a ramp, not natural risers.
func _stamp(e: PackedFloat32Array, pin: PackedByteArray, f: Dictionary, h: float, fix: float) -> void:
	var s := FieldMap.SPACING
	var dim := fm.dim
	var g := tan(deg_to_rad(_d("ramp-grade")))
	var reach := _d("ramp-reach")
	var ext: float = f.r if f.has("r") else f.half.length()
	var c0 := _cell_of(f.pos - Vector2.ONE * (ext + reach))
	var c1 := _cell_of(f.pos + Vector2.ONE * (ext + reach))
	var free := PackedInt32Array()
	for gy in range(c0.y, c1.y + 1):
		for gx in range(c0.x, c1.x + 1):
			var i := gy * dim + gx
			if pin[i] == 1:
				continue
			var d := _sdf(f, Vector2(gx, gy) * s)
			if d <= 0.0:
				e[i] = h
				pin[i] = 1
			elif d <= reach:
				var lim := g * d
				e[i] = clampf(e[i], h - lim, h + lim)
				if d <= fix:
					free.append(i)
	var nb := [Vector2i(1, 0), Vector2i(-1, 0), Vector2i(0, 1), Vector2i(0, -1), Vector2i(1, 1), Vector2i(-1, -1), Vector2i(1, -1), Vector2i(-1, 1)]
	for it in range(6):
		for k in range(free.size()):
			var i: int = free[k if it % 2 == 0 else free.size() - 1 - k]
			var x := i % dim
			var y := i / dim
			var v := e[i]
			for o in nb:
				var nx: int = x + o.x
				var ny: int = y + o.y
				if nx < 0 or ny < 0 or nx >= dim or ny >= dim:
					continue
				var lim := g * s * (1.41421356 if o.x != 0 and o.y != 0 else 1.0)
				var nv := e[ny * dim + nx]
				v = clampf(v, nv - lim, nv + lim)
			e[i] = v


func _apply_edits() -> void:
	var dim := fm.dim
	var n := dim * dim
	var s := FieldMap.SPACING
	var nat := PackedFloat32Array()
	nat.resize(n)
	for i in range(n):
		nat[i] = fm.grid[i].elevation
	var e := nat.duplicate()
	var pin := PackedByteArray()
	pin.resize(n)
	_pin = pin
	_blocked = PackedByteArray()
	_blocked.resize(n)
	# (a) pads: plateau at the median ground within 2 * pad, ramped to the ground at the ramp grade; the plateau
	# heights (and the choke floor's) are first brought within ramp-grade of each other over the gaps between
	# them, or the cones of two close pads cut cliffs into each other's rings
	var choke: Vector2 = req.choke
	var axis: Vector2 = req.dir
	var hw: float = req.choke_w * 0.5
	var gap := _d("wall-gap")
	var floor_box := {"pos": choke, "axis": axis, "half": Vector2(req.choke_len * 0.5, hw + gap)}
	var near: Dictionary = req.pads[0]
	for p in req.pads:
		p["h"] = maxf(_median(nat, p.pos, p.r * 2.0), 80.0)
		if p.pos.distance_to(choke) < near.pos.distance_to(choke):
			near = p
	var floor_h: float = near.h
	_level_heights(floor_box, floor_h)
	for p in req.pads:
		_stamp(e, pin, p, p.h, p.r + 600.0)
	# (b) the choke: floor at the levelled height, then walls either side raised by wall-rise
	req["choke_floor_h"] = req.choke_floor_h_levelled
	_stamp(e, pin, floor_box, req.choke_floor_h, 600.0)
	var span: float = req.span
	var t_mid := (hw + gap + hw + span) * 0.5
	var t_half := (span - gap) * 0.5
	var c0 := _cell_of(choke - Vector2.ONE * (hw + span + req.choke_len))
	var c1 := _cell_of(choke + Vector2.ONE * (hw + span + req.choke_len))
	var rise := _d("wall-rise")
	var face := _d("wall-face")
	var wall_gain := PackedFloat32Array()
	wall_gain.resize(n)
	for gy in range(c0.y, c1.y + 1):
		for gx in range(c0.x, c1.x + 1):
			var q: Vector2 = Vector2(gx, gy) * s - choke
			var o := Vector2(absf(q.dot(axis)) - req.choke_len * 0.5, absf(absf(q.dot(axis.orthogonal())) - t_mid) - t_half)
			var d := Vector2(maxf(o.x, 0.0), maxf(o.y, 0.0)).length() + minf(maxf(o.x, o.y), 0.0)
			if d < 0.0:
				wall_gain[gy * dim + gx] = rise * smoothstep(0.0, face, -d)
				_blocked[gy * dim + gx] = 1
	for i in range(n):
		e[i] += wall_gain[i]
	# (c) the vantage mound: rise above the local ground, one ramp face toward the choke, steep elsewhere
	var v: Vector2 = req.vantage
	var vbase := _median(e, v, 600.0)
	var vr := _d("vantage-radius")
	var vtop := vr * 0.5
	var toward := (choke - v).normalized()
	var vrise := _d("vantage-rise")
	var ramp_len := vrise / tan(deg_to_rad(_d("ramp-grade")))
	var steep_len := vrise / tan(deg_to_rad(60.0))
	var m0 := _cell_of(v - Vector2.ONE * (vr + ramp_len + vtop))
	var m1 := _cell_of(v + Vector2.ONE * (vr + ramp_len + vtop))
	for gy in range(m0.y, m1.y + 1):
		for gx in range(m0.x, m1.x + 1):
			var q: Vector2 = Vector2(gx, gy) * s - v
			var dd := q.length()
			var ang := absf(q.angle_to(toward)) if dd > 1.0 else 0.0
			var fall := lerpf(ramp_len, steep_len, smoothstep(deg_to_rad(35.0), deg_to_rad(70.0), ang))
			var k := clampf(1.0 - maxf(dd - vtop, 0.0) / fall, 0.0, 1.0)
			var i := gy * dim + gx
			e[i] = maxf(e[i], vbase + vrise * k) if k > 0.0 else e[i]
	_write_back(e, nat)
	_carve_all(e)
	_write_back(e, nat)


func _level_heights(floor_box: Dictionary, floor_h: float) -> void:
	var g := tan(deg_to_rad(_d("ramp-grade"))) * 0.9
	var hs: Array = []
	var gaps: Dictionary = {}
	var pads: Array = req.pads
	for k in range(pads.size()):
		hs.append(pads[k].h)
	hs.append(floor_h)
	var m := hs.size()
	for a in range(m):
		for b in range(a + 1, m):
			var gp: float
			if b < pads.size():
				gp = pads[a].pos.distance_to(pads[b].pos) - pads[a].r - pads[b].r
			else:
				gp = _sdf(floor_box, pads[a].pos) - pads[a].r
			gaps[a * m + b] = maxf(gp, 0.0) * g
	for it in range(40):
		var moved := false
		for a in range(m):
			for b in range(a + 1, m):
				var diff: float = hs[a] - hs[b]
				var allowed: float = gaps[a * m + b]
				if absf(diff) > allowed + 0.5:
					var excess := (absf(diff) - allowed) * 0.5
					hs[a] -= signf(diff) * excess
					hs[b] += signf(diff) * excess
					moved = true
		if not moved:
			break
	for k in range(pads.size()):
		pads[k].h = maxf(hs[k], 80.0)
	req["choke_floor_h_levelled"] = maxf(hs[m - 1], 80.0)


func _write_back(e: PackedFloat32Array, nat: PackedFloat32Array) -> void:
	for i in range(e.size()):
		if e[i] != nat[i]:
			fm.grid[i].elevation = e[i]
			if e[i] >= 60.0 and fm.grid[i].water >= 0.5:
				fm.grid[i].water = 0.0


# ---------------------------------------------------------------- 2b. route carving (the fourth edit)

# For each strategic point, the roll's route_count routes at small width and one at big width, from base_a:
# a search over the edited ground that may cross unwalkable cells at DRAFT-carve-cost, then the found path is
# graded (never steeper than ramp-grade along it, flat across it) and cut into the ground. Each carved route
# plus a one-cell margin is "taken" for the next search of the same group, so the count sees distinct corridors.
# The wall blocks of the choke are closed to the search: the choke stays the only crossing. See also: _routes()
# (the check's greedy count that these corridors are made for) and _refit_and_rebuild() (carved cells join the
# ramp cells, which the walk mask reads).
func _carve_all(e: PackedFloat32Array) -> void:
	var dim := fm.dim
	var n := dim * dim
	var s := FieldMap.SPACING
	var land := PackedByteArray()
	land.resize(n)
	for i in range(n):
		land[i] = 1 if fm.grid[i].water < 0.5 else 0
	var tn := Pass4Terrain.slope_tan(e, land, dim, fm.p4_footprint)
	var lim := tan(deg_to_rad(WALK_LIMIT_DEG))
	var walk := PackedByteArray()
	walk.resize(n)
	for i in range(n):
		if land[i] == 1 and tn[i] <= lim:
			walk[i] = 1
	_carved_set = PackedByteArray()
	_carved_set.resize(n)
	carved = PackedInt32Array()
	carved_routes = 0
	var pads := {}
	for p in req.pads:
		pads[p.name] = p
	_zone = PackedByteArray()
	_zone.resize(n)
	for gy in range(dim):
		for gx in range(dim):
			var best := INF
			for k in range(req.pads.size()):
				var p: Dictionary = req.pads[k]
				var d: float = (Vector2(gx, gy) * s).distance_to(p.pos) - p.r
				if d <= ZONE_WU and d < best:
					best = d
					_zone[gy * dim + gx] = k + 1
	var a: Dictionary = pads.base_a
	for name in POINTS:
		var b: Dictionary = pads[name]
		for kind in ["small", "big"]:
			var width := _d("route-small-width") if kind == "small" else _d("route-big-width")
			var rad := maxi(ceili(width * 0.5 / s) - 1, 0)
			var count: int = req.route_count if kind == "small" else 1
			var ok := _erode(walk, rad)
			var closed := _closed(rad, [0, req.pads.find(b)])
			var taken := PackedByteArray()
			taken.resize(n)
			for r in range(count):
				var path: PackedInt32Array
				if name == "base_b" and kind == "small" and r == 0:
					path = _choke_path(ok, taken, closed, a, b)
				else:
					path = _search(_cell_idx(a.pos), _cell_idx(b.pos), ok, taken, closed, a, b)
				if path.is_empty():
					break
				_carve_path(e, path, width, walk)
				carved_routes += 1
				var m := 1 + rad
				for i in path:
					var c := Vector2i(i % dim, i / dim)
					if _in_pad(c, a) or _in_pad(c, b):
						continue
					for oy in range(-m, m + 1):
						for ox in range(-m, m + 1):
							var nx := c.x + ox
							var ny := c.y + oy
							if nx >= 0 and ny >= 0 and nx < dim and ny < dim:
								taken[ny * dim + nx] = 1
	for i in range(n):
		if _carved_set[i] == 1:
			carved.append(i)


func _cell_idx(p: Vector2) -> int:
	var c := _cell_of(p)
	return c.y * fm.dim + c.x


func _in_pad(c: Vector2i, pad: Dictionary) -> bool:
	return (Vector2(c) * FieldMap.SPACING).distance_to(pad.pos) <= pad.r


# The first small route to base_b runs the choke corridor itself: search to the corridor's near end, straight
# through the corridor, search on from its far end.
func _choke_path(ok: PackedByteArray, taken: PackedByteArray, closed: PackedByteArray, a: Dictionary, b: Dictionary) -> PackedInt32Array:
	var reach: float = req.choke_len * 0.5 * 0.9
	var c_in := _cell_idx(req.choke - req.dir * reach)
	var c_out := _cell_idx(req.choke + req.dir * reach)
	var first := _search(_cell_idx(a.pos), c_in, ok, taken, closed, a, b)
	var last := _search(c_out, _cell_idx(b.pos), ok, taken, closed, a, b)
	if first.is_empty() or last.is_empty():
		return PackedInt32Array()
	var path := first
	var dim := fm.dim
	var c := Vector2i(c_in % dim, c_in / dim)
	var goal := Vector2i(c_out % dim, c_out / dim)
	while c != goal:
		var d := goal - c
		if absi(d.x) >= absi(d.y):
			c.x += signi(d.x)
		else:
			c.y += signi(d.y)
		path.append(c.y * dim + c.x)
	path.append_array(last)
	return path


# A* over 4-connected cells (cost 1 on cells whose eroded mask is open, DRAFT-carve-cost otherwise; Manhattan
# distance is the heuristic, so f never falls and eight rotating buckets serve as the queue). Closed cells
# (wall blocks and the rings of the pads that are not this route's ends) are never entered; taken cells are
# skipped except inside the two end pads. First found wins ties.
func _search(src: int, dst: int, ok: PackedByteArray, taken: PackedByteArray, closed: PackedByteArray, a: Dictionary, b: Dictionary) -> PackedInt32Array:
	var dim := fm.dim
	var w := dim + 2
	var n := dim * dim
	var dx := dst % dim
	var dy := dst / dim
	var cost := int(_d("carve-cost"))
	var g := PackedInt32Array()
	g.resize(n)
	g.fill(1 << 30)
	var prev := PackedInt32Array()
	prev.resize(n)
	prev.fill(-1)
	var buckets: Array = []
	for k in range(cost + 2):
		buckets.append(PackedInt32Array())
	var nb := buckets.size()
	g[src] = 0
	var f0 := absi(src % dim - dx) + absi(src / dim - dy)
	buckets[f0 % nb].append(src)
	var pending := 1
	var f := f0
	var found := false
	while pending > 0 and not found:
		var cur: PackedInt32Array = buckets[f % nb]
		var at := 0
		while at < cur.size():
			var i := cur[at]
			at += 1
			pending -= 1
			var ix := i % dim
			var iy := i / dim
			if g[i] + absi(ix - dx) + absi(iy - dy) != f:
				continue
			if i == dst:
				found = true
				break
			for o in [-1, 1, -dim, dim]:
				var j: int = i + o
				var jx: int = ix + (o if absi(o) == 1 else 0)
				if jx < 0 or jx >= dim or j < 0 or j >= n:
					continue
				var jy := j / dim
				if closed[j] == 1:
					continue
				if taken[j] == 1:
					var c := Vector2i(jx, jy)
					if not (_in_pad(c, a) or _in_pad(c, b)):
						continue
				var step := 1 if ok[(jy + 1) * w + jx + 1] == 1 else cost
				var ng := g[i] + step
				if ng < g[j]:
					g[j] = ng
					prev[j] = i
					var nf := ng + absi(jx - dx) + absi(jy - dy)
					if nf == f:
						cur.append(j)
					else:
						buckets[nf % nb].append(j)
					pending += 1
		buckets[f % nb] = PackedInt32Array()
		if not found:
			f += 1
	var path := PackedInt32Array()
	if not found:
		return path
	var c := dst
	while c != src:
		path.append(c)
		c = prev[c]
	path.append(src)
	path.reverse()
	return path


# Cells the search may not enter: the wall blocks of the choke and the ring zone of every pad that is not an end
# of this route, grown by the route's half width plus one cell so a carved corridor never reaches into them.
func _closed(rad: int, ends: Array) -> PackedByteArray:
	var dim := fm.dim
	var n := dim * dim
	var raw := PackedByteArray()
	raw.resize(n)
	for i in range(n):
		if _blocked[i] == 1 or (_zone[i] != 0 and not ends.has(_zone[i] - 1)):
			raw[i] = 1
	var m := rad + 1
	var out := PackedByteArray()
	out.resize(n)
	for gy in range(dim):
		for gx in range(dim):
			if raw[gy * dim + gx] == 0:
				continue
			for oy in range(maxi(gy - m, 0), mini(gy + m, dim - 1) + 1):
				for ox in range(maxi(gx - m, 0), mini(gx + m, dim - 1) + 1):
					out[oy * dim + ox] = 1
	for i in range(n):
		if _zone[i] != 0 and ends.has(_zone[i] - 1) and _blocked[i] == 0:
			out[i] = 0
	return out


# Height along the path: the ground's own height, held inside the envelope the pinned cells (pad plateaus, the
# choke floor) allow at ramp-grade, then smoothed so no step exceeds ramp-grade. Cells within width / 2 of the
# path take the path height (flat across), blending to the ground over DRAFT-carve-shoulder. Core cells
# become land and join the carved set. Pinned cells are never touched.
func _carve_path(e: PackedFloat32Array, path: PackedInt32Array, width: float, walk: PackedByteArray) -> void:
	var dim := fm.dim
	var s := FieldMap.SPACING
	var rise := tan(deg_to_rad(_d("ramp-grade"))) * s
	var count := path.size()
	var lo := PackedFloat32Array()
	var hi := PackedFloat32Array()
	lo.resize(count)
	hi.resize(count)
	lo.fill(80.0)
	hi.fill(1.0e9)
	for k in range(count):
		if _pin[path[k]] == 1 or _zone[path[k]] != 0 or _blocked[path[k]] == 1:
			lo[k] = maxf(lo[k], e[path[k]])
			hi[k] = minf(hi[k], e[path[k]])
	for k in range(1, count):
		lo[k] = maxf(lo[k], lo[k - 1] - rise)
		hi[k] = minf(hi[k], hi[k - 1] + rise)
	for k in range(count - 2, -1, -1):
		lo[k] = maxf(lo[k], lo[k + 1] - rise)
		hi[k] = minf(hi[k], hi[k + 1] + rise)
	var h := PackedFloat32Array()
	h.resize(count)
	for k in range(count):
		h[k] = clampf(e[path[k]], lo[k], maxf(hi[k], lo[k]))
	for k in range(1, count):
		h[k] = clampf(h[k], h[k - 1] - rise, h[k - 1] + rise)
	for k in range(count - 2, -1, -1):
		h[k] = clampf(h[k], h[k + 1] - rise, h[k + 1] + rise)
	var half := width * 0.5
	var shoulder := _d("carve-shoulder")
	var reach := ceili((half + shoulder) / s)
	var best_d := {}
	var best_h := {}
	for k in range(count):
		var cx: int = path[k] % dim
		var cy: int = path[k] / dim
		for oy in range(-reach, reach + 1):
			for ox in range(-reach, reach + 1):
				var gx := cx + ox
				var gy := cy + oy
				if gx < 0 or gy < 0 or gx >= dim or gy >= dim:
					continue
				var i := gy * dim + gx
				if _pin[i] == 1 or _blocked[i] == 1:
					continue
				var d := Vector2(ox, oy).length() * s
				if d > half + shoulder:
					continue
				if d < best_d.get(i, INF):
					best_d[i] = d
					best_h[i] = h[k]
	for i in best_d:
		var d: float = best_d[i]
		if _zone[i] != 0:
			# a pad's ring keeps its ground (the ring slope is measured there); the cell joins the route as a ramp cell
			if d <= half:
				_carved_set[i] = 1
				walk[i] = 1
		elif d <= half:
			e[i] = best_h[i]
			fm.grid[i].water = 0.0
			_carved_set[i] = 1
			walk[i] = 1
		else:
			e[i] = lerpf(e[i], best_h[i], 1.0 - smoothstep(half, half + shoulder, d))


# The mockup's own band fit, steep mask and slope finding over the edited field (cut_ramps refits the bands
# and ramps unreached layers; analyse reads them), then the ground and pieces the hud built are rebuilt.
func _refit_and_rebuild() -> void:
	var dim := fm.dim
	var n := dim * dim
	var elev := PackedFloat32Array()
	elev.resize(n)
	for i in range(n):
		elev[i] = fm.grid[i].elevation
	var old_ramps: PackedByteArray = fm.p4_info.get("ramp_cells", PackedByteArray())
	if fm.p4_ramps:
		var core: Vector2 = _find_node("objective") / FieldMap.SPACING
		Pass4Terrain.cut_ramps(fm, elev, core)
		var ramps: PackedByteArray = fm.p4_info.ramp_cells
		if old_ramps.size() == n:
			for i in range(n):
				if old_ramps[i] == 1:
					ramps[i] = 1
	elif not carved.is_empty():
		var ramps := PackedByteArray()
		ramps.resize(n)
		fm.p4_info["ramp_cells"] = ramps
	if not carved.is_empty():
		var ramps: PackedByteArray = fm.p4_info.ramp_cells
		for i in carved:
			ramps[i] = 1
	_visual_stale = true
	if _hud.get_p4().view == "visual":
		_rebuild_visual()
	else:
		_reanalyse()


func _reanalyse() -> void:
	var generated: Node3D = get_node("../World/Generated")
	_hud.get_p4().on_regenerated(fm, generated, false)
	_hud.get_p5().on_regenerated(fm, generated, false)


# The ground and pieces are only rebuilt while the plain view shows them; any other view hides them.
func _rebuild_visual() -> void:
	if not _visual_stale or _hud.get_p4().view != "visual":
		return
	_visual_stale = false
	var generated: Node3D = get_node("../World/Generated")
	for child in generated.get_children():
		child.free()
	var kit: Dictionary = _hud._kits[_hud.get_kit_name()]
	var ground = GroundBuilder.new().build(fm, kit)
	if ground != null:
		ground.name = "GroundMesh"
		generated.add_child(ground)
	Placer.new().place(fm, kit, generated)
	_reanalyse()


func _find_node(type: String) -> Vector2:
	for nd in fm.nodes:
		if nd.type == type:
			return nd.pos
	return Vector2.ZERO


# ---------------------------------------------------------------- 3. the check, on the finished per-band data

func _walk_mask() -> PackedByteArray:
	var p4: Dictionary = fm.p4
	var n := fm.dim * fm.dim
	var land: PackedByteArray = p4.land
	var tn: PackedFloat32Array = p4.tan
	var ramp: PackedByteArray = p4.ramp_cells
	var bridge: PackedByteArray = fm.p5_info.get("bridge", PackedByteArray())
	var lim := tan(deg_to_rad(WALK_LIMIT_DEG))
	var walk := PackedByteArray()
	walk.resize(n)
	for i in range(n):
		if (land[i] == 1 and tn[i] <= lim) or (ramp.size() == n and ramp[i] == 1) or (bridge.size() == n and bridge[i] == 1):
			walk[i] = 1
	return walk


# Cells (padded by one empty cell all round) whose every cell within `rad` cells (square) is walkable.
func _erode(walk: PackedByteArray, rad: int) -> PackedByteArray:
	var dim := fm.dim
	var w := dim + 2
	var row := PackedByteArray()
	row.resize(dim * dim)
	for y in range(dim):
		for x in range(dim):
			var ok := 1
			for k in range(-rad, rad + 1):
				var nx := x + k
				if nx < 0 or nx >= dim or walk[y * dim + nx] == 0:
					ok = 0
					break
			row[y * dim + x] = ok
	var out := PackedByteArray()
	out.resize(w * w)
	for y in range(dim):
		for x in range(dim):
			var ok := 1
			for k in range(-rad, rad + 1):
				var ny := y + k
				if ny < 0 or ny >= dim or row[ny * dim + x] == 0:
					ok = 0
					break
			out[(y + 1) * w + x + 1] = ok
	return out


func _bfs(ok: PackedByteArray, w: int, s: int, t: int, prev: PackedInt32Array, queue: PackedInt32Array) -> PackedInt32Array:
	var path := PackedInt32Array()
	if ok[s] == 0 or ok[t] == 0:
		return path
	prev.fill(-1)
	prev[s] = s
	queue[0] = s
	var head := 0
	var tail := 1
	while head < tail:
		var i := queue[head]
		head += 1
		if i == t:
			break
		var j := i + 1
		if ok[j] == 1 and prev[j] == -1:
			prev[j] = i
			queue[tail] = j
			tail += 1
		j = i - 1
		if ok[j] == 1 and prev[j] == -1:
			prev[j] = i
			queue[tail] = j
			tail += 1
		j = i + w
		if ok[j] == 1 and prev[j] == -1:
			prev[j] = i
			queue[tail] = j
			tail += 1
		j = i - w
		if ok[j] == 1 and prev[j] == -1:
			prev[j] = i
			queue[tail] = j
			tail += 1
	if prev[t] == -1:
		return path
	var c := t
	while c != s:
		path.append(c)
		c = prev[c]
	path.append(s)
	return path


# Greedy separate routes: each found route plus a one-cell margin is removed before the next search; cells
# inside the two end pads stay open, so the routes are separate between the pads, not through them.
func _routes(walk: PackedByteArray, rad: int, a: Dictionary, b: Dictionary) -> Array:
	var dim := fm.dim
	var w := dim + 2
	var s := FieldMap.SPACING
	var ok := _erode(walk, rad)
	var prev := PackedInt32Array()
	prev.resize(w * w)
	var queue := PackedInt32Array()
	queue.resize(w * w)
	var ca := _cell_of(a.pos)
	var cb := _cell_of(b.pos)
	var ra := ceili(a.r / s)
	var rb := ceili(b.r / s)
	var found: Array = []
	var m := 1 + rad
	var max_count := int(_d("route-max-count"))
	while found.size() < max_count:
		var path := _bfs(ok, w, (ca.y + 1) * w + ca.x + 1, (cb.y + 1) * w + cb.x + 1, prev, queue)
		if path.is_empty():
			break
		var line := PackedVector2Array()
		for idx in path:
			var cx: int = idx % w - 1
			var cy: int = idx / w - 1
			line.append(Vector2(cx, cy) * s)
			if Vector2(cx - ca.x, cy - ca.y).length() <= ra or Vector2(cx - cb.x, cy - cb.y).length() <= rb:
				continue
			for oy in range(-m, m + 1):
				for ox in range(-m, m + 1):
					ok[(cy + oy + 1) * w + cx + ox + 1] = 0
		found.append(line)
	return found


func _walkable_at(walk: PackedByteArray, p: Vector2) -> bool:
	var c := _cell_of(p)
	return walk[c.y * fm.dim + c.x] == 1


# Narrowest cross-section of walkable ground, across the corridor, along the corridor's length, in wu.
func _choke_measured(walk: PackedByteArray) -> float:
	var axis: Vector2 = req.dir
	var perp: Vector2 = req.perp
	var half: float = req.choke_len * 0.5
	var best := INF
	var along := -half + 50.0
	while along <= half - 50.0:
		var q: Vector2 = req.choke + axis * along
		var width := 0.0
		if _walkable_at(walk, q):
			for sign in [1.0, -1.0]:
				var k := 1
				while k <= 200 and _walkable_at(walk, q + perp * sign * 10.0 * k):
					k += 1
				width += 10.0 * (k - 1)
		best = minf(best, width)
		along += 50.0
	return best


# A small route from base_a to base_b that runs through the choke: base_a to the corridor's centre, then on to
# base_b (both legs found over the finished walk mask, one cell wide).
func _choke_on_route(walk: PackedByteArray) -> bool:
	var dim := fm.dim
	var w := dim + 2
	var ok := _erode(walk, 0)
	var prev := PackedInt32Array()
	prev.resize(w * w)
	var queue := PackedInt32Array()
	queue.resize(w * w)
	var cc := _cell_of(req.choke)
	var mid := (cc.y + 1) * w + cc.x + 1
	var ca := _cell_of(req.pads[0].pos)
	var cb := _cell_of(req.pads[1].pos)
	return not _bfs(ok, w, (ca.y + 1) * w + ca.x + 1, mid, prev, queue).is_empty() \
		and not _bfs(ok, w, mid, (cb.y + 1) * w + cb.x + 1, prev, queue).is_empty()


func _ring_max_deg(p: Dictionary) -> float:
	var s := FieldMap.SPACING
	var tn: PackedFloat32Array = fm.p4.tan
	var c0 := _cell_of(p.pos - Vector2.ONE * (p.r + 400.0))
	var c1 := _cell_of(p.pos + Vector2.ONE * (p.r + 400.0))
	var worst := 0.0
	for gy in range(c0.y, c1.y + 1):
		for gx in range(c0.x, c1.x + 1):
			var d := (Vector2(gx, gy) * s).distance_to(p.pos)
			if d > p.r - 150.0 and d <= p.r + 300.0:
				worst = maxf(worst, tn[gy * fm.dim + gx])
	return rad_to_deg(atan(worst))


func _check() -> Dictionary:
	var t0 := Time.get_ticks_usec()
	var s := FieldMap.SPACING
	var walk := _walk_mask()
	var small_rad := maxi(ceili(_d("route-small-width") * 0.5 / s) - 1, 0)
	var big_rad := maxi(ceili(_d("route-big-width") * 0.5 / s) - 1, 0)
	var pads := {}
	for p in req.pads:
		pads[p.name] = p
	var routes_small := {}
	var routes_big := {}
	var paths_small := {}
	var paths_big := {}
	var ring := {}
	var ring_max := 0.0
	for name in pads:
		ring[name] = _ring_max_deg(pads[name])
		ring_max = maxf(ring_max, ring[name])
	for name in POINTS:
		var ps := _routes(walk, small_rad, pads.base_a, pads[name])
		var pb := _routes(walk, big_rad, pads.base_a, pads[name])
		routes_small[name] = ps.size()
		routes_big[name] = pb.size()
		paths_small[name] = ps
		paths_big[name] = pb
	var measured := _choke_measured(walk)
	var on_route := _choke_on_route(walk)
	var fails: Array = []
	if absf(measured - req.choke_w) > s:
		fails.append("choke")
	if not on_route:
		fails.append("choke_route")
	var line: Vector2 = (pads.base_b.pos - pads.base_a.pos).normalized()
	if absf((pads.objective.pos - pads.base_a.pos).cross(line)) < _d("objective-offset"):
		fails.append("offset")
	var plist: Array = req.pads
	var overlap := false
	for i in range(plist.size()):
		for j in range(i + 1, plist.size()):
			if plist[i].pos.distance_to(plist[j].pos) < plist[i].r + plist[j].r:
				overlap = true
	if overlap:
		fails.append("pads")
	for i in carved:
		if walk[i] == 0:
			fails.append("carved")
			break
	if ring_max > WALK_LIMIT_DEG:
		fails.append("ring")
	for name in POINTS:
		if routes_small[name] < req.route_count or routes_big[name] < 1:
			fails.append("routes:" + name)
	var report := {
		"pass": fails.is_empty(),
		"choke_asked_wu": req.choke_w,
		"choke_measured_wu": measured,
		"routes_small": routes_small,
		"routes_big": routes_big,
		"pad_ring_max_deg": ring_max,
		"route_count": req.route_count,
		"carved_cells": carved.size(),
		"carved_routes": carved_routes,
		"choke_on_route": on_route,
		"check_ms": (Time.get_ticks_usec() - t0) / 1000.0,
	}
	return {"report": report, "fails": fails, "ring": ring, "paths_small": paths_small, "paths_big": paths_big, "walk": walk}


# ---------------------------------------------------------------- panel

func result_text() -> String:
	if res.is_empty():
		return "OBEY: waiting for a generated field"
	var r: Dictionary = res.report
	var lines: Array = []
	lines.append("OBEY pass 2   seed %d   canvas %d   %s" % [req.seed, int(req.canvas), "PASS" if r.pass else "FAIL (" + ", ".join(res.fails) + ")"])
	lines.append("check %.0f ms incl. carving %.0f (draft %d)   route_count %d (2 + floor(u*3))" % [r.check_ms, carve_ms, int(_d("obey-budget-2")), r.route_count])
	lines.append("carved %d cells in %d routes   choke on a route: %s   pad scale %.2f   span %d wu" % [r.carved_cells, r.carved_routes, r.choke_on_route, req.scale, int(req.span)])
	lines.append("choke asked %d wu, measured %d wu   at %.2f of the base line (rolled %.2f)" % [int(r.choke_asked_wu), int(r.choke_measured_wu), req.choke_frac, req.choke_frac_asked])
	lines.append("per point: routes small / big (need %d / 1), pad ring max slope (limit %d deg)" % [r.route_count, int(WALK_LIMIT_DEG)])
	for name in POINTS:
		var bad: bool = r.routes_small[name] < r.route_count or r.routes_big[name] < 1 or res.ring[name] > WALK_LIMIT_DEG
		lines.append("  %-9s small %d  big %d  ring %.1f deg  %s" % [name, r.routes_small[name], r.routes_big[name], res.ring[name], "FAIL" if bad else "ok"])
	lines.append("  base_a                         ring %.1f deg  %s" % [res.ring.base_a, "FAIL" if res.ring.base_a > WALK_LIMIT_DEG else "ok"])
	lines.append("keys: V overlay  F1-F3 seed  C canvas  R regenerate")
	lines.append("drafts: , . select  [ ] nudge")
	return "\n".join(lines)


func draft_text() -> String:
	var lines: Array = []
	for k in range(DRAFTS.size()):
		lines.append("%s %s %s" % [">" if k == selected else " ", DRAFTS[k][0], str(snappedf(draft[DRAFTS[k][0]], 0.01))])
	return "\n".join(lines)


func panel_text() -> String:
	return result_text() + "\n" + draft_text()


# ---------------------------------------------------------------- --shot <dir>

# The shot shows the map, the overlay and this panel only: the pass-4/5 panels and graph are hidden.
func _declutter() -> void:
	var p4 = _hud.get_p4()
	var p5 = _hud.get_p5()
	p5.set_graph(false)
	p5.set_places(false)
	for c in [p4._panel, p4._cursor, p5._boxpanel, p5._panel, p5._key, _hud.get_node("VBoxContainer")]:
		c.visible = false


func _run_shots(dir: String) -> void:
	DirAccess.make_dir_recursive_absolute(dir)
	_hud.get_p4().set_limit(35.0)
	_hud.get_p4().set_view("walk")
	# 16,000 seeds 1..3 then 8,000 seeds 3..1: each step changes one thing, so each costs one generate.
	for plan in [[16000, SHOT_SEEDS], [8000, SHOT_SEEDS.duplicate()]]:
		var canvas: int = plan[0]
		var seeds: Array = plan[1]
		if canvas != SHOT_CANVASES[0]:
			seeds.reverse()
		for sd in seeds:
			if int(_hud.get_canvas_wu()) != canvas:
				_hud.qa_set_canvas(float(canvas))
			elif _hud.get_seed() != sd:
				_hud.qa_seed(sd)
			await get_tree().process_frame
			_sync()
			_declutter()
			_camera_rig.set_top_down(true)
			_camera_rig.set_height(float(canvas) * 1.02)
			_camera_rig.pan_to(Vector3(canvas * 0.5, 0.0, canvas * 0.5))
			overlay.visible = true
			overlay.queue_redraw()
			await get_tree().process_frame
			await get_tree().process_frame
			_camera_rig.pan_to(Vector3(canvas * 0.5, 0.0, canvas * 0.5))
			await RenderingServer.frame_post_draw
			var img := get_viewport().get_texture().get_image()
			img.save_png(dir.path_join("obey_%d_%d.png" % [canvas, sd]))
			var f := FileAccess.open(dir.path_join("obey_panel_%d_%d.txt" % [canvas, sd]), FileAccess.WRITE)
			f.store_string(panel_text() + "\n")
			f.close()
	get_tree().quit(0)
