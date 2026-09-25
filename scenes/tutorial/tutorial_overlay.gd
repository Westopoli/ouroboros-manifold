extends Control

signal beat_dismissed(beat_id: String)

const BEATS_PATH := "res://simulation/library/tutorial/beats.json"
const CARD_WIDTH := 480.0
const CARD_ALPHA := 0.70
const BG_ALPHA := 0.25
const SAFE_MARGIN := 40.0

const _ANCHOR_SCREEN_RECTS := {
	"center": "viewport_center",
	"first_unit": "viewport_center",
	"selected_unit": "viewport_center",
	"objective_hud": "top_right",
	"pause_button": "top_left",
}

var _beats_cache: Dictionary = {}
var _beats_loaded: bool = false
var _bg: ColorRect = null
var _card: PanelContainer = null
var _current_beat_id: String = ""


func _ready() -> void:
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)


func show_beat(beat_id: String) -> void:
	if not _beats_loaded:
		_load_beats()

	if not _beats_cache.has(beat_id):
		print("tutorial_overlay: beat not found id=%s (beats.json missing or empty)" % beat_id)
		return

	var beat: Dictionary = _beats_cache[beat_id]
	_current_beat_id = beat_id

	var already_visible := _card != null and _card.visible
	if not already_visible:
		_render_card(beat)
	else:
		_repopulate_card(beat)

	var anchor_id: String = String(beat.get("pointed_anchor", "center"))
	var anchor_rect := _resolve_anchor_rect(anchor_id)

	await get_tree().process_frame
	var card_size: Vector2 = _card.size
	var target_pos := _compute_card_position(anchor_rect, card_size)

	if already_visible:
		var tw := create_tween().set_ease(Tween.EASE_OUT).set_trans(Tween.TRANS_CUBIC)
		tw.tween_property(_card, "position", target_pos, ThemeConstants.FADE_DURATION)
	else:
		_card.position = target_pos
		_fade_in()


func hide_beat() -> void:
	if _card == null:
		return
	var card := _card
	var bg := _bg
	_card = null
	_bg = null
	_current_beat_id = ""
	var tw := create_tween()
	tw.set_parallel(true)
	tw.tween_property(card, "modulate:a", 0.0, ThemeConstants.FADE_DURATION)
	if bg != null:
		tw.tween_property(bg, "modulate:a", 0.0, ThemeConstants.FADE_DURATION)
	tw.set_parallel(false)
	tw.tween_callback(func():
		card.queue_free()
		if bg != null:
			bg.queue_free()
	)


func _render_card(beat: Dictionary) -> void:
	_bg = ColorRect.new()
	_bg.color = Color(0.0, 0.0, 0.0, BG_ALPHA)
	_bg.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_bg.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	add_child(_bg)

	_card = PanelContainer.new()
	_card.mouse_filter = Control.MOUSE_FILTER_STOP
	_card.custom_minimum_size = Vector2(CARD_WIDTH, 0.0)
	_card.size_flags_horizontal = Control.SIZE_SHRINK_CENTER

	var sb := StyleBoxFlat.new()
	var base: Color = ThemeConstants.CARD
	sb.bg_color = Color(base.r, base.g, base.b, CARD_ALPHA)
	sb.corner_radius_top_left = 6
	sb.corner_radius_top_right = 6
	sb.corner_radius_bottom_left = 6
	sb.corner_radius_bottom_right = 6
	sb.content_margin_left = 20
	sb.content_margin_right = 20
	sb.content_margin_top = 18
	sb.content_margin_bottom = 18
	sb.border_width_left = 1
	sb.border_width_right = 1
	sb.border_width_top = 1
	sb.border_width_bottom = 1
	sb.border_color = Color(1.0, 1.0, 1.0, 0.15)
	_card.add_theme_stylebox_override("panel", sb)

	var vbox := VBoxContainer.new()
	vbox.name = "Content"
	vbox.add_theme_constant_override("separation", 12)
	_card.add_child(vbox)

	add_child(_card)
	_populate_card(beat)


func _repopulate_card(beat: Dictionary) -> void:
	var vbox: VBoxContainer = _card.get_node_or_null("Content")
	if vbox == null:
		return
	for child in vbox.get_children():
		child.queue_free()
	_populate_card(beat)


func _populate_card(beat: Dictionary) -> void:
	var vbox: VBoxContainer = _card.get_node_or_null("Content")
	if vbox == null:
		return

	var accent: Color = _resolve_accent(String(beat.get("accent_hint", "primary")))

	var headline := Label.new()
	headline.text = String(beat.get("headline", ""))
	headline.uppercase = true
	headline.add_theme_font_override("font", ThemeConstants.font_mono_bold)
	headline.add_theme_font_size_override("font_size", ThemeConstants.SUBTITLE_SIZE)
	headline.add_theme_color_override("font_color", accent)
	headline.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	vbox.add_child(headline)

	var body := Label.new()
	body.text = String(beat.get("body", ""))
	body.add_theme_font_override("font", ThemeConstants.font_serif_regular)
	body.add_theme_font_size_override("font_size", ThemeConstants.BODY_NARRATIVE_SIZE)
	body.add_theme_color_override("font_color", ThemeConstants.PRIMARY)
	body.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	vbox.add_child(body)

	var button_scene: PackedScene = load("res://theme/components/tm_button.tscn")
	var button: Button = button_scene.instantiate()
	button.text = "Acknowledge"
	if "accent_color" in button:
		button.accent_color = accent
	button.size_flags_horizontal = Control.SIZE_SHRINK_END
	button.pressed.connect(_on_acknowledge_pressed)
	vbox.add_child(button)


