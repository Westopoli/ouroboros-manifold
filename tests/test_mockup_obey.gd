extends SceneTree

# Terrain-obeys mockup, pass 1 and pass 2 (docs/northstar/plans/2026-10-15-terrain-obeys-mockup-spec.md).
# Tests first: every check below is RED until scenes/mockups/landscape/obey_layer.gd exists and the
# landscape mockup root exposes obey_report().
#
#  O1 layer-loads-without-pipe   R-189-07 (the layer is part of the scene, nothing it needs is the C sim)
#  O2 twelve-shots-not-uniform   R-189-07 / R-191-10 (the walk view with the overlay is shown, never a blank frame)
#  O3 seed1-16000-obeys          R-191-10 (a choke the layout asked for is produced: measured within 100 wu
#                                of asked), R-189-07 (>= route_count small routes and >= 1 big route per
#                                strategic point), R-189-02 (no pad ring steeper than 35 degrees)
#  O4 check-budget               DRAFT-obey-budget 250 ms, asserted at 4x = 1000 ms (printed)
#  CONTROL-ROUTE a hand-built grid with the corridor walled on both sides: the test's own reference BFS
#                reports 0 routes (and finds the route when one exists), independent of the mockup
#  CONTROL-SLOPE a pad ring built at 60 degrees reads > 35 by the test's own slope arithmetic
#
#  PASS 2 (Architect 2026-10-18; pass 1 proved pads, choke and vantage are produced but routes are not):
#  P2-ROUTES   route carving is a fourth edit: on ALL THREE seeds at 16,000 and ALL THREE at 8,000,
#              pass is true, routes_small[x] >= route_count and routes_big[x] >= 1 for base_b, objective,
#              site_0, site_1 from base_a (same reference semantics as pass 1: 4-connected erosion BFS,
#              greedy separate count, one-cell margin); carved_cells > 0 and carved_routes > 0 on seed 1
#              at 16,000; every carved cell is walkable in the finished per-band data
#  P2-OFFLINE  the objective is at least DRAFT-objective-offset 1,500 wu from the base_a-base_b line
#  P2-CANVAS   on 8,000 the pad ring max slope <= 35 degrees (pass 1 read 57-62) and no two request pads
#              overlap (pairwise centre distance >= sum of radii); checked on every seed and canvas
#  P2-CHOKE    choke measured within one cell (100 wu) of asked on every seed and canvas, and the choke
#              corridor lies on at least one of the small routes (choke_on_route)
#  P2-BUDGET   check_ms < 2000 (4x DRAFT-obey-budget-2 500 ms, carving included), printed per case
#  CONTROL-CARVE-SKIPPED  a hand-built grid where carving is skipped leaves 0 routes (reference BFS);
#                         the same grid with the corridor carved has >= 1
#  CONTROL-CARVED-WALK    a 3-cell carved route with one unwalkable cell fails the every-carved-cell-
#                         walkable check; the same route fully walkable passes
#
# Pass 2 contract added to the pass-1 contract below:
#   obey_report() gains keys (all read from the root, CURRENT terrain):
#       carved_cells     int   cells whose height the route carving changed
#       carved_routes    int   routes the carving cut (>= 1 when carved_cells > 0)
#       choke_on_route   bool  true when the choke corridor lies on at least one of the small routes
#   the ObeyLayer node (direct child "ObeyLayer" of the root) gains, for the CURRENT terrain:
#       request_positions() -> Dictionary  String -> Vector2, world wu, keys "base_a","base_b",
#                                          "objective","site_0","site_1"
#       request_pads()      -> Dictionary  String -> float, pad radius wu, same five keys
#       carved_cell_list()  -> PackedInt32Array  indices gy * dim + gx of every carved cell
#   (the test reads walkability itself, as pass 1 documents below, from root._hud.get_field_map().)
#   the objective is no longer on the base line: distance from the base_a-base_b line >= 1,500 wu
#   (DRAFT-objective-offset, a named draft in the panel). The pass-1 clause "pass is true" now also
#   requires the objective offset, the pad non-overlap and the carved-cell walkability.
#
# Contract this test defines for the builder (the spec names only --shot and the panel numbers):
#   - after _ready, the landscape mockup root (landscape_mockup.tscn) has a direct child node named
#     "ObeyLayer" whose script resource_path ends in "obey_layer.gd"; the scene loads with no pipe;
#   - the root has `obey_report() -> Dictionary` describing the CURRENT terrain (canvas and seed as set
#     in the HUD, via HUD.qa_set_canvas(float) and root.qa_seed(int)), with keys:
#       pass               bool    every clause met (routes, choke width, ring slope)
#       choke_asked_wu     float   the request's choke width w
#       choke_measured_wu  float   narrowest cross-section of walkable cells along the corridor, wu
#       routes_small       Dictionary  String -> int, keys "base_b","objective","site_0","site_1"
#       routes_big         Dictionary  same keys; routes found from base A at small / big width
#       pad_ring_max_deg   float   steepest slope on any pad ring (bases, objective, sites), degrees
#       route_count        int     the seeded roll 2 + floor(u * 3)
#       check_ms           float   wall time of the check, ms
#   - canvas 16,000 and 8,000 must both be reachable through HUD.qa_set_canvas (landscape HUD's
#     CANVAS_OPTIONS today lacks 8,000 and defaults to 24,000);
#   - `--shot <dir>` (after the scene's `--`) generates seeds 1..3 on canvases 16000 then 8000, saves
#     obey_<canvas>_<seed>.png and obey_panel_<canvas>_<seed>.txt, then quits with code 0.
#
# The real data the check must use (names in scenes/mockups/landscape/, read 2026-10-15):
#   - the finished field map:  root._hud.get_field_map() -> FieldMap (hud.gd get_field_map()), after the
#     band fit, steep mask and slope finding (Pass4Terrain.analyse stores fm.p4);
#   - cell size: FieldMap.SPACING (wu per cell; static, set per canvas by spacing_for(canvas)); grid is
#     fm.dim x fm.dim, index = gy * dim + gx, world position = Vector2(gx, gy) * SPACING;
#   - per-band data: fm.p4.layer (PackedByteArray, 0 = water, 1..5 = band) from fm.p4.lo / fm.p4.step;
#   - slope data: fm.p4.tan (PackedFloat32Array, tan of steepest rise over the fm.p4_footprint = 300 wu
#     window, 0 on water), fm.p4.land (1 = dry), fm.p4.h (heights, wu);
#   - the walk mask: walkable = fm.p4.land == 1 and fm.p4.tan <= tan(35 deg) (R-189-02), or a ramp cell
#     (fm.p4.ramp_cells == 1, cut by Pass4Terrain) or a bridge cell (fm.p5_info.bridge == 1);
#     Pass5Layout.mask(fm).walk is the same mask at the 30-degree limit and may NOT be used for 35;
#   - "joined by a slope" between bands = both cells walkable under that mask (ramp cells are walkable).
# Names this test chose where the spec is silent:
#   - the spec's "within one cell" is the brief's 100 wu (the 16,000 canvas's SPACING is asserted <= 100
#     by the test only through the 100 wu bound itself);
#   - the 4x budget is 1,000 ms; near-uniform = busyness < 0.02 OR luminance stddev < 8 (the transition
#     test's two drafts; the gate's look stage has no threshold yet).
# Child Godot processes run windowed (a --headless renderer cannot save a viewport PNG).

