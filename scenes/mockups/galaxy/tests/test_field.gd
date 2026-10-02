extends SceneTree
# Field checks: FIELD-EQ, FIELD-VALUES, FIELD-ORDER, FIELD-CONQUEST, FIELD-MEM
# (spec 2026-10-02-galaxy-bubble-field-spec.md, Step 2). Frozen after the
# "galaxy field: failing tests" commit; builders do not edit.
#
# Needs a real renderer (the grid is filled by the graphics card), so it runs
# window-free under Xvfb + Vulkan: scenes/mockups/galaxy/tests/run_fast.sh.
# Under the dummy/headless renderer every check fails on purpose (DEVICE).
#
# Contract for res://scenes/mockups/galaxy/territory_field.gd (extends Node),
# fixed here because the spec leaves the signatures to the tests:
#   const GRID_CELLS := 96            cells per side
#   const GRID_SIZE := 128.0          cube edge in world units
#   const GRID_MIN := Vector3(-64, -64, -64)   cube corner (BALL_RADIUS + INFLUENCE_RADIUS)
#   func set_systems(systems: Array) -> void
#       replace the list (Galaxy.systems entries: pos, significance, owner;
#       owner -1 = ignored); copies what it needs; marks dirty
#   func set_system_owner(index: int, owner: int) -> void
#       index into the array last given to set_systems; marks dirty if it changed
#   func is_dirty() -> bool
#   func refill() -> void
#       synchronous whole-grid fill now; clears dirty; fill_count += 1.
#       _process calls it when dirty, so at most once per frame.
#   var fill_count: int
#   var field_texture: Texture3D      FORMAT_RGH, R = net, G = seam term
#   var id_texture: Texture3D         FORMAT_R8, byte = faction id
# Cell values follow tests/field_reference.gd (exact legacy formulas).

const FieldRef := preload("res://scenes/mockups/galaxy/tests/field_reference.gd")
const BigGalaxy := preload("res://scenes/mockups/galaxy/tests/big_galaxy.gd")
const GridSampler := preload("res://scenes/mockups/galaxy/tests/grid_sampler.gd")
# TERRITORY_FIELD_SCRIPT overrides the path: used only to validate this harness
# against a stand-in that fills the grid on the CPU (never in normal runs).
var FIELD_PATH := "res://scenes/mockups/galaxy/territory_field.gd"

const RAYS := 2000
const RAY_STEP := 0.25
const SAME_SURFACE_MAX := 1.0     # first surfaces further apart than this are "different"
const MEDIAN_MAX := 0.1
const P95_MAX := 0.4
const DIFFERENT_MAX := 0.02
const MEM_MAX_BYTES := 5 * 1024 * 1024

var _failures := 0
var _field_script: GDScript


func _initialize() -> void:
	await _run()
	if _failures > 0:
		print("FIELD TESTS FAILED: %d" % _failures)
		quit(1)
	else:
		print("FIELD TESTS OK")
		quit(0)


func _run() -> void:
	if OS.get_environment("TERRITORY_FIELD_SCRIPT") != "":
		FIELD_PATH = OS.get_environment("TERRITORY_FIELD_SCRIPT")
		print("NOTE field script overridden: %s" % FIELD_PATH)
	var headless := DisplayServer.get_name() == "headless"
	_check("DEVICE", not headless, "renderer %s on %s (the grid needs a real renderer; run tests/run_fast.sh)" % [RenderingServer.get_video_adapter_name(), DisplayServer.get_name()])
	print("DEVICE name=%s method=%s" % [RenderingServer.get_video_adapter_name(), RenderingServer.get_current_rendering_method()])

	# Detector controls first: they need only the CPU reference, so they run
	# (and must pass) even before the product exists.
	_control_field_eq()
	_control_field_order()
	_control_conquest()

	if not ResourceLoader.exists(FIELD_PATH):
		_check("FIELD-EQ", false, "%s does not exist" % FIELD_PATH)
		_check("FIELD-VALUES", false, "%s does not exist" % FIELD_PATH)
		_check("FIELD-ORDER", false, "%s does not exist" % FIELD_PATH)
		_check("FIELD-CONQUEST", false, "%s does not exist" % FIELD_PATH)
		_check("FIELD-MEM", false, "%s does not exist" % FIELD_PATH)
		return
	_field_script = load(FIELD_PATH)
	if headless:
		return

	var cases := [
		["seed11", GalaxyGen.new().generate(11)],
		["seed12", GalaxyGen.new().generate(12)],
		["seed13", GalaxyGen.new().generate(13)],
		["400/15", BigGalaxy.make(11, 400, 15, 9.0)],
	]
	_check_contract_constants()
	for c in cases:
		await _check_field_eq(c[0], c[1])
	await _check_isolated_bubbles()
	await _check_field_order(cases)
	await _check_conquest(cases[0][1])
	await _check_mem()


