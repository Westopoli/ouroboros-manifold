extends SceneTree
# Rule pins: R-106-05@a91085
# test-timeout: 20000

# Piece VG-B25-vast-space (docs/northstar/plans/2026-10-07-visible-game-spec.md rev 12d, lane B, paragraph
# "VG-B25-vast-space", interface block "INTERFACE" under it; gap rulings g1 to g7, ledger rows DRAFT-b25-layers,
# -stars, -brightness, -tints, -wash, -dust, -far, -tier2 and TD-VG-B-20 in docs/northstar/plans/push_ledger_2026-09-22.md).
# Proves (bible E-16, docs/bible/epics/E-16-client-camera-hud-and-world-view.md):
#   S-106 "The galaxy between missions" and S-107 "Reading the galaxy" (the B23 S-107 frame, Westley 2026-10-12: "still
#   lacking the 3 things that were decided on regarding making the galaxy feel less like it's an isolated ball"), and
#   R-106-05  Given the world view, When idle, Then an ambient particle field (rings, inflow streams, dust, starfield,
#             central glow) fills the space behind the territory at low opacity.
#             (B25 rewrites the rule's list to: a dim direction-only wash, four world-fixed star layers at real depth and a
#             wrapping volume of motes, with no visible radius and nothing that stops at an edge.)
# Westley 2026-10-02: "vast space gets the dim wash, real-depth star layers and fading edges together".
# Source text of every row below is docs/northstar/plans/2026-10-02-galaxy-bubble-field-spec.md Step 5, lines 76-83:
#   Wash:  "a very dim, low-contrast, direction-only background, computed once, no animation."
#   Depth: "four static star layers, one draw each, at about 100, 250, 800 and 2,500 units; star size grows with depth
#           so stars stay 1 to 3 pixels; camera far plane raised to cover them."
#   Edges: "density and brightness fall off smoothly in every layer; nothing stops at a radius."
#   Dust:  "one wrapping volume of motes centred on the camera, fading near its faces; replaces the radius-60 dust."
#   Tests: "layer count and depth ratios (each at least 2.5 times the previous); star count per radial shell falls
#           monotonically over each layer's outer half; outermost layer at least 5 times beyond the camera's reach; far
#           plane covers it; wrap rule keeps every mote within half a box of the camera for 1,000 random camera positions;
#           old starfield and dust emitters gone; at most 6 added draws."
#   Accept: "Westley's eye, plus my check for a visible radius, layers moving in lock-step, and shimmering sub-pixel stars."
#
# Rows (R1 to R12 of the brief; the quoted line each row proves is repeated at the row):
#   R11 positive controls (green today, run first), R1 layer ratios, R2 shell monotonic and no visible radius, R3 reach,
#   R4 far plane, R5 wrap rule and tier 2, R6 old emitters gone and the parity list, R7 at most 6 added draws,
#   R8 lock-step tell, R9 sub-pixel tell, R10 wash, R12 qa_inventory.
#
# Rulings used (not thresholds invented here): g1 BACKDROP_SCALE 0.5 (layers 50, 125, 400, 1250); g2 far plane 3,000 and
# the 1,250 layer's 2R clip at 2,500 (DRAFT-b25-far); g3 world-fixed shells about the origin, Gaussian thickness R/4
# clipped at 2R (outer half = radius R to 2R); g4 DRAFT-b25-* numbers: 2,000 stars per layer at tier 0, box 120, 400
# motes, wash ceiling 0.012 above the background and 0.02 contrast; g5 tier 2 halves counts (DRAFT-b25-tier2 0.5) and
# qa_state "backdrop" is qa_inventory(); g6 the INTERFACE block.
#
# TEST PARAMETERS (named so the Architect sees them; none is a threshold of the rule):
#   SHELLS 3 equal-width radial shells over each layer's outer half [R, 2R] (R2). Chosen so that, for a Gaussian of
#     sigma R/4, the expected last-shell count is about 7 of 2,000 stars (a finer split leaves the last shell near zero).
#   HASH_CAMS 1000 camera positions of R5 from _h() (integer hash, seeds 11, 12, 13), each component (h % 20001 - 10000) * 0.05
#     (so within plus or minus 500); T_A 3.0 and T_B 11.0 the two drift times; WRAP_PROBES 6 far-away points per camera.
#   LOCK_DISPLACEMENT (20, 0, 0) camera step of R8 from two start positions (0,0,0) and (0,60,90).
#   WASH_DIRS 1000 hashed directions (seeds 21, 22, 23) for R10.
#   R9: viewport 1080 px, fov 45 degrees (the brief), SWEEP_STEPS 24 geometric steps from the nearest to the farthest
#     star distance over camera samples at the origin and at the six axis points at camera_reach() from it.
#   OCTANT test points: the stars of all four layers at tier 0.
#   FLOAT_EPS 1e-6 absolute and REL_SLACK 1e-5 relative are float32 rounding allowances (positions are float32), not
#     tolerances of a rule. HALF_TOL 0.02 is the existing B11 ratio tolerance (tests/test_vg_b_b11.gd:25), unchanged.
#   Floor of R3: camera_reach() >= OrbitCamera.DIST_MAX (120, read live), so a reach of 0 cannot pass "5 times" vacuously.
#   Tint reading of R6: a star's tint is read from the layer mesh's per-vertex ARRAY_COLOR rgb (red above blue = gold,
#     blue above red = blue). The INTERFACE fixes ONE surface of PRIMITIVE_POINTS but not where the tint lives; if the
#     builder keeps it elsewhere that row is a test-defect for the ruler, not a reason to move it.
# NOT ASSERTED HERE (printed as NOTE needs-display, listed in the report): the dust motes' two tints and the fade of their
# alpha toward the box faces (the CameraDust MultiMesh colours are server side and the dummy renderer does not keep
# them; the INTERFACE has no CPU accessor). They belong to tests/galaxy_field/b25_gpu_checks.gd or need an accessor.
#
# Method: red on the built tree for the missing-feature reason (the constant, function or node is absent). Every call into
# the rig's static interface goes through a has-method map, so a missing function fails its row and the file runs to the
# end (the _completed assertion, as tests/test_vg_b_b11.gd does). Headless-safe: CPU-side functions, node tree, resources
# and ArrayMesh arrays only (the dummy renderer keeps ArrayMesh surface arrays; it does not keep MultiMesh data).

