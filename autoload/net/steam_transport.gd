extends "res://autoload/net/transport.gd"
# Steam Networking Messages transport (Steam wiring spec 2026-10-06, W1).
# The peer table comes from the MatchRecord peers, never from lobby member order.

const SEND_FLAG := 13  # k_nSteamNetworkingSend_UnreliableNoDelay
const CHANNEL := 0
const MAX_MESSAGES := 32

var dropped_unknown := 0
var dropped_malformed := 0

var _steam = null
var _steam_by_peer := {}
var _peer_by_steam := {}


func set_steam(steam) -> void:
	_steam = steam
	_steam.network_messages_session_request.connect(_on_session_request)


func set_peers(peers: Array) -> void:
	_steam_by_peer.clear()
	_peer_by_steam.clear()
	for p in peers:
		_steam_by_peer[int(p["peer_id"])] = int(p["steam_id"])
		_peer_by_steam[int(p["steam_id"])] = int(p["peer_id"])


func send(_from: int, to: int, data: PackedByteArray) -> void:
	if not _steam_by_peer.has(to):
		return
	_steam.sendMessageToUser(_steam_by_peer[to], data, SEND_FLAG, CHANNEL)


func poll(_id: int) -> Array:
	var out := []
	_steam.run_callbacks()
	for m in _steam.receiveMessagesOnChannel(CHANNEL, MAX_MESSAGES):
		var sid := int(m["identity"])
		if not _peer_by_steam.has(sid):
			dropped_unknown += 1
			continue
		var data: PackedByteArray = m["payload"]
		if not _well_formed(data):
			dropped_malformed += 1
			continue
		out.append({"from": _peer_by_steam[sid], "data": data})
	return out


func _well_formed(data: PackedByteArray) -> bool:
	var v = bytes_to_var(data)
	return v is Array and v.size() == 3 and v[0] is int and v[1] is Array and v[2] is Array


func _on_session_request(remote_steam_id) -> void:
	if _peer_by_steam.has(int(remote_steam_id)):
		_steam.acceptSessionWithUser(remote_steam_id)