func _check(id: String, ok: bool, detail: String) -> void:
	if not ok:
		_failures += 1
	print("CHECK %s %s %s" % [id, "PASS" if ok else "FAIL", detail])


# A field node lives in the tree for two frames before it is first filled, as
# the shell renderer's does (a fill requested in the same frame the node was
# added is not part of the contract).
func _make_field(systems: Array) -> Node:
	var f: Node = _field_script.new()
	root.add_child(f)
	await process_frame
	await process_frame
	f.set_systems(systems.duplicate(true))
	f.refill()
	return f


func _check_contract_constants() -> void:
	var f: Node = _field_script.new()
	var ok: bool = f.GRID_CELLS == 96 and is_equal_approx(f.GRID_SIZE, 128.0) and f.GRID_MIN.is_equal_approx(Vector3(-64, -64, -64))
	_check("FIELD-GRID", ok, "GRID_CELLS=%s GRID_SIZE=%s GRID_MIN=%s (spec: 96 cells over a 128-unit cube, BALL_RADIUS + INFLUENCE_RADIUS = 64 each side)" % [f.GRID_CELLS, f.GRID_SIZE, f.GRID_MIN])
	f.free()


# ---- rays ----------------------------------------------------------------

func _rays(rng: RandomNumberGenerator, count: int) -> Array:
	var out: Array = []
	while out.size() < count:
		var start := _unit(rng) * 95.0
		var target := _unit(rng) * (45.0 * pow(rng.randf(), 1.0 / 3.0))
		var d := (target - start).normalized()
		var b := start.dot(d)
		var disc := b * b - (start.length_squared() - 66.0 * 66.0)
		if disc <= 0.0:
			continue
		var s := sqrt(disc)
		out.append([start, d, maxf(-b - s, 0.0), -b + s])
	return out


func _unit(rng: RandomNumberGenerator) -> Vector3:
	var cz := rng.randf_range(-1.0, 1.0)
	var sz := sqrt(1.0 - cz * cz)
	var th := rng.randf() * TAU
	return Vector3(cos(th) * sz, sin(th) * sz, cz)


# {median, p95, different, n, same, missed}: first surface by `a` vs `b` along
# the rays; "different" = one found none, or they are > SAME_SURFACE_MAX apart.
func _compare_surfaces(a: Callable, b: Callable, rays: Array) -> Dictionary:
	var errs: Array = []
	var different := 0
	var missed := 0
	for r in rays:
		var ta := GridSampler.first_surface(a, r[0], r[1], r[2], r[3], RAY_STEP)
		var tb := GridSampler.first_surface(b, r[0], r[1], r[2], r[3], RAY_STEP)
		if ta < 0.0 and tb < 0.0:
			continue
		if ta < 0.0 or tb < 0.0:
			different += 1
			if tb < 0.0:
				missed += 1
			continue
		var e := absf(ta - tb)
		if e > SAME_SURFACE_MAX:
			different += 1
		else:
			errs.append(e)
	errs.sort()
	return {
		"median": errs[errs.size() / 2] if errs.size() > 0 else INF,
		"p95": errs[int(errs.size() * 0.95)] if errs.size() > 0 else INF,
		"different": different, "n": rays.size(), "same": errs.size(), "missed": missed,
	}


func _surfaces_ok(r: Dictionary) -> bool:
	return r.same > 0 and r.median <= MEDIAN_MAX and r.p95 <= P95_MAX and float(r.different) / float(r.n) <= DIFFERENT_MAX


func _surface_detail(r: Dictionary) -> String:
	return "median=%.4f (<=%.2f) p95=%.4f (<=%.2f) different=%d/%d=%.2f%% (<=%.0f%%) missed_by_grid=%d" % [r.median, MEDIAN_MAX, r.p95, P95_MAX, r.different, r.n, 100.0 * r.different / r.n, 100.0 * DIFFERENT_MAX, r.missed]


# ---- FIELD-EQ ------------------------------------------------------------

