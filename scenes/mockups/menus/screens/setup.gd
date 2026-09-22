extends Control

const Palette := preload("res://scenes/mockups/menus/theme.gd")

const DIFFICULTIES := [
	{"id": "easy", "label": "Easy", "prose": "Forgiving consequences. More time, more room to recover from mistakes."},
	{"id": "medium", "label": "Medium", "prose": "The intended experience. Fair consequences, balanced resources."},
	{"id": "hard", "label": "Hard", "prose": "Punishing consequences. Every loss compounds; the enemy never gets stronger, you just cannot afford to stumble."},
]

var root
var _cards: Dictionary = {}
var _begin_btn: Button
var _selected := ""


func _ready() -> void:
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	_build()


func _build() -> void:
	var content := VBoxContainer.new()
	content.anchor_left = 0.12
	content.anchor_top = 0.18
	content.anchor_right = 0.88
	content.anchor_bottom = 0.85
	content.add_theme_constant_override("separation", 18)
	add_child(content)

	var header := Label.new()
	header.text = "Before your first chapter"
	header.add_theme_font_override("font", Palette.serif_regular())
	header.add_theme_font_size_override("font_size", Palette.SUBTITLE_SIZE + 6)
	header.add_theme_color_override("font_color", Palette.PRIMARY)
	content.add_child(header)

	var row := HBoxContainer.new()
	row.add_theme_constant_override("separation", 20)
	content.add_child(row)
	for d in DIFFICULTIES:
		row.add_child(_build_card(d))

	var note := Label.new()
	note.text = "Mission preferences come later. This choice is made once, at the beginning of the history."
	note.add_theme_font_override("font", Palette.mono_regular())
	note.add_theme_font_size_override("font_size", Palette.HINT_TEXT_SIZE)
	note.add_theme_color_override("font_color", Palette.TERTIARY)
	content.add_child(note)

	var footer := HBoxContainer.new()
	footer.add_theme_constant_override("separation", 12)
	content.add_child(footer)

	_begin_btn = Button.new()
	_begin_btn.text = "Begin"
	_begin_btn.disabled = true
	_begin_btn.focus_mode = Control.FOCUS_NONE
	_begin_btn.add_theme_font_override("font", Palette.mono_medium())
	_begin_btn.pressed.connect(func(): root.qa_go("begin"))
	footer.add_child(_begin_btn)

	var back_btn := Button.new()
	back_btn.text = "Back"
	back_btn.flat = true
	back_btn.focus_mode = Control.FOCUS_NONE
	back_btn.add_theme_font_override("font", Palette.mono_regular())
	back_btn.pressed.connect(func(): root.qa_go("back"))
	footer.add_child(back_btn)


func _build_card(d: Dictionary) -> PanelContainer:
	var panel := PanelContainer.new()
	panel.custom_minimum_size = Vector2(220, 0)
	var style := StyleBoxFlat.new()
	style.bg_color = Palette.CARD
	style.set_border_width_all(1)
	style.border_color = Color(1, 1, 1, 0.08)
	style.content_margin_left = 14
	style.content_margin_right = 14
	style.content_margin_top = 12
	style.content_margin_bottom = 12
	panel.add_theme_stylebox_override("panel", style)

	var box := VBoxContainer.new()
	panel.add_child(box)

	var btn := Button.new()
	btn.text = String(d.label)
	btn.flat = true
	btn.focus_mode = Control.FOCUS_NONE
	btn.add_theme_font_override("font", Palette.mono_medium())
	btn.add_theme_font_size_override("font_size", 20)
	btn.add_theme_color_override("font_color", Palette.PRIMARY)
	var id: String = String(d.id)
	btn.pressed.connect(func(): root.qa_go("pick_%s" % id))
	box.add_child(btn)

	var prose := Label.new()
	prose.text = String(d.prose)
	prose.autowrap_mode = TextServer.AUTOWRAP_WORD
	prose.custom_minimum_size = Vector2(200, 0)
	prose.add_theme_font_override("font", Palette.serif_regular())
	prose.add_theme_font_size_override("font_size", Palette.BODY_DATA_SIZE)
	prose.add_theme_color_override("font_color", Palette.SECONDARY)
	box.add_child(prose)

	_cards[id] = panel
	return panel


func select_external(id: String) -> void:
	_selected = id
	_begin_btn.disabled = false
	for cid in _cards.keys():
		var panel: PanelContainer = _cards[cid]
		var style: StyleBoxFlat = panel.get_theme_stylebox("panel").duplicate()
		style.border_color = Palette.ACCENT if cid == id else Color(1, 1, 1, 0.08)
		style.set_border_width_all(2 if cid == id else 1)
		panel.add_theme_stylebox_override("panel", style)


func refresh(_state: Dictionary) -> void:
	_selected = ""
	_begin_btn.disabled = true
	for cid in _cards.keys():
		var panel: PanelContainer = _cards[cid]
		var style: StyleBoxFlat = panel.get_theme_stylebox("panel").duplicate()
		style.border_color = Color(1, 1, 1, 0.08)
		style.set_border_width_all(1)
		panel.add_theme_stylebox_override("panel", style)
