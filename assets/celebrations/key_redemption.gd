extends "res://assets/celebrations/celebration_base.gd"

var _variant: int = -1
var _input_center: Vector2 = Vector2.ZERO
var _key_code: String = ""

func play_key_redemption(era_id: String, center_pos: Vector2, code: String) -> void:
	_input_center = center_pos
	_key_code = code
	_variant = randi() % 3
	play(era_id)


func _get_shader() -> Shader:
	return null


func _get_glyph_set() -> Array:
	return ["\u2713", "\u2714", "\u26a1", "\u2726", "\u2727", "\u00b7", "\u2722", "\u2733", "\u273b", "\u273d"]


func _get_title_text() -> String:
	return ""


func _run_sequence() -> void:
	var center := _input_center if _input_center != Vector2.ZERO else size / 2.0
	var glyphs := _get_glyph_set()

	match _variant:
		0: _variant_bloom_burst(center, glyphs)
		1: _variant_departure_board(center, glyphs)
		2: _variant_cascade_unlock(center, glyphs)


func _variant_bloom_burst(center: Vector2, glyphs: Array) -> void:
	# Background dot field fades in first
	bloom_scatter(center, ["\u00b7"], 20, 200, 0.0, 1.5, 0.15)
	bloom_scatter(center, ["\u00b7"], 15, 140, 0.1, 1.4, 0.12)

	# Inner ring — dots, fires first
	bloom_ring(center, ["\u00b7", "\u00b7", "\u2727", "\u00b7", "\u00b7"], 5, 30, 0.0, 0.6)
	# Middle ring — mixed glyphs
	bloom_ring(center, glyphs.slice(4, 8), 8, 60, 0.1, 0.8)
	# Outer ring — full glyphs, fires last
	bloom_ring(center, glyphs.slice(3), 12, 100, 0.2, 0.9)

	# 4 cardinal dot lines radiating outward from center
	var dirs: Array[Vector2] = [Vector2(0, -1), Vector2(0, 1), Vector2(1, 0), Vector2(-1, 0)]
	for dir in dirs:
		for d in range(4):
			var pos := center + dir * (40 + d * 20)
			var lbl := _make_glyph("\u00b7", pos - Vector2(4, 6))
			var tw := create_tween().set_ease(Tween.EASE_OUT).set_trans(Tween.TRANS_CUBIC)
			tw.tween_interval(0.15 + d * 0.06)
			tw.tween_property(lbl, "modulate:a", 0.5, 0.1)
			tw.tween_interval(0.4)
			tw.tween_property(lbl, "modulate:a", 0.0, 0.3)

	# Checkmark with bounce: 0 → 1.5 → 0.95 → 1.0
	var check := _make_glyph("\u2713", center - Vector2(12, 18), 36, Color.TRANSPARENT, true)
	check.scale = Vector2(0.0, 0.0)
	check.pivot_offset = Vector2(12, 18)

	var tw := create_tween().set_ease(Tween.EASE_OUT).set_trans(Tween.TRANS_CUBIC)
	tw.tween_interval(0.3)
	tw.tween_property(check, "modulate:a", 1.0, 0.1)
	tw.parallel().tween_property(check, "scale", Vector2(1.5, 1.5), 0.15)
	tw.tween_property(check, "scale", Vector2(0.95, 0.95), 0.08)
	tw.tween_property(check, "scale", Vector2(1.0, 1.0), 0.07)

	# Shockwave ring after checkmark lands
	bloom_ring(center, ["\u2726", "\u2727"], 8, 80, 0.55, 0.6)

	# Secondary scatter burst on check bounce
	bloom_scatter(center, glyphs.slice(3, 7), 12, 100, 0.5, 0.8, 0.5)

	# Orbiting dots around the checkmark
	for i in range(6):
		var angle := (float(i) / 6.0) * TAU
		var orbit_r := 35.0
		var pos := center + Vector2(cos(angle), sin(angle)) * orbit_r
		var lbl := _make_glyph("\u00b7", pos - Vector2(4, 6))
		var otw := create_tween()
		otw.tween_interval(0.6)
		otw.tween_property(lbl, "modulate:a", 0.6, 0.1)
		# Expand outward
		var expand_pos := center + Vector2(cos(angle), sin(angle)) * (orbit_r + 25)
		otw.tween_property(lbl, "position", expand_pos - Vector2(4, 6), 0.4).set_ease(Tween.EASE_OUT).set_trans(Tween.TRANS_CUBIC)
		otw.tween_property(lbl, "modulate:a", 0.0, 0.2)

	var finish := create_tween()
	finish.tween_interval(1.5)
	finish.tween_callback(func(): _cleanup_and_finish(0.2))