const MOCKUP := "res://scenes/mockups/landscape/landscape_mockup.tscn"
const LAYER_SCRIPT := "obey_layer.gd"
const CANVASES := [16000, 8000]
const SEEDS := [1, 2, 3]
const POINTS := ["base_b", "objective", "site_0", "site_1"]
const DRAFT_LOOK_STDDEV := 8.0
const DRAFT_LOOK_BUSYNESS := 0.02
const CHOKE_TOL_WU := 100.0
const WALK_LIMIT_DEG := 35.0
const BUDGET_MS := 250.0
const BUDGET_FACTOR := 4.0
const SHOT_TIMEOUT_S := 60
const OBJECTIVE_OFFSET_WU := 1500.0
const BUDGET2_MS := 500.0
const PAD_NAMES := ["base_a", "base_b", "objective", "site_0", "site_1"]

var _pass_count := 0
var _fail_count := 0
var _fail_msgs: Array[String] = []


func _initialize() -> void:
	await _run_tests()
	print("\n=== Terrain-Obeys Mockup Test Results ===")
	print("PASS: %d  FAIL: %d" % [_pass_count, _fail_count])
	if _fail_count > 0:
		print("Failures:")
		for msg in _fail_msgs:
			print("  - " + msg)
		print("=== RED ===\n")
		quit(1)
	else:
		print("=== GREEN ===\n")
		quit(0)


