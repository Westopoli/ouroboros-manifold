extends Node
class_name SpaceView

## VG-D-VIEW unit 3 (docs/northstar/plans/2026-10-13-d-view-spec.md, S-246 R-246-01 to R-246-04): the space era's 3D look. Five stacked
## sheets (SpaceSheets), the units on them as flyers, a layer ring under every unit (SpaceRings) and the vision tube, in a SubViewport shell
## copied in shape from scenes/ground3d/ground3d.gd:33-66. Hosted by tactical_view.gd only with OM_SPACE_VIEW=1 (the opt-in of the first look).
## The host assigns this node to its _ground3d member (duck-typed: set_frame, qa_state, camera_rig, to_screen, to_world, add_layer).
## See also: tests/test_vg_d_view.gd, tests/qa/desktop/plays/D/S-246.py.

const GroundHost := preload("res://scenes/ground3d/ground3d.gd")
const CameraRig := preload("res://scenes/ground3d/camera_rig_3d.gd")
const GroundUnits := preload("res://scenes/ground3d/ground_units.gd")
const LayerViewScript := preload("res://scenes/tactical_c/layer_view.gd")
const SpaceSheetsScript := preload("res://scenes/space3d/space_sheets.gd")
const SpaceRingsScript := preload("res://scenes/space3d/space_rings.gd")

# DRAFT-space-layer-gap, Q-246-01 (a): engine layer L (0-based) sits at y = L * LAYER_GAP_WU. Parity-tested against
# scenes/mockups/landscape/field_map_space.gd:22 (tests/test_vg_d_view.gd).
const LAYER_GAP_WU := 1000.0
# DRAFT-sheet-thickness plate 60 (kits/space.json plate.thickness): the sheet top a unit stands over is L * gap + 60 on every sheet.
const PLATE_THICKNESS_WU := 60.0
# A unit hovers 150 wu over its sheet top: Units3D.FLYER_CLEARANCE_WU (ground_units.gd:11), read live (d-view spec rev 3, Units bullet).
const UNIT_LIFT_WU := GroundUnits.FLYER_CLEARANCE_WU
# DRAFT-tube-radius, Q-S3-01 (a).
const TUBE_RADIUS_WU := 1500.0
# The next five mirror values that live in the shader or the other units and are pinned here for tests/test_vg_d_view.gd and the play:
# DRAFT-tube-alpha (sheet_tube.gdshader tube_alpha), DRAFT-tube-rim (rim_wu), DRAFT-sheet-dim (SpaceSheets.SHEET_DIM), DRAFT-ring-radius and
# the ring width (SpaceRings.RING_RADIUS_FACTOR, RING_WIDTH_WU).
const TUBE_ALPHA := 0.15
const TUBE_RIM_WU := 10.0
const SHEET_DIM := 0.55
const RING_RADIUS_FACTOR := 1.2
const RING_WIDTH_WU := 6.0
# DRAFT-space-cam-height, gap g2 ruling: the PLAY zooms out through the rig API until the rig reports at least this (the rig has no setter).
const CAM_HEIGHT_WU := 5400.0
# DRAFT-space-frame-budget: Westley's, never widened; measured in the Forward+ play and reported, not asserted here.
const FRAME_BUDGET_MS := 16.0
# d-view spec rev 1, gap 9 null action, Architect may veto on the shot: frame_ms is the mean of 1000 / Engine.get_frames_per_second() over the last 120 frames.
const FRAME_SAMPLES := 120
# State bit 4 = in transit (docs/architecture.md:392); the spawn anchor is the map node of kind 7 (tactical_view.gd SPAWN_NODE_KIND).
const STATE_TRANSIT_BIT := 4
const SPAWN_NODE_KIND := 7

# QA/test seam: false stops _process from reading the window's mouse, cursor_px is then set by the caller.
var follow_mouse := true
var cursor_px := Vector2.ZERO

var _container: SubViewportContainer
var _viewport: SubViewport
var _rig: Node3D
var _units3d: Node3D
var _sheets: Node3D
var _rings: Node3D
var _frame: Dictionary = {}
var _field_set := false
var _panned := false
var _focus := 0
var _tube := {"active": false, "cx": 0.0, "cy": 0.0, "radius_wu": TUBE_RADIUS_WU}
var _unit_info: Dictionary = {}
# id -> tick of the first frame the unit was seen in transit (d-view spec rev 1, gap 6 null action, Architect may veto on the shot)
var _transit_t0: Dictionary = {}
var _frame_ms: Array = []


