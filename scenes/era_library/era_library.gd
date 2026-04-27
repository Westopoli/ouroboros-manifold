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

	var header_row := HBoxContainer.new()
	outer.add_child(header_row)

	var header := Label.new()
	header.text = "ERA LIBRARY"
	header.uppercase = true
	header.add_theme_font_override("font", ThemeConstants.font_mono_regular)
	header.add_theme_font_size_override("font_size", ThemeConstants.CLASSIFICATION_LABEL_SIZE)
	header.add_theme_color_override("font_color", ThemeConstants.TERTIARY)
	header.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	header_row.add_child(header)

	var sub_status := UIDataBus.get_subscription_status()
	var sub_container := VBoxContainer.new()
	sub_container.add_theme_constant_override("separation", 2)
	header_row.add_child(sub_container)

	var sub_label := Label.new()
	if sub_status["active"]:
		sub_label.text = "SUBSCRIBED \u2014 %s" % sub_status["plan_name"]
		sub_label.add_theme_color_override("font_color", ThemeConstants.HEALTHY)
	else:
		sub_label.text = "FREE TIER"
		sub_label.add_theme_color_override("font_color", ThemeConstants.SECONDARY)
	sub_label.add_theme_font_override("font", ThemeConstants.font_mono_regular)
	sub_label.add_theme_font_size_override("font_size", ThemeConstants.BODY_DATA_SIZE)
	sub_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	sub_container.add_child(sub_label)

	var manage_link := Label.new()
	manage_link.text = "Manage Subscription"
	manage_link.add_theme_font_override("font", ThemeConstants.font_mono_regular)
	manage_link.add_theme_font_size_override("font_size", ThemeConstants.HINT_TEXT_SIZE)
	manage_link.add_theme_color_override("font_color", ThemeConstants.TERTIARY)
	manage_link.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	manage_link.mouse_filter = Control.MOUSE_FILTER_STOP
	manage_link.gui_input.connect(func(event: InputEvent):
		if event is InputEventMouseButton and event.pressed and event.button_index == MOUSE_BUTTON_LEFT:
			UIDataBus.initiate_purchase("", "manage_subscription")
	)
	sub_container.add_child(manage_link)

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

	_add_key_redemption_card(grid)

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
	if era["is_free"]:
		badge.text = "FREE"
		badge.add_theme_color_override("font_color", ThemeConstants.HEALTHY)
	elif era["is_owned"]:
		badge.text = "OWNED"
		badge.add_theme_color_override("font_color", accent)
	elif era["is_trial"]:
		badge.text = "TRIAL \u2014 %d MISSIONS LEFT" % era["trial_missions_remaining"]
		badge.add_theme_color_override("font_color", accent)
	elif era["subscription_required"]:
		if UIDataBus.get_subscription_status()["active"]:
			badge.text = "SUBSCRIBED"
			badge.add_theme_color_override("font_color", ThemeConstants.INFO)
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

	if not UIDataBus.is_era_accessible(era["id"]) and not UIDataBus.get_subscription_status()["active"]:
		var price := Label.new()
		price.text = "$2.99 or included with subscription"
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


func _add_key_redemption_card(parent: Control) -> void:
	var card = load("res://theme/components/tm_card.tscn").instantiate()
	card.custom_minimum_size = Vector2(300, 100)
	card.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	parent.add_child(card)

	var style: StyleBoxFlat = card.get_theme_stylebox("panel").duplicate()
	style.border_color = Color(ThemeConstants.SECONDARY.r, ThemeConstants.SECONDARY.g, ThemeConstants.SECONDARY.b, 0.3)
	card.add_theme_stylebox_override("panel", style)

	var content = card.get_content_container()

	var title := Label.new()
	title.text = "REDEEM ACCESS KEY"
	title.add_theme_font_override("font", ThemeConstants.font_mono_regular)
	title.add_theme_font_size_override("font_size", ThemeConstants.BODY_DATA_SIZE)
	title.add_theme_color_override("font_color", ThemeConstants.PRIMARY)
	content.add_child(title)

	var sub := Label.new()
	sub.text = "Enter a key code to unlock eras, trials, or subscription time."
	sub.add_theme_font_override("font", ThemeConstants.font_mono_regular)
	sub.add_theme_font_size_override("font_size", ThemeConstants.HINT_TEXT_SIZE)
	sub.add_theme_color_override("font_color", ThemeConstants.TERTIARY)
	sub.autowrap_mode = TextServer.AUTOWRAP_WORD
	content.add_child(sub)

	card.mouse_filter = Control.MOUSE_FILTER_STOP
	card.gui_input.connect(func(event: InputEvent):
		if event is InputEventMouseButton and event.pressed and event.button_index == MOUSE_BUTTON_LEFT:
			SceneRouter.go_to("key_redemption")
	)
