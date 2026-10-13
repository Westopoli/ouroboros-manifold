extends "res://tests/support/vg_c_case.gd"
# NEEDS A DISPLAY (MultiMesh transforms read identity under the dummy renderer; FU-B22-pregate-display, E1k extension):
#   xvfb-run -a -s '-screen 0 1920x1080x24' godot.real --path . --resolution 1920x1080 -s res://tests/test_vg_e_e1k.gd

# VG-E piece E1k (scenes/settlement/settlement_layer.gd, class SettlementLayer; scenes/settlement/settlement_look.gd;
# scenes/settlement/settlement_streets.gd). Spec: docs/northstar/plans/2026-10-07-visible-game-spec.md, section Rev 12d
# (2026-10-12), paragraph "E1k numbers". Proves, word for word:
#
# Westley, 2026-10-12, S-237 verdict (spec Rev 12d):
#   [W 2026-10-12 S-237 0402: "Why are units so heavily stacked? On the buildings, it's very uniform, there's no perceptible difference in level between the buildings, and the layout is super uniform and square, not looks like the sister system to the biome engine at all. Not approved yet."]
#   Cases: [STAGE1] [STAGE] [VARIATION] [HEIGHTS] [FOOTPRINT] [RUBBLE] "no perceptible difference in level between the buildings";
#   [JITTER] [YAW] [LANES] "the layout is super uniform and square"; [YAW] [STREET] [STREETFN] "sister system to the biome engine".
#
# Bible E-17 map generation (docs/bible/epics/E-17-map-generation.md):
#   - R-193-01  Given a map, When population density is set, Then it is a growing field on the same field map the landscape uses, and it spreads over the map a little at a time. It is shaped by water, slope and the core's position, so districts follow rivers, coasts and contour lines and never form rings, and walls follow defensible ground.
#   Cases: [YAW] (contour lines, "districts follow rivers, coasts and contour lines"), [LANES].
#   - R-193-02  Given difficult terrain, When density reaches it, Then the field never gives up and the city adapts by placing buildings in wild locations, such as inside a cliff, underneath a waterfall or on a steep mountainside. Difficult ground changes what gets built, not whether anything is. An opening in rock is cosmetic only: the layer mask and the land flag are unchanged (Westley, 2026-10-06).
#   Cases: [CLIFF] (a steep mountainside gets a cliff dwelling; difficult ground changes what gets built, not whether anything is).
#   - R-193-05  Given a lot, When the density at its cell passes a threshold, Then the lot rises through its stages, starting under construction, with a construction animation between stages. There are five stages: empty, staked, scaffold, small and large (Westley, 2026-10-06) [Q-191-05: the thresholds, drafted in the prototype].
#   Cases: [STAGE1] [STAGE] [HEIGHTS] [FOOTPRINT] (the five stages, rising in height), [EASE] (the animation between stages).
#   - R-193-09  Given a settlement, When armies and units cross it, Then there are always natural paths through it, so that the slowing of dense districts is never annoying to the player. The generator leaves open streets along the contour lines and rivers by rule (Westley, 2026-10-06).
#   Cases: [STREET] [STREETFN] (the route mesh joins nearby lots; it is hidden by default, DRAFT-e1k-streets), [LANES] (open lanes between lots).
# Bible E-18 visual style (docs/bible/epics/E-18-visual-style-and-combat-visuals.md):
#   - R-237-01  Given a self-built building, When it first appears, Then it is drawn under construction and rises to complete over time, and nothing about it snaps into place (E-17 R-166-01).
#   Cases: [EASE] (a lot rises over time, the first frame after load excepted), [RUBBLE].
#
# Numbers (spec "E1k numbers"; S = scenes/mockups/settlement/settlement_sim.gd, M = settlement_mockup.gd, FM = scenes/mockups/landscape/field_map.gd).
# One mockup unit = one cell = 100 wu. v = 0.8 + 0.5 * hash(key + 11) [S:304], key = the sim lot id (GAP 3).
# Stage rows [S:305-317], height x v where marked: rubble 0.14 / 0.7; stage 1 0.05 / 0.8; stage 2 0.3v / 0.7; stage 3 0.7v / 0.72;
# stage 4 1.5v / 0.8; stage 5 draws as stage 4 (GAP 6, S:317 default branch); cliff stage 1 0.05 / 0.6, stage 2 0.22 / 0.5, stage 3 0.4v / 0.62
# [S:309-311]. Depth = 0.85 of width [M:251]. Jitter 0.22 cell [S:33, M:248-249]. Yaw: contour atan2(-dx, -dz) + jit where the slope exceeds
# CONTOUR_SLOPE 0.06 [S:32] and |dx|+|dz| > 0, else hash(key+9)*PI + jit, jit = (hash(key+7)-0.5)*2*0.25 [S:34, M:273-280]. Sink 0.12 unit [M:252].
# Cliff: slope > 0.22 [S:19, S:172-173], capped at stage 3 [S:20]. Lanes: LANE_PERIOD 4 [S:35]. Ease: RISE_S 0.9 s per _process delta [S:21, S:320-327].
# Slope formula (GAP 1): mean |dh| over the orthogonal neighbours that exist, cm to wu, / 100 wu per cell, / SLOPE_NORM 6.25, clamped to 1
# [FM:380-402, csrc/economy_density.c:73-90]; on the cm heights of this file that is mean|dh_cm| / 62500.
#
# FIXTURES (40 x 40 cells, heights int32 cm; _ramp(step) and _terrain(true) rise by `step` cm per cell from column 30 on; slope of an
# interior cell on the ramp = step / 62500, computed under the four-neighbour formula):
#   old   (_terrain(true), step 6000):  slope 0.048  (negative control for BOTH thresholds: below 0.06 contour yaw, below 0.22 cliff)
#   yaw   (_ramp(9000)):                slope 0.072  (in (0.06, 0.22): contour yaw, not a cliff)
#   cliff (_ramp(30000)):               slope 0.24   (above 0.22: a cliff dwelling, and above 0.06: contour yaw)
#   flat  (_terrain(false)):            slope 0      (negative control for the yaw rule)
# Grid-edge cells have fewer neighbours (the mean runs over those that exist), so lots sit in the interior, columns 31..38, rows 1..38.
#
# Premises dumped on the skeleton (origin/main 243ed084) with `old`: lots_drawn() keys {id, x, y, stage, building, owner}, e.g.
#   {id: 10, x: 550.0, y: 2050.0, stage: 3, building: 0, owner: 0}; instance_count 3 for 3 lots; instance 1 basis X (100,0,0) Y (0,60,0)
#   Z (0,0,100), origin (3550, 390, 2050) (ground 360 + 30), colour (0.2, 0.6, 1.0, 1.0); the layer has no _process.
#
# Float epsilons are float compares, not thresholds: EPS 0.001 wu for sizes (float32 transforms), POS_EPS 0.01 wu for positions
# (coordinates reach 4000 wu), COL_EPS 0.01 for colours (the MultiMesh stores them in reduced precision), ANG_EPS 0.001 rad for yaw.
#
# Groups (run order): [CONTROL] [SKELETON] [TINT] [STAGE1] [STAGE] [VARIATION] [HEIGHTS] [FOOTPRINT] [RUBBLE] [JITTER] [YAW] [SINK]
# [LANES] [CLIFF] [EASE] [STREET] [LOOKFN] [STREETFN]. Green on the skeleton (controls): CONTROL, SKELETON, TINT, STAGE1 assertion one,
# LANES, the same-key control and the leave-the-frame check. Red until built: everything that reads a size, an offset, a yaw, a look
# function or a street. Stage changes ease by time (RISE_S 0.9 s per _process); the first frame after load snaps, so heights are read
# without driving _process.

