extends RefCounted

# One Era Library card built from a pack manifest; clicking opens the viewing-only detail.


static func build(parent: Control, m: Dictionary, owned: bool) -> void:
	var card = load("res://theme/components/tm_card.tscn").instantiate()
	card.custom_minimum_size = Vector2(300, 350)
	card.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	parent.add_child(card)
	var content = card.get_content_container()
	var accent := Color(m["era_accent_color"])

	var banner := ColorRect.new()
	banner.custom_minimum_size.y = 85
	banner.color = Color(accent.r, accent.g, accent.b, 0.15)
	content.add_child(banner)
	var vb := VBoxContainer.new()
	vb.set_anchors_preset(Control.PRESET_FULL_RECT)
	banner.add_child(vb)
	var name_label := _label(m["era_display_name"], ThemeConstants.font_serif_regular, 30, accent)
	name_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	vb.add_child(name_label)
	var badge := _label("OWNED" if owned else "LOCKED", ThemeConstants.font_mono_regular,
		ThemeConstants.ERA_BADGE_SIZE, accent if owned else ThemeConstants.TERTIARY)
	badge.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	vb.add_child(badge)

	for key in ["era_spatial_scale", "era_tone"]:
		var l := _label(str(m[key]), ThemeConstants.font_serif_regular, ThemeConstants.BODY_DATA_SIZE, ThemeConstants.SECONDARY)
		l.autowrap_mode = TextServer.AUTOWRAP_WORD
		content.add_child(l)

	var era_id: String = m["era_id"]
	card.mouse_filter = Control.MOUSE_FILTER_STOP
	card.gui_input.connect(func(event: InputEvent):
		if event is InputEventMouseButton and event.pressed and event.button_index == MOUSE_BUTTON_LEFT:
			SceneRouter.go_to("era_detail", {"era_id": era_id}))


static func _label(text: String, font: Font, size: int, color: Color) -> Label:
	var l := Label.new()
	l.text = text
	l.add_theme_font_override("font", font)
	l.add_theme_font_size_override("font_size", size)
	l.add_theme_color_override("font_color", color)
	return l