func _assert(cond: bool, msg: String) -> void:
	if cond:
		_pass_count += 1
	else:
		_fail_count += 1
		_fail_msgs.append(msg)


func _run_tests() -> void:
	_test_controls()
	var packed = load(MOCKUP) if ResourceLoader.exists(MOCKUP) else null
	_assert(packed is PackedScene, "O1 [R-189-07] %s does not load as a PackedScene" % MOCKUP)
	_test_shots()
	if not (packed is PackedScene):
		return
	var inst: Node = packed.instantiate()
	root.add_child(inst)
	await process_frame
	await process_frame
	# O1
	var layer := inst.get_node_or_null("ObeyLayer")
	_assert(layer != null, "O1 [R-189-07] the mockup root has no child node named ObeyLayer after _ready (obey_layer.gd missing)")
	if layer != null:
		var scr: Script = layer.get_script()
		_assert(scr != null and String(scr.resource_path).ends_with(LAYER_SCRIPT),
			"O1 [R-189-07] ObeyLayer's script is %s, not %s" % [scr.resource_path if scr != null else "none", LAYER_SCRIPT])
	var has_report := inst.has_method("obey_report")
	_assert(has_report, "O3 [R-191-10] the mockup root has no obey_report() method")
	if not has_report:
		_assert(false, "O3 [R-191-10/R-189-07/R-189-02] cannot read pass, choke, routes or ring slope: no obey_report()")
		_assert(false, "O4 [DRAFT-obey-budget] cannot read check_ms: no obey_report()")
		inst.queue_free()
		return
	var hud = inst.get_node("HUD")
	hud.qa_set_canvas(16000.0)
	inst.qa_seed(1)
	await process_frame
	await process_frame
	var rep: Dictionary = inst.obey_report()
	_check_report(rep)
	await _test_pass2(inst, hud)
	inst.queue_free()


# ---------------------------------------------------------------- O3 and O4

func _check_report(rep: Dictionary) -> void:
	for k in ["pass", "choke_asked_wu", "choke_measured_wu", "routes_small", "routes_big", "pad_ring_max_deg", "route_count", "check_ms"]:
		_assert(rep.has(k), "O3 [R-191-10] obey_report() lacks key '%s'" % k)
	if not (rep.has("pass") and rep.has("choke_asked_wu") and rep.has("choke_measured_wu") and rep.has("routes_small") \
			and rep.has("routes_big") and rep.has("pad_ring_max_deg") and rep.has("route_count") and rep.has("check_ms")):
		return
	_assert(bool(rep["pass"]), "O3 [R-191-10] seed 1 at 16,000: pass is false")
	var d := absf(float(rep["choke_measured_wu"]) - float(rep["choke_asked_wu"]))
	_assert(d <= CHOKE_TOL_WU, "O3 [R-191-10] choke measured %.1f wu vs asked %.1f wu: off by %.1f (max %.0f)" % [rep["choke_measured_wu"], rep["choke_asked_wu"], d, CHOKE_TOL_WU])
	_assert(float(rep["pad_ring_max_deg"]) <= WALK_LIMIT_DEG, "O3 [R-189-02] pad ring max slope %.2f deg exceeds %.0f" % [rep["pad_ring_max_deg"], WALK_LIMIT_DEG])
	var rc := int(rep["route_count"])
	_assert(rc >= 2 and rc <= 4, "O3 [R-189-07] route_count %d not in 2..4 (2 + floor(u*3), at most DRAFT-route-max-count 4)" % rc)
	for p in POINTS:
		var s := int(rep["routes_small"].get(p, -1))
		var b := int(rep["routes_big"].get(p, -1))
		_assert(s >= rc, "O3 [R-189-07] routes_small[%s] = %d < route_count %d" % [p, s, rc])
		_assert(b >= 1, "O3 [R-189-07] routes_big[%s] = %d < 1" % [p, b])
	var ms := float(rep["check_ms"])
	print("O4 check_ms (seed 1, 16000) = %.1f (draft %.0f, asserted at %.0fx)" % [ms, BUDGET_MS, BUDGET_FACTOR])
	_assert(ms > 0.0 and ms < BUDGET_MS * BUDGET_FACTOR, "O4 [DRAFT-obey-budget] check_ms %.1f not in (0, %.0f)" % [ms, BUDGET_MS * BUDGET_FACTOR])


