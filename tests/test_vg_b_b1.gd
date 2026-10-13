extends SceneTree
# test-timeout: 20000

# Lane B piece B1 (docs/northstar/plans/2026-10-07-visible-game-spec.md rev 4, lane B;
# preflight_2026-10-07/3-galaxy-field.md; bible E-16 S-106 R-106-02/03, S-107, S-108):
# the territory field grid and its GPU bake, ported from the mockup branch
# origin/push/galaxy-field (scenes/mockups/galaxy/territory_field.gd,
# shaders/field_bake.gdshader) into the game's galaxy scene, with the game's
# layout constants (galaxy_gen.gd: ball radius R_BALL 50, spacing 11; TD-VG-B-14, were 71 and 22), and fed by the
# galaxy adapter's territory signals (GalaxyAdapter -> world_view_data.set_territory /
# remove_territory -> territory_set / territory_updated / territory_removed).
# Checks: FIELD-GRID, FIELD-VALUES, FIELD-ORDER, FIELD-CONQUEST, FIELD-MEM on an
# 80-region fixture laid out by scenes/galaxy/galaxy_gen.gd. FIELD-EQ (Westley's 2%)
# lives in tests/test_vg_b_b1_park_field_eq.gd, which preloads the helpers below.
#
# Needs a real renderer (the grid is filled by the graphics card):
#   xvfb-run -a ~/.local/bin/godot.real --path . -s tests/test_vg_b_b1.gd
# Under the headless/dummy renderer DEVICE fails on purpose (as in the mockup's test_field.gd).
#
# Contract fixed here (the spec leaves signatures to the tests), res://scenes/galaxy/territory_field.gd,
# extends Node:
#   const GRID_CELLS := 96; const GRID_SIZE := 128.0; const GRID_MIN := Vector3(-64,-64,-64)   (TD-VG-B-14, were 198.0 and -99)
#   const INFLUENCE_RADIUS: float     14, the prototype's (ball R_BALL 50 + R must fit the cube: R <= 14; was 28 with R_BALL 71)
#   func bind_world_view(wv: Node)    reads wv.territories now and follows its territory_set /
#       territory_updated / territory_removed signals; a territory is {center, radius=significance, color};
#       faction identity is the colour (distinct colours -> distinct ids, first seen first; same colour -> same id)
#   func faction_id_of(region_id: String) -> int     -1 when the region has no territory
#   var palette: PackedVector3Array   palette[id] = the faction colour's rgb
#   func is_dirty() -> bool; func refill() -> void (synchronous, clears dirty, fill_count += 1);
#   _process refills when dirty, so at most once per frame
#   var fill_count: int; var field_texture: Texture3D (FORMAT_RGH, R net, G rival/seam); var id_texture: Texture3D (R8)
#   res://scenes/galaxy/shaders/field_bake.gdshader: the GPU bake (a Shader)
# Cell values follow Ref below (the legacy shell formulas, exact, no grid).

const FIELD_PATH := "res://scenes/galaxy/territory_field.gd"
const BAKE_SHADER_PATH := "res://scenes/galaxy/shaders/field_bake.gdshader"
const WV_PATH := "res://scenes/mockups/galaxy/legacy_world_view_data.gd"
const GEN_PATH := "res://scenes/galaxy/galaxy_gen.gd"

const REGIONS := 80
const FACTIONS := 6
const ISO := 0.6
const GAP := 0.5
const VALUE_TOL := 0.002          # two half-float steps, from the mockup's compare()
const MEM_MAX_BYTES := 5 * 1024 * 1024

var _failures := 0
var _field_script: GDScript


func _initialize() -> void:
	await _run()
	if _failures > 0:
		print("VG-B1 TESTS FAILED: %d" % _failures)
		quit(1)
	else:
		print("VG-B1 TESTS OK")
		quit(0)


func _check(id: String, ok: bool, detail: String) -> void:
	if not ok:
		_failures += 1
	print("CHECK %s %s %s" % [id, "PASS" if ok else "FAIL", detail])


