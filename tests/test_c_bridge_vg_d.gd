extends SceneTree

# Visible-game programme lane D, K-d bridge decode (docs/northstar/plans/2026-10-07-visible-game-spec.md rev 4,
# "Contract gates" row K-d; S-246 / R-246-03). Fenced: builders never edit this file.
# autoload/c_bridge.gd asks for ONE space_field_dump after mission_begin in a space era (era_kind 0), never in a
# ground era, never again on deltas, and decodes it to space_field() (the K-d pin, flagged for the contract doc):
#   {cells_w: int, cells_h: int, layers: int,
#    masks: Array of 5 PackedByteArray (the hex decoded, packed 8 cells per byte, LSB first, 1 = blocked, 7200 bytes),
#    polys: Array of {layer: int, kind: int, points: PackedVector2Array}}
# space_field() is {} before a dump and in a ground era (a following ground mission clears it). The mission_start
# request is unchanged. The pipe is faked (a subclass records commands and queues canned replies, as
# tests/test_c_bridge_terrain.gd does); pipe-side behaviour is tests/transport/test_pipe_vg_d.py.
# "(control)" checks pass on main and prove the harness. On main c_bridge.gd has no space_field(): the rest are red.

const DIM := 240
const GROUND_ERA := "greek_placeholder"
const SPACE_ERA := "settled_reach"

const FAKE_SRC := """
extends "res://autoload/c_bridge.gd"

var log: Array = []
var dim: int = 240
var _ground := false


func _reply(f: Dictionary) -> void:
	_mutex.lock()
	_queue.append(f)
	_mutex.unlock()


func prime() -> void:
	_session_pid = 2147483000
	_session_args = [1, 10, []]
	_snapshot = {"regions": [{"i": 0}], "tick": 0}


func fake_masks() -> Array:
	var out := []
	for k in range(5):
		var b := PackedByteArray()
		b.resize(dim * dim / 8)
		for i in range(b.size()):
			b[i] = (i * 7 + k) & 0xFF
		out.append(b.hex_encode())
	return out


func fake_polys() -> Array:
	return [[0, 0, [0.0, 0.0, 100.0, 0.0, 100.0, 100.0]], [4, 2, [200.0, 200.0, 300.0, 200.0, 300.0, 350.5, 200.0, 300.0]], [2, 1, [10.0, 10.0, 20.0, 10.0, 20.0, 20.0]]]


func send_command(cmd: Dictionary) -> void:
	log.append(cmd)
	match String(cmd.get("name", "")):
		"mission_start":
			_ground = int(cmd.get("era_kind", 0)) == 1
			_reply({"type": "mission", "units": []})
		"save":
			_reply({"type": "ack", "name": "save", "tick": 0})
		"mission_begin":
			_reply({"type": "tactical", "full": true, "tick": 0, "units": [], "map": {}})
		"tactical_step":
			_reply({"type": "tactical", "full": false, "tick": 1, "units_changed": [], "units_removed": []})
		"mission_end":
			_reply({"type": "debrief", "band": 1})
			_reply({"type": "snapshot", "regions": [{"i": 0}], "tick": 1})
		"terrain_dump":
			if not _ground:
				_reply({"type": "error", "name": "terrain_dump", "reason": "no terrain"})
				return
			var flat := PackedByteArray()
			flat.resize(dim * dim)
			flat.fill(1)
			_reply({"type": "terrain", "cells_w": dim, "cells_h": dim, "bands": flat.hex_encode(), "walkable": flat.hex_encode(), "slopes": []})
		"space_field_dump":
			if _ground:
				_reply({"type": "error", "name": "space_field_dump", "reason": "no space field"})
				return
			_reply({"type": "space_field", "cells_w": dim, "cells_h": dim, "layers": 5, "masks": fake_masks(), "polys": fake_polys()})


func count(name: String) -> int:
	var n := 0
	for c in log:
		if String(c.get("name", "")) == name:
			n += 1
	return n


func first_index(name: String) -> int:
	for i in range(log.size()):
		if String(log[i].get("name", "")) == name:
			return i
	return -1
"""

var _pass_count := 0
var _fail_count := 0
var _fail_msgs: Array[String] = []
var _completed := false


func _initialize() -> void:
	await _run_tests()
	_assert(_completed, "the checks did not run to the end (a script error aborted them)")
	print("\n=== C Bridge VG-D Test Results ===")
	print("PASS: %d  FAIL: %d" % [_pass_count, _fail_count])
	if _fail_count > 0:
		print("Failures:")
		for msg in _fail_msgs:
			print("  - " + msg)
		print("=== RED ===\n")
		quit(1)
	else:
		print("=== GREEN ===\n")
		quit(0)


func _assert(cond: bool, msg: String) -> void:
	if cond:
		_pass_count += 1
	else:
		_fail_count += 1
		_fail_msgs.append(msg)


func _set_era(id: String) -> void:
	var e := root.get_node_or_null("EraConfig")
	if e != null:
		e.set("ACTIVE_ERA_ID", id)


func _new_fake():
	var s := GDScript.new()
	s.source_code = FAKE_SRC
	if s.reload() != OK:
		return null
	var f = s.new()
	f.prime()
	return f


func _sf(f) -> Dictionary:
	return f.space_field() if f.has_method("space_field") else {}


