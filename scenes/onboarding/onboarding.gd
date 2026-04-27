extends Control

var _params: Dictionary = {}
var _selected_difficulty: String = "medium"
var _rare_marks: Array[String] = []
var _expanded_archetype: String = ""
var _difficulty_cards: Array[Control] = []
var _archetype_cards: Dictionary = {}  # archetype_id → card node
var _archetype_expand_panels: Dictionary = {}  # archetype_id → expand panel
var _archetype_chevrons: Dictionary = {}  # archetype_id → chevron label
var _archetype_badges: Dictionary = {}  # archetype_id → rare badge
var _rare_count_label: Label
var _confirm_btn: Button
var _accent: Color = ThemeConstants.DEFAULT_ACCENT

const MAX_RARE := 2

const DIFFICULTIES := [
	{"id": "easy", "name": "Easy",
	 "desc": "Forgiving consequences. More time, more resources, gentler simulation. The enemy fights the same — you just have more room to recover from mistakes."},
	{"id": "medium", "name": "Medium",
	 "desc": "The intended experience. Fair consequences, balanced resources. What the simulation was tuned for."},
	{"id": "hard", "name": "Hard",
	 "desc": "Punishing consequences. Less time, fewer resources, aggressive simulation. Every loss compounds. The enemy doesn't get stronger — you just can't afford to stumble."},
]

const ALL_ARCHETYPES := [
	{"id": "defensive_stand", "name": "Defensive Stand",
	 "one_liner": "Hold your position against an incoming assault.",
	 "detail": "You start dug in with chokepoints and cover. The enemy commits a fixed budget and approaches from multiple vectors — your job is reading which approach is the main thrust and concentrating force there. Skews toward Line and Bastion units. The map rewards patience and positioning over aggression."},
	{"id": "siege_breaking", "name": "Siege Breaking",
	 "one_liner": "Break an enemy stranglehold on a besieged region.",
	 "detail": "Your region is surrounded — enemy forward bases ring the perimeter, strangling supply lines. You start inside and push outward, choosing which positions to hit first. A balanced force for both breakthrough and holding gained ground. Large maps with multiple enemy positions that reward prioritization."},
	{"id": "reconquest", "name": "Reconquest",
	 "one_liner": "Retake a recently conquered region before the occupier digs in.",
	 "detail": "Former friendly territory occupied by a thin, still-fortifying garrison. Time-sensitive — the longer you wait, the more entrenched they get. Offensive-heavy with Raiders for fast strikes on dispersed positions. The map has infrastructure the occupier is repurposing, and the population is partially sympathetic."},
	{"id": "assault", "name": "Assault",
	 "one_liner": "Lead an offensive to conquer enemy territory.",
	 "detail": "Full offensive into established enemy territory. The defender has prepared positions, fortified chokepoints, and home-field infrastructure. You start outside and fight inward through multiple approach vectors with different risk profiles. Heavy on Vanguard and Bombard. Large maps that reward scouting during recon."},
	{"id": "suppression", "name": "Suppression",
	 "one_liner": "Crush a newly formed breakaway faction before it consolidates.",
	 "detail": "A revolt has spawned a breakaway faction holding damaged territory. They're weak but dispersed — multiple small positions rather than one fortified base. Fast, aggressive, small-scale. Raider-heavy for pursuit. Sensor interference may be present. Rewards aggressive pursuit over static defense."},
	{"id": "multi_front_defense", "name": "Multi-Front Defense",
	 "one_liner": "Survive simultaneous attacks from multiple directions.",
	 "detail": "Multiple hostile factions hitting you at once. Your force is adequate in total but insufficient at any single point — the core challenge is deciding where to concentrate and where to accept losses. Interior lines let you shift forces between fronts, but movement takes time. The largest-scale mission type."},
	{"id": "interception", "name": "Interception",
	 "one_liner": "Intercept an enemy force in the field before it reaches its target.",
	 "detail": "Pure force-on-force on open ground — no defensive infrastructure for either side. The enemy is in transit toward a target region and you must stop them before they reach the exit. Mobile, aggressive, Raider and Interceptor heavy. Open terrain with tactical features but no fortifications. Speed and positioning matter most."},
	{"id": "evacuation", "name": "Evacuation",
	 "one_liner": "Save what you can from a region that's already lost.",
	 "detail": "You're not trying to win — you're trying to save what you can before the position is overrun. Protect evacuation convoys while delaying the enemy advance with an undersized force. The map compresses as the enemy pushes forward. Multiple things to protect that can't all be defended simultaneously, forcing triage."},
	{"id": "containment", "name": "Containment",
	 "one_liner": "Draw a line and hold it against an expanding hostile faction.",
	 "detail": "A hostile faction is spreading through adjacent regions. You garrison a wide front with multiple chokepoints and natural defensive positions, but gaps between them. The enemy sends forces through multiple corridors, testing your deployment. Defensive and spread thin — Line, Bastion, and Interceptor heavy. Rewards reading the main effort and redeploying reserves."},
	{"id": "counterinsurgency", "name": "Counterinsurgency",
	 "one_liner": "Hunt down insurgent forces in your own territory without destroying it.",
	 "detail": "Internal threat — revolt chains have spawned unrest in your own region. The insurgents hide among the population, using sensor interference and difficult terrain. Collateral damage hurts you — heavy weapons risk worsening tension. Precision units like Raiders and Interceptors over blunt force. Small canvas, high sensor interference."},
]

