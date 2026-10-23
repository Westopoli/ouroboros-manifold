extends Node3D
class_name Units3D

## Units in the 3D ground (visible-game lane C, C6; S-010, S-132). Walkers stand at the ground height, flyers at
## their layer floor + 150 wu (spec section 7) with a shadow disc on the ground below. Shapes are lane A's
## UnitVisuals.SHAPES lifted to flat 3D bodies; unit_visuals.gd is untouched.

const GroundPick := preload("res://scenes/ground3d/ground_pick.gd")
const UnitVisuals := preload("res://scenes/tactical_c/unit_visuals.gd")

const FLYER_CLEARANCE_WU := 150.0
# VG-C-unitscale (FINDING-unit-draw-overlap), DRAFT-unit-body-radius: the drawn mesh bounding box fits the 30 wu spawn lattice pitch (2 * OM_UNIT_COLLISION_RADIUS 15, csrc/om_constants.h:581, csrc/mission.c:2463); the body polygons reach 1.28 x the radius, so 11.5, not 15; shadow inside the body. Named draft, Westley may veto after the shot. See also tests/test_vg_c_unitscale.gd
const BODY_RADIUS_WU := 11.5
# VG-C-unit-ground-fit, DRAFT-unit-ground-lift: a walker body is lifted this far along the ground normal so it does not z-fight the ground. See also tests/test_vg_c_unit_ground_fit.gd
const UNIT_GROUND_LIFT_WU := 1.0
const SHADOW_RADIUS_WU := 10.0
const SHADOW_LIFT_WU := 0.5
const OWN_COLOUR := Color(0.2, 0.6, 1.0)
const OTHER_COLOUR := Color(1.0, 0.3, 0.3)

var local_faction := 0
var _nodes: Dictionary = {}
var _shadows: Dictionary = {}


static func y_for(flyer: bool, ground_y: float, layer_floor_wu: float) -> float:
	return layer_floor_wu + FLYER_CLEARANCE_WU if flyer else ground_y


static func _body(type: int, colour: Color) -> MeshInstance3D:
	var pts := PackedVector2Array()
	for p in UnitVisuals.SHAPES[posmod(type, UnitVisuals.SHAPES.size())]:
		pts.append(p * BODY_RADIUS_WU)
	var tris := Geometry2D.triangulate_polygon(pts)
	var verts := PackedVector3Array()
	for i in tris:
		verts.append(Vector3(pts[i].x, 0.0, pts[i].y))
	var arr := []
	arr.resize(Mesh.ARRAY_MAX)
	arr[Mesh.ARRAY_VERTEX] = verts
	var mesh := ArrayMesh.new()
	mesh.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arr)
	var mat := StandardMaterial3D.new()
	mat.albedo_color = colour
	mat.cull_mode = BaseMaterial3D.CULL_DISABLED
	mesh.surface_set_material(0, mat)
	var mi := MeshInstance3D.new()
	mi.mesh = mesh
	return mi


static func _disc() -> MeshInstance3D:
	var cyl := CylinderMesh.new()
	cyl.top_radius = SHADOW_RADIUS_WU
	cyl.bottom_radius = SHADOW_RADIUS_WU
	cyl.height = 0.1
	var mat := StandardMaterial3D.new()
	mat.albedo_color = Color(0.0, 0.0, 0.0, 0.45)
	mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	cyl.material = mat
	var mi := MeshInstance3D.new()
	mi.mesh = cyl
	return mi


func set_units(units: Array, terrain: Dictionary, layer_floors_wu: Array, flyer_types: Array) -> void:
	var seen := {}
	for u in units:
		var id := int(u.get("id", -1))
		seen[id] = true
		var x := float(u.get("x", 0.0))
		var z := float(u.get("y", 0.0))
		var gy := GroundPick.height_at(terrain, x, z)
		var flyer := int(u.get("type", 0)) in flyer_types
		var layer := clampi(int(u.get("layer", 0)), 0, maxi(layer_floors_wu.size() - 1, 0))
		var floor_wu := float(layer_floors_wu[layer]) if layer_floors_wu.size() > 0 else 0.0
		var n: Node3D = _nodes.get(id)
		if n == null:
			var own := int(u.get("faction", 0)) == local_faction
			n = _body(int(u.get("type", 0)), OWN_COLOUR if own else OTHER_COLOUR)
			add_child(n)
			_nodes[id] = n
		var facing := float(u.get("facing", 0.0))
		if flyer:
			n.position = Vector3(x, y_for(flyer, gy, floor_wu), z)
			n.rotation.y = -facing
		else:
			var r := BODY_RADIUS_WU
			var dx := Vector3(2.0 * r, GroundPick.height_at(terrain, x + r, z) - GroundPick.height_at(terrain, x - r, z), 0.0)
			var dz := Vector3(0.0, GroundPick.height_at(terrain, x, z + r) - GroundPick.height_at(terrain, x, z - r), 2.0 * r)
			var up := dz.cross(dx).normalized()
			var fwd := Vector3(cos(facing), 0.0, sin(facing))
			fwd = (fwd - up * fwd.dot(up)).normalized()
			n.transform = Transform3D(Basis(fwd, up, fwd.cross(up)), Vector3(x, gy, z) + up * UNIT_GROUND_LIFT_WU)
		var sh: Node3D = _shadows.get(id)
		if flyer and sh == null:
			sh = _disc()
			add_child(sh)
			_shadows[id] = sh
		elif not flyer and sh != null:
			sh.queue_free()
			_shadows.erase(id)
			sh = null
		if sh != null:
			sh.position = Vector3(x, gy + SHADOW_LIFT_WU, z)
	for id in _nodes.keys():
		if not seen.has(id):
			_nodes[id].queue_free()
			_nodes.erase(id)
			if _shadows.has(id):
				_shadows[id].queue_free()
				_shadows.erase(id)


func unit_node(id: int) -> Node3D:
	return _nodes.get(id)


func shadow_of(id: int) -> Node3D:
	return _shadows.get(id)


func heights() -> Dictionary:
	var out := {}
	for id in _nodes:
		out[str(id)] = _nodes[id].position.y
	return out


func shadow_ids() -> Array:
	return _shadows.keys()
