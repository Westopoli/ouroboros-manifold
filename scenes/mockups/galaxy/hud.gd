extends CanvasLayer

const DEFAULT_SEED := 11

var _view: Node3D
var _camera: Node3D
var _seed: int = DEFAULT_SEED
var _regen_count: int = 0
var _timing_ms: Dictionary = {"gen": 0.0, "build": 0.0}

@onready var _seed_spinbox: SpinBox = $VBoxContainer/SeedSpinBox


func _ready() -> void:
	_view = get_node("../World/GalaxyView")
	_camera = get_node("../OrbitCamera")
	_seed_spinbox.value = _seed
	_regenerate()


func _regenerate() -> void:
	var t0 := Time.get_ticks_usec()
	var galaxy := GalaxyGen.new().generate(_seed)
	var t1 := Time.get_ticks_usec()
	_view.build(galaxy)
	var t2 := Time.get_ticks_usec()
	_timing_ms = {"gen": (t1 - t0) / 1000.0, "build": (t2 - t1) / 1000.0}
	_regen_count += 1


func qa_regenerate() -> void:
	_regenerate()


func qa_seed(n: int) -> void:
	_seed = n
	_seed_spinbox.value = n
	_regenerate()


func qa_set_hover_faction(_id: int) -> void:
	pass


func qa_set_pin_faction(_id: int) -> void:
	pass


func qa_replay_step() -> void:
	pass


func get_seed() -> int:
	return _seed


func get_hover_faction() -> int:
	return -1


func get_pin_faction() -> int:
	return -1


func get_timing_ms() -> Dictionary:
	return _timing_ms


func get_regen_count() -> int:
	return _regen_count


func get_replay_index() -> int:
	return 0


func is_replay_done() -> bool:
	return false
