extends Control

var _era: Dictionary = {}
var _era_id: String = ""
var _purchase_overlay: Control

func setup(params: Dictionary) -> void:
	_era_id = params.get("era_id", "roman")
	_era = UIDataBus.get_era_detail(_era_id)
	_build_ui()


func _ready() -> void:
	if _era.is_empty():
		_era_id = "roman"
		_era = UIDataBus.get_era_detail(_era_id)
		_build_ui()


func _input(event: InputEvent) -> void:
	if event.is_action_pressed("ui_cancel"):
		if _purchase_overlay and _purchase_overlay.visible:
			_purchase_overlay.visible = false
		else:
			SceneRouter.go_back()


func _build_ui() -> void:
	for child in get_children():
		child.queue_free()

	var accent := Color(_era["accent_color"])
	var accent_dim := Color(accent.r, accent.g, accent.b, 0.15)

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
	outer.add_theme_constant_override("separation", 16)
	margin.add_child(outer)

	var classification := Label.new()
	classification.text = "ERA DOSSIER"
	classification.uppercase = true
	classification.add_theme_font_override("font", ThemeConstants.font_mono_regular)
	classification.add_theme_font_size_override("font_size", ThemeConstants.CLASSIFICATION_LABEL_SIZE)
	classification.add_theme_color_override("font_color", accent)
	outer.add_child(classification)

	var title := Label.new()
	title.text = _era["name"]
	title.add_theme_font_override("font", ThemeConstants.font_serif_regular)
	title.add_theme_font_size_override("font_size", ThemeConstants.TITLE_SIZE)
	title.add_theme_color_override("font_color", accent)
	outer.add_child(title)

	var badge := Label.new()
	badge.add_theme_font_override("font", ThemeConstants.font_mono_regular)
	badge.add_theme_font_size_override("font_size", ThemeConstants.ERA_BADGE_SIZE)
	_set_badge_text(badge, accent)
	outer.add_child(badge)

	var divider = load("res://theme/components/tm_divider.tscn").instantiate()
	outer.add_child(divider)

	var scroll := ScrollContainer.new()
	scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
	outer.add_child(scroll)

	var columns := HBoxContainer.new()
	columns.add_theme_constant_override("separation", 40)
	columns.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	scroll.add_child(columns)

	_build_left_column(columns, accent)
	_build_right_column(columns, accent, accent_dim)

	var footer := HBoxContainer.new()
	footer.add_theme_constant_override("separation", 12)
	outer.add_child(footer)

	var back_btn = load("res://theme/components/tm_button.tscn").instantiate()
	back_btn.text = "BACK TO ERA LIBRARY"
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

	_build_purchase_overlay()


func _set_badge_text(badge: Label, accent: Color) -> void:
	if _era["is_owned"]:
		badge.text = "OWNED"
		badge.add_theme_color_override("font_color", accent)
	else:
		badge.text = "LOCKED"
		badge.add_theme_color_override("font_color", ThemeConstants.TERTIARY)


