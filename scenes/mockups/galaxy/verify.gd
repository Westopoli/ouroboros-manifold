extends SceneTree

const MOCKUP_SCENE := "res://scenes/mockups/galaxy/galaxy_mockup.tscn"
const REPLAY_PATH := "res://scenes/mockups/galaxy/fixtures/jump_log_seed11.json"
const CONTRACT_KEYS := ["seed", "hash", "system_count", "faction_count", "edge_counts", "band",
	"distance", "focused", "hover_faction", "pinned_faction", "systems_px", "owners", "replay",
	"timing_ms", "regen_count"]
const PLANTS := ["seed-ignored", "owner-colour-flat", "edges-2d-overlay", "pick-radius-zero",
	"bands-frozen", "conquest-no-recolour"]

var _failures := 0
var _root: Node
var _h11b: int = 0


func _initialize() -> void:
	_check_conn_3()
	_check_kind_4()

	await _boot_scene()
	if _root != null:
		await _check_det_1()
		await _check_seed_2()
		_check_colour_5()
		_check_band_6()
		_check_pick_7()
		_check_edges_8()
		_check_time_11()
		_check_replay_9()
		_check_shell_12()
		_check_adapter_13()
		await _check_replay_reset_14()
		await _check_replay_counter_15()
		# _check_json_10 activates every qa plant and qa_plants.gd has no
		# deactivate — must run last, or every check after it inherits a
		# permanently-planted fault (found while adding the checks above:
		# "conquest-no-recolour" silently broke a later replay-reset check).
		_check_json_10()

	if _failures > 0:
		print("VERIFY FAILED: %d check(s)" % _failures)
		quit(1)
		return
	print("VERIFY OK")
	quit(0)


func _boot_scene() -> void:
	var packed: PackedScene = load(MOCKUP_SCENE)
	if packed == null:
		_assert(false, "cannot load %s" % MOCKUP_SCENE)
		return
	_root = packed.instantiate()
	get_root().add_child(_root)
	await process_frame
	await process_frame
	if not (_root.has_method("qa_state") and _root.has_method("qa_plant") and _root.has_method("qa_seed")):
		_assert(false, "root missing qa_state/qa_plant/qa_seed contract")
		_root = null


# plant: none (self-test: a hand-built two-component fixture must fail this check)
func _check_conn_3() -> void:
	var g := GalaxyGen.new().generate(11)
	if g.systems.is_empty() or g.factions.is_empty():
		_assert(false, "CONN-3: generate(11) produced no systems/factions")
	else:
		_assert(_all_factions_connected(g), "a faction's territory is not one connected component over border edges")
	var bad := Galaxy.new()
	bad.systems = [{"id": 0, "owner": 0}, {"id": 1, "owner": 0}]
	bad.factions = [{"id": 0}]
	bad.edges = []
	_assert(not _all_factions_connected(bad), "CONN-3 self-test: a disconnected fixture must fail this check")


func _all_factions_connected(g: Galaxy) -> bool:
	var adj := {}
	for e in g.edges:
		if e.kind != "border":
			continue
		adj.get_or_add(e.a, []).append(e.b)
		adj.get_or_add(e.b, []).append(e.a)
	for f in g.factions:
		var members: Array = []
		for sys in g.systems:
			if sys.owner == f.id:
				members.append(sys.id)
		if members.is_empty():
			continue
		var seen := {members[0]: true}
		var queue: Array = [members[0]]
		while queue.size() > 0:
			var cur = queue.pop_front()
			for nb in adj.get(cur, []):
				if not seen.has(nb):
					seen[nb] = true
					queue.append(nb)
		if seen.size() != members.size():
			return false
	return true


# plant: none (self-test: a cross-owner border edge must fail this check)
func _check_kind_4() -> void:
	var g := GalaxyGen.new().generate(11)
	if g.edges.is_empty():
		_assert(false, "KIND-4: generate(11) produced no edges")
	else:
		_assert(_kinds_valid(g), "an edge's kind contradicts its endpoints' owners")
	var bad := Galaxy.new()
	bad.systems = [{"id": 0, "owner": 0}, {"id": 1, "owner": 1}]
	bad.edges = [{"a": 0, "b": 1, "kind": "border"}]
	_assert(not _kinds_valid(bad), "KIND-4 self-test: a cross-owner border edge must fail this check")


func _kinds_valid(g: Galaxy) -> bool:
	for e in g.edges:
		var oa: int = g.systems[e.a].owner
		var ob: int = g.systems[e.b].owner
		var same_owned: bool = oa == ob and oa != -1
		if e.kind == "border" and not same_owned:
			return false
		if e.kind == "trade" and same_owned:
			return false
	return true


