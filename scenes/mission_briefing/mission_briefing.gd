extends Control

const SimSession := preload("res://autoload/sim_session.gd")
const BetaMode := preload("res://autoload/beta_mode.gd")

# C transport v1 rebind (piece C4, leaf-01; A4-client). load_frame()/qa_state()/
# qa_plant() consume a mission frame (docs/architecture.md "chronicle frame,
# mission frame, debrief frame"). The frame carries no names (C5 rule): a
# marker name is the mission region's own name through chronicle_names.gd (A82,
# the name the sim chronicle uses), never echoed from the frame's "node" field. "parity" is data, never rendered.
const _FRAGMENTS_PATH := "res://library/chronicle/fragments.json"
const _UNIT_NAMES := ["Raider", "Interceptor", "Vanguard", "Warden", "Bombard", "Bastion"]

var _names = null
var _frame_briefing: Dictionary = {}
var _frame_archetype: int = 0
var _frame_region: int = 0
var _frame_deadline_ticks: int = 0
var _frame_objectives: Array = []
var _frame_force: Dictionary = {}
var _plant_marker_from_frame: bool = false
var _frame_loaded: bool = false
var _deploy_btn: BaseButton = null
var _deploy_error_label: Label = null
var _variant_picker: OptionButton = null  # H-060: beta only, B2 fills it
var _plant_begin_refused: bool = false
var _error_panel: Control

var _data: Dictionary = {}
var _accent: Color
var _accent_dim: Color
var _accent_border: Color

func setup(params: Dictionary) -> void:
	var mission_id: String = params.get("mission_id", "mock_001")
	_data = UIDataBus.get_mission_briefing(mission_id)
	_accent = ThemeConstants.get_era_accent(_data.get("era_id", "roman"))
	_accent_dim = ThemeConstants.get_era_accent_dim(_data.get("era_id", "roman"))
	_accent_border = ThemeConstants.get_era_accent_border(_data.get("era_id", "roman"))


func _ready() -> void:
	if _data.is_empty():
		_data = UIDataBus.get_mission_briefing("mock_001")
		_accent = ThemeConstants.get_era_accent(_data.get("era_id", "roman"))
		_accent_dim = ThemeConstants.get_era_accent_dim(_data.get("era_id", "roman"))
		_accent_border = ThemeConstants.get_era_accent_border(_data.get("era_id", "roman"))
		# C8 flow spine: self-load the live mission frame on a fresh route-in.
		# A failed live load shows the shared error panel and builds no UI;
		# it never falls back to a fixture frame (C4-3, G2).
		_load_live()
		return
	_build_ui()


func _load_live() -> void:
	var bridge = SimSession.bridge()
	if bridge.load_mission_live(bridge.live_seed(), bridge.DEFAULT_N_REGIONS, bridge.DEFAULT_FEATURES, _fog_filter()):
		if _error_panel != null:
			_error_panel.hide_error()
		load_frame(bridge.mission_frame())
		return
	var reason: String = bridge.last_error()
	push_error("mission_briefing: live mission frame failed: %s" % reason)
	if _error_panel == null:
		_error_panel = load("res://scenes/shared/error_panel.tscn").instantiate()
		_error_panel.retry_pressed.connect(_load_live)
		add_child(_error_panel)
	_error_panel.show_error(reason if reason != "" else "briefing load failed")


# The QA daemon can turn the fog filter off for probes that need enemy positions; the game default is on (R-089-03).
func _fog_filter() -> bool:
	var qa = get_node_or_null("/root/QADaemon")
	return qa == null or not qa.has_method("fog_filter") or qa.fog_filter()


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
	margin.add_theme_constant_override("margin_top", 50)
	margin.add_theme_constant_override("margin_bottom", 50)
	add_child(margin)

	var outer := VBoxContainer.new()
	outer.add_theme_constant_override("separation", 16)
	margin.add_child(outer)

	_build_header(outer)

	var divider = load("res://theme/components/tm_divider.tscn").instantiate()
	outer.add_child(divider)

	var columns := HBoxContainer.new()
	columns.add_theme_constant_override("separation", 40)
	columns.size_flags_vertical = Control.SIZE_EXPAND_FILL
	outer.add_child(columns)

	_build_left_column(columns)
	_build_right_column(columns)

	_build_footer(outer)

	_animate_entrance()


