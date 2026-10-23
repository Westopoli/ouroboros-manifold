extends "res://tests/support/vg_c_case.gd"

# VG-C-unit-ground-fit (scenes/ground3d/ground_units.gd, class Units3D). Proves S-132 (units drawn on the 3D ground)
# and FINDING-s132-body-clip (a flat body placed horizontally lies under a slope). Spec paragraph "VG-C-unit-ground-fit"
# in docs/northstar/plans/2026-10-07-visible-game-spec.md (Architect 2026-10-22). No R- rule bears on body tilt.
# Named draft: DRAFT-unit-ground-lift 1.0 wu along the body normal. Ledger row TD-VG-C-ground-lift moves the walker
# height pins by that lift (tests/test_vg_c6b_ground_units_layers.gd, edited alongside this file).
#
# UNSTATED INTERFACE CHOICES (the paragraph gives none; each is a test-writer choice):
#  1. The body is the MeshInstance3D returned by Units3D.unit_node(id) (as today); its mesh vertices are read from
#     surface 0, Mesh.ARRAY_VERTEX, and taken to world space with the node's global_transform.
#  2. "local forward" is the body's local +x axis (Basis.x): today rotation.y = -facing maps local +x to the world
#     direction (cos f, 0, sin f) (sim x, sim y as world z); facing 0 points +x. The mesh lies in local x-z, up is local +y.
#  3. The lift is applied to the ground point (x, h(x, z), z): position = that point + n * 1.0.
#  4. The plane normal n is computed here from the paragraph's formula (four samples of GroundPick.height_at at
#     r = BODY_RADIUS_WU), not read from the product.
#  5. Flyers are asserted unchanged: y = layer floor + 150, up (0, 1, 0), fed through set_units' flyer_types argument.
#  6. Tolerances: 1e-3 wu on a vertex against the ground (float epsilon on mesh arithmetic), 0.01 wu on positions,
#     up . n above 0.99 (the paragraph's number), 1e-3 on unit-length and perpendicularity checks.
#
# Positive control (spec): the un-fixed placement (lift 0, up (0, 1, 0)) fails the vertex predicate on the 30-degree
# fixture. It is built here from the body mesh alone (position (x, ground, z), rotation.y = -facing) and uses the same
# predicate as the live assertion; it is green on main (it needs no product change) and proves the predicate can fail.

const GroundPick := preload("res://scenes/ground3d/ground_pick.gd")
const CELL := 100.0
const W := 8 # spec: cells_w and cells_h 8
const H := 8
const TAN30 := 0.5773502691896258
const LIFT := 1.0 # DRAFT-unit-ground-lift
const EPS := 0.001
const FACING_EPS := 0.0001 # spec: f and f + pi dot -1 and perpendicular to n within 1e-4
const FLAT_Y_EPS := 0.05 # DRAFT-flat-y-eps
const UP_DOT := 0.99 # DRAFT-ground-fit-up-dot
const FACINGS := [0.0, 1.0, 2.5, -2.0]
const POSITIONS := [[300.0, 300.0], [500.0, 250.0], [450.0, 600.0], [600.0, 500.0]] # all >= 150 wu from every edge


# 30-degree plane: rises tan30 * 100 wu per 100 wu cell along x (tilt_x) or along z (not tilt_x). Heights int32 cm.
func _plane(tilt_x: bool) -> Dictionary:
	var hs := PackedInt32Array()
	var walk := PackedByteArray()
	for j in H:
		for i in W:
			hs.append(int(round((i if tilt_x else j) * TAN30 * CELL * 100.0)))
			walk.append(1)
	return {"cells_w": W, "cells_h": H, "heights": hs, "walkable": walk, "bands": walk.duplicate(), "slopes": []}


func _flat(cm: int) -> Dictionary:
	var hs := PackedInt32Array()
	var walk := PackedByteArray()
	for j in H:
		for i in W:
			hs.append(cm)
			walk.append(1)
	return {"cells_w": W, "cells_h": H, "heights": hs, "walkable": walk, "bands": walk.duplicate(), "slopes": []}


