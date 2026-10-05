extends RefCounted

# Prototype (disposable): the two groups, movement along a planned route, the slowest-member rule and
# the read-out numbers. A unit is a Dictionary; no drawing.

const WALKER_SPEEDS := [40.0, 80.0, 150.0]
# provisional (prototype draft, 2026-10-05)
const FLYER_SPEED := 80.0
# provisional (prototype draft, 2026-10-05)
const FLYER_START_LAYER := 3
# provisional (prototype draft, 2026-10-05): spacing of the start squads and of a group's targets, wu
const START_SPACING := 700.0
const FORMATION_WU := 140.0

var grid
var units: Array = []
var last := {}


func _init(p_grid) -> void:
	grid = p_grid
	_spawn()


func _spawn() -> void:
	var centre := Vector2(8000, 8000)
	var best := -1
	var bd := INF
	for c in grid.main_cells:
		var d: float = grid.cell_pos(c).distance_squared_to(centre)
		if d < bd:
			bd = d
			best = c
	var home: Vector2 = grid.cell_pos(best)
	var picked: Array = []
	for c in _by_distance(home, grid.main_cells, 0):
		_take(picked, grid.cell_pos(c))
		if picked.size() == 6:
			break
	for p in picked:
		units.append(_unit("w", p, 0))
	picked = []
	var all := PackedInt32Array()
	for i in range(grid.dim * grid.dim):
		all.append(i)
	for c in _by_distance(home + Vector2(-900, 0), all, FLYER_START_LAYER):
		_take(picked, grid.cell_pos(c))
		if picked.size() == 6:
			break
	for p in picked:
		units.append(_unit("f", p, FLYER_START_LAYER))


# Cells nearest to a point; with max_band > 0 only cells whose band is at or below it. First 400 only.
func _by_distance(p: Vector2, cells: PackedInt32Array, max_band: int) -> Array:
	var arr: Array = []
	for c in cells:
		if max_band == 0 or grid.band[c] <= max_band:
			arr.append([grid.cell_pos(c).distance_squared_to(p), c])
	arr.sort()
	var out: Array = []
	for i in range(mini(arr.size(), 400)):
		out.append(arr[i][1])
	return out


func _take(picked: Array, p: Vector2) -> void:
	for q in picked:
		if q.distance_to(p) < START_SPACING:
			return
	picked.append(p)


func _unit(kind: String, p: Vector2, layer: int) -> Dictionary:
	return {"kind": kind, "pos": p, "layer": layer, "route": {}, "cum": [], "t": 0.0, "secs": 0.0, "len": 0.0, "target": p}


func layer_of(u: Dictionary) -> int:
	return grid.band_at(u.pos) if u.kind == "w" else u.layer


func pace_of(sel: Array, walker_speed: float) -> float:
	var pace := INF
	for i in sel:
		pace = minf(pace, walker_speed if units[i].kind == "w" else FLYER_SPEED)
	return pace


func pick(world_rect: Rect2) -> Array:
	var out: Array = []
	for i in range(units.size()):
		if world_rect.has_point(units[i].pos):
			out.append(i)
	return out


func _offset(k: int) -> Vector2:
	if k == 0:
		return Vector2.ZERO
	return Vector2.from_angle(TAU * (k - 1) / 5.0) * FORMATION_WU


func _plan(u: Dictionary, target: Vector2, speed: float, option: String, climb: bool) -> void:
	var r: Dictionary
	if u.kind == "w":
		r = grid.route_walker(u.pos, target, option)
	else:
		r = grid.route_flyer(u.pos, target, u.layer, climb, speed)
	var pts: PackedVector2Array = r.points
	var cum := [0.0]
	for i in range(1, pts.size()):
		cum.append(cum[i - 1] + pts[i - 1].distance_to(pts[i]))
	for tr in r.transfers:
		tr["dist"] = cum[pts.find(tr.pos)]
	u.route = r
	u.target = target
	u.cum = cum
	u.len = cum[cum.size() - 1]
	u.secs = r.seconds_at.call(speed)
	u.t = 0.0
	if u.kind == "w":
		u.pos = pts[0]


# Orders the units named in sel (indices) to target; returns and stores the read-out.
func order(sel: Array, target: Vector2, walker_speed: float, option: String, climb: bool) -> Dictionary:
	if sel.is_empty():
		return {}
	var pace := pace_of(sel, walker_speed)
	var first: Dictionary = units[sel[0]]
	var start: Vector2 = first.pos
	for k in range(sel.size()):
		_plan(units[sel[k]], target + _offset(k), pace, option, climb)
	var r: Dictionary = first.route
	var other_kind := "flyer" if first.kind == "w" else "walker"
	var o: Dictionary
	for u in units:
		if u.kind == "w":
			start = u.pos
			break
	var o_speed: float
	if first.kind == "w":
		var layer := FLYER_START_LAYER
		for u in units:
			if u.kind == "f":
				layer = u.layer
				break
		o = grid.route_flyer(start, target, layer, climb, FLYER_SPEED)
		o_speed = FLYER_SPEED
	else:
		o = grid.route_walker(start, target, option)
		o_speed = walker_speed
	last = {
		"kind": _kinds(sel), "count": sel.size(), "pace": pace,
		"length": r.length, "seconds": first.secs, "bands": r.bands_crossed, "reached": r.reached,
		"other_kind": other_kind, "other_seconds": o.seconds_at.call(o_speed), "other_reached": o.reached,
		"other_length": o.length,
	}
	return last


func _kinds(sel: Array) -> String:
	var w := false
	var f := false
	for i in sel:
		w = w or units[i].kind == "w"
		f = f or units[i].kind == "f"
	return "walkers and flyers" if (w and f) else ("walkers" if w else "flyers")


func _point_at(u: Dictionary, d: float) -> Vector2:
	var pts: PackedVector2Array = u.route.points
	var cum: Array = u.cum
	for i in range(1, pts.size()):
		if d <= cum[i]:
			var seg: float = cum[i] - cum[i - 1]
			return pts[i - 1] if seg <= 0.0 else pts[i - 1].lerp(pts[i], (d - cum[i - 1]) / seg)
	return pts[pts.size() - 1]


func moving(u: Dictionary) -> bool:
	return not u.route.is_empty() and u.t < u.secs


func arrived(u: Dictionary) -> bool:
	return not u.route.is_empty() and u.t >= u.secs


func step(dt: float) -> void:
	for u in units:
		if not moving(u):
			continue
		u.t = minf(u.t + dt, u.secs)
		var d: float = u.len if u.secs <= 0.0 else u.len * u.t / u.secs
		u.pos = _point_at(u, d)
		if u.kind == "f":
			for tr in u.route.transfers:
				if d >= tr.dist:
					u.layer = tr.to_layer
