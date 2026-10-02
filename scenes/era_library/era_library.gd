extends Control

const PackSource := preload("res://scenes/era_library/era_pack_source.gd")
const Ownership := preload("res://scenes/era_library/era_ownership.gd")
const EraCard := preload("res://scenes/era_library/era_card.gd")

var _packs_root := "res://assets/eras"
var _store_path := "user://era_ownership.json"
var _grid: GridContainer
var _eras: Array = []


func _ready() -> void:
	_build_ui()
	_load_eras()


func qa_set_sources(packs_root: String, ownership_path: String) -> void:
	_packs_root = packs_root
	_store_path = ownership_path if ownership_path != "" else "user://era_ownership.json"
	_load_eras()


func _load_eras() -> void:
	if _grid == null:
		return
	for c in _grid.get_children():
		_grid.remove_child(c)
		c.queue_free()
	var source = PackSource.new(_packs_root)
	var ids := []
	for m in source.manifests():
		ids.append(m["era_id"])
	var owned: Array = Ownership.new().owned_ids(ids, _store_path)
	_eras = []
	for m in source.manifests():
		var is_owned: bool = m["era_id"] in owned
		_eras.append({"id": m["era_id"], "name": m["era_display_name"], "owned": is_owned,
			"spatial_scale": m["era_spatial_scale"], "tone": m["era_tone"], "order": int(m["era_order"])})
		EraCard.build(_grid, m, is_owned)


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

	# Subscription model removed 2026-05-09 — see docs/bible_history/game_bible_1_23.md (bible_monetization.md folded into the hub 2026-05-31; hub rewritten 2026-09-10).
	# Previously this header row held a SUBSCRIBED/FREE TIER badge and a "Manage Subscription" link.
	var header := Label.new()
	header.text = "ERA LIBRARY"
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

	var grid := GridContainer.new()
	_grid = grid
	grid.columns = 3
	grid.add_theme_constant_override("h_separation", 16)
	grid.add_theme_constant_override("v_separation", 16)
	grid.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	scroll.add_child(grid)

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


func qa_state() -> Dictionary:
	return {
		"scene": "era_library",
		"tick": -1,
		"era_count": _eras.size(),
		"eras": _eras,
		"plants": [],
	}
