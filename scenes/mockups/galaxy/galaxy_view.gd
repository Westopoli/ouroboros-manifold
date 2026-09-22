extends Node3D

const QaPlants := preload("res://scenes/mockups/_shared/qa_plants.gd")

const POINT_BASE_RADIUS := 1.4
const NEUTRAL_COLOR := Color(0.55, 0.55, 0.58, 1.0)
const TRADE_DIM := Color(0.42, 0.44, 0.5, 0.5)
const FLASH_DURATION := 0.6
const LOCAL_FAR_WU := 30.0

var _galaxy: Galaxy
var _points: MultiMeshInstance3D
var _wv_data: Node
var _constellation: Node3D
var _shell: Node3D
var _names: Node3D
var _flash_boost: Dictionary = {}
var _flash_rings: Array = []
# Mirrors each point's last-set colour outside the MultiMesh's own buffer:
# MultiMesh.get_instance_color() reads back zeroed data under the headless
# dummy renderer verify.gd runs under, so verify reads this array instead.
var _point_colors: Array = []


func _ready() -> void:
	_build_ambient()
	_wv_data = Node.new()
	_wv_data.set_script(load("res://scenes/mockups/galaxy/legacy_world_view_data.gd"))
	_wv_data.name = "WorldViewData"
	add_child(_wv_data)
	_constellation = Node3D.new()
	_constellation.set_script(load("res://scenes/mockups/galaxy/legacy_constellation_renderer.gd"))
	_constellation.name = "ConstellationRenderer"
	add_child(_constellation)
	_shell = Node3D.new()
	_shell.set_script(load("res://scenes/mockups/galaxy/legacy_shell_renderer.gd"))
	_shell.name = "ShellRenderer"
	add_child(_shell)
	# Zoom controller lives on OrbitCamera, a sibling created after GalaxyView
	# in the scene tree (World before OrbitCamera in galaxy_mockup.tscn), so
	# it does not exist yet at this _ready(). setup() with null is safe —
	# _process() no-ops until attach_camera() sets it (called from
	# galaxy_mockup.gd's own _ready(), which runs last, after every sibling).
	_constellation.setup(_wv_data, null)
	_shell.setup(_wv_data, null)


func attach_camera(camera: Node) -> void:
	_constellation._zoom_controller = camera.get_zoom_controller()
	_shell._zoom_controller = camera.get_zoom_controller()


func get_faction_shell_count() -> int:
	return _shell.get_faction_shell_count() if _shell else 0


func build(galaxy: Galaxy) -> void:
	_galaxy = galaxy
	_flash_boost.clear()
	for r in _flash_rings:
		r.node.free()
	_flash_rings.clear()
	_build_points()
	_populate_wv_data()
	_build_names()
	update_view(50.0, -1, -1, -1)


func get_galaxy() -> Galaxy:
	return _galaxy


func _region_size(significance: float) -> float:
	return 2.0 * POINT_BASE_RADIUS * (0.6 + 1.4 * significance)


func get_point_color(system_id: int) -> Color:
	if system_id < 0 or system_id >= _point_colors.size():
		return Color.BLACK
	return _point_colors[system_id]


func owner_color(owner_id: int, galaxy: Galaxy) -> Color:
	if owner_id == -1 or galaxy == null:
		return NEUTRAL_COLOR
	for f in galaxy.factions:
		if f.id == owner_id:
			var v := 0.95 if owner_id == 0 else 0.85
			return Color.from_hsv(f.hue, 0.65, v, 1.0)
	return NEUTRAL_COLOR


func _build_points() -> void:
	if _points:
		_points.free()
	_points = MultiMeshInstance3D.new()
	_points.name = "Points"
	var mm := MultiMesh.new()
	mm.transform_format = MultiMesh.TRANSFORM_3D
	mm.use_colors = true
	var sphere := SphereMesh.new()
	sphere.radius = POINT_BASE_RADIUS
	sphere.height = POINT_BASE_RADIUS * 2.0
	sphere.radial_segments = 12
	sphere.rings = 8
	mm.mesh = sphere
	mm.instance_count = _galaxy.systems.size()
	_point_colors.resize(_galaxy.systems.size())
	_point_colors.fill(Color.BLACK)
	var mat := StandardMaterial3D.new()
	mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	mat.vertex_color_use_as_albedo = true
	mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	_points.material_override = mat
	_points.multimesh = mm
	add_child(_points)