func _build_header(parent: Control) -> void:
	var header := VBoxContainer.new()
	header.add_theme_constant_override("separation", 4)
	parent.add_child(header)

	var top_row := HBoxContainer.new()
	top_row.add_theme_constant_override("separation", 12)
	header.add_child(top_row)

	var left_col := VBoxContainer.new()
	left_col.add_theme_constant_override("separation", 2)
	left_col.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	top_row.add_child(left_col)

	var classification := Label.new()
	classification.text = "MISSION BRIEFING"
	classification.uppercase = true
	classification.add_theme_font_override("font", ThemeConstants.font_mono_regular)
	classification.add_theme_font_size_override("font_size", ThemeConstants.CLASSIFICATION_LABEL_SIZE)
	classification.add_theme_color_override("font_color", _accent)
	left_col.add_child(classification)

	var meta := Label.new()
	meta.text = "%s // Chapter %d // Generation %d" % [
		_data.get("mission_id_label", ""),
		_data.get("chapter", 0),
		_data.get("generation", 0)
	]
	meta.add_theme_font_override("font", ThemeConstants.font_mono_regular)
	meta.add_theme_font_size_override("font_size", ThemeConstants.CLASSIFICATION_LABEL_SIZE)
	meta.add_theme_color_override("font_color", ThemeConstants.TERTIARY)
	left_col.add_child(meta)

	var spacer := Control.new()
	spacer.custom_minimum_size.y = 4
	left_col.add_child(spacer)

	var title := Label.new()
	title.text = _data.get("mission_title", "")
	title.add_theme_font_override("font", ThemeConstants.font_serif_regular)
	title.add_theme_font_size_override("font_size", ThemeConstants.TITLE_SIZE)
	title.add_theme_color_override("font_color", ThemeConstants.PRIMARY)
	left_col.add_child(title)

	var subtitle := Label.new()
	subtitle.text = _data.get("mission_subtitle", "")
	subtitle.add_theme_font_override("font", ThemeConstants.font_serif_italic)
	subtitle.add_theme_font_size_override("font_size", ThemeConstants.SUBTITLE_SIZE)
	subtitle.add_theme_color_override("font_color", ThemeConstants.SECONDARY)
	left_col.add_child(subtitle)

	var right_col := VBoxContainer.new()
	right_col.add_theme_constant_override("separation", 6)
	top_row.add_child(right_col)

	var era_badge := _create_era_badge()
	right_col.add_child(era_badge)

	var tick_row := HBoxContainer.new()
	tick_row.add_theme_constant_override("separation", 4)
	right_col.add_child(tick_row)

	var tick_label := Label.new()
	tick_label.text = "TICK %d" % _data.get("tick_counter", 0)
	tick_label.add_theme_font_override("font", ThemeConstants.font_mono_regular)
	tick_label.add_theme_font_size_override("font_size", ThemeConstants.CLASSIFICATION_LABEL_SIZE)
	tick_label.add_theme_color_override("font_color", ThemeConstants.TERTIARY)
	tick_row.add_child(tick_label)

	var cursor = load("res://theme/components/tm_blinking_cursor.tscn").instantiate()
	cursor.cursor_color = _accent
	tick_row.add_child(cursor)


func _create_era_badge() -> PanelContainer:
	var panel := PanelContainer.new()
	var style := StyleBoxFlat.new()
	style.bg_color = _accent_dim
	style.border_color = _accent_border
	style.set_border_width_all(1)
	style.set_corner_radius_all(3)
	style.content_margin_left = 8
	style.content_margin_right = 8
	style.content_margin_top = 3
	style.content_margin_bottom = 3
	panel.add_theme_stylebox_override("panel", style)

	var era_id: String = _data.get("era_id", "")
	var badge_label := Label.new()
	badge_label.text = "%s ERA" % era_id.to_upper()
	badge_label.add_theme_font_override("font", ThemeConstants.font_mono_regular)
	badge_label.add_theme_font_size_override("font_size", ThemeConstants.ERA_BADGE_SIZE)
	badge_label.add_theme_color_override("font_color", _accent)
	panel.add_child(badge_label)

	return panel