func _run() -> void:
	var headless := DisplayServer.get_name() == "headless"
	_check("DEVICE", not headless, "renderer %s on %s (the grid needs a real renderer; run under xvfb-run, see the header)" % [RenderingServer.get_video_adapter_name(), DisplayServer.get_name()])
	# Detector controls need only the CPU reference, so they run before the product exists.
	_control_order()
	_control_conquest()
	var exists := ResourceLoader.exists(FIELD_PATH)
	_check("FIELD-EXISTS", exists, "%s %s (missing feature: the game has no territory field yet)" % [FIELD_PATH, "exists" if exists else "does not exist"])
	var bake_ok := ResourceLoader.exists(BAKE_SHADER_PATH) and load(BAKE_SHADER_PATH) is Shader
	_check("FIELD-BAKE-SHADER", bake_ok, "%s is a loadable Shader: %s" % [BAKE_SHADER_PATH, bake_ok])
	if not exists:
		for id in ["FIELD-GRID", "FIELD-VALUES", "FIELD-ORDER", "FIELD-CONQUEST", "FIELD-MEM"]:
			_check(id, false, "%s does not exist" % FIELD_PATH)
		return
	_field_script = load(FIELD_PATH)
	_check_grid_constants()
	if headless:
		return
	await _check_values()
	await _check_signals()
	await _check_order()
	await _check_conquest()
	await _check_mem()


# ---- fixture and helpers (static: the park file preloads this script) ----------

# 80 regions laid out by the game's own galaxy_gen.gd (ball radius R_BALL 50, spacing 11; TD-VG-B-14, were 71 and 22); each
# region belongs to the nearest of FACTIONS capitals (ids 0, 13, 26, ...), every 7th
# region is unowned; significance cycles 0.3 / 0.6 / 1.0 (the tier map).
static func fixture(p_seed: int) -> Array:
	var ids: Array = []
	for i in REGIONS:
		ids.append(i)
	var pos: Dictionary = load(GEN_PATH).new().layout(ids, p_seed)
	var caps: Array = []
	for f in FACTIONS:
		caps.append(pos[(f * REGIONS) / FACTIONS])
	var out: Array = []
	for i in REGIONS:
		var best := 0
		for f in FACTIONS:
			if pos[i].distance_to(caps[f]) < pos[i].distance_to(caps[best]):
				best = f
		var fac := -1 if (i % 7 == 6) else best
		out.append({"id": str(i), "pos": pos[i], "sig": [0.3, 0.6, 1.0][i % 3], "fac": fac,
			"color": Color.from_hsv(float(maxi(fac, 0)) / FACTIONS, 0.7, 0.9)})
	return out


# Feed a world_view_data node the way the galaxy adapter does (set_territory per owned system).
static func feed(wv: Node, fx: Array) -> void:
	for s in fx:
		if s.fac >= 0:
			wv.set_territory(s.id, s.pos, s.sig, s.color)


static func new_wv() -> Node:
	return load(WV_PATH).new()


# Systems array for the reference, with the owner the field itself assigned.
static func ref_systems(field: Node, fx: Array) -> Array:
	var out: Array = []
	for s in fx:
		if s.fac >= 0:
			out.append({"pos": s.pos, "significance": s.sig, "owner": field.faction_id_of(s.id)})
	return out


# A field node lives in the tree two frames before its first fill, as the shell renderer's does.
static func make_field(tree: SceneTree, script: GDScript, wv: Node) -> Node:
	var f: Node = script.new()
	tree.root.add_child(f)
	await tree.process_frame
	await tree.process_frame
	f.bind_world_view(wv)
	f.refill()
	return f


static func rays(rng: RandomNumberGenerator, count: int) -> Array:
	var out: Array = []
	while out.size() < count:
		var start := unit(rng) * 95.0
		var target := unit(rng) * (45.0 * pow(rng.randf(), 1.0 / 3.0))
		var d := (target - start).normalized()
		var b := start.dot(d)
		var disc := b * b - (start.length_squared() - 66.0 * 66.0)
		if disc <= 0.0:
			continue
		var s := sqrt(disc)
		out.append([start, d, maxf(-b - s, 0.0), -b + s])
	return out


static func unit(rng: RandomNumberGenerator) -> Vector3:
	var cz := rng.randf_range(-1.0, 1.0)
	var sz := sqrt(1.0 - cz * cz)
	var th := rng.randf() * TAU
	return Vector3(cos(th) * sz, sin(th) * sz, cz)


# First point along o + d*t where `sampler` (p -> float) reaches ISO from below; -1.0 when none.
static func first_surface(sampler: Callable, o: Vector3, d: Vector3, t0: float, t1: float, step: float) -> float:
	var t := t0
	if float(sampler.call(o + d * t)) >= ISO:
		return t0
	while t < t1:
		var tn := minf(t + step, t1)
		if float(sampler.call(o + d * tn)) >= ISO:
			var lo := t
			var hi := tn
			for _i in 22:
				var mid := 0.5 * (lo + hi)
				if float(sampler.call(o + d * mid)) >= ISO:
					hi = mid
				else:
					lo = mid
			return 0.5 * (lo + hi)
		t = tn
	return -1.0


