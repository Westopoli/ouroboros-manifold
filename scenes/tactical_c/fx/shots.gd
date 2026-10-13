extends Node2D

# VG-A A9: shots from fire events (S-134, R-134-05), drawn when the shooter or the target is visible, from the visible end.
# Frame events: [kind, a, b, tick], kind 0 = fire (a shooter, b target).

const SCREEN := Vector2(1920.0, 1080.0)
const FIRE := 0
const STUB := 60.0
const BLOOM_R := 18.0
# categories by unit type: 0 Raider kinetic, 1 Interceptor missile, 2 Vanguard plasma, 3 Warden beam, 4 Bombard arc, 5 Bastion dual kinetic
# DRAFT volley sizes per category (R-134-05 names volleys, not counts)
const VOLLEY := [1, 3, 1, 1, 3, 2]
const COLORS := [Color(1, 0.9, 0.5), Color(1, 0.6, 0.3), Color(0.6, 0.8, 1), Color(0.5, 1, 0.8), Color(1, 0.5, 0.4), Color(1, 0.85, 0.6)]

var _scale := 0.25
var _camera := Vector2.ZERO
var _shots: Array = []
var _blooms: Array = []
var _hp: Dictionary = {}
var _proj := Callable()


func shot_category(type: int) -> int:
	return clampi(type, 0, 5)


func shots() -> Array:
	return _shots


func in_flight() -> Array:
	return _shots


func blooms() -> Array:
	return _blooms


func set_projector(projector: Callable) -> void:
	_proj = projector


func screen_points() -> Array:
	var pts: Array = []
	for s in _shots:
		pts.append(s["from"])
		pts.append(s["to"])
	for b in _blooms:
		pts.append(b["center"])
	return pts


func _to_screen(w: Vector2) -> Vector2:
	if _proj.is_valid():
		return _proj.call(w)
	return (w - _camera) * _scale + SCREEN * 0.5


func _on_screen(p: Vector2) -> bool:
	return Rect2(Vector2.ZERO, SCREEN).has_point(p)


# Two call shapes: (frame, local_faction, world_scale, camera) on the 2D view, (frame, mission, local_faction) with a projector.
func set_frame(frame: Dictionary, second, third = null, camera: Vector2 = Vector2.ZERO) -> void:
	var local_faction: int
	if second is Dictionary:
		local_faction = int(third)
	else:
		local_faction = int(second)
		_scale = float(third)
		_camera = camera
	var has_vis: bool = frame.has("visible")
	var by_id := {}
	for u in frame.get("units", []):
		by_id[int(u["id"])] = u
	var vis := {}
	for v in frame.get("visible", {}).get(str(local_faction), []):
		vis[int(v)] = true
	if not has_vis:
		for id in by_id:
			vis[id] = true
	_blooms = []
	var hp := {}
	for id in by_id:
		var u: Dictionary = by_id[id]
		hp[id] = float(u.get("hp", 0.0))
		if _hp.has(id) and hp[id] < _hp[id] and vis.has(id):
			var c := _to_screen(Vector2(float(u["x"]), float(u["y"])))
			if _on_screen(c):
				_blooms.append({"center": c})
	_hp = hp
	_shots = []
	for e in frame.get("events", []):
		if int(e[0]) != FIRE:
			continue
		var sh = by_id.get(int(e[1]))
		var tg = by_id.get(int(e[2]))
		if sh == null or tg == null:
			continue
		var sv: bool = vis.has(int(e[1]))
		var tv: bool = vis.has(int(e[2]))
		if not sv and not tv:
			continue
		var a := _to_screen(Vector2(float(sh["x"]), float(sh["y"])))
		var b := _to_screen(Vector2(float(tg["x"]), float(tg["y"])))
		if not _on_screen(a) and not _on_screen(b):
			continue
		var from := a
		if not sv:
			from = b + (a - b).normalized() * STUB
		var cat := shot_category(int(sh.get("type", 0)))
		_shots.append({"category": cat, "volley": VOLLEY[cat], "from": from, "to": b, "origin_visible": sv})
	queue_redraw()


func _draw() -> void:
	for s in _shots:
		var cat: int = s["category"]
		var f: Vector2 = s["from"]
		var t: Vector2 = s["to"]
		var n: int = s["volley"]
		var side := (t - f).orthogonal().normalized() * 3.0
		for i in range(n):
			var off := side * (float(i) - float(n - 1) * 0.5)
			if cat == 3:
				draw_line(f + off, t + off, COLORS[cat], 3.0)
			else:
				draw_line(f + off, t + off, COLORS[cat], 1.5)
				draw_circle(t + off, 2.5, COLORS[cat])
	for b in _blooms:
		draw_circle(b["center"], BLOOM_R, Color(1, 0.8, 0.4, 0.5))
