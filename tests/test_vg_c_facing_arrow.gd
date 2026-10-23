extends "res://tests/support/vg_c_case.gd"

# VG-C-facing-arrow (spec paragraph "**VG-C-facing-arrow", docs/northstar/plans/2026-10-07-visible-game-spec.md; owns
# scenes/ground3d/ground_units.gd, scenes/tactical_c/unit_visuals.gd, scenes/tactical_c/unit_squads.gd). Proves S-001
# ("arrows show facing", the S-001 ridge close frame) and the facing-offset amendment (FINDING-facing-offset-2d-only).
# Words of the request, Westley 2026-10-22: "tiny little arrows pointing away from the unit that indicate direction
# (like a white triangle, no bigger than 2/5 the unit size)". DRAFT-facing-arrow-len = 0.4 x the body size.
# Rule pins:
#
# AMENDMENT 2026-10-23 (round-two audit) WINS over the paragraph on main where they differ. Differences from the paragraph
# (as on main when this was written): (1) the arrow lies on the ray from the body centre along the heading
# h = facing + facing_offset_rad: base at distance r (3D 11.5 wu, 2D SHAPE_RADIUS 12 px x k) along the ray, apex at base +
# 0.4 x body size (3D 9.2 wu, 2D 9.6 px x k) on the same ray; NO per-shape "largest x" base (the paragraph: 1.0, 0.8 square);
# (2) 2D: Arrow is a SIBLING of Body under the unit's Node2D with rotation h (the paragraph: "child of the unit's Node2D,
# rotated with Body"; Body keeps its own rotation, the arrow is not a child of Body); (3) 3D: Arrow is a child of the body
# mesh node, local +x forward, no rotation of its own (the body's Basis carries h); (4) accessors, NO qa_state in this piece:
# Units3D.arrow_count(), Units3D.arrow_apex_world(id) -> Vector3, UnitVisuals.arrow_count(), UnitVisuals.arrow_apex_px(id) ->
# Vector2 (the paragraph: qa_state() `arrows`, which VG-C-land-marks adds, not this piece).
#
# What is asserted:
#   3D (Units3D body from ground_units.gd): a child MeshInstance3D "Arrow" with identity rotation, an unshaded white triangle
#     of one surface, length 9.2 wu (within 0.1), base width half the length, base_mid at local x 11.5, apex at x 20.7, on the
#     body axis, lifted 0.2 wu above the body plane (the paragraph's lift; the amendment does not change it).
#   2D (UnitVisuals._make_node): a Polygon2D "Arrow", child of the unit's Node2D (not of Body), white, rotation = facing +
#     facing_offset(type) (Body's own rotation untouched by it); length 9.6 x k px (within 0.5), width half, base_mid at local
#     x 12 x k, k = Body.scale.x.
#   Direction, both views, read from the accessors: arrow_apex_world(id) / arrow_apex_px(id) minus the unit centre lies on
#     the heading h (within 2 degrees) at distance r + 0.4 x size (3D 20.7 wu +-0.1; 2D (12 + 9.6) x k px +-0.5). Per type at
#     facing 0: raider -x, bombard -y, the four others +x. The half turn control: a facing change of pi flips the direction.
#   Counts: Units3D.arrow_count() and UnitVisuals.arrow_count() equal the unit count.
#   Amendment FINDING-facing-offset-2d-only: UnitVisuals.facing_offset(type) static (raider pi, bombard -pi/2, others 0); at
#     pitch 90 the raider's 3D nose and its 2D icon point within 2 degrees of each other on screen.
#   Controls of the helpers (green on main): the triangle reader is run on synthetic triangles first.
#
# UNSTATED INTERFACE choices (a builder who differs files a test-defect row):
#   U2  The 3D arrow is a MeshInstance3D whose mesh is one surface of three distinct vertices; colour from material_override,
#       else surface 0, as albedo_color; "unshaded" is shading_mode == SHADING_MODE_UNSHADED. Geometry is read in the Arrow's
#       local frame (the body's tilt cannot move it).
#   U3  arrow_apex_world(id) is a Vector3 in world space, arrow_apex_px(id) a Vector2 in the same global space as the unit
#       node's global_position (the centre); the world heading is atan2(z, x) of the apex offset (sim x = scene x, y = z).
#   U4  2D "size" is 2 x SHAPE_RADIUS x k with k = Body.scale.x; the length is 9.6 x k.
#   U5  Tolerances the amendment does not give: 0.1 wu in 3D, 0.5 px in 2D; every direction within 2 degrees; "white" is each
#       channel within 0.01 of 1.0.
#   U6  The pitch-90 test builds the real Ground3DHost, calls camera_rig().set_top_down(true) and projects with the rig
#       camera; nose = mean of the body points of largest local x.
#   U7  UnitSquads's own use of facing_offset is not asserted (its rotation lives in the private _batches).
# The Superseded pins (TD-VG-C-facing-arrow) in tests/test_vg_c6_ground_units.gd, test_vg_c6b_ground_units_layers.gd and
# test_vg_e_e1k.gd were checked earlier: none reads rotation.y or a body's child inventory, so none is edited.

