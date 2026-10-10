extends Node3D
class_name SettlementLayer

## Skeleton of the settlement layer (visible-game lane E1, S-193): one box per sim lot, all the same size,
## tinted by owner. No stages, cliffs, streets or easing yet: those are E1k, same file, after the verdict.
## See also: spec Part b under method rev 2 (docs/northstar/plans/2026-10-07-visible-game-spec.md).

const GroundPick := preload("res://scenes/ground3d/ground_pick.gd")
const StructuresLayer := preload("res://scenes/tactical_c/structures_layer.gd")

const BOX_FOOTPRINT_WU := 100.0 # liberty 2026-10-10: one 100 wu cell
const BOX_HEIGHT_WU := 60.0 # liberty 2026-10-10

var local_faction := 0
var _terrain: Dictionary = {}
var _has_terrain := false
var _lots: Array = []
var _has_frame := false
var _mmi: MultiMeshInstance3D
var _drawn: Array = []


func _ready() -> void:
	name = "SettlementLayer"


func set_terrain(t: Dictionary) -> void:
	_terrain = t
	_has_terrain = true
	_sync()


func set_frame(frame: Dictionary) -> void:
	_lots = frame.get("lots", [])
	_has_frame = true
	_sync()


func lots_drawn() -> Array:
	return _drawn.duplicate(true)


func _owner_color(owner_id: int) -> Color:
	if owner_id < 0:
		return StructuresLayer.NEUTRAL_COLOR
	return StructuresLayer.OWN_COLOR if owner_id == local_faction else StructuresLayer.ENEMY_COLOR


func _sync() -> void:
	if not (_has_terrain and _has_frame):
		return
	var sorted := _lots.duplicate()
	sorted.sort_custom(func(a, b): return int(a["id"]) < int(b["id"]))
	if _mmi == null:
		_mmi = MultiMeshInstance3D.new()
		var mm := MultiMesh.new()
		mm.transform_format = MultiMesh.TRANSFORM_3D
		mm.use_colors = true
		var box := BoxMesh.new()
		box.size = Vector3.ONE
		var mat := StandardMaterial3D.new()
		mat.vertex_color_use_as_albedo = true
		box.material = mat
		mm.mesh = box
		_mmi.multimesh = mm
		add_child(_mmi)
	var mm := _mmi.multimesh
	mm.instance_count = sorted.size()
	_drawn = []
	for i in sorted.size():
		var l: Dictionary = sorted[i]
		# Placement as Units3D.set_units (scenes/ground3d/ground_units.gd:87-91, 101): world x,y -> 3D x,z, ground height from height_at.
		var p := GroundPick.world_to_3d(_terrain, float(l.get("x", 0.0)), float(l.get("y", 0.0)))
		var basis := Basis.from_scale(Vector3(BOX_FOOTPRINT_WU, BOX_HEIGHT_WU, BOX_FOOTPRINT_WU))
		mm.set_instance_transform(i, Transform3D(basis, p + Vector3(0.0, BOX_HEIGHT_WU * 0.5, 0.0)))
		mm.set_instance_color(i, _owner_color(int(l.get("owner", -1))))
		_drawn.append({"id": int(l["id"]), "x": float(l.get("x", 0.0)), "y": float(l.get("y", 0.0)), "stage": int(l.get("stage", 0)), "building": int(l.get("building", 0)), "owner": int(l.get("owner", -1))})
