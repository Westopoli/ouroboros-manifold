extends "res://tests/support/vg_c_case.gd"

# VG-C-land-one-projection (docs/northstar/plans/2026-10-07-visible-game-spec.md, paragraph "VG-C-land-one-projection").
# Rule pins: R-009-01@4af687, R-010-01@b3e461
# Proves R-010-01 and R-009-01 as the paragraph tags them [B R-010-01] [B R-009-01]; fixes DEC-landview-one-projection
# (docs/northstar/story_reviews/westley/decisions.md) and TD-VG-C-land-one-projection: in the land era every mark of a unit or
# a structure sits where the ground host projects its world position, at every camera, with or without a sim step.
#
# FIXTURE (the paragraph: the first 12 own units by ascending id of the frame the C plays use: greek_placeholder, seed 1,
# tick 0, via the pipe the way tests/qa/desktop/plays/C/s004.py _oracle opens the mission). Read from that oracle on 2026-10-23.
# All twelve: faction 0, type 0, tier 1, hp 250, layer 2, facing 0, sight 800.
#   id  1 (12220, 920)  id  2 (12250, 920)  id  3 (12280, 920)  id  4 (12220, 950)  id  5 (12250, 950)  id  6 (12280, 950)
#   id  7 (12220, 980)  id  8 (12250, 980)  id  9 (12280, 980)  id 10 (12320, 920)  id 11 (12350, 920)  id 12 (12380, 920)
# Structures of that frame (the paragraph names structures; the four of the oracle frame are used): id 0 (13500, 5850) owner 0,
# id 1 (13500, 5950) owner -1, id 2 (13500, 6050) owner 3, id 3 (13400, 6150) owner 3; type 2, hp 3000, cap 0.
# Canvas 24000 wu (map.canvas of that frame), cells 240 x 240 of 100 wu.
# DEFAULT CAMERA HEIGHT: read from the scene, scenes/ground3d/camera_rig_3d.gd:30 `_height := 3000.0`; the test reads
# rig.camera_height() after the view is built and asserts it equals START_HEIGHT 3000.0 (the paragraph's number).
#
# UNSTATED INTERFACE CHOICES (the paragraph does not fix these; the builder matches them or a test-defect row changes them):
#  1. Terrain: the pipe terrain dump is 736 KB of JSON and cannot sit in a test file, so the ground is a SYNTHETIC 240 x 240 dump of
#     the same shape (heights int32 cm, bands, walkable, no slopes, layer_floors_wu 0..4). The unit ids and positions are the real ones.
#  2. The death and the ability event: frame 1 (tick 0) carries the 12 units; frame 2 (tick 1) is the same 12 units with
#     events [[2, 12, -1, 1], [1, 1, 0]] (death of unit 12, which stays listed; ability 0 of unit 1) and the real profile list.
#     Deaths needs the unit in the previous frame, hence two loads. The event forms are deaths.gd:73-80 and abilities.gd:26-33.
#  3. camera_set argument: one Dictionary {height?, x?, y?} as args[0] (the paragraph writes `camera_set {height?, x?, y?}`); it answers
#     {"ok": true, ...}. The 600 wu pan is x = qa_state()["camera"]["x"] + 600 with y unchanged, made AFTER height 300.
#  4. marks_px: values {"icon": [x, y]} as Arrays of two floats; structures keyed "structure:<id>". hidden_on_land is a top-level
#     qa_state() key. The hidden terrain node is named "TerrainLayer" (the name hidden_on_land carries).
#  5. has_projector() -> bool is read on the nodes Deaths, Abilities and Ambient found under the view by find_child.
#  6. sight_discs (Architect ruling 2026-10-23): qa_state()["sight_discs"] exists and is empty until VG-A-sightdisc fills it; its shape is
#     not stated (Dictionary or Array), so the test asserts present and `.size() == 0`. The piece also calls FogLayer.set_terrain(_terrain).
#
# CONTROLS: c1 the camera really moved between the passes (the icons' expected position changed by more than 10 px); c2 the death
# wreck and the ability effect exist in the fixture frame (so a has_projector pass is not on an empty layer); c3 the direct
# rig pan with no camera_set verb (reds on main for the wrong behaviour, not for a missing verb); c4 in space the flat formula
# holds and hidden_on_land is [] (the space branch stays); c5 the flat distance of the squads from the ground projection is
# printed in the squads assertion (on main 263 px for the named worst unit).

