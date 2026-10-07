extends "res://tests/support/vg_c_case.gd"

# VG-C piece C10 (objective_markers.gd): S-075, a beacon sits at each projected objective node.
# The layer is handed from VG-A to VG-C; it keeps its A-lane frame API and gains set_projector(Callable world wu -> screen px),
# set_frame(frame, mission, local_faction) and screen_points() -> Array of Vector2 (centres it draws at). Radii are
# re-derived through the projector, never multiplied by a flat scale (scout 4). Two projectors are run; each must be followed.
# CONTROL: the other projector's image of the same point must be absent.


func _run() -> void:
	var fx := _fixture()

	await _c10(TCAM + "objective_markers.gd", "S-075", [Vector2(300.0, 300.0), Vector2(600.0, 400.0)], [fx.frame()])
