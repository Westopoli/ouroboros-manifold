extends RefCounted

# C transport v1 bridge (docs/architecture.md "C transport v1" and "persistent
# client session (v1.1)"). Instantiated directly
# (res://autoload/c_bridge.gd).new()), never as a project autoload; the game
# shares ONE instance through autoload/sim_session.gd. Parses a snapshot JSON
# file written by the sim and exposes it to callers without transmitting
# anything beyond the wire shape (no positions, no names -- C5 rule).
#
# The bridge keeps one pipe/ouroboros_pipe process open (open_session /
# ensure_session) and talks the same 4-byte-big-endian-length-prefix + UTF-8
# JSON framing sim_bridge.gd uses for reading (see autoload/sim_bridge.gd's
# header comment for the Godot 4.6 stdio caveat: reads block, so a reader
# Thread decodes frames into a queue that pump() drains on the main thread).
# The load_*_live methods and list_saves / load are requests over that open
# session: they send a command, pump until the wanted reply frames arrive,
# and keep them for the accessors below.

const PIPE_BIN_RES_PATH := "res://pipe/ouroboros_pipe"
const LIVE_READ_TIMEOUT_MSEC := 5000
const _FrameDecode := preload("res://autoload/bridge/frame_decode.gd")
const _DumpDecode := preload("res://autoload/bridge/dump_decode.gd")
const DEFAULT_N_REGIONS := 80
# The pipe ABI this client speaks: OM_ABI_VERSION in csrc/ouroboros_sim.h, carried by the pipe's hello frame
# (docs/architecture.md). tests/qa/test_pipe_abi_check.py pins this equal to the header.
const EXPECTED_ABI := 9
# Every strategic om_feature id (csrc/ouroboros_sim.h OM_FEAT_EVENTS ..
# OM_FEAT_LIFECYCLE); OM_FEAT_TACTICAL (8) stays off. With [6] alone nothing
# ever changes owner (docs/architecture.md "session commands (v1.1)").
const DEFAULT_FEATURES := [0, 1, 2, 3, 4, 5, 6, 7]

signal frame_received(frame)
signal snapshot_changed(tick)
# K-e4: the answer to the oldest pending send_place (ack accepted, command error refused).
signal place_result(accepted, x, y, building)

var _snapshot: Dictionary = {}
var _region_index: Dictionary = {}
var _session_pid: int = -1
var _session_stdio: FileAccess = null
var _reader: Thread = null
var _mutex := Mutex.new()
var _queue: Array = []
var _last_error: String = ""
var _mission: Dictionary = {}
var _debrief: Dictionary = {}
var _chronicle: Dictionary = {}
var _chronicle_snapshot: Dictionary = {}
var _tactical: Dictionary = {}
var _tactical_units: Dictionary = {}
var _tactical_map: Dictionary = {}
var _tactical_structures: Dictionary = {}
var _tactical_profiles: Array = []
var _session_args: Array = []
var _session_id: int = 0
var _player_faction: int = -1
var _mission_active := false
var _mission_begun := false
var _session_mission: Dictionary = {}
var _terrain: Dictionary = {}
var _space_field: Dictionary = {}
var _lots: Array = []
var _lots_fetched := false
var _strongpoints: Array = []
var _pending_places: Array = []
var _era_kind: int = 0


func load_snapshot_file(path: String) -> bool:
	var file := FileAccess.open(path, FileAccess.READ)
	if file == null:
		return false
	var text := file.get_as_text()
	file.close()

	var parsed = JSON.parse_string(text)
	if not (parsed is Dictionary):
		return false
	if not parsed.has("regions"):
		return false

	_snapshot = parsed
	return true


func regions() -> Array:
	return _snapshot.get("regions", [])


func owner_of(i: int) -> int:
	for r in regions():
		if int(r.get("i", -999)) == i:
			return int(r.get("owner", -1))
	return -1


func checksum() -> int:
	return int(_snapshot.get("checksum", -1))


func edges() -> Array:
	return _snapshot.get("edges", [])


func snapshot() -> Dictionary:
	return _snapshot


func last_error() -> String:
	return _last_error


# The --seed user arg the game was launched with (the galaxy reads the same
# arg), 1 when absent.
func live_seed() -> int:
	var args := OS.get_cmdline_user_args()
	var idx := args.find("--seed")
	if idx == -1 or idx + 1 >= args.size():
		return 1
	return int(args[idx + 1])


