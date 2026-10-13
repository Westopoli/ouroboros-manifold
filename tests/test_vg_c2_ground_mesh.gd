extends "res://tests/support/vg_c_case.gd"

# VG-C piece C2 (scenes/ground3d/ground_mesh.gd). Proves S-236 / R-236-02: the five band steps are
# drawn as real height difference, the heights come from section 2's terrain_dump `heights`
# (int32 cm, 100 cm = 1 wu) sampled at cell centres (i + 0.5) * 100 wu, world (x, y) -> Vector3(x, h, y).
# Positive control: a flat copy of the same terrain must NOT pass the height check.


func _vertices(mi: MeshInstance3D) -> PackedVector3Array:
	var m := mi.mesh as ArrayMesh
	return m.surface_get_arrays(0)[Mesh.ARRAY_VERTEX]


func _has_vertex(v: PackedVector3Array, p: Vector3) -> bool:
	for q in v:
		if absf(q.x - p.x) < 0.01 and absf(q.z - p.z) < 0.01 and absf(q.y - p.y) < 0.01:
			return true
	return false


func _heights_ok(mi: MeshInstance3D, t: Dictionary, fx) -> bool:
	var v := _vertices(mi)
	for j in fx.H:
		for i in fx.W:
			var p := Vector3((i + 0.5) * fx.CELL_WU, fx.heights_cm(i, j) / 100.0, (j + 0.5) * fx.CELL_WU)
			if not _has_vertex(v, p):
				return false
	return true


func _run() -> void:
	var gm := _load(SCENES + "ground_mesh.gd")
	if gm == null:
		return
	var fx := _fixture()
	var t: Dictionary = fx.terrain()
	var mi = gm.build(t)
	_check(mi is MeshInstance3D, "S-236 R-236-02: GroundMesh.build(terrain) must return a MeshInstance3D")
	if not (mi is MeshInstance3D) or mi.mesh == null:
		return
	_check(mi.mesh.get_surface_count() >= 1, "S-236: the ground mesh has no surface")
	_check(_vertices(mi).size() >= fx.W * fx.H, "S-236: fewer vertices than cells (%d)" % _vertices(mi).size())
	_check(_heights_ok(mi, t, fx), "S-236 R-236-02: a cell-centre vertex does not sit at heights[] / 100 wu (half-cell offset)")
	var flat: Dictionary = t.duplicate()
	var zeros := PackedInt32Array()
	zeros.resize(fx.W * fx.H)
	flat["heights"] = zeros
	var mf = gm.build(flat)
	_check(not _heights_ok(mf, t, fx), "CONTROL: a flat terrain passes the height check, the detector is blind")
	var arrays: Array = (mi.mesh as ArrayMesh).surface_get_arrays(0)
	_check(arrays[Mesh.ARRAY_COLOR] != null and (arrays[Mesh.ARRAY_COLOR] as PackedColorArray).size() == _vertices(mi).size(),
		"S-236: no per-vertex colour (band ramp) on the ground mesh")
