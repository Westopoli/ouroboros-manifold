extends SceneTree

# Piece B6 (docs/northstar/plans/2026-10-07-visible-game-spec.md rev 4, lane B;
# preflight 3-galaxy-field.md line 94): war flashes, R-106-04 (E-16 S-106).
# Built on a FIXTURE delta frame (docs/architecture.md "delta": attacks[], revolts[],
# events[]); K-a's bridge does not yet expose these, so this marks: when K-a lands
# the fixture is replaced by a bridge-fed frame (# See also: K-a pipe/bridge pieces).
#
# INTERFACE FIXED BY THIS TEST (builder follows; it is a draft nobody else gave):
#   res://scenes/galaxy/galaxy_flash.gd, static func flashes_for_delta(delta: Dictionary) -> Array
#     one entry per attack or revolt record: {"kind": "attack"|"conquest"|"revolt", "region": int}
#     attack record -> "conquest" if conquest==1 else "attack", region = target
#     revolt record -> "revolt", region = region; "events" produce no flash
#   res://scenes/galaxy/galaxy_view.gd, func flash_from_delta(delta: Dictionary) -> int
#     spawns one flash per entry above on the drawn systems; returns the count spawned.
# OPEN (report, not guessed): the attacker is a faction id in the delta, not a region,
# so the attacker-side system flash of R-106-04 has no region source; only the target
# region is tested.

const FLASH_PATH := "res://scenes/galaxy/galaxy_flash.gd"
const VIEW_PATH := "res://scenes/galaxy/galaxy_view.tscn"
const FIXTURE_PATH := "res://tests/transport/fixtures/snapshot_seed1_tick10.json"

var _pass := 0
var _fail := 0
var _msgs: Array[String] = []


func _initialize() -> void:
	await _run()
	print("\n=== VG B6 flash Results ===\nPASS: %d  FAIL: %d" % [_pass, _fail])
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
	return {"type": "delta", "tick": 11, "regions": [],
		"events": [{"tick": 11, "region": 3, "template": 5, "chain": -1, "source": 0,
			"delta": [0, -2.0, 3.0, 0], "creates_faction": 0}],
		"attacks": [
			{"attacker": 0, "target": 7, "band": 2, "conquest": 0},
			{"attacker": 1, "target": 4, "band": 2, "conquest": 1}],
		"collisions": [],
		"revolts": [{"region": 9, "faction": 1, "roll": 0.02}],
		"factions": []}


func _run() -> void:
	# R-106-04 mapping: attack, conquest and revolt each flash at their region (test_r106_04_*)
	var script = load(FLASH_PATH)
	_check(script != null, "R-106-04: %s missing (war flashes not built)" % FLASH_PATH)
	if script != null:
		var out: Array = script.flashes_for_delta(_delta())
		_check(out.size() == 3, "R-106-04: 2 attacks + 1 revolt must give 3 flashes, got %d" % out.size())
		var seen := {}
		for f in out:
			seen[str(f.get("kind")) + ":" + str(f.get("region"))] = true
		_check(seen.has("attack:7"), "R-106-04: attack at target region 7")
		_check(seen.has("conquest:4"), "R-106-04: conquest at target region 4")
		_check(seen.has("revolt:9"), "R-106-04: revolt at region 9")
		_check(not seen.has("attack:4"), "R-106-04: a conquest is one flash, not also an attack")
		# the generic event (region 3) is not a war flash
		for f in out:
			_check(int(f.get("region")) != 3, "R-106-04: events[] must not flash")
		# positive control: empty lists give no flashes
		var empty: Array = script.flashes_for_delta({"events": [], "attacks": [], "revolts": []})
		_check(empty.size() == 0, "control: empty delta must give no flashes")
		# determinism: same frame, same list
		_check(script.flashes_for_delta(_delta()) == out, "determinism: same delta, same list")

	# Wiring: the shipped view spawns the flashes (S-106 reachable)
	var packed = load(VIEW_PATH)
	_check(packed != null, "view scene loads")
	if packed == null:
		return
	var view: Node = packed.instantiate()
	root.add_child(view)
	await process_frame
	var f := FileAccess.open(FIXTURE_PATH, FileAccess.READ)
	var snap = JSON.parse_string(f.get_as_text()) if f != null else null
	if snap is Dictionary and view.has_method("set_snapshot"):
		view.set_snapshot(snap)
		await process_frame
	_check(view.has_method("flash_from_delta"), "R-106-04: galaxy_view.gd has no flash_from_delta (not wired)")
	if view.has_method("flash_from_delta"):
		var n: int = view.flash_from_delta(_delta())
		_check(n == 3, "R-106-04: view must spawn 3 flashes, got %d" % n)
		_check(view.flash_from_delta({"events": [], "attacks": [], "revolts": []}) == 0,
			"control: empty delta spawns none")
	view.queue_free()