# ---------------------------------------------------------------- pass 2

func _test_pass2(inst: Node, hud) -> void:
	var layer := inst.get_node_or_null("ObeyLayer")
	for c in CANVASES:
		for sd in SEEDS:
			hud.qa_set_canvas(float(c))
			inst.qa_seed(sd)
			await process_frame
			await process_frame
			var tag := "seed %d at %d" % [sd, c]
			var rep: Dictionary = inst.obey_report()
			for k in ["pass", "choke_asked_wu", "choke_measured_wu", "routes_small", "routes_big", "pad_ring_max_deg", "route_count", "check_ms", "carved_cells", "carved_routes", "choke_on_route"]:
				_assert(rep.has(k), "P2 obey_report() lacks key '%s' (%s)" % [k, tag])
			if not (rep.has("pass") and rep.has("routes_small") and rep.has("routes_big") and rep.has("route_count")):
				continue
			# routes, all seeds and canvases
			_assert(bool(rep["pass"]), "P2-ROUTES [R-189-07] %s: pass is false (routes_small %s, routes_big %s, route_count %s)" % [tag, rep["routes_small"], rep["routes_big"], rep["route_count"]])
			var rc := int(rep["route_count"])
			for p in POINTS:
				var sm := int(rep["routes_small"].get(p, -1))
				var bg := int(rep["routes_big"].get(p, -1))
				_assert(sm >= rc, "P2-ROUTES [R-189-07] %s: routes_small[%s] = %d < route_count %d" % [tag, p, sm, rc])
				_assert(bg >= 1, "P2-ROUTES [R-189-07] %s: routes_big[%s] = %d < 1" % [tag, p, bg])
			# choke still a choke
			if rep.has("choke_measured_wu") and rep.has("choke_asked_wu"):
				var d := absf(float(rep["choke_measured_wu"]) - float(rep["choke_asked_wu"]))
				_assert(d <= CHOKE_TOL_WU, "P2-CHOKE [R-191-10] %s: choke measured %.1f vs asked %.1f wu, off by %.1f (max %.0f)" % [tag, rep["choke_measured_wu"], rep["choke_asked_wu"], d, CHOKE_TOL_WU])
			_assert(bool(rep.get("choke_on_route", false)), "P2-CHOKE [R-191-10] %s: choke_on_route is %s, the choke corridor is on none of the small routes" % [tag, rep.get("choke_on_route", "missing")])
			# ring slope (the 8,000 canvas is the pass-1 failure; asserted on both)
			if rep.has("pad_ring_max_deg"):
				_assert(float(rep["pad_ring_max_deg"]) <= WALK_LIMIT_DEG, "P2-CANVAS [R-189-02] %s: pad ring max slope %.2f deg exceeds %.0f" % [tag, rep["pad_ring_max_deg"], WALK_LIMIT_DEG])
			# budget
			if rep.has("check_ms"):
				var ms := float(rep["check_ms"])
				print("P2-BUDGET check_ms (%s) = %.1f (draft %.0f, asserted at %.0fx)" % [tag, ms, BUDGET2_MS, BUDGET_FACTOR])
				_assert(ms > 0.0 and ms < BUDGET2_MS * BUDGET_FACTOR, "P2-BUDGET %s: check_ms %.1f not in (0, %.0f)" % [tag, ms, BUDGET2_MS * BUDGET_FACTOR])
			# layer accessors: objective off the line, pads apart, carved cells walkable
			var has_acc: bool = layer != null and layer.has_method("request_positions") and layer.has_method("request_pads") and layer.has_method("carved_cell_list")
			_assert(has_acc, "P2 the ObeyLayer lacks request_positions()/request_pads()/carved_cell_list() (%s)" % tag)
			if has_acc:
				_check_geometry(layer.request_positions(), layer.request_pads(), tag)
				if sd == 1 and c == 16000:
					_check_carved(inst, layer, rep)
				else:
					_check_carved_walkable(inst, layer.carved_cell_list(), tag)


