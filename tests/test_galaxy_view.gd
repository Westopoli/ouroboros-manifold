extends SceneTree

# Piece C2 (docs/northstar/plans/briefs/2026-09-22-manager-M3.md item 3;
# docs/northstar/plans/briefs/2026-09-22-two-day-push.md wave-1 row C2):
# res://scenes/galaxy/galaxy_view.tscn draws the C-snapshot galaxy — one point
# per region, owner colour, pan/zoom/click bands — per docs/bible/epics/
# E-16-client-camera-hud-and-world-view.md S-106/S-107 (R-106-01..05,
# R-107-01..05). Data comes from res://autoload/c_bridge.gd's parse of a C
# transport v1 snapshot (docs/architecture.md "C transport v1"); positions are
# not transmitted (C5 rule), so the scene lays systems out itself from a seed.
# Plant ids reused verbatim from docs/northstar/plans/briefs/
# 2026-09-22-p1-galaxy-mockup.md lines ~82-84 (PLANTS list).

const SCENE_PATH := "res://scenes/galaxy/galaxy_view.tscn"
const BRIDGE_SCRIPT_PATH := "res://autoload/c_bridge.gd"
const FIXTURE_PATH := "res://tests/transport/fixtures/snapshot_seed1_tick10.json"
const FALLBACK_PATH := "user://test_galaxy_view_fallback_snapshot.json"
const FALLBACK_N_REGIONS := 60
const PLAYER_FACTION_FIXTURE := 0   # a faction id present in snapshot_seed1_tick10.json (3 regions) and in the 60-region fallback
const PLANTS := ["seed-ignored", "owner-colour-flat", "edges-2d-overlay",
	"pick-radius-zero", "bands-frozen", "conquest-no-recolour"]

var _pass_count := 0
var _fail_count := 0
var _fail_msgs: Array[String] = []
var _root: Node
var _snapshot: Dictionary


func _initialize() -> void:
	await _run_tests()
	print("\n=== Galaxy View Test Results ===")
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
	_snapshot = _load_snapshot()
	_assert(not _snapshot.is_empty(), "could not obtain a snapshot (fixture missing and fallback write failed)")
	# B23 (Architect ruling 2026-10-12, Rev 12b): the view reads the player's faction from snapshot["player_faction"]
	# (CBridge.player_faction()); the fixture has no such key (keys: type, tick, checksum, regions, factions, edges,
	# telegraphs), so without this line the player-colour branch (value 0.95) is never reached by the colour checks below.
	_snapshot["player_faction"] = PLAYER_FACTION_FIXTURE

	var packed = load(SCENE_PATH)
	_assert(packed != null, "cannot load %s (piece C2 not attached yet)" % SCENE_PATH)
	if packed == null or not (packed is PackedScene):
		return

	_root = (packed as PackedScene).instantiate()
	_assert(_root != null, "%s failed to instantiate" % SCENE_PATH)
	if _root == null:
		return
	get_root().add_child(_root)
	await process_frame
	await process_frame

	for m in ["qa_state", "qa_plant", "qa_seed", "qa_camera", "set_snapshot"]:
		_assert(_root.has_method(m), "galaxy_view root missing method: " + m)
	if not (_root.has_method("qa_state") and _root.has_method("qa_plant")
			and _root.has_method("qa_seed") and _root.has_method("qa_camera")
			and _root.has_method("set_snapshot")):
		return

	_root.set_snapshot(_snapshot)
	await process_frame

	_check_qa_state_json_safe()
	_check_system_count_S106_R106_01()
	_check_owners_S106_R106_02()
	_check_edge_counts_S106_R106_02()
	_check_systems_px_S106_R106_01()
	_check_owner_colour_S106_R106_01_02()
	_check_seed_determinism_S107_C5()
	_check_plant_seed_ignored()
	_check_plant_owner_colour_flat()
	_check_plant_edges_2d_overlay()
	_check_plant_edges_2d_overlay_draws_lines()
	_check_plant_pick_radius_zero_R107_01()
	_check_bands_match_prototype_A56()
	_check_plant_bands_frozen_R106_03()
	_check_plant_conquest_no_recolour_R106_02_04()
	_check_plant_nope_is_false()
	await _check_real_boot_loads_80_regions_S106()


