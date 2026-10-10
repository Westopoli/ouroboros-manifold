extends Node
class_name Ground3D

## SubViewport host for the 3D ground (visible-game lane C, C5; S-236 R-236-01). Holds the C2/C2b mesh and the
## C3 rig inside its own world, shown through a SubViewportContainer under the 2D shell. The rig is driven by the
## owner (process disabled): the tactical view pans and zooms it and reads camera {x,y} and scale back as the map
## band's equivalents (rulebook rows 3, 5, 12, 31). units_px and objects_px stay screen pixels.

const GroundMesh := preload("res://scenes/ground3d/ground_mesh.gd")
const CameraRig := preload("res://scenes/ground3d/camera_rig_3d.gd")
const GroundProjection := preload("res://scenes/ground3d/projection.gd")
const GroundUnits := preload("res://scenes/ground3d/ground_units.gd")
const SlopeViewNode := preload("res://scenes/ground3d/slope_view.gd")

const SCREEN_SIZE := Vector2(1920.0, 1080.0)
const SKY_COLOUR := Color(0.55, 0.68, 0.82)
const SUN_ROTATION_DEG := Vector3(-55.0, -35.0, 0.0)

var _terrain: Dictionary = {}
var _frame: Dictionary = {}
var _mission: Dictionary = {}
var _vertices := 0
var _container: SubViewportContainer
var _viewport: SubViewport
var _mesh: MeshInstance3D
var _rig: Node3D
var _units3d: Node3D
var _slope_view: Node3D
var _layers: Array = []
var _units_drawn := 0


func _ready() -> void:
	_container = SubViewportContainer.new()
	_container.stretch = true
	_container.size = SCREEN_SIZE
	_container.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_container.z_index = -1
	add_child(_container)
	_viewport = SubViewport.new()
	_viewport.size = SCREEN_SIZE
	_viewport.own_world_3d = true
	_container.add_child(_viewport)
	var env := Environment.new()
	env.background_mode = Environment.BG_COLOR
	env.background_color = SKY_COLOUR
	env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	env.ambient_light_color = Color(0.6, 0.6, 0.65)
	var we := WorldEnvironment.new()
	we.environment = env
	_viewport.add_child(we)
	var sun := DirectionalLight3D.new()
	sun.rotation_degrees = SUN_ROTATION_DEG
	_viewport.add_child(sun)
	_rig = CameraRig.new()
	_rig.process_mode = Node.PROCESS_MODE_DISABLED
	_viewport.add_child(_rig)
	_units3d = GroundUnits.new()
	_viewport.add_child(_units3d)
	_slope_view = SlopeViewNode.new()
	_viewport.add_child(_slope_view)


# E1p-a hook: a layer node (SettlementLayer, later StrongpointLayer) lives inside the SubViewport after SlopesView and is
# handed the terrain and the frame when it has set_terrain / set_frame. Units3D is added before SlopesView in _ready, so
# "after SlopesView" also places it after Units3D (3D sibling order has no depth effect); test_vg_e_e1p.gd pins this.
func add_layer(node: Node3D) -> void:
	_viewport.add_child(node)
	_layers.append(node)


func container() -> Control:
	return _container


func camera_rig() -> Node3D:
	return _rig


func terrain() -> Dictionary:
	return _terrain


func set_terrain(t: Dictionary) -> void:
	_terrain = t
	if _mesh != null:
		_mesh.queue_free()
		_viewport.remove_child(_mesh)
		_mesh = null
	_vertices = 0
	_slope_view.set_terrain(t)
	for n in _layers:
		if n.has_method("set_terrain"):
			n.set_terrain(t)
	if t.is_empty():
		_rig.set_terrain({})
		return
	_mesh = GroundMesh.build(t)
	_viewport.add_child(_mesh)
	_vertices = (int(t["cells_w"]) - 1) * (int(t["cells_h"]) - 1) * 6
	_rig.set_terrain(t)


func set_frame(frame: Dictionary, mission: Dictionary) -> void:
	_frame = frame
	_mission = mission
	for n in _layers:
		if n.has_method("set_frame"):
			n.set_frame(frame)
	if _terrain.is_empty():
		return
	var local := int(frame.get("player_faction", 0))
	_units3d.local_faction = local
	var seen := {}
	for v in frame.get("visible", {}).get(str(local), []):
		seen[int(v)] = true
	var own: Array = []
	for u in frame.get("units", []):
		if int(u.get("faction", 0)) == local or seen.has(int(u.get("id"))):
			own.append(u)
	_units_drawn = own.size()
	_units3d.set_units(own, _terrain, _terrain.get("layer_floors_wu", []), _terrain.get("flyer_types", []))
	_slope_view.set_units(frame.get("units", []))


func to_screen(wx: float, wy: float) -> Vector2:
	return GroundProjection.to_screen(_rig.get_camera(), _terrain, wx, wy)


func to_world(screen: Vector2) -> Variant:
	return GroundProjection.to_world(_rig.get_camera(), _terrain, screen)


func objects_px() -> Array:
	var out: Array = []
	var nodes: Array = _frame.get("map", {}).get("nodes", [])
	for o in _mission.get("objectives", []):
		var n := int(o.get("node", -1))
		if n >= 0 and n < nodes.size():
			var p := to_screen(float(nodes[n]["x"]), float(nodes[n]["y"]))
			out.append([p.x, p.y])
	return out


func qa_state() -> Dictionary:
	var out := {"ground3d": {"present": false}, "units_px": {}, "objects_px": []}
	if _terrain.is_empty():
		return out
	var q: Dictionary = _rig.qa_camera()
	out["ground3d"] = {
		"present": true,
		"cells_w": int(_terrain["cells_w"]),
		"cells_h": int(_terrain["cells_h"]),
		"vertices": _vertices,
		"band": _rig.band(),
		"camera_height": _rig.camera_height(),
		"camera": {"x": q["x"], "y": q["y"]},
		"scale": q["scale"],
		"slope_view": _slope_view.qa_state(),
		"units3d": _units_drawn,
		"units3d_heights": _units3d.heights(),
		"units3d_shadows": _units3d.shadow_ids(),
	}
	var upx := {}
	for u in _frame.get("units", []):
		var p := to_screen(float(u.get("x", 0.0)), float(u.get("y", 0.0)))
		upx[str(int(u.get("id")))] = [p.x, p.y]
	out["units_px"] = upx
	out["objects_px"] = objects_px()
	return out
