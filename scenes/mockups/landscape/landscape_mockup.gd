extends Node3D

const QaPlants := preload("res://scenes/mockups/_shared/qa_plants.gd")
const CITY_RADIUS_WU := 2000.0

const PLANTS: Array[String] = [
	"seed-ignored",
	"overlay-screen-space",
	"stability-noop",
	"flat-terrain",
	"city-disc",
	"regen-stall",
	"space-no-carve",
	"space-independent-layers",
]

var _hud
var _camera_rig
var _map_view: Control


func _ready() -> void:
	_hud = get_node("HUD")
	_camera_rig = get_node("CameraRig")
	_map_view = get_node("HUD/MapView")


func qa_state() -> Dictionary:
	var fm: FieldMap = _hud.get_field_map()
	var camera: Camera3D = _camera_rig.get_camera()

	var core_pos := Vector3.ZERO
	if fm != null:
		for n in fm.nodes:
			if n.type == "objective":
				core_pos = Vector3(n.pos.x, 0.0, n.pos.y)
				break

	var elev_max := 0.0
	if fm != null:
		elev_max = -INF
		for cell in fm.grid:
			elev_max = max(elev_max, cell.elevation)

	var overlay_node: Node3D = _map_view.get_overlay_node()
	var overlay: Dictionary
	if overlay_node:
		overlay = {
			"parent_class": overlay_node.get_parent().get_class(),
			"parent_path": String(get_path_to(overlay_node.get_parent())),
			"visible": overlay_node.visible,
		}
	else:
		overlay = {"parent_class": "", "parent_path": "", "visible": false}

	var city := {"footprint_aspect": 1.0, "fraction_within_r_of_core": 0.0}
	if fm != null:
		city = _compute_city_stats(fm, core_pos)

	var objective_px := Vector2.ZERO
	if camera != null:
		objective_px = camera.unproject_position(core_pos)

	var state := {
		"seed": _hud.get_seed(),
		"hash": fm.compute_hash() if fm != null else 0,
		"canvas_wu": _hud.get_canvas_wu(),
		"stability": _hud.get_stability(),
		"kit": _hud.get_kit_name(),
		"band": _camera_rig.get_current_band(),
		"camera_height": _camera_rig.get_height(),
		"elevation_max_wu": elev_max,
		"overlay": overlay,
		"city": city,
		"timing_ms": _hud.get_timing_ms(),
		"regen_count": _hud.get_regen_count(),
		"piece_total": _hud.get_piece_total(),
		"objective_px": [objective_px.x, objective_px.y],
	}
	if fm is SpaceFieldMap:
		var layer_blocked_pct: Array = []
		for stat in fm.layer_stats:
			layer_blocked_pct.append(stat.blocked * 100.0)
		state["density"] = fm.density
		state["layer_blocked_pct"] = layer_blocked_pct
		state["pockets_filled"] = fm.pockets_filled
		state["tunnels_cut"] = fm.tunnels_cut
		state["regions_unreachable_after"] = fm.regions_unreachable_after
		state["crossing_pct"] = fm.crossing_pct
		state["crossing_marks"] = fm.crossings.size()
		state["focus_layer"] = _hud.get_focus_layer()
	return state


func qa_plant(id: String) -> bool:
	if not PLANTS.has(id):
		return false
	QaPlants.activate(id)
	_hud.qa_regenerate()
	return true


func qa_seed(n: int) -> void:
	_hud.qa_seed(n)


func qa_set(name: String, value) -> void:
	match name:
		"stability":
			_hud.qa_set_stability(float(value))
		"kit":
			_hud.qa_set_kit(String(value))
		"density":
			_hud.qa_set_density(float(value))
		"focus":
			_hud.qa_set_focus(int(value))


func qa_camera(height: float, x: float, z: float) -> void:
	_camera_rig.pan_to(Vector3(x, 0.0, z))
	_camera_rig.set_height(height)


func _compute_city_stats(fm: FieldMap, core_pos: Vector3) -> Dictionary:
	var min_x := INF
	var max_x := -INF
	var min_y := INF
	var max_y := -INF
	var total := 0
	var within := 0
	var core2 := Vector2(core_pos.x, core_pos.z)
	var dim: int = fm.dim
	for gy in range(dim):
		for gx in range(dim):
			var cell: Dictionary = fm.grid[gy * dim + gx]
			if cell.district < 1:
				continue
			var wpos := Vector2(gx, gy) * FieldMap.SPACING
			min_x = min(min_x, wpos.x)
			max_x = max(max_x, wpos.x)
			min_y = min(min_y, wpos.y)
			max_y = max(max_y, wpos.y)
			total += 1
			if wpos.distance_to(core2) <= CITY_RADIUS_WU:
				within += 1

	if total == 0:
		return {"footprint_aspect": 1.0, "fraction_within_r_of_core": 0.0}

	var w: float = max_x - min_x
	var h: float = max_y - min_y
	var aspect := 1.0
	if min(w, h) > 0.001:
		aspect = max(w, h) / min(w, h)

	return {
		"footprint_aspect": aspect,
		"fraction_within_r_of_core": float(within) / float(total),
	}
