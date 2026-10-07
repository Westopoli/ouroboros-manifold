extends "res://tests/support/vg_c_case.gd"

# VG-C piece C6 (scenes/ground3d/ground_units.gd): units in 3D. Proves S-010 and S-132 (walkers seen on the ground)
# with spec section 7's liberty "flyer altitude = layer floor + 150 wu with a shadow disc"; walker Y = ground height.
# API: GroundUnits.FLYER_CLEARANCE_WU, y_for(flyer: bool, ground_y: float, layer_floor_wu: float) -> float,
# and a Node3D: set_units(units, terrain, layer_floors_wu: Array, flyer_types: Array),
# unit_node(id) -> Node3D, shadow_of(id) -> Node3D or null.
# CONTROL: a flyer's Y differs from its ground height (altitude is not flattened).


func _run() -> void:
	var gu := _load(SCENES + "ground_units.gd")
	if gu == null:
		return
	var fx := _fixture()
	_check(gu.FLYER_CLEARANCE_WU == 150.0, "section 7: flyer clearance must be 150 wu, got %s" % gu.FLYER_CLEARANCE_WU)
	_check(absf(gu.y_for(false, 12.5, 300.0) - 12.5) < 0.001, "S-010: a walker's Y is the ground height")
	_check(absf(gu.y_for(true, 12.5, 300.0) - 450.0) < 0.001, "section 7: a flyer's Y is layer floor + 150 wu")
	_check(gu.y_for(true, 12.5, 300.0) != 12.5, "CONTROL: flyer Y equals ground height")
	var node = gu.new()
	root.add_child(node)
	await process_frame
	var t: Dictionary = fx.terrain()
	var floors := [0.0, 100.0, 400.0, 800.0, 1200.0]
	node.set_units(fx.frame()["units"], t, floors, [1])
	var walker: Node3D = node.unit_node(1)
	_check(walker != null, "S-010: no 3D node for unit 1")
	if walker != null:
		_check(absf(walker.position.y - fx.ground_y(250.0, 250.0)) < 0.05, "S-010: walker Y %f is not the ground height %f" % [walker.position.y, fx.ground_y(250.0, 250.0)])
		_check(absf(walker.position.x - 250.0) < 0.01 and absf(walker.position.z - 250.0) < 0.01, "S-010: walker world (x,y) must be Vector3(x, h, y)")
	var flyer: Node3D = node.unit_node(2)
	_check(flyer != null, "S-132: no 3D node for flyer unit 2")
	if flyer != null:
		_check(absf(flyer.position.y - (floors[2] + 150.0)) < 0.05, "section 7: flyer on layer 2 at Y %f, expected %f" % [flyer.position.y, floors[2] + 150.0])
		var sh: Node3D = node.shadow_of(2)
		_check(sh != null, "section 7: a flyer has no shadow disc")
		if sh != null:
			_check(absf(sh.position.y - fx.ground_y(450.0, 350.0)) < 0.5 and absf(sh.position.x - 450.0) < 0.01, "section 7: the shadow disc is not on the ground under the flyer")
	_check(node.shadow_of(1) == null, "section 7: a walker must not get a flyer shadow")
