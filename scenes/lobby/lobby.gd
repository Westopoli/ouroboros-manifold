extends Control
# Multiplayer lobby (W4, docs/northstar/plans/2026-10-06-steam-multiplayer-wiring-spec.md; VG lane F).
# Host makes a friends-only lobby (max 4) and publishes the MatchRecord as lobby data; guests read it,
# every peer opens its world, then ready/go runs through lobby chat (NetMatch). The peer table in the
# record is the only map from Steam id to peer id.

const SimSession := preload("res://autoload/sim_session.gd")

const MAX_MEMBERS := 4
const FRIENDS_ONLY := 1
const DOCTRINES := ["balanced", "boom", "fortify", "press"]
# Architect 2026-10-14 gap 5 (R-141-01, R-241-01): the team-size choices are 2 and 4 only, default 2 (liberty 2026-10-14,
# DRAFT-team-size-default); gap 4: the member cap stays MAX_MEMBERS, the choice is a stub until R-241-03 scaling.
const TEAM_SIZES := [2, 4]
const TEAM_SIZE_DEFAULT := 2
const CHAT_LEFT_STATES := [2, 4, 8, 16]  # left, disconnected, kicked, banned

var net_match: Node = null
var left := false

var _backend = null
var _local_steam := 0
var _version := ""
var _record := {}
var _hosting := false
var _doctrine_idx := 0
var _launched := false
var _member_list: ItemList
var _lobby_id_field: LineEdit
var _era_line: Label
var _status: Label
var _host_btn: Button
var _join_btn: Button
var _start_btn: Button
var _doctrine_btn: Button
var _team_btn: OptionButton
var _team_size := TEAM_SIZE_DEFAULT
var _team_raw := ""


class SteamBackend extends RefCounted:
	var steam
	var lobby_id := 0
	func _init(s) -> void:
		steam = s
	func create_lobby(type: int, max_members: int) -> void:
		steam.createLobby(type, max_members)
	func join(id: int) -> void:
		steam.joinLobby(id)
	func set_lobby_data(key: String, value: String) -> void:
		steam.setLobbyData(lobby_id, key, value)
	func get_lobby_data(key: String) -> String:
		return String(steam.getLobbyData(lobby_id, key))
	func members() -> Array:
		var out := []
		for i in int(steam.getNumLobbyMembers(lobby_id)):
			out.append(int(steam.getLobbyMemberByIndex(lobby_id, i)))
		return out
	func send_chat(msg: Dictionary) -> void:
		steam.sendLobbyChatMsg(lobby_id, var_to_str(msg))
	func leave() -> void:
		if lobby_id != 0:
			steam.leaveLobby(lobby_id)
		lobby_id = 0
	func friends() -> Array:
		var out := []
		for i in int(steam.getFriendCount(4)):
			out.append(int(steam.getFriendByIndex(i, 4)))
		return out
	func invite(friend_id: int) -> void:
		steam.inviteUserToLobby(lobby_id, friend_id)


func _ready() -> void:
	if net_match == null:
		net_match = get_node_or_null("/root/NetMatch")
	_build_ui()
	if _backend == null:
		_attach_steam()


func setup(params: Dictionary) -> void:
	_backend = params.get("backend", _backend)
	_local_steam = int(params.get("local_steam_id", _local_steam))
	_version = String(params.get("version", _version))
	_refresh()


func _version_string() -> String:
	var ver := String(ProjectSettings.get_setting("application/config/version", ""))
	if FileAccess.file_exists("res://build_hash.txt"):
		ver = FileAccess.get_file_as_string("res://build_hash.txt").strip_edges()
	return ver


