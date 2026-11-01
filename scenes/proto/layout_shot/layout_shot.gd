extends Node

## H-025 layout shot, round two: draws one catalogue layout (JSON path in OM_LAYOUT) on the Ground3D camera rig and Units3D bodies. The layout's landscape is
## geometry (docs/stories/H-025.md "Round two format" ruling 4): walls, boxes, buildings, discs, routes and tiers, each in its own colour with a label. A ground
## preset's layers are terrain tiers joined by slopes (R-001-06, R-001-07), so no stacked planes are drawn and `layers_visible` is false. The camera frames the
## bounding box of the units and features plus a 15% margin; the glyphs are scaled up (never the camera moved) until the smallest is DRAFT-glyph-min-px wide; every
## unit with a range draws it as a thin ring in its side's colour. With OM_SHOT_OUT set (a PNG file path) it saves the frame after 30 frames and quits.
## Drawing numbers below that the story does not give are named DRAFTs for the look; Westley rules. See also scripts/skilllab/catalogue/presets.toml, produce.py.

const Ground3DHost := preload("res://scenes/ground3d/ground3d.gd")
const GroundUnits := preload("res://scenes/ground3d/ground_units.gd")
const GroundPick := preload("res://scenes/ground3d/ground_pick.gd")
const UnitVisuals := preload("res://scenes/tactical_c/unit_visuals.gd")

const SCENE_PATH := "res://scenes/proto/layout_shot/layout_shot.tscn"
const PRESETS_PATH := "res://scripts/skilllab/catalogue/presets.toml"
const ROLES := ["Raider", "Interceptor", "Vanguard", "Warden", "Bombard", "Bastion"]  # scripts/skilllab/engine.py:16; index = unit type id
const CELL_WU := 100.0
const SHOT_FRAMES := 30
const SIDE_COLOURS := {"A": Color(0.2, 0.6, 1.0), "B": Color(1.0, 0.3, 0.3)}
const GLYPH_MIN_PX := 14.0  # DRAFT-glyph-min-px (story)
const GLYPH_MARGIN := 1.1  # DRAFT-shot-glyph-margin: glyphs are scaled to 1.1 x the minimum so pixel rounding never lands under it
const CAMERA_MARGIN := 0.15  # story: 15% of the box's larger extent on each side
const BAND_HEIGHT_WU := 120.0  # DRAFT-shot-band-height-wu: drawn height of one tier, a drawing number only (was 60; a vantage rise read as a flat overlay)
const GLYPH_LIFT_WU := 8.0  # DRAFT-shot-glyph-lift-wu: the glyphs float above every translucent overlay so a tint never washes a side colour
const DEST_RADIUS_WU := 90.0  # DRAFT-shot-dest-radius-wu: the transit destination marker
const DEST_COLOUR := Color(1.0, 1.0, 1.0)
const RAMP_WU := 200.0  # DRAFT-shot-ramp-wu: the slope that joins a vantage rise to the ground
const LIFT_WU := 4.0  # DRAFT-shot-lift-wu: overlays float this far over the ground mesh so they do not z-fight
const WALL_HEIGHT_WU := 80.0  # DRAFT-shot-wall-height-wu
const BOX_HEIGHT_WU := 40.0  # DRAFT-shot-box-height-wu
const BUILDING_HEIGHT_WU := 120.0  # DRAFT-shot-building-height-wu
const RING_SEGMENTS := 48  # DRAFT-shot-ring-segments
const ROUTE_WIDTH_WU := 40.0  # DRAFT-shot-route-width-wu
const FOV_MIN_DEG := 8.0  # DRAFT-shot-fov-min-deg: the narrowest lens the fit may use
const FOV_ITERATIONS := 10  # DRAFT-shot-fov-iterations
const LEGEND_FONT := 20
const LABEL_FONT := 26
const DISC_KINDS := ["vantage", "objective", "hazard_anchor", "city"]  # kinds whose `radius` is a drawn disc (a chokepoint's radius is covered by its walls)
const FEATURE_COLOURS := {
	"chokepoint": Color(0.95, 0.75, 0.2), "vantage": Color(0.95, 0.55, 0.15), "cover": Color(0.75, 0.55, 0.35), "objective": Color(1.0, 0.95, 0.2),
	"staging": Color(0.9, 0.9, 0.9), "transit": Color(0.3, 0.9, 0.95), "flank_route": Color(0.95, 0.3, 0.95), "hazard_anchor": Color(0.75, 0.45, 0.9),
	"slope": Color(0.95, 0.55, 0.15), "city": Color(0.7, 0.7, 0.75), "trap": Color(0.85, 0.35, 0.15)}
