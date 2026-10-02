extends RefCounted
# Exact reference for the territory field: the formulas of the legacy shell
# (shaders/shell_metaball.gdshader + legacy_shell_renderer.gd), evaluated
# directly at a point with no grid. Lives with the tests, not in the product.
#
# Per evaluating faction f (the old code built one shell per faction):
#   M_f   = max significance among f's systems (floored at 0.01)
#   sig_i = clamp(significance_i / M_f, 0, 1)   <- for f's own systems AND for
#           rival systems: the old code normalised rivals by the EVALUATING
#           faction's max, not their own (the "quirk" the spec keeps).
#   r_i   = R * (0.6 + 0.4 * sig_i);  k_i = (1 - d^2/r^2)^3 inside r, else 0
#   own_f = sum of k_i over f's systems
#   rival_f = max of k_i over every other owned system (single kernel, not a sum)
#   net_f = own_f * (1 - GAP * smoothstep(0.3, 1.0, rival_f / max(own_f, 0.001)))
# The cell value is the highest net over factions: (net, rival of that faction,
# that faction's id). Ties go to the lowest faction id. A point with no field
# reads (0, 0, 0).
#
# Input: an Array of Dictionaries with pos (Vector3), significance (float) and
# owner (int, -1 = unowned, ignored) - exactly Galaxy.systems entries.

const R := GalaxyGen.INFLUENCE_RADIUS
const ISO := 0.6
const GAP := 0.5
const BIG := 1.0e30

var _pos := PackedVector3Array()
var _sig := PackedFloat32Array()
var _own := PackedInt32Array()
var _max_sig := {}
var _cells := {}
var _radius_scale := 1.0


static func from_systems(systems: Array, radius_scale := 1.0) -> RefCounted:
	var ref: RefCounted = load("res://scenes/mockups/galaxy/tests/field_reference.gd").new()
	ref._radius_scale = radius_scale
	for s in systems:
		if int(s.owner) < 0:
			continue
		var i: int = ref._pos.size()
		ref._pos.append(s.pos)
		ref._sig.append(float(s.significance))
		ref._own.append(int(s.owner))
		ref._max_sig[int(s.owner)] = maxf(ref._max_sig.get(int(s.owner), 0.0), float(s.significance))
		var key: Vector3i = ref._key(s.pos)
		if not ref._cells.has(key):
			ref._cells[key] = PackedInt32Array()
		ref._cells[key].append(i)
	return ref


func _key(p: Vector3) -> Vector3i:
	return Vector3i(floori(p.x / R), floori(p.y / R), floori(p.z / R))


func _near(p: Vector3) -> PackedInt32Array:
	var out := PackedInt32Array()
	var k: Vector3i = _key(p)
	for dx in range(-1, 2):
		for dy in range(-1, 2):
			for dz in range(-1, 2):
				var c = _cells.get(Vector3i(k.x + dx, k.y + dy, k.z + dz))
				if c != null:
					out.append_array(c)
	return out


# Per-faction nets at p: {faction_id: [net, rival]} for every faction that has
# own field at p.
func nets(p: Vector3) -> Dictionary:
	var near := _near(p)
	var factions := {}
	for i in near:
		factions[_own[i]] = true
	var out := {}
	var rr := R * _radius_scale
	for f in factions:
		var m := maxf(_max_sig[f], 0.01)
		var own := 0.0
		var rival := 0.0
		for i in near:
			var s := clampf(_sig[i] / m, 0.0, 1.0)
			var r := rr * (0.6 + 0.4 * s)
			var d2 := p.distance_squared_to(_pos[i])
			if d2 >= r * r:
				continue
			var k := 1.0 - d2 / (r * r)
			k = k * k * k
			if _own[i] == f:
				own += k
			else:
				rival = maxf(rival, k)
		if own <= 0.0:
			continue
		var ratio := rival / maxf(own, 0.001)
		out[f] = [own * (1.0 - GAP * smoothstep(0.3, 1.0, ratio)), rival]
	return out


# Cell value at p: [net, rival, id].
func eval(p: Vector3) -> Array:
	var n := nets(p)
	var ids: Array = n.keys()
	ids.sort()
	var best := 0.0
	var best_rival := 0.0
	var best_id := 0
	for f in ids:
		if n[f][0] > best:
			best = n[f][0]
			best_rival = n[f][1]
			best_id = f
	return [best, best_rival, best_id]


func net(p: Vector3) -> float:
	return eval(p)[0]


# The OLD behaviour, for the FIELD-ORDER positive control: one shell per
# faction, each shell's rival list snapshotted when that faction's LAST system
# was added (legacy_shell_renderer.gd rebuilt only the changed faction's shell,
# so factions added later were missing from earlier factions' rival lists).
# `systems` is in insertion order. Returns a Callable p -> net.
static func old_order_dependent(systems: Array) -> Callable:
	var shells := {}      # faction -> {own: Array, rival: Array, max: float}
	var added: Array = []
	for s in systems:
		if int(s.owner) < 0:
			continue
		added.append(s)
		var f := int(s.owner)
		var own: Array = []
		var rival: Array = []
		var m := 0.0
		for t in added:
			if int(t.owner) == f:
				own.append(t)
				m = maxf(m, float(t.significance))
			else:
				rival.append(t)
		shells[f] = {"own": own, "rival": rival, "max": maxf(m, 0.01)}
	return func(p: Vector3) -> float:
		var best := 0.0
		for f in shells:
			var sh: Dictionary = shells[f]
			var own := 0.0
			var rival := 0.0
			for t in sh.own:
				own += _kernel(p, t, sh.max)
			for t in sh.rival:
				rival = maxf(rival, _kernel(p, t, sh.max))
			var net := own * (1.0 - GAP * smoothstep(0.3, 1.0, rival / maxf(own, 0.001)))
			best = maxf(best, net)
		return best


static func _kernel(p: Vector3, s: Dictionary, norm_max: float) -> float:
	var r := R * (0.6 + 0.4 * clampf(float(s.significance) / norm_max, 0.0, 1.0))
	var d2: float = p.distance_squared_to(s.pos)
	if d2 >= r * r:
		return 0.0
	var k := 1.0 - d2 / (r * r)
	return k * k * k
