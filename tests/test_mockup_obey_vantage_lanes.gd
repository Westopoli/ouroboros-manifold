extends SceneTree

# R5 round 1, fix 3: vantages over traffic, lanes by width, loud failures. Tests (red) first; builders never edit this file.
# Brief: docs/northstar/plans/briefs/2026-11-08-r5-round1-vantage-lanes-tests.md. Rule pins: none (prototype fix; R-189-07 is the
# floor for rule 4's two-separate-roads clause). Companion of tests/test_mockup_obey_assault.gd (not touched here).
# Run:  scripts/run_godot_tests.sh tests/test_mockup_obey_vantage_lanes.gd     (headless, no display needed)
#
# WHERE THE GENERATOR LIVES: scenes/mockups/landscape/obey_layer.gd and obey_overlay.gd, the terrain-obeys assault mode on
# branch wip/r5-obey-shots (worktree ~/Projects/om-wt/r5-obey). A checkout without them fails group A0 below and nothing else
# runs; that is red for the right reason (the generator the fix lands in is not there).
#
# Westley's words (2026-11-08, per-picture round 1, ruled.md), quoted in the groups that pin them:
#   V: "the vantage points purpose is to be a high ground looking over 'lanes' of 'traffic', and thus strategically valuable.
#       (Or they could be vantage over economic resources)."
#   R: "vantage cliff isn't even accessible at all, that should be an automatic flag for failing loudly."
#   L: "The lanes leading toward base A are very thin, which is ok but there are only two of them. Thin = more, thick = fewer, as a
#       general rule. We want to give both players lots of options and be specifically restrictive as opposed to accidentally
#       restrictive."
#   D: "it's just a dead-end, there's no reason for the player to travel there if there's not resources there"
#
# INTERFACE the builder provides (names are the contract; the panel lines are the brief's)
#   layer.draft gains (DRAFT, Westley owns every number): vantage-overlook 600, lane-budget 720, options-min 3, deadend-area 400.
#   Panel (result_text()/panel_text(), assault mode), one per line, leading spaces allowed:
#       vantage_over: <road|site_0|site_1|none>      none is a check FAIL (check name vantage_over)
#       vantage_reach <ok|FAIL>                      check name vantage_reach
#       lanes <width> -> <count>                     one line per width used (default: "lanes 180 -> 4", "lanes 600 -> 1")
#       narrowings <n> (<m> outside chokes)          check accidental_narrowing is FAIL when m > 0
#       accidental_narrowing <ok|FAIL>
#       dead_ends <n>                                report line, never a FAIL
#   The first panel line already reads "... PASS" or "... FAIL (<check names>)": a failing vantage_over / vantage_reach /
#       accidental_narrowing is in that list, so the first line carries FAIL.
#   obey_report() gains: "vantage_over" String, and bools (true = ok, like defender_centre) "vantage_reach", "accidental_narrowing";
#       "vantage_over_ok" is NOT needed: the String is "none" when the check fails. "route_count" is the derived small-road count.
#   func shot_file_name(canvas: int, seed: int) -> String   the file name --shot writes the PNG under (and the panel .txt beside it
#       with "_panel" as today): "obey_assault_16000_<seed>.png", or "obey_assault_16000_<seed>_FAIL.png" when vantage_reach is FAIL.
#       _run_shots must use it, so the control below tests the name the real shot gets.
#   overlay.vantage_ring_color() -> Color                   FAIL_COLOR when vantage_reach is FAIL, else the normal ring colour;
#       _draw must use it for the vantage ring.
#   Re-check hook the controls use (all exist today): layer._check() -> Dictionary (re-reads fm.p4.land / ramp_cells / p5_info.bridge
#       and layer.req), layer.res, layer._walk_mask(), layer._erode(walk, rad), layer._sdf(box, p), layer.overlay.
#
# FIXTURE CHOICES (none is a threshold)
#   - Road centreline cells are layer.road_paths()[i].cells (index gy * dim + gx); "within X wu of a road" is the distance from the
#     vantage to a cell centre (cell * FieldMap.SPACING).
#   - A site's pad edge is its centre distance minus its pad radius (request_pads()).
#   - The walk flood is 4-connected over layer._walk_mask() (the 35 degree limit, ramp cells and bridges) from the cell of base_a;
#     the vantage pad is reached when a flooded cell lies within vantage-radius of the vantage.
#   - A narrowing is a road centreline cell outside every pad whose neighbourhood is not walkable to the road's own erosion radius
#     (layer._erode, radius max(ceil(width / 2 / spacing) - 1, 0), the layer's convention: small roads at route-small-width,
#     big at route-big-width). "Inside a choke" is inside the choke's wall block (corridor plus both wall spans).

