extends SceneTree

# Terrain stage 3, piece 3c (docs/northstar/plans/2026-10-06-terrain-stage3-spec.md, rev 3):
# autoload/c_bridge.gd asks for ONE terrain_dump after mission_begin in a ground era, decodes it
# to terrain() = {cells_w, cells_h, bands: PackedByteArray, walkable: PackedByteArray, slopes: Array}
# (empty in a space era), never re-requests it on deltas, and mission_start carries era_kind and the
# flat movement_kinds [type_id, kind, type_id, kind, ...] read from EraConfig. Also pinned here, as
# the spec's "What the audit changed" and "What the pre-flight changed" fix them for 3c/3d/3e:
#   - EraConfig.ACTIVE_ERA_ID is a var; EraConfig.TYPE_IDS = the OM_UT_* name table; kind();
#     movement_kinds() flat; the era comes from `--era <id>` (space form), else the saved setting
#     ([game] era_id through UIDataBus), else settled_reach
#   - a mission_start error "terrain generate failed" surfaces through last_error(), no dump follows
#   - the walkers mockup's ramp constants (origin/push/proto-walkers) in terrain_layer.gd (piece 3d)
# The pipe is faked: a subclass of c_bridge.gd records every command it is asked to send and queues
# canned replies, standing in for pipe/ouroboros_pipe (pipe-side behaviour is 3b's transport tests).
# Positive controls are marked "(control)": they pass on the contract base and prove the harness.
# Each RED check's message quotes the spec reason.

const DIM := 240
const GROUND_ERA := "greek_placeholder"
const SPACE_ERA := "settled_reach"
const TYPE_NAMES := {"raider": 0, "interceptor": 1, "vanguard": 2, "warden": 3, "bombard": 4, "bastion": 5}

const FAKE_SRC := """
extends "res://autoload/c_bridge.gd"

var log: Array = []
var dim: int = 240
var fail_generate := false
var _ground := false


func _fake_bands() -> PackedByteArray:
	var b := PackedByteArray()
	b.resize(dim * dim)
	for i in range(dim * dim):
		b[i] = 1 + int((i % dim) * 5 / dim)
	return b


func _fake_walk() -> PackedByteArray:
	var w := PackedByteArray()
	w.resize(dim * dim)
	for i in range(dim * dim):
		w[i] = 0 if int(i / dim) % 10 == 9 else 1
	return w


func _reply(f: Dictionary) -> void:
	_mutex.lock()
	_queue.append(f)
	_mutex.unlock()


func prime() -> void:
	_session_pid = 2147483000
	_session_args = [1, 10, []]
	_snapshot = {"regions": [{"i": 0}], "tick": 0}


func send_command(cmd: Dictionary) -> void:
	log.append(cmd)
	match String(cmd.get("name", "")):
		"mission_start":
			if int(cmd.get("era_kind", 0)) == 1:
				if fail_generate:
					_reply({"type": "error", "name": "mission_start", "reason": "terrain generate failed"})
					return
				_ground = true
			else:
				_ground = false
			_reply({"type": "mission", "units": []})
		"save":
			_reply({"type": "ack", "name": "save", "tick": 0})
		"mission_begin":
			_reply({"type": "tactical", "full": true, "tick": 0, "units": [], "map": {}})
		"tactical_step":
			_reply({"type": "tactical", "full": false, "tick": 1, "units_changed": [], "units_removed": []})
		"mission_end":
			_reply({"type": "debrief", "band": 1})
			_reply({"type": "snapshot", "regions": [{"i": 0}], "tick": 1})
		"lots_dump":
			_reply({"type": "lots", "lots": []})
		"space_field_dump":
			# Stand-in: the real verb answers 240x240x5 masks or error "no space field"
			# (docs/architecture.md:365); nothing here reads space_field(). TD-VG-E-15.
			_reply({"type": "space_field", "cells_w": 1, "cells_h": 1, "layers": 0, "masks": [], "polys": []})
		"terrain_dump":
			if not _ground:
				_reply({"type": "error", "name": "terrain_dump", "reason": "no terrain"})
				return
			var slopes := []
			for k in range(3):
				slopes.append({"x0": k, "y0": 0, "x1": k + 1, "y1": 0, "mx": 100.0 * k + 50.0, "my": 50.0, "length": 100.0, "lower_band": 1, "upper_band": 2})
			_reply({"type": "terrain", "cells_w": dim, "cells_h": dim, "bands": _fake_bands().hex_encode(), "walkable": _fake_walk().hex_encode(), "slopes": slopes})


func count(name: String) -> int:
	var n := 0
	for c in log:
		if String(c.get("name", "")) == name:
			n += 1
	return n


func first_index(name: String) -> int:
	for i in range(log.size()):
		if String(log[i].get("name", "")) == name:
			return i
	return -1


func first_cmd(name: String) -> Dictionary:
	var i := first_index(name)
	return log[i] if i >= 0 else {}
"""

