extends SceneTree

# VG-D-VIEW, the first space look (docs/northstar/plans/2026-10-13-d-view-spec.md rev 3; scout report
# ~/Projects/om-push/scratch/drafts-2026-10-12/dview-scout-report.md, origin/main 7080e06a). Fenced: builders never edit this file.
# Story S-246. Unit under test by prefix: _test_sheets_* = res://scenes/space3d/space_sheets.gd (SpaceSheets, built directly),
# _test_rings_* = res://scenes/space3d/space_rings.gd (SpaceRings, built directly), _test_view_* = res://scenes/space3d/space_view.tscn
# (SpaceView mounted in the tree: set_field with the fixture, set_frame with a fixture frame, follow_mouse = false, cursor_px set by
# the test), _test_host_* = tactical_view.tscn hosting it (gap g1, live pipe).
#
# THIS FILE IS RED because scenes/space3d/space_view.tscn (and space_sheets.gd, space_rings.gd, shaders/sheet_tube.gdshader) do not
# exist on origin/main. Every case loads its script or scene with load() and asserts it is not null, so the red line is a readable
# assertion ("missing ...: the piece is not built"), never a parse error. The "(control)" checks pass on main and prove the harness.
#
# Rules proved, word for word (docs/bible/epics/E-17-map-generation.md :391-394):
#   R-246-01: "Given a space-era mission in the beta, When it is set up, Then the map has a generated field: each of the five layers is
#     an open-or-blocked sheet (E-01 R-001-04), like ice over open water, and the generator is ported into the simulation as the land one
#     was (Westley, 2026-10-07; Q-STAGE3-03)."
#   R-246-02: "Given the space kit, When it is drawn, Then it follows the approved prototype with one polish: the blocked space is filled
#     across layers with real placeholder meteors instead of one plane per layer, and the layers are visibly separated."
#     (The meteors are the follow-up piece VG-D-METEORS after the verdict; only "the layers are visibly separated" and "follows the
#     approved prototype" are proved here: the sheet y, the slab shape, the dimming.)
#   R-246-03: "Given a mission, When the simulation sends the map, Then it sends the cell masks and the plate polygons once per mission,
#     and the client draws the layers as stacked 3D sheets from them (Q-166-06, Q-166-07)."
#   R-246-04: "Given a unit below an upper layer that hides it from the camera, When the player looks, Then a simple vision tube lets the
#     player see through the covering layers around the cursor or selection, with a small effect that says so (Q-S3-01); the layer-visibility
#     system of the layers prototype (`scenes/mockups/layers/`: with a unit sent to another layer, one circle moves with the unit and a second
#     sits at the exact height of the layer it is moving to) is the one the spec follows (Q-S3-02)."
#   Q-S3-01 (a) (docs/northstar/ambiguity_register.md:38, candidate and ruling): "(a) occluding geometry on layers between the camera and
#     the focus layer turns transparent inside a tube around the cursor or selection, with an effect that says so" ... closed: "(a), a simple
#     vision tube for now."
#   Q-246-01 (a) (register :45): "(a) the prototype's 1,000 wu as a draft, judged on the first in-game shot" ... closed (a) ...
#     "DRAFT-space-layer-gap = 1,000 wu (field_map_space.gd:22)."
#   Q-S3-02 (register :503): "The layers mockup (`scenes/mockups/layers/`), identified from Westley's description. Westley, 2026-10-07,
#     verbatim: "... When I selected a layer it wasn't on, there was two circles: one circle moving with the moving unit, and another circle on
#     the exact Y height of the layer it was moving to.""
#   Westley 2026-10-13 (as the d-view spec quotes it): "the space kit (pass 6) approval is conditional on the vision tube and on layer
#     indicators showing which layer each unit is on".
#   R-088-01 (one body per type for now) is NOT tested: "every type is one body for now (R-088-01 waits for DRAFT-raider-radius)".
# Spec lines quoted beside the cases that prove them are from docs/northstar/plans/2026-10-13-d-view-spec.md (the "Field", "Units",
# "Layer indicators", "Vision tube", "Camera", "qa_state" bullets) and the INTERFACE block of the VG-D-VIEW brief (the API names).
#
# Gap rulings used (Architect 2026-10-14 FINAL): g1 OPT-IN hosting (OM_SPACE_VIEW=1, host after set_terrain in _load_live); g2 camera
# height 5,400 (the PLAY zooms through the rig API until the rig reports >= 5,400; no rig change); g3 (a) the 2D bodies hidden through
# unit_node(id) (Body and LayerRing), UnitSquads.visible = false. Null actions standing (not ruled, marked "d-view spec rev 1, gap N null
# action, Architect may veto on the shot"): g4 the rig's own pitch is reported, never asserted; g5 derived floors, unit y overridden after
# Units3D.set_units; g6 the client records t0 at the first transit frame; g7 focus_layer() as is; g8 engine layer numbers; g9 frame_ms
# (not asserted); g10 ring y = sheet top + 2.0 (sheet top = sheet y + thickness 60), cell squares 100 x 100 x 60, fade when sheet y > focus_y + 0.5 * gap.
#
# DISPLAY: this file needs a real renderer. The headless dummy renderer stores no MultiMesh instance data (get_instance_transform returns
# zeros), so the cell-square case could not read the squares under scripts/run_godot_tests.sh once the piece is built. Run it as
#   timeout 1800 xvfb-run -a -s '-screen 0 1920x1080x24' godot.real --path . --resolution 1920x1080 -s tests/test_vg_d_view.gd
# (the default renderer; the hosting case at the end mounts tactical_view.tscn on the live pipe, so the pipe must be built).
# Validated 2026-10-13 against a throwaway reference implementation of the INTERFACE (not committed): 264 PASS, with only the six hosting
# lines red until tactical_view.gd hosts the view; the red-on-main run below is the same file on the tree without scenes/space3d.
#
# NOT covered by this file (said so, no case written, nothing invented):
#   - Frame time (the play measures it; FRAME_BUDGET_MS is only checked as a constant).
#   - The fragment alpha TUBE_ALPHA and the rim pulse 0.6 to 1.0 over 1.5 s (shader pixels: needs a render; the play's shot judges them).
#   - Ring width scaling with camera height / DRAFT-ring-px (spec "Layer indicators" bullet) against the interface's RING_WIDTH_WU 6.0: the
#     two statements disagree and no ring-width accessor is in the INTERFACE.
#   - The mass slab colour (#4a4038): no accessor in the INTERFACE.
#   - Walls, tunnels, crossings, meteors (not drawn: "no walls, no tunnels, no frames (the sim sends none)").

const SPACE_VIEW_TSCN := "res://scenes/space3d/space_view.tscn"
const SPACE_VIEW_GD := "res://scenes/space3d/space_view.gd"
const SPACE_SHEETS_GD := "res://scenes/space3d/space_sheets.gd"
const SPACE_RINGS_GD := "res://scenes/space3d/space_rings.gd"
const SHADER_PATH := "res://scenes/space3d/shaders/sheet_tube.gdshader"
const MOCKUP_GD := "res://scenes/mockups/landscape/field_map_space.gd"
const LAYER_VIEW_GD := "res://scenes/tactical_c/layer_view.gd"
const UNITS_GD := "res://scenes/ground3d/ground_units.gd"
const KIT_JSON := "res://scenes/mockups/landscape/kits/space.json"
const TACTICAL_TSCN := "res://scenes/tactical_c/tactical_view.tscn"

const DIM := 240
const LAYERS := 5
const CELL_WU := 100.0
# Q-246-01 (a), DRAFT-space-layer-gap, and the kit-mode spec P2.5 "darken the other layers by 55 percent" (DRAFT-sheet-dim).
const GAP_WU := 1000.0
# Architect FINAL ruling 2026-10-14 (d-view spec rev 3, Units bullet): unit y = sheet top + 150, sheet top = L * gap + sheet thickness
# (plate 60, rubble 30); 150 = Units3D FLYER_CLEARANCE_WU (ground_units.gd:11). DRAFT-space-unit-lift (40) is STRUCK. The fixture sheets
# are plate sheets (60), so a layer-2 unit is at 2,210.
const PLATE_THICKNESS_WU := 60.0
const SHEET_DIM := 0.55
const TUBE_RADIUS_WU := 1500.0
# G2 ruling (Architect FINAL): DRAFT-space-cam-height 5,400.
const PLAY_HEIGHT_WU := 5400.0
# One display pixel: the slack allowed between a projected point and a pixel (the projection is exact double arithmetic).
const ONE_PX := 1.0
# Float slack for values the spec gives exactly (a double compared with a double after one lerp or one subtraction).
const EPS := 0.01
const CURSOR_CENTRE := Vector2(960.0, 540.0)
const CURSOR_OFF := Vector2(700.0, 600.0)

var _pass_count := 0
var _fail_count := 0
var _fail_msgs: Array[String] = []
var _completed := false


func _initialize() -> void:
	await _run_tests()
	_assert(_completed, "the checks did not run to the end (a script error aborted them)")
	print("\n=== VG-D-VIEW Test Results ===")
	print("PASS: %d  FAIL: %d" % [_pass_count, _fail_count])
	if _fail_count > 0:
		print("Failures:")
		for msg in _fail_msgs:
			print("  - " + msg)
		print("=== RED ===\n")
		quit(1)
	else:
		print("=== GREEN ===\n")
		quit(0)


func _assert(cond: bool, msg: String) -> void:
	if cond:
		_pass_count += 1
		print("PASS: " + msg.get_slice(": ", 0))  # the message words the failure; a pass prints only its label
	else:
		_fail_count += 1
		var st := get_stack()
		var where := "test_vg_d_view.gd"
		for i in range(1, st.size()):
			if i == 1 or String(st[i]["function"]).begins_with("_test_"):
				where = "%s:%d (%s)" % [String(st[i]["source"]).get_file(), int(st[i]["line"]), String(st[i]["function"])]
				if String(st[i]["function"]).begins_with("_test_"):
					break
		_fail_msgs.append("%s %s" % [where, msg])
		print("FAIL: %s %s" % [where, msg])


func _run_tests() -> void:
	OS.set_environment("OM_SAVE_DIR", OS.get_user_data_dir().path_join("vgdview_saves_%d" % Time.get_ticks_usec()))
	OS.unset_environment("OM_SPACE_VIEW")
	_test_controls()
	_test_view_constants_and_parity()
	await _test_sheets_y_and_counts()
	await _test_sheets_cell_squares_and_coverage()
	await _test_sheets_slab_shape_parity()
	await _test_sheets_dim()
	await _test_sheets_tube()
	await _test_sheets_one_material()
	await _test_rings_geometry_and_colours()
	await _test_rings_transit_and_count()
	await _test_view_inventory()
	await _test_view_units_and_rings()
	await _test_view_transit()
	await _test_view_camera()
	await _test_view_projection_and_picking()
	await _test_view_tube()
	await _test_view_tube_inactive()
	await _test_view_tube_material()
	await _test_host_control_and_wiring()
	_completed = true


