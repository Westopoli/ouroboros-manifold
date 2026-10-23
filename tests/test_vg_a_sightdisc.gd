extends "res://tests/support/vg_c_case.gd"
# Rule pins: R-004-06@ebf993, R-005-09@dd0832, R-089-03@c09d1f

# VG-A-sightdisc (spec paragraph "VG-A-sightdisc", amended 2026-10-22/23). Proves S-005 / S-126 sight discs, R-089-03 (what is
# outside sight is dimmed; the disc only draws what R-089-03 computes), R-005-09 (high ground sees down, an upward look in a
# ground era sees nothing), R-004-06 (a unit below a ramp sees nothing above the midline).
# RED on main because: sight_discs() holds {center, radius} screen circles, not {points: PackedVector2Array} polygons.
#
# UNSTATED INTERFACE choices made by the test writer (the paragraph does not fix them):
#  - Ground path: FogLayer.set_projector(Callable world Vector2 -> screen px) is given a lambda over Ground3DHost.to_screen (the
#    projector the tactical view already passes, tactical_view.gd _project_ground); FogLayer.set_terrain(terrain Dictionary) is
#    called when the layer has that method (the paragraph names it, the call site is VG-C-land-one-projection's, so these tests
#    call it themselves and never rely on this piece adding either the call or the qa_state key sight_discs).
#    set_frame(frame, mission, local_faction) with mission {} is the ground call shape (unchanged from main).
#  - A point is matched to its expected screen position order-free (start angle and winding of the 48 points are not fixed);
#    theta k = 2 pi k / 48 is the set the points must equal, within 0.5 px (the tolerance of test_vg_a_fog_layer.gd A4).
#  - The unit's band is the `bands` value of the cell it stands in; fixture units carry layer == band so either reading passes.
#  - World position of a polygon point is read back with Ground3DHost.to_world (a pick); the clip assertions allow one cell
#    (CELL_WU 100, DRAFT-sightdisc-slope-cell: the one-cell error at a midline is accepted) of slack.
#  - screen_points() is compared with the polygon's area centroid or its vertex mean, either, within 0.5 px.
#  - Mask control: the composite is sampled from the root viewport (white backdrop under the FogLayer, flat 2D path) because the
#    paragraph fixes the mask as "a SubViewport" but not how a test reaches its texture; lit = backdrop colour, dimmed = darker.
#    A headless run (dummy renderer) has no pixels: there the test asserts only that a SubViewport exists under the FogLayer and
#    prints "MASK-PIXELS: not sampled"; run it under xvfb-run with OM_QA_RENDERER=vulkan to sample.
#  - qa_state()["sight_discs"] belongs to VG-C-land-one-projection (the shape of an entry's bounding box is not fixed in the
#    paragraph), so it is not asserted here.
#  - Near-plane clip (fix brief 2026-10-23, tests 24 on): the helper is FogLayer.clip_to_plane(pts: PackedVector3Array,
#    plane: Plane) -> PackedVector3Array, called statically through load(FOG); "in front" is plane.distance_to(p) >= 0.0. A test
#    that finds the method missing fails with a message (no parse error). The helper script path is FOG unless the environment
#    variable OM_CLIP_HELPER names another script (used once, to run the three helper tests against a reference). The near-plane
#    construction (camera near + margin) is the doer's and is not asserted; the low-camera test reads only qa_state() sight_discs
#    boxes. Its land fixture is a copy of tests/test_vg_c_land_one_projection.gd's (240x240 cells, 12 own units, sight 800, ground
#    era, camera_set {height} through qa_daemon._dispatch), so it needs no qa key beyond sight_discs.
# Positive controls: on main the pitch-50 ratio reads 1.0 (the fallback below builds a circle polygon from centre and radius when
# `points` is absent, so the stated reason is shown by a number, not by a missing key), both ramp discs are full circles, and the
# source still holds the radius disc field, the float texture and the hole-punch loop.

const Ground3DHost := preload("res://scenes/ground3d/ground3d.gd")
const FOG := "res://scenes/tactical_c/fog_layer.gd"
const CELL := 100.0
const SEGMENTS := 48                 # DRAFT-sightdisc-segments
const RATIO_TOL_50 := 0.05           # DRAFT-sightdisc-ratio-tol
const RATIO_TOL_90 := 0.02
const CLOSE_HEIGHT := 300.0          # DRAFT-sightdisc-close-height
const SIN50 := 0.7660444431189780