static func shuffled(a: Array, seed_: int) -> Array:
	var out := a.duplicate(true)
	var rng := RandomNumberGenerator.new()
	rng.seed = seed_
	for i in range(out.size() - 1, 0, -1):
		var j := rng.randi_range(0, i)
		var t = out[i]
		out[i] = out[j]
		out[j] = t
	return out


# The exact field (legacy shell formulas) at a point, no grid. Per evaluating faction f:
# M_f = max significance of f's systems (floor 0.01); sig_i = clamp(significance_i / M_f, 0, 1)
# for f's own systems AND for rivals (rivals are normalised by the EVALUATING faction's max);
# r_i = R * (0.6 + 0.4 * sig_i); k_i = (1 - d^2/r^2)^3 inside r; own_f = sum k over f's systems;
# rival_f = max k over every other owned system; net_f = own_f * (1 - GAP * smoothstep(0.3, 1.0,
# rival_f / max(own_f, 0.001))). The cell is the highest net: (net, rival, id), ties to the lowest id.
class Ref extends RefCounted:
	var r := 14.0
	var radius_scale := 1.0
	var pos := PackedVector3Array()
	var sig := PackedFloat32Array()
	var own := PackedInt32Array()
	var max_sig := {}

	static func from_systems(systems: Array, p_r: float, p_radius_scale := 1.0) -> Ref:
		var ref := Ref.new()
		ref.r = p_r
		ref.radius_scale = p_radius_scale
		for s in systems:
			if int(s.owner) < 0:
				continue
			ref.pos.append(s.pos)
			ref.sig.append(float(s.significance))
			ref.own.append(int(s.owner))
			ref.max_sig[int(s.owner)] = maxf(ref.max_sig.get(int(s.owner), 0.0), float(s.significance))
		return ref

	func nets(p: Vector3) -> Dictionary:
		var out := {}
		var rr := r * radius_scale
		for f in max_sig:
			var m := maxf(max_sig[f], 0.01)
			var o := 0.0
			var rival := 0.0
			for i in pos.size():
				var s := clampf(sig[i] / m, 0.0, 1.0)
				var ri := rr * (0.6 + 0.4 * s)
				var d2 := p.distance_squared_to(pos[i])
				if d2 >= ri * ri:
					continue
				var k := 1.0 - d2 / (ri * ri)
				k = k * k * k
				if own[i] == f:
					o += k
				else:
					rival = maxf(rival, k)
			if o <= 0.0:
				continue
			out[f] = [o * (1.0 - GAP * smoothstep(0.3, 1.0, rival / maxf(o, 0.001))), rival]
		return out

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


