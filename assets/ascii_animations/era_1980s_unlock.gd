extends "res://assets/ascii_animations/ascii_animation_base.gd"

func _run_animation() -> void:
	var center := size / 2.0
	var char_size := 18.0

	# Phase 1: Ocean waves build from bottom
	var wave_chars := ["~", "\u2248", "~", "\u2248"]
	var wave_labels: Array[Label] = []
	for row in range(6):
		var y_pos := size.y - 60 - row * 20
		var opacity := 1.0 - row * 0.12
		for col in range(30):
			var x_pos := col * char_size - 20
			var ch: String = wave_chars[(col + row) % wave_chars.size()]
			var lbl := Label.new()
			lbl.text = ch
			lbl.add_theme_font_override("font", ThemeConstants.font_mono_regular)
			lbl.add_theme_font_size_override("font_size", ThemeConstants.BODY_DATA_SIZE)
			lbl.add_theme_color_override("font_color", _accent_color)
			lbl.position = Vector2(x_pos, y_pos)
			lbl.modulate.a = 0.0
			add_child(lbl)
			wave_labels.append(lbl)

			var tw := create_tween()
			var delay_val := 0.1 + row * 0.15 + randf_range(0, 0.1)
			tw.tween_interval(delay_val)
			tw.tween_property(lbl, "modulate:a", opacity, 0.3)

			# Oscillation
			var wave_tw := create_tween().set_loops(6)
			wave_tw.tween_interval(delay_val + 0.3)
			wave_tw.tween_property(lbl, "position:x", x_pos + sin(col * 0.5) * 4, 0.8)
			wave_tw.tween_property(lbl, "position:x", x_pos - sin(col * 0.5) * 4, 0.8)

	# Phase 2: Submarine surfaces
	var sub_lines := [
		"      \u25ac\u25ac",
		"  \u250c\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2510",
		"\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u25cb",
		"  \u2514\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2518",
	]
	var sub_start_y := size.y - 40
	for line_i in range(sub_lines.size()):
		var line_text: String = sub_lines[line_i]
		var lbl := Label.new()
		lbl.text = line_text
		lbl.add_theme_font_override("font", ThemeConstants.font_mono_bold)
		lbl.add_theme_font_size_override("font_size", ThemeConstants.BODY_DATA_SIZE)
		lbl.add_theme_color_override("font_color", _accent_color)
		lbl.position = Vector2(center.x - 100, sub_start_y + line_i * 20)
		lbl.modulate.a = 0.0
		add_child(lbl)

		var target_y := center.y + 20 + line_i * 20
		var tw := create_tween().set_ease(Tween.EASE_OUT).set_trans(Tween.TRANS_CUBIC)
		tw.tween_interval(1.5)
		tw.tween_property(lbl, "modulate:a", 1.0, 0.4)
		tw.parallel().tween_property(lbl, "position:y", target_y, 1.0)

	# Phase 2.5: Title
	var title_text := "1980s"
	var title_start_x := center.x - (title_text.length() * char_size * 0.7) / 2.0
	for i in range(title_text.length()):
		var lbl := Label.new()
		lbl.text = title_text[i]
		lbl.add_theme_font_override("font", ThemeConstants.font_mono_bold)
		lbl.add_theme_font_size_override("font_size", 36)
		lbl.add_theme_color_override("font_color", _accent_color)
		lbl.position = Vector2(title_start_x + i * char_size * 0.7, center.y - 30)
		lbl.modulate.a = 0.0
		add_child(lbl)

		var tw := create_tween().set_ease(Tween.EASE_OUT).set_trans(Tween.TRANS_CUBIC)
		tw.tween_interval(2.2 + i * 0.08)
		tw.tween_property(lbl, "modulate:a", 1.0, 0.3)

	# Phase 3: Fade
	var finish_tw := create_tween()
	finish_tw.tween_interval(3.2)
	finish_tw.tween_callback(func():
		for child in get_children():
			var ftw := create_tween()
			ftw.tween_property(child, "modulate:a", 0.0, 0.5)
		var end := create_tween()
		end.tween_interval(0.6)
		end.tween_callback(_finish)
	)
