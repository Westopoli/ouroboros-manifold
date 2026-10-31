extends Node

## H-025 layout shot: draws one catalogue layout (JSON path in OM_LAYOUT) on the Ground3D camera rig and Units3D bodies, with the layers as
## stacked translucent planes and a legend. With OM_SHOT_OUT set (a PNG file path) it saves the frame after 30 frames and quits.
## Terrain is flat: the story gives a preset only bounds and a layer count. See also scripts/skilllab/catalogue/presets.toml.

const Ground3DHost := preload("res://scenes/ground3d/ground3d.gd")
const GroundUnits := preload("res://scenes/ground3d/ground_units.gd")
const UnitVisuals := preload("res://scenes/tactical_c/unit_visuals.gd")

const SCENE_PATH := "res://scenes/proto/layout_shot/layout_shot.tscn"
const PRESETS_PATH := "res://scripts/skilllab/catalogue/presets.toml"
const ROLES := ["Raider", "Interceptor", "Vanguard", "Warden", "Bombard", "Bastion"]  # scripts/skilllab/engine.py:16; index = unit type id
const CELL_WU := 100.0
const SHOT_FRAMES := 30
const LAYER_SPACING_WU := 600.0  # DRAFT-shot-layer-spacing-wu: floor of layer k, a drawing number only
const PLANE_LIFT_WU := 1.5  # layer 0's plane floats this far over the ground mesh
const PLANE_COLOURS := [Color(0.9, 0.9, 0.9, 0.10), Color(1.0, 0.85, 0.3, 0.14), Color(0.4, 0.9, 0.9, 0.14), Color(0.9, 0.5, 0.9, 0.14), Color(1.0, 0.6, 0.4, 0.14)]
const SIDE_COLOURS := {"A": Color(0.2, 0.6, 1.0), "B": Color(1.0, 0.3, 0.3)}
const FRAME_FRACTION := 0.6  # DRAFT-shot-frame: camera height as a fraction of the unit box's longer side
const PAD_WU := 400.0

var _layout: Dictionary = {}
var _units: Array = []
var _legend: Array = []
var _planes: Array = []
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
		floors.append(k * LAYER_SPACING_WU)
	var terrain := _flat_terrain(int(preset["width"]), int(preset["height"]), floors)
	var ground := Ground3DHost.new()
	add_child(ground)
	ground.set_terrain(terrain)
	var units3d := GroundUnits.new()
	units3d.local_faction = 0
	ground.add_layer(units3d)
	var planes := Node3D.new()
	ground.add_layer(planes)
	var frame_units := _collect_units()
	units3d.set_units(frame_units, terrain, floors, [])
	for u in frame_units:
		var layer := int(u["layer"])
		if layer > 0:
			var n: Node3D = units3d.unit_node(int(u["id"]))
			n.position.y = float(floors[mini(layer, layers - 1)]) + GroundUnits.UNIT_GROUND_LIFT_WU
	_planes = _add_planes(planes, int(preset["width"]), int(preset["height"]), floors)
	_frame_camera(ground.camera_rig())
	_add_legend()


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


func _flat_terrain(width: int, height: int, floors: Array) -> Dictionary:
	var w := int(ceil(width / CELL_WU))
	var h := int(ceil(height / CELL_WU))
	var heights := PackedInt32Array()
	heights.resize(w * h)
	var bands := PackedByteArray()
	bands.resize(w * h)
	bands.fill(1)
	var walk := PackedByteArray()
	walk.resize(w * h)
	walk.fill(1)
	return {"cells_w": w, "cells_h": h, "heights": heights, "bands": bands, "walkable": walk, "layer_floors_wu": floors, "flyer_types": []}


func _collect_units() -> Array:
	var out: Array = []
	var id := 0
	var seen := {}
	for side in ["A", "B"]:
		for row in _layout["side_" + side.to_lower()]["units"]:
			var role := String(row["role"])
			out.append({"id": id, "faction": 0 if side == "A" else 1, "type": maxi(ROLES.find(role), 0), "x": float(row["x"]), "y": float(row["y"]),
					"facing": float(row["facing"]), "layer": int(row["layer"])})
			_units.append({"id": id, "side": side, "role": role, "layer": int(row["layer"]), "x": float(row["x"]), "y": float(row["y"]),
					"facing": float(row["facing"])})
			seen[role] = true
			id += 1
	for r in ROLES:
		if seen.has(r):
			_legend.append(r)
	return out


func _add_planes(parent: Node3D, width: int, height: int, floors: Array) -> Array:
	var out: Array = []
	for k in floors.size():
		var mesh := PlaneMesh.new()
		mesh.size = Vector2(width, height)
		var mat := StandardMaterial3D.new()
		mat.albedo_color = PLANE_COLOURS[mini(k, PLANE_COLOURS.size() - 1)]
		mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
		mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
		mat.cull_mode = BaseMaterial3D.CULL_DISABLED
		var mi := MeshInstance3D.new()
		mi.mesh = mesh
		mi.material_override = mat
		mi.position = Vector3(width * 0.5, float(floors[k]) + (PLANE_LIFT_WU if k == 0 else 0.0), height * 0.5)
		parent.add_child(mi)
		out.append(mi)
	return out


func _frame_camera(rig: Node3D) -> void:
	var lo := Vector2(INF, INF)
	var hi := Vector2(-INF, -INF)
	for u in _units:
		lo = Vector2(minf(lo.x, u["x"]), minf(lo.y, u["y"]))
		hi = Vector2(maxf(hi.x, u["x"]), maxf(hi.y, u["y"]))
	lo -= Vector2(PAD_WU, PAD_WU)
	hi += Vector2(PAD_WU, PAD_WU)
	rig.pan_to((lo + hi) * 0.5)
	var want := maxf(hi.x - lo.x, hi.y - lo.y) * FRAME_FRACTION
	rig.zoom_by(int(round((want - rig.camera_height()) / rig.ZOOM_STEP)))


func _add_legend() -> void:
	var layer := CanvasLayer.new()
	add_child(layer)
	var panel := PanelContainer.new()
	panel.position = Vector2(24.0, 24.0)
	layer.add_child(panel)
	var box := VBoxContainer.new()
	panel.add_child(box)
	box.add_child(_label("%s  %s  %s  A %d : B %d" % [_layout["id"], _layout["situation"], _layout["landscape"], _layout["side_a"]["headcount"], _layout["side_b"]["headcount"]], Color.WHITE))
	box.add_child(_label("A (blue)", SIDE_COLOURS["A"]))
	box.add_child(_label("B (red)", SIDE_COLOURS["B"]))
	box.add_child(_label("layers: %d (stacked planes)" % _planes.size(), Color.WHITE))
	for role in _legend:
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
		row.add_child(_label(role, Color.WHITE))
		box.add_child(row)


func _label(text: String, colour: Color) -> Label:
	var l := Label.new()
	l.text = text
	l.add_theme_font_size_override("font_size", 22)
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
	var visible := not _planes.is_empty()
	for p in _planes:
		visible = visible and p.visible
	return {"scene": SCENE_PATH, "layout_id": String(_layout.get("id", "")), "unit_count": _units.size(), "units": _units, "legend": _legend,
			"layers_visible": visible}
