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
#  - qa_state()["sight_discs"] (ruling 2026-10-23): the key is added EMPTY by VG-C-land-one-projection and FILLED by this piece.
#    UNSTATED INTERFACE choice: a Dictionary keyed by the decimal-string unit id ("1", "2"), each value a bbox [x, y, w, h] (four
#    numbers, w and h > 0). The view is the tactical_view scene fed by load_frame(frame) with two own units. On main the key is
#    absent: red for reason (b). The test therefore needs the land-one-projection build under it before it can go green.
#
# Red reasons: (a) behaviour is wrong on main (a number or pixel differs); (b) the interface the piece adds is absent on main.
# Three assertions passed on main without discriminating (Architect ruling 2026-10-23); what each became:
#  1. pitch-90 ratio: the old assertion read the fallback circle, which is 1.0 on main. Now it reads `points` only (no fallback)
#     and also asserts the 48 points equal the circle set theta k within 0.5 px: red on main for (b). Kept at pitch 90.
#  2. unit above the midline: the extent check (x 350 to 750) is a full circle on main. Added: its points sit at their terrain
#     heights (every polygon point within 0.5 px of Ground3DHost.to_screen of the ground point, the lower ground at height 0 while
#     the unit stands at 300), read through the fallback circle too: red on main for (a) (the circle is at the unit's height all
#     round). The extent check is kept as the unclipped-looking-down control.
#  3. mask pixels: the old flat-path samples (centre lit, 120 px out dimmed) hold for main's circle too, so they are DROPPED.
#     Replaced by a ground-path sample: host hidden, white backdrop, a point on the vertical axis between the projected ellipse
#     edge and main's averaged-radius circle edge must be dimmed (main lights it): red on main for (a) under the renderer. A
#     point at half the ellipse's vertical radius must be lit (control, green on main). Headless: not sampled.
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


func host_to_screen(host, x: float, y: float) -> Vector2:
	return host.to_screen(x, y)


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
	await _qa_discs()
	_deletion()


func _ratio_and_close() -> void:
	for case in [["pitch 50 (the 3D rig's pitch)", false, SIN50, RATIO_TOL_50], ["pitch 90 (top down)", true, 1.0, RATIO_TOL_90]]:
		var r = await _rig(_terrain("flat"), Vector2(400, 400), 0, case[1])
		var fg = r[1]
		fg.set_frame(_frame([_unit(1, 400, 400, 300)]), {}, 0)
		var d := _discs(fg)
		_check(d.size() == 1, "S-126: one disc per own unit, got %d" % d.size())
		if d.size() == 1:
			var has_pts: bool = d[0].has("points") and (d[0]["points"] as PackedVector2Array).size() > 2
			var b := _bbox(_poly(d[0]))
			var ratio := b.size.y / maxf(b.size.x, 0.001)
			_check(has_pts and absf(ratio - case[2]) <= case[3], "S-126 R-089-03: bbox height over width at %s must be %.3f +- %.2f, reads %.3f (CONTROL: main reads 1.0 at pitch 50; no `points` fails (b))" % [case[0], case[2], case[3], ratio])
			_check(d[0].has("points") and (d[0]["points"] as PackedVector2Array).size() == SEGMENTS, "S-126: a disc is {points} of %d screen points (interface absent on main)" % SEGMENTS)
			if case[1]:
				var ctr: Vector2 = host_to_screen(r[0], 400, 400)
				var rad: float = (host_to_screen(r[0], 700, 400) - ctr).x
				var ok := has_pts and (d[0]["points"] as PackedVector2Array).size() == SEGMENTS
				if ok:
					for k in SEGMENTS:
						var want := ctr + Vector2(cos(TAU * k / SEGMENTS), sin(TAU * k / SEGMENTS)) * rad
						var hit := false
						for q in (d[0]["points"] as PackedVector2Array):
							hit = hit or q.distance_to(want) <= 0.5
						ok = ok and hit
				_check(ok, "S-126: at pitch 90 the 48 points are the circle theta k of radius sight x px-per-wu (%.1f px) round the unit, each within 0.5 px (interface absent on main (b))" % rad)
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
		_check(lo <= 350.0 + CELL and hi >= 750.0 - CELL, "R-005-09: a unit above the midline sees the ramp and the lower ground to its full radius (x 350 to 750, one cell of slack); reads %.0f to %.0f (control, green on main)" % [lo, hi])
		# Reason (a): the lower ground west of the midline is at height 0, the unit at 300; the polygon point for theta 180 deg
		# (ground (350, 400)) is the projection at the terrain height, not at the unit's height (main's circle is at the unit's).
		var want: Vector2 = host.to_screen(350.0, 400.0)
		var near := false
		for q in _poly(d2[0]):
			near = near or q.distance_to(want) <= 0.5
		_check(near and d2[0].has("points"), "R-005-09: the upper unit's disc point over the lower ground (350, 400) is the projection at that ground's height, screen %s (red on main for (a): the circle sits at the unit's height)" % want)
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
		await _mask_pixels()
	fg.queue_free()