func _check_geometry(pos: Dictionary, pads: Dictionary, tag: String) -> void:
	for n in PAD_NAMES:
		_assert(pos.has(n) and pads.has(n), "P2 request_positions()/request_pads() lack '%s' (%s)" % [n, tag])
	if not (pos.has("base_a") and pos.has("base_b") and pos.has("objective")):
		return
	var a: Vector2 = pos["base_a"]
	var b: Vector2 = pos["base_b"]
	var o: Vector2 = pos["objective"]
	var line := (b - a).normalized()
	var off := absf((o - a).cross(line))
	_assert(off >= OBJECTIVE_OFFSET_WU, "P2-OFFLINE [R-189-07] %s: objective is %.1f wu from the base line, need >= %.0f (DRAFT-objective-offset)" % [tag, off, OBJECTIVE_OFFSET_WU])
	for i in range(PAD_NAMES.size()):
		for j in range(i + 1, PAD_NAMES.size()):
			var n1: String = PAD_NAMES[i]
			var n2: String = PAD_NAMES[j]
			if not (pos.has(n1) and pos.has(n2) and pads.has(n1) and pads.has(n2)):
				continue
			var dist: float = (pos[n1] as Vector2).distance_to(pos[n2])
			var rr: float = float(pads[n1]) + float(pads[n2])
			_assert(dist >= rr, "P2-CANVAS %s: pads %s and %s overlap (centres %.1f wu apart, radii sum %.1f)" % [tag, n1, n2, dist, rr])


func _check_carved(inst: Node, layer: Node, rep: Dictionary) -> void:
	var cc := int(rep.get("carved_cells", 0))
	var cr := int(rep.get("carved_routes", 0))
	_assert(cc > 0, "P2-ROUTES seed 1 at 16000: carved_cells = %d, the carving did not run" % cc)
	_assert(cr > 0, "P2-ROUTES seed 1 at 16000: carved_routes = %d, the carving cut no route" % cr)
	var cells: PackedInt32Array = layer.carved_cell_list()
	_assert(cells.size() == cc, "P2-ROUTES seed 1 at 16000: carved_cell_list() has %d cells, carved_cells says %d" % [cells.size(), cc])
	_check_carved_walkable(inst, cells, "seed 1 at 16000")


func _check_carved_walkable(inst: Node, cells: PackedInt32Array, tag: String) -> void:
	var fm = inst.get_node("HUD").get_field_map()
	var walk := _walk_of(fm)
	var bad := _unwalkable_in(walk, cells)
	_assert(bad.is_empty(), "P2-ROUTES %s: %d of %d carved cells are not walkable in the finished data (first: index %s)" % [tag, bad.size(), cells.size(), str(bad[0]) if not bad.is_empty() else ""])


