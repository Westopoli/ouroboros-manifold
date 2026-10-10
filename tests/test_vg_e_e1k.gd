extends "res://tests/support/vg_c_case.gd"

# VG-E piece E1k (scenes/settlement/settlement_layer.gd, class SettlementLayer). Proves S-193 R-193-01..09
# and S-218 as the client layer: lots from frame["lots"] draw as one MultiMesh of boxes (instance i = i-th lot
# in ascending id), stage 0 lower than stage 5, a lot on a steep cell is a cliff dwelling capped at stage 3,
# a street ribbon mesh joins stage-2+ lots within 3 cells and not 10 cells apart, nothing draws before
# set_terrain. Easing is 20 frames, so a frame is applied 25 times before heights are read.
# Positive controls: equal stages draw equal heights; the ribbon check is run on both near and far pairs;
# a flat terrain flags no cliff; Units3D on the same terrain is the harness control.

const LAYER := "res://scenes/settlement/settlement_layer.gd"
const W := 40
const H := 40


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


func _lot(id: int, cx: int, cy: int, stage: int) -> Dictionary:
	return {"id": id, "x": (cx + 0.5) * 100.0, "y": (cy + 0.5) * 100.0, "stage": stage, "building": 0, "owner": 0}


func _make(script: GDScript, t: Dictionary, lots: Array, settle := true) -> Node3D:
	var n: Node3D = script.new()
	root.add_child(n)
	n.set_terrain(t)
	for k in (25 if settle else 1):
		n.set_frame({"lots": lots})
	return n


func _mm(n: Node) -> MultiMeshInstance3D:
	for c in n.find_children("*", "MultiMeshInstance3D", true, false):
		return c
	return null


func _box_h(n: Node, i: int) -> float:
	var mm := _mm(n)
	if mm == null or mm.multimesh == null or i >= mm.multimesh.instance_count:
		return -1.0
	return mm.multimesh.get_instance_transform(i).basis.y.length()


func _ribbons(n: Node) -> int:
	var c := 0
	for m in n.find_children("*", "MeshInstance3D", true, false):
		var mesh: Mesh = m.mesh
		if mesh != null and mesh.get_surface_count() > 0 and mesh.surface_get_arrays(0)[Mesh.ARRAY_VERTEX].size() > 0:
			c += 1
	return c


func _find(drawn: Array, id: int) -> Dictionary:
	for d in drawn:
		if int(d.get("id", -1)) == id:
			return d
	return {}


func _run() -> void:
	# Groups, in run order. [CONTROL] and [SKELETON] are green once E1k-skel lands (ids, instance count, equal
	# boxes, nothing before set_terrain); [STAGE], [CLIFF] and [STREET] stay red until E1k fills the file.
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

	var s := _load(LAYER)
	if s == null:
		return
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

	# [SKELETON] positive control: equal stages, equal heights.
	var eq := []
	for k in 3:
		eq.append(_lot(20 + k, 3 + 4 * k, 3, 4))
	var le := _make(s, _terrain(true), eq)
	var h0 := _box_h(le, 0)
	_check(h0 > 0.0 and absf(h0 - _box_h(le, 1)) < 0.001 and absf(h0 - _box_h(le, 2)) < 0.001, "[SKELETON] control: equal stages must draw equal heights (%f)" % h0)
	le.queue_free()

	# [STAGE] stage heights, on the six-lot layer above.
	_check(_box_h(lay, 0) >= 0.0 and _box_h(lay, 0) < _box_h(lay, 5), "[STAGE] R-193-02: stage 0 box must be lower than stage 5 (got %f vs %f)" % [_box_h(lay, 0), _box_h(lay, 5)])
	_check(_box_h(lay, 1) < _box_h(lay, 4), "[STAGE] R-193-02: stage 1 lower than stage 4")
	lay.queue_free()

	# [CLIFF] stage-5 lot in the steep region (cell 35) capped at 3 and flagged; same lot on flat ground is not.
	# lots_drawn() entry keys "stage" and "cliff" are this test's reading; the spec (E1k paragraph) does not name them.
	var cl := [_lot(30, 35, 20, 5), _lot(31, 5, 20, 5)]
	var lc := _make(s, _terrain(true), cl)
	var d30 := _find(lc.lots_drawn(), 30)
	var d31 := _find(lc.lots_drawn(), 31)
	_check(bool(d30.get("cliff", false)), "[CLIFF] R-193-07: lot in the steep region must be flagged cliff")
	_check(int(d30.get("stage", 99)) <= 3, "[CLIFF] R-193-07: cliff lot capped at stage 3, got %s" % [d30.get("stage")])
	_check(not bool(d31.get("cliff", true)) and int(d31.get("stage", 0)) == 5, "[CLIFF] control: flat-ground lot is not cliff and keeps stage 5")
	_check(_box_h(lc, 0) < _box_h(lc, 1), "[CLIFF] R-193-07: capped cliff box lower than the uncapped stage-5 box")
	lc.queue_free()

	# [STREET] ribbon meshes are counted against a baseline layer of two stage-1 lots (no street) so any other
	# MeshInstance3D the layer owns does not count: near stage-2 pair adds a ribbon, far pair adds none.
	var base := _make(s, _terrain(false), [_lot(44, 10, 10, 1), _lot(45, 12, 10, 1)])
	var near := _make(s, _terrain(false), [_lot(40, 10, 10, 2), _lot(41, 12, 10, 2)])
	var far := _make(s, _terrain(false), [_lot(42, 5, 10, 2), _lot(43, 15, 10, 2)])
	var rb := _ribbons(base)
	_check(_ribbons(near) > rb, "[STREET] R-193-06: a street ribbon mesh must exist for two stage-2 lots 2 cells apart (got %d, baseline %d)" % [_ribbons(near), rb])
	_check(_ribbons(far) == rb, "[STREET] R-193-06: no street ribbon for two stage-2 lots 10 cells apart (got %d, baseline %d)" % [_ribbons(far), rb])
	base.queue_free()
	near.queue_free()
	far.queue_free()