const SCENE_PATH := "res://scenes/galaxy/galaxy_view.tscn"
const FIXTURE_PATH := "res://tests/transport/fixtures/snapshot_seed1_tick10.json"
const RIG_PATH := "res://scenes/galaxy/ambient_rig.gd"
const SHADER_DIR := "res://scenes/galaxy/shaders/"
const OLD_SHADERS := ["starfield_particles.gdshader", "dust_particles.gdshader"]
const LAYERS := 4
const SHELLS := 3
const HASH_CAMS := 1000
const WRAP_PROBES := 6
const T_A := 3.0
const T_B := 11.0
const LOCK_DISPLACEMENT := Vector3(20.0, 0.0, 0.0)
const LOCK_STARTS := [Vector3(0.0, 0.0, 0.0), Vector3(0.0, 60.0, 90.0)]
const WASH_DIRS := 1000
const VIEWPORT_H := 1080.0
const FOV_DEG := 45.0
const SWEEP_STEPS := 24
const FLOAT_EPS := 0.000001
const REL_SLACK := 0.00001
const HALF_TOL := 0.02
const WASH_CEILING := 0.012      # DRAFT-b25-wash
const WASH_CONTRAST := 0.02      # DRAFT-b25-wash
const BG := Color(0.0392157, 0.0509804, 0.0705882, 1.0)   # galaxy_view.tscn:9-11, unchanged by B25
const STARS_TIER0 := 2000        # DRAFT-b25-stars
const DUST_BOX_G4 := 120.0       # DRAFT-b25-dust
const DUST_COUNT_G4 := 400       # DRAFT-b25-dust
const FAR_G2 := 3000.0           # DRAFT-b25-far
const SIX := ["Wash", "StarLayer0", "StarLayer1", "StarLayer2", "StarLayer3", "CameraDust"]

var _pass := 0
var _fail := 0
var _msgs: Array[String] = []
var _rows := {}
var _completed := false
var _bus: Node
var _rs: GDScript
var _consts := {}
var _mnames: Array = []
var _pos := {}       # layer -> PackedVector3Array at tier 0
var _alp := {}       # layer -> PackedFloat32Array at tier 0
var _view: Node


func _initialize() -> void:
	await _run_tests()
	_row("R0", _completed, "the B25 checks did not run to the end (a script error aborted them)")
	print("\n=== VG B25 Vast Space Test Results ===")
	var ids := _rows.keys()
	ids.sort()
	for id in ids:
		print("ROW %s pass %d fail %d" % [id, _rows[id][0], _rows[id][1]])
	print("PASS: %d  FAIL: %d" % [_pass, _fail])
	if _fail > 0:
		print("Failures:")
		for m in _msgs:
			print("  - " + m)
		print("=== RED ===\n")
		quit(1)
	else:
		print("=== GREEN ===\n")
		quit(0)


func _row(id: String, cond: bool, msg: String) -> void:
	if not _rows.has(id):
		_rows[id] = [0, 0]
	if cond:
		_pass += 1
		_rows[id][0] += 1
		return
	_fail += 1
	_rows[id][1] += 1
	var where := ""
	var st := get_stack()
	var f := 1
	while f < st.size() - 1 and st[f]["function"] == "_need":
		f += 1   # a missing-feature row is reported at the row that asked, not at the guard
	if st.size() > f:
		where = "%s:%d" % [str(st[f]["source"]).replace("res://", ""), int(st[f]["line"])]
	_msgs.append("%s [%s] %s" % [where, id, msg])


# ---- interface guards -------------------------------------------------------------------------------------------

func _load_rig_script() -> bool:
	_rs = load(RIG_PATH)
	if _rs == null:
		return false
	_consts = _rs.get_script_constant_map()
	for m in _rs.get_script_method_list():
		_mnames.append(String(m["name"]))
	return true


func _need(id: String, consts: Array, methods: Array) -> bool:
	var ok := true
	for c in consts:
		if not _consts.has(c):
			_row(id, false, "missing-feature: scenes/galaxy/ambient_rig.gd has no const %s (the B25 interface is not built)" % c)
			ok = false
	for m in methods:
		if not (m in _mnames):
			_row(id, false, "missing-feature: scenes/galaxy/ambient_rig.gd has no function %s (the B25 interface is not built)" % m)
			ok = false
	return ok


func _sc(name: String, args: Array = []):
	return _rs.callv(name, args)


func _h(a: int, b: int) -> int:
	var x: int = ((a * 73856093) ^ (b * 19349663) ^ 0x9E3779B9) & 0xFFFFFFFF
	x ^= x >> 16
	x = (x * 0x45D9F3B) & 0xFFFFFFFF
	x ^= x >> 16
	x = (x * 0x45D9F3B) & 0xFFFFFFFF
	x ^= x >> 16
	return x


func _hv(k: int, seed0: int, span: float) -> Vector3:
	return Vector3(
		(float(_h(k, seed0) % 20001) - 10000.0) * 0.0001 * span,
		(float(_h(k, seed0 + 1) % 20001) - 10000.0) * 0.0001 * span,
		(float(_h(k, seed0 + 2) % 20001) - 10000.0) * 0.0001 * span)


func _new_rig(tier: int) -> Node3D:
	var s: Dictionary = _bus.get_settings().duplicate(true)
	s["galaxy_quality"] = tier
	_bus.save_settings(s)
	var rig = _rs.new()
	rig.name = "AmbientRig"
	get_root().add_child(rig)
	rig.set_process(false)   # no camera in a bare rig; _process is exercised in the view (R5b)
	return rig


func _new_view() -> Node:
	var snap = JSON.parse_string(FileAccess.get_file_as_string(FIXTURE_PATH))
	var view: Node = (load(SCENE_PATH) as PackedScene).instantiate()
	get_root().add_child(view)
	await process_frame
	await process_frame
	if view.has_method("set_snapshot"):
		view.set_snapshot(snap)
	for _i in 8:
		await process_frame
	return view


func _free(n: Node) -> void:
	if n != null and is_instance_valid(n):
		n.queue_free()
	await process_frame


func _gpu_total(rig: Node) -> int:
	var t := [0]
	_sum_particles(rig, t)
	return t[0]


func _sum_particles(n: Node, t: Array) -> void:
	if n is GPUParticles3D:
		t[0] += int(n.amount)
	for c in n.get_children():
		_sum_particles(c, t)


func _collect(n: Node, out: Array) -> void:
	for c in n.get_children():
		out.append(c)
		_collect(c, out)


# ---- detectors (each shown live on a synthetic input in R11) -----------------------------------------------------

func _ratios_ok(radii: Array, factor: float) -> bool:
	if radii.size() < 2:
		return false
	for i in range(1, radii.size()):
		if not (float(radii[i]) >= factor * float(radii[i - 1])):
			return false
	return true


func _non_increasing(counts: Array) -> bool:
	for i in range(1, counts.size()):
		if float(counts[i]) > float(counts[i - 1]):
			return false
	return counts.size() > 0


# Whether wrap_fn(p, cam) lands inside [cam - box/2, cam + box/2) per component and differs from p by whole boxes.
func _wrap_ok(wrap_fn: Callable, p: Vector3, cam: Vector3, box: float) -> bool:
	var w: Vector3 = wrap_fn.call(p, cam)
	var half := box * 0.5
	for a in 3:
		var d: float = w[a] - cam[a]
		var slack: float = REL_SLACK * (absf(cam[a]) + absf(p[a]) + box)
		if d < -half - slack or d > half + slack:
			return false
		var k: float = (p[a] - w[a]) / box
		if absf(k - roundf(k)) > 100.0 * REL_SLACK:
			return false
	return true


func _old_emitters(root: Node) -> Array:
	var found: Array = []
	_scan_old(root, found)
	return found