const TIER_COLOURS := [Color(0, 0, 0, 0), Color(1.0, 0.85, 0.3, 0.35), Color(0.4, 0.9, 0.9, 0.35)]
const LEGEND_LIGHTEN := 0.8  # DRAFT-shot-legend-lighten: a feature's legend line is its colour mixed this far to white, so it reads on the dark panel
const RAMP_COLOUR := Color(0.85, 0.4, 0.1, 0.45)  # DRAFT-shot-ramp-colour: the slope between two tiers

var _layout: Dictionary = {}
var _terrain: Dictionary = {}
var _units: Array = []
var _legend: Array = []
var _ranges: Array = []
var _features: Array = []
var _rings: Dictionary = {}
var _legend_lines: Array = []
var _glyph_px := 0.0
var _bbox: Array = [0.0, 0.0, 0.0, 0.0]
var _frames := 0
var _shot_path := ""
var _saving := false


func _ready() -> void:
	_shot_path = OS.get_environment("OM_SHOT_OUT")
	var path := OS.get_environment("OM_LAYOUT")
	var parsed = JSON.parse_string(FileAccess.get_file_as_string(path)) if path != "" else null
	if not parsed is Dictionary:
		push_error("layout_shot: OM_LAYOUT %r is not a layout JSON" % path)
		return
	_layout = parsed
	var preset := _preset(String(_layout["landscape"]))
	var layers := int(preset["layers"])
	var floors: Array = []
	for k in layers:
		floors.append(k * BAND_HEIGHT_WU)
	var raw = _layout.get("features", [])
	_features = raw if raw is Array else []
	_terrain = _tiered_terrain(int(preset["width"]), int(preset["height"]), floors)
	var ground := Ground3DHost.new()
	add_child(ground)
	ground.set_terrain(_terrain)
	var units3d := GroundUnits.new()
	units3d.local_faction = 0
	ground.add_layer(units3d)
	var scene3d := Node3D.new()
	ground.add_layer(scene3d)
	var frame_units := _collect_units()
	units3d.set_units(frame_units, _terrain, floors, [])
	for u in frame_units:
		units3d.unit_node(int(u["id"])).position.y += GLYPH_LIFT_WU
	_add_tier_tint(scene3d)
	for f in _features:
		_add_feature(scene3d, f)
	_add_unit_rings(scene3d)
	var panel := _add_legend()
	_frame_camera(ground, panel)
	_scale_glyphs(ground, units3d)
	_add_feature_labels(ground)


# ---------------------------------------------------------------- terrain: tiers joined by slopes

func _preset(name: String) -> Dictionary:
	var out := {}
	var section := ""
	for line in FileAccess.get_file_as_string(PRESETS_PATH).split("\n"):
		var s := line.strip_edges()
		if s.begins_with("["):
			section = s.trim_prefix("[").trim_suffix("]")
		elif section == name and "=" in s and not s.begins_with("#"):
			out[s.get_slice("=", 0).strip_edges()] = int(s.get_slice("=", 1).strip_edges())
	return out