const LAYER := "res://scenes/settlement/settlement_layer.gd"
const LOOK := "res://scenes/settlement/settlement_look.gd"
const STREETS := "res://scenes/settlement/settlement_streets.gd"
const MOCK_SIM := "res://scenes/mockups/settlement/settlement_sim.gd"
const STRUCTURES := "res://scenes/tactical_c/structures_layer.gd"
const W := 40
const H := 40
const EPS := 0.001
const POS_EPS := 0.01
const COL_EPS := 0.01
const ANG_EPS := 0.001
const DT := 0.45 # the test's own fixed _process delta: two of them sum to RISE_S 0.9 s exactly (S:21)
const RUBBLE := Color(0.28, 0.2, 0.18) # S:306


func _terrain(steep: bool) -> Dictionary:
	var hs := PackedInt32Array()
	hs.resize(W * H)
	for j in H:
		for i in W:
			hs[j * W + i] = (i - 29) * 6000 if (steep and i >= 30) else 0
	var walk := PackedByteArray()
	walk.resize(W * H)
	walk.fill(1)
	return {"cells_w": W, "cells_h": H, "heights": hs, "walkable": walk, "slopes": []}


# Same shape as _terrain(true) with a chosen step in cm per cell: _ramp(6000) is the old fixture.
func _ramp(step: int) -> Dictionary:
	var t := _terrain(false)
	var hs: PackedInt32Array = t["heights"]
	for j in H:
		for i in range(30, W):
			hs[j * W + i] = (i - 29) * step
	t["heights"] = hs
	return t


# One tall spike at (spike_x, spike_y): slope there is high while dx and dz are both 0.
func _spike(h_cm: int, sx: int, sy: int) -> Dictionary:
	var t := _terrain(false)
	var hs: PackedInt32Array = t["heights"]
	hs[sy * W + sx] = h_cm
	t["heights"] = hs
	return t


func _lot(id: int, cx: int, cy: int, stage: int, owner_id := 0) -> Dictionary:
	return {"id": id, "x": (cx + 0.5) * 100.0, "y": (cy + 0.5) * 100.0, "stage": stage, "building": 0, "owner": owner_id}


# set_terrain, then ONE set_frame: the first frame after load snaps (spec :298, GAP 5), so no loop and no _process is needed.
func _make(script: GDScript, t: Dictionary, lots: Array) -> Node3D:
	var n: Node3D = script.new()
	root.add_child(n)
	n.set_terrain(t)
	n.set_frame({"lots": lots})
	return n


func _mm(n: Node) -> MultiMeshInstance3D:
	for c in n.find_children("*", "MultiMeshInstance3D", true, false):
		return c
	return null


func _tr(n: Node, i: int) -> Transform3D:
	var mm := _mm(n)
	if mm == null or mm.multimesh == null or i >= mm.multimesh.instance_count:
		return Transform3D(Basis.from_scale(Vector3(-1, -1, -1)), Vector3(-1e9, -1e9, -1e9))
	return mm.multimesh.get_instance_transform(i)


func _box_h(n: Node, i: int) -> float:
	var mm := _mm(n)
	if mm == null or mm.multimesh == null or i >= mm.multimesh.instance_count:
		return -1.0
	return mm.multimesh.get_instance_transform(i).basis.y.length()


func _box_w(n: Node, i: int) -> float:
	return _tr(n, i).basis.x.length()


func _box_d(n: Node, i: int) -> float:
	return _tr(n, i).basis.z.length()


# Yaw about +Y: Basis(UP, yaw).x = (cos yaw, 0, -sin yaw).
func _yaw(n: Node, i: int) -> float:
	var b := _tr(n, i).basis
	return atan2(-b.x.z, b.x.x)


func _col(n: Node, i: int) -> Color:
	var mm := _mm(n)
	if mm == null or mm.multimesh == null or i >= mm.multimesh.instance_count:
		return Color(-1, -1, -1, -1)
	return mm.multimesh.get_instance_color(i)


func _close(a: Color, b: Color) -> bool:
	return absf(a.r - b.r) < COL_EPS and absf(a.g - b.g) < COL_EPS and absf(a.b - b.b) < COL_EPS and absf(a.a - b.a) < COL_EPS


func _ribbons(n: Node) -> int:
	var c := 0
	for m in n.find_children("*", "MeshInstance3D", true, false):
		var mesh: Mesh = m.mesh
		if mesh != null and mesh.get_surface_count() > 0 and mesh.surface_get_arrays(0)[Mesh.ARRAY_VERTEX].size() > 0:
			c += 1
	return c


func _ribbons_hidden(n: Node) -> bool:
	var c := 0
	for m in n.find_children("*", "MeshInstance3D", true, false):
		var mesh: Mesh = m.mesh
		if mesh != null and mesh.get_surface_count() > 0 and mesh.surface_get_arrays(0)[Mesh.ARRAY_VERTEX].size() > 0:
			c += 1
			if m.visible:
				return false
	return c > 0


func _find(drawn: Array, id: int) -> Dictionary:
	for d in drawn:
		if int(d.get("id", -1)) == id:
			return d
	return {}


# The N1 hash, copied from S:137-138; [LOOKFN] proves scenes/settlement/settlement_look.gd hash01 equal to the mockup's _hash.
func _hash(i: int) -> float:
	return float(((i * 73856093) ^ (i * 19349663)) & 0xffff) / 65535.0


func _v(id: int) -> float:
	return 0.8 + 0.5 * _hash(id + 11)


# Expected [height_wu, width_wu] of a drawn lot (key = lot id, GAP 3). stage 0 = rubble, stage 5 = the stage-4 row (GAP 6),
# a cliff lot uses the cliff rows (the caller passes the capped stage).
func _row(stage: int, cliff: bool, id: int) -> Array:
	var v := _v(id)
	if stage <= 0:
		return [14.0, 70.0]
	if cliff:
		match stage:
			1:
				return [5.0, 60.0]
			2:
				return [22.0, 50.0]
			_:
				return [40.0 * v, 62.0]
	match stage:
		1:
			return [5.0, 80.0]
		2:
			return [30.0 * v, 70.0]
		3:
			return [70.0 * v, 72.0]
		_:
			return [150.0 * v, 80.0]


# FM:380-402 / economy_density.c:73-90 in cm: mean |dh| over the neighbours that exist / 62500 (= 100 * 100 * 6.25), clamped to 1.
func _slope(t: Dictionary, gx: int, gy: int) -> float:
	var hs: PackedInt32Array = t["heights"]
	var h := float(hs[gy * W + gx])
	var sum := 0.0
	var n := 0
	if gx > 0:
		sum += absf(h - hs[gy * W + gx - 1]); n += 1
	if gx < W - 1:
		sum += absf(h - hs[gy * W + gx + 1]); n += 1
	if gy > 0:
		sum += absf(h - hs[(gy - 1) * W + gx]); n += 1
	if gy < H - 1:
		sum += absf(h - hs[(gy + 1) * W + gx]); n += 1
	return minf(sum / n / 62500.0, 1.0) if n > 0 else 0.0


# N7 expected yaw for the lot with key `id` at cell (gx, gy): [M:273-280, S:34], slope threshold 0.06 [S:32].
func _yaw_expect(t: Dictionary, gx: int, gy: int, id: int) -> float:
	var hs: PackedInt32Array = t["heights"]
	var dx := float(hs[gy * W + mini(gx + 1, W - 1)] - hs[gy * W + maxi(gx - 1, 0)])
	var dz := float(hs[mini(gy + 1, H - 1) * W + gx] - hs[maxi(gy - 1, 0) * W + gx])
	var jit := (_hash(id + 7) - 0.5) * 2.0 * 0.25
	if _slope(t, gx, gy) > 0.06 and absf(dx) + absf(dz) > 0.0:
		return atan2(-dx, -dz) + jit
	return _hash(id + 9) * PI + jit


func _ground_wu(t: Dictionary, gx: int, gy: int) -> float:
	var hs: PackedInt32Array = t["heights"]
	return float(hs[gy * W + gx]) / 100.0


