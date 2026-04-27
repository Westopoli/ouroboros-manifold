## Manages unit death sequences and wreckage lifecycle.
## Detects deaths by tracking alive state per uid each frame.
## Sequence: death bloom (0.5s) -> damage particles -> drift -> darkening.
## Lifecycle: fresh (0-5s) -> cooling (5-15s) -> cold (15s+) -> despawn.
## Strike units get abbreviated death (1.0s bloom+fade, no drift).
## See also: unit_renderer.gd — hides dead units; this replaces them with wreckage visuals.
extends Node3D

const STRIKE_TYPES := ["Raider", "Interceptor", "raider", "interceptor"]

const BLOOM_DURATION := 0.5
const BLOOM_DURATION_STRIKE := 0.3
const BLOOM_SCALE := 50.0
const BLOOM_EMISSION_PEAK := 8.0

const FRESH_END := 5.0
const COOLING_END := 15.0
const COLD_DESPAWN := 30.0

const DRIFT_SPEED := 15.0
const DRIFT_SPEED_STRIKE := 0.0

const PARTICLE_COUNT := 8
const PARTICLE_LIFETIME := 3.0

const WRECK_POOL_SIZE := 128
const CULL_DISTANCE_SQ := 8000.0 * 8000.0
const CULL_CHECK_INTERVAL := 2.0

var _prev_alive: PackedByteArray = PackedByteArray()
var _unit_cache: Dictionary = {}  # uid -> {type, faction} — cached while alive, used at death

var _wreck_pool: Array[Dictionary] = []
var _active_wrecks: Array[Dictionary] = []

var _bloom_mesh: SphereMesh
var _wreck_mesh: BoxMesh

var _camera: Camera3D
var _cull_timer: float = 0.0

var _peak_wrecks: int = 0
var _total_deaths: int = 0
var _cull_count: int = 0


func _ready() -> void:
	_prev_alive.resize(TacticalBridge.MAX_UNITS)

	_bloom_mesh = SphereMesh.new()
	_bloom_mesh.radius = 1.0
	_bloom_mesh.height = 2.0

	_wreck_mesh = BoxMesh.new()
	_wreck_mesh.size = Vector3(20.0, 8.0, 20.0)

	for i in WRECK_POOL_SIZE:
		var wreck_mi := MeshInstance3D.new()
		wreck_mi.mesh = _wreck_mesh
		wreck_mi.visible = false
		wreck_mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		add_child(wreck_mi)

		var bloom_mi := MeshInstance3D.new()
		bloom_mi.mesh = _bloom_mesh
		bloom_mi.visible = false
		bloom_mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		add_child(bloom_mi)

		var particles := GPUParticles3D.new()
		particles.emitting = false
		particles.amount = PARTICLE_COUNT
		particles.lifetime = PARTICLE_LIFETIME
		particles.one_shot = false
		particles.fixed_fps = 20
		particles.visibility_aabb = AABB(Vector3(-100, -100, -100), Vector3(200, 200, 200))

		var proc_mat := ParticleProcessMaterial.new()
		proc_mat.direction = Vector3(0, 1, 0)
		proc_mat.spread = 60.0
		proc_mat.initial_velocity_min = 5.0
		proc_mat.initial_velocity_max = 20.0
		proc_mat.gravity = Vector3(0, -5, 0)
		proc_mat.damping_min = 5.0
		proc_mat.damping_max = 15.0
		proc_mat.scale_min = 0.3
		proc_mat.scale_max = 1.0
		particles.process_material = proc_mat

		var draw_mesh := SphereMesh.new()
		draw_mesh.radius = 2.0
		draw_mesh.height = 4.0
		var draw_mat := StandardMaterial3D.new()
		draw_mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
		draw_mat.emission_enabled = true
		draw_mat.emission_energy_multiplier = 1.5
		draw_mesh.surface_set_material(0, draw_mat)
		particles.draw_pass_1 = draw_mesh

		add_child(particles)

		_wreck_pool.append({
			"wreck_mi": wreck_mi,
			"bloom_mi": bloom_mi,
			"particles": particles,
			"proc_mat": proc_mat,
			"particle_draw_mat": draw_mat,
			"wreck_mat": null,
			"bloom_mat": null,
		})


func setup(camera: Camera3D) -> void:
	_camera = camera


