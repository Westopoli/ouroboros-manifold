extends Node3D

# R-106-05 ambient field. The rings, inflow streams and central glow are built from the
# prototype rig scenes/mockups/galaxy/legacy_ambient_rig.gd (its ring and stream shaders are
# read in place). The vast-space backdrop behind them is VG-B25: a dim wash baked once from the
# view direction, four world-fixed star layers at real depth, and one volume of motes that
# wraps about the camera. A60: galaxy_quality 2 halves every emitter's amount (never deletes
# one); tiers 0 and 1 carry the full field.

const TIER_FEWER := 2

# VG-B25 vast-space backdrop. Every DRAFT-b25-* value is a named draft with its row in
# docs/northstar/plans/push_ledger_2026-09-22.md (Architect gap rulings g1 to g4, 2026-10-12).
const GalaxyGen := preload("res://scenes/galaxy/galaxy_gen.gd")
const StarsShader := preload("res://scenes/galaxy/shaders/backdrop_stars.gdshader")
const WashShader := preload("res://scenes/galaxy/shaders/backdrop_wash.gdshader")
const DustShader := preload("res://scenes/galaxy/shaders/backdrop_dust.gdshader")

const LAYER_COUNT := 4
const LAYER_RADII := [100.0, 250.0, 800.0, 2500.0]   # Step 5 of the galaxy bubble field spec, unscaled
const BACKDROP_SCALE := 0.5   # g1 (b): layers at 50, 125, 400 and 1,250
const CAMERA_FAR := 3000.0   # DRAFT-b25-far: covers the 1,250 layer and its 2R clip at 2,500
const STARS_PER_LAYER := 2000   # DRAFT-b25-stars (old: Starfield _amt(2000))
const SHELL_SIGMA := 0.25   # g3: Gaussian thickness R/4 about the layer radius
const SHELL_CLIP := 4.0   # g3: clipped at 2R, which is four sigma
const LAYER_BRIGHTNESS := [1.0, 0.8, 0.6, 0.45]   # DRAFT-b25-brightness
const STAR_ALPHA_MIN := 0.3   # DRAFT-b25-brightness: alpha mix(0.3, 0.8, roll^2), the old starfield's
const STAR_ALPHA_MAX := 0.8
const STAR_GOLD := Color(1.0, 0.92, 0.7)   # DRAFT-b25-tints, the old starfield's colours
const STAR_BLUE := Color(0.7, 0.8, 1.0)
const STAR_GOLD_FRACTION := 0.6   # DRAFT-b25-tints: gold 60 percent, blue 40 percent
const STAR_PX_MIN := 1.0   # Step 5: stars stay 1 to 3 pixels
const STAR_PX_MAX := 3.0
# DRAFT-b25-star-ref: a star at its own layer radius is the middle of the STAR_PX_MIN to STAR_PX_MAX
# range (the px_min / px_max uniforms). A derivation from two fixed numbers, not new numbers: viewport
# height 1080 px (Westley's 1080p ruling) and fov 45 degrees (the scene camera's, galaxy_view.tscn:35,
# which orbit_camera.gd:131 reads from the same camera). The lever Westley would move is the 1 to 3 px range.
const STAR_REF_VIEWPORT_H := 1080.0   # DRAFT-b25-star-ref: Westley's 1080p ruling
const STAR_REF_FOV_DEG := 45.0   # DRAFT-b25-star-ref: the scene camera's fov
const BACKGROUND := Color(0.0392157, 0.0509804, 0.0705882)   # galaxy_view.tscn Environment background
const WASH_MESH_RADIUS := 1000.0
const DUST_BOX := 120.0   # DRAFT-b25-dust (old: sphere radius 60)
const DUST_COUNT := 400
const DUST_QUAD := 0.1
const DUST_DRIFT := 0.3
const DUST_FADE := 0.25   # fade over the outer quarter of the half box from each face
const DUST_GOLD := Color(1.0, 0.88, 0.5, 0.3)
const DUST_BLUE := Color(0.6, 0.7, 1.0, 0.2)

var _tier := 0

