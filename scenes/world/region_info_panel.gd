extends PanelContainer

signal open_faction_requested(faction_id: String)

const TIER_COLORS := {
	"home":     Color("#d6b86a"),
	"frontier": Color("#9aa3ad"),
	"empty":    Color(0.91, 0.90, 0.88, 0.45),
}

var _region_id: String = ""
var _faction_id: String = ""

var _name_label: Label
var _tier_label: Label
var _bar_rows: Dictionary = {}
var _stability_value: Label
var _capacity_value: Label
var _faction_swatch: ColorRect
var _faction_name_label: Label
var _faction_button: Button
var _history_label: Label


func _ready() -> void:
	_build_ui()


func _build_ui() -> void:
	var style := StyleBoxFlat.new()
	style.bg_color = Color(0.04, 0.05, 0.07, 0.92)
	style.border_color = Color(0.91, 0.90, 0.88, 0.18)
	style.border_width_left = 1
	style.border_width_right = 1
	style.border_width_top = 1
	style.border_width_bottom = 1
	style.content_margin_left = 18
	style.content_margin_right = 18
	style.content_margin_top = 16
	style.content_margin_bottom = 16
	add_theme_stylebox_override("panel", style)

	custom_minimum_size = Vector2(360, 0)

	var root := VBoxContainer.new()
	root.add_theme_constant_override("separation", 12)
	add_child(root)

	# ── Header: name + tier badge ────────────────────────────────────────
	var header := HBoxContainer.new()
	header.add_theme_constant_override("separation", 12)
	root.add_child(header)

	_name_label = Label.new()
	_name_label.text = "—"
	_name_label.add_theme_font_size_override("font_size", 22)
	_name_label.add_theme_color_override("font_color", ThemeConstants.PRIMARY)
	_name_label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	header.add_child(_name_label)

	_tier_label = Label.new()
	_tier_label.text = "—"
	_tier_label.add_theme_font_size_override("font_size", 11)
	_tier_label.add_theme_color_override("font_color", TIER_COLORS["frontier"])
	header.add_child(_tier_label)

	root.add_child(_make_separator())

	# ── Field bars ───────────────────────────────────────────────────────
	for spec in [
		{"key": "military",   "label": "Military",   "low_warn": true},
		{"key": "economy",    "label": "Economy",    "low_warn": false, "high_good": true},
		{"key": "tension",    "label": "Tension",    "high_warn": true},
		{"key": "population", "label": "Population", "neutral": true},
	]:
		root.add_child(_make_bar_row(spec))

	root.add_child(_make_separator())

	# ── Composites row ───────────────────────────────────────────────────
	var comp := HBoxContainer.new()
	comp.add_theme_constant_override("separation", 24)
	root.add_child(comp)

	var stab_box := VBoxContainer.new()
	stab_box.add_theme_constant_override("separation", 2)
	stab_box.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	comp.add_child(stab_box)
	var stab_lbl := Label.new()
	stab_lbl.text = "STABILITY"
	stab_lbl.add_theme_font_size_override("font_size", 10)
	stab_lbl.add_theme_color_override("font_color", ThemeConstants.SECONDARY)
	stab_box.add_child(stab_lbl)
	_stability_value = Label.new()
	_stability_value.text = "—"
	_stability_value.add_theme_font_size_override("font_size", 16)
	_stability_value.add_theme_color_override("font_color", ThemeConstants.PRIMARY)
	stab_box.add_child(_stability_value)

	var cap_box := VBoxContainer.new()
	cap_box.add_theme_constant_override("separation", 2)
	cap_box.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	comp.add_child(cap_box)
	var cap_lbl := Label.new()
	cap_lbl.text = "CAPACITY"
	cap_lbl.add_theme_font_size_override("font_size", 10)
	cap_lbl.add_theme_color_override("font_color", ThemeConstants.SECONDARY)
	cap_box.add_child(cap_lbl)
	_capacity_value = Label.new()
	_capacity_value.text = "—"
	_capacity_value.add_theme_font_size_override("font_size", 16)
	_capacity_value.add_theme_color_override("font_color", ThemeConstants.PRIMARY)
	cap_box.add_child(_capacity_value)

	root.add_child(_make_separator())

	# ── Controlling faction strip ────────────────────────────────────────
	var fac_row := HBoxContainer.new()
	fac_row.add_theme_constant_override("separation", 10)
	root.add_child(fac_row)

	_faction_swatch = ColorRect.new()
	_faction_swatch.custom_minimum_size = Vector2(18, 18)
	_faction_swatch.color = Color(0.5, 0.5, 0.5, 0.5)
	fac_row.add_child(_faction_swatch)

	_faction_name_label = Label.new()
	_faction_name_label.text = "—"
	_faction_name_label.add_theme_font_size_override("font_size", 14)
	_faction_name_label.add_theme_color_override("font_color", ThemeConstants.PRIMARY)
	_faction_name_label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_faction_name_label.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	fac_row.add_child(_faction_name_label)

	_faction_button = Button.new()
	_faction_button.text = "Open faction"
	_faction_button.add_theme_font_size_override("font_size", 12)
	_faction_button.pressed.connect(_on_faction_button_pressed)
	fac_row.add_child(_faction_button)

	# ── Ownership history line ───────────────────────────────────────────
	_history_label = Label.new()
	_history_label.text = ""
	_history_label.add_theme_font_size_override("font_size", 12)
	_history_label.add_theme_color_override("font_color", ThemeConstants.SECONDARY)
	_history_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	root.add_child(_history_label)


