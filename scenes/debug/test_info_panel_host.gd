extends Control

const InfoPanelHostScene := preload("res://scenes/world/info_panel_host.tscn")

const REGIONS := {
	"r_01": {
		"region_id": "1", "tier": "home",
		"military": 72, "economy": 81, "tension": 38, "population": 64,
		"stability": 78, "capacity": 82,
	},
	"r_05": {
		"region_id": "5", "tier": "empty",
		"military": 12, "economy": 18, "tension": 22, "population": 8,
		"stability": 41, "capacity": 28,
	},
}

const FACTIONS := {
	"f_alpha": {
		"meta": {
			"id": "1", "label": "Dominion of Vaer",
			"archetype": "expansionist", "tech_tier": 3,
			"status": "Rising",
			"aggregates": {"military": 312, "economy": 248, "tension": 145, "population": 426},
		},
		"regions": [
			{"region_id": "r_01", "tier": "home"},
			{"region_id": "r_02", "tier": "frontier"},
			{"region_id": "r_05", "tier": "empty"},
		],
	},
	"f_beta": {
		"meta": {
			"id": "2", "label": "Kestrel Compact",
			"archetype": "balanced", "tech_tier": 2,
			"status": "Waning",
			"aggregates": {"military": 78, "economy": 95, "tension": 130, "population": 142},
		},
		"regions": [
			{"region_id": "r_13", "tier": "home"},
			{"region_id": "r_14", "tier": "frontier"},
		],
	},
}

var _host: Control
var _log_view: RichTextLabel


func _ready() -> void:
	_build_ui()


func _build_ui() -> void:
	var bg := ColorRect.new()
	bg.color = Color("#0A0D12")
	bg.set_anchors_preset(Control.PRESET_FULL_RECT)
	add_child(bg)

	var root := VBoxContainer.new()
	root.set_anchors_preset(Control.PRESET_FULL_RECT)
	root.offset_left = 24
	root.offset_top = 24
	root.offset_right = -24
	root.offset_bottom = -24
	root.add_theme_constant_override("separation", 16)
	add_child(root)

	var title := Label.new()
	title.text = "InfoPanelHost — swap behavior test"
	title.add_theme_font_size_override("font_size", 22)
	title.add_theme_color_override("font_color", Color("#e8e6e1"))
	root.add_child(title)

	var subtitle := Label.new()
	subtitle.text = "Buttons trigger open_region / open_faction / close. Same id = no-op refresh; different = 250ms cross-fade."
	subtitle.add_theme_font_size_override("font_size", 12)
	subtitle.add_theme_color_override("font_color", Color(0.91, 0.90, 0.88, 0.65))
	subtitle.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	root.add_child(subtitle)

	# Seed FactionPalette so vivacity differs.
	FactionPalette.update_counts({"f_alpha": 12, "f_beta": 4, "f_filler": 8})

	var btns := HBoxContainer.new()
	btns.add_theme_constant_override("separation", 8)
	root.add_child(btns)

	_add_button(btns, "open_region(r_01)", func(): _open_region("r_01", "f_alpha"))
	_add_button(btns, "open_region(r_05)", func(): _open_region("r_05", "f_alpha"))
	_add_button(btns, "open_faction(f_alpha)", func(): _open_faction("f_alpha"))
	_add_button(btns, "open_faction(f_beta)", func(): _open_faction("f_beta"))
	_add_button(btns, "close", func(): _host.close())

	var stage := HBoxContainer.new()
	stage.add_theme_constant_override("separation", 24)
	stage.size_flags_vertical = Control.SIZE_EXPAND_FILL
	root.add_child(stage)

	var host_box := PanelContainer.new()
	host_box.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	host_box.size_flags_vertical = Control.SIZE_EXPAND_FILL
	var host_style := StyleBoxFlat.new()
	host_style.bg_color = Color(0.91, 0.90, 0.88, 0.04)
	host_style.border_color = Color(0.91, 0.90, 0.88, 0.10)
	host_style.border_width_left = 1
	host_style.border_width_right = 1
	host_style.border_width_top = 1
	host_style.border_width_bottom = 1
	host_box.add_theme_stylebox_override("panel", host_style)
	stage.add_child(host_box)

	_host = InfoPanelHostScene.instantiate()
	_host.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_host.size_flags_vertical = Control.SIZE_EXPAND_FILL
	_host.panel_opened.connect(_on_panel_opened)
	_host.panel_closed.connect(_on_panel_closed)
	_host.open_region_requested.connect(func(rid: String): _open_region(rid, "f_alpha"))
	_host.open_faction_requested.connect(_open_faction)
	host_box.add_child(_host)

	_log_view = RichTextLabel.new()
	_log_view.bbcode_enabled = true
	_log_view.scroll_active = true
	_log_view.custom_minimum_size = Vector2(0, 120)
	_log_view.add_theme_font_size_override("normal_font_size", 12)
	_log_view.add_theme_color_override("default_color", Color(0.91, 0.90, 0.88, 0.7))
	_log_view.append_text("[i]events:[/i]\n")
	root.add_child(_log_view)


func _add_button(parent: Control, label: String, cb: Callable) -> void:
	var b := Button.new()
	b.text = label
	b.add_theme_font_size_override("font_size", 12)
	b.pressed.connect(cb)
	parent.add_child(b)


func _open_region(rid: String, fid: String) -> void:
	var meta: Dictionary = REGIONS.get(rid, {})
	if meta.is_empty():
		_log("missing region " + rid)
		return
	var faction_meta: Dictionary = FACTIONS[fid]["meta"]
	var color: Color = FactionPalette.get_display_color(fid)
	_host.open_region(rid, meta, fid, String(faction_meta.get("label", fid)), color,
		"Held by %s for 23y. Previously: —." % faction_meta.get("label", fid))


func _open_faction(fid: String) -> void:
	if not FACTIONS.has(fid):
		_log("missing faction " + fid)
		return
	var meta: Dictionary = FACTIONS[fid]["meta"]
	var rows: Array = FACTIONS[fid]["regions"]
	var color: Color = FactionPalette.get_display_color(fid)
	_host.open_faction(fid, meta, color, rows)


func _on_panel_opened(kind: String, id: String) -> void:
	_log("panel_opened → %s:%s" % [kind, id])


func _on_panel_closed() -> void:
	_log("panel_closed")


func _log(msg: String) -> void:
	print(msg)
	if _log_view != null:
		_log_view.append_text(msg + "\n")