func mission_frame() -> Dictionary:
	return _mission


# The running mission's frame, empty when none is running.
func mission() -> Dictionary:
	return _session_mission


func debrief_frame() -> Dictionary:
	return _debrief


func chronicle_frame() -> Dictionary:
	return _chronicle


func chronicle_snapshot() -> Dictionary:
	return _chronicle_snapshot


func tactical_frame() -> Dictionary:
	return _tactical


# Save slots (docs/architecture.md "Save slots (T2g-2 rulings)"): the slot
# directory is user://saves passed absolute, or the OM_SAVE_DIR environment
# variable when set (QA runs point it at a per-run temp directory, C1-3); a slot id is the file name
# without ".omsave". The live mission/debrief/chronicle loads autosave to
# campaign_<seed> (R-111-01); the tactical load never does (R-111-04).
func saves_dir() -> String:
	var dir := OS.get_environment("OM_SAVE_DIR")
	if dir == "":
		dir = ProjectSettings.globalize_path("user://saves")
	DirAccess.make_dir_recursive_absolute(dir)
	return dir


func list_saves() -> Array:
	if not _ensure_any_session():
		return []
	var frames: Dictionary = _request([{"type": "cmd", "name": "list_saves", "dir": saves_dir()}], ["saves"])
	var rows := []
	for slot in frames.get("saves", {}).get("slots", []):
		rows.append({
			"slot": String(slot.get("path", "")).get_file().get_basename(),
			"tick": int(slot.get("tick", 0)),
			"chapter": int(slot.get("chapter", 0)),
			"version": int(slot.get("format_version", 0)),
		})
	return rows


# The post-load snapshot, or {} with last_error() set ("corrupt" covers a
# version mismatch too, csrc/pipe/om_pipe.c handle_load; R-111-03). The pipe
# can only load into a world with the save's region count, so the session is
# first opened for that world from the sidecar's seed and n_regions.
func load(slot_id: String) -> Dictionary:
	# A59: timelines are memory-only, so a load leaves no chronicle frame.
	_chronicle = {}
	_chronicle_snapshot = {}
	var path := saves_dir().path_join(slot_id + ".omsave")
	var sidecar = JSON.parse_string(FileAccess.get_file_as_string(path + ".json"))
	if not (sidecar is Dictionary) or not sidecar.has("seed") or not sidecar.has("n_regions"):
		_last_error = "save sidecar missing or unreadable"
		return {}
	# R-056-04: the world this opens is only scaffolding for the `load`
	# command below to overwrite (tick, regions, chapter all come from the
	# save); it is not a new campaign, so the R-056-04 opening jump must not
	# run for it (new_campaign:false, csrc/pipe/om_pipe.c handle_set_seed).
	if not ensure_session(int(sidecar["seed"]), int(sidecar["n_regions"]), DEFAULT_FEATURES, false):
		return {}
	var frames: Dictionary = _request([{"type": "cmd", "name": "load", "path": path}], ["snapshot"])
	return frames.get("snapshot", {})


# R-111-01: written after every mission start, debrief and chronicle jump as
# campaign_<seed>; the tactical load never calls it (R-111-04).
func _autosave() -> bool:
	var path := saves_dir().path_join("campaign_%d.omsave" % int(_session_args[0]))
	return not _request([{"type": "cmd", "name": "save", "path": path}], ["ack:save"]).is_empty()


# The pipe binary: OM_PIPE override, else next to the game executable, else
# (editor run) res://pipe.
func _pipe_path() -> String:
	var override := OS.get_environment("OM_PIPE")
	if override != "":
		return override
	var suffix := ".exe" if OS.get_name() == "Windows" else ""
	var beside := OS.get_executable_path().get_base_dir().path_join("ouroboros_pipe" + suffix)
	if not OS.has_feature("editor") and FileAccess.file_exists(beside):
		return beside
	return ProjectSettings.globalize_path(PIPE_BIN_RES_PATH) + suffix


