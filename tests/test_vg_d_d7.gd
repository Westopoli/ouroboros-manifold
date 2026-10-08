extends "res://tests/support/vg_c_case.gd"

# Visible-game lane D piece D7 (docs/northstar/plans/2026-10-07-visible-game-spec.md rev 4, lane D): the space field drawn as
# stacked 3D sheets under Ground3D's SubViewport (after C5), with the simple vision tube. Proves S-246 R-246-02
# (placeholder meteors fill the blocked space across layers, the layers are visibly separated), R-246-03 (drawn from the
# masks plus polygons of space_field(), K-d), R-246-04 (the tube: covering layers cut away around the cursor and the
# selection, the two-circle transition cue of the layers mockup, Q-S3-02), Q-009-02 (the tube makes hidden units
# visible; no occlusion mark), Q-166-06, Q-166-07, E-01 R-001-04. Fenced: builders never edit this file.
#
# DRAFT API (flagged in the report; the spec names no D7 file or method, the builder follows these names):
#   res://scenes/ground3d/space_sheets.gd, a Node3D (world 1 wu = 1 unit, sim (x, y) -> 3D (x, height, y), as the C3 rig):
#     set_field(field)        field = c_bridge.space_field(): {cells_w, cells_h, layers, masks: 5 x PackedByteArray (LSB
#                             first, 1 = blocked), polys: [{layer 0-based, kind 0 plate / 1 mass / 2 rubble, points}]}
#     layer_y(layer) -> float            layer is 0-based; (k-1) x 1000 for the 1-based k, layer_y(0) == 0
#     sheet_meshes(layer) -> Array       MeshInstance3D children for that layer; meta "sheet_kind" is "sheet" (plates and
#                                        rubble, as the prototype), "mass" or "wall"; position.y == layer_y(layer)
#     meteors() -> Array                 [{x, y (wu centre), y_min, y_max (3D heights), radius}] filling blocked space
#     set_tube(foci: Array, radius: float)   foci = [{x, y, layer}] (cursor, selection); layers ABOVE a focus layer are cut
#     is_cut(layer, wx, wy) -> bool      true inside a tube on a layer above that focus's layer
#     unit_visible(layer, wx, wy) -> bool   false only when a blocked cell on a higher layer covers (wx, wy) and no tube cuts it
#     occlusion_mark_count() -> int      0 always (Q-009-02: no mark for the beta)
#     set_transition(unit_xy: Vector2, own_layer, target_layer)   child rings "SensorOwn" (follows the unit, at its
#                             layer's height) and "SensorOther" (at the exact height of the target layer); no "SensorOther"
#                             visible when own_layer == target_layer
#   scenes/ground3d/ground3d.gd gains set_space_field(field), space_sheets() (a node inside the SubViewport) and
#   qa_state()["space3d"] = {present, layers, layer_y: [5 floats], sheets, meteors, tube: {active, radius, cut_layers},
#   occlusion_marks, cue: {own, other}}.
# "(control)" checks pass on main and prove the harness; on main none of the files exist, so the rest are red.

const DIM := 240
const CELL := 100.0
const PATH := "res://scenes/ground3d/space_sheets.gd"
const TRI := [Vector2(130, 130), Vector2(470, 210), Vector2(250, 480)]
const SQ := [Vector2(1000, 1000), Vector2(1400, 1000), Vector2(1400, 1400), Vector2(1000, 1400)]
const SQ0 := [Vector2(2000, 2000), Vector2(2400, 2000), Vector2(2400, 2400), Vector2(2000, 2400)]
const PLATE_H := 60.0
const RUBBLE_H := 30.0

var _blocked: Array = [{}, {}, {}, {}, {}]   # per layer: cell index -> true


func _inside(p: Vector2, poly: Array) -> bool:
	var c := false
	var j := poly.size() - 1
	for i in range(poly.size()):
		var a: Vector2 = poly[i]
		var b: Vector2 = poly[j]
		if (a.y > p.y) != (b.y > p.y) and p.x < (b.x - a.x) * (p.y - a.y) / (b.y - a.y) + a.x:
			c = not c
		j = i
	return c


func _raster(layer: int, poly: Array) -> void:
	for j in range(DIM):
		for i in range(DIM):
			if _inside(Vector2((i + 0.5) * CELL, (j + 0.5) * CELL), poly):
				_blocked[layer][j * DIM + i] = true


