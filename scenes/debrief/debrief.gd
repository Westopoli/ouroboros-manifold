extends Control

signal debrief_completed

var _params: Dictionary = {}
var _accent: Color = ThemeConstants.DEFAULT_ACCENT


func setup(params: Dictionary) -> void:
	_params = params
	var era_id: String = params.get("era_id", "")
	if era_id != "":
		_accent = ThemeConstants.get_era_accent(era_id)
	_build_ui()


func _input(event: InputEvent) -> void:
	if event.is_action_pressed("ui_cancel"):
		_on_exit()


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
	header.text = "MISSION DEBRIEF"
	header.uppercase = true
	header.add_theme_font_override("font", ThemeConstants.font_mono_regular)
	header.add_theme_font_size_override("font_size", ThemeConstants.CLASSIFICATION_LABEL_SIZE)
	header.add_theme_color_override("font_color", ThemeConstants.TERTIARY)
	outer.add_child(header)

	var divider = load("res://theme/components/tm_divider.tscn").instantiate()
	outer.add_child(divider)

	var scroll := ScrollContainer.new()
	scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
	scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	outer.add_child(scroll)

	var content := VBoxContainer.new()
	content.add_theme_constant_override("separation", 24)
	content.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	scroll.add_child(content)

	_build_outcome_section(content)
	_build_objectives_section(content)
	_build_ribbon_section(content)
	_build_retention_section(content)
	_build_impact_section(content)

	var footer := HBoxContainer.new()
	footer.add_theme_constant_override("separation", 12)
	outer.add_child(footer)

	var continue_btn = load("res://theme/components/tm_button.tscn").instantiate()
	continue_btn.text = "CONTINUE"
	continue_btn.accent_color = _accent
	continue_btn.pressed.connect(_on_continue)
	footer.add_child(continue_btn)

	var exit_btn = load("res://theme/components/tm_button.tscn").instantiate()
	exit_btn.text = "EXIT TO MAIN MENU"
	exit_btn.style = 1
	exit_btn.pressed.connect(_on_exit)
	footer.add_child(exit_btn)

	var spacer := Control.new()
	spacer.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	footer.add_child(spacer)

	var duration_text := ""
	var dur_sec: float = _debrief().get("mission_duration_seconds", 0.0)
	if dur_sec > 0:
		var mins := int(dur_sec) / 60
		var secs := int(dur_sec) % 60
		duration_text = "Mission duration: %d:%02d" % [mins, secs]
	var hint := Label.new()
	hint.text = duration_text
	hint.add_theme_font_override("font", ThemeConstants.font_mono_regular)
	hint.add_theme_font_size_override("font_size", ThemeConstants.HINT_TEXT_SIZE)
	hint.add_theme_color_override("font_color", ThemeConstants.TERTIARY)
	hint.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	footer.add_child(hint)