## The tier fraction (0 to 1, times the feature's band step) a vantage rise or a slope gives the point (x, y); the largest of the features.
func _tier_at(x: float, y: float) -> float:
	var best := 0.0
	for f in _features:
		var cx := float(f["x"])
		var cy := float(f["y"])
		if f["kind"] == "vantage":
			var d := Vector2(x - cx, y - cy).length()
			best = maxf(best, float(f["height_band"]) * clampf((float(f["radius"]) + RAMP_WU - d) / RAMP_WU, 0.0, 1.0))
		elif f.has("ridge"):  # a flank_route's ridge: the rectangle is the plateau, a ramp of RAMP_WU runs down from its edge
			var r: Dictionary = f["ridge"]
			var out := Vector2(maxf(absf(x - float(r["x"])) - float(r["w"]) * 0.5, 0.0), maxf(absf(y - float(r["y"])) - float(r["h"]) * 0.5, 0.0))
			best = maxf(best, float(f.get("height_band", 1)) * clampf((RAMP_WU - out.length()) / RAMP_WU, 0.0, 1.0))
		elif f["kind"] == "slope":
			var heading := float(f["heading"])
			var s := (x - cx) * cos(heading) + (y - cy) * sin(heading)
			var t := clampf(0.5 + s / float(f["length"]), 0.0, 1.0)
			best = maxf(best, float(f["from_band"]) + (float(f["to_band"]) - float(f["from_band"])) * t)
	return best


func _tiered_terrain(width: int, height: int, floors: Array) -> Dictionary:
	var w := int(ceil(width / CELL_WU))
	var h := int(ceil(height / CELL_WU))
	var heights := PackedInt32Array()
	heights.resize(w * h)
	var bands := PackedByteArray()
	bands.resize(w * h)
	var walk := PackedByteArray()
	walk.resize(w * h)
	walk.fill(1)
	for j in h:
		for i in w:
			var t := _tier_at((i + 0.5) * CELL_WU, (j + 0.5) * CELL_WU)
			heights[j * w + i] = int(round(t * BAND_HEIGHT_WU * 100.0))
			bands[j * w + i] = int(round(t)) + 1
	return {"cells_w": w, "cells_h": h, "heights": heights, "bands": bands, "walkable": walk, "layer_floors_wu": floors, "flyer_types": []}


## A translucent tint over the raised ground: a full tier in its band colour, the slope that joins it in RAMP_COLOUR, so a tier reads as a stepped rise.
func _add_tier_tint(parent: Node3D) -> void:
	var w := int(_terrain["cells_w"])
	var h := int(_terrain["cells_h"])
	var heights: PackedInt32Array = _terrain["heights"]
	var step := BAND_HEIGHT_WU * 100.0
	var by_class := {}
	for j in h - 1:
		for i in w - 1:
			var low := mini(mini(heights[j * w + i], heights[j * w + i + 1]), mini(heights[(j + 1) * w + i], heights[(j + 1) * w + i + 1]))
			var frac := low / step
			if frac <= 0.02:
				continue
			var cls := int(floor(frac + 0.02))  # 0 = a slope, 1 and up = a full tier
			if not by_class.has(cls):
				by_class[cls] = SurfaceTool.new()
				by_class[cls].begin(Mesh.PRIMITIVE_TRIANGLES)
			var st: SurfaceTool = by_class[cls]
			var p := [Vector2i(i, j), Vector2i(i + 1, j), Vector2i(i + 1, j + 1), Vector2i(i, j), Vector2i(i + 1, j + 1), Vector2i(i, j + 1)]
			for c: Vector2i in p:
				var x: float = (c.x + 0.5) * CELL_WU
				var y: float = (c.y + 0.5) * CELL_WU
				st.add_vertex(Vector3(x, GroundPick.height_at(_terrain, x, y) + LIFT_WU, y))
	for cls in by_class:
		var mi := MeshInstance3D.new()
		mi.mesh = (by_class[cls] as SurfaceTool).commit()
		mi.material_override = _unshaded(RAMP_COLOUR if cls == 0 else TIER_COLOURS[mini(cls, TIER_COLOURS.size() - 1)])
		parent.add_child(mi)


