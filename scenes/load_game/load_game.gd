extends Control

var _slot_list: VBoxContainer
var _empty_label: Label
var _confirm_overlay: Control

func _ready() -> void:
	_build_ui()


func _input(event: InputEvent) -> void:
	if event.is_action_pressed("ui_cancel"):
		if _confirm_overlay and _confirm_overlay.visible:
			_confirm_overlay.visible = false
		else:
			SceneRouter.go_back()


func _build_ui() -> void:
	var bg := ColorRect.new()
	bg.color = ThemeConstants.BASE
	bg.set_anchors_preset(Control.PRESET_FULL_RECT)
	add_child(bg)

	var margin := MarginContainer.new()
	margin.set_anchors_preset(Control.PRESET_FULL_RECT)
	margin.add_theme_constant_override("margin_left", 80)
	margin.add_theme_constant_override("margin_right", 80)
	margin.add_theme_constant_override("margin_top", 60)
	margin.add_theme_constant_override("margin_bottom", 60)
	add_child(margin)

	var outer := VBoxContainer.new()
	outer.add_theme_constant_override("separation", 20)
	margin.add_child(outer)

	var header := Label.new()
	header.text = "CONTINUE"
	header.uppercase = true
	header.add_theme_font_override("font", ThemeConstants.font_mono_regular)
	header.add_theme_font_size_override("font_size", ThemeConstants.CLASSIFICATION_LABEL_SIZE)
	header.add_theme_color_override("font_color", ThemeConstants.TERTIARY)
	outer.add_child(header)

	var divider = load("res://theme/components/tm_divider.tscn").instantiate()
	outer.add_child(divider)

	var scroll := ScrollContainer.new()
	scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
	outer.add_child(scroll)

	_slot_list = VBoxContainer.new()
	_slot_list.add_theme_constant_override("separation", 8)
	_slot_list.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	scroll.add_child(_slot_list)

	_empty_label = Label.new()
	_empty_label.text = "No saved campaigns. Start a new game to begin."
	_empty_label.add_theme_font_override("font", ThemeConstants.font_serif_regular)
	_empty_label.add_theme_font_size_override("font_size", 21)
	_empty_label.add_theme_color_override("font_color", ThemeConstants.SECONDARY)
	_empty_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_empty_label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_slot_list.add_child(_empty_label)

	_refresh_slots()

	var footer := HBoxContainer.new()
	footer.add_theme_constant_override("separation", 12)
	outer.add_child(footer)

	var back_btn = load("res://theme/components/tm_button.tscn").instantiate()
	back_btn.text = "BACK"
	back_btn.style = 1
	back_btn.pressed.connect(func(): SceneRouter.go_back())
	footer.add_child(back_btn)

	var spacer := Control.new()
	spacer.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	footer.add_child(spacer)

	var hint := Label.new()
	hint.text = "ESC to return"
	hint.add_theme_font_override("font", ThemeConstants.font_mono_regular)
	hint.add_theme_font_size_override("font_size", ThemeConstants.HINT_TEXT_SIZE)
	hint.add_theme_color_override("font_color", ThemeConstants.TERTIARY)
	hint.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	footer.add_child(hint)

	_build_confirm_overlay()


func _refresh_slots() -> void:
	for child in _slot_list.get_children():
		if child != _empty_label:
			child.queue_free()

	var slots := UIDataBus.get_save_slots()
	_empty_label.visible = slots.is_empty()

	for slot in slots:
		_add_slot_card(slot)