func _variant_departure_board(center: Vector2, glyphs: Array) -> void:
	var code := _key_code if _key_code != "" else "REDEEMED"
	var char_width := 18.0
	var start_x := center.x - (code.length() * char_width) / 2.0
	var check_labels: Array[Label] = []

	# Background ambience — faint dots drifting
	bloom_scatter(center, ["\u00b7"], 20, 180, 0.0, 2.0, 0.1)

	# Top and bottom scan lines framing the code area
	var scan_width := code.length() * char_width + 40
	var scan_start_x := center.x - scan_width / 2.0
	var scan_count := int(scan_width / 9.0)
	var top_scan_labels: Array[Label] = []
	var bottom_scan_labels: Array[Label] = []

	for i in range(scan_count):
		var x_pos := scan_start_x + i * 9.0
		var top_lbl := _make_glyph("\u2500", Vector2(x_pos, center.y - 24))
		top_scan_labels.append(top_lbl)
		var ttw := create_tween().set_ease(Tween.EASE_OUT).set_trans(Tween.TRANS_CUBIC)
		ttw.tween_interval(i * 0.015)
		ttw.tween_property(top_lbl, "modulate:a", 0.3, 0.08)

		var bot_lbl := _make_glyph("\u2500", Vector2(x_pos, center.y + 16))
		bottom_scan_labels.append(bot_lbl)
		var btw := create_tween().set_ease(Tween.EASE_OUT).set_trans(Tween.TRANS_CUBIC)
		btw.tween_interval(i * 0.015 + 0.1)
		btw.tween_property(bot_lbl, "modulate:a", 0.3, 0.08)

	# Character scramble and resolve
	for i in range(code.length()):
		if code[i] == " " or code[i] == "-":
			continue

		var pos := Vector2(start_x + i * char_width, center.y - 10)
		var lbl := _make_glyph(code[i], pos)

		var scramble_tw := create_tween()
		scramble_tw.tween_interval(0.2 + i * 0.1)
		for c in range(8):
			var g: String = glyphs[randi() % glyphs.size()]
			scramble_tw.tween_callback(func(): lbl.text = g)
			scramble_tw.tween_interval(0.04)
		scramble_tw.tween_callback(func():
			lbl.text = "\u2713"
			lbl.add_theme_color_override("font_color", ThemeConstants.HEALTHY)
		)
		lbl.modulate.a = 1.0
		check_labels.append(lbl)

		# Mini bloom ping on each character resolve
		var resolve_time := 0.2 + i * 0.1 + 0.32
		bloom_scatter(pos + Vector2(8, 6), ["\u00b7", "\u2727"], 3, 20, resolve_time, 0.3, 0.4)

	# Shimmer sweep after all resolve
	var resolve_end := 0.2 + code.length() * 0.1 + 0.32
	var shimmer_tw := create_tween()
	shimmer_tw.tween_interval(resolve_end + 0.1)
	shimmer_tw.tween_callback(func():
		for idx in range(check_labels.size()):
			var cl: Label = check_labels[idx]
			if not is_instance_valid(cl):
				continue
			var stw := create_tween()
			stw.tween_interval(idx * 0.02)
			stw.tween_callback(func(): cl.add_theme_color_override("font_color", Color.WHITE))
			stw.tween_interval(0.06)
			stw.tween_callback(func(): cl.add_theme_color_override("font_color", ThemeConstants.HEALTHY))
	)

	# Shimmer sweep along scan lines too
	var line_shimmer := create_tween()
	line_shimmer.tween_interval(resolve_end + 0.15)
	line_shimmer.tween_callback(func():
		for idx in range(top_scan_labels.size()):
			var tl: Label = top_scan_labels[idx]
			var bl: Label = bottom_scan_labels[idx]
			if not is_instance_valid(tl):
				continue
			var stw := create_tween()
			stw.tween_interval(idx * 0.01)
			stw.tween_callback(func():
				if is_instance_valid(tl):
					tl.add_theme_color_override("font_color", Color.WHITE)
				if is_instance_valid(bl):
					bl.add_theme_color_override("font_color", Color.WHITE)
			)
			stw.tween_interval(0.04)
			stw.tween_callback(func():
				if is_instance_valid(tl):
					tl.add_theme_color_override("font_color", _accent)
				if is_instance_valid(bl):
					bl.add_theme_color_override("font_color", _accent)
			)
	)

	# Scatter after shimmer
	var scatter_delay := resolve_end + 0.35
	var scatter_tw := create_tween()
	scatter_tw.tween_interval(scatter_delay)
	scatter_tw.tween_callback(func():
		bloom_scatter(center, glyphs.slice(3, 7), 10, 80, 0.0, 0.6)
		bloom_ring(center, ["\u2726", "\u2727", "\u00b7"], 6, 60, 0.05, 0.5)
	)

	# Scan lines fade outward
	var line_fade := create_tween()
	line_fade.tween_interval(scatter_delay + 0.2)
	line_fade.tween_callback(func():
		for lbl in top_scan_labels:
			if is_instance_valid(lbl):
				var ftw := create_tween()
				ftw.tween_property(lbl, "modulate:a", 0.0, 0.3)
		for lbl in bottom_scan_labels:
			if is_instance_valid(lbl):
				var ftw := create_tween()
				ftw.tween_property(lbl, "modulate:a", 0.0, 0.3)
	)

	var finish := create_tween()
	finish.tween_interval(scatter_delay + 0.7)
	finish.tween_callback(func(): _cleanup_and_finish(0.2))


