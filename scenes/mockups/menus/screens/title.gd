extends Control

const Palette := preload("res://scenes/mockups/menus/theme.gd")

var root
var _message_label: Label
var _title_labels: Array = []
var _t := 0.0


func _ready() -> void:
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	_build()
	set_process(true)


func _build() -> void:
	var content := VBoxContainer.new()
	content.anchor_left = 0.12
	content.anchor_top = 0.28
	content.anchor_right = 0.55
	content.anchor_bottom = 0.85
	content.add_theme_constant_override("separation", 4)
	add_child(content)

	var studio := Label.new()
	studio.text = "A WESTOPOLI GAME"
	studio.add_theme_font_override("font", Palette.mono_regular())
	studio.add_theme_font_size_override("font_size", Palette.CLASSIFICATION_LABEL_SIZE)
	studio.add_theme_color_override("font_color", Palette.TERTIARY)
	content.add_child(studio)

	var title_row := HBoxContainer.new()
	title_row.name = "TitleRow"
	content.add_child(title_row)
	for ch in "OUROBOROS MANIFOLD":
		var lbl := Label.new()
		lbl.text = ch
		lbl.add_theme_font_override("font", Palette.serif_regular())
		lbl.add_theme_font_size_override("font_size", Palette.TITLE_SIZE)
		lbl.add_theme_color_override("font_color", Palette.PRIMARY)
		title_row.add_child(lbl)
		_title_labels.append(lbl)

	var spacer := Control.new()
	spacer.custom_minimum_size.y = 40
	content.add_child(spacer)

	var menu_box := VBoxContainer.new()
	menu_box.name = "MenuList"
	content.add_child(menu_box)
	_add_item(menu_box, "New Campaign", "new_campaign", true)
	_add_item(menu_box, "Continue", "continue", true)
	_add_item(menu_box, "Settings", "settings", false)
	_add_item(menu_box, "Quit", "quit", true)

	_message_label = Label.new()
	_message_label.name = "Message"
	_message_label.add_theme_font_override("font", Palette.mono_regular())
	_message_label.add_theme_font_size_override("font_size", Palette.HINT_TEXT_SIZE)
	_message_label.add_theme_color_override("font_color", Palette.ACCENT)
	_message_label.visible = false
	content.add_child(_message_label)

	var version := Label.new()
	version.text = "v0.1.0-mockup"
	version.add_theme_font_override("font", Palette.mono_regular())
	version.add_theme_font_size_override("font_size", Palette.HINT_TEXT_SIZE)
	version.add_theme_color_override("font_color", Palette.TERTIARY)
	version.set_anchors_preset(Control.PRESET_BOTTOM_RIGHT)
	version.offset_left = -160
	version.offset_top = -30
	add_child(version)


func _add_item(parent: VBoxContainer, label_text: String, action_name: String, enabled: bool) -> void:
	var btn := Button.new()
	btn.text = label_text
	btn.flat = true
	btn.focus_mode = Control.FOCUS_NONE
	btn.alignment = HORIZONTAL_ALIGNMENT_LEFT
	btn.add_theme_font_override("font", Palette.mono_regular())
	btn.add_theme_font_size_override("font_size", Palette.MENU_ITEM_SIZE)
	btn.add_theme_color_override("font_color", Palette.PRIMARY if enabled else Palette.TERTIARY)
	btn.disabled = not enabled
	if enabled:
		btn.pressed.connect(func(): root.qa_go(action_name))
	parent.add_child(btn)


func refresh(state: Dictionary) -> void:
	var message: String = String(state.get("message", ""))
	_message_label.text = message
	_message_label.visible = message != ""


func _process(delta: float) -> void:
	_t += delta
	for i in range(_title_labels.size()):
		var phase: float = float(i) * 0.4
		var alpha: float = 0.92 + 0.08 * (0.5 + 0.5 * sin(_t * TAU * 0.15 + phase))
		_title_labels[i].modulate.a = alpha