func _attach_steam() -> void:
	var init := get_node_or_null("/root/SteamInit")
	if init == null or not init.steam_ready or not Engine.has_singleton("Steam"):
		if "--net-local" in OS.get_cmdline_user_args():
			_attach_local()
			return
		_status.text = "Steam is not running. Start Steam to play multiplayer."
		_host_btn.disabled = true
		_join_btn.disabled = true
		return
	var steam = Engine.get_singleton("Steam")
	var be := SteamBackend.new(steam)
	setup({"backend": be, "local_steam_id": int(steam.getSteamID()), "version": _version_string()})
	steam.lobby_created.connect(_on_lobby_created.bind(be))
	steam.lobby_joined.connect(_on_lobby_joined.bind(be))
	steam.lobby_join_requested.connect(func(id, _friend): _join(int(id)))
	steam.lobby_chat_update.connect(_on_chat_update)
	steam.lobby_message.connect(func(_id, user, message, _type): on_chat(int(user), str_to_var(String(message))))
	var args := OS.get_cmdline_user_args()
	var i := args.find("+connect_lobby")
	if i != -1 and i + 1 < args.size():
		_join(int(args[i + 1]))


# Steam-less test network (VG-F-SKEL-B, spec Rev 12b F-SKEL): the same handlers the Steam signals reach.
func _attach_local() -> void:
	var be = load("res://autoload/net/local_lobby_backend.gd").new()
	setup({"backend": be, "local_steam_id": be.local_id(), "version": _version_string()})
	be.lobby_created.connect(_on_lobby_created.bind(be))
	be.lobby_joined.connect(_on_lobby_joined.bind(be))
	be.lobby_chat_update.connect(_on_chat_update)
	be.lobby_message.connect(func(_id, user, message, _type): on_chat(int(user), str_to_var(String(message))))
	_status.text = "Local test network (no Steam)"


func _build_ui() -> void:
	var box := VBoxContainer.new()
	box.set_anchors_preset(Control.PRESET_FULL_RECT)
	box.offset_left = 120
	box.offset_top = 80
	box.offset_right = -120
	box.offset_bottom = -80
	add_child(box)
	var title := Label.new()
	title.text = "MULTIPLAYER"
	box.add_child(title)
	_era_line = Label.new()
	_era_line.name = "EraLine"
	_era_line.text = "Limited to the era set every player has."
	box.add_child(_era_line)
	var team_row := HBoxContainer.new()
	box.add_child(team_row)
	var team_label := Label.new()
	team_label.text = "Team size"
	team_row.add_child(team_label)
	_team_btn = OptionButton.new()
	_team_btn.name = "TeamSize"
	for n in TEAM_SIZES:
		_team_btn.add_item(str(n), n)
	_team_btn.item_selected.connect(_on_team_selected)
	team_row.add_child(_team_btn)
	_member_list = ItemList.new()
	_member_list.name = "MemberList"
	_member_list.custom_minimum_size.y = 160
	box.add_child(_member_list)
	_lobby_id_field = LineEdit.new()
	_lobby_id_field.name = "LobbyIdField"
	_lobby_id_field.placeholder_text = "Paste a lobby id"
	box.add_child(_lobby_id_field)
	var row := HBoxContainer.new()
	box.add_child(row)
	_host_btn = _button(row, "HostButton", "HOST")
	_host_btn.pressed.connect(host_create)
	_join_btn = _button(row, "JoinButton", "JOIN")
	_join_btn.pressed.connect(func(): _join(int(_lobby_id_field.text.strip_edges())))
	_doctrine_btn = _button(row, "DoctrineButton", "")
	_doctrine_btn.pressed.connect(func():
		_doctrine_idx = (_doctrine_idx + 1) % DOCTRINES.size()
		_refresh())
	_start_btn = _button(row, "StartButton", "START")
	_start_btn.pressed.connect(start_match)
	var back := _button(row, "BackButton", "BACK")
	back.pressed.connect(func():
		leave()
		SceneRouter.go_to("main_menu"))
	_status = Label.new()
	_status.name = "StatusLine"
	box.add_child(_status)
	_refresh()


func _button(parent: Node, node_name: String, text: String) -> Button:
	var b := Button.new()
	b.name = node_name
	b.text = text
	parent.add_child(b)
	return b


