extends "res://tests/support/vg_c_case.gd"

# VG-E1 piece E1l (scenes/settlement/strongpoint_layer.gd, class StrongpointLayer, extends Node3D), spec rev 8
# "Lane E1 part b". Proves S-218 R-218-01 (strongpoint stands on its slope), R-218-05 (rubble state 2 = flat slab),
# R-193-07 style owner colour (StructuresLayer OWN/ENEMY/NEUTRAL colours; local faction = frame player_faction).
# Contract read by this test (the spec leaves the node shape open, so it reads the generic scene tree):
#   - one drawn MeshInstance3D per strongpoint (descendants of the layer, any depth);
#   - its colour is the albedo_color of material_override or surface 0 material;
#   - its height is mesh AABB y size times global scale y;
#   - strongpoints_drawn() returns the ids (ints, or dicts with "id").
# CONTROLS: the helpers see a hand-built node tree's colours and heights, and tell two different frames apart.

const LAYER := "res://scenes/settlement/strongpoint_layer.gd"
const STRUCT := "res://scenes/tactical_c/structures_layer.gd"


func _meshes(n: Node, out: Array) -> void:
	for c in n.get_children():
		if c is MeshInstance3D and (c as MeshInstance3D).mesh != null:
			out.append(c)
		_meshes(c, out)


func _colour(m: MeshInstance3D) -> Color:
	var mat: Material = m.material_override
	if mat == null:
		mat = m.mesh.surface_get_material(0) if m.mesh.get_surface_count() > 0 else null
	return (mat as StandardMaterial3D).albedo_color if mat is StandardMaterial3D else Color(-1, -1, -1)


func _height(m: MeshInstance3D) -> float:
	return m.mesh.get_aabb().size.y * m.global_transform.basis.get_scale().y


func _ids(layer: Node) -> Array:
	var out := []
	for e in layer.strongpoints_drawn():
		out.append(int(e["id"]) if e is Dictionary else int(e))
	out.sort()
	return out


func _sp(id: int, x: float, owner: int, state: int) -> Dictionary:
	return {"id": id, "x": x, "y": 300.0, "owner": owner, "state": state}


func _frame(sps: Array) -> Dictionary:
	return {"player_faction": 0, "units": [], "strongpoints": sps}


func _run() -> void:
	# CONTROLS for the readers, on a hand-built tree.
	var probe := Node3D.new()
	var tall := MeshInstance3D.new()
	var bm := BoxMesh.new()
	bm.size = Vector3(10, 30, 10)
	tall.mesh = bm
	var pm := StandardMaterial3D.new()
	pm.albedo_color = Color(0.1, 0.2, 0.3)
	tall.material_override = pm
	probe.add_child(tall)
	root.add_child(probe)
	var found := []
	_meshes(probe, found)
	_check(found.size() == 1 and _colour(found[0]) == Color(0.1, 0.2, 0.3) and is_equal_approx(_height(found[0]), 30.0), "CONTROL: mesh/colour/height readers miss a hand-built node")
	probe.queue_free()

	var s := _load(LAYER)
	var st := _load(STRUCT)
	if s == null or st == null:
		return
	var fx := _fixture()
	var layer = s.new()
	root.add_child(layer)
	await process_frame
	var three := [_sp(1, 200.0, 0, 1), _sp(2, 400.0, 1, 1), _sp(3, 600.0, -1, 0)]
	layer.set_frame(_frame(three))
	var before := []
	_meshes(layer, before)
	_check(before.size() == 0 and layer.strongpoints_drawn().size() == 0, "nothing is drawn before set_terrain: %d meshes" % before.size())

	layer.set_terrain(fx.terrain())
	layer.set_frame(_frame(three))
	await process_frame
	_check(_ids(layer) == [1, 2, 3], "strongpoints_drawn lists ids 1,2,3: %s" % [_ids(layer)])
	var ms := []
	_meshes(layer, ms)
	_check(ms.size() == 3, "three strongpoints draw three nodes: %d" % ms.size())
	if ms.size() == 3:
		ms.sort_custom(func(a, b): return a.global_position.x < b.global_position.x)
		var cols := [_colour(ms[0]), _colour(ms[1]), _colour(ms[2])]
		_check(cols[0] == st.OWN_COLOR, "owner 0 (local) draws the own colour: %s" % [cols[0]])
		_check(cols[1] == st.ENEMY_COLOR, "owner 1 draws the enemy colour: %s" % [cols[1]])
		_check(cols[2] != cols[0] and cols[2] != cols[1], "unowned draws a third, neutral colour: %s" % [cols[2]])
		_check(cols[2].r > 0.0 and absf(cols[2].r - cols[2].g) < 0.05 and absf(cols[2].g - cols[2].b) < 0.05, "unowned is grey: %s" % [cols[2]])
		var held_h := _height(ms[0])
		_check(held_h > 0.0, "a held strongpoint has height")

		# rubble: owner 0 state 2 draws a flat slab, lower than the held one
		layer.set_frame(_frame([_sp(1, 200.0, 0, 2), _sp(2, 400.0, 1, 1), _sp(3, 600.0, -1, 0)]))
		await process_frame
		var rs := []
		_meshes(layer, rs)
		rs.sort_custom(func(a, b): return a.global_position.x < b.global_position.x)
		_check(rs.size() == 3 and _height(rs[0]) < held_h, "R-218-05: rubble draws a slab below a held one (rubble %s, held %s)" % [_height(rs[0]) if rs.size() == 3 else -1.0, held_h])
		_check(rs.size() == 3 and _height(rs[1]) == _height(ms[1]), "a held neighbour keeps its height")

		# positive control: same strongpoints twice give the same transforms; a moved one differs
		var a := []
		layer.set_frame(_frame(three))
		await process_frame
		_meshes(layer, a)
		a.sort_custom(func(p, q): return p.global_position.x < q.global_position.x)
		layer.set_frame(_frame(three))
		await process_frame
		var b := []
		_meshes(layer, b)
		b.sort_custom(func(p, q): return p.global_position.x < q.global_position.x)
		var same: bool = a.size() == 3 and b.size() == 3
		for i in mini(a.size(), b.size()):
			same = same and a[i].global_transform == b[i].global_transform
		_check(same, "two frames with the same strongpoints give the same transforms")
		layer.set_frame(_frame([_sp(1, 220.0, 0, 1), _sp(2, 400.0, 1, 1), _sp(3, 600.0, -1, 0)]))
		await process_frame
		var c := []
		_meshes(layer, c)
		c.sort_custom(func(p, q): return p.global_position.x < q.global_position.x)
		_check(c.size() == 3 and c[0].global_transform != a[0].global_transform, "CONTROL: a moved strongpoint changes its transform")
