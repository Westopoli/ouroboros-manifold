extends MarginContainer

signal finished_printing(entry_id: String)
signal expansion_requested(entry_id: String)
signal mention_clicked(kind: String, id: String)

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
var _faction_colors: Dictionary = {}
var _word_colors: PackedColorArray = []
var _word_mentions: Array = []  # parallel to _words; entry is {kind,id} or {}
var _mention_just_clicked: bool = false

# Pace defaults match the original hardcoded cadence (0.125s/word, 8.0s fade)
# so any caller that never calls set_pace() keeps the old behavior unchanged.
# See also: scenes/world/chronicle_scroll_panel.gd CHRONICLE_PACE — the
# bible-mandated numbers (0.08/0.20) now flow in via set_pace() instead of
# being reported as inert qa_state() data only.
var _word_interval_s: float = 0.125
var _fade_duration_s: float = 8.0


func setup(entry_data: Dictionary, accent: Color, faction_colors: Dictionary = {}) -> void:
	_entry_id = entry_data.get("entry_id", "")
	_entry_data = entry_data
	_accent = accent
	_faction_colors = faction_colors
	_text_color = ThemeConstants.SECONDARY
	var text: String = entry_data.get("base_form", "")
	_words = text.split(" ", false)
	_assign_word_colors()
	var mentions: Array = entry_data.get("mentions", [])
	_compute_word_mentions(text, mentions)
	_build_ui()


func set_pace(word_interval_s: float, fade_s: float) -> void:
	_word_interval_s = word_interval_s
	_fade_duration_s = fade_s


func _compute_word_mentions(text: String, mentions: Array) -> void:
	_word_mentions.clear()
	for i in range(_words.size()):
		_word_mentions.append({})
	if mentions.is_empty():
		return
	var word_ranges: Array = []
	var cursor := 0
	for w: String in _words:
		var s := text.find(w, cursor)
		if s < 0:
			word_ranges.append([cursor, cursor])
		else:
			word_ranges.append([s, s + w.length()])
			cursor = s + w.length()
	for m in mentions:
		var ms: int = int(m.get("start", -1))
		var me: int = int(m.get("end", -1))
		if ms < 0 or me <= ms:
			continue
		for i in range(_words.size()):
			var wr = word_ranges[i]
			if wr[0] < me and wr[1] > ms:
				_word_mentions[i] = {"kind": String(m.get("kind", "")), "id": String(m.get("id", ""))}


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
	_text_label.meta_clicked.connect(_on_meta_clicked)
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
	# Jitter/floor ratios (0.48, 0.4) preserve the original tuning at the
	# original 0.125s base (jitter ±0.06, floor 0.05) while scaling with
	# whatever _word_interval_s is set to via set_pace().
	var jitter := randf_range(-_word_interval_s * 0.48, _word_interval_s * 0.48)
	_cadence_timer.wait_time = maxf(_word_interval_s * 0.4, _word_interval_s + jitter)
	_cadence_timer.start()


func _on_cadence_tick() -> void:
	if _words_started >= _words.size():
		return

	var idx := _words_started
	_words_started += 1

	# Same ratio-preservation trick as _schedule_next_tick(): 0.025/0.375
	# reproduce the original ±0.2 jitter / 3.0 floor at the original 8.0s
	# base, scaled to whatever _fade_duration_s is set to via set_pace().
	var fade_jitter := randf_range(-_fade_duration_s * 0.025, _fade_duration_s * 0.025)
	var fade_dur := maxf(_fade_duration_s * 0.375, _fade_duration_s + fade_jitter)
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


func _assign_word_colors() -> void:
	_word_colors.resize(_words.size())
	for i in range(_words.size()):
		_word_colors[i] = _text_color

	if _faction_colors.is_empty():
		return

	for faction_name: String in _faction_colors:
		var color: Color = _faction_colors[faction_name]
		var name_words: PackedStringArray = faction_name.split(" ", false)
		if name_words.is_empty():
			continue
		var name_len := name_words.size()
		for i in range(_words.size() - name_len + 1):
			var match_found := true
			for j in range(name_len):
				var clean_word := _words[i + j].strip_edges()
				# Strip trailing punctuation for matching
				while clean_word.length() > 0 and clean_word[-1] in ".,;:!?—-\"'()[]":
					clean_word = clean_word.substr(0, clean_word.length() - 1)
				if clean_word.to_lower() != name_words[j].to_lower():
					match_found = false
					break
			if match_found:
				for j in range(name_len):
					_word_colors[i + j] = color


func _rebuild_bbcode() -> void:
	var bbcode := ""

	for i in range(_words.size()):
		if i > 0:
			bbcode += " "
		var c: Color = _word_colors[i]
		var a := int(_word_alphas[i] * c.a * 255)
		var piece := "[color=#%02x%02x%02x%02x]%s[/color]" % [int(c.r * 255), int(c.g * 255), int(c.b * 255), a, _words[i]]
		var m: Dictionary = _word_mentions[i] if i < _word_mentions.size() else {}
		if not m.is_empty():
			piece = "[url=%s:%s]%s[/url]" % [m.get("kind", ""), m.get("id", ""), piece]
		bbcode += piece

	_text_label.text = bbcode


func _finish_printing() -> void:
	_state = PRINTED
	_cadence_timer.stop()
	for tw in _fade_tweens:
		if tw and tw.is_valid():
			tw.kill()
	_fade_tweens.clear()
	for i in range(_word_alphas.size()):
		_word_alphas[i] = 1.0
	_rebuild_bbcode()
	_cursor.visible = false
	finished_printing.emit(_entry_id)


func _on_meta_clicked(meta: Variant) -> void:
	if typeof(meta) != TYPE_STRING:
		return
	var s := meta as String
	var colon := s.find(":")
	if colon <= 0:
		return
	var kind := s.substr(0, colon)
	var id := s.substr(colon + 1)
	_mention_just_clicked = true
	mention_clicked.emit(kind, id)


func _gui_input(event: InputEvent) -> void:
	if event is InputEventMouseButton and event.pressed and event.button_index == MOUSE_BUTTON_LEFT:
		if _mention_just_clicked:
			_mention_just_clicked = false
			get_viewport().set_input_as_handled()
			return
		if _state == PRINTED:
			expansion_requested.emit(_entry_id)
			get_viewport().set_input_as_handled()


func get_entry_id() -> String:
	return _entry_id


func get_entry_data() -> Dictionary:
	return _entry_data


func get_current_state() -> int:
	return _state