# -- fixture (a COPY of the K-d fixture in tests/test_c_bridge_vg_d.gd, FAKE_SRC fake_masks / fake_polys) ----------------------------

# fake_masks: layer k byte i = (i * 7 + k) & 0xFF over dim * dim / 8 = 7200 bytes.
func _fake_masks() -> Array:
	var out := []
	for k in range(LAYERS):
		var b := PackedByteArray()
		b.resize(DIM * DIM / 8)
		for i in range(b.size()):
			b[i] = (i * 7 + k) & 0xFF
		out.append(b)
	return out


# fake_polys: [[0, 0, [0,0, 100,0, 100,100]], [4, 2, [200,200, 300,200, 300,350.5, 200,300]], [2, 1, [10,10, 20,10, 20,20]]]
# as {layer, kind, points} (the bridge.space_field() shape, autoload/c_bridge.gd:646-672).
func _fake_polys() -> Array:
	return [
		{"layer": 0, "kind": 0, "points": PackedVector2Array([Vector2(0, 0), Vector2(100, 0), Vector2(100, 100)])},
		{"layer": 4, "kind": 2, "points": PackedVector2Array([Vector2(200, 200), Vector2(300, 200), Vector2(300, 350.5), Vector2(200, 300)])},
		{"layer": 2, "kind": 1, "points": PackedVector2Array([Vector2(10, 10), Vector2(20, 10), Vector2(20, 20)])},
	]


func _fixture_field() -> Dictionary:
	return {"cells_w": DIM, "cells_h": DIM, "layers": LAYERS, "masks": _fake_masks(), "polys": _fake_polys()}


# The K-d fixture plus ONE more plate on layer 1 (a 500 x 500 wu square on cells 10..14, centres 1050..1450, no centre on an edge): the
# K-d copy alone covers no blocked cell (premise dumped: covered = 0 on every layer), so the "covered cells get no square" half needs
# this one extra poly. The masks and the other three polys are unchanged.
func _coverage_field() -> Dictionary:
	var f := _fixture_field()
	var polys: Array = f["polys"]
	polys.append({"layer": 1, "kind": 0, "points": PackedVector2Array([Vector2(1000, 1000), Vector2(1500, 1000), Vector2(1500, 1500), Vector2(1000, 1500)])})
	f["polys"] = polys
	return f


# Independent popcount: a plain bit loop over the bytes (no lookup table, nothing shared with the builder).
func _popcount(b: PackedByteArray) -> int:
	var n := 0
	for byte in b:
		var v: int = byte
		for bit in range(8):
			if (v >> bit) & 1 == 1:
				n += 1
	return n


func _blocked(mask: PackedByteArray, cx: int, cy: int) -> bool:
	var i := cy * DIM + cx
	return (int(mask[i >> 3]) >> (i & 7)) & 1 == 1


# The sim's cell rule (csrc/space_raster.c:44-76 sr_fill_polygon, "even-odd scanline at each cell row centre"): a cell is covered when
# its centre ((cx + .5) * 100, (cy + .5) * 100) lies inside the polygon by the even-odd scanline at y = centre y, edge crossings taken
# when (ay <= y && by > y) || (by <= y && ay > y), the cell inside when xs[p] <= x <= xs[p + 1] (inclusive, as the C code). The d-view
# spec "Field" bullet: "Cells follow the sim: a fill square is centred at `((cx + 0.5)·100, (cy + 0.5)·100)`, stride 240, mask index
# `cy·240 + cx` (`csrc/space_raster.c`)".
func _in_poly(pts: PackedVector2Array, x: float, y: float) -> bool:
	var xs: Array = []
	var n := pts.size()
	for e in range(n):
		var a := pts[e]
		var b := pts[(e + 1) % n]
		if (a.y <= y and b.y > y) or (b.y <= y and a.y > y):
			xs.append(a.x + (y - a.y) / (b.y - a.y) * (b.x - a.x))
	xs.sort()
	var p := 0
	while p + 1 < xs.size():
		if x >= float(xs[p]) and x <= float(xs[p + 1]):
			return true
		p += 2
	return false


# Blocked cells of layer k whose centre is inside a poly of layer k: {index: true}.
func _covered_blocked(field: Dictionary, k: int) -> Dictionary:
	var out := {}
	var mask: PackedByteArray = field["masks"][k]
	for poly in field["polys"]:
		if int(poly["layer"]) != k:
			continue
		var pts: PackedVector2Array = poly["points"]
		var lo := Vector2(INF, INF)
		var hi := Vector2(-INF, -INF)
		for p in pts:
			lo = Vector2(minf(lo.x, p.x), minf(lo.y, p.y))
			hi = Vector2(maxf(hi.x, p.x), maxf(hi.y, p.y))
		for cy in range(maxi(int(lo.y / CELL_WU) - 1, 0), mini(int(hi.y / CELL_WU) + 2, DIM)):
			for cx in range(maxi(int(lo.x / CELL_WU) - 1, 0), mini(int(hi.x / CELL_WU) + 2, DIM)):
				if _blocked(mask, cx, cy) and _in_poly(pts, (cx + 0.5) * CELL_WU, (cy + 0.5) * CELL_WU):
					out[cy * DIM + cx] = true
	return out


func _poly_count(field: Dictionary, k: int) -> int:
	var n := 0
	for poly in field["polys"]:
		if int(poly["layer"]) == k:
			n += 1
	return n


# -- loading and tree helpers ------------------------------------------------------------------------------------------------------

func _load_script(path: String) -> GDScript:
	var s = load(path) if ResourceLoader.exists(path) else null
	_assert(s is GDScript, "missing script %s: the piece is not built (VG-D-VIEW)" % path)
	return s as GDScript


func _load_scene(path: String) -> PackedScene:
	var s = load(path) if ResourceLoader.exists(path) else null
	_assert(s is PackedScene, "missing scene %s: the piece is not built (VG-D-VIEW)" % path)
	return s as PackedScene


func _constants(path: String) -> Dictionary:
	var s = load(path) if ResourceLoader.exists(path) else null
	if s is GDScript:
		return (s as GDScript).get_script_constant_map()
	return {}


func _layer_colours() -> Array:
	return _constants(LAYER_VIEW_GD).get("LAYER_COLOURS", [])


func _kit() -> Dictionary:
	var f := FileAccess.open(KIT_JSON, FileAccess.READ)
	if f == null:
		return {}
	var d = JSON.parse_string(f.get_as_text())
	return d if d is Dictionary else {}


func _kit_colour(k: int) -> Color:
	return Color.html(str(_kit().get("layers", [])[k]))


func _all_nodes(n: Node, out: Array) -> Array:
	out.append(n)
	for c in n.get_children():
		_all_nodes(c, out)
	return out


func _find_by_script(root_node: Node, script: GDScript) -> Node:
	for n in _all_nodes(root_node, []):
		if n.get_script() == script:
			return n
	return null


func _new_sheets(field: Dictionary):
	var s := _load_script(SPACE_SHEETS_GD)
	if s == null:
		return null
	var sheets = s.new()
	root.add_child(sheets)
	await process_frame
	sheets.build(field)
	await process_frame
	return sheets


func _new_rings():
	var s := _load_script(SPACE_RINGS_GD)
	if s == null:
		return null
	var rings = s.new()
	root.add_child(rings)
	await process_frame
	return rings


func _drop(n: Node) -> void:
	if n != null:
		n.queue_free()
		await process_frame


func _ints(a: Array) -> Array:
	var out := []
	for v in a:
		out.append(int(v))
	out.sort()
	return out


func _near(a: Color, b: Color) -> bool:
	return a.is_equal_approx(b)


# -- fixture frame for the view ----------------------------------------------------------------------------------------------------

func _unit(id: int, faction: int, x: float, y: float, layer: int, extra: Dictionary = {}) -> Dictionary:
	var u := {"id": id, "faction": faction, "type": 0, "tier": 0, "x": x, "y": y, "hp": 100, "layer": layer, "facing": 0.0, "target": -1, "state": 0}
	u.merge(extra, true)
	return u


# A space-era tactical frame: the live probe's nodes (scout report 1.: "objective kind 0 (11950,11950), two kind 7 anchors (11950,150) and
# (11950,23850) - the player's army stands at the map EDGE"). Local faction 0; `visible` is {"0": [ids of enemies the player sees]}.
func _frame(tick: int, units: Array, seen: Array = []) -> Dictionary:
	return {
		"tick": tick,
		"player_faction": 0,
		"units": units,
		"visible": {"0": seen},
		"map": {
			"nodes": [
				{"i": 0, "kind": 0, "x": 11950.0, "y": 11950.0},
				{"i": 1, "kind": 7, "x": 11950.0, "y": 150.0},
				{"i": 2, "kind": 7, "x": 11950.0, "y": 23850.0},
			],
			"cover": [],
			"obstacles": [],
		},
	}


# Five own units, one per layer 0..4, around the near anchor (11950, 150); enemy 11 (visible) and enemy 12 (not visible) at the far anchor.
func _army() -> Array:
	return [
		_unit(1, 0, 11900.0, 400.0, 0),
		_unit(2, 0, 12000.0, 420.0, 1),
		_unit(3, 0, 11950.0, 450.0, 2),
		_unit(4, 0, 11980.0, 380.0, 3),
		_unit(5, 0, 11920.0, 360.0, 4),
		_unit(11, 1, 11950.0, 23700.0, 0),
		_unit(12, 1, 12050.0, 23720.0, 0),
	]


func _new_view(field: Dictionary = {}):
	var packed := _load_scene(SPACE_VIEW_TSCN)
	if packed == null:
		return null
	var v = packed.instantiate()
	v.set("follow_mouse", false)
	root.add_child(v)
	await process_frame
	if not field.is_empty():
		v.set_field(field)
	await process_frame
	return v


# The camera the play uses (gap g2, Architect FINAL): zoom out through the rig API until the rig reports >= 5,400 (8 steps of 300 from
# 3,000), so the layer-4 sheet at y 4,000 is below the camera and every sheet is in front of it.
func _zoom_to_play_height(v) -> void:
	var rig = v.camera_rig()
	var guard := 0
	while rig.camera_height() < PLAY_HEIGHT_WU - 0.001 and guard < 40:
		rig.zoom_by(1)
		guard += 1


func _mounted_view():
	var v = await _new_view(_fixture_field())
	if v == null:
		return null
	v.set_frame(_frame(10, _army(), [11]), {"objectives": []})
	_zoom_to_play_height(v)
	await process_frame
	return v


func _space3d(v) -> Dictionary:
	var q: Dictionary = v.qa_state()
	var s = q.get("space3d", {})
	return s if s is Dictionary else {}


func _tube(v, focus: int, cursor: Vector2) -> Dictionary:
	v.set_focus_layer(focus)
	v.set("cursor_px", cursor)
	await process_frame
	await process_frame
	var t = _space3d(v).get("tube", {})
	return t if t is Dictionary else {}