const MOCKUP := "res://scenes/mockups/landscape/landscape_mockup.tscn"
const LAYER_SCRIPT := "obey_layer.gd"
const SEEDS := [1, 2, 3, 4, 5]
const CANVAS := 16000.0
const POINTS := ["base_b", "objective", "site_0", "site_1"]
const OVER := ["road", "site_0", "site_1"]
const DEFAULTS := {
	"vantage-overlook": 600.0, "lane-budget": 720.0, "options-min": 3.0, "deadend-area": 400.0,
	"route-small-width": 180.0, "route-big-width": 600.0, "route-max-count": 4.0, "vantage-radius": 250.0,
}
const FAIL_RING := Color(1.0, 0.1, 0.1, 1.0)  # obey_overlay.gd FAIL_COLOR

var _pass_count := 0
var _fail_count := 0
var _fail_msgs: Array[String] = []


func _initialize() -> void:
	await _run_tests()
	print("\n=== Obey Vantage / Lanes / Loud-Failure Test Results ===")
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


func _dv(layer: Node, name: String) -> float:
	if layer != null and layer.get("draft") is Dictionary and (layer.get("draft") as Dictionary).has(name):
		return float((layer.get("draft") as Dictionary)[name])
	return float(DEFAULTS[name])


func _run_tests() -> void:
	var packed = load(MOCKUP) if ResourceLoader.exists(MOCKUP) else null
	_assert(packed is PackedScene, "A0 R5r1-fix3: %s does not load as a PackedScene" % MOCKUP)
	if not (packed is PackedScene):
		return
	var inst: Node = packed.instantiate()
	root.add_child(inst)
	await process_frame
	await process_frame
	var layer := inst.get_node_or_null("ObeyLayer")
	_assert(layer != null and String(layer.get_script().resource_path).ends_with(LAYER_SCRIPT), "A0 R5r1-fix3: the mockup root has no ObeyLayer driven by obey_layer.gd (the generator lives on wip/r5-obey-shots)")
	if layer == null:
		return
	var hud = inst.get_node("HUD")
	hud.qa_set_canvas(CANVAS)
	inst.qa_seed(1)
	await process_frame
	await process_frame
	var iface := layer.has_method("set_mode") and layer.has_method("road_paths") and layer.has_method("vantage_position")
	_assert(iface, "A0 R5r1-fix3: ObeyLayer lacks the assault interface (set_mode, road_paths, vantage_position)")
	if not iface:
		inst.queue_free()
		return
	for d in ["vantage-overlook", "lane-budget", "options-min", "deadend-area"]:
		var dr: Dictionary = layer.draft
		_assert(dr.has(d), "A1 R5r1-fix3: DRAFTS lacks '%s' (default %s)" % [d, str(DEFAULTS[d])])
		if dr.has(d):
			_assert(is_equal_approx(float(dr[d]), float(DEFAULTS[d])), "A1 R5r1-fix3: draft %s defaults to %s, brief says %s" % [d, str(dr[d]), str(DEFAULTS[d])])
	_assert(layer.has_method("shot_file_name"), "A1 R5r1-fix3 (R): ObeyLayer lacks shot_file_name(canvas, seed) (INTERFACE block)")
	_assert(layer.overlay != null and layer.overlay.has_method("vantage_ring_color"), "A1 R5r1-fix3 (R): obey_overlay.gd lacks vantage_ring_color() (INTERFACE block)")
	layer.set_mode("assault")
	await process_frame
	await process_frame
	var texts := {}
	for sd in SEEDS:
		inst.qa_seed(sd)
		await process_frame
		await process_frame
		var rep: Dictionary = inst.obey_report()
		_test_seed(inst, layer, rep, sd)
		texts[sd] = _stable(layer.panel_text())
	# the controls run on the last seed's field (they mutate that field's masks and re-run the check; nothing else reads it after)
	_test_controls(inst, layer)
	# lanes follow width: change the small width, regenerate, read the derived count
	for pair in [[360.0, 2], [600.0, 1], [120.0, 4]]:
		await _test_lane_variation(inst, layer, pair[0], pair[1])
	layer.draft["route-small-width"] = DEFAULTS["route-small-width"]
	# determinism: seed 1 again after the others, same text
	inst.qa_seed(1)
	await process_frame
	await process_frame
	inst.obey_report()
	var again := _stable(layer.panel_text())
	_assert(again == texts[1], "A9 R5r1-fix3: seed 1 panel text differs between two runs\n--- first ---\n%s\n--- second ---\n%s" % [texts[1], again])
	inst.queue_free()