# Eight lots in a row of interior cells (31..38) at row `row`, ids base..base+7, stage 3.
func _row_lots(base: int, row: int) -> Array:
	var a := []
	for k in 8:
		a.append(_lot(base + k, 31 + k, row, 3))
	return a


func _run() -> void:
	# Groups, in run order. [CONTROL] and [SKELETON] are green on the skeleton (ids, instance count, equal boxes, nothing before
	# set_terrain); the groups that read a size, offset, yaw, look function or street stay red until E1k fills the files.
	# Positive control for the harness, green today: Units3D with the same hand-built terrain draws one node per unit.
	var gu := _load(SCENES + "ground_units.gd")
	if gu != null:
		var u3: Node3D = gu.new()
		root.add_child(u3)
		var t := _terrain(true)
		u3.set_units([{"id": 1, "x": 550.0, "y": 550.0, "type": 0, "faction": 0}, {"id": 2, "x": 3550.0, "y": 2050.0, "type": 0, "faction": 0}, {"id": 3, "x": 950.0, "y": 950.0, "type": 0, "faction": 1}], t, [0.0], [])
		_check(u3.get_child_count() == 3 and u3.unit_node(1) != null and u3.unit_node(3) != null, "[CONTROL] Units3D on the hand-built terrain must draw 3 unit nodes, got %d children" % u3.get_child_count())
		_check(u3.unit_node(2) != null and absf(u3.unit_node(2).position.y - 360.0) < 0.5, "[CONTROL] unit on the steep cell must stand at height 360 wu (the fixture terrain projects)")
		_check(u3.unit_node(1) != null and absf(u3.unit_node(1).position.y) < 0.001, "[CONTROL] unit on flat ground must stand at height 0")
		u3.queue_free()
	# Fixture controls, green always: the slope oracle reads the stated slopes; the hash copy reads the hand values; the yaw reader
	# round-trips a known rotation.
	_check(absf(_slope(_terrain(true), 35, 20) - 0.048) < 1e-9 and absf(_slope(_ramp(30000), 35, 20) - 0.24) < 1e-9 and absf(_slope(_ramp(9000), 35, 20) - 0.072) < 1e-9 and _slope(_terrain(false), 35, 20) == 0.0, "[CONTROL] fixture slopes must read old 0.048, cliff 0.24, yaw 0.072, flat 0 under the four-neighbour formula")
	_check(_hash(0) == 0.0 and absf(_hash(1) - 0.7060959792477303) < 1e-12 and absf(_hash(7) - 0.41727321278706037) < 1e-12, "[CONTROL] the test's N1 hash copy must read the hand values (0, 0.7060959792477303, 0.41727321278706037)")
	var rot := Node3D.new()
	rot.transform = Transform3D(Basis(Vector3.UP, 0.7) * Basis.from_scale(Vector3(2, 1, 1)), Vector3.ZERO)
	_check(absf(atan2(-rot.transform.basis.x.z, rot.transform.basis.x.x) - 0.7) < 1e-5, "[CONTROL] the yaw reader atan2(-x.z, x.x) must round-trip Basis(UP, 0.7)")
	rot.free()

	var s := _load(LAYER)
	if s == null:
		return
	var look := _load(LOOK)
	var st_layer := _load(STRUCTURES)
	# [SKELETON] nothing before set_terrain.
	var pre: Node3D = s.new()
	root.add_child(pre)
	pre.set_frame({"lots": [_lot(1, 5, 5, 3)]})
	_check(pre.lots_drawn().is_empty(), "[SKELETON] R-193-01: lots_drawn() must be empty before set_terrain")
	var pmm := _mm(pre)
	_check(pmm == null or pmm.multimesh == null or pmm.multimesh.instance_count == 0, "[SKELETON] R-193-01: no MultiMesh instances before set_terrain")
	pre.queue_free()

	# [SKELETON] ids and count.
	var lots := []
	for k in 6:
		lots.append(_lot(10 + k, 3 + 4 * k, 3, k))
	var lay := _make(s, _terrain(true), lots)
	var drawn: Array = lay.lots_drawn()
	var ids := []
	for d in drawn:
		ids.append(int(d["id"]))
	_check(ids == [10, 11, 12, 13, 14, 15], "[SKELETON] R-193-01: lots_drawn() carries the frame's lot ids, got %s" % [ids])
	var mm := _mm(lay)
	_check(mm != null and mm.multimesh != null and mm.multimesh.instance_count == 6, "[SKELETON] R-193-01: MultiMesh instance_count must equal the lot count (6)")
	var d11 := _find(drawn, 11)
	_check(d11.get("x") == 750.0 and d11.get("y") == 350.0 and int(d11.get("stage", -1)) == 1, "[SKELETON] lots_drawn() entry keeps the frame's x, y and the drawn stage (id 11: 750, 350, stage 1), got %s" % [d11])

	# [TINT] the owner tint of a stage 1+ box equals StructuresLayer.owner_color: local, enemy, neutral (GAP 7).
	if st_layer != null:
		var cm: Dictionary = st_layer.get_script_constant_map()
		var lt := _make(s, _terrain(false), [_lot(60, 5, 5, 3, 0), _lot(61, 9, 5, 3, 1), _lot(62, 13, 5, 3, -1), _lot(63, 17, 5, 5, 1)])
		_check(_close(_col(lt, 0), cm["OWN_COLOR"]), "[TINT] a stage-3 box of the local owner must carry StructuresLayer.OWN_COLOR, got %s" % [_col(lt, 0)])
		_check(_close(_col(lt, 1), cm["ENEMY_COLOR"]), "[TINT] a stage-3 box of an enemy owner must carry StructuresLayer.ENEMY_COLOR, got %s" % [_col(lt, 1)])
		_check(_close(_col(lt, 2), cm["NEUTRAL_COLOR"]), "[TINT] a stage-3 box of owner -1 must carry StructuresLayer.NEUTRAL_COLOR (0.8, 0.8, 0.8, 0.6), got %s" % [_col(lt, 2)])
		_check(_close(_col(lt, 3), cm["ENEMY_COLOR"]), "[TINT] a stage-5 box keeps the owner tint, got %s" % [_col(lt, 3)])
		lt.queue_free()

	# [STAGE1] verdict "no perceptible difference in level": stage-1 lots (equal 0.05, no v) draw equal heights (assertion one:
	# green today, the control) and 5 wu (assertion two: red today, the skeleton draws 60). TD-VG-E-30: the old control used stage 4.
	var eq := []
	for k in 3:
		eq.append(_lot(20 + k, 3 + 4 * k, 3, 1))
	var le := _make(s, _terrain(true), eq)
	var h0 := _box_h(le, 0)
	_check(h0 > 0.0 and absf(h0 - _box_h(le, 1)) < EPS and absf(h0 - _box_h(le, 2)) < EPS, "[STAGE1] control: stage-1 lots (no v) must draw equal heights (%f)" % h0)
	_check(absf(h0 - 5.0) < EPS and absf(_box_h(le, 1) - 5.0) < EPS and absf(_box_h(le, 2) - 5.0) < EPS, "[STAGE1] R-193-05: a stage-1 box is 0.05 unit = 5 wu tall [S:314], got %f" % h0)
	le.queue_free()
	# [STAGE1] positive control for v: two stage-4 lots (ids 23 and 24) draw heights that differ (v per id, S:304; hand values v = 1.2399786, 1.1692226).
	var l4 := _make(s, _terrain(false), [_lot(23, 3, 3, 4), _lot(24, 7, 3, 4)])
	_check(absf(_box_h(l4, 0) - _box_h(l4, 1)) > EPS, "[STAGE1] control: two stage-4 lots with ids 23 and 24 must differ in height by more than %s (v per lot, S:304), got %f and %f" % [EPS, _box_h(l4, 0), _box_h(l4, 1)])
	l4.queue_free()

	# [STAGE] stage heights, on the six-lot layer above.
	_check(_box_h(lay, 0) >= 0.0 and _box_h(lay, 0) < _box_h(lay, 5), "[STAGE] R-193-05: stage 0 box must be lower than stage 5 (got %f vs %f)" % [_box_h(lay, 0), _box_h(lay, 5)])
	_check(_box_h(lay, 1) < _box_h(lay, 4), "[STAGE] R-193-05: stage 1 lower than stage 4")
	lay.queue_free()

	# [VARIATION] N1: twelve stage-4 lots, distinct keys: heights not all equal; every height in [1.5*0.8, 1.5*1.3]*100 wu (inclusive,
	# from v in [0.8, 1.3]); the same key draws the same height at another cell and in another layer.
	var vl := []
	for k in 12:
		vl.append(_lot(100 + k, 2 + 3 * k, 5, 4))
	var lv := _make(s, _terrain(false), vl)
	var hmin := 1e9
	var hmax := -1e9
	for k in 12:
		hmin = minf(hmin, _box_h(lv, k))
		hmax = maxf(hmax, _box_h(lv, k))
	_check(hmax - hmin > EPS, "[VARIATION] verdict: twelve stage-4 lots with distinct ids must not all draw one height (min %f max %f)" % [hmin, hmax])
	_check(hmin >= 120.0 - EPS and hmax <= 195.0 + EPS, "[VARIATION] N1: every stage-4 height must lie in [120, 195] wu (1.5 * [0.8, 1.3] * 100), got [%f, %f]" % [hmin, hmax])
	var k1 := _make(s, _terrain(false), [_lot(77, 5, 5, 4)])
	var k2 := _make(s, _terrain(false), [_lot(77, 20, 9, 4)])
	_check(_box_h(k1, 0) > 0.0 and absf(_box_h(k1, 0) - _box_h(k2, 0)) < EPS, "[VARIATION] control: the same key (lot id 77) at two cells draws the same height (%f vs %f)" % [_box_h(k1, 0), _box_h(k2, 0)])
	lv.queue_free()
	k1.queue_free()
	k2.queue_free()

	# [HEIGHTS] N3 stages 1 to 5 (5 per GAP 6) and [FOOTPRINT] N3/N5 on one flat layer: three ids per stage. HEIGHTS takes v from
	# scenes/settlement/settlement_look.gd (hash01 and lot_key); FOOTPRINT takes it from this file's hash copy.
	var sg := []
	var tf := _terrain(false)
	for stage in range(1, 6):
		for j in 3:
			sg.append(_lot(200 + stage * 10 + j, 3 + 4 * j, 2 + 4 * (stage - 1), stage))
	var lg := _make(s, tf, sg)
	var hi := 0
	for stage in range(1, 6):
		for j in 3:
			var lot: Dictionary = sg[hi]
			var want: Array = _row(stage, false, int(lot["id"]))
			_check(absf(_box_h(lg, hi) - float(want[0])) < EPS, "[HEIGHTS] R-193-05: stage %d id %d must draw %f wu tall (table row x v), got %f" % [stage, lot["id"], want[0], _box_h(lg, hi)])
			_check(absf(_box_w(lg, hi) - float(want[1])) < EPS, "[FOOTPRINT] N3: stage %d id %d must draw %f wu wide (footprint x 100), got %f" % [stage, lot["id"], want[1], _box_w(lg, hi)])
			_check(absf(_box_d(lg, hi) - 0.85 * float(want[1])) < EPS, "[FOOTPRINT] N5: stage %d id %d depth must be 0.85 of the width = %f wu, got %f" % [stage, lot["id"], 0.85 * float(want[1]), _box_d(lg, hi)])
			hi += 1
	if look != null:
		var rows := [[1, 0.05, false], [2, 0.3, true], [3, 0.7, true], [4, 1.5, true], [5, 1.5, true]]
		hi = 0
		for r in rows:
			for j in 3:
				var lot: Dictionary = sg[hi]
				var key: int = look.lot_key(tf, lot)
				var v: float = 0.8 + 0.5 * look.hash01(key + 11) if r[2] else 1.0
				_check(absf(_box_h(lg, hi) - float(r[1]) * v * 100.0) < EPS, "[HEIGHTS] N3: stage %d id %d must draw %f * v(%f) * 100 wu with v from settlement_look.hash01(lot_key + 11), got %f" % [r[0], lot["id"], r[1], v, _box_h(lg, hi)])
				hi += 1
	lg.queue_free()

	# [RUBBLE] N2: stage 0 draws 14 wu tall, 70 wide, colour (0.28, 0.2, 0.18) (S:305-306).
	var lr := _make(s, tf, [_lot(300, 4, 4, 0), _lot(301, 8, 4, 0), _lot(302, 12, 4, 0)])
	for k in 3:
		_check(absf(_box_h(lr, k) - 14.0) < EPS, "[RUBBLE] N2: a stage-0 box must be 14 wu tall (0.14 unit, S:305), got %f" % _box_h(lr, k))
		_check(absf(_box_w(lr, k) - 70.0) < EPS, "[RUBBLE] N2: a stage-0 box must be 70 wu wide (footprint 0.7, S:306), got %f" % _box_w(lr, k))
		_check(_close(_col(lr, k), RUBBLE), "[RUBBLE] N2: a stage-0 box must be coloured (0.28, 0.2, 0.18) (S:306), got %s" % [_col(lr, k)])
	lr.queue_free()

	# [JITTER] N6: each centre within 0.22 cell of the cell centre on each axis, at least one beyond 0.01 cell, and equal to the
	# formula (this file's hash) and to settlement_look.jitter(key) * 100.
	var jl := []
	for k in 12:
		jl.append(_lot(400 + k, 2 + 3 * k, 6 + (k % 3), 3))
	var lj := _make(s, tf, jl)
	var any_off := false
	for k in 12:
		var lot: Dictionary = jl[k]
		var id := int(lot["id"])
		var o := _tr(lj, k).origin
		var ox := (o.x - float(lot["x"])) / 100.0
		var oz := (o.z - float(lot["y"])) / 100.0
		_check(absf(ox) <= 0.22 + 1e-4 and absf(oz) <= 0.22 + 1e-4, "[JITTER] N6: id %d centre must lie within 0.22 cell of the cell centre on each axis, got (%f, %f) cells" % [id, ox, oz])
		if absf(ox) > 0.01 or absf(oz) > 0.01:
			any_off = true
		var wx := (_hash(id + 3) - 0.5) * 2.0 * 0.22
		var wz := (_hash(id + 5) - 0.5) * 2.0 * 0.22
		_check(absf(ox - wx) * 100.0 < POS_EPS and absf(oz - wz) * 100.0 < POS_EPS, "[JITTER] N6: id %d offset must be ((hash(id+3)-0.5)*0.44, (hash(id+5)-0.5)*0.44) = (%f, %f) cells, got (%f, %f)" % [id, wx, wz, ox, oz])
		if look != null:
			var jv: Vector2 = look.jitter(look.lot_key(tf, lot))
			_check(absf(o.x - float(lot["x"]) - jv.x * 100.0) < POS_EPS and absf(o.z - float(lot["y"]) - jv.y * 100.0) < POS_EPS, "[JITTER] N6: id %d offset must equal settlement_look.jitter(key) * 100 = %s wu, got (%f, %f)" % [id, jv * 100.0, o.x - float(lot["x"]), o.z - float(lot["y"])])
	_check(any_off, "[JITTER] verdict: at least one box must sit off its cell centre by more than 0.01 cell")
	lj.queue_free()

	# [YAW] N7. Yaw fixture (0.072 > 0.06): contour yaw within the 0.25 rad jitter band and exactly the formula; old fixture (0.048):
	# hashed yaw, not the contour one; flat: eight yaws not all equal and not all unrotated; spike (slope high, dx = dz = 0): hashed.
	var ty := _ramp(9000)
	var yl := _row_lots(500, 10)
	var ly := _make(s, ty, yl)
	for k in 8:
		var id := 500 + k
		var contour := atan2(-float(ty["heights"][10 * W + 32 + k] - ty["heights"][10 * W + 30 + k]), 0.0)
		_check(absf(angle_difference(_yaw(ly, k), contour)) <= 0.25 + ANG_EPS, "[YAW] R-193-01: id %d on the yaw fixture (slope 0.072) must turn to the contour within the 0.25 rad jitter band (contour %f), got yaw %f" % [id, contour, _yaw(ly, k)])
		_check(absf(angle_difference(_yaw(ly, k), _yaw_expect(ty, 31 + k, 10, id))) < ANG_EPS, "[YAW] N7: id %d on the yaw fixture must read atan2(-dx, -dz) + jit = %f, got %f" % [id, _yaw_expect(ty, 31 + k, 10, id), _yaw(ly, k)])
	ly.queue_free()
	var to := _terrain(true)
	var lo := _make(s, to, _row_lots(520, 10))
	for k in 8:
		var id := 520 + k
		var contour2 := atan2(-float(to["heights"][10 * W + 32 + k] - to["heights"][10 * W + 30 + k]), 0.0)
		_check(absf(angle_difference(_yaw(lo, k), _yaw_expect(to, 31 + k, 10, id))) < ANG_EPS, "[YAW] N7: id %d on the old fixture (slope 0.048 < 0.06) must read the hashed yaw hash(id+9)*PI + jit = %f, got %f" % [id, _yaw_expect(to, 31 + k, 10, id), _yaw(lo, k)])
		_check(absf(angle_difference(_yaw(lo, k), contour2)) > 0.25, "[YAW] N7 negative control: id %d on the old fixture must not be contour-aligned (contour %f), got yaw %f" % [id, contour2, _yaw(lo, k)])
	lo.queue_free()
	var fl := []
	for k in 8:
		fl.append(_lot(540 + k, 3 + 4 * (k % 4), 3 + 6 * (k / 4), 3))
	var lf := _make(s, tf, fl)
	var ymin := 1e9
	var ymax := -1e9
	for k in 8:
		ymin = minf(ymin, _yaw(lf, k))
		ymax = maxf(ymax, _yaw(lf, k))
		var exp_c: float = _yaw_expect(tf, 3 + 4 * (k % 4), 3 + 6 * (k / 4), 540 + k)
		_check(absf(angle_difference(_yaw(lf, k), exp_c)) < ANG_EPS, "[YAW] N7: id %d on flat ground must read the hashed yaw %f, got %f" % [540 + k, exp_c, _yaw(lf, k)])
	_check(ymax - ymin > 0.05, "[YAW] verdict: eight lots on flat ground must not all share one yaw (min %f max %f)" % [ymin, ymax])
	_check(maxf(absf(ymin), absf(ymax)) > 0.05, "[YAW] verdict: lots on flat ground must not all be unrotated (min %f max %f)" % [ymin, ymax])
	lf.queue_free()
	var tsp := _spike(30000, 35, 10)
	var lsp := _make(s, tsp, [_lot(560, 35, 10, 3)])
	_check(_slope(tsp, 35, 10) > 0.06 and absf(angle_difference(_yaw(lsp, 0), _yaw_expect(tsp, 35, 10, 560))) < ANG_EPS, "[YAW] N7: a lot on a spike (slope %f, dx = dz = 0) must read the hashed yaw %f, got %f" % [_slope(tsp, 35, 10), _yaw_expect(tsp, 35, 10, 560), _yaw(lsp, 0)])
	lsp.queue_free()

	# [SINK] N8: centre y = ground + height / 2 - 12 wu (M:252), on flat ground and on the steep cell (ground 360 wu), stages 1 and 3.
	var tk := _terrain(true)
	var sk := _make(s, tk, [_lot(600, 5, 5, 3), _lot(601, 35, 20, 3), _lot(602, 9, 5, 1)])
	for k in 3:
		var lot_c: Array = [[5, 5], [35, 20], [9, 5]][k]
		var g := _ground_wu(tk, lot_c[0], lot_c[1])
		var want_y := g + _box_h(sk, k) * 0.5 - 12.0
		_check(absf(_tr(sk, k).origin.y - want_y) < POS_EPS, "[SINK] N8: box %d centre y must be ground %f + height/2 %f - 12 = %f wu, got %f" % [k, g, _box_h(sk, k) * 0.5, want_y, _tr(sk, k).origin.y])
	sk.queue_free()

	# [LANES] N9: a 12 x 12 cell patch (cells 8..19) of stage-3 lots on every cell except lane cells (gx mod 4 == 3 or gy mod 4 == 3, S:89):
	# nothing is filled in, no centre lies in a lane cell, and the gap between nearest box edges across each lane (worst-case rotated extent)
	# is positive. The layer draws exactly the lots it is given.
	var pl := []
	var cells := []
	var pid := 700
	for gy in range(8, 20):
		for gx in range(8, 20):
			if gx % 4 == 3 or gy % 4 == 3:
				continue
			pl.append(_lot(pid, gx, gy, 3))
			cells.append(Vector2i(gx, gy))
			pid += 1
	var lp := _make(s, tf, pl)
	var pmm2 := _mm(lp)
	_check(pmm2 != null and pmm2.multimesh != null and pmm2.multimesh.instance_count == pl.size() and lp.lots_drawn().size() == pl.size(), "[LANES] N9: the layer must draw exactly the %d lots given, no lane filler (got %d instances)" % [pl.size(), pmm2.multimesh.instance_count if pmm2 != null and pmm2.multimesh != null else -1])
	var in_lane := 0
	var lx_max := {}
	var rx_min := {}
	var lz_max := {}
	var rz_min := {}
	for c in [11, 15]:
		lx_max[c] = -1e9
		rx_min[c] = 1e9
		lz_max[c] = -1e9
		rz_min[c] = 1e9
	for k in pl.size():
		var xf := _tr(lp, k)
		var cx := int(floor(xf.origin.x / 100.0))
		var cz := int(floor(xf.origin.z / 100.0))
		if cx % 4 == 3 or cz % 4 == 3:
			in_lane += 1
		var hx := 0.5 * (absf(xf.basis.x.x) + absf(xf.basis.z.x))
		var hz := 0.5 * (absf(xf.basis.x.z) + absf(xf.basis.z.z))
		for c in [11, 15]:
			if cx < c:
				lx_max[c] = maxf(lx_max[c], xf.origin.x + hx)
			elif cx > c:
				rx_min[c] = minf(rx_min[c], xf.origin.x - hx)
			if cz < c:
				lz_max[c] = maxf(lz_max[c], xf.origin.z + hz)
			elif cz > c:
				rz_min[c] = minf(rz_min[c], xf.origin.z - hz)
	_check(in_lane == 0, "[LANES] N9: no box centre may lie in a lane cell, %d do" % in_lane)
	for c in [11, 15]:
		_check(rx_min[c] - lx_max[c] > 0.0, "[LANES] N9: the gap across lane column %d must be positive, got %f wu" % [c, rx_min[c] - lx_max[c]])
		_check(rz_min[c] - lz_max[c] > 0.0, "[LANES] N9: the gap across lane row %d must be positive, got %f wu" % [c, rz_min[c] - lz_max[c]])
	lp.queue_free()

	# [CLIFF] N4. Cliff fixture (0.24 > 0.22): a stage-5 lot reads cliff true and stage 3 and draws the cliff row; stage 1 and 2 cliff
	# rows; a stage-4 lot is capped to 3. Flat ground and the old fixture (0.048, negative control) read cliff false and stage 5 (the
	# stage-4 row, GAP 6). lots_drawn() entry keys "stage" and "cliff" are this test's reading of the INTERFACE.
	var tc := _ramp(30000)
	var cl := [_lot(30, 35, 20, 5), _lot(31, 5, 20, 5), _lot(33, 36, 22, 1), _lot(34, 37, 22, 2), _lot(35, 38, 22, 3), _lot(36, 35, 25, 4)]
	var lc := _make(s, tc, cl)
	var d30 := _find(lc.lots_drawn(), 30)
	var d31 := _find(lc.lots_drawn(), 31)
	_check(bool(d30.get("cliff", false)), "[CLIFF] R-193-02: lot in the steep region (slope 0.24 > 0.22) must be flagged cliff")
	_check(int(d30.get("stage", 99)) == 3, "[CLIFF] R-193-02: a stage-5 cliff lot is capped at stage 3 (CLIFF_MAX_STAGE, S:20), got %s" % [d30.get("stage")])
	_check(not bool(d31.get("cliff", true)) and int(d31.get("stage", 0)) == 5, "[CLIFF] control: flat-ground lot is not cliff and keeps stage 5")
	_check(_box_h(lc, 0) < _box_h(lc, 1), "[CLIFF] R-193-02: capped cliff box lower than the uncapped stage-5 box")
	var rows_c := [[0, 3, true, 30], [1, 5, false, 31], [2, 1, true, 33], [3, 2, true, 34], [4, 3, true, 35], [5, 3, true, 36]]
	for r in rows_c:
		var want_c: Array = _row(int(r[1]), bool(r[2]), int(r[3]))
		_check(absf(_box_h(lc, int(r[0])) - float(want_c[0])) < EPS and absf(_box_w(lc, int(r[0])) - float(want_c[1])) < EPS, "[CLIFF] N4: id %d (drawn stage %d, cliff %s) must draw %f wu tall and %f wide, got %f x %f" % [r[3], r[1], r[2], want_c[0], want_c[1], _box_h(lc, int(r[0])), _box_w(lc, int(r[0]))])
	var d36 := _find(lc.lots_drawn(), 36)
	_check(bool(d36.get("cliff", false)) and int(d36.get("stage", 99)) == 3, "[CLIFF] R-193-02: a stage-4 lot on the cliff fixture reads cliff true and stage 3, got %s" % [d36])
	lc.queue_free()
	var lneg := _make(s, _terrain(true), [_lot(32, 35, 20, 5)])
	var d32 := _find(lneg.lots_drawn(), 32)
	_check(not bool(d32.get("cliff", true)) and int(d32.get("stage", 0)) == 5, "[CLIFF] control (TD-VG-E-30 P2): a stage-5 lot on the old fixture (slope 0.048 < 0.22) reads cliff false and stage 5, got %s" % [d32])
	var want32: Array = _row(5, false, 32)
	_check(absf(_box_h(lneg, 0) - float(want32[0])) < EPS, "[CLIFF] control: the stage-5 lot on the old fixture draws the stage-4 row %f wu tall (GAP 6), got %f" % [want32[0], _box_h(lneg, 0)])
	lneg.queue_free()

	# [EASE] N10, dt-based (spec :298, g5). The first frame after load snaps; a stage change eases over RISE_S 0.9 s of _process delta,
	# starting from the current eased value (S:320-327); a lot that leaves the frame is gone at once.
	var ea := _make(s, tf, [_lot(1, 5, 5, 2), _lot(2, 9, 5, 4)])
	var ha2 := 30.0 * _v(1)
	var ha3 := 70.0 * _v(1)
	var ha4 := 150.0 * _v(1)
	var hb := 150.0 * _v(2)
	_check(absf(_box_h(ea, 0) - ha2) < EPS and absf(_box_h(ea, 1) - hb) < EPS, "[EASE] R-237-01: the first frame after load snaps, every lot at its target without _process (want %f and %f, got %f and %f)" % [ha2, hb, _box_h(ea, 0), _box_h(ea, 1)])
	if not ea.has_method("_process"):
		_check(false, "[EASE] R-237-01: SettlementLayer must define _process(delta) to ease stage changes (RISE_S 0.9 s per call)")
	else:
		ea._process(DT)
		_check(absf(_box_h(ea, 0) - ha2) < EPS and absf(_box_h(ea, 1) - hb) < EPS, "[EASE] R-237-01: a lot with no stage change must not move under _process (no ease from zero on load), got %f and %f" % [_box_h(ea, 0), _box_h(ea, 1)])
		ea.set_frame({"lots": [_lot(1, 5, 5, 3), _lot(2, 9, 5, 4)]})
		ea._process(DT)
		var hm := _box_h(ea, 0)
		_check(hm > ha2 + EPS and hm < ha3 - EPS, "[EASE] R-237-01: after a stage change 2 to 3 one _process of %s s must leave the height strictly between %f and %f, got %f" % [DT, ha2, ha3, hm])
		_check(_box_w(ea, 0) > 70.0 + EPS and _box_w(ea, 0) < 72.0 - EPS, "[EASE] R-237-01: the footprint eases too, strictly between 70 and 72 wu, got %f" % _box_w(ea, 0))
		ea._process(DT)
		_check(absf(_box_h(ea, 0) - ha3) < EPS and absf(_box_w(ea, 0) - 72.0) < EPS, "[EASE] R-237-01: once the deltas sum to RISE_S 0.9 s the lot sits at its target %f x 72, got %f x %f" % [ha3, _box_h(ea, 0), _box_w(ea, 0)])
		_check(absf(_box_h(ea, 1) - hb) < EPS, "[EASE] R-237-01: the lot with no change stays at its target through the ease, got %f" % _box_h(ea, 1))
		ea.set_frame({"lots": [_lot(1, 5, 5, 4), _lot(2, 9, 5, 4)]})
		ea._process(DT)
		var hmid := _box_h(ea, 0)
		_check(absf(hmid - (ha3 + ha4) * 0.5) < EPS, "[EASE] R-237-01: a change 3 to 4 eases from the value at the change, %f at half way, got %f" % [(ha3 + ha4) * 0.5, hmid])
		ea.set_frame({"lots": [_lot(1, 5, 5, 2), _lot(2, 9, 5, 4)]})
		ea._process(DT)
		_check(absf(_box_h(ea, 0) - (hmid + ha2) * 0.5) < EPS, "[EASE] R-237-01: a change mid-ease starts from the current eased value %f (not from zero, not from the old target): want %f, got %f" % [hmid, (hmid + ha2) * 0.5, _box_h(ea, 0)])
		ea._process(DT)
		_check(absf(_box_h(ea, 0) - ha2) < EPS, "[EASE] R-237-01: the retargeted lot settles at stage 2, %f, got %f" % [ha2, _box_h(ea, 0)])
	ea.set_frame({"lots": [_lot(2, 9, 5, 4)]})
	var eids := []
	for d in ea.lots_drawn():
		eids.append(int(d["id"]))
	var emm := _mm(ea)
	_check(eids == [2] and emm != null and emm.multimesh.instance_count == 1, "[EASE] control: a lot that leaves the frame is gone at once, got ids %s and %d instances" % [eids, emm.multimesh.instance_count if emm != null else -1])
	_check(absf(_box_h(ea, 0) - hb) < EPS, "[EASE] control: the remaining lot keeps its own height %f after the other left, got %f" % [hb, _box_h(ea, 0)])
	ea.queue_free()

	# [STREET] ribbon meshes are counted against a baseline layer of two stage-1 lots (no street) so any other MeshInstance3D the layer
	# owns does not count: near stage-2 pair adds a ribbon, far pair adds none. DRAFT-e1k-streets / GAP 4: Euclidean distance between
	# lot centres within 3 cells (a 3 x 3 diagonal pair, Chebyshev 3 but Euclid 4.24, adds none; a 2 x 2 diagonal pair, Euclid 2.83, adds
	# one); the route mesh is hidden by default (visible false) and counts regardless of visible.
	var base := _make(s, _terrain(false), [_lot(44, 10, 10, 1), _lot(45, 12, 10, 1)])
	var near := _make(s, _terrain(false), [_lot(40, 10, 10, 2), _lot(41, 12, 10, 2)])
	var far := _make(s, _terrain(false), [_lot(42, 5, 10, 2), _lot(43, 15, 10, 2)])
	var dg3 := _make(s, _terrain(false), [_lot(46, 10, 10, 2), _lot(47, 13, 13, 2)])
	var dg2 := _make(s, _terrain(false), [_lot(48, 10, 10, 2), _lot(49, 12, 12, 2)])
	var rb := _ribbons(base)
	_check(_ribbons(near) > rb, "[STREET] R-193-09: a street ribbon mesh must exist for two stage-2 lots 2 cells apart (got %d, baseline %d)" % [_ribbons(near), rb])
	_check(_ribbons(far) == rb, "[STREET] R-193-09: no street ribbon for two stage-2 lots 10 cells apart (got %d, baseline %d)" % [_ribbons(far), rb])
	_check(_ribbons(dg3) == rb, "[STREET] GAP 4: no ribbon for stage-2 lots at (10,10) and (13,13): Euclidean distance 4.24 > 3 (got %d, baseline %d)" % [_ribbons(dg3), rb])
	_check(_ribbons(dg2) > rb, "[STREET] GAP 4: a ribbon for stage-2 lots at (10,10) and (12,12): Euclidean distance 2.83 <= 3 (got %d, baseline %d)" % [_ribbons(dg2), rb])
	_check(_ribbons_hidden(near), "[STREET] GAP 4: the route mesh exists and is hidden by default (visible false), as the mockup ships it (M:99)")
	base.queue_free()
	near.queue_free()
	far.queue_free()
	dg3.queue_free()
	dg2.queue_free()

	# [LOOKFN] scenes/settlement/settlement_look.gd against the NUMBERS and the mockup's own functions.
	if look != null:
		_lookfn(look, tf)
	# [STREETFN] scenes/settlement/settlement_streets.gd.
	var sts := _load(STREETS)
	if sts != null:
		_streetfn(sts)