# ---------------------------------------------------------------- units

func _collect_units() -> Array:
	var out: Array = []
	var id := 0
	var seen := {}
	var ranges := {}
	for side in ["A", "B"]:
		for row in _layout["side_" + side.to_lower()]["units"]:
			var role := String(row["role"])
			var rng := float(row.get("range", 0.0))
			out.append({"id": id, "faction": 0 if side == "A" else 1, "type": maxi(ROLES.find(role), 0), "x": float(row["x"]), "y": float(row["y"]),
					"facing": float(row["facing"]), "layer": int(row["layer"])})
			_units.append({"id": id, "side": side, "role": role, "layer": int(row["layer"]), "x": float(row["x"]), "y": float(row["y"]),
					"facing": float(row["facing"]), "range": rng})
			seen[role] = true
			ranges[role] = rng
			id += 1
	for r in ROLES:
		if seen.has(r):
			_legend.append(r)
			_ranges.append({"role": r, "range": ranges[r]})
	return out


func _px_ratio() -> float:
	var h := float(get_window().size.y)
	return h / Ground3DHost.SCREEN_SIZE.y if h > 0.0 else 1.0


## The drawn width in window pixels of a glyph of radius BODY_RADIUS_WU * k at the world point (x, y).
func _glyph_width_px(ground: Node, x: float, y: float, k: float) -> float:
	var r := GroundUnits.BODY_RADIUS_WU * k
	return ground.to_screen(x - r, y).distance_to(ground.to_screen(x + r, y)) * _px_ratio()


func _scale_glyphs(ground: Node, units3d: Node3D) -> void:
	var smallest := INF
	for u in _units:
		smallest = minf(smallest, _glyph_width_px(ground, u["x"], u["y"], 1.0))
	var k := maxf(1.0, GLYPH_MIN_PX * GLYPH_MARGIN / smallest) if smallest > 0.0 else 1.0
	for u in _units:
		units3d.unit_node(int(u["id"])).scale = Vector3.ONE * k
	_glyph_px = INF
	for u in _units:
		_glyph_px = minf(_glyph_px, _glyph_width_px(ground, u["x"], u["y"], k))


func _add_unit_rings(parent: Node3D) -> void:
	for u in _units:
		var rng: float = u["range"]
		if rng <= 0.0:
			continue
		var c: Color = SIDE_COLOURS[u["side"]]
		var ring := _ring(Vector2(u["x"], u["y"]), rng, Color(c.r, c.g, c.b, 0.55))
		parent.add_child(ring)
		_rings[int(u["id"])] = ring


# ---------------------------------------------------------------- features

func _unshaded(colour: Color) -> StandardMaterial3D:
	var mat := StandardMaterial3D.new()
	mat.albedo_color = colour
	mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	mat.cull_mode = BaseMaterial3D.CULL_DISABLED
	if colour.a < 1.0:
		mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	return mat


func _at(x: float, y: float, lift: float) -> Vector3:
	return Vector3(x, GroundPick.height_at(_terrain, x, y) + lift, y)


func _line(points: PackedVector3Array, colour: Color) -> MeshInstance3D:
	var im := ImmediateMesh.new()
	im.surface_begin(Mesh.PRIMITIVE_LINE_STRIP)
	for p in points:
		im.surface_add_vertex(p)
	im.surface_end()
	var mi := MeshInstance3D.new()
	mi.mesh = im
	mi.material_override = _unshaded(colour)
	return mi


func _ring(centre: Vector2, radius: float, colour: Color) -> MeshInstance3D:
	var pts := PackedVector3Array()
	for k in RING_SEGMENTS + 1:
		var a := TAU * k / RING_SEGMENTS
		pts.append(_at(centre.x + radius * cos(a), centre.y + radius * sin(a), LIFT_WU))
	return _line(pts, colour)