# Persistent session (docs/architecture.md "persistent client session
# (v1.1)"): one pipe process for the whole run. A reader Thread decodes
# frames into a mutex-guarded queue (reads block, so they cannot run on the
# main thread), pump() applies them in order on the main thread (the owning
# scene calls it from its _process; this RefCounted has no _process), and
# writes happen on the main thread only. A delta is merged into the current
# snapshot in place: region rows by index, faction rows by id, the tick, and
# the checksum on the cadence ticks that carry one (kept from the last
# cadence tick otherwise). Deltas carry no edges, so the edge list is the one
# the last snapshot frame had; request a snapshot to refresh it. Replies are
# not matched against a FIFO of sent commands: an error frame names its
# command and sets last_error(), every other frame is announced through
# frame_received for whoever awaits that type. The owner must call
# close_session() (a RefCounted cannot do it from its own destructor).
func open_session(seed: int, n_regions: int, features: Array, new_campaign: bool = true) -> bool:
	close_session()
	_last_error = ""
	var exe := _pipe_path()
	if not FileAccess.file_exists(exe):
		_last_error = "pipe binary missing: run scripts/setup_editor.sh"
		return false
	var result: Dictionary = OS.execute_with_pipe(exe, PackedStringArray())
	if result.is_empty() or not result.has("pid"):
		_last_error = "pipe spawn failed"
		return false
	_session_pid = result["pid"]
	_session_stdio = result.get("stdio") as FileAccess
	if _session_stdio == null:
		close_session()
		_last_error = "pipe has no stdio"
		return false
	_snapshot = {}
	_region_index = {}
	_session_args = [seed, n_regions, features]
	_session_id += 1
	_player_faction = -1
	_mission_active = false
	_mission_begun = false
	_session_mission = {}
	_mutex.lock()
	_queue = []
	_mutex.unlock()
	_reader = Thread.new()
	_reader.start(_reader_loop)
	if n_regions > 0:
		send_command({"type": "cmd", "name": "set_seed", "seed": seed, "n_regions": n_regions, "features": features, "new_campaign": new_campaign})
		send_command({"type": "cmd", "name": "snapshot"})
	return true


func send_command(cmd: Dictionary) -> void:
	if _session_stdio != null:
		_session_stdio.store_buffer(_FrameDecode.frame_cmd(cmd))


func step(n: int) -> void:
	send_command({"type": "cmd", "name": "step", "n": n})


func pump() -> int:
	_mutex.lock()
	var frames: Array = _queue
	_queue = []
	_mutex.unlock()
	for frame in frames:
		var changed := false
		match String(frame.get("type", "")):
			"hello":
				var abi := int(frame.get("abi", -1))
				if abi != EXPECTED_ABI:
					_last_error = "pipe binary is out of date (abi %d, expected %d): run scripts/setup_editor.sh" % [abi, EXPECTED_ABI]
			"snapshot":
				_snapshot = frame
				_region_index = {}
				var rows: Array = _snapshot.get("regions", [])
				for idx in range(rows.size()):
					_region_index[int(rows[idx].get("i", -1))] = idx
				if _snapshot.has("player_faction"):
					_player_faction = int(_snapshot["player_faction"])
				changed = true
			"delta":
				_apply_delta(frame)
				changed = true
			"mission":
				_mission_active = true
				_mission_begun = false
				_lots = []
				_lots_fetched = false
				_session_mission = frame
			"tactical":
				_mission_begun = true
			"debrief":
				_debrief = frame
				_mission_active = false
				_mission_begun = false
				_session_mission = {}
			"ack":
				if String(frame.get("name", "")) == "command":
					_resolve_place(true)
			"error":
				_last_error = String(frame.get("reason", ""))
				if String(frame.get("name", "")) == "command":
					_resolve_place(false)
		frame_received.emit(frame)
		if changed:
			snapshot_changed.emit(int(_snapshot.get("tick", 0)))
	return frames.size()


func close_session() -> void:
	_session_args = []
	_pending_places = []
	if _session_pid > 0 and OS.is_process_running(_session_pid):
		OS.kill(_session_pid)
	if _reader != null:
		_reader.wait_to_finish()
		_reader = null
	_session_pid = -1
	_session_stdio = null


func _reader_loop() -> void:
	while true:
		var msg: Variant = _FrameDecode.read_live_frame(_session_stdio)
		if msg == null:
			return
		_mutex.lock()
		_queue.append(msg)
		_mutex.unlock()


func _read_live_frame(stdio: FileAccess) -> Variant:
	return _FrameDecode.read_live_frame(stdio)


