extends SceneTree

# Piece C5-G2 (docs/northstar/plans/2026-09-28-gap-fix-and-migration-plan.md
# "G-G2 renderers"): the live galaxy view draws through the prototype's shell and
# constellation renderers, fed by one adapter from the live snapshot (region i,
# owner; edge a, b, t) into the renderers' regions / connections / territories
# shape. E-16 S-106:
#   R-106-02  faction territory: adjacent same-faction systems are joined by
#             filament arcs (border and both edges solid, trade edges thinner and
#             dimmer); each faction's systems share one translucent shell.
#   R-106-02/R-106-04 (conquest recolour, fenced today by test_galaxy_view.gd):
#             a region that changes owner is recoloured through its shell.
# The test finds the pieces by what they expose, not by file name, so the renderers
# can live at any path under scenes/galaxy:
#   data node        any node under the view whose `regions`, `connections` and
#                    `territories` properties are Dictionaries (the legacy
#                    world-view data shape; ids are strings, str(region index)).
#   shell renderer   any node with get_faction_shell_count().
#   constellation    any node with get_filament_visuals() (one visual per connection).
# Needs no display: the prototype's own verify.gd drives the same renderers headless.

const SCENE_PATH := "res://scenes/galaxy/galaxy_view.tscn"
const FIXTURE_PATH := "res://tests/transport/fixtures/snapshot_seed1_tick10.json"
const COLOUR_TOLERANCE := 0.01
const SETTLE_SEC := 3.0

var _pass_count := 0
var _fail_count := 0
var _fail_msgs: Array[String] = []
var _view: Node
var _snap: Dictionary


func _initialize() -> void:
	await _run_tests()
	print("\n=== Galaxy Renderers Test Results ===")
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


func _run_tests() -> void:
	var packed = load(SCENE_PATH)
	_assert(packed != null, "cannot load " + SCENE_PATH)
	if packed == null:
		return
	_view = (packed as PackedScene).instantiate()
	get_root().add_child(_view)
	await process_frame
	await process_frame
	var parsed = JSON.parse_string(FileAccess.get_file_as_string(FIXTURE_PATH))
	_assert(parsed is Dictionary, "snapshot fixture unreadable")
	if not (parsed is Dictionary):
		return
	_snap = parsed
	_view.set_snapshot(_snap)
	for _i in range(3):
		await process_frame

	var data := _find(_view, func(n): return n.get("regions") is Dictionary and n.get("connections") is Dictionary and n.get("territories") is Dictionary)
	var shell := _find(_view, func(n): return n.has_method("get_faction_shell_count"))
	var constellation := _find(_view, func(n): return n.has_method("get_filament_visuals"))
	_assert(data != null, "G-G2: no adapter output node with regions/connections/territories dictionaries under the galaxy view")
	_assert(shell != null, "G-G2: no shell renderer (get_faction_shell_count) under the galaxy view")
	_assert(constellation != null, "G-G2: no constellation renderer (get_filament_visuals) under the galaxy view")
	if data == null or shell == null or constellation == null:
		return

	_check_regions_R106_01(data)
	_check_territories_R106_02(data)
	_check_connections_R106_02(data, _snap)
	await _check_edge_types_R106_02(data)
	await _check_shells_R106_02(shell)
	await _check_filaments_R106_02(constellation, data)
	await _check_conquest_recolours_through_shell_R106_02(data, shell)


func _find(node: Node, pred: Callable) -> Node:
	for child in node.get_children():
		if pred.call(child):
			return child
		var deeper := _find(child, pred)
		if deeper != null:
			return deeper
	return null


func _owner_of(snap: Dictionary, i: int) -> int:
	for r in snap["regions"]:
		if int(r["i"]) == i:
			return int(r["owner"])
	return -999


func _colour_eq(a: Color, b: Array) -> bool:
	return absf(a.r - float(b[0])) < COLOUR_TOLERANCE and absf(a.g - float(b[1])) < COLOUR_TOLERANCE and absf(a.b - float(b[2])) < COLOUR_TOLERANCE


func _distinct_owners(snap: Dictionary) -> Array:
	var seen := {}
	for r in snap["regions"]:
		if int(r["owner"]) >= 0:
			seen[int(r["owner"])] = true
	return seen.keys()


func _check_regions_R106_01(data: Node) -> void:
	var regions: Dictionary = data.get("regions")
	_assert(regions.size() == _snap["regions"].size(), "G-G2: adapter holds %d regions, snapshot has %d" % [regions.size(), _snap["regions"].size()])
	var by_owner := {}
	var colours: Dictionary = _view.qa_state()["region_colours"]
	for r in _snap["regions"]:
		var key := str(int(r["i"]))
		_assert(regions.has(key), "G-G2: region %s missing from the adapter output" % key)
		if not regions.has(key):
			continue
		var entry: Dictionary = regions[key]
		var owner := int(r["owner"])
		if not by_owner.has(owner):
			by_owner[owner] = entry["faction_id"]
		_assert(entry["faction_id"] == by_owner[owner], "G-G2: region %s owner %d has faction_id %s, its faction mates have %s" % [key, owner, entry["faction_id"], by_owner[owner]])
		_assert(_colour_eq(entry["color"], colours[int(r["i"])]), "G-G2: region %s colour %s differs from qa_state region_colours %s" % [key, entry["color"], colours[int(r["i"])]])
	var seen_ids := {}
	for owner in by_owner:
		_assert(not seen_ids.has(by_owner[owner]), "G-G2: owners share faction_id %s" % by_owner[owner])
		seen_ids[by_owner[owner]] = true


