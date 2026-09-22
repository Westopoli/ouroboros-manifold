extends Control

const Palette := preload("res://scenes/mockups/menus/theme.gd")

var root
var _list: VBoxContainer


func _ready() -> void:
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	_build()


func _build() -> void:
	var content := VBoxContainer.new()
	content.anchor_left = 0.15
	content.anchor_top = 0.2
	content.anchor_right = 0.7
	content.anchor_bottom = 0.82
	content.add_theme_constant_override("separation", 12)
	add_child(content)

	var header := Label.new()
	header.text = "CAMPAIGNS"
	header.add_theme_font_override("font", Palette.mono_regular())
	header.add_theme_font_size_override("font_size", Palette.CLASSIFICATION_LABEL_SIZE)
	header.add_theme_color_override("font_color", Palette.TERTIARY)
	content.add_child(header)

	_list = VBoxContainer.new()
	_list.name = "List"
	_list.add_theme_constant_override("separation", 8)
	content.add_child(_list)

	var back := Button.new()
	back.text = "Back"
	back.flat = true
	back.focus_mode = Control.FOCUS_NONE
	back.size_flags_horizontal = Control.SIZE_SHRINK_BEGIN
	back.add_theme_font_override("font", Palette.mono_regular())
	back.pressed.connect(func(): root.qa_go("back"))
	content.add_child(back)


func refresh(state: Dictionary) -> void:
	for child in _list.get_children():
		child.queue_free()
	var campaigns: Array = state.get("campaigns", [])
	for rec in campaigns:
		_list.add_child(_build_row(rec))


func _build_row(rec: Dictionary) -> HBoxContainer:
	var row := HBoxContainer.new()
	row.add_theme_constant_override("separation", 16)

	var band: String = String(rec.get("last_band", ""))
	var band_text: String = band.replace("_", " ") if band != "" else "not yet fought"
	var name_label := Label.new()
	name_label.text = "%s — chapter %d — %s" % [rec.get("name", ""), int(rec.get("chapter", 1)), band_text]
	name_label.add_theme_font_override("font", Palette.mono_regular())
	name_label.add_theme_font_size_override("font_size", Palette.BODY_DATA_SIZE)
	name_label.add_theme_color_override("font_color", Palette.SECONDARY)
	row.add_child(name_label)

	var rec_name: String = String(rec.get("name", ""))
	var resume_btn := Button.new()
	resume_btn.text = "Resume"
	resume_btn.flat = true
	resume_btn.focus_mode = Control.FOCUS_NONE
	resume_btn.add_theme_font_override("font", Palette.mono_medium())
	resume_btn.pressed.connect(func(): root.qa_go("resume:%s" % rec_name))
	row.add_child(resume_btn)

	return row
