extends Control

# VG-A A13: the reinforcement list. R-104-06 / R-126-05: one row per own structure, next unit icon, timer bar, HP.

const BAR_W := 120.0
const BAR_H := 6.0
const TEXT := Color(0.92, 0.92, 0.92)
const BAR_BG := Color(0.15, 0.15, 0.15, 0.8)
const BAR_FILL := Color(0.4, 0.8, 0.5)
const ICON_COLORS := [Color(0.9, 0.9, 0.9), Color(0.9, 0.6, 0.3), Color(0.5, 0.8, 0.9), Color(0.9, 0.4, 0.4), Color(0.8, 0.7, 0.3), Color(0.7, 0.5, 0.9)]

var _structs := {}
var _local := 0
var _tick := 0
var _box := VBoxContainer.new()


func _ready() -> void:
	name = "Reinforcements"
	_box.add_theme_constant_override("separation", 4)
	add_child(_box)


func set_frame(frame: Dictionary, local_faction: int) -> void:
	_local = local_faction
	_tick = int(frame.get("tick", 0))
	_structs.clear()
	for s in frame.get("structures", []):
		_structs[int(s["id"])] = (s as Dictionary).duplicate()
	_rebuild()


func apply_delta(delta: Dictionary, tick: int) -> void:
	_tick = tick
	for c in delta.get("structures_changed", []):
		var id := int(c["id"])
		if _structs.has(id):
			_structs[id].merge(c, true)
		else:
			_structs[id] = (c as Dictionary).duplicate()
	_rebuild()


func rows() -> Array:
	var out := []
	var ids := _structs.keys()
	ids.sort()
	for id in ids:
		var s: Dictionary = _structs[id]
		if int(s.get("owner", -1)) != _local:
			continue
		var period := float(s.get("period", 0))
		var timer := 0.0
		if period > 0.0:
			timer = clampf(1.0 - (float(s.get("nst", 0)) - float(_tick)) / period, 0.0, 1.0)
		out.append({"id": int(id), "next_type": int(s.get("next_type", -1)), "timer": timer, "hp": float(s.get("hp", 0.0))})
	return out


func _rebuild() -> void:
	if not is_inside_tree():
		return
	for c in _box.get_children():
		_box.remove_child(c)
		c.queue_free()
	for r in rows():
		var h := HBoxContainer.new()
		var icon := ColorRect.new()
		icon.custom_minimum_size = Vector2(14, 14)
		var t: int = r["next_type"]
		icon.color = ICON_COLORS[t % ICON_COLORS.size()] if t >= 0 else BAR_BG
		h.add_child(icon)
		var bg := ColorRect.new()
		bg.custom_minimum_size = Vector2(BAR_W, BAR_H)
		bg.color = BAR_BG
		var fill := ColorRect.new()
		fill.size = Vector2(BAR_W * float(r["timer"]), BAR_H)
		fill.color = BAR_FILL
		bg.add_child(fill)
		h.add_child(bg)
		var l := Label.new()
		l.text = "HP %d" % roundi(float(r["hp"]))
		l.add_theme_font_size_override("font_size", 12)
		l.add_theme_color_override("font_color", TEXT)
		h.add_child(l)
		_box.add_child(h)
