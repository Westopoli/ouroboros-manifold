extends Control

var _selected_era_id: String = ""
var _selected_template_id: String = ""
var _era_cards: Array[Control] = []
var _template_cards: Array[Control] = []
var _template_container: VBoxContainer
var _name_input: LineEdit
var _begin_btn: Button
var _template_section: Control

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
	header.text = "NEW GAME"
	header.uppercase = true
	header.add_theme_font_override("font", ThemeConstants.font_mono_regular)
	header.add_theme_font_size_override("font_size", ThemeConstants.CLASSIFICATION_LABEL_SIZE)
	header.add_theme_color_override("font_color", ThemeConstants.TERTIARY)
	outer.add_child(header)

	var divider = load("res://theme/components/tm_divider.tscn").instantiate()
	outer.add_child(divider)

	var columns := HBoxContainer.new()
	columns.add_theme_constant_override("separation", 40)
	columns.size_flags_vertical = Control.SIZE_EXPAND_FILL
	outer.add_child(columns)

	_build_era_column(columns)
	_build_template_column(columns)

	var name_row := HBoxContainer.new()
	name_row.add_theme_constant_override("separation", 12)
	outer.add_child(name_row)

	var name_label := Label.new()
	name_label.text = "Campaign name:"
	name_label.add_theme_font_override("font", ThemeConstants.font_mono_regular)
	name_label.add_theme_font_size_override("font_size", ThemeConstants.BODY_DATA_SIZE)
	name_label.add_theme_color_override("font_color", ThemeConstants.SECONDARY)
	name_row.add_child(name_label)

	_name_input = LineEdit.new()
	_name_input.placeholder_text = "Name this campaign..."
	_name_input.add_theme_font_override("font", ThemeConstants.font_mono_regular)
	_name_input.add_theme_font_size_override("font_size", ThemeConstants.BODY_DATA_SIZE)
	_name_input.add_theme_color_override("font_color", ThemeConstants.PRIMARY)
	_name_input.add_theme_color_override("font_placeholder_color", ThemeConstants.TERTIARY)
	_name_input.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_name_input.text_changed.connect(func(new_text: String):
		_name_input.text = InputSanitizer.sanitize(new_text, "save_name")
		_name_input.caret_column = _name_input.text.length()
	)
	name_row.add_child(_name_input)

	var footer := HBoxContainer.new()
	footer.add_theme_constant_override("separation", 12)
	outer.add_child(footer)

	_begin_btn = load("res://theme/components/tm_button.tscn").instantiate()
	_begin_btn.text = "BEGIN"
	_begin_btn.disabled = true
	_begin_btn.pressed.connect(_on_begin)
	footer.add_child(_begin_btn)

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


func _build_era_column(parent: Control) -> void:
	var col := VBoxContainer.new()
	col.add_theme_constant_override("separation", 12)
	col.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	parent.add_child(col)

	var section := Label.new()
	section.text = "SELECT ERA"
	section.uppercase = true
	section.add_theme_font_override("font", ThemeConstants.font_mono_regular)
	section.add_theme_font_size_override("font_size", ThemeConstants.SECTION_LABEL_SIZE)
	section.add_theme_color_override("font_color", ThemeConstants.TERTIARY)
	col.add_child(section)

	var scroll := ScrollContainer.new()
	scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
	col.add_child(scroll)

	var list := VBoxContainer.new()
	list.add_theme_constant_override("separation", 8)
	list.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	scroll.add_child(list)

	var eras := UIDataBus.get_all_eras()
	for era in eras:
		var accessible := UIDataBus.is_era_accessible(era["id"])
		var card = load("res://theme/components/tm_card.tscn").instantiate()
		list.add_child(card)
		var content = card.get_content_container()

		var name_label := Label.new()
		name_label.text = era["name"]
		name_label.add_theme_font_override("font", ThemeConstants.font_serif_regular)
		name_label.add_theme_font_size_override("font_size", 24)
		name_label.add_theme_color_override("font_color", Color(era["accent_color"]))
		content.add_child(name_label)

		var desc := Label.new()
		desc.text = era["description"].left(80) + "..."
		desc.add_theme_font_override("font", ThemeConstants.font_mono_regular)
		desc.add_theme_font_size_override("font_size", ThemeConstants.BODY_DATA_SIZE)
		desc.add_theme_color_override("font_color", ThemeConstants.SECONDARY)
		desc.autowrap_mode = TextServer.AUTOWRAP_WORD
		content.add_child(desc)

		var badge := Label.new()
		badge.add_theme_font_override("font", ThemeConstants.font_mono_regular)
		badge.add_theme_font_size_override("font_size", ThemeConstants.ERA_BADGE_SIZE)
		if era["is_free"]:
			badge.text = "FREE"
			badge.add_theme_color_override("font_color", ThemeConstants.HEALTHY)
		elif era["is_trial"]:
			badge.text = "TRIAL \u2014 %d MISSIONS LEFT" % era["trial_missions_remaining"]
			badge.add_theme_color_override("font_color", Color(era["accent_color"]))
		elif era["is_owned"]:
			badge.text = "OWNED"
			badge.add_theme_color_override("font_color", Color(era["accent_color"]))
		elif era["subscription_required"]:
			badge.text = "SUBSCRIPTION REQUIRED"
			badge.add_theme_color_override("font_color", ThemeConstants.TERTIARY)
		content.add_child(badge)

		if not accessible:
			card.modulate.a = 0.4
			var lock_hint := Label.new()
			lock_hint.text = "Visit Era Library to unlock"
			lock_hint.add_theme_font_override("font", ThemeConstants.font_mono_regular)
			lock_hint.add_theme_font_size_override("font_size", ThemeConstants.HINT_TEXT_SIZE)
			lock_hint.add_theme_color_override("font_color", ThemeConstants.TERTIARY)
			content.add_child(lock_hint)
		else:
			card.mouse_filter = Control.MOUSE_FILTER_STOP
			var era_id: String = era["id"]
			card.gui_input.connect(func(event: InputEvent):
				if event is InputEventMouseButton and event.pressed and event.button_index == MOUSE_BUTTON_LEFT:
					_select_era(era_id)
			)

		_era_cards.append(card)