func _fade_in() -> void:
	_bg.modulate.a = 0.0
	_card.modulate.a = 0.0
	var tw := create_tween()
	tw.set_parallel(true)
	tw.set_ease(ThemeConstants.EASE_TYPE).set_trans(ThemeConstants.TRANS_TYPE)
	tw.tween_property(_bg, "modulate:a", 1.0, ThemeConstants.FADE_DURATION)
	tw.tween_property(_card, "modulate:a", 1.0, ThemeConstants.FADE_DURATION)


func _resolve_anchor_rect(anchor_id: String) -> Rect2:
	var kind: String = String(_ANCHOR_SCREEN_RECTS.get(anchor_id, "viewport_center"))
	var vp_rect: Rect2 = get_viewport().get_visible_rect()
	var w: float = vp_rect.size.x
	var h: float = vp_rect.size.y
	var spot: Vector2 = Vector2(120.0, 80.0)
	match kind:
		"viewport_center":
			return Rect2(Vector2(w * 0.5 - spot.x * 0.5, h * 0.5 - spot.y * 0.5), spot)
		"top_right":
			return Rect2(Vector2(w - spot.x - SAFE_MARGIN, SAFE_MARGIN), spot)
		"top_left":
			return Rect2(Vector2(SAFE_MARGIN, SAFE_MARGIN), spot)
		_:
			return Rect2(Vector2(w * 0.5 - spot.x * 0.5, h * 0.5 - spot.y * 0.5), spot)


func _compute_card_position(anchor_rect: Rect2, card_size: Vector2) -> Vector2:
	var vp_rect: Rect2 = get_viewport().get_visible_rect()
	var w: float = vp_rect.size.x
	var h: float = vp_rect.size.y
	var anchor_center := anchor_rect.position + anchor_rect.size * 0.5
	var anchor_left: bool = anchor_center.x < w * 0.5
	var anchor_top: bool = anchor_center.y < h * 0.5

	var pos: Vector2 = Vector2.ZERO

	if anchor_rect.size.x < w * 0.3 and anchor_rect.size.y < h * 0.3 and abs(anchor_center.x - w * 0.5) < w * 0.15 and abs(anchor_center.y - h * 0.5) < h * 0.15:
		pos.x = (w - card_size.x) * 0.5
		pos.y = h - card_size.y - SAFE_MARGIN
	else:
		if anchor_left:
			pos.x = w - card_size.x - SAFE_MARGIN
		else:
			pos.x = SAFE_MARGIN
		if anchor_top:
			pos.y = h - card_size.y - SAFE_MARGIN
		else:
			pos.y = SAFE_MARGIN

	pos.x = clamp(pos.x, SAFE_MARGIN, max(SAFE_MARGIN, w - card_size.x - SAFE_MARGIN))
	pos.y = clamp(pos.y, SAFE_MARGIN, max(SAFE_MARGIN, h - card_size.y - SAFE_MARGIN))
	return pos


func _load_beats() -> void:
	_beats_loaded = true
	if not FileAccess.file_exists(BEATS_PATH):
		print("tutorial_overlay: beats.json not present at %s" % BEATS_PATH)
		_beats_cache = {}
		return
	var f := FileAccess.open(BEATS_PATH, FileAccess.READ)
	if f == null:
		print("tutorial_overlay: failed to open %s" % BEATS_PATH)
		_beats_cache = {}
		return
	var raw := f.get_as_text()
	f.close()
	var parsed = JSON.parse_string(raw)
	if parsed is Array:
		for entry in parsed:
			if entry is Dictionary and entry.has("id"):
				_beats_cache[entry["id"]] = entry
	elif parsed is Dictionary:
		_beats_cache = parsed
	else:
		print("tutorial_overlay: beats.json parse failed or unexpected shape")
		_beats_cache = {}


func _resolve_accent(hint: String) -> Color:
	if hint == "primary":
		var era_id: String = EraThemeResolver.get_active_era() if EraThemeResolver else ""
		if era_id != "":
			return ThemeConstants.get_era_accent(era_id)
	return ThemeConstants.PRIMARY


func _on_acknowledge_pressed() -> void:
	var dismissed_id := _current_beat_id
	hide_beat()
	if dismissed_id != "":
		beat_dismissed.emit(dismissed_id)


func qa_state() -> Dictionary:
	return {
		"scene": "tutorial_overlay",
		"tick": -1,
		"beat_id": _current_beat_id,
		"card_visible": _card != null and is_instance_valid(_card),
		"plants": [],
	}