# CPU reader for the field grid. Field slice z is RGH (R net, G rival, half floats), id slice R8.
# Cell (x,y,z) is centred at gmin + (x+0.5, ...) * cell; net() is trilinear, texel-centre, edge clamp.
class Grid extends RefCounted:
	var n := 0
	var gmin := Vector3.ZERO
	var size := 0.0
	var cell := 0.0
	var colors := PackedVector3Array()    # palette: id -> rgb
	var _f: Array = []
	var _id: Array = []

	static func from_field(field: Node) -> Grid:
		var g := Grid.new()
		g.n = int(field.GRID_CELLS)
		g.gmin = field.GRID_MIN
		g.size = float(field.GRID_SIZE)
		g.cell = g.size / float(g.n)
		g.colors = field.palette.duplicate()
		for img in field.field_texture.get_data():
			g._f.append(img.get_data())
		for img in field.id_texture.get_data():
			g._id.append(img.get_data())
		return g

	static func bake_cpu(p_n: int, p_gmin: Vector3, p_size: float, eval: Callable) -> Grid:
		var g := Grid.new()
		g.n = p_n
		g.gmin = p_gmin
		g.size = p_size
		g.cell = p_size / float(p_n)
		for z in p_n:
			var f := PackedByteArray()
			f.resize(p_n * p_n * 4)
			var ids := PackedByteArray()
			ids.resize(p_n * p_n)
			for y in p_n:
				for x in p_n:
					var v: Array = eval.call(g.cell_center(x, y, z))
					var i := y * p_n + x
					f.encode_half(i * 4, v[0])
					f.encode_half(i * 4 + 2, v[1])
					ids[i] = int(v[2])
			g._f.append(f)
			g._id.append(ids)
		return g

	func cell_center(x: int, y: int, z: int) -> Vector3:
		return gmin + (Vector3(x, y, z) + Vector3(0.5, 0.5, 0.5)) * cell

	func cell_net(x: int, y: int, z: int) -> float:
		return _f[z].decode_half((y * n + x) * 4)

	func cell_rival(x: int, y: int, z: int) -> float:
		return _f[z].decode_half((y * n + x) * 4 + 2)

	func cell_id(x: int, y: int, z: int) -> int:
		return _id[z][y * n + x]

	func net(p: Vector3) -> float:
		var u := (p - gmin) / cell - Vector3(0.5, 0.5, 0.5)
		var fx := floorf(u.x)
		var fy := floorf(u.y)
		var fz := floorf(u.z)
		var tx := u.x - fx
		var ty := u.y - fy
		var tz := u.z - fz
		var x0 := clampi(int(fx), 0, n - 1)
		var x1 := clampi(int(fx) + 1, 0, n - 1)
		var y0 := clampi(int(fy), 0, n - 1)
		var y1 := clampi(int(fy) + 1, 0, n - 1)
		var z0 := clampi(int(fz), 0, n - 1)
		var z1 := clampi(int(fz) + 1, 0, n - 1)
		var c00 := lerpf(cell_net(x0, y0, z0), cell_net(x1, y0, z0), tx)
		var c10 := lerpf(cell_net(x0, y1, z0), cell_net(x1, y1, z0), tx)
		var c01 := lerpf(cell_net(x0, y0, z1), cell_net(x1, y0, z1), tx)
		var c11 := lerpf(cell_net(x0, y1, z1), cell_net(x1, y1, z1), tx)
		return lerpf(lerpf(c00, c10, ty), lerpf(c01, c11, ty), tz)

	# Cell by cell. Net and rival within VALUE_TOL * max(1, |value|). The faction must agree
	# wherever the field is present, compared by palette colour (ids depend on feed order),
	# except at exact ties by `ref` (|net_a - net_b| <= VALUE_TOL; ref ids are `a`'s ids).
	# Returns {value_bad, id_bad, id_excused, first_bad}.
	static func compare(a: Grid, b: Grid, ref: Ref) -> Dictionary:
		var out := {"value_bad": 0, "id_bad": 0, "id_excused": 0, "first_bad": ""}
		if a.n != b.n:
			out.value_bad = -1
			return out
		for z in a.n:
			if a._f[z] == b._f[z] and a._id[z] == b._id[z]:
				continue
			for y in a.n:
				for x in a.n:
					var na: float = a.cell_net(x, y, z)
					var nb: float = b.cell_net(x, y, z)
					var ga: float = a.cell_rival(x, y, z)
					var gb: float = b.cell_rival(x, y, z)
					if absf(na - nb) > VALUE_TOL * maxf(1.0, absf(nb)) or absf(ga - gb) > VALUE_TOL * maxf(1.0, absf(gb)):
						out.value_bad += 1
						if out.first_bad == "":
							out.first_bad = "cell %d,%d,%d net %.4f vs %.4f rival %.4f vs %.4f" % [x, y, z, na, nb, ga, gb]
						continue
					if na <= 0.0 and nb <= 0.0:
						continue
					var ia: int = a.cell_id(x, y, z)
					var ib: int = b.cell_id(x, y, z)
					if ia == ib and a.colors == b.colors:
						continue
					if ia < a.colors.size() and ib < b.colors.size() and a.colors[ia].is_equal_approx(b.colors[ib]):
						continue
					if ref != null:
						var nets: Dictionary = ref.nets(a.cell_center(x, y, z))
						var ib_in_a := -1
						for k in a.colors.size():
							if ib < b.colors.size() and a.colors[k].is_equal_approx(b.colors[ib]):
								ib_in_a = k
								break
						if nets.has(ia) and nets.has(ib_in_a) and absf(nets[ia][0] - nets[ib_in_a][0]) <= VALUE_TOL:
							out.id_excused += 1
							continue
					out.id_bad += 1
					if out.first_bad == "":
						out.first_bad = "cell %d,%d,%d id %d vs %d" % [x, y, z, ia, ib]
		return out


# ---- FIELD-GRID -----------------------------------------------------------

