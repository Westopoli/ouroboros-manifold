extends "res://tests/support/vg_c_case.gd"
# Rule pins: R-001-06@9f9051

# VG-C-land-marks (docs/northstar/plans/2026-10-07-visible-game-spec.md, paragraph "VG-C-land-marks"; Tests first).
# Proves S-001 R-001-06 (the ground view reads the layers: one walkable place per cell on land) through two Westley rulings
# of 2026-10-22: DEC-S001-no-layer-ring-land (the per-unit layer ring is not drawn in the land era; it stays in space) and
# FINDING-s001-marks-through-terrain (a unit behind terrain has no 2D mark drawn through the ridge).
#
# Westley 2026-10-22, quoted word for word by the spec paragraph:
#   "Why are there layer indicators on the land era? ... Space era is the only one that needs the circular indicators."
#   "a super bunched up group of forces in the backdrop that appear to be inside the land"
# The spec paragraph's [W] tag for the first quote needs the line [ASSERT tests/test_vg_c_land_marks.gd::test_ring_only_in_space]
# (the provenance lint finds the quote's key clause, "space era is the only one that needs the circular indicators", in the
# message of that function's _check line below).
#
# Interfaces this test pins, all named by the paragraph (DRAFT-occlusion-slack 20 wu, DRAFT-occlusion-recompute):
#   UnitVisuals.layer_rings_enabled: bool, set once in _ready to (EraConfig.kind() != "ground"), true when /root/EraConfig is absent.
#   Ground3D host: occluded_ids() -> Dictionary (id -> true); qa_state()["ground3d"]["occluded_ids"] = sorted ints.
#   tactical_view qa_state()["marks_visible"] = {"<id>": {"body": bool, "ring": bool}}; occluded units' UnitVisuals node.visible = false.
#
# UNSTATED INTERFACE CHOICES (the paragraph is silent; a builder may need to reconcile, nothing else is assumed):
#  (1) RIDGE ORIENTATION. The paragraph says "a ridge of 400 wu height along column 4". Taken as heights[j * 8 + 4] (constant
#      x, running along y) NO unit can be occluded: probed on main, the rig default camera sits at (920, 3000, 3437.3), looks
#      along -y, and every pick hit equals its unit's point. The ridge here runs along ROWS 3 and 4 (heights[j * 8 + i], constant
#      y, crest from y = 350 to 450, across the view axis); units "behind" it have y < 450. The paragraph needs the word "row" or
#      "across the camera's view".
#      CREST WIDTH (Architect ruling (c), 2026-10-23): rows 3 and 4 both carry the 400 wu height, so the crest is a plateau
#      from y = 350 to y = 450, 100 wu wide (cells are 100 wu) = 2 x the 50 wu GroundPick march step: the test does not
#      depend on the thin-crest fix (FINDING-groundpick-march-skips-crest). A one-row ridge was a point peak. The plateau
#      is widened toward the back, so the 8 wu control (y = 442) now sits ON the plateau, 8 wu behind its camera-side
#      edge (y = 450): measured gap -0.004 wu (the 17.6 wu of the one-row fixture came from the point peak). Widening toward
#      the camera instead (rows 4 and 5) raised the 442 gap to 48.8 wu, past the slack, so it was not used.
#  (2) "occluded_ids" in qa_state sits inside the "ground3d" block (like slope_view and units3d), which tactical_view forwards.
#  (3) Ids in marks_visible are decimal strings, as units_px keys are.
#  (4) CAMERA-CHANGE RECOMPUTE (Architect ruling 2026-10-23, no rig hooks, camera_rig_3d.gd unedited): Ground3DHost recomputes
#      occluded_ids in its own _process when the rig camera's global_transform differs from the one cached at the last recompute,
#      at most once per DRAFT-occlusion-recompute-ms 100 ms while it keeps changing, and once more when it settles. The test
#      drives the rig through its public verbs (zoom_by, pan_to, pan, set_top_down; the paragraph's pan_by is pan in the rig), then _settle() waits: until the camera
#      global_transform is unchanged for 10 consecutive frames, then 300 ms of wall time (3 x the 100 ms settle recompute) and
#      one more frame. BOUND: at most 600 frames or 10 s for the camera to settle (a failure to settle is its own red check);
#      the whole wait is therefore bounded by about 10.3 s per verb. No set_frame call between the verb and the read.
#  (5) The stub EraConfig: the real autoload is renamed aside for the duration of the unit-visuals checks and put back.
#  (6) CREST UNIT OFFSET. The paragraph says 10 wu behind the crest, "inside the 20 wu slack". Measured with GroundPick on
#      this fixture: the pick hit is 22.0 wu nearer than the unit at 10 wu (y = 440), so the paragraph's own control
#      would count as occluded; 17.6 at 8 wu (y = 442), 13.2 at 6 wu. This test uses 8 wu (the one number not from the
#      paragraph; nothing else here is). Separately, GroundPick's 50 wu march step skips the thin crest for some rays
#      (y = 438: no hit before the unit, gap -535), a false negative the paragraph does not know about.
#  (7) ARROWS KEY (Architect ruling 2026-10-23): qa_state()["arrows"] is a Dictionary {"units_3d": int, "units_2d": int},
#      from Units3D.arrow_count() (ground_units.gd) and UnitVisuals.arrow_count() (unit_visuals.gd), both added by the
#      facing-arrow piece, which lands first. Inner names are this test's choice. Red on main for reason (b): no key.
# (8) RECOMPUTE SEQUENCE (TD-VG-C-land-marks-fixture, 2026-10-23): the old sequence zoom_by(-9), pan_to, pan, set_top_down clamped
#      the camera at height 300 on its first step and gave [1] at every pose. The new one, from the rig default (height 3000,
#      pitch 50); camera poses measured on the builder tree: (a) pan_to(450,450) + set_top_down(true): camera (450,3400,450)
#      straight above the crest, vertical rays, oracle []; (b) set_top_down(false): camera (450,3400,2967), oracle [1];
#      (c) zoom_by(-9): camera (450,700,702), oracle [1]; (d) pan_to(450,900) then pan(0,-300): camera (450,300,852), oracle [1].
#      Two distinct sets, [] then [1], occur between (a) and (b); (c) and (d) keep the old low-camera coverage.
# (9) OCCLUSION COST (Architect ruling 2026-10-23, cost guard): the pass is time-sliced, DRAFT-occlusion-slice-ms 2 per frame, a full
#     pass within DRAFT-occlusion-pass-ms 500 on the S-001 frame, occluded_ids swapped in whole when a pass completes. UNSTATED
#     INTERFACE CHOICE: Ground3DHost.occlusion_stats() -> Dictionary {max_slice_us: int, last_pass_ms: float, passes: int,
#     pending: int}. max_slice_us is the largest single-frame occlusion cost (Time.get_ticks_usec around the slice loop of one
#     _process) since the PREVIOUS occlusion_stats() call and is reset by the read, so the test excludes the one-time first-frame
#     warm-up by reading (and discarding) the stats after the first frame; nothing else is excluded, no tolerance. last_pass_ms is
#     the wall time from a pass's start to its swap, passes counts completed passes, pending the units left in the running pass.
#     The S-001 frame is the real one: a CBridge session (seed 1, CBridge.DEFAULT_N_REGIONS, DEFAULT_FEATURES) with EraConfig
#     set to greek_placeholder (as the plays' --era does), load_tactical_live, terrain() and tactical_frame() into a host.
#     Renderer-only (the dummy renderer is no measure of a Vulkan frame): headless prints a RENDER-ONLY line and checks that the
#     accessor exists; the sliced work is measured under OM_QA_RENDERER=vulkan xvfb-run -a.
# (10) SPACE HOST LIVE STEP (Fable pre-landing review row 15): with OM_SPACE_VIEW=1 tactical_view's _ground3d is the SpaceView
#     host (tactical_view.gd _host_space_view sets _space_hosted = true), which has no occluded_ids(); the spec paragraph says the
#     space path is unchanged (visible = true). test_space_host_apply_motion_survives hosts a stub that lacks occluded_ids() exactly
#     as SpaceView does (the real SpaceView needs a C-sim space_field, not available headless here), assigned as that function does.
# Fixture frame (host and view): faction 0 owns all of 1 (behind), 2 (front), 3 (8 wu behind the crest); ids and points
# below in _frame(). Camera = the rig default after set_terrain (height 3000, pitch 50 degrees).
# Positive control (paragraph): a flat fixture gives an empty occluded_ids. The pick-distance controls (test_pick_geometry)
# run GroundPick directly and are GREEN on main: they prove the fixture occludes, so the host's red is the host's.

