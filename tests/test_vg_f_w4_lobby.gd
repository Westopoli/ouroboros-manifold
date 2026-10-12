extends SceneTree

# Lane F piece W4 (lobby + MULTIPLAYER menu row), docs/northstar/plans/2026-10-06-steam-multiplayer-wiring-spec.md
# W4 row, "What the Fable audit changed" (leave = leaveLobby + session end; lobby_chat_update feeds session.drop;
# paste-lobby-id field; peer table only from the record), interface 4 (MatchRecord).
# Stories S-141 (what a match is), S-144-adjacent lobby flow, S-142. Rules R-141-01 (friends-only, teams of 2 or 4,
# the spec fixes max 4), R-140-04 (a dropped peer's units stand idle; others alerted), R-143-03 (lobby says the match
# is limited to the common era set), R-144-01 (Multiplayer from the main menu).
# Fake lobby backend: no Steam, no pipe.
#
# The spec leaves these shapes open; this test FIXES them (flagged to the Architect):
#   Scene res://scenes/lobby/lobby.tscn, root script lobby.gd, with named nodes MemberList (ItemList, one row per
#   member), LobbyIdField (LineEdit, paste a lobby id), HostButton, JoinButton, StartButton, a Label named EraLine.
#   lobby.setup(backend, local_steam_id: int, version: String) wires the lobby; `net_match` property (default
#   /root/NetMatch) is the node that gets drop(peer) and on_lobby_chat(from_peer, msg).
#   Backend (Steam wrapper): create_lobby(type: int, max_members: int), set_lobby_data(key, value: String),
#   get_lobby_data(key) -> String, members() -> Array of steam ids, send_chat(msg: Dictionary), leave().
#   lobby.host_create() -> create_lobby(1 = friends only, 4); lobby.publish_record(record) writes
#   set_lobby_data("record", var_to_str(record)); lobby.read_record() -> Dictionary ({} if none);
#   lobby.accept_record(record) -> {"ok": bool, "reason": String} (version mismatch refuses, reason names "version");
#   lobby.on_member_left(steam_id) -> net_match.drop(peer_id) via the RECORD's peer table (never member order);
#   lobby.on_chat(from_steam_id, msg) -> net_match.on_lobby_chat(peer_id, msg);
#   lobby.leave() -> backend.leave() then and sets `left` true.
#   lobby.qa_state() -> {"scene": "lobby", "members": [steam ids], "max_members": 4, "friends_only": true, "tick": -1}.
#
# VG-F-SKEL-B (spec lane F part 1 + Rev 12b F-SKEL; Q-F-1 closed by Westley, 2026-10-11, "allowed, so long as the test
# does everything it can to emulate the reality of two players joining"): with the user argument --net-local the lobby
# attaches the Steam-less local backend, so HostButton and JoinButton are enabled and StatusLine reads "Local test
# network (no Steam)". User args cannot be set in-process, so the case re-runs this file as a child (--child, the
# pattern of tests/test_vg_b_b3b.gd) with and without the flag; the child with no flag is the control (no flag and no
# Steam keeps Host and Join disabled, lobby.gd:85-88).

const LOBBY_SCENE := "res://scenes/lobby/lobby.tscn"
const MENU_SCENE := "res://scenes/main_menu/main_menu.tscn"
const ROUTER := "res://autoload/scene_router.gd"

var _pass_count := 0
var _fail_count := 0
var _fail_msgs: Array[String] = []
var _completed := false
var _cur := ""
var _child := false

const LOCAL_STATUS := "Local test network (no Steam)"


class FakeBackend extends RefCounted:
	var created: Array = []
	var data := {}
	var member_ids: Array = [11]
	var chats: Array = []
	var left := false
	func create_lobby(type: int, max_members: int) -> void:
		created.append([type, max_members])
	func set_lobby_data(key: String, value: String) -> void:
		data[key] = value
	func get_lobby_data(key: String) -> String:
		return String(data.get(key, ""))
	func members() -> Array:
		return member_ids
	func send_chat(msg: Dictionary) -> void:
		chats.append(msg)
	func leave() -> void:
		left = true


