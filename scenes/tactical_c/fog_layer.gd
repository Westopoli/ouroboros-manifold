extends Node2D
# See also: R-089-03 (outside sight is dimmed), R-089-04 (nothing remembered: discs are rebuilt from each frame).

const OUTSIDE_ALPHA := 0.55
const SHADER := """
shader_type canvas_item;
uniform sampler2D disc_tex : filter_nearest;
uniform int count = 0;
uniform float alpha = 0.55;
varying vec2 pos;
void vertex() { pos = VERTEX; }
void fragment() {
	float a = alpha;
	for (int i = 0; i < count; i++) {
		vec3 d = texelFetch(disc_tex, ivec2(i, 0), 0).rgb;
		vec2 q = pos - d.xy;
		if (dot(q, q) <= d.z * d.z) { a = 0.0; break; }
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


# One dim over the canvas, one hole per own unit (no cap, no outlines): the disc list rides in a one-row float texture.
func _push_uniforms() -> void:
	if _mat == null:
		return
	var n := _discs.size()
	var data := PackedFloat32Array()
	data.resize(maxi(n, 1) * 3)
	for i in n:
		var c: Vector2 = _discs[i]["center"]
		data[i * 3] = c.x
		data[i * 3 + 1] = c.y
		data[i * 3 + 2] = float(_discs[i]["radius"])
	var img := Image.create_from_data(maxi(n, 1), 1, false, Image.FORMAT_RGBF, data.to_byte_array())
	_mat.set_shader_parameter("disc_tex", ImageTexture.create_from_image(img))
	_mat.set_shader_parameter("count", n)
	_mat.set_shader_parameter("alpha", OUTSIDE_ALPHA)


func _draw() -> void:
	var vp := get_viewport()
	var size := vp.get_visible_rect().size if vp != null else Vector2(1920, 1080)
	draw_rect(Rect2(Vector2.ZERO, size), Color.WHITE)
