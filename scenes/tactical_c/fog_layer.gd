extends Node2D
# See also: R-089-03 (outside sight is dimmed), R-089-04 (nothing remembered: discs are rebuilt from each frame).

const OUTSIDE_ALPHA := 0.55
const MAX_DISCS := 64
const SHADER := """
shader_type canvas_item;
uniform vec3 discs[64];
uniform int count = 0;
uniform float alpha = 0.55;
varying vec2 pos;
void vertex() { pos = VERTEX; }
void fragment() {
	float a = alpha;
	for (int i = 0; i < count; i++) {
		if (distance(pos, discs[i].xy) <= discs[i].z) { a = 0.0; }
	}
	COLOR = vec4(0.0, 0.0, 0.0, a);
}
"""

var _discs: Array = []
var _mat: ShaderMaterial


func _ready() -> void:
	name = "FogLayer"
	var sh := Shader.new()
	sh.code = SHADER
	_mat = ShaderMaterial.new()
	_mat.shader = sh
	material = _mat


func set_frame(frame: Dictionary, local_faction: int, world_scale: float, camera: Vector2) -> void:
	var half := Vector2(960, 540)
	var vp := get_viewport()
	if vp != null:
		half = vp.get_visible_rect().size * 0.5
	_discs.clear()
	for u in frame.get("units", []):
		if int(u.get("faction", -1)) != local_faction or not u.has("sight"):
			continue
		_discs.append({"center": (Vector2(float(u["x"]), float(u["y"])) - camera) * world_scale + half,
			"radius": float(u["sight"]) * world_scale})
	_push_uniforms()
	queue_redraw()


func sight_discs() -> Array:
	return _discs


func outside_alpha() -> float:
	return OUTSIDE_ALPHA


func _push_uniforms() -> void:
	if _mat == null:
		return
	var arr := PackedVector3Array()
	arr.resize(MAX_DISCS)
	var n := mini(_discs.size(), MAX_DISCS)
	for i in n:
		var c: Vector2 = _discs[i]["center"]
		arr[i] = Vector3(c.x, c.y, float(_discs[i]["radius"]))
	_mat.set_shader_parameter("discs", arr)
	_mat.set_shader_parameter("count", n)
	_mat.set_shader_parameter("alpha", OUTSIDE_ALPHA)


func _draw() -> void:
	var vp := get_viewport()
	var size := vp.get_visible_rect().size if vp != null else Vector2(1920, 1080)
	draw_rect(Rect2(Vector2.ZERO, size), Color.WHITE)
