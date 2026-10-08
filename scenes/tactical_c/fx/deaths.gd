extends Node2D

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
const FLARE_COLOR := Color(1.0, 0.85, 0.5)
const EMBER_COLOR := Color(1.0, 0.45, 0.1)
const WRECK_DARK := Color(0.18, 0.18, 0.2)

var _wrecks: Array = []
var _last_units: Dictionary = {}
var _scale := 0.25
var _camera := Vector2.ZERO
var _local := 0


func _init() -> void:
	name = "Deaths"


func bloom_duration() -> float:
	return BLOOM_S


func death_bloom_energy() -> float:
	return DEATH_BLOOM_ENERGY


func hit_bloom_energy() -> float:
	return HIT_BLOOM_ENERGY


func set_frame(frame: Dictionary, local_faction: int, world_scale: float, camera: Vector2) -> void:
	_local = local_faction
	_scale = world_scale
	_camera = camera
	for ev in frame.get("events", []):
		if int(ev[0]) != KILL_KIND:
			continue
		var id := int(ev[1])
		if not _last_units.has(id) or _find(id) >= 0:
			continue
		var u: Dictionary = _last_units[id]
		_wrecks.append({"id": id, "origin": Vector2(float(u["x"]), float(u["y"])), "facing": float(u.get("facing", 0.0)), "age": 0.0})
	while _wrecks.size() > CAP:
		_wrecks.pop_front()
	_last_units = {}
	for u in frame.get("units", []):
		_last_units[int(u["id"])] = u
	queue_redraw()


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
		draw_circle(c, r, body)
		if age < BLOOM_S:
			var k := 1.0 - age / BLOOM_S
			draw_circle(c, r * (1.5 + 2.0 * (1.0 - k)), Color(FLARE_COLOR, DEATH_BLOOM_ENERGY * k))
		if not lod and fade > 0.0:
			for e in EMITTERS:
				var ang := float(e) * PI + age * 2.0
				draw_circle(c + Vector2.from_angle(ang) * r * 0.6, r * 0.3, Color(EMBER_COLOR, 0.8 * fade))
