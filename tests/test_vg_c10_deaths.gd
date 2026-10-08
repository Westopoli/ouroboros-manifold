extends "res://tests/support/vg_c_case.gd"

# VG-C piece C10 (fx/deaths.gd): S-136 R-136-01, a kill event [2, unit, killer, tick] blooms at the projected last position of the dead unit.
# The layer is handed from VG-A to VG-C; it keeps its A-lane frame API and gains set_projector(Callable world wu -> screen px),
# set_frame(frame, mission, local_faction) and screen_points() -> Array of Vector2 (centres it draws at). Radii are
# re-derived through the projector, never multiplied by a flat scale (scout 4). Two projectors are run; each must be followed.
# CONTROL: the other projector's image of the same point must be absent.


func _run() -> void:
	var fx := _fixture()
	var dead: Dictionary = fx.frame().duplicate(true)
	dead["tick"] = 12
	dead["units"] = dead["units"].filter(func(u): return int(u["id"]) != 4)
	dead["events"] = [[2, 4, -1, 12]]
	await _c10(TCAM + "fx/deaths.gd", "S-136", [Vector2(350.0, 450.0)], [fx.frame(), dead])