# ---------------------------------------------------------------- per seed

func _test_seed(inst: Node, layer: Node, rep: Dictionary, sd: int) -> void:
	var tag := "seed %d at 16000" % sd
	var fm: FieldMap = inst.get_node("HUD").get_field_map()
	var dim := fm.dim
	var s := FieldMap.SPACING
	var text: String = layer.panel_text()
	var roads: Array = layer.road_paths()
	var pos: Dictionary = layer.request_positions()
	var pads: Dictionary = layer.request_pads()
	var v: Vector2 = layer.vantage_position()

	# ---- 1. vantage overlooks traffic (V)
	var overlook := _dv(layer, "vantage-overlook")
	var d_road := _road_distance(v, roads, dim, s)
	var d_s0: float = v.distance_to(pos["site_0"]) - float(pads["site_0"])
	var d_s1: float = v.distance_to(pos["site_1"]) - float(pads["site_1"])
	var oracle_over := d_road <= overlook or d_s0 <= overlook or d_s1 <= overlook
	var over := _panel_value(text, "vantage_over:")
	print("R5r1 %s vantage_over panel '%s'  road %.0f  site_0 edge %.0f  site_1 edge %.0f  (overlook %.0f)" % [tag, over, d_road, d_s0, d_s1, overlook])
	_assert(OVER.has(over), "V1 R5r1-fix3 (Westley: \"the vantage points purpose is to be a high ground looking over 'lanes' of 'traffic'\") %s: panel 'vantage_over: ...' is '%s', not road|site_0|site_1 (none = FAIL)" % [tag, over])
	_assert(oracle_over, "V1 R5r1-fix3 %s: the vantage is %.0f wu from the nearest road cell and %.0f / %.0f from the site pad edges; none is within vantage-overlook %.0f" % [tag, d_road, d_s0, d_s1, overlook])
	if over == "road":
		_assert(d_road <= overlook, "V1 R5r1-fix3 %s: panel says vantage_over road but the nearest road cell is %.0f wu away, vantage-overlook %.0f" % [tag, d_road, overlook])
	elif over == "site_0":
		_assert(d_s0 <= overlook, "V1 R5r1-fix3 %s: panel says site_0 but its pad edge is %.0f wu away, vantage-overlook %.0f" % [tag, d_s0, overlook])
	elif over == "site_1":
		_assert(d_s1 <= overlook, "V1 R5r1-fix3 %s: panel says site_1 but its pad edge is %.0f wu away, vantage-overlook %.0f" % [tag, d_s1, overlook])
	_assert(str(rep.get("vantage_over", "<missing>")) == over, "V1 R5r1-fix3 %s: obey_report()['vantage_over'] is '%s', panel says '%s'" % [tag, str(rep.get("vantage_over", "<missing>")), over])
	_assert(not _first_line(text).contains("vantage_over"), "V1 R5r1-fix3 %s: the check vantage_over FAILs on a real seed (first line: %s)" % [tag, _first_line(text)])

	# ---- 2. vantage reachable, else loud (R)
	var reached := _flood_reaches(layer._walk_mask(), fm, pos["base_a"], v, _dv(layer, "vantage-radius"))
	_assert(reached, "R1 R5r1-fix3 (Westley: \"vantage cliff isn't even accessible at all, that should be an automatic flag for failing loudly\") %s: the walk flood from base_a at 35 deg does not reach the vantage pad" % tag)
	var word := _panel_word(text, "vantage_reach")
	_assert(word == "ok" or word == "FAIL", "R1 R5r1-fix3 %s: the panel has no 'vantage_reach ok|FAIL' line" % tag)
	_assert((word == "ok") == reached, "R1 R5r1-fix3 %s: panel says vantage_reach %s, the flood says reached=%s" % [tag, word, str(reached)])
	_assert(rep.has("vantage_reach") and bool(rep["vantage_reach"]) == reached, "R1 R5r1-fix3 %s: obey_report()['vantage_reach'] is %s, expected %s" % [tag, str(rep.get("vantage_reach", "<missing>")), str(reached)])
	if layer.has_method("shot_file_name"):
		var want := "obey_assault_16000_%d.png" % sd
		var got: String = layer.shot_file_name(16000, sd)
		_assert(got == want if reached else got.ends_with("_FAIL.png"), "R1 R5r1-fix3 %s: shot_file_name is '%s', expected '%s' when the vantage is reachable" % [tag, got, want])
	if layer.overlay != null and layer.overlay.has_method("vantage_ring_color"):
		var col: Color = layer.overlay.vantage_ring_color()
		_assert((col != FAIL_RING) == reached, "R1 R5r1-fix3 %s: vantage ring colour %s with reachable=%s" % [tag, str(col), str(reached)])

	# ---- 3. lane count follows width (L)
	var lane_budget := _dv(layer, "lane-budget")
	var maxc := int(_dv(layer, "route-max-count"))
	var w_small := _dv(layer, "route-small-width")
	var w_big := _dv(layer, "route-big-width")
	var want_small := clampi(roundi(lane_budget / w_small), 1, maxc)
	var want_big := clampi(roundi(lane_budget / w_big), 1, maxc)
	_assert(int(rep.get("route_count", -1)) == want_small, "L1 R5r1-fix3 (Westley: \"Thin = more, thick = fewer\") %s: route_count is %s, derived clamp(round(%.0f / %.0f), 1, %d) = %d (it was a free 2..4 roll)" % [tag, str(rep.get("route_count", "<missing>")), lane_budget, w_small, maxc, want_small])
	var counts := {}
	for r in roads:
		var k := "%s/%s" % [r.target, r.kind]
		counts[k] = int(counts.get(k, 0)) + 1
	for n in POINTS:
		_assert(int(counts.get(n + "/small", 0)) == want_small, "L1 R5r1-fix3 %s: %d small roads to %s, expected %d (lane-budget %.0f / width %.0f)" % [tag, int(counts.get(n + "/small", 0)), n, want_small, lane_budget, w_small])
		_assert(int(counts.get(n + "/big", 0)) == want_big, "L1 R5r1-fix3 %s: %d big roads to %s, expected %d (lane-budget %.0f / width %.0f)" % [tag, int(counts.get(n + "/big", 0)), n, want_big, lane_budget, w_big])
	var lanes := _panel_lanes(text)
	_assert(lanes.get(int(w_small), -1) == want_small, "L2 R5r1-fix3 %s: panel lacks 'lanes %d -> %d' (has %s)" % [tag, int(w_small), want_small, str(lanes)])
	_assert(lanes.get(int(w_big), -1) == want_big, "L2 R5r1-fix3 %s: panel lacks 'lanes %d -> %d' (has %s)" % [tag, int(w_big), want_big, str(lanes)])
	var to_objective := roads.filter(func(r): return r.target == "objective").size()
	_assert(to_objective >= int(_dv(layer, "options-min")), "L3 R5r1-fix3 (Westley: \"give both players lots of options\") %s: %d roads reach the objective, options-min %d" % [tag, to_objective, int(_dv(layer, "options-min"))])

	# ---- 4. restriction is named, never accidental (L)
	for n in POINTS:
		var mine: Array = roads.filter(func(r): return r.target == n)
		_assert(_has_disjoint_pair(mine, pos["base_a"], float(pads["base_a"]), pos[n], float(pads[n]), dim, s), "N1 [R-189-07] R5r1-fix3 %s: no two carved roads from base_a to %s share no cell outside the pads" % [tag, n])
	var nar := _panel_narrowings(text)
	print("R5r1 %s narrowings panel %s" % [tag, str(nar)])
	_assert(not nar.is_empty(), "N2 R5r1-fix3 (Westley: \"specifically restrictive as opposed to accidentally restrictive\") %s: the panel has no 'narrowings <n> (<m> outside chokes)' line" % tag)
	var nword := _panel_word(text, "accidental_narrowing")
	_assert(nword == "ok" or nword == "FAIL", "N2 R5r1-fix3 %s: the panel has no 'accidental_narrowing ok|FAIL' line" % tag)
	if not nar.is_empty():
		_assert((nword == "FAIL") == (nar[1] > 0), "N2 R5r1-fix3 %s: panel says accidental_narrowing %s with %d narrowings outside chokes" % [tag, nword, nar[1]])
		_assert(nar[1] == 0, "N2 R5r1-fix3 %s: %d narrowings (of %d) lie outside the chokes' wall spans" % [tag, nar[1], nar[0]])
	_assert(rep.has("accidental_narrowing") and bool(rep["accidental_narrowing"]) == (nword == "ok"), "N2 R5r1-fix3 %s: obey_report()['accidental_narrowing'] is %s, panel says %s" % [tag, str(rep.get("accidental_narrowing", "<missing>")), nword])
	var oracle := _narrowings(layer, fm, roads)
	print("R5r1 %s narrowings oracle %d total, %d outside the choke wall block" % [tag, oracle[0], oracle[1]])
	_assert(oracle[1] == 0, "N3 R5r1-fix3 %s: %d road cells (of %d narrow ones) are narrower than their road's own width outside the choke wall block, first at %s" % [tag, oracle[1], oracle[0], str(oracle[2])])

	# ---- 5. dead ends are flagged, never a FAIL (D)
	var dead := _panel_int(text, "dead_ends")
	_assert(dead >= 0, "D1 R5r1-fix3 (Westley: \"it's just a dead-end\") %s: the panel has no 'dead_ends <n>' line" % tag)
	_assert(not _first_line(text).contains("dead_end"), "D1 R5r1-fix3 %s: dead_ends is a report line, not a FAIL; first line: %s" % [tag, _first_line(text)])