var _central_point: MeshInstance3D
var _stream_pivot: Node3D
var _pulse_tween: Tween
var _rotation_tween: Tween
var _dust: MultiMeshInstance3D
var _dust_homes := PackedVector3Array()
var _dust_velocities := PackedVector3Array()
var _dust_positions := PackedVector3Array()
var _dust_time := 0.0


func _ready() -> void:
	_tier = int(UIDataBus.get_settings().get("galaxy_quality", 0))
	_build_central_point()
	_build_central_glow()
	var ring_defs := [
		["Ring01", 250, 10.0, 11.0, 0.10, 0.12, 0.3, 0.15, 3.0, 0.85, 0.0, 0.0],
		["Ring02", 250, 14.0, 15.0, 0.085, 0.105, 0.3, 0.15, 3.0, 0.85, PI / 2.0, 0.0],
		["Ring03", 250, 18.0, 19.0, 0.07, 0.09, 0.3, 0.16, 2.8, 0.85, PI / 3.0, PI / 6.0],
		["Ring04", 250, 22.0, 23.0, 0.06, 0.08, 0.4, 0.17, 2.6, 0.85, 0.0, PI / 3.0],
		["Ring05", 250, 26.0, 27.0, 0.05, 0.07, 0.4, 0.17, 2.5, 0.80, PI / 4.0, PI / 2.0],
		["Ring06", 250, 30.0, 31.0, 0.045, 0.065, 0.4, 0.18, 2.5, 0.80, 2.0 * PI / 3.0, 0.0],
		["Ring07", 250, 33.0, 34.0, 0.04, 0.06, 0.5, 0.18, 2.3, 0.75, PI / 6.0, PI / 4.0],
		["Ring08", 250, 36.0, 37.0, 0.035, 0.055, 0.5, 0.19, 2.3, 0.75, PI / 2.0, PI / 3.0],
		["Ring09", 250, 39.0, 40.0, 0.03, 0.05, 0.5, 0.19, 2.0, 0.70, 5.0 * PI / 6.0, PI / 6.0],
		["Ring10", 250, 42.0, 43.0, 0.025, 0.045, 0.6, 0.20, 2.0, 0.70, PI / 3.0, 2.0 * PI / 3.0],
		["Ring11", 250, 45.0, 46.0, 0.02, 0.04, 0.6, 0.20, 1.8, 0.65, 0.0, PI / 2.0],
		["Ring12", 250, 48.0, 49.0, 0.02, 0.035, 0.6, 0.20, 1.8, 0.65, PI / 4.0, 5.0 * PI / 6.0],
	]
	# Tilted rings (tilt_x/tilt_z != 0) alias into a single bright vertical
	# column under the Compatibility renderer at Overview/Regional distance —
	# confirmed by isolation (rings alone reproduce it; zeroing tilt alone
	# removes it; screenshots in pass2/probe/ring_tilt/). Not a shader compile
	# failure, so the pass-2 relaxation clause applies per-parameter rather
	# than swapping the whole shader: Westley's Forward+ seat keeps the tilt,
	# the Compatibility QA render flattens the rings instead.
	var flat_qa := RenderingServer.get_current_rendering_method() == "gl_compatibility"
	for d in ring_defs:
		_build_ring(d[0], d[1], d[2], d[3], d[4], d[5], d[6], d[7], d[8],
			Color(1.0, 0.88, 0.5, d[9]), 0.0 if flat_qa else d[10], 0.0 if flat_qa else d[11])
	_build_radial_streams()
	_build_wash()
	_build_star_layers()
	_build_camera_dust()
	_build_grid_plane()
	_start_central_pulse()
	_start_stream_rotation()