func _check_grid_constants() -> void:
	var f: Node = _field_script.new()
	# TD-VG-B-14 (assumption-changed, Architect 2026-10-11, superseded by B23 prototype scale; history TD-VG-B-12): GRID_SIZE 198.0 -> 128.0
	# and GRID_MIN Vector3(-99,-99,-99) -> Vector3(-64,-64,-64) (2 * (R_BALL 50 + INFLUENCE_RADIUS 14), the prototype's rule
	# territory_field.gd:19-20 on origin/push/galaxy-field).
	var ok: bool = f.GRID_CELLS == 96 and is_equal_approx(f.GRID_SIZE, 128.0) and f.GRID_MIN.is_equal_approx(Vector3(-64, -64, -64))
	_check("FIELD-GRID", ok, "GRID_CELLS=%s GRID_SIZE=%s GRID_MIN=%s (96 cells over a 128-unit cube centred on the origin)" % [f.GRID_CELLS, f.GRID_SIZE, f.GRID_MIN])
	var r: float = f.INFLUENCE_RADIUS
	# TD-VG-B-14: old pin `R_BALL + r <= 99.0` (R_BALL 71 + R 28, B22), new `R_BALL + r <= 64.0` (R_BALL 50 read from galaxy_gen.gd, R 14 live).
	var r_ball: float = float(load(GEN_PATH).get_script_constant_map().get("R_BALL", -1.0))
	_check("FIELD-GRID-INFLUENCE", r > 0.0 and r_ball > 0.0 and r_ball + r <= 64.0, "INFLUENCE_RADIUS=%s, galaxy_gen R_BALL=%s: positive, ball radius + R inside the cube half-edge 64" % [r, r_ball])
	f.free()


# ---- FIELD-VALUES ---------------------------------------------------------

func _check_values() -> void:
	for p_seed in [11, 12]:
		var fx := fixture(p_seed)
		var wv := new_wv()
		feed(wv, fx)
		var field := await make_field(self, _field_script, wv)
		var grid := Grid.from_field(field)
		var ref := Ref.from_systems(ref_systems(field, fx), field.INFLUENCE_RADIUS)
		var rng := RandomNumberGenerator.new()
		rng.seed = 4242
		var bad := 0
		var id_bad := 0
		var id_checked := 0
		var present := 0
		var first := ""
		for _i in 3000:
			var x := rng.randi_range(0, grid.n - 1)
			var y := rng.randi_range(0, grid.n - 1)
			var z := rng.randi_range(0, grid.n - 1)
			var p: Vector3 = grid.cell_center(x, y, z)
			var e: Array = ref.eval(p)
			if absf(grid.cell_net(x, y, z) - e[0]) > VALUE_TOL * maxf(1.0, absf(e[0])) or absf(grid.cell_rival(x, y, z) - e[1]) > VALUE_TOL * maxf(1.0, absf(e[1])):
				bad += 1
				if first == "":
					first = "cell %d,%d,%d grid net %.4f rival %.4f exact %.4f %.4f" % [x, y, z, grid.cell_net(x, y, z), grid.cell_rival(x, y, z), e[0], e[1]]
			if e[0] > 0.01:
				present += 1
				id_checked += 1
				if grid.cell_id(x, y, z) != int(e[2]):
					var nets: Dictionary = ref.nets(p)
					if not (nets.has(grid.cell_id(x, y, z)) and absf(nets[grid.cell_id(x, y, z)][0] - e[0]) <= VALUE_TOL):
						id_bad += 1
		# Positive control for the sampling itself: the field has to be present in many sampled cells,
		# or an all-zero grid would pass the value check on empty space.
		_check("FIELD-VALUES-present", present >= 100, "seed %d: %d of 3000 sampled cells carry field (an empty grid must not pass)" % [p_seed, present])
		_check("FIELD-VALUES", bad == 0 and id_bad == 0, "seed %d: 3000 random cells, value_bad=%d id_bad=%d of %d with field %s" % [p_seed, bad, id_bad, id_checked, first])
		field.queue_free()
		wv.free()
		await process_frame


# ---- adapter signals ------------------------------------------------------

