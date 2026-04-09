extends Control

var _input_field: LineEdit
var _submit_btn: Button
var _status_label: Label
var _content_area: VBoxContainer
var _anim_container: Control

func _ready() -> void:
	_build_ui()


func _input(event: InputEvent) -> void:
	if event.is_action_pressed("ui_cancel"):
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
	header.text = "KEY REDEMPTION"
	header.uppercase = true
	header.add_theme_font_override("font", ThemeConstants.font_mono_regular)
	header.add_theme_font_size_override("font_size", ThemeConstants.CLASSIFICATION_LABEL_SIZE)
	header.add_theme_color_override("font_color", ThemeConstants.TERTIARY)
	outer.add_child(header)

	var divider = load("res://theme/components/tm_divider.tscn").instantiate()
	outer.add_child(divider)

	_content_area = VBoxContainer.new()
	_content_area.add_theme_constant_override("separation", 20)
	_content_area.size_flags_vertical = Control.SIZE_EXPAND_FILL
	outer.add_child(_content_area)

	var prompt := Label.new()
	prompt.text = "Enter your access key below."
	prompt.add_theme_font_override("font", ThemeConstants.font_serif_light)
	prompt.add_theme_font_size_override("font_size", ThemeConstants.BODY_NARRATIVE_SIZE)
	prompt.add_theme_color_override("font_color", ThemeConstants.SECONDARY)
	_content_area.add_child(prompt)

	var input_row := HBoxContainer.new()
	input_row.add_theme_constant_override("separation", 12)
	_content_area.add_child(input_row)

	_input_field = LineEdit.new()
	_input_field.placeholder_text = "XXXX-XXXX-XXXX"
	_input_field.add_theme_font_override("font", ThemeConstants.font_mono_medium)
	_input_field.add_theme_font_size_override("font_size", ThemeConstants.BODY_DATA_SIZE)
	_input_field.add_theme_color_override("font_color", ThemeConstants.PRIMARY)
	_input_field.add_theme_color_override("font_placeholder_color", ThemeConstants.TERTIARY)
	_input_field.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_input_field.max_length = 32
	_input_field.text_changed.connect(_on_text_changed)
	_input_field.text_submitted.connect(func(_t: String): _on_submit())
	input_row.add_child(_input_field)

	_submit_btn = load("res://theme/components/tm_button.tscn").instantiate()
	_submit_btn.text = "REDEEM"
	_submit_btn.disabled = true
	_submit_btn.pressed.connect(_on_submit)
	input_row.add_child(_submit_btn)

	_status_label = Label.new()
	_status_label.text = ""
	_status_label.add_theme_font_override("font", ThemeConstants.font_mono_regular)
	_status_label.add_theme_font_size_override("font_size", ThemeConstants.BODY_DATA_SIZE)
	_status_label.add_theme_color_override("font_color", ThemeConstants.DANGER)
	_status_label.visible = false
	_content_area.add_child(_status_label)

	# Animation container (full screen overlay for ASCII anims)
	_anim_container = Control.new()
	_anim_container.set_anchors_preset(Control.PRESET_FULL_RECT)
	_anim_container.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_anim_container.visible = false
	add_child(_anim_container)

	var spacer := Control.new()
	spacer.size_flags_vertical = Control.SIZE_EXPAND_FILL
	_content_area.add_child(spacer)

	var footer := HBoxContainer.new()
	footer.add_theme_constant_override("separation", 12)
	outer.add_child(footer)

	var back_btn = load("res://theme/components/tm_button.tscn").instantiate()
	back_btn.text = "BACK"
	back_btn.style = 1
	back_btn.pressed.connect(func(): SceneRouter.go_back())
	footer.add_child(back_btn)

	var footer_spacer := Control.new()
	footer_spacer.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	footer.add_child(footer_spacer)

	var hint := Label.new()
	hint.text = "ESC to return"
	hint.add_theme_font_override("font", ThemeConstants.font_mono_regular)
	hint.add_theme_font_size_override("font_size", ThemeConstants.HINT_TEXT_SIZE)
	hint.add_theme_color_override("font_color", ThemeConstants.TERTIARY)
	hint.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	footer.add_child(hint)


func _on_text_changed(new_text: String) -> void:
	var sanitized := InputSanitizer.sanitize(new_text, "key_code")
	if sanitized != new_text:
		_input_field.text = sanitized
		_input_field.caret_column = sanitized.length()
	_submit_btn.disabled = sanitized.strip_edges().length() == 0
	_status_label.visible = false


func _on_submit() -> void:
	var code := _input_field.text.strip_edges()
	if code == "":
		return

	_submit_btn.disabled = true
	_input_field.editable = false
	_status_label.visible = false

	# Brief loading state
	_status_label.text = "Validating..."
	_status_label.add_theme_color_override("font_color", ThemeConstants.TERTIARY)
	_status_label.visible = true

	var tw := create_tween()
	tw.tween_interval(0.5)
	tw.tween_callback(func(): _process_redemption(code))