func _process(delta: float) -> void:
	_detect_deaths()
	_process_wrecks(delta)
	_cull_timer += delta
	if _cull_timer >= CULL_CHECK_INTERVAL:
		_cull_timer = 0.0
		_cull_cold_wrecks()

	if _active_wrecks.size() > _peak_wrecks:
		_peak_wrecks = _active_wrecks.size()


func _detect_deaths() -> void:
	for uid in range(TacticalBridge.unit_count):
		var cur_alive: int = TacticalBridge.display_alive[uid]
		if cur_alive == 1:
			# Cache unit info while alive — TacticalBridge.units erases before display_alive transitions
			var unit: Dictionary = TacticalBridge.units.get(uid, {})
			if not unit.is_empty():
				_unit_cache[uid] = {
					"type": str(unit.get("type", "raider")),
					"faction": int(unit.get("faction", 0)),
				}
		if _prev_alive[uid] == 1 and cur_alive == 0:
			_spawn_wreck(uid)
			_total_deaths += 1
			_unit_cache.erase(uid)
		_prev_alive[uid] = cur_alive


func _spawn_wreck(uid: int) -> void:
	if _wreck_pool.is_empty():
		return

	var cached: Dictionary = _unit_cache.get(uid, {})
	var unit_type: String = str(cached.get("type", "raider"))
	var faction: int = int(cached.get("faction", 0))
	var is_strike: bool = unit_type in STRIKE_TYPES
	var color: Color = EraThemeResolver.get_faction_color(faction)

	var pos := Vector3(
		TacticalBridge.display_x[uid],
		0.0,
		TacticalBridge.display_y[uid]
	)

	var facing: float = TacticalBridge.display_facing[uid]
	var drift_dir := Vector3(sin(facing), 0.0, cos(facing))
	var drift_spd: float = DRIFT_SPEED_STRIKE if is_strike else DRIFT_SPEED

	var entry: Dictionary = _wreck_pool.pop_back()

	# Bloom
	var bloom_mat := StandardMaterial3D.new()
	bloom_mat.albedo_color = Color(color.r, color.g, color.b, 0.0)
	bloom_mat.emission_enabled = true
	bloom_mat.emission = color
	bloom_mat.emission_energy_multiplier = 0.0
	bloom_mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	bloom_mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	entry.bloom_mi.material_override = bloom_mat
	entry.bloom_mi.position = pos
	entry.bloom_mi.scale = Vector3.ONE * BLOOM_SCALE
	entry.bloom_mi.visible = true
	entry.bloom_mat = bloom_mat

	# Wreck mesh
	var dark_color := Color(color.r * 0.1, color.g * 0.1, color.b * 0.1, 1.0)
	var wreck_mat := StandardMaterial3D.new()
	wreck_mat.albedo_color = color
	wreck_mat.emission_enabled = true
	wreck_mat.emission = color
	wreck_mat.emission_energy_multiplier = 1.0
	entry.wreck_mi.material_override = wreck_mat
	entry.wreck_mi.position = pos
	entry.wreck_mi.rotation = Vector3(0.0, facing, randf_range(-0.2, 0.2))
	entry.wreck_mi.visible = true
	entry.wreck_mat = wreck_mat

	# Particles
	entry.proc_mat.color = Color(color.r, color.g, color.b, 0.6)
	entry.particle_draw_mat.albedo_color = Color(color.r, color.g, color.b, 0.5)
	entry.particle_draw_mat.emission = color
	entry.particles.position = pos
	entry.particles.emitting = true

	var bloom_dur: float = BLOOM_DURATION_STRIKE if is_strike else BLOOM_DURATION

	_active_wrecks.append({
		"entry": entry,
		"pos": pos,
		"elapsed": 0.0,
		"bloom_duration": bloom_dur,
		"is_strike": is_strike,
		"drift_dir": drift_dir,
		"drift_speed": drift_spd,
		"color": color,
		"dark_color": dark_color,
	})


