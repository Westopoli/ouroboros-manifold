## Manages active projectile instances for attack visuals.
## Projectiles travel from attacker to target, spawn impact burst on arrival.
## All visuals are cosmetic — damage is resolved independently by the engine.
extends Node3D

const POOL_SIZE := 128
const IMPACT_LIFETIME := 0.4

var _pool: Array[Dictionary] = []
var _active: Array[Dictionary] = []
var _impact_pool: Array[MeshInstance3D] = []
var _active_impacts: Array[Dictionary] = []

var _bolt_mesh: SphereMesh
var _impact_mesh: SphereMesh


func _ready() -> void:
	_bolt_mesh = SphereMesh.new()
	_bolt_mesh.radius = 8.0
	_bolt_mesh.height = 16.0

	_impact_mesh = SphereMesh.new()
	_impact_mesh.radius = 1.0
	_impact_mesh.height = 2.0

	for i in POOL_SIZE:
		var mi := MeshInstance3D.new()
		mi.mesh = _bolt_mesh
		mi.visible = false
		mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		add_child(mi)

		var trail := GPUParticles3D.new()
		trail.emitting = false
		trail.amount = 12
		trail.lifetime = 0.3
		trail.one_shot = false
		trail.fixed_fps = 30
		trail.visibility_aabb = AABB(Vector3(-200, -200, -200), Vector3(400, 400, 400))
		trail.draw_order = GPUParticles3D.DRAW_ORDER_LIFETIME

		var trail_mat := ParticleProcessMaterial.new()
		trail_mat.direction = Vector3(0, 0, 0)
		trail_mat.spread = 15.0
		trail_mat.initial_velocity_min = 5.0
		trail_mat.initial_velocity_max = 15.0
		trail_mat.gravity = Vector3.ZERO
		trail_mat.scale_min = 0.8
		trail_mat.scale_max = 1.2
		trail_mat.color = Color(0.8, 0.9, 1.0, 0.6)
		trail.process_material = trail_mat

		var trail_mesh := SphereMesh.new()
		trail_mesh.radius = 4.0
		trail_mesh.height = 8.0
		var trail_draw_mat := StandardMaterial3D.new()
		trail_draw_mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
		trail_draw_mat.emission_enabled = true
		trail_draw_mat.emission = Color(0.6, 0.7, 1.0)
		trail_draw_mat.emission_energy_multiplier = 1.5
		trail_draw_mat.albedo_color = Color(0.6, 0.7, 1.0, 0.4)
		trail_mesh.surface_set_material(0, trail_draw_mat)
		trail.draw_pass_1 = trail_mesh
		mi.add_child(trail)

		_pool.append({"mi": mi, "trail": trail, "mat": null, "trail_draw_mat": trail_draw_mat, "trail_proc_mat": trail_mat})

	for i in 32:
		var imp := MeshInstance3D.new()
		imp.mesh = _impact_mesh
		imp.visible = false
		imp.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		add_child(imp)
		_impact_pool.append(imp)


func spawn_projectile(from_pos: Vector3, to_pos: Vector3, speed: float, scale: float, color: Color) -> void:
	if _pool.is_empty():
		return

	var entry: Dictionary = _pool.pop_back()
	var mi: MeshInstance3D = entry.mi
	var trail: GPUParticles3D = entry.trail

	var mat := StandardMaterial3D.new()
	mat.albedo_color = color
	mat.emission_enabled = true
	mat.emission = color
	mat.emission_energy_multiplier = 3.0
	mi.material_override = mat
	entry.mat = mat

	var trail_draw_mat: StandardMaterial3D = entry.trail_draw_mat
	trail_draw_mat.emission = color * 0.7
	trail_draw_mat.albedo_color = Color(color.r, color.g, color.b, 0.4)

	var trail_proc_mat: ParticleProcessMaterial = entry.trail_proc_mat
	trail_proc_mat.color = Color(color.r, color.g, color.b, 0.6)

	mi.scale = Vector3.ONE * scale
	mi.position = from_pos
	mi.visible = true
	trail.emitting = true

	var dist := from_pos.distance_to(to_pos)
	var travel_time := dist / maxf(speed, 1.0)

	_active.append({
		"entry": entry,
		"from": from_pos,
		"to": to_pos,
		"elapsed": 0.0,
		"duration": travel_time,
		"color": color,
	})


func get_active_count() -> int:
	return _active.size()


func _process(delta: float) -> void:
	var i := 0
	while i < _active.size():
		var proj: Dictionary = _active[i]
		proj.elapsed += delta
		var t: float = clampf(proj.elapsed / maxf(proj.duration, 0.001), 0.0, 1.0)
		var mi: MeshInstance3D = proj.entry.mi
		mi.position = proj.from.lerp(proj.to, t)

		if t >= 1.0:
			_spawn_impact(proj.to, proj.color)
			mi.visible = false
			proj.entry.trail.emitting = false
			_pool.append(proj.entry)
			_active.remove_at(i)
		else:
			i += 1

	var j := 0
	while j < _active_impacts.size():
		var imp: Dictionary = _active_impacts[j]
		imp.elapsed += delta
		var t: float = imp.elapsed / IMPACT_LIFETIME
		if t >= 1.0:
			imp.mi.visible = false
			_impact_pool.append(imp.mi)
			_active_impacts.remove_at(j)
		else:
			var s: float = (1.0 - t) * imp.base_scale
			imp.mi.scale = Vector3.ONE * s
			j += 1


func _spawn_impact(pos: Vector3, color: Color) -> void:
	if _impact_pool.is_empty():
		return
	var mi: MeshInstance3D = _impact_pool.pop_back()
	var mat := StandardMaterial3D.new()
	mat.albedo_color = color
	mat.emission_enabled = true
	mat.emission = color
	mat.emission_energy_multiplier = 5.0
	mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	mi.material_override = mat
	mi.position = pos
	mi.scale = Vector3.ONE * 20.0
	mi.visible = true
	_active_impacts.append({"mi": mi, "elapsed": 0.0, "base_scale": 20.0})
