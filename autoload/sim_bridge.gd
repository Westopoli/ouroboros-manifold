## Autoload singleton that owns the Python sim child process and communicates
## over stdio pipes using a 4-byte big-endian length-prefix JSON protocol.
## See simulation/pipe_transport.py — that file is the Python side of this protocol.
##
## execute_with_pipe returns {"pid", "stdio", "stderr"} in Godot 4.6.
## "stdio" is a single bidirectional FileAccess, BUT writing to it permanently
## breaks reading (ERR_FILE_CANT_READ). So we use "stdio" ONLY for reading
## (sim→godot) and a temp file for writing commands (godot→sim).
##
## Command channel: Godot appends newline-delimited JSON to a temp file.
## The sim polls it for new lines. Simple, no thread-safety issues.
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
const ENTITLEMENT_SETTLED_REACH := true

## Development: python3 + this script. Production: swap to compiled executable.
const SIM_SCRIPT_PATH := "simulation/pipe_transport.py"
const SIM_UNITS_PER_SIDE := 10

var ownership_timeline: Array = []

var _pid: int = -1
var _startup_elapsed: float = 0.0
var _ready_received: bool = false
var _pending_error_screen: bool = false

## Read-only pipe for sim→godot data (stdout from the sim process).
var _stdio_pipe: FileAccess = null

## Command file for godot→sim commands. Godot appends JSON lines, sim polls.
var _cmd_file: FileAccess = null
var _cmd_file_path: String = ""

## Reader thread — blocks on _stdio_pipe reads, pushes parsed messages to _incoming.
var _reader_thread: Thread = null
var _reader_running: bool = false
var _incoming: Array = []
var _incoming_mutex: Mutex = Mutex.new()


func _ready() -> void:
	if not USE_LIVE_SIM:
		return
	_spawn_sim()


## Restart the sim subprocess with `--load <slot_id>` so it rehydrates from
## the autosave and replays the persisted time-jump message stream after the
## `ready_for_time_jump` cmd. Same message types as a live jump — no fan-out
## shim needed; existing time_jump_started / keyframe / chronicle_entry /
## time_jump_ended handlers cover it.
func restart_with_load(slot_id: String) -> void:
	_kill_sim()
	_startup_elapsed = 0.0
	_ready_received = false
	_pending_error_screen = false
	_spawn_sim(PackedStringArray(["--load", slot_id]))


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


func _spawn_sim(extra_args: PackedStringArray = PackedStringArray()) -> void:
	# Create a temp file for the command channel (godot→sim).
	_cmd_file_path = ProjectSettings.globalize_path("res://") + "logs/sim_cmd_%d.jsonl" % randi()
	_cmd_file = FileAccess.open(_cmd_file_path, FileAccess.WRITE)
	if _cmd_file == null:
		push_warning("SimBridge: failed to open cmd file at %s" % _cmd_file_path)

	# BLOCKER 1 Step C — tell sim where to write saves so they land where
	# `get_save_slots()` reads. ProjectSettings.globalize_path resolves user://
	# to the OS user-data dir; without this the sim resolves user:// via
	# os.getcwd() (project root in dev mode) and the load screen never sees
	# the file. See simulation/pipe_transport.py `--save-root` parsing.
	var save_root := ProjectSettings.globalize_path("user://saves")

	# B5-C release-mode branch. In a packaged build the Python sim is bundled
	# as a PyInstaller binary at <game_root>/sim/ouroboros_sim[.exe]. game_root
	# resolves via OS.get_executable_path().get_base_dir() — directory containing
	# the Godot game binary. pipe_transport.py reads --root to chdir before any
	# file I/O (see simulation/pipe_transport.py line 1283).
	# See also: autoload/theme_constants.gd — IS_RELEASE_BUILD source of truth.
	var exec_target: String
	var args: PackedStringArray
	if ThemeConstants.IS_RELEASE_BUILD:
		var game_root := OS.get_executable_path().get_base_dir()
		var bin_name := "ouroboros_sim.exe" if OS.has_feature("windows") else "ouroboros_sim"
		exec_target = game_root + "/sim/" + bin_name
		args = ["--cmd-file", _cmd_file_path, "--units", str(SIM_UNITS_PER_SIDE), "--real-missions", "--save-root", save_root, "--root", game_root]
	else:
		var script := ProjectSettings.globalize_path("res://") + SIM_SCRIPT_PATH
		exec_target = "python3"
		args = [script, "--cmd-file", _cmd_file_path, "--units", str(SIM_UNITS_PER_SIDE), "--real-missions", "--save-root", save_root]

	for a in extra_args:
		args.append(a)

	var result: Dictionary = OS.execute_with_pipe(exec_target, args)
	if (result.is_empty() or not result.has("pid")) and not ThemeConstants.IS_RELEASE_BUILD:
		result = OS.execute_with_pipe("python", args)
	if result.is_empty() or not result.has("pid"):
		sim_error.emit({"kind": "spawn_failed", "message": "OS.execute_with_pipe failed — exec target %s not found" % exec_target})
		return

	_pid = result["pid"]
	_stdio_pipe = result.get("stdio") as FileAccess

	if _stdio_pipe == null:
		sim_error.emit({"kind": "spawn_failed", "message": "stdio pipe handle is null"})
		_pid = -1
		return

	print("SimBridge: spawned sim  pid=%d  cmd_file=%s" % [_pid, _cmd_file_path])

	_reader_running = true
	_reader_thread = Thread.new()
	_reader_thread.start(_reader_loop)