func _terrain(kind: String) -> Dictionary:
	var bands := PackedByteArray()
	var walk := PackedByteArray()
	var heights := PackedInt32Array()
	for j in 8:
		for i in 8:
			walk.append(1)
			match kind:
				"ramp":  # bands 1 on columns 0..3, 2 on 4..7; heights 0 and 300 wu (30000 cm)
					bands.append(1 if i < 4 else 2)
					heights.append(0 if i < 4 else 30000)
				"rise":  # one band, ground rising 50 wu per row toward row 0 (far from the camera)
					bands.append(1)
					heights.append((7 - j) * 5000)
				_:
					bands.append(1)
					heights.append(0)
	return {"cells_w": 8, "cells_h": 8, "bands": bands, "walkable": walk, "heights": heights, "slopes": []}


func _frame(units: Array) -> Dictionary:
	return {"type": "tactical", "tick": 100, "player_faction": 0, "units": units, "visible": {"0": [], "1": []},
		"profiles": [], "events": [], "structures": [], "objectives": []}


func _unit(id: int, x: float, y: float, sight: float, layer: int = 1) -> Dictionary:
	return {"id": id, "faction": 0, "type": 0, "tier": 0, "x": x, "y": y, "hp": 100.0, "layer": layer, "facing": 0.0,
		"target": -1, "state": 0, "sight": sight}


# A host on `t` with the rig panned to `at`, a FogLayer given its projector (and terrain when it can take it).
func _rig(t: Dictionary, at: Vector2, steps: int = 0, top_down: bool = false) -> Array:
	var host = Ground3DHost.new()
	root.add_child(host)
	await process_frame
	host.set_terrain(t)
	var rig = host.camera_rig()
	rig.zoom_by(steps)
	rig.set_top_down(top_down)
	rig.pan_to(at)
	await process_frame
	var fg = load(FOG).new()
	root.add_child(fg)
	await process_frame
	fg.set_projector(func(w: Vector2) -> Vector2: return host.to_screen(w.x, w.y))
	if fg.has_method("set_terrain"):
		fg.set_terrain(t)
	return [host, fg]


# The polygon of disc i; on main (no `points`) a 48-point circle from centre and radius, so the control reads a number.
func _poly(d: Dictionary) -> PackedVector2Array:
	if d.has("points"):
		return d["points"]
	var out := PackedVector2Array()
	for k in SEGMENTS:
		var a := TAU * k / SEGMENTS
		out.append((d["center"] as Vector2) + Vector2(cos(a), sin(a)) * float(d["radius"]))
	return out


func _bbox(p: PackedVector2Array) -> Rect2:
	var r := Rect2(p[0], Vector2.ZERO)
	for q in p:
		r = r.expand(q)
	return r


func _area_centroid(p: PackedVector2Array) -> Vector2:
	var a := 0.0
	var c := Vector2.ZERO
	for k in p.size():
		var u := p[k]
		var v := p[(k + 1) % p.size()]
		var cr := u.x * v.y - v.x * u.y
		a += cr
		c += (u + v) * cr
	return c / (3.0 * a) if absf(a) > 0.0001 else p[0]


func _vertex_mean(p: PackedVector2Array) -> Vector2:
	var s := Vector2.ZERO
	for q in p:
		s += q
	return s / p.size()


func _discs(fg) -> Array:
	return fg.sight_discs()


# World (x, y) of every polygon point through the host's pick; a point that picks nothing is returned as Vector2(INF, INF).
func _world_points(host, p: PackedVector2Array) -> Array:
	var out := []
	for q in p:
		var w = host.to_world(q)
		out.append(w if w is Vector2 else Vector2(INF, INF))
	return out


func _run() -> void:
	if load(FOG) == null:
		_check(false, "VG-A-sightdisc: fog_layer.gd is missing")
		return
	await _ratio_and_close()
	await _slope_heights()
	await _ramp_clip()
	await _space_path()
	await _mask()
	_deletion()
	_clip_tests()
	await _low_camera()