func _check_signals() -> void:
	var fx := fixture(11)
	var owned: Array = fx.filter(func(s): return s.fac >= 0)
	# Binding after the territories exist reads them (a late-bound field is not blind).
	var wv := new_wv()
	feed(wv, fx)
	var late := await make_field(self, _field_script, wv)
	var ids_ok := true
	for s in owned:
		ids_ok = ids_ok and late.faction_id_of(s.id) >= 0
	_check("FIELD-FEED-late-bind", ids_ok and late.faction_id_of("no-such-region") == -1, "every owned region has a faction id after a late bind; unknown region reads -1")
	# Same colour -> same id, distinct colours -> distinct ids, palette carries the colour.
	var by_fac := {}
	var map_ok := true
	for s in owned:
		var id: int = late.faction_id_of(s.id)
		if by_fac.has(s.fac) and by_fac[s.fac] != id:
			map_ok = false
		by_fac[s.fac] = id
		var c: Vector3 = late.palette[id]
		map_ok = map_ok and c.is_equal_approx(Vector3(s.color.r, s.color.g, s.color.b))
	var distinct := {}
	for v in by_fac.values():
		distinct[v] = true
	_check("FIELD-FEED-identity", map_ok and distinct.size() == by_fac.size() and by_fac.size() == FACTIONS, "%d colours -> %d ids, palette matches the colour (identity is the territory colour)" % [by_fac.size(), distinct.size()])
	late.queue_free()
	wv.free()
	# Live signals: a field bound to an empty node follows territory_set and territory_removed.
	var wv2 := new_wv()
	var live := await make_field(self, _field_script, wv2)
	_check("FIELD-FEED-clean", not live.is_dirty(), "a freshly filled field reports is_dirty()=%s" % live.is_dirty())
	var first_owned: Dictionary = owned[0]
	wv2.set_territory(first_owned.id, first_owned.pos, first_owned.sig, first_owned.color)
	_check("FIELD-FEED-set-dirty", live.is_dirty() and live.faction_id_of(first_owned.id) >= 0, "territory_set marks dirty and gives the region an id (dirty=%s)" % live.is_dirty())
	await process_frame
	await process_frame
	_check("FIELD-FEED-set-fill", not live.is_dirty() and live.fill_count >= 2, "the next frame refills (fill_count=%d, dirty=%s)" % [live.fill_count, live.is_dirty()])
	var before: int = live.fill_count
	wv2.remove_territory(first_owned.id)
	_check("FIELD-FEED-remove-dirty", live.is_dirty() and live.faction_id_of(first_owned.id) == -1, "territory_removed marks dirty and clears the region's id (id=%d)" % live.faction_id_of(first_owned.id))
	await process_frame
	await process_frame
	_check("FIELD-FEED-remove-fill", live.fill_count == before + 1 and not live.is_dirty(), "one refill after the removal (%d -> %d)" % [before, live.fill_count])
	# territory_updated: the node's data changes and the signal fires; the field must re-read.
	wv2.set_territory(first_owned.id, first_owned.pos, first_owned.sig, first_owned.color)
	await process_frame
	await process_frame
	var moved: Vector3 = first_owned.pos + Vector3(5, 0, 0)
	wv2.territories[first_owned.id]["center"] = moved
	wv2.territory_updated.emit(first_owned.id)
	_check("FIELD-FEED-updated-dirty", live.is_dirty(), "territory_updated marks dirty (dirty=%s)" % live.is_dirty())
	await process_frame
	await process_frame
	var one := Ref.from_systems([{"pos": moved, "significance": first_owned.sig, "owner": live.faction_id_of(first_owned.id)}], live.INFLUENCE_RADIUS)
	var grid := Grid.from_field(live)
	var bad := 0
	for p in [moved, moved + Vector3(2, 1, 0), moved + Vector3(-3, 0, 2)]:
		if absf(grid.net(p) - one.net(p)) > 0.02:
			bad += 1
	_check("FIELD-FEED-updated-moved", bad == 0 and grid.net(moved) > ISO, "after territory_updated the bubble sits at the new centre (net there %.3f, off-reference points %d)" % [grid.net(moved), bad])
	live.queue_free()
	wv2.free()
	await process_frame


# ---- FIELD-ORDER ----------------------------------------------------------