const ROMAN_ARCHETYPES := ["defensive_stand", "assault", "reconquest", "siege_breaking", "evacuation"]


func setup(params: Dictionary) -> void:
	_params = params
	var era_id: String = params.get("era_id", "")
	if era_id != "":
		_accent = ThemeConstants.get_era_accent(era_id)
	_build_ui()


func _ready() -> void:
	pass


func _input(event: InputEvent) -> void:
	if event.is_action_pressed("ui_cancel"):
		SceneRouter.go_back()


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
	header.text = "COMMANDER ONBOARDING"
	header.uppercase = true
	header.add_theme_font_override("font", ThemeConstants.font_mono_regular)
	header.add_theme_font_size_override("font_size", ThemeConstants.CLASSIFICATION_LABEL_SIZE)
	header.add_theme_color_override("font_color", ThemeConstants.TERTIARY)
	outer.add_child(header)

	var divider = load("res://theme/components/tm_divider.tscn").instantiate()
	outer.add_child(divider)

	var columns := HBoxContainer.new()
	columns.add_theme_constant_override("separation", 40)
	columns.size_flags_vertical = Control.SIZE_EXPAND_FILL
	outer.add_child(columns)

	_build_difficulty_column(columns)
	_build_archetype_column(columns)

	var footer := HBoxContainer.new()
	footer.add_theme_constant_override("separation", 12)
	outer.add_child(footer)

	_confirm_btn = load("res://theme/components/tm_button.tscn").instantiate()
	_confirm_btn.text = "CONFIRM"
	_confirm_btn.accent_color = _accent
	_confirm_btn.pressed.connect(_on_confirm)
	footer.add_child(_confirm_btn)

	var back_btn = load("res://theme/components/tm_button.tscn").instantiate()
	back_btn.text = "BACK"
	back_btn.style = 1
	back_btn.pressed.connect(func(): SceneRouter.go_back())
	footer.add_child(back_btn)

	var spacer := Control.new()
	spacer.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	footer.add_child(spacer)

	var hint := Label.new()
	hint.text = "ESC to return"
	hint.add_theme_font_override("font", ThemeConstants.font_mono_regular)
	hint.add_theme_font_size_override("font_size", ThemeConstants.HINT_TEXT_SIZE)
	hint.add_theme_color_override("font_color", ThemeConstants.TERTIARY)
	hint.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	footer.add_child(hint)

	_select_difficulty("medium")


func _build_difficulty_column(parent: Control) -> void:
	var col := VBoxContainer.new()
	col.add_theme_constant_override("separation", 12)
	col.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	col.custom_minimum_size.x = 300
	parent.add_child(col)

	var section := Label.new()
	section.text = "DIFFICULTY"
	section.uppercase = true
	section.add_theme_font_override("font", ThemeConstants.font_mono_regular)
	section.add_theme_font_size_override("font_size", ThemeConstants.SECTION_LABEL_SIZE)
	section.add_theme_color_override("font_color", ThemeConstants.TERTIARY)
	col.add_child(section)

	for diff in DIFFICULTIES:
		var card = load("res://theme/components/tm_card.tscn").instantiate()
		col.add_child(card)
		var content = card.get_content_container()

		var name_label := Label.new()
		name_label.text = diff["name"]
		name_label.add_theme_font_override("font", ThemeConstants.font_serif_regular)
		name_label.add_theme_font_size_override("font_size", 24)
		name_label.add_theme_color_override("font_color", ThemeConstants.PRIMARY)
		content.add_child(name_label)

		var desc := Label.new()
		desc.text = diff["desc"]
		desc.add_theme_font_override("font", ThemeConstants.font_mono_regular)
		desc.add_theme_font_size_override("font_size", ThemeConstants.BODY_DATA_SMALL_SIZE)
		desc.add_theme_color_override("font_color", ThemeConstants.SECONDARY)
		desc.autowrap_mode = TextServer.AUTOWRAP_WORD
		content.add_child(desc)

		card.mouse_filter = Control.MOUSE_FILTER_STOP
		var diff_id: String = diff["id"]
		card.gui_input.connect(func(event: InputEvent):
			if event is InputEventMouseButton and event.pressed and event.button_index == MOUSE_BUTTON_LEFT:
				_select_difficulty(diff_id)
		)
		_difficulty_cards.append(card)