func _apply_delta(delta: Dictionary) -> void:
	if _snapshot.is_empty():
		return
	var rows: Array = _snapshot.get("regions", [])
	for row in delta.get("regions", []):
		var idx: int = _region_index.get(int(row.get("i", -1)), -1)
		if idx >= 0:
			(rows[idx] as Dictionary).merge(row, true)
	var factions: Array = _snapshot.get("factions", [])
	for row in delta.get("factions", []):
		for f in factions:
			if int(f.get("id", -1)) == int(row.get("id", -2)):
				(f as Dictionary).merge(row, true)
	_snapshot["tick"] = delta.get("tick", _snapshot.get("tick", 0))
	var checksum: int = int(delta.get("checksum", 0))
	if checksum != 0:
		_snapshot["checksum"] = checksum


func session_id() -> int:
	return _session_id


func player_faction() -> int:
	return _player_faction


func mission_active() -> bool:
	return _mission_active


# False while a started mission is still in recon (E-12 S-092: clock not
# started, no unit moves); true once mission_begin has been answered.
func mission_begun() -> bool:
	return _mission_begun


# Opens the session for this world if none is open, reuses it when the same
# arguments are already open, reopens it when they differ; blocks until the
# first snapshot. False (session closed again, last_error() set) when the
# pipe cannot spawn or set_seed fails.
func ensure_session(seed: int, n_regions: int, features: Array, new_campaign: bool = true) -> bool:
	if _session_pid > 0 and _session_args == [seed, n_regions, features]:
		return true
	if not open_session(seed, n_regions, features, new_campaign):
		return false
	var deadline_msec := Time.get_ticks_msec() + LIVE_READ_TIMEOUT_MSEC
	while Time.get_ticks_msec() < deadline_msec and _last_error == "" and (_snapshot.get("regions", []) as Array).is_empty():
		pump()
		OS.delay_msec(5)
	# A stale pipe's hello sets _last_error even when its snapshot arrived in the same batch.
	if _last_error != "" or (_snapshot.get("regions", []) as Array).is_empty():
		if _last_error == "":
			_last_error = "timed out waiting for the first snapshot"
		close_session()
		return false
	return true


# A session for commands that need no world (list_saves): opened without one
# (n_regions 0 skips set_seed) so the main menu does not generate a galaxy
# just to list saves.
func _ensure_any_session() -> bool:
	return _session_pid > 0 or open_session(0, 0, [])


func has_world() -> bool:
	return not (_snapshot.get("regions", []) as Array).is_empty()


# The world the scenes read: the one already open (a new game, or a loaded
# save) if there is one, else a fresh world for these arguments. ensure_session
# is the stricter form that reopens when the arguments differ.
func ensure_world(seed: int, n_regions: int, features: Array) -> bool:
	return has_world() or ensure_session(seed, n_regions, features)


# Sends the commands, pumps until the first frame of every type in want has
# arrived ({type: frame}; an ack is keyed "ack:<command name>"); {} on an
# error frame, a timeout or a session that is not open, with last_error() set.
func _request(cmds: Array, want: Array) -> Dictionary:
	_last_error = ""
	if _session_pid <= 0:
		_last_error = "no open session"
		return {}
	var found := {}
	var on_frame := func(frame):
		var type_name: String = String(frame.get("type", ""))
		var key: String = type_name if type_name != "ack" else "ack:%s" % frame.get("name", "")
		if want.has(key) and not found.has(key):
			found[key] = frame
	frame_received.connect(on_frame)
	for cmd in cmds:
		send_command(cmd)
	var deadline_msec := Time.get_ticks_msec() + LIVE_READ_TIMEOUT_MSEC
	while found.size() < want.size() and _last_error == "" and Time.get_ticks_msec() < deadline_msec:
		if pump() == 0:
			OS.delay_msec(5)
	frame_received.disconnect(on_frame)
	if found.size() != want.size():
		if _last_error == "":
			_last_error = "timed out waiting for %s" % ", ".join(want)
		return {}
	return found


