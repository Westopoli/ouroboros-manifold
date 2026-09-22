extends Control

const QaPlants := preload("res://scenes/mockups/_shared/qa_plants.gd")
const GROUP_HIT_RADIUS := 18.0
const ARC_BEND := 0.18
const GRID_DIVISIONS := 10
# Flat height above the nominal y=0 ground plane for all world-space overlay geometry.
# A real implementation would sample terrain height per point (ground.gd's job, out of
# scope here); a constant offset is the correct simple stand-in for a schematic overlay.
const HEIGHT_OFFSET := 30.0

const GRID_COLOR := Color(1, 1, 1, 0.25)
const OBJECTIVE_COLOR := Color(1, 0.85, 0.2, 1)
const BORDER_COLORS := {
	"coast": Color(0.25, 0.55, 0.95, 1),
	"cliff": Color(0.5, 0.42, 0.35, 1),
	"wall": Color(0.75, 0.7, 0.55, 1),
}
const FACTION_COLORS := [Color("#4099FF"), Color("#FF4738")]

var _field_map: FieldMap
var _camera_rig: Node3D
var _camera: Camera3D
var _world_container: Node3D
var _unit_groups: Array = []
var _arrows: Array = []
var _selected_group_index: int = -1


func _ready() -> void:
	_camera_rig = get_node("../../CameraRig")
	_camera = _camera_rig.get_node("Camera3D")
	_camera_rig.band_changed.connect(_on_band_changed)
	_apply_band(_camera_rig.get_current_band())


func get_overlay_node() -> Node3D:
	return _world_container


func _ensure_world_container() -> void:
	if QaPlants.is_active("overlay-screen-space"):
		if _world_container:
			_world_container.queue_free()
			_world_container = null
		return
	if _world_container == null:
		_world_container = Node3D.new()
		_world_container.name = "MapViewGeometry"
		get_node("../../World").add_child(_world_container)


func set_field_map(field_map: FieldMap) -> void:
	_field_map = field_map
	_rebuild_world_geometry()
	# Fake unit groups: no real factions/units in this mockup, so we just plant one
	# marker per spawn_point node (there are always exactly two) and alternate colors.
	_unit_groups.clear()
	var faction := 0
	for node in field_map.nodes:
		if node.type == "spawn_point":
			_unit_groups.append({pos = Vector3(node.pos.x, 0.0, node.pos.y), faction = faction})
			faction = (faction + 1) % FACTION_COLORS.size()
	_arrows.clear()
	_selected_group_index = -1
	queue_redraw()


func _on_band_changed(band: String) -> void:
	_apply_band(band)


func _apply_band(band: String) -> void:
	visible = band == "map"
	if _world_container:
		_world_container.visible = visible


func _process(_delta: float) -> void:
	if visible:
		queue_redraw()


func _rebuild_world_geometry() -> void:
	_ensure_world_container()
	_apply_band(_camera_rig.get_current_band())
	if _world_container == null:
		return
	for child in _world_container.get_children():
		child.queue_free()

	var canvas: float = _field_map.canvas

	var grid_mesh := ImmediateMesh.new()
	grid_mesh.surface_begin(Mesh.PRIMITIVE_LINES)
	for i in range(GRID_DIVISIONS + 1):
		var t: float = canvas * i / float(GRID_DIVISIONS)
		grid_mesh.surface_add_vertex(Vector3(t, HEIGHT_OFFSET, 0.0))
		grid_mesh.surface_add_vertex(Vector3(t, HEIGHT_OFFSET, canvas))
		grid_mesh.surface_add_vertex(Vector3(0.0, HEIGHT_OFFSET, t))
		grid_mesh.surface_add_vertex(Vector3(canvas, HEIGHT_OFFSET, t))
	grid_mesh.surface_end()
	var grid_mat := StandardMaterial3D.new()
	grid_mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	grid_mat.albedo_color = GRID_COLOR
	grid_mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	var grid_instance := MeshInstance3D.new()
	grid_instance.mesh = grid_mesh
	grid_instance.material_override = grid_mat
	_world_container.add_child(grid_instance)

	var border_mesh := ImmediateMesh.new()
	border_mesh.surface_begin(Mesh.PRIMITIVE_LINES)
	for border in _field_map.borders:
		var pts: Array = border.points
		if pts.size() < 2:
			continue
		var color: Color = BORDER_COLORS.get(border.kind, Color.WHITE)
		for i in range(pts.size() - 1):
			var a: Vector2 = pts[i]
			var b: Vector2 = pts[i + 1]
			border_mesh.surface_set_color(color)
			border_mesh.surface_add_vertex(Vector3(a.x, HEIGHT_OFFSET, a.y))
			border_mesh.surface_set_color(color)
			border_mesh.surface_add_vertex(Vector3(b.x, HEIGHT_OFFSET, b.y))
	border_mesh.surface_end()
	var border_mat := StandardMaterial3D.new()
	border_mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	border_mat.vertex_color_use_as_albedo = true
	var border_instance := MeshInstance3D.new()
	border_instance.mesh = border_mesh
	border_instance.material_override = border_mat
	_world_container.add_child(border_instance)

	for col in range(GRID_DIVISIONS):
		var letter := String.chr(65 + col)
		var x: float = canvas * (col + 0.5) / float(GRID_DIVISIONS)
		_add_grid_label(letter, Vector3(x, HEIGHT_OFFSET, 0.0))
	for row in range(GRID_DIVISIONS):
		var z: float = canvas * (row + 0.5) / float(GRID_DIVISIONS)
		_add_grid_label(str(row + 1), Vector3(0.0, HEIGHT_OFFSET, z))


