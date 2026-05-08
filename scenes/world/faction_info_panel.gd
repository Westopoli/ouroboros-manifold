extends PanelContainer

signal open_region_requested(region_id: String)

const STATUS_COLORS := {
	"Rising":   Color("#4a9e6e"),
	"Stable":   Color(0.91, 0.90, 0.88, 0.70),
	"Waning":   Color("#d6b86a"),
	"Defeated": Color("#c44a3f"),
}
const REGION_LIST_VISIBLE_CAP := 8

var _faction_id: String = ""

var _name_label: Label
var _swatch: ColorRect
var _status_label: Label
var _identity_label: Label
var _aggregate_rows: Dictionary = {}
var _systems_value: Label
var _region_list_box: VBoxContainer
var _region_list_more: Label


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

	# ── Header: swatch + name + status badge ─────────────────────────────
	var header := HBoxContainer.new()
	header.add_theme_constant_override("separation", 10)
	root.add_child(header)

	_swatch = ColorRect.new()
	_swatch.custom_minimum_size = Vector2(22, 22)
	_swatch.color = Color(0.5, 0.5, 0.5, 0.5)
	_swatch.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	header.add_child(_swatch)

	_name_label = Label.new()
	_name_label.text = "—"
	_name_label.add_theme_font_size_override("font_size", 22)
	_name_label.add_theme_color_override("font_color", ThemeConstants.PRIMARY)
	_name_label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_name_label.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	header.add_child(_name_label)

	_status_label = Label.new()
	_status_label.text = "—"
	_status_label.add_theme_font_size_override("font_size", 11)
	_status_label.add_theme_color_override("font_color", STATUS_COLORS["Stable"])
	_status_label.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	header.add_child(_status_label)

	# ── Identity row: archetype + tech tier ──────────────────────────────
	_identity_label = Label.new()
	_identity_label.text = ""
	_identity_label.add_theme_font_size_override("font_size", 12)
	_identity_label.add_theme_color_override("font_color", ThemeConstants.SECONDARY)
	root.add_child(_identity_label)

	root.add_child(_make_separator())

	# ── Aggregates ───────────────────────────────────────────────────────
	var systems_row := HBoxContainer.new()
	systems_row.add_theme_constant_override("separation", 10)
	root.add_child(systems_row)
	var systems_lbl := Label.new()
	systems_lbl.text = "TOTAL SYSTEMS"
	systems_lbl.add_theme_font_size_override("font_size", 10)
	systems_lbl.add_theme_color_override("font_color", ThemeConstants.SECONDARY)
	systems_lbl.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	systems_row.add_child(systems_lbl)
	_systems_value = Label.new()
	_systems_value.text = "—"
	_systems_value.add_theme_font_size_override("font_size", 16)
	_systems_value.add_theme_color_override("font_color", ThemeConstants.PRIMARY)
	systems_row.add_child(_systems_value)

	var agg_header := Label.new()
	agg_header.text = "AGGREGATE"
	agg_header.add_theme_font_size_override("font_size", 10)
	agg_header.add_theme_color_override("font_color", ThemeConstants.SECONDARY)
	root.add_child(agg_header)

	for spec in [
		{"key": "military",   "label": "Military"},
		{"key": "economy",    "label": "Economy"},
		{"key": "tension",    "label": "Tension"},
		{"key": "population", "label": "Population"},
	]:
		root.add_child(_make_aggregate_row(spec))

	root.add_child(_make_separator())

	# ── Region list ──────────────────────────────────────────────────────
	var region_header := Label.new()
	region_header.text = "REGIONS"
	region_header.add_theme_font_size_override("font_size", 10)
	region_header.add_theme_color_override("font_color", ThemeConstants.SECONDARY)
	root.add_child(region_header)

	var scroll := ScrollContainer.new()
	scroll.custom_minimum_size = Vector2(0, 180)
	scroll.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	root.add_child(scroll)

	_region_list_box = VBoxContainer.new()
	_region_list_box.add_theme_constant_override("separation", 2)
	_region_list_box.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	scroll.add_child(_region_list_box)

	_region_list_more = Label.new()
	_region_list_more.text = ""
	_region_list_more.add_theme_font_size_override("font_size", 11)
	_region_list_more.add_theme_color_override("font_color", ThemeConstants.SECONDARY)
	root.add_child(_region_list_more)