# ---------------------------------------------------------------- positive controls (rules 1, 2 and 4)

func _test_controls(inst: Node, layer: Node) -> void:
	var fm: FieldMap = inst.get_node("HUD").get_field_map()
	var dim := fm.dim
	var s := FieldMap.SPACING
	var sd: int = inst.get_node("HUD").get_seed()
	var roads: Array = layer.road_paths()
	var pos: Dictionary = layer.request_positions()
	var v0: Vector2 = layer.vantage_position()
	var req: Dictionary = layer.req

	# CONTROL-NARROW first: it must not disturb the reach control, so it runs on the unmodified field, then is undone by re-reading p4.
	var saved := _save_masks(fm)
	var pick := _pick_neck(layer, fm, roads)
	_assert(not pick.is_empty(), "C0 R5r1-fix3 CONTROL-NARROW: no big-road cell outside pads and chokes to close (seed %d); the control cannot run" % sd)
	if not pick.is_empty():
		_block(fm, pick.blocked)
		layer.res = layer._check()
		var oracle := _narrowings(layer, fm, roads)
		_assert(oracle[1] >= 1, "C1 R5r1-fix3 CONTROL-NARROW: after closing %d cells beside road cell %d the oracle finds %d outside narrowings, expected >= 1 (control is vacuous)" % [pick.blocked.size(), pick.cell, oracle[1]])
		var text: String = layer.panel_text()
		var nar := _panel_narrowings(text)
		print("R5r1 CONTROL-NARROW panel %s  oracle %d / %d" % [str(nar), oracle[0], oracle[1]])
		_assert(not nar.is_empty() and nar[1] >= 1, "C1 R5r1-fix3 CONTROL-NARROW: the panel says narrowings %s, expected >= 1 outside chokes" % str(nar))
		_assert(_panel_word(text, "accidental_narrowing") == "FAIL", "C1 R5r1-fix3 CONTROL-NARROW: accidental_narrowing reads '%s', expected FAIL" % _panel_word(text, "accidental_narrowing"))
		_assert(_first_line(text).contains("FAIL") and _first_line(text).contains("accidental_narrowing"), "C1 R5r1-fix3 CONTROL-NARROW: first panel line lacks FAIL / accidental_narrowing: %s" % _first_line(text))
		_assert(not bool(layer.res.report.get("accidental_narrowing", true)), "C1 R5r1-fix3 CONTROL-NARROW: obey_report()['accidental_narrowing'] stays true")
	_restore_masks(fm, saved)

	# CONTROL-REACH (Westley: "vantage cliff isn't even accessible at all, that should be an automatic flag for failing loudly"):
	# an unwalkable annulus round the vantage pad, so the flood cannot get up. All four signs must show.
	var vr := _dv(layer, "vantage-radius")
	var cut: Array = []
	for gy in range(dim):
		for gx in range(dim):
			var d := (Vector2(gx, gy) * s).distance_to(v0)
			if d > vr + 200.0 and d <= vr + 700.0:
				cut.append(gy * dim + gx)
	_block(fm, cut)
	var reached := _flood_reaches(layer._walk_mask(), fm, pos["base_a"], v0, vr)
	_assert(not reached, "C2 R5r1-fix3 CONTROL-REACH: the annulus did not cut the vantage off (the control is vacuous)")
	layer.res = layer._check()
	layer.overlay.queue_redraw()
	var text2: String = layer.panel_text()
	_assert(_panel_word(text2, "vantage_reach") == "FAIL", "C2 R5r1-fix3 CONTROL-REACH sign 1/4: panel vantage_reach reads '%s', expected FAIL" % _panel_word(text2, "vantage_reach"))
	_assert(not bool(layer.res.report.get("vantage_reach", true)), "C2 R5r1-fix3 CONTROL-REACH sign 1/4: obey_report()['vantage_reach'] is not false")
	_assert(_first_line(text2).contains("FAIL") and _first_line(text2).contains("vantage_reach"), "C2 R5r1-fix3 CONTROL-REACH sign 2/4: first panel line lacks FAIL / vantage_reach: %s" % _first_line(text2))
	if layer.overlay.has_method("vantage_ring_color"):
		_assert(layer.overlay.vantage_ring_color() == FAIL_RING, "C2 R5r1-fix3 CONTROL-REACH sign 3/4: vantage ring colour is %s, expected FAIL_COLOR" % str(layer.overlay.vantage_ring_color()))
	else:
		_assert(false, "C2 R5r1-fix3 CONTROL-REACH sign 3/4: overlay has no vantage_ring_color()")
	if layer.has_method("shot_file_name"):
		_assert(layer.shot_file_name(16000, sd) == "obey_assault_16000_%d_FAIL.png" % sd, "C2 R5r1-fix3 CONTROL-REACH sign 4/4: shot_file_name is '%s', expected obey_assault_16000_%d_FAIL.png" % [layer.shot_file_name(16000, sd), sd])
	else:
		_assert(false, "C2 R5r1-fix3 CONTROL-REACH sign 4/4: layer has no shot_file_name()")
	_restore_masks(fm, saved)

	# CONTROL-OVER: the vantage moved to the canvas corner farthest from every road and site reads vantage_over none, a check FAIL.
	var best := Vector2.ZERO
	var best_d := -1.0
	for corner in [Vector2(400, 400), Vector2(CANVAS - 400, 400), Vector2(400, CANVAS - 400), Vector2(CANVAS - 400, CANVAS - 400)]:
		var dd := _road_distance(corner, roads, dim, s)
		for n in ["site_0", "site_1"]:
			dd = minf(dd, corner.distance_to(pos[n]) - float(layer.request_pads()[n]))
		if dd > best_d:
			best_d = dd
			best = corner
	_assert(best_d > _dv(layer, "vantage-overlook"), "C3 R5r1-fix3 CONTROL-OVER: no canvas corner is farther than vantage-overlook from every road and site (best %.0f); the control is vacuous" % best_d)
	req["vantage"] = best
	layer.res = layer._check()
	var text3: String = layer.panel_text()
	_assert(_panel_value(text3, "vantage_over:") == "none", "C3 R5r1-fix3 CONTROL-OVER: panel reads 'vantage_over: %s' for a vantage %.0f wu from traffic, expected none" % [_panel_value(text3, "vantage_over:"), best_d])
	_assert(_first_line(text3).contains("FAIL") and _first_line(text3).contains("vantage_over"), "C3 R5r1-fix3 CONTROL-OVER: first panel line lacks FAIL / vantage_over: %s" % _first_line(text3))
	req["vantage"] = v0


