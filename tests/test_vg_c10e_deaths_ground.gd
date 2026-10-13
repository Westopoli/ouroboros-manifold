extends "res://tests/support/vg_c_case.gd"

# VG-C piece C10e (fx/deaths.gd, projector mode on the 3D ground): S-136 R-136-01/03 with spec section 7's liberty
# "flyer altitude = layer floor + 150 wu with a shadow disc". Builds on C10 (set_projector, set_frame(frame, mission, faction),
# screen_points()) and adds the ground interface, the same shape as C6's GroundUnits.set_units:
#   set_ground(terrain: Dictionary, layer_floors_wu: Array, flyer_types: Array)
#   wreck_height(id) -> float (wu, Y of the wreck), wreck_shadow(id) -> bool (a flyer's shadow disc is drawn).
# A walker's wreck sits at GroundPick.height_at(terrain, wreck x, y). A flyer's wreck starts at layer floor + 150 wu with a
# shadow disc and falls to the ground height; its shadow disc is gone once it lands. DRAFT (nobody gave a fall time): landed
# by LANDED_S = 20.0 s, inside the 30 s fade. Drift stays along the heading through the projector; CAP 150 / LOD 60 unchanged.
# CONTROL: a flyer's wreck is above ground at age 0; the other projector's image of the drifted point is absent.

const LANDED_S := 20.0
const FLOORS := [0.0, 100.0, 400.0, 800.0, 1200.0]


func _kill_frames(fx: GDScript, id: int, facing: float) -> Array:
	var before: Dictionary = fx.frame().duplicate(true)
	for u in before["units"]:
		if int(u["id"]) == id:
			u["facing"] = facing
	var dead: Dictionary = before.duplicate(true)
	dead["tick"] = 12
	dead["units"] = dead["units"].filter(func(u): return int(u["id"]) != id)
	dead["events"] = [[2, id, -1, 12]]
	return [before, dead]


func _layer(s: GDScript, fx: GDScript, proj: Callable) -> Node:
	var layer = s.new()
	root.add_child(layer)
	await process_frame
	layer.set_projector(proj)
	layer.set_ground(fx.terrain(), FLOORS, [1])
	return layer


func _run() -> void:
	var s := _load(TCAM + "fx/deaths.gd")
	var gp := _load(SCENES + "ground_pick.gd")
	if s == null or gp == null:
		return
	var fx := _fixture()
	var t: Dictionary = fx.terrain()
	_check(s.CAP == 150 and s.LOD_WRECKS == 60 and s.FADE_S == 30.0, "R-136-03: lane A cap 150 / LOD 60 / fade 30 s must hold unchanged")
	var probe = s.new()
	root.add_child(probe)
	await process_frame
	_check(probe.has_method("set_projector") and probe.has_method("set_ground") and probe.has_method("wreck_height") and probe.has_method("wreck_shadow") and probe.has_method("screen_points"), "S-136: fx/deaths.gd lacks set_projector/set_ground/wreck_height/wreck_shadow/screen_points (projector mode not built)")
	if not (probe.has_method("set_projector") and probe.has_method("set_ground") and probe.has_method("wreck_height") and probe.has_method("wreck_shadow")):
		return
	for pair in [[Callable(self, "proj_a"), Callable(self, "proj_b")], [Callable(self, "proj_b"), Callable(self, "proj_a")]]:
		# walker (id 4 at 350,450), heading 0: sits on the ground at its last position, drifts along the heading
		var w = await _layer(s, fx, pair[0])
		for f in _kill_frames(fx, 4, 0.0):
			w.set_frame(f, fx.mission(), 0)
		var origin := Vector2(350.0, 450.0)
		_check(has_near(w.screen_points(), pair[0].call(origin)), "S-136: walker wreck not at the projected last position")
		_check(absf(w.wreck_height(4) - gp.height_at(t, 350.0, 450.0)) < 0.05, "S-136: walker wreck height %f is not the ground height %f" % [w.wreck_height(4), gp.height_at(t, 350.0, 450.0)])
		_check(w.wreck_height(4) > 0.5, "CONTROL: walker ground height is zero, the check proves nothing")
		_check(not w.wreck_shadow(4), "section 7: a walker wreck must not get a flyer shadow disc")
		w.advance(2.0)
		var d: float = s.DRIFT_SPEED * (2.0 - 4.0 / (2.0 * s.DRIFT_STOP_S))
		var moved := origin + Vector2(d, 0.0)
		_check(has_near(w.screen_points(), pair[0].call(moved)), "R-136-01: wreck did not drift along the projected heading (want %s)" % pair[0].call(moved))
		_check(not has_near(w.screen_points(), pair[1].call(moved)), "CONTROL: drifted wreck also matches the other projector")
		_check(absf(w.wreck_height(4) - gp.height_at(t, moved.x, moved.y)) < 0.05, "S-136: drifting walker wreck left the ground")
		# flyer (id 2 at 450,350, layer 2): starts at floor + 150 with a shadow disc, falls to the ground, shadow gone
		var f2 = await _layer(s, fx, pair[0])
		for f in _kill_frames(fx, 2, 0.0):
			f2.set_frame(f, fx.mission(), 0)
		var up: float = FLOORS[2] + 150.0
		_check(absf(f2.wreck_height(2) - up) < 0.05, "section 7: fresh flyer wreck at %f, expected layer floor + 150 = %f" % [f2.wreck_height(2), up])
		_check(f2.wreck_height(2) > gp.height_at(t, 450.0, 350.0) + 1.0, "CONTROL: flyer wreck starts on the ground")
		_check(f2.wreck_shadow(2), "section 7: a falling flyer wreck has no shadow disc")
		f2.advance(LANDED_S)
		var p: Vector2 = f2.wreck_position(2)
		_check(absf(f2.wreck_height(2) - gp.height_at(t, p.x, p.y)) < 0.05, "S-136: flyer wreck did not fall to the ground height (%f vs %f)" % [f2.wreck_height(2), gp.height_at(t, p.x, p.y)])
		_check(not f2.wreck_shadow(2), "section 7: shadow disc must be gone once the flyer wreck is on the ground")
		_check(has_near(f2.screen_points(), pair[0].call(p)), "S-136: landed flyer wreck not at the projected position")
	# cap and LOD, lane A rules unchanged under the projector
	var big = await _layer(s, fx, Callable(self, "proj_a"))
	var f0: Dictionary = fx.frame().duplicate(true)
	var f1: Dictionary = f0.duplicate(true)
	f1["units"] = []
	f1["events"] = []
	for i in 160:
		f0["units"].append({"id": 1000 + i, "faction": 1, "type": 0, "tier": 0, "x": 100.0 + i, "y": 300.0, "hp": 10, "layer": 0, "facing": 0.0, "target": -1, "state": 0})
		f1["events"].append([2, 1000 + i, -1, 12])
	big.set_frame(f0, fx.mission(), 0)
	big.set_frame(f1, fx.mission(), 0)
	_check(big.wrecks().size() == 150, "R-136-03: cap 150 wrecks, got %d" % big.wrecks().size())
	var ids: Array = big.wrecks().map(func(w): return int(w["id"]))
	_check(not ids.has(1000) and ids.has(1159), "R-136-03: the cap must drop the oldest wrecks first")
	_check(big.wreck_emitters(1159) == s.EMITTERS, "R-136-03: damage emitters unchanged")
	big.advance(s.FADE_S + 1.0)
	_check(big.wrecks().size() == 0, "R-136-03: wrecks must be gone after the 30 s fade")
