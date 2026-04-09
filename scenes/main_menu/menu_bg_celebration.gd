extends Control

signal celebration_climax

const GLYPH_SET := ["·", "✧", "✦", "✶", "✹", "✺", "✻", "✽"]
const LOOP_DURATION := 50.0
const GLYPH_POOL_CAP := 80
const DOT_MAX_AGE := 20.0
const DOT_SPAWN_INTERVAL := 0.8
const DOT_DRIFT_SPEED := 8.0
var _dot_drift_dir := Vector2(-0.3, -1.0).normalized()

var _shader_rect: ColorRect
var _glyph_layer: Control
var _glyph_pool: Array[Label] = []
var _dot_pool: Array[Dictionary] = []
var _dot_timer: Timer
var _viewport_size := Vector2.ZERO

func _ready() -> void:
	_viewport_size = get_viewport_rect().size
	get_viewport().size_changed.connect(_on_viewport_resized)
	_setup_layers()
	_start_loop()


func _on_viewport_resized() -> void:
	_viewport_size = get_viewport_rect().size


func _setup_layers() -> void:
	set_anchors_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_IGNORE

	_shader_rect = ColorRect.new()
	_shader_rect.set_anchors_preset(Control.PRESET_FULL_RECT)
	_shader_rect.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var mat := ShaderMaterial.new()
	mat.shader = load("res://assets/shaders/starfield.gdshader")
	mat.set_shader_parameter("tint_color", Vector3(0.54, 0.61, 0.72))
	_shader_rect.material = mat
	_shader_rect.modulate.a = 0.0
	add_child(_shader_rect)

	_glyph_layer = Control.new()
	_glyph_layer.set_anchors_preset(Control.PRESET_FULL_RECT)
	_glyph_layer.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(_glyph_layer)


func _start_loop() -> void:
	_dot_timer = Timer.new()
	_dot_timer.wait_time = DOT_SPAWN_INTERVAL
	_dot_timer.timeout.connect(_spawn_ambient_dot)
	add_child(_dot_timer)
	_dot_timer.start()

	_schedule_phase_1()
	_schedule_phase_2()
	_schedule_phase_3()
	_schedule_loop_restart()


func _schedule_phase_1() -> void:
	_fade_shader(0.0, 0.0, 0.15, 6.0)
	_schedule_bloom_ring(8.0, Vector2(0.6, 0.45), 8, 120.0, 4.0, 0.35)
	_schedule_bloom_ring(14.0, Vector2(0.7, 0.3), 12, 200.0, 5.0, 0.30)


func _schedule_phase_2() -> void:
	_schedule_bloom_ring(18.0, Vector2(0.55, 0.5), 16, 280.0, 6.0, 0.40)
	_schedule_bloom_scatter(20.0, Vector2(0.55, 0.5), 15, 300.0, 4.0, 0.35)
	_schedule_depth_scatter(22.0, Vector2(0.55, 0.5), 30, 450.0, 6.0, 0.15)

	var climax_tw := create_tween()
	climax_tw.tween_interval(24.0)
	climax_tw.tween_callback(func(): celebration_climax.emit())

	_schedule_sweep_line(26.0)
	_schedule_bloom_ring(30.0, Vector2(0.55, 0.5), 20, 100.0, 6.0, 0.35, 350.0)


func _schedule_phase_3() -> void:
	var dissolve_tw := create_tween()
	dissolve_tw.tween_interval(36.0)
	dissolve_tw.tween_callback(_dissolve_bloom_glyphs)

	_fade_shader(38.0, 0.15, 0.05, 6.0)


func _schedule_loop_restart() -> void:
	_fade_shader(48.0, 0.05, 0.15, 2.0)

	var restart_tw := create_tween()
	restart_tw.tween_interval(LOOP_DURATION)
	restart_tw.tween_callback(_restart_loop)


func _restart_loop() -> void:
	_schedule_phase_1()
	_schedule_phase_2()
	_schedule_phase_3()
	_schedule_loop_restart()


func _fade_shader(delay: float, from: float, to: float, duration: float) -> void:
	var tw := create_tween()
	tw.tween_interval(delay)
	tw.tween_callback(func(): _shader_rect.modulate.a = from)
	tw.tween_property(_shader_rect, "modulate:a", to, duration)


