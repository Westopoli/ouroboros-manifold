extends CanvasLayer

var _downloads_path: String
var _reports_path: String


func setup(downloads_path: String, reports_path: String) -> void:
	_downloads_path = downloads_path
	_reports_path = reports_path


func _ready() -> void:
	layer = 100
	_build_ui()


func _build_ui() -> void:
	var bg := ColorRect.new()
	bg.color = Color(0.0, 0.0, 0.0, 0.6)
	bg.set_anchors_preset(Control.PRESET_FULL_RECT)
	add_child(bg)

	var center := CenterContainer.new()
	center.set_anchors_preset(Control.PRESET_FULL_RECT)
	add_child(center)

	var panel := PanelContainer.new()
	var sb := StyleBoxFlat.new()
	sb.bg_color = Color(0.08, 0.10, 0.14)
	sb.border_color = Color(0.3, 0.8, 0.5)
	sb.set_border_width_all(2)
	sb.set_corner_radius_all(6)
	sb.set_content_margin_all(32)
	panel.add_theme_stylebox_override("panel", sb)
	center.add_child(panel)

	var vbox := VBoxContainer.new()
	vbox.add_theme_constant_override("separation", 12)
	panel.add_child(vbox)

	var title := Label.new()
	title.text = "BUG REPORT CAPTURED"
	title.add_theme_font_size_override("font_size", 20)
	title.add_theme_color_override("font_color", Color(0.3, 0.9, 0.5))
	title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	if ThemeConstants.font_mono_regular:
		title.add_theme_font_override("font", ThemeConstants.font_mono_regular)
	vbox.add_child(title)

	var msg := Label.new()
	msg.text = "File copied to clipboard.\nPaste into Discord with Cmd+V / Ctrl+V."
	msg.add_theme_color_override("font_color", Color(0.85, 0.87, 0.92))
	msg.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	vbox.add_child(msg)

	var path_label := Label.new()
	path_label.text = _downloads_path
	path_label.add_theme_font_size_override("font_size", 12)
	path_label.add_theme_color_override("font_color", Color(0.55, 0.58, 0.65))
	path_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	path_label.autowrap_mode = TextServer.AUTOWRAP_WORD
	path_label.custom_minimum_size.x = 500
	vbox.add_child(path_label)

	var also := Label.new()
	also.text = "Also saved to: %s" % _reports_path
	also.add_theme_font_size_override("font_size", 11)
	also.add_theme_color_override("font_color", Color(0.45, 0.48, 0.55))
	also.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	also.autowrap_mode = TextServer.AUTOWRAP_WORD
	also.custom_minimum_size.x = 500
	vbox.add_child(also)

	var words := TextEdit.new()
	words.name = "WordsField"
	words.placeholder_text = "What happened? (optional)"
	words.custom_minimum_size = Vector2(500, 80)
	vbox.add_child(words)

	var send := Button.new()
	send.name = "SendButton"
	send.text = "SEND"
	send.custom_minimum_size = Vector2(120, 36)
	send.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	send.pressed.connect(_send_words.bind(words))
	vbox.add_child(send)

	var btn := Button.new()
	btn.text = "DISMISS"
	btn.custom_minimum_size = Vector2(120, 36)
	btn.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	btn.pressed.connect(_dismiss)
	vbox.add_child(btn)


func _input(event: InputEvent) -> void:
	if event is InputEventKey and event.pressed:
		if event.keycode == KEY_ESCAPE or event.keycode == KEY_F12:
			_dismiss()
			get_viewport().set_input_as_handled()


func _send_words(field: TextEdit) -> void:
	if field.text.is_empty():
		return
	for zip_path in [_downloads_path, _reports_path]:
		var f := FileAccess.open(zip_path.get_basename() + ".words.txt", FileAccess.WRITE)
		if f:
			f.store_string(field.text)
			f.close()
	_dismiss()


func _dismiss() -> void:
	queue_free()


func qa_state() -> Dictionary:
	return {
		"scene": "bug_report_popup",
		"tick": -1,
		"downloads_path": _downloads_path,
		"reports_path": _reports_path,
		"plants": [],
	}
