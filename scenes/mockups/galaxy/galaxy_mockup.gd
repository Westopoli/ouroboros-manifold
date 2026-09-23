extends Node3D

const QaPlants := preload("res://scenes/mockups/_shared/qa_plants.gd")

const PLANTS: Array[String] = [
	"seed-ignored",
	"owner-colour-flat",
	"edges-2d-overlay",
	"pick-radius-zero",
	"bands-frozen",
	"conquest-no-recolour",
]

@onready var _view: Node3D = $World/GalaxyView
@onready var _camera: Node3D = $OrbitCamera
@onready var _hud = $HUD


func _ready() -> void:
	_camera.set_galaxy_view(_view)
	_view.attach_camera(_camera)


func _process(_delta: float) -> void:
	_view.update_view(_camera.get_distance(), _camera.get_focused(), _hud.get_hover_faction(), _hud.get_pin_faction())


func qa_state() -> Dictionary:
	var g: Galaxy = _view.get_galaxy()
	var border := 0
	var trade := 0
	var systems_px := {}
	var owners := {}
	if g != null:
		for e in g.edges:
			if e.kind == "border":
				border += 1
			else:
				trade += 1
		for sys in g.systems:
			var p: Vector2 = _camera.project(sys.id)
			systems_px[sys.id] = [p.x, p.y]
			owners[sys.id] = sys.owner

	return {
		"seed": _hud.get_seed(),
		"hash": g.compute_hash() if g != null else 0,
		"system_count": g.systems.size() if g != null else 0,
		"faction_count": g.factions.size() if g != null else 0,
		"edge_counts": {"border": border, "trade": trade},
		"band": _camera.get_band(),
		"distance": _camera.get_distance(),
		"focused": _camera.get_focused(),
		"hover_faction": _hud.get_hover_faction(),
		"pinned_faction": _hud.get_pin_faction(),
		"systems_px": systems_px,
		"owners": owners,
		"replay": {"index": _hud.get_replay_index(), "done": _hud.is_replay_done(), "total": _hud.get_replay_total()},
		"timing_ms": _hud.get_timing_ms(),
		"regen_count": _hud.get_regen_count(),
	}


func qa_plant(id: String) -> bool:
	if not PLANTS.has(id):
		return false
	QaPlants.activate(id)
	_hud.qa_regenerate()
	return true


func qa_seed(n: int) -> void:
	_hud.qa_seed(n)


func qa_set(name: String, value) -> void:
	match name:
		"hover_faction":
			_hud.qa_set_hover_faction(int(value))
		"pin_faction":
			_hud.qa_set_pin_faction(int(value))


func qa_camera(distance: float, target_system_id: int) -> void:
	_camera.qa_camera(distance, target_system_id)


func qa_replay_step() -> void:
	_hud.qa_replay_step()


func qa_replay_restart() -> void:
	_hud.qa_replay_restart()
