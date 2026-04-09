extends Control

const TITLE_TEXT := "OUROBOROS MANIFOLD"
const UNRESOLVE_MIN_INTERVAL := 8.0
const UNRESOLVE_MAX_INTERVAL := 15.0
const FIRST_UNRESOLVE_DELAY := 1.5
const FADE_DURATION := 0.12
const GLYPH_HOLD_MIN := 0.4
const GLYPH_HOLD_MAX := 0.7
const GLYPH_CYCLE_INTERVAL := 0.15
const PULSE_FREQ := 0.15
const PULSE_MIN := 0.92
const PULSE_MAX := 1.0
const ERA_ROTATION_INTERVAL := 90.0

const ERA_GLYPHS := {
	"roman": ["✦", "✧", "◆", "❖", "✶", "⬥", "◈", "✴"],
	"settled_reach": ["·", "✧", "✦", "✶", "✹", "✺", "✻", "✽"],
	"1980s": ["─", "━", "═", "▪", "▫", "◽", "◾", "■"],
}
const ERA_ORDER := ["roman", "settled_reach", "1980s"]

var _char_labels: Array[Label] = []
var _char_positions: Array[Vector2] = []
var _title_origin := Vector2.ZERO
var _unresolve_timer: Timer
var _era_timer: Timer
var _pulse_timer: Timer
var _current_era_index := 0
var _is_intensified := false
var _first_event := true

func _ready() -> void:
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	_build_title_labels()
	_start_breathing()
	_start_unresolve_timer()
	_start_era_rotation()


func set_title_origin(origin: Vector2) -> void:
	_title_origin = origin
	if _char_labels.size() > 0:
		_position_labels()


func connect_to_celebration(bg_celebration: Control) -> void:
	if bg_celebration.has_signal("celebration_climax"):
		bg_celebration.celebration_climax.connect(_on_climax)


func _build_title_labels() -> void:
	var font: Font = ThemeConstants.font_serif_regular
	var font_size: int = ThemeConstants.TITLE_SIZE

	var x_offset := 0.0
	for i in range(TITLE_TEXT.length()):
		var ch: String = TITLE_TEXT[i]
		var char_width := font.get_string_size(ch, HORIZONTAL_ALIGNMENT_LEFT, -1, font_size).x

		var lbl := Label.new()
		lbl.text = ch
		lbl.add_theme_font_override("font", font)
		lbl.add_theme_font_size_override("font_size", font_size)
		lbl.add_theme_color_override("font_color", ThemeConstants.PRIMARY)
		lbl.mouse_filter = Control.MOUSE_FILTER_IGNORE
		lbl.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		lbl.custom_minimum_size.x = char_width
		lbl.size.x = char_width
		add_child(lbl)
		_char_labels.append(lbl)

		_char_positions.append(Vector2(x_offset, 0.0))
		x_offset += char_width

	_position_labels()


func _position_labels() -> void:
	for i in range(_char_labels.size()):
		_char_labels[i].position = _title_origin + _char_positions[i]


func _start_breathing() -> void:
	_pulse_timer = Timer.new()
	_pulse_timer.wait_time = 0.1
	_pulse_timer.timeout.connect(_update_breathing)
	add_child(_pulse_timer)
	_pulse_timer.start()


func _update_breathing() -> void:
	var t := Time.get_ticks_msec() / 1000.0
	for i in range(_char_labels.size()):
		var lbl := _char_labels[i]
		if lbl.get_meta("unresolving", false):
			continue
		var phase := float(i) * 0.4
		var alpha := PULSE_MIN + (PULSE_MAX - PULSE_MIN) * (0.5 + 0.5 * sin(t * TAU * PULSE_FREQ + phase))
		lbl.modulate.a = alpha


func _start_unresolve_timer() -> void:
	_unresolve_timer = Timer.new()
	_unresolve_timer.one_shot = true
	_unresolve_timer.timeout.connect(_trigger_unresolve)
	add_child(_unresolve_timer)
	_unresolve_timer.wait_time = FIRST_UNRESOLVE_DELAY
	_unresolve_timer.start()


func _schedule_next_unresolve() -> void:
	_unresolve_timer.wait_time = randf_range(UNRESOLVE_MIN_INTERVAL, UNRESOLVE_MAX_INTERVAL)
	_unresolve_timer.start()


