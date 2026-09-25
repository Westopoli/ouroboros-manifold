extends Control

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

	# Subscription model removed 2026-05-09 — see docs/bible_history/game_bible_1_23.md (bible_monetization.md folded into the hub 2026-05-31; hub rewritten 2026-09-10).
	# Previously this header row held a SUBSCRIBED/FREE TIER badge and a "Manage Subscription" link.
	var header := Label.new()
	header.text = "ERA LIBRARY"
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

	var grid := GridContainer.new()
	grid.columns = 3
	grid.add_theme_constant_override("h_separation", 16)
	grid.add_theme_constant_override("v_separation", 16)
	grid.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	scroll.add_child(grid)

	var eras := UIDataBus.get_all_eras()
	for era in eras:
		_add_era_card(grid, era)

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


func qa_state() -> Dictionary:
	return {
		"scene": "era_library",
		"tick": -1,
		"era_count": UIDataBus.get_all_eras().size(),
		"plants": [],
	}


func _add_era_card(parent: Control, era: Dictionary) -> void:
	var card = load("res://theme/components/tm_card.tscn").instantiate()
	card.custom_minimum_size = Vector2(300, 350)
	card.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	parent.add_child(card)
	var content = card.get_content_container()

	var accent := Color(era["accent_color"])
	var accent_dim := Color(accent.r, accent.g, accent.b, 0.15)

	var banner := ColorRect.new()
	banner.custom_minimum_size.y = 85
	banner.color = accent_dim
	content.add_child(banner)

	var banner_vbox := VBoxContainer.new()
	banner_vbox.set_anchors_preset(Control.PRESET_FULL_RECT)
	banner_vbox.add_theme_constant_override("separation", 6)
	banner.add_child(banner_vbox)

	var spacer_top := Control.new()
	spacer_top.custom_minimum_size.y = 10
	banner_vbox.add_child(spacer_top)

	var era_name := Label.new()
	era_name.text = era["name"]
	era_name.add_theme_font_override("font", ThemeConstants.font_serif_regular)
	era_name.add_theme_font_size_override("font_size", 30)
	era_name.add_theme_color_override("font_color", accent)
	era_name.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	banner_vbox.add_child(era_name)

	var badge := Label.new()
	badge.add_theme_font_override("font", ThemeConstants.font_mono_regular)
	badge.add_theme_font_size_override("font_size", ThemeConstants.ERA_BADGE_SIZE)
	badge.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	if era["is_owned"]:
		badge.text = "OWNED"
		badge.add_theme_color_override("font_color", accent)
	else:
		badge.text = "LOCKED"
		badge.add_theme_color_override("font_color", ThemeConstants.TERTIARY)
	banner_vbox.add_child(badge)

	var banner_spacer := Control.new()
	banner_spacer.custom_minimum_size.y = 12
	content.add_child(banner_spacer)

	var desc := Label.new()
	desc.text = era["description"]
	desc.add_theme_font_override("font", ThemeConstants.font_serif_regular)
	desc.add_theme_font_size_override("font_size", ThemeConstants.BODY_DATA_SIZE)
	desc.add_theme_color_override("font_color", ThemeConstants.SECONDARY)
	desc.autowrap_mode = TextServer.AUTOWRAP_WORD
	content.add_child(desc)

	var tier_label := Label.new()
	tier_label.text = "TIER %d/3" % era["tier_progress"]["current_tier"]
	tier_label.add_theme_font_override("font", ThemeConstants.font_mono_regular)
	tier_label.add_theme_font_size_override("font_size", ThemeConstants.BODY_DATA_SMALL_SIZE)
	tier_label.add_theme_color_override("font_color", ThemeConstants.SECONDARY)
	content.add_child(tier_label)

	var tier_bar = load("res://theme/components/tm_progress_bar.tscn").instantiate()
	tier_bar.value = era["tier_progress"]["progress_to_next"]
	tier_bar.bar_color = accent
	tier_bar.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	content.add_child(tier_bar)

	var mastery_label := Label.new()
	mastery_label.text = "MASTERY"
	mastery_label.add_theme_font_override("font", ThemeConstants.font_mono_regular)
	mastery_label.add_theme_font_size_override("font_size", ThemeConstants.BODY_DATA_SMALL_SIZE)
	mastery_label.add_theme_color_override("font_color", ThemeConstants.SECONDARY)
	content.add_child(mastery_label)

	var mastery_bar = load("res://theme/components/tm_progress_bar.tscn").instantiate()
	mastery_bar.value = era["mastery_progress"]
	mastery_bar.bar_color = Color(accent.r, accent.g, accent.b, 0.6)
	mastery_bar.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	content.add_child(mastery_bar)

	if not UIDataBus.is_era_accessible(era["id"]):
		var price := Label.new()
		price.text = "Available on Steam"
		price.add_theme_font_override("font", ThemeConstants.font_mono_regular)
		price.add_theme_font_size_override("font_size", ThemeConstants.BODY_DATA_SMALL_SIZE)
		price.add_theme_color_override("font_color", ThemeConstants.SECONDARY)
		content.add_child(price)

	var era_id: String = era["id"]
	var playable := era_id == "settled_reach"
	if not playable:
		card.modulate = Color(1, 1, 1, 0.35)
		var coming_soon := Label.new()
		coming_soon.text = "COMING SOON"
		coming_soon.add_theme_font_override("font", ThemeConstants.font_mono_regular)
		coming_soon.add_theme_font_size_override("font_size", ThemeConstants.BODY_DATA_SMALL_SIZE)
		coming_soon.add_theme_color_override("font_color", ThemeConstants.TERTIARY)
		coming_soon.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		content.add_child(coming_soon)
	else:
		card.mouse_filter = Control.MOUSE_FILTER_STOP
		card.gui_input.connect(func(event: InputEvent):
			if event is InputEventMouseButton and event.pressed and event.button_index == MOUSE_BUTTON_LEFT:
				SceneRouter.go_to("era_detail", {"era_id": era_id})
		)


