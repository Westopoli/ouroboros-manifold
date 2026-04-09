extends "res://assets/ascii_animations/ascii_animation_base.gd"

func _run_animation() -> void:
	var center := size / 2.0
	var char_size := 18.0

	# Phase 1: Starfield assembles
	var star_chars := [".", "\u00b7", "*", "\u2726"]
	var star_labels: Array[Label] = []
	for i in range(80):
		var lbl := Label.new()
		lbl.text = star_chars[randi() % star_chars.size()]
		lbl.add_theme_font_override("font", ThemeConstants.font_mono_regular)
		lbl.add_theme_font_size_override("font_size", ThemeConstants.BODY_DATA_SMALL_SIZE)
		lbl.add_theme_color_override("font_color", _accent_color)
		lbl.position = Vector2(randf_range(20, size.x - 20), randf_range(20, size.y - 20))
		lbl.modulate.a = 0.0
		add_child(lbl)
		star_labels.append(lbl)

		var tw := create_tween()
		tw.tween_interval(randf_range(0.0, 1.2))
		tw.tween_property(lbl, "modulate:a", randf_range(0.3, 1.0), 0.4)

		# Twinkling
		if randf() > 0.6:
			var twinkle := create_tween().set_loops(3)
			twinkle.tween_interval(randf_range(0.5, 1.5))
			twinkle.tween_property(lbl, "modulate:a", 0.2, 0.3)
			twinkle.tween_property(lbl, "modulate:a", 0.8, 0.3)

	# Phase 2: Horizontal line draws, stars part, title resolves
	var line_chars := ["\u2500", "\u2550", "\u2501"]
	for i in range(20):
		var x_pos := center.x - 180 + i * char_size
		var ch: String = line_chars[i % line_chars.size()]
		var lbl := Label.new()
		lbl.text = ch
		lbl.add_theme_font_override("font", ThemeConstants.font_mono_regular)
		lbl.add_theme_font_size_override("font_size", ThemeConstants.BODY_DATA_SIZE)
		lbl.add_theme_color_override("font_color", _accent_color)
		lbl.position = Vector2(x_pos, center.y)
		lbl.modulate.a = 0.0
		add_child(lbl)

		var tw := create_tween()
		tw.tween_interval(1.5 + i * 0.04)
		tw.tween_property(lbl, "modulate:a", 1.0, 0.2)

	var title_text := "SETTLED REACH"
	var title_start_x := center.x - (title_text.length() * char_size * 0.55) / 2.0
	for i in range(title_text.length()):
		if title_text[i] == " ":
			continue
		var lbl := Label.new()
		lbl.text = title_text[i]
		lbl.add_theme_font_override("font", ThemeConstants.font_serif_regular)
		lbl.add_theme_font_size_override("font_size", 36)
		lbl.add_theme_color_override("font_color", _accent_color)
		lbl.modulate.a = 0.0
		lbl.position = Vector2(title_start_x + i * char_size * 0.55, center.y - 40)
		add_child(lbl)

		var tw := create_tween().set_ease(Tween.EASE_OUT).set_trans(Tween.TRANS_CUBIC)
		tw.tween_interval(1.8 + i * 0.06)
		tw.tween_property(lbl, "modulate:a", 1.0, 0.4)

	# Phase 3: Fade out
	var finish_tw := create_tween()
	finish_tw.tween_interval(3.0)
	finish_tw.tween_callback(func():
		for child in get_children():
			var ftw := create_tween()
			ftw.tween_property(child, "modulate:a", 0.0, 0.5)
		var end := create_tween()
		end.tween_interval(0.6)
		end.tween_callback(_finish)
	)
