## Headless test for B4 selection upgrades — exercises real _click_select /
## _box_select with a SubViewport-hosted Camera3D so the additive contract
## is locked in against future regressions. The double-click type-select path
## is left to Westley's spot-check (depends on full tactical scene + theme).
## See also: scenes/tactical/input_router.gd
extends Node

var _viewport: SubViewport
var _camera: Camera3D
var _router: Node
var _pass_count := 0
var _fail_count := 0


func _ready() -> void:
	# A SubViewport with a Camera3D inside it — InputRouter pulls
	# get_viewport().get_camera_3d(), so the router must live inside this viewport.
	_viewport = SubViewport.new()
	_viewport.size = Vector2i(1280, 720)
	add_child(_viewport)

	_camera = Camera3D.new()
	_viewport.add_child(_camera)
	# Tactical-style angled camera (avoids the top-down up-vector singularity
	# that causes Camera3D's projection matrix to go degenerate).
	_camera.look_at_from_position(Vector3(0, 5000, 5000), Vector3(0, 0, 0), Vector3.UP)
	_camera.current = true

	var script := load("res://scenes/tactical/input_router.gd")
	_router = Node2D.new()
	_router.set_script(script)
	_viewport.add_child(_router)

	_seed_two_units()
	# Wait one frame so the viewport/camera transforms settle.
	await get_tree().process_frame

	_run_tests()

	print("\n=== InputRouter Selection Test Results ===")
	print("PASS: %d  FAIL: %d" % [_pass_count, _fail_count])
	if _fail_count == 0:
		print("ALL TESTS PASSED")
	else:
		print("SOME TESTS FAILED")
	print("===========================================\n")
	get_tree().quit()


# Seeds two friendly units at known world positions and makes them visible to
# the player. The fog gate (Visibility.is_unit_visible_to_player) returns true
# for faction 0 unconditionally, so faction-0 units suffice.
func _seed_two_units() -> void:
	TacticalBridge.units.clear()
	for i in range(TacticalBridge.MAX_UNITS):
		TacticalBridge.display_alive[i] = 0
		TacticalBridge.display_x[i] = 0.0
		TacticalBridge.display_y[i] = 0.0
	# uid 0 at world (-200, 0, 0)
	_add_unit(0, "raider", -200.0, 0.0)
	# uid 1 at world (+200, 0, 0)
	_add_unit(1, "raider", 200.0, 0.0)
	TacticalBridge.unit_count = 2


func _add_unit(uid: int, type: String, x: float, z: float) -> void:
	TacticalBridge.units[uid] = {
		"uid": uid, "type": type, "faction": 0, "layer": 0,
		"hp": 100.0, "max_hp": 100.0, "selection_eligible": true,
	}
	TacticalBridge.display_x[uid] = x
	TacticalBridge.display_y[uid] = z
	TacticalBridge.display_alive[uid] = 1


func _run_tests() -> void:
	_test_click_replace()
	_test_click_additive_keeps_existing()
	_test_click_additive_dedupes()
	_test_box_replace()
	_test_box_additive_dedupes()


# ── Tests ─────────────────────────────────────────────────────────────────────

func _test_click_replace() -> void:
	_router.selected_uids = [99] as Array[int]
	var sp := _camera.unproject_position(Vector3(-200, 0, 0))
	_router._click_select(sp, false)
	_assert_eq("click replace: stale [99] cleared, uid 0 selected",
		_router.selected_uids, [0])


func _test_click_additive_keeps_existing() -> void:
	_router.selected_uids = [99] as Array[int]
	var sp := _camera.unproject_position(Vector3(-200, 0, 0))
	_router._click_select(sp, true)
	_assert_eq("click additive: 99 kept, uid 0 appended",
		_router.selected_uids, [99, 0])


func _test_click_additive_dedupes() -> void:
	_router.selected_uids = [0] as Array[int]
	var sp := _camera.unproject_position(Vector3(-200, 0, 0))
	_router._click_select(sp, true)
	_assert_eq("click additive: uid 0 already present, not duplicated",
		_router.selected_uids, [0])


func _test_box_replace() -> void:
	_router.selected_uids = [99] as Array[int]
	# A box that covers both unit positions in screen space.
	var sp_a := _camera.unproject_position(Vector3(-400, 0, -100))
	var sp_b := _camera.unproject_position(Vector3(400, 0, 100))
	_router._box_select(sp_a, sp_b, false)
	_assert_eq("box replace: stale [99] cleared, [0,1] selected",
		_router.selected_uids, [0, 1])


func _test_box_additive_dedupes() -> void:
	_router.selected_uids = [0, 99] as Array[int]
	var sp_a := _camera.unproject_position(Vector3(-400, 0, -100))
	var sp_b := _camera.unproject_position(Vector3(400, 0, 100))
	_router._box_select(sp_a, sp_b, true)
	_assert_eq("box additive: 99 kept, 0 deduped, 1 appended",
		_router.selected_uids, [0, 99, 1])


func _assert_eq(label: String, actual, expected) -> void:
	var a := str(actual)
	var e := str(expected)
	if a == e:
		_pass_count += 1
		print("  PASS  %s" % label)
	else:
		_fail_count += 1
		print("  FAIL  %s  (got %s, expected %s)" % [label, a, e])