func _make_separator() -> HSeparator:
	var sep := HSeparator.new()
	var sep_style := StyleBoxFlat.new()
	sep_style.bg_color = Color(0.91, 0.90, 0.88, 0.10)
	sep.add_theme_stylebox_override("separator", sep_style)
	sep.custom_minimum_size = Vector2(0, 1)
	return sep


func _make_aggregate_row(spec: Dictionary) -> Control:
	var row := HBoxContainer.new()
	row.add_theme_constant_override("separation", 10)

	var label := Label.new()
	label.text = spec["label"]
	label.add_theme_font_size_override("font_size", 12)
	label.add_theme_color_override("font_color", ThemeConstants.SECONDARY)
	label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	row.add_child(label)

	var value_lbl := Label.new()
	value_lbl.text = "—"
	value_lbl.add_theme_font_size_override("font_size", 13)
	value_lbl.add_theme_color_override("font_color", ThemeConstants.PRIMARY)
	value_lbl.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	row.add_child(value_lbl)

	_aggregate_rows[spec["key"]] = value_lbl
	return row


func bind(faction_meta: Dictionary, faction_color: Color, region_rows: Array) -> void:
	# region_rows: Array of {region_id, name, tier}
	_faction_id = String(faction_meta.get("id", ""))

	_swatch.color = faction_color
	_name_label.text = String(faction_meta.get("name", _faction_id))

	var status := String(faction_meta.get("status", "Stable"))
	_status_label.text = status.to_upper()
	_status_label.add_theme_color_override("font_color",
		STATUS_COLORS.get(status, STATUS_COLORS["Stable"]))

	var archetype := String(faction_meta.get("archetype", "—"))
	var tech_tier: int = int(faction_meta.get("tech_tier", 0))
	_identity_label.text = "%s · tech tier %d" % [archetype.capitalize(), tech_tier]

	_systems_value.text = "%d" % region_rows.size()

	var aggregates: Dictionary = faction_meta.get("aggregates", {})
	for key in ["military", "economy", "tension", "population"]:
		var lbl: Label = _aggregate_rows.get(key)
		if lbl == null:
			continue
		if aggregates.has(key):
			lbl.text = "%d" % int(aggregates[key])
		else:
			lbl.text = "—"

	_rebuild_region_list(region_rows)


func _rebuild_region_list(region_rows: Array) -> void:
	for c in _region_list_box.get_children():
		_region_list_box.remove_child(c)
		c.queue_free()

	var visible_count: int = mini(region_rows.size(), REGION_LIST_VISIBLE_CAP)
	for i in range(visible_count):
		var r: Dictionary = region_rows[i]
		_region_list_box.add_child(_build_region_row(r))

	var hidden := region_rows.size() - visible_count
	if hidden > 0:
		_region_list_more.text = "+%d more" % hidden
	else:
		_region_list_more.text = ""


func _build_region_row(row: Dictionary) -> Control:
	var btn := Button.new()
	var rid: String = String(row.get("region_id", ""))
	var rname: String = String(row.get("name", rid))
	var tier: String = String(row.get("tier", ""))
	btn.text = "%s    %s" % [rname, tier.to_upper()]
	btn.alignment = HORIZONTAL_ALIGNMENT_LEFT
	btn.flat = true
	btn.add_theme_font_size_override("font_size", 12)
	btn.add_theme_color_override("font_color", ThemeConstants.PRIMARY)
	btn.pressed.connect(func(): open_region_requested.emit(rid))
	return btn


func get_faction_id() -> String:
	return _faction_id