func _build_template_column(parent: Control) -> void:
	_template_section = VBoxContainer.new()
	_template_section.add_theme_constant_override("separation", 12)
	_template_section.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_template_section.modulate.a = 0.3
	parent.add_child(_template_section)

	var section := Label.new()
	section.text = "SELECT STARTING TEMPLATE"
	section.uppercase = true
	section.add_theme_font_override("font", ThemeConstants.font_mono_regular)
	section.add_theme_font_size_override("font_size", ThemeConstants.SECTION_LABEL_SIZE)
	section.add_theme_color_override("font_color", ThemeConstants.TERTIARY)
	_template_section.add_child(section)

	_template_container = VBoxContainer.new()
	_template_container.add_theme_constant_override("separation", 8)
	_template_section.add_child(_template_container)

	var templates := UIDataBus.get_starting_templates()
	for tmpl in templates:
		var card = load("res://theme/components/tm_card.tscn").instantiate()
		_template_container.add_child(card)
		var content = card.get_content_container()

		var name_label := Label.new()
		name_label.text = tmpl["name"]
		name_label.add_theme_font_override("font", ThemeConstants.font_mono_regular)
		name_label.add_theme_font_size_override("font_size", 21)
		name_label.add_theme_color_override("font_color", ThemeConstants.PRIMARY)
		content.add_child(name_label)

		var desc := Label.new()
		desc.text = tmpl["description"]
		desc.add_theme_font_override("font", ThemeConstants.font_serif_regular)
		desc.add_theme_font_size_override("font_size", ThemeConstants.BODY_DATA_SIZE)
		desc.add_theme_color_override("font_color", ThemeConstants.SECONDARY)
		desc.autowrap_mode = TextServer.AUTOWRAP_WORD
		content.add_child(desc)

		var diagram := Label.new()
		diagram.text = tmpl["ascii_diagram"]
		diagram.add_theme_font_override("font", ThemeConstants.font_mono_regular)
		diagram.add_theme_font_size_override("font_size", ThemeConstants.BODY_DATA_SMALL_SIZE)
		diagram.add_theme_color_override("font_color", ThemeConstants.TERTIARY)
		content.add_child(diagram)

		card.mouse_filter = Control.MOUSE_FILTER_STOP
		var tmpl_id: String = tmpl["id"]
		card.gui_input.connect(func(event: InputEvent):
			if event is InputEventMouseButton and event.pressed and event.button_index == MOUSE_BUTTON_LEFT:
				_select_template(tmpl_id)
		)
		_template_cards.append(card)


func _select_era(era_id: String) -> void:
	_selected_era_id = era_id
	var accent := ThemeConstants.get_era_accent(era_id)
	var eras := UIDataBus.get_all_eras()

	for i in range(_era_cards.size()):
		var card: PanelContainer = _era_cards[i]
		var style: StyleBoxFlat = card.get_theme_stylebox("panel").duplicate()
		if eras[i]["id"] == era_id:
			style.border_color = accent
			style.set_border_width_all(2)
		else:
			style.border_color = ThemeConstants.BORDER_COLOR
			style.set_border_width_all(1)
		card.add_theme_stylebox_override("panel", style)

	_template_section.modulate.a = 1.0
	_begin_btn.accent_color = accent

	var era := UIDataBus.get_era_detail(era_id)
	var era_name: String = era.get("name", era_id)
	if _selected_template_id != "":
		var templates := UIDataBus.get_starting_templates()
		for t in templates:
			if t["id"] == _selected_template_id:
				_name_input.placeholder_text = "%s \u2014 %s" % [era_name, t["name"]]
				break
	else:
		_name_input.placeholder_text = "Name this campaign..."

	_update_begin_state()


func _select_template(template_id: String) -> void:
	_selected_template_id = template_id
	var accent := ThemeConstants.get_era_accent(_selected_era_id) if _selected_era_id != "" else ThemeConstants.DEFAULT_ACCENT
	var templates := UIDataBus.get_starting_templates()

	for i in range(_template_cards.size()):
		var card: PanelContainer = _template_cards[i]
		var style: StyleBoxFlat = card.get_theme_stylebox("panel").duplicate()
		if templates[i]["id"] == template_id:
			style.border_color = accent
			style.set_border_width_all(2)
		else:
			style.border_color = ThemeConstants.BORDER_COLOR
			style.set_border_width_all(1)
		card.add_theme_stylebox_override("panel", style)

	if _selected_era_id != "":
		var era := UIDataBus.get_era_detail(_selected_era_id)
		for t in templates:
			if t["id"] == template_id:
				_name_input.placeholder_text = "%s \u2014 %s" % [era.get("name", _selected_era_id), t["name"]]
				break

	_update_begin_state()


func _update_begin_state() -> void:
	_begin_btn.disabled = _selected_era_id == "" or _selected_template_id == ""


func _on_begin() -> void:
	var slot_name := _name_input.text
	if slot_name.strip_edges() == "":
		slot_name = _name_input.placeholder_text
	UIDataBus.create_save_slot(_selected_era_id, _selected_template_id, slot_name)
	SceneRouter.go_to("onboarding", {"era_id": _selected_era_id, "template_id": _selected_template_id, "slot_name": slot_name})