# Positive control: a field whose rival list depends on insertion order differs between two orders
# under this comparator; the exact reference does not.
func _control_order() -> void:
	var fx := fixture(11)
	var owned: Array = fx.filter(func(s): return s.fac >= 0)
	var a: Array = []
	for s in owned:
		a.append({"pos": s.pos, "significance": s.sig, "owner": s.fac})
	var b := shuffled(a, 5)
	var gmin := Vector3(-64, -64, -64)
	var wrap := func(f: Callable) -> Callable:
		return func(p: Vector3) -> Array: return [f.call(p), 0.0, 0]
	var ga := Grid.bake_cpu(32, gmin, 128.0, wrap.call(_old_order_dependent(a)))
	var gb := Grid.bake_cpu(32, gmin, 128.0, wrap.call(_old_order_dependent(b)))
	var old_cmp := Grid.compare(ga, gb, null)
	_check("FIELD-ORDER-control-old-rivals", old_cmp.value_bad > 0, "old per-faction rival list, two orders: %d cells differ (must be > 0 so the comparator catches an order-dependent field)" % old_cmp.value_bad)
	var ref_a := Ref.from_systems(a, 14.0)
	var ref_b := Ref.from_systems(b, 14.0)
	var ca := Grid.bake_cpu(32, gmin, 128.0, ref_a.eval)
	var cb := Grid.bake_cpu(32, gmin, 128.0, ref_b.eval)
	var exact_cmp := Grid.compare(ca, cb, ref_a)
	_check("FIELD-ORDER-control-exact", exact_cmp.value_bad == 0 and exact_cmp.id_bad == 0, "exact reference, two orders: value_bad=%d id_bad=%d (must be 0)" % [exact_cmp.value_bad, exact_cmp.id_bad])


# The OLD behaviour: one shell per faction, its rival list snapshotted when that faction's LAST
# system was added, so factions added later are missing from earlier factions' rival lists.
func _old_order_dependent(systems: Array) -> Callable:
	var shells := {}
	var added: Array = []
	for s in systems:
		added.append(s)
		var f := int(s.owner)
		var o: Array = []
		var rv: Array = []
		var m := 0.0
		for t in added:
			if int(t.owner) == f:
				o.append(t)
				m = maxf(m, float(t.significance))
			else:
				rv.append(t)
		shells[f] = {"own": o, "rival": rv, "max": maxf(m, 0.01)}
	return func(p: Vector3) -> float:
		var best := 0.0
		for f in shells:
			var sh: Dictionary = shells[f]
			var o := 0.0
			var rv := 0.0
			for t in sh.own:
				o += _kernel(p, t, sh.max)
			for t in sh.rival:
				rv = maxf(rv, _kernel(p, t, sh.max))
			best = maxf(best, o * (1.0 - GAP * smoothstep(0.3, 1.0, rv / maxf(o, 0.001))))
		return best


func _kernel(p: Vector3, s: Dictionary, norm_max: float) -> float:
	var r := 14.0 * (0.6 + 0.4 * clampf(float(s.significance) / norm_max, 0.0, 1.0))
	var d2: float = p.distance_squared_to(s.pos)
	if d2 >= r * r:
		return 0.0
	var k := 1.0 - d2 / (r * r)
	return k * k * k


# The same 80 regions fed in the original, reversed and two shuffled orders give the same grid.
func _check_order() -> void:
	var fx := fixture(11)
	var base_wv := new_wv()
	feed(base_wv, fx)
	var base := await make_field(self, _field_script, base_wv)
	var base_grid := Grid.from_field(base)
	var ref := Ref.from_systems(ref_systems(base, fx), base.INFLUENCE_RADIUS)
	var orders: Array = []
	var rev := fx.duplicate(true)
	rev.reverse()
	orders.append(rev)
	orders.append(shuffled(fx, 101))
	orders.append(shuffled(fx, 102))
	var worst := {"value_bad": 0, "id_bad": 0, "id_excused": 0, "first_bad": ""}
	for o in orders:
		var wv := new_wv()
		feed(wv, o)
		var f := await make_field(self, _field_script, wv)
		var cmp := Grid.compare(base_grid, Grid.from_field(f), ref)
		worst.value_bad += cmp.value_bad
		worst.id_bad += cmp.id_bad
		worst.id_excused += cmp.id_excused
		if worst.first_bad == "":
			worst.first_bad = cmp.first_bad
		f.queue_free()
		wv.free()
	_check("FIELD-ORDER", worst.value_bad == 0 and worst.id_bad == 0, "reversed + 2 shuffles vs original order: value_bad=%d id_bad=%d id_tie_excused=%d %s" % [worst.value_bad, worst.id_bad, worst.id_excused, worst.first_bad])
	base.queue_free()
	base_wv.free()
	await process_frame


# ---- FIELD-CONQUEST -------------------------------------------------------

