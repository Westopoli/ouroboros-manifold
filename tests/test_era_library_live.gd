extends SceneTree

# Piece C4-E1 (owner G-eralib, docs/northstar/plans/push/pieces.toml; ruling A45 in
# docs/northstar/plans/2026-10-01-architect-rulings-2.md). Proves:
#   R-110-05  one card per installed era pack that passes validation; a failing pack is not listed;
#             each card has name and owned flag
#   R-110-06  the detail shows identity, three tiers and unit roster, all from the pack manifest;
#             nothing on screen is hard-coded
#   R-110-07  ownership comes from a local ownership store; in dev builds every installed era is
#             owned; the screen shows no mastery or tier progress (A51, Q-110-05 closed (a):
#             removed, not "not yet tracked")
# A58 (Addendum 24, Q-C4-E1-04 to 08) changes, all proved below:
#   04 ownership store user://era_ownership.json {"owned":[ids]}: a debug build ignores it and owns every
#      installed pack; the release reader is a unit with a path seam (below); no file = all installed owned
#   05 manifests carry era_spatial_scale, era_tone (text) and era_order (int); a pack missing one fails
#      validation and is not listed; the library lists packs in ascending era_order
#   06 roster shows the unit type id as the title plus its category; no role text
#   07 "test_only": true in a manifest = never listed (test_era); tests still load it by id
#   08 viewing screens only: no play-this-era control on the library or the detail
# Validation here is the required-key rule of scripts/specfactory/pack_validate.py (R-146-03).
#
# Contract required (the scene roots, res://scenes/era_library/):
#   era_library.tscn root:
#     qa_set_sources(packs_root: String, ownership_path: String) -> void
#         re-reads packs from <packs_root>/<era_id>/manifest.json and rebuilds the cards;
#         ownership_path "" = the real store user://era_ownership.json; a debug build ignores the store
#         and owns every installed era either way (A58 04)
#     qa_state() -> Dictionary   gains "eras": Array of {id, name, owned: bool, spatial_scale, tone,
#         order: int} in ascending era_order;
#         "era_count" == eras.size(); no mastery or tier-progress key anywhere in the state
#   era_detail.tscn root:
#     qa_set_sources(packs_root, ownership_path) -> void   (call before setup)
#     setup({"era_id": id}) as today
#     qa_state() -> Dictionary   gains "era_id", "name", "owned": bool, "tiers": Array[int]
#         (the tier numbers in the manifest), "roster": Array of {abstract_type, category};
#         no mastery, tier-progress, role or play key. Each roster row shows abstract_type as its
#         title label and the category in another label.
#   era_ownership.gd (res://scenes/era_library/era_ownership.gd, extends RefCounted, loaded with
#     load(...).new(), no class_name):
#     owned_from_store(path: String, installed_ids: Array) -> Array   the release-build reader, no
#         debug check: file {"owned":[...]} limits the result to listed ids that are installed; no
#         file = every installed id
#     owned_ids(installed_ids: Array, path := "user://era_ownership.json") -> Array
#         OS.is_debug_build() ? every installed id : owned_from_store(path, installed_ids)
# With no qa_set_sources call both scenes read res://assets/eras/ (the live default).

const LIB := "res://scenes/era_library/era_library.tscn"
const DETAIL := "res://scenes/era_library/era_detail.tscn"
const REAL_PACKS := "res://assets/eras"
const FIX_ROOT := "user://c4_e1_fixture_packs"
const STORE := "user://era_ownership.json"
const SEAM_STORE := "user://c4_e1_seam_ownership.json"
const PLAY_TEXT := ["play", "start campaign", "begin campaign", "launch era"]
const PROGRESS_TEXT := ["mastery", "tier progress", "not yet tracked"]
const LEGACY_TEXT := ["Legionary", "Medicus", "Roman", "Cold War", "Available on Steam", "COMING SOON", "Thalassa", "Tomcat"]

var _pass_count := 0
var _fail_count := 0
var _fail_msgs: Array[String] = []
var _completed := false


func _initialize() -> void:
	await _run_tests()
	_assert(_completed, "the era-library checks did not run to the end (a script error aborted them)")
	print("\n=== Era Library Live Test Results ===")
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


