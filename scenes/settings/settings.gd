extends Control

const RESOLUTIONS := [
	Vector2i(1280, 720),
	Vector2i(1600, 900),
	Vector2i(1920, 1080),
	Vector2i(2560, 1440),
	Vector2i(3440, 1440),
	Vector2i(3840, 2160),
]

var _settings: Dictionary = {}

func _ready() -> void:
	_settings = UIDataBus.get_settings()
	_build_ui()


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
	header.text = "SETTINGS"
	header.uppercase = true
	header.add_theme_font_override("font", ThemeConstants.font_mono_regular)
	header.add_theme_font_size_override("font_size", ThemeConstants.CLASSIFICATION_LABEL_SIZE)
	header.add_theme_color_override("font_color", ThemeConstants.TERTIARY)
	outer.add_child(header)

	var divider_scene = load("res://theme/components/tm_divider.tscn")
	var divider = divider_scene.instantiate()
	outer.add_child(divider)

	var scroll := ScrollContainer.new()
	scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
	outer.add_child(scroll)

	var cards := VBoxContainer.new()
	cards.add_theme_constant_override("separation", 16)
	cards.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	scroll.add_child(cards)

	_build_display_card(cards)
	_build_camera_card(cards)
	_build_audio_card(cards)
	_build_keybinds_card(cards)

	var footer := HBoxContainer.new()
	footer.add_theme_constant_override("separation", 12)
	outer.add_child(footer)

	var apply_btn = load("res://theme/components/tm_button.tscn").instantiate()
	apply_btn.text = "APPLY"
	apply_btn.pressed.connect(func():
		UIDataBus.save_settings(_settings)
	)
	footer.add_child(apply_btn)

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


func _build_display_card(parent: Control) -> void:
	var card = load("res://theme/components/tm_card.tscn").instantiate()
	card.card_title = "DISPLAY"
	parent.add_child(card)
	var content = card.get_content_container()

	var res_row := HBoxContainer.new()
	res_row.add_theme_constant_override("separation", 12)
	content.add_child(res_row)
	var res_label := Label.new()
	res_label.text = "Resolution"
	res_label.add_theme_font_override("font", ThemeConstants.font_mono_regular)
	res_label.add_theme_font_size_override("font_size", ThemeConstants.BODY_DATA_SIZE)
	res_label.add_theme_color_override("font_color", ThemeConstants.SECONDARY)
	res_label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	res_row.add_child(res_label)

	var res_option := OptionButton.new()
	for i in range(RESOLUTIONS.size()):
		var r = RESOLUTIONS[i]
		res_option.add_item("%dx%d" % [r.x, r.y], i)
	res_option.selected = _settings.get("resolution_index", 2)
	res_option.item_selected.connect(func(idx: int):
		_settings["resolution_index"] = idx
		var r = RESOLUTIONS[idx]
		DisplayServer.window_set_size(r)
	)
	res_row.add_child(res_option)

	_add_toggle(content, "Fullscreen", _settings.get("fullscreen", false), func(toggled: bool):
		_settings["fullscreen"] = toggled
		if toggled:
			DisplayServer.window_set_mode(DisplayServer.WINDOW_MODE_FULLSCREEN)
		else:
			DisplayServer.window_set_mode(DisplayServer.WINDOW_MODE_WINDOWED)
	)

	_add_toggle(content, "VSync", _settings.get("vsync", true), func(toggled: bool):
		_settings["vsync"] = toggled
		if toggled:
			DisplayServer.window_set_vsync_mode(DisplayServer.VSYNC_ENABLED)
		else:
			DisplayServer.window_set_vsync_mode(DisplayServer.VSYNC_DISABLED)
	)


func _build_camera_card(parent: Control) -> void:
	var card = load("res://theme/components/tm_card.tscn").instantiate()
	card.card_title = "CAMERA"
	parent.add_child(card)
	var content = card.get_content_container()

	_add_slider(content, "Pan Speed", float(_settings.get("pan_speed", 1.0)), func(val: float) -> void:
		_settings["pan_speed"] = val
	, 0.5, 2.0, 0.1)


func _build_audio_card(parent: Control) -> void:
	var card = load("res://theme/components/tm_card.tscn").instantiate()
	card.card_title = "AUDIO"
	parent.add_child(card)
	var content = card.get_content_container()

	var bus_map := {
		"Master Volume": "master_volume",
		"Music Volume": "music_volume",
		"SFX Volume": "sfx_volume",
		"Narration Volume": "narration_volume",
	}

	var bus_names := ["Master", "Music", "SFX", "Narration"]
	var keys := bus_map.keys()
	for i in range(keys.size()):
		var display_name: String = keys[i]
		var settings_key: String = bus_map[display_name]
		var bus_name: String = bus_names[i]
		_add_slider(content, display_name, _settings.get(settings_key, 80), func(val: float) -> void:
			_settings[settings_key] = int(val)
			var bus_idx := AudioServer.get_bus_index(bus_name)
			if bus_idx >= 0:
				AudioServer.set_bus_volume_db(bus_idx, linear_to_db(val / 100.0))
		)


