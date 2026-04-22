## Object pool for flyby ship instances on Bezier paths.
## Ships spawn at map boundary, follow curved paths biased toward combat,
## and despawn on exit. Each ship has a GPU particle trail.
extends Node3D

const POOL_SIZE := 16
const SHIP_SPEED := 200.0
const TRAIL_LIFETIME := 2.0
const TRAIL_PARTICLE_COUNT := 20
const SHIP_Y := 50.0

var _pool: Array[Dictionary] = []
var _active: Array[Dictionary] = []

var _ship_mesh: BoxMesh

var _peak_active: int = 0


func _ready() -> void:
	_ship_mesh = BoxMesh.new()
	_ship_mesh.size = Vector3(2.5, 1.2, 5.0)

	for i in POOL_SIZE:
		var mi := MeshInstance3D.new()
		mi.mesh = _ship_mesh
		mi.visible = false
		mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF

		var mat := StandardMaterial3D.new()
		mat.albedo_color = Color(0.5, 0.55, 0.65, 0.8)
		mat.emission_enabled = true
		mat.emission = Color(0.4, 0.5, 0.7)
		mat.emission_energy_multiplier = 2.0
		mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
		mi.material_override = mat
		add_child(mi)

		var trail := GPUParticles3D.new()
		trail.emitting = false
		trail.amount = TRAIL_PARTICLE_COUNT
		trail.lifetime = TRAIL_LIFETIME
		trail.one_shot = false
		trail.fixed_fps = 30
		trail.visibility_aabb = AABB(Vector3(-500, -500, -500), Vector3(1000, 1000, 1000))

		var proc_mat := ParticleProcessMaterial.new()
		proc_mat.direction = Vector3(0, 0, 0)
		proc_mat.spread = 0.0
		proc_mat.initial_velocity_min = 0.0
		proc_mat.initial_velocity_max = 0.0
		proc_mat.gravity = Vector3.ZERO
		proc_mat.scale_min = 0.8
		proc_mat.scale_max = 1.0
		# Fade out over lifetime
		proc_mat.color = Color(0.5, 0.6, 0.9, 0.6)
		trail.process_material = proc_mat

		var trail_mesh := SphereMesh.new()
		trail_mesh.radius = 1.0
		trail_mesh.height = 2.0
		var trail_mat := StandardMaterial3D.new()
		trail_mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
		trail_mat.emission_enabled = true
		trail_mat.emission = Color(0.4, 0.5, 0.9)
		trail_mat.emission_energy_multiplier = 2.0
		trail_mat.albedo_color = Color(0.4, 0.5, 0.9, 0.5)
		trail_mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
		trail_mesh.surface_set_material(0, trail_mat)
		trail.draw_pass_1 = trail_mesh
		mi.add_child(trail)

		_pool.append({"mi": mi, "trail": trail, "mat": mat})


func spawn_ship(start: Vector3, control1: Vector3, control2: Vector3, end_pos: Vector3) -> void:
	if _pool.is_empty():
		return

	var entry: Dictionary = _pool.pop_back()
	var mi: MeshInstance3D = entry.mi
	mi.position = start
	mi.visible = true
	entry.trail.emitting = true

	var path_length: float = start.distance_to(control1) + control1.distance_to(control2) + control2.distance_to(end_pos)
	var duration: float = path_length / maxf(SHIP_SPEED, 1.0)

	# Per-ship sin wave: random frequency, amplitude, and phase
	# amplitude_drift causes the wave to fade in and out over the path
	_active.append({
		"entry": entry,
		"p0": start,
		"p1": control1,
		"p2": control2,
		"p3": end_pos,
		"elapsed": 0.0,
		"duration": duration,
		"wave_freq": randf_range(2.0, 5.0),
		"wave_amp": randf_range(30.0, 120.0),
		"wave_phase": randf_range(0.0, TAU),
		"wave_drift_freq": randf_range(0.3, 0.8),
	})

	if _active.size() > _peak_active:
		_peak_active = _active.size()


func process_ships(delta: float) -> void:
	var i := 0
	while i < _active.size():
		var ship: Dictionary = _active[i]
		ship.elapsed += delta
		var t: float = clampf(ship.elapsed / maxf(ship.duration, 0.001), 0.0, 1.0)

		if t >= 1.0:
			ship.entry.mi.visible = false
			ship.entry.trail.emitting = false
			_pool.append(ship.entry)
			_active.remove_at(i)
			continue

		var base_pos: Vector3 = _cubic_bezier(ship.p0, ship.p1, ship.p2, ship.p3, t)
		var look_t: float = minf(t + 0.01, 1.0)
		var look_base: Vector3 = _cubic_bezier(ship.p0, ship.p1, ship.p2, ship.p3, look_t)

		# Sin wave oscillation perpendicular to path direction
		var fwd: Vector3 = look_base - base_pos
		if fwd.length_squared() < 0.001:
			fwd = Vector3(0, 0, 1)
		fwd = fwd.normalized()
		var perp := Vector3(-fwd.z, 0.0, fwd.x)

		var wave_envelope: float = sin(t * float(ship.wave_drift_freq) * TAU) * 0.5 + 0.5
		var wave_offset: float = sin(t * float(ship.wave_freq) * TAU + float(ship.wave_phase)) * float(ship.wave_amp) * wave_envelope

		var pos: Vector3 = base_pos + perp * wave_offset
		var mi: MeshInstance3D = ship.entry.mi
		mi.position = pos

		var look_pos: Vector3 = look_base + perp * wave_offset
		var dir: Vector3 = look_pos - pos
		if dir.length_squared() > 0.001:
			mi.look_at(pos + dir, Vector3.UP)

		i += 1


func _cubic_bezier(p0: Vector3, p1: Vector3, p2: Vector3, p3: Vector3, t: float) -> Vector3:
	var u: float = 1.0 - t
	return u * u * u * p0 + 3.0 * u * u * t * p1 + 3.0 * u * t * t * p2 + t * t * t * p3


func get_active_count() -> int:
	return _active.size()


func get_peak() -> int:
	return _peak_active
