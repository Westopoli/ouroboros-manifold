extends Label

@export var section_text: String = "":
	set(value):
		section_text = value
		text = value

func _ready() -> void:
	uppercase = true
	add_theme_font_override("font", ThemeConstants.font_mono_regular)
	add_theme_font_size_override("font_size", ThemeConstants.SECTION_LABEL_SIZE)
	add_theme_color_override("font_color", ThemeConstants.TERTIARY)
	text = section_text