const SLACK_WU := 20.0 # DRAFT-occlusion-slack, ledger day38
const RIDGE_CM := 40000 # 400 wu
const BEHIND := Vector2(450.0, 100.0)
const FRONT := Vector2(450.0, 700.0)
const CREST := Vector2(450.0, 442.0) # 8 wu behind the crest's camera-side edge at y = 450 (cell 4's centre); see choice (6)
const UnitVisualsScript := "res://scenes/tactical_c/unit_visuals.gd"

var _stub_src := "extends Node\nvar era := \"ground\"\nfunc kind() -> String:\n\treturn era\n"


func _terrain(ridge: bool) -> Dictionary:
	var hs := PackedInt32Array()
	var bands := PackedByteArray()
	var walk := PackedByteArray()
	for j in 8:
		for i in 8:
			hs.append(RIDGE_CM if (ridge and (j == 3 or j == 4)) else 0)
			bands.append(1)
			walk.append(1)
	return {"cells_w": 8, "cells_h": 8, "bands": bands, "walkable": walk, "heights": hs, "slopes": []}


func _unit(id: int, p: Vector2, layer: int = 0) -> Dictionary:
	return {"id": id, "faction": 0, "type": 0, "tier": 0, "x": p.x, "y": p.y, "hp": 100, "layer": layer, "facing": 0.0,
		"target": -1, "state": 0, "sight": 200}