# Sends a unit command (move/attack_move/attack_target) over the open session.
# Wire format: {"type":"cmd","name":"command","verb":"<kind>","units":[...],...}
# (docs/architecture.md "session commands (v1.1)").
# Validates the kind and unit_ids; returns false for unknown kinds or empty
# unit_ids without sending (avoids poisoning the pipe with error frames that
# would stall the next _request).
func send_unit_command(cmd: Dictionary) -> bool:
	var kind := str(cmd.get("kind", ""))
	var unit_ids: Array = cmd.get("unit_ids", [])
	if not kind in ["move", "attack_move", "attack_target", "set_layer", "activate_ability"]:
		return false
	if kind == "set_layer" and unit_ids.is_empty():
		return false
	var pipe_cmd := {
		"type": "cmd",
		"name": "command",
		"verb": kind,
		"units": unit_ids,
	}
	if kind in ["move", "attack_move"]:
		pipe_cmd["x"] = float(cmd.get("x", 0.0))
		pipe_cmd["y"] = float(cmd.get("y", 0.0))
	elif kind == "attack_target":
		pipe_cmd["target"] = int(cmd.get("target", -1))
	elif kind == "set_layer":
		pipe_cmd["layer"] = int(cmd.get("layer", 0))
	elif kind == "activate_ability":
		pipe_cmd["x"] = float(cmd.get("x", 0.0))
		pipe_cmd["y"] = float(cmd.get("y", 0.0))
	send_command(pipe_cmd)
	return true


# Sends the K-e place command (docs/architecture.md, K-e4): `building` is the position of the building
# in the era manifest's buildings list (liberty 2026-10-10). The answer arrives as place_result.
func send_place(x: float, y: float, building: int) -> bool:
	_pending_places.append([x, y, building])
	send_command({"type": "cmd", "name": "command", "verb": "place", "units": [], "x": x, "y": y, "building": building})
	return true


func _resolve_place(accepted: bool) -> void:
	if _pending_places.is_empty():
		return
	var p: Array = _pending_places.pop_front()
	place_result.emit(accepted, p[0], p[1], p[2])


# Folds a full or delta tactical frame (A7) into the id -> unit dictionary and
# returns the reconstructed full view tactical_view.gd reads. The map is kept
# from the last full frame; units are listed in ascending id.
func _reconstruct_tactical(frame: Dictionary) -> Dictionary:
	if bool(frame.get("full", true)):
		_tactical_units = {}
		_tactical_map = frame.get("map", {})
		_tactical_structures = {}
		_tactical_profiles = frame.get("profiles", [])
		_strongpoints = frame.get("strongpoints", [])
		_strongpoints.sort_custom(func(a, b): return int(a["id"]) < int(b["id"]))
		for st in frame.get("structures", []):
			_tactical_structures[int(st["id"])] = st
		if frame.has("lots"):
			_lots = []
			for r in frame["lots"]:
				_lots.append(_lot_row(r))
			_tactical["lots"] = _lots
	else:
		for id in frame.get("units_removed", []):
			_tactical_units.erase(int(id))
		for id in frame.get("structures_removed", []):
			_tactical_structures.erase(int(id))
		for ch in frame.get("structures_changed", []):
			var sid := int(ch["id"])
			var row: Dictionary = _tactical_structures.get(sid, {}).duplicate()
			row.merge(ch, true)
			_tactical_structures[sid] = row
		_fold_lots(frame.get("lots_changed", []))
	for u in frame.get("units", frame.get("units_changed", [])):
		_tactical_units[int(u["id"])] = u
	var ids := _tactical_units.keys()
	ids.sort()
	var units: Array = []
	for id in ids:
		units.append(_tactical_units[id])
	var view := frame.duplicate()
	var sids := _tactical_structures.keys()
	sids.sort()
	var structures: Array = []
	for id in sids:
		structures.append(_tactical_structures[id])
	for k in ["units_changed", "units_removed", "structures_changed", "structures_removed", "lots_changed"]:
		view.erase(k)
	view["structures"] = structures
	view["profiles"] = _tactical_profiles
	view["lots"] = _lots
	view["strongpoints"] = _strongpoints
	view["economy"] = frame.get("economy", {"doctrine": 3, "resources": {}})
	view["full"] = true
	view["units"] = units
	view["map"] = _tactical_map
	return view


