extends Control

const Palette := preload("res://scenes/mockups/menus/theme.gd")
const QaPlants := preload("res://scenes/mockups/_shared/qa_plants.gd")

var root
var _header: Label
var _situation: Label
var _objective: Label
var _assets: Label
var _heading_labels: Dictionary = {}


static func parity_words(pct: int) -> String:
	if pct >= 95:
		return "even parity"
	if pct >= 85:
		return "near parity"
	if pct >= 70:
		return "outnumbered by a fifth"
	if pct >= 55:
		return "outnumbered by a third"
	if pct >= 40:
		return "badly outnumbered"
	return "hopelessly outnumbered"


static func compose(fixture: Dictionary) -> Dictionary:
	var force: Dictionary = fixture.get("player_force", {})
	var pct: int = int(force.get("parity_percentage", 100))
	var parity_text: String = ("%d percent parity" % pct) if QaPlants.is_active("digits-in-prose") else parity_words(pct)
	var enemy: Dictionary = fixture.get("enemy_assessment", {})
	var attacker: String = String(enemy.get("faction_name", "the enemy"))
	var situation: String = String(fixture.get("situation_text", ""))
	var objective: String = String(fixture.get("objective_primary", {}).get("text", ""))
	var assets_template: String = String(fixture.get("assets_note", ""))
	var assets: String = assets_template.replace("{parity}", parity_text)

	var drop_assets: bool = QaPlants.is_active("briefing-two-sections")
	var sections: Array = ["Situation", "Objective"]
	if not drop_assets:
		sections.append("Assets")

	var scan_text: String = situation + " " + objective + ("" if drop_assets else (" " + assets))
	var has_digits := false
	for c in scan_text:
		if c >= "0" and c <= "9":
			has_digits = true
			break

	return {
		"title": String(fixture.get("mission_title", "")),
		"subtitle": String(fixture.get("mission_subtitle", "")),
		"region": String(fixture.get("region_state", {}).get("name", "")),
		"sections": sections,
		"attacker_named": situation.to_lower().find(attacker.to_lower()) != -1,
		"has_digits": has_digits,
		"situation": situation,
		"objective": objective,
		"assets": assets,
		"drop_assets": drop_assets,
	}


func _ready() -> void:
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	_build()


func _build() -> void:
	var content := VBoxContainer.new()
	content.anchor_left = 0.1
	content.anchor_top = 0.08
	content.anchor_right = 0.68
	content.anchor_bottom = 0.86
	content.add_theme_constant_override("separation", 14)
	add_child(content)

	_header = Label.new()
	_header.add_theme_font_override("font", Palette.serif_regular())
	_header.add_theme_font_size_override("font_size", Palette.TITLE_SIZE - 10)
	_header.add_theme_color_override("font_color", Palette.PRIMARY)
	content.add_child(_header)

	_situation = _make_section(content, "Situation")
	_objective = _make_section(content, "Objective")
	_assets = _make_section(content, "Assets")

	var footer := HBoxContainer.new()
	footer.add_theme_constant_override("separation", 12)
	content.add_child(footer)

	var accept := Button.new()
	accept.text = "Accept"
	accept.focus_mode = Control.FOCUS_NONE
	accept.add_theme_font_override("font", Palette.mono_medium())
	accept.pressed.connect(func(): root.qa_go("accept"))
	footer.add_child(accept)

	var refuse := Button.new()
	refuse.text = "Refuse"
	refuse.flat = true
	refuse.focus_mode = Control.FOCUS_NONE
	refuse.add_theme_font_override("font", Palette.mono_regular())
	refuse.pressed.connect(func(): root.qa_go("refuse"))
	footer.add_child(refuse)


func _make_section(parent: VBoxContainer, heading: String) -> Label:
	var head := Label.new()
	head.name = heading + "Heading"
	head.text = heading.to_upper()
	head.add_theme_font_override("font", Palette.mono_regular())
	head.add_theme_font_size_override("font_size", Palette.SECTION_LABEL_SIZE)
	head.add_theme_color_override("font_color", Palette.TERTIARY)
	parent.add_child(head)
	_heading_labels[heading] = head

	var body := Label.new()
	body.autowrap_mode = TextServer.AUTOWRAP_WORD
	body.custom_minimum_size = Vector2(640, 0)
	body.add_theme_font_override("font", Palette.serif_regular())
	body.add_theme_font_size_override("font_size", Palette.BODY_NARRATIVE_SIZE)
	body.add_theme_color_override("font_color", Palette.SECONDARY)
	parent.add_child(body)
	return body


func refresh(state: Dictionary) -> void:
	var fixture: Dictionary = state.get("fixture", {})
	var c: Dictionary = compose(fixture)
	_header.text = "%s  —  %s" % [c.title, c.region]
	_situation.text = c.situation
	_objective.text = c.objective
	var assets_visible: bool = not c.drop_assets
	_heading_labels["Assets"].visible = assets_visible
	_assets.visible = assets_visible
	_assets.text = c.assets if assets_visible else ""
