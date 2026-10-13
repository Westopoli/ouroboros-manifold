extends SceneTree
# test-timeout: 20000

# Piece VG-B23b-dotcolour (docs/northstar/plans/2026-10-07-visible-game-spec.md :306, Rev 12d; lane B, after B23).
# Proves Westley's ruling 2026-10-12 (pixel-test frames side by side):
#   "I like the coloring of the MAIN-passing better, but other than that they both look exactly the same to me.
#    My eyes approve, pending the color change."
# Spec :306, Detector: "test_galaxy_pixels.py::test_c2_5_owner_colours_reach_the_pixels green ... with its thresholds
#   untouched" (the renderer that decides it is the DEFAULT one, Architect 2026-10-13).
# Spec :306, Parity: "the dot material and vertex-colour path as on origin/main before B23 (the srgb flag and the
#   prototype's dot transparency are reverted on the dots only); every other B23 value stays."
# Findings and ledger rows: FINDING-dot-colour-pixels (the pixel test is red on B23: the owner colours do not reach the
# pixels), TD-VG-B-15 (tests/test_vg_b_b23.gd lines 311-312 re-pinned to main's dot values).
# The frame check is tests/qa/desktop/test_galaxy_pixels.py::test_c2_5_owner_colours_reach_the_pixels; this file proves
# the material the frame is drawn with, the half of the contract a headless run can read. No threshold appears here.
#
# Cases, in order: CONTROL (the view instantiates on the 80-region fixture); POSITIVE CONTROL (the predicate tells main's
# dot material from B23's); LIVE (World/Points carries main's dot material; red on a tree with B23's); INVENTORY (one
# region colour per region, one distinct colour per distinct owner, galaxy_view.gd qa_state contract).
# Headless-safe: no MultiMesh transform is read, the material is read as a resource.

const SCENE_PATH := "res://scenes/galaxy/galaxy_view.tscn"
const FIXTURE_PATH := "res://tests/transport/fixtures/snapshot_seed1_tick10.json"

var _pass := 0
var _fail := 0
var _msgs: Array[String] = []


func _initialize() -> void:
	await _run()
	print("\n=== VG-B23b dot colour: PASS %d FAIL %d ===" % [_pass, _fail])
	print("PASS: %d  FAIL: %d" % [_pass, _fail])   # the summary line scripts/run_godot_tests.sh reads
	for m in _msgs:
		print("  - " + m)
	print("=== %s ===" % ("RED" if _fail > 0 else "GREEN"))
	quit(1 if _fail > 0 else 0)


func _check(c: bool, msg: String) -> void:
	if c:
		_pass += 1
	else:
		_fail += 1
		_msgs.append(msg)


func _frames(n: int) -> void:
	for _i in range(n):
		await process_frame


func _new_view(snap: Dictionary) -> Node:
	var v: Node = (load(SCENE_PATH) as PackedScene).instantiate()
	v.driven = true
	get_root().add_child(v)
	await _frames(2)
	v.set_snapshot(snap)
	await _frames(2)
	return v


# Main's dot material (galaxy_view.gd at 33e3bc2f^, _build_materials): unshaded, vertex colour as albedo, vertex
# colour read as sRGB, transparency left at its default (DISABLED).
func _is_mains_dot_material(mat) -> bool:
	return mat is StandardMaterial3D \
		and mat.shading_mode == BaseMaterial3D.SHADING_MODE_UNSHADED \
		and mat.vertex_color_use_as_albedo \
		and mat.vertex_color_is_srgb \
		and mat.transparency == BaseMaterial3D.TRANSPARENCY_DISABLED


func _key(c: Array) -> String:
	return "%.4f,%.4f,%.4f,%.4f" % [float(c[0]), float(c[1]), float(c[2]), float(c[3])]


func _run() -> void:
	var f := FileAccess.open(FIXTURE_PATH, FileAccess.READ)
	var snap = JSON.parse_string(f.get_as_text()) if f != null else null
	_check(snap is Dictionary, "CONTROL: fixture snapshot_seed1_tick10.json is not readable")
	if not (snap is Dictionary):
		return
	var regions: Array = snap.get("regions", [])
	var owners := {}
	for r in regions:
		owners[int(r.get("owner", -1))] = true

	# ---- CONTROL: the scene instantiates the way tests/test_vg_b_b23.gd:127-136 does ----
	var view: Node = await _new_view(snap)
	var st: Dictionary = view.qa_state()
	print("PREMISE regions %d owners %d qa_state keys %s system_count %s" % [regions.size(), owners.size(), str(st.keys()), str(st.get("system_count"))])
	_check(int(st.get("system_count", -1)) == regions.size(), "CONTROL: qa_state.system_count %s, want the fixture region count %d" % [str(st.get("system_count")), regions.size()])

	# ---- POSITIVE CONTROL: the predicate is true for main's values and false for B23's ----
	var mains := StandardMaterial3D.new()
	mains.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	mains.vertex_color_use_as_albedo = true
	mains.vertex_color_is_srgb = true
	var b23 := StandardMaterial3D.new()
	b23.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	b23.vertex_color_use_as_albedo = true
	b23.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	b23.vertex_color_is_srgb = false
	_check(_is_mains_dot_material(mains), "POSITIVE CONTROL: the predicate rejects a material built with main's values")
	_check(not _is_mains_dot_material(b23), "POSITIVE CONTROL: the predicate accepts a material built with B23's values (transparency ALPHA, vertex_color_is_srgb false)")

	# ---- LIVE: World/Points carries main's dot material ----
	var points: MultiMeshInstance3D = view.get_node_or_null("World/Points")
	var mat = points.material_override if points != null else null
	_check(mat is StandardMaterial3D, "LIVE: World/Points material_override is not a StandardMaterial3D")
	if mat is StandardMaterial3D:
		print("PREMISE live dot material: shading %d vertex_color_use_as_albedo %s vertex_color_is_srgb %s transparency %d" % [mat.shading_mode, str(mat.vertex_color_use_as_albedo), str(mat.vertex_color_is_srgb), mat.transparency])
		_check(mat.shading_mode == BaseMaterial3D.SHADING_MODE_UNSHADED, "LIVE: dot material shading_mode %d, want UNSHADED %d" % [mat.shading_mode, BaseMaterial3D.SHADING_MODE_UNSHADED])
		_check(mat.vertex_color_use_as_albedo, "LIVE: dot material vertex_color_use_as_albedo false, want true")
		_check(mat.vertex_color_is_srgb, "LIVE: dot material vertex_color_is_srgb false, want true (main before B23, spec :306)")
		_check(mat.transparency == BaseMaterial3D.TRANSPARENCY_DISABLED, "LIVE: dot material transparency %d, want DISABLED %d (main before B23, spec :306)" % [mat.transparency, BaseMaterial3D.TRANSPARENCY_DISABLED])
		_check(_is_mains_dot_material(mat), "LIVE: the dot material is not main's dot material (predicate _is_mains_dot_material false)")

	# ---- INVENTORY: galaxy_view.gd:455-465 contract, region_colours[i] == owner_colours[owner_of(i)], distinct owners distinct colours ----
	var rc: Dictionary = st.get("region_colours", {})
	_check(rc.size() == regions.size(), "INVENTORY: qa_state.region_colours holds %d entries, want one per region (%d)" % [rc.size(), regions.size()])
	var distinct := {}
	for k in rc:
		distinct[_key(rc[k])] = true
	_check(distinct.size() == owners.size(), "INVENTORY: %d distinct region colours, want one per distinct owner (%d)" % [distinct.size(), owners.size()])

	view.queue_free()
	await _frames(1)
