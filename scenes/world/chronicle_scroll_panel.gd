extends PanelContainer

signal entry_finished_printing(entry_id: String)
signal entry_expansion_opened(entry_id: String)
signal entry_expansion_closed(entry_id: String)
signal all_entries_finished()

var _entries: Dictionary = {}
var _printing_id: String = ""
var _total_expected: int = 0
var _finished_count: int = 0
var _paused: bool = false
var _time_jump_active: bool = false
var _accent: Color

var _scroll: ScrollContainer
var _entry_container: VBoxContainer
var _expansion_overlay: Control


func _ready() -> void:
	_accent = ThemeConstants.get_era_accent(EraConfig.ACTIVE_ERA_ID)
	_build_ui()


func _build_ui() -> void:
	var style := StyleBoxFlat.new()
	style.bg_color = ThemeConstants.SURFACE
	style.border_color = ThemeConstants.BORDER_COLOR
	style.border_width_left = ThemeConstants.BORDER_WIDTH
	add_theme_stylebox_override("panel", style)

	var margin := MarginContainer.new()
	margin.set_anchors_preset(Control.PRESET_FULL_RECT)
	margin.add_theme_constant_override("margin_left", 20)
	margin.add_theme_constant_override("margin_right", 20)
	margin.add_theme_constant_override("margin_top", 24)
	margin.add_theme_constant_override("margin_bottom", 24)
	add_child(margin)

	var vbox := VBoxContainer.new()
	vbox.add_theme_constant_override("separation", 12)
	margin.add_child(vbox)

	var header := Label.new()
	header.text = "CHRONICLE"
	header.uppercase = true
	header.add_theme_font_override("font", ThemeConstants.font_mono_regular)
	header.add_theme_font_size_override("font_size", ThemeConstants.SECTION_LABEL_SIZE)
	header.add_theme_color_override("font_color", ThemeConstants.TERTIARY)
	vbox.add_child(header)

	var divider = load("res://theme/components/tm_divider.tscn").instantiate()
	vbox.add_child(divider)

	_scroll = ScrollContainer.new()
	_scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
	_scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	vbox.add_child(_scroll)

	_entry_container = VBoxContainer.new()
	_entry_container.add_theme_constant_override("separation", 4)
	_entry_container.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_scroll.add_child(_entry_container)

	_expansion_overlay = Control.new()
	_expansion_overlay.set_anchors_preset(Control.PRESET_FULL_RECT)
	_expansion_overlay.visible = false
	_expansion_overlay.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(_expansion_overlay)


func begin_time_jump(total_entries: int) -> void:
	_total_expected = total_entries
	_finished_count = 0
	_time_jump_active = true
	_paused = false
	_printing_id = ""
	_entries.clear()
	for child in _entry_container.get_children():
		child.queue_free()
	_close_expansion()


func queue_entry(entry_data: Dictionary) -> void:
	var entry_id: String = entry_data.get("entry_id", "")
	var entry_scene := load("res://scenes/world/chronicle_entry.tscn")
	var entry_node: Node = entry_scene.instantiate()
	entry_node.setup(entry_data, _accent)
	entry_node.finished_printing.connect(_on_entry_finished)
	entry_node.expansion_requested.connect(_on_expansion_requested)
	_entry_container.add_child(entry_node)
	_entries[entry_id] = entry_node

	entry_node.modulate.a = 0.0
	entry_node.position.x = 40
	var tw := create_tween().set_ease(Tween.EASE_OUT).set_trans(Tween.TRANS_CUBIC)
	tw.tween_property(entry_node, "modulate:a", 1.0, 0.3)
	tw.parallel().tween_property(entry_node, "position:x", 0.0, 0.3)


func start_printing(entry_id: String) -> void:
	if not _entries.has(entry_id):
		return
	_printing_id = entry_id
	_entries[entry_id].start_printing()
	_auto_scroll_to_entry(entry_id)


func end_time_jump() -> void:
	_time_jump_active = false


func pause() -> void:
	_paused = true
	if _printing_id != "" and _entries.has(_printing_id):
		_entries[_printing_id].pause_printing()


func resume() -> void:
	_paused = false
	if _printing_id != "" and _entries.has(_printing_id) and not _expansion_overlay.visible:
		_entries[_printing_id].resume_printing()


var _rest_position_x: float = 0.0
var _rest_position_stored: bool = false


func slide_in() -> void:
	if not _rest_position_stored:
		await get_tree().process_frame
		_rest_position_x = position.x
		_rest_position_stored = true
	position.x = _rest_position_x + 200
	modulate.a = 0.0
	visible = true
	var tw := create_tween().set_ease(Tween.EASE_OUT).set_trans(Tween.TRANS_CUBIC)
	tw.tween_property(self, "position:x", _rest_position_x, 0.4)
	tw.parallel().tween_property(self, "modulate:a", 1.0, 0.4)


func slide_out() -> void:
	if not _rest_position_stored:
		_rest_position_x = position.x
		_rest_position_stored = true
	var tw := create_tween().set_ease(Tween.EASE_IN).set_trans(Tween.TRANS_CUBIC)
	tw.tween_property(self, "position:x", _rest_position_x + 200, 0.4)
	tw.parallel().tween_property(self, "modulate:a", 0.0, 0.4)


func _on_entry_finished(entry_id: String) -> void:
	_finished_count += 1
	_printing_id = ""
	entry_finished_printing.emit(entry_id)
	if _finished_count >= _total_expected:
		all_entries_finished.emit()


func _on_expansion_requested(entry_id: String) -> void:
	if not _entries.has(entry_id):
		return
	_show_expansion(entry_id)


func _show_expansion(entry_id: String) -> void:
	_close_expansion()

	if _printing_id != "" and _entries.has(_printing_id):
		_entries[_printing_id].pause_printing()

	var entry_data: Dictionary = _entries[entry_id].get_entry_data()
	var expansion: Node = load("res://scenes/world/chronicle_entry_expansion.tscn").instantiate()
	expansion.setup(entry_data, _accent)
	expansion.dismissed.connect(func():
		_close_expansion()
		if not _paused and _printing_id != "" and _entries.has(_printing_id):
			_entries[_printing_id].resume_printing()
		entry_expansion_closed.emit(entry_id)
	)
	_expansion_overlay.add_child(expansion)
	_expansion_overlay.visible = true
	_expansion_overlay.mouse_filter = Control.MOUSE_FILTER_STOP
	entry_expansion_opened.emit(entry_id)


func _close_expansion() -> void:
	for child in _expansion_overlay.get_children():
		child.queue_free()
	_expansion_overlay.visible = false
	_expansion_overlay.mouse_filter = Control.MOUSE_FILTER_IGNORE


func _auto_scroll_to_entry(entry_id: String) -> void:
	if not _entries.has(entry_id):
		return
	await get_tree().process_frame
	var entry_node: Control = _entries[entry_id]
	var target_scroll := maxf(0.0, entry_node.position.y - 20.0)
	var tw := create_tween().set_ease(Tween.EASE_OUT).set_trans(Tween.TRANS_CUBIC)
	tw.tween_property(_scroll, "scroll_vertical", int(target_scroll), 0.3)
