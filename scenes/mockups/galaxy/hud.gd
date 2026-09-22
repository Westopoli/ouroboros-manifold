extends CanvasLayer

const QaPlants := preload("res://scenes/mockups/_shared/qa_plants.gd")
const REPLAY_PATH := "res://scenes/mockups/galaxy/fixtures/jump_log_seed11.json"
const REPLAY_INTERVAL := 0.5
const DEFAULT_SEED := 11
const ATTACK_COLOR := Color(1.0, 0.35, 0.25)
const CONQUEST_COLOR := Color(1.0, 0.85, 0.3)
const REVOLT_COLOR := Color(0.6, 0.6, 0.62)

var _view: Node3D
var _camera: Node3D

var _seed: int = DEFAULT_SEED
var _regen_count: int = 0
var _timing_ms: Dictionary = {"gen": 0.0, "build": 0.0}
var _hover_faction: int = -1
var _pin_faction: int = -1

var _replay_events: Array = []
var _replay_index: int = 0
var _replay_timer: float = 0.0
var _replay_playing: bool = false

@onready var _seed_label: Label = $VBoxContainer/SeedLabel
@onready var _seed_spinbox: SpinBox = $VBoxContainer/SeedSpinBox
@onready var _band_label: Label = $VBoxContainer/BandLabel
@onready var _regenerate_button: Button = $VBoxContainer/RegenerateButton
@onready var _play_button: Button = $VBoxContainer/PlayButton
@onready var _count_label: Label = $VBoxContainer/CountLabel
@onready var _faction_list: VBoxContainer = $VBoxContainer/FactionList
@onready var _tooltip: Label = $Tooltip


func _ready() -> void:
	_view = get_node("../World/GalaxyView")
	_camera = get_node("../OrbitCamera")
	_camera.empty_clicked.connect(_on_empty_clicked)
	_seed_spinbox.value = _seed
	_seed_spinbox.focus_mode = Control.FOCUS_NONE
	_regenerate_button.focus_mode = Control.FOCUS_NONE
	_play_button.focus_mode = Control.FOCUS_NONE
	_regenerate_button.pressed.connect(_on_regenerate_pressed)
	_play_button.pressed.connect(_on_play_pressed)
	_tooltip.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_tooltip.visible = false
	_load_replay()
	_regenerate()


func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventKey and event.pressed and not event.echo:
		if event.keycode == KEY_R:
			_on_regenerate_pressed()
		elif event.keycode == KEY_J:
			_on_play_pressed()


func _process(delta: float) -> void:
	_band_label.text = "Band: %s" % _camera.get_band()
	if _replay_playing:
		_replay_timer += delta
		if _replay_timer >= REPLAY_INTERVAL:
			_replay_timer = 0.0
			if not _advance_replay():
				_replay_playing = false
	_update_tooltip()


func _update_tooltip() -> void:
	var hovered: int = _camera.get_hovered()
	var g: Galaxy = _view.get_galaxy()
	if hovered == -1 or g == null:
		_tooltip.visible = false
		return
	var sys: Dictionary = g.systems[hovered]
	var owner_name := "Neutral"
	for f in g.factions:
		if f.id == sys.owner:
			owner_name = f.name
			break
	_tooltip.text = "%s (%s)" % [sys.name, owner_name]
	_tooltip.visible = true
	_tooltip.position = _tooltip.get_global_mouse_position() + Vector2(16, 16)


func _regenerate() -> void:
	var t0 := Time.get_ticks_usec()
	var gen_seed := 11 if QaPlants.is_active("seed-ignored") else _seed
	var galaxy := GalaxyGen.new().generate(gen_seed)
	var t1 := Time.get_ticks_usec()
	_view.build(galaxy)
	var t2 := Time.get_ticks_usec()
	_timing_ms = {"gen": (t1 - t0) / 1000.0, "build": (t2 - t1) / 1000.0}
	_seed_label.text = "Seed: %d" % _seed
	_replay_index = 0
	_replay_playing = false
	_rebuild_faction_list(galaxy)
	_update_count_label(galaxy)
	_regen_count += 1