func _run_tests() -> void:
	OS.set_environment("OM_SAVE_DIR", OS.get_user_data_dir().path_join("vgd_saves_%d" % Time.get_ticks_usec()))
	_assert(root.get_node_or_null("EraConfig") != null, "EraConfig autoload missing (control)")
	var CBridge = load("res://autoload/c_bridge.gd")
	var probe = CBridge.new()
	_assert(probe.has_method("begin_mission_live") and probe.has_method("load_tactical_live"), "c_bridge.gd lost begin_mission_live / load_tactical_live (control)")
	_assert(probe.has_method("space_field"), "c_bridge.gd has no space_field(); K-d: 'bridge decode into space_field()' (R-246-03)")

	var f = _new_fake()
	_assert(f != null, "the fake pipe subclass did not compile (control)")
	if f == null:
		_completed = true
		return

	# space era: before the dump, empty; mission_start unchanged; one dump after mission_begin
	_set_era(SPACE_ERA)
	_assert(_sf(f).is_empty(), "space_field() is not empty before any dump; K-d")
	_assert(f.load_mission_live(1, 10, []), "control: space mission_start through the fake failed: %s" % f.last_error())
	_assert(f.count("space_field_dump") == 0, "space_field_dump sent before mission_begin; K-d: 'after mission_begin' like terrain_dump")
	_assert(f.begin_mission_live(1, 10, []), "control: space begin_mission_live failed: %s" % f.last_error())
	_assert(f.count("space_field_dump") == 1, "a space era sent %d space_field_dump after mission_begin, expected 1; K-d 'once per mission' (R-246-03)" % f.count("space_field_dump"))
	_assert(f.first_index("space_field_dump") > f.first_index("mission_begin"), "space_field_dump was not sent after mission_begin; K-d")

	var d: Dictionary = _sf(f)
	_assert(int(d.get("cells_w", 0)) == DIM and int(d.get("cells_h", 0)) == DIM and int(d.get("layers", 0)) == 5,
		"space_field() cells_w/cells_h/layers not 240/240/5 (got %s/%s/%s); K-d" % [str(d.get("cells_w")), str(d.get("cells_h")), str(d.get("layers"))])
	var masks: Variant = d.get("masks", null)
	var masks_ok: bool = masks is Array and (masks as Array).size() == 5
	_assert(masks_ok, "space_field().masks is not an Array of 5; K-d")
	if masks_ok:
		var all_bytes := true
		for k in range(5):
			all_bytes = all_bytes and (masks[k] is PackedByteArray) and (masks[k] as PackedByteArray).size() == DIM * DIM / 8
		_assert(all_bytes, "space_field().masks entries are not PackedByteArray of cells/8 = 7200 bytes (the hex decoded, still packed); K-d")
		if all_bytes:
			var m3: PackedByteArray = masks[3]
			_assert(m3[0] == 3 and m3[1] == ((7 + 3) & 0xFF) and m3[7199] == ((7199 * 7 + 3) & 0xFF), "decoded layer-3 mask differs from the dump (hex decode or layer order wrong)")
			_assert((masks[0] as PackedByteArray)[5] != (masks[1] as PackedByteArray)[5], "layers 0 and 1 decoded to the same bytes (layer order lost)")
	var polys: Variant = d.get("polys", null)
	var polys_ok: bool = polys is Array and (polys as Array).size() == 3
	_assert(polys_ok, "space_field().polys is not the dump's 3 polygons; K-d")
	if polys_ok:
		var p1: Variant = polys[1]
		var shape_ok: bool = p1 is Dictionary and int((p1 as Dictionary).get("layer", -1)) == 4 and int((p1 as Dictionary).get("kind", -1)) == 2 and (p1 as Dictionary).get("points", null) is PackedVector2Array
		_assert(shape_ok, "polys[1] is not {layer: 4, kind: 2, points: PackedVector2Array}; K-d pin")
		if shape_ok:
			var pts: PackedVector2Array = (p1 as Dictionary)["points"]
			_assert(pts.size() == 4 and pts[2] == Vector2(300.0, 350.5) and pts[3] == Vector2(200.0, 300.0), "decoded polygon points differ from the dump's [x,y,...] pairs")

	# never re-requested on deltas
	_assert(f.load_tactical_live(1, 10, []), "space load_tactical_live failed: %s" % f.last_error())
	_assert(f.tactical_step_n(3), "space tactical_step_n failed: %s" % f.last_error())
	_assert(f.count("tactical_step") >= 2 and f.count("space_field_dump") == 1,
		"space_field_dump was re-requested after tactical frames (%d dumps); K-d 'once per mission'" % f.count("space_field_dump"))
	_assert(int(_sf(f).get("cells_w", 0)) == DIM, "space_field() lost its content after tactical frames; K-d")

	# a ground mission: no dump, empty, and it clears the earlier one
	_assert(f.load_debrief_live(1, 10, []), "load_debrief_live failed: %s" % f.last_error())
	_set_era(GROUND_ERA)
	var before: int = f.count("space_field_dump")
	_assert(f.begin_mission_live(1, 10, []), "ground mission after a space one failed: %s" % f.last_error())
	_assert(f.count("space_field_dump") == before, "a ground era requested space_field_dump; K-d: space only")
	_assert(_sf(f).is_empty(), "space_field() kept the space mission's field into a ground mission; K-d")

	# a fresh ground bridge never asks (control-ish: passes on main)
	var g = _new_fake()
	_set_era(GROUND_ERA)
	_assert(g.load_mission_live(1, 10, []) and g.begin_mission_live(1, 10, []), "control: ground mission through the fake failed: %s" % g.last_error())
	_assert(g.count("space_field_dump") == 0, "a fresh ground era sent space_field_dump; K-d")

	_set_era(SPACE_ERA)
	_completed = true