class FakeNet extends Node:
	var dropped: Array = []
	var chat: Array = []
	func drop(peer: int) -> void:
		dropped.append(peer)
	func on_lobby_chat(from_peer: int, msg: Dictionary) -> void:
		chat.append([from_peer, msg])


func _initialize() -> void:
	_child = "--child" in OS.get_cmdline_user_args()
	if _child:
		await _child_probe()
		return
	await _run_tests()
	_assert(_completed, "the checks did not run to the end (a script error aborted them)")
	print("\n=== VG-F W4 Lobby Test Results ===")
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
		_fail_msgs.append("[%s] %s" % [_cur, msg])


func _record(version := "abc123") -> Dictionary:
	return {"seed": 5, "n_regions": 80, "features": [0, 1], "new_campaign": true, "faction": 0, "input_delay": 3,
		"repeat": 5, "stall_ticks": 20, "drop_ticks": 1200, "version": version, "host_peer": 0, "local_peer": 0,
		"peers": [{"peer_id": 0, "steam_id": 11, "faction": 0}, {"peer_id": 1, "steam_id": 22, "faction": 0},
			{"peer_id": 2, "steam_id": 33, "faction": 0}]}


func _texts(node: Node, out: Array[String]) -> void:
	if node is Label:
		out.append((node as Label).text.to_lower())
	elif node is Button:
		out.append((node as Button).text.to_lower())
	for c in node.get_children():
		_texts(c, out)


func _run_tests() -> void:
	await _t_control_menu_texts_scan()
	await _t_menu_row_and_route()
	if _have_lobby():
		await _t_lobby()
		_t_net_local_children()
	_completed = true


func _have_lobby() -> bool:
	if ResourceLoader.exists(LOBBY_SCENE):
		return true
	_cur = "lobby_scene"
	_assert(false, "%s does not exist yet (W4 not built)" % LOBBY_SCENE)
	return false


func _t_control_menu_texts_scan() -> void:
	_cur = "control_menu_scan"
	var scene: Node = (load(MENU_SCENE) as PackedScene).instantiate()
	get_root().add_child(scene)
	await process_frame
	var texts: Array[String] = []
	_texts(scene, texts)
	_assert(texts.any(func(t): return t.find("quit") != -1), "CONTROL: the text scan sees the menu (a QUIT item); texts %s" % str(texts))
	scene.queue_free()
	await process_frame


func _t_menu_row_and_route() -> void:
	_cur = "menu_row"
	var scene: Node = (load(MENU_SCENE) as PackedScene).instantiate()
	get_root().add_child(scene)
	await process_frame
	await process_frame
	var texts: Array[String] = []
	_texts(scene, texts)
	_assert(texts.any(func(t): return t.find("multiplayer") != -1), "R-144-01: the main menu has no MULTIPLAYER item; texts %s" % str(texts))
	scene.queue_free()
	await process_frame
	var scenes: Dictionary = load(ROUTER).SCENES
	_assert(scenes.get("lobby", "") == LOBBY_SCENE, "scene_router.gd SCENES has no \"lobby\" route to %s" % LOBBY_SCENE)