const UV := "res://scenes/tactical_c/unit_visuals.gd"
const LEN_RATIO := 0.4 # DRAFT-facing-arrow-len, x the body width
const BODY_R_WU := 11.5 # BODY_RADIUS_WU
const SHAPE_R_PX := 12.0 # SHAPE_RADIUS
const LEN_3D := 9.2 # 0.4 x 2 x 11.5
const LEN_2D := 9.6 # 0.4 x 2 x 12, x k
const TOL_3D := 0.1
const TOL_2D := 0.5
const LIFT_WU := 0.2
const DIR_TOL_DEG := 2.0
const TYPE_NAME := ["raider", "interceptor", "vanguard", "warden", "bombard", "bastion"]
# the paragraph's per-type apex direction at facing 0 (x, y of the world / the unit's node)
const DIR0 := [Vector2(-1, 0), Vector2(1, 0), Vector2(1, 0), Vector2(1, 0), Vector2(0, -1), Vector2(1, 0)]
const OFFSET_RAD := [PI, 0.0, 0.0, 0.0, -PI / 2.0, 0.0] # the manifest's facing_offset_rad, assets/eras/*/manifest.json


func _unit(id: int, faction: int, type: int, x: float, y: float, facing: float) -> Dictionary:
	return {"id": id, "faction": faction, "type": type, "tier": 1, "x": x, "y": y, "hp": 100, "layer": 0, "facing": facing, "target": -1, "state": 0, "sight": 200}


# Six types, own (ids 1-6) and enemy (ids 11-16) alike, spread over the fixture terrain.
func _units(facing: float) -> Array:
	var out := []
	for t in 6:
		out.append(_unit(1 + t, 0, t, 150.0 + 80.0 * t, 250.0, facing))
		out.append(_unit(11 + t, 1, t, 150.0 + 80.0 * t, 450.0, facing))
	return out


func _frame(units: Array) -> Dictionary:
	var vis0 := []
	for u in units:
		vis0.append(int(u["id"]))
	var profiles := []
	for t in 6:
		profiles.append({"type": t, "max_hp": 100.0, "range": 600.0, "interval": 10, "sensor": 800.0, "ability": t, "acd_max": 100, "aoe": 0.0})
	return {"type": "tactical", "tick": 100, "player_faction": 0, "units": units, "visible": {"0": vis0, "1": vis0},
		"profiles": profiles, "events": [], "structures": [], "objectives": [], "map": {"nodes": [], "cover": [], "obstacles": []}}


func _deg(a: float, b: float) -> float:
	return absf(rad_to_deg(angle_difference(a, b)))


func _white(c: Color) -> bool:
	return absf(c.r - 1.0) < 0.01 and absf(c.g - 1.0) < 0.01 and absf(c.b - 1.0) < 0.01