# Owner changes the way the adapter's sync_system makes them: faction 0's first region goes to
# faction 1 (set_territory with faction 1's colour), faction 2's first to 3, one of faction 1's
# becomes unowned (remove_territory). Returns the changed region ids.
func _apply_conquests(fx: Array, wv: Node) -> Array:
	var changed: Array = []
	for p in [[0, 1], [2, 3], [1, -1]]:
		for s in fx:
			if s.fac == p[0] and not changed.has(s.id):
				changed.append(s.id)
				s.fac = p[1]
				if p[1] >= 0:
					s.color = Color.from_hsv(float(p[1]) / FACTIONS, 0.7, 0.9)
					if wv != null:
						wv.set_territory(s.id, s.pos, s.sig, s.color)
				elif wv != null:
					wv.remove_territory(s.id)
				break
	return changed


# Positive control: the grid before and after the owner changes differ (a skipped refill is detectable).
func _control_conquest() -> void:
	var fx := fixture(11)
	var after := fixture(11)
	_apply_conquests(after, null)
	var gmin := Vector3(-64, -64, -64)
	var as_sys := func(a: Array) -> Array:
		var out: Array = []
		for s in a:
			out.append({"pos": s.pos, "significance": s.sig, "owner": s.fac})
		return out
	var before_grid := Grid.bake_cpu(24, gmin, 128.0, Ref.from_systems(as_sys.call(fx), 14.0).eval)
	var after_grid := Grid.bake_cpu(24, gmin, 128.0, Ref.from_systems(as_sys.call(after), 14.0).eval)
	var cmp := Grid.compare(before_grid, after_grid, null)
	_check("FIELD-CONQUEST-control", cmp.value_bad + cmp.id_bad > 0, "grid before vs after the owner changes: %d value + %d id cells differ (must be > 0)" % [cmp.value_bad, cmp.id_bad])


func _check_conquest() -> void:
	var fx := fixture(11)
	var wv := new_wv()
	feed(wv, fx)
	var field := await make_field(self, _field_script, wv)
	var before := Grid.from_field(field)
	_check("FIELD-CONQUEST-clean", not field.is_dirty(), "freshly filled field reports is_dirty()=%s" % field.is_dirty())
	var fills_before: int = field.fill_count
	var changed := _apply_conquests(fx, wv)
	_check("FIELD-CONQUEST-dirty", field.is_dirty(), "after %d owner changes via the territory signals is_dirty()=%s (true before the next frame)" % [changed.size(), field.is_dirty()])
	for _f in 3:
		await process_frame
	var fills: int = field.fill_count - fills_before
	_check("FIELD-CONQUEST-once", fills == 1 and not field.is_dirty(), "%d owner changes in one frame caused %d fill(s) over 3 frames (exactly 1), dirty afterwards=%s" % [changed.size(), fills, field.is_dirty()])
	var wv2 := new_wv()
	feed(wv2, fx)
	var fresh := await make_field(self, _field_script, wv2)
	var ref := Ref.from_systems(ref_systems(field, fx), field.INFLUENCE_RADIUS)
	var cmp := Grid.compare(Grid.from_field(field), Grid.from_field(fresh), ref)
	_check("FIELD-CONQUEST", cmp.value_bad == 0 and cmp.id_bad == 0, "grid after owner changes vs a fresh fill of the same state: value_bad=%d id_bad=%d id_tie_excused=%d %s" % [cmp.value_bad, cmp.id_bad, cmp.id_excused, cmp.first_bad])
	var stale := Grid.compare(before, Grid.from_field(fresh), ref)
	_check("FIELD-CONQUEST-effect", stale.value_bad + stale.id_bad > 0, "the owner changes did alter the grid (%d value + %d id cells differ from the before-grid)" % [stale.value_bad, stale.id_bad])
	field.queue_free()
	fresh.queue_free()
	wv.free()
	wv2.free()
	await process_frame


# ---- FIELD-MEM ------------------------------------------------------------

func _check_mem() -> void:
	var fx := fixture(11)
	var wv := new_wv()
	feed(wv, fx)
	var field := await make_field(self, _field_script, wv)
	var bytes := 0
	for img in field.field_texture.get_data():
		bytes += img.get_data().size()
	for img in field.id_texture.get_data():
		bytes += img.get_data().size()
	var formats_ok: bool = field.field_texture.get_format() == Image.FORMAT_RGH and field.id_texture.get_format() == Image.FORMAT_R8
	_check("FIELD-MEM", bytes <= MEM_MAX_BYTES and bytes == 96 * 96 * 96 * 5 and formats_ok, "field + id textures hold %d bytes (96^3 cells * (4 RGH + 1 R8) = 4423680, limit %d), formats RGH/R8 ok=%s" % [bytes, MEM_MAX_BYTES, formats_ok])
	field.queue_free()
	wv.free()
	await process_frame