func _units(flyer_too: bool) -> Array:
	var out := []
	for k in POSITIONS.size():
		out.append({"id": k + 1, "faction": 0, "type": k % 3, "x": POSITIONS[k][0], "y": POSITIONS[k][1], "layer": 0, "facing": FACINGS[k]})
	if flyer_too:
		out.append({"id": 9, "faction": 0, "type": 5, "x": 400.0, "y": 400.0, "layer": 1, "facing": 0.5})
	return out


# The paragraph's normal: n = dz x dx normalised, dx = (2r, h(x+r) - h(x-r), 0), dz = (0, h(z+r) - h(z-r), 2r).
func _normal(t: Dictionary, x: float, z: float, r: float) -> Vector3:
	var dx := Vector3(2.0 * r, GroundPick.height_at(t, x + r, z) - GroundPick.height_at(t, x - r, z), 0.0)
	var dz := Vector3(0.0, GroundPick.height_at(t, x, z + r) - GroundPick.height_at(t, x, z - r), 2.0 * r)
	return dz.cross(dx).normalized()


func _verts(mi: MeshInstance3D) -> PackedVector3Array:
	return mi.mesh.surface_get_arrays(0)[Mesh.ARRAY_VERTEX]


# The one predicate for the live assertion and the control: how many world-space vertices lie under the ground.
func _under(t: Dictionary, verts: PackedVector3Array, xf: Transform3D) -> int:
	var n := 0
	for v in verts:
		var w := xf * v
		if w.y < GroundPick.height_at(t, w.x, w.z) - EPS:
			n += 1
	return n


func _fed(t: Dictionary, units: Array) -> Node3D:
	var gu := _load(SCENES + "ground_units.gd")
	if gu == null:
		return null
	var node: Node3D = gu.new()
	root.add_child(node)
	await process_frame
	node.set_units(units, t, [0.0, 100.0], [5])
	await process_frame
	return node