# Positive control: exact field vs the same field with a wrong radius (0.9 R)
# must fail; exact vs itself must pass (so the comparator is neither blind nor
# trigger-happy).
func _control_field_eq() -> void:
	var g := GalaxyGen.new().generate(11)
	var exact := FieldRef.from_systems(g.systems)
	var wrong := FieldRef.from_systems(g.systems, 0.9)
	var rays := _rays(RandomNumberGenerator.new(), RAYS)
	var same := _compare_surfaces(exact.net, exact.net, rays)
	var bad := _compare_surfaces(exact.net, wrong.net, rays)
	_check("FIELD-EQ-control-same", _surfaces_ok(same), "exact vs exact: " + _surface_detail(same))
	_check("FIELD-EQ-control-wrong-radius", not _surfaces_ok(bad), "exact vs radius*0.9 must FAIL the comparator: " + _surface_detail(bad))


func _check_field_eq(label: String, g: Galaxy) -> void:
	var field := await _make_field(g.systems)
	var grid := GridSampler.from_field(field)
	var exact := FieldRef.from_systems(g.systems)
	var rng := RandomNumberGenerator.new()
	rng.seed = 4242
	var r := _compare_surfaces(exact.net, grid.net, _rays(rng, RAYS))
	_check("FIELD-EQ", _surfaces_ok(r), "%s: %s" % [label, _surface_detail(r)])
	# FIELD-VALUES (added by the test author, not in the spec table): cell values
	# match the exact formulas to half-float rounding, ids match off exact ties.
	var bad := 0
	var id_bad := 0
	var id_checked := 0
	var first := ""
	for _i in 3000:
		var x := rng.randi_range(0, grid.n - 1)
		var y := rng.randi_range(0, grid.n - 1)
		var z := rng.randi_range(0, grid.n - 1)
		var p: Vector3 = grid.cell_center(x, y, z)
		var e: Array = exact.eval(p)
		var tol: float = 0.002 * maxf(1.0, absf(e[0]))
		if absf(grid.cell_net(x, y, z) - e[0]) > tol or absf(grid.cell_rival(x, y, z) - e[1]) > 0.002 * maxf(1.0, absf(e[1])):
			bad += 1
			if first == "":
				first = "cell %d,%d,%d grid net %.4f rival %.4f exact %.4f %.4f" % [x, y, z, grid.cell_net(x, y, z), grid.cell_rival(x, y, z), e[0], e[1]]
		if e[0] > 0.01:
			id_checked += 1
			if grid.cell_id(x, y, z) != int(e[2]):
				var nets: Dictionary = exact.nets(p)
				if not (nets.has(grid.cell_id(x, y, z)) and absf(nets[grid.cell_id(x, y, z)][0] - e[0]) <= 0.002):
					id_bad += 1
	_check("FIELD-VALUES", bad == 0 and id_bad == 0, "%s: 3000 random cells, value_bad=%d id_bad=%d of %d with field %s" % [label, bad, id_bad, id_checked, first])
	field.queue_free()
	await process_frame


# No isolated bubble missed: 24 single-system bubbles (smallest normalised
# significances, 0.3 and 0.0) at random sub-cell offsets; 40 rays through each
# centre; the grid must find a surface on every ray that the exact field does.
func _check_isolated_bubbles() -> void:
	var rng := RandomNumberGenerator.new()
	rng.seed = 77
	var sites: Array = []
	for ix in 4:
		for iy in 4:
			for iz in 4:
				sites.append(Vector3(-42 + 28 * ix, -42 + 28 * iy, -42 + 28 * iz))
	# deterministic shuffle
	for i in range(sites.size() - 1, 0, -1):
		var j := rng.randi_range(0, i)
		var t = sites[i]
		sites[i] = sites[j]
		sites[j] = t
	var systems: Array = []
	var bubbles: Array = []
	for i in 24:
		var pos: Vector3 = sites[i] + Vector3(rng.randf(), rng.randf(), rng.randf()) * (128.0 / 96.0)
		var f := 0 if i < 12 else 1
		systems.append({"id": systems.size(), "pos": pos, "significance": 0.3 if f == 0 else 0.0, "owner": f})
		bubbles.append(pos)
	systems.append({"id": systems.size(), "pos": sites[24], "significance": 1.0, "owner": 0})
	systems.append({"id": systems.size(), "pos": sites[25], "significance": 1.0, "owner": 1})
	var field := await _make_field(systems)
	var grid := GridSampler.from_field(field)
	var exact := FieldRef.from_systems(systems)
	var missed := 0
	var exact_missed := 0
	var total := 0
	for c in bubbles:
		for _k in 40:
			var d := _unit(rng)
			var o: Vector3 = c + d * 30.0
			var dir := -d
			var te := GridSampler.first_surface(exact.net, o, dir, 0.0, 30.0, RAY_STEP)
			var tg := GridSampler.first_surface(grid.net, o, dir, 0.0, 30.0, RAY_STEP)
			total += 1
			if te < 0.0:
				exact_missed += 1
			if tg < 0.0:
				missed += 1
	_check("FIELD-EQ-isolated", missed == 0 and exact_missed == 0, "24 isolated bubbles (significance 0.3 and 0.0), %d rays: grid missed %d, exact missed %d (scenario sanity, must be 0)" % [total, missed, exact_missed])
	field.queue_free()
	await process_frame