func _unit(cat: String, scale := 1.0) -> Dictionary:
	var tiers := {}
	for t in ["1", "2", "3"]:
		tiers[t] = {"scene": "placeholder.glb"}
	return {"category": cat, "squad_count": 1, "visual_scale": scale, "facing_offset_rad": 0.0, "tiers": tiers}


func _manifest(era_id: String, name: String, accent: String, units: Dictionary, order := 50) -> Dictionary:
	return {
		"era_id": era_id, "era_display_name": name, "era_accent_color": accent,
		"era_spatial_scale": "Scale of " + name, "era_tone": "Tone of " + name, "era_order": order,
		"units": units, "structures": {}, "environment": {}, "materials": {},
		"faction_colors": {"0": "#4099FF"},
	}


func _write_pack(era_id: String, manifest: Dictionary) -> void:
	var dir := FIX_ROOT + "/" + era_id
	DirAccess.make_dir_recursive_absolute(dir)
	var f := FileAccess.open(dir + "/manifest.json", FileAccess.WRITE)
	f.store_string(JSON.stringify(manifest))
	f.close()
	# placeholder.glb so scene paths resolve for the validator; content is irrelevant here
	var g := FileAccess.open(dir + "/placeholder.glb", FileAccess.WRITE)
	g.store_string("x")
	g.close()


func _texts(node: Node, out: Array) -> Array:
	if node is Label:
		out.append((node as Label).text)
	elif node is RichTextLabel:
		out.append((node as RichTextLabel).text)
	elif node is Button:
		out.append((node as Button).text)
	for c in node.get_children():
		_texts(c, out)
	return out


func _legacy_hits(node: Node) -> Array:
	var hits := []
	for t in _texts(node, []):
		for bad in LEGACY_TEXT:
			if str(t).findn(bad) >= 0:
				hits.append("%s in '%s'" % [bad, t])
	return hits


# Names of any mastery/tier-progress text, state key, or progress-bar node under the scene or state.
func _progress_hits(node: Node, state) -> Array:
	var hits := []
	for t in _texts(node, []):
		for bad in PROGRESS_TEXT:
			if str(t).findn(bad) >= 0:
				hits.append("text '%s'" % t)
	_progress_nodes(node, hits)
	_progress_keys(state, hits)
	return hits


func _progress_nodes(node: Node, hits: Array) -> void:
	if node is ProgressBar:
		hits.append("ProgressBar node %s" % node.name)
	for c in node.get_children():
		_progress_nodes(c, hits)


func _progress_keys(v, hits: Array) -> void:
	if v is Dictionary:
		for k in v.keys():
			var ks := str(k).to_lower()
			if ks.find("mastery") >= 0 or ks.find("progress") >= 0:
				hits.append("state key '%s'" % k)
			_progress_keys(v[k], hits)
	elif v is Array:
		for x in v:
			_progress_keys(x, hits)


func _play_hits(node: Node) -> Array:
	var hits := []
	if node is Button:
		for bad in PLAY_TEXT:
			if str((node as Button).text).findn(bad) >= 0:
				hits.append("Button '%s'" % (node as Button).text)
	for c in node.get_children():
		hits.append_array(_play_hits(c))
	return hits


func _role_hits(node: Node, state) -> Array:
	var hits := []
	for t in _texts(node, []):
		if str(t).findn("role") >= 0:
			hits.append("text '%s'" % t)
	_role_keys(state, hits)
	return hits


func _role_keys(v, hits: Array) -> void:
	if v is Dictionary:
		for k in v.keys():
			var ks := str(k).to_lower()
			if ks.find("role") >= 0 or ks.find("description") >= 0:
				hits.append("state key '%s'" % k)
			_role_keys(v[k], hits)
	elif v is Array:
		for x in v:
			_role_keys(x, hits)


func _ids_in_order(eras: Array) -> Array:
	var ids := []
	for e in eras:
		ids.append(e.get("id", ""))
	return ids


func _read_json(path: String) -> Dictionary:
	var f := FileAccess.open(path, FileAccess.READ)
	if f == null:
		return {}
	var v = JSON.parse_string(f.get_as_text())
	return v if v is Dictionary else {}