func _build_archetype_column(parent: Control) -> void:
	var col := VBoxContainer.new()
	col.add_theme_constant_override("separation", 12)
	col.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	parent.add_child(col)

	var section := Label.new()
	section.text = "MISSION PREFERENCES"
	section.uppercase = true
	section.add_theme_font_override("font", ThemeConstants.font_mono_regular)
	section.add_theme_font_size_override("font_size", ThemeConstants.SECTION_LABEL_SIZE)
	section.add_theme_color_override("font_color", ThemeConstants.TERTIARY)
	col.add_child(section)

	var guidance := Label.new()
	guidance.text = "You can mark up to 2 mission types as rare. Rare missions still appear occasionally \u2014 they're deprioritized, not removed. If you're not sure, leave them all unmarked."
	guidance.add_theme_font_override("font", ThemeConstants.font_serif_regular)
	guidance.add_theme_font_size_override("font_size", ThemeConstants.BODY_DATA_SMALL_SIZE)
	guidance.add_theme_color_override("font_color", ThemeConstants.SECONDARY)
	guidance.autowrap_mode = TextServer.AUTOWRAP_WORD
	col.add_child(guidance)

	var scroll := ScrollContainer.new()
	scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
	scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	col.add_child(scroll)

	var list := VBoxContainer.new()
	list.add_theme_constant_override("separation", 6)
	list.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	scroll.add_child(list)

	var era_id: String = _params.get("era_id", "")
	var available := _get_available_archetypes(era_id)

	for arch in available:
		var arch_id: String = arch["id"]
		var card = load("res://theme/components/tm_card.tscn").instantiate()
		list.add_child(card)
		var content = card.get_content_container()

		# Header row: name + chevron + rare badge
		var header_row := HBoxContainer.new()
		header_row.add_theme_constant_override("separation", 8)
		content.add_child(header_row)

		var name_label := Label.new()
		name_label.text = arch["name"]
		name_label.add_theme_font_override("font", ThemeConstants.font_serif_regular)
		name_label.add_theme_font_size_override("font_size", 21)
		name_label.add_theme_color_override("font_color", ThemeConstants.PRIMARY)
		name_label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		header_row.add_child(name_label)

		var badge := Label.new()
		badge.text = "RARE"
		badge.add_theme_font_override("font", ThemeConstants.font_mono_regular)
		badge.add_theme_font_size_override("font_size", ThemeConstants.ERA_BADGE_SIZE)
		badge.add_theme_color_override("font_color", _accent)
		badge.visible = false
		badge.size_flags_vertical = Control.SIZE_SHRINK_CENTER
		header_row.add_child(badge)
		_archetype_badges[arch_id] = badge

		var chevron := Label.new()
		chevron.text = "\u25b8"
		chevron.add_theme_font_override("font", ThemeConstants.font_mono_regular)
		chevron.add_theme_font_size_override("font_size", 18)
		chevron.add_theme_color_override("font_color", ThemeConstants.TERTIARY)
		chevron.size_flags_vertical = Control.SIZE_SHRINK_CENTER
		header_row.add_child(chevron)
		_archetype_chevrons[arch_id] = chevron

		# One-liner
		var one_liner := Label.new()
		one_liner.text = arch["one_liner"]
		one_liner.add_theme_font_override("font", ThemeConstants.font_mono_regular)
		one_liner.add_theme_font_size_override("font_size", ThemeConstants.BODY_DATA_SMALL_SIZE)
		one_liner.add_theme_color_override("font_color", ThemeConstants.SECONDARY)
		one_liner.autowrap_mode = TextServer.AUTOWRAP_WORD
		content.add_child(one_liner)

		# Expandable detail panel
		var detail_panel := Label.new()
		detail_panel.text = arch["detail"]
		detail_panel.add_theme_font_override("font", ThemeConstants.font_serif_regular)
		detail_panel.add_theme_font_size_override("font_size", ThemeConstants.BODY_DATA_SMALL_SIZE)
		detail_panel.add_theme_color_override("font_color", ThemeConstants.SECONDARY)
		detail_panel.autowrap_mode = TextServer.AUTOWRAP_WORD
		detail_panel.visible = false
		content.add_child(detail_panel)
		_archetype_expand_panels[arch_id] = detail_panel

		card.mouse_filter = Control.MOUSE_FILTER_STOP
		card.gui_input.connect(func(event: InputEvent):
			if event is InputEventMouseButton and event.pressed and event.button_index == MOUSE_BUTTON_LEFT:
				if event.ctrl_pressed or event.meta_pressed:
					_expand_archetype(arch_id)
				else:
					_toggle_rare(arch_id)
		)
		_archetype_cards[arch_id] = card

	_rare_count_label = Label.new()
	_rare_count_label.add_theme_font_override("font", ThemeConstants.font_mono_regular)
	_rare_count_label.add_theme_font_size_override("font_size", ThemeConstants.HINT_TEXT_SIZE)
	_rare_count_label.add_theme_color_override("font_color", ThemeConstants.TERTIARY)
	col.add_child(_rare_count_label)
	_update_rare_count()


