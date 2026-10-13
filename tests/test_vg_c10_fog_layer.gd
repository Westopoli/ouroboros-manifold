extends "res://tests/support/vg_c_case.gd"

# VG-C piece C10 (fog_layer.gd): S-005 R-089-04 / S-091, own units' sight discs are drawn at the projected unit positions.
# The layer is handed from VG-A to VG-C; it keeps its A-lane frame API and gains set_projector(Callable world wu -> screen px),
# set_frame(frame, mission, local_faction) and screen_points() -> Array of Vector2 (centres it draws at). Radii are
# re-derived through the projector, never multiplied by a flat scale (scout 4). Two projectors are run; each must be followed.
# CONTROL: the other projector's image of the same point must be absent.


func _run() -> void:
	var fx := _fixture()

	await _c10(TCAM + "fog_layer.gd", "S-091", [Vector2(250.0, 250.0), Vector2(450.0, 350.0), Vector2(350.0, 450.0)], [fx.frame()])