# P1 rung finding (galaxy screen empty in real play): scenes/galaxy/
# galaxy_view.gd:69 _load_live_snapshot() asks the live pipe for only 60
# regions, below the 75-region feasibility floor for the default 15-faction
# generator (csrc/ouroboros_sim.h om_world_generate; tests/transport/
# test_pipe_shapes.py's n_regions=80 comment), the pipe answers an error
# frame on set_seed, and nothing surfaces -- qa_state().system_count stays 0.
# Unlike every other check in this file (which calls set_snapshot() directly,
# bypassing _ready()'s own live-load path entirely), this instantiates its
# own galaxy_view through the real boot path -- add_child triggers _ready(),
# which calls _load_live_snapshot() -- and never calls set_snapshot(), so it
# is the real S-106/R-106-01 boot-time content check (docs/bible/epics/
# E-16-client-camera-hud-and-world-view.md), not a check of the render pass
# alone. Requires pipe/ouroboros_pipe to be built (`make pipe/ouroboros_pipe`).
func _check_real_boot_loads_80_regions_S106() -> void:
	var packed = load(SCENE_PATH)
	if packed == null or not (packed is PackedScene):
		_assert(false, "cannot load %s for the live-boot check" % SCENE_PATH)
		return

	var live_root = (packed as PackedScene).instantiate()
	_assert(live_root != null, "%s failed to instantiate for the live-boot check" % SCENE_PATH)
	if live_root == null:
		return

	get_root().add_child(live_root)
	await process_frame
	await process_frame

	if not live_root.has_method("qa_state"):
		_assert(false, "galaxy_view root (live boot) missing method: qa_state")
		live_root.queue_free()
		return

	var state: Dictionary = live_root.qa_state()
	_assert(int(state.get("system_count", -1)) == 80,
		"S-106/R-106-01 (real boot path, scenes/galaxy/galaxy_view.gd:69 _load_live_snapshot -> "
		+ "c_bridge.gd load_snapshot_live, docs/architecture.md \"C transport v1\"): system_count = %s, expected 80"
		% state.get("system_count"))

	live_root.queue_free()


func _check_qa_state_json_safe() -> void:
	var text := JSON.stringify(_root.qa_state())
	_assert(text != "", "qa_state() did not survive JSON.stringify")


func _check_system_count_S106_R106_01() -> void:
	var state: Dictionary = _root.qa_state()
	var expected_n: int = _snapshot.get("regions", []).size()
	_assert(int(state.get("system_count", -1)) == expected_n,
		"S-106/R-106-01: system_count = %s, expected %d" % [state.get("system_count"), expected_n])


func _check_owners_S106_R106_02() -> void:
	var state: Dictionary = _root.qa_state()
	var owners: Dictionary = state.get("owners", {})
	var expected_n: int = _snapshot.get("regions", []).size()
	_assert(owners.size() == expected_n,
		"S-106/R-106-02: owners has %d entries, expected %d" % [owners.size(), expected_n])
	var mismatches := 0
	for r in _snapshot.get("regions", []):
		var i := int(r.get("i", -1))
		var expected := int(r.get("owner", -999))
		if int(owners.get(i, -999)) != expected:
			mismatches += 1
	_assert(mismatches == 0, "S-106/R-106-02: %d region(s) have owners[i] != fixture owner" % mismatches)


func _check_edge_counts_S106_R106_02() -> void:
	var state: Dictionary = _root.qa_state()
	var edge_counts = state.get("edge_counts", null)
	_assert(typeof(edge_counts) == TYPE_DICTIONARY, "edge_counts must be a Dictionary keyed by om_edge_type")
	var total := 0
	if typeof(edge_counts) == TYPE_DICTIONARY:
		for k in edge_counts:
			total += int(edge_counts[k])
	var expected: int = _snapshot.get("edges", []).size()
	_assert(total == expected,
		"S-106/R-106-02: edge_counts totals %d, fixture has %d edges" % [total, expected])


