extends Control

const FACTION_IDS := ["f_dominion", "f_kestrel", "f_pellian", "f_outer_spiral", "f_remnant"]

var _swatch_grid: GridContainer
var _print_log: RichTextLabel
var _scenario_index: int = 0

const SCENARIOS := [
	{
		"label": "Scenario 1 — uneven (Dominion dominant)",
		"counts": {"f_dominion": 12, "f_kestrel": 6, "f_pellian": 3, "f_outer_spiral": 2, "f_remnant": 1},
	},
	{
		"label": "Scenario 2 — flipped (Remnant dominant)",
		"counts": {"f_dominion": 1, "f_kestrel": 2, "f_pellian": 3, "f_outer_spiral": 6, "f_remnant": 12},
	},
	{
		"label": "Scenario 3 — even split",
		"counts": {"f_dominion": 5, "f_kestrel": 5, "f_pellian": 5, "f_outer_spiral": 5, "f_remnant": 5},
	},
	{
		"label": "Scenario 4 — single dominant, others near zero",
		"counts": {"f_dominion": 20, "f_kestrel": 1, "f_pellian": 1, "f_outer_spiral": 1, "f_remnant": 1},
	},
]


func _ready() -> void:
	_build_ui()
	_dump_all_scenarios()
	_apply_scenario(0)


func _dump_all_scenarios() -> void:
	for i in range(SCENARIOS.size()):
		var s: Dictionary = SCENARIOS[i]
		FactionPalette.update_counts(s["counts"])
		_scenario_index = i
		_print_to_console()


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
	title.text = "FactionPalette — vivacity sanity test"
	title.add_theme_font_size_override("font_size", 22)
	title.add_theme_color_override("font_color", Color("#e8e6e1"))
	root.add_child(title)

	var btn_row := HBoxContainer.new()
	btn_row.add_theme_constant_override("separation", 8)
	root.add_child(btn_row)

	for i in range(SCENARIOS.size()):
		var b := Button.new()
		b.text = "Scenario %d" % (i + 1)
		var idx := i
		b.pressed.connect(func(): _apply_scenario(idx))
		btn_row.add_child(b)

	var print_btn := Button.new()
	print_btn.text = "Print current to console"
	print_btn.pressed.connect(_print_to_console)
	btn_row.add_child(print_btn)

	_swatch_grid = GridContainer.new()
	_swatch_grid.columns = FACTION_IDS.size()
	_swatch_grid.add_theme_constant_override("h_separation", 12)
	_swatch_grid.add_theme_constant_override("v_separation", 8)
	root.add_child(_swatch_grid)

	_print_log = RichTextLabel.new()
	_print_log.bbcode_enabled = true
	_print_log.fit_content = false
	_print_log.scroll_active = true
	_print_log.size_flags_vertical = Control.SIZE_EXPAND_FILL
	_print_log.add_theme_font_size_override("normal_font_size", 13)
	_print_log.add_theme_color_override("default_color", Color("#e8e6e1"))
	root.add_child(_print_log)


func _apply_scenario(idx: int) -> void:
	_scenario_index = idx
	var scenario: Dictionary = SCENARIOS[idx]
	FactionPalette.update_counts(scenario["counts"])
	_rebuild_swatches()
	_log_scenario(scenario)
	_print_to_console()


func _rebuild_swatches() -> void:
	for child in _swatch_grid.get_children():
		_swatch_grid.remove_child(child)
		child.queue_free()
	for fid in FACTION_IDS:
		_swatch_grid.add_child(_build_swatch_card(fid))


func _build_swatch_card(faction_id: String) -> Control:
	var col := VBoxContainer.new()
	col.custom_minimum_size = Vector2(180, 140)
	col.add_theme_constant_override("separation", 4)

	var c := FactionPalette.get_display_color(faction_id)
	var swatch := ColorRect.new()
	swatch.color = c
	swatch.custom_minimum_size = Vector2(180, 60)
	col.add_child(swatch)

	var name_lbl := Label.new()
	name_lbl.text = faction_id
	name_lbl.add_theme_font_size_override("font_size", 14)
	name_lbl.add_theme_color_override("font_color", Color("#e8e6e1"))
	col.add_child(name_lbl)

	var count := FactionPalette.get_count(faction_id)
	var total := FactionPalette.get_total()
	var detail := Label.new()
	detail.text = "count %d / %d  (%.1f%%)\nhue %.0f°  S %.2f V %.2f A %.2f\n#%s" % [
		count,
		total,
		100.0 * float(count) / float(max(total, 1)),
		FactionPalette.hue_for(faction_id) * 360.0,
		c.s,
		c.v,
		c.a,
		c.to_html(true),
	]
	detail.add_theme_font_size_override("font_size", 11)
	detail.add_theme_color_override("font_color", Color(0.91, 0.90, 0.88, 0.75))
	col.add_child(detail)

	return col


func _log_scenario(scenario: Dictionary) -> void:
	_print_log.append_text("\n[b]%s[/b]\n" % scenario["label"])


func _print_to_console() -> void:
	print("")
	print("=== FactionPalette dump  (scenario %d) ===" % (_scenario_index + 1))
	print("total regions: %d" % FactionPalette.get_total())
	print("%-18s %5s  %5s  %6s  %5s  %5s  %5s  %s" % [
		"faction_id", "count", "frac", "hue°", "sat", "val", "alpha", "hex",
	])
	for fid in FACTION_IDS:
		var c := FactionPalette.get_display_color(fid)
		var n := FactionPalette.get_count(fid)
		var t := FactionPalette.get_total()
		print("%-18s %5d  %5.2f  %6.1f  %5.2f  %5.2f  %5.2f  #%s" % [
			fid,
			n,
			float(n) / float(max(t, 1)),
			FactionPalette.hue_for(fid) * 360.0,
			c.s,
			c.v,
			c.a,
			c.to_html(true),
		])
		var line := "[color=#%s]████[/color]  %s   count=%d  vivacity=%.2f  hex=#%s\n" % [
			c.to_html(true),
			fid,
			n,
			FactionPalette.vivacity_for(fid),
			c.to_html(true),
		]
		_print_log.append_text(line)