const START_HEIGHT := 3000.0  # camera_rig_3d.gd:30 `_height := 3000.0`
const TOL_PX := 1.0
const OWN := [
	[1, 12220.0, 920.0], [2, 12250.0, 920.0], [3, 12280.0, 920.0], [4, 12220.0, 950.0], [5, 12250.0, 950.0], [6, 12280.0, 950.0],
	[7, 12220.0, 980.0], [8, 12250.0, 980.0], [9, 12280.0, 980.0], [10, 12320.0, 920.0], [11, 12350.0, 920.0], [12, 12380.0, 920.0]]
const STRUCTS := [[0, 13500.0, 5850.0, 0], [1, 13500.0, 5950.0, -1], [2, 13500.0, 6050.0, 3], [3, 13400.0, 6150.0, 3]]
const N := 240


func _terrain() -> Dictionary:
	var heights := PackedInt32Array()
	var bands := PackedByteArray()
	var walk := PackedByteArray()
	for j in N:
		for i in N:
			heights.append(i * 12 + j * 7 + (300 if (i / 10 + j / 10) % 2 == 0 else 0))
			bands.append(3)
			walk.append(1)
	return {"cells_w": N, "cells_h": N, "bands": bands, "walkable": walk, "heights": heights, "slopes": [],
		"layer_floors_wu": [0.0, 150.0, 300.0, 450.0, 600.0], "flyer_types": []}


func _profiles() -> Array:
	var out := []
	for t in 6:
		out.append({"type": t, "max_hp": 250, "range": 200, "interval": 1.0, "sensor": 800, "ability": t, "acd_max": 1500, "aoe": 0})
	return out


func _frame(tick: int, events: Array) -> Dictionary:
	var units := []
	var ids := []
	for p in OWN:
		units.append({"id": p[0], "faction": 0, "type": 0, "tier": 1, "x": p[1], "y": p[2], "hp": 250, "layer": 2, "facing": 0.0,
			"target": -1, "state": 0, "sight": 800})
		ids.append(p[0])
	var structs := []
	for s in STRUCTS:
		structs.append({"id": s[0], "type": 2, "owner": s[3], "x": s[1], "y": s[2], "hp": 3000, "stage": 0, "cap": 0, "nst": 600,
			"next_type": 2, "period": 600})
	return {"type": "tactical", "tick": tick, "player_faction": 0, "mission_over": false, "units": units, "structures": structs,
		"visible": {"0": ids}, "profiles": _profiles(), "events": events, "objectives": [],
		"map": {"canvas": 24000.0, "nodes": [], "cover": [], "obstacles": []}}


func _view(era: String) -> Node:
	var cfg = root.get_node("EraConfig")
	cfg.set_era(era)
	var v: Node = (load("res://scenes/tactical_c/tactical_view.tscn") as PackedScene).instantiate()
	root.add_child(v)
	await process_frame
	v.set_process(false)
	await process_frame
	cfg.set_era(era)
	v.load_frame(_frame(0, []))
	v.set_terrain(_terrain() if era == cfg.GROUND_ERA_ID else {})
	await process_frame
	v.load_frame(_frame(1, [[2, 12, -1, 1], [1, 1, 0]]))
	await process_frame
	return v


func _p2(a) -> Vector2:
	return Vector2(float(a[0]), float(a[1]))


