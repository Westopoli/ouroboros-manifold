extends Node3D

const QaPlants := preload("res://scenes/mockups/_shared/qa_plants.gd")

const HIT_FLASH_TICKS := 7
const DEATH_BLOOM_TICKS := 10
const DEATH_REMOVE_TICKS := 80
const DRIFT_WU_PER_TICK := 0.6
const DRIFT_CAP_TICKS := 40.0
const PING_LIFETIME_TICKS := 30
const FLASH_BOOST := Color(1.0, 0.95, 0.8, 1.0)
const DEATH_BOOST := Color(1.0, 0.85, 0.55, 1.0)
const WRECK_DARK := Color(0.12, 0.12, 0.12, 1.0)
const SQUAD_OFFSETS: Array[Vector2] = [Vector2.ZERO, Vector2(-0.7, 0.6), Vector2(0.7, 0.6), Vector2(-1.3, 1.15), Vector2(1.3, 1.15)]
const SHAPE_POINTS := {
	"swept_dart": [Vector2(0, -0.5), Vector2(0.15, 0.15), Vector2(0, 0.5), Vector2(-0.15, 0.15)],
	"flat_wing": [Vector2(0, -0.5), Vector2(0.5, 0.3), Vector2(0.15, 0.5), Vector2(-0.15, 0.5), Vector2(-0.5, 0.3)],
	"wedge_slab": [Vector2(-0.5, -0.5), Vector2(0.5, -0.5), Vector2(0.3, 0.5), Vector2(-0.3, 0.5)],
	"spire_radial": [Vector2(0.5, 0), Vector2(0.35, 0.35), Vector2(0, 0.5), Vector2(-0.35, 0.35), Vector2(-0.5, 0), Vector2(-0.35, -0.35), Vector2(0, -0.5), Vector2(0.35, -0.35)],
	"long_barrel": [Vector2(0, -0.5), Vector2(0.12, -0.35), Vector2(0.12, 0.4), Vector2(0, 0.5), Vector2(-0.12, 0.4), Vector2(-0.12, -0.35)],
	"wide_block": [Vector2(-0.5, -0.35), Vector2(0.5, -0.35), Vector2(0.5, 0.35), Vector2(-0.5, 0.35)],
}

var roster: Roster
var current_tick: int = 0
var wrecks_active: int = 0
var flashes_active: int = 0

var _batches: Dictionary = {}
var _mesh_cache: Dictionary = {}
var _mat_cache: Dictionary = {}
var _extent_cache: Dictionary = {}
var _selected: Dictionary = {}
var _sel_rings: Dictionary = {}
var _pings: Array = []
var _ping_root: Node3D


func _ready() -> void:
	_ping_root = Node3D.new()
	_ping_root.name = "Pings"
	add_child(_ping_root)


func set_roster(r: Roster) -> void:
	roster = r
	_mesh_cache.clear()
	_mat_cache.clear()
	_rebuild_batches()


func _rebuild_batches() -> void:
	if roster == null:
		return
	for role in Roster.ROLE_ORDER:
		for faction in [0, 1]:
			var key := "%s_%d" % [role, faction]
			var mmi: MultiMeshInstance3D = _batches.get(key)
			if mmi == null:
				mmi = MultiMeshInstance3D.new()
				var mm := MultiMesh.new()
				mm.transform_format = MultiMesh.TRANSFORM_3D
				mm.use_colors = true
				mm.instance_count = 64
				mm.visible_instance_count = 0
				mmi.multimesh = mm
				mmi.name = "Batch_%s" % key
				mmi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_ON
				add_child(mmi)
				_batches[key] = mmi
			mmi.multimesh.mesh = _get_mesh(role)
			mmi.material_override = _get_material(role, faction)


func _get_material(role: String, faction: int) -> StandardMaterial3D:
	var key := "%s_%d" % [role, faction]
	if _mat_cache.has(key):
		return _mat_cache[key]
	var mat := StandardMaterial3D.new()
	var color_key := "faction_%d" % faction
	mat.albedo_color = Color(String(roster.palette.get(color_key, "#ffffff")))
	mat.roughness = 0.7
	_mat_cache[key] = mat
	return mat


func _get_mesh(role: String) -> Mesh:
	var shape := String(roster.get_silhouette(role).get("shape", "wide_block"))
	if _mesh_cache.has(shape):
		return _mesh_cache[shape]
	var points: Array = SHAPE_POINTS.get(shape, SHAPE_POINTS["wide_block"])
	var mesh := _build_spire(points) if shape == "spire_radial" else _build_prism(points)
	_mesh_cache[shape] = mesh
	return mesh


