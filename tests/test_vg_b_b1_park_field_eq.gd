extends SceneTree
# test-timeout: 20000

# PARK FILE (Westley's threshold): FIELD-EQ of lane B piece B1, the fraction of rays whose first
# surface in the grid differs from the exact field's (DIFFERENT_MAX = 2%, Westley 2026-10-07).
# The clerk leaves this file off the candidate when red and keeps it on push/vg-parked; the code
# it covers lands. Helpers (fixture, Ref, Grid, rays) are preloaded from tests/test_vg_b_b1.gd.
# See also: tests/test_vg_b_b1.gd, scenes/mockups/galaxy/tests/test_field.gd (origin/push/galaxy-field).
# Run: xvfb-run -a ~/.local/bin/godot.real --path . -s tests/test_vg_b_b1_park_field_eq.gd

const B1 := preload("res://tests/test_vg_b_b1.gd")

const RAYS := 2000
const RAY_STEP := 0.25
const SAME_SURFACE_MAX := 1.0     # first surfaces further apart than this are "different"
const MEDIAN_MAX := 0.1
const P95_MAX := 0.4
const DIFFERENT_MAX := 0.02       # Westley's

var _failures := 0


func _initialize() -> void:
	await _run()
	print("FIELD-EQ PARK %s" % ("FAILED: %d" % _failures if _failures > 0 else "OK"))
	quit(1 if _failures > 0 else 0)


func _check(id: String, ok: bool, detail: String) -> void:
	if not ok:
		_failures += 1
	print("CHECK %s %s %s" % [id, "PASS" if ok else "FAIL", detail])


func _compare(a: Callable, b: Callable, rs: Array) -> Dictionary:
	var errs: Array = []
	var different := 0
	var missed := 0
	for r in rs:
		var ta: float = B1.first_surface(a, r[0], r[1], r[2], r[3], RAY_STEP)
		var tb: float = B1.first_surface(b, r[0], r[1], r[2], r[3], RAY_STEP)
		if ta < 0.0 and tb < 0.0:
			continue
		if ta < 0.0 or tb < 0.0:
			different += 1
			if tb < 0.0:
				missed += 1
			continue
		if absf(ta - tb) > SAME_SURFACE_MAX:
			different += 1
		else:
			errs.append(absf(ta - tb))
	errs.sort()
	return {"median": errs[errs.size() / 2] if errs.size() > 0 else INF, "p95": errs[int(errs.size() * 0.95)] if errs.size() > 0 else INF,
		"different": different, "n": rs.size(), "same": errs.size(), "missed": missed}


func _ok(r: Dictionary) -> bool:
	return r.same > 0 and r.median <= MEDIAN_MAX and r.p95 <= P95_MAX and float(r.different) / float(r.n) <= DIFFERENT_MAX


func _detail(r: Dictionary) -> String:
	return "median=%.4f (<=%.2f) p95=%.4f (<=%.2f) different=%d/%d=%.2f%% (<=%.0f%%) missed_by_grid=%d" % [r.median, MEDIAN_MAX, r.p95, P95_MAX, r.different, r.n, 100.0 * r.different / r.n, 100.0 * DIFFERENT_MAX, r.missed]


func _run() -> void:
	# Positive controls (CPU only): exact vs exact passes; exact vs radius * 0.9 must fail.
	var fx0 := B1.fixture(11)
	var sys0: Array = []
	for s in fx0:
		if s.fac >= 0:
			sys0.append({"pos": s.pos, "significance": s.sig, "owner": s.fac})
	var exact0 := B1.Ref.from_systems(sys0, 14.0)
	var wrong0 := B1.Ref.from_systems(sys0, 14.0, 0.9)
	var rs0 := B1.rays(RandomNumberGenerator.new(), RAYS)
	_check("FIELD-EQ-control-same", _ok(_compare(exact0.net, exact0.net, rs0)), "exact vs exact")
	var bad := _compare(exact0.net, wrong0.net, rs0)
	_check("FIELD-EQ-control-wrong-radius", not _ok(bad), "exact vs radius*0.9 must FAIL: " + _detail(bad))
	var headless := DisplayServer.get_name() == "headless"
	_check("DEVICE", not headless, "renderer %s on %s (run under xvfb-run)" % [RenderingServer.get_video_adapter_name(), DisplayServer.get_name()])
	if not ResourceLoader.exists(B1.FIELD_PATH):
		_check("FIELD-EQ", false, "%s does not exist" % B1.FIELD_PATH)
		return
	if headless:
		return
	var script: GDScript = load(B1.FIELD_PATH)
	for p_seed in [11, 12, 13]:
		var fx := B1.fixture(p_seed)
		var wv := B1.new_wv()
		B1.feed(wv, fx)
		var field: Node = await B1.make_field(self, script, wv)
		var grid := B1.Grid.from_field(field)
		var exact := B1.Ref.from_systems(B1.ref_systems(field, fx), field.INFLUENCE_RADIUS)
		var rng := RandomNumberGenerator.new()
		rng.seed = 4242
		var r := _compare(exact.net, grid.net, B1.rays(rng, RAYS))
		_check("FIELD-EQ", _ok(r), "seed%d: %s" % [p_seed, _detail(r)])
		field.queue_free()
		wv.free()
		await process_frame
