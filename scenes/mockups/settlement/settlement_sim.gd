extends RefCounted
# Prototype growth sim for the settlement mockup. Not the game's sim; every constant is a candidate.

const WIN := 121
const HALF := 60
const SPACING_WU := 100.0

# Candidates (printed by the scene, listed in the README).
const THRESHOLDS := [0.10, 0.22, 0.38, 0.58]  # marked ground, scaffold, built, dense
const TICK_S := 3.0
const BASE_DECAY := 0.99
const CLIMB_WU := 900.0
const NONWATER_FAR := 0.99
const WATER_NEAR_CELLS := 3
const WATER_CROSS := 0.85
const EASE := 0.35
const M_START := 0.6
const M_FULL_S := 300.0
const CLIFF_SLOPE := 0.22
const CLIFF_MAX_STAGE := 3
const RISE_S := 0.9
const WAVE_RISE_S := 0.4
const WAVE_LEN := 24
const WAVE_STAGGER_S := 0.04
const PLAYER_HALF := 2
const REFILL_RING := 2
const DAMAGE_R := 6
const REBUILD_DELAY_S := 10.0
const PATH_DILATE := 1
const MAX_WET_PATH := 6
const SHORE_MARGIN := 1
const CONTOUR_SLOPE := 0.06
const JITTER_CELLS := 0.22
const YAW_JITTER := 0.25
const LANE_PERIOD := 4

var fm
var ox := 0
var oy := 0
var elev := PackedFloat32Array()
var slope := PackedFloat32Array()
var water := PackedByteArray()
var wdist := PackedByteArray()
var lane := PackedByteArray()
var path := PackedByteArray()
var P := PackedFloat32Array()
var D := PackedFloat32Array()
var state := PackedByteArray()
var rubble := PackedByteArray()
var player := PackedByteArray()
var ready_at := PackedFloat32Array()
var active: Array = []
var reached: Array = []
var want := {}
var anims := {}
var dirty := {}
var players: Array = []
var path_ends: Array = []
var path_routes: Array = []
var routes_dirty := true
var path_connected := 0
var core := Vector2i.ZERO
var t := 0.0
var tick_acc := 0.0
var rng := RandomNumberGenerator.new()
var tick_ms := 0.0
var path_ms := 0.0
var path_cells_cleared := 0


func setup(p_fm) -> void:
	fm = p_fm
	var c: Vector2 = fm.nodes[0].pos / SPACING_WU
	ox = clampi(int(round(c.x)) - HALF, 0, fm.dim - WIN)
	oy = clampi(int(round(c.y)) - HALF, 0, fm.dim - WIN)
	core = Vector2i(int(round(c.x)) - ox, int(round(c.y)) - oy)
	var n := WIN * WIN
	elev.resize(n)
	slope.resize(n)
	water.resize(n)
	lane.resize(n)
	for gy in WIN:
		for gx in WIN:
			var cell: Dictionary = fm.grid[(oy + gy) * fm.dim + ox + gx]
			var i := gy * WIN + gx
			elev[i] = cell.elevation
			slope[i] = cell.slope
			water[i] = 1 if cell.water > 0.5 else 0
			lane[i] = 1 if (gx % LANE_PERIOD == LANE_PERIOD - 1 or gy % LANE_PERIOD == LANE_PERIOD - 1) else 0
	_build_wdist()
	reset()


func reset() -> void:
	var n := WIN * WIN
	P = PackedFloat32Array()
	P.resize(n)
	D = PackedFloat32Array()
	D.resize(n)
	state = PackedByteArray()
	state.resize(n)
	rubble = PackedByteArray()
	rubble.resize(n)
	player = PackedByteArray()
	player.resize(n)
	ready_at = PackedFloat32Array()
	ready_at.resize(n)
	path = PackedByteArray()
	path.resize(n)
	active = []
	reached = []
	want = {}
	anims = {}
	players = []
	dirty = {}
	for i in n:
		dirty[i] = true
	t = 0.0
	wave_until = -1.0
	tick_acc = 0.0
	rng.seed = 7
	var ci := core.y * WIN + core.x
	P[ci] = 1.0
	active.append(ci)
	reached.append(ci)
	recompute_paths()