func _frame() -> Dictionary:
	var units := [_unit(1, BEHIND), _unit(2, FRONT), _unit(3, CREST)]
	var profiles := []
	for t in 6:
		profiles.append({"type": t, "max_hp": 100.0, "range": 600.0, "interval": 10, "sensor": 800.0, "ability": t, "acd_max": 100, "aoe": 0.0})
	return {"type": "tactical", "tick": 10, "player_faction": 0, "units": units, "visible": {"0": [1, 2, 3], "1": []},
		"profiles": profiles, "events": [], "structures": [], "objectives": [],
		"map": {"nodes": [], "cover": [], "obstacles": [], "canvas": 1000.0}}


# Oracle, independent of the product: ids the paragraph's rule marks occluded for this camera.
func _oracle(t: Dictionary, cam: Camera3D, pts: Dictionary) -> Array:
	var out: Array = []
	var Pick := load("res://scenes/ground3d/ground_pick.gd")
	for id in pts:
		var p: Vector2 = pts[id]
		var up: Vector3 = Pick.world_to_3d(t, p.x, p.y)
		var d := up - cam.global_position
		var hit = Pick.pick(t, cam.global_position, d.normalized())
		if hit == null:
			continue
		var hp: Vector3 = Pick.world_to_3d(t, hit.x, hit.y)
		if d.length() - (hp - cam.global_position).length() > SLACK_WU:
			out.append(id)
	out.sort()
	return out


func _points() -> Dictionary:
	return {1: BEHIND, 2: FRONT, 3: CREST}


func _host(t: Dictionary):
	var hs := _load(SCENES + "ground3d.gd")
	if hs == null:
		return null
	var host = hs.new()
	root.add_child(host)
	await process_frame
	host.set_terrain(t)
	host.set_frame(_frame(), {"objectives": []})
	return host


# The spec provenance lint (spec_provenance.assertions) reads only lines that start with `_assert(`, so the line that
# carries the Westley quote's words uses this wrapper; it is _check under another name.
func _assert(cond: bool, msg: String) -> void:
	_check(cond, msg)


