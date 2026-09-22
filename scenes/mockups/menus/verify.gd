extends SceneTree

const MOCKUP_SCENE := "res://scenes/mockups/menus/menus_mockup.tscn"
const Resolve := preload("res://scenes/mockups/menus/resolve.gd")
const Flow := preload("res://scenes/mockups/menus/flow.gd")
const CONTRACT_KEYS := ["seed", "hash", "screen", "difficulty", "campaigns", "briefing", "resolve", "controls", "timing_ms", "regen_count"]
const DEFENSIVE_THRESHOLDS := [0.20, 0.40, 0.60, 0.80]

var _failures := 0
var _root: Node


func _initialize() -> void:
	_check_det_1()
	_check_edges_2()
	_check_setup_3()
	_check_bands_6()
	_check_weights_7()
	_check_camp_9()
	await _check_sect_4()
	await _check_digits_5()
	await _check_controls_8()
	await _check_json_10()

	if _failures > 0:
		print("VERIFY FAILED: %d check(s)" % _failures)
		quit(1)
		return
	print("VERIFY OK")
	quit(0)


func _new_root() -> Node:
	var packed: PackedScene = load(MOCKUP_SCENE)
	if packed == null:
		return null
	var r: Node = packed.instantiate()
	get_root().add_child(r)
	await process_frame
	await process_frame
	return r


func _check_det_1() -> void:
	var a := Resolve.resolve(0.9, "medium", 11, DEFENSIVE_THRESHOLDS)
	var b := Resolve.resolve(0.9, "medium", 11, DEFENSIVE_THRESHOLDS)
	var c := Resolve.resolve(0.9, "medium", 12, DEFENSIVE_THRESHOLDS)
	var d := Resolve.resolve(0.9, "medium", 11, DEFENSIVE_THRESHOLDS)
	# plant: band-random
	_assert(a.score == b.score and a.band == b.band and c.score != a.score and d.band == a.band, "DET-1", "seed 11 must repeat exactly, seed 12 must differ in roll, same seed must give the same band")


func _check_edges_2() -> void:
	var f := Flow.new()
	var all_ok := true
	for from in Flow.EDGES.keys():
		for action in Flow.EDGES[from].keys():
			var r: Dictionary = f.attempt(from, action)
			if not (r.ok and r.to == Flow.EDGES[from][action]):
				all_ok = false
	var bad := f.attempt("title", "accept")
	var rejects_ok: bool = not bad.ok and bad.has("reason")
	# plant: flow-skips-setup
	var edge: Dictionary = f.attempt("title", "new_campaign")
	var no_skip: bool = edge.ok and edge.to == "setup"
	_assert(all_ok and rejects_ok and no_skip, "EDGES-2", "every allowed edge must transition correctly, disallowed ones rejected with a reason, and title must not skip setup")


func _check_setup_3() -> void:
	var f := Flow.new()
	f.do("new_campaign")
	f.do("begin", "hard")
	var record_ok: bool = f.campaigns.size() == 1 and f.campaigns[0].difficulty == "hard"
	var hard := Resolve.resolve(0.9, "hard", 11, DEFENSIVE_THRESHOLDS)
	var easy := Resolve.resolve(0.9, "easy", 11, DEFENSIVE_THRESHOLDS)
	# plant: difficulty-dropped
	_assert(record_ok and hard.score != easy.score, "SETUP-3", "the campaign record must carry the chosen difficulty and it must change the resolve score")


func _check_bands_6() -> void:
	var finals := [0.1, 0.3, 0.5, 0.7, 0.9]
	var expected := ["total_failure", "partial_failure", "partial_success", "strong_success", "total_success"]
	var bands_ok := true
	for i in range(finals.size()):
		if Resolve.band_for(finals[i], DEFENSIVE_THRESHOLDS) != expected[i]:
			bands_ok = false
	var low: float = Resolve.resolve(0.3, "medium", 11, DEFENSIVE_THRESHOLDS).score
	var high: float = Resolve.resolve(0.9, "medium", 11, DEFENSIVE_THRESHOLDS).score
	# plant: four-bands
	_assert(bands_ok and high >= low, "BANDS-6", "finals 0.1/0.3/0.5/0.7/0.9 must map to the five bands in order and resolve must be monotone in parity")


