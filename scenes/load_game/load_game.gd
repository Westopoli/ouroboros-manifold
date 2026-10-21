extends Control

const SimSession := preload("res://autoload/sim_session.gd")

const CURRENT_SAVE_VERSION := 12

var _slot_list: VBoxContainer
var _empty_label: Label
var _confirm_overlay: Control

var _bridge = null
var _bridge_rows: Array = []

func _ready() -> void:
	_build_ui()
	qa_set_bridge(SimSession.bridge())


func _input(event: InputEvent) -> void:
	if event.is_action_pressed("ui_cancel"):
		if _confirm_overlay and _confirm_overlay.visible:
			_confirm_overlay.visible = false
		else:
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
	header.text = "CONTINUE"
	header.uppercase = true
	header.add_theme_font_override("font", ThemeConstants.font_mono_regular)
	header.add_theme_font_size_override("font_size", ThemeConstants.CLASSIFICATION_LABEL_SIZE)
	header.add_theme_color_override("font_color", ThemeConstants.TERTIARY)
	outer.add_child(header)

	var divider = load("res://theme/components/tm_divider.tscn").instantiate()
	outer.add_child(divider)

	var scroll := ScrollContainer.new()
	scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
	outer.add_child(scroll)

	_slot_list = VBoxContainer.new()
	_slot_list.add_theme_constant_override("separation", 8)
	_slot_list.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	scroll.add_child(_slot_list)

	_empty_label = Label.new()
	_empty_label.text = "No saved campaigns. Start a new game to begin."
	_empty_label.add_theme_font_override("font", ThemeConstants.font_serif_regular)
	_empty_label.add_theme_font_size_override("font_size", 21)
	_empty_label.add_theme_color_override("font_color", ThemeConstants.SECONDARY)
	_empty_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_empty_label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_slot_list.add_child(_empty_label)

	var footer := HBoxContainer.new()
	footer.add_theme_constant_override("separation", 12)
	outer.add_child(footer)

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


func qa_set_bridge(bridge) -> void:
	_bridge = bridge
	_bridge_rows = []
	for entry in _bridge.list_saves():
		var slot: String = str(entry.get("slot", ""))
		var tick: int = int(entry.get("tick", 0))
		var chapter: int = int(entry.get("chapter", 0))
		var version: int = int(entry.get("version", 0))
		var refused: bool = version != CURRENT_SAVE_VERSION
		var label_text: String
		if refused:
			label_text = "Chapter %d — build v%d, save v%d — incompatible" % [chapter, CURRENT_SAVE_VERSION, version]
		else:
			label_text = "Chapter %d" % chapter
		_bridge_rows.append({
			"slot": slot,
			"tick": tick,
			"chapter": chapter,
			"version": version,
			"refused": refused,
			"label_text": label_text,
		})
	_render_bridge_rows()


# Replaces the legacy UIDataBus cards with one row per bridge slot: the row
# text, and a LOAD button (disabled for a refused save) that loads the slot
# through the bridge and, once loaded, opens the galaxy on that world (the
# shared session keeps it); a refusal is shown on the row.
func _render_bridge_rows() -> void:
	for child in _slot_list.get_children():
		if child != _empty_label:
			child.queue_free()
	_empty_label.visible = _bridge_rows.is_empty()
	for row in _bridge_rows:
		var box := HBoxContainer.new()
		box.add_theme_constant_override("separation", 12)
		var label := Label.new()
		label.text = String(row["label_text"])
		label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		box.add_child(label)
		var load_btn := Button.new()
		load_btn.text = "LOAD"
		load_btn.disabled = bool(row["refused"])
		var slot_id: String = row["slot"]
		load_btn.name = "Load_" + slot_id
		load_btn.pressed.connect(func():
			var snap: Dictionary = _bridge.load(slot_id)
			if snap.is_empty():
				label.text = "%s -- %s" % [row["label_text"], _bridge.last_error()]
			else:
				SceneRouter.go_to("galaxy")
		)
		box.add_child(load_btn)
		_slot_list.add_child(box)


func qa_state() -> Dictionary:
	return {
		"scene": "load_game",
		"tick": -1,
		"slot_count": _bridge_rows.size(),
		"current_version": CURRENT_SAVE_VERSION,
		"has_save_button": false,
		"rows": _bridge_rows,
		"plants": [],
	}


func qa_load_slot(slot_id: String) -> Dictionary:
	return _bridge.load(slot_id)