func _build_outcome_section(parent: Control) -> void:
	var data := _debrief()
	var band: String = data.get("outcome_band", "")
	var prose: String = data.get("outcome_band_prose", "")
	var score: float = data.get("final_score", 0.0)

	var card = load("res://theme/components/tm_card.tscn").instantiate()
	parent.add_child(card)
	var content = card.get_content_container()

	var section := Label.new()
	section.text = "OUTCOME"
	section.uppercase = true
	section.add_theme_font_override("font", ThemeConstants.font_mono_regular)
	section.add_theme_font_size_override("font_size", ThemeConstants.SECTION_LABEL_SIZE)
	section.add_theme_color_override("font_color", ThemeConstants.TERTIARY)
	content.add_child(section)

	var prose_label := Label.new()
	prose_label.text = prose
	prose_label.add_theme_font_override("font", ThemeConstants.font_serif_medium)
	prose_label.add_theme_font_size_override("font_size", 28)
	prose_label.add_theme_color_override("font_color", ThemeConstants.PRIMARY)
	prose_label.autowrap_mode = TextServer.AUTOWRAP_WORD
	content.add_child(prose_label)

	var detail_row := HBoxContainer.new()
	detail_row.add_theme_constant_override("separation", 24)
	content.add_child(detail_row)

	var band_label := Label.new()
	band_label.text = band.replace("_", " ").to_upper()
	band_label.add_theme_font_override("font", ThemeConstants.font_mono_regular)
	band_label.add_theme_font_size_override("font_size", ThemeConstants.BODY_DATA_SIZE)
	band_label.add_theme_color_override("font_color", _band_color(band))
	detail_row.add_child(band_label)

	var score_label := Label.new()
	score_label.text = "Score: %.0f%%" % (score * 100.0)
	score_label.add_theme_font_override("font", ThemeConstants.font_mono_regular)
	score_label.add_theme_font_size_override("font_size", ThemeConstants.BODY_DATA_SMALL_SIZE)
	score_label.add_theme_color_override("font_color", ThemeConstants.SECONDARY)
	detail_row.add_child(score_label)

	var style: StyleBoxFlat = card.get_theme_stylebox("panel").duplicate()
	style.border_color = _band_color(band)
	style.set_border_width_all(2)
	card.add_theme_stylebox_override("panel", style)


func _build_objectives_section(parent: Control) -> void:
	var data := _debrief()
	var objectives: Array = data.get("objectives", [])
	if objectives.is_empty():
		return

	var card = load("res://theme/components/tm_card.tscn").instantiate()
	parent.add_child(card)
	var content = card.get_content_container()

	var section := Label.new()
	section.text = "OBJECTIVES"
	section.uppercase = true
	section.add_theme_font_override("font", ThemeConstants.font_mono_regular)
	section.add_theme_font_size_override("font_size", ThemeConstants.SECTION_LABEL_SIZE)
	section.add_theme_color_override("font_color", ThemeConstants.TERTIARY)
	content.add_child(section)

	for obj in objectives:
		var row := VBoxContainer.new()
		row.add_theme_constant_override("separation", 4)
		content.add_child(row)

		var header_row := HBoxContainer.new()
		header_row.add_theme_constant_override("separation", 12)
		row.add_child(header_row)

		var obj_label := Label.new()
		obj_label.text = str(obj.get("label", obj.get("id", "")))
		obj_label.add_theme_font_override("font", ThemeConstants.font_serif_regular)
		obj_label.add_theme_font_size_override("font_size", ThemeConstants.BODY_DATA_SIZE)
		obj_label.add_theme_color_override("font_color", ThemeConstants.PRIMARY)
		obj_label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		header_row.add_child(obj_label)

		var completion: float = obj.get("completion", 0.0)
		var weight: float = obj.get("weight", 0.0)
		var pct_label := Label.new()
		pct_label.text = "%.0f%%  (weight %.0f%%)" % [completion * 100.0, weight * 100.0]
		pct_label.add_theme_font_override("font", ThemeConstants.font_mono_regular)
		pct_label.add_theme_font_size_override("font_size", ThemeConstants.BODY_DATA_SMALL_SIZE)
		pct_label.add_theme_color_override("font_color", ThemeConstants.SECONDARY)
		header_row.add_child(pct_label)

		# Progress bar
		var bar_bg := ColorRect.new()
		bar_bg.custom_minimum_size = Vector2(0, 6)
		bar_bg.color = ThemeConstants.BORDER_COLOR
		row.add_child(bar_bg)

		var bar_fill := ColorRect.new()
		bar_fill.custom_minimum_size = Vector2(0, 6)
		bar_fill.color = _accent
		bar_fill.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		row.add_child(bar_fill)

		# Defer sizing the fill bar after layout
		var fill_pct: float = completion
		bar_fill.resized.connect(func():
			var parent_w := bar_bg.size.x
			if parent_w > 0:
				bar_fill.custom_minimum_size.x = parent_w * fill_pct
				bar_fill.size.x = parent_w * fill_pct
		, CONNECT_ONE_SHOT)