func _build_left_column(parent: Control) -> void:
	var col := VBoxContainer.new()
	col.add_theme_constant_override("separation", 16)
	col.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	col.size_flags_stretch_ratio = 1.2
	parent.add_child(col)

	var scroll := ScrollContainer.new()
	scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
	scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	col.add_child(scroll)

	var inner := VBoxContainer.new()
	inner.add_theme_constant_override("separation", 20)
	inner.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	scroll.add_child(inner)

	var intel_label := Label.new()
	intel_label.text = "INTELLIGENCE REPORT"
	intel_label.uppercase = true
	intel_label.add_theme_font_override("font", ThemeConstants.font_mono_regular)
	intel_label.add_theme_font_size_override("font_size", ThemeConstants.SECTION_LABEL_SIZE)
	intel_label.add_theme_color_override("font_color", ThemeConstants.TERTIARY)
	inner.add_child(intel_label)

	var briefing := RichTextLabel.new()
	briefing.bbcode_enabled = true
	briefing.fit_content = true
	briefing.scroll_active = false
	briefing.text = _format_briefing_text(_data.get("situation_text", ""))
	briefing.add_theme_font_override("normal_font", ThemeConstants.font_serif_light)
	briefing.add_theme_font_override("bold_font", ThemeConstants.font_serif_regular)
	briefing.add_theme_font_size_override("normal_font_size", ThemeConstants.BODY_NARRATIVE_SIZE)
	briefing.add_theme_font_size_override("bold_font_size", ThemeConstants.BODY_NARRATIVE_SIZE)
	briefing.add_theme_color_override("default_color", ThemeConstants.SECONDARY)
	inner.add_child(briefing)

	var short_objective_header := RichTextLabel.new()
	short_objective_header.name = "short_objective_header"
	short_objective_header.bbcode_enabled = true
	short_objective_header.fit_content = true
	short_objective_header.scroll_active = false
	short_objective_header.add_theme_color_override("default_color", _accent)
	var header_font_size := int(ThemeConstants.BODY_NARRATIVE_SIZE * 1.6)
	short_objective_header.add_theme_font_size_override("normal_font_size", header_font_size)
	short_objective_header.add_theme_font_size_override("bold_font_size", header_font_size)
	var objective_text: String = _data.get("objective", "")
	if objective_text == "":
		short_objective_header.visible = false
	else:
		var accent_hex := "#" + _accent.to_html(false)
		short_objective_header.text = "[color=%s][b]%s[/b][/color]" % [accent_hex, objective_text.to_upper()]
	inner.add_child(short_objective_header)

	var obj_label := Label.new()
	obj_label.text = "MISSION OBJECTIVES"
	obj_label.uppercase = true
	obj_label.add_theme_font_override("font", ThemeConstants.font_mono_regular)
	obj_label.add_theme_font_size_override("font_size", ThemeConstants.SECTION_LABEL_SIZE)
	obj_label.add_theme_color_override("font_color", ThemeConstants.TERTIARY)
	inner.add_child(obj_label)

	var primary_obj: Dictionary = _data.get("objective_primary", {})
	var obj_card := _create_objective_card(primary_obj, true)
	inner.add_child(obj_card)

	var secondary_objs: Array = _data.get("objectives_secondary", [])
	for obj in secondary_objs:
		var sec_card := _create_objective_card(obj, false)
		inner.add_child(sec_card)


func _format_briefing_text(raw: String) -> String:
	var text := raw
	var accent_hex := "#" + _accent.to_html(false)
	var primary_hex := "#" + ThemeConstants.PRIMARY.to_html(false)
	text = text.replace("{accent}", "[color=%s][b]" % accent_hex)
	text = text.replace("{/accent}", "[/b][/color]")
	text = text.replace("{strong}", "[color=%s][b]" % primary_hex)
	text = text.replace("{/strong}", "[/b][/color]")
	return text


func _create_objective_card(obj: Dictionary, is_primary: bool) -> PanelContainer:
	var panel := PanelContainer.new()
	var style := StyleBoxFlat.new()
	style.bg_color = ThemeConstants.CARD
	style.border_color = Color.TRANSPARENT
	style.border_width_left = 3
	style.border_color = _accent if is_primary else ThemeConstants.SECONDARY
	style.set_corner_radius_all(0)
	style.corner_radius_top_right = ThemeConstants.BORDER_RADIUS
	style.corner_radius_bottom_right = ThemeConstants.BORDER_RADIUS
	style.content_margin_left = 16
	style.content_margin_right = 16
	style.content_margin_top = 12
	style.content_margin_bottom = 12
	panel.add_theme_stylebox_override("panel", style)

	var vbox := VBoxContainer.new()
	vbox.add_theme_constant_override("separation", 4)
	panel.add_child(vbox)

	var obj_text := Label.new()
	obj_text.text = obj.get("text", "")
	obj_text.add_theme_font_override("font", ThemeConstants.font_mono_regular)
	obj_text.add_theme_font_size_override("font_size", ThemeConstants.BODY_DATA_SIZE)
	obj_text.add_theme_color_override("font_color", ThemeConstants.PRIMARY)
	obj_text.autowrap_mode = TextServer.AUTOWRAP_WORD
	vbox.add_child(obj_text)

	var detail_text: String = obj.get("detail", "") if is_primary else ""
	var detail_label: Label = null
	if is_primary and detail_text != "":
		detail_label = Label.new()
		detail_label.text = detail_text
		detail_label.add_theme_font_override("font", ThemeConstants.font_serif_light_italic)
		detail_label.add_theme_font_size_override("font_size", ThemeConstants.BODY_DATA_SMALL_SIZE)
		detail_label.add_theme_color_override("font_color", ThemeConstants.SECONDARY)
		detail_label.autowrap_mode = TextServer.AUTOWRAP_WORD
		detail_label.visible = false
		vbox.add_child(detail_label)

	var meta_parts: Array[String] = []
	if obj.has("archetype"):
		meta_parts.append(obj["archetype"])
	if obj.has("success_spectrum_label"):
		meta_parts.append(obj["success_spectrum_label"])
	if obj.has("weight_label"):
		meta_parts.append(obj["weight_label"])

	var meta_row: HBoxContainer = null
	if meta_parts.size() > 0 or detail_label != null:
		meta_row = HBoxContainer.new()
		meta_row.add_theme_constant_override("separation", 8)
		vbox.add_child(meta_row)

		if meta_parts.size() > 0:
			var meta_label := Label.new()
			meta_label.text = " // ".join(meta_parts)
			meta_label.add_theme_font_override("font", ThemeConstants.font_mono_regular)
			meta_label.add_theme_font_size_override("font_size", ThemeConstants.BODY_DATA_SMALL_SIZE)
			meta_label.add_theme_color_override("font_color", ThemeConstants.TERTIARY)
			meta_label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
			meta_row.add_child(meta_label)
		else:
			var spacer := Control.new()
			spacer.size_flags_horizontal = Control.SIZE_EXPAND_FILL
			meta_row.add_child(spacer)

		if detail_label != null:
			var toggle_btn := Button.new()
			toggle_btn.text = "[+]"
			toggle_btn.flat = true
			toggle_btn.focus_mode = Control.FOCUS_NONE
			toggle_btn.add_theme_font_override("font", ThemeConstants.font_mono_regular)
			toggle_btn.add_theme_font_size_override("font_size", ThemeConstants.BODY_DATA_SMALL_SIZE)
			toggle_btn.add_theme_color_override("font_color", _accent)
			toggle_btn.add_theme_color_override("font_hover_color", ThemeConstants.PRIMARY)
			toggle_btn.add_theme_color_override("font_pressed_color", ThemeConstants.PRIMARY)
			toggle_btn.pressed.connect(func():
				detail_label.visible = not detail_label.visible
				toggle_btn.text = "[-]" if detail_label.visible else "[+]"
			)
			meta_row.add_child(toggle_btn)

	return panel


