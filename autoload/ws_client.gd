## Raw TCP client — reads newline-delimited JSON from socket_server.py.
## Transport is plain TCP (not WebSocket protocol). Stage 10 replaces this
## entire file with stdio pipes when Godot spawns the sim as a child process.
extends Node

signal connected()
signal disconnected()
signal message_received(payload: Dictionary)

# Use integer literals for status constants — avoids class-constant default-
# value restrictions in GDScript 2.0. Values match StreamPeerTCP.Status enum:
# NONE=0, CONNECTING=1, CONNECTED=2, ERROR=3.
var _peer: StreamPeerTCP
var _buffer: PackedByteArray
var _last_status: int = 0  # STATUS_NONE


func connect_to_server(host: String, port: int) -> void:
	_peer = StreamPeerTCP.new()
	var err := _peer.connect_to_host(host, port)
	if err != OK:
		push_error("ws_client: connect_to_host failed (err=%d)" % err)


func disconnect_from_server() -> void:
	if _peer != null:
		_peer.disconnect_from_host()
	_peer = null
	_buffer = PackedByteArray()
	_last_status = 0


func send(payload: Dictionary) -> void:
	if _peer == null:
		return
	if _peer.get_status() != StreamPeerTCP.STATUS_CONNECTED:
		return
	var line := JSON.stringify(payload) + "\n"
	_peer.put_data(line.to_utf8_buffer())


func _process(_delta: float) -> void:
	if _peer == null:
		return

	_peer.poll()
	var status: int = _peer.get_status()

	if status != _last_status:
		_last_status = status
		if status == StreamPeerTCP.STATUS_CONNECTED:
			connected.emit()
		elif status == StreamPeerTCP.STATUS_NONE or status == StreamPeerTCP.STATUS_ERROR:
			disconnected.emit()

	if status != StreamPeerTCP.STATUS_CONNECTED:
		return

	var available: int = _peer.get_available_bytes()
	if available <= 0:
		return

	var result: Array = _peer.get_partial_data(available)
	if result[0] != OK:
		push_warning("ws_client: read error %d" % result[0])
		return

	_buffer.append_array(result[1])
	_drain_buffer()


func _drain_buffer() -> void:
	while true:
		var nl: int = _buffer.find(10)  # '\n' = 10
		if nl == -1:
			break
		var line: String = _buffer.slice(0, nl).get_string_from_utf8()
		_buffer = _buffer.slice(nl + 1)
		if line.is_empty():
			continue
		var json := JSON.new()
		if json.parse(line) == OK:
			message_received.emit(json.get_data())
		else:
			push_warning("ws_client: JSON parse failed: %s" % line.left(120))