# qa_state()["sight_discs"] (ruling 2026-10-23, shape in the header): per own unit a bbox [x, y, w, h], w and h > 0. Red on main (b).
func _qa_discs() -> void:
	var v: Node = load("res://scenes/tactical_c/tactical_view.tscn").instantiate()
	get_root().add_child(v)
	await process_frame
	v.set_process(false)
	await process_frame
	var f := _frame([_unit(1, 400, 400, 300), _unit(2, 600, 500, 250)])
	v.load_frame(f)
	await process_frame
	var st: Dictionary = v.qa_state()
	var inv = st.get("inventory", st)
	var sd = inv.get("sight_discs") if inv is Dictionary else null
	_check(sd is Dictionary, "S-126: qa_state()[\"sight_discs\"] is present as a Dictionary keyed by unit id (absent on main (b); filled by this piece, the key is added by VG-C-land-one-projection, so that build must be under this test)")
	if sd is Dictionary:
		_check(sd.size() == 2 and sd.has("1") and sd.has("2"), "S-126: sight_discs has an entry per own unit (\"1\", \"2\"), keys %s" % [sd.keys()])
		for k in sd:
			var bb = sd[k]
			_check(bb is Array and bb.size() == 4 and float(bb[2]) > 0.0 and float(bb[3]) > 0.0, "S-126: sight_discs[%s] is a non-empty screen bbox [x, y, w, h], reads %s" % [k, bb])
	v.queue_free()


# Ground path under a renderer: host hidden so only the white backdrop and the fog mask show. The unit's ground disc at pitch 50 is
# an ellipse with vertical radius ry < rx; main's averaged-radius circle reaches (rx + ry) / 2 > ry, so a point between is dimmed
# by the polygon mask and lit by main.
func _mask_pixels() -> void:
	var back := ColorRect.new()
	back.color = Color.WHITE
	back.size = get_root().get_visible_rect().size
	root.add_child(back)
	var r = await _rig(_terrain("flat"), Vector2(400, 400))
	var host = r[0]
	var fg = r[1]
	for c in host.get_children():
		if c is Node3D or c is CanvasItem:
			c.visible = false
	fg.set_frame(_frame([_unit(1, 400, 400, 300)]), {}, 0)
	for i in 3:
		await process_frame
	var ctr: Vector2 = host.to_screen(400, 400)
	var ry: float = ctr.y - host.to_screen(400, 100).y
	var rx: float = host.to_screen(700, 400).x - ctr.x
	var vis := get_root().get_visible_rect().size
	var img: Image = get_root().get_texture().get_image()
	var to_px := Vector2(img.get_size()) / vis
	var inside := img.get_pixelv(Vector2i((ctr + Vector2(0, ry * 0.5)) * to_px))
	var between_y := ry + 0.5 * ((rx + ry) * 0.5 - ry)
	var outside := img.get_pixelv(Vector2i((ctr + Vector2(0, between_y)) * to_px))
	_check(inside.r > 0.95, "R-089-03: a point at half the ellipse's vertical radius is lit (control, green on main), reads %s" % inside)
	_check(outside.r < 0.60 and outside.r > 0.30, "R-089-03: a point %.0f px below the unit (ellipse edge %.0f, main's circle edge %.0f) is dimmed (about 0.45), reads %s (red on main for (a))" % [between_y, ry, (rx + ry) * 0.5, outside])
	back.queue_free()
	host.queue_free()
	fg.queue_free()


# The screen-circle path is deleted, not left beside the new one.
func _deletion() -> void:
	var src := FileAccess.get_file_as_string(FOG)
	_check(not src.contains("\"radius\"") and not src.contains("\"center\""), "VG-A-sightdisc: fog_layer.gd still holds the centre-and-radius disc field (CONTROL: main fails this)")
	_check(not src.contains("disc_tex") and not src.contains("texelFetch") and not src.contains("FORMAT_RGBF"), "VG-A-sightdisc: fog_layer.gd still declares the one-row float texture (disc_tex / texelFetch / FORMAT_RGBF)")
	_check(not src.contains("uniform int count"), "VG-A-sightdisc: the shader still declares the hole-punch loop's count uniform")
