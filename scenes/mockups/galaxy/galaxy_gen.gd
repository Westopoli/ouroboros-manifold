class_name GalaxyGen
extends RefCounted

const DISC_RADIUS := 100.0
const Y_JITTER := 8.0
const MIN_SPACING := 6.0
const LINK_RADIUS := 30.0
const LINK_NEAREST := 3
const CAPITAL_SIG := 0.85
const PLAYER_CAPITAL_SIG := 1.0
const OWN_FRACTION := 0.85
const SYSTEM_COUNT_MIN := 40
const SYSTEM_COUNT_MAX := 80
const FACTION_COUNT_MIN := 4
const FACTION_COUNT_MAX := 8

const SYLLABLES_A := ["Ka", "Vel", "Nor", "Tha", "Ori", "Zan", "Bre", "Sol", "Quin", "Aer", "Dro", "Myl", "Esk", "Pyr", "Ust"]
const SYLLABLES_B := ["dor", "ris", "nak", "vess", "tum", "lyn", "gar", "phos", "reth", "vane", "kor", "sil", "mund", "thys", "vor"]


func generate(p_seed: int) -> Galaxy:
	var rng := RandomNumberGenerator.new()
	rng.seed = p_seed
	var galaxy := Galaxy.new()
	galaxy.seed_used = p_seed
	_place_systems(galaxy, rng)
	_link_systems(galaxy)
	_assign_factions(galaxy, rng)
	_assign_significance(galaxy, rng)
	_classify_edges(galaxy)
	return galaxy


func _place_systems(galaxy: Galaxy, rng: RandomNumberGenerator) -> void:
	var count := rng.randi_range(SYSTEM_COUNT_MIN, SYSTEM_COUNT_MAX)
	var placed: Array = []
	var attempts := 0
	while placed.size() < count and attempts < count * 250:
		attempts += 1
		var r := DISC_RADIUS * pow(rng.randf(), 1.6)
		var theta := rng.randf() * TAU
		var x := cos(theta) * r
		var z := sin(theta) * r
		var ok := true
		for p in placed:
			if Vector2(p.x, p.z).distance_to(Vector2(x, z)) < MIN_SPACING:
				ok = false
				break
		if ok:
			var y := rng.randf_range(-Y_JITTER, Y_JITTER)
			placed.append(Vector3(x, y, z))
	for i in range(placed.size()):
		galaxy.systems.append({
			"id": i,
			"pos": placed[i],
			"significance": 0.5,
			"owner": -1,
			"name": _make_name(rng),
		})


func _make_name(rng: RandomNumberGenerator) -> String:
	var a: String = SYLLABLES_A[rng.randi_range(0, SYLLABLES_A.size() - 1)]
	var b: String = SYLLABLES_B[rng.randi_range(0, SYLLABLES_B.size() - 1)]
	return a + b


func _link_systems(galaxy: Galaxy) -> void:
	var n := galaxy.systems.size()
	var linked: Array = []
	for i in range(n):
		linked.append({})
	for i in range(n):
		var dists: Array = []
		for j in range(n):
			if j == i:
				continue
			var d: float = galaxy.systems[i].pos.distance_to(galaxy.systems[j].pos)
			dists.append([d, j])
		dists.sort_custom(func(a, b): return a[0] < b[0])
		var claimed := 0
		for pair in dists:
			if claimed >= LINK_NEAREST:
				break
			if pair[0] <= LINK_RADIUS:
				linked[i][pair[1]] = true
				linked[pair[1]][i] = true
				claimed += 1
	for i in range(n):
		if linked[i].is_empty():
			var best_j := -1
			var best_d := INF
			for j in range(n):
				if j == i:
					continue
				var d: float = galaxy.systems[i].pos.distance_to(galaxy.systems[j].pos)
				if d < best_d:
					best_d = d
					best_j = j
			if best_j != -1:
				linked[i][best_j] = true
				linked[best_j][i] = true
	for i in range(n):
		for j in linked[i]:
			if j > i:
				galaxy.edges.append({"a": i, "b": j, "kind": "trade"})