func _test_lane_variation(inst: Node, layer: Node, width: float, want: int) -> void:
	layer.draft["route-small-width"] = width
	inst.qa_seed(1)
	await process_frame
	await process_frame
	var rep: Dictionary = inst.obey_report()
	var text: String = layer.panel_text()
	_assert(int(rep.get("route_count", -1)) == want, "L4 R5r1-fix3 (Thin = more, thick = fewer): route-small-width %.0f gives route_count %s, expected %d" % [width, str(rep.get("route_count", "<missing>")), want])
	var lanes := _panel_lanes(text)
	_assert(lanes.get(int(width), -1) == want, "L4 R5r1-fix3: route-small-width %.0f: panel lacks 'lanes %d -> %d' (has %s)" % [width, int(width), want, str(lanes)])
	var n_small: int = layer.road_paths().filter(func(r): return r.target == "base_b" and r.kind == "small").size()
	_assert(n_small == want, "L4 R5r1-fix3: route-small-width %.0f carves %d small roads to base_b, expected %d" % [width, n_small, want])


# ---------------------------------------------------------------- measures

func _road_distance(p: Vector2, roads: Array, dim: int, s: float) -> float:
	var best := INF
	for r in roads:
		for i in (r.cells as PackedInt32Array):
			best = minf(best, p.distance_to(Vector2(i % dim, i / dim) * s))
	return best