func _sorted_ids(d: Variant) -> Array:
	var out: Array = []
	if d is Dictionary:
		for k in (d as Dictionary).keys():
			out.append(int(k))
	out.sort()
	return out


func _run() -> void:
	await test_pick_geometry()
	await test_ring_only_in_space()
	await test_ring_follows_flag_after_recreate()
	await test_host_occlusion()
	await test_host_flat_control()
	await test_host_recompute_on_camera_change()
	await test_occlusion_cost()
	await test_view_marks_land()
	await test_view_marks_space_control()
	await test_space_host_apply_motion_survives()


# GREEN on main: GroundPick on the ridge fixture (R-001-06; the paragraph's "compares the pick distance to the unit distance").
func test_pick_geometry() -> void:
	var t := _terrain(true)
	var host = await _host(t)
	if host == null:
		return
	var cam: Camera3D = host.camera_rig().get_camera()
	var Pick := load("res://scenes/ground3d/ground_pick.gd")
	var gaps := {}
	for id in _points():
		var p: Vector2 = _points()[id]
		var up: Vector3 = Pick.world_to_3d(t, p.x, p.y)
		var d := up - cam.global_position
		var hit = Pick.pick(t, cam.global_position, d.normalized())
		gaps[id] = d.length() - (Pick.world_to_3d(t, hit.x, hit.y) - cam.global_position).length() if hit != null else 0.0
	_check(gaps[1] > SLACK_WU, "R-001-06: the unit behind the ridge: pick hit not nearer than its point by more than %s wu (gap %s)" % [SLACK_WU, gaps[1]])
	_check(absf(gaps[2]) <= SLACK_WU, "R-001-06 CONTROL: the unit in front: pick hit is not at its own point (gap %s)" % gaps[2])
	_check(gaps[3] <= SLACK_WU, "R-001-06 CONTROL: the unit 8 wu behind the crest is inside the %s wu slack (gap %s)" % [SLACK_WU, gaps[3]])
	_check(host.camera_rig().get_camera().global_position.y > 2500.0, "R-001-06: the camera is at the rig default height, got %s" % host.camera_rig().get_camera().global_position)
	host.queue_free()


func _with_era(kind_name: String, uv_frame: Dictionary) -> Node:
	var real := root.get_node_or_null("EraConfig")
	if real != null:
		real.name = "EraConfigReal"
	if kind_name != "":
		var s := GDScript.new()
		s.source_code = _stub_src
		s.reload()
		var stub = s.new()
		stub.name = "EraConfig"
		stub.era = kind_name
		root.add_child(stub)
	var uvs := _load(UnitVisualsScript)
	if uvs == null:
		return null
	var uv = uvs.new()
	root.add_child(uv)
	uv.set_frame(uv_frame, 0, 0.25, Vector2(400, 400))
	return uv


func _restore_era() -> void:
	var stub := root.get_node_or_null("EraConfig")
	if stub != null:
		root.remove_child(stub)
		stub.queue_free()
	var real := root.get_node_or_null("EraConfigReal")
	if real != null:
		real.name = "EraConfig"


