extends Node3D
class_name SlopesView

## Slopes, blocked ground and layer transitions in the 3D ground (visible-game lane C, C7; R-001-06, R-004-06,
## R-001-01, Q-S3-02). A slope is ground joining two layers, marked at its midline. A unit mid-transition (state
## bit 4) gets two circles: one on the unit, one at the Y of the layer it is moving to.

const GroundPick := preload("res://scenes/ground3d/ground_pick.gd")

const TRANSIT_BIT := 4
# Named draft: wu of Y per layer step for the target circle; the only altitude the spec gives is the flyer's +150 wu.
const LAYER_STEP_WU := 150.0
const MIDLINE_COLOUR := Color(1.0, 1.0, 1.0)
const CIRCLE_RADIUS := 30.0

var _terrain: Dictionary = {}
var _midlines: Array = []
var _blocked: Array = []
var _transit: Array = []
var _midline_nodes: Array = []
var _circle_nodes: Array = []


func set_terrain(t: Dictionary) -> void:
	_terrain = t
	for n in _midline_nodes:
		n.queue_free()
	_midline_nodes.clear()
	_midlines.clear()
	_blocked.clear()
	if t.is_empty():
		return
	for s in t.get("slopes", []):
		var p := GroundPick.world_to_3d(t, float(s["mx"]), float(s["my"]))
		_midlines.append(p)
		var bar := MeshInstance3D.new()
		var box := BoxMesh.new()
		box.size = Vector3(float(s.get("length", 100.0)), 2.0, 4.0)
		bar.mesh = box
		bar.material_override = _flat(MIDLINE_COLOUR)
		bar.position = p
		bar.rotation.y = -atan2(float(s["y1"]) - float(s["y0"]), float(s["x1"]) - float(s["x0"]))
		add_child(bar)
		_midline_nodes.append(bar)
	var walk: PackedByteArray = t.get("walkable", PackedByteArray())
	for i in walk.size():
		if walk[i] == 0:
			_blocked.append(i)


func set_units(units: Array) -> void:
	for n in _circle_nodes:
		n.queue_free()
	_circle_nodes.clear()
	_transit.clear()
	for u in units:
		if (int(u.get("state", 0)) & TRANSIT_BIT) == 0:
			continue
		_transit.append(int(u["id"]))
		if _terrain.is_empty():
			continue
		var x := float(u["x"])
		var y := float(u["y"])
		var ground := GroundPick.height_at(_terrain, x, y)
		var dl := int(u.get("tl", u.get("layer", 0))) - int(u.get("layer", 0))
		_circle(Vector3(x, ground, y))
		_circle(Vector3(x, ground + dl * LAYER_STEP_WU, y))


func midline_count() -> int:
	return _midlines.size()


func midline_world(i: int) -> Vector3:
	return _midlines[i]


func blocked_cells() -> Array:
	return _blocked.duplicate()


func in_transit_ids() -> Array:
	return _transit.duplicate()


func qa_state() -> Dictionary:
	return {
		"slopes": (_terrain.get("slopes", []) as Array).size(),
		"midlines": _midlines.size(),
		"blocked_cells": _blocked.size(),
		"in_transit": _transit.size(),
	}


func _circle(p: Vector3) -> void:
	var m := MeshInstance3D.new()
	var d := CylinderMesh.new()
	d.top_radius = CIRCLE_RADIUS
	d.bottom_radius = CIRCLE_RADIUS
	d.height = 1.0
	m.mesh = d
	m.material_override = _flat(MIDLINE_COLOUR)
	m.position = p
	add_child(m)
	_circle_nodes.append(m)


static func _flat(c: Color) -> StandardMaterial3D:
	var mat := StandardMaterial3D.new()
	mat.albedo_color = c
	mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	return mat
