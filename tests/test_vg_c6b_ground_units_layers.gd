extends "res://tests/support/vg_c_case.gd"

# VG-C6b (feed lines in scenes/ground3d/ground3d.gd, shared with VG-C-wire): set_frame passes [] for the layer floors
# and the flyer types to Units3D.set_units, so every 3D body stands at ground height and no flyer has a shadow disc.
# Proves S-010/S-132 with spec section 7 (flyer Y = layer floor + 150 wu, shadow disc; walker Y = ground height).
# RED NOW because (a) ground3d qa_state()["ground3d"] has no "units3d_heights" key and (b) the feed is empty arrays.
# NO DATA SOURCE EXISTS YET: the terrain dict (vg_c_fixture.terrain, c_bridge terrain_from_frame) carries no layer
# floors and no flyer types, and no frame field marks a flyer (frame units have only "type" and "layer"). Only
# config.LAYER_Z_FLOORS (python, architecture.md line 202) names floors. This test PINS a proposed contract that a
# contract piece must deliver: terrain["layer_floors_wu"]: Array of float (one per layer) and
# terrain["flyer_types"]: Array of int (unit type ids that fly). The builder may rename them, and then edits this test's
# two constants below via a test-defect ledger row.
# Key pinned for the builder to add to qa_state()["ground3d"]:
#   "units3d_heights": {str(unit id): body Y in wu} and "units3d_shadows": [unit ids that have a shadow disc].
# Note: Units3D.y_for puts WALKERS at ground height whatever the layer; only flyers use the floor. So the "layer 1"
# expectation is on a flyer (type 1) and a layer-1 walker is expected at ground height.
# CONTROL: terrain without the two keys (today's behaviour) puts every body at ground height, no shadows.

const FLOORS_KEY := "layer_floors_wu"
const FLYERS_KEY := "flyer_types"
const FLOORS := [0.0, 100.0, 400.0, 800.0, 1200.0]
# TD-VG-C-ground-lift (VG-C-unit-ground-fit): a walker's body is lifted 1.0 wu (DRAFT-unit-ground-lift) along the ground
# normal; the fixture slope is shallow (normal y > 0.9998), so the y pin moves by 1.0 within the 0.05 tolerance.
# See also: tests/test_vg_c_unit_ground_fit.gd
const GROUND_LIFT_WU := 1.0


func _unit(id: int, type: int, x: float, y: float, layer: int) -> Dictionary:
	return {"id": id, "faction": 0, "type": type, "tier": 0, "x": x, "y": y, "hp": 100, "layer": layer, "facing": 0.0, "target": -1, "state": 0, "sight": 200}


func _frame() -> Dictionary:
	return {"tick": 10, "player_faction": 0, "visible": {"0": []}, "map": {"nodes": [], "cover": [], "obstacles": []}, "units": [
		_unit(1, 0, 250.0, 250.0, 0), _unit(6, 0, 350.0, 250.0, 1),
		_unit(2, 1, 450.0, 350.0, 2), _unit(7, 1, 250.0, 450.0, 1)]}


func _qa(hs, terrain: Dictionary) -> Dictionary:
	var host = hs.new()
	root.add_child(host)
	await process_frame
	host.set_terrain(terrain)
	host.set_frame(_frame(), _fixture().mission())
	await process_frame
	var q: Dictionary = host.qa_state()
	host.queue_free()
	return q


func _run() -> void:
	var hs := _load(SCENES + "ground3d.gd")
	if hs == null:
		return
	var fx := _fixture()
	# CONTROL: today's terrain (no floors, no flyer types) -> every body at ground height, no shadow disc.
	var q0: Dictionary = await _qa(hs, fx.terrain())
	var g0: Dictionary = q0["ground3d"]
	var h0 = g0.get("units3d_heights", null)
	_check(h0 is Dictionary, "S-132: ground3d qa_state has no units3d_heights (key not built); keys %s" % [g0.keys()])
	if h0 is Dictionary:
		for p in [[1, 250.0, 250.0], [6, 350.0, 250.0], [2, 450.0, 350.0], [7, 250.0, 450.0]]:
			var y := float(h0.get(str(p[0]), -9999.0))
			_check(absf(y - (fx.ground_y(p[1], p[2]) + GROUND_LIFT_WU)) < 0.05, "CONTROL: with no floors/flyer types unit %d Y %f is not the ground height + lift %f" % [p[0], y, fx.ground_y(p[1], p[2]) + GROUND_LIFT_WU])
	_check((g0.get("units3d_shadows", []) as Array).is_empty(), "CONTROL: no flyer types yet a shadow disc exists: %s" % [g0.get("units3d_shadows")])
	# Real case: the same frame with floors and flyer types on the terrain.
	var t: Dictionary = fx.terrain()
	t[FLOORS_KEY] = FLOORS
	t[FLYERS_KEY] = [1]
	var g: Dictionary = (await _qa(hs, t))["ground3d"]
	var h = g.get("units3d_heights", null)
	_check(h is Dictionary, "S-132: no units3d_heights with floors fed")
	if h is Dictionary:
		_check(absf(float(h.get("1", -9999.0)) - (fx.ground_y(250.0, 250.0) + GROUND_LIFT_WU)) < 0.05, "S-010: layer-0 walker Y %s, expected ground + lift %f" % [h.get("1"), fx.ground_y(250.0, 250.0) + GROUND_LIFT_WU])
		_check(absf(float(h.get("6", -9999.0)) - (fx.ground_y(350.0, 250.0) + GROUND_LIFT_WU)) < 0.05, "section 7: layer-1 walker Y %s, expected ground + lift %f (walkers ignore the floor)" % [h.get("6"), fx.ground_y(350.0, 250.0) + GROUND_LIFT_WU])
		_check(absf(float(h.get("7", -9999.0)) - (FLOORS[1] + 150.0)) < 0.05, "section 7: layer-1 flyer Y %s, expected floor %f + 150" % [h.get("7"), FLOORS[1]])
		_check(absf(float(h.get("2", -9999.0)) - (FLOORS[2] + 150.0)) < 0.05, "section 7: layer-2 flyer Y %s, expected floor %f + 150" % [h.get("2"), FLOORS[2]])
	var sh: Array = g.get("units3d_shadows", [])
	_check(sh.has(2) and sh.has(7), "section 7: flyers 2 and 7 need shadow discs, got %s" % [sh])
	_check(not sh.has(1) and not sh.has(6), "section 7: walkers must not get a shadow disc, got %s" % [sh])