# S-001 R-001-06, DEC-S001-no-layer-ring-land. The [ASSERT] target for the paragraph's first [W] quote.
func test_ring_only_in_space() -> void:
	var f := _frame()
	var uv = _with_era("ground", f)
	if uv == null:
		_restore_era()
		return
	_check("layer_rings_enabled" in uv and uv.layer_rings_enabled == false, "R-001-06: on land UnitVisuals.layer_rings_enabled is false, got %s" % [uv.get("layer_rings_enabled")])
	for id in [1, 2, 3]:
		var ring = uv.layer_ring(id)
		_check(ring != null, "R-001-06: layer_ring(%d) still returns the node on land (parity with test_vg_a_unit_visuals)" % id)
		_assert(ring != null and not (ring as Node2D).visible, "R-001-06: Space era is the only one that needs the circular indicators: the land ring of unit %d is invisible" % id)
		var body = uv.unit_node(id).get_node("Body") if uv.unit_node(id) != null else null
		_check(body != null and (body as Node2D).visible, "R-001-06: the land Body of unit %d stays visible" % id)
	uv.set_frame(f, 0, 0.25, Vector2(400, 400))
	_check(uv.layer_ring(1) != null and not (uv.layer_ring(1) as Node2D).visible, "R-001-06: a second set_frame never turns a disabled ring on")
	uv.queue_free()
	_restore_era()
	# CONTROL (space era stub): the ring is drawn.
	uv = _with_era("space", f)
	if uv != null:
		_check("layer_rings_enabled" in uv and uv.layer_rings_enabled == true, "R-001-06 CONTROL: space era layer_rings_enabled is true, got %s" % [uv.get("layer_rings_enabled")])
		_check(uv.layer_ring(1) != null and (uv.layer_ring(1) as Node2D).visible, "R-001-06 CONTROL: the space era ring is visible")
		uv.queue_free()
	_restore_era()
	# CONTROL (era node absent): true, the space path unchanged.
	uv = _with_era("", f)
	if uv != null:
		_check(root.get_node_or_null("EraConfig") == null, "R-001-06 CONTROL: fixture has no EraConfig node")
		_check(uv.layer_ring(1) != null and (uv.layer_ring(1) as Node2D).visible, "R-001-06 CONTROL: with the era node absent the ring is visible")
		uv.queue_free()
	_restore_era()


# A ring recreated by _drop (unit changes layer) follows the flag.
func test_ring_follows_flag_after_recreate() -> void:
	var f := _frame()
	var uv = _with_era("ground", f)
	if uv == null:
		_restore_era()
		return
	var f2 := _frame()
	(f2["units"][0] as Dictionary)["layer"] = 2
	uv.set_frame(f2, 0, 0.25, Vector2(400, 400))
	var ring = uv.layer_ring(1)
	_check(ring != null and not (ring as Node2D).visible, "R-001-06: a ring recreated after a layer change is invisible on land")
	uv.queue_free()
	_restore_era()


func test_host_occlusion() -> void:
	var t := _terrain(true)
	var host = await _host(t)
	if host == null:
		return
	var has: bool = host.has_method("occluded_ids")
	_check(has, "R-001-06: Ground3D host lacks occluded_ids()")
	if has:
		var got := _sorted_ids(host.occluded_ids())
		_check(got == [1], "R-001-06: occluded_ids is exactly the unit behind the ridge [1] (front 2 and 8-wu-behind-crest 3 are not), got %s" % [got])
		var qa = host.qa_state().get("ground3d", {}).get("occluded_ids", null)
		_check(qa is Array and qa == [1], "R-001-06: qa_state ground3d.occluded_ids is the sorted ints [1], got %s" % [qa])
	host.queue_free()


# Positive control (paragraph): a flat fixture gives an empty occluded_ids.
func test_host_flat_control() -> void:
	var host = await _host(_terrain(false))
	if host == null:
		return
	var has: bool = host.has_method("occluded_ids")
	_check(has, "R-001-06 CONTROL: Ground3D host lacks occluded_ids()")
	if has:
		_check(host.occluded_ids().is_empty(), "R-001-06 CONTROL: a flat fixture gives an empty occluded_ids, got %s" % [host.occluded_ids()])
	# GREEN on main: the pick-rule oracle itself finds nothing occluded on flat ground.
	_check(_oracle(_terrain(false), host.camera_rig().get_camera(), _points()).is_empty(), "R-001-06 CONTROL: the pick rule marks nothing on flat ground")
	host.queue_free()


