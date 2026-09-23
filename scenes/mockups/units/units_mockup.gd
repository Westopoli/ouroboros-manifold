extends Node3D

const QaPlants := preload("res://scenes/mockups/_shared/qa_plants.gd")

const PLANTS: Array[String] = [
	"pass-through",
	"facing-fixed",
	"instant-fight",
	"silhouettes-same",
	"seed-ignored",
	"no-death-visual",
]

@onready var _hud = $HUD
@onready var _camera_rig = $CameraRig


func qa_state() -> Dictionary:
	return _hud.get_state_dict()


func qa_plant(id: String) -> bool:
	if not PLANTS.has(id):
		return false
	QaPlants.activate(id)
	_hud.qa_regenerate()
	return true


func qa_seed(n: int) -> void:
	_hud.qa_seed(n)


func qa_set(name: String, value) -> void:
	_hud.qa_set(name, value)


func qa_camera(height: float, x: float, z: float) -> void:
	_camera_rig.pan_to(Vector3(x, 0.0, z))
	_camera_rig.set_height(height)


func qa_tick(n: int) -> void:
	_hud.qa_tick(n)


func qa_tick_until_flash(max_ticks: int) -> int:
	return _hud.qa_tick_until_flash(max_ticks)


func qa_command(kind: String, uids: Array, x: float, z: float) -> void:
	_hud.qa_command(kind, uids, x, z)


func qa_drag_start(x: float, y: float) -> void:
	_hud.qa_drag_start(x, y)


func qa_drag_to(x: float, y: float) -> void:
	_hud.qa_drag_to(x, y)


func qa_drag_end(x: float, y: float) -> void:
	_hud.qa_drag_end(x, y)
