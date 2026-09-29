extends Control

const SimSession := preload("res://autoload/sim_session.gd")


func _ready() -> void:
	_build_ui()


func _build_ui() -> void:
	var bg := ColorRect.new()
	bg.color = ThemeConstants.BASE
	bg.set_anchors_preset(Control.PRESET_FULL_RECT)
	add_child(bg)

	var center := CenterContainer.new()
	center.set_anchors_preset(Control.PRESET_FULL_RECT)
	add_child(center)

	var vbox := VBoxContainer.new()
	vbox.add_theme_constant_override("separation", 24)
	vbox.custom_minimum_size.x = 640
	center.add_child(vbox)

	var msg := Label.new()
	msg.text = "The simulation encountered an error and had to stop."
	msg.add_theme_font_override("font", ThemeConstants.font_serif_regular)
	msg.add_theme_font_size_override("font_size", ThemeConstants.BODY_NARRATIVE_SIZE)
	msg.add_theme_color_override("font_color", ThemeConstants.PRIMARY)
	msg.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	msg.autowrap_mode = TextServer.AUTOWRAP_WORD
	msg.custom_minimum_size.x = 640
	vbox.add_child(msg)

	var log_hint := Label.new()
	log_hint.text = "A crash report has been saved to logs/crash_report.txt in your game folder.\nIf you'd like to help, send this file to Westopoli."
	log_hint.add_theme_font_override("font", ThemeConstants.font_mono_regular)
	log_hint.add_theme_font_size_override("font_size", ThemeConstants.HINT_TEXT_SIZE)
	log_hint.add_theme_color_override("font_color", ThemeConstants.TERTIARY)
	log_hint.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	log_hint.autowrap_mode = TextServer.AUTOWRAP_WORD
	log_hint.custom_minimum_size.x = 640
	vbox.add_child(log_hint)

	var spacer := Control.new()
	spacer.custom_minimum_size.y = 16
	vbox.add_child(spacer)

	var buttons := HBoxContainer.new()
	buttons.add_theme_constant_override("separation", 24)
	buttons.alignment = BoxContainer.ALIGNMENT_CENTER
	vbox.add_child(buttons)

	var restart_btn := _make_button("RESTART")
	restart_btn.pressed.connect(_on_retry)
	buttons.add_child(restart_btn)

	var quit_btn := _make_button("QUIT")
	quit_btn.pressed.connect(_on_quit)
	buttons.add_child(quit_btn)


func _make_button(label_text: String) -> Button:
	var btn := Button.new()
	btn.text = label_text
	btn.add_theme_font_override("font", ThemeConstants.font_mono_regular)
	btn.add_theme_font_size_override("font_size", ThemeConstants.BUTTON_PRIMARY_SIZE)
	btn.custom_minimum_size = Vector2(160, 48)
	return btn


func _on_retry() -> void:
	SimSession.reset()
	SceneRouter.go_to("main_menu")


func _on_quit() -> void:
	get_tree().quit()


func qa_state() -> Dictionary:
	return {
		"scene": "error_screen",
		"tick": -1,
		"button_count": 2,
		"plants": [],
	}