func _lookfn(look: GDScript, tf: Dictionary) -> void:
	var cm: Dictionary = look.get_script_constant_map()
	# Constant parity table: name, expected value, prototype file:line.
	var table := [
		["CELL_WU", 100.0, "one cell = 100 wu, spec E1k numbers"],
		["JITTER_CELLS", 0.22, "S:33, M:248-249"],
		["YAW_JITTER", 0.25, "S:34"],
		["CLIFF_SLOPE", 0.22, "S:19"],
		["CLIFF_MAX_STAGE", 3, "S:20"],
		["CONTOUR_SLOPE", 0.06, "S:32"],
		["DEPTH_RATIO", 0.85, "M:251"],
		["SINK_UNITS", 0.12, "M:252"],
		["V_BASE", 0.8, "S:304"],
		["V_SPAN", 0.5, "S:304"],
		["RISE_S", 0.9, "S:21"],
		["SLOPE_NORM", 6.25, "FM:380-402 reference, csrc/economy_density.c:25"],
		["RUBBLE_COLOR", RUBBLE, "S:306"],
	]
	for r in table:
		_check(cm.has(r[0]), "[LOOKFN] settlement_look.gd must define const %s (%s)" % [r[0], r[2]])
		if cm.has(r[0]):
			var ok: bool
			if r[1] is Color:
				ok = _close(cm[r[0]], r[1])
			else:
				ok = absf(float(cm[r[0]]) - float(r[1])) < 1e-9
			_check(ok, "[LOOKFN] %s must equal %s (%s), got %s" % [r[0], r[1], r[2], cm[r[0]]])
	# lot_key: the sim lot id (GAP 3).
	_check(look.lot_key(tf, {"id": 23, "x": 1250.0, "y": 350.0}) == 23 and look.lot_key(tf, {"id": 0}) == 0, "[LOOKFN] GAP 3: lot_key(t, lot) must be the sim lot id")
	# hash01 against the mockup's _hash, 2000 inputs, plus the hand values.
	var ms = load(MOCK_SIM).new()
	var bad := 0
	for k in 2000:
		var i := k * 13
		if absf(look.hash01(i) - ms._hash(i)) > 1e-12:
			bad += 1
	_check(bad == 0, "[LOOKFN] N1: hash01 must equal the mockup's _hash (S:137-138) for 2000 inputs, %d differ" % bad)
	_check(look.hash01(0) == 0.0 and absf(look.hash01(1) - 0.7060959792477303) < 1e-12 and absf(look.hash01(7) - 0.41727321278706037) < 1e-12, "[LOOKFN] N1: hash01 hand values hash(0) = 0, hash(1) = 0.7060959792477303, hash(7) = 0.41727321278706037")
	# vis against the mockup's _vis_of for stages 0..4 (cliff true and false) and ten values of i; stage 5 against the default branch.
	var sl := PackedFloat32Array()
	sl.resize(5000)
	ms.slope = sl
	var keys = [3, 17, 42, 99, 123, 256, 777, 1234, 2500, 4999]
	var vbad := []
	for i in keys:
		for cliff in [false, true]:
			sl[i] = 0.5 if cliff else 0.0
			ms.slope = sl
			for stage in range(0, 5):
				var mv: Array = ms._vis_of(i, stage, stage == 0)
				var lv: Array = look.vis(stage, cliff, i)
				if lv.size() < 2 or absf(float(lv[0]) - float(mv[0])) > 1e-9 or absf(float(lv[1]) - float(mv[1])) > 1e-9:
					vbad.append("stage %d cliff %s i %d: want [%s, %s] got %s" % [stage, cliff, i, mv[0], mv[1], lv])
		sl[i] = 0.0
		ms.slope = sl
		var m5: Array = ms._vis_of(i, 5, false)
		var l5: Array = look.vis(5, false, i)
		if l5.size() < 2 or absf(float(l5[0]) - float(m5[0])) > 1e-9 or absf(float(l5[1]) - float(m5[1])) > 1e-9:
			vbad.append("stage 5 i %d: want [%s, %s] got %s" % [i, m5[0], m5[1], l5])
	_check(vbad.is_empty(), "[LOOKFN] N2/N3/N4: vis(stage, cliff, i) must equal the mockup's _vis_of (S:303-317) for stages 0-4 both ways and stage 5 (GAP 6); first mismatch: %s" % [vbad.slice(0, 1)])
	# slope_at (GAP 1) on the fixtures.
	_check(absf(look.slope_at(_terrain(true), 35, 20) - 0.048) < 1e-6, "[LOOKFN] GAP 1: slope_at on the old fixture interior must read 0.048, got %s" % look.slope_at(_terrain(true), 35, 20))
	_check(absf(look.slope_at(_ramp(30000), 35, 20) - 0.24) < 1e-6, "[LOOKFN] GAP 1: slope_at on the cliff fixture must read 0.24, got %s" % look.slope_at(_ramp(30000), 35, 20))
	_check(absf(look.slope_at(_ramp(9000), 35, 20) - 0.072) < 1e-6, "[LOOKFN] GAP 1: slope_at on the yaw fixture must read 0.072, got %s" % look.slope_at(_ramp(9000), 35, 20))
	_check(look.slope_at(tf, 35, 20) == 0.0 and look.slope_at(tf, 0, 0) == 0.0, "[LOOKFN] GAP 1: slope_at on flat ground must read 0")
	_check(absf(look.slope_at(_terrain(true), 35, 0) - 0.064) < 1e-6, "[LOOKFN] GAP 1: slope_at on an edge cell averages the 3 neighbours that exist (4000 / 62500 = 0.064), got %s" % look.slope_at(_terrain(true), 35, 0))
	_check(look.slope_at(_ramp(200000), 35, 20) == 1.0, "[LOOKFN] GAP 1: slope_at clamps to 1, got %s" % look.slope_at(_ramp(200000), 35, 20))
	# jitter and yaw against hand-computed values (id 7: hash(10), hash(12), hash(14), hash(16) per the formulas).
	var jv: Vector2 = look.jitter(7)
	_check(absf(jv.x - (-0.19666224155031664)) < 1e-6 and absf(jv.y - (-0.02207217517357137)) < 1e-6, "[LOOKFN] N6: jitter(7) must be (-0.19666224155031664, -0.02207217517357137) cells, got %s" % [jv])
	_check(absf(angle_difference(look.yaw(_ramp(9000), 35, 20, 7), -1.4035231140078361)) < 1e-9, "[LOOKFN] N7: yaw on the yaw fixture at (35,20), key 7, must be atan2(-18000, -0) + jit = -PI/2 + 0.16727321278706037 = -1.4035231140078361, got %s" % look.yaw(_ramp(9000), 35, 20, 7))
	_check(absf(angle_difference(look.yaw(_ramp(30000), 35, 20, 7), -1.4035231140078361)) < 1e-9, "[LOOKFN] N7: yaw on the cliff fixture (0.24 > 0.06) is the contour yaw too, got %s" % look.yaw(_ramp(30000), 35, 20, 7))
	_check(absf(angle_difference(look.yaw(_terrain(true), 35, 20, 7), 1.1014817675006925)) < 1e-9, "[LOOKFN] N7: yaw on the old fixture (0.048 < 0.06), key 7, must be the hashed hash(16)*PI + jit = 1.1014817675006925, got %s" % look.yaw(_terrain(true), 35, 20, 7))
	_check(absf(angle_difference(look.yaw(tf, 35, 20, 7), 1.1014817675006925)) < 1e-9, "[LOOKFN] N7: yaw on flat ground, key 7, must be the hashed 1.1014817675006925, got %s" % look.yaw(tf, 35, 20, 7))
	_check(absf(angle_difference(look.yaw(_spike(30000, 35, 10), 35, 10, 7), 1.1014817675006925)) < 1e-9, "[LOOKFN] N7: yaw on a spike (slope above 0.06, |dx|+|dz| = 0) is the hashed one, got %s" % look.yaw(_spike(30000, 35, 10), 35, 10, 7))


