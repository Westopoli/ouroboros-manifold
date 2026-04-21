extends MarginContainer

signal finished_printing(entry_id: String)
signal expansion_requested(entry_id: String)

enum { QUEUED, PRINTING, PRINTED }

var _state: int = QUEUED
var _entry_id: String = ""
var _entry_data: Dictionary = {}
var _words: PackedStringArray = []
var _word_alphas: PackedFloat32Array = []
var _words_started: int = 0
var _words_done: int = 0
var _fade_tweens: Array[Tween] = []
var _text_label: RichTextLabel
var _cursor: Node
var _cadence_timer: Timer
var _text_color: Color
var _accent: Color
var _dirty: bool = false


func setup(entry_data: Dictionary, accent: Color) -> void:
	_entry_id = entry_data.get("entry_id", "")
	_entry_data = entry_data
	_accent = accent
	_text_color = ThemeConstants.SECONDARY
	var text: String = entry_data.get("base_form", "")
	_words = text.split(" ", false)
	_build_ui()


func _build_ui() -> void:
	add_theme_constant_override("margin_left", 0)
	add_theme_constant_override("margin_right", 0)
	add_theme_constant_override("margin_top", 4)
	add_theme_constant_override("margin_bottom", 4)
	mouse_filter = Control.MOUSE_FILTER_STOP

	var panel := PanelContainer.new()
	var style := StyleBoxFlat.new()
	style.bg_color = Color.TRANSPARENT
	style.border_color = Color(_accent.r, _accent.g, _accent.b, 0.4)
	style.border_width_left = 2
	style.content_margin_left = 14
	style.content_margin_right = 14
	style.content_margin_top = 10
	style.content_margin_bottom = 10
	panel.add_theme_stylebox_override("panel", style)
	add_child(panel)

	var container := VBoxContainer.new()
	container.add_theme_constant_override("separation", 4)
	panel.add_child(container)

	_text_label = RichTextLabel.new()
	_text_label.bbcode_enabled = true
	_text_label.fit_content = true
	_text_label.scroll_active = false
	_text_label.mouse_filter = Control.MOUSE_FILTER_PASS
	_text_label.add_theme_font_override("normal_font", ThemeConstants.font_serif_light)
	_text_label.add_theme_font_size_override("normal_font_size", ThemeConstants.BODY_NARRATIVE_SIZE)
	_text_label.add_theme_color_override("default_color", _text_color)
	_text_label.text = ""
	container.add_child(_text_label)

	_cursor = load("res://theme/components/tm_blinking_cursor.tscn").instantiate()
	_cursor.cursor_color = _accent
	_cursor.visible = false
	container.add_child(_cursor)

	_cadence_timer = Timer.new()
	_cadence_timer.one_shot = true
	_cadence_timer.timeout.connect(_on_cadence_tick)
	add_child(_cadence_timer)


func start_printing() -> void:
	_state = PRINTING
	_words_started = 0
	_words_done = 0
	_word_alphas.resize(_words.size())
	_word_alphas.fill(0.0)
	_fade_tweens.clear()
	_dirty = false
	_schedule_next_tick()


func pause_printing() -> void:
	_cadence_timer.stop()
	for tw in _fade_tweens:
		if tw and tw.is_valid():
			tw.pause()


func resume_printing() -> void:
	if _state == PRINTING:
		for tw in _fade_tweens:
			if tw and tw.is_valid():
				tw.play()
		if _words_started < _words.size():
			_schedule_next_tick()


func _process(_delta: float) -> void:
	if _dirty:
		_dirty = false
		_rebuild_bbcode()


func _schedule_next_tick() -> void:
	var jitter := randf_range(-0.06, 0.06)
	_cadence_timer.wait_time = maxf(0.05, 0.125 + jitter)
	_cadence_timer.start()


func _on_cadence_tick() -> void:
	if _words_started >= _words.size():
		return

	var idx := _words_started
	_words_started += 1

	var fade_jitter := randf_range(-0.2, 0.2)
	var fade_dur := maxf(3.0, 8.0 + fade_jitter)
	var tw := create_tween().set_ease(Tween.EASE_OUT).set_trans(Tween.TRANS_CUBIC)
	tw.tween_method(func(p: float):
		_word_alphas[idx] = p
		_dirty = true
	, 0.0, 1.0, fade_dur)
	tw.tween_callback(func():
		_word_alphas[idx] = 1.0
		_fade_tweens.erase(tw)
		_words_done += 1
		_dirty = true
		if _words_done >= _words.size():
			_finish_printing()
	)
	_fade_tweens.append(tw)
	_dirty = true

	if _words_started < _words.size():
		_schedule_next_tick()


func _rebuild_bbcode() -> void:
	var bbcode := ""
	var r := int(_text_color.r * 255)
	var g := int(_text_color.g * 255)
	var b := int(_text_color.b * 255)

	for i in range(_words.size()):
		if i > 0:
			bbcode += " "
		var a := int(_word_alphas[i] * _text_color.a * 255)
		bbcode += "[color=#%02x%02x%02x%02x]%s[/color]" % [r, g, b, a, _words[i]]

	_text_label.text = bbcode


func _finish_printing() -> void:
	_state = PRINTED
	_cadence_timer.stop()
	for tw in _fade_tweens:
		if tw and tw.is_valid():
			tw.kill()
	_fade_tweens.clear()
	_text_label.text = " ".join(_words)
	_cursor.visible = true
	finished_printing.emit(_entry_id)


func _gui_input(event: InputEvent) -> void:
	if _state == PRINTED and event is InputEventMouseButton and event.pressed and event.button_index == MOUSE_BUTTON_LEFT:
		expansion_requested.emit(_entry_id)
		get_viewport().set_input_as_handled()


func get_entry_id() -> String:
	return _entry_id


func get_entry_data() -> Dictionary:
	return _entry_data


func get_current_state() -> int:
	return _state
