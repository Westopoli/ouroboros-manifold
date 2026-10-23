extends Node2D

# One shape per unit type, faction fill, tier look, HP bar above, layer ring beneath (R-104-10, R-132-01, R-133).
# Shapes and colours are drafts; scale per type comes from the era manifest.

const MANIFEST := "res://assets/eras/settled_reach/manifest.json"
const TYPE_NAMES := ["raider", "interceptor", "vanguard", "warden", "bombard", "bastion"]
const SHAPE_RADIUS := 12.0
# draft: the manifest scale is for the 3D model (warden is 200.0); uncapped, one 2D body fills ~2400 px and 330 of them cost ~1.2 s a frame
const MAX_VISUAL_SCALE := 1.0
# draft: an HP bar shows only on a damaged or selected unit, so a full-health dense force shows shapes, not merged bars
const BAR_SIZE := Vector2(20.0, 3.0)
const OTHER_COLOR := Color(1.0, 0.3, 0.3)
const FALLBACK_OWN := Color(0.2, 0.6, 1.0)
const LAYER_TINTS := [Color(0.6, 0.45, 0.25), Color(0.4, 0.8, 0.4), Color(0.9, 0.85, 0.3), Color(0.8, 0.5, 1.0), Color(0.95, 0.95, 1.0)]
const SELECT_COLOR := Color(1.0, 1.0, 1.0)
# draft, unit-radius outlines: dart, arrow, kite, wide hexagon, long rectangle, square
const SHAPES := [
	[Vector2(1.0, 0.0), Vector2(-0.8, 0.7), Vector2(-0.4, 0.0), Vector2(-0.8, -0.7)],
	[Vector2(1.0, 0.0), Vector2(0.0, 0.5), Vector2(-1.0, 0.8), Vector2(-0.6, 0.0), Vector2(-1.0, -0.8), Vector2(0.0, -0.5)],
	[Vector2(1.0, 0.0), Vector2(0.0, 0.8), Vector2(-1.0, 0.0), Vector2(0.0, -0.8)],
	[Vector2(1.0, 0.0), Vector2(0.5, 0.9), Vector2(-0.5, 0.9), Vector2(-1.0, 0.0), Vector2(-0.5, -0.9), Vector2(0.5, -0.9)],
	[Vector2(1.0, 0.4), Vector2(-1.0, 0.4), Vector2(-1.0, -0.4), Vector2(1.0, -0.4)],
	[Vector2(0.8, 0.8), Vector2(-0.8, 0.8), Vector2(-0.8, -0.8), Vector2(0.8, -0.8)],
]

var _nodes: Dictionary = {}
var _types: Dictionary = {}
var _layers: Dictionary = {}
var _tiers: Dictionary = {}
var _facing: Dictionary = {}
var _hp: Dictionary = {}
var _bars: Dictionary = {}
var _fills: Dictionary = {}
var _rings: Dictionary = {}
var _layer_rings: Dictionary = {}
var _selected: Array = []
var _scale := 0.25
var _camera := Vector2.ZERO
var _vscale: Array = [1.0, 1.0, 1.0, 1.0, 1.0, 1.0]
var _offset: Array = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
var _own_color := FALLBACK_OWN
var _projector := Callable()


func _init() -> void:
	name = "UnitVisuals"
	var f := FileAccess.open(MANIFEST, FileAccess.READ)
	if f == null:
		return
	var m = JSON.parse_string(f.get_as_text())
	if not (m is Dictionary):
		return
	if m.has("era_accent_color"):
		_own_color = Color.html(str(m["era_accent_color"]))
	var units: Dictionary = m.get("units", {})
	for i in TYPE_NAMES.size():
		var e: Dictionary = units.get(TYPE_NAMES[i], {})
		_vscale[i] = minf(float(e.get("visual_scale", 1.0)), MAX_VISUAL_SCALE)
		_offset[i] = float(e.get("facing_offset_rad", 0.0))


func set_projector(projector: Callable) -> void:
	_projector = projector


func _to_screen(w: Vector2) -> Vector2:
	if _projector.is_valid():
		return _projector.call(w)
	return (w - _camera) * _scale + Vector2(960.0, 540.0)


func _shape(type: int) -> PackedVector2Array:
	var pts := PackedVector2Array()
	for p in SHAPES[posmod(type, SHAPES.size())]:
		pts.append(p * SHAPE_RADIUS)
	return pts


func _tint(layer: int) -> Color:
	return LAYER_TINTS[clampi(layer, 0, LAYER_TINTS.size() - 1)]


func _circle(r: float) -> PackedVector2Array:
	var pts := PackedVector2Array()
	for i in 24:
		pts.append(Vector2.from_angle(TAU * i / 24.0) * r)
	return pts


# R-133: tier 1 matte and seamed, tier 2 polished with a faint seam glow, tier 3 emissive.
func _tier_look(body: Polygon2D, edge: Line2D, tier: int) -> void:
	match clampi(tier, 1, 3):
		1:
			body.color = body.color.darkened(0.25)
			edge.default_color = edge.default_color.darkened(0.3)
		2:
			body.color = body.color.lightened(0.15)
		3:
			body.color = body.color.lightened(0.3)
			body.self_modulate = Color(1.6, 1.6, 1.6)
			edge.default_color = edge.default_color.lightened(0.5)
			edge.width = 3.0