func _ratio_and_close() -> void:
	for case in [["pitch 50 (the 3D rig's pitch)", false, SIN50, RATIO_TOL_50], ["pitch 90 (top down)", true, 1.0, RATIO_TOL_90]]:
		var r = await _rig(_terrain("flat"), Vector2(400, 400), 0, case[1])
		var fg = r[1]
		fg.set_frame(_frame([_unit(1, 400, 400, 300)]), {}, 0)
		var d := _discs(fg)
		_check(d.size() == 1, "S-126: one disc per own unit, got %d" % d.size())
		if d.size() == 1:
			var b := _bbox(_poly(d[0]))
			var ratio := b.size.y / maxf(b.size.x, 0.001)
			_check(absf(ratio - case[2]) <= case[3], "S-126 R-089-03: bbox height over width at %s must be %.3f +- %.2f, reads %.3f (CONTROL: main reads 1.0 at pitch 50)" % [case[0], case[2], case[3], ratio])
			_check(d[0].has("points") and (d[0]["points"] as PackedVector2Array).size() == SEGMENTS, "S-126: a disc is {points} of %d screen points (interface absent on main)" % SEGMENTS)
			var sp: Array = fg.screen_points()
			var c := _poly(d[0])
			_check(sp.size() == 1 and d[0].has("points") and ((sp[0] as Vector2).distance_to(_area_centroid(c)) <= 0.5 or (sp[0] as Vector2).distance_to(_vertex_mean(c)) <= 0.5), "S-126: screen_points() returns each polygon's centroid, got %s" % [sp])
		r[0].queue_free()
		fg.queue_free()
	# Close zoom: camera height 300 (FINDING-fog-dim-close-zoom): the disc is a finite polygon on screen at the unit.
	var r2 = await _rig(_terrain("flat"), Vector2(400, 400), -9)
	_check(absf(r2[0].camera_rig().camera_height() - CLOSE_HEIGHT) < 0.5, "fixture: close-zoom camera height must be %.0f, got %.1f" % [CLOSE_HEIGHT, r2[0].camera_rig().camera_height()])
	r2[1].set_frame(_frame([_unit(1, 400, 400, 200)]), {}, 0)
	var d2 := _discs(r2[1])
	if d2.size() == 1:
		var p := _poly(d2[0])
		var b2 := _bbox(p)
		var finite := true
		for q in p:
			finite = finite and is_finite(q.x) and is_finite(q.y)
		var cen := _area_centroid(p)
		_check(d2[0].has("points") and finite and b2.size.x > 1.0 and b2.size.y > 1.0 and Rect2(Vector2.ZERO, Ground3DHost.SCREEN_SIZE).has_point(cen),
			"FINDING-fog-dim-close-zoom: at camera height 300 the disc is a finite polygon around the unit on screen, bbox %s centroid %s" % [b2, cen])
	else:
		_check(false, "FINDING-fog-dim-close-zoom: no disc at camera height 300")
	r2[0].queue_free()
	r2[1].queue_free()


# Points sit at the terrain heights: on ground that rises away from the camera the far points are higher on screen than a flat
# disc (the unit's own height all round) would put them.
func _slope_heights() -> void:
	var t := _terrain("rise")
	var r = await _rig(t, Vector2(400, 400))
	var host = r[0]
	var fg = r[1]
	var u := Vector2(400, 400)
	var sight := 250.0
	fg.set_frame(_frame([_unit(1, u.x, u.y, sight)]), {}, 0)
	var d := _discs(fg)
	if d.size() != 1 or not d[0].has("points"):
		_check(false, "S-126: a disc polygon is needed for the terrain-height check (interface absent on main)")
	else:
		var pts: PackedVector2Array = d[0]["points"]
		var cam: Camera3D = host.camera_rig().get_camera()
		var h0: float = host.camera_rig().height_at(u.x, u.y)
		var matched := 0
		var flat_matched := 0
		var far_terrain := INF
		var far_flat := INF
		for k in SEGMENTS:
			var a := TAU * k / SEGMENTS
			var g := u + Vector2(cos(a), sin(a)) * sight
			var want: Vector2 = host.to_screen(g.x, g.y)
			var flat := cam.unproject_position(Vector3(g.x, h0, g.y))
			var near := false
			var near_flat := false
			for q in pts:
				near = near or q.distance_to(want) <= 0.5
				near_flat = near_flat or q.distance_to(flat) <= 0.5
			matched += 1 if near else 0
			flat_matched += 1 if near_flat else 0
			if k == 36:  # theta 270 deg: the point straight away from the camera
				far_terrain = want.y
				far_flat = flat.y
		_check(matched == SEGMENTS, "S-126: every disc point is the projection of the ground point at ITS terrain height; %d of %d match" % [matched, SEGMENTS])
		_check(far_terrain < far_flat - 1.0 and flat_matched < SEGMENTS, "CONTROL: the far point sits higher on screen than a flat disc puts it (terrain y %.1f, flat y %.1f), and the flat set is not what the polygon holds (%d of %d)" % [far_terrain, far_flat, flat_matched, SEGMENTS])
	host.queue_free()
	fg.queue_free()