# -- controls (green today: the harness and the fixture are sound) -----------------------------------------------------------------

func _test_controls() -> void:
	# CONTROL: the independent popcount equals the hand count of one byte: byte 3 of layer 0 is (3 * 7 + 0) & 0xFF = 21 = 0b10101, three bits.
	var masks := _fake_masks()
	_assert(int(masks[0][3]) == 21, "CONTROL fixture: layer 0 byte 3 is %d, not (3 * 7 + 0) & 0xFF = 21" % int(masks[0][3]))
	_assert(_popcount(PackedByteArray([21])) == 3, "CONTROL popcount: the bit loop counts byte 21 (0b10101) as %d, not 3" % _popcount(PackedByteArray([21])))
	_assert(_popcount(PackedByteArray([255, 0, 1])) == 9, "CONTROL popcount: the bit loop counts 255, 0, 1 as %d, not 9" % _popcount(PackedByteArray([255, 0, 1])))
	_assert(masks.size() == LAYERS and masks[0].size() == 7200 and masks[4].size() == 7200, "CONTROL fixture: expected 5 masks of 7200 bytes")
	var polys := _fake_polys()
	_assert(polys.size() == 3 and int(polys[0]["layer"]) == 0 and int(polys[1]["layer"]) == 4 and int(polys[2]["layer"]) == 2, "CONTROL fixture: the poly layers are not [0, 4, 2]")
	# CONTROL: the point-in-polygon helper against hand-worked cells. Triangle (0,0),(100,0),(100,100): the centre (50,50) lies ON the
	# diagonal edge; the sim's inclusive rule (xs = [50, 100], 50 >= 50) covers it; (150,50) is outside. Quad (200,200),(300,200),
	# (300,350.5),(200,300): centre (250,250) is inside (xs = [200, 300]); centre (250,350) is outside (xs = [299.0, 300]).
	var tri: PackedVector2Array = polys[0]["points"]
	var quad: PackedVector2Array = polys[1]["points"]
	_assert(_in_poly(tri, 50.0, 50.0), "CONTROL point-in-polygon: (50,50) on the triangle's diagonal edge must be inside by the sim's inclusive rule")
	_assert(not _in_poly(tri, 150.0, 50.0), "CONTROL point-in-polygon: (150,50) is outside the triangle")
	_assert(_in_poly(quad, 250.0, 250.0), "CONTROL point-in-polygon: (250,250) is inside the quad")
	_assert(not _in_poly(quad, 250.0, 350.0), "CONTROL point-in-polygon: (250,350) is outside the quad")
	# PREMISES dumped (printed so a run shows them): popcounts per layer, covered blocked cells per layer (the K-d copy covers none, hence the
	# extra layer-1 plate of _coverage_field), poly layers, the coverage field's layer-1 covered count.
	var pops := []
	var covs := []
	var field := _fixture_field()
	for k in range(LAYERS):
		pops.append(_popcount(masks[k]))
		covs.append(_covered_blocked(field, k).size())
	print("PREMISE popcounts per layer %s; covered blocked cells per layer %s; poly layers %s; cell centre ((cx + .5) * 100, (cy + .5) * 100), stride 240, even-odd inclusive scanline (csrc/space_raster.c:44-76); coverage field layer 1 covered = %d of %d blocked" % [pops, covs, [polys[0]["layer"], polys[1]["layer"], polys[2]["layer"]], _covered_blocked(_coverage_field(), 1).size(), pops[1]])
	# CONTROL: the mockup constant the parity test reads is 1,000 (field_map_space.gd:22) and the strip has five colours (layer_view.gd:12).
	var mock := _constants(MOCKUP_GD)
	_assert(is_equal_approx(float(mock.get("LAYER_GAP_WU", -1.0)), GAP_WU), "CONTROL parity: field_map_space.gd LAYER_GAP_WU is %s, not 1000.0" % mock.get("LAYER_GAP_WU", "missing"))
	_assert(_layer_colours().size() == LAYERS, "CONTROL: LayerView.LAYER_COLOURS has %d entries, not 5" % _layer_colours().size())
	var kit := _kit()
	_assert(kit.get("layers", []).size() == LAYERS and int(kit.get("plate", {}).get("thickness", -1)) == 60 and int(kit.get("rubble", {}).get("thickness", -1)) == 30, "CONTROL kit: kits/space.json must give 5 layer colours, plate thickness 60, rubble thickness 30")
	_assert(is_equal_approx(float(_constants(UNITS_GD).get("BODY_RADIUS_WU", -1.0)), 11.5), "CONTROL: Units3D.BODY_RADIUS_WU is not 11.5")


# -- PARITY of the layer gap and the pinned numbers --------------------------------------------------------------------------------

# d-view spec "Field": "Sheets: engine layer L (0-based) sits at `y = L * LAYER_GAP_WU`, `LAYER_GAP_WU := 1000.0` pinned in `space_view.gd`
# with a parity test that reads `scenes/mockups/landscape/field_map_space.gd:22` (`DRAFT-space-layer-gap`, Q-246-01)."
# Method rev 3 (rules.md (d)): "a piece that copies numbers ... from an approved prototype or mockup ships a test that reads each copied
# constant from the live script or scene and compares it to the prototype's as-run value". Spec "Numbers": "DRAFT-space-layer-gap 1,000;
# DRAFT-sheet-thickness 60/30; DRAFT-sheet-dim 0.55; DRAFT-ring-radius 1.2×; ... DRAFT-tube-radius 1,500; DRAFT-tube-alpha 0.15;
# DRAFT-tube-rim 10; DRAFT-space-cam-height 5,400; DRAFT-space-frame-budget 16 ms."
# The constant half reads the mockup (green today, the CONTROL above); the SpaceView half is red until built.
func _test_view_constants_and_parity() -> void:
	var s := _load_script(SPACE_VIEW_GD)
	var mock := _constants(MOCKUP_GD)
	if s == null:
		return
	var c := s.get_script_constant_map()
	_assert(c.has("LAYER_GAP_WU") and is_equal_approx(float(c["LAYER_GAP_WU"]), float(mock.get("LAYER_GAP_WU", -1.0))), "PARITY: SpaceView.LAYER_GAP_WU (%s) must equal field_map_space.gd:22 LAYER_GAP_WU (%s)" % [c.get("LAYER_GAP_WU", "missing"), mock.get("LAYER_GAP_WU", "missing")])
	# INTERFACE constants, each with the draft it carries.
	var want := {
		"UNIT_LIFT_WU": 150.0, "TUBE_RADIUS_WU": 1500.0, "TUBE_ALPHA": 0.15, "TUBE_RIM_WU": 10.0, "SHEET_DIM": 0.55,
		"RING_RADIUS_FACTOR": 1.2, "RING_WIDTH_WU": 6.0, "CAM_HEIGHT_WU": 5400.0, "FRAME_BUDGET_MS": 16.0,
	}
	for k in want:
		_assert(c.has(k) and is_equal_approx(float(c[k]), float(want[k])), "SpaceView.%s must be %s (INTERFACE / d-view spec Numbers; G2 for CAM_HEIGHT_WU); got %s" % [k, want[k], c.get(k, "missing")])
	# Parity with Units3D: UNIT_LIFT_WU is Units3D.FLYER_CLEARANCE_WU (ground_units.gd:11), read live, not copied.
	_assert(is_equal_approx(float(_constants(UNITS_GD).get("FLYER_CLEARANCE_WU", -1.0)), float(c.get("UNIT_LIFT_WU", -2.0))), "PARITY: SpaceView.UNIT_LIFT_WU (%s) must equal Units3D.FLYER_CLEARANCE_WU (%s)" % [c.get("UNIT_LIFT_WU", "missing"), _constants(UNITS_GD).get("FLYER_CLEARANCE_WU", "missing")])
	# Parity with Units3D: the ring radius is RING_RADIUS_FACTOR times Units3D.BODY_RADIUS_WU (11.5), read live, not copied.
	_assert(is_equal_approx(float(_constants(UNITS_GD).get("BODY_RADIUS_WU", -1.0)) * float(c.get("RING_RADIUS_FACTOR", -1.0)), 13.8), "PARITY: RING_RADIUS_FACTOR * Units3D.BODY_RADIUS_WU must be 1.2 * 11.5 = 13.8")


# -- SHEETS: y per layer, blocked_cells and slabs per sheet ------------------------------------------------------------------------

# d-view spec "Field": "engine layer L (0-based) sits at `y = L * LAYER_GAP_WU`"; spec "qa_state": "Deterministic element inventory: 5 sheets,
# `blocked_cells` per sheet equal to the mask's popcount, `slabs` equal to the poly count per layer"; INTERFACE counts(): "Array of 5
# {layer, y, blocked_cells, slabs, cell_squares} where blocked_cells = the mask popcount (ALL blocked cells, covered or not), slabs = the poly
# count of that layer". R-246-02 "the layers are visibly separated" (sheet y 0, 1000, ... 4000). R-246-03 "the client draws the layers as
# stacked 3D sheets from them".
func _test_sheets_y_and_counts() -> void:
	var field := _fixture_field()
	var sheets = await _new_sheets(field)
	if sheets == null:
		return
	var counts: Array = sheets.counts()
	_assert(counts.size() == LAYERS, "SHEETS: counts() has %d entries, not 5" % counts.size())
	var slab_want := [1, 0, 1, 0, 1]
	for k in range(LAYERS):
		_assert(is_equal_approx(float(sheets.sheet_y(k)), k * GAP_WU), "SHEET Y: sheet_y(%d) = %s, not %s (y = L * 1000, 0-based)" % [k, sheets.sheet_y(k), k * GAP_WU])
		if counts.size() == LAYERS:
			var c: Dictionary = counts[k]
			_assert(int(c.get("layer", -1)) == k and is_equal_approx(float(c.get("y", -1.0)), k * GAP_WU), "SHEET Y: counts()[%d] says layer %s y %s, want layer %d y %s" % [k, c.get("layer"), c.get("y"), k, k * GAP_WU])
			_assert(int(c.get("blocked_cells", -1)) == _popcount(field["masks"][k]), "BLOCKED CELLS: counts()[%d].blocked_cells = %s, the independent popcount of mask %d is %d" % [k, c.get("blocked_cells"), k, _popcount(field["masks"][k])])
			_assert(int(c.get("slabs", -1)) == slab_want[k] and slab_want[k] == _poly_count(field, k), "SLABS: counts()[%d].slabs = %s, the fixture has %d poly(s) on layer %d" % [k, c.get("slabs"), _poly_count(field, k), k])
			var covered := _covered_blocked(field, k).size()
			_assert(int(c.get("cell_squares", -1)) + covered == int(c.get("blocked_cells", -2)), "CELL SQUARES: layer %d cell_squares %s + covered %d != blocked_cells %s" % [k, c.get("cell_squares"), covered, c.get("blocked_cells")])
	await _drop(sheets)


