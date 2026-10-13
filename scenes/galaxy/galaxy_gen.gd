extends RefCounted

# Lays out one Vector3 per region id, seeded, following the sim graph (spec
# docs/northstar/plans/2026-10-07-visible-game-spec.md Rev 12d, paragraph VG-B24-layout; Westley 2026-10-12:
# civilizations congregate regionally). C5 rule (docs/architecture.md "C transport v1"): the server never
# transmits positions, so the client owns layout. Same region-id set + same edges + same seed always yields the
# same positions (determinism contract, CLAUDE.md): everything is drawn from a hash of the seed and the region id,
# nothing from an engine RNG, and every loop runs over sorted ids and sorted edge pairs.
#
# Placement: breadth-first from the region of highest degree (ties by lower id), the root at the ball centre; each
# region at the centroid of its already-placed neighbours plus a hashed direction at a hashed distance in
# [EDGE_MIN, EDGE_MAX], re-hashed up to PLACEMENT_ATTEMPTS times when nearer than MIN_SPACING to a placed region or
# outside R_BALL. Then RELAX_PASSES passes of relaxation. The generator reads ids and edges only, never owner, tier
# or capacity.

# B23 (spec rev 12b): the prototype's values as run, origin/push/galaxy-field at 99f35887 (CIV_SCALE 0.5 at galaxy_gen.gd:7).
const CIV_SCALE := 0.5   # prototype galaxy_gen.gd:7
const R_BALL := 50.0   # prototype galaxy_gen.gd:8 BALL_RADIUS 100 x CIV_SCALE
const MIN_SPACING := 11.0   # prototype galaxy_gen.gd:11, 22 x CIV_SCALE, now in 3D

# B24 (spec VG-B24-layout; ledger row DRAFT-b24-relax and the Architect's gap rulings G4, G5, G8, G11 of 2026-10-12).
const PLACEMENT_ATTEMPTS := 16   # spec: "up to 16 tries" per region (was 250; TD-VG-B-16 pins this name)
const EDGE_MIN := 11.0   # spec: distance drawn by hash from [11, 18] wu; G8 null action: world units directly, CIV_SCALE not applied again
const EDGE_MAX := 18.0   # DRAFT-b24-relax: the prototype's longest edge (max 18.0 over 398 edges)
const EDGE_REST := 13.0   # spec: edges spring toward 13 wu (the prototype's median edge 13.07)
const RELAX_PASSES := 20   # spec: 20 relaxation passes
const SPRING_GAIN := 0.25   # G5: each edge moves both ends toward EDGE_REST by a quarter of the error
const REPEL_GAIN := 0.5   # G5: each pair under MIN_SPACING is pushed apart by half the deficit (read as each end, so one pass clears it)
const BALL_MARGIN := 2.0   # G5: positions clamped to R_BALL minus 2
const FREE_CANDIDATES := 32   # G4: a disconnected component compares 32 hashed candidates
# G11 null action: the multiply-xor mix of galaxy_view.gd (_mix, 64-bit wrapping ints), a draw k = mix(mix(seed, id), k),
# the low 24 bits over 2^24. Liberty: HASH_ROUNDS extra mix rounds fold the high half down first. Measured 2026-10-13:
# the bare mix returns the same low 24 bits for every k (xor with a small k, no multiply after it), so the draws of one
# region were identical; 4 rounds give uncorrelated draws (correlation under 0.03) and flat buckets.
const HASH_PRIME := 1099511628211
const HASH_ROUNDS := 4
const FREE_K0 := 100   # draw index where the free-position candidates start (above 3 * PLACEMENT_ATTEMPTS)

var _fallbacks := 0
var _cache_key: Array = []
var _cache_positions := {}


# Count of regions the last layout() placed unchecked after PLACEMENT_ATTEMPTS misses (the best of its candidates).
func last_fallbacks() -> int:
	return _fallbacks


# edges: the snapshot's list of {a, b, t} dictionaries (G1: optional, an empty list lays out a graph with no edges).
# G2: the result is cached by (ids, edge pairs, seed); galaxy_view asks on every snapshot, and only ids, edges and
# seed move the layout.
func layout(region_ids: Array, p_seed: int, edges: Array = []) -> Dictionary:
	var ids: Array = region_ids.duplicate()
	ids.sort()
	var pairs := _edge_pairs(ids, edges)
	var key := [ids, pairs, p_seed]
	if key == _cache_key:
		return _cache_positions.duplicate()
	_fallbacks = 0
	var adj := {}
	for id in ids:
		adj[id] = []
	for pr in pairs:
		adj[pr.x].append(pr.y)
		adj[pr.y].append(pr.x)
	var positions := _place(ids, adj, p_seed)
	_relax(ids, pairs, positions)
	_cache_key = key
	_cache_positions = positions
	return positions.duplicate()


# Sorted, de-duplicated (lo, hi) pairs over ids that exist; self-loops and unknown ids dropped.
func _edge_pairs(ids: Array, edges: Array) -> Array[Vector2i]:
	var members := {}
	for id in ids:
		members[id] = true
	var seen := {}
	var out: Array[Vector2i] = []
	for e in edges:
		var a := int(e.get("a", -1))
		var b := int(e.get("b", -1))
		if a == b or not members.has(a) or not members.has(b):
			continue
		var pr := Vector2i(mini(a, b), maxi(a, b))
		if not seen.has(pr):
			seen[pr] = true
			out.append(pr)
	out.sort_custom(func(p, q): return p.x < q.x or (p.x == q.x and p.y < q.y))
	return out