func _ready() -> void:
	_container = SubViewportContainer.new()
	_container.stretch = true
	_container.size = GroundHost.SCREEN_SIZE
	_container.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_container.z_index = -1
	add_child(_container)
	_viewport = SubViewport.new()
	_viewport.size = GroundHost.SCREEN_SIZE
	_viewport.own_world_3d = true
	_container.add_child(_viewport)
	var env := Environment.new()
	env.background_mode = Environment.BG_COLOR
	env.background_color = _sky_colour()
	env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	# ground3d.gd:51, the same ambient colour as the ground shell.
	env.ambient_light_color = Color(0.6, 0.6, 0.65)
	var we := WorldEnvironment.new()
	we.environment = env
	_viewport.add_child(we)
	var sun := DirectionalLight3D.new()
	sun.rotation_degrees = GroundHost.SUN_ROTATION_DEG
	_viewport.add_child(sun)
	_rig = CameraRig.new()
	_rig.process_mode = Node.PROCESS_MODE_DISABLED
	_viewport.add_child(_rig)
	_sheets = SpaceSheetsScript.new()
	_viewport.add_child(_sheets)
	_units3d = GroundUnits.new()
	_viewport.add_child(_units3d)
	_rings = SpaceRingsScript.new()
	_viewport.add_child(_rings)


# The kit's own sky ("palette.sky" of kits/space.json, the pass 6 look); the ground shell's sky when the kit cannot be read.
func _sky_colour() -> Color:
	var f := FileAccess.open(SpaceSheetsScript.KIT_PATH, FileAccess.READ)
	var kit = JSON.parse_string(f.get_as_text()) if f != null else null
	if kit is Dictionary and kit.has("palette"):
		return Color.html(str(kit["palette"]["sky"]))
	return GroundHost.SKY_COLOUR


func _process(_delta: float) -> void:
	_frame_ms.append(1000.0 / maxf(float(Engine.get_frames_per_second()), 1.0))
	if _frame_ms.size() > FRAME_SAMPLES:
		_frame_ms.pop_front()
	if follow_mouse:
		cursor_px = get_viewport().get_mouse_position()
	_update_tube()


# Once per frame: the tube centre is the cursor ray's hit on the focus sheet plane; the sheets above the focus sheet fade inside it.
func _update_tube() -> void:
	if not _field_set:
		return
	var hit = to_world(cursor_px)
	var active: bool = hit != null
	var centre: Vector2 = hit if active else Vector2.ZERO
	_sheets.set_tube(active, centre, TUBE_RADIUS_WU, _focus * LAYER_GAP_WU)
	_tube = {"active": active, "cx": centre.x, "cy": centre.y, "radius_wu": TUBE_RADIUS_WU}


# Once after mission_begin: the host passes SimSession.bridge().space_field().
func set_field(field: Dictionary) -> void:
	_sheets.build(field)
	_field_set = true


func set_focus_layer(n: int) -> void:
	if n == _focus:
		return
	_focus = n
	_sheets.set_focus_layer(n)


func camera_rig() -> Node3D:
	return _rig


func add_layer(node: Node3D) -> void:
	_viewport.add_child(node)


func _sheet_top(layer: int) -> float:
	return layer * LAYER_GAP_WU + PLATE_THICKNESS_WU


# Own units always, enemies only when in frame.visible[str(player_faction)] (as Ground3D.set_frame filters).
func set_frame(frame: Dictionary, _mission: Dictionary) -> void:
	_frame = frame
	var local := int(frame.get("player_faction", 0))
	_units3d.local_faction = local
	var seen := {}
	for v in frame.get("visible", {}).get(str(local), []):
		seen[int(v)] = true
	var drawn: Array = []
	var own: Array = []
	for u in frame.get("units", []):
		if int(u.get("faction", 0)) == local:
			own.append(u)
		if int(u.get("faction", 0)) == local or seen.has(int(u.get("id"))):
			drawn.append(u)
	if not _panned and _pan_to_spawn(frame, own):
		_panned = true
	var floors: Array = []
	for k in range(LayerViewScript.LAYER_COUNT):
		floors.append(_sheet_top(k))
	var flyers: Array = []  # every type is one flyer body for now (d-view spec, Units bullet)
	for u in drawn:
		if not flyers.has(int(u.get("type", 0))):
			flyers.append(int(u.get("type", 0)))
	_units3d.set_units(drawn, {}, floors, flyers)
	var tick := int(frame.get("tick", 0))
	var items: Array = []
	var info := {}
	var in_transit := {}
	for u in drawn:
		var id := int(u.get("id"))
		var layer := clampi(int(u.get("layer", 0)), 0, LayerViewScript.LAYER_COUNT - 1)
		var dest := -1
		var y := _sheet_top(layer) + UNIT_LIFT_WU
		if (int(u.get("state", 0)) & STATE_TRANSIT_BIT) != 0 and u.has("tl"):
			dest = clampi(int(u["tl"]), 0, LayerViewScript.LAYER_COUNT - 1)
			in_transit[id] = true
			if not _transit_t0.has(id):
				_transit_t0[id] = tick
			var t0 := int(_transit_t0[id])
			var ld := int(u.get("ld", t0))
			var frac := 0.0 if ld == t0 else clampf(float(tick - t0) / float(ld - t0), 0.0, 1.0)
			y = lerpf(y, _sheet_top(dest) + UNIT_LIFT_WU, frac)
		var node: Node3D = _units3d.unit_node(id)
		if node != null:
			node.position.y = y
		var shadow: Node3D = _units3d.shadow_of(id)
		if shadow != null:
			shadow.position.y = _sheet_top(layer) + GroundUnits.SHADOW_LIFT_WU  # on its own sheet top, never under sheet 0
		items.append({"id": id, "x": float(u.get("x", 0.0)), "y": float(u.get("y", 0.0)), "layer": layer, "dest_layer": dest})
		info[str(id)] = {"layer": layer, "y": y, "ring_layer": layer, "dest_ring_layer": dest}
	for id in _transit_t0.keys():
		if not in_transit.has(id):
			_transit_t0.erase(id)
	_unit_info = info
	_rings.update(items)


