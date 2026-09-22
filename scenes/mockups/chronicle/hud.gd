extends CanvasLayer

const MONO_FONT := preload("res://theme/fonts/JetBrainsMono-Regular.ttf")

var _root: Node
var _skip_btn: Button
var _proceed_btn: Button
var _reset_btn: Button
var _pace_label: Label
var _count_label: Label


func _ready() -> void:
	_root = get_parent()
	var box := VBoxContainer.new()
	box.name = "VBoxContainer"
	box.position = Vector2(16, 16)
	box.add_theme_constant_override("separation", 6)
	var t := Theme.new()
	t.default_font = MONO_FONT
	box.theme = t
	add_child(box)

	_skip_btn = Button.new()
	_skip_btn.name = "SkipButton"
	_skip_btn.text = "Skip (S)"
	_skip_btn.focus_mode = Control.FOCUS_NONE
	_skip_btn.pressed.connect(func(): _root._on_skip())
	box.add_child(_skip_btn)

	_proceed_btn = Button.new()
	_proceed_btn.name = "ProceedButton"
	_proceed_btn.text = "Proceed (Enter)"
	_proceed_btn.focus_mode = Control.FOCUS_NONE
	_proceed_btn.disabled = true
	_proceed_btn.pressed.connect(func(): _root._on_proceed())
	box.add_child(_proceed_btn)

	_reset_btn = Button.new()
	_reset_btn.name = "ResetButton"
	_reset_btn.text = "Reset (R)"
	_reset_btn.focus_mode = Control.FOCUS_NONE
	_reset_btn.pressed.connect(func(): _root._on_reset())
	box.add_child(_reset_btn)

	_pace_label = Label.new()
	_pace_label.name = "PaceLabel"
	box.add_child(_pace_label)

	_count_label = Label.new()
	_count_label.name = "CountLabel"
	box.add_child(_count_label)


func refresh(state: Dictionary) -> void:
	_proceed_btn.disabled = String(state.get("phase", "")) != "done"
	var pace: Dictionary = state.get("pace", {})
	_pace_label.text = "Pace: %.2fs/word   Tick: %d   Phase: %s" % [float(pace.get("word_interval_s", 0.0)), int(state.get("tick", 0)), String(state.get("phase", ""))]
	var entries: Array = state.get("entries", [])
	var printed_count := 0
	for e in entries:
		if e.get("printed", false):
			printed_count += 1
	_count_label.text = "Entries: %d/%d printed" % [printed_count, entries.size()]