# One camera pass: every id-carrying node under UnitVisuals and StructuresLayer within 1 px of the ground host projection.
func _pass(v: Node, label: String) -> float:
	var host = v._ground3d
	var worst := 0.0
	var uvn = v._node("UnitVisuals")
	for p in OWN:
		var want: Vector2 = host.to_screen(p[1], p[2])
		var n: Node2D = uvn.unit_node(p[0])
		_check(n != null and n.is_visible_in_tree(), "R-010-01 %s: no visible UnitVisuals node for unit %d" % [label, p[0]])
		if n != null:
			var d := n.global_position.distance_to(want)
			worst = maxf(worst, d)
			_check(d <= TOL_PX, "R-010-01 %s: unit %d node at %s, ground host projects %s (%.1f px off)" % [label, p[0], n.global_position, want, d])
	var sl = v._node("StructuresLayer")
	for s in STRUCTS:
		var want: Vector2 = host.to_screen(s[1], s[2])
		var n: Node2D = sl.structure_node(s[0])
		_check(n != null and n.is_visible_in_tree(), "R-009-01 %s: no visible StructuresLayer node for structure %d" % [label, s[0]])
		if n != null:
			var d := n.global_position.distance_to(want)
			worst = maxf(worst, d)
			_check(d <= TOL_PX, "R-009-01 %s: structure %d node at %s, ground host projects %s (%.1f px off)" % [label, s[0], n.global_position, want, d])
	var q: Dictionary = v.qa_state()
	var marks = q.get("marks_px", null)
	_check(marks is Dictionary, "R-010-01 %s: qa_state() has no marks_px Dictionary (interface not built)" % label)
	if marks is Dictionary:
		var px: Dictionary = q.get("units_px", {})
		for p in OWN:
			var m = marks.get(str(p[0]), null)
			_check(m is Dictionary and m.has("icon"), "R-010-01 %s: marks_px[\"%d\"] has no icon" % [label, p[0]])
			if m is Dictionary and m.has("icon"):
				var want: Vector2 = host.to_screen(p[1], p[2])
				_check(_p2(m["icon"]).distance_to(want) <= TOL_PX, "R-010-01 %s: marks_px icon of unit %d %s, projection %s" % [label, p[0], m["icon"], want])
				if px.has(str(p[0])):
					_check(_p2(m["icon"]).distance_to(_p2(px[str(p[0])])) <= TOL_PX, "R-010-01 %s: marks_px icon of unit %d %s differs from units_px %s" % [label, p[0], m["icon"], px[str(p[0])]])
		for s in STRUCTS:
			var m = marks.get("structure:%d" % s[0], null)
			_check(m is Dictionary and m.has("icon"), "R-009-01 %s: marks_px[\"structure:%d\"] has no icon" % [label, s[0]])
			if m is Dictionary and m.has("icon"):
				var want: Vector2 = host.to_screen(s[1], s[2])
				_check(_p2(m["icon"]).distance_to(want) <= TOL_PX, "R-009-01 %s: marks_px structure %d icon %s, projection %s" % [label, s[0], m["icon"], want])
	return worst


func _hidden(v: Node, label: String) -> void:
	var sq = v._node("UnitSquads")
	var flat_worst := 0.0
	for p in OWN:
		var flat: Vector2 = (Vector2(p[1], p[2]) - v._camera) * v._world_scale + Vector2(960.0, 540.0)
		flat_worst = maxf(flat_worst, flat.distance_to(v._ground3d.to_screen(p[1], p[2])))
	_check(sq != null and not sq.visible, "R-010-01 %s: UnitSquads is visible on land; its flat placement is %.0f px from the ground projection at worst (named control: 263 px on main)" % [label, flat_worst])
	var tl = v._ground_layer
	_check(tl != null and not tl.visible, "R-010-01 %s: TerrainLayer is visible on land" % label)
	if tl != null:
		_check(tl.name == "TerrainLayer", "R-010-01 %s: the terrain layer node is named %s, hidden_on_land carries TerrainLayer" % [label, tl.name])
	var h = v.qa_state().get("hidden_on_land", null)
	_check(h is Array and h.has("UnitSquads") and h.has("TerrainLayer"), "R-010-01 %s: hidden_on_land is %s, want UnitSquads and TerrainLayer" % [label, h])


func _camera(d: Node, args: Dictionary) -> void:
	var r: Dictionary = await d._dispatch("camera_set", [args])
	_check(bool(r.get("ok", false)), "camera_set %s answered %s (verb not built)" % [args, r])
	await process_frame


