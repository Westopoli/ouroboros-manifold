extends SceneTree

# Piece C5-G3 (docs/northstar/plans/2026-09-28-gap-fix-and-migration-plan.md
# "G-G3 labels and hover"; mission-plays plan item C5): the live galaxy view
# floats faction name labels from the snapshot's factions[] and tracks which
# system the pointer is on.
#   R-106-03  in Overview (camera distance >= 35, TD-VG-B-14: was 70) faction names float at the
#             shell centres.
#   R-107-05  a system hover gives the system under the pointer; off every
#             system there is none.
#   G-G3      names come from the client's own derivation (chronicle_names.gd,
#             "{faction_name}" for the faction id), since the wire carries none.
#   A48-6     a faction id the snapshot's factions[] does not list is an error:
#             its label reads "Unknown", qa_state()["unknown_factions"] (sorted
#             array of those owner ids, [] when none) reports it, and the text
#             "[faction]" never reaches the screen. The 15-factions-for-8-names
#             wrap is a known visual defect (ledger), not tested.
# Labels are found by being Label3D nodes under the view; the hovered system is
# read from OrbitCamera.get_hovered() (-1 for none), the prototype camera's name
# for it. Runs on a real display (hover needs the pick radius in real pixels),
# from tests/qa/desktop/test_galaxy_labels.py, which parses the RESULT lines.
# Positive control: labels_follow_conquest asserts a label is present before the
# conquest and absent after, so a view that never draws labels fails the first
# half and one that never retires them fails the second.

const SCENE_PATH := "res://scenes/galaxy/galaxy_view.tscn"
const FIXTURE_PATH := "res://tests/transport/fixtures/snapshot_seed1_tick10.json"
const NAMES_SCRIPT := "res://scenes/world/chronicle_names.gd"
const LIBRARY_PATH := "res://library/chronicle/fragments.json"
const CHECKS := ["labels_overview", "labels_at_centroid", "labels_follow_conquest", "hover_system", "hover_clear", "unknown_faction"]
const OVERVIEW_DISTANCE := 75.0   # TD-VG-B-14: was 150.0 (B23 prototype scale, halved); still Overview, 75 >= split 35
const SETTLE_SEC := 3.0

var _check_name := ""
var _failed: Dictionary = {}
var _view: Node
var _rig: Node
var _snap: Dictionary
var _names


func _initialize() -> void:
	await _run_tests()
	for name in CHECKS:
		print("RESULT " + JSON.stringify({"check": name, "ok": not _failed.has(name) and not _failed.has(""), "msg": _failed.get(name, _failed.get("", ""))}))
	print("PASS: %d  FAIL: %d" % [CHECKS.size() - _failed.size(), _failed.size()])
	quit(1 if not _failed.is_empty() else 0)


func _assert(cond: bool, msg: String) -> void:
	if not cond and not _failed.has(_check_name):
		_failed[_check_name] = msg


func _run_tests() -> void:
	var packed = load(SCENE_PATH)
	_assert(packed != null, "cannot load " + SCENE_PATH)
	if packed == null:
		return
	_view = (packed as PackedScene).instantiate()
	get_root().add_child(_view)
	await process_frame
	await process_frame
	_snap = JSON.parse_string(FileAccess.get_file_as_string(FIXTURE_PATH))
	_view.set_snapshot(_snap)
	await process_frame
	_rig = _view.get_node_or_null("OrbitCamera")
	_assert(_rig != null, "galaxy_view has no OrbitCamera node")
	_names = load(NAMES_SCRIPT).new()
	var lib = JSON.parse_string(FileAccess.get_file_as_string(LIBRARY_PATH))
	_names.load_tables(lib.get("name_tables", {}))
	if _rig == null:
		return

	_check_name = "labels_overview"
	await _check_labels_overview()
	_check_name = "labels_at_centroid"
	await _check_labels_at_centroid()
	_check_name = "labels_follow_conquest"
	await _check_labels_follow_conquest()
	_check_name = "hover_system"
	await _check_hover_system()
	_check_name = "hover_clear"
	await _check_hover_clear()
	_check_name = "unknown_faction"
	await _check_unknown_faction()


