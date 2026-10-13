extends SceneTree
# test-timeout: 20000

# Piece B22, the prototype's geometry (docs/northstar/plans/2026-10-07-visible-game-spec.md rev 10d,
# lane B, paragraph "B22"; bible E-16 S-106 R-106-01..03; prototype origin/push/galaxy-field
# 99f35887, scenes/mockups/galaxy/{galaxy_gen,galaxy_view,territory_field}.gd, approved 2026-10-07).
# TD-VG-B-14 (test-defect, assumption-changed, Architect 2026-10-11, superseded by B23 prototype scale):
# the numbers below moved from B22's 2x values to the prototype's as-run values (CIV_SCALE 0.5,
# galaxy_gen.gd:7 on the branch): R_BALL 71 -> 50, spacing 22 -> 11, INFLUENCE_RADIUS 28 -> 14,
# overview factor points 80 / 70 / 60 -> 40 / 35 / 30, qa_camera(60) -> qa_camera(30).
# Fixture: res://scenes/galaxy/galaxy_view.tscn, driven=true, snapshot_seed1_tick10.json (80 regions),
# the view's default layout seed 1 (galaxy_view.gd DEFAULT_SEED). Same fixture as test_vg_b_b18.gd.
#
# Control (green today): the view instantiates with the 80-region fixture, galaxy_gen.layout returns 80
# positions, the view's dot MultiMesh holds 80 instances, qa_camera moves the distance.
# Red until built (spec B22):
#   (1) the minimum pairwise 3D distance of the fixture seed's positions >= MIN_SPACING 11 (was 22, TD-VG-B-14)
#   (2) the Y spread (max y minus min y) exceeds 40 (a uniform ball of R_BALL 50, not a flat disc; was R_BALL 71, TD-VG-B-14;
#       measured at the fixture seed 1: 89.5, scratch run of the layout loop)
#   (3) territory_field INFLUENCE_RADIUS == 14 (was 28, TD-VG-B-14)
#   (4) a tier-1.0 dot's instance basis scale exceeds a tier-0.3 dot's at the same camera distance
#   (5) overview scale factor = instance scale / (0.6 + 1.4 * sig) of one tier-1.0 dot is 0.6 at camera
#       distance 40, 0.8 at 35, 1.0 at 30 (was 80 / 70 / 60 under the B22 controller thresholds 75 / 65;
#       TD-VG-B-14: the controller blend is now 37.5 to 32.5, so 40 is full overview, 35 the midpoint, 30 regional;
#       tolerance 0.001: a derived float compare, not a threshold)
#   (6) galaxy_gen.last_fallbacks() exists and qa_state() carries layout_fallbacks; layout(ids, seed) with no edges
#       gives 0 (every region is its own component, placed by _free_position, never a G4 fallback); the view's
#       edge-aware layout (the sim edges, spec VG-B24-layout, G4) reports the placement exhaustion count, 6 at the
#       fixture seed 1 on aba6468b (TD-VG-B-18: was 0 under the B22 random ball)
# The B22 scratch-run note (seeds 1 to 5 give 0 fallbacks, TD-VG-B-14) described the random ball and is retired;
# under B24 the no-edge count is 0 by construction and the edge-aware 6 is the built run's own figure.
#
# NEEDS A DISPLAY like test_vg_b_b18.gd: xvfb-run -a godot.real --path . --resolution 1920x1080 -s res://tests/test_vg_b_b22.gd

const SCENE_PATH := "res://scenes/galaxy/galaxy_view.tscn"
const GEN_PATH := "res://scenes/galaxy/galaxy_gen.gd"
const FIELD_PATH := "res://scenes/galaxy/territory_field.gd"
const FIXTURE_PATH := "res://tests/transport/fixtures/snapshot_seed1_tick10.json"
const FIXTURE_SEED := 1
const REGIONS := 80
const MIN_SPACING := 11.0          # TD-VG-B-14: was 22.0 (spec B22); B23 prototype as-run value galaxy_gen.gd:11 (22 x CIV_SCALE 0.5)
const Y_SPREAD_MIN := 40.0         # spec B22: "Y spread exceeds 40"
const INFLUENCE_RADIUS_WANT := 14.0   # TD-VG-B-14: was 28.0 (spec B22); B23 prototype as-run value galaxy_gen.gd:17 (28 x CIV_SCALE 0.5)
const FACTOR_TOL := 0.001          # derived float compare, brief: not a Westley threshold
# [camera distance, overview scale factor]: TD-VG-B-14 old [[80, 0.6], [70, 0.8], [60, 1.0]] (spec B22), new
# [[40, 0.6], [35, 0.8], [30, 1.0]] against the controller's 37.5 / 32.5 thresholds (legacy_zoom_disclosure_controller.gd, B23)
const FACTORS := [[40.0, 0.6], [35.0, 0.8], [30.0, 1.0]]
const TIER_SIG := {0: 0.3, 2: 1.0}   # galaxy_view.gd TIER_SIGNIFICANCE