const PROBE_SRC := """
extends SceneTree
func _initialize() -> void:
	await process_frame
	var n = root.get_node_or_null("EraConfig")
	print("ERA=" + (str(n.get("ACTIVE_ERA_ID")) if n != null else "none"))
	quit(0)
"""

var _pass_count := 0
var _fail_count := 0
var _fail_msgs: Array[String] = []
var _completed := false


func _initialize() -> void:
	await _run_tests()
	_assert(_completed, "the checks did not run to the end (a script error aborted them)")
	print("\n=== C Bridge Terrain Test Results ===")
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
		_fail_msgs.append(msg)


func _era() -> Node:
	return root.get_node_or_null("EraConfig")


func _set_era(id: String) -> void:
	var e := _era()
	if e != null:
		e.set("ACTIVE_ERA_ID", id)


func _era_is_var() -> bool:
	var e := _era()
	return e != null and not (e.get_script() as Script).get_script_constant_map().has("ACTIVE_ERA_ID")


func _new_fake():
	var s := GDScript.new()
	s.source_code = FAKE_SRC
	var err := s.reload()
	if err != OK:
		return null
	var f = s.new()
	f.prime()
	return f


func _flat_pairs_ok(a: Variant) -> bool:
	if not (a is Array) or (a as Array).size() % 2 != 0 or (a as Array).is_empty():
		return false
	for i in range((a as Array).size()):
		if typeof(a[i]) != TYPE_INT:
			return false
	for i in range(0, (a as Array).size(), 2):
		if int(a[i]) < 0 or int(a[i]) > 5 or not (int(a[i + 1]) == 0 or int(a[i + 1]) == 1):
			return false
	return true


func _run_tests() -> void:
	var tmp := OS.get_user_data_dir().path_join("t3c_saves_%d" % Time.get_ticks_usec())
	OS.set_environment("OM_SAVE_DIR", tmp)
	var era := _era()
	_assert(era != null, "EraConfig autoload missing (control)")
	var cfg_path := ProjectSettings.globalize_path("user://settings.cfg")
	var had_cfg := FileAccess.file_exists(cfg_path)
	var cfg_bytes := FileAccess.get_file_as_bytes(cfg_path) if had_cfg else PackedByteArray()
	var bag := {"fake_ok": false}

	_check_era_config(era)
	await _check_bridge(bag)
	_check_ui_data_bus(cfg_path)
	_check_era_arg(cfg_path)
	_check_ramp_constants()

	# restore the user's settings file
	if had_cfg:
		var f := FileAccess.open(cfg_path, FileAccess.WRITE)
		if f != null:
			f.store_buffer(cfg_bytes)
			f.close()
	elif FileAccess.file_exists(cfg_path):
		DirAccess.remove_absolute(cfg_path)
	_set_era(SPACE_ERA)
	_completed = true


# ---- 3e/3f reader contract, as the spec fixes it ---------------------------------------------

