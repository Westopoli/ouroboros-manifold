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
var _projector := Callable()


func _ready() -> void:
	name = "FogLayer"
	var sh := Shader.new()
	sh.code = SHADER
	_mat = ShaderMaterial.new()
	_mat.shader = sh
	material = _mat


# Two call shapes. Flat 2D: set_frame(frame, local_faction, world_scale, camera). Ground era (C10a):
# set_frame(frame, mission, local_faction) with set_projector(world wu -> screen px) set; the disc radius is
# re-derived through the projector (mean of the x and y offsets), never a flat scale.
func set_projector(projector: Callable) -> void:
	_projector = projector


func set_frame(frame: Dictionary, a: Variant, b: Variant = null, c: Variant = null) -> void:
	var half := Vector2(960, 540)
	var vp := get_viewport()
	if vp != null:
		half = vp.get_visible_rect().size * 0.5
	var flat: bool = c is Vector2 or not _projector.is_valid()
	var local_faction := int(a) if flat else int(b)
	var world_scale := float(b) if flat else 1.0
	var camera: Vector2 = c if c is Vector2 else Vector2.ZERO
	_discs.clear()
	for u in frame.get("units", []):
		if int(u.get("faction", -1)) != local_faction or not u.has("sight"):
			continue
		var w := Vector2(float(u["x"]), float(u["y"]))
		var sight := float(u["sight"])
		if flat:
			_discs.append({"center": (w - camera) * world_scale + half, "radius": sight * world_scale})
		else:
			var ctr: Vector2 = _projector.call(w)
			var rx := ctr.distance_to(_projector.call(w + Vector2(sight, 0.0)))
			var ry := ctr.distance_to(_projector.call(w + Vector2(0.0, sight)))
			_discs.append({"center": ctr, "radius": (rx + ry) * 0.5})
	_push_uniforms()
	queue_redraw()


func screen_points() -> Array:
	var out := []
	for d in _discs:
		out.append(d["center"])
	return out


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