# The walk mask as the pass-1 header documents it: dry and tan <= tan(35), or a ramp cell, or a bridge cell.
func _walk_of(fm) -> PackedByteArray:
	var p4: Dictionary = fm.p4
	var n: int = fm.dim * fm.dim
	var land: PackedByteArray = p4.land
	var tn: PackedFloat32Array = p4.tan
	var ramp: PackedByteArray = p4.ramp_cells
	var bridge: PackedByteArray = fm.p5_info.get("bridge", PackedByteArray())
	var lim := tan(deg_to_rad(WALK_LIMIT_DEG))
	var walk := PackedByteArray()
	walk.resize(n)
	for i in range(n):
		if (land[i] == 1 and tn[i] <= lim) or (ramp.size() == n and ramp[i] == 1) or (bridge.size() == n and bridge[i] == 1):
			walk[i] = 1
	return walk


func _unwalkable_in(walk: PackedByteArray, cells: PackedInt32Array) -> Array:
	var bad: Array = []
	for i in cells:
		if i < 0 or i >= walk.size() or walk[i] == 0:
			bad.append(i)
	return bad


# ---------------------------------------------------------------- O2

func _test_shots() -> void:
	var dir := OS.get_temp_dir().path_join("om_obey_shots_%d" % Time.get_ticks_usec())
	DirAccess.make_dir_recursive_absolute(dir)
	# create_process + poll, so a scene that ignores --shot and never quits is killed, not waited on forever
	var pid := OS.create_process(OS.get_executable_path(),
		["--path", ProjectSettings.globalize_path("res://"), MOCKUP, "--", "--shot", dir])
	var t0 := Time.get_ticks_msec()
	while pid > 0 and OS.is_process_running(pid) and Time.get_ticks_msec() - t0 < SHOT_TIMEOUT_S * 1000:
		OS.delay_msec(500)
	var code := 0
	if pid <= 0:
		code = -1
	elif OS.is_process_running(pid):
		OS.kill(pid)
		code = -2
	else:
		code = OS.get_process_exit_code(pid)
	_assert(code == 0, "O2 [R-189-07] the scene run with --shot %s exited %d, not 0 (-2 = still running at the %d s timeout, i.e. --shot ignored)" % [dir, code, SHOT_TIMEOUT_S])
	for c in CANVASES:
		for s in SEEDS:
			var png := "obey_%d_%d.png" % [c, s]
			var txt := "obey_panel_%d_%d.txt" % [c, s]
			var tx_ok := FileAccess.file_exists(dir.path_join(txt))
			_assert(tx_ok, "O2 [R-189-07] panel file %s was not written to the --shot dir" % txt)
			var p := dir.path_join(png)
			var exists := FileAccess.file_exists(p)
			_assert(exists, "O2 [R-191-10] shot %s was not written to the --shot dir" % png)
			if not exists:
				continue
			var img := Image.load_from_file(p)
			_assert(img != null and not img.is_empty(), "O2 shot %s is not a readable PNG" % png)
			if img == null or img.is_empty():
				continue
			var st := _frame_stats(img)
			_assert(st.busyness >= DRAFT_LOOK_BUSYNESS and st.stddev >= DRAFT_LOOK_STDDEV,
				"O2 [R-191-10] shot %s is near-uniform: busyness %.4f (min %.2f), stddev %.2f (min %.1f)" % [png, st.busyness, DRAFT_LOOK_BUSYNESS, st.stddev, DRAFT_LOOK_STDDEV])
	var flat := Image.create(64, 64, false, Image.FORMAT_RGB8)
	flat.fill(Color(0.1, 0.1, 0.1))
	var fs := _frame_stats(flat)
	_assert(fs.busyness < DRAFT_LOOK_BUSYNESS and fs.stddev < DRAFT_LOOK_STDDEV, "CONTROL-O2 a flat frame was not flagged near-uniform")
	for f in DirAccess.get_files_at(dir):
		DirAccess.remove_absolute(dir.path_join(f))
	DirAccess.remove_absolute(dir)