# The player's spawn anchor: the kind-7 map node nearest the centroid of the own units (A18 gap ruling G3, tactical_view.gd).
# Only once per field, so the player's own panning is never undone. No own unit or no such node leaves the rig where it is
# (nothing ruled for that case; it does not arise in a live space mission).
func _pan_to_spawn(frame: Dictionary, own: Array) -> bool:
	if own.is_empty():
		return false
	var c := Vector2.ZERO
	for u in own:
		c += Vector2(float(u.get("x", 0.0)), float(u.get("y", 0.0)))
	c /= own.size()
	var best := Vector2.ZERO
	var best_d := INF
	for n in frame.get("map", {}).get("nodes", []):
		if int(n.get("kind", -1)) != SPAWN_NODE_KIND:
			continue
		var p := Vector2(float(n.get("x", 0.0)), float(n.get("y", 0.0)))
		if p.distance_squared_to(c) < best_d:
			best_d = p.distance_squared_to(c)
			best = p
	if best_d == INF:
		return false
	_rig.pan_to(best)
	return true


# The camera projection of the world point (wx, wy) on the sheet of `layer` (y = layer * gap); a negative layer is the FOCUS sheet
# (d-view spec rev 3, Hosting "Planes": markers, fog, shots, clicks and the daemon project verb use the focus sheet).
func to_screen(wx: float, wy: float, layer: int = -1) -> Vector2:
	var l := _focus if layer < 0 else layer
	return _rig.get_camera().unproject_position(Vector3(wx, l * LAYER_GAP_WU, wy))


# The camera ray through `screen` meets the FOCUS sheet plane y = focus * gap: the view's own ray test, not physics. Null when the
# ray does not reach the plane (the camera is below it or the ray points up).
func to_world(screen: Vector2) -> Variant:
	var cam: Camera3D = _rig.get_camera()
	var o := cam.project_ray_origin(screen)
	var d := cam.project_ray_normal(screen)
	if d.y >= 0.0:
		return null
	var t := (_focus * LAYER_GAP_WU - o.y) / d.y
	if t < 0.0:
		return null
	return Vector2(o.x + d.x * t, o.z + d.z * t)


func qa_state() -> Dictionary:
	var out := {"ground3d": {"present": false}, "space3d": {"present": false}, "units_px": {}}
	if not _field_set:
		return out
	var sheets: Array = []
	for c in _sheets.counts():
		sheets.append({"layer": c["layer"], "y": c["y"], "blocked_cells": c["blocked_cells"], "slabs": c["slabs"]})
	var q: Dictionary = _rig.qa_camera()
	var cam: Camera3D = _rig.get_camera()
	var ms := 0.0
	for m in _frame_ms:
		ms += float(m)
	var tube := _tube.duplicate()
	tube["faded_layers"] = _sheets.faded_layers()
	out["space3d"] = {
		"present": true,
		"gap_wu": LAYER_GAP_WU,
		"focus_layer": _focus,
		"sheets": sheets,
		"units": _unit_info.duplicate(true),
		"tube": tube,
		"camera": {"x": q["x"], "y": q["y"], "height": _rig.camera_height(), "pitch": -rad_to_deg(cam.rotation.x)},
		"frame_ms": ms / _frame_ms.size() if _frame_ms.size() > 0 else 0.0,
	}
	var upx := {}
	for u in _frame.get("units", []):
		var p := to_screen(float(u.get("x", 0.0)), float(u.get("y", 0.0)), clampi(int(u.get("layer", 0)), 0, LayerViewScript.LAYER_COUNT - 1))
		upx[str(int(u.get("id")))] = [p.x, p.y]
	out["units_px"] = upx
	return out
