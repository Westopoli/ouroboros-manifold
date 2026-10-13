extends Control

# R-105-07 the Comb: holding a bound digit blooms the layer strip into one bar per occupied layer, sized by count.
const BAR_W := 28.0
const BAR_GAP := 6.0
const BAR_MAX_H := 120.0

var _open := false
var _bars: Array = []
var _ids_by_layer := {}
var _drag_from := -1
var _drag_to := -1


func open(group_ids: Array, frame: Dictionary) -> bool:
	close()
	var want := {}
	for id in group_ids:
		want[int(id)] = true
	for u in frame.get("units", []):
		if want.has(int(u["id"])):
			var l := int(u.get("layer", 1))
			if not _ids_by_layer.has(l):
				_ids_by_layer[l] = []
			_ids_by_layer[l].append(int(u["id"]))
	if _ids_by_layer.size() < 2:
		_ids_by_layer.clear()
		return false
	var layers: Array = _ids_by_layer.keys()
	layers.sort()
	for l in layers:
		_bars.append({"layer": l, "count": _ids_by_layer[l].size()})
	_open = true
	queue_redraw()
	return true


func is_open() -> bool:
	return _open


func bars() -> Array:
	return _bars.duplicate(true)


func drag(from_layer: int, to_layer: int) -> Array:
	var lo := mini(from_layer, to_layer)
	var hi := maxi(from_layer, to_layer)
	_drag_from = lo
	_drag_to = hi
	var out: Array = []
	for b in _bars:
		var l := int(b["layer"])
		if l >= lo and l <= hi:
			out.append_array(_ids_by_layer[l])
	queue_redraw()
	return out


func release() -> void:
	close()


func close() -> void:
	_open = false
	_bars.clear()
	_ids_by_layer.clear()
	_drag_from = -1
	_drag_to = -1
	queue_redraw()


func _draw() -> void:
	if not _open:
		return
	var top := 1
	for b in _bars:
		top = maxi(top, int(b["count"]))
	for i in _bars.size():
		var b: Dictionary = _bars[i]
		var h := BAR_MAX_H * float(b["count"]) / float(top)
		var l := int(b["layer"])
		var hot := _drag_from >= 0 and l >= _drag_from and l <= _drag_to
		var r := Rect2(i * (BAR_W + BAR_GAP), BAR_MAX_H - h, BAR_W, h)
		draw_rect(r, Color(0.95, 0.8, 0.3) if hot else Color(0.4, 0.6, 0.8))
		draw_string(ThemeDB.fallback_font, r.position + Vector2(4, -4), "%d" % l)