func _populate_wv_data() -> void:
	var skip_connections := QaPlants.is_active("edges-2d-overlay")
	GalaxyAdapter.populate(_wv_data, _galaxy, Callable(self, "owner_color"), Callable(self, "_region_size"), TRADE_DIM, skip_connections)
	if skip_connections:
		_build_filaments_2d_fault()


# fault: edges-2d-overlay draws lanes in a full-rect Control's _draw() under HUD
# instead of ConstellationRenderer's tubes; the adapter skips add_connection()
# so ConstellationRenderer stays empty and EDGES-8 can tell them apart.
func _build_filaments_2d_fault() -> void:
	var hud := get_node("../../HUD")
	var existing := hud.get_node_or_null("FilamentOverlay2D")
	if existing:
		existing.free()
	var overlay := Control.new()
	overlay.name = "FilamentOverlay2D"
	overlay.set_anchors_preset(Control.PRESET_FULL_RECT)
	overlay.mouse_filter = Control.MOUSE_FILTER_IGNORE
	hud.add_child(overlay)


func _build_names() -> void:
	if _names:
		_names.free()
	_names = Node3D.new()
	_names.name = "Names"
	add_child(_names)
	for f in _galaxy.factions:
		var sum := Vector3.ZERO
		var n := 0
		for sys in _galaxy.systems:
			if sys.owner == f.id:
				sum += sys.pos
				n += 1
		if n == 0:
			continue
		var label := Label3D.new()
		label.name = "Name_%d" % f.id
		label.text = f.name
		label.position = sum / float(n) + Vector3(0, 6, 0)
		label.modulate = owner_color(f.id, _galaxy)
		label.font_size = 40
		# default pixel_size (0.01) renders 40px text ~0.4wu tall, invisible
		# against a ~100wu-radius galaxy; scale it up to read at Overview range.
		label.pixel_size = 0.05
		label.billboard = BaseMaterial3D.BILLBOARD_ENABLED
		label.no_depth_test = true
		label.modulate.a = 0.0
		_names.add_child(label)


func _build_ambient() -> void:
	# Pass 1's own dust/star/grid quads are superseded by the legacy rig below
	# (settled_reach_renderer.gd), which already carries its own ambient dust,
	# starfield, and polar grid alongside the rings and central glow.
	var ambient := Node3D.new()
	ambient.name = "Ambient"
	ambient.set_script(load("res://scenes/mockups/galaxy/legacy_ambient_rig.gd"))
	add_child(ambient)


func _band_weights(d: float) -> Dictionary:
	var w_local := 0.0
	var w_regional := 0.0
	var w_overview := 0.0
	if d <= 25.0:
		w_local = 1.0
	elif d < 40.0:
		var t := (d - 25.0) / 15.0
		w_local = 1.0 - t
		w_regional = t
	elif d <= 65.0:
		w_regional = 1.0
	elif d < 75.0:
		var t2 := (d - 65.0) / 10.0
		w_regional = 1.0 - t2
		w_overview = t2
	else:
		w_overview = 1.0
	return {"local": w_local, "regional": w_regional, "overview": w_overview}


func _faction_emphasis(owner: int, hover_faction: int, pin_faction: int) -> float:
	if pin_faction != -1:
		return 1.0 if owner == pin_faction else 0.05
	if hover_faction != -1:
		return 1.3 if owner == hover_faction else 0.25
	return 1.0


func _flash_scale(system_id: int) -> float:
	if not _flash_boost.has(system_id):
		return 1.0
	var t: float = _flash_boost[system_id] / FLASH_DURATION
	return lerpf(1.0, 3.0, sin(clampf(t, 0.0, 1.0) * PI))


