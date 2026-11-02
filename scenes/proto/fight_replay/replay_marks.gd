extends RefCounted

## H-053 Replay readability: the marks the fight replay draws that the layout shot does not. Ring line styles (one per role, so a ring is told apart by its
## line and not only by its size), role glyph shapes (six distinct, so Raider and Interceptor never look alike) and the facing tick. Pure geometry, no scene state.
## Every number below is a DRAFT-stage2-look (the Architect's, 2026-11-02); Westley rules. See also scenes/proto/fight_replay/fight_replay.gd.

const STYLES := ["solid", "dotted", "dashed", "dash_dot", "long_dash", "double"]  # index = role index (Raider, Interceptor, Vanguard, Warden, Bombard, Bastion)
const SHAPES := ["triangle", "diamond", "square", "pentagon", "circle", "hexagon"]  # same order
const RING_SEGMENTS := 192  # DRAFT-stage2-ring-segments: a ring is this many chords, a dash pattern counts chords
const DOUBLE_GAP := 0.05  # DRAFT-stage2-double-gap: the second line of a double ring sits this fraction of the radius inside the first
## DRAFT-stage2-ring-patterns: alternating drawn and blank chord counts, by style; solid and double are unbroken.
const PATTERNS := {"dotted": [1, 2], "dashed": [4, 3], "dash_dot": [6, 2, 1, 2], "long_dash": [12, 4]}
const CIRCLE_POINTS := 24
const TICK_HALF_WIDTH := 0.5  # DRAFT-stage2-tick-width: the facing tick's half base, in glyph radii


## The world polylines of a ring of `radius` about `centre` in `style`: one closed loop for solid, two for double, the drawn dashes otherwise.
static func ring_runs(centre: Vector2, radius: float, style: String) -> Array:
	var out: Array = []
	if style == "double":
		out.append(_loop(centre, radius))
		out.append(_loop(centre, radius * (1.0 - DOUBLE_GAP)))
		return out
	if style == "solid" or not PATTERNS.has(style):
		out.append(_loop(centre, radius))
		return out
	var pattern: Array = PATTERNS[style]
	var cycle := 0
	for n in pattern:
		cycle += n
	var run := PackedVector2Array()
	for k in RING_SEGMENTS:
		var phase := k % cycle
		var on := true
		var edge := 0
		for slot in pattern.size():
			edge += pattern[slot]
			if phase < edge:
				on = slot % 2 == 0
				break
		if on:
			if run.is_empty():
				run.append(_on_ring(centre, radius, k))
			run.append(_on_ring(centre, radius, k + 1))
		elif not run.is_empty():
			out.append(run)
			run = PackedVector2Array()
	if not run.is_empty():
		out.append(run)
	return out


static func _on_ring(centre: Vector2, radius: float, k: int) -> Vector2:
	return centre + Vector2.from_angle(TAU * float(k) / float(RING_SEGMENTS)) * radius


static func _loop(centre: Vector2, radius: float) -> PackedVector2Array:
	var pts := PackedVector2Array()
	for k in RING_SEGMENTS + 1:
		pts.append(_on_ring(centre, radius, k))
	return pts


## The outline of role glyph `role` (an index into SHAPES) in glyph radii, pointing along +x.
static func shape_points(role: int) -> PackedVector2Array:
	var pts := PackedVector2Array()
	match SHAPES[role]:
		"triangle":
			pts = PackedVector2Array([Vector2(1.0, 0.0), Vector2(-0.8, 0.9), Vector2(-0.8, -0.9)])
		"diamond":
			pts = PackedVector2Array([Vector2(1.0, 0.0), Vector2(0.0, 0.8), Vector2(-1.0, 0.0), Vector2(0.0, -0.8)])
		"square":
			pts = PackedVector2Array([Vector2(0.8, 0.8), Vector2(-0.8, 0.8), Vector2(-0.8, -0.8), Vector2(0.8, -0.8)])
		"pentagon":
			pts = _regular(5)
		"circle":
			pts = _regular(CIRCLE_POINTS)
		_:
			pts = _regular(6)
	return pts


static func _regular(n: int) -> PackedVector2Array:
	var pts := PackedVector2Array()
	for k in n:
		pts.append(Vector2.from_angle(TAU * float(k) / float(n)))
	return pts


## A flat body mesh for role glyph `role`, `radius` wu, in `colour`, turned by `offset` radians about the up axis (UnitVisuals.facing_offset, so the shape cancels it).
static func glyph_mesh(role: int, radius: float, colour: Color, offset: float) -> ArrayMesh:
	var pts := shape_points(role)
	var tris := Geometry2D.triangulate_polygon(pts)
	var verts := PackedVector3Array()
	var turn := Basis(Vector3.UP, offset)
	for i in tris:
		verts.append(turn * Vector3(pts[i].x * radius, 0.0, pts[i].y * radius))
	var mesh := _mesh(verts)
	var mat := StandardMaterial3D.new()
	mat.albedo_color = colour
	mat.cull_mode = BaseMaterial3D.CULL_DISABLED
	mesh.surface_set_material(0, mat)
	return mesh


## The facing tick: a white triangle on the +x ray from the glyph's edge, as long as the glyph is wide (2 x radius), so it scales with the glyph.
static func tick_mesh(radius: float, lift: float) -> ArrayMesh:
	var hw := radius * TICK_HALF_WIDTH
	var mesh := _mesh(PackedVector3Array([Vector3(radius * 3.0, lift, 0.0), Vector3(radius, lift, hw), Vector3(radius, lift, -hw)]))
	var mat := StandardMaterial3D.new()
	mat.albedo_color = Color.WHITE
	mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	mat.cull_mode = BaseMaterial3D.CULL_DISABLED
	mesh.surface_set_material(0, mat)
	return mesh


static func _mesh(verts: PackedVector3Array) -> ArrayMesh:
	var arr := []
	arr.resize(Mesh.ARRAY_MAX)
	arr[Mesh.ARRAY_VERTEX] = verts
	var mesh := ArrayMesh.new()
	mesh.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arr)
	return mesh
