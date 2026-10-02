extends Control

const FactionInfoPanelScene := preload("res://scenes/world/faction_info_panel.tscn")

const MOCK_FACTIONS := [
	{
		"meta": {
			"id": "1", "label": "Dominion of Vaer",
			"archetype": "expansionist", "tech_tier": 3,
			"status": "Rising",
			"aggregates": {"military": 312, "economy": 248, "tension": 145, "population": 426},
		},
		"count": 12, "total": 24,
		"regions": [
			{"region_id": "r_01", "tier": "home"},
			{"region_id": "r_02", "tier": "frontier"},
			{"region_id": "r_03", "tier": "frontier"},
			{"region_id": "r_04", "tier": "frontier"},
			{"region_id": "r_05", "tier": "empty"},
			{"region_id": "r_06", "tier": "frontier"},
			{"region_id": "r_07", "tier": "frontier"},
			{"region_id": "r_08", "tier": "frontier"},
			{"region_id": "r_09", "tier": "empty"},
			{"region_id": "r_10", "tier": "frontier"},
			{"region_id": "r_11", "tier": "home"},
			{"region_id": "r_12", "tier": "empty"},
		],
	},
	{
		"meta": {
			"id": "2", "label": "Kestrel Compact",
			"archetype": "balanced", "tech_tier": 2,
			"status": "Waning",
			"aggregates": {"military": 78, "economy": 95, "tension": 130, "population": 142},
		},
		"count": 4, "total": 24,
		"regions": [
			{"region_id": "r_13", "tier": "home"},
			{"region_id": "r_14", "tier": "frontier"},
			{"region_id": "r_15", "tier": "frontier"},
			{"region_id": "r_16", "tier": "empty"},
		],
	},
	{
		"meta": {
			"id": "3", "label": "Outer Spiral",
			"archetype": "raider", "tech_tier": 1,
			"status": "Defeated",
			"aggregates": {},
		},
		"count": 0, "total": 24,
		"regions": [],
	},
]

var _signal_log: Array[String] = []
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
	title.text = "FactionInfoPanel — visual sanity test"
	title.add_theme_font_size_override("font_size", 22)
	title.add_theme_color_override("font_color", Color("#e8e6e1"))
	root.add_child(title)

	var subtitle := Label.new()
	subtitle.text = "Three factions: Rising dominant (12 regions, +N more truncation), Waning mid (4 regions, full list), Defeated (0 regions, empty list)."
	subtitle.add_theme_font_size_override("font_size", 12)
	subtitle.add_theme_color_override("font_color", Color(0.91, 0.90, 0.88, 0.65))
	subtitle.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	root.add_child(subtitle)

	# Seed FactionPalette
	var counts := {}
	var total: int = MOCK_FACTIONS[0]["total"]
	for f in MOCK_FACTIONS:
		counts[f["meta"]["id"]] = f["count"]
	var sum_seen: int = 0
	for v in counts.values():
		sum_seen += int(v)
	if sum_seen < total:
		counts["f_filler"] = total - sum_seen
	FactionPalette.update_counts(counts)

	var row := HBoxContainer.new()
	row.add_theme_constant_override("separation", 16)
	row.size_flags_vertical = Control.SIZE_EXPAND_FILL
	root.add_child(row)

	for f in MOCK_FACTIONS:
		var col := VBoxContainer.new()
		col.add_theme_constant_override("separation", 4)
		col.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		col.size_flags_vertical = Control.SIZE_SHRINK_BEGIN
		row.add_child(col)

		var panel := FactionInfoPanelScene.instantiate()
		panel.size_flags_horizontal = Control.SIZE_SHRINK_BEGIN
		panel.open_region_requested.connect(_on_open_region)
		col.add_child(panel)

		var fid: String = f["meta"]["id"]
		var faction_color: Color = FactionPalette.get_display_color(fid)
		panel.bind(f["meta"], faction_color, f["regions"])

		var caption := Label.new()
		caption.text = "%s · %d / %d regions · vivacity %.2f" % [
			f["meta"]["label"], f["count"], f["total"],
			FactionPalette.vivacity_for(fid),
		]
		caption.add_theme_font_size_override("font_size", 10)
		caption.add_theme_color_override("font_color", Color(0.91, 0.90, 0.88, 0.55))
		col.add_child(caption)

	_log_view = RichTextLabel.new()
	_log_view.bbcode_enabled = true
	_log_view.scroll_active = true
	_log_view.custom_minimum_size = Vector2(0, 80)
	_log_view.add_theme_font_size_override("normal_font_size", 12)
	_log_view.add_theme_color_override("default_color", Color(0.91, 0.90, 0.88, 0.7))
	_log_view.append_text("[i]click any region row — open_region_requested will be logged here.[/i]\n")
	root.add_child(_log_view)


func _on_open_region(region_id: String) -> void:
	var msg := "open_region_requested → %s" % region_id
	print(msg)
	_signal_log.append(msg)
	if _log_view != null:
		_log_view.append_text(msg + "\n")