# DRAFT-occlusion-recompute: the host recomputes from the rig camera's transform in its own _process (header choice 4).
func test_host_recompute_on_camera_change() -> void:
	var t := _terrain(true)
	var host = await _host(t)
	if host == null or not host.has_method("occluded_ids"):
		_check(false, "R-001-06: Ground3D host lacks occluded_ids() (recompute test)")
		if host != null:
			host.queue_free()
		return
	var rig = host.camera_rig()
	var cam: Camera3D = rig.get_camera()
	var seen := {}
	for step in ["top_down_over_crest", "side_view", "zoom_in", "pan_far"]:
		match step:
			"top_down_over_crest":
				rig.pan_to(Vector2(450.0, 450.0))
				rig.set_top_down(true)
			"side_view":
				rig.set_top_down(false)
			"zoom_in":
				rig.zoom_by(-9)
			"pan_far":
				rig.pan_to(Vector2(450.0, 900.0))
				rig.pan(Vector2(0.0, -300.0))
		var settled: bool = await _settle(cam)
		_check(settled, "R-001-06 CONTROL: the camera settled within the bound after rig %s" % step)
		var want := _oracle(t, cam, _points())
		var got := _sorted_ids(host.occluded_ids())
		seen[str(want)] = true
		_check(got == want, "R-001-06: after rig %s and the settle wait occluded_ids is %s, the pick rule gives %s" % [step, got, want])
	_check(seen.size() >= 2, "R-001-06 CONTROL: the camera moves produce at least two different occluded sets, saw %s" % [seen.keys()])
	host.queue_free()


# DRAFT-occlusion-slice-ms 2 and DRAFT-occlusion-pass-ms 500 (header choice 9). Renderer-only: see the header.
func test_occlusion_cost() -> void:
	var stats_ok := false
	if DisplayServer.get_name() == "headless":
		var h = await _host(_terrain(true))
		if h != null:
			stats_ok = h.has_method("occlusion_stats")
			h.queue_free()
		print("RENDER-ONLY: test_occlusion_cost measurements not run (headless dummy renderer; run under OM_QA_RENDERER=vulkan xvfb-run -a); only the occlusion_stats accessor is checked")
		_check(stats_ok, "R-001-06: Ground3D host lacks occlusion_stats() ({max_slice_us, last_pass_ms, passes, pending})")
		return
	var era = root.get_node_or_null("EraConfig")
	if era == null:
		_check(false, "R-001-06: no EraConfig autoload, the S-001 frame cannot be loaded")
		return
	var prev: String = era.ACTIVE_ERA_ID
	era.set_era("greek_placeholder")
	var CBridge = load("res://autoload/c_bridge.gd")
	var bridge = CBridge.new()
	var live: bool = bridge.load_tactical_live(1, CBridge.DEFAULT_N_REGIONS, CBridge.DEFAULT_FEATURES)
	_check(live, "R-001-06: the S-001 frame did not load live (%s)" % [bridge.last_error()])
	var t: Dictionary = bridge.terrain()
	var frame: Dictionary = bridge.tactical_frame()
	var mission: Dictionary = bridge.mission()
	bridge.close_session()
	era.set_era(prev)
	if not live or t.is_empty():
		_check(false, "R-001-06: no ground terrain for the S-001 frame")
		return
	var units: Array = frame.get("units", [])
	_check(units.size() >= 100, "R-001-06 CONTROL: the S-001 frame is the real crowded one (at least 100 units), got %d" % units.size())
	var host = (_load(SCENES + "ground3d.gd")).new()
	root.add_child(host)
	await process_frame
	host.set_terrain(t)
	var t0 := Time.get_ticks_msec()
	host.set_frame(frame, mission)
	_check(host.has_method("occlusion_stats"), "R-001-06: Ground3D host lacks occlusion_stats() ({max_slice_us, last_pass_ms, passes, pending})")
	if not host.has_method("occlusion_stats"):
		host.queue_free()
		return
	await process_frame
	host.occlusion_stats() # discard: the one-time first-frame warm-up, and the reset of max_slice_us
	var worst_us := 0
	var pass_wall_ms := -1
	for f in 60:
		await process_frame
		var s: Dictionary = host.occlusion_stats()
		worst_us = maxi(worst_us, int(s.get("max_slice_us", 0)))
		if pass_wall_ms < 0 and int(s.get("passes", 0)) >= 1:
			pass_wall_ms = Time.get_ticks_msec() - t0
	_check(worst_us < 2000, "R-001-06: max per-frame occlusion cost over 60 frames is %.3f ms, DRAFT-occlusion-slice-ms is 2" % [worst_us / 1000.0])
	# Wait for the passes to stop (camera settled, nothing pending), bounded at 600 frames.
	var quiet := 0
	var last_passes := -1
	var n := 0
	while quiet < 30 and n < 600:
		await process_frame
		n += 1
		var s2: Dictionary = host.occlusion_stats()
		if int(s2.get("pending", 1)) == 0 and int(s2.get("passes", 0)) == last_passes and int(s2.get("passes", 0)) >= 1:
			quiet += 1
		else:
			quiet = 0
		last_passes = int(s2.get("passes", 0))
		if pass_wall_ms < 0 and last_passes >= 1:
			pass_wall_ms = Time.get_ticks_msec() - t0
	_check(quiet >= 30, "R-001-06 CONTROL: the occlusion passes settled (no pending units, passes unchanged for 30 frames) within 600 frames")
	var final: Dictionary = host.occlusion_stats()
	_check(pass_wall_ms >= 0 and pass_wall_ms <= 500, "R-001-06: a full pass over the S-001 frame completes within 500 ms (DRAFT-occlusion-pass-ms), first completed after %d ms" % pass_wall_ms)
	_check(float(final.get("last_pass_ms", 1e9)) <= 500.0, "R-001-06: the host's own last_pass_ms is within 500 ms, got %s" % [final.get("last_pass_ms")])
	var pts := {}
	for u in units:
		pts[int(u.get("id"))] = Vector2(float(u.get("x", 0.0)), float(u.get("y", 0.0)))
	var want := _oracle(t, host.camera_rig().get_camera(), pts)
	var got := _sorted_ids(host.occluded_ids())
	_check(got == want, "R-001-06: after the sliced passes occluded_ids (%d ids) equals the unsliced pick-rule oracle (%d ids); only in got: %s, only in want: %s" % [got.size(), want.size(), got.filter(func(i): return not want.has(i)), want.filter(func(i): return not got.has(i))])
	print("OCCLUSION-COST units=%d worst_slice_ms=%.3f first_pass_wall_ms=%d last_pass_ms=%s passes=%s occluded=%d" % [units.size(), worst_us / 1000.0, pass_wall_ms, final.get("last_pass_ms"), final.get("passes"), got.size()])
	host.queue_free()