func _rect_outline(r: Dictionary, grow: float, colour: Color) -> MeshInstance3D:
	var hw := float(r["w"]) * 0.5 + grow
	var hh := float(r["h"]) * 0.5 + grow
	var cx := float(r["x"])
	var cy := float(r["y"])
	var pts := PackedVector3Array()
	for c in [Vector2(-hw, -hh), Vector2(hw, -hh), Vector2(hw, hh), Vector2(-hw, hh), Vector2(-hw, -hh)]:
		pts.append(_at(cx + c.x, cy + c.y, LIFT_WU))
	return _line(pts, colour)


func _box(parent: Node3D, r: Dictionary, height: float, colour: Color) -> void:
	var mesh := BoxMesh.new()
	mesh.size = Vector3(float(r["w"]), height, float(r["h"]))
	var mi := MeshInstance3D.new()
	mi.mesh = mesh
	var mat := StandardMaterial3D.new()
	mat.albedo_color = colour
	mi.material_override = mat
	var base := _at(float(r["x"]), float(r["y"]), 0.0)
	mi.position = base + Vector3(0.0, height * 0.5, 0.0)
	parent.add_child(mi)


func _disc(parent: Node3D, centre: Vector2, radius: float, colour: Color) -> void:
	var mesh := CylinderMesh.new()
	mesh.top_radius = radius
	mesh.bottom_radius = radius
	mesh.height = 1.0
	mesh.radial_segments = 64
	var mi := MeshInstance3D.new()
	mi.mesh = mesh
	mi.material_override = _unshaded(Color(colour.r, colour.g, colour.b, 0.28))
	mi.position = _at(centre.x, centre.y, LIFT_WU * 0.5)
	parent.add_child(mi)
	parent.add_child(_ring(centre, radius, colour))


## A ribbon along a polyline, ROUTE_WIDTH_WU wide, lying on the ground.
func _route(parent: Node3D, points: Array, colour: Color) -> void:
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	for k in points.size() - 1:
		var a := Vector2(points[k][0], points[k][1])
		var b := Vector2(points[k + 1][0], points[k + 1][1])
		var side := (b - a).normalized().orthogonal() * ROUTE_WIDTH_WU * 0.5
		var q := [a - side, a + side, b + side, a - side, b + side, b - side]
		for p in q:
			st.add_vertex(_at(p.x, p.y, LIFT_WU * 1.5))
	var mi := MeshInstance3D.new()
	mi.mesh = st.commit()
	mi.material_override = _unshaded(colour)
	parent.add_child(mi)


## The transit destination: a filled white disc and ring, distinct from the route's colour.
func _marker(parent: Node3D, at: Vector2) -> void:
	_disc(parent, at, DEST_RADIUS_WU, DEST_COLOUR)


func _add_feature(parent: Node3D, f: Dictionary) -> void:
	var kind := String(f["kind"])
	var colour: Color = FEATURE_COLOURS.get(kind, Color.WHITE)
	var centre := Vector2(float(f["x"]), float(f["y"]))
	match kind:
		"chokepoint", "trap":
			for r in f["walls"]:
				_box(parent, r, WALL_HEIGHT_WU, colour)
		"cover":
			for r in f["boxes"]:
				_box(parent, r, BOX_HEIGHT_WU, colour)
		"city":
			for r in f["buildings"]:
				_box(parent, r, BUILDING_HEIGHT_WU, colour)
			_disc(parent, centre, float(f["radius"]), colour)
		"vantage":  # the raised tier itself is the fill (terrain heights and the tier tint); its top edge and the foot of its slope are outlined
			parent.add_child(_ring(centre, float(f["radius"]), colour))
			parent.add_child(_ring(centre, float(f["radius"]) + RAMP_WU, RAMP_COLOUR))
		"objective", "hazard_anchor":
			_disc(parent, centre, float(f["radius"]), colour)
		"staging":
			var half := float(f["size"]) * 0.5
			var pts := PackedVector3Array()
			for c in [Vector2(-half, -half), Vector2(half, -half), Vector2(half, half), Vector2(-half, half), Vector2(-half, -half)]:
				pts.append(_at(centre.x + c.x, centre.y + c.y, LIFT_WU))
			parent.add_child(_line(pts, colour))
			_route(parent, [[centre.x - half, centre.y - half], [centre.x + half, centre.y - half], [centre.x + half, centre.y + half],
					[centre.x - half, centre.y + half], [centre.x - half, centre.y - half]], Color(colour.r, colour.g, colour.b, 0.6))
		"transit":
			_route(parent, f["points"], colour)
			_marker(parent, Vector2(float(f["dest"]["x"]), float(f["dest"]["y"])))
		"flank_route":
			_route(parent, f["points"], colour)
			var r: Dictionary = f["ridge"]  # the raised tier itself is the fill; its top edge and the foot of its slope are outlined
			parent.add_child(_rect_outline(r, 0.0, colour))
			parent.add_child(_rect_outline(r, RAMP_WU, RAMP_COLOUR))
		"slope":
			_slope_strip(parent, f, colour)