# Ramp fixture: unit below the ramp lights nothing past the midline (x = 400); above it, the ramp and the lower ground to full radius.
func _ramp_clip() -> void:
	var t := _terrain("ramp")
	var r = await _rig(t, Vector2(400, 400))
	var host = r[0]
	var fg = r[1]
	_check(fg.has_method("set_terrain"), "VG-A-sightdisc: FogLayer.set_terrain(terrain) exists (interface absent on main)")
	fg.set_frame(_frame([_unit(1, 300, 400, 250, 1)]), {}, 0)
	var d := _discs(fg)
	if d.size() == 1:
		var xs := _world_points(host, _poly(d[0]))
		var max_x := -INF
		var min_x := INF
		for w in xs:
			max_x = maxf(max_x, w.x)
			min_x = minf(min_x, w.x)
		_check(max_x <= 400.0 + CELL, "R-004-06 R-005-09: a unit on the lower band lights no point past the ramp's midline (x 400, one cell of slack); farthest east point at x %.0f (CONTROL: main's full circle reaches 550)" % max_x)
		_check(min_x <= 50.0 + CELL, "R-005-09: the clip leaves the unclipped side whole; westmost point at x %.0f, want about 50" % min_x)
	else:
		_check(false, "R-004-06: no disc for the lower unit")
	fg.set_frame(_frame([_unit(2, 550, 400, 200, 2)]), {}, 0)
	var d2 := _discs(fg)
	if d2.size() == 1:
		var xs2 := _world_points(host, _poly(d2[0]))
		var lo := INF
		var hi := -INF
		for w in xs2:
			lo = minf(lo, w.x)
			hi = maxf(hi, w.x)
		_check(lo <= 350.0 + CELL and hi >= 750.0 - CELL, "R-005-09: a unit above the midline sees the ramp and the lower ground to its full radius (x 350 to 750, one cell of slack); reads %.0f to %.0f" % [lo, hi])
	else:
		_check(false, "R-005-09: no disc for the upper unit")
	host.queue_free()
	fg.queue_free()


# Space path (no ground host, flat set_frame): (p - camera) * world_scale + half, no terrain; the 48 points form the old circle.
func _space_path() -> void:
	var fg = load(FOG).new()
	root.add_child(fg)
	await process_frame
	var scale := 0.25
	var cam := Vector2(2000, 2000)
	fg.set_frame(_frame([_unit(1, 1500, 1500, 800)]), 0, scale, cam)
	var d := _discs(fg)
	if d.size() == 1 and d[0].has("points"):
		var p: PackedVector2Array = d[0]["points"]
		var c := _area_centroid(p)
		var far := 0.0
		for q in p:
			far = maxf(far, q.distance_to(c))
		var b := _bbox(p)
		_check(p.size() == SEGMENTS and absf(far - 800.0 * scale) <= 0.5, "S-126: space path, the farthest point from the centroid is sight x world_scale (200) within 0.5 px, reads %.2f over %d points" % [far, p.size()])
		_check(absf(b.size.y / b.size.x - 1.0) <= 0.02, "S-126: space path, the disc is a circle (ratio 1.0 within 0.02), reads %.3f" % (b.size.y / b.size.x))
		var half := get_root().get_visible_rect().size * 0.5
		_check(c.distance_to((Vector2(1500, 1500) - cam) * scale + half) <= 0.5, "S-126: space path, the disc is centred on (p - camera) * world_scale + half, centroid %s" % c)
	else:
		_check(false, "S-126: space path disc polygon missing (interface absent on main)")
	fg.queue_free()


