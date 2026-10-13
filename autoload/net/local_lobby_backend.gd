extends RefCounted
# Steam-less lobby backend for the local test network (VG-F-SKEL-A): the SteamBackend seam of
# scenes/lobby/lobby.gd over JSON frames on 127.0.0.1 UDP. Plain script, load(path).new(), no class_name.
# The host binds the lobby port, guests bind an ephemeral port and say hello to it; the host relays everything.

signal lobby_created(result: int, lobby_id: int)
signal lobby_joined(lobby_id: int, perm: int, locked: bool, response: int)
signal lobby_chat_update(lobby: int, changed_id: int, making_change_id: int, chat_state: int)
signal lobby_message(lobby: int, user: int, message: String, type: int)

const LOBBY_PORT := 47000  # DRAFT-lobby-port

var lobby_id := 0
var _port := LOBBY_PORT
var _id := -1
var _sock: PacketPeerUDP = null
var _host := false
var _max := 4
var _members: Array = []
var _ports := {}  # host only: member id -> its socket port
var _data := {}
var _inbox: Array = []  # host only: its own chat, delivered by poll()


func _init() -> void:
	var args := OS.get_cmdline_user_args()
	var i := args.find("--net-local-lobby-port")
	var env := OS.get_environment("OM_TEST_PORT_BASE")
	if i != -1 and i + 1 < args.size() and String(args[i + 1]).is_valid_int():
		_port = int(args[i + 1])
	elif env.is_valid_int():
		_port = int(env)


func local_id() -> int:
	if _id >= 0:
		return _id
	var args := OS.get_cmdline_user_args()
	var i := args.find("--net-local-id")
	if i != -1 and i + 1 < args.size() and String(args[i + 1]).is_valid_int():
		return int(args[i + 1])
	return OS.get_process_id()


func set_local_id(n: int) -> void:
	_id = n


func create_lobby(_type: int, max_members: int) -> void:
	_sock = PacketPeerUDP.new()
	if _sock.bind(_port, "127.0.0.1") != OK:
		push_error("LocalLobbyBackend: cannot bind lobby port %d" % _port)
		_sock = null
		lobby_created.emit(2, 0)
		return
	_host = true
	_max = max_members
	lobby_id = _port
	_members = [local_id()]
	lobby_created.emit(1, lobby_id)


func join(id: int) -> void:
	_sock = PacketPeerUDP.new()
	if _sock.bind(0, "127.0.0.1") != OK:
		push_error("LocalLobbyBackend: cannot bind a guest socket")
		_sock = null
		lobby_joined.emit(id, 0, false, 2)
		return
	_host = false
	lobby_id = id
	_send(id, {"t": "hello", "id": local_id()})


func set_lobby_data(key: String, value: String) -> void:
	if not _host:
		return
	_data[key] = value
	_fan({"t": "data", "k": key, "v": value})


func get_lobby_data(key: String) -> String:
	return String(_data.get(key, ""))


func members() -> Array:
	return _members.duplicate()


func send_chat(msg: Dictionary) -> void:
	var text := var_to_str(msg)
	if _host:
		_inbox.append([local_id(), text])
		_fan({"t": "msg", "from": local_id(), "text": text})
	elif _sock != null:
		_send(lobby_id, {"t": "chat", "id": local_id(), "text": text})


func leave() -> void:
	if _sock != null:
		if _host:
			_fan({"t": "bye", "id": local_id()})
		else:
			_send(lobby_id, {"t": "bye", "id": local_id()})
		_sock.close()
	_sock = null
	_host = false
	lobby_id = 0
	_members = []
	_ports.clear()
	_data.clear()
	_inbox.clear()


func poll() -> void:
	if _sock == null:
		return
	for m in _inbox:
		lobby_message.emit(lobby_id, int(m[0]), String(m[1]), 0)
	_inbox.clear()
	while _sock != null and _sock.get_available_packet_count() > 0:
		var pkt := _sock.get_packet()
		var port := _sock.get_packet_port()
		var f = JSON.parse_string(pkt.get_string_from_utf8())
		if f is Dictionary:
			_on_frame(f, port)


func _on_frame(f: Dictionary, port: int) -> void:
	var t := String(f.get("t", ""))
	if _host:
		var who := int(f.get("id", -1))
		if t == "hello" and (_members.has(who) or _members.size() < _max):
			var fresh := not _members.has(who)
			_ports[who] = port
			if fresh:
				_members.append(who)
			_send(port, {"t": "welcome", "members": _members, "data": _data})
			if fresh:
				_fan({"t": "members", "members": _members, "id": who, "state": 1}, who)
				lobby_chat_update.emit(lobby_id, who, who, 1)
		elif t == "bye" and _members.has(who):
			_members.erase(who)
			_ports.erase(who)
			_fan({"t": "members", "members": _members, "id": who, "state": 2})
			lobby_chat_update.emit(lobby_id, who, who, 2)
		elif t == "chat" and _members.has(who):
			var text := String(f.get("text", ""))
			_fan({"t": "msg", "from": who, "text": text})
			lobby_message.emit(lobby_id, who, text, 0)
		return
	if t == "welcome":
		_data = f.get("data", {})
		_members = _ints(f.get("members", []))
		lobby_joined.emit(lobby_id, 0, false, 1)
		lobby_chat_update.emit(lobby_id, local_id(), local_id(), 1)
	elif t == "members":
		_members = _ints(f.get("members", []))
		lobby_chat_update.emit(lobby_id, int(f.get("id", 0)), int(f.get("id", 0)), int(f.get("state", 1)))
	elif t == "data":
		_data[String(f.get("k", ""))] = String(f.get("v", ""))
	elif t == "msg":
		lobby_message.emit(lobby_id, int(f.get("from", 0)), String(f.get("text", "")), 0)
	elif t == "bye":
		var gone: int = _members[0] if _members.size() > 0 else 0
		_members.erase(gone)
		lobby_chat_update.emit(lobby_id, gone, gone, 2)


func _ints(a: Array) -> Array:
	var out: Array = []
	for v in a:
		out.append(int(v))
	return out


func _send(port: int, frame: Dictionary) -> void:
	_sock.set_dest_address("127.0.0.1", port)
	_sock.put_packet(JSON.stringify(frame).to_utf8_buffer())


# Host to every guest (optionally not `skip`); the new guest already got its welcome.
func _fan(frame: Dictionary, skip := -1) -> void:
	if _sock == null:
		return
	for m in _ports:
		if m != skip:
			_send(int(_ports[m]), frame)
