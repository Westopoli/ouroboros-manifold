extends Control
# See also: legacy tactical_loading_overlay.gd (git show 009c99ac^:scenes/tactical/tactical_loading_overlay.gd), S-138.
# Covers the view with "DEPLOYING FORCES" until the first frame is in; the view calls dismiss() from load_frame.

const TITLE := "DEPLOYING FORCES"
const ACCENT := Color("#c9a84c")
const FADE_SECONDS := 0.3

var _bg: ColorRect
var _header: Label
var _dismissed := false


func _ready() -> void:
	name = "LoadingOverlay"
	set_anchors_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	_bg = ColorRect.new()
	_bg.color = ThemeConstants.BASE
	_bg.set_anchors_preset(Control.PRESET_FULL_RECT)
	_bg.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(_bg)
	_header = Label.new()
	_header.text = TITLE
	_header.add_theme_font_override("font", ThemeConstants.font_mono_regular)
	_header.add_theme_font_size_override("font_size", ThemeConstants.CLASSIFICATION_LABEL_SIZE)
	_header.add_theme_color_override("font_color", ACCENT)
	_header.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_header.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	_header.set_anchors_preset(Control.PRESET_FULL_RECT)
	_header.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(_header)


func is_showing() -> bool:
	return visible and not _dismissed


func dismiss() -> void:
	if _dismissed:
		return
	_dismissed = true
	visible = false