func _check_systems_px_S106_R106_01() -> void:
	var state: Dictionary = _root.qa_state()
	var px: Dictionary = state.get("systems_px", {})
	var expected_n: int = _snapshot.get("regions", []).size()
	# TD-VG-B-13 (assumption-changed, Architect 2026-10-11): old `px.size() == expected_n` assumed every system
	# is in front of a camera outside the disc. With the camera inside the ball (B22) a system behind it has no
	# pixel, so systems_px lists only systems in front (the pick rule, orbit_camera.gd:135). New: every key is a
	# region id, and for every region id `id in px` equals `not camera.is_position_behind(position)`.
	var cam: Camera3D = _root.get_node("OrbitCamera").get_camera()
	var positions: Dictionary = _root.get_positions()
	var region_ids := {}
	for r in _snapshot.get("regions", []):
		region_ids[int(r.get("i", -1))] = true
	var bad_keys := 0
	for k in px:
		if not region_ids.has(int(k)):
			bad_keys += 1
	_assert(bad_keys == 0, "S-106/R-106-01: systems_px has %d key(s) that are not region ids" % bad_keys)
	var wrong := 0
	for id in region_ids:
		var in_front: bool = positions.has(id) and not cam.is_position_behind(positions[id])
		if px.has(id) != in_front:
			wrong += 1
	_assert(wrong == 0,
		"S-106/R-106-01: %d region(s) where (id in systems_px) != not camera.is_position_behind(position)" % wrong)
	var vp := Vector2(get_root().size)
	if vp.x <= 0 or vp.y <= 0:
		vp = Vector2(1920, 1080)
	var outside := 0
	for i in px:
		var p = px[i]
		if typeof(p) != TYPE_ARRAY or p.size() != 2 or p[0] < 0 or p[0] > vp.x or p[1] < 0 or p[1] > vp.y:
			outside += 1
	# TD-VG-B-12 (assumption-changed, Architect 2026-10-10, bound corrected 2026-10-11): old `outside == 0`
	# (every system inside the viewport), then "at least a fifth of the systems_px entries inside the viewport
	# at the default camera" (`inside * 5 >= expected_n`, B22: distance 50, ball radius 71, 23 of 80 inside).
	# TD-VG-B-14 (superseded by B23 prototype scale, Architect 2026-10-12): new `inside * 10 >= expected_n`, at
	# least a tenth, DRAFT-b23-viewport-frac. The prototype's regional default (distance 25 in a ball of radius 50)
	# is a close view of part of the galaxy. The bound is the Architect's own spec number, not a Westley threshold;
	# it guards against the empty "small cluster on grey" frame. The measured count at the built geometry is
	# filled in by the build checker (the ledger row), not by the test writer.
	# TD-VG-B-13: the denominator is the region count, not systems_px.size() (behind-camera systems are absent).
	var inside := px.size() - outside
	_assert(inside * 10 >= expected_n,
		"S-106/R-106-01: only %d/%d systems_px entries fall inside the %dx%d viewport, want at least a tenth of the regions (TD-VG-B-14, DRAFT-b23-viewport-frac)" % [inside, expected_n, int(vp.x), int(vp.y)])


func _check_owner_colour_S106_R106_01_02() -> void:
	var state: Dictionary = _root.qa_state()
	var owners: Dictionary = state.get("owners", {})
	var region_colours: Dictionary = state.get("region_colours", {})
	var owner_colours: Dictionary = state.get("owner_colours", {})
	var expected_n: int = _snapshot.get("regions", []).size()
	_assert(region_colours.size() == expected_n,
		"S-106/R-106-01: region_colours has %d entries, expected %d" % [region_colours.size(), expected_n])
	var mismatches := 0
	for i in owners:
		var owner = owners[i]
		var expected = owner_colours.get(owner, owner_colours.get(str(owner), null))
		if expected == null or not _colour_eq(region_colours.get(i, null), expected):
			mismatches += 1
	_assert(mismatches == 0,
		"S-106/R-106-02: %d region colour(s) do not equal their owner's palette colour (FactionPalette or the scene's own table)" % mismatches)


# C5 rule (docs/architecture.md "C transport v1"): the server sends no
# positions, so the client layout pass owns them; the layout must still be
# deterministic per seed (determinism contract, CLAUDE.md).
func _check_seed_determinism_S107_C5() -> void:
	_root.qa_seed(11)
	var h11 = _root.qa_state().get("hash")
	_root.qa_seed(11)
	var h11b = _root.qa_state().get("hash")
	_assert(h11 == h11b, "qa_seed(11) twice must give an equal hash")
	_root.qa_seed(12)
	var h12 = _root.qa_state().get("hash")
	_assert(h12 != h11, "qa_seed(12) must give a different hash from qa_seed(11)")
	_root.qa_seed(11)


