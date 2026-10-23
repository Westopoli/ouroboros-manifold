extends Node2D
# See also: R-089-03 (outside sight is dimmed), R-089-04 (nothing remembered: discs are rebuilt from each frame).

const OUTSIDE_ALPHA := 0.55
const SEGMENTS := 48  # DRAFT-sightdisc-segments
const CLIP_EPS_WU := 0.5  # DRAFT-sightdisc-clip-eps: margin past the camera near plane
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
var _failed := 0  # mask rings Geometry2D.triangulate_polygon rejected this frame; such a ring would draw no hole
var _mat: ShaderMaterial
var _projector := Callable()
var _terrain := {}
var _rig: Node3D
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


# The camera rig of the ground era: its camera's near plane clips each disc in world space before projection.
func set_rig(rig: Node3D) -> void:
	_rig = rig


# Sutherland-Hodgman against one plane: the points with plane.distance_to(p) >= 0 stay, each crossing edge adds its intersection.
static func clip_to_plane(pts: PackedVector3Array, plane: Plane) -> PackedVector3Array:
	var out := PackedVector3Array()
	var n := pts.size()
	for k in n:
		var a := pts[k]
		var b := pts[(k + 1) % n]
		var a_in := plane.distance_to(a) >= 0.0
		var b_in := plane.distance_to(b) >= 0.0
		if a_in:
			out.append(a)
		if a_in != b_in:
			var hit: Variant = plane.intersects_segment(a, b)
			if hit != null:
				out.append(hit)
	return out


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
	_failed = 0
	var near_plane := Plane()
	var cam: Camera3D = _rig.get_camera() if _rig != null and not flat else null
	if cam != null:
		var forward := -cam.global_transform.basis.z
		near_plane = Plane(forward, cam.global_position + forward * (cam.near + CLIP_EPS_WU))
	for u in frame.get("units", []):
		if int(u.get("faction", -1)) != local_faction or not u.has("sight"):
			continue
		var w := Vector2(float(u["x"]), float(u["y"]))
		var sight := float(u["sight"])
		var unit_band := _unit_band(w, int(u.get("layer", 1)))
		var pts := PackedVector2Array()
		var world := PackedVector2Array()
		var ring := PackedVector3Array()
		for k in SEGMENTS:
			var dir := Vector2.from_angle(TAU * k / SEGMENTS)
			if flat:
				pts.append((w + dir * sight - camera) * world_scale + half)
			else:
				var wp := w + dir * _clipped_reach(w, dir, sight, unit_band)
				if cam == null:
					world.append(wp)
					pts.append(_projector.call(wp))
				else:
					ring.append(Vector3(wp.x, _rig.height_at(wp.x, wp.y), wp.y))
		if cam != null:
			for q in clip_to_plane(ring, near_plane):
				var wp := Vector2(q.x, q.z)
				world.append(wp)
				pts.append(_projector.call(wp))
			if pts.size() < 3:
				pts = PackedVector2Array()
				world = PackedVector2Array()
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


func sight_discs_failed() -> int:
	return _failed


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
	var rings: Array = []
	for d in _discs:
		var p: PackedVector2Array = d["points"]
		if p.size() < 3:
			continue
		if Geometry2D.triangulate_polygon(p).is_empty():
			_failed += 1
			continue
		rings.append(p)
	_mask_draw.polys = rings
	_mask_draw.queue_redraw()


func _draw() -> void:
	var vp := get_viewport()
	var size := vp.get_visible_rect().size if vp != null else Vector2(1920, 1080)
	draw_rect(Rect2(Vector2.ZERO, size), Color.WHITE)