# plant: seed-ignored (does not break this check itself, see SEED-2)
# Awaits a frame after each qa_seed(): rebuild frees the previous filaments/
# shells via queue_free() (legacy_constellation_renderer.gd/legacy_shell_
# renderer.gd's regions_cleared handlers), which only actually leaves the
# tree at end-of-frame; without the wait, EDGES-8 later in this same script
# counts stale not-yet-freed children on top of the current ones.
func _check_det_1() -> void:
	_root.qa_seed(11)
	await process_frame
	var h11a = _root.qa_state().hash
	_root.qa_seed(11)
	await process_frame
	_h11b = _root.qa_state().hash
	_assert(h11a == _h11b, "qa_seed(11) twice must hash equal")


# plant: seed-ignored
func _check_seed_2() -> void:
	var systems11: Array = _root.get_node("World/GalaxyView").get_galaxy().systems.duplicate(true)
	_root.qa_seed(12)
	await process_frame
	var h12 = _root.qa_state().hash
	_assert(_h11b != h12, "qa_seed(12) must hash differently from qa_seed(11)")
	var systems12: Array = _root.get_node("World/GalaxyView").get_galaxy().systems.duplicate(true)
	var moved := 0
	var n: int = min(systems11.size(), systems12.size())
	for i in range(n):
		if systems11[i].pos.distance_to(systems12[i].pos) > 5.0 * GalaxyGen.CIV_SCALE:
			moved += 1
	var ok: bool = systems11.size() != systems12.size() or float(moved) / float(n) >= 0.30
	_assert(ok, "seed 12 must move >=30%% of systems or change count (moved %d/%d)" % [moved, n])
	_root.qa_seed(11)
	await process_frame


# plant: owner-colour-flat
func _check_colour_5() -> void:
	var view := _root.get_node("World/GalaxyView")
	var g: Galaxy = view.get_galaxy()
	var bad := 0
	for i in range(g.systems.size()):
		var expected: Color = view.owner_color(g.systems[i].owner, g)
		if not view.get_point_color(i).is_equal_approx(expected):
			bad += 1
	_assert(bad == 0, "%d/%d point colours do not match their owner's palette" % [bad, g.systems.size()])


# plant: bands-frozen
func _check_band_6() -> void:
	var cam := _root.get_node("OrbitCamera")
	cam.qa_camera(80.0 * GalaxyGen.CIV_SCALE, -1)
	_assert(cam.get_band() == "Overview", "distance 80 should be Overview, got %s" % cam.get_band())
	cam.qa_camera(50.0 * GalaxyGen.CIV_SCALE, -1)
	_assert(cam.get_band() == "Regional", "distance 50 should be Regional, got %s" % cam.get_band())
	cam.qa_camera(20.0 * GalaxyGen.CIV_SCALE, -1)
	_assert(cam.get_band() == "Local", "distance 20 should be Local, got %s" % cam.get_band())


# plant: pick-radius-zero
func _check_pick_7() -> void:
	var cam := _root.get_node("OrbitCamera")
	cam.qa_camera(20.0 * GalaxyGen.CIV_SCALE, 0)
	var px: Vector2 = cam.project(0)
	_assert(cam.pick_at(px) == 0, "pick at system 0's own projected pixel must return 0")
	_assert(cam.pick_at(px + Vector2(40, 0)) == -1, "pick 40px away must return -1")


# plant: edges-2d-overlay
# Filament container moved from a bespoke "Filaments" node (pass 1) to
# legacy_constellation_renderer.gd's own "ConstellationRenderer" (pass 2,
# see galaxy_view.gd) — the copied legacy renderer parents each filament
# tube MeshInstance3D directly on itself instead of a separate holder.
func _check_edges_8() -> void:
	var view := _root.get_node("World/GalaxyView")
	var filaments := view.get_node_or_null("ConstellationRenderer")
	_assert(filaments != null and filaments is Node3D, "filament container missing or not a Node3D")
	var g: Galaxy = view.get_galaxy()
	if filaments != null:
		_assert(filaments.get_child_count() == g.edges.size(), "ConstellationRenderer has %d children, expected %d (edges-2d-overlay draws lanes in 2D instead)" % [filaments.get_child_count(), g.edges.size()])
	var overlay := _root.get_node_or_null("HUD/FilamentOverlay2D")
	_assert(overlay == null, "found the 2D fault overlay Control under HUD")


