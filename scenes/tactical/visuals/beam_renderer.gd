extends Node3D

const POOL_SIZE := 32
const SHIMMER_FREQ := 12.0
const FADE_START := 0.7

var _pool: Array[Dictionary] = []
var _active: Array[Dictionary] = []

var _beam_mesh: BoxMesh


func _ready() -> void:
	_beam_mesh = BoxMesh.new()
	_beam_mesh.size = Vector3(1.0, 1.0, 1.0)

	for i in POOL_SIZE:
		var mi := MeshInstance3D.new()
		mi.mesh = _beam_mesh
		mi.visible = false
		mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		add_child(mi)
		_pool.append({"mi": mi, "mat": null})


func spawn_beam(from_pos: Vector3, to_pos: Vector3, duration: float, thickness: float, color: Color, camera_zoom: float = 0.0) -> void:
	if camera_zoom >= 5000.0:
		return
	if _pool.is_empty():
		return

	var entry: Dictionary = _pool.pop_back()
	var mi: MeshInstance3D = entry.mi

	var mat := StandardMaterial3D.new()
	mat.albedo_color = color
	mat.emission_enabled = true
	mat.emission = color
	mat.emission_energy_multiplier = 4.0
	mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	mi.material_override = mat
	entry.mat = mat

	mi.visible = true

	_active.append({
		"entry": entry,
		"from": from_pos,
		"to": to_pos,
		"elapsed": 0.0,
		"duration": duration,
		"thickness": thickness,
		"color": color,
	})


func get_active_count() -> int:
	return _active.size()


func _process(delta: float) -> void:
	var i := 0
	while i < _active.size():
		var beam: Dictionary = _active[i]
		beam.elapsed += delta
		var t: float = clampf(beam.elapsed / maxf(beam.duration, 0.001), 0.0, 1.0)

		if t >= 1.0:
			beam.entry.mi.visible = false
			_pool.append(beam.entry)
			_active.remove_at(i)
			continue

		var from_pos: Vector3 = beam.from
		var to_pos: Vector3 = beam.to
		var mi: MeshInstance3D = beam.entry.mi
		var mat: StandardMaterial3D = beam.entry.mat
		var base_thickness: float = beam.thickness
		var color: Color = beam.color

		var midpoint: Vector3 = (from_pos + to_pos) * 0.5
		var diff: Vector3 = to_pos - from_pos
		var length: float = diff.length()

		mi.position = midpoint
		if length > 0.01:
			mi.look_at(to_pos, Vector3.UP)

		var shimmer: float = 1.0 + 0.15 * sin(beam.elapsed * SHIMMER_FREQ * TAU)
		var fade_alpha: float = 1.0
		if t > FADE_START:
			fade_alpha = 1.0 - (t - FADE_START) / (1.0 - FADE_START)

		var thick: float = base_thickness * shimmer
		mi.scale = Vector3(thick, thick, length)

		mat.albedo_color = Color(color.r, color.g, color.b, 0.8 * fade_alpha)
		mat.emission_energy_multiplier = 4.0 * fade_alpha

		i += 1