func _field() -> Dictionary:
	_blocked = [{}, {}, {}, {}, {}]
	_raster(1, TRI)
	_raster(2, SQ)
	_raster(3, SQ)
	_raster(0, SQ0)   # blocked on layer 0 by mask only, no polygon (a pocket)
	var masks := []
	for k in range(5):
		var b := PackedByteArray()
		b.resize(DIM * DIM / 8)
		for idx in _blocked[k].keys():
			b[idx >> 3] = b[idx >> 3] | (1 << (idx & 7))
		masks.append(b)
	var polys := [
		{"layer": 1, "kind": 0, "points": PackedVector2Array(TRI)},
		{"layer": 2, "kind": 1, "points": PackedVector2Array(SQ)},
		{"layer": 3, "kind": 2, "points": PackedVector2Array(SQ)},
	]
	return {"cells_w": DIM, "cells_h": DIM, "layers": 5, "masks": masks, "polys": polys}


func _cell(wx: float, wy: float) -> int:
	return int(wy / CELL) * DIM + int(wx / CELL)


func _verts(m: Mesh) -> PackedVector3Array:
	var out := PackedVector3Array()
	for s in range(m.get_surface_count()):
		out.append_array(m.surface_get_arrays(s)[Mesh.ARRAY_VERTEX])
	return out


func _kind(s, layer: int, kind: String) -> MeshInstance3D:
	for mi in s.sheet_meshes(layer):
		if (mi as Node).get_meta("sheet_kind", "") == kind:
			return mi
	return null


func _run() -> void:
	var f := _field()
	# CONTROL: the fixture polygon is not cell-aligned, so a mask-only drawing would differ from the polygon drawing.
	_check(Rect2(130, 130, 340, 350).position.x != 100.0, "CONTROL: fixture triangle is cell-aligned")
	_check(_blocked[1].size() > 0 and _blocked[2].size() > 0 and _blocked[0].size() == 16, "CONTROL: fixture masks empty or wrong (layer0=%d)" % _blocked[0].size())
	var ss := _load(PATH)
	var hs := _load(SCENES + "ground3d.gd")
	if ss != null:
		await _sheets(ss, f)
	if hs != null:
		await _host(hs, f)


