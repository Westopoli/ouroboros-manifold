extends "res://assets/ascii_animations/ascii_animation_base.gd"

func _run_animation() -> void:
	var center := size / 2.0
	var char_size := 18.0

	# Phase 1: Column characters assemble
	var left_col_x := center.x - 160
	var right_col_x := center.x + 140
	var col_chars := ["|", "\u2551", "\u2502", "|"]
	var arch_chars := ["\u2550", "\u2500", "\u2550"]

	for y_i in range(8):
		var y_pos := center.y - 80 + y_i * char_size
		for col_x in [left_col_x, right_col_x]:
			var ch: String = col_chars[y_i % col_chars.size()]
			var lbl := Label.new()
			lbl.text = ch
			lbl.add_theme_font_override("font", ThemeConstants.font_mono_bold)
			lbl.add_theme_font_size_override("font_size", ThemeConstants.BODY_DATA_SIZE)
			lbl.add_theme_color_override("font_color", _accent_color)
			lbl.position = Vector2(randf_range(0, size.x), randf_range(0, size.y))
			lbl.modulate.a = 0.0
			add_child(lbl)

			var target := Vector2(col_x, y_pos)
			var delay_val := randf_range(0.0, 1.0)
			var tw := create_tween().set_ease(Tween.EASE_OUT).set_trans(Tween.TRANS_CUBIC)
			tw.tween_interval(delay_val)
			tw.tween_property(lbl, "modulate:a", 1.0, 0.3)
			tw.parallel().tween_property(lbl, "position", target, 0.8)

	# Arch across top
	for i in range(12):
		var x_pos := left_col_x + 10 + i * char_size * 0.8
		var ch: String = arch_chars[i % arch_chars.size()]
		var lbl := Label.new()
		lbl.text = ch
		lbl.add_theme_font_override("font", ThemeConstants.font_mono_bold)
		lbl.add_theme_font_size_override("font_size", ThemeConstants.BODY_DATA_SIZE)
		lbl.add_theme_color_override("font_color", _accent_color)
		lbl.position = Vector2(randf_range(0, size.x), randf_range(0, size.y))
		lbl.modulate.a = 0.0
		add_child(lbl)

		var target := Vector2(x_pos, center.y - 90)
		var tw := create_tween().set_ease(Tween.EASE_OUT).set_trans(Tween.TRANS_CUBIC)
		tw.tween_interval(0.8 + i * 0.05)
		tw.tween_property(lbl, "modulate:a", 1.0, 0.3)
		tw.parallel().tween_property(lbl, "position", target, 0.6)

	# Phase 2: "ROMAN ERA" title resolves
	var title_text := "ROMAN ERA"
	var title_start_x := center.x - (title_text.length() * char_size * 0.6) / 2.0
	for i in range(title_text.length()):
		if title_text[i] == " ":
			continue
		var lbl := Label.new()
		lbl.text = title_text[i]
		lbl.add_theme_font_override("font", ThemeConstants.font_serif_regular)
		lbl.add_theme_font_size_override("font_size", 36)
		lbl.add_theme_color_override("font_color", _accent_color)
		lbl.position = center + Vector2(randf_range(-40, 40), randf_range(-40, 40))
		lbl.modulate.a = 0.0
		add_child(lbl)

		var target := Vector2(title_start_x + i * char_size * 0.6, center.y - 20)
		var tw := create_tween().set_ease(Tween.EASE_OUT).set_trans(Tween.TRANS_CUBIC)
		tw.tween_interval(1.5 + i * 0.08)
		tw.tween_property(lbl, "modulate:a", 1.0, 0.3)
		tw.parallel().tween_property(lbl, "position", target, 0.5)

	# Phase 3: Pulse then fade
	var finish_tw := create_tween()
	finish_tw.tween_interval(3.0)
	finish_tw.tween_callback(func():
		var fade := create_tween()
		for child in get_children():
			var ftw := create_tween()
			ftw.tween_property(child, "modulate:a", 0.0, 0.5)
		fade.tween_interval(0.6)
		fade.tween_callback(_finish)
	)
