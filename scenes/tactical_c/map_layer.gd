extends Node2D

# Objective rings, cover and obstacle discs, and the sight fog (S-234: one world, readable).

# provisional (draft): sight radius in world units until the frame carries "sight_radius"
const SIGHT_RADIUS_DRAFT := 600.0
const FOG_DIM_ALPHA := 0.45
const MAX_FOG_DISCS := 128
const OBJECTIVE_COLOR := Color(1.0, 0.85, 0.2, 0.9)
const COVER_COLOR := Color(0.3, 0.5, 0.3, 0.45)
const OBSTACLE_COLOR := Color(0.35, 0.3, 0.3, 0.8)
const SIGHT_COLOR := Color(1.0, 1.0, 1.0, 0.12)
const SCREEN := Vector2(1920.0, 1080.0)
const FOG_SHADER := """
shader_type canvas_item;
uniform vec3 discs[128];
uniform int disc_count = 0;
uniform float dim = 0.45;
varying vec2 pos;
void vertex() { pos = VERTEX; }
void fragment() {
	float inside = 0.0;
	for (int i = 0; i < 128; i++) {
		if (i >= disc_count) { break; }
		if (distance(pos, discs[i].xy) < discs[i].z) { inside = 1.0; }
	}
	COLOR = vec4(0.0, 0.0, 0.0, dim * (1.0 - inside));
}
"""

var _rings: Array = []
var _cover: Array = []
var _obstacles: Array = []
var _discs: Array = []
var _fog: Node2D


func _to_screen(w: Vector2, scale: float, camera: Vector2) -> Vector2:
	return (w - camera) * scale + SCREEN * 0.5


func _circle(c: Vector2, r: float) -> PackedVector2Array:
	var pts := PackedVector2Array()
	for i in 24:
		pts.append(c + Vector2.from_angle(TAU * i / 24.0) * r)
	return pts


func set_frame(frame: Dictionary, mission: Dictionary, local_faction: int, world_scale: float, camera: Vector2) -> void:
	_rings = []
	_cover = []
	_obstacles = []
	_discs = []
	var map: Dictionary = frame.get("map", {})
	if map.is_empty():
		if _fog != null:
			_fog.free()
			_fog = null
		queue_redraw()
		return
	var nodes: Array = map.get("nodes", [])
	for o in mission.get("objectives", []):
		var i := int(o.get("node", -1))
		if i >= 0 and i < nodes.size():
			var n: Dictionary = nodes[i]
			_rings.append({"center": _to_screen(Vector2(float(n.get("x", 0.0)), float(n.get("y", 0.0))), world_scale, camera),
				"radius": float(o.get("radius", 0.0)) * world_scale})
	for c in map.get("cover", []):
		_cover.append(_circle(_to_screen(Vector2(float(c.get("x", 0.0)), float(c.get("y", 0.0))), world_scale, camera), float(c.get("r", 0.0)) * world_scale))
	for c in map.get("obstacles", []):
		_obstacles.append(_circle(_to_screen(Vector2(float(c.get("x", 0.0)), float(c.get("y", 0.0))), world_scale, camera), float(c.get("r", 0.0)) * world_scale))
	var sight := float(frame.get("sight_radius", SIGHT_RADIUS_DRAFT)) * world_scale
	for u in frame.get("units", []):
		if int(u.get("faction", -1)) == local_faction:
			_discs.append({"center": _to_screen(Vector2(float(u.get("x", 0.0)), float(u.get("y", 0.0))), world_scale, camera), "radius": sight})
	_ensure_fog()
	_update_fog()
	queue_redraw()


func _ensure_fog() -> void:
	if _fog != null:
		return
	_fog = Node2D.new()
	_fog.name = "Fog"
	var sh := Shader.new()
	sh.code = FOG_SHADER
	var mat := ShaderMaterial.new()
	mat.shader = sh
	_fog.material = mat
	_fog.draw.connect(func(): _fog.draw_rect(Rect2(Vector2.ZERO, SCREEN), Color.WHITE))
	add_child(_fog)


func _update_fog() -> void:
	var arr := PackedVector3Array()
	for d in _discs.slice(0, MAX_FOG_DISCS):
		arr.append(Vector3(d["center"].x, d["center"].y, d["radius"]))
	var mat: ShaderMaterial = _fog.material
	mat.set_shader_parameter("discs", arr)
	mat.set_shader_parameter("disc_count", arr.size())
	mat.set_shader_parameter("dim", FOG_DIM_ALPHA)
	_fog.queue_redraw()


func _draw() -> void:
	for p in _cover:
		draw_colored_polygon(p, COVER_COLOR)
	for p in _obstacles:
		draw_colored_polygon(p, OBSTACLE_COLOR)
	for d in _discs:
		draw_arc(d["center"], d["radius"], 0.0, TAU, 48, SIGHT_COLOR, 2.0)
	for r in _rings:
		draw_arc(r["center"], r["radius"], 0.0, TAU, 64, OBJECTIVE_COLOR, 3.0)


func objective_rings() -> Array:
	return _rings


func cover_polygons() -> Array:
	return _cover


func obstacle_polygons() -> Array:
	return _obstacles


func fog_node() -> Node2D:
	return _fog


func fog_discs() -> Array:
	return _discs