func _add_slot_card(slot: Dictionary) -> void:
	var card = load("res://theme/components/tm_card.tscn").instantiate()
	_slot_list.add_child(card)
	var content = card.get_content_container()

	var accent := Color(slot["era_accent_color"])
	var style: StyleBoxFlat = card.get_theme_stylebox("panel").duplicate()
	style.border_width_left = 2
	style.border_color = accent
	card.add_theme_stylebox_override("panel", style)

	var top_row := HBoxContainer.new()
	top_row.add_theme_constant_override("separation", 12)
	content.add_child(top_row)

	var name_label := Label.new()
	name_label.text = slot["name"]
	name_label.add_theme_font_override("font", ThemeConstants.font_mono_regular)
	name_label.add_theme_font_size_override("font_size", 21)
	name_label.add_theme_color_override("font_color", ThemeConstants.PRIMARY)
	name_label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	top_row.add_child(name_label)

	var playtime := _format_playtime(slot["playtime_seconds"])
	var time_label := Label.new()
	time_label.text = playtime
	time_label.add_theme_font_override("font", ThemeConstants.font_mono_regular)
	time_label.add_theme_font_size_override("font_size", ThemeConstants.HINT_TEXT_SIZE)
	time_label.add_theme_color_override("font_color", ThemeConstants.TERTIARY)
	top_row.add_child(time_label)

	var delete_btn := Button.new()
	delete_btn.text = "\u00d7"
	delete_btn.add_theme_color_override("font_color", ThemeConstants.DANGER)
	delete_btn.add_theme_font_size_override("font_size", 24)
	delete_btn.flat = true
	var slot_id: String = slot["id"]
	delete_btn.pressed.connect(func(): _show_delete_confirm(slot_id))
	top_row.add_child(delete_btn)

	var era_line := Label.new()
	era_line.text = "%s \u2014 %s" % [slot["era_name"], slot["template_name"]]
	era_line.add_theme_font_override("font", ThemeConstants.font_mono_regular)
	era_line.add_theme_font_size_override("font_size", ThemeConstants.BODY_DATA_SIZE)
	era_line.add_theme_color_override("font_color", ThemeConstants.SECONDARY)
	content.add_child(era_line)

	var chapter_line := Label.new()
	chapter_line.text = "Chapter %d, Generation %d" % [slot["chapter"], slot["generation"]]
	chapter_line.add_theme_font_override("font", ThemeConstants.font_mono_regular)
	chapter_line.add_theme_font_size_override("font_size", ThemeConstants.BODY_DATA_SMALL_SIZE)
	chapter_line.add_theme_color_override("font_color", ThemeConstants.TERTIARY)
	content.add_child(chapter_line)

	card.mouse_filter = Control.MOUSE_FILTER_STOP
	card.gui_input.connect(func(event: InputEvent):
		if event is InputEventMouseButton and event.pressed and event.button_index == MOUSE_BUTTON_LEFT:
			SceneRouter.go_to("mission_briefing", {"slot_id": slot_id})
	)


func _format_playtime(seconds: int) -> String:
	var hours := seconds / 3600
	var minutes := (seconds % 3600) / 60
	return "%dh %02dm" % [hours, minutes]


func _build_confirm_overlay() -> void:
	_confirm_overlay = ColorRect.new()
	_confirm_overlay.color = Color(0, 0, 0, 0.6)
	_confirm_overlay.set_anchors_preset(Control.PRESET_FULL_RECT)
	_confirm_overlay.visible = false
	_confirm_overlay.mouse_filter = Control.MOUSE_FILTER_STOP
	add_child(_confirm_overlay)

	var center := CenterContainer.new()
	center.set_anchors_preset(Control.PRESET_FULL_RECT)
	_confirm_overlay.add_child(center)

	var card = load("res://theme/components/tm_card.tscn").instantiate()
	card.custom_minimum_size = Vector2(400, 0)
	center.add_child(card)
	var content = card.get_content_container()

	var msg := Label.new()
	msg.text = "Delete this save? This cannot be undone."
	msg.add_theme_font_override("font", ThemeConstants.font_mono_regular)
	msg.add_theme_font_size_override("font_size", ThemeConstants.BODY_DATA_SIZE)
	msg.add_theme_color_override("font_color", ThemeConstants.PRIMARY)
	msg.autowrap_mode = TextServer.AUTOWRAP_WORD
	content.add_child(msg)

	var btn_row := HBoxContainer.new()
	btn_row.add_theme_constant_override("separation", 12)
	content.add_child(btn_row)

	var delete_btn = load("res://theme/components/tm_button.tscn").instantiate()
	delete_btn.text = "DELETE"
	delete_btn.accent_color = ThemeConstants.DANGER
	delete_btn.name = "DeleteConfirmBtn"
	btn_row.add_child(delete_btn)

	var cancel_btn = load("res://theme/components/tm_button.tscn").instantiate()
	cancel_btn.text = "CANCEL"
	cancel_btn.style = 1
	cancel_btn.pressed.connect(func(): _confirm_overlay.visible = false)
	btn_row.add_child(cancel_btn)


var _pending_delete_id: String = ""

func _show_delete_confirm(slot_id: String) -> void:
	_pending_delete_id = slot_id
	_confirm_overlay.visible = true
	var delete_btn: Button = _confirm_overlay.find_child("DeleteConfirmBtn", true, false)
	if delete_btn:
		for conn in delete_btn.pressed.get_connections():
			delete_btn.pressed.disconnect(conn["callable"])
		delete_btn.pressed.connect(func():
			UIDataBus.delete_save_slot(_pending_delete_id)
			_confirm_overlay.visible = false
			_refresh_slots()
		)