func _scan_old(n: Node, found: Array) -> void:
	if n.name == &"Starfield" or n.name == &"AmbientDust":
		found.append("node " + String(n.name))
	if n is GPUParticles3D:
		var pm = n.process_material
		if pm is ShaderMaterial and pm.shader != null:
			for s in OLD_SHADERS:
				if String(pm.shader.resource_path).ends_with(s):
					found.append("emitter %s uses %s" % [n.name, s])
	for c in n.get_children():
		_scan_old(c, found)


# Wash detectors (R10; shown live on synthetic washes in R11). wash_fn(dir) -> Color over the hashed directions.
func _wash_cols(wash_fn: Callable) -> Array:
	var cols: Array = []
	for k in WASH_DIRS:
		var v := _hv(k, 21, 1.0)
		var dir: Vector3 = v.normalized() if v.length() > 0.05 else Vector3.RIGHT
		cols.append(wash_fn.call(dir))
	return cols


# Floor: no channel of the wash is below the background in any sampled direction (the wash only brightens: blend_add).
func _wash_floor_ok(cols: Array) -> bool:
	for c in cols:
		for ch in 3:
			if c[ch] < BG[ch] - FLOAT_EPS:
				return false
	return cols.size() > 0


# Varies with the view direction: across the sampled directions the spread of the wash value is above zero (some channel).
func _wash_varies(cols: Array) -> bool:
	var sp := _spread(cols)
	return cols.size() > 0 and (sp.x > 0.0 or sp.y > 0.0 or sp.z > 0.0)


func _spread(cols: Array) -> Vector3:
	var lo := Vector3(INF, INF, INF)
	var hi := Vector3(-INF, -INF, -INF)
	for c in cols:
		lo = Vector3(minf(lo.x, c.r), minf(lo.y, c.g), minf(lo.z, c.b))
		hi = Vector3(maxf(hi.x, c.r), maxf(hi.y, c.g), maxf(hi.z, c.b))
	return hi - lo


# The material a backdrop node draws with (override first, then the surface material).
func _material_of(n: Node) -> Material:
	if n is MeshInstance3D:
		if n.material_override != null:
			return n.material_override
		if n.mesh != null and n.mesh.get_surface_count() > 0:
			return n.mesh.surface_get_material(0)
	elif n is MultiMeshInstance3D:
		if n.material_override != null:
			return n.material_override
		if n.multimesh != null and n.multimesh.mesh != null and n.multimesh.mesh.get_surface_count() > 0:
			return n.multimesh.mesh.surface_get_material(0)
	return null


func _shader_code(n: Node) -> String:
	var m := _material_of(n)
	if m is ShaderMaterial and m.shader != null:
		return m.shader.code
	return ""


func _shader_path(n: Node) -> String:
	var m := _material_of(n)
	if m is ShaderMaterial and m.shader != null:
		return String(m.shader.resource_path)
	return ""


func _star_arrays(rig: Node, i: int) -> Array:
	var n = rig.get_node_or_null("StarLayer%d" % i)
	if not (n is MeshInstance3D) or n.mesh == null or n.mesh.get_surface_count() < 1:
		return []
	return n.mesh.surface_get_arrays(0)


# ---- the run ------------------------------------------------------------------------------------------------------

func _run_tests() -> void:
	_bus = get_root().get_node_or_null("UIDataBus")
	_row("R11", _bus != null, "control: UIDataBus autoload missing")
	if _bus == null:
		return
	var original: Dictionary = _bus.get_settings().duplicate(true)
	_row("R11", _load_rig_script(), "control: scenes/galaxy/ambient_rig.gd does not load")
	if _rs == null:
		return

	await _controls()
	await _build_rows()

	_bus.save_settings(original)
	_completed = true


