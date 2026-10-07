extends Node2D

# One flat polygon per unit type, a faction fill and a layer-coloured outline (R-104-10, S-234).
# The shapes are drafts: the walker prototype draws only a triangle, so the type table is new.

const SHAPE_RADIUS := 12.0
const OWN_COLOR := Color(0.2, 0.6, 1.0)
const OTHER_COLOR := Color(1.0, 0.3, 0.3)
const LAYER_TINTS := [Color(0.6, 0.45, 0.25), Color(0.4, 0.8, 0.4), Color(0.9, 0.85, 0.3), Color(0.8, 0.5, 1.0), Color(0.95, 0.95, 1.0)]
const SELECT_COLOR := Color(1.0, 1.0, 1.0)
const MARKER_COLOR := Color(0.3, 1.0, 0.5)
# provisional (draft): corner count per unit type 0..3, repeated for higher ids
const TYPE_CORNERS := [3, 4, 5, 6]

var _nodes: Dictionary = {}
var _types: Dictionary = {}
var _layers: Dictionary = {}
var _selected: Array = []
var _rings: Dictionary = {}
var _marker: Node2D
var _marker_world := Vector2.ZERO
var _scale := 0.25
var _camera := Vector2.ZERO


func _to_screen(w: Vector2) -> Vector2:
	return (w - _camera) * _scale + Vector2(960.0, 540.0)


func _shape(type: int) -> PackedVector2Array:
	var n: int = TYPE_CORNERS[posmod(type, TYPE_CORNERS.size())]
	var pts := PackedVector2Array()
	for i in n:
		pts.append(Vector2.from_angle(-PI / 2.0 + TAU * i / n) * SHAPE_RADIUS)
	return pts


func _tint(layer: int) -> Color:
	return LAYER_TINTS[clampi(layer, 0, LAYER_TINTS.size() - 1)]


func _circle(r: float) -> PackedVector2Array:
	var pts := PackedVector2Array()
	for i in 24:
		pts.append(Vector2.from_angle(TAU * i / 24.0) * r)
	return pts


func _make_node(u: Dictionary, own: bool) -> Node2D:
	var node := Node2D.new()
	var body := Polygon2D.new()
	body.polygon = _shape(int(u.get("type", 0)))
	body.color = OWN_COLOR if own else OTHER_COLOR
	node.add_child(body)
	var edge := Line2D.new()
	edge.points = body.polygon
	edge.closed = true
	edge.width = 2.0
	edge.default_color = _tint(int(u.get("layer", 0)))
	node.add_child(edge)
	return node


func set_frame(frame: Dictionary, local_faction: int, world_scale: float, camera: Vector2) -> void:
	_scale = world_scale
	_camera = camera
	var seen := {}
	for v in frame.get("visible", {}).get(str(local_faction), []):
		seen[int(v)] = true
	var live := {}
	for u in frame.get("units", []):
		var id := int(u.get("id"))
		var own := int(u.get("faction", 0)) == local_faction
		if not (own or seen.has(id)):
			continue
		live[id] = true
		var type := int(u.get("type", 0))
		var layer := int(u.get("layer", 0))
		if _nodes.has(id) and (_types[id] != type or _layers[id] != layer):
			_nodes[id].free()
			_nodes.erase(id)
		if not _nodes.has(id):
			_nodes[id] = _make_node(u, own)
			_types[id] = type
			_layers[id] = layer
			add_child(_nodes[id])
		_nodes[id].position = _to_screen(Vector2(float(u.get("x", 0.0)), float(u.get("y", 0.0))))
	for id in _nodes.keys().duplicate():
		if not live.has(id):
			_nodes[id].free()
			_nodes.erase(id)
			_rings.erase(id)
	set_selected(_selected)
	if _marker != null:
		_marker.position = _to_screen(_marker_world)


func unit_node(id: int) -> Node2D:
	return _nodes.get(id)


func unit_polygon(id: int) -> PackedVector2Array:
	return _shape(_types[id]) if _types.has(id) else PackedVector2Array()


func unit_tint(id: int) -> Color:
	return _tint(_layers[id]) if _layers.has(id) else Color.TRANSPARENT


func set_selected(ids: Array) -> void:
	_selected = ids.duplicate()
	for id in _rings.keys().duplicate():
		if not _selected.has(id) or not _nodes.has(id):
			_rings[id].free()
			_rings.erase(id)
	for id in _selected:
		if _nodes.has(id) and not _rings.has(id):
			var ring := Line2D.new()
			ring.points = _circle(SHAPE_RADIUS * 1.6)
			ring.closed = true
			ring.width = 2.0
			ring.default_color = SELECT_COLOR
			_nodes[id].add_child(ring)
			_rings[id] = ring


func selection_ring(id: int) -> Node2D:
	return _rings.get(id)


func set_move_marker(world: Vector2) -> void:
	_marker_world = world
	if _marker == null:
		_marker = Node2D.new()
		for d in [Vector2(1, 1), Vector2(1, -1)]:
			var bar := Line2D.new()
			bar.points = PackedVector2Array([-d * 8.0, d * 8.0])
			bar.width = 3.0
			bar.default_color = MARKER_COLOR
			_marker.add_child(bar)
		add_child(_marker)
	_marker.position = _to_screen(world)


func move_marker() -> Node2D:
	return _marker