func _build_right_column(parent: Control) -> void:
	var col := VBoxContainer.new()
	col.add_theme_constant_override("separation", 12)
	col.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	parent.add_child(col)

	var scroll := ScrollContainer.new()
	scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
	scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	col.add_child(scroll)

	var inner := VBoxContainer.new()
	inner.add_theme_constant_override("separation", 12)
	inner.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	scroll.add_child(inner)

	_build_enemy_card(inner)
	_build_force_card(inner)
	_build_region_card(inner)
	_build_lineage_card(inner)


func _build_enemy_card(parent: Control) -> void:
	var enemy: Dictionary = _data.get("enemy_assessment", {})
	var card = load("res://theme/components/tm_card.tscn").instantiate()
	card.card_title = "ENEMY ASSESSMENT"
	card.show_title = true
	parent.add_child(card)
	var content = card.get_content_container()

	var faction := Label.new()
	faction.text = enemy.get("faction_name", "")
	faction.add_theme_font_override("font", ThemeConstants.font_mono_regular)
	faction.add_theme_font_size_override("font_size", ThemeConstants.BODY_DATA_SIZE)
	faction.add_theme_color_override("font_color", _accent)
	content.add_child(faction)

	var archetype := Label.new()
	archetype.text = enemy.get("archetype_label", "")
	archetype.add_theme_font_override("font", ThemeConstants.font_mono_regular)
	archetype.add_theme_font_size_override("font_size", ThemeConstants.BODY_DATA_SMALL_SIZE)
	archetype.add_theme_color_override("font_color", ThemeConstants.SECONDARY)
	content.add_child(archetype)

	var mil_bar = load("res://theme/components/tm_progress_bar.tscn").instantiate()
	mil_bar.label_text = "MILITARY"
	mil_bar.show_label = true
	mil_bar.show_value = true
	var mil_stat: float = enemy.get("military_stat", 0)
	var mil_max: float = enemy.get("military_stat_max", 100)
	mil_bar.value = mil_stat / mil_max
	mil_bar.max_display_value = mil_max
	mil_bar.bar_color = ThemeConstants.DANGER if mil_stat / mil_max > 0.6 else _accent
	content.add_child(mil_bar)

	var tech := Label.new()
	tech.text = "TECH TIER %d" % enemy.get("tech_tier", 0)
	tech.add_theme_font_override("font", ThemeConstants.font_mono_regular)
	tech.add_theme_font_size_override("font_size", ThemeConstants.BODY_DATA_SMALL_SIZE)
	tech.add_theme_color_override("font_color", ThemeConstants.TERTIARY)
	content.add_child(tech)

	var behavior_tag: String = enemy.get("behavior_tag", "")
	if behavior_tag != "":
		var tag_panel := PanelContainer.new()
		var tag_style := StyleBoxFlat.new()
		var info_dim := Color(ThemeConstants.INFO.r, ThemeConstants.INFO.g, ThemeConstants.INFO.b, 0.15)
		var info_border := Color(ThemeConstants.INFO.r, ThemeConstants.INFO.g, ThemeConstants.INFO.b, 0.30)
		tag_style.bg_color = info_dim
		tag_style.border_color = info_border
		tag_style.set_border_width_all(1)
		tag_style.set_corner_radius_all(3)
		tag_style.content_margin_left = 8
		tag_style.content_margin_right = 8
		tag_style.content_margin_top = 3
		tag_style.content_margin_bottom = 3
		tag_panel.add_theme_stylebox_override("panel", tag_style)

		var tag_label := Label.new()
		tag_label.text = behavior_tag
		tag_label.add_theme_font_override("font", ThemeConstants.font_mono_regular)
		tag_label.add_theme_font_size_override("font_size", ThemeConstants.ERA_BADGE_SIZE)
		tag_label.add_theme_color_override("font_color", ThemeConstants.INFO)
		tag_panel.add_child(tag_label)
		content.add_child(tag_panel)