func _build_ribbon_section(parent: Control) -> void:
	var metrics := MissionMetricsRecorder.get_metrics()
	var samples: Array = metrics.get("samples", [])
	if samples.size() < 2:
		return

	var card = load("res://theme/components/tm_card.tscn").instantiate()
	parent.add_child(card)
	var content = card.get_content_container()

	var section := Label.new()
	section.text = "PERFORMANCE"
	section.uppercase = true
	section.add_theme_font_override("font", ThemeConstants.font_mono_regular)
	section.add_theme_font_size_override("font_size", ThemeConstants.SECTION_LABEL_SIZE)
	section.add_theme_color_override("font_color", ThemeConstants.TERTIARY)
	content.add_child(section)

	var legend := Label.new()
	legend.text = "Gold = your forces     Blue = enemy forces"
	legend.add_theme_font_override("font", ThemeConstants.font_mono_regular)
	legend.add_theme_font_size_override("font_size", ThemeConstants.HINT_TEXT_SIZE)
	legend.add_theme_color_override("font_color", ThemeConstants.TERTIARY)
	content.add_child(legend)

	var vp_container := SubViewportContainer.new()
	vp_container.custom_minimum_size = Vector2(0, 300)
	vp_container.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	vp_container.stretch = true
	content.add_child(vp_container)

	var vp := SubViewport.new()
	vp.size = Vector2i(1200, 300)
	vp.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	vp.transparent_bg = true
	vp_container.add_child(vp)

	var graph = load("res://scenes/debrief/ribbon_graph.tscn").instantiate()
	vp.add_child(graph)
	graph.build(metrics)


func _build_retention_section(parent: Control) -> void:
	var data := _debrief()
	var retention: float = data.get("force_retention", 0.0)
	var obj_score: float = data.get("objective_score", 0.0)

	var card = load("res://theme/components/tm_card.tscn").instantiate()
	parent.add_child(card)
	var content = card.get_content_container()

	var section := Label.new()
	section.text = "FORCE STATUS"
	section.uppercase = true
	section.add_theme_font_override("font", ThemeConstants.font_mono_regular)
	section.add_theme_font_size_override("font_size", ThemeConstants.SECTION_LABEL_SIZE)
	section.add_theme_color_override("font_color", ThemeConstants.TERTIARY)
	content.add_child(section)

	var stats := HBoxContainer.new()
	stats.add_theme_constant_override("separation", 40)
	content.add_child(stats)

	_add_stat(stats, "Force Retained", "%.0f%%" % (retention * 100.0))
	_add_stat(stats, "Objective Score", "%.0f%%" % (obj_score * 100.0))

	var fate: String = data.get("commander_fate", "survived")
	var fate_text := "SURVIVED" if fate == "survived" else "KILLED IN ACTION"
	var fate_color := ThemeConstants.PRIMARY if fate == "survived" else Color(0.9, 0.3, 0.3)
	_add_stat(stats, "Commander", fate_text, fate_color)