func update_view(distance: float, focused_id: int, hover_faction: int, pin_faction: int) -> void:
	if _galaxy == null or _points == null:
		return
	var w := _band_weights(distance)
	var point_scale_band: float = lerpf(1.0, 0.6, w.overview)
	var name_alpha: float = w.overview

	for i in range(_galaxy.systems.size()):
		var sys: Dictionary = _galaxy.systems[i]
		var emph := _faction_emphasis(sys.owner, hover_faction, pin_faction)
		var local_boost := 1.0
		var sat_mul := 1.0
		if focused_id != -1 and w.local > 0.0:
			if sys.id == focused_id:
				local_boost = lerpf(1.0, 1.5, w.local)
			else:
				var d: float = sys.pos.distance_to(_galaxy.systems[focused_id].pos)
				if d > LOCAL_FAR_WU:
					sat_mul = lerpf(1.0, 0.3, w.local)
		var scale: float = (0.6 + 1.4 * float(sys.significance)) * point_scale_band * local_boost * _flash_scale(sys.id)
		_points.multimesh.set_instance_transform(i, Transform3D(Basis().scaled(Vector3.ONE * scale), sys.pos))
		var base_color: Color = Color.WHITE if QaPlants.is_active("owner-colour-flat") else owner_color(sys.owner, _galaxy)
		var c := Color(base_color.r * emph, base_color.g * emph, base_color.b * emph, base_color.a)
		if sat_mul < 1.0:
			c = c.lerp(Color(0.5, 0.5, 0.5, c.a), 1.0 - sat_mul)
		_points.multimesh.set_instance_color(i, c)
		_point_colors[i] = c

	# Filament alpha-by-band is legacy_constellation_renderer.gd's own
	# _process(), driven by the zoom controller (see attach_camera()); this
	# loop only carries pass 1's hover/pin emphasis into the shader's own
	# emphasis_multiplier uniform, kept separate so the two writers never
	# fight over alpha_multiplier in the same frame.
	if _constellation:
		for key in _constellation.get_filament_visuals():
			var node: MeshInstance3D = _constellation.get_filament_visuals()[key]
			var edge_meta: Dictionary = node.get_meta("edge")
			var owner_a: int = _galaxy.systems[int(edge_meta.a_id)].owner
			var owner_b: int = _galaxy.systems[int(edge_meta.b_id)].owner
			var is_border: bool = owner_a == owner_b and owner_a != -1
			var emph := _faction_emphasis(owner_a if is_border else -1, hover_faction, pin_faction)
			var mat: ShaderMaterial = node.material_override
			if mat:
				mat.set_shader_parameter("emphasis_multiplier", emph)

	if _names:
		for label in _names.get_children():
			label.modulate.a = name_alpha
			# Label3D's outline has its own alpha, separate from modulate; left
			# opaque it stays a fully readable dark silhouette even at alpha 0.
			label.outline_modulate.a = name_alpha


func flash(system_id: int, color: Color) -> void:
	if _galaxy == null or system_id < 0 or system_id >= _galaxy.systems.size():
		return
	_flash_boost[system_id] = 0.0
	var ring := MeshInstance3D.new()
	var quad := QuadMesh.new()
	quad.size = Vector2(3.0, 3.0)
	ring.mesh = quad
	ring.position = _galaxy.systems[system_id].pos
	var mat := StandardMaterial3D.new()
	mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	mat.albedo_color = color
	mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	mat.billboard_mode = BaseMaterial3D.BILLBOARD_ENABLED
	ring.material_override = mat
	add_child(ring)
	_flash_rings.append({"node": ring, "mat": mat, "t": 0.0})


func _process(delta: float) -> void:
	for id in _flash_boost.keys():
		var t: float = _flash_boost[id] + delta
		if t >= FLASH_DURATION:
			_flash_boost.erase(id)
		else:
			_flash_boost[id] = t
	var done: Array = []
	for r in _flash_rings:
		r.t += delta
		var t: float = r.t / FLASH_DURATION
		if t >= 1.0:
			r.node.free()
			done.append(r)
			continue
		r.node.scale = Vector3.ONE * lerpf(1.0, 8.0, t)
		r.mat.albedo_color.a = 1.0 - t
	for r in done:
		_flash_rings.erase(r)


func set_system_owner(system_id: int, faction_id: int) -> void:
	if _galaxy == null or system_id < 0 or system_id >= _galaxy.systems.size():
		return
	_galaxy.systems[system_id].owner = faction_id
	GalaxyAdapter.sync_system(_wv_data, _galaxy, system_id, Callable(self, "owner_color"), Callable(self, "_region_size"), TRADE_DIM)