# Mask control: inside the polygon lit, outside dimmed. Structural (a SubViewport under the FogLayer) always; pixels with a renderer.
func _mask() -> void:
	var back := ColorRect.new()
	back.color = Color.WHITE
	back.size = get_root().get_visible_rect().size
	root.add_child(back)
	var fg = load(FOG).new()
	root.add_child(fg)
	await process_frame
	var scale := 0.25
	fg.set_frame(_frame([_unit(1, 2000, 2000, 400)]), 0, scale, Vector2(2000, 2000))
	for i in 3:
		await process_frame
	_check(fg.find_children("*", "SubViewport", true, false).size() >= 1, "R-089-03: the fog mask is drawn into a SubViewport under the FogLayer (absent on main)")
	if DisplayServer.get_name() == "headless":
		print("MASK-PIXELS: not sampled (headless, dummy renderer)")
	else:
		var img: Image = get_root().get_texture().get_image()
		# The captured image can differ in size from the visible rect (xvfb), so points are taken as fractions of the rect.
		var vis := get_root().get_visible_rect().size
		var to_px := Vector2(img.get_size()) / vis
		var inside := img.get_pixelv(Vector2i(vis * 0.5 * to_px))
		var outside := img.get_pixelv(Vector2i((vis * 0.5 + Vector2(120, 0)) * to_px))
		_check(inside.r > 0.95, "R-089-03: a point inside the polygon is lit (backdrop white), reads %s" % inside)
		_check(outside.r < 0.60 and outside.r > 0.30, "R-089-03: a point outside the polygon is dimmed (white under alpha 0.55 reads about 0.45), reads %s" % outside)
	back.queue_free()
	fg.queue_free()


# The screen-circle path is deleted, not left beside the new one.
func _deletion() -> void:
	var src := FileAccess.get_file_as_string(FOG)
	_check(not src.contains("\"radius\"") and not src.contains("\"center\""), "VG-A-sightdisc: fog_layer.gd still holds the centre-and-radius disc field (CONTROL: main fails this)")
	_check(not src.contains("disc_tex") and not src.contains("texelFetch") and not src.contains("FORMAT_RGBF"), "VG-A-sightdisc: fog_layer.gd still declares the one-row float texture (disc_tex / texelFetch / FORMAT_RGBF)")
	_check(not src.contains("uniform int count"), "VG-A-sightdisc: the shader still declares the hole-punch loop's count uniform")


# --- near-plane clip (fix brief 2026-10-23) -----------------------------------------------------------------------------------
# Rule pins for these tests are the file's: R-089-03 (the disc draws only what R-089-03 computes, so points behind the camera must not corrupt it).

func _clip(pts: PackedVector3Array, plane: Plane) -> Variant:
	var path := OS.get_environment("OM_CLIP_HELPER")
	var g = load(path if path != "" else FOG)
	if g == null or not g.has_method("clip_to_plane"):
		_check(false, "VG-A-sightdisc: FogLayer.clip_to_plane(pts, plane) does not exist (helper not built)")
		return null
	return g.clip_to_plane(pts, plane)


func _square(z0: float, z1: float) -> PackedVector3Array:
	return PackedVector3Array([Vector3(0, 0, z0), Vector3(10, 0, z0), Vector3(10, 0, z1), Vector3(0, 0, z1)])


func _clip_tests() -> void:
	var plane := Plane(Vector3(0, 0, 1), 0.0)  # in front is z >= 0
	# test_clip_keeps_front_points
	var front := _square(1.0, 3.0)
	var r1 = _clip(front, plane)
	if r1 != null:
		_check(r1.size() == 4, "test_clip_keeps_front_points: %d points came back, want the 4 in front unchanged" % r1.size())
		if r1.size() == 4:
			var same: bool = true
			for k in 4:
				same = same and r1[k].distance_to(front[k]) < 0.001
			_check(same, "test_clip_keeps_front_points: the four front points changed: %s" % [r1])
	# test_clip_cuts_crossing_edges
	var r2 = _clip(_square(-1.0, 1.0), plane)
	if r2 != null:
		var all_front: bool = r2.size() >= 3
		var on_plane := 0
		for p in r2:
			all_front = all_front and plane.distance_to(p) >= -0.001
			if absf(plane.distance_to(p)) < 0.001:
				on_plane += 1
		_check(all_front, "test_clip_cuts_crossing_edges: %d points, a point lies behind the plane (or fewer than 3 came back): %s" % [r2.size(), r2])
		_check(on_plane == 2, "test_clip_cuts_crossing_edges: %d points on the plane, want the 2 intersection points" % on_plane)
	# test_clip_behind_is_empty
	var r3 = _clip(_square(-3.0, -1.0), plane)
	if r3 != null:
		_check(r3.size() == 0, "test_clip_behind_is_empty: %d points came back, want an empty array" % r3.size())


