extends Node2D

# VG-A A14 (S-135): a ring, glow and pulse on the unit for each ability event of the frame.
const SCREEN_CENTER := Vector2(960.0, 540.0)
const EVENT_ABILITY := 1
const RING_COLOR := Color(0.5, 0.85, 1.0)
const RING_WIDTH := 3.0
const RING_SEGMENTS := 64
const GLOW_PX := 14.0

var _effects: Array = []
var _projector := Callable()


func _ready() -> void:
	name = "Abilities"


func set_projector(projector: Callable) -> void:
	_projector = projector


func has_projector() -> bool:
	return _projector.is_valid()


func set_frame(frame: Dictionary, _local_faction: int, world_scale: float, camera: Vector2) -> void:
	_effects = []
	var units := {}
	for u in frame.get("units", []):
		units[int(u["id"])] = u
	var aoe := {}
	for p in frame.get("profiles", []):
		aoe[int(p["ability"])] = float(p.get("aoe", 0.0))
	for ev in frame.get("events", []):
		if int(ev[0]) != EVENT_ABILITY or not units.has(int(ev[1])):
			continue
		var u: Dictionary = units[int(ev[1])]
		var ability := int(ev[2])
		var w := Vector2(float(u["x"]), float(u["y"]))
		_effects.append({"unit": int(ev[1]), "ability": ability,
			"center": _projector.call(w) if _projector.is_valid() else (w - camera) * world_scale + SCREEN_CENTER,
			"radius": float(aoe.get(ability, 0.0)) * world_scale})
	queue_redraw()


func effects() -> Array:
	return _effects


func _draw() -> void:
	for e in _effects:
		var c: Vector2 = e["center"]
		var r: float = e["radius"]
		draw_circle(c, GLOW_PX, Color(RING_COLOR, 0.35))
		if r > 0.0:
			draw_arc(c, r, 0.0, TAU, RING_SEGMENTS, Color(RING_COLOR, 0.7), RING_WIDTH)
			draw_circle(c, r, Color(RING_COLOR, 0.08))