func _check_era_config(era: Node) -> void:
	if era == null:
		return
	var consts: Dictionary = (era.get_script() as Script).get_script_constant_map()
	_assert(not consts.has("ACTIVE_ERA_ID"),
		"EraConfig.ACTIVE_ERA_ID is still a const; spec 3e: 'makes it a var set once at startup from settings (readers unchanged)'")
	_assert(consts.has("TYPE_IDS") and consts["TYPE_IDS"] == TYPE_NAMES,
		"EraConfig.TYPE_IDS missing or wrong; pre-flight: 'const TYPE_IDS = {raider 0, interceptor 1, vanguard 2, warden 3, bombard 4, bastion 5}' (csrc/unit.c:69-76)")
	_assert(era.has_method("kind") and era.has_method("movement_kinds"),
		"EraConfig.kind() / movement_kinds() missing; spec 3e: 'EraConfig.kind() and EraConfig.movement_kinds() read from the manifest'")
	if not (era.has_method("kind") and era.has_method("movement_kinds")):
		return
	_set_era(GROUND_ERA)
	_assert(_era_is_var() and str(era.call("kind")) == "ground", "EraConfig.kind() for greek_placeholder is not 'ground' (manifest kind, spec 3e)")
	var g: Array = era.call("movement_kinds")
	_assert(_flat_pairs_ok(g), "movement_kinds() is not the flat int list [t, k, t, k, ...] with t in 0..5, k in 0|1; pre-flight: 'the wire form is flat movement_kinds: [t, k, t, k, ...]'")
	_assert(_flat_pairs_ok(g) and g.size() == 12, "movement_kinds() for greek_placeholder does not cover all six types (12 ints); spec 3f: each roster row gains movement")
	var any_walking := false
	for i in range(1, g.size(), 2):
		any_walking = any_walking or int(g[i]) == 1
	_assert(any_walking, "greek_placeholder movement_kinds() has no walking type; spec 3f: 'greek_placeholder walking except the placeholder scout'")
	_set_era(SPACE_ERA)
	_assert(_era_is_var() and str(era.call("kind")) == "space", "EraConfig.kind() for settled_reach is not 'space' (spec 3e)")
	var s: Array = era.call("movement_kinds")
	var all_fly := _flat_pairs_ok(s)
	for i in range(1, s.size(), 2):
		all_fly = all_fly and int(s[i]) == 0
	_assert(all_fly, "settled_reach movement_kinds() is not all flying (kind 0); spec 3f: 'settled_reach all flying'")


# ---- 3c: the bridge --------------------------------------------------------------------------