# Wait until the camera has settled plus one frame past the 100 ms settle recompute; see header choice (4).
func _settle(cam: Camera3D) -> bool:
	var last := cam.global_transform
	var still := 0
	var frames := 0
	var t0 := Time.get_ticks_msec()
	while still < 10 and frames < 600 and Time.get_ticks_msec() - t0 < 10000:
		await process_frame
		frames += 1
		if cam.global_transform == last:
			still += 1
		else:
			still = 0
			last = cam.global_transform
	if still < 10:
		return false
	var t1 := Time.get_ticks_msec()
	while Time.get_ticks_msec() - t1 < 300:
		await process_frame
	await process_frame
	return true


func _view_land():
	var cfg = root.get_node("EraConfig")
	cfg.set_era(cfg.GROUND_ERA_ID)
	var v: Node = (load("res://scenes/tactical_c/tactical_view.tscn") as PackedScene).instantiate()
	root.add_child(v)
	await process_frame
	v.set_process(false)
	await process_frame
	cfg.set_era(cfg.GROUND_ERA_ID)
	v.load_frame(_frame())
	v.set_terrain(_terrain(true))
	await process_frame
	return v


# The 2D marks on the real view: behind-ridge unit hidden (Body and ring), others' Body visible, no ring on land.
func test_view_marks_land() -> void:
	var v = await _view_land()
	var qa: Dictionary = v.qa_state()
	var mv = qa.get("marks_visible", null)
	_check(mv is Dictionary, "R-001-06: tactical_view qa_state has no marks_visible, keys %s" % [qa.keys()])
	if mv is Dictionary:
		var m: Dictionary = mv
		_check(m.get("1", {}) == {"body": false, "ring": false}, "R-001-06: the unit behind the ridge has no mark drawn, got %s" % [m.get("1")])
		_check(m.get("2", {}) == {"body": true, "ring": false}, "R-001-06: the unit in front keeps its Body and has no land ring, got %s" % [m.get("2")])
		_check(m.get("3", {}) == {"body": true, "ring": false}, "R-001-06 CONTROL: the unit inside the slack keeps its Body, got %s" % [m.get("3")])
	var uvn = v.get_node("UnitVisuals")
	var n1 = uvn.unit_node(1)
	var n2 = uvn.unit_node(2)
	_check(n1 != null and not n1.visible, "R-001-06: the 2D node of the occluded unit 1 is invisible")
	_check(n2 != null and n2.visible, "R-001-06 CONTROL: the 2D node of the unit in front is visible")
	var ar = qa.get("arrows", null)
	_check(ar is Dictionary and (ar as Dictionary).get("units_3d", null) is int and (ar as Dictionary).get("units_2d", null) is int, "R-001-06: qa_state has an arrows Dictionary {units_3d: int, units_2d: int}, got %s" % [ar])
	var g: Dictionary = qa.get("ground3d", {})
	_check(g.get("occluded_ids", null) == [1], "R-001-06: the view's ground3d block carries occluded_ids [1], got %s" % [g.get("occluded_ids")])
	root.get_node("EraConfig").set_era(root.get_node("EraConfig").SPACE_ERA_ID)
	v.queue_free()