func _rebuild_faction_list(galaxy: Galaxy) -> void:
	for child in _faction_list.get_children():
		child.free()
	_hover_faction = -1
	_pin_faction = -1
	for f in galaxy.factions:
		var row := HBoxContainer.new()
		row.name = "FactionRow_%d" % f.id
		row.mouse_filter = Control.MOUSE_FILTER_STOP
		var swatch := ColorRect.new()
		swatch.custom_minimum_size = Vector2(14, 14)
		swatch.color = _view.owner_color(f.id, galaxy)
		var label := Label.new()
		label.text = f.name
		row.add_child(swatch)
		row.add_child(label)
		row.mouse_entered.connect(_on_faction_row_hover.bind(f.id))
		row.mouse_exited.connect(_on_faction_row_unhover.bind(f.id))
		row.gui_input.connect(_on_faction_row_input.bind(f.id))
		_faction_list.add_child(row)


func _on_faction_row_hover(id: int) -> void:
	_hover_faction = id


func _on_faction_row_unhover(id: int) -> void:
	if _hover_faction == id:
		_hover_faction = -1


func _on_faction_row_input(event: InputEvent, id: int) -> void:
	if event is InputEventMouseButton and event.pressed and event.button_index == MOUSE_BUTTON_LEFT:
		_pin_faction = -1 if _pin_faction == id else id


func _on_empty_clicked() -> void:
	_pin_faction = -1


func _update_count_label(galaxy: Galaxy) -> void:
	var border := 0
	var trade := 0
	for e in galaxy.edges:
		if e.kind == "border":
			border += 1
		else:
			trade += 1
	_count_label.text = "Systems: %d  Edges: %d border / %d trade" % [galaxy.systems.size(), border, trade]


func _on_regenerate_pressed() -> void:
	_seed = int(_seed_spinbox.value)
	_regenerate()


func _on_play_pressed() -> void:
	_replay_playing = not _replay_playing
	_replay_timer = 0.0


func _load_replay() -> void:
	var text := FileAccess.get_file_as_string(REPLAY_PATH)
	var parsed = JSON.parse_string(text)
	_replay_events = parsed if typeof(parsed) == TYPE_ARRAY else []


func _advance_replay() -> bool:
	if _replay_index >= _replay_events.size():
		return false
	var e: Dictionary = _replay_events[_replay_index]
	match String(e.kind):
		"attack":
			_view.flash(int(e.from), ATTACK_COLOR)
			_view.flash(int(e.to), ATTACK_COLOR)
		"conquest":
			_view.flash(int(e.from), CONQUEST_COLOR)
			_view.flash(int(e.to), CONQUEST_COLOR)
			if not QaPlants.is_active("conquest-no-recolour"):
				_view.set_system_owner(int(e.to), _view.get_galaxy().systems[int(e.from)].owner)
		"revolt":
			_view.flash(int(e.at), REVOLT_COLOR)
	_replay_index += 1
	_update_count_label(_view.get_galaxy())
	return true


func qa_replay_step() -> void:
	_advance_replay()


func qa_regenerate() -> void:
	_regenerate()


func qa_seed(n: int) -> void:
	_seed = n
	_seed_spinbox.value = n
	_regenerate()


func qa_set_hover_faction(id: int) -> void:
	_hover_faction = id


func qa_set_pin_faction(id: int) -> void:
	_pin_faction = id


func get_seed() -> int:
	return _seed


func get_hover_faction() -> int:
	return _hover_faction


func get_pin_faction() -> int:
	return _pin_faction


func get_timing_ms() -> Dictionary:
	return _timing_ms


func get_regen_count() -> int:
	return _regen_count


func get_replay_index() -> int:
	return _replay_index


func is_replay_done() -> bool:
	return _replay_index >= _replay_events.size()