# Apex of a triangle given as three points (Vector3, 2D points with z = 0): the vertex whose two sides are equal; returns
# {"apex": Vector3, "base_mid": Vector3, "length": float, "width": float}, empty when not exactly three distinct points.
func _tri(pts: Array) -> Dictionary:
	var u := []
	for p in pts:
		var dup := false
		for q in u:
			if (p as Vector3).distance_to(q) < 1e-4:
				dup = true
		if not dup:
			u.append(p)
	if u.size() != 3:
		return {}
	var best := 0
	var best_d := INF
	for i in 3:
		var d: float = absf((u[i] as Vector3).distance_to(u[(i + 1) % 3]) - (u[i] as Vector3).distance_to(u[(i + 2) % 3]))
		if d < best_d:
			best_d = d
			best = i
	var a: Vector3 = u[best]
	var b: Vector3 = u[(best + 1) % 3]
	var c: Vector3 = u[(best + 2) % 3]
	var mid := (b + c) * 0.5
	return {"apex": a, "base_mid": mid, "length": a.distance_to(mid), "width": b.distance_to(c)}


func _mesh_pts(mi: MeshInstance3D) -> Array:
	var out := []
	if mi.mesh == null or mi.mesh.get_surface_count() == 0:
		return out
	for v in mi.mesh.surface_get_arrays(0)[Mesh.ARRAY_VERTEX]:
		out.append(v)
	return out


func _mat_of(mi: MeshInstance3D) -> BaseMaterial3D:
	if mi.material_override is BaseMaterial3D:
		return mi.material_override
	if mi.mesh != null and mi.mesh.get_surface_count() > 0 and mi.mesh.surface_get_material(0) is BaseMaterial3D:
		return mi.mesh.surface_get_material(0)
	return null


func _has_static(s: GDScript, name: String) -> bool:
	for m in s.get_script_method_list():
		if str(m["name"]) == name:
			return true
	return false


func _run() -> void:
	_helper_controls()
	await _test_arrow_3d()
	await _test_arrow_2d()
	await _test_direction_and_half_turn()
	await _test_offset_single_source_pitch90()
	await _test_arrow_counts()


# CONTROL (green on main): the triangle reader finds the apex, length and width of a known triangle, 3D and 2D.
func _helper_controls() -> void:
	var t3: Dictionary = _tri([Vector3(20.0, 0.2, 0.0), Vector3(10.8, 0.2, 2.3), Vector3(10.8, 0.2, -2.3)])
	_check(not t3.is_empty() and absf(t3["length"] - 9.2) < 1e-4 and absf(t3["width"] - 4.6) < 1e-4 and (t3["apex"] as Vector3).x > 19.9, "CONTROL: the triangle reader must read apex (20,.,0), length 9.2, width 4.6 from a known 3D triangle, got %s" % [t3])
	var t2: Dictionary = _tri([Vector3(-5.0, 0.0, 0.0), Vector3(4.6, 2.4, 0.0), Vector3(4.6, -2.4, 0.0)])
	_check(not t2.is_empty() and (t2["apex"] as Vector3).x < -4.9 and absf(t2["length"] - 9.6) < 1e-4, "CONTROL: the triangle reader must read the apex at -x and length 9.6 from a known 2D triangle, got %s" % [t2])
	_check(_deg(0.0, PI) > 179.0 and _deg(0.1, 0.1 + TAU) < 0.001 and not _white(Color(1, 0.3, 0.3)) and _white(Color.WHITE), "CONTROL: the angle and white helpers must tell opposite sides and a red from white")