# CONTROL: the space era (no Ground3D host) leaves every mark as today: Body and ring both visible.
func test_view_marks_space_control() -> void:
	var cfg = root.get_node("EraConfig")
	cfg.set_era(cfg.SPACE_ERA_ID)
	var v: Node = (load("res://scenes/tactical_c/tactical_view.tscn") as PackedScene).instantiate()
	root.add_child(v)
	await process_frame
	v.set_process(false)
	await process_frame
	v.load_frame(_frame())
	await process_frame
	var mv = v.qa_state().get("marks_visible", null)
	_check(mv is Dictionary, "R-001-06 CONTROL: tactical_view qa_state has no marks_visible in the space era")
	if mv is Dictionary:
		for id in ["1", "2", "3"]:
			_check((mv as Dictionary).get(id, {}) == {"body": true, "ring": true}, "R-001-06 CONTROL: space era unit %s keeps Body and ring, got %s" % [id, (mv as Dictionary).get(id)])
	v.queue_free()


class SpaceHostStub extends Node:
	func to_screen(wx: float, wy: float, _layer: int = -1) -> Vector2:
		return Vector2(wx, wy)


# CONTROL: a SpaceView-like host (no occluded_ids(), _space_hosted true) survives a live _apply_motion step and leaves every
# own unit's node visible (the space path is unchanged), see choice (10).
func test_space_host_apply_motion_survives() -> void:
	var cfg = root.get_node("EraConfig")
	cfg.set_era(cfg.SPACE_ERA_ID)
	var v: Node = (load("res://scenes/tactical_c/tactical_view.tscn") as PackedScene).instantiate()
	root.add_child(v)
	await process_frame
	v.set_process(false)
	await process_frame
	v.load_frame(_frame())
	await process_frame
	var host := SpaceHostStub.new()
	_check(not host.has_method("occluded_ids"), "R-001-06 CONTROL: the stub space host lacks occluded_ids() as SpaceView does")
	v.add_child(host)
	v._ground3d = host
	v._space_hosted = true
	v._live_stepped = true
	v._motion.push_frame(_frame())
	v._apply_motion()
	for id in [1, 2, 3]:
		var n = v.get_node("UnitVisuals").unit_node(id)
		_check(n != null and n.visible, "R-001-06: space host, one live _apply_motion step keeps unit %d's node visible (space path unchanged)" % id)
	v._ground3d = null
	v._space_hosted = false
	host.queue_free()
	v.queue_free()
