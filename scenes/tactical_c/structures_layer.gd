extends Node2D

const SCREEN_CENTER := Vector2(960.0, 540.0)
const OWN_COLOR := Color(0.2, 0.6, 1.0)
const ENEMY_COLOR := Color(1.0, 0.3, 0.3)
const NEUTRAL_COLOR := Color(0.8, 0.8, 0.8, 0.6)
const RING_RADIUS_PX := 24.0
const RING_WIDTH := 3.0
const BAR_SIZE := Vector2(48.0, 6.0)
const BAR_OFFSET := Vector2(-24.0, 30.0)
const CAP_MAX := 1000.0

var _local := 0
var _scale := 1.0
var _camera := Vector2.ZERO
var _data := {}
var _max_hp := {}
var _nodes := {}


func _ready() -> void:
	name = "StructuresLayer"


func set_frame(frame: Dictionary, local_faction: int, world_scale: float, camera: Vector2) -> void:
	_local = local_faction
	_scale = world_scale
	_camera = camera
	_data = {}
	for s in frame.get("structures", []):
		_data[int(s["id"])] = s.duplicate()
	_sync()


func apply_delta(delta: Dictionary) -> void:
	for ch in delta.get("structures_changed", []):
		var id := int(ch["id"])
		if _data.has(id):
			_data[id].merge(ch, true)
		else:
			_data[id] = ch.duplicate()
	for id in delta.get("structures_removed", []):
		_data.erase(int(id))
		_max_hp.erase(int(id))
	_sync()


func structure_node(id: int) -> Node2D:
	return _nodes.get(id)


func owner_color(id: int) -> Color:
	var o := int(_data.get(id, {}).get("owner", -1))
	if o < 0:
		return NEUTRAL_COLOR
	return OWN_COLOR if o == _local else ENEMY_COLOR


func hp_bar(id: int) -> Node:
	var n: Node2D = _nodes.get(id)
	return n.get_node_or_null("HpBar") if n else null


func _sync() -> void:
	for id in _nodes.keys():
		if not _data.has(id):
			_nodes[id].queue_free()
			_nodes.erase(id)
	for id in _data:
		var s: Dictionary = _data[id]
		var hp := float(s.get("hp", 0.0))
		_max_hp[id] = maxf(float(_max_hp.get(id, 0.0)), hp)
		var n: Node2D = _nodes.get(id)
		if n == null:
			n = _make_node()
			_nodes[id] = n
			add_child(n)
		n.position = (Vector2(float(s["x"]), float(s["y"])) - _camera) * _scale + SCREEN_CENTER
		n.set_meta("color", owner_color(id))
		n.set_meta("cap", clampf(float(s.get("cap", 0.0)) / CAP_MAX, 0.0, 1.0))
		n.queue_redraw()
		var bar: Node = n.get_node("HpBar")
		var frac := 0.0
		if _max_hp[id] > 0.0:
			frac = clampf(hp / _max_hp[id], 0.0, 1.0)
		bar.get_node("Fill").size.x = BAR_SIZE.x * frac


func _make_node() -> Node2D:
	var n := Node2D.new()
	n.draw.connect(_draw_ring.bind(n))
	var bar := Control.new()
	bar.name = "HpBar"
	bar.position = BAR_OFFSET
	bar.size = BAR_SIZE
	var back := ColorRect.new()
	back.name = "Back"
	back.color = Color(0.1, 0.1, 0.1, 0.8)
	back.size = BAR_SIZE
	bar.add_child(back)
	var fill := ColorRect.new()
	fill.name = "Fill"
	fill.color = Color(0.3, 0.9, 0.3)
	fill.size = BAR_SIZE
	bar.add_child(fill)
	n.add_child(bar)
	return n


func _draw_ring(n: Node2D) -> void:
	var col: Color = n.get_meta("color", NEUTRAL_COLOR)
	n.draw_arc(Vector2.ZERO, RING_RADIUS_PX, 0.0, TAU, 48, col, RING_WIDTH)
	var cap: float = n.get_meta("cap", 0.0)
	if cap > 0.0:
		n.draw_arc(Vector2.ZERO, RING_RADIUS_PX - 5.0, -PI / 2.0, -PI / 2.0 + TAU * cap, 48, Color(1, 1, 1, 0.9), RING_WIDTH)
