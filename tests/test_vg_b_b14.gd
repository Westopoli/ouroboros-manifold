extends SceneTree

# Piece B14 (docs/northstar/plans/2026-10-07-visible-game-spec.md rev 4, lane B; bible E-16
# S-106/S-107/S-108): the WIRING of galaxy_view.gd to the B-lane pieces, proven on the instanced
# scene (driven=true, no pipe) through qa_state() and the node tree.
#   B3a shell_renderer.gd on the child ShellRenderer; legacy_shell_renderer.gd deleted.
#   B11 AmbientRig (Node3D, ambient_rig.gd) built in _build_renderers BEFORE the stored tier is read.
#   B10 GalaxyQuality.apply on ready; its res_divisor goes to the renderer.
#   B6  flash_from_delta(delta) -> int, via GalaxyFlash.flashes_for_delta, one flash per region.
#   B7  a TerritoryTween stepped in _process on every owner change.
#   B13 qa_state.unknown_factions; also ambient_rig {present,tier}, galaxy_quality {tier,res_divisor},
#       flashes_active. Every pre-B14 qa_state key stays.
# OPEN (reported, not guessed): B7 has no fixed interface (no class API, no qa_state key), so the
# TerritoryTween wiring is pinned only by source text of galaxy_view.gd (preload of
# res://scenes/galaxy/territory_tween.gd, a TerritoryTween mention in _process). A behavioural
# tween test needs the Architect to fix B7's API. flashes_active is asserted as an int, == 3 right
# after spawning 3 flashes (no frame between).

const SCENE_PATH := "res://scenes/galaxy/galaxy_view.tscn"
const VIEW_SRC := "res://scenes/galaxy/galaxy_view.gd"
const FIXTURE_PATH := "res://tests/transport/fixtures/snapshot_seed1_tick10.json"
const UNKNOWN_OWNER := 9999
# every key galaxy_view.qa_state() exposes on the base (origin/push/vg-b-land), read 2026-10-08
const BASE_KEYS := ["scene", "tick", "plants", "system_count", "owners", "edge_counts", "systems_px",
	"region_colours", "owner_colours", "band", "distance", "pick_radius_px", "edges_3d", "hash",
	"shell_renderer", "error_panel"]

var _pass := 0
var _fail := 0
var _msgs: Array[String] = []


func _initialize() -> void:
	await _run()
	print("\n=== VG B14 galaxy_view wiring Results ===\nPASS: %d  FAIL: %d" % [_pass, _fail])
	if _fail > 0:
		for m in _msgs:
			print("  - " + m)
		print("=== RED ===")
		quit(1)
	else:
		print("=== GREEN ===")
		quit(0)


func _check(ok: bool, msg: String) -> void:
	if ok:
		_pass += 1
	else:
		_fail += 1
		_msgs.append(msg)


func _delta() -> Dictionary:
	return {"type": "delta", "tick": 11, "regions": [], "events": [],
		"attacks": [{"attacker": 0, "target": 7, "band": 2, "conquest": 0},
			{"attacker": 1, "target": 4, "band": 2, "conquest": 1}],
		"collisions": [], "revolts": [{"region": 9, "faction": 1, "roll": 0.02}], "factions": []}


func _snap() -> Dictionary:
	var f := FileAccess.open(FIXTURE_PATH, FileAccess.READ)
	var s = JSON.parse_string(f.get_as_text()) if f != null else null
	return s if s is Dictionary else {}


func _body(src: String, fn: String) -> String:
	var a := src.find("func %s(" % fn)
	if a == -1:
		return ""
	var b := src.find("\nfunc ", a + 5)
	return src.substr(a, (b if b != -1 else src.length()) - a)


func _view() -> Node:
	var v: Node = (load(SCENE_PATH) as PackedScene).instantiate()
	v.driven = true
	root.add_child(v)
	await process_frame
	await process_frame
	return v


