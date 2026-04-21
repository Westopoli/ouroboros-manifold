extends PanelContainer

signal dismissed()

var _accent: Color


func setup(entry_data: Dictionary, accent: Color) -> void:
	_accent = accent
	_build_ui(entry_data)


func _build_ui(entry_data: Dictionary) -> void:
	set_anchors_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_STOP

	var style := StyleBoxFlat.new()
	style.bg_color = ThemeConstants.ELEVATED
	style.border_color = ThemeConstants.BORDER_COLOR
	style.set_border_width_all(ThemeConstants.BORDER_WIDTH)
	style.set_corner_radius_all(ThemeConstants.BORDER_RADIUS)
	style.content_margin_left = 24
	style.content_margin_right = 24
	style.content_margin_top = 20
	style.content_margin_bottom = 20
	add_theme_stylebox_override("panel", style)

	var vbox := VBoxContainer.new()
	vbox.add_theme_constant_override("separation", 16)
	add_child(vbox)

	var text_label := RichTextLabel.new()
	text_label.bbcode_enabled = true
	text_label.fit_content = true
	text_label.scroll_active = false
	text_label.add_theme_font_override("normal_font", ThemeConstants.font_serif_light)
	text_label.add_theme_font_size_override("normal_font_size", ThemeConstants.BODY_NARRATIVE_SIZE)
	text_label.add_theme_color_override("default_color", ThemeConstants.SECONDARY)
	text_label.text = entry_data.get("expanded_form", "")
	text_label.size_flags_vertical = Control.SIZE_EXPAND_FILL
	vbox.add_child(text_label)

	var hint := Label.new()
	hint.text = "Click or press ESC to dismiss"
	hint.add_theme_font_override("font", ThemeConstants.font_mono_regular)
	hint.add_theme_font_size_override("font_size", ThemeConstants.HINT_TEXT_SIZE)
	hint.add_theme_color_override("font_color", ThemeConstants.TERTIARY)
	hint.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	vbox.add_child(hint)

	modulate.a = 0.0
	var tw := create_tween().set_ease(Tween.EASE_OUT).set_trans(Tween.TRANS_CUBIC)
	tw.tween_property(self, "modulate:a", 1.0, 0.2)


func _gui_input(event: InputEvent) -> void:
	if event is InputEventMouseButton and event.pressed and event.button_index == MOUSE_BUTTON_LEFT:
		dismissed.emit()
		get_viewport().set_input_as_handled()


func _input(event: InputEvent) -> void:
	if visible and event.is_action_pressed("ui_cancel"):
		dismissed.emit()
		get_viewport().set_input_as_handled()