func _check_territories_R106_02(data: Node) -> void:
	var territories: Dictionary = data.get("territories")
	var owned := 0
	for r in _snap["regions"]:
		var key := str(int(r["i"]))
		if int(r["owner"]) >= 0:
			owned += 1
			_assert(territories.has(key), "G-G2: owned region %s has no territory (it joins its faction's shell)" % key)
		else:
			_assert(not territories.has(key), "G-G2: unowned region %s has a territory" % key)
	_assert(territories.size() == owned, "G-G2: %d territories, %d owned regions" % [territories.size(), owned])


func _check_connections_R106_02(data: Node, snap: Dictionary) -> void:
	var connections: Dictionary = data.get("connections")
	var checked := 0
	for e in snap["edges"]:
		var a := int(e["a"])
		var b := int(e["b"])
		var oa := _owner_of(snap, a)
		if oa < 0 or oa != _owner_of(snap, b):
			continue
		checked += 1
		var key := str(a) + "::" + str(b) if str(a) < str(b) else str(b) + "::" + str(a)
		_assert(connections.has(key), "R-106-02: same-faction edge %d-%d has no connection" % [a, b])
		if connections.has(key):
			var want := "trade" if int(e["t"]) == 1 else "border"
			_assert(connections[key]["connection_type"] == want, "R-106-02: edge %d-%d type t=%d should be %s, adapter says %s" % [a, b, int(e["t"]), want, connections[key]["connection_type"]])
	_assert(checked >= 5, "fixture has fewer than 5 same-faction edges (checked %d)" % checked)


# The fixture's same-faction edges are all type 2 (both); give some of them
# type 0 (border) and 1 (trade) so the type mapping is exercised.
func _check_edge_types_R106_02(data: Node) -> void:
	var mutated: Dictionary = _snap.duplicate(true)
	var n := 0
	for e in mutated["edges"]:
		var oa := _owner_of(mutated, int(e["a"]))
		if oa >= 0 and oa == _owner_of(mutated, int(e["b"])):
			e["t"] = n % 3
			n += 1
	_view.set_snapshot(mutated)
	await process_frame
	_check_connections_R106_02(data, mutated)
	_view.set_snapshot(_snap)
	await process_frame


func _wait_until(pred: Callable) -> bool:
	var deadline := Time.get_ticks_msec() + int(SETTLE_SEC * 1000.0)
	while Time.get_ticks_msec() < deadline:
		if pred.call():
			return true
		await process_frame
	return pred.call()


func _check_shells_R106_02(shell: Node) -> void:
	var want := _distinct_owners(_snap).size()
	var ok: bool = await _wait_until(func(): return shell.get_faction_shell_count() == want)
	_assert(ok, "R-106-02: %d shells for %d owning factions (each faction's systems share one shell)" % [shell.get_faction_shell_count(), want])


func _check_filaments_R106_02(constellation: Node, data: Node) -> void:
	var want: int = (data.get("connections") as Dictionary).size()
	var ok: bool = await _wait_until(func(): return constellation.get_filament_visuals().size() == want)
	_assert(ok, "R-106-02: %d filament arcs for %d connections" % [constellation.get_filament_visuals().size(), want])
	_assert(want > 0, "no connections to draw")


func _check_conquest_recolours_through_shell_R106_02(data: Node, shell: Node) -> void:
	# Hand every region of the faction that owns the most regions to the faction
	# that owns the fewest: one shell disappears and the surviving faction's
	# shell and territory colours cover the conquered regions.
	var counts := {}
	for r in _snap["regions"]:
		if int(r["owner"]) >= 0:
			counts[int(r["owner"])] = int(counts.get(int(r["owner"]), 0)) + 1
	var loser := -1
	var winner := -1
	for o in counts:
		if loser == -1 or counts[o] < counts[loser]:
			loser = o
		if winner == -1 or counts[o] > counts[winner]:
			winner = o
	_assert(loser != winner, "fixture has only one owning faction")
	if loser == winner:
		return
	var mutated: Dictionary = _snap.duplicate(true)
	var moved := []
	for r in mutated["regions"]:
		if int(r["owner"]) == loser:
			r["owner"] = winner
			moved.append(int(r["i"]))
	_view.set_snapshot(mutated)
	var want := _distinct_owners(mutated).size()
	var ok: bool = await _wait_until(func(): return shell.get_faction_shell_count() == want)
	_assert(ok, "R-106-02: after faction %d lost all regions the shell count is %d, expected %d" % [loser, shell.get_faction_shell_count(), want])
	var colours: Dictionary = _view.qa_state()["region_colours"]
	var territories: Dictionary = data.get("territories")
	var regions: Dictionary = data.get("regions")
	var winner_region := ""
	for r in _snap["regions"]:
		if int(r["owner"]) == winner:
			winner_region = str(int(r["i"]))
			break
	var winner_fid = regions[winner_region]["faction_id"] if regions.has(winner_region) else null
	for i in moved:
		var key := str(i)
		_assert(territories.has(key) and _colour_eq(territories[key]["color"], colours[i]), "R-106-02: conquered region %d territory not recoloured to the new owner" % i)
		_assert(regions.has(key) and _colour_eq(regions[key]["color"], colours[i]), "R-106-02: conquered region %d point not recoloured to the new owner" % i)
		_assert(regions.has(key) and regions[key]["faction_id"] == winner_fid, "R-106-02: conquered region %d not grouped with the conqueror's shell" % i)
