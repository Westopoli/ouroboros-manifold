extends Node3D

signal empty_clicked

var _galaxy_view: Node3D
var _distance: float = 50.0
var _focused_id: int = -1
var _hovered_id: int = -1

@onready var _camera: Camera3D = $Camera3D


func set_galaxy_view(view: Node3D) -> void:
	_galaxy_view = view


func get_camera() -> Camera3D:
	return _camera


func qa_camera(distance: float, _target_system_id: int) -> void:
	_distance = distance


func get_band() -> String:
	return "Regional"


func get_distance() -> float:
	return _distance


func get_focused() -> int:
	return _focused_id


func get_hovered() -> int:
	return _hovered_id


func project(_system_id: int) -> Vector2:
	return Vector2(-1, -1)


func pick_at(_px: Vector2) -> int:
	return -1