func _check_plant_seed_ignored() -> void:
	_assert(_root.qa_plant("seed-ignored"), "qa_plant(seed-ignored) must return true")
	_root.qa_seed(11)
	var h11 = _root.qa_state().get("hash")
	_root.qa_seed(12)
	var h12 = _root.qa_state().get("hash")
	_assert(h11 == h12, "PLANT seed-ignored: qa_seed(12) should no longer change the hash")


func _check_plant_owner_colour_flat() -> void:
	var owner_variety := _distinct_owner_values(_snapshot.get("regions", []))
	if owner_variety.size() < 2:
		print("SKIP: owner-colour-flat positive control needs >=2 distinct owners in the snapshot, found %d" % owner_variety.size())
		_assert(_root.qa_plant("owner-colour-flat"), "qa_plant(owner-colour-flat) must return true")
		return

	var before: Dictionary = _root.qa_state().get("region_colours", {})
	var distinct_before := _count_distinct(before.values())
	_assert(distinct_before > 1,
		"clean: region_colours should not already be one colour (positive control), got %d distinct" % distinct_before)

	_assert(_root.qa_plant("owner-colour-flat"), "qa_plant(owner-colour-flat) must return true")
	var after: Dictionary = _root.qa_state().get("region_colours", {})
	var distinct_after := _count_distinct(after.values())
	_assert(distinct_after == 1,
		"PLANT owner-colour-flat: region_colours should collapse to one colour, got %d distinct" % distinct_after)


func _check_plant_edges_2d_overlay() -> void:
	var before: bool = bool(_root.qa_state().get("edges_3d", false))
	_assert(before, "clean: edges_3d should be true before the plant (positive control)")
	_assert(_root.qa_plant("edges-2d-overlay"), "qa_plant(edges-2d-overlay) must return true")
	var after: bool = bool(_root.qa_state().get("edges_3d", true))
	_assert(after == false, "PLANT edges-2d-overlay: edges_3d should be false (filaments drawn as a 2D overlay instead of tubes in World)")


func _check_plant_pick_radius_zero_R107_01() -> void:
	var before: float = float(_root.qa_state().get("pick_radius_px", -1))
	_assert(before > 0.0, "R-107-01: clean pick_radius_px should be > 0 before the plant (positive control), got %s" % before)
	_assert(_root.qa_plant("pick-radius-zero"), "qa_plant(pick-radius-zero) must return true")
	var after: float = float(_root.qa_state().get("pick_radius_px", -1))
	_assert(after == 0.0, "PLANT pick-radius-zero: pick_radius_px should be 0, got %s" % after)


# A56 (suspends A48-3): the prototype's band splits stand until Westley has
# compared it with the game. scenes/mockups/galaxy/orbit_camera.gd:28-29 splits
# Overview/Regional at 70 * CIV_SCALE 0.5 = 35 and Regional/Local at 32.5 * 0.5 = 16.25
# (BAND_SPLIT_HIGH/LOW); the game's view uses the same numbers since B23. The bible's
# R-106-03 now carries 37.5 / 32.5 / 20 / 12.5 (its band edges, not these splits, which
# are their midpoints); it is not tested here.
# TD-VG-B-14 (superseded by B23 prototype scale): old pinned dict (splits 70 and 32.5)
# {220: Overview, 100: Overview, 70: Overview, 69.9: Regional, 50: Regional, 32.5: Regional, 32.4: Local, 15: Local},
# new: every distance halved (splits 35 and 16.25).
func _check_bands_match_prototype_A56() -> void:
	var pinned := {110.0: "Overview", 50.0: "Overview", 35.0: "Overview", 34.95: "Regional", 25.0: "Regional", 16.25: "Regional", 16.2: "Local", 7.5: "Local"}
	for d in pinned:
		_root.qa_camera(d, -1)
		_assert(str(_root.qa_state().get("band")) == pinned[d], "A56 prototype parity: band at distance %s should be %s, got %s" % [d, pinned[d], _root.qa_state().get("band")])