func _name_of(faction: int) -> String:
	return _names.fill_template("{faction_name}", -1, faction)


func _owners(snap: Dictionary) -> Array:
	var seen := {}
	for r in snap["regions"]:
		if int(r["owner"]) >= 0:
			seen[int(r["owner"])] = true
	var out := seen.keys()
	out.sort()
	return out


func _labels(node: Node, out: Array) -> void:
	for child in node.get_children():
		if child is Label3D:
			out.append(child)
		_labels(child, out)


func _label_for(text: String) -> Label3D:
	var all := []
	_labels(_view, all)
	for l in all:
		if (l as Label3D).text == text:
			return l
	return null


# The placeholder name table has 8 names for 15 factions, so two factions can
# share a name: labels are counted per name, not looked up by it.
func _shown_count(text: String) -> int:
	var all := []
	_labels(_view, all)
	var n := 0
	for l in all:
		if (l as Label3D).text == text and _shown(l):
			n += 1
	return n


func _owners_named(snap: Dictionary, text: String) -> int:
	var n := 0
	for f in _owners(snap):
		if _name_of(f) == text:
			n += 1
	return n


func _shown(l: Label3D) -> bool:
	return l.is_visible_in_tree() and l.modulate.a > 0.05


func _frames(n: int) -> void:
	for _i in range(n):
		await process_frame


func _overview() -> void:
	_view.qa_camera(OVERVIEW_DISTANCE, -1)
	await _frames(12)


func _px(id: int) -> Vector2:
	var p = _view.qa_state()["systems_px"][id]
	return Vector2(p[0], p[1])


func _check_labels_overview() -> void:
	await _overview()
	_assert(_view.qa_state()["band"] == "Overview", "camera at %s is not in the Overview band" % OVERVIEW_DISTANCE)
	for f in _owners(_snap):
		var text := _name_of(f)
		_assert(_shown_count(text) == _owners_named(_snap, text), "R-106-03: '%s' (faction %d) shown on %d labels, %d owning factions carry that name" % [text, f, _shown_count(text), _owners_named(_snap, text)])
	_assert(_shown_count("[faction]") == 0, "a label carries the unresolved '[faction]' placeholder")


# The label floats over its faction's systems: inside the screen bounding box of
# their points, with a margin for the lift above the shell centre.
func _check_labels_at_centroid() -> void:
	await _overview()
	var width := float(get_root().size.x)
	for f in _owners(_snap):
		if _owners_named(_snap, _name_of(f)) != 1:
			continue
		var label := _label_for(_name_of(f))
		if label == null:
			_assert(false, "R-106-03: no label for faction %d to place" % f)
			continue
		var lo := Vector2(INF, INF)
		var hi := Vector2(-INF, -INF)
		for r in _snap["regions"]:
			if int(r["owner"]) == f:
				var p := _px(int(r["i"]))
				lo = Vector2(minf(lo.x, p.x), minf(lo.y, p.y))
				hi = Vector2(maxf(hi.x, p.x), maxf(hi.y, p.y))
		var margin := width * 0.06
		var at: Vector2 = _rig.project(label.global_position)
		_assert(at.x >= lo.x - margin and at.x <= hi.x + margin and at.y >= lo.y - margin and at.y <= hi.y + margin, "R-106-03: faction %d's label is at %s, outside its systems' box %s to %s" % [f, at, lo, hi])


func _check_labels_follow_conquest() -> void:
	await _overview()
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
	_assert(loser != -1 and loser != winner, "fixture has fewer than two owners")
	if loser == -1 or loser == winner:
		return
	var loser_name := _name_of(loser)
	_assert(_shown_count(loser_name) == _owners_named(_snap, loser_name) and _shown_count(loser_name) >= 1, "R-106-03: faction %d has no label before its conquest" % loser)
	var mutated: Dictionary = _snap.duplicate(true)
	for r in mutated["regions"]:
		if int(r["owner"]) == loser:
			r["owner"] = winner
	_view.set_snapshot(mutated)
	await _frames(12)
	_assert(_shown_count(loser_name) == _owners_named(mutated, loser_name), "R-106-03: faction %d holds no region and its label is still shown (%d labels '%s', %d owners carry it)" % [loser, _shown_count(loser_name), loser_name, _owners_named(mutated, loser_name)])
	var winner_name := _name_of(winner)
	_assert(_shown_count(winner_name) == _owners_named(mutated, winner_name), "R-106-03: the conqueror's label count changed (%d labels '%s')" % [_shown_count(winner_name), winner_name])
	_view.set_snapshot(_snap)
	await _frames(12)


