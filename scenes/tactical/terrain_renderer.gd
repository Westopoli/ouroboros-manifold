## Draws the tactical map: boundary, gradient-source heatmap circles, and
## spine nodes. Debug visualization only — not final art.
## Redraws only when a new snapshot arrives (map data changes infrequently).
extends Node2D

const BOUNDARY_COLOR := Color(0.4, 0.4, 0.4, 0.8)
const BOUNDARY_WIDTH := 6.0

# Gradient property → tint color for the heatmap overlay
const GRADIENT_COLORS: Dictionary = {
	"obstacle_density": Color(0.9, 0.2, 0.1, 0.25),
	"cover_density":    Color(0.1, 0.8, 0.2, 0.20),
	"sensor_interference": Color(0.8, 0.2, 0.9, 0.20),
}
const GRADIENT_DEFAULT_COLOR := Color(0.5, 0.5, 0.5, 0.15)

const SPINE_NODE_COLORS: Dictionary = {
	"objective":    Color(1.0, 0.9, 0.1, 0.9),
	"chokepoint":   Color(0.8, 0.4, 0.1, 0.8),
	"staging":      Color(0.3, 0.7, 1.0, 0.8),
	"extraction":   Color(0.2, 1.0, 0.5, 0.9),
	"vantage_point": Color(0.9, 0.5, 1.0, 0.8),
}
const SPINE_DEFAULT_COLOR := Color(0.8, 0.8, 0.8, 0.7)
const SPINE_RADIUS := 24.0

var _map_width: float = 4000.0
var _map_height: float = 4000.0


func _ready() -> void:
	TacticalBridge.snapshot_received.connect(_on_snapshot)


func _on_snapshot(_snap: Dictionary) -> void:
	var md: Dictionary = TacticalBridge.map_data
	var canvas: Array = md.get("canvas_size", [4000, 4000])
	_map_width = float(canvas[0])
	_map_height = float(canvas[1])
	queue_redraw()


func _draw() -> void:
	var md: Dictionary = TacticalBridge.map_data

	# Map boundary
	draw_rect(Rect2(0, 0, _map_width, _map_height), BOUNDARY_COLOR, false, BOUNDARY_WIDTH)

	# Gradient sources — translucent heatmap circles
	for gs in md.get("gradient_sources", []):
		var pos := Vector2(float(gs["pos"][0]), float(gs["pos"][1]))
		var radius: float = float(gs.get("radius", 200))
		var intensity: float = float(gs.get("intensity", 0.5))
		var prop: String = gs.get("property", "")
		var col: Color = GRADIENT_COLORS.get(prop, GRADIENT_DEFAULT_COLOR)
		col.a *= intensity
		draw_circle(pos, radius, col)

	# Spine nodes — markers with label
	for sn in md.get("spine_nodes", []):
		var pos := Vector2(float(sn["pos"][0]), float(sn["pos"][1]))
		var node_type: String = sn.get("type", "")
		var col: Color = SPINE_NODE_COLORS.get(node_type, SPINE_DEFAULT_COLOR)
		draw_circle(pos, SPINE_RADIUS, col)
		draw_arc(pos, SPINE_RADIUS, 0, TAU, 24, col.lightened(0.3), 2.0)