func _run() -> void:
	# --- B3a: ShellRenderer is the new renderer, the legacy file is gone
	_check(not FileAccess.file_exists("res://scenes/galaxy/legacy_shell_renderer.gd"),
		"B14: scenes/galaxy/legacy_shell_renderer.gd must be deleted (still exists)")
	var src := FileAccess.get_file_as_string(VIEW_SRC)
	_check(src != "", "control: galaxy_view.gd readable")
	_check(not src.contains("legacy_shell_renderer"), "B14: galaxy_view.gd still references legacy_shell_renderer")
	_check(src.contains("res://scenes/galaxy/shell_renderer.gd"), "B14: galaxy_view.gd does not preload shell_renderer.gd")

	var view := await _view()
	var shell: Node = view.get_node_or_null("ShellRenderer")
	_check(shell != null, "B14: no child node ShellRenderer")
	if shell != null:
		var sp: Script = shell.get_script()
		var path: String = sp.resource_path if sp != null else ""
		_check(path.ends_with("/shell_renderer.gd") and not path.ends_with("legacy_shell_renderer.gd"),
			"B14: ShellRenderer script is '%s', want .../shell_renderer.gd (B3a)" % path)

	# --- B11: AmbientRig
	var rig: Node = view.get_node_or_null("AmbientRig")
	_check(rig is Node3D, "B14: no child Node3D named AmbientRig")
	if rig != null:
		var rp: Script = rig.get_script()
		_check(rp != null and rp.resource_path == "res://scenes/galaxy/ambient_rig.gd",
			"B14: AmbientRig script must be res://scenes/galaxy/ambient_rig.gd")
	var build := _body(src, "_build_renderers")
	var i_rig := build.find("AmbientRig")
	var i_apply := build.find("GalaxyQuality")
	var i_read := build.find("read_tier")
	_check(i_rig != -1, "B14: _build_renderers does not build AmbientRig")
	var first_tier := i_apply if i_read == -1 else (i_read if i_apply == -1 else mini(i_apply, i_read))
	_check(i_rig != -1 and (first_tier == -1 or i_rig < first_tier),
		"B14: AmbientRig must be added in _build_renderers before the stored quality tier is read")

	# --- B10: quality applied on ready, divisor reaches the renderer
	var Quality = load("res://scenes/galaxy/galaxy_quality.gd")
	_check(src.contains("GalaxyQuality") or src.contains("galaxy_quality.gd"), "B14: galaxy_view.gd does not use GalaxyQuality")
	var st: Dictionary = view.qa_state()
	var gq = st.get("galaxy_quality", null)
	_check(gq is Dictionary and gq.has("tier") and gq.has("res_divisor"),
		"B14: qa_state.galaxy_quality {tier, res_divisor} missing, got %s" % str(gq))
	if gq is Dictionary and Quality != null:
		var tier: int = int(gq.get("tier", -1))
		_check(tier == Quality.read_tier(), "B14: galaxy_quality.tier %d != stored tier %d" % [tier, Quality.read_tier()])
		_check(int(gq.get("res_divisor", -1)) == Quality.res_divisor_for_tier(tier), "B14: res_divisor does not match the tier")
		if shell != null:
			_check(shell.get("res_divisor") == gq.get("res_divisor"),
				"B14: ShellRenderer.res_divisor %s != qa_state res_divisor %s" % [str(shell.get("res_divisor")), str(gq.get("res_divisor"))])
	var ar = st.get("ambient_rig", null)
	_check(ar is Dictionary and ar.has("present") and ar.has("tier"), "B14: qa_state.ambient_rig {present, tier} missing, got %s" % str(ar))
	if ar is Dictionary:
		_check(bool(ar.get("present", false)), "B14: qa_state.ambient_rig.present must be true")
		if gq is Dictionary:
			_check(ar.get("tier") == gq.get("tier"), "B14: ambient_rig.tier != galaxy_quality.tier")

	# --- B6: flash_from_delta
	_check(src.contains("flashes_for_delta"), "B14: galaxy_view.gd does not call GalaxyFlash.flashes_for_delta")
	_check(view.has_method("flash_from_delta"), "B14: galaxy_view.gd has no flash_from_delta")
	view.set_snapshot(_snap())
	await process_frame
	if view.has_method("flash_from_delta"):
		_check(int(view.flash_from_delta({"events": [], "attacks": [], "revolts": []})) == 0, "control: empty delta spawns no flash")
		var n = view.flash_from_delta(_delta())
		_check(n == 3, "B14: flash_from_delta must spawn 3 (2 attacks + 1 revolt), got %s" % str(n))
		var fa = view.qa_state().get("flashes_active", null)
		_check(fa is int and fa == 3, "B14: qa_state.flashes_active must be int 3 right after 3 spawns, got %s" % str(fa))
	else:
		_check(false, "B14: qa_state.flashes_active unreachable without flash_from_delta")
	_check(view.qa_state().has("flashes_active"), "B14: qa_state.flashes_active missing")

	# --- B7: tween wiring (source-level, see OPEN above)
	_check(src.contains("res://scenes/galaxy/territory_tween.gd"), "B14: galaxy_view.gd does not preload territory_tween.gd")
	var proc := _body(src, "_process")
	_check(proc.contains("TerritoryTween") or proc.contains("_tween"), "B14: _process does not step a TerritoryTween")

	# --- B13: unknown_factions
	var snap := _snap()
	var known: Array = []
	for fac in snap.get("factions", []):
		known.append(int(fac.get("id", fac.get("i", -1))) if fac is Dictionary else int(fac))
	_check(not known.has(UNKNOWN_OWNER), "fixture precondition: %d must not be a known faction id" % UNKNOWN_OWNER)
	_check(view.qa_state().has("unknown_factions"), "B14: qa_state.unknown_factions missing")
	var bad := snap.duplicate(true)
	bad["regions"][0]["owner"] = UNKNOWN_OWNER
	view.set_snapshot(bad)
	await process_frame
	await process_frame
	var uf = view.qa_state().get("unknown_factions", null)
	_check(uf is Array and (uf as Array).has(UNKNOWN_OWNER), "B14: unknown_factions must list %d, got %s" % [UNKNOWN_OWNER, str(uf)])
	var clean := snap.duplicate(true)
	clean["regions"][0]["owner"] = 0
	view.set_snapshot(clean)
	await process_frame
	await process_frame
	var uf2 = view.qa_state().get("unknown_factions", null)
	_check(uf2 is Array and (uf2 as Array).is_empty(), "control: all owners known gives empty unknown_factions, got %s" % str(uf2))

	# --- parity: every pre-B14 key stays
	var final_state: Dictionary = view.qa_state()
	for k in BASE_KEYS:
		_check(final_state.has(k), "parity: qa_state lost the key '%s'" % k)
	_check(final_state.get("scene") == "galaxy_view", "parity: scene key value")
	var sr = final_state.get("shell_renderer", {})
	_check(sr is Dictionary and bool(sr.get("present", false)) and sr.has("significance"), "parity: shell_renderer {present, significance}")
	view.queue_free()