# 4-connected flood over `walk` from the cell of `start`; true when a flooded cell is within `radius` wu of `target`.
func _flood_reaches(walk: PackedByteArray, fm: FieldMap, start: Vector2, target: Vector2, radius: float) -> bool:
	var dim := fm.dim
	var s := FieldMap.SPACING
	var sx := clampi(int(round(start.x / s)), 0, dim - 1)
	var sy := clampi(int(round(start.y / s)), 0, dim - 1)
	var seen := PackedByteArray()
	seen.resize(dim * dim)
	var stack := PackedInt32Array([sy * dim + sx])
	seen[sy * dim + sx] = 1
	while not stack.is_empty():
		var i: int = stack[stack.size() - 1]
		stack.remove_at(stack.size() - 1)
		var x := i % dim
		var y := i / dim
		if (Vector2(x, y) * s).distance_to(target) <= radius:
			return true
		for o in [Vector2i(1, 0), Vector2i(-1, 0), Vector2i(0, 1), Vector2i(0, -1)]:
			var nx: int = x + o.x
			var ny: int = y + o.y
			if nx < 0 or ny < 0 or nx >= dim or ny >= dim:
				continue
			var j: int = ny * dim + nx
			if seen[j] == 0 and walk[j] == 1:
				seen[j] = 1
				stack.append(j)
	return false