func _check_bridge(_bag: Dictionary) -> void:
	var CBridge = load("res://autoload/c_bridge.gd")
	var probe = CBridge.new()
	_assert(probe.has_method("terrain"), "c_bridge.gd has no terrain(); spec 3c: 'terrain() -> Dictionary (empty in space)'")
	_assert(probe.has_method("load_tactical_live") and probe.has_method("begin_mission_live"), "c_bridge.gd lost begin_mission_live / load_tactical_live (control: the fake drives these)")

	var f = _new_fake()
	_assert(f != null, "the fake pipe subclass did not compile (control)")
	if f == null:
		return

	# control: a space mission against the fake works and sends no terrain_dump
	_set_era(SPACE_ERA)
	_assert(f.load_mission_live(1, 10, []), "control: space mission_start through the fake failed: %s" % f.last_error())
	_assert(f.count("terrain_dump") == 0, "control: a space mission sent terrain_dump")
	var ms: Dictionary = f.first_cmd("mission_start")
	_assert(int(ms.get("era_kind", -1)) == 0,
		"space mission_start does not carry era_kind 0; spec 3c: 'mission_start sends era_kind and movement_kinds from EraConfig' (got %s)" % str(ms.get("era_kind")))
	_assert(_flat_pairs_ok(ms.get("movement_kinds", null)),
		"space mission_start does not carry a flat movement_kinds [t, k, ...]; pre-flight: 'the wire form is flat movement_kinds' (got %s)" % str(ms.get("movement_kinds")))
	_assert(f.begin_mission_live(1, 10, []), "control: begin_mission_live failed in space: %s" % f.last_error())
	_assert(f.count("terrain_dump") == 0, "a space mission requested terrain_dump after mission_begin; spec 3c: 'terrain() (empty in space)', one dump only 'in a ground era'")
	_assert(f.has_method("terrain") and (f.terrain() as Dictionary).is_empty(), "terrain() is not empty in a space era; spec 3c")

	# ground: one dump after mission_begin, decoded
	var g = _new_fake()
	_set_era(GROUND_ERA)
	_assert(g.load_mission_live(1, 10, []), "ground mission_start through the fake failed: %s" % g.last_error())
	var gm: Dictionary = g.first_cmd("mission_start")
	_assert(int(gm.get("era_kind", -1)) == 1,
		"ground mission_start does not carry era_kind 1; spec 3c: 'mission_start sends era_kind' (era %s; got %s)" % [GROUND_ERA, str(gm.get("era_kind"))])
	var mk: Variant = gm.get("movement_kinds", null)
	_assert(_flat_pairs_ok(mk), "ground mission_start movement_kinds is not flat ints [t, k, ...]; pre-flight: flat form parsed by get_int_array (got %s)" % str(mk))
	var e := _era()
	if e != null and e.has_method("movement_kinds"):
		_assert(mk == e.call("movement_kinds"), "mission_start movement_kinds differs from EraConfig.movement_kinds(); spec 3c: 'the request carries the kinds'")
	_assert(g.count("terrain_dump") == 0, "terrain_dump sent before mission_begin; spec 3c: 'After mission_begin'")
	_assert(g.begin_mission_live(1, 10, []), "ground begin_mission_live failed: %s" % g.last_error())
	_assert(g.count("terrain_dump") == 1, "ground era sent %d terrain_dump after mission_begin, expected 1; spec 3c: 'one terrain_dump'" % g.count("terrain_dump"))
	_assert(g.first_index("terrain_dump") > g.first_index("mission_begin"), "terrain_dump was not sent after mission_begin; spec 3c")
	var t: Dictionary = g.terrain() if g.has_method("terrain") else {}
	_assert(int(t.get("cells_w", 0)) == DIM and int(t.get("cells_h", 0)) == DIM, "terrain() cells_w/cells_h not 240x240 (got %s x %s); spec 3c: 'a fake pipe answering a 240^2 dump fills terrain()'" % [str(t.get("cells_w")), str(t.get("cells_h"))])
	var bands: Variant = t.get("bands", null)
	_assert(bands is PackedByteArray and (bands as PackedByteArray).size() == DIM * DIM, "terrain().bands is not a PackedByteArray of cells_w*cells_h bytes; spec 3c: 'decoded to bands'")
	if bands is PackedByteArray and (bands as PackedByteArray).size() == DIM * DIM:
		var b: PackedByteArray = bands
		var seen := {}
		for v in b:
			seen[int(v)] = true
		_assert(seen.size() == 5 and b[0] == 1 and b[DIM - 1] == 5 and b[7 * DIM + 100] == 3, "decoded bands differ from the dump (hex decode wrong)")
	var walk: Variant = t.get("walkable", null)
	_assert(walk is PackedByteArray and (walk as PackedByteArray).size() == DIM * DIM, "terrain().walkable is not a PackedByteArray of cells_w*cells_h bytes; spec 3c: 'decoded to bands, walkable and slopes'")
	if walk is PackedByteArray and (walk as PackedByteArray).size() == DIM * DIM:
		var w: PackedByteArray = walk
		_assert(w[0] == 1 and w[9 * DIM + 3] == 0 and w[10 * DIM + 3] == 1, "decoded walkable differs from the dump")
	var sl: Variant = t.get("slopes", null)
	_assert(sl is Array and (sl as Array).size() == 3, "terrain().slopes is not the dump's 3 slope rows; spec 3c: 'decoded to bands, walkable and slopes'")
	if sl is Array and (sl as Array).size() == 3:
		var s1: Dictionary = sl[1]
		_assert(float(s1.get("mx", -1.0)) == 150.0 and int(s1.get("upper_band", 0)) == 2 and s1.has("length"), "slope rows lost their fields (mx, length, lower_band, upper_band)")

	# never re-requested on deltas
	_assert(g.load_tactical_live(1, 10, []), "ground load_tactical_live failed: %s" % g.last_error())
	_assert(g.tactical_step_n(3), "ground tactical_step_n failed: %s" % g.last_error())
	_assert(g.count("tactical_step") >= 2 and g.count("terrain_dump") == 1,
		"terrain_dump was re-requested after tactical frames (%d dumps); spec 3c: 'never re-requested on deltas'" % g.count("terrain_dump"))
	_assert(int((g.terrain() as Dictionary).get("cells_w", 0)) == DIM if g.has_method("terrain") else false, "terrain() lost its content after tactical frames; spec 3c")

	# a following space mission leaves terrain() empty
	_assert(g.load_debrief_live(1, 10, []), "ground load_debrief_live failed: %s" % g.last_error())
	_set_era(SPACE_ERA)
	_assert(g.begin_mission_live(1, 10, []), "space mission after a ground one failed: %s" % g.last_error())
	_assert(g.count("terrain_dump") == 1, "a space mission after a ground one requested a dump; spec 3c: 'empty in space'")
	_assert(g.has_method("terrain") and (g.terrain() as Dictionary).is_empty(), "terrain() kept the ground mission's terrain into a space mission; spec 3a/3c: 'a ground then a space mission ... leaves no terrain'")

	# named error on generate failure
	var h = _new_fake()
	h.fail_generate = true
	_set_era(GROUND_ERA)
	var ok: bool = h.load_mission_live(1, 10, [])
	_assert(not ok, "a ground mission_start answered 'terrain generate failed' but load_mission_live returned true (no silent flat mission); spec 3a")
	_assert(h.last_error() == "terrain generate failed", "last_error() = '%s', expected 'terrain generate failed'; pre-flight: 'write_error(\"mission_start\", \"terrain generate failed\")'" % h.last_error())
	_assert(h.count("terrain_dump") == 0 and h.count("mission_begin") == 0, "the bridge went on to dump terrain / begin after a failed generate; spec 3a: no silent flat mission")
	_assert(int(h.first_cmd("mission_start").get("era_kind", -1)) == 1, "the failing request never carried era_kind 1 (the fake only fails ground missions); spec 3c")
	_set_era(SPACE_ERA)