func _build_spire(points: Array) -> ArrayMesh:
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	var n := points.size()
	var base_h := 0.55
	for i in range(1, n - 1):
		st.add_vertex(Vector3(points[0].x, base_h, points[0].y))
		st.add_vertex(Vector3(points[i].x, base_h, points[i].y))
		st.add_vertex(Vector3(points[i + 1].x, base_h, points[i + 1].y))
	for i in range(1, n - 1):
		st.add_vertex(Vector3(points[0].x, 0.0, points[0].y))
		st.add_vertex(Vector3(points[i + 1].x, 0.0, points[i + 1].y))
		st.add_vertex(Vector3(points[i].x, 0.0, points[i].y))
	for i in range(n):
		var a: Vector2 = points[i]
		var b: Vector2 = points[(i + 1) % n]
		st.add_vertex(Vector3(a.x, base_h, a.y))
		st.add_vertex(Vector3(a.x, 0.0, a.y))
		st.add_vertex(Vector3(b.x, 0.0, b.y))
		st.add_vertex(Vector3(a.x, base_h, a.y))
		st.add_vertex(Vector3(b.x, 0.0, b.y))
		st.add_vertex(Vector3(b.x, base_h, b.y))
	var apex := Vector3(0.0, 1.0, 0.0)
	for i in range(n):
		var a: Vector2 = points[i]
		var b: Vector2 = points[(i + 1) % n]
		st.add_vertex(Vector3(a.x, base_h, a.y))
		st.add_vertex(Vector3(b.x, base_h, b.y))
		st.add_vertex(apex)
	st.generate_normals()
	return st.commit()


func _get_shape_extent(shape: String) -> Vector2:
	if _extent_cache.has(shape):
		return _extent_cache[shape]
	var points: Array = SHAPE_POINTS.get(shape, SHAPE_POINTS["wide_block"])
	var min_x := INF
	var max_x := -INF
	var min_z := INF
	var max_z := -INF
	for p in points:
		min_x = min(min_x, p.x)
		max_x = max(max_x, p.x)
		min_z = min(min_z, p.y)
		max_z = max(max_z, p.y)
	var extent := Vector2(max_x - min_x, max_z - min_z)
	_extent_cache[shape] = extent
	return extent


func _build_prism(points: Array) -> ArrayMesh:
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	var n := points.size()
	for i in range(1, n - 1):
		st.add_vertex(Vector3(points[0].x, 1.0, points[0].y))
		st.add_vertex(Vector3(points[i].x, 1.0, points[i].y))
		st.add_vertex(Vector3(points[i + 1].x, 1.0, points[i + 1].y))
	for i in range(1, n - 1):
		st.add_vertex(Vector3(points[0].x, 0.0, points[0].y))
		st.add_vertex(Vector3(points[i + 1].x, 0.0, points[i + 1].y))
		st.add_vertex(Vector3(points[i].x, 0.0, points[i].y))
	for i in range(n):
		var a: Vector2 = points[i]
		var b: Vector2 = points[(i + 1) % n]
		st.add_vertex(Vector3(a.x, 1.0, a.y))
		st.add_vertex(Vector3(a.x, 0.0, a.y))
		st.add_vertex(Vector3(b.x, 0.0, b.y))
		st.add_vertex(Vector3(a.x, 1.0, a.y))
		st.add_vertex(Vector3(b.x, 0.0, b.y))
		st.add_vertex(Vector3(b.x, 1.0, b.y))
	st.generate_normals()
	return st.commit()


func sync(tick: int, units: Array) -> void:
	current_tick = tick
	wrecks_active = 0
	flashes_active = 0
	var per_batch: Dictionary = {}
	for u in units:
		var key: String = "%s_%d" % [u.role, u.faction]
		if not per_batch.has(key):
			per_batch[key] = []
		if u.alive:
			var col := Color(1, 1, 1, 1)
			var since_hit: int = tick - int(u.last_hit_tick)
			if since_hit >= 0 and since_hit <= HIT_FLASH_TICKS:
				var t: float = 1.0 - float(since_hit) / float(HIT_FLASH_TICKS)
				col = col.lerp(FLASH_BOOST, t)
				flashes_active += 1
			_append_squad(per_batch[key], u, u.pos, u.facing, col, u.uid in _selected)
		else:
			if QaPlants.is_active("no-death-visual"):
				continue
			var since: int = tick - int(u.death_tick)
			if since < 0 or since >= DEATH_REMOVE_TICKS:
				continue
			wrecks_active += 1
			var col2 := Color(1, 1, 1, 1)
			if since <= DEATH_BLOOM_TICKS:
				var bt: float = 1.0 - float(since) / float(DEATH_BLOOM_TICKS)
				col2 = col2.lerp(DEATH_BOOST, bt)
			var dt2: float = clampf(float(since) / float(DEATH_REMOVE_TICKS), 0.0, 1.0)
			col2 = col2.lerp(WRECK_DARK, dt2)
			var drift_dir := Vector2(cos(u.facing), sin(u.facing))
			var drift_pos: Vector2 = u.pos + drift_dir * (min(float(since), DRIFT_CAP_TICKS) * DRIFT_WU_PER_TICK)
			_append_squad(per_batch[key], u, drift_pos, u.facing, col2, false)
	_write_batches(per_batch)
	_update_pings(tick)