func _slope_strip(parent: Node3D, f: Dictionary, colour: Color) -> void:
	var heading := float(f["heading"])
	var dir := Vector2(cos(heading), sin(heading))
	var side := dir.orthogonal() * float(f["width"]) * 0.5
	var centre := Vector2(float(f["x"]), float(f["y"]))
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	var steps := 12
	for k in steps:
		var a := centre + dir * float(f["length"]) * (float(k) / steps - 0.5)
		var b := centre + dir * float(f["length"]) * (float(k + 1) / steps - 0.5)
		for p in [a - side, a + side, b + side, a - side, b + side, b - side]:
			st.add_vertex(_at(p.x, p.y, LIFT_WU * 1.5))
	var mi := MeshInstance3D.new()
	mi.mesh = st.commit()
	mi.material_override = _unshaded(Color(colour.r, colour.g, colour.b, 0.75))
	parent.add_child(mi)


## The world points that bound a feature: rectangles, drawn discs, the staging square, route points, the slope band.
func _feature_points(f: Dictionary) -> Array:
	var kind := String(f["kind"])
	var c := Vector2(float(f["x"]), float(f["y"]))
	var pts: Array = []
	for key in ["walls", "boxes", "buildings"]:
		for r in f.get(key, []):
			var hw := float(r["w"]) * 0.5
			var hh := float(r["h"]) * 0.5
			for s in [Vector2(-hw, -hh), Vector2(hw, -hh), Vector2(hw, hh), Vector2(-hw, hh)]:
				pts.append(Vector2(float(r["x"]), float(r["y"])) + s)
	if kind in DISC_KINDS:
		var rad := float(f["radius"])
		for s in [Vector2(-rad, -rad), Vector2(rad, -rad), Vector2(rad, rad), Vector2(-rad, rad)]:
			pts.append(c + s)
	if kind == "staging":
		var half := float(f["size"]) * 0.5
		for s in [Vector2(-half, -half), Vector2(half, -half), Vector2(half, half), Vector2(-half, half)]:
			pts.append(c + s)
	for p in f.get("points", []):
		pts.append(Vector2(p[0], p[1]))
	if f.has("ridge"):
		var rr: Dictionary = f["ridge"]
		for s in [Vector2(-1, -1), Vector2(1, -1), Vector2(1, 1), Vector2(-1, 1)]:
			pts.append(Vector2(float(rr["x"]) + s.x * float(rr["w"]) * 0.5, float(rr["y"]) + s.y * float(rr["h"]) * 0.5))
	if kind == "slope":
		var dir := Vector2(cos(float(f["heading"])), sin(float(f["heading"])))
		for a in [-0.5, 0.5]:
			for b in [-0.5, 0.5]:
				pts.append(c + dir * float(f["length"]) * a + dir.orthogonal() * float(f["width"]) * b)
	if pts.is_empty():
		pts.append(c)
	return pts


# ---------------------------------------------------------------- camera