var _pass := 0
var _fail := 0
var _msgs: Array[String] = []


func _initialize() -> void:
	await _run()
	print("\n=== B22 prototype geometry: PASS %d FAIL %d ===" % [_pass, _fail])
	print("PASS: %d  FAIL: %d" % [_pass, _fail])   # the summary line scripts/run_godot_tests.sh reads
	for m in _msgs:
		print("  - " + m)
	print("=== %s ===" % ("RED" if _fail > 0 else "GREEN"))
	quit(1 if _fail > 0 else 0)


func _check(c: bool, msg: String) -> void:
	if c:
		_pass += 1
	else:
		_fail += 1
		_msgs.append(msg)


# Dot MultiMesh instance index of every region id, matched by instance origin to get_positions().
func _dot_index(mm: MultiMesh, positions: Dictionary) -> Dictionary:
	var out := {}
	for idx in mm.instance_count:
		var origin: Vector3 = mm.get_instance_transform(idx).origin
		for id in positions:
			if origin.distance_to(positions[id]) < 0.01:
				out[id] = idx
				break
	return out


func _dot_scale(mm: MultiMesh, idx: int) -> float:
	return mm.get_instance_transform(idx).basis.x.length()


func _run() -> void:
	var f := FileAccess.open(FIXTURE_PATH, FileAccess.READ)
	var snap = JSON.parse_string(f.get_as_text()) if f != null else null
	_check(snap is Dictionary, "control: fixture readable")
	if not (snap is Dictionary):
		return
	var regions: Array = snap.get("regions", [])
	var ids: Array = []
	var tier2 := -1
	var tier0 := -1
	for r in regions:
		var i := int(r.get("i", -1))
		ids.append(i)
		if int(r.get("tier", -1)) == 2 and tier2 == -1:
			tier2 = i
		if int(r.get("tier", -1)) == 0 and tier0 == -1:
			tier0 = i
	ids.sort()

	# --- control: layout and the view on the same 80-region fixture ---
	var gen = load(GEN_PATH).new()
	var pos: Dictionary = gen.layout(ids, FIXTURE_SEED)
	_check(regions.size() == REGIONS and pos.size() == REGIONS,
		"control: fixture has %d regions and galaxy_gen.layout returns %d positions, want %d" % [regions.size(), pos.size(), REGIONS])
	_check(tier2 != -1 and tier0 != -1, "control: fixture holds a tier-2 (sig 1.0) and a tier-0 (sig 0.3) region")

	var v: Node = (load(SCENE_PATH) as PackedScene).instantiate()
	v.driven = true
	get_root().add_child(v)
	await process_frame
	await process_frame
	v.set_snapshot(snap)
	await process_frame
	await process_frame
	var st: Dictionary = v.qa_state()
	_check(int(st.get("system_count", -1)) == REGIONS, "control: view qa_state.system_count %s, want %d" % [st.get("system_count"), REGIONS])
	var points: MultiMeshInstance3D = v.get_node_or_null("World/Points")
	var mm: MultiMesh = points.multimesh if points != null else null
	_check(mm != null and mm.instance_count == REGIONS,
		"control: view World/Points MultiMesh holds %s instances, want %d" % [str(mm.instance_count) if mm != null else "none", REGIONS])
	if mm == null or tier2 == -1 or tier0 == -1:
		v.queue_free()
		return
	var vpos: Dictionary = v.get_positions()
	var dots := _dot_index(mm, vpos)
	_check(dots.has(tier2) and dots.has(tier0), "control: a dot instance sits at the position of region %d (tier 2) and %d (tier 0)" % [tier2, tier0])
	v.qa_camera(30.0, -1)   # TD-VG-B-14: was 60.0 (the same Regional regime under splits 35 / 16.25)
	await process_frame
	await process_frame
	_check(absf(float(v.qa_state().get("distance", -1.0)) - 30.0) < 0.001, "control: qa_camera(30) sets qa_state.distance to 30")
	if not (dots.has(tier2) and dots.has(tier0)):
		v.queue_free()
		return

	# --- (1) minimum pairwise 3D spacing of the fixture seed's layout ---
	var min_d := INF
	var y_lo := INF
	var y_hi := -INF
	for a in ids:
		y_lo = minf(y_lo, pos[a].y)
		y_hi = maxf(y_hi, pos[a].y)
		for b in ids:
			if int(a) < int(b):
				min_d = minf(min_d, pos[a].distance_to(pos[b]))
	_check(min_d >= MIN_SPACING, "B22 (1): minimum pairwise 3D distance %.3f for seed %d, want >= %s (MIN_SPACING in 3D)" % [min_d, FIXTURE_SEED, MIN_SPACING])
	# --- (2) Y spread ---
	_check(y_hi - y_lo > Y_SPREAD_MIN, "B22 (2): Y spread %.3f (y %.3f..%.3f) for seed %d, want > %s (uniform ball, not a flat disc)" % [y_hi - y_lo, y_lo, y_hi, FIXTURE_SEED, Y_SPREAD_MIN])
	# --- (3) INFLUENCE_RADIUS ---
	var r_infl: float = float((load(FIELD_PATH) as GDScript).get_script_constant_map().get("INFLUENCE_RADIUS", -1.0))
	_check(is_equal_approx(r_infl, INFLUENCE_RADIUS_WANT), "B22 (3): territory_field INFLUENCE_RADIUS %s, want %s" % [r_infl, INFLUENCE_RADIUS_WANT])

	# --- (4) tier-1.0 dot larger than a tier-0.3 dot at the same camera distance ---
	v.qa_camera(30.0, -1)   # TD-VG-B-14: was 60.0
	await process_frame
	await process_frame
	await process_frame
	var big := _dot_scale(mm, dots[tier2])
	var small := _dot_scale(mm, dots[tier0])
	_check(big > small, "B22 (4): tier-1.0 dot (region %d) basis scale %.4f must exceed tier-0.3 dot (region %d) %.4f at camera distance 30 (today every dot has an identity basis)" % [tier2, big, tier0, small])

	# --- (5) overview scale factor at camera distance 40, 35, 30 (TD-VG-B-14, was 80, 70, 60) ---
	var sig2: float = float(st.get("shell_renderer", {}).get("significance", {}).get(tier2, TIER_SIG[2]))
	for pair in FACTORS:
		var d: float = pair[0]
		var want: float = pair[1]
		v.qa_camera(d, -1)
		await process_frame
		await process_frame
		await process_frame
		var cam_d := float(v.qa_state().get("distance", -1.0))
		var factor := _dot_scale(mm, dots[tier2]) / (0.6 + 1.4 * sig2)
		_check(absf(cam_d - d) < 0.001 and absf(factor - want) <= FACTOR_TOL,
			"B22 (5): overview scale factor %.4f at camera distance %.1f (qa_state.distance %.1f), want %s +- %s" % [factor, d, cam_d, want, FACTOR_TOL])

	# --- (6) layout fallbacks, counted and reported ---
	var has_fn: bool = gen.has_method("last_fallbacks")
	_check(has_fn, "B22 (6): galaxy_gen.last_fallbacks() does not exist")
	if has_fn:
		gen.layout(ids, FIXTURE_SEED)
		_check(int(gen.last_fallbacks()) == 0, "B22 (6): galaxy_gen.last_fallbacks() = %s after layout(fixture ids, seed %d), want 0" % [gen.last_fallbacks(), FIXTURE_SEED])
	_check(st.has("layout_fallbacks"), "B22 (6): qa_state() has no layout_fallbacks key")
	if st.has("layout_fallbacks"):
		# TD-VG-B-18: was `== 0 ... want 0` (B22 random ball); the view's edge-aware layout (VG-B24-layout, G4) counts 6 at seed 1.
		_check(int(st["layout_fallbacks"]) == 6, "B22 (6): qa_state().layout_fallbacks = %s for the fixture seed, want 6" % st["layout_fallbacks"])
	v.queue_free()