func _reader_loop() -> void:
	print("SimBridge: reader thread started")
	var count := 0
	while _reader_running:
		var msg: Variant = _read_framed()
		if msg == null:
			print("SimBridge: reader got null after %d msgs" % count)
			break
		count += 1
		var mt: String = msg.get("type", "?") if msg is Dictionary else "?"
		if count <= 10 or mt == "snapshot":
			print("SimBridge: reader #%d type=%s" % [count, mt])
		_incoming_mutex.lock()
		_incoming.append(msg)
		_incoming_mutex.unlock()
	_reader_running = false
	print("SimBridge: reader exited")


func _read_framed() -> Variant:
	if _stdio_pipe == null:
		return null
	# Pipe reads may return 0 bytes when the OS buffer is empty but the pipe
	# is still open.  Accumulate into header until we have 4 bytes, retrying
	# on empty reads.  Only bail on genuine EOF / error.
	var header := PackedByteArray()
	var retries := 0
	while header.size() < 4:
		var chunk: PackedByteArray = _stdio_pipe.get_buffer(4 - header.size())
		if chunk.size() > 0:
			header.append_array(chunk)
			retries = 0
		else:
			if _stdio_pipe.eof_reached():
				print("SimBridge: _read_framed EOF after %d header bytes" % header.size())
				return null
			var err := _stdio_pipe.get_error()
			if err != OK:
				print("SimBridge: _read_framed header err=%d after %d bytes" % [err, header.size()])
				return null
			# Pipe empty but still open — wait for more data
			retries += 1
			if retries == 1:
				print("SimBridge: _read_framed waiting for header data...")
			OS.delay_msec(5)
			if not _reader_running:
				return null
	var length: int = (header[0] << 24) | (header[1] << 16) | (header[2] << 8) | header[3]
	if length <= 0 or length > 10 * 1024 * 1024:
		print("SimBridge: _read_framed bad length=%d" % length)
		return null
	# Same retry logic for the body
	var body := PackedByteArray()
	while body.size() < length:
		var chunk: PackedByteArray = _stdio_pipe.get_buffer(length - body.size())
		if chunk.size() > 0:
			body.append_array(chunk)
		else:
			if _stdio_pipe.eof_reached():
				print("SimBridge: _read_framed body EOF after %d/%d bytes" % [body.size(), length])
				return null
			var err := _stdio_pipe.get_error()
			if err != OK:
				print("SimBridge: _read_framed body err=%d after %d/%d bytes" % [err, body.size(), length])
				return null
			OS.delay_msec(5)
			if not _reader_running:
				return null
	var json := JSON.new()
	if json.parse(body.get_string_from_utf8()) != OK:
		return null
	return json.get_data()


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
		"time_jump_start":
			ownership_timeline = msg.get("ownership_timeline", [])
			print("SimBridge: TIME_JUMP_START entries=%d keyframes=%d factions=%s" % [
				int(msg.get("total_entries", 0)), int(msg.get("total_keyframes", 0)),
				str(msg.get("faction_names", {}).keys())])
			UIDataBus.time_jump_started.emit(
				msg.get("time_jump_id", ""),
				int(msg.get("span_years", 0)),
				int(msg.get("total_keyframes", 0)),
				int(msg.get("total_entries", 0)),
				msg.get("faction_names", {}))
		"time_jump_end":
			print("SimBridge: TIME_JUMP_END")
			UIDataBus.time_jump_ended.emit(msg.get("time_jump_id", ""))
		"keyframe":
			print("SimBridge: KEYFRAME entry_id=%s chronicle_entry_id=%s regions=%d" % [
				str(msg.get("entry_id", "")), str(msg.get("chronicle_entry_id", "")),
				msg.get("regions_snapshot", []).size()])
			UIDataBus.time_jump_keyframe.emit(msg)
		"chronicle_entry":
			print("SimBridge: CHRONICLE_ENTRY id=%s text=%s" % [
				str(msg.get("entry_id", "")), str(msg.get("base_form", "")).left(60)])
			UIDataBus.chronicle_entry.emit(msg)
		"debrief":
			print("SimBridge: DEBRIEF band=%s" % str(msg.get("outcome_band", "?")))
			SceneRouter.go_to("debrief", {"debrief": msg, "era_id": EraConfig.ACTIVE_ERA_ID})
		"next_mission":
			SceneRouter.go_to("mission_briefing")
		"heartbeat":
			pass
		_:
			pass


func _route_to_error_screen() -> void:
	_pending_error_screen = true


func send_command(cmd_dict: Dictionary) -> void:
	if _cmd_file == null:
		return
	_cmd_file.store_line(JSON.stringify(cmd_dict))
	_cmd_file.flush()


func _kill_sim() -> void:
	_reader_running = false
	if _pid != -1 and OS.is_process_running(_pid):
		OS.kill(_pid)
	if _reader_thread != null and _reader_thread.is_started():
		_reader_thread.wait_to_finish()
	_pid = -1
	_stdio_pipe = null
	if _cmd_file != null:
		_cmd_file.close()
		_cmd_file = null
	if _cmd_file_path != "":
		DirAccess.remove_absolute(_cmd_file_path)
		_cmd_file_path = ""


func restart() -> void:
	_kill_sim()
	_startup_elapsed = 0.0
	_ready_received = false
	_pending_error_screen = false
	_spawn_sim()


func _notification(what: int) -> void:
	if what == NOTIFICATION_WM_CLOSE_REQUEST or what == NOTIFICATION_PREDELETE:
		_kill_sim()