func _spawn_ambient_dot() -> void:
	_recycle_old_dots()
	if _active_glyph_count() >= GLYPH_POOL_CAP:
		return

	var pos := Vector2(randf() * _viewport_size.x, randf() * _viewport_size.y)
	var lbl := _make_glyph("·", pos, 14, Color("#D4A017"))
	lbl.modulate.a = 0.0

	var fade_tw := create_tween()
	fade_tw.tween_property(lbl, "modulate:a", 0.25, 1.5)

	var drift_tw := create_tween().set_loops()
	drift_tw.tween_property(lbl, "position", lbl.position + _dot_drift_dir * DOT_DRIFT_SPEED * 10.0, 10.0)

	var pulse_tw := create_tween().set_loops()
	var phase_offset := randf() * TAU
	pulse_tw.tween_method(func(t: float):
		if is_instance_valid(lbl):
			lbl.modulate.a = 0.25 + 0.07 * sin(t * TAU * 0.4 + phase_offset)
	, 0.0, 2.5, 2.5)

	_dot_pool.append({
		"label": lbl,
		"birth": Time.get_ticks_msec() / 1000.0,
		"drift_tween": drift_tw,
		"pulse_tween": pulse_tw,
	})


func _recycle_old_dots() -> void:
	var now := Time.get_ticks_msec() / 1000.0
	var to_remove: Array[int] = []
	for i in range(_dot_pool.size()):
		var dot: Dictionary = _dot_pool[i]
		if now - dot["birth"] > DOT_MAX_AGE:
			to_remove.append(i)

	for i in range(to_remove.size() - 1, -1, -1):
		var idx: int = to_remove[i]
		var dot: Dictionary = _dot_pool[idx]
		var lbl: Label = dot["label"]
		if dot.has("drift_tween") and dot["drift_tween"] is Tween:
			dot["drift_tween"].kill()
		if dot.has("pulse_tween") and dot["pulse_tween"] is Tween:
			dot["pulse_tween"].kill()
		if is_instance_valid(lbl):
			var fade := create_tween()
			fade.tween_property(lbl, "modulate:a", 0.0, 1.5)
			fade.tween_callback(func():
				if is_instance_valid(lbl):
					_glyph_pool.erase(lbl)
					lbl.queue_free()
			)
		_dot_pool.remove_at(idx)


func _schedule_bloom_ring(delay: float, center_frac: Vector2, count: int, radius: float, duration: float, alpha: float, expand_radius: float = -1.0) -> void:
	var tw := create_tween()
	tw.tween_interval(delay)
	tw.tween_callback(func():
		if _active_glyph_count() >= GLYPH_POOL_CAP:
			return
		var center := Vector2(center_frac.x * _viewport_size.x, center_frac.y * _viewport_size.y)
		var final_radius := expand_radius if expand_radius > 0 else radius
		_bloom_ring(center, count, radius, final_radius, duration, alpha)
	)


func _bloom_ring(center: Vector2, count: int, start_radius: float, end_radius: float, duration: float, alpha: float) -> void:
	var stagger := duration / float(count) / 3.0
	for i in range(count):
		if _active_glyph_count() >= GLYPH_POOL_CAP:
			break
		var angle := (float(i) / float(count)) * TAU
		var start_pos := center + Vector2(cos(angle), sin(angle)) * start_radius
		var end_pos := center + Vector2(cos(angle), sin(angle)) * end_radius
		var glyph_text := _weighted_glyph()

		var lbl := _make_glyph(glyph_text, start_pos, 16, Color("#D4A017"))
		lbl.modulate.a = 0.0

		var char_delay := i * stagger
		var btw := create_tween().set_ease(Tween.EASE_OUT).set_trans(Tween.TRANS_CUBIC)
		btw.tween_interval(char_delay)
		btw.tween_property(lbl, "modulate:a", alpha, duration * 0.3)
		btw.parallel().tween_property(lbl, "position", end_pos, duration * 0.6)
		btw.tween_interval(duration * 0.2)
		btw.tween_property(lbl, "modulate:a", 0.0, duration * 0.3)
		btw.tween_callback(func():
			if is_instance_valid(lbl):
				_glyph_pool.erase(lbl)
				lbl.queue_free()
		)


func _schedule_bloom_scatter(delay: float, center_frac: Vector2, count: int, radius: float, duration: float, alpha: float) -> void:
	var tw := create_tween()
	tw.tween_interval(delay)
	tw.tween_callback(func():
		if _active_glyph_count() >= GLYPH_POOL_CAP:
			return
		var center := Vector2(center_frac.x * _viewport_size.x, center_frac.y * _viewport_size.y)
		_bloom_scatter(center, count, radius, duration, alpha)
	)


