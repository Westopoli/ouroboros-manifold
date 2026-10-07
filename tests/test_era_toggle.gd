extends SceneTree

# Piece 3e (docs/northstar/plans/2026-10-06-terrain-stage3-spec.md rev 3: the Pieces table row 3e,
# "What the audit changed", "What the pre-flight changed"; Q-STAGE3-02 a). Tests first: every
# test marked RED must fail on origin/push/t3-contract.
#
# 3e makes the era a startup choice: EraConfig.ACTIVE_ERA_ID becomes a `var` (was a `const`,
# era_config.gd:3), resolved at startup from the user arg `--era <id>` (SPACE form, not `--era=<id>`;
# c_bridge.gd:100-103 reads `--seed <n>` the same way), else the saved setting
# [game] era_id (UIDataBus, both branches of _load_settings and save_settings), else settled_reach.
# EraConfig reads the manifest `kind` (EraConfig.kind(), "space" or "ground") and the roster rows'
# `movement` (EraConfig.movement_kinds(), the FLAT list [type_id, kind, type_id, kind, ...],
# kind 0 flying, 1 walking), through the table EraConfig.TYPE_IDS (manifests key units by name;
# the sim's ids are OM_UT_* at csrc/unit.c:69-76). The main menu gets an Era toggle
# (space = settled_reach, ground = greek_placeholder) persisted through UIDataBus.
#
# Names this test chooses where the spec gives none (report them to the card writer):
#   - EraConfig.kind() returns the manifest string "space" or "ground";
#   - the toggle is the one visible OptionButton or BaseButton on the main menu whose text (or, for
#     an OptionButton, whose items) names the era, found by a scan, not by node name; "Era Library"
#     is not the toggle;
#   - greek_placeholder has exactly one flying type (the placeholder scout, R-201-01); which type
#     it is, is 3f's to say, so it is not asserted.
# Boots run as child processes (own XDG_DATA_HOME) because the startup resolution and the
# user args can only be seen at boot. Linux/XDG only.

const SCRIPT_PATH := "res://tests/test_era_toggle.gd"
const SPACE_ID := "settled_reach"
const GROUND_ID := "greek_placeholder"
# csrc/unit.c:69-76 (spec "What the pre-flight changed").
const SIM_TYPE_IDS := {"raider": 0, "interceptor": 1, "vanguard": 2, "warden": 3, "bombard": 4, "bastion": 5}

var _pass_count := 0
var _fail_count := 0
var _fail_msgs: Array[String] = []
var _completed := false


func _initialize() -> void:
	var args := OS.get_cmdline_user_args()
	var idx := args.find("--probe")
	if idx != -1 and idx + 1 < args.size():
		await _probe(args[idx + 1])
		return
	await _run_tests()
	_assert(_completed, "the era-toggle checks did not run to the end (a script error aborted them)")
	print("\n=== Era Toggle Test Results ===")
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


# ---- child ------------------------------------------------------------------

func _era_snapshot(out: Dictionary) -> void:
	var era = get_root().get_node_or_null("EraConfig")
	if era == null:
		out["era_missing"] = true
		return
	out["active"] = String(era.ACTIVE_ERA_ID)
	var consts: Dictionary = era.get_script().get_script_constant_map()
	out["active_is_const"] = consts.has("ACTIVE_ERA_ID")
	out["has_layer_height_const"] = consts.has("LAYER_HEIGHT")
	out["type_ids"] = consts.get("TYPE_IDS", {})
	out["has_kind"] = era.has_method("kind")
	out["has_movement_kinds"] = era.has_method("movement_kinds")
	if era.has_method("kind"):
		out["kind"] = str(era.kind())
	if era.has_method("movement_kinds"):
		out["movement_kinds"] = era.movement_kinds()


func _scan_toggle(node: Node, found: Array) -> void:
	if node is Control and not (node as Control).is_visible_in_tree():
		return
	if node is OptionButton:
		var ob := node as OptionButton
		var names: Array = []
		for i in range(ob.item_count):
			names.append(ob.get_item_text(i).to_lower())
		if ob.text.to_lower().find("era") != -1 or str(names).find("space") != -1 or str(names).find("ground") != -1:
			found.append(node)
	elif node is BaseButton:
		var t := ""
		if node is Button:
			t = (node as Button).text.to_lower()
		if t.find("era") != -1 and t.find("library") == -1:
			found.append(node)
	for c in node.get_children():
		_scan_toggle(c, found)


func _menu_texts(node: Node, out: Array) -> void:
	if node is Label:
		out.append((node as Label).text.to_lower())
	elif node is Button:
		out.append((node as Button).text.to_lower())
	for c in node.get_children():
		_menu_texts(c, out)


