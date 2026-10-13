extends "res://tests/support/vg_c_case.gd"

# VG-C-unitscale (scenes/ground3d/ground_units.gd, class Units3D). Proves FINDING-unit-draw-overlap and the
# named draft DRAFT-unit-body-radius. No bible rule bears on drawn body size (R-095-05 and R-099-04 name the
# collision radius only as an arrival distance), so the only source is spec line :302. Quoted word for word:
#
#   Test sentence (spec :302): "Test: the drawn mesh bounding box is at most 30 wu, the lattice pitch
#   `[P csrc/mission.c:2463]`; the pitch 30.0 is pinned with a comment naming `om_constants.h:581` and
#   `mission.c:2463`; positive control: 20 (a 40 wu box) fails."
#
#   Draft sentence (spec :302): "so the body is drawn at `BODY_RADIUS_WU` 11.5 and `SHADOW_RADIUS_WU` 10 (shadow
#   inside the body as today's 18 is inside 20): `[DRAFT-unit-body-radius]` (old values 20 and 18; Westley may
#   veto after the shot) `[A 2026-10-12, drafter gap ruling]`."
#
# FINDING-unit-draw-overlap: bodies 40 wu wide on a 30 wu lattice overlap by a third. The lattice is the spawn
# grid of csrc/mission.c:2463 (spacing = 2.0 * OM_UNIT_COLLISION_RADIUS); OM_UNIT_COLLISION_RADIUS is 15 at
# csrc/om_constants.h:581. Ledger rows: FINDING-unit-draw-overlap, DRAFT-unit-body-radius
# (docs/northstar/plans/push_ledger_2026-09-22.md). The two numbers 11.5 and 10 are the named draft's; 30 wu is
# the pitch. The 0.001 wu below is a float epsilon on the mesh extent, not a threshold.

# Lattice pitch, wu: 2 * OM_UNIT_COLLISION_RADIUS (15) per csrc/om_constants.h:581 and csrc/mission.c:2463.
# Pinned as a literal: no GDScript accessor for the collision radius is loaded (spec :302 gap 2, null action).
const LATTICE_PITCH_WU := 30.0
const COLLISION_RADIUS_WU := 15.0 # csrc/om_constants.h:581
const EPS := 0.001 # float epsilon on a mesh extent, not a threshold
# DRAFT-unit-body-radius (spec :302, Architect ruling 2026-10-12; old values 20 and 18; Westley may veto).
const DRAFT_BODY_RADIUS_WU := 11.5
const DRAFT_SHADOW_RADIUS_WU := 10.0
const OLD_BODY_RADIUS_WU := 20.0 # the positive control's radius (a 40 wu box)


# The one predicate used by the live assertion and by the control: a body's x and z extent both fit the pitch.
static func _box_fits(extent_x: float, extent_z: float) -> bool:
	return extent_x <= LATTICE_PITCH_WU + EPS and extent_z <= LATTICE_PITCH_WU + EPS


# Extent (Vector2(x, z)) of the SHAPES polygon of type scaled by radius, from the polygon vertices.
func _poly_extent(shapes: Array, type: int, radius: float) -> Vector2:
	var lo := Vector2(INF, INF)
	var hi := Vector2(-INF, -INF)
	for p in shapes[type]:
		var q: Vector2 = p * radius
		lo = Vector2(minf(lo.x, q.x), minf(lo.y, q.y))
		hi = Vector2(maxf(hi.x, q.x), maxf(hi.y, q.y))
	return hi - lo