# d-view spec "Field": "plus one MultiMesh square per mask-blocked cell not covered by a poly (the client rasterises polys to find them)";
# INTERFACE: "one MultiMesh instance (100 x 100 wu square prism, thickness 60 [G10]) per mask-blocked cell NOT covered by any poly of that layer
# (the client rasterises the polys: a cell is covered when its centre, in the sim's cell to world convention that the Preflight quotes, is inside
# a poly of that layer)"; spec "Field": "a fill square is centred at `((cx + 0.5)·100, (cy + 0.5)·100)`, stride 240, mask index `cy·240 + cx`".
# Run on the coverage field (the K-d copy plus one layer-1 plate, see _coverage_field): covered must be > 0 (premise), the MultiMesh instances at
# layer 1 are EXACTLY the blocked-and-uncovered cells, centred on the cell centres; the total over all layers equals sum(cell_squares).
func _test_sheets_cell_squares_and_coverage() -> void:
	var field := _coverage_field()
	var sheets = await _new_sheets(field)
	if sheets == null:
		return
	var covered := _covered_blocked(field, 1)
	_assert(covered.size() > 0, "PREMISE: the layer-1 plate covers no blocked cell, so the coverage case proves nothing")
	var counts: Array = sheets.counts()
	if counts.size() == LAYERS:
		var c: Dictionary = counts[1]
		var blocked := _popcount(field["masks"][1])
		_assert(int(c.get("blocked_cells", -1)) == blocked, "BLOCKED CELLS: layer 1 blocked_cells = %s, popcount %d (covered cells still count)" % [c.get("blocked_cells"), blocked])
		_assert(int(c.get("slabs", -1)) == 1, "SLABS: layer 1 slabs = %s with the extra plate, want 1" % c.get("slabs"))
		_assert(int(c.get("cell_squares", -1)) == blocked - covered.size(), "CELL SQUARES: layer 1 cell_squares = %s, blocked %d - covered %d = %d" % [c.get("cell_squares"), blocked, covered.size(), blocked - covered.size()])
	else:
		_assert(false, "CELL SQUARES: counts() has %d entries, not 5" % counts.size())
	# The MultiMesh instances themselves (world origin of each instance), binned to a sheet by the nearest layer y.
	var by_layer := {0: {}, 1: {}, 2: {}, 3: {}, 4: {}}
	var total := 0
	for n in _all_nodes(sheets, []):
		if n is MultiMeshInstance3D and n.multimesh != null:
			var mm: MultiMesh = n.multimesh
			var cnt := mm.visible_instance_count if mm.visible_instance_count >= 0 else mm.instance_count
			for i in range(cnt):
				var o: Vector3 = (n.global_transform * mm.get_instance_transform(i)).origin
				var layer := clampi(int(round(o.y / GAP_WU)), 0, LAYERS - 1)
				var idx := int(floor(o.z / CELL_WU)) * DIM + int(floor(o.x / CELL_WU))
				var centre_ok: bool = absf(o.x - (floorf(o.x / CELL_WU) + 0.5) * CELL_WU) < EPS and absf(o.z - (floorf(o.z / CELL_WU) + 0.5) * CELL_WU) < EPS
				(by_layer[layer] as Dictionary)[idx] = centre_ok
				total += 1
	var want_total := 0
	for k in range(LAYERS):
		var cov_k := _covered_blocked(field, k)
		want_total += _popcount(field["masks"][k]) - cov_k.size()
	_assert(total == want_total, "CELL SQUARES: %d MultiMesh instances in all, want sum over layers of blocked - covered = %d" % [total, want_total])
	var got: Dictionary = by_layer[1]
	var missing := 0
	var wrong_covered := 0
	var off_centre := 0
	var mask: PackedByteArray = field["masks"][1]
	for cy in range(DIM):
		for cx in range(DIM):
			var want: bool = _blocked(mask, cx, cy) and not covered.has(cy * DIM + cx)
			var idx := cy * DIM + cx
			if want and not got.has(idx):
				missing += 1
			if (not want) and got.has(idx):
				wrong_covered += 1
	for idx in got:
		if not bool(got[idx]):
			off_centre += 1
	_assert(missing == 0, "CELL SQUARES: %d blocked uncovered cells of layer 1 have no square" % missing)
	_assert(wrong_covered == 0, "COVERED CELLS: %d squares on layer 1 sit on an open cell or a cell a plate covers (a plate cell must get no square)" % wrong_covered)
	_assert(off_centre == 0, "CELL CENTRES: %d squares are not centred at ((cx + 0.5) * 100, (cy + 0.5) * 100)" % off_centre)
	await _drop(sheets)


# PARITY of the slab (method rev 3: a prototype copy's parity test compares a frame, not only constants). The fixture triangle (layer 0,
# kind 0) A(0,0) B(100,0) C(100,100), plate thickness 60 (kits/space.json plate.thickness, "plate kind 0 and mass kind 1 thickness 60,
# rubble kind 2 thickness 30"), by scenes/mockups/landscape/placer.gd _add_slab :424-443, derived by hand:
#   centroid = ((0 + 100 + 100) / 3, (0 + 0 + 100) / 3) = (66.667, 33.333); centre_top = (66.667, 60, 33.333)  [:429-434]
#   edge A->B: tris [centre_top, (0,60,0), (100,60,0)]; skirt [(0,60,0), (100,0,0), (100,60,0), (0,60,0), (0,0,0), (100,0,0)]
#   edge B->C: tris [centre_top, (100,60,0), (100,60,100)]; skirt [(100,60,0), (100,0,100), (100,60,100), (100,60,0), (100,0,0), (100,0,100)]
#   edge C->A: tris [centre_top, (100,60,100), (0,60,0)]; skirt [(100,60,100), (0,0,0), (0,60,0), (100,60,100), (100,0,100), (0,0,0)]
# so the top vertices are centre_top and A, B, C at y 60 and the skirts reach y 0 at A, B, C (placer.gd :436-443 "a skirt down to y = 0 on
# every edge"). The sheet sits at y = L * 1000 (here L = 0), so the expected world y values are 60 and 0. The builder may bake or move
# the vertices (the test applies each MeshInstance3D's transform); the check is that the set of vertex positions contains these seven.
# Mass (kind 1, layer 2, thickness 60) and rubble (kind 2, layer 4, thickness 30) are checked the same way at y = L * 1000 + thickness.
func _test_sheets_slab_shape_parity() -> void:
	var field := _fixture_field()
	var sheets = await _new_sheets(field)
	if sheets == null:
		return
	var kit := _kit()
	var plate_h := float(kit.get("plate", {}).get("thickness", -1))
	var rubble_h := float(kit.get("rubble", {}).get("thickness", -1))
	var verts: Array = []
	for n in _all_nodes(sheets, []):
		if n is MeshInstance3D and n.mesh is ArrayMesh:
			var xf: Transform3D = sheets.global_transform.affine_inverse() * n.global_transform
			for s in range(n.mesh.get_surface_count()):
				var arr: Array = n.mesh.surface_get_arrays(s)
				if arr.size() > Mesh.ARRAY_VERTEX and arr[Mesh.ARRAY_VERTEX] is PackedVector3Array:
					for p in arr[Mesh.ARRAY_VERTEX]:
						verts.append(xf * p)
	_assert(verts.size() > 0, "SLAB PARITY: SpaceSheets holds no ArrayMesh vertex (a slab is an ArrayMesh fan from the centroid, as placer.gd _add_slab)")
	var cases := [
		{"name": "plate triangle L0", "layer": 0, "h": plate_h, "pts": field["polys"][0]["points"]},
		{"name": "mass triangle L2", "layer": 2, "h": plate_h, "pts": field["polys"][2]["points"]},
		{"name": "rubble quad L4", "layer": 4, "h": rubble_h, "pts": field["polys"][1]["points"]},
	]
	for cs in cases:
		var pts: PackedVector2Array = cs["pts"]
		var centroid := Vector2.ZERO
		for p in pts:
			centroid += p
		centroid /= pts.size()
		var base: float = float(cs["layer"]) * GAP_WU
		var want: Array = [Vector3(centroid.x, base + float(cs["h"]), centroid.y)]
		for p in pts:
			want.append(Vector3(p.x, base + float(cs["h"]), p.y))
			want.append(Vector3(p.x, base, p.y))
		var lost: Array = []
		for w in want:
			var found := false
			for v in verts:
				if (v as Vector3).distance_to(w) < EPS:
					found = true
					break
			if not found:
				lost.append(w)
		_assert(lost.is_empty(), "SLAB PARITY %s: placer.gd _add_slab vertices not in SpaceSheets (top at sheet y + %s, skirts at sheet y): %s" % [cs["name"], cs["h"], lost])
	await _drop(sheets)


# -- SHEET DIM ---------------------------------------------------------------------------------------------------------------------

# Kit-mode spec section 4 "Layer focus": "Pieces on unfocused layers are drawn with their colour darkened by 55 percent." P2.5: "keys 1 to 5 darken
# the other layers by 55 percent; 0 shows all." d-view spec "Field": "Darkening of non-focus sheets 55 percent as the kit-mode spec section 4
# (`DRAFT-sheet-dim`)." INTERFACE: "set_focus_layer(n: int) (re-dims: sheets other than n darkened 0.55)"; "sheet_colour(layer: int) -> Color (the dimmed
# colour in use)"; "Color.darkened(0.55) on every sheet but the focus sheet"; sheet colours from kits/space.json "layers".
func _test_sheets_dim() -> void:
	var sheets = await _new_sheets(_fixture_field())
	if sheets == null:
		return
	for focus in [0, 3]:
		sheets.set_focus_layer(focus)
		await process_frame
		for k in range(LAYERS):
			var want: Color = _kit_colour(k) if k == focus else _kit_colour(k).darkened(SHEET_DIM)
			_assert(_near(sheets.sheet_colour(k), want), "SHEET DIM focus %d: sheet_colour(%d) = %s, want %s (%s)" % [focus, k, sheets.sheet_colour(k), want, "kit colour" if k == focus else "kit colour darkened 0.55"])
	# CONTROL for the dim: moving the focus moves the undimmed sheet (sheet 3 undimmed under focus 3, dimmed under focus 0).
	sheets.set_focus_layer(0)
	var dimmed3: Color = sheets.sheet_colour(3)
	sheets.set_focus_layer(3)
	_assert(not _near(dimmed3, sheets.sheet_colour(3)), "SHEET DIM control: sheet 3 has the same colour under focus 0 and focus 3 (set_focus_layer re-dims nothing)")
	await _drop(sheets)


# -- TUBE on the sheets, no camera (INTERFACE: set_tube(active, center, radius, focus_y), faded_layers()) --------------------------------

