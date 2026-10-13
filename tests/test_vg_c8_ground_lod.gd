extends "res://tests/support/vg_c_case.gd"

# VG-C piece C8 (scenes/ground3d/ground_lod.gd): level of detail. Proves S-236 R-236-01 (continuous detail from one
# unit up to the map view; the mockup had one mesh, scout 4). The numeric no-pop tolerance is Westley's and lives in
# test_vg_c8_park_nopop.gd. API: GroundLod.new(): set_terrain(t), level_count() -> int, level_for(camera_height) -> int
# (0 finest), blend_for(camera_height) -> float 0..1, mesh_for(level) -> MeshInstance3D.
# CONTROL: a deliberately skipping sequence [0, 2] is rejected by the same step check.


func _steps_ok(seq: Array) -> bool:
	for i in range(1, seq.size()):
		if absi(int(seq[i]) - int(seq[i - 1])) > 1:
			return false
	return true


func _verts(mi: MeshInstance3D) -> int:
	return (mi.mesh as ArrayMesh).surface_get_arrays(0)[Mesh.ARRAY_VERTEX].size()


func _run() -> void:
	var gl := _load(SCENES + "ground_lod.gd")
	if gl == null:
		return
	var fx := _fixture()
	var lod = gl.new()
	lod.set_terrain(fx.terrain())
	_check(lod.level_count() >= 2, "R-236-01: fewer than two detail levels (%d)" % lod.level_count())
	var seq: Array = []
	var levels_ok := true
	var last := 0
	for k in 600:
		var h := 50.0 + k * 100.0
		var l: int = lod.level_for(h)
		seq.append(l)
		if l < last or l < 0 or l >= lod.level_count():
			levels_ok = false
		last = l
		var b: float = lod.blend_for(h)
		if b < 0.0 or b > 1.0:
			levels_ok = false
	_check(levels_ok, "R-236-01: level_for must rise monotonically with height inside 0..level_count-1 and blend_for stay in 0..1")
	_check(_steps_ok(seq), "R-236-01: a level is skipped between adjacent camera heights (pop)")
	_check(not _steps_ok([0, 2]), "CONTROL: the step check accepts a skipped level")
	_check(int(seq[-1]) == lod.level_count() - 1 and int(seq[0]) == 0, "R-236-01: the sweep must reach both the finest and coarsest level")
	var prev := 1 << 30
	var box0 := AABB()
	for l in lod.level_count():
		var mi: MeshInstance3D = lod.mesh_for(l)
		_check(mi != null and mi.mesh != null, "R-236-01: no mesh for level %d" % l)
		if mi == null or mi.mesh == null:
			return
		_check(_verts(mi) <= prev, "R-236-01: level %d has more vertices than the finer level" % l)
		prev = _verts(mi)
		if l == 0:
			box0 = mi.get_aabb()
		else:
			var b := mi.get_aabb()
			_check(absf(b.position.x - box0.position.x) < 0.01 and absf(b.end.x - box0.end.x) < 0.01
				and absf(b.position.z - box0.position.z) < 0.01 and absf(b.end.z - box0.end.z) < 0.01,
				"R-236-01: level %d covers a different footprint than level 0 (an edge pops)" % l)
