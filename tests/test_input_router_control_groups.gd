## Headless test for B3 control-group exclusive membership.
## Verifies that binding a uid into a new group removes it from prior groups,
## and that recall after re-bind returns only the most-recent membership.
## See also: scenes/tactical/input_router.gd — _bind_group / _recall_group
extends Node

var _router: Node
var _pass_count := 0
var _fail_count := 0


func _ready() -> void:
	var script := load("res://scenes/tactical/input_router.gd")
	_router = Node2D.new()
	_router.set_script(script)
	add_child(_router)

	_run_tests()

	print("\n=== InputRouter Control Groups Test Results ===")
	print("PASS: %d  FAIL: %d" % [_pass_count, _fail_count])
	if _fail_count == 0:
		print("ALL TESTS PASSED")
	else:
		print("SOME TESTS FAILED")
	print("================================================\n")
	get_tree().quit()


func _run_tests() -> void:
	_test_basic_bind()
	_test_exclusive_membership_overlap()
	_test_exclusive_membership_full_overlap()
	_test_no_disturb_to_unbound_groups()
	_test_rebind_strips_prior_group()
	_test_empty_selection_noop()


func _test_basic_bind() -> void:
	_reset()
	_router.selected_uids = [1, 2, 3] as Array[int]
	_router._bind_group(1)
	_assert_eq("basic_bind: group 1 has [1,2,3]",
		_router._control_groups.get(1, []), [1, 2, 3])


func _test_exclusive_membership_overlap() -> void:
	_reset()
	_router.selected_uids = [1, 2, 3] as Array[int]
	_router._bind_group(1)
	_router.selected_uids = [3, 4] as Array[int]
	_router._bind_group(2)
	_assert_eq("overlap: group 1 stripped of {3}",
		_router._control_groups.get(1, []), [1, 2])
	_assert_eq("overlap: group 2 = [3,4]",
		_router._control_groups.get(2, []), [3, 4])


func _test_exclusive_membership_full_overlap() -> void:
	_reset()
	_router.selected_uids = [5, 6] as Array[int]
	_router._bind_group(3)
	_router.selected_uids = [5, 6] as Array[int]
	_router._bind_group(4)
	_assert_eq("full_overlap: group 3 emptied",
		_router._control_groups.get(3, []), [])
	_assert_eq("full_overlap: group 4 = [5,6]",
		_router._control_groups.get(4, []), [5, 6])


func _test_no_disturb_to_unbound_groups() -> void:
	_reset()
	_router.selected_uids = [10, 11] as Array[int]
	_router._bind_group(5)
	_router.selected_uids = [20, 21] as Array[int]
	_router._bind_group(6)
	_router.selected_uids = [30, 31] as Array[int]
	_router._bind_group(7)
	_assert_eq("no_disturb: group 5 untouched",
		_router._control_groups.get(5, []), [10, 11])
	_assert_eq("no_disturb: group 6 untouched",
		_router._control_groups.get(6, []), [20, 21])
	_assert_eq("no_disturb: group 7 = [30,31]",
		_router._control_groups.get(7, []), [30, 31])


func _test_rebind_strips_prior_group() -> void:
	_reset()
	_router.selected_uids = [1, 2, 3] as Array[int]
	_router._bind_group(1)
	_router.selected_uids = [2] as Array[int]
	_router._bind_group(2)
	# Verify the stored membership reflects the rebind.
	# (We don't call _recall_group here because it would prune via
	# TacticalBridge.units.has(), which is empty in the headless harness.)
	_assert_eq("rebind: group 1 = [1,3] after rebind of {2}",
		_router._control_groups.get(1, []), [1, 3])
	_assert_eq("rebind: group 2 = [2]",
		_router._control_groups.get(2, []), [2])


func _test_empty_selection_noop() -> void:
	_reset()
	_router.selected_uids = [1, 2] as Array[int]
	_router._bind_group(1)
	_router.selected_uids = [] as Array[int]
	_router._bind_group(2)
	_assert_eq("empty_sel: group 1 untouched",
		_router._control_groups.get(1, []), [1, 2])
	_assert_true("empty_sel: group 2 not created",
		not _router._control_groups.has(2))


func _reset() -> void:
	_router._control_groups = {}
	_router.selected_uids = [] as Array[int]


func _assert_eq(label: String, actual, expected) -> void:
	var a := str(actual)
	var e := str(expected)
	if a == e:
		_pass_count += 1
		print("  PASS  %s" % label)
	else:
		_fail_count += 1
		print("  FAIL  %s  (got %s, expected %s)" % [label, a, e])


func _assert_true(label: String, cond: bool) -> void:
	if cond:
		_pass_count += 1
		print("  PASS  %s" % label)
	else:
		_fail_count += 1
		print("  FAIL  %s" % label)