func idx(c: Vector2i) -> int:
	return c.y * WIN + c.x


func inside(c: Vector2i) -> bool:
	return c.x >= 0 and c.y >= 0 and c.x < WIN and c.y < WIN


func _hash(i: int) -> float:
	return float(((i * 73856093) ^ (i * 19349663)) & 0xffff) / 65535.0


func _build_wdist() -> void:
	var n := WIN * WIN
	wdist.resize(n)
	var q: Array = []
	for i in n:
		if water[i] == 1:
			wdist[i] = 0
			q.append(i)
		else:
			wdist[i] = 255
	var head := 0
	while head < q.size():
		var i: int = q[head]
		head += 1
		var d: int = wdist[i]
		if d >= 8:
			continue
		var cx := i % WIN
		var cy := i / WIN
		for dy in range(-1, 2):
			for dx in range(-1, 2):
				var nx := cx + dx
				var ny := cy + dy
				if nx < 0 or ny < 0 or nx >= WIN or ny >= WIN:
					continue
				var j := ny * WIN + nx
				if wdist[j] == 255:
					wdist[j] = d + 1
					q.append(j)


func is_cliff(i: int) -> bool:
	return slope[i] > CLIFF_SLOPE


func buildable(i: int) -> bool:
	return water[i] == 0 and wdist[i] > SHORE_MARGIN and lane[i] == 0 and path[i] == 0 and player[i] == 0


func _factor(from_i: int, to_i: int, diag: bool) -> float:
	var f := BASE_DECAY
	if diag:
		f *= 0.99
	if water[to_i] == 1:
		return f * WATER_CROSS
	var de: float = absf(elev[to_i] - elev[from_i])
	f *= 1.0 - clampf(de / CLIMB_WU, 0.0, 0.8) * 0.5
	f *= 1.0 - 0.25 * slope[to_i]
	if wdist[to_i] > WATER_NEAR_CELLS:
		f *= NONWATER_FAR
	return f


func maturity() -> float:
	return M_START + (1.0 - M_START) * minf(1.0, t / M_FULL_S)


func update(dt: float) -> void:
	t += dt
	tick_acc += dt
	while tick_acc >= TICK_S:
		tick_acc -= TICK_S
		var t0 := Time.get_ticks_usec()
		_tick()
		tick_ms = lerpf(tick_ms, (Time.get_ticks_usec() - t0) / 1000.0, 0.2)
	_rise()
	_advance_anims(dt)


func _tick() -> void:
	var next := {}
	for i in active:
		var cx: int = i % WIN
		var cy: int = i / WIN
		for dy in range(-1, 2):
			for dx in range(-1, 2):
				if dx == 0 and dy == 0:
					continue
				var nx := cx + dx
				var ny := cy + dy
				if nx < 0 or ny < 0 or nx >= WIN or ny >= WIN:
					continue
				var j := ny * WIN + nx
				var v: float = P[i] * _factor(i, j, dx != 0 and dy != 0)
				if v > P[j] + 0.0005 and v > 0.02:
					if P[j] == 0.0:
						reached.append(j)
					P[j] = v
					next[j] = true
	active = next.keys()
	var m := maturity()
	for i in reached:
		var tgt: float = minf(1.0, P[i] * m)
		if tgt > D[i]:
			D[i] += (tgt - D[i]) * EASE
		_want_check(i)


func _target(i: int) -> int:
	if not buildable(i):
		return 0
	var k := 0
	for th in THRESHOLDS:
		if D[i] >= th:
			k += 1
	return mini(k, CLIFF_MAX_STAGE) if is_cliff(i) else k


func _want_check(i: int) -> void:
	if state[i] < _target(i) and not anims.has(i):
		want[i] = true


func _rise() -> void:
	var done: Array = []
	for i in want:
		if anims.has(i):
			continue
		if state[i] >= _target(i):
			done.append(i)
			continue
		if t < ready_at[i]:
			continue
		rubble[i] = 0
		_set_state(i, state[i] + 1, RISE_S if t > wave_until else WAVE_RISE_S)
	for i in done:
		want.erase(i)


