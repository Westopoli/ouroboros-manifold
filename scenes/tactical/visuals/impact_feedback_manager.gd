## Spawns impact particle bursts and hit-reaction emission blooms when units take damage.
## Detects hits by tracking per-unit HP each frame — when HP drops, a hit occurred.
## Scale varies with damage dealt. Color matches attacker faction.
## See also: attack_visual_manager.gd — spawns the projectile/beam that caused the hit.
extends Node3D

const BURST_POOL_SIZE := 64
const BLOOM_POOL_SIZE := 64

const BURST_LIFETIME_MIN := 0.5
const BURST_LIFETIME_MAX := 1.0
const BURST_PARTICLE_COUNT := 16
const BURST_SCALE_MIN := 8.0
const BURST_SCALE_MAX := 40.0
const BURST_DAMAGE_REF := 200.0

const BLOOM_RISE_TIME := 0.4
const BLOOM_FADE_TIME := 0.3
const BLOOM_SCALE := 35.0
const BLOOM_EMISSION_PEAK := 6.0

const IMPACT_COOLDOWN := 0.5

var _prev_hp: PackedFloat32Array = PackedFloat32Array()
var _impact_cooldowns: PackedFloat32Array = PackedFloat32Array()

var _burst_pool: Array[Dictionary] = []
var _active_bursts: Array[Dictionary] = []

var _bloom_pool: Array[Dictionary] = []
var _active_blooms: Array[Dictionary] = []

var _bloom_mesh: SphereMesh

var camera_zoom: float = 0.0

const IMPACT_CULL_ZOOM := 4000.0
const BLOOM_CULL_ZOOM := 3000.0

var _total_impacts: int = 0
var _peak_active: int = 0


func _ready() -> void:
	_prev_hp.resize(TacticalBridge.MAX_UNITS)
	_impact_cooldowns.resize(TacticalBridge.MAX_UNITS)

	_bloom_mesh = SphereMesh.new()
	_bloom_mesh.radius = 1.0
	_bloom_mesh.height = 2.0

	for i in BURST_POOL_SIZE:
		var particles := GPUParticles3D.new()
		particles.emitting = false
		particles.amount = BURST_PARTICLE_COUNT
		particles.lifetime = BURST_LIFETIME_MAX
		particles.one_shot = true
		particles.explosiveness = 0.9
		particles.fixed_fps = 30
		particles.visibility_aabb = AABB(Vector3(-100, -100, -100), Vector3(200, 200, 200))

		var proc_mat := ParticleProcessMaterial.new()
		proc_mat.direction = Vector3(0, 1, 0)
		proc_mat.spread = 180.0
		proc_mat.initial_velocity_min = 30.0
		proc_mat.initial_velocity_max = 80.0
		proc_mat.gravity = Vector3(0, -20, 0)
		proc_mat.damping_min = 10.0
		proc_mat.damping_max = 30.0
		proc_mat.scale_min = 0.5
		proc_mat.scale_max = 1.5
		particles.process_material = proc_mat

		var draw_mesh := SphereMesh.new()
		draw_mesh.radius = 3.0
		draw_mesh.height = 6.0
		var draw_mat := StandardMaterial3D.new()
		draw_mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
		draw_mat.emission_enabled = true
		draw_mat.emission_energy_multiplier = 2.0
		draw_mesh.surface_set_material(0, draw_mat)
		particles.draw_pass_1 = draw_mesh

		add_child(particles)
		_burst_pool.append({
			"particles": particles,
			"proc_mat": proc_mat,
			"draw_mat": draw_mat,
		})

	for i in BLOOM_POOL_SIZE:
		var mi := MeshInstance3D.new()
		mi.mesh = _bloom_mesh
		mi.visible = false
		mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		add_child(mi)
		_bloom_pool.append({"mi": mi, "mat": null})


func _process(delta: float) -> void:
	_decay_cooldowns(delta)
	_detect_hits()
	_process_bursts(delta)
	_process_blooms(delta)

	var current: int = _active_bursts.size() + _active_blooms.size()
	if current > _peak_active:
		_peak_active = current


func _decay_cooldowns(delta: float) -> void:
	for i in range(_impact_cooldowns.size()):
		if _impact_cooldowns[i] > 0.0:
			_impact_cooldowns[i] -= delta


func _detect_hits() -> void:
	for uid in range(TacticalBridge.unit_count):
		if TacticalBridge.display_alive[uid] == 0:
			_prev_hp[uid] = 0.0
			continue

		var unit: Dictionary = TacticalBridge.units.get(uid, {})
		var cur_hp: float = float(unit.get("hp", 0.0))
		var prev: float = _prev_hp[uid]

		if prev > 0.0 and (prev - cur_hp) >= 0.5:
			_total_impacts += 1

			if _impact_cooldowns[uid] > 0.0:
				_prev_hp[uid] = cur_hp
				continue
			_impact_cooldowns[uid] = IMPACT_COOLDOWN

			var damage: float = prev - cur_hp
			var pos := Vector3(
				TacticalBridge.display_x[uid],
				0.0,
				TacticalBridge.display_y[uid]
			)

			var defender_faction: int = int(unit.get("faction", 0))

			if camera_zoom < IMPACT_CULL_ZOOM:
				var attacker_faction: int = _find_attacker_faction(uid)
				var burst_color: Color = EraThemeResolver.get_faction_color(attacker_faction)
				_spawn_burst(pos, damage, burst_color)

			if camera_zoom < BLOOM_CULL_ZOOM:
				var bloom_color: Color = EraThemeResolver.get_faction_color(defender_faction)
				_spawn_bloom(uid, bloom_color)

		_prev_hp[uid] = cur_hp