func _build_force_card(parent: Control) -> void:
	var force: Dictionary = _data.get("player_force", {})
	var card = load("res://theme/components/tm_card.tscn").instantiate()
	card.card_title = "YOUR FORCE"
	card.show_title = true
	parent.add_child(card)
	var content = card.get_content_container()

	if force.has("parity_percentage"):
		var parity_bar = load("res://theme/components/tm_progress_bar.tscn").instantiate()
		parity_bar.label_text = "FORCE PARITY"
		parity_bar.show_label = true
		parity_bar.show_value = true
		parity_bar.value = force.get("parity_percentage", 0) / 100.0
		parity_bar.max_display_value = 100.0
		parity_bar.bar_color = ThemeConstants.INFO
		content.add_child(parity_bar)

		var spacer := Control.new()
		spacer.custom_minimum_size.y = 4
		content.add_child(spacer)

	var units: Array = force.get("units", [])
	for unit in units:
		var row := HBoxContainer.new()
		row.add_theme_constant_override("separation", 10)
		content.add_child(row)

		var dot := ColorRect.new()
		dot.custom_minimum_size = Vector2(6, 6)
		dot.color = _accent
		dot.size_flags_vertical = Control.SIZE_SHRINK_CENTER
		row.add_child(dot)

		var unit_name := Label.new()
		unit_name.text = "%s \u00d7%d" % [unit.get("type_display_name", ""), unit.get("count", 0)]
		unit_name.add_theme_font_override("font", ThemeConstants.font_mono_regular)
		unit_name.add_theme_font_size_override("font_size", ThemeConstants.BODY_DATA_SIZE)
		unit_name.add_theme_color_override("font_color", ThemeConstants.PRIMARY)
		unit_name.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		row.add_child(unit_name)

		var cat_label := Label.new()
		cat_label.text = unit.get("category", "").to_upper()
		cat_label.add_theme_font_override("font", ThemeConstants.font_mono_regular)
		cat_label.add_theme_font_size_override("font_size", ThemeConstants.BODY_DATA_SMALL_SIZE)
		cat_label.add_theme_color_override("font_color", ThemeConstants.TERTIARY)
		row.add_child(cat_label)


func _build_region_card(parent: Control) -> void:
	var region: Dictionary = _data.get("region_state", {})
	var card = load("res://theme/components/tm_card.tscn").instantiate()
	card.card_title = "REGION STATE"
	card.show_title = true
	parent.add_child(card)
	var content = card.get_content_container()

	var name_row := HBoxContainer.new()
	name_row.add_theme_constant_override("separation", 12)
	content.add_child(name_row)

	var region_name := Label.new()
	region_name.text = region.get("name", "")
	region_name.add_theme_font_override("font", ThemeConstants.font_mono_regular)
	region_name.add_theme_font_size_override("font_size", ThemeConstants.BODY_DATA_SIZE)
	region_name.add_theme_color_override("font_color", ThemeConstants.PRIMARY)
	name_row.add_child(region_name)

	var tier_label := Label.new()
	tier_label.text = region.get("tier", "")
	tier_label.add_theme_font_override("font", ThemeConstants.font_mono_regular)
	tier_label.add_theme_font_size_override("font_size", ThemeConstants.BODY_DATA_SMALL_SIZE)
	tier_label.add_theme_color_override("font_color", ThemeConstants.TERTIARY)
	name_row.add_child(tier_label)

	var econ: Dictionary = region.get("economy", {})
	var econ_bar = load("res://theme/components/tm_progress_bar.tscn").instantiate()
	econ_bar.label_text = "ECONOMY"
	econ_bar.show_label = true
	econ_bar.show_value = true
	econ_bar.value = econ.get("value", 0) / float(econ.get("max", 100))
	econ_bar.max_display_value = float(econ.get("max", 100))
	econ_bar.bar_color = ThemeConstants.HEALTHY
	content.add_child(econ_bar)

	var mil: Dictionary = region.get("military", {})
	var mil_bar = load("res://theme/components/tm_progress_bar.tscn").instantiate()
	mil_bar.label_text = "MILITARY"
	mil_bar.show_label = true
	mil_bar.show_value = true
	var mil_ratio: float = mil.get("value", 0) / float(mil.get("max", 100))
	mil_bar.value = mil_ratio
	mil_bar.max_display_value = float(mil.get("max", 100))
	mil_bar.bar_color = ThemeConstants.DANGER if mil_ratio < 0.4 else _accent
	content.add_child(mil_bar)

	var tens: Dictionary = region.get("tension", {})
	var tens_bar = load("res://theme/components/tm_progress_bar.tscn").instantiate()
	tens_bar.label_text = "TENSION"
	tens_bar.show_label = true
	tens_bar.show_value = true
	var tens_ratio: float = tens.get("value", 0) / float(tens.get("max", 100))
	tens_bar.value = tens_ratio
	tens_bar.max_display_value = float(tens.get("max", 100))
	tens_bar.bar_color = ThemeConstants.DANGER if tens_ratio > 0.6 else _accent
	content.add_child(tens_bar)

	var reinforce_note: String = _data.get("reinforcement_note", "")
	if reinforce_note != "":
		var note := Label.new()
		note.text = reinforce_note
		note.add_theme_font_override("font", ThemeConstants.font_serif_light_italic)
		note.add_theme_font_size_override("font_size", ThemeConstants.BODY_DATA_SIZE)
		note.add_theme_color_override("font_color", ThemeConstants.TERTIARY)
		note.autowrap_mode = TextServer.AUTOWRAP_WORD
		content.add_child(note)