func _flip(toggle: Node) -> void:
	if toggle is OptionButton:
		var ob := toggle as OptionButton
		var next := (ob.selected + 1) % maxi(ob.item_count, 1)
		ob.select(next)
		ob.item_selected.emit(next)
	elif (toggle as BaseButton).toggle_mode:
		(toggle as BaseButton).button_pressed = not (toggle as BaseButton).button_pressed
	else:
		(toggle as BaseButton).pressed.emit()


func _file_game() -> Dictionary:
	var cfg := ConfigFile.new()
	var out := {}
	if cfg.load("user://settings.cfg") == OK:
		if cfg.has_section("game"):
			for key in cfg.get_section_keys("game"):
				out[key] = cfg.get_value("game", key)
		out["audio_master"] = cfg.get_value("audio", "master_volume", null)
	return out


func _probe(mode: String) -> void:
	await process_frame
	await process_frame
	var out := {"mode": mode}
	_era_snapshot(out)
	var bus = get_root().get_node_or_null("UIDataBus")
	out["stored"] = bus.get_settings() if bus != null else {}
	if mode == "roundtrip":
		var s: Dictionary = bus.get_settings()
		bus.save_settings(s)
		out["after_save"] = bus.get_settings()
		out["file_game"] = _file_game()
	elif mode == "toggle":
		var menu: Node = (load("res://scenes/main_menu/main_menu.tscn") as PackedScene).instantiate()
		get_root().add_child(menu)
		await process_frame
		await process_frame
		var texts: Array = []
		_menu_texts(menu, texts)
		out["menu_has_new_campaign"] = str(texts).find("new campaign") != -1
		var found: Array = []
		_scan_toggle(menu, found)
		out["toggle_count"] = found.size()
		if found.size() == 1:
			_flip(found[0])
			await process_frame
			out["after_one"] = {"settings": bus.get_settings(), "file": _file_game()}
			_era_snapshot(out["after_one"])
			_flip(found[0])
			await process_frame
			out["after_two"] = {"settings": bus.get_settings(), "file": _file_game()}
			_era_snapshot(out["after_two"])
	print("PROBE ", JSON.stringify(out))
	quit(0)


# ---- parent -----------------------------------------------------------------

func _boot_child(fixture: String, mode: String, extra: Array = []) -> Dictionary:
	var base := OS.get_cache_dir().path_join("om_3e_%d_%s_%d" % [OS.get_process_id(), mode, extra.size()])
	var user_dir := base.path_join(str(ProjectSettings.get_setting("application/config/custom_user_dir_name", "data")))
	DirAccess.make_dir_recursive_absolute(user_dir)
	if fixture != "":
		var f := FileAccess.open(user_dir.path_join("settings.cfg"), FileAccess.WRITE)
		f.store_string(fixture)
		f.close()
	var prior := OS.get_environment("XDG_DATA_HOME")
	OS.set_environment("XDG_DATA_HOME", base)
	var output: Array = []
	var cmd: Array = ["--headless", "--path", ProjectSettings.globalize_path("res://"), "--quit-after", "3000",
		"--script", SCRIPT_PATH, "--", "--probe", mode]
	cmd.append_array(extra)
	var code := OS.execute(OS.get_executable_path(), cmd, output, true)
	if prior == "":
		OS.unset_environment("XDG_DATA_HOME")
	else:
		OS.set_environment("XDG_DATA_HOME", prior)
	DirAccess.remove_absolute(user_dir.path_join("settings.cfg"))
	DirAccess.remove_absolute(user_dir)
	DirAccess.remove_absolute(base)
	var text := "\n".join(PackedStringArray(output))
	for line in text.split("\n"):
		if line.begins_with("PROBE "):
			var parsed = JSON.parse_string(line.substr(6))
			if parsed is Dictionary:
				return parsed
	return {"error": "no PROBE line (exit %d): %s" % [code, text.left(400)]}


func _flat_pairs(flat) -> Dictionary:
	# [t, k, t, k, ...] -> {t: k}; empty dict when it is not a flat even list of numbers.
	var out := {}
	if not (flat is Array) or (flat as Array).size() % 2 != 0:
		return out
	for i in range(0, (flat as Array).size(), 2):
		var t = flat[i]
		var k = flat[i + 1]
		if typeof(t) == TYPE_ARRAY or typeof(k) == TYPE_ARRAY:
			return {}
		out[int(t)] = int(k)
	return out


