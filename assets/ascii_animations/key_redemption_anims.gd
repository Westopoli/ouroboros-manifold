extends "res://assets/ascii_animations/ascii_animation_base.gd"

var _variant: int = -1

func play_random() -> void:
	_variant = randi() % 5
	play()


func _run_animation() -> void:
	if _variant < 0:
		_variant = randi() % 5

	match _variant:
		0: _anim_wink()
		1: _anim_key_unlock()
		2: _anim_slot_machine()
		3: _anim_code_spiral()
		4: _anim_unfurl()


func _anim_wink() -> void:
	var center := size / 2.0
	var face_parts := [
		{ch = ";", offset = Vector2(-30, -10)},
		{ch = "-", offset = Vector2(0, 0)},
		{ch = ")", offset = Vector2(20, -10)},
	]
	for i in range(face_parts.size()):
		var part: Dictionary = face_parts[i]
		var lbl := Label.new()
		lbl.text = part["ch"]
		lbl.add_theme_font_override("font", ThemeConstants.font_mono_bold)
		lbl.add_theme_font_size_override("font_size", 48)
		lbl.add_theme_color_override("font_color", _accent_color)
		var target: Vector2 = center + part["offset"]
		lbl.position = Vector2(randf_range(0, size.x), randf_range(0, size.y))
		lbl.modulate.a = 0.0
		add_child(lbl)

		var tw := create_tween().set_ease(Tween.EASE_OUT).set_trans(Tween.TRANS_CUBIC)
		tw.tween_interval(0.1 + i * 0.2)
		tw.tween_property(lbl, "modulate:a", 1.0, 0.2)
		tw.parallel().tween_property(lbl, "position", target, 0.4)

	var finish_tw := create_tween()
	finish_tw.tween_interval(1.5)
	finish_tw.tween_callback(_fade_and_finish)


func _anim_key_unlock() -> void:
	var center := size / 2.0
	var key_lines := [
		"\u2554\u2550\u2550\u2557",
		"\u2551  \u2551",
		"\u255a\u2550\u2550\u255d\u2500\u2500\u2500",
	]
	for i in range(key_lines.size()):
		var lbl := Label.new()
		lbl.text = key_lines[i]
		lbl.add_theme_font_override("font", ThemeConstants.font_mono_bold)
		lbl.add_theme_font_size_override("font_size", 24)
		lbl.add_theme_color_override("font_color", _accent_color)
		lbl.position = Vector2(center.x - 60, center.y - 30 + i * 24)
		lbl.modulate.a = 0.0
		add_child(lbl)

		var tw := create_tween().set_ease(Tween.EASE_OUT).set_trans(Tween.TRANS_CUBIC)
		tw.tween_interval(i * 0.15)
		tw.tween_property(lbl, "modulate:a", 1.0, 0.3)

	# Burst after key assembles
	var burst_tw := create_tween()
	burst_tw.tween_interval(0.8)
	burst_tw.tween_callback(func():
		particle_burst(center, [".", "*", "\u00b7", "\u2726"], 20, 120, 0.6)
	)

	var finish_tw := create_tween()
	finish_tw.tween_interval(1.8)
	finish_tw.tween_callback(_fade_and_finish)


func _anim_slot_machine() -> void:
	var center := size / 2.0
	var random_chars := "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789@#$%&"
	var lbl := Label.new()
	lbl.text = "?"
	lbl.add_theme_font_override("font", ThemeConstants.font_mono_bold)
	lbl.add_theme_font_size_override("font_size", 48)
	lbl.add_theme_color_override("font_color", _accent_color)
	lbl.position = center - Vector2(15, 25)
	add_child(lbl)

	var cycle_tw := create_tween()
	for i in range(20):
		var ch := random_chars[randi() % random_chars.length()]
		cycle_tw.tween_callback(func(): lbl.text = ch)
		cycle_tw.tween_interval(0.05 + i * 0.005)

	cycle_tw.tween_callback(func():
		lbl.text = "\u2713"
		lbl.add_theme_color_override("font_color", ThemeConstants.HEALTHY)
		particle_burst(center, [".", "*"], 15, 80, 0.5)
	)

	var finish_tw := create_tween()
	finish_tw.tween_interval(1.8)
	finish_tw.tween_callback(_fade_and_finish)