func _isolated_system() -> int:
	var state: Dictionary = _view.qa_state()
	var radius := float(state["pick_radius_px"])
	var ids: Array = state["systems_px"].keys()
	ids.sort()
	var size := Vector2(get_root().size)
	for id in ids:
		var p := _px(int(id))
		if p.x < 80.0 or p.y < 80.0 or p.x > size.x - 80.0 or p.y > size.y - 80.0:
			continue
		var ok := true
		for other in ids:
			if other != id and _px(int(other)).distance_to(p) < radius * 3.0:
				ok = false
				break
		if ok:
			return int(id)
	return -1


func _move_to(at: Vector2) -> void:
	var ev := InputEventMouseMotion.new()
	ev.position = at
	ev.global_position = at
	ev.relative = Vector2(1, 0)
	get_root().push_input(ev)
	await _frames(3)


func _check_hover_system() -> void:
	_assert(_rig.has_method("get_hovered"), "R-107-05: OrbitCamera has no get_hovered()")
	if not _rig.has_method("get_hovered"):
		return
	await _overview()
	var id := _isolated_system()
	_assert(id != -1, "no isolated on-screen system to hover")
	if id == -1:
		return
	await _move_to(_px(id))
	_assert(int(_rig.get_hovered()) == id, "R-107-05: pointer on system %d, get_hovered() says %s" % [id, _rig.get_hovered()])


func _check_hover_clear() -> void:
	if not _rig.has_method("get_hovered"):
		_assert(false, "R-107-05: OrbitCamera has no get_hovered()")
		return
	await _overview()
	var id := _isolated_system()
	if id == -1:
		_assert(false, "no isolated on-screen system to hover")
		return
	await _move_to(_px(id))
	var on := int(_rig.get_hovered())
	await _move_to(_px(id) + Vector2(0, 90))
	_assert(on == id and int(_rig.get_hovered()) == -1, "R-107-05: hover did not clear when the pointer left the system (on=%s, after=%s)" % [on, _rig.get_hovered()])


# A48-6. Region 0's owner is re-pointed at id 99, which factions[] does not list.
# Positive control: on the clean fixture unknown_factions is [] and no label
# reads "Unknown", so a view that always says Unknown, or never reports, fails.
func _check_unknown_faction() -> void:
	await _overview()
	var clean: Dictionary = _view.qa_state()
	_assert(clean.get("unknown_factions", null) is Array and (clean.get("unknown_factions") as Array).is_empty(), "A48-6 (control): qa_state unknown_factions should be [] on the clean fixture (got %s)" % [clean.get("unknown_factions", null)])
	_assert(_shown_count("Unknown") == 0, "A48-6 (control): a label reads Unknown with every faction known")
	var mutated: Dictionary = _snap.duplicate(true)
	var victim := -1
	for r in mutated["regions"]:
		if int(r["owner"]) >= 0:
			r["owner"] = 99
			victim = int(r["i"])
			break
	_assert(victim != -1, "fixture has no owned region to re-point")
	_view.set_snapshot(mutated)
	await _frames(12)
	var state: Dictionary = _view.qa_state()
	_assert(state.get("unknown_factions", null) is Array and 99 in (state.get("unknown_factions") as Array), "A48-6: qa_state unknown_factions does not report faction 99 (got %s)" % [state.get("unknown_factions", null)])
	_assert(_shown_count("Unknown") == 1, "A48-6: expected one shown label reading Unknown for faction 99, found %d" % _shown_count("Unknown"))
	_assert(_shown_count("[faction]") == 0, "A48-6: a label carries the unresolved '[faction]' placeholder")
	_view.set_snapshot(_snap)
	await _frames(12)