func _run() -> void:
	var gu := _load(SCENES + "ground_units.gd")
	if gu == null:
		return
	var uv := load(TCAM + "unit_visuals.gd") as GDScript
	_check(uv != null, "CONTROL: scenes/tactical_c/unit_visuals.gd does not load")
	if uv == null:
		return
	var shapes: Array = uv.SHAPES
	var node = gu.new()
	root.add_child(node)
	await process_frame
	# (1) CONTROL, green today
	_check(node is Node3D, "CONTROL: Units3D.new() is not a Node3D")
	_check(LATTICE_PITCH_WU == 2.0 * COLLISION_RADIUS_WU, "CONTROL: pitch %s is not 2 * the collision radius %s (csrc/om_constants.h:581, csrc/mission.c:2463)" % [LATTICE_PITCH_WU, COLLISION_RADIUS_WU])
	_check(LATTICE_PITCH_WU == 30.0, "CONTROL: the lattice pitch must be 30.0")
	_check(shapes.size() == 6, "CONTROL: UnitVisuals.SHAPES must hold six types, got %d" % shapes.size())

	# (2) POSITIVE CONTROL, green today: the same predicate on the SHAPES polygons scaled by a radius.
	# Built from the six SHAPES polygons scaled by 20 (independent of the live script's current radius).
	var worst_old := Vector2.ZERO
	var worst_new := Vector2.ZERO
	for t in shapes.size():
		var eo := _poly_extent(shapes, t, OLD_BODY_RADIUS_WU)
		var en := _poly_extent(shapes, t, DRAFT_BODY_RADIUS_WU)
		worst_old = Vector2(maxf(worst_old.x, eo.x), maxf(worst_old.y, eo.y))
		worst_new = Vector2(maxf(worst_new.x, en.x), maxf(worst_new.y, en.y))
	_check(not _box_fits(worst_old.x, worst_old.y), "CONTROL: radius 20 (a %s x %s wu box) must fail the predicate" % [worst_old.x, worst_old.y])
	_check(absf(maxf(worst_old.x, worst_old.y) - 40.0) < EPS, "CONTROL: radius 20 widest box must be 40 wu, got %s" % maxf(worst_old.x, worst_old.y))
	_check(_box_fits(worst_new.x, worst_new.y), "CONTROL: radius 11.5 (a %s x %s wu box) must pass the predicate" % [worst_new.x, worst_new.y])
	_check(absf(maxf(worst_new.x, worst_new.y) - 23.0) < EPS, "CONTROL: radius 11.5 widest box must be 23 wu, got %s" % maxf(worst_new.x, worst_new.y))

	# (3) The live assertion, RED today: the static _body mesh of every SHAPES type fits the pitch.
	var info: Array[String] = []
	for t in shapes.size():
		var mi: MeshInstance3D = gu._body(t, Color.WHITE)
		_check(mi != null and mi.mesh != null, "type %d: _body returned no mesh" % t)
		if mi == null or mi.mesh == null:
			if mi != null:
				mi.free()
			continue
		var box: AABB = mi.mesh.get_aabb()
		mi.free()
		var far := 0.0
		for p in shapes[t]:
			far = maxf(far, (p as Vector2).length())
		var live_r: float = gu.BODY_RADIUS_WU
		info.append("type %d: extent x %.3f z %.3f, farthest vertex %.3f, diagonal reach %.3f" % [t, box.size.x, box.size.z, far * live_r, Vector2(box.size.x, box.size.z).length()])
		_check(_box_fits(box.size.x, box.size.z), "FINDING-unit-draw-overlap: type %d drawn body box is %.3f x %.3f wu, more than the %.1f wu lattice pitch (BODY_RADIUS_WU %s)" % [t, box.size.x, box.size.z, LATTICE_PITCH_WU, gu.BODY_RADIUS_WU])
	for line in info:
		print("INFO " + line)

	# (4) The named draft's radii. SHADOW <= BODY is green today (18 < 20) and stays green (10 < 11.5).
	_check(absf(gu.BODY_RADIUS_WU - DRAFT_BODY_RADIUS_WU) < EPS, "DRAFT-unit-body-radius: BODY_RADIUS_WU must be 11.5, got %s" % gu.BODY_RADIUS_WU)
	_check(absf(gu.SHADOW_RADIUS_WU - DRAFT_SHADOW_RADIUS_WU) < EPS, "DRAFT-unit-body-radius: SHADOW_RADIUS_WU must be 10.0, got %s" % gu.SHADOW_RADIUS_WU)
	_check(gu.SHADOW_RADIUS_WU <= gu.BODY_RADIUS_WU, "DRAFT-unit-body-radius: the shadow (%s) must be inside the body (%s)" % [gu.SHADOW_RADIUS_WU, gu.BODY_RADIUS_WU])
	print("PREMISES BODY_RADIUS_WU=%s SHADOW_RADIUS_WU=%s LATTICE_PITCH_WU=%s" % [gu.BODY_RADIUS_WU, gu.SHADOW_RADIUS_WU, LATTICE_PITCH_WU])
	node.queue_free()