# S-001: every 3D body, own and enemy, has the white Arrow child of the stated size and place (3D).
func _test_arrow_3d() -> void:
	var gu := _load(SCENES + "ground_units.gd")
	if gu == null:
		return
	var fx := _fixture()
	var node: Node3D = gu.new()
	root.add_child(node)
	await process_frame
	node.set_units(_units(0.0), fx.terrain(), [0.0], [])
	for id in [1, 2, 3, 4, 5, 6, 11, 12, 13, 14, 15, 16]:
		var t: int = (id - 1) % 10
		var body: Node3D = node.unit_node(id)
		_check(body != null, "S-001: no 3D body for unit %d" % id)
		if body == null:
			continue
		var ar = body.get_node_or_null("Arrow") as MeshInstance3D
		_check(ar != null, "S-001 (a): 3D %s body (unit %d) has no MeshInstance3D child named Arrow; children %s" % [TYPE_NAME[t], id, body.get_children()])
		if ar == null:
			continue
		var m: BaseMaterial3D = _mat_of(ar)
		_check(m != null and _white(m.albedo_color), "S-001: 3D %s arrow must be white, got %s" % [TYPE_NAME[t], m.albedo_color if m != null else "no material"])
		_check(m != null and m.shading_mode == BaseMaterial3D.SHADING_MODE_UNSHADED, "S-001: 3D %s arrow must be unshaded" % TYPE_NAME[t])
		_check(ar.transform.basis.is_equal_approx(Basis.IDENTITY), "S-001 amendment: 3D %s Arrow has no rotation of its own (local +x forward), basis %s" % [TYPE_NAME[t], ar.transform.basis])
		var pts := []
		for p in _mesh_pts(ar):
			pts.append(ar.transform * (p as Vector3))
		var tri: Dictionary = _tri(pts)
		_check(not tri.is_empty(), "S-001: 3D %s arrow must be one triangle of three distinct points, got %d points" % [TYPE_NAME[t], pts.size()])
		if tri.is_empty():
			continue
		_check(absf(tri["length"] - LEN_3D) <= TOL_3D, "S-001 DRAFT-facing-arrow-len: 3D %s arrow length %.3f wu, draft %.1f (0.4 x 2 x 11.5), within %.1f" % [TYPE_NAME[t], tri["length"], LEN_3D, TOL_3D])
		_check(absf(tri["width"] - tri["length"] * 0.5) <= TOL_3D, "S-001: 3D %s arrow base width %.3f must be half its length %.3f" % [TYPE_NAME[t], tri["width"], tri["length"]])
		var bm: Vector3 = tri["base_mid"]
		var ap: Vector3 = tri["apex"]
		_check(absf(bm.x - BODY_R_WU) <= TOL_3D and absf(bm.z) <= TOL_3D, "S-001 amendment: 3D %s arrow base must sit at distance r = 11.5 wu on the body's +x axis (no per-shape front edge), got (%.2f, %.2f)" % [TYPE_NAME[t], bm.x, bm.z])
		_check(absf(bm.y - LIFT_WU) <= TOL_3D and absf(ap.y - LIFT_WU) <= TOL_3D, "S-001: 3D %s arrow must be lifted 0.2 wu above the body plane, base y %.3f apex y %.3f" % [TYPE_NAME[t], bm.y, ap.y])
		_check(ap.x > bm.x and absf(ap.z - bm.z) <= TOL_3D, "S-001 (U3): 3D %s arrow apex must point outward along +x of the body frame, apex %s base %s" % [TYPE_NAME[t], ap, bm])
	node.queue_free()