# d-view spec "Vision tube": "Every sheet above the focus layer fades its slabs and cell squares inside the tube"; INTERFACE: "faded_layers() ->
# Array of ints (sheets above the focus layer while the tube is active; empty when inactive)". Q-S3-01 (a): "occluding geometry on layers between
# the camera and the focus layer turns transparent inside a tube around the cursor or selection". POSITIVE CONTROLS: focus 4 fades nothing,
# focus 0 fades exactly [1, 2, 3, 4], focus 2 fades [3, 4]; inactive fades nothing.
func _test_sheets_tube() -> void:
	var sheets = await _new_sheets(_fixture_field())
	if sheets == null:
		return
	var want := {4: [], 0: [1, 2, 3, 4], 2: [3, 4], 3: [4], 1: [2, 3, 4]}
	for focus in want:
		sheets.set_focus_layer(focus)
		sheets.set_tube(true, Vector2(12000.0, 12000.0), TUBE_RADIUS_WU, focus * GAP_WU)
		await process_frame
		_assert(_ints(sheets.faded_layers()) == want[focus], "TUBE FADE focus %d: faded_layers() = %s, want %s (exactly the sheets above the focus layer)" % [focus, sheets.faded_layers(), want[focus]])
	sheets.set_focus_layer(0)
	sheets.set_tube(false, Vector2(12000.0, 12000.0), TUBE_RADIUS_WU, 0.0)
	await process_frame
	_assert(sheets.faded_layers().is_empty(), "TUBE INACTIVE: faded_layers() = %s with the tube off, want []" % [sheets.faded_layers()])
	await _drop(sheets)


# INTERFACE: "One ShaderMaterial resource (shaders/sheet_tube.gdshader) shared by every slab and every cell MultiMesh; uniforms tube_center (vec2,
# world x/z), tube_radius (float, wu), focus_y (float, world y of the focus sheet) set once per frame". d-view spec "Vision tube": "one material
# for every slab and square, so the cost is one uniform update per frame." Exactly ONE ShaderMaterial across all slab and cell instances, and the
# uniforms equal what set_tube was given.
func _test_sheets_one_material() -> void:
	var sheets = await _new_sheets(_coverage_field())
	if sheets == null:
		return
	sheets.set_focus_layer(2)
	sheets.set_tube(true, Vector2(3000.0, 4000.0), 1500.0, 2000.0)
	await process_frame
	await process_frame
	var mats := _sheet_materials(sheets)
	_assert(int(mats["drawables"]) > 0, "ONE MATERIAL: SpaceSheets has no slab MeshInstance3D and no cell MultiMeshInstance3D")
	_assert(int(mats["unmaterialed"]) == 0, "ONE MATERIAL: %d slab or cell instances carry no material" % int(mats["unmaterialed"]))
	_assert((mats["unique"] as Dictionary).size() == 1, "ONE MATERIAL: %d distinct material resources across the slabs and cell instances, want exactly 1" % (mats["unique"] as Dictionary).size())
	var one: Material = null
	for id in mats["unique"]:
		one = mats["unique"][id]
	_assert(one is ShaderMaterial, "ONE MATERIAL: the shared material is %s, want a ShaderMaterial" % [one])
	if one is ShaderMaterial:
		var sm := one as ShaderMaterial
		_assert(sm.shader != null and sm.shader.resource_path == SHADER_PATH, "ONE MATERIAL: the shader is %s, want %s" % [sm.shader.resource_path if sm.shader != null else "null", SHADER_PATH])
		var tc = sm.get_shader_parameter("tube_center")
		_assert(tc is Vector2 and (tc as Vector2).distance_to(Vector2(3000.0, 4000.0)) < EPS, "UNIFORMS: tube_center = %s, set_tube was given (3000, 4000)" % [tc])
		_assert(is_equal_approx(float(sm.get_shader_parameter("tube_radius") if sm.get_shader_parameter("tube_radius") != null else -1.0), 1500.0), "UNIFORMS: tube_radius = %s, set_tube was given 1500.0" % [sm.get_shader_parameter("tube_radius")])
		_assert(is_equal_approx(float(sm.get_shader_parameter("focus_y") if sm.get_shader_parameter("focus_y") != null else -1.0), 2000.0), "UNIFORMS: focus_y = %s, set_tube was given 2000.0" % [sm.get_shader_parameter("focus_y")])
		# RIM COLOUR: Q-S3-01 (a) "with an effect that says so"; d-view spec "Vision tube": "the 'small effect that says so' is a rim line at the tube's
		# edge on each faded sheet in that sheet's layer colour"; INTERFACE: "layer colours of rings and rims LayerView.LAYER_COLOURS" and "uniforms ...
		# plus the tube alpha, rim width and the layer colours". The INTERFACE names no uniform and no accessor for the rim colour, so the
		# uniform is found by value: the shared material must carry the strip's five colours in layer order (a contiguous run) so layer k's rim is
		# LAYER_COLOURS[k]. GAP reported: add rim_colour(layer) to the INTERFACE and this check becomes a direct read.
		_assert(_has_layer_colour_run(sm), "RIM COLOUR: the shared ShaderMaterial carries no run of the five LayerView.LAYER_COLOURS in layer order among its uniforms (found colour triples %s)" % [_colour_triples(sm)])
	await _drop(sheets)


# -- helpers for the material checks -----------------------------------------------------------------------------------------------

func _sheet_materials(sheets: Node) -> Dictionary:
	var unique := {}
	var drawables := 0
	var unmaterialed := 0
	for n in _all_nodes(sheets, []):
		var mats: Array = []
		if n is MeshInstance3D:
			drawables += 1
			if n.material_override != null:
				mats.append(n.material_override)
			if n.mesh != null:
				for s in range(n.mesh.get_surface_count()):
					var m = n.mesh.surface_get_material(s)
					if m != null:
						mats.append(m)
		elif n is MultiMeshInstance3D:
			drawables += 1
			if n.material_override != null:
				mats.append(n.material_override)
			if n.multimesh != null and n.multimesh.mesh != null:
				var mesh: Mesh = n.multimesh.mesh
				for s in range(mesh.get_surface_count()):
					var m = mesh.surface_get_material(s)
					if m != null:
						mats.append(m)
				if mesh.has_method("get_material") and mesh.get("material") != null:
					mats.append(mesh.get("material"))
		else:
			continue
		if mats.is_empty():
			unmaterialed += 1
		for m in mats:
			unique[(m as Object).get_instance_id()] = m
	return {"unique": unique, "drawables": drawables, "unmaterialed": unmaterialed}


func _flatten_colours(v: Variant, out: Array) -> void:
	match typeof(v):
		TYPE_COLOR:
			out.append([v.r, v.g, v.b])
		TYPE_VECTOR4:
			out.append([v.x, v.y, v.z])
		TYPE_VECTOR3:
			out.append([v.x, v.y, v.z])
		TYPE_ARRAY, TYPE_PACKED_COLOR_ARRAY, TYPE_PACKED_VECTOR3_ARRAY, TYPE_PACKED_VECTOR4_ARRAY:
			for e in v:
				_flatten_colours(e, out)


func _colour_triples(sm: ShaderMaterial) -> Array:
	var out: Array = []
	# Read through Shader.get_shader_uniform_list(), never ShaderMaterial.get_property_list(): in Godot 4.6.3 the latter drops a stored
	# PackedColorArray given to a vec4[] uniform (it re-types the parameter), which would make this check lie about the builder's material.
	if sm.shader == null:
		return out
	for u in sm.shader.get_shader_uniform_list():
		_flatten_colours(sm.get_shader_parameter(String(u["name"])), out)
	return out


func _has_layer_colour_run(sm: ShaderMaterial) -> bool:
	var tr := _colour_triples(sm)
	var lc := _layer_colours()
	if lc.size() != LAYERS:
		return false
	for i0 in range(0, tr.size() - LAYERS + 1):
		var ok := true
		for k in range(LAYERS):
			var c: Color = lc[k]
			var t: Array = tr[i0 + k]
			if absf(float(t[0]) - c.r) > EPS or absf(float(t[1]) - c.g) > EPS or absf(float(t[2]) - c.b) > EPS:
				ok = false
				break
		if ok:
			return true
	return false


# -- RINGS, built directly ---------------------------------------------------------------------------------------------------------

# d-view spec "Layer indicators (R-246-04, the condition)": "`space_rings.gd`: a flat ring under every unit at its sheet top + 2 (sheet top = L * gap + 60), coloured by the
# unit's layer with the strip's five colours (`scenes/tactical_c/layer_view.gd:13 LAYER_COLOURS`)"; "(`DRAFT-ring-radius` 1.2 × body radius ...)".
# INTERFACE: "one flat ring (radius RING_RADIUS_FACTOR * 11.5, width RING_WIDTH_WU) per item at world (x, layer * LAYER_GAP_WU + sheet thickness 60 + 2.0 [G10, Architect FINAL 2026-10-14: sheet top + 2], y) in
# LayerView.LAYER_COLOURS[layer]"; "ring_of(id) -> {layer, y, colour, radius, dashed: false}". Westley 2026-10-13: "layer indicators showing which
# layer each unit is on". (LAYER_COLOURS is at layer_view.gd:12 in this tree; the line number in the spec is off by one.)
# RING COLOURS: five units, one per layer 0..4, ring_of(id).colour == LayerView.LAYER_COLOURS[layer].
func _test_rings_geometry_and_colours() -> void:
	var rings = await _new_rings()
	if rings == null:
		return
	var items := []
	for k in range(LAYERS):
		items.append({"id": 100 + k, "x": 1000.0 + 50.0 * k, "y": 2000.0 + 70.0 * k, "layer": k, "dest_layer": -1})
	rings.update(items)
	await process_frame
	var lc := _layer_colours()
	for k in range(LAYERS):
		var r = rings.ring_of(100 + k)
		_assert(r is Dictionary, "RING COLOURS: ring_of(%d) is %s, not a ring Dictionary" % [100 + k, r])
		if not (r is Dictionary):
			continue
		_assert(int(r.get("layer", -1)) == k, "RING: unit on layer %d has ring layer %s" % [k, r.get("layer")])
		_assert(lc.size() == LAYERS and _near(r.get("colour", Color(0, 0, 0, 0)), lc[k]), "RING COLOURS: ring_of(%d).colour = %s, want LayerView.LAYER_COLOURS[%d] = %s" % [100 + k, r.get("colour"), k, lc[k] if lc.size() == LAYERS else "missing"])
		_assert(is_equal_approx(float(r.get("y", -1.0)), k * GAP_WU + PLATE_THICKNESS_WU + 2.0), "RING Y: ring_of(%d).y = %s, want sheet top + 2.0 = %s" % [100 + k, r.get("y"), k * GAP_WU + PLATE_THICKNESS_WU + 2.0])
		_assert(is_equal_approx(float(r.get("radius", -1.0)), 1.2 * 11.5), "RING RADIUS: ring_of(%d).radius = %s, want 1.2 * 11.5 = 13.8" % [100 + k, r.get("radius")])
		_assert(r.get("dashed", true) == false, "RING: the own-layer ring of unit %d is dashed" % [100 + k])
		_assert(rings.dest_ring_of(100 + k) == null, "RING: unit %d is not in transit but dest_ring_of is %s" % [100 + k, rings.dest_ring_of(100 + k)])
	_assert(rings.ring_count() == LAYERS and rings.dest_ring_count() == 0, "RING COUNT: ring_count() = %s, dest_ring_count() = %s, want 5 and 0" % [rings.ring_count(), rings.dest_ring_count()])
	await _drop(rings)