func _build_central_point() -> void:
	_central_point = MeshInstance3D.new()
	var sphere := SphereMesh.new()
	sphere.radius = 1.5
	sphere.height = 3.0
	sphere.radial_segments = 32
	sphere.rings = 16
	_central_point.mesh = sphere

	var mat := StandardMaterial3D.new()
	mat.albedo_color = Color(1.0, 0.95, 0.75, 1.0)
	mat.emission_enabled = true
	mat.emission = Color(1.0, 0.90, 0.55)
	mat.emission_energy_multiplier = 2.5
	mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	_central_point.material_override = mat
	add_child(_central_point)

	var halo := MeshInstance3D.new()
	var halo_quad := QuadMesh.new()
	halo_quad.size = Vector2(20.0, 20.0)
	halo.mesh = halo_quad

	var grad := GradientTexture2D.new()
	var g := Gradient.new()
	g.set_color(0, Color(1.0, 0.92, 0.6, 1.0))
	g.set_color(1, Color(1.0, 0.92, 0.6, 0.0))
	grad.gradient = g
	grad.fill = GradientTexture2D.FILL_RADIAL
	grad.fill_from = Vector2(0.5, 0.5)
	grad.fill_to = Vector2(0.5, 0.0)
	grad.width = 256
	grad.height = 256

	var halo_mat := StandardMaterial3D.new()
	halo_mat.albedo_color = Color(1.0, 0.92, 0.6, 0.5)
	halo_mat.albedo_texture = grad
	halo_mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	halo_mat.blend_mode = BaseMaterial3D.BLEND_MODE_ADD
	halo_mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	halo_mat.billboard_mode = BaseMaterial3D.BILLBOARD_ENABLED
	halo_mat.no_depth_test = true
	halo.material_override = halo_mat
	add_child(halo)


func _build_central_glow() -> void:
	var particles := GPUParticles3D.new()
	particles.amount = _amt(200)
	particles.lifetime = 6.0
	particles.fixed_fps = 60
	particles.interpolate = true

	var proc_mat := ParticleProcessMaterial.new()
	proc_mat.emission_shape = ParticleProcessMaterial.EMISSION_SHAPE_SPHERE
	proc_mat.emission_sphere_radius = 3.0
	proc_mat.initial_velocity_min = 0.3
	proc_mat.initial_velocity_max = 1.0
	proc_mat.damping_min = 2.0
	proc_mat.damping_max = 4.0
	proc_mat.gravity = Vector3.ZERO
	proc_mat.color = Color(1.0, 0.92, 0.6, 0.6)
	particles.process_material = proc_mat

	particles.draw_pass_1 = _make_particle_quad(0.3)
	particles.material_override = _make_additive_material(
		Color(1.0, 0.92, 0.6, 0.6),
		Color(1.0, 0.90, 0.55),
		3.0
	)
	particles.visibility_aabb = AABB(Vector3(-200, -200, -200), Vector3(400, 400, 400))
	add_child(particles)


func _build_ring(ring_name: String, count: int, r_min: float, r_max: float,
		s_min: float, s_max: float, thickness: float, quad_size: float,
		energy: float, gold_override := Color(1.0, 0.88, 0.5, 0.85),
		p_tilt_x := 0.0, p_tilt_z := 0.0) -> void:
	var particles := GPUParticles3D.new()
	particles.name = ring_name
	particles.amount = _amt(count)
	particles.lifetime = 1000.0
	particles.explosiveness = 1.0
	particles.fixed_fps = 60
	particles.interpolate = true

	var shader_mat := ShaderMaterial.new()
	shader_mat.shader = load("res://scenes/mockups/galaxy/shaders/ring_particles.gdshader")
	shader_mat.set_shader_parameter("radius_min", r_min)
	shader_mat.set_shader_parameter("radius_max", r_max)
	shader_mat.set_shader_parameter("speed_min", s_min)
	shader_mat.set_shader_parameter("speed_max", s_max)
	shader_mat.set_shader_parameter("disc_thickness", thickness)
	shader_mat.set_shader_parameter("total_particles", _amt(count))
	shader_mat.set_shader_parameter("blue_fraction", 0.15)
	shader_mat.set_shader_parameter("gold_color", gold_override)
	shader_mat.set_shader_parameter("blue_color", Color(0.7, 0.8, 1.0, 0.7))
	shader_mat.set_shader_parameter("tilt_x", p_tilt_x)
	shader_mat.set_shader_parameter("tilt_z", p_tilt_z)
	particles.process_material = shader_mat

	particles.draw_pass_1 = _make_particle_quad(quad_size)
	particles.material_override = _make_additive_material(
		Color(1.0, 0.88, 0.5, 0.85),
		Color(1.0, 0.88, 0.5),
		energy
	)
	particles.visibility_aabb = AABB(Vector3(-200, -200, -200), Vector3(400, 400, 400))
	add_child(particles)