func _sheets(ss: GDScript, f: Dictionary) -> void:
	var s = ss.new()
	root.add_child(s)
	await process_frame
	for m in ["set_field", "layer_y", "sheet_meshes", "meteors", "set_tube", "is_cut", "unit_visible", "occlusion_mark_count", "set_transition"]:
		_check(s.has_method(m), "D7: space_sheets.gd lacks %s()" % m)
		if not s.has_method(m):
			return
	s.set_field(f)

	# visible separation: layer k at y = (k-1) x 1000 wu (Q-STAGE3-03 b, R-246-02)
	for k in range(5):
		_check(is_equal_approx(float(s.layer_y(k)), k * 1000.0), "R-246-02: layer_y(%d) = %s, want %s" % [k, s.layer_y(k), k * 1000.0])
	for k in [0, 1, 2, 3]:
		for mi in s.sheet_meshes(k):
			_check(is_equal_approx((mi as MeshInstance3D).position.y, k * 1000.0), "R-246-02: layer %d sheet at y %s, not %s" % [k, (mi as MeshInstance3D).position.y, k * 1000.0])

	# plates: opaque flat-colour meshes from the polygons, no stair-step (Q-166-06 b)
	var plate := _kind(s, 1, "sheet")
	_check(plate != null, "R-246-03: layer 1 has no 'sheet' mesh for its plate polygon")
	if plate != null:
		var mat = plate.material_override
		_check(mat is StandardMaterial3D, "R-246-02: plate material is not a flat StandardMaterial3D")
		if mat is StandardMaterial3D:
			_check(mat.transparency == BaseMaterial3D.TRANSPARENCY_DISABLED and is_equal_approx(mat.albedo_color.a, 1.0), "R-246-02: plate sheet is not opaque")
			_check(mat.albedo_texture == null, "R-246-02: plate sheet is not flat colour (has a texture)")
		var vs := _verts(plate.mesh)
		for p in TRI:
			var hit := false
			for v in vs:
				if absf(v.x - p.x) < 0.5 and absf(v.z - p.y) < 0.5:
					hit = true
					break
			_check(hit, "Q-166-06: no mesh vertex at polygon point %s (stair-stepped from the mask?)" % p)
		var bb: AABB = plate.mesh.get_aabb()
		_check(absf(bb.position.x - 130.0) < 1.0 and absf(bb.end.x - 470.0) < 1.0 and absf(bb.position.z - 130.0) < 1.0 and absf(bb.end.z - 480.0) < 1.0,
			"Q-166-06: plate mesh extent %s is not the polygon's (130..470 x 130..480)" % bb)
		_check(absf(bb.size.y - PLATE_H) < 1.0, "R-246-02: plate thickness %s, kit says %s" % [bb.size.y, PLATE_H])
	var rub := _kind(s, 3, "sheet")
	_check(rub != null and absf(rub.mesh.get_aabb().size.y - RUBBLE_H) < 1.0, "R-246-02: rubble sheet missing or not the kit's 30 wu thick")

	# mass as walls: a mass polygon is a raised block with vertical faces
	var mass := _kind(s, 2, "mass")
	_check(mass != null, "R-246-02: layer 2 has no 'mass' mesh for its mass polygon")
	if mass != null:
		var bm: AABB = mass.mesh.get_aabb()
		_check(bm.size.y >= PLATE_H - 1.0, "R-246-02: mass block %s is not a wall (rises less than a plate)" % bm)
		_check(absf(bm.position.x - 1000.0) < 1.0 and absf(bm.end.x - 1400.0) < 1.0, "R-246-03: mass extent %s not the polygon's" % bm)
	# CONTROL: an empty layer has no sheet meshes (the drawing is not a plane on every layer)
	_check(s.sheet_meshes(4).is_empty(), "CONTROL/R-246-02: layer 4 is empty yet has sheet meshes (a plane per layer)")

	# placeholder meteors fill the blocked space across layers (R-246-02)
	var ms: Array = s.meteors()
	_check(ms.size() > 0, "R-246-02: no placeholder meteors")
	var uncovered := 0
	for k in range(5):
		for idx in _blocked[k].keys():
			var cx: float = (idx % DIM + 0.5) * CELL
			var cy: float = (idx / DIM + 0.5) * CELL
			var ok := false
			for m in ms:
				if Vector2(m["x"] - cx, m["y"] - cy).length() <= float(m["radius"]) + 71.0 and float(m["y_min"]) <= k * 1000.0 and float(m["y_max"]) >= k * 1000.0:
					ok = true
					break
			if not ok:
				uncovered += 1
	_check(uncovered == 0, "R-246-02: %d blocked cells have no meteor at their layer height" % uncovered)
	var stray := 0
	var pocket_reaches_up := false
	var spans := false
	for m in ms:
		var c: int = _cell(m["x"], m["y"])
		var any := false
		for k in range(5):
			if _blocked[k].has(c) and float(m["y_min"]) <= k * 1000.0 and float(m["y_max"]) >= k * 1000.0:
				any = true
		if not any:
			stray += 1
		if absf(m["x"] - 2200.0) < 300.0 and absf(m["y"] - 2200.0) < 300.0 and float(m["y_max"]) >= 1000.0:
			pocket_reaches_up = true
		if absf(m["x"] - 1200.0) < 300.0 and absf(m["y"] - 1200.0) < 300.0 and float(m["y_min"]) <= 2000.0 and float(m["y_max"]) >= 3000.0:
			spans = true
	_check(stray == 0, "R-246-02: %d meteors stand on cells blocked on no layer in their height range" % stray)
	_check(not pocket_reaches_up, "R-246-02 (control): a meteor over a layer-0-only pocket reaches layer 1's height, filling open space")
	_check(spans, "R-246-02: no single meteor spans layers 2 and 3 where the column is blocked on both (not filled across layers)")

	# the vision tube (R-246-04): covering layers cut away around the focus
	s.set_tube([], 400.0)
	_check(not s.is_cut(2, 1200.0, 1200.0), "CONTROL: a layer is cut with no tube")
	s.set_tube([{"x": 1200.0, "y": 1200.0, "layer": 1}], 400.0)
	_check(s.is_cut(2, 1200.0, 1200.0) and s.is_cut(3, 1200.0, 1200.0) and s.is_cut(4, 1200.0, 1200.0), "R-246-04: layers above the focus are not cut at its centre")
	_check(s.is_cut(2, 1590.0, 1200.0) and not s.is_cut(2, 1610.0, 1200.0), "R-246-04: the cut edge is not at the tube radius (400 wu)")
	_check(not s.is_cut(1, 1200.0, 1200.0) and not s.is_cut(0, 1200.0, 1200.0), "R-246-04: the focus layer or one below it was cut away")
	s.set_tube([{"x": 3000.0, "y": 3000.0, "layer": 4}], 400.0)
	_check(not s.is_cut(4, 3000.0, 3000.0), "CONTROL: a focus on the top layer cuts away its own layer")
	s.set_tube([{"x": 1200.0, "y": 1200.0, "layer": 1}, {"x": 3000.0, "y": 3000.0, "layer": 2}], 400.0)
	_check(s.is_cut(2, 1200.0, 1200.0) and s.is_cut(3, 3000.0, 3000.0) and not s.is_cut(2, 3000.0, 3000.0), "R-246-04: cursor and selection foci do not both cut (or the second cuts its own layer)")

	# hidden units become visible inside the tube; no occlusion mark (Q-009-02)
	s.set_tube([], 400.0)
	_check(not s.unit_visible(1, 1200.0, 1200.0), "CONTROL/Q-009-02: a unit under a blocked upper column is visible with no tube")
	_check(s.unit_visible(1, 3000.0, 3000.0), "CONTROL: a unit under open space reads hidden")
	_check(s.unit_visible(3, 1200.0, 1200.0), "CONTROL: a unit on the blocked layer itself reads hidden")
	s.set_tube([{"x": 1200.0, "y": 1200.0, "layer": 1}], 400.0)
	_check(s.unit_visible(1, 1200.0, 1200.0), "Q-009-02: the tube does not reveal a hidden unit")
	s.set_tube([{"x": 1200.0, "y": 1200.0, "layer": 4}], 400.0)
	_check(not s.unit_visible(1, 1200.0, 1200.0), "CONTROL/Q-009-02: a tube focused above the unit reveals it")
	_check(s.occlusion_mark_count() == 0, "Q-009-02: an occlusion mark is drawn (post-beta)")

	# the two-circle transition cue (Q-S3-02)
	s.set_transition(Vector2(1200.0, 1200.0), 1, 3)
	var own: Node3D = s.find_child("SensorOwn", true, false)
	var other: Node3D = s.find_child("SensorOther", true, false)
	_check(own != null and other != null, "Q-S3-02: the rings SensorOwn/SensorOther are missing")
	if own != null and other != null:
		_check(own.visible and other.visible, "Q-S3-02: the rings are not both shown for a layer change")
		_check(own.position.distance_to(Vector3(1200.0, 1000.0, 1200.0)) < 1.0, "Q-S3-02: SensorOwn at %s, want the unit's xy on its own layer height" % own.position)
		_check(is_equal_approx(other.position.y, 3000.0), "Q-S3-02: SensorOther at y %s, not the exact height of the target layer (3000)" % other.position.y)
		s.set_transition(Vector2(1500.0, 1300.0), 1, 3)
		_check(own.position.distance_to(Vector3(1500.0, 1000.0, 1300.0)) < 1.0, "Q-S3-02: SensorOwn does not move with the unit")
		_check(is_equal_approx(other.position.y, 3000.0), "Q-S3-02: SensorOther left the target layer's height when the unit moved")
		s.set_transition(Vector2(1500.0, 1300.0), 1, 1)
		_check(not other.visible and own.visible, "CONTROL/Q-S3-02: the second ring shows when the unit is not changing layer")
	s.queue_free()


