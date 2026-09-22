extends Control

const Palette := preload("res://scenes/mockups/menus/theme.gd")

var root
var _band_label: Label
var _objective_label: Label
var _retention_label: Label
var _fate_label: Label


static func retention_words(r: float) -> String:
	if r >= 0.9:
		return "the force came home largely intact"
	if r >= 0.7:
		return "losses were light"
	if r >= 0.5:
		return "losses were heavy"
	if r >= 0.3:
		return "the force was gutted"
	return "almost no one came home"


static func completion_words(band: String) -> String:
	if band == "total_success":
		return "fully achieved"
	if band == "strong_success":
		return "achieved"
	if band == "partial_success":
		return "partially achieved"
	if band == "partial_failure":
		return "not achieved"
	return "not achieved, decisively"


func _ready() -> void:
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	_build()


func _build() -> void:
	var content := VBoxContainer.new()
	content.anchor_left = 0.15
	content.anchor_top = 0.22
	content.anchor_right = 0.75
	content.anchor_bottom = 0.8
	content.add_theme_constant_override("separation", 14)
	add_child(content)

	var header := Label.new()
	header.text = "DEBRIEF"
	header.add_theme_font_override("font", Palette.mono_regular())
	header.add_theme_font_size_override("font_size", Palette.CLASSIFICATION_LABEL_SIZE)
	header.add_theme_color_override("font_color", Palette.TERTIARY)
	content.add_child(header)

	_band_label = Label.new()
	_band_label.name = "BandLabel"
	_band_label.add_theme_font_override("font", Palette.serif_medium())
	_band_label.add_theme_font_size_override("font_size", Palette.TITLE_SIZE - 8)
	content.add_child(_band_label)

	_objective_label = Label.new()
	_objective_label.autowrap_mode = TextServer.AUTOWRAP_WORD
	_objective_label.add_theme_font_override("font", Palette.serif_regular())
	_objective_label.add_theme_font_size_override("font_size", Palette.BODY_NARRATIVE_SIZE)
	_objective_label.add_theme_color_override("font_color", Palette.PRIMARY)
	content.add_child(_objective_label)

	_retention_label = Label.new()
	_retention_label.add_theme_font_override("font", Palette.mono_regular())
	_retention_label.add_theme_font_size_override("font_size", Palette.BODY_DATA_SIZE)
	_retention_label.add_theme_color_override("font_color", Palette.SECONDARY)
	content.add_child(_retention_label)

	_fate_label = Label.new()
	_fate_label.add_theme_font_override("font", Palette.mono_regular())
	_fate_label.add_theme_font_size_override("font_size", Palette.BODY_DATA_SIZE)
	_fate_label.add_theme_color_override("font_color", Palette.SECONDARY)
	content.add_child(_fate_label)

	var proceed := Button.new()
	proceed.text = "Proceed"
	proceed.focus_mode = Control.FOCUS_NONE
	proceed.add_theme_font_override("font", Palette.mono_medium())
	proceed.pressed.connect(func(): root.qa_go("proceed"))
	content.add_child(proceed)


func refresh(state: Dictionary) -> void:
	var result: Dictionary = state.get("result", {})
	var fixture: Dictionary = state.get("fixture", {})
	var band: String = String(result.get("band", ""))
	_band_label.text = band.replace("_", " ").to_upper()
	_band_label.add_theme_color_override("font_color", Palette.band_color(band))
	var objective_text: String = String(fixture.get("objective_primary", {}).get("text", ""))
	_objective_label.text = "%s Objective %s." % [objective_text, completion_words(band)]
	_retention_label.text = "Force retention: %s." % retention_words(float(result.get("retention", 0.0)))
	var fate: String = "killed in action" if band == "total_failure" else "survived"
	_fate_label.text = "Commander %s." % fate