func _verts(mesh: ArrayMesh) -> PackedVector3Array:
	if mesh == null or mesh.get_surface_count() == 0:
		return PackedVector3Array()
	return mesh.surface_get_arrays(0)[Mesh.ARRAY_VERTEX]


func _has_vertex_x(vs: PackedVector3Array, x: float) -> bool:
	for v in vs:
		if absf(v.x - x) < POS_EPS:
			return true
	return false


func _streetfn(sts: GDScript) -> void:
	var tf := _terrain(false)
	var near: ArrayMesh = sts.ribbons([_lot(1, 10, 10, 2), _lot(2, 12, 10, 2)], tf)
	_check(near != null and near.get_surface_count() > 0 and _verts(near).size() > 0, "[STREETFN] R-193-09: ribbons() on a near stage-2 pair must return a mesh with a surface")
	var far: ArrayMesh = sts.ribbons([_lot(1, 5, 10, 2), _lot(2, 15, 10, 2)], tf)
	_check(far != null and far.get_surface_count() == 0, "[STREETFN] R-193-09: ribbons() on a far pair must return a mesh with zero surfaces")
	var one: ArrayMesh = sts.ribbons([_lot(1, 10, 10, 2)], tf)
	_check(one != null and one.get_surface_count() == 0, "[STREETFN] ribbons() on one lot must return a mesh with zero surfaces")
	var s1: ArrayMesh = sts.ribbons([_lot(1, 10, 10, 1), _lot(2, 12, 10, 1)], tf)
	_check(s1 != null and s1.get_surface_count() == 0, "[STREETFN] DRAFT-e1k-streets: stage-1 lots are ignored (zero surfaces)")
	var mix: ArrayMesh = sts.ribbons([_lot(1, 10, 10, 2), _lot(2, 11, 10, 1), _lot(3, 20, 10, 2)], tf)
	_check(mix != null and mix.get_surface_count() == 0, "[STREETFN] DRAFT-e1k-streets: a stage-1 lot is not a neighbour (stage-2 lots 10 apart, a stage-1 lot between) -> zero surfaces")
	var dg: ArrayMesh = sts.ribbons([_lot(1, 10, 10, 2), _lot(2, 13, 13, 2)], tf)
	_check(dg != null and dg.get_surface_count() == 0, "[STREETFN] GAP 4: Euclidean metric, (10,10)-(13,13) is 4.24 cells -> zero surfaces")
	# Width and lift: a horizontal link on flat ground is 2 cells wide (the mockup's +-1 unit, M:297) at y = 0 + 0.15 unit = 15 wu (M:292-301).
	var vs := _verts(near)
	var zmin := 1e9
	var zmax := -1e9
	var ybad := 0
	for v in vs:
		zmin = minf(zmin, v.z)
		zmax = maxf(zmax, v.z)
		if absf(v.y - 15.0) > POS_EPS:
			ybad += 1
	_check(vs.size() > 0 and absf((zmax - zmin) - 200.0) < POS_EPS, "[STREETFN] GAP 4: a horizontal link is 2 cells = 200 wu wide, got %f" % (zmax - zmin))
	_check(vs.size() > 0 and ybad == 0, "[STREETFN] GAP 4: on flat ground the ribbon lies 0.15 unit = 15 wu above the ground, %d vertices differ" % ybad)
	# Follows the ground: on the old fixture row 10, cells 33..35, y = max of the 3x3 cells around each sampled cell + 15 wu.
	var tslope := _terrain(true)
	var rr: ArrayMesh = sts.ribbons([_lot(1, 33, 10, 2), _lot(2, 35, 10, 2)], tslope)
	var want_y := []
	for cx in range(33, 36):
		var top := -1e9
		for dy in range(-1, 2):
			for dx in range(-1, 2):
				top = maxf(top, _ground_wu(tslope, cx + dx, 10 + dy))
		want_y.append(top + 15.0)
	var distinct := {}
	var yout := 0
	for v in _verts(rr):
		var hit := false
		for wy in want_y:
			if absf(v.y - float(wy)) < POS_EPS:
				hit = true
				distinct[snappedf(float(wy), 0.01)] = true
		if not hit:
			yout += 1
	_check(_verts(rr).size() > 0 and yout == 0 and distinct.size() >= 2, "[STREETFN] GAP 4: on a slope every ribbon vertex must lie at the max of the 3x3 ground heights around its cell + 15 wu, one of %s, with at least two levels; %d vertices elsewhere, %d levels" % [want_y, yout, distinct.size()])
	# Tie-break: lot 3 at (10,10) has equal neighbours 2 cells away on each side, ids 5 (left, cell 8) and 6 (right, cell 12); the
	# left one's nearer lot (cell 7, id 4) takes its own link, the right one (cell 12) links to lot 3 either way. Lot 3's own link to
	# the lower id 5 crosses x = 9.5 cells = 950 wu; with the ids swapped it links to the other and nothing crosses 950.
	var tie: ArrayMesh = sts.ribbons([_lot(4, 7, 10, 2), _lot(5, 8, 10, 2), _lot(3, 10, 10, 2), _lot(6, 12, 10, 2)], tf)
	_check(_has_vertex_x(_verts(tie), 950.0), "[STREETFN] GAP 4: a tie between equally near lots goes to the lower lot id: lot 3 links to lot 5, so the ribbon crosses x = 950 wu")
	var swap: ArrayMesh = sts.ribbons([_lot(4, 7, 10, 2), _lot(6, 8, 10, 2), _lot(3, 10, 10, 2), _lot(5, 12, 10, 2)], tf)
	_check(not _has_vertex_x(_verts(swap), 950.0) and _verts(swap).size() > 0, "[STREETFN] GAP 4 control: with the ids swapped lot 3 links to the right one (id 5) and no ribbon crosses x = 950 wu")