func _frame_stats(img: Image) -> Dictionary:
	var w := img.get_width()
	var h := img.get_height()
	var counts := {}
	var sum := 0.0
	var sumsq := 0.0
	var n := w * h
	for y in range(h):
		for x in range(w):
			var c := img.get_pixel(x, y)
			var l := int(round((c.r * 0.299 + c.g * 0.587 + c.b * 0.114) * 255.0))
			counts[l] = int(counts.get(l, 0)) + 1
			sum += l
			sumsq += float(l) * l
	var mx := 0
	for k in counts:
		mx = max(mx, int(counts[k]))
	var mean := sum / n
	return {"busyness": 1.0 - float(mx) / n, "stddev": sqrt(max(0.0, sumsq / n - mean * mean))}


# ---------------------------------------------------------------- controls (independent of the mockup)

# Reference route finder: width_cells-wide route from a to b over `walk` (Array of bool, dim x dim,
# 4-connected). A cell qualifies if every cell within radius (width_cells - 1) / 2 (Chebyshev) is
# walkable and on the grid. Returns the number of greedy separate routes, each found route plus a one-cell
# margin removed before the next search, up to max_count.
func _ref_routes(walk: Array, dim: int, a: Vector2i, b: Vector2i, width_cells: int, max_count: int) -> int:
	var rad := int(ceil(width_cells / 2.0)) - 1
	var ok: Array = []
	ok.resize(dim * dim)
	for y in range(dim):
		for x in range(dim):
			var good := true
			for oy in range(-rad, rad + 1):
				for ox in range(-rad, rad + 1):
					var nx := x + ox
					var ny := y + oy
					if nx < 0 or ny < 0 or nx >= dim or ny >= dim or not walk[ny * dim + nx]:
						good = false
			ok[y * dim + x] = good
	var found := 0
	while found < max_count:
		var path := _ref_bfs(ok, dim, a, b)
		if path.is_empty():
			break
		found += 1
		for i in path:
			var px: int = i % dim
			var py: int = i / dim
			for oy in range(-1 - rad, 2 + rad):
				for ox in range(-1 - rad, 2 + rad):
					var nx := px + ox
					var ny := py + oy
					if nx >= 0 and ny >= 0 and nx < dim and ny < dim:
						ok[ny * dim + nx] = false
	return found


func _ref_bfs(ok: Array, dim: int, a: Vector2i, b: Vector2i) -> Array:
	var s := a.y * dim + a.x
	var t := b.y * dim + b.x
	if not ok[s] or not ok[t]:
		return []
	var prev := {}
	prev[s] = -1
	var q: Array = [s]
	var head := 0
	while head < q.size():
		var i: int = q[head]
		head += 1
		if i == t:
			var path: Array = []
			var k := t
			while k != -1:
				path.append(k)
				k = prev[k]
			return path
		var x := i % dim
		var y := i / dim
		for d in [Vector2i(1, 0), Vector2i(-1, 0), Vector2i(0, 1), Vector2i(0, -1)]:
			var nx: int = x + d.x
			var ny: int = y + d.y
			if nx < 0 or ny < 0 or nx >= dim or ny >= dim:
				continue
			var j := ny * dim + nx
			if ok[j] and not prev.has(j):
				prev[j] = i
				q.append(j)
	return []


# Steepest slope in degrees between neighbouring samples of a height profile spaced `spacing` wu apart.
func _max_slope_deg(heights: Array, spacing: float) -> float:
	var m := 0.0
	for i in range(1, heights.size()):
		m = maxf(m, rad_to_deg(atan(absf(float(heights[i]) - float(heights[i - 1])) / spacing)))
	return m