const LC_OWN := [
	[1, 12220.0, 920.0], [2, 12250.0, 920.0], [3, 12280.0, 920.0], [4, 12220.0, 950.0], [5, 12250.0, 950.0], [6, 12280.0, 950.0],
	[7, 12220.0, 980.0], [8, 12250.0, 980.0], [9, 12280.0, 980.0], [10, 12320.0, 920.0], [11, 12350.0, 920.0], [12, 12380.0, 920.0]]


func _lc_terrain() -> Dictionary:
	var n := 240
	var heights := PackedInt32Array()
	var bands := PackedByteArray()
	var walk := PackedByteArray()
	for j in n:
		for i in n:
			heights.append(i * 12 + j * 7 + (300 if (i / 10 + j / 10) % 2 == 0 else 0))
			bands.append(3)
			walk.append(1)
	return {"cells_w": n, "cells_h": n, "bands": bands, "walkable": walk, "heights": heights, "slopes": [],
		"layer_floors_wu": [0.0, 150.0, 300.0, 450.0, 600.0], "flyer_types": []}


func _lc_frame(tick: int) -> Dictionary:
	var units := []
	var ids := []
	for p in LC_OWN:
		units.append({"id": p[0], "faction": 0, "type": 0, "tier": 1, "x": p[1], "y": p[2], "hp": 250, "layer": 2, "facing": 0.0,
			"target": -1, "state": 0, "sight": 800})
		ids.append(p[0])
	var profiles := []
	for t in 6:
		profiles.append({"type": t, "max_hp": 250, "range": 200, "interval": 1.0, "sensor": 800, "ability": t, "acd_max": 1500, "aoe": 0})
	return {"type": "tactical", "tick": tick, "player_faction": 0, "mission_over": false, "units": units, "structures": [],
		"visible": {"0": ids}, "profiles": profiles, "events": [], "objectives": [],
		"map": {"canvas": 24000.0, "nodes": [], "cover": [], "obstacles": []}}


# test_low_camera_boxes_not_all_full_width. Positive control: the height-3000 half is green on 743e4f35.
func _low_camera() -> void:
	var cfg = root.get_node("EraConfig")
	var d = load("res://autoload/qa_daemon.gd").new()
	root.add_child(d)
	await process_frame
	cfg.set_era(cfg.GROUND_ERA_ID)
	var v: Node = (load("res://scenes/tactical_c/tactical_view.tscn") as PackedScene).instantiate()
	root.add_child(v)
	current_scene = v
	await process_frame
	v.set_process(false)
	await process_frame
	cfg.set_era(cfg.GROUND_ERA_ID)
	v.load_frame(_lc_frame(0))
	v.set_terrain(_lc_terrain())
	await process_frame
	v.load_frame(_lc_frame(1))
	await process_frame
	var vp: Vector2 = Ground3D.SCREEN_SIZE
	var high: Dictionary = v.qa_state().get("sight_discs", {})
	var inside: bool = high.size() == 12
	for k in high:
		var b = high[k]
		inside = inside and b is Array and b.size() == 4 and b[0] >= 0.0 and b[1] >= 0.0 and b[0] + b[2] <= vp.x and b[1] + b[3] <= vp.y
	_check(inside, "test_low_camera_boxes_not_all_full_width: at height 3000 sight_discs has %d entries (want 12), every box inside the viewport: %s" % [high.size(), high])
	var r: Dictionary = await d._dispatch("camera_set", [{"height": 300.0}])
	_check(bool(r.get("ok", false)), "test_low_camera_boxes_not_all_full_width: camera_set height 300 answered %s" % [r])
	await process_frame
	var low: Dictionary = v.qa_state().get("sight_discs", {})
	var narrow := 0
	var first = null
	for k in low:
		var b = low[k]
		if first == null:
			first = b
		if b is Array and b.size() == 4 and float(b[2]) < vp.x:
			narrow += 1
	_check(narrow >= 1, "test_low_camera_boxes_not_all_full_width: at height 300 none of %d sight_discs boxes has w < %s (every box is full width, e.g. %s)" % [low.size(), vp.x, first])
	v.queue_free()
	current_scene = null
	await process_frame