# Q-S3-02 / R-246-04: "one circle moves with the moving unit, and another circle on the exact Y height of the layer it was moving to";
# d-view spec: "a unit in transit shows a second, dashed ring on its destination sheet in the destination colour"; INTERFACE: "an item with
# dest_layer >= 0 also gets a second, dashed ring at the same x/z on the destination sheet (dest_layer * gap + 60 + 2.0, sheet top + 2) in LAYER_COLOURS[dest_layer];
# ... ring_count() -> int (one per drawn unit; the dest rings are counted apart by dest_ring_count())". One ring per item, replaced on update.
func _test_rings_transit_and_count() -> void:
	var rings = await _new_rings()
	if rings == null:
		return
	var lc := _layer_colours()
	rings.update([
		{"id": 7, "x": 4000.0, "y": 5000.0, "layer": 1, "dest_layer": 3},
		{"id": 8, "x": 4100.0, "y": 5100.0, "layer": 2, "dest_layer": -1},
		{"id": 9, "x": 4200.0, "y": 5200.0, "layer": 0, "dest_layer": -1},
	])
	await process_frame
	var d = rings.dest_ring_of(7)
	_assert(d is Dictionary, "TRANSIT RING: dest_ring_of(7) is %s, want the destination ring" % [d])
	if d is Dictionary:
		_assert(int(d.get("layer", -1)) == 3 and is_equal_approx(float(d.get("y", -1.0)), 3.0 * GAP_WU + PLATE_THICKNESS_WU + 2.0), "TRANSIT RING: destination ring at layer %s y %s, want layer 3 y 3062.0 (sheet top + 2)" % [d.get("layer"), d.get("y")])
		_assert(d.get("dashed", false) == true, "TRANSIT RING: the destination ring is not dashed")
		_assert(lc.size() == LAYERS and _near(d.get("colour", Color(0, 0, 0, 0)), lc[3]), "TRANSIT RING: destination ring colour %s, want LAYER_COLOURS[3]" % [d.get("colour")])
	var own = rings.ring_of(7)
	_assert(own is Dictionary and int(own.get("layer", -1)) == 1 and own.get("dashed", true) == false, "TRANSIT RING: the unit's own ring stays on its layer 1, solid; got %s" % [own])
	_assert(rings.dest_ring_of(8) == null and rings.dest_ring_of(9) == null, "TRANSIT RING: units not in transit must have no destination ring")
	_assert(rings.ring_count() == 3 and rings.dest_ring_count() == 1, "RING COUNT: ring_count() = %s, dest_ring_count() = %s, want 3 and 1" % [rings.ring_count(), rings.dest_ring_count()])
	rings.update([{"id": 8, "x": 4100.0, "y": 5100.0, "layer": 2, "dest_layer": -1}])
	await process_frame
	_assert(rings.ring_count() == 1 and rings.dest_ring_count() == 0 and rings.ring_of(7) == null, "RING COUNT: after update([unit 8]) ring_count() = %s, dest_ring_count() = %s, ring_of(7) = %s, want 1, 0, null" % [rings.ring_count(), rings.dest_ring_count(), rings.ring_of(7)])
	await _drop(rings)


# -- VIEW: inventory ---------------------------------------------------------------------------------------------------------------

# G1 ruling: "SpaceView.qa_state returns ground3d {present: false} and space3d {present: true, ...}"; INTERFACE: "{"space3d": {"present": false}} before
# set_field"; spec "qa_state": "`space3d: {present: true, gap_wu, sheets: [{layer, y, blocked_cells, slabs}], ...}`; `units_px` from the `to_screen`
# analogue. Deterministic element inventory: 5 sheets, `blocked_cells` per sheet equal to the mask's popcount, `slabs` equal to the poly count per layer,
# one ring per drawn unit." R-246-03 "stacked 3D sheets".
func _test_view_inventory() -> void:
	var v = await _new_view()
	if v == null:
		return
	var before := _space3d(v)
	_assert(before.has("present") and not bool(before["present"]), "VIEW: before set_field qa_state.space3d.present must be false, got %s" % [before])
	var g0: Dictionary = (v.qa_state() as Dictionary).get("ground3d", {"present": true})
	_assert(not bool(g0.get("present", true)), "VIEW (G1): qa_state.ground3d.present must stay false for the space view, got %s" % [g0])
	var field := _fixture_field()
	v.set_field(field)
	await process_frame
	var s3 := _space3d(v)
	_assert(bool(s3.get("present", false)), "VIEW: qa_state.space3d.present is not true after set_field; space3d = %s" % [s3])
	_assert(is_equal_approx(float(s3.get("gap_wu", -1.0)), GAP_WU), "VIEW: space3d.gap_wu = %s, want 1000.0" % [s3.get("gap_wu")])
	var sh: Array = s3.get("sheets", [])
	_assert(sh.size() == LAYERS, "INVENTORY: space3d.sheets has %d entries, want 5" % sh.size())
	if sh.size() == LAYERS:
		for k in range(LAYERS):
			var e: Dictionary = sh[k]
			_assert(int(e.get("layer", -1)) == k and is_equal_approx(float(e.get("y", -1.0)), k * GAP_WU), "SHEET Y: space3d.sheets[%d] = layer %s y %s, want layer %d y %s" % [k, e.get("layer"), e.get("y"), k, k * GAP_WU])
			_assert(int(e.get("blocked_cells", -1)) == _popcount(field["masks"][k]), "BLOCKED CELLS: space3d.sheets[%d].blocked_cells = %s, independent popcount %d" % [k, e.get("blocked_cells"), _popcount(field["masks"][k])])
			_assert(int(e.get("slabs", -1)) == _poly_count(field, k), "SLABS: space3d.sheets[%d].slabs = %s, poly count %d" % [k, e.get("slabs"), _poly_count(field, k)])
	await _drop(v)


# -- VIEW: units, rings, the visible filter ----------------------------------------------------------------------------------------

# Spec "Units": "Own units always; enemies only when visible, as `Ground3D.set_frame` filters." INTERFACE: "own units always; enemies only when in
# frame.visible[str(player_faction)]"; "unit y = sheet top + 150" (Architect FINAL 2026-10-14, spec rev 3: sheet top = L * gap + sheet thickness 60, 150 = Units3D
# FLYER_CLEARANCE_WU; this REVERSES the older INTERFACE line "L * gap + UNIT_LIFT_WU 40", struck with DRAFT-space-unit-lift; y 2,210 on layer 2); "ring_layer == layer; dest_ring_layer == tl for a unit in transit, else -1"; "a plate-sheet unit on
# layer 2 has y 2,210 (2000 + 60 + 150) outside transit". ONE RING PER DRAWN UNIT: the rings node holds exactly the drawn units (own 1..5, visible
# enemy 11), not the unseen enemy 12.
func _test_view_units_and_rings() -> void:
	var v = await _new_view(_fixture_field())
	if v == null:
		return
	v.set_frame(_frame(10, _army(), [11]), {"objectives": []})
	await process_frame
	var s3 := _space3d(v)
	var units: Dictionary = s3.get("units", {})
	var drawn := ["1", "2", "3", "4", "5", "11"]
	_assert(_str_sorted(units.keys()) == _str_sorted(drawn), "ONE RING PER UNIT: space3d.units keys %s, want exactly the drawn units %s (own always, enemy 11 visible, enemy 12 hidden)" % [units.keys(), drawn])
	var lift_want := {"1": 210.0, "2": 1210.0, "3": 2210.0, "4": 3210.0, "5": 4210.0}
	for id in lift_want:
		var u: Dictionary = units.get(id, {})
		_assert(is_equal_approx(float(u.get("y", -1.0)), float(lift_want[id])), "UNIT Y: unit %s (layer %s) y = %s, want %s (layer * 1000 + 60 + 150)" % [id, u.get("layer"), u.get("y"), lift_want[id]])
		_assert(int(u.get("ring_layer", -2)) == int(u.get("layer", -3)) and int(u.get("layer", -3)) == int(id) - 1, "RING LAYER: unit %s layer %s ring_layer %s, want both %d" % [id, u.get("layer"), u.get("ring_layer"), int(id) - 1])
		_assert(int(u.get("dest_ring_layer", -2)) == -1, "RING: unit %s is not in transit but dest_ring_layer = %s, want -1" % [id, u.get("dest_ring_layer")])
	var u2: Dictionary = units.get("3", {})
	_assert(int(u2.get("layer", -1)) == 2 and is_equal_approx(float(u2.get("y", -1.0)), 2210.0) and int(u2.get("ring_layer", -1)) == 2 and int(u2.get("dest_ring_layer", -2)) == -1, "UNIT on layer 2: want ring_layer 2, y 2210.0, dest_ring_layer -1; got %s" % [u2])
	var u0: Dictionary = units.get("1", {})
	_assert(is_equal_approx(float(u0.get("y", -1.0)), 210.0), "UNIT on layer 0 (control for the lift): y = %s, want 210.0 (sheet top 60 + 150)" % [u0.get("y")])
	var rings = _find_by_script(v, _load_script(SPACE_RINGS_GD))
	_assert(rings != null, "ONE RING PER UNIT: no SpaceRings node under the view")
	if rings != null:
		_assert(rings.ring_count() == 6, "ONE RING PER UNIT: SpaceRings.ring_count() = %s, want 6 (the drawn units)" % rings.ring_count())
		_assert(rings.ring_of(12) == null and rings.ring_of(11) != null, "ONE RING PER UNIT: the unseen enemy 12 has a ring (%s) or the visible enemy 11 has none (%s)" % [rings.ring_of(12), rings.ring_of(11)])
		var lc := _layer_colours()
		for k in range(LAYERS):
			var r = rings.ring_of(k + 1)
			_assert(r is Dictionary and lc.size() == LAYERS and _near(r.get("colour", Color(0, 0, 0, 0)), lc[k]), "RING COLOURS: the view's ring for the unit on layer %d is %s, want LAYER_COLOURS[%d]" % [k, r, k])
	await _drop(v)


func _str_sorted(a: Array) -> Array:
	var out := []
	for e in a:
		out.append(str(e))
	out.sort()
	return out