func _t_lobby() -> void:
	_cur = "lobby"
	var lobby: Node = (load(LOBBY_SCENE) as PackedScene).instantiate()
	var net := FakeNet.new()
	net.name = "FakeNetMatch"
	get_root().add_child(net)
	get_root().add_child(lobby)
	var be := FakeBackend.new()
	lobby.net_match = net
	lobby.setup(be, 11, "abc123")
	await process_frame
	for n in ["MemberList", "LobbyIdField", "HostButton", "JoinButton", "StartButton", "EraLine"]:
		_assert(lobby.find_child(n, true, false) != null, "lobby scene lacks a node named %s" % n)
	_assert(lobby.find_child("LobbyIdField", true, false) is LineEdit, "LobbyIdField is a LineEdit (the paste-lobby-id field for the Spacewar test)")

	lobby.host_create()
	_assert(be.created == [[1, 4]], "host_create makes a friends-only lobby of at most 4 (R-141-01), got %s" % str(be.created))

	# A host record reaches the guest through lobby data.
	var rec := _record()
	lobby.publish_record(rec)
	var back: Dictionary = lobby.read_record()
	_assert(back.get("seed", -1) == 5 and back.get("peers", []).size() == 3 and back.get("version", "") == "abc123", "the record read from lobby data equals the one published, got %s" % str(back))
	be.data.clear()
	_assert(lobby.read_record().is_empty(), "CONTROL: with no lobby data read_record() is empty, not a stale record")

	# A mismatched version refuses before ready.
	var ok: Dictionary = lobby.accept_record(_record("abc123"))
	_assert(ok.get("ok", false) == true, "a record with the same version is accepted")
	var bad: Dictionary = lobby.accept_record(_record("deadbee"))
	_assert(bad.get("ok", true) == false and String(bad.get("reason", "")).to_lower().find("version") != -1, "a record with another version refuses with a reason naming version, got %s" % str(bad))

	# Members leaving: drop via the record's table, never member order.
	lobby.publish_record(rec)
	lobby.on_member_left(33)
	_assert(net.dropped == [2], "steam id 33 is peer 2 in the record's table: drop(2), got %s" % str(net.dropped))
	lobby.on_member_left(999)
	_assert(net.dropped == [2], "a steam id not in the peer table drops nobody, got %s" % str(net.dropped))

	# Lobby chat reaches NetMatch with the sender's peer id (the ready/go barrier).
	lobby.on_chat(22, {"t": "ready"})
	_assert(net.chat == [[1, {"t": "ready"}]], "chat from steam id 22 reaches NetMatch as peer 1, got %s" % str(net.chat))

	var st: Dictionary = lobby.qa_state()
	_assert(st.get("scene", "") == "lobby" and st.get("max_members", 0) == 4 and st.get("friends_only", false) == true, "qa_state names the lobby, max 4, friends only, got %s" % str(st))

	lobby.leave()
	_assert(be.left, "leave() leaves the Steam lobby (End Mission means leave in a match)")
	lobby.queue_free()
	net.queue_free()
	await process_frame


# Child half of the --net-local case: instantiates the lobby with no setup() call, so it takes the real _attach path.
func _child_probe() -> void:
	var lobby: Node = (load(LOBBY_SCENE) as PackedScene).instantiate()
	get_root().add_child(lobby)
	await process_frame
	await process_frame
	var host := lobby.find_child("HostButton", true, false) as Button
	var join := lobby.find_child("JoinButton", true, false) as Button
	var status := lobby.find_child("StatusLine", true, false) as Label
	print("CHILD-STATE net_local=%s host_disabled=%s join_disabled=%s status=%s" % [
		"--net-local" in OS.get_cmdline_user_args(), host.disabled, join.disabled, status.text])
	lobby.queue_free()
	await process_frame
	quit(0)


func _run_child(flag: bool) -> String:
	var args := ["--headless", "--path", ProjectSettings.globalize_path("res://"), "--script", "res://tests/test_vg_f_w4_lobby.gd", "--", "--child"]
	if flag:
		args.append("--net-local")
	var out: Array = []
	OS.execute(OS.get_executable_path(), args, out, true)
	for line in "\n".join(out).split("\n"):
		if line.begins_with("CHILD-STATE"):
			return line
	return ""


func _t_net_local_children() -> void:
	_cur = "net_local_flag"
	var off := _run_child(false)
	print(off)
	_assert(off != "", "CONTROL: the child run (no flag) printed no CHILD-STATE line, so the child harness is broken")
	_assert(off.contains("net_local=false") and off.contains("host_disabled=true") and off.contains("join_disabled=true"),
		"CONTROL: with no --net-local and no Steam the lobby keeps HostButton and JoinButton disabled, got: %s" % off)
	var on := _run_child(true)
	print(on)
	_assert(on != "", "the child run (--net-local) printed no CHILD-STATE line")
	_assert(on.contains("net_local=true") and on.contains("host_disabled=false") and on.contains("join_disabled=false"),
		"VG-F-SKEL-B: with --net-local HostButton and JoinButton are enabled (lobby.gd:85-88 disables them without Steam), got: %s" % on)
	_assert(on.contains("status=" + LOCAL_STATUS), "VG-F-SKEL-B: with --net-local StatusLine reads \"%s\", got: %s" % [LOCAL_STATUS, on])