func _make_node(u: Dictionary, own: bool) -> Node2D:
	var type := int(u.get("type", 0))
	var k: float = _vscale[clampi(type, 0, 5)]
	var node := Node2D.new()
	var body := Polygon2D.new()
	body.name = "Body"
	body.polygon = _shape(type)
	body.scale = Vector2(k, k)
	body.color = _own_color if own else OTHER_COLOR
	var edge := Line2D.new()
	edge.points = body.polygon
	edge.closed = true
	edge.width = 1.5
	edge.default_color = body.color.lightened(0.4)
	_tier_look(body, edge, int(u.get("tier", 1)))
	body.add_child(edge)
	node.add_child(body)
	_fills[int(u["id"])] = body
	var half := SHAPE_RADIUS * k
	var ring := Line2D.new()
	ring.name = "LayerRing"
	ring.points = _circle(SHAPE_RADIUS * 0.6 * k)
	ring.closed = true
	ring.width = 2.0
	ring.default_color = _tint(int(u.get("layer", 0)))
	ring.position = Vector2(0.0, half + 4.0)
	node.add_child(ring)
	_layer_rings[int(u["id"])] = ring
	var bar := Node2D.new()
	bar.name = "HpBar"
	bar.position = Vector2(0.0, -half - 6.0)
	var back := ColorRect.new()
	back.color = Color(0.1, 0.1, 0.1, 0.8)
	back.position = Vector2(-BAR_SIZE.x * 0.5, 0.0)
	back.size = BAR_SIZE
	bar.add_child(back)
	var fill := ColorRect.new()
	fill.name = "Fill"
	fill.color = Color(0.3, 0.9, 0.3)
	fill.position = back.position
	fill.size = BAR_SIZE
	bar.add_child(fill)
	node.add_child(bar)
	_bars[int(u["id"])] = bar
	return node


func _drop(id: int) -> void:
	if _nodes.has(id):
		_nodes[id].free()
	for d in [_nodes, _types, _layers, _tiers, _facing, _hp, _bars, _fills, _rings, _layer_rings]:
		d.erase(id)


func set_frame(frame: Dictionary, local_faction: int, world_scale: float, camera: Vector2) -> void:
	_scale = world_scale
	_camera = camera
	var seen := {}
	for v in frame.get("visible", {}).get(str(local_faction), []):
		seen[int(v)] = true
	var max_hp := {}
	for p in frame.get("profiles", []):
		max_hp[int(p.get("type", -1))] = float(p.get("max_hp", 1.0))
	var live := {}
	for u in frame.get("units", []):
		var id := int(u.get("id"))
		var own := int(u.get("faction", 0)) == local_faction
		if not (own or seen.has(id)):
			continue
		live[id] = true
		var type := int(u.get("type", 0))
		var layer := int(u.get("layer", 0))
		var tier := int(u.get("tier", 1))
		if _nodes.has(id) and (_types[id] != type or _layers[id] != layer or _tiers[id] != tier):
			_drop(id)
		if not _nodes.has(id):
			_nodes[id] = _make_node(u, own)
			_types[id] = type
			_layers[id] = layer
			_tiers[id] = tier
			add_child(_nodes[id])
		var fac := float(u.get("facing", 0.0))
		_facing[id] = fac
		_fills[id].rotation = fac + _offset[clampi(type, 0, 5)]
		var frac := clampf(float(u.get("hp", 0.0)) / maxf(float(max_hp.get(type, 1.0)), 0.001), 0.0, 1.0)
		_hp[id] = frac
		_bars[id].get_node("Fill").size.x = BAR_SIZE.x * frac
		_bars[id].visible = frac < 1.0 or _selected.has(id)
		_nodes[id].position = _to_screen(Vector2(float(u.get("x", 0.0)), float(u.get("y", 0.0))))
	for id in _nodes.keys().duplicate():
		if not live.has(id):
			_drop(id)
	set_selected(_selected)


func unit_node(id: int) -> Node2D:
	return _nodes.get(id)


func unit_polygon(id: int) -> PackedVector2Array:
	return _shape(_types[id]) if _types.has(id) else PackedVector2Array()


func unit_color(id: int) -> Color:
	if not _fills.has(id):
		return Color.TRANSPARENT
	var c: Color = _fills[id].color
	return c


func unit_facing(id: int) -> float:
	return _facing.get(id, 0.0)


func hp_bar(id: int) -> Node2D:
	return _bars.get(id)


func hp_fraction(id: int) -> float:
	return _hp.get(id, 0.0)


func layer_ring(id: int) -> Node2D:
	return _layer_rings.get(id)


func layer_ring_color(id: int) -> Color:
	return _tint(_layers[id]) if _layers.has(id) else Color.TRANSPARENT


func set_selected(ids: Array) -> void:
	_selected = ids.duplicate()
	for id in _bars:
		_bars[id].visible = _hp.get(id, 1.0) < 1.0 or _selected.has(id)
	for id in _rings.keys().duplicate():
		if not _selected.has(id) or not _nodes.has(id):
			_rings[id].free()
			_rings.erase(id)
	for id in _selected:
		if _nodes.has(id) and not _rings.has(id):
			var ring := Line2D.new()
			ring.points = _circle(SHAPE_RADIUS * _vscale[clampi(_types[id], 0, 5)] * 1.6)
			ring.closed = true
			ring.width = 2.0
			ring.default_color = SELECT_COLOR
			_nodes[id].add_child(ring)
			_rings[id] = ring


func selection_ring(id: int) -> Node2D:
	return _rings.get(id)
