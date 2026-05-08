## Stage 13 Checkpoint D — F3-toggled FPS/tick/unit/sim-status overlay.
## Off by default. Read-only: invariant I10 forbids any effect on sim or
## frame timing beyond the Label render cost.
##
## See also: docs/stage_specs/stage_13_spec.md (Checkpoint D, Invariant I10).
##
## Spec text suggested tick from SimBridge and units from UIDataBus, but in
## this codebase tick/units live on TacticalBridge — same source the bug
## report manager already reads (autoload/bug_report_manager.gd).
extends CanvasLayer

const PANEL_MARGIN := 12.0
const PANEL_PAD := 8.0

var _label: Label
var _panel: ColorRect
var _connected: bool = false


func _ready() -> void:
	layer = 200
	process_mode = Node.PROCESS_MODE_ALWAYS

	_panel = ColorRect.new()
	_panel.color = Color(0.0, 0.0, 0.0, 0.55)
	_panel.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_panel.set_anchors_and_offsets_preset(Control.PRESET_TOP_RIGHT)
	add_child(_panel)

	_label = Label.new()
	_label.add_theme_font_override("font", ThemeDB.fallback_font)
	_label.add_theme_font_size_override("font_size", 14)
	_label.add_theme_color_override("font_color", Color(0.85, 0.95, 0.85, 1.0))
	_label.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_label.text = "..."
	_panel.add_child(_label)

	visible = false

	if get_node_or_null("/root/TacticalBridge") != null:
		TacticalBridge.connection_state_changed.connect(_on_connection_changed)


func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventKey and event.pressed and not event.echo:
		if event.keycode == KEY_F3:
			visible = not visible
			get_viewport().set_input_as_handled()


func _process(_delta: float) -> void:
	if not visible:
		return

	var fps := int(Engine.get_frames_per_second())
	var tick := -1
	var unit_count := 0
	if get_node_or_null("/root/TacticalBridge") != null:
		tick = int(TacticalBridge.current_tick)
		unit_count = TacticalBridge.units.size()

	var status := "connected" if _connected else "disconnected"
	var tick_str := str(tick) if tick >= 0 else "N/A"

	_label.text = "FPS: %d\nTick: %s\nUnits: %d\nSim: %s" % [fps, tick_str, unit_count, status]

	var sz := _label.get_minimum_size()
	var w := sz.x + PANEL_PAD * 2.0
	var h := sz.y + PANEL_PAD * 2.0
	_panel.offset_left = -w - PANEL_MARGIN
	_panel.offset_top = PANEL_MARGIN
	_panel.offset_right = -PANEL_MARGIN
	_panel.offset_bottom = PANEL_MARGIN + h
	_label.position = Vector2(PANEL_PAD, PANEL_PAD)


func _on_connection_changed(connected: bool) -> void:
	_connected = connected