# ---- 3e: UIDataBus key -----------------------------------------------------------------------

func _check_ui_data_bus(cfg_path: String) -> void:
	var bus := root.get_node_or_null("UIDataBus")
	_assert(bus != null, "UIDataBus autoload missing (control)")
	if bus == null:
		return
	var s: Dictionary = bus.get_settings()
	s["era_id"] = GROUND_ERA
	bus.save_settings(s)
	_assert(str(bus.get_settings().get("era_id", "")) == GROUND_ERA,
		"UIDataBus.save_settings drops era_id (get_settings has %s); pre-flight: 'edits ui_data_bus.gd ... section [game] era_id'" % str(bus.get_settings().get("era_id")))
	var c := ConfigFile.new()
	_assert(c.load(cfg_path) == OK and str(c.get_value("game", "era_id", "")) == GROUND_ERA,
		"settings.cfg has no [game] era_id after save_settings; pre-flight: section [game] era_id")
	bus.call("_load_settings")
	_assert(str(bus.get_settings().get("era_id", "")) == GROUND_ERA, "UIDataBus._load_settings does not read [game] era_id back (the rebuild from a fixed key list drops it); pre-flight")
	var s2: Dictionary = bus.get_settings()
	s2["era_id"] = SPACE_ERA
	bus.save_settings(s2)
	_assert(str(bus.get_settings().get("pan_speed", "x")) != "x" and float(bus.get_settings().get("pan_speed", 0.0)) > 0.0, "control: other settings keys survived save_settings")
	# an unrelated save without era_id must not wipe a chosen era: callers pass partial dicts today
	var partial: Dictionary = bus.get_settings()
	partial.erase("era_id")
	bus.save_settings(partial)
	_assert(str(bus.get_settings().get("era_id", "")) in [SPACE_ERA, ""], "control: era_id after a partial save is an unexpected value")


