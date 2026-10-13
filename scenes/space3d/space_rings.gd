extends Node3D
class_name SpaceRings

## VG-D-VIEW unit 2 (R-246-04, Q-S3-02): a flat ring under every drawn unit on its sheet, coloured by the unit's layer; a unit in
## transit also gets a dashed ring on its destination sheet. Rings are never faded by the tube (they draw through it, like their units).
## See also: docs/northstar/plans/2026-10-13-d-view-spec.md "Layer indicators"; tests/test_vg_d_view.gd _test_rings_*.

const LayerViewScript := preload("res://scenes/tactical_c/layer_view.gd")

# DRAFT-space-layer-gap, Q-246-01 (a). See also: space_view.gd LAYER_GAP_WU (same value, pinned there by a parity test).
const LAYER_GAP_WU := 1000.0
# DRAFT-sheet-thickness plate 60 (scenes/mockups/landscape/kits/space.json "plate"); sheet top = layer * gap + thickness.
const PLATE_THICKNESS_WU := 60.0
# d-view spec rev 1, gap 10 null action, Architect may veto on the shot: ring y = sheet top + 2.0.
const RING_LIFT_WU := 2.0
# DRAFT-ring-radius 1.2 x Units3D.BODY_RADIUS_WU.
const RING_RADIUS_FACTOR := 1.2
# DRAFT-ring-width 6 wu (d-view spec INTERFACE RING_WIDTH_WU).
const RING_WIDTH_WU := 6.0
# 24 segments as the strip's draw_arc ring (scenes/tactical_c/layer_view.gd:147); the dashed ring keeps every other segment.
const RING_SEGMENTS := 24

var _solid_mesh: ArrayMesh
var _dashed_mesh: ArrayMesh
var _materials: Array = []
# id -> MeshInstance3D
var _rings: Dictionary = {}
var _dest_rings: Dictionary = {}


func _ready() -> void:
	_ensure_assets()


func update(items: Array) -> void:
	_ensure_assets()
	var seen := {}
	for it in items:
		var id := int(it.get("id", -1))
		seen[id] = true
		var x := float(it.get("x", 0.0))
		var z := float(it.get("y", 0.0))
		var layer := _clamp_layer(int(it.get("layer", 0)))
		var dest := int(it.get("dest_layer", -1))
		var ring: MeshInstance3D = _rings.get(id)
		if ring == null:
			ring = _make_ring(false)
			_rings[id] = ring
		_place(ring, x, z, layer)
		if dest >= 0:
			var dring: MeshInstance3D = _dest_rings.get(id)
			if dring == null:
				dring = _make_ring(true)
				_dest_rings[id] = dring
			_place(dring, x, z, _clamp_layer(dest))
		elif _dest_rings.has(id):
			_dest_rings[id].queue_free()
			_dest_rings.erase(id)
	for id in _rings.keys():
		if not seen.has(id):
			_rings[id].queue_free()
			_rings.erase(id)
			if _dest_rings.has(id):
				_dest_rings[id].queue_free()
				_dest_rings.erase(id)


func ring_of(id: int) -> Variant:
	return _readout(_rings.get(id), false)


func dest_ring_of(id: int) -> Variant:
	return _readout(_dest_rings.get(id), true)


func ring_count() -> int:
	return _rings.size()


func dest_ring_count() -> int:
	return _dest_rings.size()


func _readout(ring: MeshInstance3D, dashed: bool) -> Variant:
	if ring == null:
		return null
	var layer: int = ring.get_meta("layer")
	return {
		"layer": layer,
		"y": ring.position.y,
		"colour": LayerViewScript.LAYER_COLOURS[layer],
		"radius": RING_RADIUS_FACTOR * Units3D.BODY_RADIUS_WU,
		"dashed": dashed,
	}


func _clamp_layer(layer: int) -> int:
	return clampi(layer, 0, LayerViewScript.LAYER_COUNT - 1)


func _make_ring(dashed: bool) -> MeshInstance3D:
	var mi := MeshInstance3D.new()
	mi.mesh = _dashed_mesh if dashed else _solid_mesh
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	add_child(mi)
	return mi


func _place(ring: MeshInstance3D, x: float, z: float, layer: int) -> void:
	ring.position = Vector3(x, layer * LAYER_GAP_WU + PLATE_THICKNESS_WU + RING_LIFT_WU, z)
	ring.material_override = _materials[layer]
	ring.set_meta("layer", layer)


func _ensure_assets() -> void:
	if _solid_mesh != null:
		return
	# liberty 2026-10-12: an annulus ArrayMesh (the spec allows torus or annulus), unshaded, one material per layer, no transparency.
	_solid_mesh = _annulus(false)
	_dashed_mesh = _annulus(true)
	for c in LayerViewScript.LAYER_COLOURS:
		var mat := StandardMaterial3D.new()
		mat.albedo_color = c
		mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
		mat.cull_mode = BaseMaterial3D.CULL_DISABLED
		_materials.append(mat)


static func _annulus(dashed: bool) -> ArrayMesh:
	var mid := RING_RADIUS_FACTOR * Units3D.BODY_RADIUS_WU
	var r_in := mid - RING_WIDTH_WU * 0.5
	var r_out := mid + RING_WIDTH_WU * 0.5
	var verts := PackedVector3Array()
	for i in range(RING_SEGMENTS):
		if dashed and i % 2 == 1:
			continue
		var a0 := TAU * float(i) / float(RING_SEGMENTS)
		var a1 := TAU * float(i + 1) / float(RING_SEGMENTS)
		var i0 := Vector3(cos(a0) * r_in, 0.0, sin(a0) * r_in)
		var o0 := Vector3(cos(a0) * r_out, 0.0, sin(a0) * r_out)
		var i1 := Vector3(cos(a1) * r_in, 0.0, sin(a1) * r_in)
		var o1 := Vector3(cos(a1) * r_out, 0.0, sin(a1) * r_out)
		verts.append_array(PackedVector3Array([i0, o0, o1, i0, o1, i1]))
	var arr := []
	arr.resize(Mesh.ARRAY_MAX)
	arr[Mesh.ARRAY_VERTEX] = verts
	var mesh := ArrayMesh.new()
	mesh.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arr)
	return mesh