# Advances the already-begun mission by n tactical ticks and stores the
# reconstructed frame of the last tick. tactical_step n=k answers one frame
# (the last step's), so this waits for one. Returns false (leaves _tactical
# empty) if the session is not open, the pipe sends an error, or it times out.
func tactical_step_n(n: int) -> bool:
	if n <= 0:
		return true
	if _session_pid <= 0:
		_last_error = "no open session"
		return false
	_tactical = {}
	_last_error = ""
	# A dict so the lambda can mutate state visible outside it (primitives are captured by value).
	var state := {"last": {}}
	var on_frame := func(frame):
		if String(frame.get("type", "")) == "tactical":
			state["last"] = frame
	frame_received.connect(on_frame)
	send_command({"type": "cmd", "name": "tactical_step", "n": n})
	var deadline_msec := Time.get_ticks_msec() + LIVE_READ_TIMEOUT_MSEC
	while (state["last"] as Dictionary).is_empty() and _last_error == "" and Time.get_ticks_msec() < deadline_msec:
		if pump() == 0:
			OS.delay_msec(5)
	frame_received.disconnect(on_frame)
	if (state["last"] as Dictionary).is_empty():
		if _last_error == "":
			_last_error = "timed out waiting for the tactical frame"
		return false
	_tactical = _reconstruct_tactical(state["last"])
	return true


func net_reset() -> bool:
	return not _request([{"type": "cmd", "name": "net_reset"}], ["net_ack"]).is_empty()


# The net_ack code of the submitted command (0 accepted), -1 on a pipe failure.
func net_submit(cmd: Dictionary) -> int:
	var c := cmd.duplicate()
	c["type"] = "cmd"
	c["name"] = "net_submit"
	var r := _request([c], ["net_ack"])
	if r.is_empty():
		return -1
	return int(r["net_ack"].get("code", -1))


# {"net_ack": ack, "tactical": frame} (frame only when asked); {} on failure.
func net_step(n: int = 1, frame: bool = true) -> Dictionary:
	var cmd := {"type": "cmd", "name": "net_step", "n": n}
	var want := ["net_ack"]
	if frame:
		cmd["frame"] = true
		want.append("tactical")
	return _request([cmd], want)


func net_checksum() -> Dictionary:
	var r := _request([{"type": "cmd", "name": "net_checksum"}], ["net_ack"])
	return r.get("net_ack", {})


func _ensure_mission(fog_filter: bool = false) -> bool:
	if _mission_active:
		return true
	_terrain = {}
	_space_field = {}
	var era: Node = (Engine.get_main_loop() as SceneTree).root.get_node_or_null("EraConfig")
	var cmd := {"type": "cmd", "name": "mission_start", "faction": 0, "era_kind": 0, "movement_kinds": []}
	if era != null and era.has_method("kind") and era.has_method("movement_kinds"):
		cmd["era_kind"] = 1 if str(era.call("kind")) == "ground" else 0
		cmd["movement_kinds"] = era.call("movement_kinds")
	if fog_filter:
		cmd["fog_filter"] = true
	_era_kind = int(cmd["era_kind"])
	return not _request([cmd], ["mission"]).is_empty()


# The ground terrain of the begun mission; {} in a space era (spec 3c).
func terrain() -> Dictionary:
	return _terrain


func _fetch_terrain() -> bool:
	var t: Dictionary = _request([{"type": "cmd", "name": "terrain_dump"}], ["terrain"])
	if t.is_empty():
		return false
	_terrain = _DumpDecode.terrain_from_frame(t["terrain"])
	return true


# The space field of the begun mission (K-d, docs/architecture.md space_field_dump): {cells_w, cells_h, layers,
# masks: 5 PackedByteArray (8 cells per byte, LSB first, 1 = blocked), polys: [{layer, kind, points}]}; {} in a ground era.
func space_field() -> Dictionary:
	return _space_field


func _fetch_space_field() -> bool:
	var t: Dictionary = _request([{"type": "cmd", "name": "space_field_dump"}], ["space_field"])
	if t.is_empty():
		return false
	var f: Dictionary = t["space_field"]
	var masks: Array = []
	for m in f.get("masks", []):
		masks.append(String(m).hex_decode())
	var polys: Array = []
	for p in f.get("polys", []):
		var pts := PackedVector2Array()
		var xy: Array = p[2]
		for i in range(0, xy.size() - 1, 2):
			pts.append(Vector2(float(xy[i]), float(xy[i + 1])))
		polys.append({"layer": int(p[0]), "kind": int(p[1]), "points": pts})
	_space_field = {"cells_w": int(f.get("cells_w", 0)), "cells_h": int(f.get("cells_h", 0)), "layers": int(f.get("layers", 0)), "masks": masks, "polys": polys}
	return true