func _make_separator() -> HSeparator:
	var sep := HSeparator.new()
	var sep_style := StyleBoxFlat.new()
	sep_style.bg_color = Color(0.91, 0.90, 0.88, 0.10)
	sep_style.content_margin_top = 0
	sep_style.content_margin_bottom = 0
	sep.add_theme_stylebox_override("separator", sep_style)
	sep.custom_minimum_size = Vector2(0, 1)
	return sep


func _make_bar_row(spec: Dictionary) -> Control:
	var row := HBoxContainer.new()
	row.add_theme_constant_override("separation", 10)

	var label := Label.new()
	label.text = spec["label"]
	label.add_theme_font_size_override("font_size", 12)
	label.add_theme_color_override("font_color", ThemeConstants.SECONDARY)
	label.custom_minimum_size = Vector2(80, 0)
	row.add_child(label)

	var bar_bg := PanelContainer.new()
	bar_bg.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	bar_bg.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	var bg_style := StyleBoxFlat.new()
	bg_style.bg_color = Color(0.91, 0.90, 0.88, 0.08)
	bar_bg.add_theme_stylebox_override("panel", bg_style)
	bar_bg.custom_minimum_size = Vector2(0, 8)
	row.add_child(bar_bg)

	var fill := ColorRect.new()
	fill.color = Color(0.91, 0.90, 0.88, 0.6)
	fill.size_flags_horizontal = Control.SIZE_FILL
	fill.anchor_left = 0.0
	fill.anchor_top = 0.0
	fill.anchor_right = 0.5
	fill.anchor_bottom = 1.0
	bar_bg.add_child(fill)

	var value_lbl := Label.new()
	value_lbl.text = "—"
	value_lbl.add_theme_font_size_override("font_size", 12)
	value_lbl.add_theme_color_override("font_color", ThemeConstants.PRIMARY)
	value_lbl.custom_minimum_size = Vector2(40, 0)
	value_lbl.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	row.add_child(value_lbl)

	_bar_rows[spec["key"]] = {
		"fill": fill,
		"bar_bg": bar_bg,
		"value": value_lbl,
		"spec": spec,
	}
	return row


func bind(region_meta: Dictionary, faction_id: String, faction_name: String,
		  faction_color: Color, ownership_line: String) -> void:
	_faction_id = faction_id

	_name_label.text = String(region_meta.get("name", "—"))
	var tier := String(region_meta.get("tier", "—"))
	_tier_label.text = tier.to_upper()
	_tier_label.add_theme_color_override("font_color",
		TIER_COLORS.get(tier, TIER_COLORS["frontier"]))

	_set_bar("military",   int(region_meta.get("military", 0)))
	_set_bar("economy",    int(region_meta.get("economy", 0)))
	_set_bar("tension",    int(region_meta.get("tension", 0)))
	_set_bar("population", int(region_meta.get("population", 0)))

	if region_meta.has("stability"):
		_stability_value.text = "%d" % int(region_meta["stability"])
	else:
		_stability_value.text = "—"
	if region_meta.has("capacity"):
		_capacity_value.text = "%d" % int(region_meta["capacity"])
	else:
		_capacity_value.text = "—"

	_faction_swatch.color = faction_color
	_faction_name_label.text = faction_name if faction_name != "" else faction_id
	_faction_button.disabled = (faction_id == "")
	_history_label.text = ownership_line
	# TEMP — Stage 11g Checkpoint K diagnostic
	print("[CP-K] region_panel.bind  rid=", _region_id, "  fid=", _faction_id,
		"  fname=", faction_name, "  button_disabled=", _faction_button.disabled)


func _set_bar(key: String, raw_value: int) -> void:
	if not _bar_rows.has(key):
		return
	var row: Dictionary = _bar_rows[key]
	var fill: ColorRect = row["fill"]
	var value_lbl: Label = row["value"]
	var spec: Dictionary = row["spec"]
	var v := clampi(raw_value, 0, 100)
	fill.anchor_right = float(v) / 100.0
	value_lbl.text = "%d" % v
	fill.color = _bar_color(spec, v)


func _bar_color(spec: Dictionary, v: int) -> Color:
	var t := float(v) / 100.0
	if spec.get("low_warn", false):
		# military: red when low, neutral when high
		var red := Color("#c44a3f")
		var neutral := Color(0.91, 0.90, 0.88, 0.7)
		return red.lerp(neutral, t)
	if spec.get("high_good", false):
		# economy: muted when low, green when high
		var muted := Color(0.91, 0.90, 0.88, 0.4)
		var green := Color("#4a9e6e")
		return muted.lerp(green, t)
	if spec.get("high_warn", false):
		# tension: neutral when low, accent when high
		var neutral := Color(0.91, 0.90, 0.88, 0.4)
		var accent := Color("#d6b86a")
		return neutral.lerp(accent, t)
	return Color(0.91, 0.90, 0.88, 0.6)


func _on_faction_button_pressed() -> void:
	# TEMP — Stage 11g Checkpoint K diagnostic
	print("[CP-K] open_faction button pressed  fid=", _faction_id)
	if _faction_id != "":
		open_faction_requested.emit(_faction_id)


func get_region_id() -> String:
	return _region_id


func set_region_id(rid: String) -> void:
	_region_id = rid
