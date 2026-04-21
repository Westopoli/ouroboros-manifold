extends Node3D

const PLAYER_COLOR := Color("#c9a84c")
const ENEMY_COLOR := Color(0.4, 0.55, 0.9)
const RIBBON_WIDTH := 0.3
const ORBIT_SPEED := 0.08
const ORBIT_RADIUS := 4.0
const ORBIT_HEIGHT := 2.5
const GRAPH_X_EXTENT := 6.0

const HP_RIBBON_Z_OFFSET := 0.0
const STRUCT_RIBBON_Z_OFFSET := 1.2

var _camera: Camera3D
var _orbit_angle := 0.0
var _orbit_center := Vector3.ZERO
var _built := false


func build(metrics: Dictionary) -> void:
	var samples: Array = metrics.get("samples", [])
	if samples.is_empty():
		return

	_setup_environment()
	_setup_camera(samples)

	var hp_max := _find_max(samples, "player_force_hp", "enemy_force_hp")
	var struct_max := _find_max(samples, "structures_player", "structures_enemy")
	if struct_max < 1.0:
		struct_max = 1.0

	_build_ribbon_pair(samples, "player_force_hp", "enemy_force_hp",
					   hp_max, HP_RIBBON_Z_OFFSET, "Force HP")
	_build_ribbon_pair(samples, "structures_player", "structures_enemy",
					   struct_max, STRUCT_RIBBON_Z_OFFSET, "Structures")

	_build_time_axis(samples)
	_built = true


func _process(delta: float) -> void:
	if not _built or not _camera:
		return
	_orbit_angle += ORBIT_SPEED * delta
	_camera.position = _orbit_center + Vector3(
		cos(_orbit_angle) * ORBIT_RADIUS,
		ORBIT_HEIGHT,
		sin(_orbit_angle) * ORBIT_RADIUS,
	)
	_camera.look_at(_orbit_center, Vector3.UP)


func _setup_environment() -> void:
	var env := Environment.new()
	env.background_mode = Environment.BG_COLOR
	env.background_color = Color(0.02, 0.02, 0.04)
	env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	env.ambient_light_color = Color(0.2, 0.2, 0.3)
	env.ambient_light_energy = 0.4
	env.glow_enabled = true
	env.glow_intensity = 0.8
	env.glow_bloom = 0.3
	env.glow_blend_mode = Environment.GLOW_BLEND_MODE_ADDITIVE
	var we := WorldEnvironment.new()
	we.environment = env
	add_child(we)

	var light := DirectionalLight3D.new()
	light.rotation_degrees = Vector3(-45, -30, 0)
	light.light_energy = 0.5
	light.shadow_enabled = false
	add_child(light)


func _setup_camera(_samples: Array) -> void:
	_orbit_center = Vector3(GRAPH_X_EXTENT * 0.5, 1.0, 0.6)
	_camera = Camera3D.new()
	_camera.fov = 50.0
	add_child(_camera)
	_camera.current = true


func _build_ribbon_pair(samples: Array, player_key: String, enemy_key: String,
						max_val: float, z_offset: float, _label: String) -> void:
	_build_single_ribbon(samples, player_key, max_val, z_offset, PLAYER_COLOR)
	_build_single_ribbon(samples, enemy_key, max_val, z_offset + 0.5, ENEMY_COLOR)


func _build_single_ribbon(samples: Array, key: String, max_val: float,
						  z_offset: float, color: Color) -> void:
	if samples.size() < 2 or max_val <= 0:
		return

	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLE_STRIP)

	var time_extent := _time_extent(samples)
	var x_scale: float = GRAPH_X_EXTENT / maxf(time_extent, 1.0)

	for i in range(samples.size()):
		var s: Dictionary = samples[i]
		var t: float = s.get("elapsed_sec", 0.0)
		var val: float = float(s.get(key, 0.0))
		var height: float = (val / max_val) * 3.0

		var x := t * x_scale
		var y_top := height
		var y_bot := height - RIBBON_WIDTH

		var alpha: float = 0.7
		st.set_color(Color(color.r, color.g, color.b, alpha))
		st.set_normal(Vector3(0, 0, 1))
		st.add_vertex(Vector3(x, y_bot, z_offset))
		st.set_color(Color(color.r, color.g, color.b, alpha))
		st.set_normal(Vector3(0, 0, 1))
		st.add_vertex(Vector3(x, y_top, z_offset))

	var mesh := st.commit()
	var mi := MeshInstance3D.new()
	mi.mesh = mesh

	var mat := StandardMaterial3D.new()
	mat.albedo_color = color
	mat.emission_enabled = true
	mat.emission = color
	mat.emission_energy_multiplier = 2.0
	mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	mat.vertex_color_use_as_albedo = true
	mi.material_override = mat

	add_child(mi)


func _build_time_axis(samples: Array) -> void:
	if samples.size() < 2:
		return

	var time_extent := _time_extent(samples)
	var x_scale := GRAPH_X_EXTENT / maxf(time_extent, 1.0)

	# Tick marks every 60 seconds
	var interval := 60.0
	var t := interval
	while t < time_extent:
		var x := t * x_scale
		var marker := _make_tick_mark(x, t)
		add_child(marker)
		t += interval


func _make_tick_mark(x_pos: float, time_sec: float) -> Node3D:
	var root := Node3D.new()

	# Vertical line
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_LINES)
	st.set_color(ThemeConstants.TERTIARY)
	st.add_vertex(Vector3(x_pos, -0.05, -0.2))
	st.set_color(ThemeConstants.TERTIARY)
	st.add_vertex(Vector3(x_pos, 0.1, -0.2))
	var mesh := st.commit()
	var mi := MeshInstance3D.new()
	mi.mesh = mesh
	var mat := StandardMaterial3D.new()
	mat.albedo_color = ThemeConstants.TERTIARY
	mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	mat.vertex_color_use_as_albedo = true
	mi.material_override = mat
	root.add_child(mi)

	# Time label as 3D text
	var label := Label3D.new()
	label.text = "%d:%02d" % [int(time_sec) / 60, int(time_sec) % 60]
	label.font_size = 32
	label.modulate = ThemeConstants.TERTIARY
	label.position = Vector3(x_pos, -0.15, -0.2)
	label.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	label.pixel_size = 0.005
	root.add_child(label)

	return root


func _time_extent(samples: Array) -> float:
	if samples.is_empty():
		return 1.0
	return maxf(float(samples[samples.size() - 1].get("elapsed_sec", 1.0)), 1.0)


func _find_max(samples: Array, key_a: String, key_b: String) -> float:
	var m := 0.0
	for s in samples:
		m = maxf(m, float(s.get(key_a, 0.0)))
		m = maxf(m, float(s.get(key_b, 0.0)))
	return m if m > 0 else 1.0
