class_name FogView
extends Node3D

const FRIENDLY_COLOR := Color(0.251, 0.6, 1.0)
const ENEMY_COLOR := Color(1.0, 0.2784, 0.2196)
const NODE_LABEL_COLOR := Color(0.91, 0.90, 0.88)

var _terrain: Node3D
var _obstacles_node: Node3D
var _zones_node: Node3D
var _nodes_node: Node3D
var _circles_node: Node3D
var _friendlies_node: Node3D
var _enemies_node: Node3D
var _structures_node: Node3D

var _dim: int
var _cell_size: float
var _canvas: float
var _fog_image: Image
var _fog_texture: ImageTexture


func _ready() -> void:
	_terrain = Node3D.new(); _terrain.name = "Terrain"; add_child(_terrain)
	_obstacles_node = Node3D.new(); _obstacles_node.name = "Obstacles"; add_child(_obstacles_node)
	_zones_node = Node3D.new(); _zones_node.name = "Zones"; add_child(_zones_node)
	_nodes_node = Node3D.new(); _nodes_node.name = "MapNodes"; add_child(_nodes_node)
	_circles_node = Node3D.new(); _circles_node.name = "SensorCircles"; add_child(_circles_node)
	_friendlies_node = Node3D.new(); _friendlies_node.name = "Friendlies"; add_child(_friendlies_node)
	_enemies_node = Node3D.new(); _enemies_node.name = "EnemyUnits"; add_child(_enemies_node)
	_structures_node = Node3D.new(); _structures_node.name = "EnemyStructures"; add_child(_structures_node)


func build_static(truth: FogTruth, dim: int, cell_size: float) -> void:
	_dim = dim
	_cell_size = cell_size
	_canvas = truth.canvas
	_build_ground()
	_build_obstacles(truth.obstacles)
	_build_zones(truth.zones)
	_build_nodes(truth.nodes)
	_build_structures(truth.structures)
	_build_fog_mesh()


func _build_ground() -> void:
	var mesh := PlaneMesh.new()
	mesh.size = Vector2(_canvas, _canvas)
	var mi := MeshInstance3D.new()
	mi.mesh = mesh
	mi.position = Vector3(_canvas * 0.5, -1.0, _canvas * 0.5)
	var mat := StandardMaterial3D.new()
	mat.albedo_color = Color(0.16, 0.18, 0.14)
	mi.material_override = mat
	_terrain.add_child(mi)


func _build_obstacles(obstacles: Array) -> void:
	for o in obstacles:
		var height: float = 400.0 if o.tall else 120.0
		var box := BoxMesh.new()
		box.size = Vector3(o.half_extents.x * 2.0, height, o.half_extents.y * 2.0)
		var mi := MeshInstance3D.new()
		mi.mesh = box
		mi.position = Vector3(o.pos.x, height * 0.5, o.pos.y)
		var mat := StandardMaterial3D.new()
		mat.albedo_color = Color(0.45, 0.42, 0.38) if o.tall else Color(0.55, 0.5, 0.4)
		mi.material_override = mat
		_obstacles_node.add_child(mi)


func _build_zones(zones: Array) -> void:
	for z in zones:
		var cyl := CylinderMesh.new()
		cyl.top_radius = z.radius
		cyl.bottom_radius = z.radius
		cyl.height = 4.0
		var mi := MeshInstance3D.new()
		mi.mesh = cyl
		mi.position = Vector3(z.pos.x, 2.0, z.pos.y)
		var mat := StandardMaterial3D.new()
		mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
		match z.kind:
			"interference":
				mat.albedo_color = Color(0.55, 0.25, 0.75, 0.35)
			"hazard":
				mat.albedo_color = Color(0.85, 0.45, 0.15, 0.30)
			_:
				mat.albedo_color = Color(0.25, 0.65, 0.35, 0.30)
		mi.material_override = mat
		_zones_node.add_child(mi)


func _build_nodes(nodes: Array) -> void:
	for n in nodes:
		var mesh := SphereMesh.new()
		mesh.radius = 60.0
		mesh.height = 120.0
		var mi := MeshInstance3D.new()
		mi.mesh = mesh
		mi.position = Vector3(n.pos.x, 60.0, n.pos.y)
		var mat := StandardMaterial3D.new()
		mat.albedo_color = Color(0.9, 0.85, 0.3)
		mi.material_override = mat
		_nodes_node.add_child(mi)
		var label := Label3D.new()
		label.text = String(n.type)
		label.position = Vector3(n.pos.x, 220.0, n.pos.y)
		label.font_size = 48
		label.billboard = BaseMaterial3D.BILLBOARD_ENABLED
		label.modulate = NODE_LABEL_COLOR
		_nodes_node.add_child(label)