func _get_available_archetypes(era_id: String) -> Array:
	if era_id == "roman":
		var filtered: Array = []
		for arch in ALL_ARCHETYPES:
			if arch["id"] in ROMAN_ARCHETYPES:
				filtered.append(arch)
		return filtered
	return ALL_ARCHETYPES


func _select_difficulty(diff_id: String) -> void:
	_selected_difficulty = diff_id
	for i in range(_difficulty_cards.size()):
		var card: PanelContainer = _difficulty_cards[i]
		var style: StyleBoxFlat = card.get_theme_stylebox("panel").duplicate()
		if DIFFICULTIES[i]["id"] == diff_id:
			style.border_color = _accent
			style.set_border_width_all(2)
		else:
			style.border_color = ThemeConstants.BORDER_COLOR
			style.set_border_width_all(1)
		card.add_theme_stylebox_override("panel", style)


func _toggle_rare(arch_id: String) -> void:
	if arch_id in _rare_marks:
		_rare_marks.erase(arch_id)
	elif _rare_marks.size() < MAX_RARE:
		_rare_marks.append(arch_id)
	else:
		return
	_update_archetype_visuals()
	_update_rare_count()


func _expand_archetype(arch_id: String) -> void:
	if _expanded_archetype == arch_id:
		_archetype_expand_panels[arch_id].visible = false
		_archetype_chevrons[arch_id].text = "\u25b8"
		_expanded_archetype = ""
		return

	if _expanded_archetype != "" and _archetype_expand_panels.has(_expanded_archetype):
		_archetype_expand_panels[_expanded_archetype].visible = false
		_archetype_chevrons[_expanded_archetype].text = "\u25b8"

	_archetype_expand_panels[arch_id].visible = true
	_archetype_chevrons[arch_id].text = "\u25be"
	_expanded_archetype = arch_id


func _update_archetype_visuals() -> void:
	for arch_id in _archetype_cards:
		var card: PanelContainer = _archetype_cards[arch_id]
		var is_rare: bool = arch_id in _rare_marks
		_archetype_badges[arch_id].visible = is_rare

		var style: StyleBoxFlat = card.get_theme_stylebox("panel").duplicate()
		if is_rare:
			style.border_color = _accent
			style.set_border_width_all(2)
			card.modulate.a = 0.7
		else:
			style.border_color = ThemeConstants.BORDER_COLOR
			style.set_border_width_all(1)
			card.modulate.a = 1.0
		card.add_theme_stylebox_override("panel", style)


func _update_rare_count() -> void:
	if _rare_marks.is_empty():
		_rare_count_label.text = "No archetypes marked rare"
	else:
		_rare_count_label.text = "%d/%d rare marks used" % [_rare_marks.size(), MAX_RARE]


func _on_confirm() -> void:
	var onboarding_data := {
		"difficulty": _selected_difficulty,
		"rare_marks": _rare_marks.duplicate(),
	}
	var forward_params := _params.duplicate()
	forward_params["onboarding"] = onboarding_data
	SceneRouter.go_to("time_jump", forward_params)
