extends "res://tests/support/vg_c_case.gd"

# VG-C piece C10 (fx/shots.gd): S-134 R-134-05, a fire event [0, shooter, target, tick] draws from the projected shooter to the projected target.
# The layer is handed from VG-A to VG-C; it keeps its A-lane frame API and gains set_projector(Callable world wu -> screen px),
# set_frame(frame, mission, local_faction) and screen_points() -> Array of Vector2 (centres it draws at). Radii are
# re-derived through the projector, never multiplied by a flat scale (scout 4). Two projectors are run; each must be followed.
# CONTROL: the other projector's image of the same point must be absent.


func _run() -> void:
	var fx := _fixture()
	var fire: Dictionary = fx.frame().duplicate(true)
	fire["tick"] = 11
	fire["events"] = [[0, 1, 3, 11]]
	await _c10(TCAM + "fx/shots.gd", "S-134", [Vector2(250.0, 250.0), Vector2(550.0, 150.0)], [fx.frame(), fire])