# Breadth-first order; each component starts at its highest-degree unvisited region (ties by lower id).
func _place(ids: Array, adj: Dictionary, p_seed: int) -> Dictionary:
	var positions := {}
	var placed: Array[Vector3] = []
	var visited := {}
	while visited.size() < ids.size():
		var root: int = -1
		var root_degree := -1
		for id in ids:
			if not visited.has(id) and adj[id].size() > root_degree:
				root = id
				root_degree = adj[id].size()
		visited[root] = true
		var pos := Vector3.ZERO if placed.is_empty() else _free_position(p_seed, root, placed)   # G4: the root sits at the ball centre
		positions[root] = pos
		placed.append(pos)
		var queue: Array = [root]
		var head := 0
		while head < queue.size():
			var cur: int = queue[head]
			head += 1
			for nb in adj[cur]:
				if visited.has(nb):
					continue
				visited[nb] = true
				var np := _near_neighbours(p_seed, nb, adj[nb], positions, placed)
				positions[nb] = np
				placed.append(np)
				queue.append(nb)
	return positions


func _near_neighbours(p_seed: int, id: int, neighbours: Array, positions: Dictionary, placed: Array[Vector3]) -> Vector3:
	var sum := Vector3.ZERO
	var count := 0
	for nb in neighbours:
		if positions.has(nb):
			sum += positions[nb]
			count += 1
	var centroid := sum / float(count)   # the BFS parent is always placed, so count >= 1
	var best := centroid
	var best_gap := -1.0
	for t in range(PLACEMENT_ATTEMPTS):
		var dist := EDGE_MIN + (EDGE_MAX - EDGE_MIN) * _unit(p_seed, id, 3 * t + 2)
		var cand := centroid + _direction(p_seed, id, 3 * t) * dist
		var gap := _nearest_gap(cand, placed)
		if gap >= MIN_SPACING and cand.length() <= R_BALL:
			return cand
		if gap > best_gap:
			best_gap = gap
			best = cand
	# G4: after PLACEMENT_ATTEMPTS misses the region takes the best candidate by distance to its nearest placed
	# region (still seeded and deterministic); counted, and qa_state reports it as layout_fallbacks.
	_fallbacks += 1
	return best


# G4: a disconnected component starts at the farthest (from its nearest placed region) of FREE_CANDIDATES hashed
# positions in the ball. Liberty (G4 gives no radius): the ball of radius R_BALL minus BALL_MARGIN, the radius the
# relaxation clamps to, so the clamp never squeezes the first region of a component against its neighbours.
func _free_position(p_seed: int, id: int, placed: Array[Vector3]) -> Vector3:
	var best := Vector3.ZERO
	var best_gap := -1.0
	for j in range(FREE_CANDIDATES):
		var k := FREE_K0 + 3 * j
		var cand := _direction(p_seed, id, k + 1) * ((R_BALL - BALL_MARGIN) * pow(_unit(p_seed, id, k), 1.0 / 3.0))   # uniform in the ball
		var gap := _nearest_gap(cand, placed)
		if gap > best_gap:
			best_gap = gap
			best = cand
	return best


func _nearest_gap(p: Vector3, placed: Array[Vector3]) -> float:
	var m := INF
	for q in placed:
		m = minf(m, q.distance_to(p))
	return m


# G5: per pass, edges (ascending pair order) move both ends toward EDGE_REST, then pairs under MIN_SPACING (ascending
# id order) are pushed apart, then every position is clamped to R_BALL minus BALL_MARGIN; so pass 20 ends repel then clamp.
func _relax(ids: Array, pairs: Array[Vector2i], positions: Dictionary) -> void:
	var index := {}
	var pos: Array[Vector3] = []
	for i in ids.size():
		index[ids[i]] = i
		pos.append(positions[ids[i]])
	var limit := R_BALL - BALL_MARGIN
	for _pass in range(RELAX_PASSES):
		for pr in pairs:
			var i: int = index[pr.x]
			var j: int = index[pr.y]
			var d := pos[i].distance_to(pos[j])
			if d < 1.0e-9:
				continue
			var shift := (pos[j] - pos[i]) / d * ((d - EDGE_REST) * SPRING_GAIN)
			pos[i] += shift
			pos[j] -= shift
		for i in range(pos.size()):
			for j in range(i + 1, pos.size()):
				var d := pos[i].distance_to(pos[j])
				if d >= MIN_SPACING:
					continue
				var axis := Vector3.RIGHT if d < 1.0e-9 else (pos[j] - pos[i]) / d
				var shift := axis * ((MIN_SPACING - d) * REPEL_GAIN)
				pos[i] -= shift
				pos[j] += shift
		for i in range(pos.size()):
			if pos[i].length() > limit:
				pos[i] = pos[i].normalized() * limit
	for i in ids.size():
		positions[ids[i]] = pos[i]


func _mix(h: int, v: int) -> int:
	return (h * HASH_PRIME) ^ v


# A float in [0, 1) for draw k of region id.
func _unit(p_seed: int, id: int, k: int) -> float:
	var h := _mix(_mix(p_seed, id), k)
	for _round in range(HASH_ROUNDS):
		h = _mix(h, (h >> 32) & 0xFFFFFFFF)
	return float(h & 0xFFFFFF) / 16777216.0


# Uniform direction on the sphere from draws k and k + 1 (the formula the random ball used: cos_phi in [-1, 1], theta in [0, TAU)).
func _direction(p_seed: int, id: int, k: int) -> Vector3:
	var cos_phi := 2.0 * _unit(p_seed, id, k) - 1.0
	var sin_phi := sqrt(1.0 - cos_phi * cos_phi)
	var theta := _unit(p_seed, id, k + 1) * TAU
	return Vector3(cos(theta) * sin_phi, cos_phi, sin(theta) * sin_phi)