func _in_pad(i: int, dim: int, s: float, pos: Vector2, r: float) -> bool:
	return (Vector2(i % dim, i / dim) * s).distance_to(pos) <= r


# True when two roads in `mine` have no cell in common outside the pad of base_a and the pad of the target.
func _has_disjoint_pair(mine: Array, a_pos: Vector2, a_r: float, b_pos: Vector2, b_r: float, dim: int, s: float) -> bool:
	var sets: Array = []
	for r in mine:
		var d := {}
		for i in (r.cells as PackedInt32Array):
			if not _in_pad(i, dim, s, a_pos, a_r) and not _in_pad(i, dim, s, b_pos, b_r):
				d[i] = true
		sets.append(d)
	for i in range(sets.size()):
		for j in range(i + 1, sets.size()):
			var shared := false
			for k in sets[i]:
				if sets[j].has(k):
					shared = true
					break
			if not shared:
				return true
	return false


# Narrow road centreline cells: [total, outside the choke wall block, first outside cell (Vector2i)].
func _narrowings(layer: Node, fm: FieldMap, roads: Array) -> Array:
	var dim := fm.dim
	var w := dim + 2
	var s := FieldMap.SPACING
	var walk: PackedByteArray = layer._walk_mask()
	var req: Dictionary = layer.req
	var block := {"pos": req.choke, "axis": req.dir, "half": Vector2(float(req.choke_len) * 0.5, float(req.choke_w) * 0.5 + float(req.span))}
	var eroded := {}
	var total := 0
	var outside := 0
	var first := Vector2i(-1, -1)
	for r in roads:
		var width := _dv(layer, "route-small-width") if r.kind == "small" else _dv(layer, "route-big-width")
		var rad := maxi(ceili(width * 0.5 / s) - 1, 0)
		if not eroded.has(rad):
			eroded[rad] = layer._erode(walk, rad)
		var ok: PackedByteArray = eroded[rad]
		for i in (r.cells as PackedInt32Array):
			var in_pad := false
			for p in req.pads:
				in_pad = in_pad or _in_pad(i, dim, s, p.pos, p.r)
			if in_pad:
				continue
			if ok[(i / dim + 1) * w + i % dim + 1] == 1:
				continue
			total += 1
			if float(layer._sdf(block, Vector2(i % dim, i / dim) * s)) > 0.0:
				outside += 1
				if first.x < 0:
					first = Vector2i(i % dim, i / dim)
	return [total, outside, first]