func _build_radial_streams() -> void:
	_stream_pivot = Node3D.new()
	_stream_pivot.name = "StreamPivot"
	add_child(_stream_pivot)

	var particles := GPUParticles3D.new()
	particles.name = "RadialStreams"
	particles.amount = _amt(600)
	particles.lifetime = 1000.0
	particles.explosiveness = 1.0
	particles.fixed_fps = 60
	particles.interpolate = true

	var shader_mat := ShaderMaterial.new()
	shader_mat.shader = load("res://scenes/mockups/galaxy/shaders/stream_particles.gdshader")
	shader_mat.set_shader_parameter("outer_radius", 45.0)
	shader_mat.set_shader_parameter("inner_radius", 5.0)
	shader_mat.set_shader_parameter("flow_speed", 0.03)
	shader_mat.set_shader_parameter("stream_width", 1.5)
	shader_mat.set_shader_parameter("y_scatter", 1.5)
	shader_mat.set_shader_parameter("num_streams", 6)
	shader_mat.set_shader_parameter("stream_color", Color(1.0, 0.92, 0.65, 0.7))
	particles.process_material = shader_mat

	particles.draw_pass_1 = _make_particle_quad(0.12)
	particles.material_override = _make_additive_material(
		Color(1.0, 0.92, 0.65, 0.7),
		Color(1.0, 0.90, 0.55),
		2.5
	)
	particles.visibility_aabb = AABB(Vector3(-200, -200, -200), Vector3(400, 400, 400))
	_stream_pivot.add_child(particles)


func _process(delta: float) -> void:
	var cam := get_viewport().get_camera_3d()
	if cam == null:
		return
	if cam.far != CAMERA_FAR:
		cam.far = CAMERA_FAR
	_dust_time += delta
	update_dust(cam.global_position, _dust_time)


static func layer_radius(i: int) -> float:
	return LAYER_RADII[i] * BACKDROP_SCALE


static func layer_star_count(_i: int, tier: int) -> int:
	return maxi(1, STARS_PER_LAYER / 2) if tier == TIER_FEWER else STARS_PER_LAYER


static func _hash(a: int, b: int) -> int:
	var x: int = ((a * 73856093) ^ (b * 19349663) ^ 0x9E3779B9) & 0xFFFFFFFF
	x ^= x >> 16
	x = (x * 0x45D9F3B) & 0xFFFFFFFF
	x ^= x >> 16
	x = (x * 0x45D9F3B) & 0xFFFFFFFF
	x ^= x >> 16
	return x


static func _unit(a: int, b: int) -> float:
	return float(_hash(a, b)) / 4294967296.0


# A direction uniform on the sphere from integer hashes: points in the unit cube are redrawn
# until one falls inside the ball, then normalised.
static func _direction(key: int) -> Vector3:
	for attempt in 32:
		var v := Vector3(
			_unit(key, 3 * attempt + 1) * 2.0 - 1.0,
			_unit(key, 3 * attempt + 2) * 2.0 - 1.0,
			_unit(key, 3 * attempt + 3) * 2.0 - 1.0)
		var l2 := v.length_squared()
		if l2 > 0.0001 and l2 <= 1.0:
			return v / sqrt(l2)
	return Vector3.UP


# Radial offset of star k of layer i in sigmas: twelve hashed uniforms summed (mean 0, variance 1),
# clipped at SHELL_CLIP.
static func _shell_z(key: int) -> float:
	var z := -6.0
	for m in 12:
		z += _unit(key, 100 + m)
	return clampf(z, -SHELL_CLIP, SHELL_CLIP)


static func _star_key(i: int, k: int) -> int:
	return i * 1000003 + k


