## In-world objective beacon per stage_11d D3.
## One instance per active objective with a location.
## See also: scenes/tactical/tactical.gd — spawns/removes these on objective updates.
extends Node3D

const BEAM_HEIGHT := 800.0
const BEAM_RADIUS := 8.0
const PRIMARY_COLOR := Color(0.3, 0.85, 1.0)
const SECONDARY_COLOR := Color(0.4, 0.5, 0.6)

var obj_id: String = ""

var _beam: MeshInstance3D
var _label: Label3D


func setup(obj: Dictionary) -> void:
	obj_id = obj.get("id", "")
	var is_primary: bool = obj.get("is_primary", false)
	var col: Color = PRIMARY_COLOR if is_primary else SECONDARY_COLOR

	_beam = MeshInstance3D.new()
	var cyl := CylinderMesh.new()
	cyl.top_radius = BEAM_RADIUS
	cyl.bottom_radius = BEAM_RADIUS
	cyl.height = BEAM_HEIGHT
	_beam.mesh = cyl
	var mat := StandardMaterial3D.new()
	mat.albedo_color = Color(col.r, col.g, col.b, 0.35)
	mat.emission_enabled = true
	mat.emission = col
	mat.emission_energy_multiplier = 1.5
	mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	mat.no_depth_test = true
	mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	_beam.material_override = mat
	_beam.position.y = BEAM_HEIGHT / 2.0
	add_child(_beam)

	var desc_table: Dictionary = {
		"hold_zone": "Hold the zone",
		"clear_zone": "Clear the zone",
		"eliminate_force": "Destroy enemy force",
		"escort_to_extraction": "Escort to extraction",
		"survive_duration": "Survive",
		"destroy_targets": "Destroy targets",
	}
	_label = Label3D.new()
	_label.text = desc_table.get(obj.get("type", ""), obj.get("type", ""))
	_label.font_size = 48
	_label.modulate = col
	_label.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	_label.no_depth_test = true
	_label.position.y = 120.0
	add_child(_label)

	_apply_position(obj)


func update_objective(obj: Dictionary) -> void:
	_apply_position(obj)


func _apply_position(obj: Dictionary) -> void:
	var loc: Dictionary = obj.get("location", {})
	if loc.is_empty():
		return
	position = Vector3(float(loc.get("x", 0.0)), 0.0, float(loc.get("y", 0.0)))
