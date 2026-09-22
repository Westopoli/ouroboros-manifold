extends Control

const EntryView := preload("res://scenes/mockups/chronicle/entry_view.gd")

var _root: Node
var _rows: Dictionary = {}
var _last_rows: Dictionary = {}
var _list: VBoxContainer
var _scroll_container: ScrollContainer
var _expansion: Control
var _expansion_label: RichTextLabel


func _ready() -> void:
	mouse_filter = Control.MOUSE_FILTER_IGNORE

	_scroll_container = ScrollContainer.new()
	_scroll_container.set_anchors_preset(Control.PRESET_FULL_RECT)
	_scroll_container.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	_scroll_container.mouse_filter = Control.MOUSE_FILTER_PASS
	add_child(_scroll_container)

	_list = VBoxContainer.new()
	_list.add_theme_constant_override("separation", 20)
	_list.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_list.mouse_filter = Control.MOUSE_FILTER_PASS
	_scroll_container.add_child(_list)

	_expansion = Control.new()
	_expansion.set_anchors_preset(Control.PRESET_FULL_RECT)
	_expansion.visible = false
	_expansion.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(_expansion)

	var bg := ColorRect.new()
	bg.color = Color(0.04, 0.05, 0.07, 0.94)
	bg.set_anchors_preset(Control.PRESET_FULL_RECT)
	bg.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_expansion.add_child(bg)

	_expansion_label = RichTextLabel.new()
	_expansion_label.bbcode_enabled = true
	_expansion_label.scroll_active = false
	_expansion_label.set_anchors_preset(Control.PRESET_FULL_RECT)
	_expansion_label.offset_left = 24
	_expansion_label.offset_right = -24
	_expansion_label.offset_top = 24
	_expansion_label.offset_bottom = -24
	_expansion_label.add_theme_font_size_override("normal_font_size", 24)
	_expansion_label.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_expansion.add_child(_expansion_label)

	_expansion.gui_input.connect(_on_expansion_input)


func setup(root: Node) -> void:
	_root = root


func begin() -> void:
	for c in _list.get_children():
		_list.remove_child(c)
		c.free()
	_rows.clear()
	_last_rows.clear()
	_expansion.visible = false
	position.x = 60
	modulate.a = 0.0
	var tw := create_tween()
	tw.set_ease(Tween.EASE_OUT).set_trans(Tween.TRANS_CUBIC)
	tw.tween_property(self, "position:x", 0.0, 0.40)
	tw.parallel().tween_property(self, "modulate:a", 1.0, 0.40)


func render(rows: Array, expanded_id: String) -> void:
	_last_rows.clear()
	for r in rows:
		var eid := String(r.entry_id)
		_last_rows[eid] = r
		if not _rows.has(eid):
			var view := EntryView.new()
			view.setup(_root)
			_list.add_child(view)
			_rows[eid] = view
		_rows[eid].render(r)

	if expanded_id != "" and _last_rows.has(expanded_id):
		_show_expansion(_last_rows[expanded_id])
	else:
		_expansion.visible = false

	if _rows.has(expanded_id):
		_scroll_container.ensure_control_visible(_rows[expanded_id])
	elif not rows.is_empty():
		var last_id := String(rows[rows.size() - 1].entry_id)
		if _rows.has(last_id):
			_scroll_container.ensure_control_visible(_rows[last_id])


func _show_expansion(row: Dictionary) -> void:
	var text := String(row.expanded_text)
	var mentions: Array = row.expanded_mentions
	_expansion_label.text = EntryView.build_bbcode(text, mentions) + "\n\n[color=#8f8c86]click or press Escape to close[/color]"
	_expansion.visible = true


func _on_expansion_input(event: InputEvent) -> void:
	if event is InputEventMouseButton and event.pressed:
		if _root != null:
			_root.qa_dismiss()
