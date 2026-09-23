extends CanvasLayer

const LAYER_COLORS: Array[Color] = [Color(0.20, 0.90, 1.00), Color(1.00, 0.55, 0.15)]

var _root: Node3D
var _highlighted_layer: int = 1

@onready var _seed_label: Label = $VBox/SeedLabel
@onready var _seed_spinbox: SpinBox = $VBox/SeedSpinBox
@onready var _reset_button: Button = $VBox/ResetButton
@onready var _step_button: Button = $VBox/StepButton
@onready var _play_button: Button = $VBox/PlayButton
@onready var _to1_button: Button = $VBox/ToLayer1Button
@onready var _to2_button: Button = $VBox/ToLayer2Button
@onready var _tick_label: Label = $VBox/TickLabel
@onready var _timing_label: Label = $VBox/TimingLabel
@onready var _unit_list: VBoxContainer = $UnitList
@onready var _strip_l1: Button = $LayerStrip/L1Button
@onready var _strip_l2: Button = $LayerStrip/L2Button
@onready var _paused_label: Label = $PausedLabel
@onready var _selection_label: Label = $VBox/SelectionLabel
@onready var _demo_label: Label = $DemoLabel


func _ready() -> void:
	_root = get_parent()
	for b in [_reset_button, _step_button, _play_button, _to1_button, _to2_button, _strip_l1, _strip_l2]:
		b.focus_mode = Control.FOCUS_NONE
	_seed_spinbox.focus_mode = Control.FOCUS_NONE

	_reset_button.pressed.connect(func(): _root.reset(int(_seed_spinbox.value)))
	_seed_spinbox.value_changed.connect(func(v): _root.reset(int(v)))
	_step_button.pressed.connect(func(): _root.step_ticks(1))
	_play_button.pressed.connect(func(): _root.toggle_play())
	_to1_button.pressed.connect(func(): _root.transfer_selected(1))
	_to2_button.pressed.connect(func(): _root.transfer_selected(2))
	_strip_l1.pressed.connect(func(): _root.set_focus_layer_direct(1))
	_strip_l2.pressed.connect(func(): _root.set_focus_layer_direct(2))


func get_seed_value() -> int:
	return int(_seed_spinbox.value)


func set_seed_value(n: int) -> void:
	_seed_spinbox.value = n


func get_highlighted_layer() -> int:
	return _highlighted_layer


func refresh() -> void:
	if _root == null:
		return
	var sim: ToySim = _root.get_sim()
	_seed_label.text = "Seed: %d" % _root.get_seed()
	_tick_label.text = "Tick: %d" % sim.tick
	_timing_label.text = "tick_avg: %.3fms  regen: %d" % [sim.tick_avg_ms(), _root.get_regen_count()]
	_play_button.text = "Pause" if _root.is_playing() else "Play"

	_highlighted_layer = _root.get_focus_layer()
	_strip_l1.text = "L1*" if _highlighted_layer == 1 else "L1"
	_strip_l2.text = "L2*" if _highlighted_layer == 2 else "L2"
	_strip_l1.modulate = Color(1, 1, 1, 1) if _highlighted_layer == 1 else Color(0.5, 0.5, 0.5, 1)
	_strip_l2.modulate = Color(1, 1, 1, 1) if _highlighted_layer == 2 else Color(0.5, 0.5, 0.5, 1)

	_paused_label.visible = not _root.is_playing()

	if _root.has_selection():
		var sel: Dictionary = sim.units[_root.get_selected_uid()]
		_selection_label.text = "Selected: unit %d (%s)" % [_root.get_selected_uid(), sel.type]
	else:
		_selection_label.text = "Selected: none — Q/E apply to every friendly"

	var narration: String = _root.get_demo_narration()
	_demo_label.visible = narration != ""
	_demo_label.text = narration

	for child in _unit_list.get_children():
		child.free()
	var uids: Array = sim.units.keys()
	uids.sort()
	for uid in uids:
		var u: Dictionary = sim.units[uid]
		if u.faction == 1 and not sim.visible_enemy_uids().has(uid):
			continue
		var row := HBoxContainer.new()
		var swatch := ColorRect.new()
		swatch.custom_minimum_size = Vector2(12, 12)
		swatch.color = LAYER_COLORS[clampi(u.layer - 1, 0, 1)]
		row.add_child(swatch)
		var label := Label.new()
		var sel_mark := " <" if uid == _root.get_selected_uid() else ""
		label.text = " %d %s L%d%s" % [uid, u.type, u.layer, sel_mark]
		label.add_theme_font_size_override("font_size", 13)
		row.add_child(label)
		_unit_list.add_child(row)