var wave_until := -1.0


func _set_state(i: int, s: int, dur: float) -> void:
	var from := vis(i)
	state[i] = s
	anims[i] = {"t": 0.0, "dur": dur, "from": from}
	dirty[i] = true


func _advance_anims(dt: float) -> void:
	var ended: Array = []
	for i in anims:
		var a: Dictionary = anims[i]
		a.t += dt
		dirty[i] = true
		if a.t >= a.dur:
			ended.append(i)
	for i in ended:
		anims.erase(i)
		if state[i] < _target(i):
			want[i] = true


func _clear_lot(i: int) -> void:
	state[i] = 0
	rubble[i] = 0
	anims.erase(i)
	want.erase(i)
	dirty[i] = true


# vis: [height (godot units), footprint, color]
func _vis_of(i: int, s: int, rub: bool) -> Array:
	var v := 0.8 + 0.5 * _hash(i + 11)
	if rub:
		return [0.14, 0.7, Color(0.28, 0.2, 0.18)]
	if is_cliff(i):
		match s:
			1: return [0.05, 0.6, Color(0.7, 0.55, 0.8)]
			2: return [0.22, 0.5, Color(0.8, 0.5, 0.2)]
			_: return [0.4 * v, 0.62, Color(0.55, 0.28, 0.62)]
	match s:
		0: return [0.0, 0.0, Color(1, 1, 1)]
		1: return [0.05, 0.8, Color(0.85, 0.78, 0.55)]
		2: return [0.3 * v, 0.7, Color(0.88, 0.5, 0.15)]
		3: return [0.7 * v, 0.72, Color(0.78, 0.74, 0.66)]
		_: return [1.5 * v, 0.8, Color(0.5, 0.55, 0.7)]


func vis(i: int) -> Array:
	var base := _vis_of(i, state[i], rubble[i] == 1)
	if anims.has(i):
		var a: Dictionary = anims[i]
		var e := clampf(a.t / a.dur, 0.0, 1.0)
		var f: Array = a.from
		return [lerpf(f[0], base[0], e), lerpf(f[1], base[1], e), (f[2] as Color).lerp(base[2], e)]
	return base


func counts() -> Dictionary:
	var c := {"stage1": 0, "stage2": 0, "stage3": 0, "stage4": 0, "cliff": 0, "rubble": 0}
	for i in WIN * WIN:
		var s: int = state[i]
		if rubble[i] == 1:
			c.rubble += 1
		elif s > 0:
			if is_cliff(i):
				c.cliff += 1
			else:
				c["stage%d" % s] += 1
	return c


func piece_total() -> int:
	var c := counts()
	return c.stage1 + c.stage2 + c.stage3 + c.stage4 + c.cliff + c.rubble + players.size()


func _street_candidate(horizontal: bool) -> Array:
	var best: Array = []
	var best_score := -1
	for k in 80:
		var line := rng.randi_range(0, WIN / LANE_PERIOD - 1) * LANE_PERIOD + (rng.randi_range(0, 1) * 2)
		var start := rng.randi_range(0, WIN - WAVE_LEN)
		var cells: Array = []
		var score := 0
		for s in WAVE_LEN:
			for off in [0, 1]:
				var c := Vector2i(start + s, line + off) if horizontal else Vector2i(line + off, start + s)
				if not inside(c):
					continue
				var i := idx(c)
				if buildable(i) and P[i] >= THRESHOLDS[0]:
					cells.append([i, s])
					if state[i] < 3:
						score += 1
		if score > best_score:
			best_score = score
			best = cells
	return best


func wave(kind: String) -> Dictionary:
	var streets := 3 if kind == "season" else 1
	var raised := 0
	for n in streets:
		var cells := _street_candidate(rng.randf() < 0.5)
		for e in cells:
			var i: int = e[0]
			D[i] = maxf(D[i], minf(1.0, P[i] + 0.35))
			ready_at[i] = t + float(e[1]) * WAVE_STAGGER_S
			want[i] = true
			raised += 1
		if kind == "expansion" and not cells.is_empty():
			var far: int = cells[cells.size() - 1][0]
			P[far] = maxf(P[far], 0.7)
			active.append(far)
			reached.append(far)
	wave_until = t + 20.0
	return {"kind": kind, "lots": raised}


