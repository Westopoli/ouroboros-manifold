class_name FogView
extends Node3D

const FRIENDLY_COLOR := Color(0.251, 0.6, 1.0)
const ENEMY_COLOR := Color(1.0, 0.2784, 0.2196)

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


func _ready() -> void:
	_terrain = Node3D.new(); _terrain.name = "Terrain"; add_child(_terrain)
	_obstacles_node = Node3D.new(); _obstacles_node.name = "Obstacles"; add_child(_obstacles_node)
	_zones_node = Node3D.new(); _zones_node.name = "Zones"; add_child(_zones_node)
	_nodes_node = Node3D.new(); _nodes_node.name = "MapNodes"; add_child(_nodes_node)
	_circles_node = Node3D.new(); _circles_node.name = "SensorCircles"; add_child(_circles_node)
	_friendlies_node = Node3D.new(); _friendlies_node.name = "Friendlies"; add_child(_friendlies_node)
	_enemies_node = Node3D.new(); _enemies_node.name = "EnemyUnits"; add_child(_enemies_node)
	_structures_node = Node3D.new(); _structures_node.name = "EnemyStructures"; add_child(_structures_node)


func build_static(_truth: FogTruth, _dim_in: int, _cell_size_in: float) -> void:
	pass


func update_fog(_grid: FogCellGrid, _recon: bool) -> void:
	pass


func update_structures(_states: Dictionary) -> void:
	pass


func update_friendlies(_friendlies: Array, _selected_uid: int) -> void:
	pass


func update_enemies(_visible_enemies: Array) -> void:
	pass


func update_circles(_circles: Array, _selected_uid: int) -> void:
	pass


func get_enemy_count() -> int:
	return _enemies_node.get_child_count()


func get_enemy_uids() -> Array:
	var out := []
	for child in _enemies_node.get_children():
		out.append(int(child.get_meta("uid")))
	return out


func get_structure_visible(_sid: int) -> bool:
	return false