static func layer_star_positions(i: int, tier: int) -> PackedVector3Array:
	var out := PackedVector3Array()
	var r0 := layer_radius(i)
	for k in layer_star_count(i, tier):
		var key := _star_key(i, k)
		out.append(_direction(key) * (r0 * (1.0 + SHELL_SIGMA * _shell_z(key))))
	return out


static func layer_star_alphas(i: int, tier: int) -> PackedFloat32Array:
	var out := PackedFloat32Array()
	for k in layer_star_count(i, tier):
		var key := _star_key(i, k)
		var roll := _unit(key, 200)
		var fall := 1.0 - pow(_shell_z(key) / SHELL_CLIP, 2.0)
		out.append(lerpf(STAR_ALPHA_MIN, STAR_ALPHA_MAX, roll * roll) * LAYER_BRIGHTNESS[i] * fall * fall)
	return out


static func _star_world_size(i: int) -> float:
	return 0.5 * (STAR_PX_MIN + STAR_PX_MAX) * 2.0 * layer_radius(i) * tan(deg_to_rad(STAR_REF_FOV_DEG) * 0.5) / STAR_REF_VIEWPORT_H


static func star_pixel_size(i: int, distance: float, viewport_h_px: float, fov_deg: float) -> float:
	return clampf(_star_world_size(i) * viewport_h_px / (2.0 * maxf(distance, 0.001) * tan(deg_to_rad(fov_deg) * 0.5)), STAR_PX_MIN, STAR_PX_MAX)


# The view-direction wash as the colour the player sees (the background plus a few thousandths).
static func wash_colour(dir: Vector3) -> Color:
	var up := 0.5 + 0.5 * dir.y
	var side := 0.5 + 0.5 * dir.x
	return BACKGROUND + Color(
		0.002 + 0.004 * side,
		0.002 + 0.003 * up + 0.002 * side,
		0.003 + 0.005 * up + 0.003 * (1.0 - side), 0.0)


static func wrap_mote(p: Vector3, cam: Vector3) -> Vector3:
	var half := DUST_BOX * 0.5
	return cam + Vector3(
		fposmod(p.x - cam.x + half, DUST_BOX) - half,
		fposmod(p.y - cam.y + half, DUST_BOX) - half,
		fposmod(p.z - cam.z + half, DUST_BOX) - half)


func camera_reach() -> float:
	var oc: Node = get_parent().get_node_or_null("OrbitCamera") if get_parent() != null else null
	return (oc.DIST_MAX if oc != null else 0.0) + GalaxyGen.R_BALL


func qa_inventory() -> Dictionary:
	var layers: Array = []
	for i in LAYER_COUNT:
		var node := get_node_or_null("StarLayer%d" % i) as MeshInstance3D
		layers.append({"radius": layer_radius(i), "stars": node.mesh.surface_get_array_len(0) if node != null and node.mesh != null else 0})
	var wash := get_node_or_null("Wash") as MeshInstance3D
	var cam: Camera3D = get_viewport().get_camera_3d() if is_inside_tree() else null
	return {
		"wash": wash != null and wash.mesh != null and wash.mesh.get_surface_count() == 1,
		"star_layers": layers,
		"dust": {"motes": _dust.multimesh.instance_count if _dust != null else 0, "box": DUST_BOX},
		"far": cam.far if cam != null else 0.0,
		"added_draws": _added_draws(),
	}


func _added_draws() -> int:
	var draws := 0
	for node_name in ["Wash", "StarLayer0", "StarLayer1", "StarLayer2", "StarLayer3", "CameraDust"]:
		var node := get_node_or_null(node_name)
		if node is MeshInstance3D and node.mesh != null:
			draws += node.mesh.get_surface_count()
		elif node is MultiMeshInstance3D and node.multimesh != null and node.multimesh.mesh != null:
			draws += node.multimesh.mesh.get_surface_count()
	return draws