func _process_wrecks(delta: float) -> void:
	var i := 0
	while i < _active_wrecks.size():
		var wreck: Dictionary = _active_wrecks[i]
		wreck.elapsed += delta
		var elapsed: float = wreck.elapsed
		var entry: Dictionary = wreck.entry
		var is_strike: bool = wreck.is_strike

		# Strike: abbreviated — bloom then fade, total ~3.0s, then despawn
		if is_strike and elapsed > 3.0:
			_recycle_wreck(i)
			continue

		# Bloom phase
		var bloom_dur: float = wreck.bloom_duration
		if elapsed < bloom_dur:
			var bt: float = elapsed / bloom_dur
			var intensity: float = sin(bt * PI)
			var bloom_mat: StandardMaterial3D = entry.bloom_mat
			var color: Color = wreck.color
			bloom_mat.albedo_color = Color(color.r, color.g, color.b, 0.5 * intensity)
			bloom_mat.emission_energy_multiplier = BLOOM_EMISSION_PEAK * intensity
		elif entry.bloom_mi.visible:
			entry.bloom_mi.visible = false

		# Drift
		if not is_strike and wreck.drift_speed > 0.0:
			var drift_vec: Vector3 = wreck.drift_dir * wreck.drift_speed * delta
			wreck.pos += drift_vec
			entry.wreck_mi.position = wreck.pos
			entry.particles.position = wreck.pos

		# Lifecycle phases: fresh -> cooling -> cold
		if elapsed < FRESH_END:
			pass
		elif elapsed < COOLING_END:
			# Cooling: darken, reduce particles
			var cool_t: float = (elapsed - FRESH_END) / (COOLING_END - FRESH_END)
			var wreck_mat: StandardMaterial3D = entry.wreck_mat
			var color: Color = wreck.color
			var dark: Color = wreck.dark_color
			wreck_mat.albedo_color = color.lerp(dark, cool_t)
			wreck_mat.emission_energy_multiplier = 1.0 * (1.0 - cool_t)

			if cool_t > 0.5 and entry.particles.emitting:
				entry.particles.emitting = false
		else:
			# Cold: dark mesh, no particles, no emission
			var wreck_mat: StandardMaterial3D = entry.wreck_mat
			wreck_mat.albedo_color = wreck.dark_color
			wreck_mat.emission_energy_multiplier = 0.0
			if entry.particles.emitting:
				entry.particles.emitting = false

			if elapsed > COLD_DESPAWN:
				_recycle_wreck(i)
				continue

		i += 1


func _recycle_wreck(index: int) -> void:
	var wreck: Dictionary = _active_wrecks[index]
	var entry: Dictionary = wreck.entry
	entry.wreck_mi.visible = false
	entry.bloom_mi.visible = false
	entry.particles.emitting = false
	_wreck_pool.append(entry)
	_active_wrecks.remove_at(index)


func _cull_cold_wrecks() -> void:
	if not _camera:
		return
	# Cull aggressively when pool is running low, otherwise only when < 25% free
	var pool_pressure: bool = _wreck_pool.size() < WRECK_POOL_SIZE / 8
	if not pool_pressure and _wreck_pool.size() > WRECK_POOL_SIZE / 4:
		return

	var cam_pos: Vector3 = _camera.global_position
	var candidates: Array[Dictionary] = []

	var min_age: float = FRESH_END if pool_pressure else COOLING_END
	for i in range(_active_wrecks.size()):
		var wreck: Dictionary = _active_wrecks[i]
		if wreck.elapsed < min_age:
			continue
		var dx: float = wreck.pos.x - cam_pos.x
		var dz: float = wreck.pos.z - cam_pos.z
		var dist_sq: float = dx * dx + dz * dz
		candidates.append({"index": i, "dist_sq": dist_sq})

	if candidates.is_empty():
		return

	candidates.sort_custom(func(a: Dictionary, b: Dictionary) -> bool:
		return float(a.dist_sq) > float(b.dist_sq)
	)

	var to_cull: int = mini(candidates.size(), maxi(1, WRECK_POOL_SIZE / 4 - _wreck_pool.size()))
	var indices_to_remove: Array[int] = []
	for j in range(to_cull):
		var candidate: Dictionary = candidates[j]
		if float(candidate.dist_sq) > CULL_DISTANCE_SQ:
			indices_to_remove.append(int(candidate.index))

	indices_to_remove.sort()
	indices_to_remove.reverse()
	for idx in indices_to_remove:
		_recycle_wreck(idx)
		_cull_count += 1


func get_stats() -> Dictionary:
	var fresh := 0
	var cooling := 0
	var cold := 0
	for wreck in _active_wrecks:
		var elapsed: float = wreck.elapsed
		if elapsed < FRESH_END:
			fresh += 1
		elif elapsed < COOLING_END:
			cooling += 1
		else:
			cold += 1
	return {
		"active_wrecks": _active_wrecks.size(),
		"fresh": fresh,
		"cooling": cooling,
		"cold": cold,
		"peak_wrecks": _peak_wrecks,
		"total_deaths": _total_deaths,
		"cull_count": _cull_count,
		"pool_remaining": _wreck_pool.size(),
	}
