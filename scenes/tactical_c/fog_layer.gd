extends Node2D
# See also: R-089-03 (outside sight is dimmed), R-089-04 (nothing remembered: discs are rebuilt from each frame).

const OUTSIDE_ALPHA := 0.55
const SEGMENTS := 48  # DRAFT-sightdisc-segments
const CELL_WU := 100.0  # terrain cell size, as camera_rig_3d.gd CELL_WU
const SHADER := """
shader_type canvas_item;
uniform sampler2D mask_tex : filter_linear;
uniform float alpha = 0.55;
void fragment() {
	COLOR = vec4(0.0, 0.0, 0.0, alpha * (1.0 - texture(mask_tex, UV).r));
}
"""


# The sight mask: a black canvas with white where a sight polygon is, drawn into the SubViewport each frame.
class MaskDraw extends Node2D:
	var polys: Array = []
	var size := Vector2(1920, 1080)

	func _draw() -> void:
		draw_rect(Rect2(Vector2.ZERO, size), Color.BLACK)
		for p in polys:
			draw_colored_polygon(p, Color.WHITE)


var _discs: Array = []
var _mat: ShaderMaterial
var _projector := Callable()
var _terrain := {}
var _mask_vp: SubViewport
var _mask_draw: MaskDraw


func _ready() -> void:
	name = "FogLayer"
	var sh := Shader.new()
	sh.code = SHADER
	_mat = ShaderMaterial.new()
	_mat.shader = sh
	material = _mat
	_mask_vp = SubViewport.new()
	_mask_vp.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	_mask_draw = MaskDraw.new()
	_mask_vp.add_child(_mask_draw)
	add_child(_mask_vp)
	_mat.set_shader_parameter("mask_tex", _mask_vp.get_texture())
	_mat.set_shader_parameter("alpha", OUTSIDE_ALPHA)


# Two call shapes. Flat 2D: set_frame(frame, local_faction, world_scale, camera). Ground era (C10a):
# set_frame(frame, mission, local_faction) with set_projector(world wu -> screen px) set; each disc point is projected
# through the projector (ground height included), never a flat scale.
func set_projector(projector: Callable) -> void:
	_projector = projector


# The frame's terrain dict (bands, cells_w, cells_h): a ground-era disc stops at ground of a higher band than the unit's (R-005-09).
func set_terrain(terrain: Dictionary) -> void:
	_terrain = terrain


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
		var unit_band := _unit_band(w, int(u.get("layer", 1)))
		var pts := PackedVector2Array()
		var world := PackedVector2Array()
		for k in SEGMENTS:
			var dir := Vector2.from_angle(TAU * k / SEGMENTS)
			if flat:
				pts.append((w + dir * sight - camera) * world_scale + half)
			else:
				var wp := w + dir * _clipped_reach(w, dir, sight, unit_band)
				world.append(wp)
				pts.append(_projector.call(wp))
		_discs.append({"points": pts, "world": world})
	_push_mask()
	queue_redraw()


func screen_points() -> Array:
	var out := []
	for d in _discs:
		out.append(_centroid(d["points"]))
	return out


func sight_discs() -> Array:
	return _discs


func outside_alpha() -> float:
	return OUTSIDE_ALPHA


# Band of the terrain cell at world point w; 0 with no terrain, off the map, or a cell without a band.
func _band_at(w: Vector2) -> int:
	if _terrain.is_empty():
		return 0
	var cw := int(_terrain["cells_w"])
	var cx := int(floorf(w.x / CELL_WU))
	var cy := int(floorf(w.y / CELL_WU))
	if cx < 0 or cy < 0 or cx >= cw or cy >= int(_terrain["cells_h"]):
		return 0
	return int((_terrain["bands"] as PackedByteArray)[cy * cw + cx])


func _unit_band(w: Vector2, layer: int) -> int:
	var b := _band_at(w)
	return b if b > 0 else layer


# How far along dir from w the unit sees: walks cells outward and stops before the first one of a higher band (R-005-09).
func _clipped_reach(w: Vector2, dir: Vector2, sight: float, unit_band: int) -> float:
	if _terrain.is_empty():
		return sight
	var d := 0.0
	while d < sight:
		var nd := minf(d + CELL_WU, sight)
		if _band_at(w + dir * nd) > unit_band:
			break
		d = nd
	return d


func _centroid(p: PackedVector2Array) -> Vector2:
	var area := 0.0
	var c := Vector2.ZERO
	for k in p.size():
		var u := p[k]
		var v := p[(k + 1) % p.size()]
		var cr := u.x * v.y - v.x * u.y
		area += cr
		c += (u + v) * cr
	if absf(area) < 0.0001:
		return p[0] if p.size() > 0 else Vector2.ZERO
	return c / (3.0 * area)


# One dim over the canvas, one hole per sight polygon (no cap, no outlines): the polygons are drawn into the mask SubViewport.
func _push_mask() -> void:
	if _mat == null:
		return
	var vp := get_viewport()
	var size := vp.get_visible_rect().size if vp != null else Vector2(1920, 1080)
	_mask_vp.size = Vector2i(size)
	_mask_draw.size = size
	_mask_draw.polys = _discs.map(func(d: Dictionary) -> PackedVector2Array: return d["points"])
	_mask_draw.queue_redraw()


func _draw() -> void:
	var vp := get_viewport()
	var size := vp.get_visible_rect().size if vp != null else Vector2(1920, 1080)
	draw_rect(Rect2(Vector2.ZERO, size), Color.WHITE)
