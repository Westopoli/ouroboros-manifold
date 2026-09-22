extends Control

const Palette := preload("res://scenes/mockups/menus/theme.gd")

const OUTCOME_PROSE := {
	"total_success": "The line held; the attackers broke first.",
	"strong_success": "A hard fight, but the objective is ours.",
	"partial_success": "The objective holds, at a cost we will feel.",
	"partial_failure": "The line bent further than command hoped.",
	"total_failure": "The position is lost.",
}

var root
var _band_label: Label
var _prose_label: Label
var _casualties_label: Label
var _continue_btn: Button
var _t := 0.0
var _fading := false


func _ready() -> void:
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	_build()
	set_process(true)


func _build() -> void:
	var content := VBoxContainer.new()
	content.set_anchors_preset(Control.PRESET_CENTER)
	content.add_theme_constant_override("separation", 10)
	add_child(content)

	var fought := Label.new()
	fought.text = "The battle is fought."
	fought.add_theme_font_override("font", Palette.serif_italic())
	fought.add_theme_font_size_override("font_size", Palette.SUBTITLE_SIZE)
	fought.add_theme_color_override("font_color", Palette.SECONDARY)
	content.add_child(fought)

	_band_label = Label.new()
	_band_label.name = "BandLabel"
	_band_label.add_theme_font_override("font", Palette.mono_medium())
	_band_label.add_theme_font_size_override("font_size", Palette.TITLE_SIZE - 8)
	_band_label.visible = false
	content.add_child(_band_label)

	_prose_label = Label.new()
	_prose_label.add_theme_font_override("font", Palette.serif_regular())
	_prose_label.add_theme_font_size_override("font_size", Palette.BODY_NARRATIVE_SIZE)
	_prose_label.add_theme_color_override("font_color", Palette.PRIMARY)
	_prose_label.visible = false
	content.add_child(_prose_label)

	_casualties_label = Label.new()
	_casualties_label.add_theme_font_override("font", Palette.mono_regular())
	_casualties_label.add_theme_font_size_override("font_size", Palette.BODY_DATA_SIZE)
	_casualties_label.add_theme_color_override("font_color", Palette.TERTIARY)
	_casualties_label.visible = false
	content.add_child(_casualties_label)

	_continue_btn = Button.new()
	_continue_btn.text = "Continue"
	_continue_btn.focus_mode = Control.FOCUS_NONE
	_continue_btn.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	_continue_btn.visible = false
	_continue_btn.add_theme_font_override("font", Palette.mono_medium())
	_continue_btn.pressed.connect(func(): root.qa_go("resolve_continue"))
	content.add_child(_continue_btn)


func refresh(state: Dictionary) -> void:
	var result: Dictionary = state.get("result", {})
	_t = 0.0
	_fading = true
	_band_label.visible = false
	_prose_label.visible = false
	_casualties_label.visible = false
	_continue_btn.visible = false
	if result.is_empty():
		return
	var band: String = String(result.get("band", ""))
	_band_label.text = band.replace("_", " ").to_upper()
	_band_label.add_theme_color_override("font_color", Palette.band_color(band))
	_prose_label.text = String(OUTCOME_PROSE.get(band, ""))
	var casualties: int = int(result.get("casualties", 0))
	var force: int = int(state.get("force_size", 12))
	_casualties_label.text = "%d of %d did not return" % [casualties, force]


func _process(delta: float) -> void:
	if not visible or not _fading:
		return
	_t += delta
	if _t >= 2.0:
		_fading = false
		_band_label.visible = true
		_prose_label.visible = true
		_casualties_label.visible = true
		_continue_btn.visible = true
