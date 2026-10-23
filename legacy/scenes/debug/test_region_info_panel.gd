extends Control

const RegionInfoPanelScene := preload("res://scenes/world/region_info_panel.tscn")

const MOCK_REGIONS := [
	{
		"meta": {
			"region_id": "1", "tier": "home",
			"military": 78, "economy": 84, "tension": 22, "population": 92,
			"stability": 71, "capacity": 88,
		},
		"faction_id": "f_alpha", "faction_name": "Dominion of Vaer",
		"faction_count": 12, "total": 24,
		"history": "Held by Dominion of Vaer for 142y.",
	},
	{
		"meta": {
			"region_id": "3", "tier": "frontier",
			"military": 38, "economy": 41, "tension": 78, "population": 56,
			"stability": 35, "capacity": 60,
		},
		"faction_id": "f_beta", "faction_name": "Kestrel Compact",
		"faction_count": 4, "total": 24,
		"history": "Held by Kestrel Compact for 23y. Previously: Outer Spiral, Dominion of Vaer.",
	},
	{
		"meta": {
			"region_id": "5", "tier": "empty",
			"military": 12, "economy": 18, "tension": 44, "population": 28,
		},
		"faction_id": "f_gamma", "faction_name": "Pellian Order",
		"faction_count": 1, "total": 24,
		"history": "Held by Pellian Order for 8y. Previously: Kestrel Compact.",
	},
]

var _panels: Array[Node] = []
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
	title.text = "RegionInfoPanel — visual sanity test"
	title.add_theme_font_size_override("font_size", 22)
	title.add_theme_color_override("font_color", Color("#e8e6e1"))
	root.add_child(title)

	var subtitle := Label.new()
	subtitle.text = "Three mock regions: home (high stats), contested frontier (high tension), empty (sparse). Faction-strip swatch uses FactionPalette vivacity scaling."
	subtitle.add_theme_font_size_override("font_size", 12)
	subtitle.add_theme_color_override("font_color", Color(0.91, 0.90, 0.88, 0.65))
	subtitle.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	root.add_child(subtitle)

	# Row of panels
	var row := HBoxContainer.new()
	row.add_theme_constant_override("separation", 16)
	row.size_flags_vertical = Control.SIZE_EXPAND_FILL
	root.add_child(row)

	# Seed FactionPalette so the swatches are vivified
	var counts := {}
	var total := MOCK_REGIONS[0]["total"]
	for r in MOCK_REGIONS:
		counts[r["faction_id"]] = r["faction_count"]
	# Add a fourth faction's count to make the totals plausible
	counts["f_filler"] = total - counts.values().reduce(func(a, b): return a + b, 0)
	FactionPalette.update_counts(counts)

	for r in MOCK_REGIONS:
		var col := VBoxContainer.new()
		col.add_theme_constant_override("separation", 4)
		col.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		col.size_flags_vertical = Control.SIZE_SHRINK_BEGIN
		row.add_child(col)

		var panel := RegionInfoPanelScene.instantiate()
		panel.size_flags_horizontal = Control.SIZE_SHRINK_BEGIN
		panel.open_faction_requested.connect(_on_open_faction)
		col.add_child(panel)
		_panels.append(panel)

		var fid: String = r["faction_id"]
		var faction_color: Color = FactionPalette.get_display_color(fid)
		panel.bind(r["meta"], fid, r["faction_name"], faction_color, r["history"])

		var caption := Label.new()
		caption.text = "%s · %d / %d regions · vivacity %.2f" % [
			r["faction_name"], r["faction_count"], r["total"],
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
	_log_view.append_text("[i]click 'Open faction' on any panel — signal will be logged here.[/i]\n")
	root.add_child(_log_view)


func _on_open_faction(faction_id: String) -> void:
	var msg := "open_faction_requested → %s" % faction_id
	print(msg)
	_signal_log.append(msg)
	if _log_view != null:
		_log_view.append_text(msg + "\n")