# ---- FIELD-ORDER ---------------------------------------------------------

func _shuffled(systems: Array, seed_: int) -> Array:
	var out := systems.duplicate(true)
	var rng := RandomNumberGenerator.new()
	rng.seed = seed_
	for i in range(out.size() - 1, 0, -1):
		var j := rng.randi_range(0, i)
		var t = out[i]
		out[i] = out[j]
		out[j] = t
	return out


# Positive control: the old per-faction rival list (snapshotted at each
# faction's last add) is order dependent, so the same comparator must flag two
# orders of it. Coarse 24-cell CPU grids.
func _control_field_order() -> void:
	var g := BigGalaxy.make(11, 150, 8, 10.0)
	var a_sys: Array = g.systems.duplicate(true)
	var b_sys := _shuffled(g.systems, 5)
	var gmin := Vector3(-64, -64, -64)
	var old_a: Callable = FieldRef.old_order_dependent(a_sys)
	var old_b: Callable = FieldRef.old_order_dependent(b_sys)
	var wrap := func(f: Callable) -> Callable:
		return func(p: Vector3) -> Array: return [f.call(p), 0.0, 0]
	var ga := GridSampler.bake_cpu(32, gmin, 128.0, wrap.call(old_a))
	var gb := GridSampler.bake_cpu(32, gmin, 128.0, wrap.call(old_b))
	var old_cmp := GridSampler.compare(ga, gb, null)
	_check("FIELD-ORDER-control-old-rivals", old_cmp.value_bad > 0, "old per-faction rival list, two orders: %d cells differ (must be > 0 so the comparator catches an order-dependent field)" % old_cmp.value_bad)
	var ref_a := FieldRef.from_systems(a_sys)
	var ref_b := FieldRef.from_systems(b_sys)
	var ca := GridSampler.bake_cpu(32, gmin, 128.0, ref_a.eval)
	var cb := GridSampler.bake_cpu(32, gmin, 128.0, ref_b.eval)
	var exact_cmp := GridSampler.compare(ca, cb, ref_a)
	_check("FIELD-ORDER-control-exact", exact_cmp.value_bad == 0 and exact_cmp.id_bad == 0, "exact reference, two orders: value_bad=%d id_bad=%d (must be 0, comparator not trigger-happy)" % [exact_cmp.value_bad, exact_cmp.id_bad])


func _check_field_order(cases: Array) -> void:
	for c in [cases[0], cases[3]]:
		var g: Galaxy = c[1]
		var base := await _make_field(g.systems)
		var base_grid := GridSampler.from_field(base)
		var ref := FieldRef.from_systems(g.systems)
		var worst := {"value_bad": 0, "id_bad": 0, "id_excused": 0, "first_bad": ""}
		var orders := [g.systems.duplicate(true)]
		orders[0].reverse()
		orders.append(_shuffled(g.systems, 101))
		orders.append(_shuffled(g.systems, 102))
		for o in orders:
			var f := await _make_field(o)
			var cmp := GridSampler.compare(base_grid, GridSampler.from_field(f), ref)
			worst.value_bad += cmp.value_bad
			worst.id_bad += cmp.id_bad
			worst.id_excused += cmp.id_excused
			if worst.first_bad == "":
				worst.first_bad = cmp.first_bad
			f.queue_free()
		_check("FIELD-ORDER", worst.value_bad == 0 and worst.id_bad == 0, "%s: reversed + 2 shuffles vs original order: value_bad=%d id_bad=%d id_tie_excused=%d %s" % [c[0], worst.value_bad, worst.id_bad, worst.id_excused, worst.first_bad])
		base.queue_free()
		await process_frame