# ---- 3e: --era <id> (space form) -------------------------------------------------------------

func _run_probe(args: PackedStringArray) -> String:
	var probe_path := OS.get_user_data_dir().path_join("t3c_probe.gd")
	var f := FileAccess.open(probe_path, FileAccess.WRITE)
	if f == null:
		return "probe-unwritable"
	f.store_string(PROBE_SRC)
	f.close()
	var argv := PackedStringArray(["--headless", "--path", ProjectSettings.globalize_path("res://"), "--script", probe_path])
	if args.size() > 0:
		argv.append("--")
		argv.append_array(args)
	var out := []
	OS.execute(OS.get_executable_path(), argv, out, false)
	for chunk in out:
		for line in String(chunk).split("\n"):
			if line.begins_with("ERA="):
				return line.substr(4).strip_edges()
	return "no-output"


func _write_era_setting(cfg_path: String, id: String) -> void:
	var c := ConfigFile.new()
	if id != "":
		c.set_value("game", "era_id", id)
	c.save(cfg_path)


func _check_era_arg(cfg_path: String) -> void:
	_write_era_setting(cfg_path, "")
	var base := _run_probe(PackedStringArray())
	_assert(base == SPACE_ERA, "control: with no --era and no saved era the active era is '%s', expected settled_reach" % base)
	var arg := _run_probe(PackedStringArray(["--era", GROUND_ERA]))
	_assert(arg == GROUND_ERA, "`--era greek_placeholder` leaves the active era '%s'; spec 3e/pre-flight: 'user arg --era <id> (space form), read by EraConfig before settings'" % arg)
	var eq := _run_probe(PackedStringArray(["--era=" + GROUND_ERA]))
	_assert(eq == SPACE_ERA, "the '--era=<id>' form changed the era to '%s'; pre-flight fixes the space form only (c_bridge.gd:100-103 --seed <n>); spec's 3d '--era=' text is stale" % eq)
	_write_era_setting(cfg_path, GROUND_ERA)
	var saved := _run_probe(PackedStringArray())
	_assert(saved == GROUND_ERA, "with saved [game] era_id greek_placeholder and no arg the active era is '%s'; spec 3e: 'else the saved setting'" % saved)
	_write_era_setting(cfg_path, SPACE_ERA)
	var over := _run_probe(PackedStringArray(["--era", GROUND_ERA]))
	_assert(over == GROUND_ERA, "`--era greek_placeholder` does not override a saved settled_reach (got '%s'); spec 3e: '--era overrides the setting'" % over)


# ---- 3d: ramp constants from origin/push/proto-walkers ---------------------------------------

func _check_ramp_constants() -> void:
	var path := "res://scenes/tactical_c/terrain_layer.gd"
	_assert(ResourceLoader.exists(path), "scenes/tactical_c/terrain_layer.gd does not exist; spec 3d: 'terrain_layer.gd (new, under the C5 glob)'")
	if not ResourceLoader.exists(path):
		return
	var consts: Dictionary = (load(path) as Script).get_script_constant_map()
	var ramp := [Color(0.40, 0.72, 0.42), Color(0.72, 0.80, 0.38), Color(0.90, 0.68, 0.30), Color(0.72, 0.48, 0.30), Color(0.92, 0.90, 0.88)]
	_assert(consts.get("BAND_COLOURS", []) == ramp, "terrain_layer.gd BAND_COLOURS is not the walkers mockup's ramp (0.40,0.72,0.42) (0.72,0.80,0.38) (0.90,0.68,0.30) (0.72,0.48,0.30) (0.92,0.90,0.88); pre-flight: 'reads its constants from origin/push/proto-walkers'")
	_assert(consts.get("STEEP_COLOUR", Color()) == Color(0.85, 0.10, 0.85), "terrain_layer.gd STEEP_COLOUR is not (0.85,0.10,0.85); pre-flight: 'lerped 0.5 on unwalkable land'")