# plant: none
func _check_shell_12() -> void:
	var view := _root.get_node("World/GalaxyView")
	var g: Galaxy = view.get_galaxy()
	var owned_factions: Dictionary = {}
	for sys in g.systems:
		if sys.owner != -1:
			owned_factions[sys.owner] = true
	var shell_count: int = view.get_faction_shell_count()
	_assert(shell_count == owned_factions.size(), "expected %d faction shells (one per owning faction), got %d" % [owned_factions.size(), shell_count])


# plant: none
func _check_adapter_13() -> void:
	var view := _root.get_node("World/GalaxyView")
	var g: Galaxy = view.get_galaxy()
	var wv := view.get_node("WorldViewData")
	_assert(wv.regions.size() == g.systems.size(), "adapter regions count %d != generator systems count %d" % [wv.regions.size(), g.systems.size()])
	var bad := 0
	for sys in g.systems:
		var key := str(sys.id)
		if not wv.regions.has(key):
			bad += 1
			continue
		var expected_fk: String = "neutral" if sys.owner == -1 else "faction_%d" % sys.owner
		if wv.regions[key].faction_id != expected_fk:
			bad += 1
	_assert(bad == 0, "%d/%d adapter regions have wrong id/owner vs the generator" % [bad, g.systems.size()])


# plant: none (self-test: two replay steps must actually move owners[1],
# otherwise the reset half of this check could never fail)
func _check_replay_reset_14() -> void:
	_root.qa_seed(11)
	await process_frame
	var owners_fresh: Dictionary = _root.qa_state().owners
	_root.qa_replay_step()
	_root.qa_replay_step()
	var owners_changed: Dictionary = _root.qa_state().owners
	_assert(owners_changed[1] != owners_fresh[1], "replay-reset self-test: two replay steps should have changed owners[1]")
	_root.qa_replay_restart()
	await process_frame
	var owners_after_restart: Dictionary = _root.qa_state().owners
	var mismatches := 0
	for key in owners_fresh:
		if owners_after_restart.get(key, null) != owners_fresh[key]:
			mismatches += 1
	_assert(mismatches == 0, "%d owners did not reset to the seed's initial ownership after qa_replay_restart" % mismatches)
	_assert(_root.qa_state().replay.index == 0, "qa_replay_restart must reset replay.index to 0")


# plant: none
func _check_replay_counter_15() -> void:
	_root.qa_seed(11)
	await process_frame
	var total: int = _root.qa_state().replay.total
	_assert(total > 0, "replay.total must be > 0 (fixture length)")
	var guard := 0
	while not _root.qa_state().replay.done and guard < 50:
		_root.qa_replay_step()
		guard += 1
	var state: Dictionary = _root.qa_state()
	_assert(state.replay.done, "replay did not reach done within %d steps" % guard)
	_assert(state.replay.index == total, "replay.index %d != replay.total %d at done" % [state.replay.index, total])
	_root.qa_replay_restart()
	await process_frame


func _check_time_11() -> void:
	var state: Dictionary = _root.qa_state()
	var total: float = state.timing_ms.gen + state.timing_ms.build
	_assert(total < 500.0, "timing_ms.gen+build = %.1fms, expected < 500ms" % total)


# plant: conquest-no-recolour
func _check_replay_9() -> void:
	_root.qa_seed(11)
	var text := FileAccess.get_file_as_string(REPLAY_PATH)
	var events = JSON.parse_string(text)
	var max_id: int = _root.get_node("World/GalaxyView").get_galaxy().systems.size() - 1
	for e in events:
		for k in ["from", "to", "at"]:
			if e.has(k):
				_assert(int(e[k]) <= max_id and int(e[k]) >= 0, "event %s=%s out of range [0,%d]" % [k, e[k], max_id])
	var before: Dictionary = _root.qa_state().owners
	_root.qa_replay_step()
	_root.qa_replay_step()
	var after: Dictionary = _root.qa_state().owners
	_assert(after[1] == before[0], "after the first conquest event, owners[1] must equal owners_before[0]")


func _check_json_10() -> void:
	var state: Dictionary = _root.qa_state()
	var text := JSON.stringify(state)
	_assert(text != "", "qa_state() did not survive JSON.stringify")
	for key in CONTRACT_KEYS:
		_assert(state.has(key), "qa_state() missing key %s" % key)
	for id in PLANTS:
		_assert(_root.qa_plant(id), "qa_plant(%s) must return true" % id)
	_assert(not _root.qa_plant("nope"), "qa_plant('nope') must return false")


func _assert(condition: bool, message: String) -> void:
	if not condition:
		_failures += 1
		print("FAIL: %s" % message)