# TRANSIT: Q-S3-02 "another circle on the exact Y height of the layer it was moving to"; spec "Units": "in transit (state bit 4) `y` interpolates
# linearly from its layer to `tl` between the current tick and `ld`"; INTERFACE: "a unit with state bit 4 (value 4) and tl: y interpolates linearly
# between top(L) + 150 and top(tl) + 150 (top(L) = L * gap + 60) with frac per [G6]"; G6 null action (d-view spec rev 1, gap 6 null action, Architect may veto on the shot): "the
# client records t0 at the first transit frame", so frac = (tick - t0) / (ld - t0). Unit 6 on layer 1, tl 3, ld 200; frames at ticks 100, 140, 180:
# frac 0, 0.4, 0.8, so y = 1210, 2010, 2810 (the ends of the range are 1210 = 1000 + 60 + 150 and 3210 = 3000 + 60 + 150). The destination ring is on sheet 3 in LAYER_COLOURS[3].
func _test_view_transit() -> void:
	var v = await _new_view(_fixture_field())
	if v == null:
		return
	var seen_y := []
	var want_y := [1210.0, 2010.0, 2810.0]
	var ticks := [100, 140, 180]
	for i in range(3):
		var u := _unit(6, 0, 12000.0, 500.0, 1, {"state": 4, "tl": 3, "ld": 200})
		v.set_frame(_frame(ticks[i], [u, _unit(1, 0, 11900.0, 400.0, 0)]), {"objectives": []})
		await process_frame
		var e: Dictionary = _space3d(v).get("units", {}).get("6", {})
		seen_y.append(float(e.get("y", -1.0)))
		_assert(is_equal_approx(float(e.get("y", -1.0)), float(want_y[i])), "TRANSIT Y: tick %d y = %s, want %s (linear from 1210 at the first transit frame toward 3210 at ld 200)" % [ticks[i], e.get("y"), want_y[i]])
		_assert(int(e.get("dest_ring_layer", -2)) == 3, "TRANSIT RING: tick %d dest_ring_layer = %s, want 3 (tl)" % [ticks[i], e.get("dest_ring_layer")])
		_assert(int(e.get("ring_layer", -2)) == 1, "TRANSIT RING: tick %d ring_layer = %s, want the unit's own layer 1" % [ticks[i], e.get("ring_layer")])
	_assert(seen_y.size() == 3 and seen_y[0] < seen_y[1] and seen_y[1] < seen_y[2] and seen_y[0] >= 1210.0 - EPS and seen_y[2] <= 3210.0 + EPS, "TRANSIT Y: the three frames give %s, want strictly rising within [1210, 3210]" % [seen_y])
	var rings = _find_by_script(v, _load_script(SPACE_RINGS_GD))
	if rings != null:
		var d = rings.dest_ring_of(6)
		var lc := _layer_colours()
		_assert(d is Dictionary and int(d.get("layer", -1)) == 3 and d.get("dashed", false) == true and lc.size() == LAYERS and _near(d.get("colour", Color(0, 0, 0, 0)), lc[3]), "TRANSIT RING: the view's destination ring is %s, want a dashed ring on layer 3 in LAYER_COLOURS[3]" % [d])
	else:
		_assert(false, "TRANSIT RING: no SpaceRings node under the view")
	# Out of transit again (state 0, layer 3): the destination ring goes, y is 3210.
	v.set_frame(_frame(220, [_unit(6, 0, 12000.0, 500.0, 3), _unit(1, 0, 11900.0, 400.0, 0)]), {"objectives": []})
	await process_frame
	var e2: Dictionary = _space3d(v).get("units", {}).get("6", {})
	_assert(is_equal_approx(float(e2.get("y", -1.0)), 3210.0) and int(e2.get("dest_ring_layer", -2)) == -1, "TRANSIT END: arrived on layer 3, y = %s dest_ring_layer = %s, want 3210.0 and -1" % [e2.get("y"), e2.get("dest_ring_layer")])
	await _drop(v)


# -- VIEW: camera ------------------------------------------------------------------------------------------------------------------

# Spec "Camera (gap g2)": "the play pans to the player's spawn anchor and zooms out through the rig API until the rig reports a height of at least
# `DRAFT-space-cam-height` 5,400"; INTERFACE: "the rig panned to the player's spawn anchor (the map.nodes kind 7 node nearest the local faction's units;
# the army stands at the map edge, y near 150)"; A18 G3 (tests/test_tactical_camera.gd header): "the player's spawn point is the kind-7 map node nearest
# the centroid of the own units". The fixture's own units stand near (11950, 400): nearest kind 7 node is (11950, 150), not (11950, 23850). G2: the
# height is 5,400 once the rig is zoomed the way the play zooms it (3,000 plus 8 steps of 300; if the view already starts at 5,400 the loop adds none).
# G4 null action (d-view spec rev 1, gap 4 null action, Architect may veto on the shot): the rig's own pitch is reported, so only that the key is a
# number is asserted, never its value.
func _test_view_camera() -> void:
	var v = await _new_view(_fixture_field())
	if v == null:
		return
	v.set_frame(_frame(10, _army(), [11]), {"objectives": []})
	await process_frame
	_zoom_to_play_height(v)
	await process_frame
	var cam: Dictionary = _space3d(v).get("camera", {})
	_assert(absf(float(cam.get("x", -1.0)) - 11950.0) < EPS and absf(float(cam.get("y", -1.0)) - 150.0) < EPS, "CAMERA: qa_state.space3d.camera x,y = (%s, %s), want the spawn anchor (11950, 150)" % [cam.get("x"), cam.get("y")])
	_assert(is_equal_approx(float(cam.get("height", -1.0)), PLAY_HEIGHT_WU), "CAMERA: qa_state.space3d.camera.height = %s after zooming through the rig API, want 5400.0 (G2)" % [cam.get("height")])
	_assert(is_equal_approx(float(cam.get("height", -1.0)), float(v.camera_rig().camera_height())), "CAMERA: reported height %s differs from the rig's camera_height() %s" % [cam.get("height"), v.camera_rig().camera_height()])
	_assert(cam.has("pitch") and typeof(cam["pitch"]) in [TYPE_FLOAT, TYPE_INT], "CAMERA (G4): qa_state.space3d.camera.pitch must be reported as a number; got %s" % [cam.get("pitch")])
	await _drop(v)


# -- VIEW: projection and picking --------------------------------------------------------------------------------------------------

# INTERFACE: "to_screen(wx, wy, layer = 0) -> Vector2 (the camera projection of the world point at y = layer * gap ...)"; "to_world(screen) -> Variant
# (the intersection of the camera ray with the focus sheet plane y = focus_layer * gap, null on no hit: the view's own ray test, not physics)"; spec
# "Planes": "`units_px` uses each unit's own sheet" (the d-view spec Hosting bullet: "`units_px` uses each unit's own sheet"). PICKING (spec "Vision tube"):
# "Picking inside the tube resolves on the focus sheet (the ray hits the focus sheet's plane first because faded geometry is `no_depth` for picking: the
# view's own ray test, not physics)". to_world's result type is not fixed by the INTERFACE (Ground3D's returns the Vector2 (x, z); a Vector3 carries y):
# both are accepted. Whatever it is, projecting that (x, z) back at the focus layer must land on the screen point, and the hit on the faded upper sheet
# (the ray's intersection with y = 3000) must differ from it.
func _test_view_projection_and_picking() -> void:
	var v = await _mounted_view()
	if v == null:
		return
	var cam: Camera3D = v.camera_rig().get_camera()
	for layer in [0, 2, 4]:
		var p := Vector2(11950.0, 600.0)
		var want: Vector2 = cam.unproject_position(Vector3(p.x, layer * GAP_WU, p.y))
		var got: Vector2 = v.to_screen(p.x, p.y, layer)
		_assert(got.distance_to(want) <= ONE_PX, "PROJECTION: to_screen(%s, %s, %d) = %s, the camera projects (x, %s, z) to %s" % [p.x, p.y, layer, got, layer * GAP_WU, want])
	var units_px: Dictionary = v.qa_state().get("units_px", {})
	for id in [1, 3, 5]:
		var u: Dictionary = {}
		for e in _army():
			if int(e["id"]) == id:
				u = e
		var layer := int(u["layer"])
		var want2: Vector2 = cam.unproject_position(Vector3(float(u["x"]), layer * GAP_WU, float(u["y"])))
		var px = units_px.get(str(id), units_px.get(id, null))
		var got2 := Vector2(-1e9, -1e9)
		if px is Vector2:
			got2 = px
		elif px is Array and px.size() == 2:
			got2 = Vector2(float(px[0]), float(px[1]))
		_assert(got2.distance_to(want2) <= ONE_PX, "UNITS_PX: units_px[%d] = %s, the unit's own sheet (layer %d) projects to %s" % [id, got2, layer, want2])
	for focus in [1, 2]:
		v.set_focus_layer(focus)
		v.set("cursor_px", CURSOR_CENTRE)
		await process_frame
		await process_frame
		var hit = v.to_world(CURSOR_CENTRE)
		_assert(hit != null, "PICKING: to_world(%s) is null with the camera above the focus sheet %d" % [CURSOR_CENTRE, focus])
		if hit == null:
			continue
		var hx := 0.0
		var hz := 0.0
		var plane_ok := true
		if hit is Vector3:
			hx = (hit as Vector3).x
			hz = (hit as Vector3).z
			plane_ok = absf((hit as Vector3).y - focus * GAP_WU) < EPS
		elif hit is Vector2:
			hx = (hit as Vector2).x
			hz = (hit as Vector2).y
		else:
			plane_ok = false
		_assert(plane_ok, "PICKING: to_world returned %s, not a point on the focus sheet plane y = %s" % [hit, focus * GAP_WU])
		var back: Vector2 = v.to_screen(hx, hz, focus)
		_assert(back.distance_to(CURSOR_CENTRE) <= ONE_PX, "PICKING: to_world(%s) = (%s, %s) projects back at sheet %d to %s: it is not the focus sheet plane's hit" % [CURSOR_CENTRE, hx, hz, focus, back])
		var o := cam.project_ray_origin(CURSOR_CENTRE)
		var d := cam.project_ray_normal(CURSOR_CENTRE)
		var upper_t := (3.0 * GAP_WU - o.y) / d.y
		var upper := Vector2(o.x + d.x * upper_t, o.z + d.z * upper_t)
		_assert(not Vector2(hx, hz).is_equal_approx(upper), "PICKING: to_world(%s) = (%s, %s) is the hit on the faded upper sheet 3, not the focus sheet %d" % [CURSOR_CENTRE, hx, hz, focus])
	await _drop(v)


# -- VIEW: the tube ----------------------------------------------------------------------------------------------------------------