# A big-road cell near the middle of its road, outside every pad and 3 cells clear of the choke wall block; the 3x3 neighbours
# that are not themselves carved cells are listed to be closed. {} when none.
func _pick_neck(layer: Node, fm: FieldMap, roads: Array) -> Dictionary:
	var dim := fm.dim
	var s := FieldMap.SPACING
	var req: Dictionary = layer.req
	var block := {"pos": req.choke, "axis": req.dir, "half": Vector2(float(req.choke_len) * 0.5, float(req.choke_w) * 0.5 + float(req.span))}
	var road_cells := {}
	for r in roads:
		for i in (r.cells as PackedInt32Array):
			road_cells[i] = true
	for r in roads:
		if r.kind != "big":
			continue
		var cells: PackedInt32Array = r.cells
		var mid := cells.size() / 2
		for off in range(0, cells.size() / 2):
			for sign in [1, -1]:
				var k: int = mid + sign * off
				if k < 3 or k >= cells.size() - 3:
					continue
				var i: int = cells[k]
				var p := Vector2(i % dim, i / dim) * s
				var bad := float(layer._sdf(block, p)) < 3.0 * s
				for pd in req.pads:
					bad = bad or p.distance_to(pd.pos) <= pd.r + 3.0 * s
				if bad:
					continue
				var blocked: Array = []
				for oy in range(-1, 2):
					for ox in range(-1, 2):
						var nx: int = i % dim + ox
						var ny: int = i / dim + oy
						var j: int = ny * dim + nx
						if (ox != 0 or oy != 0) and nx >= 0 and ny >= 0 and nx < dim and ny < dim and not road_cells.has(j):
							blocked.append(j)
				if not blocked.is_empty():
					return {"cell": i, "blocked": blocked}
	return {}


# Close cells for the walk mask: land, ramp cells and bridge all off (the mask is land & slope, or ramp, or bridge).
func _block(fm: FieldMap, cells: Array) -> void:
	var land: PackedByteArray = fm.p4.land
	var ramp: PackedByteArray = fm.p4.ramp_cells
	var bridge: PackedByteArray = fm.p5_info.get("bridge", PackedByteArray())
	for i in cells:
		land[i] = 0
		if ramp.size() == land.size():
			ramp[i] = 0
		if bridge.size() == land.size():
			bridge[i] = 0
	fm.p4["land"] = land
	fm.p4["ramp_cells"] = ramp
	if bridge.size() == land.size():
		fm.p5_info["bridge"] = bridge


func _save_masks(fm: FieldMap) -> Dictionary:
	return {"land": (fm.p4.land as PackedByteArray).duplicate(), "ramp": (fm.p4.ramp_cells as PackedByteArray).duplicate(), "bridge": (fm.p5_info.get("bridge", PackedByteArray()) as PackedByteArray).duplicate()}


func _restore_masks(fm: FieldMap, saved: Dictionary) -> void:
	fm.p4["land"] = saved.land
	fm.p4["ramp_cells"] = saved.ramp
	if (saved.bridge as PackedByteArray).size() > 0:
		fm.p5_info["bridge"] = saved.bridge


# ---------------------------------------------------------------- panel helpers

func _first_line(text: String) -> String:
	return text.split("\n")[0]


func _panel_word(text: String, name: String) -> String:
	for line in text.split("\n"):
		var parts := line.strip_edges().split(" ", false)
		if parts.size() >= 2 and parts[0] == name:
			return parts[1]
	return ""


func _panel_value(text: String, label: String) -> String:
	for line in text.split("\n"):
		var t := line.strip_edges()
		if t.begins_with(label):
			return t.substr(label.length()).strip_edges()
	return ""


# "name <n>" -> n, -1 when absent.
func _panel_int(text: String, name: String) -> int:
	var w := _panel_word(text, name)
	return int(w) if w.is_valid_int() else -1


# {width: count} from every "lanes <width> -> <count>" line.
func _panel_lanes(text: String) -> Dictionary:
	var out := {}
	for line in text.split("\n"):
		var parts := line.strip_edges().split(" ", false)
		if parts.size() >= 4 and parts[0] == "lanes" and parts[2] == "->" and parts[1].is_valid_int() and parts[3].is_valid_int():
			out[int(parts[1])] = int(parts[3])
	return out


# [n, n_outside_choke] from "narrowings <n> (<m> outside chokes)", [] when absent.
func _panel_narrowings(text: String) -> Array:
	for line in text.split("\n"):
		var parts := line.strip_edges().split(" ", false)
		if parts.size() >= 3 and parts[0] == "narrowings" and parts[1].is_valid_int() and parts[2].begins_with("(") and parts[2].substr(1).is_valid_int():
			return [int(parts[1]), int(parts[2].substr(1))]
	return []


func _stable(text: String) -> String:
	var keep: Array = []
	for line in text.strip_edges().split("\n"):
		if not line.contains(" ms"):
			keep.append(line)
	return "\n".join(keep)
