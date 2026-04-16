## Autoload singleton that owns the Python sim child process and communicates
## over stdio pipes using a 4-byte big-endian length-prefix JSON protocol.
## See simulation/pipe_transport.py — that file is the Python side of this protocol.
##
## execute_with_pipe returns {"pid", "stdio", "stderr"} in Godot 4.6.
## "stdio" is a single bidirectional FileAccess: reader thread reads (stdout),
## writer thread writes (stdin). Safe because reads/writes go to separate kernel
## buffers on the underlying pty/socket.
##
## Signals
##   progress_updated(step, pct)  — emitted during sim startup
##   sim_ready(metadata)          — sim initialization complete
##   state_updated(state)         — snapshot or delta from the running sim
##   sim_error(info)              — startup timeout or unexpected process death
##
## Kill switch: set USE_LIVE_SIM = false to disable entirely. No process is
## spawned and no pipes are opened. The autoload is still registered but inert.

extends Node

signal progress_updated(step: String, pct: float)
signal sim_ready(metadata: Dictionary)
signal state_updated(state: Dictionary)
signal sim_error(info: Dictionary)

const USE_LIVE_SIM := true
const SIM_STARTUP_TIMEOUT_SEC := 30.0

## Development: python3 + this script. Production: swap to compiled executable.
const SIM_SCRIPT_PATH := "simulation/pipe_transport.py"

var _pid: int = -1
var _startup_elapsed: float = 0.0
var _ready_received: bool = false
var _pending_error_screen: bool = false

## Single bidirectional pipe handle returned as "stdio" by execute_with_pipe.
## Reader thread reads (sim stdout); writer thread writes (sim stdin).
var _stdio_pipe: FileAccess = null

## Reader thread — blocks on pipe reads, pushes parsed messages to _incoming.
var _reader_thread: Thread = null
var _reader_running: bool = false
var _incoming: Array = []
var _incoming_mutex: Mutex = Mutex.new()

## Writer thread — drains _outgoing to the stdio pipe, woken by semaphore.
var _writer_thread: Thread = null
var _writer_running: bool = false
var _outgoing: Array = []
var _outgoing_mutex: Mutex = Mutex.new()
var _outgoing_semaphore: Semaphore = Semaphore.new()


func _ready() -> void:
	if not USE_LIVE_SIM:
		return
	_spawn_sim()


func _process(delta: float) -> void:
	if _pending_error_screen and not SceneRouter._transitioning:
		_pending_error_screen = false
		SceneRouter.go_to("error_screen")
		return

	if _pid == -1:
		return

	# Startup timeout guard
	if not _ready_received:
		_startup_elapsed += delta
		if _startup_elapsed >= SIM_STARTUP_TIMEOUT_SEC:
			sim_error.emit({"kind": "timeout", "message": "Sim startup timed out after %s sec" % SIM_STARTUP_TIMEOUT_SEC})
			_pid = -1
			_route_to_error_screen.call_deferred()
			return

	# Detect unexpected process death
	if not OS.is_process_running(_pid):
		sim_error.emit({
			"kind": "crash",
			"crash_log_path": "logs/crash_report.txt",
			"message": "Sim process exited unexpectedly",
		})
		_pid = -1
		_route_to_error_screen.call_deferred()
		return

	# Drain messages from the reader thread
	_incoming_mutex.lock()
	var batch: Array = _incoming.duplicate()
	_incoming.clear()
	_incoming_mutex.unlock()

	for msg in batch:
		_dispatch(msg)


func _spawn_sim() -> void:
	var script := ProjectSettings.globalize_path("res://") + SIM_SCRIPT_PATH

	var result: Dictionary = OS.execute_with_pipe("python3", [script])
	if result.is_empty() or not result.has("pid"):
		result = OS.execute_with_pipe("python", [script])
	if result.is_empty() or not result.has("pid"):
		sim_error.emit({"kind": "spawn_failed", "message": "OS.execute_with_pipe failed — python3/python not found"})
		return

	_pid = result["pid"]
	_stdio_pipe = result.get("stdio") as FileAccess

	if _stdio_pipe == null:
		sim_error.emit({"kind": "spawn_failed", "message": "stdio pipe handle is null"})
		_pid = -1
		return

	print("SimBridge: spawned sim  pid=%d" % _pid)

	_reader_running = true
	_reader_thread = Thread.new()
	_reader_thread.start(_reader_loop)

	_writer_running = true
	_writer_thread = Thread.new()
	_writer_thread.start(_writer_loop)


