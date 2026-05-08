extends Node

signal colors_changed

var _counts: Dictionary = {}
var _total: int = 0


func update_counts(counts: Dictionary) -> void:
	_counts = counts.duplicate()
	var total := 0
	for fid in _counts:
		total += int(_counts[fid])
	_total = total
	colors_changed.emit()


func get_display_color(faction_id: String) -> Color:
	var n := int(_counts.get(faction_id, 0))
	var v := _vivacity(n, _total)
	var s := lerpf(0.20, 0.85, v)
	var val := lerpf(0.55, 0.95, v)
	var a := lerpf(0.55, 1.0, v)
	var c := Color.from_hsv(hue_for(faction_id), s, val)
	c.a = a
	return c


func hue_for(faction_id: String) -> float:
	return float(posmod(faction_id.hash(), 360)) / 360.0


func vivacity_for(faction_id: String) -> float:
	var n := int(_counts.get(faction_id, 0))
	return _vivacity(n, _total)


func _vivacity(region_count: int, total_regions: int) -> float:
	var r := float(region_count) / float(max(total_regions, 1))
	return clampf(0.25 + 0.75 * smoothstep(0.04, 0.45, r), 0.25, 1.0)


func get_total() -> int:
	return _total


func get_count(faction_id: String) -> int:
	return int(_counts.get(faction_id, 0))
