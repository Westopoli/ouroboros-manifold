extends Node3D

const QaPlants := preload("res://scenes/mockups/_shared/qa_plants.gd")
const MORPH_TICKS := 40
const ORBIT_RATE := 0.0006
const STARFIELD_SEED := 20260922

var _systems: Dictionary = {}
var _spheres: Dictionary = {}
var _materials: Dictionary = {}
var _rings: Dictionary = {}
var _ring_materials: Dictionary = {}
var _morph_by_system: Dictionary = {}
var _owners: Dictionary = {}
var _drag_active := false
var _orbit_root: Node3D


func _ready() -> void:
	_orbit_root = Node3D.new()
	add_child(_orbit_root)
	_build_starfield()


func set_data(systems: Array, edges: Array) -> void:
	for c in _orbit_root.get_children():
		c.queue_free()
	_systems.clear()
	_spheres.clear()
	_materials.clear()
	_rings.clear()
	_ring_materials.clear()
	_owners.clear()
	_morph_by_system.clear()

	for s in systems:
		var sid := String(s.get("id", ""))
		_systems[sid] = s
		_owners[sid] = String(s.get("owner", ""))

		var sphere := MeshInstance3D.new()
		var mesh := SphereMesh.new()
		mesh.radius = 6.0
		mesh.height = 12.0
		sphere.mesh = mesh
		var mat := StandardMaterial3D.new()
		mat.albedo_color = _owner_color(_owners[sid])
		sphere.material_override = mat
		sphere.position = Vector3(float(s.get("x", 0.0)), 0.0, float(s.get("y", 0.0)))
		_orbit_root.add_child(sphere)
		_spheres[sid] = sphere
		_materials[sid] = mat

		var ring := MeshInstance3D.new()
		var rmesh := CylinderMesh.new()
		rmesh.top_radius = 9.0
		rmesh.bottom_radius = 9.0
		rmesh.height = 0.4
		ring.mesh = rmesh
		var rmat := StandardMaterial3D.new()
		rmat.albedo_color = Color(1, 1, 1, 0.0)
		rmat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
		rmat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
		ring.material_override = rmat
		ring.position = sphere.position
		ring.visible = false
		_orbit_root.add_child(ring)
		_rings[sid] = ring
		_ring_materials[sid] = rmat

	_build_edges(edges)


func _build_edges(edges: Array) -> void:
	var im := ImmediateMesh.new()
	var mi := MeshInstance3D.new()
	mi.mesh = im
	var mat := StandardMaterial3D.new()
	mat.albedo_color = Color(0.85, 0.75, 0.4, 0.45)
	mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	mi.material_override = mat
	im.surface_begin(Mesh.PRIMITIVE_LINES)
	for e in edges:
		var a: Dictionary = _systems.get(String(e[0]), {})
		var b: Dictionary = _systems.get(String(e[1]), {})
		if a.is_empty() or b.is_empty():
			continue
		im.surface_add_vertex(Vector3(float(a.get("x", 0.0)), 0.0, float(a.get("y", 0.0))))
		im.surface_add_vertex(Vector3(float(b.get("x", 0.0)), 0.0, float(b.get("y", 0.0))))
	im.surface_end()
	_orbit_root.add_child(mi)


func _build_starfield() -> void:
	var mmi := MultiMeshInstance3D.new()
	var mm := MultiMesh.new()
	mm.transform_format = MultiMesh.TRANSFORM_3D
	mm.use_colors = true
	var quad := QuadMesh.new()
	quad.size = Vector2(2.5, 2.5)
	mm.mesh = quad
	var n := 260
	mm.instance_count = n
	var rng := RandomNumberGenerator.new()
	rng.seed = STARFIELD_SEED
	for i in range(n):
		var r := rng.randf_range(500.0, 1500.0)
		var ang := rng.randf_range(0.0, TAU)
		var x := r * cos(ang)
		var z := r * sin(ang)
		var y := rng.randf_range(-60.0, 260.0)
		mm.set_instance_transform(i, Transform3D(Basis(), Vector3(x, y, z)))
		var b := rng.randf_range(0.45, 1.0)
		mm.set_instance_color(i, Color(b, b, b, 1.0))
	mmi.multimesh = mm
	var mat := StandardMaterial3D.new()
	mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	mat.vertex_color_use_as_albedo = true
	mat.billboard_mode = BaseMaterial3D.BILLBOARD_ENABLED
	mmi.material_override = mat
	add_child(mmi)


func set_morph_events(events: Array) -> void:
	_morph_by_system.clear()
	for ev in events:
		_morph_by_system[String(ev.get("system_id", ""))] = ev


func update_tick(t: int) -> void:
	if not _drag_active:
		_orbit_root.rotation.y = float(t) * ORBIT_RATE
	for sid in _systems.keys():
		var owner := String(_systems[sid].get("owner", ""))
		var color := _owner_color(owner)
		var ring_alpha := 0.0
		var ring_scale := 1.0
		if _morph_by_system.has(sid):
			var ev: Dictionary = _morph_by_system[sid]
			var start := int(ev.get("tick", 0))
			if t >= start:
				var from_c := _owner_color(String(ev.get("from_owner", "")))
				var to_c := _owner_color(String(ev.get("to_owner", "")))
				var prog := 1.0
				if not QaPlants.is_active("morph-instant"):
					prog = clampf(float(t - start) / float(MORPH_TICKS), 0.0, 1.0)
				color = from_c.lerp(to_c, prog)
				owner = String(ev.get("to_owner", ""))
				if prog < 1.0:
					ring_alpha = (1.0 - prog) * 0.65
					ring_scale = lerpf(1.0, 2.6, prog)
		_owners[sid] = owner
		_materials[sid].albedo_color = color
		var rmat: StandardMaterial3D = _ring_materials[sid]
		rmat.albedo_color = Color(1, 1, 1, ring_alpha)
		_rings[sid].visible = ring_alpha > 0.001
		_rings[sid].scale = Vector3.ONE * ring_scale


func get_owners() -> Dictionary:
	return _owners.duplicate()


func get_system_color(id: String) -> Color:
	if not _materials.has(id):
		return Color.BLACK
	return _materials[id].albedo_color


func _owner_color(owner: String) -> Color:
	if owner == "":
		return Color(0.42, 0.44, 0.5)
	return Color.from_hsv(_hue_for(owner), 0.72, 0.88)


func _hue_for(id: String) -> float:
	return float(posmod(id.hash(), 360)) / 360.0


func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventMouseButton and event.button_index == MOUSE_BUTTON_RIGHT:
		_drag_active = event.pressed
	elif event is InputEventMouseMotion and _drag_active:
		_orbit_root.rotate_y(-event.relative.x * 0.005)