func _reader_loop() -> void:
	while _reader_running:
		var msg: Variant = _read_framed()
		if msg == null:
			break
		_incoming_mutex.lock()
		_incoming.append(msg)
		_incoming_mutex.unlock()
	_reader_running = false


func _writer_loop() -> void:
	while _writer_running:
		_outgoing_semaphore.wait()
		if not _writer_running:
			break
		_outgoing_mutex.lock()
		var batch: Array = _outgoing.duplicate()
		_outgoing.clear()
		_outgoing_mutex.unlock()
		for msg in batch:
			_write_framed(msg)


func _read_framed() -> Variant:
	if _stdio_pipe == null:
		return null
	var header: PackedByteArray = _stdio_pipe.get_buffer(4)
	if header.size() < 4 or _stdio_pipe.get_error() != OK:
		return null
	var length: int = (header[0] << 24) | (header[1] << 16) | (header[2] << 8) | header[3]
	if length <= 0 or length > 10 * 1024 * 1024:
		return null
	var body: PackedByteArray = _stdio_pipe.get_buffer(length)
	if body.size() < length or _stdio_pipe.get_error() != OK:
		return null
	var json := JSON.new()
	if json.parse(body.get_string_from_utf8()) != OK:
		return null
	return json.get_data()


func _write_framed(msg: Dictionary) -> void:
	if _stdio_pipe == null:
		print("SimBridge: _write_framed called but _stdio_pipe is null — command dropped")
		return
	var body: PackedByteArray = JSON.stringify(msg).to_utf8_buffer()
	var length: int = body.size()
	var header := PackedByteArray([
		(length >> 24) & 0xFF,
		(length >> 16) & 0xFF,
		(length >> 8) & 0xFF,
		length & 0xFF,
	])
	_stdio_pipe.store_buffer(header)
	_stdio_pipe.store_buffer(body)
	_stdio_pipe.flush()


func _dispatch(msg: Dictionary) -> void:
	match msg.get("type", ""):
		"progress":
			var step: String = msg.get("step", "")
			var pct: float = float(msg.get("pct", 0.0))
			print("SimBridge: progress  step=%-30s  pct=%.0f%%" % [step, pct * 100])
			progress_updated.emit(step, pct)
		"ready":
			_ready_received = true
			print("SimBridge: sim ready  version=%s" % msg.get("version", "?"))
			sim_ready.emit(msg)
		"snapshot", "delta", "sim_state":
			state_updated.emit(msg)
		_:
			pass


func _route_to_error_screen() -> void:
	_pending_error_screen = true


func send_command(cmd_dict: Dictionary) -> void:
	_outgoing_mutex.lock()
	_outgoing.append(cmd_dict)
	_outgoing_mutex.unlock()
	_outgoing_semaphore.post()


func _kill_sim() -> void:
	_reader_running = false
	_writer_running = false
	_outgoing_semaphore.post()  # unblock writer so it can exit
	if _reader_thread != null and _reader_thread.is_started():
		_reader_thread.wait_to_finish()
	if _writer_thread != null and _writer_thread.is_started():
		_writer_thread.wait_to_finish()
	if _pid != -1:
		if OS.is_process_running(_pid):
			OS.kill(_pid)
		_pid = -1
	_stdio_pipe = null


func restart() -> void:
	_kill_sim()
	_startup_elapsed = 0.0
	_ready_received = false
	_pending_error_screen = false
	_spawn_sim()


func _notification(what: int) -> void:
	if what == NOTIFICATION_WM_CLOSE_REQUEST or what == NOTIFICATION_PREDELETE:
		_kill_sim()
