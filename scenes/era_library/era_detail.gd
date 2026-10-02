extends Control

const PackSource := preload("res://scenes/era_library/era_pack_source.gd")
const Ownership := preload("res://scenes/era_library/era_ownership.gd")
const Roster := preload("res://scenes/era_library/era_roster.gd")

var _packs_root := "res://assets/eras"
var _store_path := "user://era_ownership.json"
var _era_id := ""
var _name := ""
var _owned := false
var _tiers: Array = []
var _roster: Array = []


func qa_set_sources(packs_root: String, ownership_path: String) -> void:
	_packs_root = packs_root
	_store_path = ownership_path if ownership_path != "" else "user://era_ownership.json"


func setup(params: Dictionary) -> void:
	_era_id = params.get("era_id", "")
	var source = PackSource.new(_packs_root)
	var m: Dictionary = source.find(_era_id)
	if m.is_empty():
		return
	_name = m["era_display_name"]
	_tiers = source.tiers(_era_id)
	_roster = source.roster(_era_id)
	var ids := []
	for p in source.manifests():
		ids.append(p["era_id"])
	_owned = _era_id in Ownership.new().owned_ids(ids, _store_path)
	_build_ui(m)


func _input(event: InputEvent) -> void:
	if event.is_action_pressed("ui_cancel"):
		SceneRouter.go_back()


func _build_ui(m: Dictionary) -> void:
	for child in get_children():
		child.queue_free()
	var accent := Color(m["era_accent_color"])
	var bg := ColorRect.new()
	bg.color = ThemeConstants.BASE
	bg.set_anchors_preset(Control.PRESET_FULL_RECT)
	add_child(bg)
	var margin := MarginContainer.new()
	margin.set_anchors_preset(Control.PRESET_FULL_RECT)
	for side in ["left", "right"]:
		margin.add_theme_constant_override("margin_" + side, 80)
	for side in ["top", "bottom"]:
		margin.add_theme_constant_override("margin_" + side, 60)
	add_child(margin)
	var outer := VBoxContainer.new()
	outer.add_theme_constant_override("separation", 16)
	margin.add_child(outer)

	outer.add_child(_label("ERA DOSSIER", ThemeConstants.font_mono_regular, ThemeConstants.CLASSIFICATION_LABEL_SIZE, accent))
	outer.add_child(_label(_name, ThemeConstants.font_serif_regular, ThemeConstants.TITLE_SIZE, accent))
	outer.add_child(_label("OWNED" if _owned else "LOCKED", ThemeConstants.font_mono_regular,
		ThemeConstants.ERA_BADGE_SIZE, accent if _owned else ThemeConstants.TERTIARY))
	for key in ["era_spatial_scale", "era_tone"]:
		var l := _label(str(m[key]), ThemeConstants.font_serif_light, 22, ThemeConstants.SECONDARY)
		l.autowrap_mode = TextServer.AUTOWRAP_WORD
		outer.add_child(l)
	outer.add_child(load("res://theme/components/tm_divider.tscn").instantiate())

	var scroll := ScrollContainer.new()
	scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
	outer.add_child(scroll)
	var columns := HBoxContainer.new()
	columns.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	scroll.add_child(columns)
	Roster.build(columns, _roster, _tiers)

	var back_btn = load("res://theme/components/tm_button.tscn").instantiate()
	back_btn.text = "BACK TO ERA LIBRARY"
	back_btn.style = 1
	back_btn.pressed.connect(func(): SceneRouter.go_back())
	outer.add_child(back_btn)


func _label(text: String, font: Font, size: int, color: Color) -> Label:
	var l := Label.new()
	l.text = text
	l.add_theme_font_override("font", font)
	l.add_theme_font_size_override("font_size", size)
	l.add_theme_color_override("font_color", color)
	return l


func qa_state() -> Dictionary:
	return {
		"scene": "era_detail",
		"tick": -1,
		"era_id": _era_id,
		"name": _name,
		"owned": _owned,
		"tiers": _tiers,
		"roster": _roster,
		"plants": [],
	}
