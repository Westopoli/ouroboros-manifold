extends RefCounted

const BASE := Color("#0A0D12")
const CARD := Color("#171C24")
const PRIMARY := Color("#e8e6e1")
const SECONDARY := Color(0.91, 0.90, 0.88, 0.55)
const TERTIARY := Color(0.91, 0.90, 0.88, 0.30)
const ACCENT := Color("#D4A017")

const BAND_COLORS := {
	"total_success": Color(0.3, 0.9, 0.4),
	"strong_success": Color(0.5, 0.8, 0.4),
	"partial_success": Color(0.8, 0.7, 0.3),
	"partial_failure": Color(0.9, 0.5, 0.3),
	"total_failure": Color(0.9, 0.3, 0.3),
}

const TITLE_SIZE := 42
const SUBTITLE_SIZE := 21
const SECTION_LABEL_SIZE := 14
const CLASSIFICATION_LABEL_SIZE := 15
const BODY_NARRATIVE_SIZE := 22
const BODY_DATA_SIZE := 18
const HINT_TEXT_SIZE := 15
const MENU_ITEM_SIZE := 27


static func mono_regular() -> Font:
	return load("res://theme/fonts/JetBrainsMono-Regular.ttf")


static func mono_medium() -> Font:
	return load("res://theme/fonts/JetBrainsMono-Medium.ttf")


static func serif_regular() -> Font:
	return load("res://theme/fonts/Newsreader-Regular.ttf")


static func serif_italic() -> Font:
	return load("res://theme/fonts/Newsreader-Italic.ttf")


static func serif_medium() -> Font:
	return load("res://theme/fonts/Newsreader-Medium.ttf")


static func band_color(band: String) -> Color:
	return BAND_COLORS.get(band, SECONDARY)