func _bloom_scatter(center: Vector2, count: int, radius: float, duration: float, alpha: float) -> void:
	for i in range(count):
		if _active_glyph_count() >= GLYPH_POOL_CAP:
			break
		var angle := randf() * TAU
		var dist := randf() * radius
		var pos := center + Vector2(cos(angle), sin(angle)) * dist

		var dist_ratio := dist / radius
		var glyph_text: String
		if dist_ratio < 0.4:
			glyph_text = GLYPH_SET[randi() % 4]
		else:
			glyph_text = _weighted_glyph()

		var lbl := _make_glyph(glyph_text, pos, 16, Color("#D4A017"))
		lbl.modulate.a = 0.0

		var drift := (pos - center).normalized() * 30.0
		var char_delay := randf() * duration * 0.2

		var stw := create_tween().set_ease(Tween.EASE_OUT).set_trans(Tween.TRANS_CUBIC)
		stw.tween_interval(char_delay)
		stw.tween_property(lbl, "modulate:a", alpha, duration * 0.2)
		stw.parallel().tween_property(lbl, "position", lbl.position + drift, duration * 0.7)
		stw.tween_interval(duration * 0.3)
		stw.tween_property(lbl, "modulate:a", 0.0, duration * 0.3)
		stw.tween_callback(func():
			if is_instance_valid(lbl):
				_glyph_pool.erase(lbl)
				lbl.queue_free()
		)


func _schedule_depth_scatter(delay: float, center_frac: Vector2, count: int, radius: float, duration: float, alpha: float) -> void:
	var tw := create_tween()
	tw.tween_interval(delay)
	tw.tween_callback(func():
		var center := Vector2(center_frac.x * _viewport_size.x, center_frac.y * _viewport_size.y)
		for i in range(count):
			if _active_glyph_count() >= GLYPH_POOL_CAP:
				break
			var angle := randf() * TAU
			var dist := randf() * radius
			var pos := center + Vector2(cos(angle), sin(angle)) * dist
			var lbl := _make_glyph("·", pos, 12, Color("#D4A017"))
			lbl.modulate.a = 0.0

			var dtw := create_tween().set_ease(Tween.EASE_OUT).set_trans(Tween.TRANS_CUBIC)
			dtw.tween_property(lbl, "modulate:a", alpha, duration * 0.2)
			dtw.tween_interval(duration * 0.5)
			dtw.tween_property(lbl, "modulate:a", 0.0, duration * 0.3)
			dtw.tween_callback(func():
				if is_instance_valid(lbl):
					_glyph_pool.erase(lbl)
					lbl.queue_free()
			)
	)


func _schedule_sweep_line(delay: float) -> void:
	var tw := create_tween()
	tw.tween_interval(delay)
	tw.tween_callback(func():
		var y_pos := _viewport_size.y * 0.7
		var start_x := _viewport_size.x * 0.3
		var char_width := 14.0
		var count := 40
		var stagger := 2.0 / float(count)

		for i in range(count):
			if _active_glyph_count() >= GLYPH_POOL_CAP:
				break
			var pos := Vector2(start_x + i * char_width, y_pos)
			var lbl := _make_glyph("─", pos, 14, Color("#D4A017"))
			lbl.modulate.a = 0.0

			var stw := create_tween()
			stw.tween_interval(i * stagger)
			stw.tween_property(lbl, "modulate:a", 0.30, 0.1)
			stw.tween_interval(2.0 - i * stagger)
			stw.tween_property(lbl, "modulate:a", 0.0, 4.0)
			stw.tween_callback(func():
				if is_instance_valid(lbl):
					_glyph_pool.erase(lbl)
					lbl.queue_free()
			)
	)


func _dissolve_bloom_glyphs() -> void:
	for lbl in _glyph_pool.duplicate():
		if not is_instance_valid(lbl):
			_glyph_pool.erase(lbl)
			continue
		if lbl.text == "·":
			continue
		var dtw := create_tween()
		dtw.tween_property(lbl, "modulate:a", 0.0, 4.0)
		dtw.tween_callback(func():
			if is_instance_valid(lbl):
				_glyph_pool.erase(lbl)
				lbl.queue_free()
		)


func _weighted_glyph() -> String:
	var roll := randf()
	if roll < 0.40:
		return GLYPH_SET[randi() % 4]
	elif roll < 0.75:
		return GLYPH_SET[4 + randi() % 2]
	else:
		return GLYPH_SET[6 + randi() % 2]


func _make_glyph(text: String, pos: Vector2, font_size: int, color: Color) -> Label:
	var lbl := Label.new()
	lbl.text = text
	lbl.add_theme_font_override("font", ThemeConstants.font_mono_regular)
	lbl.add_theme_font_size_override("font_size", font_size)
	lbl.add_theme_color_override("font_color", color)
	lbl.position = pos
	lbl.modulate.a = 0.0
	lbl.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_glyph_layer.add_child(lbl)
	_glyph_pool.append(lbl)
	return lbl


func _active_glyph_count() -> int:
	var count := 0
	for lbl in _glyph_pool:
		if is_instance_valid(lbl):
			count += 1
	return count
