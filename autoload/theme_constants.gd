extends Node

# Set to true for distribution builds. Gates all print() calls and debug output.
const IS_RELEASE_BUILD: bool = OS.has_feature("release_build")

# --- Background colors ---
const BASE := Color("#0A0D12")
const SURFACE := Color("#10141A")
const CARD := Color("#171C24")
const ELEVATED := Color("#1E242E")

# --- Text colors ---
const PRIMARY := Color("#e8e6e1")
const SECONDARY := Color(0.91, 0.90, 0.88, 0.55)
const TERTIARY := Color(0.91, 0.90, 0.88, 0.30)

# --- Semantic colors ---
const DANGER := Color("#c44a3f")
const INFO := Color("#5a8fbf")
const HEALTHY := Color("#4a9e6e")

# --- Era accent colors ---
const ERA_ACCENTS := {
	"roman": Color("#c9a84c"),
	"settled_reach": Color("#4a9eb8"),
	"1980s": Color("#8b9a3c"),
}

const DEFAULT_ACCENT := Color("#888888")

# --- Border values ---
const BORDER_WIDTH := 1
const BORDER_COLOR := Color(1.0, 1.0, 1.0, 0.08)
const BORDER_RADIUS := 6

# --- Typography sizes (px) ---
const CLASSIFICATION_LABEL_SIZE := 15
const CLASSIFICATION_LABEL_SPACING := 3
const SECTION_LABEL_SIZE := 14
const SECTION_LABEL_SPACING := 2.5
const ERA_BADGE_SIZE := 14
const TITLE_SIZE := 42
const SUBTITLE_SIZE := 21
const BODY_NARRATIVE_SIZE := 22
const BODY_DATA_SIZE := 18
const BODY_DATA_SMALL_SIZE := 16
const HINT_TEXT_SIZE := 15
const BUTTON_PRIMARY_SIZE := 16
const BUTTON_SECONDARY_SIZE := 16

# --- Animation timing ---
const STAGGER_BASE_DELAY := 0.2
const STAGGER_INCREMENT := 0.15
const ELEMENT_ANIM_DURATION := 0.5
const EASE_TYPE := Tween.EASE_OUT
const TRANS_TYPE := Tween.TRANS_CUBIC
const STAT_BAR_DURATION := 1.0
const CURSOR_BLINK_INTERVAL := 1.0
const DIVIDER_EXPAND_DURATION := 0.5
const FADE_DURATION := 0.3

# --- Font resources ---
var font_mono_regular: Font
var font_mono_medium: Font
var font_mono_bold: Font
var font_serif_regular: Font
var font_serif_light: Font
var font_serif_italic: Font
var font_serif_light_italic: Font
var font_serif_medium: Font

func _ready() -> void:
	font_mono_regular = load("res://theme/fonts/JetBrainsMono-Regular.ttf")
	font_mono_medium = load("res://theme/fonts/JetBrainsMono-Medium.ttf")
	font_mono_bold = load("res://theme/fonts/JetBrainsMono-Bold.ttf")
	font_serif_regular = load("res://theme/fonts/Newsreader-Regular.ttf")
	font_serif_light = load("res://theme/fonts/Newsreader-Light.ttf")
	font_serif_italic = load("res://theme/fonts/Newsreader-Italic.ttf")
	font_serif_light_italic = load("res://theme/fonts/Newsreader-LightItalic.ttf")
	font_serif_medium = load("res://theme/fonts/Newsreader-Medium.ttf")


func get_era_accent(era_id: String) -> Color:
	return ERA_ACCENTS.get(era_id, DEFAULT_ACCENT)


func get_era_accent_dim(era_id: String) -> Color:
	var accent := get_era_accent(era_id)
	return Color(accent.r, accent.g, accent.b, 0.15)


func get_era_accent_border(era_id: String) -> Color:
	var accent := get_era_accent(era_id)
	return Color(accent.r, accent.g, accent.b, 0.30)
