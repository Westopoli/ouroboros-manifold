extends RefCounted

## LAB stage 5 (H-091 R-091-18 to R-091-22): the marks the fight replay draws for a file with a top-level `stage5` key: the firing-arc wedge, the hit mark, the climb bar,
## the band mark, their legend rows and the running hit totals. Geometry and per-frame state only, no scene state; fight_replay.gd draws what this returns, in the style of
## replay_marks.gd. Every number below that the story does not give is a named DRAFT; Westley rules. See also scenes/proto/fight_replay/replay_marks.gd and fight_replay.gd.

const WEDGE_SEGMENTS := 24  # DRAFT-stage5-wedge-segments: the arc of a wedge is this many chords at the full 360, never fewer than 2
const WEDGE_ALPHA := 0.35  # DRAFT-stage5-wedge-alpha: a wedge's outline, in its side's colour
const HIT_COLOURS := {"front": Color.WHITE, "side": Color(1.0, 0.5, 0.0), "rear": Color(1.0, 0.0, 0.0)}  # story: front white, side orange, rear red
const HIT_RING_RADII := 2.0  # DRAFT-stage5-hit-ring: a hit mark is a ring this many glyph radii wide, a further hit on the same victim in the frame 0.6 radii wider each
const HIT_RING_STEP := 0.6
const HIT_RING_SEGMENTS := 16
const BAR_LENGTH := 3.0  # DRAFT-stage5-bar: the climb bar's size and its distance from the glyph centre, in glyph radii (the bar sits on the -y side of the unit)
const BAR_THICK := 0.5
const BAR_OFFSET := 2.2
const BAR_BACK := Color(0.1, 0.1, 0.1, 0.8)
const BAR_FILL := Color(0.95, 0.95, 0.3)
const BAND_COLOURS := [Color(0.65, 0.65, 0.65), Color(1.0, 0.85, 0.3), Color(0.4, 0.9, 0.9)]  # DRAFT-stage5-band-colours: band 0 grey, then the layout shot's tier colours at full strength (TIER_COLOURS in layout_shot.gd)
const BAND_RADIUS := 0.4  # DRAFT-stage5-band-mark: a disc this many glyph radii wide, set at the glyph's +x, +y shoulder
const BAND_OFFSET := 0.9


## The outline of a wedge of `arc_deg` centred on `facing` (radians, x toward y), `length` wu long, from `centre`: centre, the arc, centre. A full circle (360 or more) has no spokes.
static func wedge_points(centre: Vector2, facing: float, arc_deg: float, length: float) -> PackedVector2Array:
	var pts := PackedVector2Array()
	var full := arc_deg >= 360.0
	var span := deg_to_rad(minf(arc_deg, 360.0))
	var n := maxi(2, ceili(float(WEDGE_SEGMENTS) * span / TAU))
	if not full:
		pts.append(centre)
	for k in n + 1:
		pts.append(centre + Vector2.from_angle(facing - span * 0.5 + span * float(k) / float(n)) * length)
	if not full:
		pts.append(centre)
	return pts


## The ring of hit mark number `k` (0 for the first on a victim in the frame) about `centre`; `radius` is the glyph radius in wu.
static func hit_ring(centre: Vector2, radius: float, k: int) -> PackedVector2Array:
	var pts := PackedVector2Array()
	var r := radius * (HIT_RING_RADII + HIT_RING_STEP * float(k))
	for j in HIT_RING_SEGMENTS + 1:
		pts.append(centre + Vector2.from_angle(TAU * float(j) / float(HIT_RING_SEGMENTS)) * r)
	return pts


## The corners of a climb bar above the unit at `centre`: the whole bar (fraction 1) or the filled part (fraction `f`), as a rectangle from the bar's -x end.
static func bar_rect(centre: Vector2, radius: float, f: float) -> PackedVector2Array:
	var left := centre + Vector2(-0.5 * BAR_LENGTH * radius, -BAR_OFFSET * radius - 0.5 * BAR_THICK * radius)
	var w := BAR_LENGTH * radius * f
	var t := BAR_THICK * radius
	return PackedVector2Array([left, left + Vector2(w, 0.0), left + Vector2(w, t), left + Vector2(0.0, t)])