func _trigger_unresolve() -> void:
	var count := randi_range(1, 3)
	var glyph_hold := randf_range(GLYPH_HOLD_MIN, GLYPH_HOLD_MAX)
	var white_blend := 0.30

	if _is_intensified:
		count = randi_range(4, 6)
		glyph_hold = 1.0
		white_blend = 0.40
		_is_intensified = false

	var valid_indices: Array[int] = []
	for i in range(TITLE_TEXT.length()):
		if TITLE_TEXT[i] != " ":
			valid_indices.append(i)

	var selected: Array[int] = []
	for _n in range(count):
		if valid_indices.is_empty():
			break
		var weights: Array[float] = []
		var center := float(TITLE_TEXT.length()) / 2.0
		for idx in valid_indices:
			var dist := absf(float(idx) - center)
			weights.append(1.0 / (1.0 + dist * 0.3))

		var total := 0.0
		for w in weights:
			total += w
		var roll := randf() * total
		var accum := 0.0
		for j in range(weights.size()):
			accum += weights[j]
			if roll <= accum:
				selected.append(valid_indices[j])
				valid_indices.remove_at(j)
				break

	var era_key: String = ERA_ORDER[_current_era_index]
	var glyphs: Array = ERA_GLYPHS[era_key]

	for idx in selected:
		_unresolve_character(idx, glyphs, glyph_hold, white_blend)

	_schedule_next_unresolve()


func _unresolve_character(idx: int, glyphs: Array, glyph_hold: float, white_blend: float) -> void:
	var lbl := _char_labels[idx]
	if lbl.get_meta("unresolving", false):
		return
	var original_char: String = TITLE_TEXT[idx]
	lbl.set_meta("unresolving", true)

	var cycle_count := int(glyph_hold / GLYPH_CYCLE_INTERVAL)
	if cycle_count < 1:
		cycle_count = 1

	# Phase 1: fade out the serif character
	var tw := create_tween().set_ease(Tween.EASE_IN).set_trans(Tween.TRANS_CUBIC)
	tw.tween_property(lbl, "modulate:a", 0.0, FADE_DURATION)

	# Phase 2: swap to gold glyph, fade in
	tw.tween_callback(func():
		if is_instance_valid(lbl):
			lbl.add_theme_font_override("font", ThemeConstants.font_mono_regular)
			lbl.add_theme_color_override("font_color", Color("#D4A017"))
			lbl.text = glyphs[randi() % glyphs.size()]
	)
	tw.tween_property(lbl, "modulate:a", 1.0, FADE_DURATION).set_ease(Tween.EASE_OUT)

	# Phase 3: hold and cycle glyphs
	for c in range(cycle_count):
		tw.tween_interval(GLYPH_CYCLE_INTERVAL)
		tw.tween_callback(func():
			if is_instance_valid(lbl):
				lbl.text = glyphs[randi() % glyphs.size()]
		)

	# Phase 4: fade out the gold glyph
	tw.tween_property(lbl, "modulate:a", 0.0, FADE_DURATION).set_ease(Tween.EASE_IN)

	# Phase 5: swap back to serif, fade in with brightness pulse
	tw.tween_callback(func():
		if is_instance_valid(lbl):
			lbl.text = original_char
			lbl.add_theme_font_override("font", ThemeConstants.font_serif_regular)
			var flash_color := ThemeConstants.PRIMARY.lerp(Color.WHITE, white_blend)
			lbl.add_theme_color_override("font_color", flash_color)
	)
	tw.tween_property(lbl, "modulate:a", 1.0, FADE_DURATION).set_ease(Tween.EASE_OUT)

	# Phase 6: decay brightness back to normal
	tw.tween_method(func(t: float):
		if is_instance_valid(lbl):
			var flash_color := ThemeConstants.PRIMARY.lerp(Color.WHITE, white_blend)
			lbl.add_theme_color_override("font_color", flash_color.lerp(ThemeConstants.PRIMARY, t))
	, 0.0, 1.0, 0.3)
	tw.tween_callback(func():
		if is_instance_valid(lbl):
			lbl.set_meta("unresolving", false)
	)


func _start_era_rotation() -> void:
	_era_timer = Timer.new()
	_era_timer.wait_time = ERA_ROTATION_INTERVAL
	_era_timer.timeout.connect(func():
		_current_era_index = (_current_era_index + 1) % ERA_ORDER.size()
	)
	add_child(_era_timer)
	_era_timer.start()


func _on_climax() -> void:
	_is_intensified = true
	_unresolve_timer.stop()
	_trigger_unresolve()