## Frame the box of all units and features plus CAMERA_MARGIN, backing the camera off until every corner is on screen right of the legend.
func _frame_camera(ground: Node, panel: Control) -> void:
	var lo := Vector2(INF, INF)
	var hi := Vector2(-INF, -INF)
	var pts: Array = []
	for u in _units:
		pts.append(Vector2(u["x"], u["y"]))
	for f in _features:
		pts.append_array(_feature_points(f))
	for p in pts:
		lo = Vector2(minf(lo.x, p.x), minf(lo.y, p.y))
		hi = Vector2(maxf(hi.x, p.x), maxf(hi.y, p.y))
	_bbox = [lo.x, lo.y, hi.x, hi.y]
	var m := CAMERA_MARGIN * maxf(hi.x - lo.x, hi.y - lo.y)
	var box_lo := lo - Vector2(m, m)
	var box_hi := hi + Vector2(m, m)
	var corners := [box_lo, Vector2(box_hi.x, box_lo.y), box_hi, Vector2(box_lo.x, box_hi.y)]
	var centre := (box_lo + box_hi) * 0.5
	var screen := Ground3DHost.SCREEN_SIZE
	var left := panel.position.x + panel.get_combined_minimum_size().x + 24.0
	var rect := Rect2(left, 24.0, screen.x - left - 24.0, screen.y - 48.0)
	var rig: Node3D = ground.camera_rig()
	var cam: Camera3D = rig.get_camera()
	rig.pan_to(centre)
	rig.zoom_by(-1000)
	while not _box_fits(ground, rig, corners, centre, rect) and rig.camera_height() < rig.ZOOM_MAX_MIN:
		rig.zoom_by(1)
	# The rig's height moves in whole steps; narrow the lens in between so the box fills the free rectangle (DRAFT-shot-fov-iterations).
	var wide := cam.fov
	var narrow := FOV_MIN_DEG
	for _i in FOV_ITERATIONS:
		cam.fov = (wide + narrow) * 0.5
		if _box_fits(ground, rig, corners, centre, rect):
			wide = cam.fov
		else:
			narrow = cam.fov
	cam.fov = wide
	_box_fits(ground, rig, corners, centre, rect)


## Pan so the box's centre sits in the middle of the free rectangle, then say whether every corner is inside it.
func _box_fits(ground: Node, rig: Node3D, corners: Array, centre: Vector2, rect: Rect2) -> bool:
	var sin_pitch := sin(deg_to_rad(rig.PITCH_LOW_DEG))
	var pan := centre
	rig.pan_to(pan)
	for _pass in 3:
		var d: Vector2 = rect.get_center() - ground.to_screen(centre.x, centre.y)
		var s: float = rig.qa_camera()["scale"]
		pan -= Vector2(d.x / s, d.y / (s * sin_pitch))
		rig.pan_to(pan)
	for c in corners:
		if not rect.has_point(ground.to_screen(c.x, c.y)):
			return false
	return true


# ---------------------------------------------------------------- legend and labels

