extends CanvasLayer

const KITS_DIR := "res://scenes/mockups/landscape/kits/"
const DEFAULT_CANVAS := 16000.0
const DEFAULT_KIT := "greek"

var _world: Node3D
var _camera_rig: Node3D
var _generated: Node3D

var _kits: Dictionary = {}
var _kit_name: String = DEFAULT_KIT
var _seed: int = 11
var _canvas: float = DEFAULT_CANVAS
var _stability: float = 60.0

@onready var _seed_label: Label = $VBoxContainer/SeedLabel
@onready var _seed_spinbox: SpinBox = $VBoxContainer/SeedSpinBox
@onready var _band_label: Label = $VBoxContainer/BandLabel
@onready var _regenerate_button: Button = $VBoxContainer/RegenerateButton
@onready var _kit_toggle_button: Button = $VBoxContainer/KitToggleButton
@onready var _piece_count_label: Label = $VBoxContainer/PieceCountLabel
@onready var _stability_slider: HSlider = $VBoxContainer/StabilitySlider


func _ready() -> void:
	_world = get_node("../World")
	_camera_rig = get_node("../CameraRig")

	# A container we own and wipe wholesale, instead of diffing World's children: World also
	# holds WorldEnvironment/DirectionalLight3D that must survive every regen, and matching by
	# name/type would be fragile as the placer's node vocabulary grows.
	_generated = Node3D.new()
	_generated.name = "Generated"
	_world.add_child(_generated)

	_load_kits()
	if not _kits.has(_kit_name):
		_kit_name = _kits.keys()[0] if not _kits.is_empty() else _kit_name

	_seed = int(_seed_spinbox.value)
	_stability = _stability_slider.value
	_kit_toggle_button.text = "Kit: %s" % _kit_name
	_band_label.text = "Band: %s" % _camera_rig.get_current_band()

	_camera_rig.band_changed.connect(_on_band_changed)
	_regenerate_button.pressed.connect(_on_regenerate_pressed)
	_kit_toggle_button.pressed.connect(_on_kit_toggle_pressed)
	_stability_slider.value_changed.connect(_on_stability_slider_value_changed)

	_regenerate()


func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventKey and event.pressed and not event.echo:
		if event.keycode == KEY_R:
			_on_regenerate_pressed()
		elif event.keycode == KEY_TAB:
			_on_kit_toggle_pressed()


func _load_kits() -> void:
	var dir := DirAccess.open(KITS_DIR)
	if dir == null:
		return
	dir.list_dir_begin()
	var file_name := dir.get_next()
	while file_name != "":
		if not dir.current_is_dir() and file_name.ends_with(".json"):
			var kit := Placer.load_kit(KITS_DIR + file_name)
			var kit_name: String = kit.get("name", "")
			if kit_name != "":
				_kits[kit_name] = kit
		file_name = dir.get_next()
	dir.list_dir_end()


func _regenerate() -> void:
	for child in _generated.get_children():
		child.free()

	var field_map := FieldMap.new()
	field_map.generate(_seed, _canvas, _stability)

	var kit: Dictionary = _kits[_kit_name]

	var ground_builder := GroundBuilder.new()
	_generated.add_child(ground_builder.build(field_map, kit))

	var placer := Placer.new()
	var result := placer.place(field_map, kit, _generated)

	_seed_label.text = "Seed: %d" % _seed
	_piece_count_label.text = "Pieces: %d" % result.total


func _on_regenerate_pressed() -> void:
	_seed = int(_seed_spinbox.value)
	_regenerate()


func _on_kit_toggle_pressed() -> void:
	var kit_names: Array = _kits.keys()
	var idx: int = kit_names.find(_kit_name)
	_kit_name = kit_names[(idx + 1) % kit_names.size()]
	_kit_toggle_button.text = "Kit: %s" % _kit_name
	_regenerate()


func _on_stability_slider_value_changed(value: float) -> void:
	_stability = value
	_regenerate()


func _on_band_changed(band: String) -> void:
	_band_label.text = "Band: %s" % band
