extends SceneTree

const QaPlants := preload("res://scenes/mockups/_shared/qa_plants.gd")
const MOCKUP_SCENE := "res://scenes/mockups/chronicle/chronicle_mockup.tscn"
const CONTRACT_KEYS := ["seed", "hash", "tick", "phase", "entries", "expanded_id", "owners",
	"map_width_fraction", "pace", "dropped_entries", "timing_ms", "regen_count"]
const PLANTS := ["order-shuffled", "expand-noop", "no-pause", "entries-duplicate", "morph-instant", "cadence-wallclock"]

var _failures := 0
var _root


func _initialize() -> void:
	await _boot()

	_check_json_contract()
	_check_determinism()
	_check_count()
	_check_order()
	_check_words()
	_check_dedup()
	_check_keyframes()
	_check_pace()
	_check_pause()
	_check_morph()
	_check_layout()
	_check_background()

	for id in PLANTS:
		_assert(_root.qa_plant(id), "qa_plant(%s) must return true" % id)
	_assert(not _root.qa_plant("nope"), "qa_plant('nope') must return false")

	if _failures > 0:
		print("VERIFY FAILED: %d check(s)" % _failures)
		quit(1)
		return
	print("VERIFY OK")
	quit(0)


func _boot() -> void:
	var packed: PackedScene = load(MOCKUP_SCENE)
	_root = packed.instantiate()
	get_root().add_child(_root)
	await process_frame
	await process_frame


# plant: none
func _check_json_contract() -> void:
	_root.qa_seed(11)
	var st: Dictionary = _root.qa_state()
	_assert(JSON.stringify(st) != "", "qa_state() did not survive JSON.stringify")
	for key in CONTRACT_KEYS:
		_assert(st.has(key), "qa_state() missing key %s" % key)


# plant: cadence-wallclock
func _check_determinism() -> void:
	_root.qa_seed(11)
	_root.qa_tick(1200)
	var a: Dictionary = _root.qa_state()
	_root.qa_seed(11)
	_root.qa_tick(1200)
	var b: Dictionary = _root.qa_state()
	_assert(a.hash == b.hash, "qa_seed(11)+tick(1200) twice must hash equal")
	for i in range(a.entries.size()):
		_assert(a.entries[i].printed_words == b.entries[i].printed_words, "printed_words mismatch for %s" % a.entries[i].entry_id)
	_root.qa_seed(12)
	_root.qa_tick(1200)
	var c: Dictionary = _root.qa_state()
	_assert(a.hash != c.hash, "seed 12 must hash differently from seed 11")


# plant: entries-duplicate
func _check_count() -> void:
	for n in [11, 12]:
		_root.qa_seed(n)
		var st: Dictionary = _root.qa_state()
		_assert(st.entries.size() >= 5 and st.entries.size() <= 10, "seed %d entry count %d outside 5..10" % [n, st.entries.size()])
	var jump := ChronicleJump.new()
	jump.load_dict(_make_synthetic_fixture(10, true))
	_assert(jump.entries.size() >= 5 and jump.entries.size() <= 10, "synthetic 10-entry fixture produced %d entries" % jump.entries.size())


# plant: order-shuffled
func _check_order() -> void:
	for n in [11, 12]:
		_root.qa_seed(n)
		_assert(_root._jump.errors.is_empty(), "seed %d validation errors: %s" % [n, _root._jump.errors])
		_assert(String(_root._jump.entries[0].category).begins_with("consequence_"), "seed %d entries[0] not consequence" % n)


# plant: expand-noop
func _check_words() -> void:
	for n in [11, 12]:
		_root.qa_seed(n)
		var errs: Array = _root._jump.errors
		var word_errs := errs.filter(func(e): return String(e).contains("word") or String(e).contains("mention"))
		_assert(word_errs.is_empty(), "seed %d word/mention errors: %s" % [n, word_errs])


# plant: entries-duplicate
func _check_dedup() -> void:
	_root.qa_seed(11)
	_assert(_root._jump.dropped_entries.is_empty(), "clean seed 11 should not need drops: %s" % str(_root._jump.dropped_entries))
	var synth := _make_synthetic_fixture(6, true)
	synth.entries.append(_near_copy_of(synth.entries[2]))
	var jump := ChronicleJump.new()
	jump.load_dict(synth)
	if QaPlants.is_active("entries-duplicate"):
		_assert(jump.entries.size() == 7, "near-copy should survive under entries-duplicate")
	else:
		_assert(jump.dropped_entries.size() == 1, "near-copy should be dropped and reported")


# plant: none
func _check_keyframes() -> void:
	var good := ChronicleJump.new()
	good.load_dict(_make_synthetic_fixture(6, true))
	_assert(good.errors.is_empty(), "well-formed synthetic fixture should validate clean: %s" % str(good.errors))
	var bad := ChronicleJump.new()
	bad.load_dict(_make_synthetic_fixture(6, false))
	_assert(not bad.errors.is_empty(), "fixture with no keyframes must fail KEY-6 validation")