# Spec "Vision tube": "Focus layer = the strip's `focus_layer`. Tube centre = the cursor's position projected onto the focus sheet; radius `DRAFT-tube-radius`
# 1,500 wu. Every sheet above the focus layer fades its slabs and cell squares inside the tube"; INTERFACE: "The tube is active when the cursor ray hits the
# focus sheet plane; tube centre (cx, cy) = that hit point; radius TUBE_RADIUS_WU; faded_layers = the sheets above the focus layer ([] when inactive)".
# POSITIVE CONTROLS: focus 4 fades nothing (active, faded []), focus 0 fades exactly [1,2,3,4], focus 2 fades [3,4]. Centre: projecting (cx, cy) back at
# the focus sheet lands within one display pixel of cursor_px (checked for two cursor points).
func _test_view_tube() -> void:
	var v = await _mounted_view()
	if v == null:
		return
	var want := {4: [], 0: [1, 2, 3, 4], 2: [3, 4]}
	for focus in want:
		var t := await _tube(v, focus, CURSOR_CENTRE)
		_assert(bool(t.get("active", false)), "TUBE: focus %d, cursor %s: tube.active is false although the cursor ray hits the focus sheet plane (camera height 5400); tube = %s" % [focus, CURSOR_CENTRE, t])
		_assert(_ints(t.get("faded_layers", [-1])) == want[focus], "TUBE FADE focus %d: tube.faded_layers = %s, want %s" % [focus, t.get("faded_layers"), want[focus]])
		_assert(is_equal_approx(float(t.get("radius_wu", -1.0)), TUBE_RADIUS_WU), "TUBE: focus %d radius_wu = %s, want 1500.0" % [focus, t.get("radius_wu")])
	for cursor in [CURSOR_CENTRE, CURSOR_OFF]:
		var t2 := await _tube(v, 1, cursor)
		var back: Vector2 = v.to_screen(float(t2.get("cx", -1e9)), float(t2.get("cy", -1e9)), 1)
		_assert(back.distance_to(cursor) <= ONE_PX, "TUBE CENTRE: focus 1, cursor %s: (cx, cy) = (%s, %s) projects on sheet 1 to %s, more than one pixel from the cursor" % [cursor, t2.get("cx"), t2.get("cy"), back])
		_assert(_ints(t2.get("faded_layers", [])) == [2, 3, 4], "TUBE FADE focus 1: faded_layers = %s, want [2, 3, 4]" % [t2.get("faded_layers")])
	await _drop(v)


# INTERFACE: "tube inactive when the cursor ray misses the focus sheet plane (faded_layers == [], active false)"; "to_world ... null on no hit".
# The miss is made by zooming the rig in to its floor (ZOOM_MIN 150, camera_rig_3d.gd:11) with focus layer 4: the camera is then at y 150, below the
# focus plane y 4000, and every ray of the frame (pitch 50 below the horizontal, vertical fov 75) points downward, so none reaches the plane.
func _test_view_tube_inactive() -> void:
	var v = await _mounted_view()
	if v == null:
		return
	var up := await _tube(v, 4, CURSOR_CENTRE)
	_assert(bool(up.get("active", false)), "TUBE INACTIVE control: at camera height 5400 and focus 4 the tube must be active; tube = %s" % [up])
	v.camera_rig().zoom_by(-100)
	await process_frame
	var t := await _tube(v, 4, CURSOR_CENTRE)
	_assert(not bool(t.get("active", true)), "TUBE INACTIVE: the cursor ray cannot reach the focus sheet (camera at y %s, sheet at 4000) but tube.active = %s" % [v.camera_rig().get_camera().global_position.y, t.get("active")])
	_assert(_ints(t.get("faded_layers", [-1])) == [], "TUBE INACTIVE: faded_layers = %s, want []" % [t.get("faded_layers")])
	_assert(v.to_world(CURSOR_CENTRE) == null, "PICKING: to_world is %s with the ray missing the focus plane, want null" % [v.to_world(CURSOR_CENTRE)])
	await _drop(v)


# The shader's uniforms equal the qa_state tube values (INTERFACE: "uniforms tube_center (vec2, world x/z), tube_radius (float, wu), focus_y (float, world y of
# the focus sheet) set once per frame"), read from the ONE shared material of the view's SpaceSheets; the rim colour of every faded sheet is its layer colour
# (the run of LAYER_COLOURS in the material, see _test_sheets_one_material for the reading).
func _test_view_tube_material() -> void:
	var v = await _mounted_view()
	if v == null:
		return
	var sheets = _find_by_script(v, _load_script(SPACE_SHEETS_GD))
	_assert(sheets != null, "TUBE MATERIAL: no SpaceSheets node under the view")
	if sheets == null:
		await _drop(v)
		return
	for focus in [0, 2]:
		var t := await _tube(v, focus, CURSOR_OFF)
		var mats := _sheet_materials(sheets)
		_assert((mats["unique"] as Dictionary).size() == 1, "TUBE MATERIAL: %d distinct materials across slabs and cells, want exactly ONE ShaderMaterial" % (mats["unique"] as Dictionary).size())
		var one: Material = null
		for id in mats["unique"]:
			one = mats["unique"][id]
		if not (one is ShaderMaterial):
			_assert(false, "TUBE MATERIAL: the shared material is %s, want a ShaderMaterial" % [one])
			continue
		var sm := one as ShaderMaterial
		var tc = sm.get_shader_parameter("tube_center")
		_assert(tc is Vector2 and (tc as Vector2).distance_to(Vector2(float(t.get("cx", -1e9)), float(t.get("cy", -1e9)))) < EPS, "UNIFORMS focus %d: shader tube_center = %s, qa_state tube (cx, cy) = (%s, %s)" % [focus, tc, t.get("cx"), t.get("cy")])
		var tr = sm.get_shader_parameter("tube_radius")
		_assert(tr != null and is_equal_approx(float(tr), float(t.get("radius_wu", -1.0))), "UNIFORMS focus %d: shader tube_radius = %s, qa_state radius_wu = %s" % [focus, tr, t.get("radius_wu")])
		var fy = sm.get_shader_parameter("focus_y")
		_assert(fy != null and is_equal_approx(float(fy), focus * GAP_WU), "UNIFORMS focus %d: shader focus_y = %s, want the focus sheet's y %s" % [focus, fy, focus * GAP_WU])
		_assert(_has_layer_colour_run(sm), "RIM COLOUR focus %d: faded sheets %s must show a rim in LAYER_COLOURS[layer]; the shared material carries no run of the five layer colours in layer order" % [focus, t.get("faded_layers")])
	await _drop(v)


# -- HOST: tactical_view.tscn with the live pipe (gap g1, g3) ------------------------------------------------------------------------

# G1 (Architect FINAL): "Hosting happens only when the environment has OM_SPACE_VIEW=1 (read once in tactical_view.gd through OS.get_environment); the
# default space era stays 2D until Westley approves the shot ... host AFTER set_terrain: in _load_live right after the set_terrain call ... `if
# _space_view_opted_in() and _ground3d == null and not _ground_era() and space_field() non-empty: _host_space_view()`"; "M2: one qa_state line forwarding
# the host's `space3d` key"; G3 (a): "the per-unit loop in tactical_view.gd's _redraw through the public unit_node(id): hide Body and LayerRing ...;
# UnitSquads.visible = false". The hosting lives in _load_live, which asks the live pipe (SimSession.bridge(): mission_start, space_field_dump), so the
# case mounts tactical_view.tscn on the real pipe in the default space era (the same way tests/test_tactical_camera.gd mounts it); no fixture can
# replace the bridge's field there. The field is the live one, so only counts that hold for any field are asserted (5 sheets, y per layer, one ring per
# own unit). CONTROL first (green today): without OM_SPACE_VIEW the view is 2D and qa_state.space3d is absent or present false, the 2D unit bodies are visible.
func _test_host_control_and_wiring() -> void:
	var packed := _load_scene(TACTICAL_TSCN)
	if packed == null:
		return
	OS.unset_environment("OM_SPACE_VIEW")
	var v: Node = packed.instantiate()
	root.add_child(v)
	await process_frame
	v.set_process(false)
	await process_frame
	var q: Dictionary = v.qa_state()
	var sp = q.get("space3d", {"present": false})
	_assert(not bool((sp as Dictionary).get("present", false)), "HOST CONTROL: without OM_SPACE_VIEW the view hosts the SpaceView (space3d = %s)" % [sp])
	_assert((q.get("units", {}) as Dictionary).size() > 0, "HOST CONTROL premise: the live space mission has no units in qa_state (units = %s)" % [q.get("units")])
	var era := root.get_node_or_null("EraConfig")
	_assert(era != null and str(era.call("kind")) == "space", "HOST CONTROL premise: EraConfig.kind() is %s, want space" % [era.call("kind") if era != null else "no autoload"])
	_assert(v.get_node_or_null("SpaceView") == null, "HOST CONTROL: a SpaceView node exists without OM_SPACE_VIEW")
	v.queue_free()
	await process_frame
	# Opt in.
	OS.set_environment("OM_SPACE_VIEW", "1")
	var h: Node = packed.instantiate()
	root.add_child(h)
	await process_frame
	h.set_process(false)
	await process_frame
	var hq: Dictionary = h.qa_state()
	var s3: Dictionary = hq.get("space3d", {})
	_assert(bool(s3.get("present", false)), "HOST WIRING (G1): with OM_SPACE_VIEW=1 qa_state.space3d.present is not true; space3d = %s" % [s3])
	_assert((s3.get("sheets", []) as Array).size() == LAYERS, "HOST WIRING: space3d.sheets has %d entries, want 5" % (s3.get("sheets", []) as Array).size())
	_assert(h.get_node_or_null("SpaceView") != null, "HOST WIRING (G1): no child named SpaceView on the tactical view")
	if bool(s3.get("present", false)):
		_assert(not bool((hq.get("ground3d", {"present": false}) as Dictionary).get("present", false)), "HOST WIRING (M2): qa_state.ground3d.present must stay false with the SpaceView")
	# G3: the 2D bodies and rings are hidden, the squads layer is off.
	var uv := h.get_node_or_null("UnitVisuals")
	var squads := h.get_node_or_null("UnitSquads")
	_assert(squads != null and not squads.visible, "HOST 2D UNITS (G3): UnitSquads.visible must be false under the SpaceView")
	var shown := 0
	var checked := 0
	if uv != null:
		for id in hq.get("units", {}):
			var n = uv.unit_node(int(id))
			if n == null:
				continue
			checked += 1
			for part in ["Body", "LayerRing"]:
				var c = n.get_node_or_null(part)
				if c != null and c.visible:
					shown += 1
	_assert(checked > 0, "HOST 2D UNITS (G3) premise: no UnitVisuals unit_node for any qa_state unit")
	_assert(shown == 0, "HOST 2D UNITS (G3): %d Body or LayerRing nodes are still visible under the SpaceView" % shown)
	# One ring per drawn unit in the live army (all own units on layer 0 at the start: scout report 1.).
	var own := 0
	for id in hq.get("units", {}):
		if int(hq["units"][id].get("faction", -1)) == int(hq.get("local_faction", 0)):
			own += 1
	var su: Dictionary = s3.get("units", {})
	_assert(su.size() >= own and own > 0, "HOST WIRING: space3d.units has %d entries for %d own units" % [su.size(), own])
	h.queue_free()
	await process_frame
	OS.unset_environment("OM_SPACE_VIEW")
