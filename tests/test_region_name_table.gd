extends SceneTree

# A66 (f) (docs/northstar/plans/2026-10-01-architect-rulings-2.md, Addendum 26):
# the region name table is built from simple invented syllable names so each of
# 512 region ids resolves to its own name in the client. Source is the C pool in
# csrc/chronicle.c; library/chronicle/fragments.json is regenerated from it by
# scripts/library/emit_chronicle_fragments.py. The client resolves a name with
# scenes/world/chronicle_names.gd fill_template("{region_name}", id, -1).
# Positive control: the same checker, fed a 16-name table (today's), must report
# a clash at ids 0 and 16, so a checker that never complains cannot pass.

const NamesScript := preload("res://scenes/world/chronicle_names.gd")
const LIBRARY_PATH := "res://library/chronicle/fragments.json"
const N_IDS := 512

var _pass_count := 0
var _fail_count := 0
var _fail_msgs: Array[String] = []


func _initialize() -> void:
	_run_tests()
	print("\n=== Region Name Table Test Results ===")
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


func _first_clash(tables: Dictionary) -> Array:
	var names = NamesScript.new()
	names.load_tables(tables)
	var seen := {}
	for id in range(N_IDS):
		var name: String = names.fill_template("{region_name}", id, -1)
		if seen.has(name):
			return [seen[name], id]
		seen[name] = id
	return []


func _run_tests() -> void:
	var sixteen: Array = []
	for i in range(16):
		sixteen.append("N%d" % i)
	_assert(_first_clash({"region_names": sixteen}) == [0, 16], "A66f (control): a 16-name table should clash at ids 0 and 16, got %s" % [_first_clash({"region_names": sixteen})])
	var full: Array = []
	for i in range(N_IDS):
		full.append("N%d" % i)
	_assert(_first_clash({"region_names": full}) == [], "A66f (control): a 512-distinct-name table should not clash")

	var f := FileAccess.open(LIBRARY_PATH, FileAccess.READ)
	_assert(f != null, "could not open " + LIBRARY_PATH)
	if f == null:
		return
	var data = JSON.parse_string(f.get_as_text())
	_assert(data is Dictionary and data.get("name_tables") is Dictionary, "fragments.json has no name_tables")
	if not (data is Dictionary and data.get("name_tables") is Dictionary):
		return
	var tables: Dictionary = data["name_tables"]
	var listed: Array = tables.get("region_names", [])
	_assert(listed.size() >= N_IDS, "A66f: region_names has %d entries, need at least %d" % [listed.size(), N_IDS])
	var clash := _first_clash(tables)
	_assert(clash.is_empty(), "A66f: region ids %s share a name (all %d ids must differ)" % [clash, N_IDS])
	for n in listed:
		_assert(str(n).strip_edges() != "", "A66f: region_names has an empty entry")