func _build_lineage_card(parent: Control) -> void:
	var lineage: Dictionary = _data.get("commander_lineage", {})
	var card = load("res://theme/components/tm_card.tscn").instantiate()
	card.card_title = "COMMANDER LINEAGE"
	card.show_title = true
	parent.add_child(card)
	var content = card.get_content_container()

	var name_label := Label.new()
	name_label.text = lineage.get("name", "")
	name_label.add_theme_font_override("font", ThemeConstants.font_mono_regular)
	name_label.add_theme_font_size_override("font_size", ThemeConstants.BODY_DATA_SIZE)
	name_label.add_theme_color_override("font_color", _accent)
	content.add_child(name_label)

	var gen_label := Label.new()
	gen_label.text = "Generation %d" % lineage.get("generation_number", 1)
	gen_label.add_theme_font_override("font", ThemeConstants.font_mono_regular)
	gen_label.add_theme_font_size_override("font_size", ThemeConstants.BODY_DATA_SMALL_SIZE)
	gen_label.add_theme_color_override("font_color", ThemeConstants.TERTIARY)
	content.add_child(gen_label)

	var pred_name: String = lineage.get("predecessor_name", "")
	if pred_name != "":
		var pred_row := HBoxContainer.new()
		pred_row.add_theme_constant_override("separation", 8)
		content.add_child(pred_row)

		var pred_label := Label.new()
		pred_label.text = pred_name
		pred_label.add_theme_font_override("font", ThemeConstants.font_mono_regular)
		pred_label.add_theme_font_size_override("font_size", ThemeConstants.BODY_DATA_SIZE)
		pred_label.add_theme_color_override("font_color", ThemeConstants.SECONDARY)
		pred_row.add_child(pred_label)

		var dash := Label.new()
		dash.text = "\u2014"
		dash.add_theme_font_override("font", ThemeConstants.font_mono_regular)
		dash.add_theme_font_size_override("font_size", ThemeConstants.BODY_DATA_SIZE)
		dash.add_theme_color_override("font_color", ThemeConstants.TERTIARY)
		pred_row.add_child(dash)

		var status_label := Label.new()
		var status_text: String = lineage.get("predecessor_status", "")
		status_label.text = status_text
		status_label.add_theme_font_override("font", ThemeConstants.font_mono_regular)
		status_label.add_theme_font_size_override("font_size", ThemeConstants.BODY_DATA_SIZE)
		var is_kia := status_text.begins_with("KIA")
		status_label.add_theme_color_override("font_color", ThemeConstants.DANGER if is_kia else ThemeConstants.SECONDARY)
		pred_row.add_child(status_label)
	else:
		var first_line := Label.new()
		first_line.text = "First of the line."
		first_line.add_theme_font_override("font", ThemeConstants.font_serif_light_italic)
		first_line.add_theme_font_size_override("font_size", ThemeConstants.BODY_DATA_SIZE)
		first_line.add_theme_color_override("font_color", ThemeConstants.TERTIARY)
		content.add_child(first_line)


# The player's Begin (E-12 S-092): ends recon over the shared session. The
# tactical view is only routed to when the pipe accepted it. On failure,
# last_error() is surfaced in _deploy_error_label (C4-6: QA-004/005/006).
func begin_mission() -> bool:
	var bridge = SimSession.bridge()
	if not _plant_begin_refused and bridge.begin_mission_live(bridge.live_seed(), bridge.DEFAULT_N_REGIONS, bridge.DEFAULT_FEATURES):
		return true
	var err: String = "begin refused (plant)" if _plant_begin_refused else bridge.last_error()
	push_error("mission_briefing: Begin failed: %s" % err)
	if _deploy_error_label != null:
		_deploy_error_label.text = err
		_deploy_error_label.visible = true
	return false