# S-001: every 2D unit node has the white Arrow child of the stated size and place, rotated with Body (2D).
func _test_arrow_2d() -> void:
	var uvs = load(UV)
	_check(uvs != null, "unit_visuals.gd must load")
	if uvs == null:
		return
	var uv: Node2D = uvs.new()
	root.add_child(uv)
	uv.set_frame(_frame(_units(0.5)), 0, 0.25, Vector2.ZERO)
	for id in [1, 2, 3, 4, 5, 6, 11, 12, 13, 14, 15, 16]:
		var t: int = (id - 1) % 10
		var n: Node2D = uv.unit_node(id)
		_check(n != null, "S-001: no 2D node for unit %d" % id)
		if n == null:
			continue
		var ar = n.get_node_or_null("Arrow") as Polygon2D
		_check(ar != null, "S-001 (a): 2D %s node (unit %d) has no Polygon2D child named Arrow; children %s" % [TYPE_NAME[t], id, n.get_children()])
		if ar == null:
			continue
		_check(_white(ar.color), "S-001: 2D %s arrow must be white, got %s" % [TYPE_NAME[t], ar.color])
		var pts := []
		for p in ar.polygon:
			pts.append(Vector3(p.x, p.y, 0.0))
		var tri: Dictionary = _tri(pts)
		_check(not tri.is_empty() and ar.polygon.size() == 3, "S-001 (U4): 2D %s arrow must be one triangle of three points, got %d" % [TYPE_NAME[t], ar.polygon.size()])
		if tri.is_empty():
			continue
		var body: Polygon2D = n.get_node("Body")
		var k := body.scale.x
		_check(ar.get_parent() == n, "S-001 amendment: 2D %s Arrow must be a sibling of Body under the unit's Node2D (not a child of Body), parent %s" % [TYPE_NAME[t], ar.get_parent()])
		var h: float = 0.5 + OFFSET_RAD[t]
		_check(absf(angle_difference(ar.rotation, h)) < 1e-3, "S-001 amendment: 2D %s Arrow rotation %.4f must be h = facing + offset = %.4f" % [TYPE_NAME[t], ar.rotation, h])
		_check(absf(tri["length"] - LEN_2D * k) <= TOL_2D, "S-001 DRAFT-facing-arrow-len: 2D %s arrow length %.3f px, draft %.1f x k %.2f (0.4 x 2 x 12 x k), within %.1f" % [TYPE_NAME[t], tri["length"], LEN_2D * k, k, TOL_2D])
		_check(absf(tri["width"] - tri["length"] * 0.5) <= TOL_2D, "S-001: 2D %s arrow base width %.3f must be half its length %.3f" % [TYPE_NAME[t], tri["width"], tri["length"]])
		var bm: Vector3 = tri["base_mid"]
		_check(absf(bm.x - SHAPE_R_PX * k) <= TOL_2D and absf(bm.y) <= TOL_2D, "S-001 amendment: 2D %s arrow base must sit at r = 12 x k = %.2f px on its local +x ray (no per-shape front edge), got (%.2f, %.2f)" % [TYPE_NAME[t], SHAPE_R_PX * k, bm.x, bm.y])
	uv.queue_free()