func _adjacency_map(galaxy: Galaxy) -> Dictionary:
	var m := {}
	for i in range(galaxy.systems.size()):
		m[i] = []
	for e in galaxy.edges:
		m[e.a].append(e.b)
		m[e.b].append(e.a)
	return m


func _seeded_shuffle_range(n: int, rng: RandomNumberGenerator) -> Array:
	var arr: Array = range(n)
	for i in range(arr.size() - 1, 0, -1):
		var j := rng.randi_range(0, i)
		var tmp = arr[i]
		arr[i] = arr[j]
		arr[j] = tmp
	return arr


func _assign_factions(galaxy: Galaxy, rng: RandomNumberGenerator) -> void:
	var n := galaxy.systems.size()
	var faction_count: int = clampi(rng.randi_range(FACTION_COUNT_MIN, FACTION_COUNT_MAX), 1, max(n, 1))
	var capitals: Array = []
	capitals.append(rng.randi_range(0, n - 1))
	while capitals.size() < faction_count:
		var best_i := -1
		var best_d := -1.0
		for i in range(n):
			if capitals.has(i):
				continue
			var min_d := INF
			for c in capitals:
				var d: float = galaxy.systems[i].pos.distance_to(galaxy.systems[c].pos)
				min_d = min(min_d, d)
			if min_d > best_d:
				best_d = min_d
				best_i = i
		if best_i == -1:
			break
		capitals.append(best_i)
	faction_count = capitals.size()

	for i in range(faction_count):
		galaxy.factions.append({
			"id": i,
			"name": "Faction %d" % i,
			"capital": capitals[i],
			"hue": _hue_for(i),
		})
		galaxy.systems[capitals[i]].owner = i

	var adjacency := _adjacency_map(galaxy)
	var target_owned := int(floor(n * OWN_FRACTION))
	var owned_count := faction_count
	var queues: Array = []
	for i in range(faction_count):
		queues.append([capitals[i]])

	while owned_count < target_owned:
		var any_progress := false
		var order := _seeded_shuffle_range(faction_count, rng)
		for f in order:
			if owned_count >= target_owned:
				break
			var q: Array = queues[f]
			while q.size() > 0:
				var cur: int = q.pop_front()
				var claimed := -1
				for nb in adjacency.get(cur, []):
					if galaxy.systems[nb].owner == -1:
						claimed = nb
						break
				if claimed != -1:
					galaxy.systems[claimed].owner = f
					q.append(cur)
					q.append(claimed)
					owned_count += 1
					any_progress = true
					break
		if not any_progress:
			break


const GOLDEN_ANGLE := 0.6180339887498949

# faction_palette.gd:38 hashes a string faction id ("f_dominion", ...), whose
# hash output spreads well across hue space. Ids here are small sequential
# ints (0..7); str(id).hash() % 360 puts them all within a few degrees of
# each other (measured: ids 0-7 all landed in hue 0.39-0.41, all the same
# green) since a 1-character string differing by one byte barely moves the
# hash. Golden-angle stepping is the standard fix for maximally distinct
# hues over a small sequential id space.
func _hue_for(id: int) -> float:
	return fmod(float(id) * GOLDEN_ANGLE, 1.0)


func _assign_significance(galaxy: Galaxy, rng: RandomNumberGenerator) -> void:
	var player_capital: int = galaxy.factions[0].capital if galaxy.factions.size() > 0 else -1
	var capitals := {}
	for f in galaxy.factions:
		capitals[f.capital] = true
	for sys in galaxy.systems:
		if sys.id == player_capital:
			sys.significance = PLAYER_CAPITAL_SIG
		elif capitals.has(sys.id):
			sys.significance = CAPITAL_SIG
		else:
			sys.significance = rng.randf_range(0.3, 0.8)


func _classify_edges(galaxy: Galaxy) -> void:
	for e in galaxy.edges:
		var oa: int = galaxy.systems[e.a].owner
		var ob: int = galaxy.systems[e.b].owner
		e.kind = "border" if (oa == ob and oa != -1) else "trade"
