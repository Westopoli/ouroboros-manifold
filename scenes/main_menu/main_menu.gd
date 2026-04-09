extends Control

var _menu_items: Array[Control] = []

func _ready() -> void:
	_build_ui()
	_animate_entrance()


func _build_ui() -> void:
	var bg := ColorRect.new()
	bg.color = ThemeConstants.BASE
	bg.set_anchors_preset(Control.PRESET_FULL_RECT)
	add_child(bg)

	var content := VBoxContainer.new()
	content.set_anchors_preset(Control.PRESET_CENTER_LEFT)
	content.anchor_left = 0.15
	content.anchor_right = 0.5
	content.anchor_top = 0.3
	content.anchor_bottom = 0.8
	content.offset_left = 0
	content.offset_right = 0
	content.offset_top = 0
	content.offset_bottom = 0
	content.add_theme_constant_override("separation", 0)
	add_child(content)

	var classification := Label.new()
	classification.text = "OUROBOROS MANIFOLD"
	classification.uppercase = true
	classification.add_theme_font_override("font", ThemeConstants.font_mono_regular)
	classification.add_theme_font_size_override("font_size", ThemeConstants.CLASSIFICATION_LABEL_SIZE)
	classification.add_theme_color_override("font_color", ThemeConstants.TERTIARY)
	content.add_child(classification)

	var spacer1 := Control.new()
	spacer1.custom_minimum_size.y = 8
	content.add_child(spacer1)

	var title := Label.new()
	title.text = "Ouroboros Manifold"
	title.add_theme_font_override("font", ThemeConstants.font_serif_regular)
	title.add_theme_font_size_override("font_size", ThemeConstants.TITLE_SIZE)
	title.add_theme_color_override("font_color", ThemeConstants.PRIMARY)
	content.add_child(title)

	var spacer2 := Control.new()
	spacer2.custom_minimum_size.y = 40
	content.add_child(spacer2)

	var menu_data := [
		{"label": "NEW GAME", "action": "new_game"},
		{"label": "CONTINUE", "action": "load_game"},
		{"label": "ERA LIBRARY", "action": "era_library"},
		{"label": "SETTINGS", "action": "settings"},
		{"label": "QUIT", "action": "quit"},
	]

	var has_saves := UIDataBus.get_save_slots().size() > 0

	for item_data in menu_data:
		var item := _create_menu_item(item_data["label"], item_data["action"])
		if item_data["action"] == "load_game" and not has_saves:
			item.modulate.a = 0.3
			item.mouse_filter = Control.MOUSE_FILTER_IGNORE
		content.add_child(item)
		_menu_items.append(item)

	var spacer3 := Control.new()
	spacer3.custom_minimum_size.y = 40
	content.add_child(spacer3)

	var key_hint := Label.new()
	key_hint.text = "Have an access key? Visit the Era Library to redeem it."
	key_hint.add_theme_font_override("font", ThemeConstants.font_mono_regular)
	key_hint.add_theme_font_size_override("font_size", ThemeConstants.HINT_TEXT_SIZE)
	key_hint.add_theme_color_override("font_color", ThemeConstants.TERTIARY)
	content.add_child(key_hint)

	var version := Label.new()
	version.text = "v0.9.0"
	version.add_theme_font_override("font", ThemeConstants.font_mono_regular)
	version.add_theme_font_size_override("font_size", ThemeConstants.HINT_TEXT_SIZE)
	version.add_theme_color_override("font_color", ThemeConstants.TERTIARY)
	version.set_anchors_preset(Control.PRESET_BOTTOM_RIGHT)
	version.offset_left = -80
	version.offset_top = -30
	version.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	add_child(version)


func _create_menu_item(label_text: String, action: String) -> Control:
	var container := HBoxContainer.new()
	container.custom_minimum_size.y = 48
	container.add_theme_constant_override("separation", 12)

	var accent_line := ColorRect.new()
	accent_line.custom_minimum_size = Vector2(0, 2)
	accent_line.color = ThemeConstants.SECONDARY
	accent_line.modulate.a = 0.0
	container.add_child(accent_line)

	var label := Label.new()
	label.text = label_text
	label.add_theme_font_override("font", ThemeConstants.font_mono_regular)
	label.add_theme_font_size_override("font_size", 21)
	label.add_theme_color_override("font_color", ThemeConstants.SECONDARY)
	container.add_child(label)

	container.mouse_filter = Control.MOUSE_FILTER_STOP
	container.mouse_entered.connect(func():
		label.add_theme_color_override("font_color", ThemeConstants.PRIMARY)
		var tw := create_tween()
		tw.tween_property(accent_line, "custom_minimum_size:x", 16.0, 0.15)
		tw.parallel().tween_property(accent_line, "modulate:a", 1.0, 0.15)
	)
	container.mouse_exited.connect(func():
		label.add_theme_color_override("font_color", ThemeConstants.SECONDARY)
		var tw := create_tween()
		tw.tween_property(accent_line, "custom_minimum_size:x", 0.0, 0.15)
		tw.parallel().tween_property(accent_line, "modulate:a", 0.0, 0.15)
	)
	container.gui_input.connect(func(event: InputEvent):
		if event is InputEventMouseButton and event.pressed and event.button_index == MOUSE_BUTTON_LEFT:
			_on_menu_action(action)
	)
	return container


func _on_menu_action(action: String) -> void:
	match action:
		"quit":
			get_tree().quit()
		_:
			SceneRouter.go_to(action)


func _animate_entrance() -> void:
	var delay := ThemeConstants.STAGGER_BASE_DELAY
	for i in range(get_child_count()):
		var child := get_child(i)
		if child is ColorRect:
			continue
		if child is Label:
			child.modulate.a = 0.0
			child.position.y += 8.0
			var original_y: float = child.position.y - 8.0
			var tw := create_tween().set_ease(Tween.EASE_OUT).set_trans(Tween.TRANS_CUBIC)
			tw.tween_interval(delay)
			tw.tween_property(child, "modulate:a", 1.0, ThemeConstants.ELEMENT_ANIM_DURATION)
			tw.parallel().tween_property(child, "position:y", original_y, ThemeConstants.ELEMENT_ANIM_DURATION)
			delay += ThemeConstants.STAGGER_INCREMENT

	var content_node: VBoxContainer = null
	for child in get_children():
		if child is VBoxContainer:
			content_node = child
			break
	if not content_node:
		return

	for i in range(content_node.get_child_count()):
		var child := content_node.get_child(i)
		child.modulate.a = 0.0
		var tw := create_tween().set_ease(Tween.EASE_OUT).set_trans(Tween.TRANS_CUBIC)
		tw.tween_interval(delay)
		tw.tween_property(child, "modulate:a", 1.0, ThemeConstants.ELEMENT_ANIM_DURATION)
		delay += ThemeConstants.STAGGER_INCREMENT