# Apex direction (S-001: the arrow shows the facing) in both views, per type, plus the half-turn positive control.
func _test_direction_and_half_turn() -> void:
	var gu := _load(SCENES + "ground_units.gd")
	var uvs = load(UV)
	if gu == null or uvs == null:
		return
	var fx := _fixture()
	var u3: Node3D = gu.new()
	root.add_child(u3)
	var uv: Node2D = uvs.new()
	root.add_child(uv)
	await process_frame
	var dir3 := {}
	var dir2 := {}
	for f in [0.0, PI, 0.9, 0.9 + PI]:
		u3.set_units(_units(f), fx.terrain(), [0.0], [])
		uv.set_frame(_frame(_units(f)), 0, 0.25, Vector2.ZERO)
		for id in [1, 2, 3, 4, 5, 6, 11, 15]:
			var t: int = (id - 1) % 10
			var want: float = DIR0[t].rotated(f).angle() # the paragraph's per-type direction, turned by the facing
			var r3 = _apex_angle_3d(u3, id)
			var r2 = _apex_angle_2d(uv, id)
			var a3 = r3["a"] if r3 != null else null
			var a2 = r2["a"] if r2 != null else null
			dir3[[id, f]] = a3
			dir2[[id, f]] = a2
			var k: float = uv.unit_node(id).get_node("Body").scale.x
			_check(a3 != null and _deg(a3, want) <= DIR_TOL_DEG, "S-001 (b): 3D %s (unit %d) at facing %.2f: apex angle %s, want %.1f deg (facing + offset)" % [TYPE_NAME[t], id, f, ("%.1f deg" % rad_to_deg(a3)) if a3 != null else "no arrow_apex_world", rad_to_deg(want)])
			_check(a2 != null and _deg(a2, want) <= DIR_TOL_DEG, "S-001 (b): 2D %s (unit %d) at facing %.2f: apex angle %s, want %.1f deg (facing + offset)" % [TYPE_NAME[t], id, f, ("%.1f deg" % rad_to_deg(a2)) if a2 != null else "no arrow_apex_px", rad_to_deg(want)])
			_check(r3 != null and absf(r3["d"] - (BODY_R_WU + LEN_3D)) <= TOL_3D, "S-001 (b): 3D %s (unit %d) apex must be r + 0.4 x size = 20.7 wu from the centre, got %s" % [TYPE_NAME[t], id, r3["d"] if r3 != null else "no arrow_apex_world"])
			_check(r2 != null and absf(r2["d"] - (SHAPE_R_PX + LEN_2D) * k) <= TOL_2D, "S-001 (b): 2D %s (unit %d) apex must be (12 + 9.6) x k = %.2f px from the centre, got %s" % [TYPE_NAME[t], id, (SHAPE_R_PX + LEN_2D) * k, r2["d"] if r2 != null else "no arrow_apex_px"])
	# Positive control: the same unit, facing changed by a half turn between two frames -> apex on the opposite side.
	for id in [1, 4, 5]:
		for pair in [[0.0, PI], [0.9, 0.9 + PI]]:
			for view in [dir3, dir2]:
				var p = view[[id, pair[0]]]
				var q = view[[id, pair[1]]]
				_check(p != null and q != null and _deg(p, q) > 180.0 - DIR_TOL_DEG, "CONTROL S-001 (b): unit %d turned a half turn (%.2f -> %.2f) must have its apex on the opposite side, got %s and %s deg" % [id, pair[0], pair[1], ("%.1f" % rad_to_deg(p)) if p != null else "no accessor", ("%.1f" % rad_to_deg(q)) if q != null else "no accessor"])
	u3.queue_free()
	uv.queue_free()


# World angle (x, y of the sim = x, z of the 3D scene) and distance of the 3D apex from the body centre, from the accessor;
# null without the accessor or the body.
func _apex_angle_3d(u3: Node3D, id: int) -> Variant:
	var body: Node3D = u3.unit_node(id)
	if body == null or not u3.has_method("arrow_apex_world"):
		return null
	var v: Vector3 = (u3.call("arrow_apex_world", id) as Vector3) - body.global_position
	return {"a": atan2(v.z, v.x), "d": v.length()}


# Angle and distance of the 2D apex from the unit node's centre, from the accessor; null without it.
func _apex_angle_2d(uv: Node2D, id: int) -> Variant:
	var n: Node2D = uv.unit_node(id)
	if n == null or not uv.has_method("arrow_apex_px"):
		return null
	var v: Vector2 = (uv.call("arrow_apex_px", id) as Vector2) - n.global_position
	return {"a": v.angle(), "d": v.length()}