func _build_left_column(parent: Control, accent: Color) -> void:
	var col := VBoxContainer.new()
	col.add_theme_constant_override("separation", 16)
	col.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	parent.add_child(col)

	var overview_label := Label.new()
	overview_label.text = "THEMATIC OVERVIEW"
	overview_label.uppercase = true
	overview_label.add_theme_font_override("font", ThemeConstants.font_mono_regular)
	overview_label.add_theme_font_size_override("font_size", ThemeConstants.SECTION_LABEL_SIZE)
	overview_label.add_theme_color_override("font_color", ThemeConstants.TERTIARY)
	col.add_child(overview_label)

	var desc := Label.new()
	desc.text = _era["description"]
	desc.add_theme_font_override("font", ThemeConstants.font_serif_light)
	desc.add_theme_font_size_override("font_size", 22)
	desc.add_theme_color_override("font_color", ThemeConstants.SECONDARY)
	desc.autowrap_mode = TextServer.AUTOWRAP_WORD
	col.add_child(desc)

	var chronicle_label := Label.new()
	chronicle_label.text = "SAMPLE CHRONICLE"
	chronicle_label.uppercase = true
	chronicle_label.add_theme_font_override("font", ThemeConstants.font_mono_regular)
	chronicle_label.add_theme_font_size_override("font_size", ThemeConstants.SECTION_LABEL_SIZE)
	chronicle_label.add_theme_color_override("font_color", ThemeConstants.TERTIARY)
	col.add_child(chronicle_label)

	var chronicle_card = load("res://theme/components/tm_card.tscn").instantiate()
	col.add_child(chronicle_card)
	var cc = chronicle_card.get_content_container()

	var chronicle_text := Label.new()
	chronicle_text.text = _era["sample_chronicle_text"]
	chronicle_text.add_theme_font_override("font", ThemeConstants.font_serif_light)
	chronicle_text.add_theme_font_size_override("font_size", 21)
	chronicle_text.add_theme_color_override("font_color", ThemeConstants.SECONDARY)
	chronicle_text.autowrap_mode = TextServer.AUTOWRAP_WORD
	cc.add_child(chronicle_text)

	var roster_label := Label.new()
	roster_label.text = "UNIT ROSTER"
	roster_label.uppercase = true
	roster_label.add_theme_font_override("font", ThemeConstants.font_mono_regular)
	roster_label.add_theme_font_size_override("font_size", ThemeConstants.SECTION_LABEL_SIZE)
	roster_label.add_theme_color_override("font_color", ThemeConstants.TERTIARY)
	col.add_child(roster_label)

	for unit in _era["unit_roster"]:
		var row := HBoxContainer.new()
		row.add_theme_constant_override("separation", 12)
		col.add_child(row)

		var cat := Label.new()
		cat.text = unit["category"].to_upper()
		cat.add_theme_font_override("font", ThemeConstants.font_mono_regular)
		cat.add_theme_font_size_override("font_size", ThemeConstants.BODY_DATA_SMALL_SIZE)
		cat.add_theme_color_override("font_color", ThemeConstants.TERTIARY)
		cat.custom_minimum_size.x = 50
		row.add_child(cat)

		var unit_name := Label.new()
		unit_name.text = unit["display_name"]
		unit_name.add_theme_font_override("font", ThemeConstants.font_mono_regular)
		unit_name.add_theme_font_size_override("font_size", ThemeConstants.BODY_DATA_SIZE)
		unit_name.add_theme_color_override("font_color", ThemeConstants.PRIMARY)
		unit_name.custom_minimum_size.x = 120
		row.add_child(unit_name)

		var tier_badge := Label.new()
		tier_badge.text = "T%d" % unit["tier"]
		tier_badge.add_theme_font_override("font", ThemeConstants.font_mono_regular)
		tier_badge.add_theme_font_size_override("font_size", ThemeConstants.ERA_BADGE_SIZE)
		var max_unlocked: int = _era["tier_progress"]["max_tier_unlocked"]
		if unit["tier"] <= max_unlocked:
			tier_badge.add_theme_color_override("font_color", accent)
		else:
			tier_badge.add_theme_color_override("font_color", ThemeConstants.TERTIARY)
			tier_badge.modulate.a = 0.5
		row.add_child(tier_badge)

		var role := Label.new()
		role.text = unit["role_description"]
		role.add_theme_font_override("font", ThemeConstants.font_mono_regular)
		role.add_theme_font_size_override("font_size", ThemeConstants.BODY_DATA_SMALL_SIZE)
		role.add_theme_color_override("font_color", ThemeConstants.SECONDARY)
		role.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		row.add_child(role)


func _build_right_column(parent: Control, accent: Color, accent_dim: Color) -> void:
	var col := VBoxContainer.new()
	col.add_theme_constant_override("separation", 16)
	col.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	col.custom_minimum_size.x = 340
	parent.add_child(col)

	_build_tier_card(col, accent, accent_dim)
	_build_mastery_card(col, accent)
	_build_access_card(col, accent)


func _build_tier_card(parent: Control, accent: Color, accent_dim: Color) -> void:
	var card = load("res://theme/components/tm_card.tscn").instantiate()
	card.card_title = "TIER PROGRESSION"
	parent.add_child(card)
	var content = card.get_content_container()

	var tier_row := HBoxContainer.new()
	tier_row.add_theme_constant_override("separation", 8)
	content.add_child(tier_row)

	var max_unlocked: int = _era["tier_progress"]["max_tier_unlocked"]
	for i in range(1, 4):
		var slot := ColorRect.new()
		slot.custom_minimum_size = Vector2(80, 24)
		slot.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		if i <= max_unlocked:
			slot.color = accent
		else:
			slot.color = ThemeConstants.SURFACE
		tier_row.add_child(slot)

		var slot_label := Label.new()
		slot_label.text = str(i)
		slot_label.add_theme_font_override("font", ThemeConstants.font_mono_regular)
		slot_label.add_theme_font_size_override("font_size", ThemeConstants.BODY_DATA_SIZE)
		slot_label.add_theme_color_override("font_color", ThemeConstants.PRIMARY if i <= max_unlocked else ThemeConstants.TERTIARY)
		slot_label.set_anchors_preset(Control.PRESET_CENTER)
		slot.add_child(slot_label)

	if max_unlocked >= 3:
		var done := Label.new()
		done.text = "ALL TIERS UNLOCKED"
		done.add_theme_font_override("font", ThemeConstants.font_mono_regular)
		done.add_theme_font_size_override("font_size", ThemeConstants.BODY_DATA_SMALL_SIZE)
		done.add_theme_color_override("font_color", accent)
		content.add_child(done)
	else:
		var bar = load("res://theme/components/tm_progress_bar.tscn").instantiate()
		bar.value = _era["tier_progress"]["progress_to_next"]
		bar.bar_color = accent
		bar.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		content.add_child(bar)

		var skip_btn = load("res://theme/components/tm_button.tscn").instantiate()
		skip_btn.text = "Skip to Tier 3 \u2014 ~$1"
		skip_btn.style = 1
		skip_btn.pressed.connect(func(): _show_purchase_modal())
		content.add_child(skip_btn)