func place_building(c: Vector2i) -> int:
	c = Vector2i(clampi(c.x, PLAYER_HALF, WIN - 1 - PLAYER_HALF), clampi(c.y, PLAYER_HALF, WIN - 1 - PLAYER_HALF))
	var cleared := 0
	for dy in range(-PLAYER_HALF - REFILL_RING, PLAYER_HALF + REFILL_RING + 1):
		for dx in range(-PLAYER_HALF - REFILL_RING, PLAYER_HALF + REFILL_RING + 1):
			var cc := c + Vector2i(dx, dy)
			if not inside(cc):
				continue
			var i := idx(cc)
			var in_foot: bool = absi(dx) <= PLAYER_HALF and absi(dy) <= PLAYER_HALF
			if state[i] > 0 or rubble[i] == 1:
				cleared += 1
			_clear_lot(i)
			if in_foot:
				player[i] = 1
			else:
				var ring := maxi(absi(dx), absi(dy)) - PLAYER_HALF
				ready_at[i] = t + 1.0 + float(ring) * 1.5 + rng.randf() * 1.5
				want[i] = true
	var ci := idx(c)
	players.append({"cell": c, "elev": elev[ci]})
	P[ci] = maxf(P[ci], 0.85)
	D[ci] = maxf(D[ci], 0.5)
	active.append(ci)
	reached.append(ci)
	recompute_paths()
	return cleared


func damage(c: Vector2i) -> int:
	var hit := 0
	for dy in range(-DAMAGE_R, DAMAGE_R + 1):
		for dx in range(-DAMAGE_R, DAMAGE_R + 1):
			if dx * dx + dy * dy > DAMAGE_R * DAMAGE_R:
				continue
			var cc := c + Vector2i(dx, dy)
			if not inside(cc):
				continue
			var i := idx(cc)
			if rubble[i] == 1 or state[i] == 0:
				continue
			anims.erase(i)
			if state[i] > 1:
				_set_state(i, state[i] - 1, RISE_S)
			else:
				state[i] = 0
				rubble[i] = 1
				anims[i] = {"t": 0.0, "dur": RISE_S, "from": _vis_of(i, 1, false)}
				dirty[i] = true
			ready_at[i] = t + REBUILD_DELAY_S
			want[i] = true
			hit += 1
	return hit