func _process_redemption(code: String) -> void:
	var result := UIDataBus.redeem_key(code)

	if not result.get("success", false):
		_status_label.text = result.get("error_display", "Invalid key. Please check and try again.")
		_status_label.add_theme_color_override("font_color", ThemeConstants.DANGER)
		_status_label.visible = true
		_input_field.editable = true
		_submit_btn.disabled = false
		return

	_status_label.visible = false

	# Play ASCII animation
	_play_redemption_animation(result)


func _play_redemption_animation(result: Dictionary) -> void:
	_anim_container.visible = true

	var anim_bg := ColorRect.new()
	anim_bg.color = Color(ThemeConstants.BASE.r, ThemeConstants.BASE.g, ThemeConstants.BASE.b, 0.9)
	anim_bg.set_anchors_preset(Control.PRESET_FULL_RECT)
	anim_bg.mouse_filter = Control.MOUSE_FILTER_STOP
	_anim_container.add_child(anim_bg)

	var anim_script = load("res://assets/celebrations/key_redemption.gd")
	var anim := Control.new()
	anim.set_script(anim_script)
	anim.set_anchors_preset(Control.PRESET_FULL_RECT)
	_anim_container.add_child(anim)

	anim.animation_finished.connect(func():
		_show_confirmation(result)
	)

	var era_ids: Array = result.get("era_ids", [])
	var era_id: String = era_ids[0] if era_ids.size() > 0 else "roman"

	# Wait a frame for size to propagate, then play
	await get_tree().process_frame
	anim.play_key_redemption(era_id, anim.size / 2.0, _input_field.text)


func _show_confirmation(result: Dictionary) -> void:
	# Clear animation
	for child in _anim_container.get_children():
		child.queue_free()

	var overlay := ColorRect.new()
	overlay.color = Color(ThemeConstants.BASE.r, ThemeConstants.BASE.g, ThemeConstants.BASE.b, 0.9)
	overlay.set_anchors_preset(Control.PRESET_FULL_RECT)
	overlay.mouse_filter = Control.MOUSE_FILTER_STOP
	_anim_container.add_child(overlay)

	var center_box := VBoxContainer.new()
	center_box.add_theme_constant_override("separation", 16)
	center_box.set_anchors_preset(Control.PRESET_CENTER)
	center_box.grow_horizontal = Control.GROW_DIRECTION_BOTH
	center_box.grow_vertical = Control.GROW_DIRECTION_BOTH
	center_box.offset_left = -200
	center_box.offset_right = 200
	center_box.offset_top = -100
	center_box.offset_bottom = 100
	overlay.add_child(center_box)

	# Flavor message
	var flavor: String = result.get("flavor_message", "")
	if flavor != "":
		var era_ids: Array = result.get("era_ids", [])
		var accent := ThemeConstants.DEFAULT_ACCENT
		if era_ids.size() > 0:
			accent = ThemeConstants.get_era_accent(era_ids[0])

		var flavor_label := Label.new()
		flavor_label.text = flavor
		flavor_label.add_theme_font_override("font", ThemeConstants.font_mono_regular)
		flavor_label.add_theme_font_size_override("font_size", ThemeConstants.BODY_DATA_SIZE)
		flavor_label.add_theme_color_override("font_color", accent)
		flavor_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		flavor_label.modulate.a = 0.0
		center_box.add_child(flavor_label)

		var ftw := create_tween()
		ftw.tween_property(flavor_label, "modulate:a", 1.0, 0.5)

	# Confirmation details
	var era_names: Array = result.get("era_names", [])
	var key_type: String = result.get("key_type", "")
	var confirm_text := ""
	match key_type:
		"permanent":
			confirm_text = "%s \u2014 permanently unlocked" % ", ".join(era_names)
		"time_limited":
			var duration: String = result.get("duration_label", "")
			confirm_text = "%s \u2014 unlocked for %s" % [", ".join(era_names), duration]
		"trial":
			var missions: int = result.get("missions_granted", 0)
			confirm_text = "%s \u2014 %d trial missions granted" % [", ".join(era_names), missions]
		_:
			confirm_text = "Key redeemed successfully"

	var confirm_label := Label.new()
	confirm_label.text = confirm_text
	confirm_label.add_theme_font_override("font", ThemeConstants.font_mono_regular)
	confirm_label.add_theme_font_size_override("font_size", ThemeConstants.BODY_DATA_SIZE)
	confirm_label.add_theme_color_override("font_color", ThemeConstants.SECONDARY)
	confirm_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	confirm_label.modulate.a = 0.0
	center_box.add_child(confirm_label)

	var ctw := create_tween()
	ctw.tween_interval(0.8)
	ctw.tween_property(confirm_label, "modulate:a", 1.0, 0.5)

	# Continue button
	var continue_btn = load("res://theme/components/tm_button.tscn").instantiate()
	continue_btn.text = "CONTINUE"
	continue_btn.style = 1
	continue_btn.modulate.a = 0.0
	continue_btn.pressed.connect(func():
		SceneRouter.go_back()
	)
	center_box.add_child(continue_btn)

	var btw := create_tween()
	btw.tween_interval(1.5)
	btw.tween_property(continue_btn, "modulate:a", 1.0, 0.3)