func _add_legend() -> Control:
	var layer := CanvasLayer.new()
	add_child(layer)
	var panel := PanelContainer.new()
	panel.position = Vector2(24.0, 24.0)
	layer.add_child(panel)
	var box := VBoxContainer.new()
	panel.add_child(box)
	var head := [
		"%s  %s  %s" % [_layout["id"], _layout["situation"], _layout["landscape"]],
		"A %d : B %d   defender: %s" % [_layout["side_a"]["headcount"], _layout["side_b"]["headcount"], String(_layout.get("defender", "")) if String(_layout.get("defender", "")) != "" else "none"],
		"predict: %s" % _layout["predict"]]
	for line in head:
		_legend_lines.append(line)
		box.add_child(_label(line, Color.WHITE, LEGEND_FONT))
	box.add_child(_label("A (blue)", SIDE_COLOURS["A"], LEGEND_FONT))
	box.add_child(_label("B (red)", SIDE_COLOURS["B"], LEGEND_FONT))
	for f in _features:
		var line := "feature: %s" % f["kind"]
		_legend_lines.append(line)
		box.add_child(_label(line, Color(FEATURE_COLOURS.get(String(f["kind"]), Color.WHITE)).lerp(Color.WHITE, LEGEND_LIGHTEN), LEGEND_FONT))
	for r in _ranges:
		var role := String(r["role"])
		var text := "%s: range %d wu" % [role, int(round(float(r["range"])))] if float(r["range"]) > 0.0 else "%s: no range" % role
		_legend_lines.append(text)
		var row := HBoxContainer.new()
		var icon := Control.new()
		icon.custom_minimum_size = Vector2(32.0, 28.0)
		var poly := Polygon2D.new()
		var pts := PackedVector2Array()
		for p in UnitVisuals.SHAPES[ROLES.find(role)]:
			pts.append(p * 12.0)
		poly.polygon = pts
		poly.position = Vector2(16.0, 14.0)
		icon.add_child(poly)
		row.add_child(icon)
		row.add_child(_label(text, Color.WHITE, LEGEND_FONT))
		box.add_child(row)
	return panel


func _add_feature_labels(ground: Node) -> void:
	var layer := CanvasLayer.new()
	add_child(layer)
	for f in _features:
		var anchor := Vector2(float(f["x"]), float(f["y"]))
		var pts: Array = f.get("points", [])
		if pts.size() >= 2:  # a route starts under a side's block, so its label sits mid-way along the first leg
			anchor = (Vector2(pts[0][0], pts[0][1]) + Vector2(pts[1][0], pts[1][1])) * 0.5
		_add_label_at(layer, ground, anchor, String(f["kind"]).replace("_", " ").to_upper())
		if f.has("dest"):
			_add_label_at(layer, ground, Vector2(float(f["dest"]["x"]), float(f["dest"]["y"])), "DESTINATION")


func _add_label_at(layer: CanvasLayer, ground: Node, world: Vector2, text: String) -> void:
	var l := _label(text, Color.WHITE, LABEL_FONT)
	l.add_theme_color_override("font_outline_color", Color.BLACK)
	l.add_theme_constant_override("outline_size", 8)
	l.position = ground.to_screen(world.x, world.y) + Vector2(-60.0, -70.0)
	layer.add_child(l)


func _label(text: String, colour: Color, size: int) -> Label:
	var l := Label.new()
	l.text = text
	l.add_theme_font_size_override("font_size", size)
	l.add_theme_color_override("font_color", colour)
	return l


func _process(_delta: float) -> void:
	if _shot_path == "" or _saving:
		return
	_frames += 1
	if _frames >= SHOT_FRAMES:
		_saving = true
		_save_shot()


func _save_shot() -> void:
	await RenderingServer.frame_post_draw
	var err := get_viewport().get_texture().get_image().save_png(_shot_path)
	if err != OK:
		push_error("layout_shot: save_png %s failed (%d)" % [_shot_path, err])
	get_tree().quit()


func qa_state() -> Dictionary:
	var shown := 0
	var ranged := 0
	for u in _units:
		if float(u["range"]) > 0.0:
			ranged += 1
			if _rings.has(int(u["id"])) and _rings[int(u["id"])].visible:
				shown += 1
	var feats: Array = []
	for f in _features:
		feats.append({"kind": f["kind"], "x": f["x"], "y": f["y"]})
	# layers_visible: false on every ground preset, no planes are drawn (R-001-07); the key stays for a future space preset.
	return {"scene": SCENE_PATH, "layout_id": String(_layout.get("id", "")), "unit_count": _units.size(), "units": _units, "legend": _legend,
			"layers_visible": false, "features": feats, "defender": String(_layout.get("defender", "")), "ranges_visible": shown == ranged,
			"ranges": _ranges, "glyph_px": _glyph_px, "legend_text": "\n".join(_legend_lines),
			"camera": {"bbox": _bbox, "margin": CAMERA_MARGIN}}