func _add_grid_label(text: String, world_pos: Vector3) -> void:
	var label := Label3D.new()
	label.text = text
	label.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	label.modulate = GRID_COLOR
	label.position = world_pos
	_world_container.add_child(label)


func _project(world_pos: Vector3) -> Vector2:
	return _camera.unproject_position(world_pos)


func _gui_input(event: InputEvent) -> void:
	if not (event is InputEventMouseButton):
		return
	var mb := event as InputEventMouseButton
	if mb.button_index != MOUSE_BUTTON_LEFT or not mb.pressed:
		return

	if _selected_group_index == -1:
		for i in range(_unit_groups.size()):
			var world_pos: Vector3 = _unit_groups[i].pos
			if _camera.is_position_behind(world_pos):
				continue
			var screen_pos: Vector2 = _project(world_pos)
			if screen_pos.distance_to(mb.position) <= GROUP_HIT_RADIUS:
				_selected_group_index = i
				break
	else:
		# Ray from the click through the current camera, intersected with the y=0 ground
		# plane, so the stored order point is a real world position, not a screen pixel.
		var origin: Vector3 = _camera.project_ray_origin(mb.position)
		var dir: Vector3 = _camera.project_ray_normal(mb.position)
		var ground := Plane(Vector3.UP, 0.0)
		var hit = ground.intersects_ray(origin, dir)
		if hit != null:
			_arrows.append({from_world = _unit_groups[_selected_group_index].pos, to_world = hit})
		_selected_group_index = -1

	queue_redraw()


func _draw() -> void:
	if _field_map == null or _camera == null:
		return
	if QaPlants.is_active("overlay-screen-space"):
		_draw_grid_screen_space()
	_draw_objectives()
	_draw_unit_groups()
	_draw_arrows()


func _draw_grid_screen_space() -> void:
	var rect: Vector2 = get_viewport_rect().size
	for i in range(GRID_DIVISIONS + 1):
		var x: float = rect.x * i / float(GRID_DIVISIONS)
		draw_line(Vector2(x, 0.0), Vector2(x, rect.y), GRID_COLOR, 1.0)
		var y: float = rect.y * i / float(GRID_DIVISIONS)
		draw_line(Vector2(0.0, y), Vector2(rect.x, y), GRID_COLOR, 1.0)


func _draw_objectives() -> void:
	for node in _field_map.nodes:
		if node.type == "objective":
			var world_pos := Vector3(node.pos.x, 0.0, node.pos.y)
			if _camera.is_position_behind(world_pos):
				continue
			draw_arc(_project(world_pos), 16.0, 0.0, TAU, 24, OBJECTIVE_COLOR, 2.0)


func _draw_unit_groups() -> void:
	for i in range(_unit_groups.size()):
		var group: Dictionary = _unit_groups[i]
		var world_pos: Vector3 = group.pos
		if _camera.is_position_behind(world_pos):
			continue
		var pos: Vector2 = _project(world_pos)
		var color: Color = FACTION_COLORS[group.faction]
		var chevron := PackedVector2Array([pos + Vector2(-10, 8), pos + Vector2(0, -10), pos + Vector2(10, 8)])
		draw_polyline(chevron, color, 3.0)
		if i == _selected_group_index:
			draw_arc(pos, 14.0, 0.0, TAU, 20, Color.WHITE, 1.5)


func _draw_arrows() -> void:
	for arrow in _arrows:
		var from_world: Vector3 = arrow.from_world
		var to_world: Vector3 = arrow.to_world
		if _camera.is_position_behind(from_world) or _camera.is_position_behind(to_world):
			continue
		var from: Vector2 = _project(from_world)
		var to: Vector2 = _project(to_world)
		var mid: Vector2 = (from + to) * 0.5
		var dir: Vector2 = to - from
		# Curve bend: offset the Bezier control point perpendicular to the straight line by
		# a fraction of its length, so short and long orders both curve proportionally.
		var perp: Vector2 = Vector2(-dir.y, dir.x).normalized() if dir.length() > 0.001 else Vector2.ZERO
		var control: Vector2 = mid + perp * dir.length() * ARC_BEND

		var segments := 16
		var prev := from
		for s in range(1, segments + 1):
			var t := float(s) / float(segments)
			var point: Vector2 = from.lerp(control, t).lerp(control.lerp(to, t), t)
			draw_line(prev, point, Color.WHITE, 2.0)
			prev = point

		var tangent: Vector2 = (to - control).normalized() if to.distance_to(control) > 0.001 else (to - from).normalized()
		var back: Vector2 = -tangent
		var head_a: Vector2 = to + back.rotated(deg_to_rad(25)) * 14.0
		var head_b: Vector2 = to + back.rotated(deg_to_rad(-25)) * 14.0
		draw_line(to, head_a, Color.WHITE, 2.0)
		draw_line(to, head_b, Color.WHITE, 2.0)