func _build_wash() -> void:
	var lat_bands := 12
	var lon_bands := 24
	var verts := PackedVector3Array()
	var custom := PackedFloat32Array()
	var base := BACKGROUND.srgb_to_linear()
	for lat in lat_bands + 1:
		var theta := PI * float(lat) / float(lat_bands)
		for lon in lon_bands + 1:
			var phi := TAU * float(lon) / float(lon_bands)
			var dir := Vector3(sin(theta) * cos(phi), cos(theta), sin(theta) * sin(phi))
			verts.append(dir * WASH_MESH_RADIUS)
			# the additive term that lands the display colour wash_colour(dir) on the background
			var add := wash_colour(dir).srgb_to_linear() - base
			custom.append_array(PackedFloat32Array([add.r, add.g, add.b, 0.0]))
	var indices := PackedInt32Array()
	for lat in lat_bands:
		for lon in lon_bands:
			var a := lat * (lon_bands + 1) + lon
			var b := a + lon_bands + 1
			indices.append_array(PackedInt32Array([a, b, a + 1, a + 1, b, b + 1]))
	var arrays := []
	arrays.resize(Mesh.ARRAY_MAX)
	arrays[Mesh.ARRAY_VERTEX] = verts
	arrays[Mesh.ARRAY_CUSTOM0] = custom
	arrays[Mesh.ARRAY_INDEX] = indices
	var mesh := ArrayMesh.new()
	mesh.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arrays, [], {}, Mesh.ARRAY_CUSTOM_RGBA_FLOAT << Mesh.ARRAY_FORMAT_CUSTOM0_SHIFT)
	var mat := ShaderMaterial.new()
	mat.shader = WashShader
	var node := MeshInstance3D.new()
	node.name = "Wash"
	node.mesh = mesh
	node.material_override = mat
	node.extra_cull_margin = 16384.0
	add_child(node)


func _build_star_layers() -> void:
	for i in LAYER_COUNT:
		var positions := layer_star_positions(i, _tier)
		var alphas := layer_star_alphas(i, _tier)
		var colours := PackedColorArray()
		for k in positions.size():
			var tint := STAR_GOLD if _unit(_star_key(i, k), 300) < STAR_GOLD_FRACTION else STAR_BLUE
			colours.append(Color(tint.r, tint.g, tint.b, alphas[k]))
		var arrays := []
		arrays.resize(Mesh.ARRAY_MAX)
		arrays[Mesh.ARRAY_VERTEX] = positions
		arrays[Mesh.ARRAY_COLOR] = colours
		var mesh := ArrayMesh.new()
		mesh.add_surface_from_arrays(Mesh.PRIMITIVE_POINTS, arrays)
		var mat := ShaderMaterial.new()
		mat.shader = StarsShader
		mat.set_shader_parameter("px_min", STAR_PX_MIN)
		mat.set_shader_parameter("px_max", STAR_PX_MAX)
		mat.set_shader_parameter("world_size", _star_world_size(i))
		var node := MeshInstance3D.new()
		node.name = "StarLayer%d" % i
		node.mesh = mesh
		node.material_override = mat
		add_child(node)


func _build_camera_dust() -> void:
	var count := _amt(DUST_COUNT)
	var half := DUST_BOX * 0.5
	for k in count:
		_dust_homes.append(Vector3(
			_unit(k, 401) * DUST_BOX - half, _unit(k, 402) * DUST_BOX - half, _unit(k, 403) * DUST_BOX - half))
		_dust_velocities.append(Vector3(
			_unit(k, 501) - 0.5, _unit(k, 502) - 0.5, _unit(k, 503) - 0.5) * DUST_DRIFT)
	_dust_positions.resize(count)
	var quad := QuadMesh.new()
	quad.size = Vector2(DUST_QUAD, DUST_QUAD)
	var mat := ShaderMaterial.new()
	mat.shader = DustShader
	quad.material = mat
	var mm := MultiMesh.new()
	mm.transform_format = MultiMesh.TRANSFORM_3D
	mm.use_colors = true
	mm.mesh = quad
	mm.instance_count = count
	_dust = MultiMeshInstance3D.new()
	_dust.name = "CameraDust"
	_dust.multimesh = mm
	add_child(_dust)
	update_dust(Vector3.ZERO, 0.0)


