extends Node3D

var _galaxy: Galaxy
var _points: MultiMeshInstance3D
var _filaments: Node3D


func build(galaxy: Galaxy) -> void:
	_galaxy = galaxy
	if _points:
		_points.free()
	_points = MultiMeshInstance3D.new()
	_points.name = "Points"
	var mm := MultiMesh.new()
	mm.transform_format = MultiMesh.TRANSFORM_3D
	mm.use_colors = true
	var sphere := SphereMesh.new()
	sphere.radius = 1.0
	mm.mesh = sphere
	mm.instance_count = galaxy.systems.size()
	for i in range(galaxy.systems.size()):
		mm.set_instance_color(i, Color.WHITE)
	_points.multimesh = mm
	add_child(_points)

	if _filaments:
		_filaments.free()
	_filaments = Node3D.new()
	_filaments.name = "Filaments"
	add_child(_filaments)


func get_galaxy() -> Galaxy:
	return _galaxy


func owner_color(owner_id: int, galaxy: Galaxy) -> Color:
	if owner_id == -1 or galaxy == null:
		return Color(0.55, 0.55, 0.58, 1.0)
	for f in galaxy.factions:
		if f.id == owner_id:
			return Color.from_hsv(f.hue, 0.65, 0.85, 1.0)
	return Color(0.55, 0.55, 0.58, 1.0)


func update_view(_distance: float, _focused_id: int, _hover_faction: int, _pin_faction: int) -> void:
	pass


func flash(_system_id: int, _color: Color) -> void:
	pass


func set_system_owner(system_id: int, faction_id: int) -> void:
	if _galaxy != null and system_id >= 0 and system_id < _galaxy.systems.size():
		_galaxy.systems[system_id].owner = faction_id