func _check_plant_bands_frozen_R106_03() -> void:
	# TD-VG-B-14 (superseded by B23 prototype scale): qa_camera 80 / 20 / 80 / 20 -> 40 / 10 / 40 / 10; the relation is kept
	# (40 is Overview and 10 is Local under splits 35 and 16.25, as 80 and 20 were under 70 and 32.5).
	_root.qa_camera(40.0, -1)
	var overview: String = str(_root.qa_state().get("band"))
	_root.qa_camera(10.0, -1)
	var local_clean: String = str(_root.qa_state().get("band"))
	_assert(local_clean != overview,
		"R-106-03: clean band at distance 10 should differ from distance 40 (positive control), both %s" % overview)

	_root.qa_camera(40.0, -1)
	_assert(_root.qa_plant("bands-frozen"), "qa_plant(bands-frozen) must return true")
	var frozen_overview: String = str(_root.qa_state().get("band"))
	_root.qa_camera(10.0, -1)
	var frozen_local: String = str(_root.qa_state().get("band"))
	_assert(frozen_local == frozen_overview,
		"PLANT bands-frozen: band should stay %s at distance 10, got %s" % [frozen_overview, frozen_local])


func _check_plant_conquest_no_recolour_R106_02_04() -> void:
	var regions: Array = _snapshot.get("regions", [])
	if regions.size() < 2:
		_assert(false, "fixture has fewer than 2 regions; cannot build a conquest test")
		return
	var target_i := int(regions[0].get("i", 0))
	var other_owner := int(regions[0].get("owner", -1)) + 1

	var clean_before = _root.qa_state().get("region_colours", {}).get(target_i)
	_root.set_snapshot(_mutated_snapshot(target_i, other_owner))
	var clean_after = _root.qa_state().get("region_colours", {}).get(target_i)
	_assert(not _colour_eq(clean_before, clean_after),
		"R-106-02/04: clean region_colours[%d] should change once its owner changes (positive control)" % target_i)
	_root.set_snapshot(_snapshot)

	_assert(_root.qa_plant("conquest-no-recolour"), "qa_plant(conquest-no-recolour) must return true")
	var planted_before = _root.qa_state().get("region_colours", {}).get(target_i)
	_root.set_snapshot(_mutated_snapshot(target_i, other_owner))
	var planted_after = _root.qa_state().get("region_colours", {}).get(target_i)
	_assert(_colour_eq(planted_before, planted_after),
		"PLANT conquest-no-recolour: region_colours[%d] should stay unchanged after the owner changes, was %s now %s" % [target_i, planted_before, planted_after])
	_root.set_snapshot(_snapshot)


# QA-002: edges-2d-overlay plant drew nothing because the 2D branch had no
# assets and returned early (scenes/galaxy/galaxy_view.gd _render_filaments).
# After the fix, Line2D nodes must appear in the scene tree (one per edge).
# Also verifies that edge_counts in qa_state() is preserved by the plant
# (the plant changes rendering, never the underlying edge data).
func _check_plant_edges_2d_overlay_draws_lines() -> void:
	# edges-2d-overlay was planted in _check_plant_edges_2d_overlay().
	var expected_edges: int = _snapshot.get("edges", []).size()
	if expected_edges == 0:
		return
	var line2d_count := _count_line2d_nodes(_root)
	_assert(line2d_count > 0,
		"QA-002/PLANT edges-2d-overlay: 0 Line2D nodes in scene tree (%d edges in snapshot); plant drew nothing"
		% expected_edges)
	_assert(line2d_count == expected_edges,
		"QA-002/PLANT edges-2d-overlay: %d Line2D nodes, expected %d (one per edge)"
		% [line2d_count, expected_edges])
	var edge_counts: Dictionary = _root.qa_state().get("edge_counts", {})
	var total := 0
	for k in edge_counts:
		total += int(edge_counts[k])
	_assert(total == expected_edges,
		"QA-002/PLANT edges-2d-overlay: edge_counts total is %d after plant, expected %d (data must be preserved)"
		% [total, expected_edges])


func _count_line2d_nodes(node: Node) -> int:
	var count := 0
	if node is Line2D:
		count += 1
	for child in node.get_children():
		count += _count_line2d_nodes(child)
	return count


func _check_plant_nope_is_false() -> void:
	_assert(not _root.qa_plant("nope"), "qa_plant('nope') must return false")
	for id in PLANTS:
		_assert(_root.qa_plant(id), "qa_plant(%s) must return true" % id)


