extends Control

# VG-A A6: the objective list, top-left. S-075, S-104 / R-104-01. Sizes follow the legacy hud (15 primary, 12 secondary).

const PRIMARY_FONT := 15
const SECONDARY_FONT := 12
const BAR_W := 180.0
const BAR_H := 6.0
const STATUS := ["open", "complete", "failed"]
const TEXT := Color(0.92, 0.92, 0.92)
const DIM := Color(0.7, 0.7, 0.7)
const BAR_BG := Color(0.15, 0.15, 0.15, 0.8)
const BAR_PRIMARY := Color(0.95, 0.75, 0.2)
const BAR_SECONDARY := Color(0.4, 0.7, 0.9)
const BAR_FAILED := Color(0.8, 0.25, 0.25)

var _rows: Array = []
var _box := VBoxContainer.new()


func _ready() -> void:
	name = "Objectives"
	position = Vector2(12, 12)
	_box.add_theme_constant_override("separation", 6)
	add_child(_box)


func set_objectives(mission_objectives: Array, frame_objectives: Array) -> void:
	var by_i := {}
	for f in frame_objectives:
		by_i[int(f["i"])] = f
	var primaries: Array = []
	var secondaries: Array = []
	for m in mission_objectives:
		var i := int(m["i"])
		var f: Dictionary = by_i.get(i, {})
		var bar := clampf(float(f.get("progress", 0.0)), 0.0, 1.0)
		var done := clampi(int(f.get("done", 0)), 0, 2)
		var primary := bool(m.get("primary", false))
		var label := "Primary objective" if primary else "Objective %d" % (i + 1)
		var row := {"i": i, "primary": primary, "text": "%s  %d%%" % [label, roundi(bar * 100.0)],
			"bar": bar, "status": STATUS[done],
			"font_size": PRIMARY_FONT if primary else SECONDARY_FONT}
		(primaries if primary else secondaries).append(row)
	_rows = primaries + secondaries
	_rebuild()


func rows() -> Array:
	return _rows.duplicate(true)


func _rebuild() -> void:
	for c in _box.get_children():
		_box.remove_child(c)
		c.queue_free()
	for r in _rows:
		var v := VBoxContainer.new()
		v.add_theme_constant_override("separation", 2)
		var l := Label.new()
		l.text = r["text"] if r["status"] == "open" else "%s  %s" % [r["text"], String(r["status"]).to_upper()]
		l.add_theme_font_size_override("font_size", int(r["font_size"]))
		l.add_theme_color_override("font_color", TEXT if r["primary"] else DIM)
		v.add_child(l)
		var bg := ColorRect.new()
		bg.custom_minimum_size = Vector2(BAR_W, BAR_H)
		bg.color = BAR_BG
		var fill := ColorRect.new()
		fill.size = Vector2(BAR_W * float(r["bar"]), BAR_H)
		fill.color = BAR_FAILED if r["status"] == "failed" else (BAR_PRIMARY if r["primary"] else BAR_SECONDARY)
		bg.add_child(fill)
		v.add_child(bg)
		_box.add_child(v)