# The player's Refuse (R-078-05): sends mission_refuse and pumps until the
# refusal debrief frame ends the mission (the bridge holds it for the debrief
# scene). The debrief is only routed to when the pipe answered; otherwise the
# reason is surfaced in _deploy_error_label.
func refuse_mission() -> bool:
	var bridge = SimSession.bridge()
	bridge.send_command({"type": "cmd", "name": "mission_refuse"})
	var deadline: int = Time.get_ticks_msec() + bridge.LIVE_READ_TIMEOUT_MSEC
	while bridge.mission_active() and bridge.last_error() == "" and Time.get_ticks_msec() < deadline:
		if bridge.pump() == 0:
			OS.delay_msec(5)
	if not bridge.mission_active():
		return true
	var err: String = bridge.last_error() if bridge.last_error() != "" else "timed out waiting for the refusal debrief"
	push_error("mission_briefing: Refuse failed: %s" % err)
	if _deploy_error_label != null:
		_deploy_error_label.text = err
		_deploy_error_label.visible = true
	return false


func _build_footer(parent: Control) -> void:
	var footer := HBoxContainer.new()
	footer.add_theme_constant_override("separation", 12)
	parent.add_child(footer)

	var deploy_btn = load("res://theme/components/tm_button.tscn").instantiate()
	deploy_btn.name = "Deploy"
	deploy_btn.text = "DEPLOY FORCES"
	deploy_btn.accent_color = _accent
	# C4-6 (QA-004/005/006): disabled until the session has an active mission in
	# recon (active but not yet begun); mission_begin is refused outside recon.
	var bridge = SimSession.bridge()
	deploy_btn.disabled = not bridge.mission_active() or bridge.mission_begun()
	_deploy_btn = deploy_btn
	deploy_btn.pressed.connect(func():
		if begin_mission():
			SceneRouter.go_to("beta_field" if BetaMode.active() else "tactical_c")
	)
	footer.add_child(deploy_btn)

	var refuse_btn = load("res://theme/components/tm_button.tscn").instantiate()
	refuse_btn.name = "Refuse"
	refuse_btn.text = "REFUSE"
	refuse_btn.style = 1
	# R-078-05: mission_refuse is valid only in recon, like Begin.
	refuse_btn.disabled = not bridge.mission_active() or bridge.mission_begun()
	refuse_btn.pressed.connect(func():
		if refuse_mission():
			SceneRouter.go_to("debrief")
	)
	footer.add_child(refuse_btn)

	var back_btn = load("res://theme/components/tm_button.tscn").instantiate()
	back_btn.text = "BACK"
	back_btn.style = 1
	back_btn.pressed.connect(func(): SceneRouter.go_back())
	footer.add_child(back_btn)

	if BetaMode.active():  # H-060 dev picker placeholder: one entry, B2 fills it
		var variant_label := Label.new()
		variant_label.text = "variant"
		footer.add_child(variant_label)
		_variant_picker = OptionButton.new()
		_variant_picker.name = "VariantPicker"
		_variant_picker.add_item("default")
		footer.add_child(_variant_picker)

	var spacer := Control.new()
	spacer.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	footer.add_child(spacer)

	var hints := Label.new()
	hints.text = "ESC to return to galaxy view // TAB for force details"
	hints.add_theme_font_override("font", ThemeConstants.font_mono_regular)
	hints.add_theme_font_size_override("font_size", ThemeConstants.HINT_TEXT_SIZE)
	hints.add_theme_color_override("font_color", ThemeConstants.TERTIARY)
	hints.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	footer.add_child(hints)

	# C4-6: error label shown on screen when mission_begin is refused (QA-006).
	var err_label := Label.new()
	err_label.name = "DeployError"
	err_label.text = ""
	err_label.visible = false
	err_label.add_theme_font_override("font", ThemeConstants.font_mono_regular)
	err_label.add_theme_font_size_override("font_size", ThemeConstants.BODY_DATA_SIZE)
	err_label.add_theme_color_override("font_color", ThemeConstants.DANGER)
	parent.add_child(err_label)
	_deploy_error_label = err_label


func _animate_entrance() -> void:
	var delay := ThemeConstants.STAGGER_BASE_DELAY

	var margin_node: MarginContainer = null
	for child in get_children():
		if child is MarginContainer:
			margin_node = child
			break
	if not margin_node:
		return

	var outer_node: VBoxContainer = null
	for child in margin_node.get_children():
		if child is VBoxContainer:
			outer_node = child
			break
	if not outer_node:
		return

	for i in range(outer_node.get_child_count()):
		var child := outer_node.get_child(i)
		child.modulate.a = 0.0
		var tw := create_tween().set_ease(Tween.EASE_OUT).set_trans(Tween.TRANS_CUBIC)
		tw.tween_interval(delay)
		tw.tween_property(child, "modulate:a", 1.0, ThemeConstants.ELEMENT_ANIM_DURATION)
		if i == 0:
			delay = 0.4
		elif i == 1:
			delay = 0.5
		else:
			delay += ThemeConstants.STAGGER_INCREMENT


func load_frame(mission: Dictionary) -> void:
	_frame_loaded = true
	_frame_archetype = int(mission.get("archetype", 0))
	_frame_region = int(mission.get("region", 0))
	_frame_deadline_ticks = int(mission.get("deadline_ticks", 0))
	_frame_objectives = (mission.get("objectives", []) as Array).duplicate(true)
	_frame_force = (mission.get("force", {}) as Dictionary).duplicate(true)
	_frame_briefing = (mission.get("briefing", {}) as Dictionary).duplicate(true)
	_apply_frame_to_data()
	_clear_ui()
	_build_ui()