# The lots of the begun mission (K-e, docs/architecture.md lots_dump), ascending id, kept current by
# delta lots_changed rows and replaced by a full frame's `lots` (K-e6): [{id, x, y, stage, building, owner}]; [] before the dump.
func lots() -> Array:
	return _lots


# The strongpoints of the last full tactical frame (K-e4), ascending id: [{id, x, y, owner, state}].
func strongpoints() -> Array:
	return _strongpoints


func _lot_row(r: Array) -> Dictionary:
	return {"id": int(r[0]), "x": float(r[1]), "y": float(r[2]), "stage": int(r[3]), "building": int(r[4]), "owner": int(r[5])}


func _fold_lots(rows: Array) -> void:
	if rows.is_empty():
		return
	var by_id := {}
	for l in _lots:
		by_id[int(l["id"])] = l
	for r in rows:
		by_id[int(r[0])] = _lot_row(r)
	var ids := by_id.keys()
	ids.sort()
	_lots = []
	for id in ids:
		_lots.append(by_id[id])
	_tactical["lots"] = _lots


func _fetch_lots() -> bool:
	var t: Dictionary = _request([{"type": "cmd", "name": "lots_dump"}], ["lots"])
	if t.is_empty():
		return false
	_lots_fetched = true
	_lots = []
	_fold_lots_dump(t["lots"].get("lots", []))
	return true


func _fold_lots_dump(rows: Array) -> void:
	for r in rows:
		_lots.append(_lot_row(r))
	_lots.sort_custom(func(a, b): return int(a["id"]) < int(b["id"]))
	_tactical["lots"] = _lots


# The mission frame of the shared world: a mission is started if none is
# running (one already running is reused), then autosaved (R-111-01).
func load_mission_live(seed: int, n_regions: int, features: Array, fog_filter: bool = false) -> bool:
	_mission = {}
	if not ensure_world(seed, n_regions, features) or not _ensure_mission(fog_filter) or not _autosave():
		return false
	_mission = _session_mission
	return true


# ... mission_end answers the debrief frame (a mission is started first if
# none is running), then autosaves.
func load_debrief_live(seed: int, n_regions: int, features: Array) -> bool:
	_debrief = {}
	if not ensure_world(seed, n_regions, features) or not _ensure_mission():
		return false
	var frames: Dictionary = _request([{"type": "cmd", "name": "mission_end"}], ["debrief", "snapshot"])
	if frames.is_empty() or not _autosave():
		return false
	_debrief = frames["debrief"]
	return true


# ... a 50-tick jump answers the chronicle frame, then a snapshot of the
# world after the jump, and autosaves. Refused while a mission is running.
func load_chronicle_live(seed: int, n_regions: int, features: Array) -> bool:
	_chronicle = {}
	_chronicle_snapshot = {}
	if not ensure_world(seed, n_regions, features):
		return false
	var frames: Dictionary = _request([{"type": "cmd", "name": "jump", "ticks": 50}], ["chronicle", "snapshot"])
	if frames.is_empty() or not _autosave():
		return false
	_chronicle = frames["chronicle"]
	_chronicle_snapshot = frames["snapshot"]
	return true


# ... mission_begin, the player's Begin, ends recon and answers the first
# tactical frame; idempotent once begun. Never autosaved: R-111-04.
func begin_mission_live(seed: int, n_regions: int, features: Array) -> bool:
	if not ensure_world(seed, n_regions, features) or not _ensure_mission():
		return false
	if _mission_begun:
		return true
	var frames: Dictionary = _request([{"type": "cmd", "name": "mission_begin"}], ["tactical"])
	if frames.is_empty():
		return false
	_tactical = _reconstruct_tactical(frames["tactical"])
	var ok := _fetch_terrain() if _era_kind == 1 else _fetch_space_field()
	if not _lots_fetched:
		_fetch_lots()
	return ok


# ... one tactical_step of the begun mission (begun here if the player has
# not pressed Begin yet) answers the tactical frame.
func load_tactical_live(seed: int, n_regions: int, features: Array) -> bool:
	_tactical = {}
	if not begin_mission_live(seed, n_regions, features):
		return false
	var frames: Dictionary = _request([{"type": "cmd", "name": "tactical_step", "n": 1}], ["tactical"])
	if frames.is_empty():
		return false
	_tactical = _reconstruct_tactical(frames["tactical"])
	return true
