extends SceneTree

# K-c6 bridge decode: _DumpDecode.terrain_from_frame (autoload/bridge/dump_decode.gd) passes layer_floors_wu and
# flyer_types through unchanged. Red now: terrain_from_frame builds a fixed dict and drops both keys.
# Control (passes now and after): a frame without them yields a dict without them (no defaults invented).
# Pipe side: tests/transport/test_pipe_vg_c6.py.

const Dec := preload("res://autoload/bridge/dump_decode.gd")

var _pass_count := 0
var _fail_count := 0
var _fail_msgs: Array[String] = []


func _initialize() -> void:
	var fr := {"cells_w": 2, "cells_h": 1, "bands": "0102", "walkable": "0101", "slopes": [],
		"layer_floors_wu": [0.0, 1.5, 3.0, 4.5, 6.0], "flyer_types": [1, 4]}
	var t: Dictionary = Dec.terrain_from_frame(fr)
	_assert(t.has("layer_floors_wu") and t["layer_floors_wu"] == fr["layer_floors_wu"], "layer_floors_wu not passed through (K-c6)")
	_assert(t.has("flyer_types") and t["flyer_types"] == fr["flyer_types"], "flyer_types not passed through (K-c6)")
	var bare: Dictionary = Dec.terrain_from_frame({"cells_w": 2, "cells_h": 1, "bands": "0102", "walkable": "0101", "slopes": []})
	_assert(not bare.has("layer_floors_wu") and not bare.has("flyer_types"), "control: defaults invented for absent keys")
	print("\n=== C Bridge VG-C6 Test Results ===")
	print("PASS: %d  FAIL: %d" % [_pass_count, _fail_count])
	for m in _fail_msgs:
		print("  - " + m)
	print("=== RED ===\n" if _fail_count > 0 else "=== GREEN ===\n")
	quit(1 if _fail_count > 0 else 0)


func _assert(cond: bool, msg: String) -> void:
	if cond:
		_pass_count += 1
	else:
		_fail_count += 1
		_fail_msgs.append(msg)