func _refresh() -> void:
	if _member_list == null:
		return
	_member_list.clear()
	if _backend != null:
		for m in _backend.members():
			_member_list.add_item(str(m) + ("  (you)" if int(m) == _local_steam else ""))
	_doctrine_btn.text = "DOCTRINE: " + String(DOCTRINES[_doctrine_idx]).to_upper()
	_start_btn.disabled = not _hosting
	_refresh_team_size()


# Gap 5: only the host changes the team size; a guest reads the host's choice from lobby data "team_size" and refuses
# any value that is not a choice. A lobby data frame emits no signal, so _process calls this when the key changed (spec Rev 13a).
func _refresh_team_size() -> void:
	if _team_btn == null:
		return
	if not _hosting and _backend != null and _backend.has_method("get_lobby_data"):
		_team_raw = _backend.get_lobby_data("team_size")
		if _team_raw.is_valid_int() and int(_team_raw) in TEAM_SIZES and str(int(_team_raw)) == _team_raw:
			_team_size = int(_team_raw)
	_team_btn.select(_team_btn.get_item_index(_team_size))
	_team_btn.disabled = not _hosting


func _on_team_selected(index: int) -> void:
	if not _hosting:
		_refresh_team_size()
		return
	_team_size = _team_btn.get_item_id(index)
	_publish_team_size()


func _publish_team_size() -> void:
	if _backend != null and _backend.lobby_id != 0:
		_backend.set_lobby_data("team_size", str(_team_size))


func host_create() -> void:
	_hosting = true
	_backend.create_lobby(FRIENDS_ONLY, MAX_MEMBERS)
	_refresh()


func _join(lobby_id: int) -> void:
	if lobby_id == 0 or _backend == null or not _backend.has_method("join"):
		return
	_backend.join(lobby_id)
	_status.text = "Joining lobby %d" % lobby_id


func _on_lobby_created(result: int, lobby_id: int, be) -> void:
	if result != 1:
		_status.text = "Could not create the lobby (code %d)." % result
		return
	be.lobby_id = lobby_id
	_status.text = "Lobby id %d (friends only). Invite friends or share the id." % lobby_id
	_lobby_id_field.text = str(lobby_id)
	_publish_team_size()
	_refresh()


func _on_lobby_joined(lobby_id: int, _perm, _locked, response: int, be) -> void:
	if response != 1:
		_status.text = "Could not join the lobby (code %d)." % response
		return
	be.lobby_id = lobby_id
	_refresh()


func _on_chat_update(_lobby, changed_id, _making_change_id, chat_state) -> void:
	_refresh()
	if int(chat_state) in CHAT_LEFT_STATES:
		on_member_left(int(changed_id))


func publish_record(record: Dictionary) -> void:
	_record = record
	_backend.set_lobby_data("record", var_to_str(record))


func read_record() -> Dictionary:
	var s: String = _backend.get_lobby_data("record")
	if s == "":
		return {}
	var v = str_to_var(s)
	return v if v is Dictionary else {}


func accept_record(record: Dictionary) -> Dictionary:
	if String(record.get("version", "")) != _version:
		return {"ok": false, "reason": "version mismatch: host %s, you %s" % [record.get("version", "?"), _version]}
	return {"ok": true, "reason": ""}


func _table() -> Array:
	return (_record if not _record.is_empty() else read_record()).get("peers", [])


func _peer_of(steam_id: int) -> int:
	for p in _table():
		if int(p["steam_id"]) == steam_id:
			return int(p["peer_id"])
	return -1


func on_member_left(steam_id: int) -> void:
	var peer := _peer_of(steam_id)
	if peer >= 0 and net_match != null:
		net_match.drop(peer)


func on_chat(from_steam_id: int, msg) -> void:
	if not msg is Dictionary:
		return
	var peer := _peer_of(from_steam_id)
	if msg.get("t", "") == "start":
		if peer >= 0 and not _launched:
			_guest_start()
		return
	if peer >= 0 and net_match != null:
		net_match.on_lobby_chat(peer, msg)


