## Infers normal attack timing from unit state and spawns projectile visuals.
## Does NOT receive per-attack events from the engine — the delta stream would
## explode at 200v200. Instead, tracks each unit's attack_target and runs a local
## timer at the unit's attack_interval. When the timer fires and the target is in
## range, a projectile visual is spawned via ProjectileRenderer.
##
## See also: snapshot_serializer.py — sends attack_target, attack_interval, attack_range
extends Node3D

const VISUAL_CONFIGS := {
	"raider":      {"category": "projectile", "speed": 1200.0, "scale": 0.3, "volley": 1, "stagger": 0.0},
	"interceptor": {"category": "projectile", "speed": 1000.0, "scale": 0.25, "volley": 1, "stagger": 0.0},
	"vanguard":    {"category": "projectile", "speed": 800.0,  "scale": 0.5, "volley": 1, "stagger": 0.0},
	"warden":      {"category": "beam", "beam_duration": 0.4, "beam_thickness": 6.0},
	"bombard":     {"category": "projectile", "speed": 600.0,  "scale": 0.6, "volley": 5, "stagger": 0.08},
	"bastion":     {"category": "projectile", "speed": 500.0,  "scale": 0.7, "volley": 3, "stagger": 0.06},
}

var _unit_timers: Dictionary = {}  # uid → float (countdown)
var _pending_volleys: Array[Dictionary] = []  # deferred stagger spawns
var _projectile_renderer: Node3D
var _beam_renderer: Node3D
var _area_pulse_renderer: Node3D

# See also: scenes/tactical/unit_renderer.gd — squad-pos formula source
@onready var _unit_renderer: Node3D = $"../UnitRenderer"

var camera_zoom: float = 0.0

var _peak_active: int = 0
var _total_spawned: int = 0


func _ready() -> void:
	_projectile_renderer = preload("res://scenes/tactical/visuals/projectile_renderer.gd").new()
	_projectile_renderer.name = "ProjectileRenderer"
	add_child(_projectile_renderer)

	_beam_renderer = preload("res://scenes/tactical/visuals/beam_renderer.gd").new()
	_beam_renderer.name = "BeamRenderer"
	add_child(_beam_renderer)

	_area_pulse_renderer = preload("res://scenes/tactical/visuals/area_pulse_renderer.gd").new()
	_area_pulse_renderer.name = "AreaPulseRenderer"
	add_child(_area_pulse_renderer)


func _process(delta: float) -> void:
	_process_attacks(delta)
	_process_volleys(delta)

	var current: int = _projectile_renderer.get_active_count() + _beam_renderer.get_active_count() + _area_pulse_renderer.get_active_count()
	if current > _peak_active:
		_peak_active = current


func _process_attacks(delta: float) -> void:
	for uid: int in range(TacticalBridge.unit_count):
		if TacticalBridge.display_alive[uid] == 0:
			_unit_timers.erase(uid)
			continue

		var unit: Dictionary = TacticalBridge.units.get(uid, {})
		var target_uid: int = int(unit.get("attack_target", -1))

		if target_uid < 0:
			_unit_timers.erase(uid)
			continue

		if target_uid >= TacticalBridge.unit_count or TacticalBridge.display_alive[target_uid] == 0:
			_unit_timers.erase(uid)
			continue

		var atk_range: float = float(unit.get("attack_range", 200.0))
		var ax: float = TacticalBridge.display_x[uid]
		var ay: float = TacticalBridge.display_y[uid]
		var tx: float = TacticalBridge.display_x[target_uid]
		var ty: float = TacticalBridge.display_y[target_uid]
		var dx: float = tx - ax
		var dy: float = ty - ay
		var dist_sq: float = dx * dx + dy * dy

		if dist_sq > atk_range * atk_range:
			continue

		var interval: float = float(unit.get("attack_interval", 1.0))

		if uid not in _unit_timers:
			_unit_timers[uid] = interval * randf_range(0.0, 0.5)

		_unit_timers[uid] -= delta
		if _unit_timers[uid] <= 0.0:
			_unit_timers[uid] = interval
			_fire_attack(uid, target_uid, unit)


func _fire_attack(attacker_uid: int, target_uid: int, unit: Dictionary) -> void:
	var unit_type: String = unit.get("type", "raider").to_lower()
	var cfg: Dictionary = VISUAL_CONFIGS.get(unit_type, VISUAL_CONFIGS["raider"])
	var faction: int = int(unit.get("faction", 0))
	var color: Color = EraThemeResolver.get_faction_color(faction)

	var from_pos: Vector3 = _unit_renderer.get_squad_world_position(attacker_uid)
	var to_pos: Vector3 = _unit_renderer.get_squad_world_position(target_uid)

	var category: String = str(cfg.get("category", "projectile"))

	if category == "beam":
		var beam_dur: float = float(cfg.get("beam_duration", 0.4))
		var beam_thick: float = float(cfg.get("beam_thickness", 6.0))
		_beam_renderer.spawn_beam(from_pos, to_pos, beam_dur, beam_thick, color, camera_zoom)
		_total_spawned += 1
		return

	var volley_count: int = int(cfg["volley"])
	var stagger: float = float(cfg["stagger"])
	var speed: float = float(cfg["speed"])
	var proj_scale: float = float(cfg["scale"])

	_projectile_renderer.spawn_projectile(from_pos, to_pos, speed, proj_scale, color, camera_zoom)
	_total_spawned += 1

	for i in range(1, volley_count):
		_pending_volleys.append({
			"delay": stagger * float(i),
			"from": from_pos,
			"to_uid": target_uid,
			"speed": speed,
			"scale": proj_scale,
			"color": color,
		})


func _process_volleys(delta: float) -> void:
	var i := 0
	while i < _pending_volleys.size():
		var v: Dictionary = _pending_volleys[i]
		v.delay -= delta
		if v.delay <= 0.0:
			var to_uid: int = int(v.to_uid)
			if to_uid < TacticalBridge.unit_count and TacticalBridge.display_alive[to_uid] == 1:
				var to_pos: Vector3 = _unit_renderer.get_squad_world_position(to_uid)
				_projectile_renderer.spawn_projectile(v.from, to_pos, v.speed, v.scale, v.color, camera_zoom)
				_total_spawned += 1
			_pending_volleys.remove_at(i)
		else:
			i += 1


func spawn_area_pulse(center: Vector3, max_radius: float, duration: float, color: Color) -> void:
	_area_pulse_renderer.spawn_pulse(center, max_radius, duration, color)
	_total_spawned += 1


func get_stats() -> Dictionary:
	return {
		"active_projectiles": _projectile_renderer.get_active_count(),
		"active_beams": _beam_renderer.get_active_count(),
		"active_pulses": _area_pulse_renderer.get_active_count(),
		"peak": _peak_active,
		"total_spawned": _total_spawned,
		"pending_volleys": _pending_volleys.size(),
		"lod_culled": _projectile_renderer.get_lod_culled(),
	}