# R11 positive controls: green today. "the rig builds under the default renderer; the 12 rings, RadialStreams, central
# glow and grid plane still exist; the ratio, shell-monotonic, wrap and node-scanner detectors each shown live on a
# synthetic input; tier-2 amounts of the remaining GPUParticles3D stay half."
func _controls() -> void:
	_view = await _new_view()
	var rig = _view.get_node_or_null("AmbientRig")
	_row("R11", rig is Node3D, "control: the built galaxy view has no Node3D named AmbientRig")
	if rig != null:
		var sp: Script = rig.get_script()
		_row("R11", sp != null and sp.resource_path == RIG_PATH, "control: AmbientRig script is not %s (tests/test_vg_b_b14.gd:102-137)" % RIG_PATH)
		# premises, dumped from the live run
		var kids: Array = []
		for c in rig.get_children():
			kids.append("%s:%s" % [c.name, c.get_class()])
		print("PREMISE AmbientRig children: ", kids)
		print("PREMISE GPUParticles3D amount total under the rig: ", _gpu_total(rig))
		for i in range(1, 13):
			var r = rig.get_node_or_null("Ring%02d" % i)
			_row("R11", r is GPUParticles3D, "control: Ring%02d (GPUParticles3D) missing" % i)
		var streams = rig.get_node_or_null("StreamPivot/RadialStreams")
		_row("R11", streams is GPUParticles3D, "control: StreamPivot/RadialStreams missing")
		_row("R11", rig.get_node_or_null("GridPlane") is MeshInstance3D, "control: GridPlane missing")
		var glow := 0
		var sphere := 0
		var halo := 0
		for c in rig.get_children():
			if String(c.name) in SIX:
				continue   # the backdrop nodes of B25 may use any mesh class; the central point and halo are the old nodes
			if c is GPUParticles3D and c.process_material is ParticleProcessMaterial:
				glow += 1
			if c is MeshInstance3D and c.mesh is SphereMesh:
				sphere += 1
			if c is MeshInstance3D and c.mesh is QuadMesh:
				halo += 1
		_row("R11", glow == 1, "control: central glow emitter count %d, want 1" % glow)
		_row("R11", sphere == 1 and halo == 1, "control: central point (SphereMesh) %d and halo (QuadMesh) %d, want 1 and 1" % [sphere, halo])
	var oc = _view.get_node_or_null("OrbitCamera")
	var cam: Camera3D = oc.get_camera() if oc != null else null
	_row("R11", cam != null, "control: the view has no OrbitCamera/Camera3D")
	if cam != null:
		print("PREMISE Camera3D far=%s near=%s fov=%s; OrbitCamera DIST_MIN=%s DIST_MAX=%s" % [cam.far, cam.near, cam.fov, oc.DIST_MIN, oc.DIST_MAX])
	var we = _view.get_node_or_null("WorldEnvironment")
	if we != null and we.environment != null:
		print("PREMISE Environment background_color=", we.environment.background_color, " fog=", we.environment.fog_enabled)
		_row("R11", we.environment.background_color.is_equal_approx(BG), "control: Environment background is not (0.0392157, 0.0509804, 0.0705882) (galaxy_view.tscn:9-11)")
	print("PREMISE tier read by the rig: ", int(_bus.get_settings().get("galaxy_quality", 0)), " ; renderer ", RenderingServer.get_current_rendering_driver_name())

	# detectors live on synthetic input
	_row("R11", _ratios_ok([100.0, 250.0, 800.0, 2500.0], 2.5), "control: ratio detector rejects the Step 5 radii 100/250/800/2500")
	_row("R11", not _ratios_ok([100.0, 200.0, 800.0, 2500.0], 2.5), "control: ratio detector accepts a 2.0x step")
	_row("R11", _non_increasing([9, 5, 5, 1]), "control: shell detector rejects a monotone histogram")
	_row("R11", not _non_increasing([9, 5, 6, 1]), "control: shell detector accepts a non-monotone histogram")
	var wrapping := func(p: Vector3, c: Vector3) -> Vector3:
		var h := 60.0
		return Vector3(c.x + fposmod(p.x - c.x + h, 2.0 * h) - h, c.y + fposmod(p.y - c.y + h, 2.0 * h) - h, c.z + fposmod(p.z - c.z + h, 2.0 * h) - h)
	var not_wrapping := func(p: Vector3, _c: Vector3) -> Vector3:
		return p
	_row("R11", _wrap_ok(wrapping, Vector3(500.0, -300.0, 17.0), Vector3(3.0, 4.0, 5.0), 120.0), "control: wrap check rejects a function that wraps")
	_row("R11", not _wrap_ok(not_wrapping, Vector3(500.0, -300.0, 17.0), Vector3(3.0, 4.0, 5.0), 120.0), "control: wrap check accepts a function that does not wrap")
	var fx := Node3D.new()
	var star := Node3D.new()
	star.name = "Starfield"
	fx.add_child(star)
	var pf := GPUParticles3D.new()
	pf.name = "Anything"
	var sm := ShaderMaterial.new()
	sm.shader = load("res://scenes/mockups/galaxy/shaders/dust_particles.gdshader")
	pf.process_material = sm
	fx.add_child(pf)
	var clean := Node3D.new()
	clean.add_child(Node3D.new())
	_row("R11", _old_emitters(fx).size() == 2, "control: node scanner found %s in a fixture holding a node named Starfield and an emitter of dust_particles.gdshader, want 2 hits" % str(_old_emitters(fx)))
	_row("R11", _old_emitters(clean).size() == 0, "control: node scanner flags a clean fixture")
	fx.free()
	clean.free()
	var st := _spread([Color(0.04, 0.05, 0.07), Color(0.09, 0.05, 0.07)])
	_row("R11", st.x > WASH_CONTRAST and st.y == 0.0, "control: spread detector reads %s on a synthetic pair, want x above the contrast and y 0" % str(st))
	# wash floor and variation detectors on synthetic washes (Architect 2026-10-20: a dead wash must not pass R10)
	var wash_const := func(_d: Vector3) -> Color:
		return Color(BG.r + 0.005, BG.g + 0.005, BG.b + 0.005, 1.0)
	var wash_dark := func(d: Vector3) -> Color:
		var t := 0.004 * (0.5 + 0.5 * d.x)
		return Color(BG.r - t, BG.g - t, BG.b - t, 1.0)
	var wash_good := func(d: Vector3) -> Color:
		var t := 0.005 * (0.5 + 0.5 * d.x)
		return Color(BG.r + t, BG.g + t, BG.b + t, 1.0)
	var cc := _wash_cols(wash_const)
	var cd := _wash_cols(wash_dark)
	var cg := _wash_cols(wash_good)
	_row("R11", not _wash_varies(cc), "control: wash variation detector accepts a constant wash")
	_row("R11", _wash_floor_ok(cc), "control: wash floor detector rejects a constant brightening wash (it must only judge the floor)")
	_row("R11", not _wash_floor_ok(cd), "control: wash floor detector accepts a wash that darkens below the background")
	_row("R11", _wash_varies(cd), "control: wash variation detector rejects a wash that varies with the direction (the darkening one)")
	_row("R11", _wash_floor_ok(cg) and _wash_varies(cg), "control: wash detectors reject a varying, brightening wash (floor %s, varies %s)" % [str(_wash_floor_ok(cg)), str(_wash_varies(cg))])
	var fs := GDScript.new()
	fs.source_code = "extends RefCounted\nstatic func twice(x: int) -> int:\n\treturn x * 2\n"
	fs.reload()
	_row("R11", fs.callv("twice", [4]) == 8, "control: the static-call mechanism used by this file does not call a static function")

	# the B11 contract, run here on bare rigs: tier 2 halves the GPUParticles3D amounts, tier 1 equals tier 0
	var r0 := _new_rig(0)
	var r1 := _new_rig(1)
	var r2 := _new_rig(2)
	var t0 := _gpu_total(r0)
	var t1 := _gpu_total(r1)
	var t2 := _gpu_total(r2)
	_row("R11", t0 > 0, "control: tier 0 GPUParticles3D total is %d" % t0)
	_row("R11", t1 == t0, "control (B11): tier 1 total %d differs from tier 0 %d" % [t1, t0])
	if t0 > 0:
		_row("R11", absf(float(t2) / float(t0) - 0.5) <= HALF_TOL, "control (B11): tier 2 total %d vs tier 0 %d, ratio %.3f, want 0.5 within %.2f" % [t2, t0, float(t2) / float(t0), HALF_TOL])
	r0.free()
	r1.free()
	r2.free()
	await process_frame


