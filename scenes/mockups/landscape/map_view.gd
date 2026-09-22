extends Control

const GROUP_HIT_RADIUS := 18.0
const ARC_BEND := 0.18
const GRID_DIVISIONS := 10

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
var _unit_groups: Array = []
var _arrows: Array = []
var _selected_group_index: int = -1


func _ready() -> void:
	_camera_rig = get_node("../../CameraRig")
	_camera_rig.band_changed.connect(_on_band_changed)
	visible = _camera_rig.get_current_band() == "map"


func set_field_map(field_map: FieldMap) -> void:
	_field_map = field_map
	# Fake unit groups: no real factions/units in this mockup, so we just plant one
	# marker per spawn_point node (there are always exactly two) and alternate colors.
	_unit_groups.clear()
	var faction := 0
	for node in field_map.nodes:
		if node.type == "spawn_point":
			_unit_groups.append({pos = node.pos, faction = faction})
			faction = (faction + 1) % FACTION_COLORS.size()
	_arrows.clear()
	_selected_group_index = -1
	queue_redraw()


func _on_band_changed(band: String) -> void:
	visible = band == "map"


func _world_to_screen(world_xz: Vector2) -> Vector2:
	return (world_xz / _field_map.canvas) * size


func _gui_input(event: InputEvent) -> void:
	if not (event is InputEventMouseButton):
		return
	var mb := event as InputEventMouseButton
	if mb.button_index != MOUSE_BUTTON_LEFT or not mb.pressed:
		return

	if _selected_group_index == -1:
		for i in range(_unit_groups.size()):
			var screen_pos: Vector2 = _world_to_screen(_unit_groups[i].pos)
			if screen_pos.distance_to(mb.position) <= GROUP_HIT_RADIUS:
				_selected_group_index = i
				break
	else:
		var from_pos: Vector2 = _world_to_screen(_unit_groups[_selected_group_index].pos)
		_arrows.append({from = from_pos, to = mb.position})
		_selected_group_index = -1

	queue_redraw()


func _draw() -> void:
	if _field_map == null:
		return
	_draw_grid()
	_draw_borders()
	_draw_objectives()
	_draw_unit_groups()
	_draw_arrows()


func _draw_grid() -> void:
	var font := ThemeDB.fallback_font
	var font_size := 14
	for i in range(GRID_DIVISIONS + 1):
		var x: float = size.x * i / float(GRID_DIVISIONS)
		var y: float = size.y * i / float(GRID_DIVISIONS)
		draw_line(Vector2(x, 0), Vector2(x, size.y), GRID_COLOR, 1.0)
		draw_line(Vector2(0, y), Vector2(size.x, y), GRID_COLOR, 1.0)
	for col in range(GRID_DIVISIONS):
		var letter := String.chr(65 + col)
		var cx: float = size.x * (col + 0.5) / float(GRID_DIVISIONS)
		draw_string(font, Vector2(cx - 4, 14), letter, HORIZONTAL_ALIGNMENT_LEFT, -1, font_size, GRID_COLOR)
	for row in range(GRID_DIVISIONS):
		var cy: float = size.y * (row + 0.5) / float(GRID_DIVISIONS)
		draw_string(font, Vector2(4, cy + 4), str(row + 1), HORIZONTAL_ALIGNMENT_LEFT, -1, font_size, GRID_COLOR)


func _draw_borders() -> void:
	for border in _field_map.borders:
		var pts: Array = border.points
		if pts.size() < 2:
			continue
		var screen_pts := PackedVector2Array()
		for p in pts:
			screen_pts.append(_world_to_screen(p))
		var color: Color = BORDER_COLORS.get(border.kind, Color.WHITE)
		# No flood-fill area data for water, only the coast polyline itself, so water is
		# rendered as a thicker line rather than a filled region — a schematic minimum.
		var width: float = 4.0 if border.kind == "coast" else 2.0
		draw_polyline(screen_pts, color, width)


func _draw_objectives() -> void:
	for node in _field_map.nodes:
		if node.type == "objective":
			var center: Vector2 = _world_to_screen(node.pos)
			draw_arc(center, 16.0, 0.0, TAU, 24, OBJECTIVE_COLOR, 2.0)


func _draw_unit_groups() -> void:
	for i in range(_unit_groups.size()):
		var group: Dictionary = _unit_groups[i]
		var pos: Vector2 = _world_to_screen(group.pos)
		var color: Color = FACTION_COLORS[group.faction]
		var chevron := PackedVector2Array([pos + Vector2(-10, 8), pos + Vector2(0, -10), pos + Vector2(10, 8)])
		draw_polyline(chevron, color, 3.0)
		if i == _selected_group_index:
			draw_arc(pos, 14.0, 0.0, TAU, 20, Color.WHITE, 1.5)


func _draw_arrows() -> void:
	for arrow in _arrows:
		var from: Vector2 = arrow.from
		var to: Vector2 = arrow.to
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