func _build_mastery_card(parent: Control, accent: Color) -> void:
	var card = load("res://theme/components/tm_card.tscn").instantiate()
	card.card_title = "ERA MASTERY"
	parent.add_child(card)
	var content = card.get_content_container()

	var pct := Label.new()
	pct.text = "%d%%" % int(_era["mastery_progress"] * 100)
	pct.add_theme_font_override("font", ThemeConstants.font_mono_regular)
	pct.add_theme_font_size_override("font_size", ThemeConstants.BODY_DATA_SIZE)
	pct.add_theme_color_override("font_color", ThemeConstants.PRIMARY)
	content.add_child(pct)

	var bar = load("res://theme/components/tm_progress_bar.tscn").instantiate()
	bar.value = _era["mastery_progress"]
	bar.bar_color = accent
	bar.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	content.add_child(bar)

	var hint := Label.new()
	hint.text = "Earn cosmetic rewards, achievement badges, and era-specific doctrines through sustained play."
	hint.add_theme_font_override("font", ThemeConstants.font_mono_regular)
	hint.add_theme_font_size_override("font_size", ThemeConstants.HINT_TEXT_SIZE)
	hint.add_theme_color_override("font_color", ThemeConstants.TERTIARY)
	hint.autowrap_mode = TextServer.AUTOWRAP_WORD
	content.add_child(hint)


func _build_access_card(parent: Control, _accent: Color) -> void:
	# Subscription model removed 2026-05-09 — see docs/bible_history/game_bible_1_23.md (bible_monetization.md folded into the hub 2026-05-31; hub rewritten 2026-09-10).
	# Locked eras now route to Steam DLC overlay (currently stubbed).
	var card = load("res://theme/components/tm_card.tscn").instantiate()
	card.card_title = "ACCESS"
	parent.add_child(card)
	var content = card.get_content_container()

	var msg := Label.new()
	msg.add_theme_font_override("font", ThemeConstants.font_mono_regular)
	msg.add_theme_font_size_override("font_size", ThemeConstants.BODY_DATA_SIZE)
	msg.autowrap_mode = TextServer.AUTOWRAP_WORD
	content.add_child(msg)

	if _era["is_owned"]:
		msg.text = "You own this era."
		msg.add_theme_color_override("font_color", ThemeConstants.HEALTHY)
	else:
		msg.text = "Locked. Available as DLC on Steam."
		msg.add_theme_color_override("font_color", ThemeConstants.TERTIARY)
		var buy_btn = load("res://theme/components/tm_button.tscn").instantiate()
		buy_btn.text = "View on Steam"
		buy_btn.style = 1
		buy_btn.pressed.connect(func(): _show_purchase_modal())
		content.add_child(buy_btn)


func _build_purchase_overlay() -> void:
	_purchase_overlay = ColorRect.new()
	_purchase_overlay.color = Color(0, 0, 0, 0.6)
	_purchase_overlay.set_anchors_preset(Control.PRESET_FULL_RECT)
	_purchase_overlay.visible = false
	_purchase_overlay.mouse_filter = Control.MOUSE_FILTER_STOP
	add_child(_purchase_overlay)

	var center := CenterContainer.new()
	center.set_anchors_preset(Control.PRESET_FULL_RECT)
	_purchase_overlay.add_child(center)

	var card = load("res://theme/components/tm_card.tscn").instantiate()
	card.custom_minimum_size = Vector2(450, 0)
	center.add_child(card)
	var content = card.get_content_container()

	var msg := Label.new()
	msg.text = "This will open the Steam store page for this expansion.\n(Stub \u2014 Steam integration pending.)"
	msg.add_theme_font_override("font", ThemeConstants.font_mono_regular)
	msg.add_theme_font_size_override("font_size", ThemeConstants.BODY_DATA_SIZE)
	msg.add_theme_color_override("font_color", ThemeConstants.PRIMARY)
	msg.autowrap_mode = TextServer.AUTOWRAP_WORD
	content.add_child(msg)

	var dismiss = load("res://theme/components/tm_button.tscn").instantiate()
	dismiss.text = "DISMISS"
	dismiss.style = 1
	dismiss.pressed.connect(func(): _purchase_overlay.visible = false)
	content.add_child(dismiss)


func _show_purchase_modal() -> void:
	UIDataBus.initiate_purchase(_era_id, "dlc")
	_purchase_overlay.visible = true


func qa_state() -> Dictionary:
	return {
		"scene": "era_detail",
		"tick": -1,
		"era_id": _era_id,
		"is_owned": bool(_era.get("is_owned", false)),
		"purchase_overlay_visible": _purchase_overlay != null and is_instance_valid(_purchase_overlay) and _purchase_overlay.visible,
		"plants": [],
	}