func _build_rows() -> void:
	var rig: Node = _view.get_node_or_null("AmbientRig")
	var oc = _view.get_node_or_null("OrbitCamera")
	var cam: Camera3D = oc.get_camera() if oc != null else null

	# R1: "layer count and depth ratios (each at least 2.5 times the previous)"; "four static star layers ... at about
	# 100, 250, 800 and 2,500 units"; g1 (b): layers at 50, 125, 400, 1250.
	var have1 := _need("R1", ["LAYER_COUNT", "LAYER_RADII", "BACKDROP_SCALE"], ["layer_radius"])
	var radii: Array = []
	if have1:
		_row("R1", int(_consts["LAYER_COUNT"]) == LAYERS, "R1 LAYER_COUNT is %s, want 4 (Step 5: four static star layers)" % str(_consts["LAYER_COUNT"]))
		var raw: Array = _consts["LAYER_RADII"]
		var want_raw := [100.0, 250.0, 800.0, 2500.0]
		_row("R1", raw.size() == 4, "R1 LAYER_RADII holds %d entries, want 4" % raw.size())
		for i in mini(raw.size(), 4):
			_row("R1", is_equal_approx(float(raw[i]), want_raw[i]), "R1 LAYER_RADII[%d] is %s, Step 5 says about %s" % [i, str(raw[i]), str(want_raw[i])])
		_row("R1", is_equal_approx(float(_consts["BACKDROP_SCALE"]), 0.5), "R1 BACKDROP_SCALE is %s, g1 (b) rules 0.5" % str(_consts["BACKDROP_SCALE"]))
		var want := [50.0, 125.0, 400.0, 1250.0]
		for i in LAYERS:
			var r: float = float(_sc("layer_radius", [i]))
			radii.append(r)
			_row("R1", is_equal_approx(r, want[i]), "R1 layer_radius(%d) is %s, g1 (b) rules %s" % [i, str(r), str(want[i])])
		_row("R1", _ratios_ok(radii, 2.5), "R1 layer radii %s: not each at least 2.5 times the previous" % str(radii))

	# R2: "star count per radial shell falls monotonically over each layer's outer half"; "density and brightness fall off
	# smoothly in every layer; nothing stops at a radius" (g3: shells about the origin, Gaussian R/4 clipped at 2R).
	var have2 := _need("R2", [], ["layer_radius", "layer_star_count", "layer_star_positions", "layer_star_alphas"])
	if have2:
		for i in LAYERS:
			var R: float = float(_sc("layer_radius", [i]))
			var n := int(_sc("layer_star_count", [i, 0]))
			var pos: PackedVector3Array = _sc("layer_star_positions", [i, 0])
			var alp: PackedFloat32Array = _sc("layer_star_alphas", [i, 0])
			_pos[i] = pos
			_alp[i] = alp
			_row("R2", n == STARS_TIER0, "R2 layer_star_count(%d, 0) is %d, DRAFT-b25-stars says %d" % [i, n, STARS_TIER0])
			_row("R2", pos.size() == n and alp.size() == n, "R2 layer %d: %d positions and %d alphas for a count of %d (same order and length)" % [i, pos.size(), alp.size(), n])
			var again: PackedVector3Array = _sc("layer_star_positions", [i, 0])
			_row("R2", again == pos, "R2 layer %d: layer_star_positions is not deterministic (two calls differ)" % i)
			var counts: Array = []
			var asum: Array = []
			counts.resize(SHELLS)
			asum.resize(SHELLS)
			counts.fill(0)
			asum.fill(0.0)
			var over := 0
			for k in mini(pos.size(), alp.size()):
				var r: float = pos[k].length()
				if r > 2.0 * R * (1.0 + REL_SLACK):
					over += 1
				if r < R:
					continue
				var s := mini(int((r - R) / (R / float(SHELLS))), SHELLS - 1)
				counts[s] += 1
				asum[s] += alp[k]
			_row("R2", over == 0, "R2 layer %d: %d stars beyond the 2R clip (%s)" % [i, over, str(2.0 * R)])
			var mean_a: Array = []
			for s in SHELLS:
				mean_a.append(float(asum[s]) / float(counts[s]) if counts[s] > 0 else 0.0)
			_row("R2", _non_increasing(counts), "R2 layer %d: star count per equal-width shell over [R, 2R] is %s, not non-increasing" % [i, str(counts)])
			_row("R2", _non_increasing(mean_a), "R2 layer %d: mean alpha per shell is %s, not non-increasing" % [i, str(mean_a)])
			_row("R2", counts[0] > 0 and counts[SHELLS - 1] >= 1, "R2 layer %d: the last shell of the outer half holds %d stars (counts %s); a layer that stops at a radius is the visible-radius tell" % [i, int(counts[SHELLS - 1]), str(counts)])
			if counts[SHELLS - 1] >= 1 and counts[SHELLS - 2] >= 1:
				_row("R2", mean_a[SHELLS - 1] <= mean_a[SHELLS - 2], "R2 layer %d: mean alpha at the clip shell %.4f exceeds the shell inside it %.4f (the visible-radius tell)" % [i, mean_a[SHELLS - 1], mean_a[SHELLS - 2]])
			var neg := 0
			for a in alp:
				if a < 0.0:
					neg += 1
			_row("R2", neg == 0, "R2 layer %d: %d negative alphas" % [i, neg])
		# tier 2 (DRAFT-b25-tier2 0.5) and tier 1 (the full field)
		for i in LAYERS:
			var n0 := int(_sc("layer_star_count", [i, 0]))
			var n1 := int(_sc("layer_star_count", [i, 1]))
			var n2 := int(_sc("layer_star_count", [i, 2]))
			_row("R2", n1 == n0, "R2 layer %d: tier 1 count %d differs from tier 0 %d (tier 1 carries the full field)" % [i, n1, n0])
			_row("R2", n0 > 0 and absf(float(n2) / float(n0) - 0.5) <= HALF_TOL, "R2 layer %d: tier 2 count %d vs tier 0 %d, ratio %.3f, want 0.5 within %.2f (DRAFT-b25-tier2)" % [i, n2, n0, float(n2) / float(maxi(n0, 1)), HALF_TOL])
			var p2: PackedVector3Array = _sc("layer_star_positions", [i, 2])
			var a2: PackedFloat32Array = _sc("layer_star_alphas", [i, 2])
			_row("R2", p2.size() == n2 and a2.size() == n2, "R2 layer %d: tier 2 has %d positions and %d alphas for a count of %d" % [i, p2.size(), a2.size(), n2])

	# R3: "outermost layer at least 5 times beyond the camera's reach" (g2).
	var have3 := _need("R3", [], ["layer_radius", "camera_reach"])
	var reach := 0.0
	if have3 and rig != null and rig.has_method("camera_reach"):
		reach = float(rig.camera_reach())
		var l3: float = float(_sc("layer_radius", [3]))
		_row("R3", reach >= float(oc.DIST_MAX), "R3 camera_reach() is %s, below OrbitCamera.DIST_MAX %s (a reach of the camera cannot be less than its farthest zoom)" % [str(reach), str(oc.DIST_MAX)])
		_row("R3", l3 >= 5.0 * reach, "R3 layer_radius(3) %s is not at least 5 times camera_reach() %s" % [str(l3), str(reach)])
	elif have3:
		_row("R3", false, "R3 the AmbientRig instance has no camera_reach()")

	# R4: "camera far plane raised to cover them"; DRAFT-b25-far: the live Camera3D.far equals 3000 and exceeds 2,500.
	if cam != null:
		_row("R4", is_equal_approx(cam.far, FAR_G2), "R4 live Camera3D.far is %s, DRAFT-b25-far says %s" % [str(cam.far), str(FAR_G2)])
		_row("R4", cam.far > 2500.0, "R4 live Camera3D.far %s does not exceed 2,500 (the 1,250 layer's 2R clip)" % str(cam.far))
		var vc := get_root().get_camera_3d()
		_row("R4", vc != null and is_equal_approx(vc.far, FAR_G2), "R4 the active viewport camera far is %s, want %s" % [str(vc.far if vc != null else "none"), str(FAR_G2)])

	# R5: "wrap rule keeps every mote within half a box of the camera for 1,000 random camera positions"; "one wrapping
	# volume of motes centred on the camera" (DRAFT-b25-dust: box 120, 400 motes; DRAFT-b25-tier2 0.5 halves the motes).
	var have5 := _need("R5", ["DUST_BOX", "DUST_COUNT"], ["wrap_mote"])
	if have5:
		var box: float = float(_consts["DUST_BOX"])
		var count: int = int(_consts["DUST_COUNT"])
		_row("R5", is_equal_approx(box, DUST_BOX_G4) and count == DUST_COUNT_G4, "R5 DUST_BOX %s DUST_COUNT %s, DRAFT-b25-dust says %s and %d" % [str(box), str(count), str(DUST_BOX_G4), DUST_COUNT_G4])
		var wrapper := func(p: Vector3, c: Vector3) -> Vector3: return _sc("wrap_mote", [p, c])
		var bad_wrap := 0
		for k in HASH_CAMS:
			var c := _hv(k, 11, 500.0)
			for j in WRAP_PROBES:
				var p: Vector3 = c + _hv(k * 8 + j, 12, 1000.0)
				if not _wrap_ok(wrapper, p, c, box):
					bad_wrap += 1
		_row("R5", bad_wrap == 0, "R5 wrap_mote left %d of %d probe points outside [cam - box/2, cam + box/2) or off a whole-box shift" % [bad_wrap, HASH_CAMS * WRAP_PROBES])
		var dust_rig: Node3D = _new_rig(0)
		var tier2_rig: Node3D = _new_rig(2)
		var have_dust := dust_rig.has_method("update_dust") and dust_rig.has_method("get_dust_positions")
		_row("R5", have_dust, "missing-feature: the rig has no update_dust / get_dust_positions")
		if have_dust:
			var half := box * 0.5
			var outside := 0
			var wrong_count := 0
			var never_moved := 0
			var not_det := 0
			for k in HASH_CAMS:
				var c := _hv(k, 11, 500.0)
				dust_rig.update_dust(c, T_A)
				var a: PackedVector3Array = dust_rig.get_dust_positions().duplicate()   # packed arrays are passed by reference
				dust_rig.update_dust(c, T_A)
				var a_again: PackedVector3Array = dust_rig.get_dust_positions().duplicate()
				dust_rig.update_dust(c, T_B)
				var b: PackedVector3Array = dust_rig.get_dust_positions().duplicate()
				if a.size() != count or b.size() != count:
					wrong_count += 1
				if a != a_again:
					not_det += 1
				for arr in [a, b]:
					for p in arr:
						for ax in 3:
							var d: float = p[ax] - c[ax]
							var sl: float = REL_SLACK * (absf(c[ax]) + half)
							if d < -half - sl or d > half + sl:
								outside += 1
				if a == b:
					never_moved += 1
			_row("R5", wrong_count == 0, "R5 get_dust_positions() size differs from DUST_COUNT %d at tier 0 for %d of %d camera positions" % [count, wrong_count, HASH_CAMS])
			_row("R5", outside == 0, "R5 %d mote components lie farther than DUST_BOX/2 = %s from the camera over %d hashed camera positions" % [outside, str(half), HASH_CAMS])
			_row("R5", never_moved == 0, "R5 the motes did not drift between t=%s and t=%s for %d of %d camera positions" % [str(T_A), str(T_B), never_moved, HASH_CAMS])
			_row("R5", not_det == 0, "R5 update_dust(cam, t) is not deterministic for %d camera positions" % not_det)
			var dm = dust_rig.get_node_or_null("CameraDust")
			_row("R5", dm is MultiMeshInstance3D and dm.multimesh != null and dm.multimesh.instance_count == count, "R5 CameraDust MultiMesh instance_count is %s, want DUST_COUNT %d" % [str(dm.multimesh.instance_count if dm is MultiMeshInstance3D and dm.multimesh != null else "none"), count])
			if tier2_rig.has_method("get_dust_positions"):
				tier2_rig.update_dust(Vector3.ZERO, T_A)
				var n2: int = tier2_rig.get_dust_positions().size()
				_row("R5", absf(float(n2) / float(count) - 0.5) <= HALF_TOL, "R5 tier 2 motes %d vs tier 0 %d, ratio %.3f, want 0.5 within %.2f (DRAFT-b25-tier2)" % [n2, count, float(n2) / float(count), HALF_TOL])
		dust_rig.free()
		tier2_rig.free()
		await process_frame
		# R5b: the wrap follows the live camera from _process (g5 item b), not only a call from a test.
		var live: Node = _view.get_node_or_null("AmbientRig")
		if live != null and live.has_method("get_dust_positions") and oc != null:
			var targets := [Vector3(300.0, 0.0, -200.0), Vector3(-900.0, 40.0, 700.0)]
			var far_off := 0
			for tgt in targets:
				oc.set_view(60.0, tgt)
				for _i in 3:
					await process_frame
				var cp: Vector3 = get_root().get_camera_3d().global_position
				var pts: PackedVector3Array = live.get_dust_positions()
				var half2 := box * 0.5
				for p in pts:
					for ax in 3:
						if absf(p[ax] - cp[ax]) > half2 + REL_SLACK * (absf(cp[ax]) + half2):
							far_off += 1
			_row("R5", far_off == 0, "R5b %d mote components stay farther than DUST_BOX/2 from the live camera after it moved (update_dust is not called from _process with the active camera position)" % far_off)
			oc.set_view(60.0, Vector3.ZERO)
			await process_frame

	# R6: "old starfield and dust emitters gone" plus the parity list (CLAUDE.md "No deletion without parity").
	var rig6: Node = _view.get_node_or_null("AmbientRig")
	if rig6 != null:
		var old := _old_emitters(rig6)
		_row("R6", old.size() == 0, "R6 the old emitters are still under the rig: %s (the node scanner of R11 finds them; delete _build_starfield and _build_ambient_dust)" % str(old))
		# what the old emitters showed (V1 starfield, V2 dust), listed and checked on the replacement:
		# V1a stars in every direction
		if _pos.size() == LAYERS:
			var oct := {}
			for i in LAYERS:
				for p in _pos[i]:
					oct[int(p.x >= 0.0) * 4 + int(p.y >= 0.0) * 2 + int(p.z >= 0.0)] = true
			_row("R6", oct.size() == 8, "R6 parity V1: stars of the four layers fill %d of 8 octants about the origin (the old starfield filled all 8)" % oct.size())
		else:
			_row("R6", false, "R6 parity V1: no layer positions to count octants (layer_star_positions missing)")
		# V1b both tints in every layer, V1c brightness varies star to star
		for i in LAYERS:
			var arrs := _star_arrays(rig6, i)
			var cols: PackedColorArray = arrs[Mesh.ARRAY_COLOR] if arrs.size() > Mesh.ARRAY_COLOR and arrs[Mesh.ARRAY_COLOR] != null else PackedColorArray()
			var gold := 0
			var blue := 0
			for c in cols:
				if c.r > c.b:
					gold += 1
				elif c.b > c.r:
					blue += 1
			_row("R6", gold > 0 and blue > 0, "R6 parity V1: StarLayer%d carries %d gold and %d blue stars (per-vertex ARRAY_COLOR; the old starfield had both tints; mesh arrays read: %d)" % [i, gold, blue, arrs.size()])
			var distinct := {}
			if _alp.has(i):
				for a in _alp[i]:
					distinct[snappedf(a, 0.000001)] = true
			_row("R6", distinct.size() >= 2, "R6 parity V1: layer %d has %d distinct alphas, want at least 2 (brightness varies star to star)" % [i, distinct.size()])
		# V1d/V2 additive blend, no depth write, fog_disabled on every backdrop material
		for nm in SIX:
			var n = rig6.get_node_or_null(nm)
			var code := _shader_code(n) if n != null else ""
			_row("R6", code.contains("blend_add"), "R6 parity: %s material shader has no blend_add (the old emitters were additive); shader '%s'" % [nm, _shader_path(n) if n != null else "no node"])
			_row("R6", code.contains("depth_draw_never"), "R6 parity: %s material shader has no depth_draw_never (no depth write)" % nm)
			_row("R6", code.contains("fog_disabled"), "R6 spec: %s material shader has no fog_disabled (spec rev 12d: the three backdrop shaders use fog_disabled)" % nm)
		# V2 dust twinkle: the shader reads TIME (allowed for the twinkle only)
		var dcode := _shader_code(rig6.get_node_or_null("CameraDust")) if rig6.get_node_or_null("CameraDust") != null else ""
		_row("R6", dcode.contains("TIME"), "R6 parity V2: backdrop_dust.gdshader does not contain TIME (the old dust twinkled)")
		print("NOTE needs-display: R6 parity V2 dust tints (gold and blue motes) and the alpha fade toward the box faces are MultiMesh colours, not readable under the dummy renderer; route to tests/galaxy_field/b25_gpu_checks.gd or add a CPU accessor")

	# R7: "at most 6 added draws".
	if rig6 != null:
		for nm in SIX:
			var n = rig6.get_node_or_null(nm)
			var want_mm: bool = nm == "CameraDust"
			var kind_ok: bool = (n is MultiMeshInstance3D) if want_mm else (n is MeshInstance3D)
			_row("R7", kind_ok, "R7 node %s is %s, want %s" % [nm, n.get_class() if n != null else "missing", "MultiMeshInstance3D" if want_mm else "MeshInstance3D"])
			if n != null and kind_ok:
				var mesh: Mesh = n.multimesh.mesh if want_mm and n.multimesh != null else (n.mesh if not want_mm else null)
				var surfaces: int = mesh.get_surface_count() if mesh != null else -1
				_row("R7", surfaces == 1, "R7 node %s holds %d surfaces, want exactly 1 (one draw)" % [nm, surfaces])
				if nm.begins_with("StarLayer") and mesh != null and surfaces == 1:
					_row("R7", mesh is ArrayMesh and mesh.surface_get_primitive_type(0) == Mesh.PRIMITIVE_POINTS, "R7 %s is not an ArrayMesh of PRIMITIVE_POINTS" % nm)
		var all: Array = []
		_collect(rig6, all)
		var others: Array = []
		for c in all:
			if (c is MeshInstance3D or c is MultiMeshInstance3D) and not (String(c.name) in SIX):
				others.append(c)
		var kinds: Array = []
		for c in others:
			kinds.append("%s:%s" % [c.name, (c.mesh.get_class() if c is MeshInstance3D and c.mesh != null else c.get_class())])
		var grid := 0
		var sph := 0
		var qd := 0
		for c in others:
			if String(c.name) == "GridPlane":
				grid += 1
			elif c is MeshInstance3D and c.mesh is SphereMesh:
				sph += 1
			elif c is MeshInstance3D and c.mesh is QuadMesh:
				qd += 1
		_row("R7", others.size() == 3 and grid == 1 and sph == 1 and qd == 1, "R7 other MeshInstance3D / MultiMeshInstance3D under the rig: %s, want exactly the central point, halo and GridPlane" % str(kinds))
		_row("R7", rig6.has_method("qa_inventory") and int(rig6.qa_inventory().get("added_draws", -1)) == 6, "R7 qa_inventory()[\"added_draws\"] is %s, want 6" % str(rig6.qa_inventory().get("added_draws", "no key") if rig6.has_method("qa_inventory") else "no qa_inventory"))
		var gp := 0
		for c in all:
			if c is GPUParticles3D:
				gp += 1
		_row("R7", gp == 14, "R7 GPUParticles3D under the rig: %d, want 14 (12 rings, RadialStreams, central glow; the Starfield and AmbientDust emitters are gone)" % gp)

	# R8: the tell "layers moving in lock-step": for two camera positions a displacement apart, the mean angular shift of
	# the same stars is strictly larger for layer 0 than 1, than 2, than 3 (g3 (a): world-fixed layers).
	if _pos.size() == LAYERS:
		for start in LOCK_STARTS:
			var shifts: Array = []
			for i in LAYERS:
				var tot := 0.0
				for p in _pos[i]:
					tot += (p - start).angle_to(p - (start + LOCK_DISPLACEMENT))
				shifts.append(tot / float(maxi(_pos[i].size(), 1)))
			var ordered: bool = shifts.size() == 4 and shifts[0] > shifts[1] and shifts[1] > shifts[2] and shifts[2] > shifts[3]
			_row("R8", ordered, "R8 mean angular shift of the same stars for a camera step of %s from %s is %s per layer 0..3, not strictly falling (layers moving in lock-step)" % [str(LOCK_DISPLACEMENT), str(start), str(shifts)])
	else:
		_row("R8", false, "R8 no layer positions to measure parallax (layer_star_positions missing)")

	# R9: the tell "shimmering sub-pixel stars": "star size grows with depth so stars stay 1 to 3 pixels".
	var have9 := _need("R9", ["STAR_PX_MIN", "STAR_PX_MAX"], ["star_pixel_size", "layer_radius"])
	if have9:
		_row("R9", is_equal_approx(float(_consts["STAR_PX_MIN"]), 1.0) and is_equal_approx(float(_consts["STAR_PX_MAX"]), 3.0), "R9 STAR_PX_MIN %s STAR_PX_MAX %s, want 1.0 and 3.0 (Step 5)" % [str(_consts["STAR_PX_MIN"]), str(_consts["STAR_PX_MAX"])])
		var cams9: Array = [Vector3.ZERO]
		for ax in [Vector3.RIGHT, Vector3.LEFT, Vector3.UP, Vector3.DOWN, Vector3.BACK, Vector3.FORWARD]:
			cams9.append(ax * reach)
		for i in LAYERS:
			if not _pos.has(i):
				_row("R9", false, "R9 layer %d has no star positions to measure distances" % i)
				continue
			var dmin := INF
			var dmax := 0.0
			for c in cams9:
				for p in _pos[i]:
					var d: float = p.distance_to(c)
					dmin = minf(dmin, d)
					dmax = maxf(dmax, d)
			dmin = maxf(dmin, 0.001)
			var bad: Array = []
			var ds: Array = [dmin, dmax, float(_sc("layer_radius", [i]))]
			for s in SWEEP_STEPS + 1:
				ds.append(dmin * pow(dmax / dmin, float(s) / float(SWEEP_STEPS)))
			for d in ds:
				var px: float = float(_sc("star_pixel_size", [i, d, VIEWPORT_H, FOV_DEG]))
				if not (px >= 1.0 and px <= 3.0):
					bad.append("%.3f px at d=%.1f" % [px, d])
			_row("R9", bad.size() == 0, "R9 layer %d star_pixel_size outside [1, 3] px for %d of %d distances in [%.1f, %.1f]: %s" % [i, bad.size(), ds.size(), dmin, dmax, str(bad.slice(0, 3))])
		for i in LAYERS:
			var n = rig6.get_node_or_null("StarLayer%d" % i) if rig6 != null else null
			var mat := _material_of(n) if n != null else null
			var ok_mat: bool = mat is ShaderMaterial
			_row("R9", ok_mat and String(mat.shader.resource_path) == SHADER_DIR + "backdrop_stars.gdshader", "R9 StarLayer%d material is not a ShaderMaterial of %sbackdrop_stars.gdshader (got '%s')" % [i, SHADER_DIR, _shader_path(n) if n != null else "no node"])
			if ok_mat:
				var pmin = mat.get_shader_parameter("px_min")
				var pmax = mat.get_shader_parameter("px_max")
				_row("R9", pmin != null and pmax != null and is_equal_approx(float(pmin), 1.0) and is_equal_approx(float(pmax), 3.0), "R9 StarLayer%d uniforms px_min %s px_max %s, want 1.0 and 3.0" % [i, str(pmin), str(pmax)])
				_row("R9", not mat.shader.code.contains("TIME"), "R9 StarLayer%d shader contains TIME (stars are static, no shimmer)" % i)

	# R10: "a very dim, low-contrast, direction-only background, computed once, no animation" (DRAFT-b25-wash).
	# The ceiling (0.012 above the background) and the contrast cap (0.02) bound the wash from above only. The floor row
	# proves the wash never darkens the background (no channel below it in any sampled direction: the wash is blend_add, it
	# only brightens), and the variation row proves it is not dead (the spread over the sampled directions is above 0, no
	# new number), so a constant or darkening wash cannot pass (Architect ruling 2026-10-20, item 3).
	var have10 := _need("R10", [], ["wash_colour"])
	if have10:
		var bad_level := 0
		var unstable := 0
		var cols := _wash_cols(func(dir: Vector3) -> Color: return _sc("wash_colour", [dir]))
		var again := _wash_cols(func(dir: Vector3) -> Color: return _sc("wash_colour", [dir]))
		for k in cols.size():
			if cols[k] != again[k]:
				unstable += 1
			for ch in 3:
				if cols[k][ch] - BG[ch] > WASH_CEILING + FLOAT_EPS:
					bad_level += 1
		_row("R10", unstable == 0, "R10 wash_colour is not a function of the direction alone: %d of %d directions gave two colours" % [unstable, WASH_DIRS])
		_row("R10", bad_level == 0, "R10 %d channel values exceed the background by more than %s (DRAFT-b25-wash)" % [bad_level, str(WASH_CEILING)])
		var sp := _spread(cols)
		_row("R10", sp.x <= WASH_CONTRAST + FLOAT_EPS and sp.y <= WASH_CONTRAST + FLOAT_EPS and sp.z <= WASH_CONTRAST + FLOAT_EPS, "R10 wash spread over %d hashed directions is %s per channel, want at most %s (DRAFT-b25-wash)" % [WASH_DIRS, str(sp), str(WASH_CONTRAST)])
		_row("R10", _wash_floor_ok(cols), "R10 wash floor: some channel of wash_colour is below the background in a sampled direction (the wash only brightens, blend_add)")
		_row("R10", _wash_varies(cols), "R10 wash does not vary with the view direction: spread %s over %d hashed directions, want above 0 in some channel (a dead wash)" % [str(sp), WASH_DIRS])
	if rig6 != null:
		var w = rig6.get_node_or_null("Wash")
		_row("R10", w is MeshInstance3D, "R10 no MeshInstance3D named Wash under the rig")
		if w != null:
			var wc := _shader_code(w)
			_row("R10", wc != "" and not wc.contains("TIME"), "R10 backdrop_wash.gdshader missing on Wash, or it contains TIME (no animation)")
			_row("R10", _shader_path(w) == SHADER_DIR + "backdrop_wash.gdshader", "R10 Wash shader is '%s', want %sbackdrop_wash.gdshader" % [_shader_path(w), SHADER_DIR])

	# R12: qa_inventory() reports the live counts (g5 item c): wash true, four layers with radii and star counts, dust motes
	# and box, far, added_draws; qa_state()["backdrop"] is that inventory.
	if rig6 != null and rig6.has_method("qa_inventory") and cam != null:
		var inv: Dictionary = rig6.qa_inventory()
		_row("R12", bool(inv.get("wash", false)), "R12 qa_inventory wash is %s, want true" % str(inv.get("wash", "no key")))
		var layers: Array = inv.get("star_layers", [])
		_row("R12", layers.size() == 4, "R12 qa_inventory star_layers has %d entries, want 4" % layers.size())
		for i in mini(layers.size(), 4):
			var arrs12 := _star_arrays(rig6, i)
			var verts: int = arrs12[Mesh.ARRAY_VERTEX].size() if arrs12.size() > 0 and arrs12[Mesh.ARRAY_VERTEX] != null else -1
			_row("R12", int(layers[i].get("stars", -2)) == verts and verts > 0, "R12 qa_inventory star_layers[%d].stars is %s, the StarLayer%d mesh holds %d vertices" % [i, str(layers[i].get("stars")), i, verts])
			if _pos.has(i) and arrs12.size() > 0 and arrs12[Mesh.ARRAY_VERTEX] != null:
				_row("R12", arrs12[Mesh.ARRAY_VERTEX] == _pos[i], "R12 StarLayer%d vertices differ from layer_star_positions(%d, 0) (the mesh must hold the world-fixed positions)" % [i, i])
			if have1 and radii.size() == 4:
				_row("R12", is_equal_approx(float(layers[i].get("radius", -1.0)), float(radii[i])), "R12 qa_inventory star_layers[%d].radius is %s, layer_radius is %s" % [i, str(layers[i].get("radius")), str(radii[i])])
		var dust: Dictionary = inv.get("dust", {})
		var dm = rig6.get_node_or_null("CameraDust")
		_row("R12", dm is MultiMeshInstance3D and dm.multimesh != null and int(dust.get("motes", -1)) == dm.multimesh.instance_count, "R12 qa_inventory dust.motes is %s, the CameraDust MultiMesh holds %s" % [str(dust.get("motes")), str(dm.multimesh.instance_count if dm is MultiMeshInstance3D and dm.multimesh != null else "no node")])
		if have5:
			_row("R12", is_equal_approx(float(dust.get("box", -1.0)), float(_consts["DUST_BOX"])), "R12 qa_inventory dust.box is %s, DUST_BOX is %s" % [str(dust.get("box")), str(_consts["DUST_BOX"])])
		_row("R12", is_equal_approx(float(inv.get("far", -1.0)), cam.far), "R12 qa_inventory far is %s, the live Camera3D.far is %s" % [str(inv.get("far")), str(cam.far)])
		_row("R12", int(inv.get("added_draws", -1)) == 6, "R12 qa_inventory added_draws is %s, want 6" % str(inv.get("added_draws")))
		var qs: Dictionary = _view.qa_state()
		_row("R12", qs.has("backdrop") and qs["backdrop"] == inv, "R12 qa_state()[\"backdrop\"] is %s, want rig.qa_inventory() (scenes/galaxy/galaxy_view.gd qa_state, next to \"ambient_rig\")" % str(qs.get("backdrop", "no key")))
	else:
		_row("R12", false, "R12 the AmbientRig has no qa_inventory()")

	await _free(_view)