func _write_text(path: String, text: String) -> void:
	var f := FileAccess.open(path, FileAccess.WRITE)
	f.store_string(text)
	f.close()


func _entry(eras: Array, id: String) -> Dictionary:
	for e in eras:
		if e is Dictionary and e.get("id", "") == id:
			return e
	return {}


func _mount(path: String, packs_root: String):
	var scene: Node = (load(path) as PackedScene).instantiate()
	get_root().add_child(scene)
	await process_frame
	if packs_root != "":
		if not scene.has_method("qa_set_sources"):
			_assert(false, "%s root missing qa_set_sources (piece C4-E1 not attached yet)" % path)
			scene.queue_free()
			return null
		scene.qa_set_sources(packs_root, "")
		await process_frame
	return scene


func _run_tests() -> void:
	# Positive control for the hard-coded-text detector: a tree that holds legacy text must be caught.
	var ctl := Control.new()
	var ctl_label := Label.new()
	ctl_label.text = "Legionary"
	ctl.add_child(ctl_label)
	_assert(_legacy_hits(ctl).size() == 1, "control: legacy-text scan failed to catch a planted 'Legionary' label")
	var ctl_prog := Label.new()
	ctl_prog.text = "Mastery 40%"
	ctl.add_child(ctl_prog)
	var ctl_bar := ProgressBar.new()
	ctl.add_child(ctl_bar)
	var ctl_hits := _progress_hits(ctl, {"eras": [{"id": "x", "tier_progress": 1}]})
	_assert(ctl_hits.size() == 3, "control: progress scan caught %s, expected a planted mastery label, ProgressBar and tier_progress key (3)" % [ctl_hits])
	var ctl_play := Button.new()
	ctl_play.text = "Play this era"
	ctl.add_child(ctl_play)
	_assert(_play_hits(ctl).size() == 1, "control: play-control scan failed to catch a planted 'Play this era' button")
	var ctl_role := Label.new()
	ctl_role.text = "Role: flanker"
	ctl.add_child(ctl_role)
	var ctl_role_hits := _role_hits(ctl, {"roster": [{"abstract_type": "x", "role_text": "y"}]})
	_assert(ctl_role_hits.size() == 2, "control: role scan caught %s, expected a planted 'Role:' label and a role_text key (2)" % [ctl_role_hits])
	ctl.free()

	# Fixture packs: two valid, one that fails validation (missing the required key "materials").
	_write_pack("zz_dunes", _manifest("zz_dunes", "The Fixture Dunes", "#aa5500",
		{"alpha": _unit("line"), "beta": _unit("strike"), "gamma": _unit("siege")}, 20))
	_write_pack("zz_tide", _manifest("zz_tide", "The Fixture Tide", "#0055aa", {"delta": _unit("line")}, 10))
	# A58 07: a valid pack that says test_only is never listed (flipped to false later as the control)
	var hidden := _manifest("zz_hidden", "Hidden Fixture Pack", "#222222", {"zeta": _unit("line")}, 5)
	hidden["test_only"] = true
	_write_pack("zz_hidden", hidden)
	# A58 05: a pack missing era_tone fails validation and is not listed (control: repaired later)
	var notone := _manifest("zz_notone", "No Tone Fixture Pack", "#333333", {"eta": _unit("line")}, 6)
	notone.erase("era_tone")
	_write_pack("zz_notone", notone)
	var broken := _manifest("zz_broken", "Broken Fixture Pack", "#111111", {"eps": _unit("line")})
	broken.erase("materials")
	_write_pack("zz_broken", broken)

	# --- Library over the fixture packs (R-110-05, R-110-07) ---
	var lib = await _mount(LIB, FIX_ROOT)
	if lib == null:
		return
	for m in ["qa_set_sources", "qa_state"]:
		_assert(lib.has_method(m), "era_library root missing method: " + m)
	var st: Dictionary = lib.qa_state()
	_assert(JSON.stringify(st) != "", "era_library qa_state() did not survive JSON.stringify")
	var eras: Array = st.get("eras", [])
	var ids := _ids_in_order(eras)
	# zz_tide has era_order 10 and zz_dunes 20: ascending era_order is the reverse of alphabetical
	_assert(ids == ["zz_tide", "zz_dunes"], "R-110-05/A58 05: library over fixture packs lists %s, expected exactly [zz_tide, zz_dunes] in era_order (invalid, missing-key and test_only packs hidden, nothing hard-coded)" % [ids])
	_assert(int(_entry(eras, "zz_dunes").get("order", -1)) == 20, "A58 05: card order is the manifest's era_order (20), got %s" % [_entry(eras, "zz_dunes").get("order")])
	_assert(int(st.get("era_count", -1)) == eras.size(), "era_count %s != eras.size() %d" % [st.get("era_count"), eras.size()])
	var dunes := _entry(eras, "zz_dunes")
	_assert(dunes.get("name", "") == "The Fixture Dunes", "R-110-05: card name '%s' is not the manifest's era_display_name" % dunes.get("name", ""))
	_assert(bool(dunes.get("owned", false)) and bool(_entry(eras, "zz_tide").get("owned", false)),
		"R-110-07: in a dev build every installed era is owned, got %s" % [eras])
	var phits := _progress_hits(lib, st)
	_assert(phits.is_empty(), "R-110-07/A51: library shows mastery or tier progress, it must be removed entirely: %s" % [phits])
	var texts := _texts(lib, [])
	_assert("The Fixture Dunes" in texts, "R-110-05: no label on the library screen shows the manifest name 'The Fixture Dunes'")
	_assert(dunes.get("spatial_scale", "") == "Scale of The Fixture Dunes" and dunes.get("tone", "") == "Tone of The Fixture Dunes",
		"R-110-05/A58 05: card scale/tone %s/%s are not the manifest's era_spatial_scale/era_tone" % [dunes.get("spatial_scale"), dunes.get("tone")])
	_assert("Scale of The Fixture Dunes" in texts and "Tone of The Fixture Dunes" in texts,
		"R-110-05/A58 05: the library screen does not show the manifest scale and tone sentences, labels were %s" % [texts])
	var lib_play := _play_hits(lib)
	_assert(lib_play.is_empty(), "A58 08: the Era Library is a viewing screen, it has a play control: %s" % [lib_play])
	var hits := _legacy_hits(lib)
	_assert(hits.is_empty(), "R-110-06: hard-coded legacy text still on the library screen: %s" % [hits])

	# Positive control for the validation filter: repair the broken pack, it must now be listed.
	_write_pack("zz_broken", _manifest("zz_broken", "Broken Fixture Pack", "#111111", {"eps": _unit("line")}))
	lib.qa_set_sources(FIX_ROOT, "")
	await process_frame
	var ids2 := []
	for e in lib.qa_state().get("eras", []):
		ids2.append(e.get("id", ""))
	_assert("zz_broken" in ids2, "control: a repaired pack must appear once it passes validation, got %s" % [ids2])
	# Controls for A58 05 and 07: restore era_tone / drop test_only and both packs must appear.
	_write_pack("zz_notone", _manifest("zz_notone", "No Tone Fixture Pack", "#333333", {"eta": _unit("line")}, 6))
	hidden.erase("test_only")
	_write_pack("zz_hidden", hidden)
	lib.qa_set_sources(FIX_ROOT, "")
	await process_frame
	var ids3 := _ids_in_order(lib.qa_state().get("eras", []))
	_assert("zz_notone" in ids3, "control: a pack with era_tone restored must be listed, got %s" % [ids3])
	_assert("zz_hidden" in ids3, "control: a pack without test_only must be listed, got %s" % [ids3])
	_assert(ids3.find("zz_hidden") < ids3.find("zz_tide"), "A58 05: era_order 5 sorts before 10, got %s" % [ids3])
	lib.queue_free()
	await process_frame

	# --- Ownership (A58 04). This runner is a debug build: the store must be ignored. ---
	_assert(OS.is_debug_build(), "precondition: the test runner is a debug build (godot binary, not an export)")
	var backup := ""
	var had_store := FileAccess.file_exists(STORE)
	if had_store:
		backup = FileAccess.get_file_as_string(STORE)
	_write_text(STORE, JSON.stringify({"owned": ["zz_dunes"]}))
	_write_text(SEAM_STORE, JSON.stringify({"owned": ["zz_dunes"]}))
	var own = await _mount(LIB, "")
	own.qa_set_sources(FIX_ROOT, "")
	await process_frame
	var own_eras: Array = own.qa_state().get("eras", [])
	var own_ok := not own_eras.is_empty()
	for e in own_eras:
		own_ok = own_ok and bool(e.get("owned", false))
	_assert(own_ok, "A58 04: debug build must own every installed pack even with the store planted as only zz_dunes, got %s" % [own_eras])
	own.qa_set_sources(FIX_ROOT, SEAM_STORE)
	await process_frame
	var own_ok2 := true
	for e in own.qa_state().get("eras", []):
		own_ok2 = own_ok2 and bool(e.get("owned", false))
	_assert(own_ok2, "A58 04: debug build ignores an explicit ownership path too")
	own.queue_free()
	await process_frame
	var odet = await _mount(DETAIL, FIX_ROOT)
	odet.setup({"era_id": "zz_tide"})
	await process_frame
	_assert(bool(odet.qa_state().get("owned", false)), "A58 04: debug build, detail of zz_tide owned although the store lists only zz_dunes")
	odet.queue_free()
	await process_frame
	if had_store:
		_write_text(STORE, backup)
	else:
		DirAccess.remove_absolute(STORE)

	# The release-path reader, tested through its path seam.
	var own_script = load("res://scenes/era_library/era_ownership.gd")
	if own_script == null or not own_script.can_instantiate():
		_assert(false, "era_ownership.gd missing or not instantiable (piece C4-E1 not attached yet)")
	else:
		var reader = own_script.new()
		for m in ["owned_from_store", "owned_ids"]:
			_assert(reader.has_method(m), "era_ownership.gd missing method: " + m)
		if reader.has_method("owned_from_store") and reader.has_method("owned_ids"):
			var installed := ["zz_dunes", "zz_tide", "zz_hidden"]
			var limited: Array = reader.owned_from_store(SEAM_STORE, installed)
			limited.sort()
			_assert(limited == ["zz_dunes"], "A58 04: store {owned:[zz_dunes]} must limit owned to [zz_dunes], got %s" % [limited])
			_write_text(SEAM_STORE, JSON.stringify({"owned": []}))
			var none: Array = reader.owned_from_store(SEAM_STORE, installed)
			_assert(none.is_empty(), "A58 04: store {owned:[]} owns nothing, got %s" % [none])
			DirAccess.remove_absolute(SEAM_STORE)
			var all: Array = reader.owned_from_store(SEAM_STORE, installed)
			all.sort()
			var want := installed.duplicate()
			want.sort()
			_assert(all == want, "A58 04: no store file = every installed pack owned (nothing is sold yet), got %s" % [all])
			_write_text(SEAM_STORE, JSON.stringify({"owned": ["zz_dunes"]}))
			var dbg: Array = reader.owned_ids(installed, SEAM_STORE)
			dbg.sort()
			_assert(dbg == want, "A58 04: owned_ids in a debug build owns every installed pack despite the store, got %s" % [dbg])
			DirAccess.remove_absolute(SEAM_STORE)

	# --- Library over the live packs (default path) ---
	var live = await _mount(LIB, "")
	var live_ids := []
	for e in live.qa_state().get("eras", []):
		live_ids.append(e.get("id", ""))
	_assert("settled_reach" in live_ids and "greek_placeholder" in live_ids,
		"R-110-05: live library must list the installed packs settled_reach and greek_placeholder, got %s" % [live_ids])
	_assert(not ("test_era" in live_ids), "A58 07: test_era is test_only and must not be listed, got %s" % [live_ids])
	var live_order := {}
	for id in ["settled_reach", "greek_placeholder"]:
		live_order[id] = int(_read_json("%s/%s/manifest.json" % [REAL_PACKS, id]).get("era_order", -1))
	_assert(live_order["settled_reach"] >= 0 and live_order["greek_placeholder"] >= 0 and live_order["settled_reach"] != live_order["greek_placeholder"],
		"A58 05: the installed manifests need distinct integer era_order, got %s" % [live_order])
	var expect_first: String = "settled_reach" if live_order["settled_reach"] < live_order["greek_placeholder"] else "greek_placeholder"
	var expect_second: String = "greek_placeholder" if expect_first == "settled_reach" else "settled_reach"
	_assert(live_ids.find(expect_first) >= 0 and live_ids.find(expect_first) < live_ids.find(expect_second),
		"A58 05: the live library lists in era_order %s, got %s" % [live_order, live_ids])
	for e in live.qa_state().get("eras", []):
		_assert(str(e.get("spatial_scale", "")).strip_edges() != "" and str(e.get("tone", "")).strip_edges() != "",
			"A58 05: live card '%s' has no spatial scale or tone from its manifest" % e.get("id"))
	for gone in ["roman", "1980s"]:
		_assert(not (gone in live_ids), "R-110-06: '%s' has no pack under assets/eras/ yet is listed (hard-coded era)" % gone)
	for id in live_ids:
		_assert(FileAccess.file_exists("%s/%s/manifest.json" % [REAL_PACKS, id]), "listed era '%s' has no installed pack manifest" % id)
	live.queue_free()
	await process_frame

	# --- Detail (R-110-06, R-110-07) ---
	var det = await _mount(DETAIL, FIX_ROOT)
	if det == null:
		return
	det.setup({"era_id": "zz_dunes"})
	await process_frame
	var ds: Dictionary = det.qa_state() if det.has_method("qa_state") else {}
	_assert(JSON.stringify(ds) != "", "era_detail qa_state() did not survive JSON.stringify")
	_assert(ds.get("era_id", "") == "zz_dunes" and ds.get("name", "") == "The Fixture Dunes",
		"R-110-06: detail identity %s/%s, expected zz_dunes / The Fixture Dunes" % [ds.get("era_id"), ds.get("name")])
	_assert(bool(ds.get("owned", false)), "R-110-07: dev build, detail must report owned")
	var tiers := []
	for t in ds.get("tiers", []):
		tiers.append(int(t))
	tiers.sort()
	_assert(tiers == [1, 2, 3], "R-110-06: detail tiers %s, expected [1, 2, 3] from the manifest" % [tiers])
	var roster := {}
	for r in ds.get("roster", []):
		roster[r.get("abstract_type", "")] = r.get("category", "")
	_assert(roster == {"alpha": "line", "beta": "strike", "gamma": "siege"},
		"R-110-06: detail roster %s, expected exactly the manifest units alpha/beta/gamma with their categories" % [roster])
	# A58 06: roster title is the type id, then the category; no role text. A58 08: no play control.
	var dl_texts := _texts(det, [])
	var dl_lower := []
	for t in dl_texts:
		dl_lower.append(str(t).to_lower())
	for id in ["alpha", "beta", "gamma"]:
		_assert(id in dl_lower, "A58 06: roster shows no label with the type id '%s' as its title, labels were %s" % [id, dl_texts])
	for cat in ["line", "strike", "siege"]:
		var seen := false
		for t in dl_lower:
			seen = seen or (t.find(cat) >= 0)
		_assert(seen, "A58 06: roster shows no label with the category '%s'" % cat)
	var drhits := _role_hits(det, ds)
	_assert(drhits.is_empty(), "A58 06: the roster shows or exposes role text, the manifest has none and none is invented: %s" % [drhits])
	var det_play := _play_hits(det)
	_assert(det_play.is_empty(), "A58 08: the era detail is a viewing screen, it has a play control: %s" % [det_play])
	_assert(not (ds.has("can_play") or ds.has("play_enabled") or ds.has("playable")), "A58 08: detail state exposes a play flag: %s" % [ds.keys()])
	var dphits := _progress_hits(det, ds)
	_assert(dphits.is_empty(), "R-110-07/A51: detail shows mastery or tier progress, it must be removed entirely: %s" % [dphits])
	var dtexts := _texts(det, [])
	_assert("The Fixture Dunes" in dtexts, "R-110-06: detail screen shows no label with the manifest name")
	var dhits := _legacy_hits(det)
	_assert(dhits.is_empty(), "R-110-06: hard-coded legacy text still on the detail screen: %s" % [dhits])
	det.queue_free()
	await process_frame

	_completed = true