# Amendment FINDING-facing-offset-2d-only: one source, UnitVisuals.facing_offset(type); and at pitch 90 the raider's 3D nose
# and its 2D icon point within 2 degrees of each other on screen (stationary unit, planted facing; on main they differ by 180).
func _test_offset_single_source_pitch90() -> void:
	var uvs = load(UV)
	var gs := _load(SCENES + "ground3d.gd")
	if uvs == null or gs == null:
		return
	var has: bool = _has_static(uvs, "facing_offset")
	_check(has, "amendment (b): UnitVisuals.facing_offset(type) static does not exist")
	if has:
		for t in 6:
			_check(absf(float(uvs.call("facing_offset", t)) - OFFSET_RAD[t]) < 0.001, "amendment: UnitVisuals.facing_offset(%d) (%s) must be the manifest's %.4f" % [t, TYPE_NAME[t], OFFSET_RAD[t]])
	var fx := _fixture()
	var host = gs.new()
	root.add_child(host)
	await process_frame
	host.set_terrain(fx.terrain())
	host.camera_rig().set_top_down(true)
	var f := 0.6 # planted facing; no travel
	var units := [_unit(1, 0, 0, 450.0, 350.0, f), _unit(2, 0, 4, 550.0, 350.0, f)]
	host.set_frame(_frame(units), fx.mission())
	await process_frame
	await process_frame
	var u3: Node = null
	for c in host.find_children("*", "Node3D", true, false):
		if c.has_method("unit_node") and c.has_method("shadow_of"):
			u3 = c
	_check(u3 != null, "pitch 90: no Units3D found under the ground host")
	var uv: Node2D = uvs.new()
	root.add_child(uv)
	uv.set_frame(_frame(units), 0, 0.25, Vector2.ZERO)
	var cam: Camera3D = host.camera_rig().get_camera()
	if u3 != null:
		for pair in [[1, 0], [2, 4]]:
			var body: Node3D = u3.unit_node(pair[0])
			if body == null:
				_check(false, "pitch 90: no 3D body for unit %d" % pair[0])
				continue
			var nose_local := _nose3(_mesh_pts(body))
			var c0 := cam.unproject_position(body.global_position)
			var c1 := cam.unproject_position(body.global_transform * nose_local)
			var a3 := (c1 - c0).angle()
			var bd: Polygon2D = uv.unit_node(pair[0]).get_node("Body")
			var nose2 := _nose2(bd.polygon)
			var a2 := (bd.transform * nose2 - bd.transform * Vector2.ZERO).angle()
			_check(_deg(a3, a2) <= DIR_TOL_DEG, "amendment: %s at pitch 90: 3D nose points %.1f deg on screen, 2D icon %.1f deg (differ by %.1f, want within 2; on main 180)" % [TYPE_NAME[pair[1]], rad_to_deg(a3), rad_to_deg(a2), _deg(a3, a2)])
	host.queue_free()
	uv.queue_free()


# The nose of a shape: the mean of its distinct points of largest x (the bombard's front edge has two, its nose is on the axis).
func _nose3(pts: Array) -> Vector3:
	var mx := -INF
	for p in pts:
		mx = maxf(mx, (p as Vector3).x)
	var sum := Vector3.ZERO
	var n := 0
	var seen := []
	for p in pts:
		if (p as Vector3).x > mx - 1e-4 and not seen.has(snapped(p, Vector3.ONE * 1e-3)):
			seen.append(snapped(p, Vector3.ONE * 1e-3))
			sum += p
			n += 1
	return sum / maxf(n, 1)


func _nose2(pts: PackedVector2Array) -> Vector2:
	var a := []
	for p in pts:
		a.append(Vector3(p.x, p.y, 0.0))
	var n := _nose3(a)
	return Vector2(n.x, n.z * 0.0 + n.y)


# S-001: arrow_count() of each view equals the unit count (no qa_state in this piece; VG-C-land-marks adds `arrows`).
func _test_arrow_counts() -> void:
	var gu := _load(SCENES + "ground_units.gd")
	var uvs = load(UV)
	if gu == null or uvs == null:
		return
	var fx := _fixture()
	var u3: Node3D = gu.new()
	root.add_child(u3)
	var uv: Node2D = uvs.new()
	root.add_child(uv)
	await process_frame
	var units := _units(0.3)
	u3.set_units(units, fx.terrain(), [0.0], [])
	uv.set_frame(_frame(units), 0, 0.25, Vector2.ZERO)
	_check(u3.has_method("arrow_count") and int(u3.call("arrow_count")) == units.size(), "S-001 (b): Units3D.arrow_count() must equal the unit count %d, got %s" % [units.size(), u3.call("arrow_count") if u3.has_method("arrow_count") else "no accessor"])
	_check(uv.has_method("arrow_count") and int(uv.call("arrow_count")) == units.size(), "S-001 (b): UnitVisuals.arrow_count() must equal the unit count %d, got %s" % [units.size(), uv.call("arrow_count") if uv.has_method("arrow_count") else "no accessor"])
	u3.queue_free()
	uv.queue_free()