func _mutated_snapshot(target_i: int, new_owner: int) -> Dictionary:
	var mutated: Dictionary = _snapshot.duplicate(true)
	var mutated_regions: Array = mutated["regions"].duplicate(true)
	for j in range(mutated_regions.size()):
		if int(mutated_regions[j].get("i", -1)) == target_i:
			mutated_regions[j] = mutated_regions[j].duplicate(true)
			mutated_regions[j]["owner"] = new_owner
			break
	mutated["regions"] = mutated_regions
	return mutated


func _distinct_owner_values(regions: Array) -> Array:
	var seen := []
	for r in regions:
		var o = int(r.get("owner", -1))
		if not seen.has(o):
			seen.append(o)
	return seen


func _count_distinct(colours: Array) -> int:
	var uniq := []
	for c in colours:
		var found := false
		for u in uniq:
			if _colour_eq(c, u):
				found = true
				break
		if not found:
			uniq.append(c)
	return uniq.size()


func _colour_eq(a, b) -> bool:
	if a == null or b == null:
		return false
	if typeof(a) != TYPE_ARRAY or typeof(b) != TYPE_ARRAY or a.size() != b.size():
		return false
	for i in range(a.size()):
		if abs(float(a[i]) - float(b[i])) > 0.01:
			return false
	return true


func _load_snapshot() -> Dictionary:
	var via_bridge := _load_snapshot_via_bridge()
	if not via_bridge.is_empty():
		return via_bridge
	if FileAccess.file_exists(FIXTURE_PATH):
		var data = _read_json(FIXTURE_PATH)
		if data != null:
			return data
	var built := _build_minimal_snapshot()
	_write_json(FALLBACK_PATH, built)
	return built


# "feeds it the bridge's snapshot": when res://autoload/c_bridge.gd already
# exists this reads the fixture through it (regions()/edges()/checksum()),
# same as tests/test_c_bridge.gd exercises directly. Degrades to a direct
# JSON parse below when the bridge script is not there yet, so this file's
# red stays attributed to the galaxy_view scene, not a second missing piece.
func _load_snapshot_via_bridge() -> Dictionary:
	var script = load(BRIDGE_SCRIPT_PATH)
	if script == null or not (script is GDScript):
		return {}
	var bridge = (script as GDScript).new()
	if bridge == null:
		return {}
	if not (bridge.has_method("load_snapshot_file") and bridge.has_method("regions")
			and bridge.has_method("edges") and bridge.has_method("checksum")):
		return {}
	var path := FIXTURE_PATH
	if not FileAccess.file_exists(path):
		var built := _build_minimal_snapshot()
		if not _write_json(FALLBACK_PATH, built):
			return {}
		path = FALLBACK_PATH
	var ok = bridge.load_snapshot_file(path)
	if not bool(ok):
		return {}
	return {"regions": bridge.regions(), "edges": bridge.edges(), "checksum": bridge.checksum()}


# Minimal valid instance of docs/northstar/spec_factory/transport/snapshot.schema.json,
# same shape as tests/test_c_bridge.gd's fallback (kept independent per-file: fenced
# tests do not share a non-fenced helper module). Used only when the real fixture
# is missing; FALLBACK_N_REGIONS is fallback-only data, not the expected count.
func _build_minimal_snapshot() -> Dictionary:
	var regions := []
	for i in range(FALLBACK_N_REGIONS):
		regions.append({
			"i": i,
			"owner": (i % 3) - 1,
			"tier": 1,
			"military": 10.0,
			"economy": 10.0,
			"tension": 10.0,
			"population": 10.0,
			"stability": 10.0,
			"capacity": 10.0,
		})
	var edges := []
	for i in range(FALLBACK_N_REGIONS - 1):
		edges.append({"a": i, "b": i + 1, "t": i % 2})
	var factions := []
	for f in range(3):
		factions.append({"id": f, "archetype": 0, "budget": 100.0, "tech": 1.0, "stance": [1, 1, 1]})
	return {
		"type": "snapshot",
		"tick": 10,
		"checksum": 424242,
		"regions": regions,
		"factions": factions,
		"edges": edges,
	}


func _read_json(path: String):
	var f := FileAccess.open(path, FileAccess.READ)
	if f == null:
		return null
	var text := f.get_as_text()
	f.close()
	return JSON.parse_string(text)


func _write_json(path: String, data: Dictionary) -> bool:
	var f := FileAccess.open(path, FileAccess.WRITE)
	if f == null:
		return false
	f.store_string(JSON.stringify(data))
	f.close()
	return true
