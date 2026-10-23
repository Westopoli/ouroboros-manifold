extends Node2D

const GroundPick := preload("res://scenes/ground3d/ground_pick.gd")

# Destruction (S-136, R-136-01/03): a 0.5 s death bloom, damage emitters, a drift along the last heading that decelerates,
# darkening over 3 to 5 s, fade out at 30 s, cap 150 wrecks. All numbers below are drafts.

const KILL_KIND := 2
const BLOOM_S := 0.5
const DEATH_BLOOM_ENERGY := 1.0
const HIT_BLOOM_ENERGY := 0.6
const DRIFT_SPEED := 120.0
const DRIFT_STOP_S := 6.0
const DARKEN_S := 4.0
const FADE_S := 30.0
const CAP := 150
const LOD_WRECKS := 60
const EMITTERS := 2
const WRECK_RADIUS := 10.0
const FLYER_RISE_WU := 150.0
const FALL_S := DRIFT_STOP_S
const FLARE_COLOR := Color(1.0, 0.85, 0.5)
const EMBER_COLOR := Color(1.0, 0.45, 0.1)
const WRECK_DARK := Color(0.18, 0.18, 0.2)

var _wrecks: Array = []
var _last_units: Dictionary = {}
var _scale := 0.25
var _camera := Vector2.ZERO
var _local := 0
var _projector := Callable()
var _terrain: Dictionary = {}
var _floors: Array = []
var _flyers: Array = []


func _init() -> void:
	name = "Deaths"


func bloom_duration() -> float:
	return BLOOM_S


func death_bloom_energy() -> float:
	return DEATH_BLOOM_ENERGY


func hit_bloom_energy() -> float:
	return HIT_BLOOM_ENERGY


func set_projector(projector: Callable) -> void:
	_projector = projector


func has_projector() -> bool:
	return _projector.is_valid()
	queue_redraw()


func set_ground(terrain: Dictionary, layer_floors_wu: Array, flyer_types: Array) -> void:
	_terrain = terrain
	_floors = layer_floors_wu
	_flyers = flyer_types


# Flat 2D (lane A): set_frame(frame, local_faction, world_scale, camera). Ground era: set_frame(frame, mission, local_faction)
# with set_projector set.
func set_frame(frame: Dictionary, a: Variant, b: Variant = null, camera: Vector2 = Vector2.ZERO) -> void:
	if a is Dictionary:
		_local = int(b)
	else:
		_local = int(a)
		_scale = float(b)
		_camera = camera
	for ev in frame.get("events", []):
		if int(ev[0]) != KILL_KIND:
			continue
		var id := int(ev[1])
		if not _last_units.has(id) or _find(id) >= 0:
			continue
		var u: Dictionary = _last_units[id]
		_wrecks.append({"id": id, "origin": Vector2(float(u["x"]), float(u["y"])), "facing": float(u.get("facing", 0.0)), "age": 0.0, "up": _rise(u)})
	while _wrecks.size() > CAP:
		_wrecks.pop_front()
	_last_units = {}
	for u in frame.get("units", []):
		_last_units[int(u["id"])] = u
	queue_redraw()


func _rise(u: Dictionary) -> float:
	if not _flyers.has(int(u.get("type", -1))):
		return -1.0
	var layer := int(u.get("layer", 0))
	return (float(_floors[layer]) if layer < _floors.size() else 0.0) + FLYER_RISE_WU


func screen_points() -> Array:
	var out := []
	for w in _wrecks:
		out.append(_to_screen(wreck_position(int(w["id"]))))
	return out


func wreck_height(id: int) -> float:
	var w: Dictionary = _wrecks[_find(id)]
	var p := wreck_position(id)
	var ground := GroundPick.height_at(_terrain, p.x, p.y)
	var up: float = w["up"]
	if up < 0.0:
		return ground
	return lerpf(up, ground, clampf(float(w["age"]) / FALL_S, 0.0, 1.0))


func wreck_shadow(id: int) -> bool:
	var w: Dictionary = _wrecks[_find(id)]
	return float(w["up"]) >= 0.0 and float(w["age"]) < FALL_S


func advance(dt_s: float) -> void:
	for w in _wrecks:
		w["age"] += dt_s
	_wrecks = _wrecks.filter(func(w): return w["age"] < FADE_S)
	queue_redraw()


func wrecks() -> Array:
	var out := []
	for w in _wrecks:
		out.append({"id": w["id"]})
	return out


func wreck_position(id: int) -> Vector2:
	var w: Dictionary = _wrecks[_find(id)]
	var t := minf(float(w["age"]), DRIFT_STOP_S)
	var dist := DRIFT_SPEED * (t - t * t / (2.0 * DRIFT_STOP_S))
	return w["origin"] + Vector2.RIGHT.rotated(w["facing"]) * dist


func wreck_speed(id: int) -> float:
	var w: Dictionary = _wrecks[_find(id)]
	return DRIFT_SPEED * maxf(0.0, 1.0 - float(w["age"]) / DRIFT_STOP_S)


func wreck_darkness(id: int) -> float:
	var w: Dictionary = _wrecks[_find(id)]
	return clampf(float(w["age"]) / DARKEN_S, 0.0, 1.0)


func wreck_emitters(id: int) -> int:
	_find(id)
	return EMITTERS


func _find(id: int) -> int:
	for i in _wrecks.size():
		if _wrecks[i]["id"] == id:
			return i
	return -1


func _to_screen(w: Vector2) -> Vector2:
	if _projector.is_valid():
		return _projector.call(w)
	return (w - _camera) * _scale + Vector2(960.0, 540.0)


func _draw() -> void:
	var lod := _wrecks.size() > LOD_WRECKS
	for w in _wrecks:
		var id: int = w["id"]
		var c := _to_screen(wreck_position(id))
		var r := WRECK_RADIUS * _scale * 4.0
		var age: float = w["age"]
		var fade := clampf((FADE_S - age) / 3.0, 0.0, 1.0)
		var body := FLARE_COLOR.lerp(WRECK_DARK, wreck_darkness(id))
		body.a = fade
		if wreck_shadow(id):
			draw_circle(c, r, Color(0.0, 0.0, 0.0, 0.35 * fade))
		draw_circle(c, r, body)
		if age < BLOOM_S:
			var k := 1.0 - age / BLOOM_S
			draw_circle(c, r * (1.5 + 2.0 * (1.0 - k)), Color(FLARE_COLOR, DEATH_BLOOM_ENERGY * k))
		if not lod and fade > 0.0:
			for e in EMITTERS:
				var ang := float(e) * PI + age * 2.0
				draw_circle(c + Vector2.from_angle(ang) * r * 0.6, r * 0.3, Color(EMBER_COLOR, 0.8 * fade))