func _check_weights_7() -> void:
	var final := Resolve.final_score(1.0, 0.67)
	var band := Resolve.band_for(final, DEFENSIVE_THRESHOLDS)
	_assert(is_equal_approx(final, 0.9175) and band == "total_success", "WEIGHTS-7", "0.75*1.0 + 0.25*0.67 must equal 0.9175 and band total_success, got %.4f/%s" % [final, band])


func _check_camp_9() -> void:
	var f := Flow.new()
	f.do("new_campaign")
	f.do("begin", "easy")
	f.do("refuse")
	f.do("new_campaign")
	f.do("begin", "hard")
	var both_listed := f.campaigns.size() == 2
	var records_ok := true
	for rec in f.campaigns:
		if not (rec.has("chapter") and rec.has("last_band")):
			records_ok = false
	var name0: String = f.campaigns[0].name if f.campaigns.size() > 0 else ""
	f.do("refuse")
	f.do("continue")
	var r := f.do("resume:%s" % name0)
	_assert(both_listed and records_ok and r.ok and f.screen == "briefing", "CAMP-9", "two started campaigns must be listed with chapter/last_band, and Resume must reach the briefing")


func _check_sect_4() -> void:
	_root = await _new_root()
	if _root == null:
		_assert(false, "SECT-4", "cannot load %s" % MOCKUP_SCENE)
		return
	_root.qa_go("new_campaign")
	_root.qa_go("pick_medium")
	_root.qa_go("begin")
	var b: Dictionary = _root.qa_state().briefing
	# plant: briefing-two-sections
	_assert(b.sections == ["Situation", "Objective", "Assets"] and b.attacker_named, "SECT-4", "sections must be exactly Situation, Objective, Assets in order and Situation must name the attacker")


func _check_digits_5() -> void:
	_root = await _new_root()
	_root.qa_go("new_campaign")
	_root.qa_go("pick_medium")
	_root.qa_go("begin")
	var briefing_no_digits: bool = not _root.qa_state().briefing.has_digits
	_root.qa_go("accept")
	_root.qa_go("resolve_continue")
	var texts: Array = []
	var debrief_node := _root.get_node_or_null("Screens/Debrief")
	if debrief_node != null:
		_collect_texts(debrief_node, texts)
	# plant: digits-in-prose
	_assert(briefing_no_digits and not _has_digit(" ".join(texts)), "DIGITS-5", "briefing and debrief text must contain no digits")


func _check_controls_8() -> void:
	_root = await _new_root()
	var title_ok: bool = _root.qa_state().controls == ["New Campaign", "Continue", "Settings", "Quit"]
	_root.qa_go("new_campaign")
	_root.qa_go("pick_medium")
	_root.qa_go("begin")
	var briefing_ok: bool = _root.qa_state().controls == ["Accept", "Refuse"]
	_assert(title_ok and briefing_ok, "CONTROLS-8", "title controls must be New Campaign/Continue/Settings/Quit; briefing controls must be Accept/Refuse")


func _check_json_10() -> void:
	_root = await _new_root()
	var st: Dictionary = _root.qa_state()
	var keys_ok := JSON.stringify(st) != ""
	for key in CONTRACT_KEYS:
		if not st.has(key):
			keys_ok = false
	var plants_ok: bool = not _root.qa_plant("nope")
	for id in _root.PLANTS:
		if not _root.qa_plant(id):
			plants_ok = false
	_assert(keys_ok and plants_ok, "JSON-10", "qa_state() must round-trip through JSON with every contract key, qa_plant('nope') false, every PLANTS id true")


func _collect_texts(node: Node, out: Array) -> void:
	if node is Label or node is RichTextLabel:
		out.append(String(node.text))
	for child in node.get_children():
		_collect_texts(child, out)


func _has_digit(s: String) -> bool:
	for c in s:
		if c >= "0" and c <= "9":
			return true
	return false


func _assert(cond: bool, id: String, msg: String) -> void:
	if not cond:
		_failures += 1
		print("FAIL: %s %s" % [id, msg])
