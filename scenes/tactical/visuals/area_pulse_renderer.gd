extends Node3D

const POOL_SIZE := 16
const RING_MINOR_RADIUS := 8.0

var _pool: Array[MeshInstance3D] = []
var _active: Array[Dictionary] = []

var _torus_mesh: TorusMesh


func _ready() -> void:
	_torus_mesh = TorusMesh.new()
	_torus_mesh.inner_radius = 1.0
	_torus_mesh.outer_radius = 1.0 + RING_MINOR_RADIUS
	_torus_mesh.rings = 32
	_torus_mesh.ring_segments = 12

	for i in POOL_SIZE:
		var mi := MeshInstance3D.new()
		mi.mesh = _torus_mesh
		mi.visible = false
		mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		add_child(mi)
		_pool.append(mi)


func spawn_pulse(center: Vector3, max_radius: float, duration: float, color: Color) -> void:
	if _pool.is_empty():
		return

	var mi: MeshInstance3D = _pool.pop_back()

	var mat := StandardMaterial3D.new()
	mat.albedo_color = color
	mat.emission_enabled = true
	mat.emission = color
	mat.emission_energy_multiplier = 3.0
	mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	mat.cull_mode = BaseMaterial3D.CULL_DISABLED
	mi.material_override = mat

	mi.position = center
	mi.scale = Vector3.ONE * 0.01
	mi.visible = true

	_active.append({
		"mi": mi,
		"mat": mat,
		"elapsed": 0.0,
		"duration": duration,
		"max_radius": max_radius,
		"color": color,
	})


func get_active_count() -> int:
	return _active.size()


func _process(delta: float) -> void:
	var i := 0
	while i < _active.size():
		var pulse: Dictionary = _active[i]
		pulse.elapsed += delta
		var t: float = clampf(pulse.elapsed / maxf(pulse.duration, 0.001), 0.0, 1.0)

		if t >= 1.0:
			pulse.mi.visible = false
			_pool.append(pulse.mi)
			_active.remove_at(i)
			continue

		var mi: MeshInstance3D = pulse.mi
		var mat: StandardMaterial3D = pulse.mat
		var color: Color = pulse.color
		var max_r: float = pulse.max_radius

		var radius: float = max_r * t
		var scale_factor: float = maxf(radius / (1.0 + RING_MINOR_RADIUS), 0.01)
		mi.scale = Vector3(scale_factor, scale_factor, scale_factor)

		var alpha: float = 1.0 - t * t
		mat.albedo_color = Color(color.r, color.g, color.b, 0.7 * alpha)
		mat.emission_energy_multiplier = 3.0 * alpha

		i += 1
