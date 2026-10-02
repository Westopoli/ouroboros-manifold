extends RefCounted
# Test-side galaxy builder for sizes the shipped generator does not produce
# (400 systems / 15 factions, or a chosen faction count), so the product code
# carries no test hook. Same recipe as galaxy_gen.gd: random points in the
# ball with a minimum spacing, nearest-neighbour links, capitals by
# farthest-point, ownership grown breadth-first over the links, 85% owned.
# Reuses GalaxyGen's own link/significance/edge-kind helpers.


static func make(p_seed: int, system_count: int, faction_count: int, min_spacing: float) -> Galaxy:
	var gen := GalaxyGen.new()
	var rng := RandomNumberGenerator.new()
	rng.seed = p_seed
	var g := Galaxy.new()
	g.seed_used = p_seed
	var placed: Array = []
	var attempts := 0
	while placed.size() < system_count and attempts < system_count * 400:
		attempts += 1
		var r := GalaxyGen.BALL_RADIUS * pow(rng.randf(), 1.0 / 3.0)
		var cos_phi := rng.randf_range(-1.0, 1.0)
		var sin_phi := sqrt(1.0 - cos_phi * cos_phi)
		var theta := rng.randf() * TAU
		var candidate := Vector3(cos(theta) * sin_phi, cos_phi, sin(theta) * sin_phi) * r
		var ok := true
		for p in placed:
			if p.distance_to(candidate) < min_spacing:
				ok = false
				break
		if ok:
			placed.append(candidate)
	for i in placed.size():
		g.systems.append({"id": i, "pos": placed[i], "significance": 0.5, "owner": -1, "name": "S%d" % i})
	gen._link_systems(g)
	_assign_factions(gen, g, rng, faction_count)
	gen._assign_significance(g, rng)
	gen._classify_edges(g)
	return g


static func _assign_factions(gen: GalaxyGen, g: Galaxy, rng: RandomNumberGenerator, faction_count: int) -> void:
	var n := g.systems.size()
	var capitals: Array = [rng.randi_range(0, n - 1)]
	while capitals.size() < faction_count:
		var best_i := -1
		var best_d := -1.0
		for i in n:
			if capitals.has(i):
				continue
			var min_d := INF
			for c in capitals:
				min_d = minf(min_d, g.systems[i].pos.distance_to(g.systems[c].pos))
			if min_d > best_d:
				best_d = min_d
				best_i = i
		capitals.append(best_i)
	for i in faction_count:
		g.factions.append({"id": i, "name": "Faction %d" % i, "capital": capitals[i], "hue": gen._hue_for(i)})
		g.systems[capitals[i]].owner = i
	var adjacency := gen._adjacency_map(g)
	var target_owned := int(floor(n * GalaxyGen.OWN_FRACTION))
	var owned := faction_count
	var queues: Array = []
	for i in faction_count:
		queues.append([capitals[i]])
	while owned < target_owned:
		var progress := false
		for f in gen._seeded_shuffle_range(faction_count, rng):
			if owned >= target_owned:
				break
			var q: Array = queues[f]
			while q.size() > 0:
				var cur: int = q.pop_front()
				var claimed := -1
				for nb in adjacency.get(cur, []):
					if g.systems[nb].owner == -1:
						claimed = nb
						break
				if claimed != -1:
					g.systems[claimed].owner = f
					q.append(cur)
					q.append(claimed)
					owned += 1
					progress = true
					break
		if not progress:
			break