func _build_structures(structures: Array) -> void:
	for s in structures:
		var box := BoxMesh.new()
		box.size = Vector3(300, 180, 300)
		var mi := MeshInstance3D.new()
		mi.mesh = box
		mi.position = Vector3(s.pos.x, 90.0, s.pos.y)
		mi.set_meta("sid", s.sid)
		var mat := StandardMaterial3D.new()
		mat.albedo_color = ENEMY_COLOR
		mi.material_override = mat
		mi.visible = false
		_structures_node.add_child(mi)


func _build_fog_mesh() -> void:
	_fog_image = Image.create(_dim, _dim, false, Image.FORMAT_RGBA8)
	_fog_image.fill(Color(0, 0, 0, 1))
	_fog_texture = ImageTexture.create_from_image(_fog_image)
	var mesh := PlaneMesh.new()
	mesh.size = Vector2(_canvas, _canvas)
	var mi := MeshInstance3D.new()
	mi.mesh = mesh
	mi.position = Vector3(_canvas * 0.5, 30.0, _canvas * 0.5)
	var mat := StandardMaterial3D.new()
	mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	mat.albedo_texture = _fog_texture
	mi.material_override = mat
	add_child(mi)


func update_fog(grid: FogCellGrid, recon: bool) -> void:
	if recon:
		_fog_image.fill(Color(0, 0, 0, 0))
		_fog_texture.update(_fog_image)
		return
	for gy in range(grid.dim):
		for gx in range(grid.dim):
			var s: int = grid.cells[gy * grid.dim + gx]
			var c: Color
			match s:
				FogCellGrid.VISIBLE:
					c = Color(0, 0, 0, 0)
				FogCellGrid.EXPLORED:
					c = Color(0, 0, 0, 0.6)
				_:
					c = Color(0, 0, 0, 1)
			_fog_image.set_pixel(gx, gy, c)
	_fog_texture.update(_fog_image)


func update_structures(states: Dictionary) -> void:
	for child in _structures_node.get_children():
		var sid: int = child.get_meta("sid")
		var st: String = states.get(sid, "never_seen")
		child.visible = st != "never_seen"
		if child.visible:
			var mat: StandardMaterial3D = child.material_override
			mat.albedo_color = ENEMY_COLOR.darkened(0.6) if st == "explored" else ENEMY_COLOR


func update_friendlies(friendlies: Array, _selected_uid: int) -> void:
	for child in _friendlies_node.get_children():
		child.free()
	for f in friendlies:
		var box := BoxMesh.new()
		box.size = Vector3(120, 140, 120)
		var mi := MeshInstance3D.new()
		mi.mesh = box
		mi.position = Vector3(f.pos.x, 70.0, f.pos.y)
		var mat := StandardMaterial3D.new()
		mat.albedo_color = FRIENDLY_COLOR
		mi.material_override = mat
		_friendlies_node.add_child(mi)


func update_enemies(visible_enemies: Array) -> void:
	for child in _enemies_node.get_children():
		child.free()
	for e in visible_enemies:
		var box := BoxMesh.new()
		box.size = Vector3(100, 120, 100)
		var mi := MeshInstance3D.new()
		mi.mesh = box
		mi.position = Vector3(e.pos.x, 60.0, e.pos.y)
		mi.set_meta("uid", e.uid)
		var mat := StandardMaterial3D.new()
		mat.albedo_color = ENEMY_COLOR
		mi.material_override = mat
		_enemies_node.add_child(mi)


func update_circles(circles: Array, selected_uid: int) -> void:
	for child in _circles_node.get_children():
		child.free()
	for c in circles:
		var bold: bool = c.uid == selected_uid
		var mi := MeshInstance3D.new()
		mi.mesh = _make_ring_mesh(c.radius_eff, 64)
		mi.position = Vector3(c.pos.x, 5.0, c.pos.y)
		var mat := StandardMaterial3D.new()
		mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
		mat.albedo_color = Color(1, 1, 1, 0.9) if bold else Color(1, 1, 1, 0.35)
		mi.material_override = mat
		_circles_node.add_child(mi)


func _make_ring_mesh(radius: float, segments: int) -> ArrayMesh:
	var pts := PackedVector3Array()
	for i in range(segments + 1):
		var a := TAU * float(i) / float(segments)
		pts.append(Vector3(cos(a) * radius, 0.0, sin(a) * radius))
	var arrays := []
	arrays.resize(Mesh.ARRAY_MAX)
	arrays[Mesh.ARRAY_VERTEX] = pts
	var mesh := ArrayMesh.new()
	mesh.add_surface_from_arrays(Mesh.PRIMITIVE_LINE_STRIP, arrays)
	return mesh


func get_enemy_count() -> int:
	return _enemies_node.get_child_count()


func get_enemy_uids() -> Array:
	var out := []
	for child in _enemies_node.get_children():
		out.append(int(child.get_meta("uid")))
	return out


func get_structure_visible(sid: int) -> bool:
	for child in _structures_node.get_children():
		if int(child.get_meta("sid")) == sid:
			return child.visible
	return false