# Rule RULE-lobby-seed-arg (Architect 2026-10-12): `--seed <n>` fixes the match seed, randi() otherwise.
func _match_seed() -> int:
	var args := OS.get_cmdline_user_args()
	var i := args.find("--seed")
	if i >= 0 and i + 1 < args.size():
		return int(args[i + 1])
	return randi() & 0x7fffffff


func build_record() -> Dictionary:
	var era = get_node_or_null("/root/EraConfig")
	var ground: bool = era != null and era.has_method("kind") and str(era.call("kind")) == "ground"
	var peers := []
	var ids: Array = _backend.members()
	for i in ids.size():
		peers.append({"peer_id": i, "steam_id": int(ids[i]), "faction": 0})
	return {"seed": _match_seed(), "n_regions": 80, "features": [0, 1], "new_campaign": true,
		"archetype": 0, "era_kind": 1 if ground else 0,
		"movement_kinds": era.call("movement_kinds") if era != null and era.has_method("movement_kinds") else [],
		"faction": 0, "doctrine": DOCTRINES[_doctrine_idx], "peers": peers, "host_peer": 0,
		"input_delay": 3, "repeat": 5, "stall_ticks": 20, "drop_ticks": 1200, "version": _version}


func start_match() -> void:
	if not _hosting or _launched:
		return
	var rec := build_record()
	publish_record(rec)
	_backend.send_chat({"t": "start"})
	_launch(rec, 0)


func _guest_start() -> void:
	var rec := read_record()
	var ok := accept_record(rec)
	if not ok["ok"]:
		_status.text = String(ok["reason"])
		return
	_record = rec
	var me := _peer_of(_local_steam)
	if me < 0:
		_status.text = "You are not in the host's peer table."
		return
	_launch(rec, me)


func _launch(rec: Dictionary, local_peer: int) -> void:
	_launched = true
	var record := rec.duplicate(true)
	record["local_peer"] = local_peer
	var bridge = SimSession.bridge()
	var feats: Array = record["features"]
	if not bridge.ensure_session(int(record["seed"]), int(record["n_regions"]), feats, bool(record["new_campaign"])) \
			or not bridge.begin_mission_live(int(record["seed"]), int(record["n_regions"]), feats) \
			or not bridge.net_reset():
		_launched = false
		_status.text = "Could not open the match world: " + String(bridge.last_error())
		return
	var steam = Engine.get_singleton("Steam") if Engine.has_singleton("Steam") else null
	var transport
	if _backend.has_method("poll"):
		transport = load("res://autoload/net/udp_transport.gd").new()
	else:
		transport = load("res://autoload/net/steam_transport.gd").new()
		if steam != null:
			transport.set_steam(steam)
	transport.set_peers(record["peers"])
	transport.attach(local_peer)  # UdpTransport binds its socket here; the base and Steam transports ignore it
	var sim = load("res://autoload/net/pipe_sim.gd").new(bridge)
	net_match.start(record, transport, sim, _backend.send_chat, _backend)
	_status.text = "Waiting for every player to be ready."


func _process(_delta: float) -> void:
	if _backend != null and _backend.has_method("poll"):
		_backend.poll()
	if _backend != null and not _hosting and _backend.has_method("get_lobby_data") \
			and _backend.get_lobby_data("team_size") != _team_raw:
		_refresh()
	if _launched and net_match != null and net_match.active():
		_launched = false
		set_process(false)
		SceneRouter.go_to("tactical_c")


func leave() -> void:
	_backend.leave()
	left = true
	_hosting = false


func qa_state() -> Dictionary:
	return {"scene": "lobby", "members": _backend.members() if _backend != null else [], "max_members": MAX_MEMBERS,
		"friends_only": true, "tick": -1, "team_sizes": TEAM_SIZES.duplicate(), "team_size": _team_size}
