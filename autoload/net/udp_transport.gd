extends "res://autoload/net/transport.gd"
# Local UDP transport for the Steam-less lobby skeleton (VG-F-SKEL-A): one 127.0.0.1 port per peer id.
# Plain script, loaded with load(path).new(), no class_name (spec rev 12b F-SKEL (4)).

const UDP_BASE_PORT := 47100  # DRAFT-udp-base-port

var _base := UDP_BASE_PORT
var _socks := {}  # id -> PacketPeerUDP


func _init() -> void:
	var args := OS.get_cmdline_user_args()
	var i := args.find("--net-local-udp-base")
	var env := OS.get_environment("OM_TEST_PORT_BASE")
	if i != -1 and i + 1 < args.size() and String(args[i + 1]).is_valid_int():
		_base = int(args[i + 1])
	elif env.is_valid_int():
		_base = int(env) + 100


func attach(id: int) -> void:
	if _socks.has(id):
		return
	var s := PacketPeerUDP.new()
	var err := s.bind(_base + id, "127.0.0.1")
	if err != OK:
		push_error("UdpTransport: cannot bind 127.0.0.1:%d (error %d)" % [_base + id, err])
		return
	_socks[id] = s


func send(from: int, to: int, data: PackedByteArray) -> void:
	if not _socks.has(from):
		return
	var s: PacketPeerUDP = _socks[from]
	s.set_dest_address("127.0.0.1", _base + to)
	s.put_packet(data)


func poll(id: int) -> Array:
	var out: Array = []
	if not _socks.has(id):
		return out
	var s: PacketPeerUDP = _socks[id]
	while s.get_available_packet_count() > 0:
		var pkt := s.get_packet()
		if s.get_packet_error() != OK:
			continue
		out.append({"from": s.get_packet_port() - _base, "data": pkt})
	return out


# See also: scenes/lobby/lobby.gd _launch, which calls set_peers for every transport; ports need no peer table.
func set_peers(_peers) -> void:
	pass