func recompute_paths() -> void:
	var t0 := Time.get_ticks_usec()
	var n := WIN * WIN
	var dist := PackedFloat32Array()
	dist.resize(n)
	dist.fill(1e30)
	var parent := PackedInt32Array()
	parent.resize(n)
	parent.fill(-1)
	var hk: Array = []
	var hv: Array = []
	var ci := idx(core)
	if player[ci] == 1:
		ci = _nearest_open(ci)
	dist[ci] = 0.0
	hk.append(0.0)
	hv.append(ci)
	while not hk.is_empty():
		var k: float = hk[0]
		var i: int = hv[0]
		var lk: float = hk.pop_back()
		var lv: int = hv.pop_back()
		if not hk.is_empty():
			var p := 0
			hk[0] = lk
			hv[0] = lv
			while true:
				var l := p * 2 + 1
				if l >= hk.size():
					break
				var r := l + 1
				var m := r if (r < hk.size() and hk[r] < hk[l]) else l
				if hk[m] >= hk[p]:
					break
				var tk = hk[m]
				var tv = hv[m]
				hk[m] = hk[p]
				hv[m] = hv[p]
				hk[p] = tk
				hv[p] = tv
				p = m
		if k > dist[i]:
			continue
		var cx := i % WIN
		var cy := i / WIN
		for dy in range(-1, 2):
			for dx in range(-1, 2):
				if dx == 0 and dy == 0:
					continue
				var nx := cx + dx
				var ny := cy + dy
				if nx < 0 or ny < 0 or nx >= WIN or ny >= WIN:
					continue
				var j := ny * WIN + nx
				if player[j] == 1:
					continue
				var cost := 1.0 + 6.0 * slope[j] + (25.0 if water[j] == 1 else 0.0)
				if dx != 0 and dy != 0:
					cost *= 1.414
				var nd := k + cost
				if nd < dist[j]:
					dist[j] = nd
					parent[j] = i
					var q := hk.size()
					hk.append(nd)
					hv.append(j)
					while q > 0:
						var pp := (q - 1) / 2
						if hk[pp] <= hk[q]:
							break
						var tk2 = hk[pp]
						var tv2 = hv[pp]
						hk[pp] = hk[q]
						hv[pp] = hv[q]
						hk[q] = tk2
						hv[q] = tv2
						q = pp
	var old := path.duplicate()
	path.fill(0)
	path_ends = []
	path_routes = []
	var best_end := []
	var best_d := []
	for s in 8:
		best_end.append(-1)
		best_d.append(1e30)
	for e in WIN:
		for pos in [Vector2i(e, 0), Vector2i(e, WIN - 1), Vector2i(0, e), Vector2i(WIN - 1, e)]:
			var d: Vector2 = Vector2(pos - core)
			var sec := int(floor((d.angle() + PI) / (TAU / 8.0))) % 8
			var i := idx(pos)
			if dist[i] < best_d[sec]:
				best_d[sec] = dist[i]
				best_end[sec] = i
	for s in 8:
		var cur: int = best_end[s]
		if cur < 0:
			continue
		var wet := 0
		var probe := cur
		while probe != -1:
			wet += water[probe]
			probe = parent[probe]
		if wet > MAX_WET_PATH:
			continue
		path_ends.append(cur)
		var route := PackedInt32Array()
		var walk := cur
		while walk != -1:
			route.append(walk)
			walk = parent[walk]
		path_routes.append(route)
		while cur != -1:
			var cx := cur % WIN
			var cy := cur / WIN
			for dy in range(-PATH_DILATE, PATH_DILATE + 1):
				for dx in range(-PATH_DILATE, PATH_DILATE + 1):
					var nx := cx + dx
					var ny := cy + dy
					if nx >= 0 and ny >= 0 and nx < WIN and ny < WIN:
						var j := ny * WIN + nx
						if player[j] == 0 and path[j] == 0:
							path[j] = 2
			path[cur] = 1 if player[cur] == 0 else 0
			cur = parent[cur]
	path_cells_cleared = 0
	for i in n:
		if path[i] != old[i]:
			dirty[i] = true
		if path[i] != 0 and (state[i] > 0 or rubble[i] == 1):
			_clear_lot(i)
			path_cells_cleared += 1
		elif path[i] == 0 and old[i] != 0:
			want[i] = true
	path_connected = _check_connected()
	routes_dirty = true
	path_ms = (Time.get_ticks_usec() - t0) / 1000.0


func _nearest_open(i: int) -> int:
	var cx := i % WIN
	var cy := i / WIN
	for r in range(1, WIN):
		for dy in range(-r, r + 1):
			for dx in range(-r, r + 1):
				if maxi(absi(dx), absi(dy)) != r:
					continue
				var nx := cx + dx
				var ny := cy + dy
				if nx < 0 or ny < 0 or nx >= WIN or ny >= WIN:
					continue
				var j := ny * WIN + nx
				if player[j] == 0 and water[j] == 0:
					return j
	return i


func _check_connected() -> int:
	var seen := PackedByteArray()
	seen.resize(WIN * WIN)
	var root := idx(core)
	if player[root] == 1:
		root = _nearest_open(root)
	var q: Array = [root]
	seen[root] = 1
	var head := 0
	while head < q.size():
		var i: int = q[head]
		head += 1
		var cx := i % WIN
		var cy := i / WIN
		for dy in range(-1, 2):
			for dx in range(-1, 2):
				var nx := cx + dx
				var ny := cy + dy
				if nx < 0 or ny < 0 or nx >= WIN or ny >= WIN:
					continue
				var j := ny * WIN + nx
				if seen[j] == 0 and path[j] != 0 and player[j] == 0 and state[j] == 0:
					seen[j] = 1
					q.append(j)
	var ok := 0
	for e in path_ends:
		if seen[e] == 1:
			ok += 1
	return ok
