extends SceneTree
# PARK file (lane B, B0 pre-check; spec 2026-10-07-visible-game-spec.md rev 4):
# FIELD-EQ, the territory field's first surface along random rays against the
# exact legacy formulas, on the game's 80-region fixture. The thresholds are
# Westley's (FIELD-EQ 2% different, median, p95): this file is run and its
# numbers reported, a red here is parked for him, never widened by a builder.
# Needs a real renderer (the card fills the grid): xvfb-run godot --path . --rendering-driver vulkan
# --script res://tests/test_galaxy_field_park_field_eq.gd. Headless fails DEVICE on purpose.
# Contract for the product (B1): res://scenes/galaxy/territory_field.gd, extends Node, with
# GRID_CELLS, GRID_SIZE, GRID_MIN, set_systems(Array of {pos, significance, owner}), refill(),
# field_texture (RGH), id_texture (R8) and a const INFLUENCE_RADIUS (default 14.0 here when absent).
# Positive controls: exact vs itself passes the comparator, exact vs radius*0.9 fails it.
# TERRITORY_FIELD_SCRIPT overrides the product path (used for the B0 measurement on a copy of the
# field branch's node).
# See also: tests/test_galaxy_field_park_refill.gd; origin/push/galaxy-field test_field.gd (source).

const FieldRef := preload("res://tests/galaxy_field/field_reference.gd")
const GridSampler := preload("res://tests/galaxy_field/grid_sampler.gd")
const Fixture := preload("res://tests/galaxy_field/game_fixture.gd")
var FIELD_PATH := "res://scenes/galaxy/territory_field.gd"

const RAYS := 2000
const RAY_STEP := 0.25
const SAME_SURFACE_MAX := 1.0     # first surfaces further apart than this are "different"
const MEDIAN_MAX := 0.1
const P95_MAX := 0.4
const DIFFERENT_MAX := 0.02       # Westley's FIELD-EQ 2%
const BALL := 45.0                # ray targets stay inside the fixture's disc (radius 40) plus a margin

var _failures := 0


func _initialize() -> void:
	await _run()
	print("FIELD-EQ PARK %s" % ("FAILED: %d" % _failures if _failures > 0 else "OK"))
	quit(1 if _failures > 0 else 0)


func _check(id: String, ok: bool, detail: String) -> void:
	if not ok:
		_failures += 1
	print("CHECK %s %s %s" % [id, "PASS" if ok else "FAIL", detail])


func _run() -> void:
	if OS.get_environment("TERRITORY_FIELD_SCRIPT") != "":
		FIELD_PATH = OS.get_environment("TERRITORY_FIELD_SCRIPT")
	var headless := DisplayServer.get_name() == "headless"
	_check("DEVICE", not headless, "renderer %s on %s (the grid needs a real renderer)" % [RenderingServer.get_video_adapter_name(), DisplayServer.get_name()])
	var systems := Fixture.systems()
	var rays := _rays(_rng(4242), RAYS)
	var exact := FieldRef.from_systems(systems)
	var wrong := FieldRef.from_systems(systems, 0.9)
	_check("FIELD-EQ-control-same", _ok(_compare(exact.net, exact.net, rays)), "exact vs exact")
	_check("FIELD-EQ-control-wrong-radius", not _ok(_compare(exact.net, wrong.net, rays)), "exact vs radius*0.9 must FAIL the comparator")
	if not ResourceLoader.exists(FIELD_PATH):
		_check("FIELD-EQ", false, "%s does not exist" % FIELD_PATH)
		return
	if headless:
		return
	var script: GDScript = load(FIELD_PATH)
	var field: Node = script.new()
	var radius: float = script.get_script_constant_map().get("INFLUENCE_RADIUS", 14.0)
	root.add_child(field)
	await process_frame
	await process_frame
	field.set_systems(systems.duplicate(true))
	field.refill()
	var grid := GridSampler.from_field(field)
	var exact_r := FieldRef.from_systems(systems, 1.0, radius)
	var r := _compare(exact_r.net, grid.net, rays)
	_check("FIELD-EQ", _ok(r), "80-region fixture, %d systems owned, R=%.1f: %s" % [_owned(systems), radius, _detail(r)])
	field.queue_free()


func _owned(systems: Array) -> int:
	var n := 0
	for s in systems:
		if int(s.owner) >= 0:
			n += 1
	return n


func _rng(s: int) -> RandomNumberGenerator:
	var rng := RandomNumberGenerator.new()
	rng.seed = s
	return rng


func _rays(rng: RandomNumberGenerator, count: int) -> Array:
	var out: Array = []
	while out.size() < count:
		var start := _unit(rng) * 95.0
		var target := _unit(rng) * (BALL * pow(rng.randf(), 1.0 / 3.0))
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


func _compare(a: Callable, b: Callable, rays: Array) -> Dictionary:
	var errs: Array = []
	var different := 0
	var missed := 0
	var hit_a := 0
	for r in rays:
		var ta := GridSampler.first_surface(a, r[0], r[1], r[2], r[3], RAY_STEP)
		var tb := GridSampler.first_surface(b, r[0], r[1], r[2], r[3], RAY_STEP)
		if ta < 0.0 and tb < 0.0:
			continue
		hit_a += 1
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
		"different": different, "n": rays.size(), "same": errs.size(), "missed": missed, "hit": hit_a,
	}


func _ok(r: Dictionary) -> bool:
	return r.same > 0 and r.median <= MEDIAN_MAX and r.p95 <= P95_MAX and float(r.different) / float(r.n) <= DIFFERENT_MAX


func _detail(r: Dictionary) -> String:
	return "median=%.4f (<=%.2f) p95=%.4f (<=%.2f) different=%d/%d=%.2f%% (<=%.0f%%) rays_with_a_surface=%d missed_by_grid=%d" % [r.median, MEDIAN_MAX, r.p95, P95_MAX, r.different, r.n, 100.0 * r.different / r.n, 100.0 * DIFFERENT_MAX, r.hit, r.missed]