func _run() -> void:
	var gu := _load(SCENES + "ground_units.gd")
	if gu == null:
		return
	var r: float = gu.BODY_RADIUS_WU
	for tilt_x in [true, false]:
		var fwds := {}
		var tag := "30-degree plane tilted along %s" % ("x" if tilt_x else "z")
		var t := _plane(tilt_x)
		# CONTROL: the fixture really is 30 degrees (normal . up = cos 30).
		var n0 := _normal(t, 500.0, 500.0, r)
		_check(absf(n0.dot(Vector3.UP) - cos(deg_to_rad(30.0))) < 0.002, "CONTROL: %s: fixture normal . up %f is not cos 30" % [tag, n0.dot(Vector3.UP)])
		var node := await _fed(t, _units(true))
		if node == null:
			return
		for k in POSITIONS.size():
			var id := k + 1
			var x: float = POSITIONS[k][0]
			var z: float = POSITIONS[k][1]
			var f: float = FACINGS[k]
			var body: MeshInstance3D = node.unit_node(id)
			_check(body != null, "S-132: %s: no body for walker %d" % [tag, id])
			if body == null:
				continue
			var xf: Transform3D = body.global_transform
			var verts := _verts(body)
			# POSITIVE CONTROL: the un-fixed placement (lift 0, up (0, 1, 0)) puts vertices under this plane.
			var unfixed := Transform3D(Basis(Vector3.UP, -f), Vector3(x, GroundPick.height_at(t, x, z), z))
			_check(_under(t, verts, unfixed) > 0, "CONTROL: %s walker %d: the un-fixed placement has no vertex under the ground, the predicate cannot fail" % [tag, id])
			# (1) no vertex under the ground
			var under := _under(t, verts, xf)
			_check(under == 0, "FINDING-s132-body-clip: %s walker %d: %d of %d body vertices are under the ground" % [tag, id, under, verts.size()])
			# (2) up follows the plane normal
			var n := _normal(t, x, z, r)
			var up := xf.basis.y.normalized()
			_check(up.dot(n) > UP_DOT, "S-132: %s walker %d: body up . plane normal is %f, not above 0.99 (DRAFT-ground-fit-up-dot)" % [tag, id, up.dot(n)])
			# (3) lift 1.0 wu along n above the ground point
			var want := Vector3(x, GroundPick.height_at(t, x, z), z) + n * LIFT
			_check(xf.origin.distance_to(want) < 0.01, "DRAFT-unit-ground-lift: %s walker %d: body origin %s, expected ground + 1.0 along n = %s" % [tag, id, xf.origin, want])
			# (4) facing still turns the body about n: forward = facing projected onto the plane of n
			var face := Vector3(cos(f), 0.0, sin(f))
			var proj := (face - n * face.dot(n)).normalized()
			var fwd := xf.basis.x.normalized()
			fwds[k] = fwd
			_check(fwd.distance_to(proj) < EPS, "S-132: %s walker %d: body forward %s is not the facing %f projected on the plane %s" % [tag, id, fwd, f, proj])
			# facing f + pi gives the opposite local x: re-feed the same unit turned by pi and compare
			_check(absf(fwd.dot(n)) < FACING_EPS, "S-132: %s walker %d: body forward is not perpendicular to n within 1e-4 (dot %f)" % [tag, id, fwd.dot(n)])
			_check(xf.basis.z.distance_to(xf.basis.x.cross(xf.basis.y)) < EPS, "S-132: %s walker %d: body basis z is not x cross y" % [tag, id])
			_check(absf(fwd.dot(up)) < EPS and absf(xf.basis.x.length() - 1.0) < EPS and absf(xf.basis.y.length() - 1.0) < EPS and absf(xf.basis.z.length() - 1.0) < EPS, "S-132: %s walker %d: body basis is not orthonormal (no shear, no scale)" % [tag, id])
		var turned: Array = _units(true)
		for u in turned:
			u["facing"] = float(u["facing"]) + PI
		node.set_units(turned, t, [0.0, 100.0], [5])
		await process_frame
		for k in POSITIONS.size():
			var b2: MeshInstance3D = node.unit_node(k + 1)
			var xa: Vector3 = b2.global_transform.basis.x if b2 != null else Vector3.ZERO
			var xb: Vector3 = fwds[k]
			_check(absf(xa.dot(xb) + 1.0) < FACING_EPS, "S-132: %s walker %d: facings f and f + pi must give local x vectors with dot -1 within 1e-4, got %f" % [tag, k + 1, xa.dot(xb)])
		# Flyers unchanged: layer floor + 150, up (0, 1, 0), whatever the ground below.
		var fl: Node3D = node.unit_node(9)
		_check(fl != null and absf(fl.position.y - 250.0) < 0.01 and fl.global_transform.basis.y.distance_to(Vector3.UP) < EPS, "S-132: %s: flyer must stay at floor + 150 = 250 with up (0, 1, 0), got %s" % [tag, fl.global_transform if fl != null else null])
		node.queue_free()

	# Flat ground: up is (0, 1, 0), y is ground + 1.0, facing turns about up (forward (cos f, 0, sin f)).
	var tf := _flat(500)
	var nf := await _fed(tf, _units(false))
	for k in POSITIONS.size():
		var body: MeshInstance3D = nf.unit_node(k + 1)
		_check(body != null, "S-132: flat: no body for walker %d" % (k + 1))
		if body == null:
			continue
		var xf: Transform3D = body.global_transform
		_check(xf.basis.y.distance_to(Vector3.UP) < EPS, "S-132: flat ground walker %d: body up %s is not (0, 1, 0)" % [k + 1, xf.basis.y])
		_check(absf(xf.origin.y - (5.0 + LIFT)) < FLAT_Y_EPS, "DRAFT-unit-ground-lift: flat ground walker %d: y %f, expected ground 5.0 + 1.0" % [k + 1, xf.origin.y])
		_check(xf.basis.x.distance_to(Vector3(cos(FACINGS[k]), 0.0, sin(FACINGS[k]))) < EPS, "S-132: flat ground walker %d: facing %f does not turn the body about up, forward %s" % [k + 1, FACINGS[k], xf.basis.x])
		_check(absf(float(nf.heights().get(str(k + 1), -9999.0)) - (5.0 + LIFT)) < FLAT_Y_EPS, "DRAFT-unit-ground-lift: heights() for walker %d must report position.y = ground + 1.0, got %s" % [k + 1, nf.heights().get(str(k + 1))])
	nf.queue_free()
