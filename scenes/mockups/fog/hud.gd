extends CanvasLayer

var _root: Node
var _playing: bool = false

@onready var _phase_label: Label = $VBoxContainer/PhaseLabel
@onready var _begin_button: Button = $VBoxContainer/BeginButton
@onready var _memory_check: CheckBox = $VBoxContainer/MemoryCheck
@onready var _seed_spinbox: SpinBox = $VBoxContainer/SeedSpinBox
@onready var _reset_button: Button = $VBoxContainer/ResetButton
@onready var _step_button: Button = $VBoxContainer/StepButton
@onready var _readout_label: Label = $VBoxContainer/ReadoutLabel


func bind(root: Node) -> void:
	_root = root
	_begin_button.pressed.connect(_on_begin_pressed)
	_memory_check.toggled.connect(_on_memory_toggled)
	_reset_button.pressed.connect(_on_reset_pressed)
	_step_button.pressed.connect(_on_step_pressed)
	_memory_check.button_pressed = true
	_update_readout()


func _process(_delta: float) -> void:
	if _playing and _root != null:
		_root.qa_tick(1)
	_update_readout()


func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventKey and event.pressed and not event.echo:
		match event.keycode:
			KEY_B:
				_on_begin_pressed()
			KEY_M:
				_memory_check.button_pressed = not _memory_check.button_pressed
			KEY_R:
				_on_reset_pressed()
			KEY_T:
				_on_step_pressed()
			KEY_SPACE:
				_playing = not _playing


func _on_begin_pressed() -> void:
	_root.qa_set("phase", "mission")


func _on_memory_toggled(pressed: bool) -> void:
	_root.qa_set("memory", pressed)


func _on_reset_pressed() -> void:
	_root.qa_seed(int(_seed_spinbox.value))
	_playing = false


func _on_step_pressed() -> void:
	_root.qa_tick(20)


func _update_readout() -> void:
	if _root == null:
		return
	var s: Dictionary = _root.qa_state()
	_phase_label.text = "RECON" if s.phase == "recon" else "MISSION t=%d" % s.tick
	var total: int = s.enemy_count_total
	var vis: int = s.view_enemy_uids.size()
	var cells: Dictionary = s.cells
	var total_cells: int = int(cells.never_seen) + int(cells.explored) + int(cells.visible)
	var seen_pct := 0.0
	if total_cells > 0:
		seen_pct = 100.0 * float(int(cells.explored) + int(cells.visible)) / float(total_cells)
	_readout_label.text = "visible enemies %d of %d, cells seen %.0f%%" % [vis, total, seen_pct]