var _attacker_faction_cache: Dictionary = {}  # target_uid → attacker_faction
var _cache_tick: int = -1

func _find_attacker_faction(target_uid: int) -> int:
	if TacticalBridge.current_tick != _cache_tick:
		_cache_tick = TacticalBridge.current_tick
		_attacker_faction_cache.clear()
		for uid in range(TacticalBridge.unit_count):
			if TacticalBridge.display_alive[uid] == 0:
				continue
			var unit: Dictionary = TacticalBridge.units.get(uid, {})
			var atk_target: int = int(unit.get("attack_target", -1))
			if atk_target >= 0:
				_attacker_faction_cache[atk_target] = int(unit.get("faction", 1))
	return int(_attacker_faction_cache.get(target_uid, 1))


func _spawn_burst(pos: Vector3, damage: float, color: Color) -> void:
	if _burst_pool.is_empty():
		return

	var entry: Dictionary = _burst_pool.pop_back()
	var particles: GPUParticles3D = entry.particles
	var proc_mat: ParticleProcessMaterial = entry.proc_mat
	var draw_mat: StandardMaterial3D = entry.draw_mat

	var damage_t: float = clampf(damage / BURST_DAMAGE_REF, 0.0, 1.0)
	var burst_scale: float = BURST_SCALE_MIN + (BURST_SCALE_MAX - BURST_SCALE_MIN) * damage_t
	var lifetime: float = BURST_LIFETIME_MIN + (BURST_LIFETIME_MAX - BURST_LIFETIME_MIN) * damage_t

	proc_mat.initial_velocity_min = 30.0 + 50.0 * damage_t
	proc_mat.initial_velocity_max = 80.0 + 80.0 * damage_t
	proc_mat.color = Color(color.r, color.g, color.b, 0.8)

	draw_mat.albedo_color = Color(color.r, color.g, color.b, 0.7)
	draw_mat.emission = color
	draw_mat.emission_energy_multiplier = 2.0 + 2.0 * damage_t

	particles.lifetime = lifetime
	particles.position = pos
	particles.scale = Vector3.ONE * (burst_scale / BURST_SCALE_MIN)
	particles.restart()
	particles.emitting = true

	_active_bursts.append({
		"entry": entry,
		"elapsed": 0.0,
		"lifetime": lifetime + 0.1,
	})


func _spawn_bloom(uid: int, color: Color) -> void:
	if _bloom_pool.is_empty():
		return

	var entry: Dictionary = _bloom_pool.pop_back()
	var mi: MeshInstance3D = entry.mi

	var mat := StandardMaterial3D.new()
	mat.albedo_color = Color(color.r, color.g, color.b, 0.0)
	mat.emission_enabled = true
	mat.emission = color
	mat.emission_energy_multiplier = 0.0
	mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	mi.material_override = mat
	entry.mat = mat

	mi.scale = Vector3.ONE * BLOOM_SCALE
	mi.visible = true

	_active_blooms.append({
		"entry": entry,
		"uid": uid,
		"elapsed": 0.0,
		"duration": BLOOM_RISE_TIME + BLOOM_FADE_TIME,
		"color": color,
	})


func _process_bursts(delta: float) -> void:
	var i := 0
	while i < _active_bursts.size():
		var burst: Dictionary = _active_bursts[i]
		burst.elapsed += delta
		if burst.elapsed >= burst.lifetime:
			burst.entry.particles.emitting = false
			_burst_pool.append(burst.entry)
			_active_bursts.remove_at(i)
		else:
			i += 1


func _process_blooms(delta: float) -> void:
	var i := 0
	while i < _active_blooms.size():
		var bloom: Dictionary = _active_blooms[i]
		bloom.elapsed += delta
		var t: float = clampf(bloom.elapsed / maxf(bloom.duration, 0.001), 0.0, 1.0)

		if t >= 1.0:
			bloom.entry.mi.visible = false
			_bloom_pool.append(bloom.entry)
			_active_blooms.remove_at(i)
			continue

		var uid: int = int(bloom.uid)
		var mi: MeshInstance3D = bloom.entry.mi

		if uid < TacticalBridge.unit_count and TacticalBridge.display_alive[uid] == 1:
			mi.position = Vector3(
				TacticalBridge.display_x[uid],
				0.0,
				TacticalBridge.display_y[uid]
			)

		var mat: StandardMaterial3D = bloom.entry.mat
		var color: Color = bloom.color

		var rise_t: float = BLOOM_RISE_TIME / bloom.duration
		var intensity: float
		if t < rise_t:
			intensity = t / rise_t
		else:
			intensity = 1.0 - (t - rise_t) / (1.0 - rise_t)

		intensity = intensity * intensity
		mat.albedo_color = Color(color.r, color.g, color.b, 0.3 * intensity)
		mat.emission_energy_multiplier = BLOOM_EMISSION_PEAK * intensity

		i += 1


func get_stats() -> Dictionary:
	return {
		"active_bursts": _active_bursts.size(),
		"active_blooms": _active_blooms.size(),
		"peak_active": _peak_active,
		"total_impacts": _total_impacts,
	}
