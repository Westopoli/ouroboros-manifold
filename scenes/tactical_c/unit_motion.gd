extends Node

var _prev := {}
var _cur := {}


func push_frame(frame: Dictionary) -> void:
	_prev = _cur
	_cur = {}
	for u in frame.get("units", []):
		_cur[int(u["id"])] = Vector3(float(u["x"]), float(u["y"]), float(u.get("facing", 0.0)))


func has_unit(id: int) -> bool:
	return _cur.has(id)


func position_at(id: int, alpha: float) -> Vector2:
	var c: Vector3 = _cur[id]
	if not _prev.has(id):
		return Vector2(c.x, c.y)
	var p: Vector3 = _prev[id]
	return Vector2(p.x, p.y).lerp(Vector2(c.x, c.y), alpha)


func facing_at(id: int, alpha: float) -> float:
	var c: Vector3 = _cur[id]
	if not _prev.has(id):
		return c.z
	var p: Vector3 = _prev[id]
	return lerp_angle(p.z, c.z, alpha)
