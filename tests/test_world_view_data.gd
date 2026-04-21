extends Node

var _data: Node
var _signals_received: Array[Dictionary] = []
var _pass_count := 0
var _fail_count := 0


func _ready() -> void:
	var script := load("res://scenes/shared/world_view/world_view_data.gd")
	_data = Node.new()
	_data.set_script(script)
	add_child(_data)

	_connect_all_signals()
	_run_tests()

	print("\n=== WorldViewData Test Results ===")
	print("PASS: %d  FAIL: %d" % [_pass_count, _fail_count])
	if _fail_count == 0:
		print("ALL TESTS PASSED")
	else:
		print("SOME TESTS FAILED")
	print("==================================\n")
	get_tree().quit()


func _connect_all_signals() -> void:
	_data.region_added.connect(func(id): _record("region_added", {"region_id": id}))
	_data.region_updated.connect(func(id): _record("region_updated", {"region_id": id}))
	_data.region_removed.connect(func(id): _record("region_removed", {"region_id": id}))
	_data.regions_cleared.connect(func(): _record("regions_cleared", {}))
	_data.territory_set.connect(func(id): _record("territory_set", {"region_id": id}))
	_data.territory_updated.connect(func(id): _record("territory_updated", {"region_id": id}))
	_data.territory_removed.connect(func(id): _record("territory_removed", {"region_id": id}))
	_data.connection_added.connect(func(f, t): _record("connection_added", {"from_id": f, "to_id": t}))
	_data.connection_removed.connect(func(f, t): _record("connection_removed", {"from_id": f, "to_id": t}))
	_data.flash_region_requested.connect(func(id, i): _record("flash_region_requested", {"region_id": id, "intensity": i}))
	_data.flash_conflict_requested.connect(func(f, t, i): _record("flash_conflict_requested", {"from_id": f, "to_id": t, "intensity": i}))
	_data.highlight_changed.connect(func(id): _record("highlight_changed", {"region_id": id}))


func _record(signal_name: String, args: Dictionary) -> void:
	_signals_received.append({"signal": signal_name, "args": args})


func _clear_signals() -> void:
	_signals_received.clear()


func _last_signal() -> Dictionary:
	if _signals_received.is_empty():
		return {}
	return _signals_received[-1]


func _assert(condition: bool, test_name: String) -> void:
	if condition:
		_pass_count += 1
		print("  PASS: %s" % test_name)
	else:
		_fail_count += 1
		print("  FAIL: %s" % test_name)


func _run_tests() -> void:
	print("\n--- Region tests ---")
	_test_add_region()
	_test_update_region()
	_test_remove_region()
	_test_clear_regions()

	print("\n--- Territory tests ---")
	_test_set_territory()
	_test_update_territory()
	_test_remove_territory()

	print("\n--- Connection tests ---")
	_test_add_connection()
	_test_connection_key_ordering()
	_test_remove_connection()

	print("\n--- Flash tests ---")
	_test_flash_region()
	_test_flash_conflict()

	print("\n--- Highlight tests ---")
	_test_highlight()
	_test_clear_highlight()

	print("\n--- Getter tests ---")
	_test_getters()


func _test_add_region() -> void:
	_clear_signals()
	_data.add_region("r1", Vector3(1, 2, 3), 5.0, Color.RED, "faction_a")
	_assert(_last_signal()["signal"] == "region_added", "add_region emits region_added")
	_assert(_last_signal()["args"]["region_id"] == "r1", "region_added has correct id")
	var r: Dictionary = _data.get_region("r1")
	_assert(r["position"] == Vector3(1, 2, 3), "stored position correct")
	_assert(r["size"] == 5.0, "stored size correct")
	_assert(r["color"] == Color.RED, "stored color correct")
	_assert(r["faction_id"] == "faction_a", "stored faction_id correct")


func _test_update_region() -> void:
	_clear_signals()
	_data.update_region("r1", 10.0, Color.BLUE)
	_assert(_last_signal()["signal"] == "region_updated", "update_region emits region_updated")
	var r: Dictionary = _data.get_region("r1")
	_assert(r["size"] == 10.0, "updated size correct")
	_assert(r["color"] == Color.BLUE, "updated color correct")
	_assert(r["position"] == Vector3(1, 2, 3), "position unchanged after update")

	_clear_signals()
	_data.update_region("nonexistent", 1.0, Color.WHITE)
	_assert(_signals_received.is_empty(), "update_region on missing id emits nothing")


func _test_remove_region() -> void:
	_clear_signals()
	_data.remove_region("r1")
	_assert(_last_signal()["signal"] == "region_removed", "remove_region emits region_removed")
	_assert(_data.get_region("r1").is_empty(), "region removed from store")

	_clear_signals()
	_data.remove_region("r1")
	_assert(_signals_received.is_empty(), "remove_region on missing id emits nothing")


func _test_clear_regions() -> void:
	_data.add_region("r2", Vector3.ZERO, 1.0, Color.GREEN, "f1")
	_data.add_region("r3", Vector3.ONE, 2.0, Color.YELLOW, "f2")
	_clear_signals()
	_data.clear_regions()
	_assert(_last_signal()["signal"] == "regions_cleared", "clear_regions emits regions_cleared")
	_assert(_data.get_all_regions().is_empty(), "all regions cleared")