func _run() -> void:
	var cfg = root.get_node("EraConfig")
	var d = load("res://autoload/qa_daemon.gd").new()
	root.add_child(d)
	await process_frame
	var v: Node = await _view(cfg.GROUND_ERA_ID)
	current_scene = v
	var rig = v._rig()
	_check(rig != null, "no ground rig: the view made no Ground3D host")
	if rig == null:
		return
	_check(absf(rig.camera_height() - START_HEIGHT) < 0.01, "default camera height is %s, the paragraph names %s (camera_rig_3d.gd:30)" % [rig.camera_height(), START_HEIGHT])
	# c2: the fixture frame's events reached the fx layers
	_check(v._node("Deaths").wrecks().size() == 1, "c2: the death event of unit 12 made %d wrecks" % v._node("Deaths").wrecks().size())
	_check(v._node("Abilities").effects().size() == 1, "c2: the ability event of unit 1 made %d effects" % v._node("Abilities").effects().size())
	# default camera
	var w0 := _pass(v, "default camera h=%s" % rig.camera_height())
	_hidden(v, "default camera")
	var e0: Vector2 = v._ground3d.to_screen(OWN[0][1], OWN[0][2])
	# height 300
	await _camera(d, {"height": 300.0})
	_check(absf(rig.camera_height() - 300.0) < 0.01, "camera_set height 300 left the rig at %s" % rig.camera_height())
	_pass(v, "height 300")
	_hidden(v, "height 300")
	var e1: Vector2 = v._ground3d.to_screen(OWN[0][1], OWN[0][2])
	# pan 600 wu in +x with no step
	var cx := float(v.qa_state()["camera"]["x"])
	var cy := float(v.qa_state()["camera"]["y"])
	var tick0 := int(v.qa_state()["tick"])
	await _camera(d, {"x": cx + 600.0, "y": cy})
	_check(int(v.qa_state()["tick"]) == tick0, "the pan stepped the sim: tick %d to %d" % [tick0, int(v.qa_state()["tick"])])
	_pass(v, "pan +600 wu in x, no step")
	var e2: Vector2 = v._ground3d.to_screen(OWN[0][1], OWN[0][2])
	_check(e0.distance_to(e1) > 10.0 and e1.distance_to(e2) > 10.0, "c1: the camera did not move the projection of unit 1 (%s, %s, %s)" % [e0, e1, e2])
	# c5: the squads at a low camera reached with the rig only (no camera_set verb): the flat distance is in the message
	for _i in 60:
		if rig.camera_height() <= 300.0:
			break
		rig.zoom_by(-1)
	v._sync_from_rig()
	v._redraw()
	await process_frame
	_hidden(v, "c5 direct rig zoom to h=%s" % rig.camera_height())
	# c3: a pan of 600 wu made directly on the rig (after c5, at the low camera), then a redraw, with no camera_set verb
	rig.pan_to(Vector2(cx + 600.0, cy))
	v._sync_from_rig()
	v._redraw()
	await process_frame
	var host = v._ground3d
	var n1: Node2D = v._node("UnitVisuals").unit_node(1)
	var want3: Vector2 = host.to_screen(OWN[0][1], OWN[0][2])
	_check(n1 != null and n1.global_position.distance_to(want3) <= TOL_PX, "c3 R-010-01: after a rig pan and a redraw (no step) unit 1 stays at %s, the ground host projects %s (flat delta on main)" % [n1.global_position if n1 != null else null, want3])
	# fx projectors
	for n in ["Deaths", "Abilities", "Ambient"]:
		var fxn = v._node(n)
		_check(fxn != null and fxn.has_method("has_projector") and fxn.has_projector(), "R-010-01: %s has no valid projector on land (has_projector missing or false)" % n)
	var qd: Dictionary = v.qa_state()
	_check(qd.has("sight_discs") and qd["sight_discs"].size() == 0, "R-010-01: qa_state() sight_discs is %s, want the key present and empty (key missing on main)" % [qd.get("sight_discs", "<no key>")])
	_check(w0 >= 0.0, "worst default-camera offset is %s" % w0)
	v.queue_free()
	current_scene = null
	await process_frame
	# c4: the space branch keeps the flat formula; nothing is hidden
	var s: Node = await _view(cfg.SPACE_ERA_ID)
	var qs: Dictionary = s.qa_state()
	var hs = qs.get("hidden_on_land", null)
	_check(hs is Array and hs.is_empty(), "c4: hidden_on_land in space is %s, want []" % [hs])
	_check(s._ground3d == null, "c4: the space era has a ground host")
	var sqs = s._node("UnitSquads")
	_check(sqs != null and sqs.visible, "c4: UnitSquads is hidden in space")
	var un: Node2D = s._node("UnitVisuals").unit_node(1)
	var flat: Vector2 = (Vector2(OWN[0][1], OWN[0][2]) - s._camera) * s._world_scale + Vector2(960.0, 540.0)
	_check(un != null and un.global_position.distance_to(flat) <= TOL_PX, "c4: in space unit 1 is at %s, the flat formula gives %s" % [un.global_position if un != null else null, flat])
	cfg.set_era(cfg.SPACE_ERA_ID)
