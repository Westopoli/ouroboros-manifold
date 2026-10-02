extends SceneTree

# A82 (Addendum 29): the client fallback resolver (scenes/world/chronicle_names.gd) stays
# only as the structural-line fallback of A73 and uses the sim's unowned wording
# "an unclaimed people" (csrc/chronicle.c chron_faction_name, negative id), not "[faction]".
# Its A73 role is unchanged: region and faction names for in-range ids come from the
# library tables, equal to the sim's table[id % size].
# Positive control: an in-range faction id resolves to its table name, so a resolver that
# returned the unowned wording for everything would fail.

const NamesScript := preload("res://scenes/world/chronicle_names.gd")
const LIBRARY_PATH := "res://library/chronicle/fragments.json"
const UNOWNED := "an unclaimed people"

var _pass_count := 0
var _fail_count := 0
var _fail_msgs: Array[String] = []


func _assert(cond: bool, msg: String) -> void:
	if cond:
		_pass_count += 1
	else:
		_fail_count += 1
		_fail_msgs.append(msg)


func _finish(title: String) -> void:
	print("\n=== %s Test Results ===" % title)
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


func _initialize() -> void:
	_run_tests()
	_finish("A82 Name Fallback")


func _run_tests() -> void:
	var lib = JSON.parse_string(FileAccess.get_file_as_string(LIBRARY_PATH))
	_assert(lib is Dictionary, "setup: fragments.json unreadable")
	if not (lib is Dictionary):
		return
	var tables: Dictionary = lib["name_tables"]
	var names = NamesScript.new()
	names.load_tables(tables)
	var f_table: Array = tables["faction_names"]
	var r_table: Array = tables["region_names"]
	_assert(names.fill_template("{faction_name}", 3, 0) == str(f_table[0]),
		"control: faction 0 should resolve to '%s'" % f_table[0])
	_assert(names.fill_template("{region_name}", 3, 0) == str(r_table[3]),
		"control: region 3 should resolve to '%s'" % r_table[3])
	for r in [0, 3, 41]:
		var out: String = names.fill_template("The {faction_name} hold {region_name}.", r, -1)
		_assert(out.begins_with("The %s hold" % UNOWNED),
			"A82: unowned (faction -1) must read '%s', got '%s'" % [UNOWNED, out])
		_assert(out.find("[faction]") == -1, "A82: '[faction]' placeholder still emitted: '%s'" % out)
	# Same wording with no tables loaded (still the unowned wording, not a bracket).
	var empty = NamesScript.new()
	_assert(empty.fill_template("{faction_name}", -1, -1) == UNOWNED,
		"A82: with no tables, faction -1 must still read '%s'" % UNOWNED)