func _variant_cascade_unlock(center: Vector2, glyphs: Array) -> void:
	var spinner := ["\u00b7", "\u2722", "\u2733", "\u273b", "\u273d"]
	# 4 evenly spaced positions
	var positions := [
		center + Vector2(-90, 0),
		center + Vector2(-30, 0),
		center + Vector2(30, 0),
		center + Vector2(90, 0),
	]

	# Background haze
	bloom_scatter(center, ["\u00b7"], 24, 200, 0.0, 2.0, 0.1)

	# Horizontal connecting baseline (faint, appears early)
	var baseline_y := center.y + 4
	var baseline_start: float = positions[0].x - 20
	var baseline_end: float = positions[3].x + 20
	var baseline_count := int((baseline_end - baseline_start) / 10.0)
	var baseline_labels: Array[Label] = []
	for i in range(baseline_count):
		var lbl := _make_glyph("\u00b7", Vector2(baseline_start + i * 10, baseline_y))
		baseline_labels.append(lbl)
		var tw := create_tween()
		tw.tween_interval(0.1 + i * 0.008)
		tw.tween_property(lbl, "modulate:a", 0.2, 0.1)

	for p_i in range(positions.size()):
		var base_pos: Vector2 = positions[p_i]
		var cascade_delay := p_i * 0.15

		for g_i in range(spinner.size()):
			var lbl := _make_glyph(spinner[g_i], base_pos - Vector2(8, 10) + Vector2(0, -g_i * 22))

			var tw := create_tween().set_ease(Tween.EASE_OUT).set_trans(Tween.TRANS_CUBIC)
			tw.tween_interval(cascade_delay + g_i * 0.08)
			tw.tween_property(lbl, "modulate:a", 1.0, 0.15)
			tw.tween_interval(0.3)
			tw.tween_property(lbl, "modulate:a", 0.3, 0.2)

		# Peak glyph
		var peak := _make_glyph("\u2726", base_pos - Vector2(8, 10) + Vector2(0, -spinner.size() * 22), 24, Color.TRANSPARENT, true)
		var ptw := create_tween()
		ptw.tween_interval(cascade_delay + spinner.size() * 0.08 + 0.1)
		ptw.tween_property(peak, "modulate:a", 1.0, 0.1)

		# Mini bloom at each column peak
		var peak_pos := base_pos + Vector2(0, -spinner.size() * 22)
		bloom_scatter(peak_pos, ["\u00b7", "\u2727"], 4, 25, cascade_delay + spinner.size() * 0.08 + 0.15, 0.4, 0.4)

	# Connecting line between peaks
	var line_y := center.y - 10 - spinner.size() * 22
	var line_start_x: float = positions[0].x - 8
	var line_end_x: float = positions[3].x + 8
	var line_count := int((line_end_x - line_start_x) / 12.0)
	var line_labels: Array[Label] = []

	for i in range(line_count):
		var lbl := _make_glyph("\u2500", Vector2(line_start_x + i * 12, line_y))
		line_labels.append(lbl)

		var ltw := create_tween().set_ease(Tween.EASE_OUT).set_trans(Tween.TRANS_CUBIC)
		ltw.tween_interval(0.75 + i * 0.015)
		ltw.tween_property(lbl, "modulate:a", 0.6, 0.08)

	# Shimmer sweep along the connecting line
	var shimmer_tw := create_tween()
	shimmer_tw.tween_interval(0.95)
	shimmer_tw.tween_callback(func():
		for idx in range(line_labels.size()):
			var ll: Label = line_labels[idx]
			if not is_instance_valid(ll):
				continue
			var stw := create_tween()
			stw.tween_interval(idx * 0.01)
			stw.tween_callback(func(): ll.add_theme_color_override("font_color", Color.WHITE))
			stw.tween_interval(0.04)
			stw.tween_callback(func(): ll.add_theme_color_override("font_color", _accent))
	)

	# Shimmer along baseline too
	var base_shimmer := create_tween()
	base_shimmer.tween_interval(1.0)
	base_shimmer.tween_callback(func():
		for idx in range(baseline_labels.size()):
			var bl: Label = baseline_labels[idx]
			if not is_instance_valid(bl):
				continue
			var stw := create_tween()
			stw.tween_interval(idx * 0.008)
			stw.tween_callback(func():
				if is_instance_valid(bl):
					bl.add_theme_color_override("font_color", Color.WHITE)
			)
			stw.tween_interval(0.03)
			stw.tween_callback(func():
				if is_instance_valid(bl):
					bl.add_theme_color_override("font_color", _accent)
			)
	)

	# Bloom ring at center after all cascades finish
	bloom_ring(center, ["\u2726", "\u2727", "\u00b7"], 8, 70, 1.05, 0.5)

	# Line segments fall and fade
	var fall_tw := create_tween()
	fall_tw.tween_interval(1.15)
	fall_tw.tween_callback(func():
		for ll in line_labels:
			if not is_instance_valid(ll):
				continue
			var ftw := create_tween().set_ease(Tween.EASE_IN).set_trans(Tween.TRANS_CUBIC)
			ftw.tween_property(ll, "position:y", ll.position.y + 20, 0.25)
			ftw.parallel().tween_property(ll, "modulate:a", 0.0, 0.25)
		# Baseline also fades
		for bl in baseline_labels:
			if not is_instance_valid(bl):
				continue
			var ftw := create_tween()
			ftw.tween_property(bl, "modulate:a", 0.0, 0.3)
	)

	# Final checkmark wink at center
	var check := _make_glyph("\u2713", center - Vector2(10, 14), 28, ThemeConstants.HEALTHY, true)
	var check_tw := create_tween()
	check_tw.tween_interval(1.3)
	check_tw.tween_property(check, "modulate:a", 1.0, 0.1)
	check_tw.tween_interval(0.15)
	check_tw.tween_property(check, "modulate:a", 0.0, 0.15)

	var finish := create_tween()
	finish.tween_interval(1.7)
	finish.tween_callback(func(): _cleanup_and_finish(0.2))