# ---- FIELD-CONQUEST ------------------------------------------------------

# Positive control: grids of the state before and after an owner change differ
# (a renderer that skipped the refill would keep serving the "before" grid).
func _control_conquest() -> void:
	var g := GalaxyGen.new().generate(11)
	var after := g.systems.duplicate(true)
	_apply_conquests(after)
	var gmin := Vector3(-64, -64, -64)
	var before_grid := GridSampler.bake_cpu(24, gmin, 128.0, FieldRef.from_systems(g.systems).eval)
	var after_grid := GridSampler.bake_cpu(24, gmin, 128.0, FieldRef.from_systems(after).eval)
	var cmp := GridSampler.compare(before_grid, after_grid, null)
	_check("FIELD-CONQUEST-control", cmp.value_bad + cmp.id_bad > 0, "grid before vs after the owner changes: %d value + %d id cells differ (must be > 0 so a skipped refill is detectable)" % [cmp.value_bad, cmp.id_bad])


func _apply_conquests(systems: Array) -> Array:
	# faction 0's first system goes to faction 1, faction 2's first to 3, and
	# one of faction 1's becomes unowned (revolt); returns the changed indices.
	var changed: Array = []
	var picks := [[0, 1], [2, 3], [1, -1]]
	for p in picks:
		for s in systems:
			if s.owner == p[0] and not changed.has(s.id):
				s.owner = p[1]
				changed.append(s.id)
				break
	return changed


func _check_conquest(g: Galaxy) -> void:
	var start := g.systems.duplicate(true)
	var field := await _make_field(start)
	var before := GridSampler.from_field(field)
	_check("FIELD-CONQUEST-clean", not field.is_dirty(), "freshly filled field reports is_dirty()=%s (must be false)" % field.is_dirty())
	var final_sys := start.duplicate(true)
	var changed := _apply_conquests(final_sys)
	var fills_before: int = field.fill_count
	for i in changed:
		field.set_system_owner(i, final_sys[i].owner)
	_check("FIELD-CONQUEST-dirty", field.is_dirty(), "after %d owner changes is_dirty()=%s (must be true before the next frame)" % [changed.size(), field.is_dirty()])
	for _f in 3:
		await process_frame
	var fills: int = field.fill_count - fills_before
	_check("FIELD-CONQUEST-once", fills == 1 and not field.is_dirty(), "%d owner changes in one frame caused %d fill(s) over 3 frames (must be exactly 1), dirty afterwards=%s" % [changed.size(), fills, field.is_dirty()])
	var fresh := await _make_field(final_sys)
	var ref := FieldRef.from_systems(final_sys)
	var after := GridSampler.from_field(field)
	var cmp := GridSampler.compare(after, GridSampler.from_field(fresh), ref)
	_check("FIELD-CONQUEST", cmp.value_bad == 0 and cmp.id_bad == 0, "grid after owner changes vs a fresh fill: value_bad=%d id_bad=%d id_tie_excused=%d %s" % [cmp.value_bad, cmp.id_bad, cmp.id_excused, cmp.first_bad])
	var stale := GridSampler.compare(before, GridSampler.from_field(fresh), ref)
	_check("FIELD-CONQUEST-effect", stale.value_bad + stale.id_bad > 0, "the owner changes did alter the grid (%d value + %d id cells differ from the before-grid); a skipped refill would have failed" % [stale.value_bad, stale.id_bad])
	field.queue_free()
	fresh.queue_free()
	await process_frame


# ---- FIELD-MEM -----------------------------------------------------------

func _check_mem() -> void:
	var g := GalaxyGen.new().generate(11)
	var field := await _make_field(g.systems)
	var total := 0
	var parts: Array = []
	for t in [field.field_texture, field.id_texture]:
		var px := Image.create(1, 1, false, t.get_format()).get_data().size()
		var bytes: int = t.get_width() * t.get_height() * t.get_depth() * px
		total += bytes
		parts.append("%dx%dx%d fmt %d = %d B" % [t.get_width(), t.get_height(), t.get_depth(), t.get_format(), bytes])
	var formats_ok: bool = field.field_texture.get_format() == Image.FORMAT_RGH and field.id_texture.get_format() == Image.FORMAT_R8
	_check("FIELD-MEM", total <= MEM_MAX_BYTES and formats_ok, "field textures %.2f MiB (<= 5 MiB): %s; formats RGH + R8 required" % [total / 1048576.0, ", ".join(parts)])
	field.queue_free()
	await process_frame