func _build_keybinds_card(parent: Control) -> void:
	var card = load("res://theme/components/tm_card.tscn").instantiate()
	card.card_title = "KEYBINDS"
	parent.add_child(card)
	var content = card.get_content_container()

	var binds := [
		["Select", "LMB"],
		["Box Select", "LMB Drag"],
		["Move", "RMB"],
		["Attack Move", "A, then left-click"],
		["Stop", "S"],
		["Control Group Assign", "Ctrl+1-9"],
		["Control Group Select", "1-9"],
		["All Army", "F1"],
		["Ability", "P"],
		["Layer Up", "Q"],
		["Layer Down", "E"],
		["Sensor Pulse", "Space"],
	]

	for bind in binds:
		var row := HBoxContainer.new()
		row.add_theme_constant_override("separation", 12)
		content.add_child(row)

		var action_label := Label.new()
		action_label.text = bind[0]
		action_label.add_theme_font_override("font", ThemeConstants.font_mono_regular)
		action_label.add_theme_font_size_override("font_size", ThemeConstants.BODY_DATA_SIZE)
		action_label.add_theme_color_override("font_color", ThemeConstants.SECONDARY)
		action_label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		row.add_child(action_label)

		var key_label := Label.new()
		key_label.text = bind[1]
		key_label.add_theme_font_override("font", ThemeConstants.font_mono_regular)
		key_label.add_theme_font_size_override("font_size", ThemeConstants.BODY_DATA_SIZE)
		key_label.add_theme_color_override("font_color", ThemeConstants.PRIMARY)
		row.add_child(key_label)

	var note := Label.new()
	note.text = "Keybind customization coming soon."
	note.add_theme_font_override("font", ThemeConstants.font_mono_regular)
	note.add_theme_font_size_override("font_size", ThemeConstants.HINT_TEXT_SIZE)
	note.add_theme_color_override("font_color", ThemeConstants.TERTIARY)
	content.add_child(note)


func _add_toggle(parent: Control, label_text: String, initial: bool, callback: Callable) -> void:
	var row := HBoxContainer.new()
	row.add_theme_constant_override("separation", 12)
	parent.add_child(row)

	var label := Label.new()
	label.text = label_text
	label.add_theme_font_override("font", ThemeConstants.font_mono_regular)
	label.add_theme_font_size_override("font_size", ThemeConstants.BODY_DATA_SIZE)
	label.add_theme_color_override("font_color", ThemeConstants.SECONDARY)
	label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	row.add_child(label)

	var toggle := CheckButton.new()
	toggle.button_pressed = initial
	toggle.toggled.connect(callback)
	row.add_child(toggle)


func _add_slider(parent: Control, label_text: String, initial: float, callback: Callable, min_v := 0.0, max_v := 100.0, step := 1.0) -> void:
	var pct := max_v == 100.0
	var row := HBoxContainer.new()
	row.add_theme_constant_override("separation", 12)
	parent.add_child(row)

	var label := Label.new()
	label.text = label_text
	label.add_theme_font_override("font", ThemeConstants.font_mono_regular)
	label.add_theme_font_size_override("font_size", ThemeConstants.BODY_DATA_SIZE)
	label.add_theme_color_override("font_color", ThemeConstants.SECONDARY)
	label.custom_minimum_size.x = 160
	row.add_child(label)

	var slider := HSlider.new()
	slider.min_value = min_v
	slider.max_value = max_v
	slider.step = step
	slider.value = initial
	slider.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	slider.custom_minimum_size.x = 200
	row.add_child(slider)

	var val_label := Label.new()
	val_label.text = ("%d%%" % int(initial)) if pct else "%.1fx" % initial
	val_label.add_theme_font_override("font", ThemeConstants.font_mono_regular)
	val_label.add_theme_font_size_override("font_size", ThemeConstants.BODY_DATA_SIZE)
	val_label.add_theme_color_override("font_color", ThemeConstants.PRIMARY)
	val_label.custom_minimum_size.x = 40
	row.add_child(val_label)

	slider.value_changed.connect(func(val: float):
		val_label.text = ("%d%%" % int(val)) if pct else "%.1fx" % val
		callback.call(val)
	)


func qa_state() -> Dictionary:
	return {
		"scene": "settings",
		"tick": -1,
		"resolution_index": int(_settings.get("resolution_index", 2)),
		"fullscreen": bool(_settings.get("fullscreen", false)),
		"vsync": bool(_settings.get("vsync", true)),
		"plants": [],
	}