func _test_controls() -> void:
	# 21 x 21 field: left room (x < 8), right room (x > 12), a corridor between at y 8..10 (3 cells wide)
	var dim := 21
	var walk: Array = []
	walk.resize(dim * dim)
	for y in range(dim):
		for x in range(dim):
			var room := x < 8 or x > 12
			var corridor := y >= 8 and y <= 10
			walk[y * dim + x] = room or corridor
	var a := Vector2i(2, 9)
	var b := Vector2i(18, 9)
	var small := _ref_routes(walk, dim, a, b, 1, 4)
	var big := _ref_routes(walk, dim, a, b, 5, 4)
	_assert(small >= 1, "CONTROL-ROUTE the reference BFS found no small route through an open 3-wide corridor (%d)" % small)
	_assert(big == 0, "CONTROL-ROUTE a 5-wide route went through a 3-wide corridor (%d routes, expected 0)" % big)
	# the corridor walled on both sides and shut: no route at any width
	var walled := walk.duplicate()
	for y in range(dim):
		for x in range(8, 13):
			walled[y * dim + x] = false
	_assert(_ref_routes(walled, dim, a, b, 1, 4) == 0, "CONTROL-ROUTE a fully walled corridor still reported routes")
	# the corridor walled on both sides (rows 7 and 11 blocked, its own cells blocked mid-way too)
	var cut := walk.duplicate()
	for y in range(8, 11):
		cut[y * dim + 10] = false
	_assert(_ref_routes(cut, dim, a, b, 1, 4) == 0, "CONTROL-ROUTE a corridor cut across its width still reported routes")
	print("CONTROL-ROUTE small=%d big=%d (expected >=1, 0), walled=0, cut=0" % [small, big])
	# pass-2 control: carving skipped. The two rooms with the wall between them left solid: 0 routes at any
	# width; the same grid with a 3-wide corridor carved through the wall: >= 1 small route, 0 big (5-wide).
	var solid: Array = []
	solid.resize(dim * dim)
	for y in range(dim):
		for x in range(dim):
			solid[y * dim + x] = x < 8 or x > 12
	var uncarved := _ref_routes(solid, dim, a, b, 1, 4)
	_assert(uncarved == 0, "CONTROL-CARVE-SKIPPED a grid with no carving reported %d routes, expected 0" % uncarved)
	var carved := solid.duplicate()
	for x in range(8, 13):
		for y in range(8, 11):
			carved[y * dim + x] = true
	var after := _ref_routes(carved, dim, a, b, 1, 4)
	_assert(after >= 1, "CONTROL-CARVE-SKIPPED the same grid with the corridor carved reported %d routes, expected >= 1" % after)
	print("CONTROL-CARVE-SKIPPED uncarved=%d carved=%d (expected 0, >=1)" % [uncarved, after])
	# pass-2 control: a 3-cell carved route with one unwalkable cell fails the every-carved-cell-walkable check
	var wm := PackedByteArray()
	wm.resize(9)
	wm.fill(1)
	var route := PackedInt32Array([3, 4, 5])
	_assert(_unwalkable_in(wm, route).is_empty(), "CONTROL-CARVED-WALK a fully walkable 3-cell route was flagged")
	wm[4] = 0
	var flagged := _unwalkable_in(wm, route)
	_assert(flagged.size() == 1 and flagged[0] == 4, "CONTROL-CARVED-WALK a 3-cell route with an unwalkable middle cell was not flagged (%s)" % str(flagged))
	print("CONTROL-CARVED-WALK flagged cells with one unwalkable: %s (expected [4])" % str(flagged))
	# slope control: a pad ring ramp built at 60 degrees (rise 173.2 wu per 100 wu) must read > 35
	var spacing := 100.0
	var ring60: Array = []
	for i in range(6):
		ring60.append(i * spacing * tan(deg_to_rad(60.0)))
	var deg60 := _max_slope_deg(ring60, spacing)
	_assert(deg60 > WALK_LIMIT_DEG, "CONTROL-SLOPE a 60 degree pad ring read %.2f, not > %.0f" % [deg60, WALK_LIMIT_DEG])
	var ring20: Array = []
	for i in range(6):
		ring20.append(i * spacing * tan(deg_to_rad(20.0)))
	var deg20 := _max_slope_deg(ring20, spacing)
	_assert(deg20 <= WALK_LIMIT_DEG, "CONTROL-SLOPE a 20 degree pad ring read %.2f, not <= %.0f" % [deg20, WALK_LIMIT_DEG])
	print("CONTROL-SLOPE 60 deg ring read %.2f, 20 deg ring read %.2f" % [deg60, deg20])