func get_unit_render_transform(role: String, pos: Vector2, facing: float) -> Transform3D:
	var sil := roster.get_silhouette(role)
	var size: Array = sil.get("size", [20, 20, 10])
	var extent := _get_shape_extent(String(sil.get("shape", "wide_block")))
	var scale_v := Vector3(float(size[1]) / extent.x, float(size[2]), float(size[0]) / extent.y)
	var basis_rot := Basis(Vector3.UP, -facing - PI / 2.0)
	return Transform3D(basis_rot * Basis.from_scale(scale_v), Vector3(pos.x, 0.0, pos.y))


func get_role_mesh_aabb(role: String) -> AABB:
	return _get_mesh(role).get_aabb()


func _append_squad(list: Array, u: Dictionary, pos: Vector2, facing: float, color: Color, selected: bool) -> void:
	var sil := roster.get_silhouette(u.role)
	var squad: int = int(sil.get("squad", 1))
	var size: Array = sil.get("size", [20, 20, 10])
	var xf0 := get_unit_render_transform(u.role, pos, facing)
	if squad <= 1:
		list.append({"xform": xf0, "color": color})
	else:
		var spacing: float = float(size[0]) * 0.9
		var basis_rot := Basis(Vector3.UP, -facing - PI / 2.0)
		for i in range(squad):
			var off2: Vector2 = SQUAD_OFFSETS[i % SQUAD_OFFSETS.size()] * spacing
			var world_off: Vector3 = basis_rot * Vector3(off2.x, 0.0, off2.y)
			list.append({"xform": Transform3D(xf0.basis, xf0.origin + world_off), "color": color})
	_update_ring(u.uid, pos, selected)


func _update_ring(uid: int, pos: Vector2, selected: bool) -> void:
	if not selected:
		if _sel_rings.has(uid):
			_sel_rings[uid].queue_free()
			_sel_rings.erase(uid)
		return
	var ring: MeshInstance3D
	if _sel_rings.has(uid):
		ring = _sel_rings[uid]
	else:
		var mesh := TorusMesh.new()
		mesh.inner_radius = 24.0
		mesh.outer_radius = 28.0
		ring = MeshInstance3D.new()
		ring.mesh = mesh
		var mat := StandardMaterial3D.new()
		mat.albedo_color = Color(1.0, 1.0, 1.0, 0.9)
		mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
		ring.material_override = mat
		add_child(ring)
		_sel_rings[uid] = ring
	ring.position = Vector3(pos.x, 1.0, pos.y)


func _write_batches(per_batch: Dictionary) -> void:
	for key in _batches.keys():
		var mmi: MultiMeshInstance3D = _batches[key]
		var mm: MultiMesh = mmi.multimesh
		var entries: Array = per_batch.get(key, [])
		if entries.size() > mm.instance_count:
			mm.instance_count = entries.size()
		mm.visible_instance_count = entries.size()
		for i in range(entries.size()):
			mm.set_instance_transform(i, entries[i].xform)
			mm.set_instance_color(i, entries[i].color)


func set_selected(uids: Array) -> void:
	_selected.clear()
	for uid in uids:
		_selected[int(uid)] = true
	for uid in _sel_rings.keys():
		if not _selected.has(uid):
			_sel_rings[uid].queue_free()
	for uid in _sel_rings.keys().duplicate():
		if not _selected.has(uid):
			_sel_rings.erase(uid)


func add_ping(pos: Vector2, is_attack_move: bool) -> void:
	var mesh := TorusMesh.new()
	mesh.inner_radius = 34.0
	mesh.outer_radius = 40.0
	var mi := MeshInstance3D.new()
	mi.mesh = mesh
	var mat := StandardMaterial3D.new()
	mat.albedo_color = Color(1.0, 0.4, 0.2, 0.8) if is_attack_move else Color(0.3, 1.0, 0.4, 0.8)
	mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	mi.material_override = mat
	mi.position = Vector3(pos.x, 1.0, pos.y)
	_ping_root.add_child(mi)
	_pings.append({"node": mi, "tick": current_tick})


func _update_pings(tick: int) -> void:
	var i := _pings.size() - 1
	while i >= 0:
		if tick - int(_pings[i].tick) > PING_LIFETIME_TICKS:
			_pings[i].node.queue_free()
			_pings.remove_at(i)
		i -= 1
