extends RefCounted

# Unit roster column of the era detail: type id as title, then category (A58 06).


static func build(parent: Control, roster: Array, tiers: Array) -> void:
	var col := VBoxContainer.new()
	col.add_theme_constant_override("separation", 12)
	col.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	parent.add_child(col)
	col.add_child(_label("TIERS  " + "  ".join(tiers.map(func(t): return str(t))), ThemeConstants.SECTION_LABEL_SIZE, ThemeConstants.TERTIARY))
	col.add_child(_label("UNIT ROSTER", ThemeConstants.SECTION_LABEL_SIZE, ThemeConstants.TERTIARY))
	for unit in roster:
		var row := HBoxContainer.new()
		row.add_theme_constant_override("separation", 12)
		col.add_child(row)
		var title := _label(unit["abstract_type"], ThemeConstants.BODY_DATA_SIZE, ThemeConstants.PRIMARY)
		title.custom_minimum_size.x = 160
		row.add_child(title)
		row.add_child(_label(unit["category"], ThemeConstants.BODY_DATA_SMALL_SIZE, ThemeConstants.SECONDARY))


static func _label(text: String, size: int, color: Color) -> Label:
	var l := Label.new()
	l.text = text
	l.add_theme_font_override("font", ThemeConstants.font_mono_regular)
	l.add_theme_font_size_override("font_size", size)
	l.add_theme_color_override("font_color", color)
	return l
