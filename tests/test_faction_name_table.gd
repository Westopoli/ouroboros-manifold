extends SceneTree

# A55 (docs/northstar/plans/2026-10-01-architect-rulings-2.md, Addendum 23):
# the faction name table has at least fifteen simple invented names, so no two
# of fifteen consecutive faction ids share a name. Content job for a Doer: the
# source is CHRON_FACTION_NAMES in csrc/chronicle.c (with CHRON_N_FACTION_NAMES),
# library/chronicle/fragments.json is regenerated from it by
# scripts/library/emit_chronicle_fragments.py. The client resolves a name with
# scenes/world/chronicle_names.gd fill_template("{faction_name}", -1, id).
# Positive control: the same checker, fed an 8-name table (today's), must
# report a clash, so a checker that never complains cannot pass.

const NamesScript := preload("res://scenes/world/chronicle_names.gd")
const LIBRARY_PATH := "res://library/chronicle/fragments.json"
const MIN_NAMES := 15

var _pass_count := 0
var _fail_count := 0
var _fail_msgs: Array[String] = []


func _initialize() -> void:
	_run_tests()
	print("\n=== Faction Name Table Test Results ===")
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


# Returns the first pair [id_a, id_b] of ids in 0..MIN_NAMES-1 whose resolved
# names are equal, or [] when all MIN_NAMES names differ.
func _first_clash(tables: Dictionary) -> Array:
	var names = NamesScript.new()
	names.load_tables(tables)
	var seen := {}
	for id in range(MIN_NAMES):
		var name: String = names.fill_template("{faction_name}", -1, id)
		if seen.has(name):
			return [seen[name], id]
		seen[name] = id
	return []


func _run_tests() -> void:
	var f := FileAccess.open(LIBRARY_PATH, FileAccess.READ)
	_assert(f != null, "could not open " + LIBRARY_PATH)
	if f == null:
		return
	var data = JSON.parse_string(f.get_as_text())
	_assert(data is Dictionary and data.get("name_tables") is Dictionary, "fragments.json has no name_tables")
	if not (data is Dictionary and data.get("name_tables") is Dictionary):
		return
	var tables: Dictionary = data["name_tables"]
	var listed: Array = tables.get("faction_names", [])

	# Positive control: today's wrap (8 names) is a clash the checker sees.
	var wrapped := {"faction_names": ["A", "B", "C", "D", "E", "F", "G", "H"]}
	_assert(_first_clash(wrapped) == [0, 8], "A55 (control): an 8-name table should clash at ids 0 and 8, got %s" % [_first_clash(wrapped)])
	var fifteen := {"faction_names": ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O"]}
	_assert(_first_clash(fifteen) == [], "A55 (control): a 15-distinct-name table should not clash, got %s" % [_first_clash(fifteen)])

	_assert(listed.size() >= MIN_NAMES, "A55: faction_names has %d entries, need at least %d" % [listed.size(), MIN_NAMES])
	var clash := _first_clash(tables)
	_assert(clash.is_empty(), "A55: faction ids %s share the name '%s' (15 consecutive ids must all differ)" % [clash, listed[clash[0] % maxi(listed.size(), 1)] if not clash.is_empty() else ""])
	var distinct := {}
	for n in listed:
		_assert(str(n).strip_edges() != "", "A55: faction_names has an empty entry")
		_assert(not distinct.has(str(n)), "A55: faction_names lists '%s' twice" % str(n))
		distinct[str(n)] = true