func _check_movement(snap: Dictionary, label: String, expect_flying: int) -> void:
	var flat = snap.get("movement_kinds", null)
	_assert(flat is Array and (flat as Array).size() == 12 and typeof((flat as Array)[0]) != TYPE_ARRAY,
		"RED (audit: 'the wire form is flat movement_kinds [t, k, t, k, ...]'): %s EraConfig.movement_kinds() is not a flat 12-number list: %s" % [label, JSON.stringify(flat)])
	var pairs := _flat_pairs(flat)
	var all_types := true
	for t in range(6):
		all_types = all_types and pairs.has(t) and (int(pairs[t]) == 0 or int(pairs[t]) == 1)
	_assert(pairs.size() == 6 and all_types,
		"RED (3e: movement kinds read from the manifest roster rows): %s covers type ids 0..5 once each with kind 0 or 1: %s" % [label, JSON.stringify(flat)])
	var flying := 0
	for t in pairs:
		if int(pairs[t]) == 0:
			flying += 1
	_assert(pairs.size() == 6 and flying == expect_flying,
		"RED (3f/3e: %s): %d flying types expected, got %d in %s" % [label, expect_flying, flying, JSON.stringify(flat)])


func _run_tests() -> void:
	# --- default boot: no setting, no arg -> settled_reach (CONTROL: green today; proves the probe reads EraConfig) ---
	var base := _boot_child("", "default")
	_assert(not base.has("error"), "default boot child failed: %s" % str(base.get("error", "")))
	_assert(str(base.get("active", "")) == SPACE_ID,
		"CONTROL: with no setting and no --era the active era is settled_reach (got %s)" % str(base.get("active")))
	_assert(bool(base.get("has_layer_height_const", false)) and not bool(base.get("era_missing", false)),
		"CONTROL: the probe sees EraConfig's existing constants (LAYER_HEIGHT)")

	# --- ACTIVE_ERA_ID is a var, not a const (audit: era_config.gd:3 is a const) ---
	_assert(not bool(base.get("active_is_const", true)),
		"RED (audit: 'ACTIVE_ERA_ID is a const (era_config.gd:3)'; 3e 'makes it a var set once at startup'): ACTIVE_ERA_ID is still a script constant")

	# --- TYPE_IDS table (pre-flight: 'const TYPE_IDS = {raider 0, ...}' in era_config.gd) ---
	var ids = base.get("type_ids", {})
	var ids_ok: bool = ids is Dictionary and (ids as Dictionary).size() == SIM_TYPE_IDS.size()
	if ids_ok:
		for name in SIM_TYPE_IDS:
			ids_ok = ids_ok and (ids as Dictionary).has(name) and int(ids[name]) == int(SIM_TYPE_IDS[name])
	_assert(ids_ok,
		"RED (pre-flight: 'no name-to-id table exists; 3f writes const TYPE_IDS = {raider 0, interceptor 1, vanguard 2, warden 3, bombard 4, bastion 5} in era_config.gd'): got %s" % JSON.stringify(ids))

	# --- manifest readers exist and a space era is space with all-flying kinds ---
	_assert(bool(base.get("has_kind", false)),
		"RED (3e: 'EraConfig.kind() ... read from the manifest'): EraConfig has no kind()")
	_assert(str(base.get("kind", "")) == "space",
		"RED (3e): settled_reach's kind() is 'space' (got %s)" % str(base.get("kind")))
	_assert(bool(base.get("has_movement_kinds", false)),
		"RED (3e: 'EraConfig.movement_kinds() read from the manifest'): EraConfig has no movement_kinds()")
	_check_movement(base, "settled_reach", 6)

	# --- stored setting [game] era_id selects the era at startup ---
	var stored := _boot_child("[audio]\nmaster_volume=30\n[game]\nera_id=\"%s\"\n" % GROUND_ID, "roundtrip")
	_assert(str(stored.get("active", "")) == GROUND_ID,
		"RED (3e: 'else the saved setting'; pre-flight: '_load_settings, section [game] era_id'): a saved era_id of %s boots as %s" % [GROUND_ID, str(stored.get("active"))])
	_assert(str((stored.get("stored", {}) as Dictionary).get("era_id", "")) == GROUND_ID,
		"RED (pre-flight: '_load_settings drops unknown keys'): UIDataBus.get_settings() has era_id %s (got %s)" % [GROUND_ID, JSON.stringify((stored.get("stored", {}) as Dictionary).get("era_id"))])
	_assert(str(stored.get("kind", "")) == "ground",
		"RED (3e): greek_placeholder's kind() is 'ground' (got %s)" % str(stored.get("kind")))
	_check_movement(stored, "greek_placeholder", 0)  # TD-T3-ground-roster-flying: no scout row until S-201
	# round trip through save_settings keeps era_id and the other sections
	_assert(str((stored.get("after_save", {}) as Dictionary).get("era_id", "")) == GROUND_ID,
		"RED (pre-flight: 'save_settings rebuilds from a fixed key list; an unknown key is dropped'): era_id survives save_settings (got %s)" % JSON.stringify((stored.get("after_save", {}) as Dictionary).get("era_id")))
	_assert(str((stored.get("file_game", {}) as Dictionary).get("era_id", "")) == GROUND_ID,
		"RED (pre-flight: 'section [game] era_id'): settings.cfg [game] era_id is written (got %s)" % JSON.stringify(stored.get("file_game")))
	_assert(int((stored.get("file_game", {}) as Dictionary).get("audio_master", -1)) == 30,
		"CONTROL: the save round trip keeps [audio] master_volume 30 (the file is rewritten, not clobbered)")

	# --- the no-file branch also carries era_id (pre-flight: 'both branches of _load_settings') ---
	_assert(str((base.get("stored", {}) as Dictionary).get("era_id", "")) == SPACE_ID,
		"RED (pre-flight: 'both branches of _load_settings'): with no settings file get_settings().era_id is settled_reach (got %s)" % JSON.stringify((base.get("stored", {}) as Dictionary).get("era_id")))

	# --- --era <id> (space form) overrides the setting, and works with no setting ---
	var over := _boot_child("[game]\nera_id=\"%s\"\n" % SPACE_ID, "default", ["--era", GROUND_ID])
	_assert(str(over.get("active", "")) == GROUND_ID,
		"RED (3e: '--era overrides the setting'; pre-flight: '--era <id> space form'): setting settled_reach + --era %s boots as %s" % [GROUND_ID, str(over.get("active"))])
	_assert(str(over.get("kind", "")) == "ground",
		"RED (3e): --era greek_placeholder gives kind() 'ground' (got %s)" % str(over.get("kind")))
	var bare := _boot_child("", "default", ["--era", GROUND_ID])
	_assert(str(bare.get("active", "")) == GROUND_ID,
		"RED (3e: '--era=<id> user arg ... else the saved setting'): no setting + --era %s boots as %s" % [GROUND_ID, str(bare.get("active"))])
	# CONTROL for the arg detector: the same flag set to the space era over a ground setting gives space.
	var back := _boot_child("[game]\nera_id=\"%s\"\n" % GROUND_ID, "default", ["--era", SPACE_ID])
	_assert(str(back.get("active", "")) == SPACE_ID,
		"CONTROL (space form with an id that is already the default; passes before 3e, must still pass after): setting greek_placeholder + --era settled_reach boots as %s" % str(back.get("active")))

	# --- the main-menu Era toggle (Q-STAGE3-02 a) ---
	var tog := _boot_child("[audio]\nmaster_volume=30\n[game]\nera_id=\"%s\"\n" % SPACE_ID, "toggle")
	_assert(bool(tog.get("menu_has_new_campaign", false)),
		"CONTROL: the toggle scan sees the real main menu (it holds 'new campaign'); child result: %s" % str(tog.get("error", "ok")))
	_assert(int(tog.get("toggle_count", 0)) == 1,
		"RED (3e: 'an Era toggle on the main menu'): expected exactly one visible era toggle on the main menu, found %d" % int(tog.get("toggle_count", 0)))
	var one: Dictionary = tog.get("after_one", {})
	_assert(str((one.get("settings", {}) as Dictionary).get("era_id", "")) == GROUND_ID,
		"RED (3e: 'the toggle changes the setting'): one flip from space sets era_id %s (got %s)" % [GROUND_ID, JSON.stringify((one.get("settings", {}) as Dictionary).get("era_id"))])
	_assert(str((one.get("file", {}) as Dictionary).get("era_id", "")) == GROUND_ID,
		"RED (3e: 'persisted through UIDataBus settings'): one flip writes [game] era_id %s to the file" % GROUND_ID)
	_assert(str(one.get("kind", "")) == "ground" and str(one.get("active", "")) == GROUND_ID,
		"RED (3e: 'the next mission_start carries era_kind 1', which 3c reads from EraConfig): after one flip EraConfig is the ground era (active %s, kind %s)" % [str(one.get("active")), str(one.get("kind"))])
	var two: Dictionary = tog.get("after_two", {})
	_assert(str((two.get("settings", {}) as Dictionary).get("era_id", "")) == SPACE_ID and str(two.get("kind", "")) == "space",
		"RED (3e): a second flip returns to settled_reach / space (got %s / %s)" % [JSON.stringify((two.get("settings", {}) as Dictionary).get("era_id")), str(two.get("kind"))])
	_assert(int((one.get("file", {}) as Dictionary).get("audio_master", -1)) == 30,
		"RED (3e): the toggle's save keeps [audio] master_volume 30 (got %s); needs the toggle to exist first" % JSON.stringify((one.get("file", {}) as Dictionary).get("audio_master")))

	_completed = true
