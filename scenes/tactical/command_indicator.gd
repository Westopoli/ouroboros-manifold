## Transient ground decal for move/attack-move commands per stage_11d D4.
## Fades out and self-deletes after LIFETIME seconds.
## See also: scenes/tactical/tactical.gd — spawns these on command_sent signal.
extends Node3D

const LIFETIME := 1.5
const RADIUS := 40.0
const MOVE_COLOR := Color(0.8, 0.9, 1.0, 0.6)
const ATTACK_MOVE_COLOR := Color(1.0, 0.3, 0.3, 0.6)

var _mat: StandardMaterial3D


func setup(world_pos: Vector3, is_attack_move: bool) -> void:
	position = world_pos

	_mat = StandardMaterial3D.new()
	_mat.albedo_color = ATTACK_MOVE_COLOR if is_attack_move else MOVE_COLOR
	_mat.emission_enabled = true
	_mat.emission = _mat.albedo_color
	_mat.emission_energy_multiplier = 1.2
	_mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	_mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	_mat.no_depth_test = true

	if is_attack_move:
		_build_crosshair()
	else:
		_build_circle()

	var tw := create_tween()
	tw.tween_property(_mat, "albedo_color:a", 0.0, LIFETIME)
	tw.parallel().tween_property(_mat, "emission_energy_multiplier", 0.0, LIFETIME)
	tw.tween_callback(queue_free)


func _build_circle() -> void:
	var mesh := TorusMesh.new()
	mesh.inner_radius = RADIUS - 3.0
	mesh.outer_radius = RADIUS
	mesh.rings = 32
	mesh.ring_segments = 32
	var mi := MeshInstance3D.new()
	mi.mesh = mesh
	mi.material_override = _mat
	mi.rotation_degrees.x = 0.0
	add_child(mi)


func _build_crosshair() -> void:
	for angle in [0.0, 90.0]:
		var mesh := BoxMesh.new()
		mesh.size = Vector3(RADIUS * 2.0, 1.0, 4.0)
		var mi := MeshInstance3D.new()
		mi.mesh = mesh
		mi.material_override = _mat
		mi.rotation_degrees.y = angle
		add_child(mi)