# plant: cadence-wallclock
func _check_pace() -> void:
	_root.qa_seed(11)
	_assert(float(_root.qa_state().pace.word_interval_s) == 0.08, "pace.word_interval_s must be 0.08")
	_root.qa_tick(16)
	var printed: int = int(_root.qa_state().entries[0].printed_words)
	_assert(printed == 10, "16 ticks should print exactly 10 words, got %d" % printed)


# plant: no-pause
func _check_pause() -> void:
	_root.qa_seed(11)
	_root.qa_tick(200)
	_root.qa_click_entry(0)
	var st1: Dictionary = _root.qa_state()
	_assert(String(st1.phase) == "paused", "click on a printed entry must pause")
	_root.qa_tick(100)
	var st2: Dictionary = _root.qa_state()
	_assert(int(st2.tick) == int(st1.tick), "qa_tick(100) while paused must not advance the clock")
	_root.qa_click_entry(1)
	_assert(String(_root.qa_state().phase) == "paused", "clicking a printing entry must do nothing")
	_root.qa_dismiss()
	_assert(String(_root.qa_state().phase) == "narrating", "dismiss must resume narrating")


# plant: morph-instant
func _check_morph() -> void:
	_root.qa_seed(11)
	_root.qa_tick(463)
	var before: Color = _root._mini_galaxy.get_system_color("r_moorwick")
	_root.qa_tick(20)
	var mid: Color = _root._mini_galaxy.get_system_color("r_moorwick")
	_root.qa_tick(20)
	var after: Color = _root._mini_galaxy.get_system_color("r_moorwick")
	var new_c: Color = _root._mini_galaxy._owner_color("f_ostrel")
	_assert(mid != before and mid != new_c, "at 1.0s the colour must be strictly between old and new")
	_assert(after.is_equal_approx(new_c), "at 2.0s the colour must equal the new owner colour")


# plant: none
func _check_layout() -> void:
	_root.qa_seed(11)
	_assert(is_equal_approx(float(_root.qa_state().map_width_fraction), 0.62), "map_width_fraction must be 0.62 at narration start")
	_root.qa_set("skip", true)
	_assert(is_equal_approx(float(_root.qa_state().map_width_fraction), 1.0), "map_width_fraction must be 1.0 at the end")
	var on_screen: int = _root._scroll._list.get_child_count()
	_assert(on_screen == _root._jump.entries.size(), "on-screen entry count %d must equal validated count %d" % [on_screen, _root._jump.entries.size()])


# plant: none
func _check_background() -> void:
	var env: Environment = _root.get_node("MapViewport/SubViewport/WorldEnvironment").environment
	_assert(env.background_mode == Environment.BG_COLOR, "map environment must use BG_COLOR, not BG_SKY, for background_color to render")
	var c: Color = env.background_color
	_assert(c.r < 0.08 and c.g < 0.08 and c.b < 0.12, "map environment background_color must be near-black, got %s" % c)


func _make_synthetic_fixture(n: int, with_keyframes: bool) -> Dictionary:
	var cats := ["consequence_success", "lineage_thrived", "chain_expansion", "regional_growth",
		"regional_decline", "chain_cascade", "regional_stable", "lineage_military_action",
		"chain_conflict_stalemate", "regional_faction_shift"]
	var entries: Array = []
	var keyframes: Array = []
	for i in range(n):
		var zone := "Zone%d" % i
		var base := "%s Grove%d Ridge%d Cycle%d Basin%d moved quiet." % [zone, i, i, i, i]
		var recorder := "Warden%d" % i
		var expanded := base + " %s recorded it plainly." % recorder
		var zs := base.find(zone)
		var rs := expanded.find(recorder)
		entries.append({
			"entry_id": "s_%02d" % i, "category": cats[i % cats.size()], "score": 100.0 - i,
			"tick_range_start": i * 100, "tick_range_end": i * 100 + 80,
			"base_form": base, "expanded_form": expanded,
			"mentions": [{"kind": "region", "id": zone, "form": "base", "span_start": zs, "span_end": zs + zone.length()}],
			"expanded_mentions": [
				{"kind": "region", "id": zone, "form": "expanded", "span_start": zs, "span_end": zs + zone.length()},
				{"kind": "character", "id": recorder, "form": "expanded", "span_start": rs, "span_end": rs + recorder.length()},
			],
		})
		if with_keyframes:
			keyframes.append({"tick": i * 100 + 10, "system_id": zone, "owner": ""})
	return {"time_jump_start": {"time_jump_id": "synthetic", "ownership_timeline": []}, "entries": entries, "galaxy": {"systems": [], "edges": []}, "keyframes": keyframes}


func _near_copy_of(e: Dictionary) -> Dictionary:
	var c: Dictionary = e.duplicate(true)
	c["entry_id"] = String(e.entry_id) + "_near"
	c["base_form"] = String(e.base_form) + " Or so it seemed at the time."
	return c


func _assert(condition: bool, message: String) -> void:
	if not condition:
		_failures += 1
		print("FAIL: %s" % message)