## The band mark's disc about the unit at `centre`.
static func band_disc(centre: Vector2, radius: float) -> PackedVector2Array:
	var pts := PackedVector2Array()
	var c := centre + Vector2(BAND_OFFSET, BAND_OFFSET) * radius
	for j in HIT_RING_SEGMENTS:
		pts.append(c + Vector2.from_angle(TAU * float(j) / float(HIT_RING_SEGMENTS)) * BAND_RADIUS * radius)
	return pts


static func band_colour(layer: int) -> Color:
	return BAND_COLOURS[clampi(layer, 0, BAND_COLOURS.size() - 1)]


## A flat filled polygon (a convex outline in the x-z plane, already lifted onto the terrain) as an unshaded mesh in `colour`.
static func fill_mesh(outline: PackedVector3Array, colour: Color) -> MeshInstance3D:
	var verts := PackedVector3Array()
	for i in range(1, outline.size() - 1):
		verts.append_array([outline[0], outline[i], outline[i + 1]])
	var arr := []
	arr.resize(Mesh.ARRAY_MAX)
	arr[Mesh.ARRAY_VERTEX] = verts
	var mesh := ArrayMesh.new()
	mesh.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arr)
	var mat := StandardMaterial3D.new()
	mat.albedo_color = colour
	mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	mat.cull_mode = BaseMaterial3D.CULL_DISABLED
	var mi := MeshInstance3D.new()
	mi.mesh = mesh
	mi.material_override = mat
	return mi


## `qa_state().arcs`: {id, facing, arc_deg} per living unit of `frame`.
static func arcs_state(frame: Dictionary, arc_deg: float) -> Array:
	var out: Array = []
	for u in frame["units"]:
		if bool(u["alive"]):
			out.append({"id": int(u["id"]), "facing": float(u["facing"]), "arc_deg": arc_deg})
	return out


## `qa_state().hit_marks`: {v, cls} per entry of the frame's `hits`.
static func hit_marks_state(frame: Dictionary) -> Array:
	var out: Array = []
	for h in frame.get("hits", []):
		out.append({"v": int(h["v"]), "cls": String(h["cls"])})
	return out


## `qa_state().climbing_units`: {id, climbing} per living unit whose `climbing` is strictly between 0 and 1.
static func climbing_state(frame: Dictionary) -> Array:
	var out: Array = []
	for u in frame["units"]:
		var c := float(u.get("climbing", 0.0))
		if bool(u["alive"]) and c > 0.0 and c < 1.0:
			out.append({"id": int(u["id"]), "climbing": c})
	return out


## `qa_state().band_marks`: {id, layer} per living unit.
static func band_state(frame: Dictionary) -> Array:
	var out: Array = []
	for u in frame["units"]:
		if bool(u["alive"]):
			out.append({"id": int(u["id"]), "layer": int(u["layer"])})
	return out


## The running hit totals [front, side, rear] after each frame: the hits of frame 0 up to that frame.
static func running_totals(frames: Array) -> Array:
	var out: Array = []
	var sum := {"front": 0, "side": 0, "rear": 0}
	for f in frames:
		for h in f.get("hits", []):
			sum[String(h["cls"])] += 1
		out.append([sum["front"], sum["side"], sum["rear"]])
	return out


static func totals_text(t: Array) -> String:
	return "front %d  side %d  rear %d" % [t[0], t[1], t[2]]


## The legend rows the stage 5 drawing adds: [{text, colour}], the arc, the three hit colours, the climb bar and the bands.
static func legend_rows(arc_deg: float) -> Array:
	var rows: Array = [{"text": "arc: %d deg wedge, role range" % roundi(arc_deg), "colour": Color.WHITE}]
	for cls in ["front", "side", "rear"]:
		rows.append({"text": "hit %s" % cls, "colour": HIT_COLOURS[cls]})
	rows.append({"text": "climb bar: filled to the climb", "colour": BAR_FILL})
	for k in BAND_COLOURS.size():
		rows.append({"text": "band %d mark" % k, "colour": BAND_COLOURS[k]})
	return rows
