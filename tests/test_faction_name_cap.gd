extends SceneTree

# A82 (docs/northstar/plans/2026-10-01-architect-rulings-2.md, Addendum 29): the
# client faction name table covers the faction cap (OM_MAX_FACTIONS = 64), so
# fill_template("{faction_name}", -1, id) gives each id 0..63 its own name. The first
# 18 names are the ones printed since A55 and do not change. The sim side and the
# JSON-regeneration check are in tests/csim/test_E09_faction_name_pool.py.
# Positive control: an 18-name table must clash at ids 0 and 18.

const NamesScript := preload("res://scenes/world/chronicle_names.gd")
const LIBRARY_PATH := "res://library/chronicle/fragments.json"
const CAP := 64
const FIRST_18 := [
	"the Dominion", "the Concord", "the Ashen League", "the Iron Compact",
	"the Free Cities", "the Sable Court", "the Vanguard Accord", "the Twin Banners",
	"the Amber Throne", "the River Pact", "the Stonewrights", "the Northwind Host",
	"the Lantern Guild", "the Hollow Standard", "the Saltmarsh Union", "the Quiet Fleet",
	"the Copper Assembly", "the Evenfall Realm",
]

var _pass_count := 0
var _fail_count := 0
var _fail_msgs: Array[String] = []


func _initialize() -> void:
	_run_tests()
	print("\n=== Faction Name Cap Test Results ===")
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


func _resolved(tables: Dictionary) -> Array:
	var names = NamesScript.new()
	names.load_tables(tables)
	var out: Array = []
	for id in range(CAP):
		out.append(names.fill_template("{faction_name}", -1, id))
	return out


func _first_clash(resolved: Array) -> Array:
	var seen := {}
	for id in range(resolved.size()):
		if seen.has(resolved[id]):
			return [seen[resolved[id]], id]
		seen[resolved[id]] = id
	return []


func _run_tests() -> void:
	var eighteen := {"faction_names": FIRST_18.duplicate()}
	_assert(_first_clash(_resolved(eighteen)) == [0, 18], "A82 (control): an 18-name table should clash at ids 0 and 18, got %s" % [_first_clash(_resolved(eighteen))])
	var distinct: Array = []
	for i in range(CAP):
		distinct.append("N%d" % i)
	_assert(_first_clash(_resolved({"faction_names": distinct})) == [], "A82 (control): a 64-distinct-name table should not clash")

	var f := FileAccess.open(LIBRARY_PATH, FileAccess.READ)
	_assert(f != null, "could not open " + LIBRARY_PATH)
	if f == null:
		return
	var data = JSON.parse_string(f.get_as_text())
	var tables: Dictionary = data["name_tables"]
	var listed: Array = tables.get("faction_names", [])
	_assert(listed.size() >= CAP, "A82: faction_names has %d entries, need at least %d" % [listed.size(), CAP])
	var resolved := _resolved(tables)
	var clash := _first_clash(resolved)
	_assert(clash.is_empty(), "A82: faction ids %s share a name (ids 0..%d must all differ)" % [clash, CAP - 1])
	for id in range(18):
		_assert(resolved[id] == FIRST_18[id], "A82: faction id %d resolves to '%s', must stay '%s'" % [id, resolved[id], FIRST_18[id]])
	for id in range(CAP):
		_assert(str(resolved[id]).strip_edges() != "" and not str(resolved[id]).contains("[faction]"), "A82: faction id %d has an empty or placeholder name" % id)