func _host(hs: GDScript, f: Dictionary) -> void:
	var host = hs.new()
	root.add_child(host)
	await process_frame
	for m in ["set_space_field", "space_sheets"]:
		_check(host.has_method(m), "D7: ground3d.gd lacks %s()" % m)
		if not host.has_method(m):
			return
	var before: Dictionary = host.qa_state().get("space3d", {})
	_check(not bool(before.get("present", false)), "CONTROL: space3d.present is true with no field")
	host.set_space_field(f)
	var sh = host.space_sheets()
	_check(sh != null and sh.get_viewport() is SubViewport and sh.get_viewport() != root, "S-246: the sheets are not inside Ground3D's SubViewport")
	var q: Dictionary = host.qa_state().get("space3d", {})
	_check(bool(q.get("present", false)), "S-246: qa_state.space3d.present false after set_space_field; keys %s" % [q.keys()])
	_check(int(q.get("layers", 0)) == 5, "R-001-04: space3d.layers is not 5")
	var ly: Array = q.get("layer_y", [])
	_check(ly.size() == 5 and absf(float(ly[4]) - 4000.0) < 0.5 and absf(float(ly[1]) - 1000.0) < 0.5, "R-246-02: space3d.layer_y %s is not (k-1) x 1000" % [ly])
	_check(int(q.get("sheets", 0)) >= 4 and int(q.get("meteors", 0)) > 0, "R-246-02: space3d sheets/meteors counts missing (%s)" % [q])
	_check(int(q.get("occlusion_marks", -1)) == 0, "Q-009-02: space3d.occlusion_marks is not 0")
	_check(q.has("cue") and q.has("tube"), "R-246-04: space3d lacks tube/cue blocks")
	if sh != null:
		sh.set_tube([{"x": 1200.0, "y": 1200.0, "layer": 1}], 400.0)
		var t: Dictionary = host.qa_state().get("space3d", {}).get("tube", {})
		_check(bool(t.get("active", false)) and is_equal_approx(float(t.get("radius", 0.0)), 400.0), "R-246-04: space3d.tube not active at 400 wu: %s" % [t])
		var cl: Array = t.get("cut_layers", [])
		cl = cl.map(func(v): return int(v))
		cl.sort()
		_check(cl == [2, 3, 4], "R-246-04: tube.cut_layers %s, want [2, 3, 4]" % [cl])
		sh.set_tube([], 400.0)
		_check(not bool(host.qa_state().get("space3d", {}).get("tube", {}).get("active", true)), "CONTROL: tube still active after clearing")
	host.set_space_field({})
	_check(not bool(host.qa_state().get("space3d", {}).get("present", false)), "S-246: space3d.present stays true after an empty field (a ground mission follows)")
	host.queue_free()