# Piece C4-1 (extended C4-2): overlays what the C-transport mission frame
# carries onto the legacy _build_ui() data shape (_data), so _build_ui()
# does not need a second rendering path. Only objective_primary/
# objectives_secondary and the tick display are frame-derived. Every
# other _data key the frame doesn't carry is a prose field that only
# ever came from UIDataBus.get_mission_briefing()'s mock fixture — on a
# frame-driven load _ready() has typically already backfilled _data from
# that mock (see _ready()) before load_frame() ever runs, so those keys
# must be reset to neutral placeholders here rather than left showing
# mock_001's fake situation text, enemy assessment, force roster, region
# name, and commander lineage. era_id is left alone (not prose; it only
# selects the accent color/badge and the frame carries no era field).
# Marker names go through _marker_name_for_node(), never the frame's raw node id.
func _apply_frame_to_data() -> void:
	_data["tick_counter"] = _frame_deadline_ticks

	var primary_obj: Dictionary = {}
	var secondary_objs: Array = []
	for o in _frame_objectives:
		var node := int(o.get("node", 0))
		var entry := {
			"text": _marker_name_for_node(node),
			"detail": "",
		}
		if bool(o.get("primary", false)):
			primary_obj = entry
		else:
			secondary_objs.append(entry)
	_data["objective_primary"] = primary_obj
	_data["objectives_secondary"] = secondary_objs

	if _frame_loaded:
		_data["mission_id_label"] = ""
		_data["chapter"] = 0
		_data["generation"] = 0
		_data["mission_title"] = ""
		_data["mission_subtitle"] = ""
		var situation: String = str(_frame_briefing.get("situation", ""))
		var assets: String = str(_frame_briefing.get("assets", ""))
		_data["situation_text"] = (situation + "\n\n" + assets).strip_edges()
		_data["objective"] = str(_frame_briefing.get("objective", ""))
		_data["enemy_assessment"] = {}
		_data["player_force"] = {"units": _roster_units()}
		_data["region_state"] = {}
		_data["commander_lineage"] = {}
		_data["reinforcement_note"] = ""


# Piece C4-1: makes _build_ui() safe to call more than once (load_frame()
# calls it on every rebind). Mirrors scenes/world/chronicle_scroll_panel.gd's
# begin_time_jump(), which clears _entry_container's children before
# rebuilding, except this clears the root's own direct children (bg,
# margin) since _build_ui() adds straight to self. remove_child() first so
# a load_frame() call that immediately rebuilds again (no frame boundary in
# between, as the fenced test does) does not see stale children still
# reporting as present.
func _clear_ui() -> void:
	for child in get_children():
		if child == _error_panel:
			continue
		remove_child(child)
		child.queue_free()


func qa_state() -> Dictionary:
	var objectives: Array = []
	for o in _frame_objectives:
		var node := int(o.get("node", 0))
		objectives.append({
			"i": int(o.get("i", 0)),
			"kind": int(o.get("kind", 0)),
			"node": node,
			"primary": bool(o.get("primary", false)),
			"marker_name": _marker_name_for_node(node),
		})
	var state := {
		"scene": "mission_briefing",
		"tick": -1,
		"plants": ["marker-from-frame"],
		"archetype": _frame_archetype,
		"deadline_ticks": _frame_deadline_ticks,
		"objectives": objectives,
		"deploy_enabled": _deploy_btn != null and not _deploy_btn.disabled,
		"deploy_error": _deploy_error_label.text if _deploy_error_label != null else "",
		"error_panel": _error_panel != null and _error_panel.visible and _error_panel.get_node("ErrorPanel").visible,
	}
	if _variant_picker != null:  # H-060 ruling 3: present only in beta mode
		state["variant_picker"] = {"count": _variant_picker.item_count, "selected": _variant_picker.selected}
	return state


func qa_plant(id: String) -> bool:
	match id:
		"marker-from-frame":
			_plant_marker_from_frame = true
			return true
		"begin-refused":
			_plant_begin_refused = true
			return true
		_:
			return false


# A82: a marker shows its region's own name; node only picks the offline "Node N" plant.
func _marker_name_for_node(node: int) -> String:
	if _plant_marker_from_frame:
		return "Node %d" % node
	if _names == null:
		_names = load("res://scenes/world/chronicle_names.gd").new()
		var data = JSON.parse_string(FileAccess.get_file_as_string(_FRAGMENTS_PATH))
		if data is Dictionary:
			_names.load_tables(data.get("name_tables", {}))
	return _names.fill_template("{region_name}", _frame_region, 0)


func _roster_units() -> Array:
	var units: Array = []
	var counts: Array = _frame_force.get("types", [])
	for i in mini(counts.size(), _UNIT_NAMES.size()):
		if int(counts[i]) > 0:
			units.append({"type_display_name": _UNIT_NAMES[i], "count": int(counts[i])})
	return units
