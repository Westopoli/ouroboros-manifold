## Stage 13 Checkpoint D — F3-toggled FPS/tick/unit/sim-status overlay.
## Off by default. Read-only: invariant I10 forbids any effect on sim or
## frame timing beyond the Label render cost.
##
## See also: docs/legacy/stage_specs/stage_13_spec.md (Checkpoint D, Invariant I10).
## Gated by FeatureFlags.ENABLE_DEBUG_OVERLAY (default false): F3 does nothing
## unless the flag is set. Tick and units come from the live tactical frame.
extends CanvasLayer

const SimSession := preload("res://autoload/sim_session.gd")
const PANEL_MARGIN := 12.0
const PANEL_PAD := 8.0

var _label: Label
var _panel: ColorRect


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


func _unhandled_input(event: InputEvent) -> void:
	if not FeatureFlags.ENABLE_DEBUG_OVERLAY:
		return
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
	var frame: Dictionary = SimSession.bridge().tactical_frame()
	if not frame.is_empty():
		tick = int(frame.get("tick", -1))
		unit_count = (frame.get("units", []) as Array).size()

	var status := "connected" if not frame.is_empty() else "disconnected"
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