func _anim_code_spiral() -> void:
	var center := size / 2.0
	var chars := "ABCDEFGH12345"
	var count := chars.length()

	for i in range(count):
		var angle := (float(i) / count) * TAU
		var radius := 80.0
		var target := center + Vector2(cos(angle), sin(angle)) * radius

		var lbl := Label.new()
		lbl.text = chars[i]
		lbl.add_theme_font_override("font", ThemeConstants.font_mono_bold)
		lbl.add_theme_font_size_override("font_size", 24)
		lbl.add_theme_color_override("font_color", _accent_color)
		lbl.position = center
		lbl.modulate.a = 0.0
		add_child(lbl)

		var tw := create_tween().set_ease(Tween.EASE_OUT).set_trans(Tween.TRANS_CUBIC)
		tw.tween_interval(i * 0.06)
		tw.tween_property(lbl, "modulate:a", 1.0, 0.2)
		tw.parallel().tween_property(lbl, "position", target, 0.5)

	# Collapse into checkmark
	var collapse_tw := create_tween()
	collapse_tw.tween_interval(1.0)
	collapse_tw.tween_callback(func():
		for child in get_children():
			var ctw := create_tween().set_ease(Tween.EASE_IN).set_trans(Tween.TRANS_CUBIC)
			ctw.tween_property(child, "position", center, 0.3)
			ctw.tween_property(child, "modulate:a", 0.0, 0.1)

		var check := Label.new()
		check.text = "\u2713"
		check.add_theme_font_override("font", ThemeConstants.font_mono_bold)
		check.add_theme_font_size_override("font_size", 48)
		check.add_theme_color_override("font_color", ThemeConstants.HEALTHY)
		check.position = center - Vector2(15, 25)
		check.modulate.a = 0.0
		add_child(check)

		var show := create_tween()
		show.tween_interval(0.35)
		show.tween_property(check, "modulate:a", 1.0, 0.2)
	)

	var finish_tw := create_tween()
	finish_tw.tween_interval(1.8)
	finish_tw.tween_callback(_fade_and_finish)


func _anim_unfurl() -> void:
	var center := size / 2.0
	var line_width := 24

	# Horizontal line draws
	for i in range(line_width):
		var lbl := Label.new()
		lbl.text = "\u2500"
		lbl.add_theme_font_override("font", ThemeConstants.font_mono_regular)
		lbl.add_theme_font_size_override("font_size", ThemeConstants.BODY_DATA_SIZE)
		lbl.add_theme_color_override("font_color", _accent_color)
		lbl.position = Vector2(center.x - (line_width * 9) / 2.0 + i * 9, center.y)
		lbl.modulate.a = 0.0
		add_child(lbl)

		var tw := create_tween()
		tw.tween_interval(i * 0.03)
		tw.tween_property(lbl, "modulate:a", 1.0, 0.1)

	# Vertical frame unfurls
	var frame_delay := line_width * 0.03 + 0.2
	var left_x := center.x - (line_width * 9) / 2.0
	var right_x := center.x + (line_width * 9) / 2.0 - 9

	for j in range(4):
		for side_x in [left_x, right_x]:
			var lbl := Label.new()
			lbl.text = "\u2502"
			lbl.add_theme_font_override("font", ThemeConstants.font_mono_regular)
			lbl.add_theme_font_size_override("font_size", ThemeConstants.BODY_DATA_SIZE)
			lbl.add_theme_color_override("font_color", _accent_color)
			lbl.position = Vector2(side_x, center.y + (j + 1) * 18)
			lbl.modulate.a = 0.0
			add_child(lbl)

			var tw := create_tween()
			tw.tween_interval(frame_delay + j * 0.08)
			tw.tween_property(lbl, "modulate:a", 1.0, 0.15)

	var finish_tw := create_tween()
	finish_tw.tween_interval(1.5)
	finish_tw.tween_callback(_fade_and_finish)


func _fade_and_finish() -> void:
	for child in get_children():
		var tw := create_tween()
		tw.tween_property(child, "modulate:a", 0.0, 0.3)
	var end := create_tween()
	end.tween_interval(0.4)
	end.tween_callback(_finish)
