extends SceneTree

# Piece B17 (docs/northstar/plans/2026-10-07-visible-game-spec.md rev 4, lane B; bible E-16
# R-106-03, S-106; review docs/northstar/story_reviews/B.md row S-106: "placeholder 'Faction N'
# text doubled over real names"): faction labels on the instanced galaxy view
# (res://scenes/galaxy/galaxy_view.tscn, driven=true, no pipe, seed1 tick10 fixture).
#   - exactly ONE label per faction (every Label3D/Label under the view whose text equals the
#     faction's name counts; a second label set makes the count 2);
#   - its text is the faction's name from snapshot.factions[].name, never "Faction N" while a name
#     exists; "Unknown" only for an owner that is not in the faction list.
# Headless; needs no renderer.
# OPEN (reported, not guessed): the fixture's factions carry NO "name" key, and docs/architecture.md
# line 103 says a "name" entry in a payload is not read (names come from chronicle_names.gd). This
# test injects "name" into a copy of snapshot.factions, as the B17 brief states the wire does.
# Run: scripts/run_godot_tests.sh tests/test_vg_b_b17.gd

const SCENE_PATH := "res://scenes/galaxy/galaxy_view.tscn"
const FIXTURE_PATH := "res://tests/transport/fixtures/snapshot_seed1_tick10.json"
const UNKNOWN_OWNER := 9999
const NAMES := ["Aurelian Concord", "Brine Hegemony", "Cobalt Reach", "Dunmark League",
	"Ember Compact", "Fenwick Union", "Garnet Syndicate", "Hollow Crown", "Ivory Assembly",
	"Jasper Dominion", "Kestrel Pact", "Lumen Circle", "Marrow Throne", "Nettle Court", "Opal Company"]

var _pass := 0
var _fail := 0
var _msgs: Array[String] = []


func _initialize() -> void:
	await _run()
	print("\n=== B17 labels: PASS %d FAIL %d ===" % [_pass, _fail])
	for m in _msgs:
		print("  - " + m)
	print("=== %s ===" % ("RED" if _fail > 0 else "GREEN"))
	quit(1 if _fail > 0 else 0)


func _check(c: bool, msg: String) -> void:
	if c:
		_pass += 1
	else:
		_fail += 1
		_msgs.append(msg)


func _texts(n: Node, out: Array) -> void:
	if n is Label3D:
		out.append((n as Label3D).text)
	elif n is Label:
		out.append((n as Label).text)
	for c in n.get_children():
		_texts(c, out)


func _count(texts: Array, s: String) -> int:
	var k := 0
	for t in texts:
		if t == s:
			k += 1
	return k


func _run() -> void:
	var f := FileAccess.open(FIXTURE_PATH, FileAccess.READ)
	var snap = JSON.parse_string(f.get_as_text()) if f != null else null
	_check(snap is Dictionary, "control: fixture readable")
	if not (snap is Dictionary):
		return
	var factions: Array = snap.get("factions", [])
	_check(factions.size() >= 3 and factions.size() <= NAMES.size(), "control: fixture has 3..%d factions, got %d" % [NAMES.size(), factions.size()])
	var named := (snap as Dictionary).duplicate(true)
	var known: Array = []
	for i in named["factions"].size():
		named["factions"][i]["name"] = NAMES[i]
		known.append(int(named["factions"][i]["id"]))
	var owned := {}
	for r in named["regions"]:
		var o := int(r.get("owner", -1))
		if known.has(o):
			owned[o] = true
	_check(owned.size() >= 3, "control: at least 3 factions own a region, got %d" % owned.size())

	var v: Node = (load(SCENE_PATH) as PackedScene).instantiate()
	v.driven = true
	get_root().add_child(v)
	await process_frame
	await process_frame
	v.set_snapshot(named)
	await process_frame
	await process_frame
	var texts: Array = []
	_texts(v, texts)

	for o in owned:
		var nm: String = NAMES[known.find(o)]
		var k := _count(texts, nm)
		_check(k == 1, "B17: faction %d name '%s' is drawn %d times, want exactly 1 (labels seen: %s)" % [o, nm, k, str(texts)])
	for t in texts:
		var s := String(t)
		_check(not s.begins_with("Faction "), "B17: placeholder label '%s' drawn while every faction has a name" % s)

	# an owner that is not in the list reads "Unknown", once, and never a name or a Faction N
	var bad := named.duplicate(true)
	bad["regions"][0]["owner"] = UNKNOWN_OWNER
	v.set_snapshot(bad)
	await process_frame
	await process_frame
	var t2: Array = []
	_texts(v, t2)
	_check(_count(t2, "Unknown") >= 1, "B17: owner %d is not in the faction list but no label reads 'Unknown' (labels: %s)" % [UNKNOWN_OWNER, str(t2)])
	_check(_count(t2, "Faction %d" % UNKNOWN_OWNER) == 0, "B17: unknown owner drawn as 'Faction %d'" % UNKNOWN_OWNER)
	v.queue_free()