func _test_set_territory() -> void:
	_clear_signals()
	_data.set_territory("r1", Vector3(5, 0, 5), 10.0, Color.RED)
	_assert(_last_signal()["signal"] == "territory_set", "set_territory emits territory_set")
	var t: Dictionary = _data.get_territory("r1")
	_assert(t["center"] == Vector3(5, 0, 5), "territory center correct")
	_assert(t["radius"] == 10.0, "territory radius correct")
	_assert(t["color"] == Color.RED, "territory color correct")


func _test_update_territory() -> void:
	_clear_signals()
	_data.update_territory("r1", 20.0, Color.BLUE)
	_assert(_last_signal()["signal"] == "territory_updated", "update_territory emits territory_updated")
	var t: Dictionary = _data.get_territory("r1")
	_assert(t["radius"] == 20.0, "updated territory radius correct")

	_clear_signals()
	_data.update_territory("nonexistent", 1.0, Color.WHITE)
	_assert(_signals_received.is_empty(), "update_territory on missing id emits nothing")


func _test_remove_territory() -> void:
	_clear_signals()
	_data.remove_territory("r1")
	_assert(_last_signal()["signal"] == "territory_removed", "remove_territory emits territory_removed")
	_assert(_data.get_territory("r1").is_empty(), "territory removed from store")

	_clear_signals()
	_data.remove_territory("r1")
	_assert(_signals_received.is_empty(), "remove_territory on missing id emits nothing")


func _test_add_connection() -> void:
	_clear_signals()
	_data.add_connection("a", "b", "trade", Color.GREEN)
	_assert(_last_signal()["signal"] == "connection_added", "add_connection emits connection_added")
	var c: Dictionary = _data.get_connection("a", "b")
	_assert(c["from_id"] == "a", "connection from_id correct")
	_assert(c["to_id"] == "b", "connection to_id correct")
	_assert(c["connection_type"] == "trade", "connection type correct")
	_assert(c["color"] == Color.GREEN, "connection color correct")


func _test_connection_key_ordering() -> void:
	var c: Dictionary = _data.get_connection("b", "a")
	_assert(not c.is_empty(), "connection retrievable with reversed id order")
	_assert(c["from_id"] == "a", "reversed lookup returns original from_id")


func _test_remove_connection() -> void:
	_clear_signals()
	_data.remove_connection("b", "a")
	_assert(_last_signal()["signal"] == "connection_removed", "remove_connection emits connection_removed")
	_assert(_data.get_connection("a", "b").is_empty(), "connection removed from store")

	_clear_signals()
	_data.remove_connection("a", "b")
	_assert(_signals_received.is_empty(), "remove_connection on missing key emits nothing")


func _test_flash_region() -> void:
	_clear_signals()
	_data.request_flash_region("r5", 0.8)
	_assert(_last_signal()["signal"] == "flash_region_requested", "flash_region emits signal")
	_assert(_last_signal()["args"]["region_id"] == "r5", "flash_region id correct")
	_assert(_last_signal()["args"]["intensity"] == 0.8, "flash_region intensity correct")


func _test_flash_conflict() -> void:
	_clear_signals()
	_data.request_flash_conflict("r1", "r2", 0.5)
	_assert(_last_signal()["signal"] == "flash_conflict_requested", "flash_conflict emits signal")
	_assert(_last_signal()["args"]["from_id"] == "r1", "flash_conflict from_id correct")
	_assert(_last_signal()["args"]["to_id"] == "r2", "flash_conflict to_id correct")
	_assert(_last_signal()["args"]["intensity"] == 0.5, "flash_conflict intensity correct")


func _test_highlight() -> void:
	_clear_signals()
	_data.set_highlight("r3")
	_assert(_last_signal()["signal"] == "highlight_changed", "set_highlight emits highlight_changed")
	_assert(_last_signal()["args"]["region_id"] == "r3", "highlight_changed id correct")
	_assert(_data.highlight_id == "r3", "highlight_id stored")


func _test_clear_highlight() -> void:
	_clear_signals()
	_data.set_highlight("")
	_assert(_last_signal()["signal"] == "highlight_changed", "clear highlight emits highlight_changed")
	_assert(_last_signal()["args"]["region_id"] == "", "highlight_changed empty string")
	_assert(_data.highlight_id == "", "highlight_id cleared")


func _test_getters() -> void:
	_data.clear_regions()
	_data.add_region("g1", Vector3.ZERO, 1.0, Color.WHITE, "f1")
	_data.add_region("g2", Vector3.ONE, 2.0, Color.BLACK, "f2")
	var all: Dictionary = _data.get_all_regions()
	_assert(all.size() == 2, "get_all_regions returns correct count")
	_assert("g1" in all, "get_all_regions contains g1")
	_assert("g2" in all, "get_all_regions contains g2")

	_assert(_data.get_region("nonexistent").is_empty(), "get_region on missing returns empty dict")
	_assert(_data.get_connection("x", "y").is_empty(), "get_connection on missing returns empty dict")
	_assert(_data.get_territory("nonexistent").is_empty(), "get_territory on missing returns empty dict")

	_data.clear_regions()