func update_dust(cam_pos: Vector3, t: float) -> void:
	var count := _dust_homes.size()
	var half := DUST_BOX * 0.5
	var buffer := PackedFloat32Array()
	buffer.resize(count * 16)
	for k in count:
		var p := wrap_mote(_dust_homes[k] + _dust_velocities[k] * t, cam_pos)
		_dust_positions[k] = p
		var d := _dust_positions[k] - cam_pos
		var face := maxf(absf(d.x), maxf(absf(d.y), absf(d.z)))
		var tint := DUST_GOLD if k % 2 == 0 else DUST_BLUE
		var o := k * 16
		buffer[o] = 1.0
		buffer[o + 3] = _dust_positions[k].x
		buffer[o + 5] = 1.0
		buffer[o + 7] = _dust_positions[k].y
		buffer[o + 10] = 1.0
		buffer[o + 11] = _dust_positions[k].z
		buffer[o + 12] = tint.r
		buffer[o + 13] = tint.g
		buffer[o + 14] = tint.b
		buffer[o + 15] = tint.a * clampf((half - face) / (half * DUST_FADE), 0.0, 1.0)
	_dust.multimesh.buffer = buffer


func get_dust_positions() -> PackedVector3Array:
	return _dust_positions


func _build_grid_plane() -> void:
	var grid := MeshInstance3D.new()
	grid.name = "GridPlane"
	grid.position.y = -5.0

	var im := ImmediateMesh.new()
	var mat := StandardMaterial3D.new()
	mat.albedo_color = Color(0.8, 0.75, 0.55, 0.04)
	mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	mat.no_depth_test = true

	var ring_radii := [10.0, 20.0, 30.0, 40.0, 50.0]
	var segments := 64

	for radius in ring_radii:
		im.surface_begin(Mesh.PRIMITIVE_LINE_STRIP)
		for i in range(segments + 1):
			var angle := float(i) / float(segments) * TAU
			im.surface_add_vertex(Vector3(cos(angle) * radius, 0.0, sin(angle) * radius))
		im.surface_end()

	var radial_count := 12
	var max_radius := 50.0
	for i in range(radial_count):
		var angle := float(i) / float(radial_count) * TAU
		im.surface_begin(Mesh.PRIMITIVE_LINES)
		im.surface_add_vertex(Vector3.ZERO)
		im.surface_add_vertex(Vector3(cos(angle) * max_radius, 0.0, sin(angle) * max_radius))
		im.surface_end()

	grid.mesh = im
	grid.material_override = mat
	add_child(grid)


func _start_central_pulse() -> void:
	_pulse_tween = create_tween().set_loops()
	_pulse_tween.tween_property(_central_point, "scale", Vector3.ONE * 1.08, 3.927).set_ease(Tween.EASE_IN_OUT).set_trans(Tween.TRANS_SINE)
	_pulse_tween.tween_property(_central_point, "scale", Vector3.ONE * 0.92, 3.927).set_ease(Tween.EASE_IN_OUT).set_trans(Tween.TRANS_SINE)


func _start_stream_rotation() -> void:
	_rotation_tween = create_tween().set_loops()
	_rotation_tween.tween_property(_stream_pivot, "rotation:y", TAU, TAU / 0.01).set_ease(Tween.EASE_IN_OUT)
	_rotation_tween.tween_callback(func(): _stream_pivot.rotation.y = 0.0)


func _make_particle_quad(size: float) -> QuadMesh:
	var quad := QuadMesh.new()
	quad.size = Vector2(size, size)
	return quad


func _make_additive_material(albedo: Color, emission: Color, energy: float) -> StandardMaterial3D:
	var mat := StandardMaterial3D.new()
	mat.albedo_color = albedo
	mat.emission_enabled = true
	mat.emission = emission
	mat.emission_energy_multiplier = energy
	mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	mat.blend_mode = BaseMaterial3D.BLEND_MODE_ADD
	mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	mat.billboard_mode = BaseMaterial3D.BILLBOARD_ENABLED
	return mat


func _amt(n: int) -> int:
	return maxi(1, n / 2) if _tier == TIER_FEWER else n