func _build_impact_section(parent: Control) -> void:
	var data := _debrief()
	var preview: String = data.get("impact_preview", "")
	var field_deltas: Dictionary = data.get("field_deltas", {})
	if preview.is_empty() and field_deltas.is_empty():
		return

	var card = load("res://theme/components/tm_card.tscn").instantiate()
	parent.add_child(card)
	var content = card.get_content_container()

	var section := Label.new()
	section.text = "SIMULATION IMPACT"
	section.uppercase = true
	section.add_theme_font_override("font", ThemeConstants.font_mono_regular)
	section.add_theme_font_size_override("font_size", ThemeConstants.SECTION_LABEL_SIZE)
	section.add_theme_color_override("font_color", ThemeConstants.TERTIARY)
	content.add_child(section)

	if not preview.is_empty():
		var preview_label := Label.new()
		preview_label.text = preview
		preview_label.add_theme_font_override("font", ThemeConstants.font_serif_italic)
		preview_label.add_theme_font_size_override("font_size", ThemeConstants.BODY_DATA_SIZE)
		preview_label.add_theme_color_override("font_color", ThemeConstants.SECONDARY)
		preview_label.autowrap_mode = TextServer.AUTOWRAP_WORD
		content.add_child(preview_label)

	var deltas_row := HBoxContainer.new()
	deltas_row.add_theme_constant_override("separation", 32)
	content.add_child(deltas_row)

	for field_name in ["military", "tension", "economy", "population"]:
		var fd: Dictionary = field_deltas.get(field_name, {})
		var raw: float = fd.get("raw", 0.0)
		if absf(raw) < 0.01:
			continue
		var direction: String = fd.get("direction", "stable")
		var arrow := "\u25b2" if direction == "up" else "\u25bc"
		var delta_color := Color(0.3, 0.9, 0.4) if direction == "up" else Color(0.9, 0.4, 0.3)
		# Tension is inverted — up is bad, down is good
		if field_name == "tension":
			delta_color = Color(0.9, 0.4, 0.3) if direction == "up" else Color(0.3, 0.9, 0.4)

		var delta_vbox := VBoxContainer.new()
		delta_vbox.add_theme_constant_override("separation", 2)
		deltas_row.add_child(delta_vbox)

		var field_label := Label.new()
		field_label.text = field_name.to_upper()
		field_label.add_theme_font_override("font", ThemeConstants.font_mono_regular)
		field_label.add_theme_font_size_override("font_size", ThemeConstants.HINT_TEXT_SIZE)
		field_label.add_theme_color_override("font_color", ThemeConstants.TERTIARY)
		delta_vbox.add_child(field_label)

		var val_label := Label.new()
		val_label.text = "%s %+.1f" % [arrow, raw]
		val_label.add_theme_font_override("font", ThemeConstants.font_mono_regular)
		val_label.add_theme_font_size_override("font_size", ThemeConstants.BODY_DATA_SIZE)
		val_label.add_theme_color_override("font_color", delta_color)
		delta_vbox.add_child(val_label)


func _add_stat(parent: Control, label_text: String, value_text: String, value_color: Color = ThemeConstants.PRIMARY) -> void:
	var vbox := VBoxContainer.new()
	vbox.add_theme_constant_override("separation", 2)
	parent.add_child(vbox)

	var label := Label.new()
	label.text = label_text
	label.add_theme_font_override("font", ThemeConstants.font_mono_regular)
	label.add_theme_font_size_override("font_size", ThemeConstants.HINT_TEXT_SIZE)
	label.add_theme_color_override("font_color", ThemeConstants.TERTIARY)
	vbox.add_child(label)

	var val := Label.new()
	val.text = value_text
	val.add_theme_font_override("font", ThemeConstants.font_mono_regular)
	val.add_theme_font_size_override("font_size", 24)
	val.add_theme_color_override("font_color", value_color)
	vbox.add_child(val)


func _band_color(band: String) -> Color:
	match band:
		"total_success":
			return Color(0.3, 0.9, 0.4)
		"strong_success":
			return Color(0.5, 0.8, 0.4)
		"partial_success":
			return Color(0.8, 0.7, 0.3)
		"partial_failure":
			return Color(0.9, 0.5, 0.3)
		"total_failure":
			return Color(0.9, 0.3, 0.3)
	return ThemeConstants.SECONDARY


func _debrief() -> Dictionary:
	return _params.get("debrief", {})


func _on_continue() -> void:
	debrief_completed.emit()
	# Stage 11 sequencer will listen for this signal and trigger pull-back.
	# For now, go to main menu as fallback.
	SceneRouter.go_to("main_menu")


func _on_exit() -> void:
	SceneRouter.go_to("main_menu")
