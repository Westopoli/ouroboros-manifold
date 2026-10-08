extends Node2D

const SCREEN_CENTER := Vector2(960.0, 540.0)
const PRIMARY_COLOR := Color(0.3, 0.85, 1.0)
const SECONDARY_COLOR := Color(0.4, 0.5, 0.6)
const DONE_COLOR := Color(0.35, 0.9, 0.4)
const FAILED_COLOR := Color(0.9, 0.25, 0.2)
const BEAM_PX := 60.0
const BEAM_WIDTH := 4.0
const RING_WIDTH := 2.0
const RING_SEGMENTS := 64

var _beacons: Array = []
var _rings: Array = []


func _ready() -> void:
	name = "ObjectiveMarkers"


func set_frame(frame: Dictionary, mission: Dictionary, _local_faction: int, world_scale: float, camera: Vector2) -> void:
	_beacons = []
	_rings = []
	var nodes := {}
	for n in frame.get("map", {}).get("nodes", []):
		nodes[int(n["i"])] = Vector2(float(n["x"]), float(n["y"]))
	var states := {}
	for o in frame.get("objectives", []):
		states[int(o["i"])] = int(o["done"])
	for o in mission.get("objectives", []):
		var node := int(o.get("node", -1))
		if not nodes.has(node):
			continue
		var i := int(o["i"])
		var state: int = states.get(i, 0)
		var c: Vector2 = (nodes[node] - camera) * world_scale + SCREEN_CENTER
		var col := PRIMARY_COLOR if o.get("primary", false) else SECONDARY_COLOR
		if state == 1:
			col = DONE_COLOR
		elif state == 2:
			col = FAILED_COLOR
		_beacons.append({"objective": i, "center": c, "state": state, "color": col})
		var radius := float(o.get("radius", 0.0))
		if radius > 0.0:
			_rings.append({"objective": i, "center": c, "radius": radius * world_scale, "color": col})
	queue_redraw()


func beacons() -> Array:
	return _beacons


func rings() -> Array:
	return _rings


func _draw() -> void:
	for r in _rings:
		var col: Color = r["color"]
		draw_arc(r["center"], r["radius"], 0.0, TAU, RING_SEGMENTS, Color(col, 0.6), RING_WIDTH)
	for b in _beacons:
		var col: Color = b["color"]
		var c: Vector2 = b["center"]
		draw_line(c, c - Vector2(0.0, BEAM_PX), Color(col, 0.5), BEAM_WIDTH)
		draw_circle(c, 6.0, col)
